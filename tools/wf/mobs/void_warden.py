"""The Void Warden (Gardien du vide): the final boss, a tall void knight (about 5 blocks to the helm, the
horns higher still) in obsidian and purpur plate split by glowing starlight seams.

Silhouette: great crescent horns sweeping out and back from a slit-visored helm, a broken halo of stars
behind the head, wide layered pauldrons, a living cape of stars that opens into two tattered wings, and a
huge curved void greatsword held in a low guard, its tip hovering over the ground."""
import math

from ..models import Model, FACE_ID
from ..texgen import mix, mul

OBS = (26, 18, 40)          # obsidian plate
OBS_L = (54, 40, 82)        # sheen
OBS_D = (12, 8, 20)
PUR = (176, 124, 196)       # purpur trim
PUR_D = (118, 80, 140)
PUR_L = (214, 172, 226)
VOID = (12, 8, 24)          # void cloth
VOID_L = (30, 20, 54)
STAR = (250, 236, 255)      # starlight
STAR_V = (206, 136, 255)
STAR_C = (150, 220, 255)
VIS = (214, 110, 255)       # visor glow


def _h(*v):
    r = 0x9E3779B9
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        r ^= r >> 13
    return r


def plate(seed=0, seam=None, rim=PUR_D):
    """Obsidian plate: a purpur rim, a diagonal sheen on the face; ``seam`` = faces with a glowing
    starlight seam down their middle."""
    def f(face, x, y, w, h):
        if seam and face in seam and w >= 3 and abs(x - (w - 1) / 2) < 0.6 and 0 < y < h - 1:
            return STAR_V
        if face not in ("top", "bottom") and h > 3 and y == 0:
            return rim
        if face not in ("top", "bottom") and h > 3 and y == h - 1:
            return OBS_D
        if face == "top":
            return mix(OBS, OBS_L, 0.3)
        if face != "bottom" and h >= 8 and w >= 5:
            if y == 2 and 1 <= x <= w - 2:
                return PUR_D                       # engraved band under the rim
            if (x, y) in ((1, h - 2), (w - 2, h - 2)):
                return PUR_L                       # rivets
        if (x + y + seed) % 12 == 0:
            return mix(OBS, OBS_L, 0.7)            # a faint diagonal sheen
        return mix(OBS_L, OBS_D, min(1.0, 0.25 + y / max(1, h - 1) * 0.75)) if face != "bottom" else OBS_D
    return f


def seam_glow(seam):
    def f(face, x, y, w, h):
        if face in seam and w >= 3 and abs(x - (w - 1) / 2) < 0.6 and 0 < y < h - 1:
            return STAR_V
        return None
    return f


def trim(face, x, y, w, h):
    """Purpur trim: lit top row, a darker groove."""
    if face == "top" or y == 0:
        return PUR_L
    if y == h - 1:
        return PUR_D
    return PUR if (x + y) % 4 else mix(PUR, PUR_D, 0.5)


def _star(face, x, y, seed):
    """Sparse star field: big four-point stars, small dots, a faint nebula."""
    hh = _h(x // 6, y // 6, seed, FACE_ID[face])
    cx, cy = (x // 6) * 6 + hh % 5, (y // 6) * 6 + (hh >> 4) % 5
    dx, dy = abs(x - cx), abs(y - cy)
    if hh % 3 == 0:
        if dx + dy == 0:
            return STAR
        if dx + dy == 1:
            return STAR_V if hh % 2 else STAR_C
    elif dx == 0 and dy == 0 and hh % 3 == 1:
        return STAR_V if (hh >> 8) % 2 else STAR_C
    return None


def cloth(seed=0, ragged=True):
    """The cape of stars: deep void with a violet nebula toward the hem and a field of stars;
    a ragged, torn hem (transparent)."""
    def f(face, x, y, w, h):
        if ragged and face in ("front", "back", "left", "right") and y >= h - 1 - (_h(x, seed) % 5):
            return None
        if face in ("front", "back"):
            s = _star(face, x, y, seed)
            if s:
                return s
            t = y / max(1, h - 1)
            base = mix(VOID, VOID_L, 0.25 + 0.5 * t * (0.6 + 0.4 * ((x * 3 + seed) % 5) / 4))
            if x % 5 == 0:
                base = mul(base, 0.8)          # folds
            return base
        return VOID
    return f


def cloth_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            return _star(face, x, y, seed)
        return None
    return f


def blade(face, x, y, w, h):
    """Void steel: black core, a violet glowing edge, star runes down the fuller."""
    if face in ("left", "right"):
        if x == 0:
            return VIS
        return OBS_D if x < w - 1 else mix(OBS, PUR_D, 0.4)
    if face in ("top", "bottom"):
        return OBS_D
    if x == 0:
        return VIS                           # cutting edge
    if x == w - 1:
        return PUR_D
    if x == w // 2 and y % 5 == 2:
        return STAR
    return mix(OBS_D, OBS, ((x + y) % 3) / 3)


def blade_glow(face, x, y, w, h):
    if face in ("left", "right") and x == 0:
        return VIS
    if face in ("front", "back"):
        if x == 0:
            return VIS
        if x == w // 2 and y % 5 == 2:
            return STAR
    return None


def build():
    m = Model("void_warden", seed=77, shadow=1.3, walk_speed=0.9, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -34, 0))
    m.part("torso", "hips", pivot=(0, -2, 0), rot=(4, 0, 0))
    m.part("head", "torso", pivot=(0, -27, -1))
    m.part("horn_r", "head", pivot=(-5, -8, 0), rot=(-10, 0, -78))
    m.part("horn_r2", "horn_r", pivot=(0, -9, 0), rot=(-18, 0, 42))
    m.part("horn_r3", "horn_r2", pivot=(0, -11, 0), rot=(-30, 0, 40))
    m.part("horn_l", "head", pivot=(5, -8, 0), rot=(-10, 0, 78))
    m.part("horn_l2", "horn_l", pivot=(0, -9, 0), rot=(-18, 0, -42))
    m.part("horn_l3", "horn_l2", pivot=(0, -11, 0), rot=(-30, 0, -40))
    m.part("halo", "torso", pivot=(0, -36, 10), rot=(-8, 0, 0))
    m.part("cape_r", "torso", pivot=(-3, -25, 6), rot=(10, 0, 4))
    m.part("cape_r2", "cape_r", pivot=(0, 26, 0), rot=(6, 0, 0))
    m.part("cape_l", "torso", pivot=(3, -25, 6), rot=(10, 0, -4))
    m.part("cape_l2", "cape_l", pivot=(0, 26, 0), rot=(6, 0, 0))
    m.part("arm_r", "torso", pivot=(-12, -21, 0), rot=(-12, 0, 10))
    m.part("forearm_r", "arm_r", pivot=(0, 12, 0), rot=(-38, 0, 0))
    m.part("sword", "forearm_r", pivot=(0, 15, -1), rot=(172, 0, 28))
    m.part("blade2", "sword", pivot=(0, -24, 0), rot=(-9, 0, 0))
    m.part("blade3", "blade2", pivot=(0, -20, 0), rot=(-12, 0, 0))
    m.part("arm_l", "torso", pivot=(12, -21, 0), rot=(-6, 0, -10))
    m.part("forearm_l", "arm_l", pivot=(0, 12, 0), rot=(-22, 0, 0))
    m.part("leg_r", "hips", pivot=(-5, 0, 0), rot=(-4, 0, 3))
    m.part("shin_r", "leg_r", pivot=(0, 16, 0), rot=(6, 0, 0))
    m.part("leg_l", "hips", pivot=(5, 0, 0), rot=(4, 0, -3))
    m.part("shin_l", "leg_l", pivot=(0, 16, 0), rot=(4, 0, 0))

    # ------------------------------------------------------------------ legs: plated, long and slender
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -4, -1, -4, 8, 17, 8, plate(10 + sx))
        m.box(leg, -4, 4, -5, 8, 9, 1, plate(11 + sx, seam=("front",)), glow=seam_glow(("front",)))  # cuisse
        m.box(shin, -3, 0, -3, 6, 16, 6, plate(12 + sx))
        m.box(shin, -4, -2, -5, 8, 5, 3, trim)                                    # knee cop
        m.box(shin, -4, 3, -4, 8, 9, 1, plate(13 + sx, seam=("front",)), glow=seam_glow(("front",)))  # greave
        m.box(shin, -4, 14, -7, 8, 4, 11, plate(14 + sx))                         # sabaton
        m.box(shin, -2, 15, -9, 4, 3, 2, plate(15 + sx))                          # pointed toe

    # ------------------------------------------------------------------ torso: faulds, waist, breastplate
    m.box("hips", -8, -4, -5, 16, 7, 10, plate(1))
    m.box("hips", -6, 3, -6, 12, 20, 1, cloth(3, ragged=True), glow=cloth_glow(3))   # tabard front
    m.box("hips", -9, 2, -5, 1, 9, 10, plate(2))                                  # tassets
    m.box("hips", 8, 2, -5, 1, 9, 10, plate(2))
    m.box("torso", -7, -9, -4, 14, 10, 8, plate(3))
    m.box("torso", -11, -25, -6, 22, 17, 12, plate(4, seam=("front",)), glow=seam_glow(("front",)))
    m.box("torso", -8, -21, -7, 16, 10, 1, plate(5, seam=("front",)), glow=seam_glow(("front",)))  # raised cuirass
    m.box("torso", -9, -10, -5, 18, 2, 10, trim)                                  # belt
    m.box("torso", -1, -17, -8, 2, 3, 1, STAR, glow=STAR)                          # the star heart
    m.box("torso", -6, -28, -5, 12, 4, 10, plate(6))                              # gorget
    m.box("torso", -7, -26, -6, 14, 2, 1, trim)

    # ------------------------------------------------------------------ head: slit-visored helm, horns, halo
    m.box("head", -5, -12, -6, 10, 12, 11, {
        "front": lambda f_, x, y, w, h: VIS if (y == 5 and 1 <= x <= w - 2) or (x in (4, 5) and 5 <= y <= 8)
        else plate(20)(f_, x, y, w, h), "*": plate(20)},
        glow={"front": lambda f_, x, y, w, h: VIS if (y == 5 and 1 <= x <= w - 2) or (x in (4, 5) and 5 <= y <= 8) else None})
    m.box("head", -1, -15, -7, 2, 5, 12, trim)                                    # crest
    m.box("head", -6, -6, -7, 12, 2, 1, plate(21))                                # cheek guard line
    for side, sx in (("r", -1), ("l", 1)):
        h1, h2, h3 = f"horn_{side}", f"horn_{side}2", f"horn_{side}3"
        m.box(h1, -3, -10, -3, 5, 10, 5, plate(22 + sx, rim=OBS_L))
        m.box(h2, -2, -12, -2, 4, 12, 4, plate(23 + sx, rim=OBS_L))
        m.box(h3, -1, -10, -1, 3, 10, 3, plate(24 + sx, rim=OBS_L))
        m.box(h3, -1, -15, 0, 2, 5, 2, lambda f_, x, y, w, h: STAR if y < 2 else PUR_L,
              glow=lambda f_, x, y, w, h: STAR if y < 2 else PUR_L if y < 4 else None)
    # broken halo: a ring of starlight shards behind the helm, cracked open at two places
    for k in range(30):
        if k in (6, 7, 19):
            continue
        a = math.radians(k * 12)
        x, y = math.cos(a) * 19, math.sin(a) * 19
        big = k % 3 == 0
        col = STAR if big else STAR_V
        m.box("halo", round(x) - (1 if big else 0), round(y) - (1 if big else 0), 0, 3 if big else 2, 3 if big else 2, 1,
              col, glow=col)

    # ------------------------------------------------------------------ cape of stars (folds open into wings)
    for side, sx in (("r", -1), ("l", 1)):
        c1, c2 = f"cape_{side}", f"cape_{side}2"
        x0 = -11 if sx < 0 else 0
        m.box(c1, x0, 0, 0, 11, 26, 1, cloth(30 + sx, ragged=False), glow=cloth_glow(30 + sx))
        m.box(c2, x0, 0, 0, 11, 26, 1, cloth(32 + sx, ragged=True), glow=cloth_glow(32 + sx))
    # ------------------------------------------------------------------ arms: layered pauldrons, gauntlets
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -3, -1, -3, 6, 14, 6, plate(40 + sx))
        m.box(arm, -7, -7, -7, 14, 8, 14, plate(41 + sx, seam=("top",)), glow=seam_glow(("top",)))   # pauldron
        m.box(arm, -8 if sx < 0 else -6, 1, -7, 14, 3, 14, trim)                                      # lames
        m.box(arm, -8 if sx < 0 else -6, 4, -6, 14, 3, 12, plate(42 + sx))
        m.box(arm, 5 if sx > 0 else -8, -15, -6, 3, 9, 12, plate(46 + sx, seam=("left", "right")),      # flared crest
              glow=seam_glow(("left", "right")))
        m.box(arm, 5 if sx > 0 else -8, -18, -3, 3, 3, 6, lambda f_, x, y, w, h: PUR_L)
        m.box(fore, -3, 0, -3, 6, 13, 6, plate(43 + sx))
        m.box(fore, -4, 6, -4, 8, 6, 8, plate(44 + sx, seam=("front", "back")), glow=seam_glow(("front", "back")))
        m.box(fore, -3, 13, -3, 6, 5, 6, plate(45 + sx))                                              # fist

    # ------------------------------------------------------------------ the void greatsword (curved)
    m.box("sword", -1, 1, -1, 2, 7, 2, lambda f_, x, y, w, h: PUR_D if y % 2 else OBS)                  # grip
    m.box("sword", -2, 8, -2, 4, 3, 4, trim)                                                            # pommel
    m.box("sword", -7, -2, -2, 14, 3, 4, trim)                                                          # crossguard
    m.box("sword", -1, -3, -3, 2, 2, 1, STAR, glow=STAR)                                                # guard gem
    m.box("sword", -1, -24, -3, 2, 22, 6, blade, glow=blade_glow)
    m.box("blade2", -1, -20, -3, 2, 20, 6, blade, glow=blade_glow)
    m.box("blade3", -1, -16, -2, 2, 16, 5, blade, glow=blade_glow)
    m.box("blade3", -1, -22, -1, 2, 6, 3, blade, glow=blade_glow)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.6)
    idle.rot("torso", (0, (0, 0, 0)), (1.8, (-2, 0, 0)), (3.6, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (3, 5, 0)), (2.4, (3, -4, 0)), (3.6, (0, 0, 0)))
    idle.rot("halo", (0, (0, 0, 0)), (1.8, (0, 0, 8)), (3.6, (0, 0, 0)))
    idle.pos("halo", (0, (0, 0, 0)), (1.8, (0, 1.5, 0)), (3.6, (0, 0, 0)))
    for c, sx in (("cape_r", -1), ("cape_l", 1)):
        idle.rot(c, (0, (0, 0, 0)), (0.9, (6, 0, 3 * sx)), (1.8, (2, 0, 0)), (2.7, (8, 0, 2 * sx)), (3.6, (0, 0, 0)))
    for c in ("cape_r2", "cape_l2"):
        idle.rot(c, (0, (0, 0, 0)), (1.2, (8, 0, 0)), (2.4, (3, 0, 0)), (3.6, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.8, (-3, 0, 0)), (3.6, (0, 0, 0)))

    walk = m.anim("walk", 1.4)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (24 * sign, 0, 0)), (0.7, (-24 * sign, 0, 0)), (1.4, (24 * sign, 0, 0)))
    for shin, sign in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, (0, 0, 0)), (0.35, (22 if sign > 0 else 0, 0, 0)), (0.7, (0, 0, 0)),
                 (1.05, (22 if sign < 0 else 0, 0, 0)), (1.4, (0, 0, 0)))
    walk.rot("arm_l", (0, (-16, 0, 0)), (0.7, (16, 0, 0)), (1.4, (-16, 0, 0)))
    walk.rot("torso", (0, (0, 4, 0)), (0.7, (0, -4, 0)), (1.4, (0, 4, 0)))
    for c in ("cape_r", "cape_l"):
        walk.rot(c, (0, (14, 0, 0)), (0.7, (20, 0, 0)), (1.4, (14, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.35, (0, -1.5, 0)), (0.7, (0, 0, 0)), (1.05, (0, -1.5, 0)), (1.4, (0, 0, 0)))

    # combo: three cuts, right-to-left (0.6 s), backhand (1.1 s), then a leaping overhead (1.75 s)
    a = m.anim("combo", 2.4)
    a.rot("sword", (0, (0, 0, 0)), (0.45, (20, 0, 0)), (0.6, (0, 0, 30), "linear"), (0.85, (0, 0, 30)), (1.1, (50, 0, -75), "linear"), (1.4, (60, 0, 15)), (1.75, (0, 0, -30), "linear"), (2.0, (0, 0, -30)), (2.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.45, (0, 50, 0)), (0.6, (6, -45, 0), "linear"), (0.85, (4, -55, 0)),
          (1.1, (6, 40, 0), "linear"), (1.4, (-18, 10, 0)), (1.75, (26, 0, 0), "linear"), (2.0, (24, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (-60, 70, 30)), (0.6, (-80, -60, 10), "linear"), (0.85, (-90, -70, 30)),
          (1.1, (-80, 50, 30), "linear"), (1.4, (-190, 0, 10)), (1.75, (-60, 0, 0), "linear"), (2.0, (-55, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.45, (20, 0, 0)), (0.6, (30, 0, 0)), (1.4, (-30, 0, 0)), (1.75, (30, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, 0, -4)), (1.1, (0, 0, -7)), (1.4, (0, 5, -8)), (1.75, (0, -2, -14), "linear"), (2.0, (0, -2, -14)), (2.4, (0, 0, 0)))
    for c in ("cape_r", "cape_l"):
        a.rot(c, (0, (0, 0, 0)), (0.6, (25, 0, 0)), (1.4, (40, 0, 0)), (1.75, (10, 0, 0)), (2.4, (0, 0, 0)))

    # blink: dissolves crouching (0-0.3 s), reappears and cuts down diagonally (impact 0.75 s)
    a = m.anim("blink", 1.6)
    a.rot("sword", (0, (0, 0, 0)), (0.4, (0, 0, 30)), (0.6, (20, 0, 45)), (0.75, (10, 0, 0), "linear"), (1.1, (10, 0, 0)), (1.6, (0, 0, 0)))
    a.scale("bone", (0, (1, 1, 1)), (0.25, (0.2, 1.4, 0.2)), (0.3, (0.2, 1.4, 0.2)), (0.4, (1, 1, 1)), (1.6, (1, 1, 1)))
    a.rot("torso", (0, (0, 0, 0)), (0.4, (-16, 40, 0)), (0.6, (-20, 50, 0)), (0.75, (24, -40, 0), "linear"), (1.1, (20, -35, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-160, 20, 30)), (0.6, (-170, 30, 30)), (0.75, (-40, -30, 0), "linear"), (1.1, (-40, -30, 0)), (1.6, (0, 0, 0)))
    for c, sx in (("cape_r", -1), ("cape_l", 1)):
        a.rot(c, (0, (0, 0, 0)), (0.3, (60, 0, 30 * sx)), (0.6, (30, 0, 10 * sx)), (0.75, (10, 0, 0)), (1.6, (0, 0, 0)))

    # pulse: plants the sword point-down, the void lifts everyone around (impact 0.9 s)
    a = m.anim("pulse", 1.9)
    a.rot("sword", (0, (0, 0, 0)), (0.6, (40, 0, 0)), (0.75, (20, 0, 0)), (0.9, (80, 30, 0), "linear"), (1.4, (80, 30, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-150, 0, 20)), (0.75, (-150, 0, 20)), (0.9, (-40, 0, 10), "linear"), (1.4, (-40, 0, 10)), (1.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-150, 0, -20)), (0.9, (-60, 0, -40), "linear"), (1.4, (-60, 0, -40)), (1.9, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.6, (-14, 0, 0)), (0.9, (18, 0, 0), "linear"), (1.4, (16, 0, 0)), (1.9, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, 3, 0)), (0.9, (0, -4, 0), "linear"), (1.4, (0, -4, 0)), (1.9, (0, 0, 0)))
    a.rot("halo", (0, (0, 0, 0)), (0.6, (0, 0, 90)), (0.9, (0, 0, 180)), (1.9, (0, 0, 360)))

    # orbs: the free hand raised, conjuring a handful of void orbs (cast at 0.8 s)
    a = m.anim("orbs", 1.6)
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-170, 0, -15)), (0.8, (-100, 0, -30), "linear"), (1.2, (-100, 0, -30)), (1.6, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.6, (-10, -20, 0)), (0.8, (6, 10, 0), "linear"), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-15, 0, 0)), (1.6, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (0.6, (1.3, 1.3, 1.3)), (0.8, (0.9, 0.9, 0.9)), (1.6, (1, 1, 1)))

    # well: drives the sword into the floor, the void collapses toward it (impact 0.85 s, held to 2.2 s)
    a = m.anim("well", 2.8)
    a.rot("sword", (0, (0, 0, 0)), (0.65, (60, 0, -30)), (0.85, (60, 0, -45), "linear"), (2.2, (60, 0, -45)), (2.8, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.65, (-170, 0, 10 * sx)), (0.85, (-50, 0, -10 * sx), "linear"), (2.2, (-50, 0, -10 * sx)), (2.8, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.65, (-16, 0, 0)), (0.85, (28, 0, 0), "linear"), (2.2, (28, 0, 0)), (2.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.65, (0, 2, 0)), (0.85, (0, -7, 0), "linear"), (2.2, (0, -7, 0)), (2.8, (0, 0, 0)))
    for leg, sh, s in (("leg_r", "shin_r", 1), ("leg_l", "shin_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.85, (-30 if s > 0 else 20, 0, 0)), (2.2, (-30 if s > 0 else 20, 0, 0)), (2.8, (0, 0, 0)))
        a.rot(sh, (0, (0, 0, 0)), (0.85, (40 if s > 0 else 30, 0, 0)), (2.2, (40 if s > 0 else 30, 0, 0)), (2.8, (0, 0, 0)))
    for c, sx in (("cape_r", -1), ("cape_l", 1)):
        a.rot(c, (0, (0, 0, 0)), (0.85, (-20, 0, 50 * sx)), (2.2, (-20, 0, 50 * sx)), (2.8, (0, 0, 0)))

    # summon: sword to the sky, the halo spins, stalkers step out of the void (cast at 0.6 s)
    a = m.anim("summon", 1.8)
    a.rot("sword", (0, (0, 0, 0)), (0.5, (50, 0, 0)), (1.3, (50, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-175, 0, 10)), (1.3, (-175, 0, 10)), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-25, 0, 0)), (1.3, (-25, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("halo", (0, (0, 0, 0)), (1.8, (0, 0, -360)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-40, 0, -60)), (1.3, (-40, 0, -60)), (1.8, (0, 0, 0)))

    # dive (phase 2): crouch, wings snap open, launch (0.5 s), hang in the air, plunge sword-first (1.75 s)
    a = m.anim("dive", 2.6)
    a.rot("sword", (0, (0, 0, 0)), (1.5, (40, 0, 0)), (1.75, (60, 0, -30), "linear"), (2.2, (50, 0, -30)), (2.6, (0, 0, 0)))
    for c, c2, sx in (("cape_r", "cape_r2", 1), ("cape_l", "cape_l2", -1)):
        a.rot(c, (0, (0, 0, 0)), (0.4, (-10, 30 * sx, 108 * sx)), (1.3, (-20, 25 * sx, 118 * sx)), (1.45, (-10, 30 * sx, 92 * sx)),
              (1.6, (-20, 25 * sx, 118 * sx)), (1.75, (40, 0, 20 * sx), "linear"), (2.2, (30, 0, 10 * sx)), (2.6, (0, 0, 0)))
        a.rot(c2, (0, (0, 0, 0)), (0.4, (0, 0, -15 * sx)), (1.3, (0, 0, -22 * sx)), (1.75, (20, 0, 0)), (2.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.35, (0, -6, 0)), (0.6, (0, 20, 0)), (1.6, (0, 22, 0)), (1.75, (0, -5, -10), "linear"), (2.2, (0, -5, -10)), (2.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-20, 0, 30)), (1.5, (-190, 0, 10)), (1.75, (-70, 0, 0), "linear"), (2.2, (-60, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.35, (20, 0, 0)), (0.6, (-15, 0, 0)), (1.5, (-20, 0, 0)), (1.75, (35, 0, 0), "linear"), (2.2, (30, 0, 0)), (2.6, (0, 0, 0)))
    for leg in ("leg_r", "leg_l"):
        a.rot(leg, (0, (0, 0, 0)), (0.35, (-35, 0, 0)), (0.6, (10, 0, 0)), (1.5, (-30, 0, 0)), (1.75, (-40, 0, 0)), (2.2, (-30, 0, 0)), (2.6, (0, 0, 0)))
    for sh in ("shin_r", "shin_l"):
        a.rot(sh, (0, (0, 0, 0)), (0.35, (50, 0, 0)), (0.6, (5, 0, 0)), (1.5, (60, 0, 0)), (1.75, (60, 0, 0)), (2.2, (45, 0, 0)), (2.6, (0, 0, 0)))

    # starrain (phase 2): wings open, sword raised to the sky, the stars fall (called at 0.9 s)
    a = m.anim("starrain", 2.6)
    a.rot("sword", (0, (0, 0, 0)), (0.7, (60, 0, 15)), (2.1, (70, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-175, 0, 15)), (0.9, (-180, 0, 5), "linear"), (2.1, (-180, 0, 5)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-120, 0, -50)), (2.1, (-120, 0, -50)), (2.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (2.1, (-30, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (2.1, (-14, 0, 0)), (2.6, (0, 0, 0)))
    for c, sx in (("cape_r", -1), ("cape_l", 1)):
        a.rot(c, (0, (0, 0, 0)), (0.7, (-20, -25 * sx, -118 * sx)), (2.1, (-20, -25 * sx, -118 * sx)), (2.6, (0, 0, 0)))
    for c2, sx in (("cape_r2", 1), ("cape_l2", -1)):
        a.rot(c2, (0, (0, 0, 0)), (0.7, (0, 0, -22 * sx)), (2.1, (0, 0, -22 * sx)), (2.6, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (0.7, (1.5, 1.5, 1.5)), (2.1, (1.5, 1.5, 1.5)), (2.6, (1, 1, 1)))
    a.rot("halo", (0, (0, 0, 0)), (2.6, (0, 0, 360)))

    # waves (phase 2): two great cuts that send crescents of void along the floor (0.7 s and 1.3 s)
    a = m.anim("waves", 2.1)
    a.rot("sword", (0, (0, 0, 0)), (0.55, (110, 0, -15)), (0.7, (0, 0, 30), "linear"), (1.0, (30, 0, 0)), (1.3, (20, 0, -75), "linear"), (1.6, (20, 0, -75)), (2.1, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.55, (-10, 60, 0)), (0.7, (14, -55, 0), "linear"), (1.0, (-10, -60, 0)),
          (1.3, (16, 40, 0), "linear"), (1.6, (14, 35, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-120, 70, 40)), (0.7, (-60, -70, 0), "linear"), (1.0, (-150, -60, 30)),
          (1.3, (-40, 60, 40), "linear"), (1.6, (-40, 60, 40)), (2.1, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.7, (0, 0, -5), "linear"), (1.3, (0, 0, -9), "linear"), (1.6, (0, 0, -9)), (2.1, (0, 0, 0)))
    for c, sx in (("cape_r", -1), ("cape_l", 1)):
        a.rot(c, (0, (0, 0, 0)), (0.7, (30, 0, 20 * sx)), (1.3, (35, 0, -10 * sx)), (2.1, (0, 0, 0)))

    # roar: the phase change: the wings tear open, the halo flares, the sword flung out to the side
    a = m.anim("roar", 2.6)
    a.rot("sword", (0, (0, 0, 0)), (0.5, (70, 0, 0)), (2.1, (70, 0, 0)), (2.6, (0, 0, 0)))
    for c, c2, sx in (("cape_r", "cape_r2", 1), ("cape_l", "cape_l2", -1)):
        a.rot(c, (0, (0, 0, 0)), (0.5, (-20, 25 * sx, 118 * sx)), (0.65, (-10, 30 * sx, 100 * sx)), (0.8, (-20, 25 * sx, 118 * sx)),
              (2.1, (-20, 25 * sx, 118 * sx)), (2.6, (0, 0, 0)))
        a.rot(c2, (0, (0, 0, 0)), (0.5, (0, 0, -22 * sx)), (2.1, (0, 0, -22 * sx)), (2.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-18, 0, 0)), (2.1, (-18, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-25, 0, 0)), (2.1, (-25, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-30, 0, 70)), (2.1, (-30, 0, 70)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-30, 0, -70)), (2.1, (-30, 0, -70)), (2.6, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (0.5, (1.6, 1.6, 1.6)), (2.1, (1.6, 1.6, 1.6)), (2.6, (1, 1, 1)))

    # stagger: posture broken, down on one knee, leaning on the planted sword
    a = m.anim("stagger", 2.2)
    a.rot("sword", (0, (0, 0, 0)), (0.3, (70, 30, 0)), (1.8, (70, 30, 0)), (2.2, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -9, 2)), (1.8, (0, -9, 2)), (2.2, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-80, 0, 0)), (1.8, (-80, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.8, (80, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (10, 0, 0)), (1.8, (10, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (75, 0, 0)), (1.8, (75, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.3, (22, 0, 0)), (1.8, (22, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.8, (20, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (1.8, (-40, 0, 0)), (2.2, (0, 0, 0)))
    return m
