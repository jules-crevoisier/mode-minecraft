"""The Grave Knight (Le Chevalier des tombes): a huge (about 3.6 blocks) skeleton knight-lord in black plate
filigreed with gold, a torn royal purple cape hanging from one shoulder, a crowned great helm whose T-visor
shows a skull with cold soul-fire eyes, a skull-pauldron on the left shoulder, and a two-handed greatsword
with a glowing rune fuller that he drags behind him."""
from ..models import Model
from ..texgen import mix, mul
from .skeleton_knight import BONE, BONE_D, BONE_DD, SOCKET, H, bone, cloth, ribs

BLACK = (38, 36, 44)
BLACK_L = (74, 72, 86)
GOLD = (226, 182, 72)
GOLD_L = (252, 224, 130)
GOLD_D = (148, 102, 36)
PURPLE = (82, 30, 96)
PURPLE_D = (46, 16, 58)
SOUL = (110, 232, 255)
# rest pose of the sword arm (degrees): the blade is held low and forward, pointing at the foe
ARM, FORE, SWORD = -20, -25, 155
BLADE = (84, 88, 100)
BLADE_L = (150, 156, 170)


def plate(seed=0, rim=GOLD_D, filigree=False, sheen=True):
    """Blackened royal plate: a gold rim, a soft top-lit sheen, fine scratches, optional gold filigree."""
    def f(face, x, y, w, h):
        edge = x == 0 or y == 0 or x == w - 1 or y == h - 1
        if rim is not None and edge and w > 2 and h > 2 and face != "bottom":
            return GOLD if (y == 0 and face != "top") or face == "top" else rim
        c = BLACK
        if sheen and face in ("front", "back", "left", "right"):
            c = mix(BLACK_L, BLACK, min(1.0, y / max(1.0, h * 0.55)))
        if face == "top":
            c = mix(BLACK, BLACK_L, 0.45)
        r = H(x, y, seed)
        if r % 23 == 0:
            c = mix(c, BLACK_L, 0.7)  # scratch
        if filigree and face == "front":
            cx = (w - 1) / 2
            dx = abs(x - cx)
            # a gold chevron and two scrolling lines either side of the centre ridge
            if abs(dx - (h - 1 - y) * 0.6) < 0.55 and y > h * 0.35:
                return GOLD
            if dx < 0.6 and y < h * 0.7:
                return GOLD_D
            if 2 <= y <= 3 and 1 < dx < w * 0.35:
                return GOLD_D if (x + y) % 2 else GOLD
        return c
    return f


def gold(seed=0, base=GOLD, dark=GOLD_D):
    def f(face, x, y, w, h):
        r = H(x, y, seed) % 100
        c = mul(base, 1 + (r / 100 - 0.5) * 0.12)
        if face == "top":
            c = mix(c, GOLD_L, 0.35)
        elif face == "bottom" or (face in ("front", "back", "left", "right") and y == h - 1 and h > 1):
            c = mix(c, dark, 0.6)
        return c
    return f


def build():
    m = Model("grave_knight", seed=44, shadow=1.3, walk_speed=0.85, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -22, 0))
    m.part("torso", "hips", pivot=(0, -3, 0), rot=(7, 0, 0))
    m.part("head", "torso", pivot=(0, -20, -1), rot=(-7, 0, 0))
    m.part("cape", "torso", pivot=(2, -19, 5.5), rot=(6, 0, 4))
    m.part("cape_low", "cape", pivot=(0, 19, 0), rot=(4, 0, 0))
    m.part("arm_r", "torso", pivot=(-9.5, -16, 0), rot=(ARM, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(0, 10, 0), rot=(FORE, 0, 0))
    m.part("sword", "forearm_r", pivot=(0, 11.5, -0.5), rot=(SWORD, 0, 0))
    m.part("arm_l", "torso", pivot=(9.5, -16, 0), rot=(-26, 24, -4))
    m.part("forearm_l", "arm_l", pivot=(0, 10, 0), rot=(-30, 0, 0))
    m.part("leg_r", "bone", pivot=(-4, -22, 0))
    m.part("shin_r", "leg_r", pivot=(0, 11, 0))
    m.part("leg_l", "bone", pivot=(4, -22, 0))
    m.part("shin_l", "leg_l", pivot=(0, 11, 0))

    # ------------------------------------------------------------------ hips and torso
    m.box("hips", -6, -3, -4, 12, 5, 8, plate(1))                                   # belt / pelvis plate
    m.box("hips", -6.5, -2, -4.5, 13, 1, 9, gold(2))                                # gold belt
    m.box("hips", -1.5, -2.5, -5, 3, 3, 1, gold(3, GOLD_L))                         # buckle
    m.box("hips", -6.5, 1, -4.5, 6, 8, 1, plate(4))                                 # front tassets
    m.box("hips", 0.5, 1, -4.5, 6, 8, 1, plate(5))
    m.box("hips", -7, 0, -3.5, 1, 7, 7, plate(6))                                   # hip guards
    m.box("hips", 6, 0, -3.5, 1, 7, 7, plate(7))
    m.box("torso", -4.5, -6, -3, 9, 6, 6, ribs(8))                                  # bare ribs at the waist
    m.box("torso", -1, -6, 1.5, 2, 6, 2, bone(9))                                   # spine
    m.box("torso", -8, -19, -5, 16, 13, 10, {"front": plate(10, filigree=True), "*": plate(11)})
    m.box("torso", -1, -18, -5.6, 2, 11, 1, gold(12))                               # centre ridge
    m.box("torso", -5.5, -22, -4, 11, 3, 8, plate(13, rim=None))                    # gorget
    m.box("torso", -4.5, -9, 3.5, 9, 3, 2, plate(14))                               # back plate lip

    # head: crowned great helm, a T-visor opening on a skull with soul-fire eyes
    def helm_front(face, x, y, w, h):
        cx = (w - 1) / 2
        eye_row = 4
        if y == eye_row and 1 <= x <= w - 2:
            if x in (2, 3, w - 4, w - 3):
                return SOUL
            return SOCKET
        if y == eye_row + 1 and 1 <= x <= w - 2:
            return BONE_D if x in (2, 3, w - 4, w - 3) else SOCKET
        if y > eye_row + 1 and abs(x - cx) < 1.1 and y < h - 1:
            return BONE if y % 2 == 0 else SOCKET  # skull teeth behind the vertical slit
        if face == "front" and (H(x, y, 15) % 9 == 0) and y > eye_row + 1:
            return mix(BLACK_L, BLACK, 0.3)  # breathing holes
        return plate(15, rim=None)(face, x, y, w, h)

    def helm_glow(face, x, y, w, h):
        return SOUL if y == 4 and x in (2, 3, w - 4, w - 3) else None
    m.box("head", -5, -10, -5, 10, 11, 10, {"front": helm_front, "*": plate(16, rim=None)}, glow={"front": helm_glow})
    m.box("head", -5.5, -11, -5.5, 11, 2, 11, gold(17))                              # crown band
    for i, (x, z, hgt) in enumerate(((-5.5, -5.5, 3), (-1.5, -5.5, 5), (3.5, -5.5, 3), (-5.5, -0.5, 3),
                                     (3.5, -0.5, 3), (-5.5, 3.5, 2), (3.5, 3.5, 2), (-1.5, 3.5, 3))):
        m.box("head", x, -11 - hgt, z, 2, hgt, 2, gold(18 + i))
    m.box("head", -1, -12.5, -6, 2, 2, 1, SOUL, glow=SOUL)                          # soul gem in the crown
    m.box("head", -0.5, -2, -5.6, 1, 2, 1, gold(26))                                # nasal guard tip

    # torn royal cape from both shoulders, heavier on the left
    def cape_paint(seed, ragged):
        inner = cloth(seed, PURPLE, PURPLE_D, trim=GOLD, ragged=ragged)

        def f(face, x, y, w, h):
            c = inner(face, x, y, w, h)
            if c is None:
                return None
            if face == "back" and (x in (1, w - 2)):
                return GOLD_D  # gold hem stripes
            if face == "back" and 6 <= y <= 12 and abs(x - (w - 1) / 2) < 3:
                # a faded gold crowned skull emblem
                dx, dy = abs(x - (w - 1) / 2), y - 6
                if dy == 0 and dx < 3 and x % 2 == 0:
                    return GOLD
                if 1 <= dy <= 4 and dx < 2.5 - (dy > 3):
                    return SOCKET if (dy == 2 and 0.5 < dx < 1.6) else mix(GOLD, PURPLE, 0.3)
            if face == "front":
                return mix(c, (30, 10, 30), 0.4)  # dark lining
            return c
        return f
    m.box("cape", -11, 0, 0, 20, 19, 1, {"back": cape_paint(30, 0), "front": cape_paint(31, 0), "*": PURPLE_D})
    m.box("cape_low", -11, 0, 0, 20, 19, 1, {"back": cape_paint(32, 6), "front": cape_paint(33, 6), "*": PURPLE_D})
    m.box("cape", 5, -2, -3, 6, 3, 4, cape_paint(34, 0))                             # folds over the left shoulder

    # ------------------------------------------------------------------ arms
    # right: a plain rounded pauldron; left: a huge pauldron crowned with a skull and a spike
    m.box("arm_r", -4.5, -3.5, -4.5, 8, 6, 9, plate(40))
    m.box("arm_r", -4.5, 2.5, -4, 7, 2, 8, plate(41, rim=GOLD))
    m.box("arm_l", -3.5, -4.5, -5, 10, 7, 10, plate(42))
    m.box("arm_l", -2.5, 2.5, -4.5, 9, 2, 9, plate(43, rim=GOLD))
    skull_f = lambda f_, x, y, w, h: (SOUL if y == 2 and x in (1, 4) else SOCKET if y in (2, 3) and x in (1, 4)  # noqa: E731
                                      else SOCKET if y == 4 and x in (2, 3) else bone(44)(f_, x, y, w, h))
    m.box("arm_l", -0.5, -9.5, -3, 6, 5, 6, {"front": skull_f, "*": bone(45)},
          glow={"front": lambda f_, x, y, w, h: SOUL if y == 2 and x in (1, 4) else None})
    m.box("arm_l", 4.5, -12, -0.5, 1, 7, 1, gold(46))                               # spike
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -2.5, 0, -2.5, 5, 10, 5, plate(47 + sx, rim=None))
        m.box(arm, -2, 8.5, -2, 4, 3, 4, bone(48 + sx))                              # bare elbow joint
        m.box(fore, -2.5, 1, -2.5, 5, 8, 5, plate(49 + sx))
        m.box(fore, -3, 1, -3, 6, 2, 6, gold(50 + sx))                               # gold cuff
        m.box(fore, -2, 9, -2.5, 4, 4, 5, plate(51 + sx, rim=None))                   # gauntlet
        m.box(fore, -2, 12.5, -2, 4, 1, 4, bone(52 + sx, BONE_D))                     # bony fingers

    # greatsword: blade along the part's -y (up from the fist)
    def blade(face, x, y, w, h):
        if face in ("front", "back"):
            if abs(x - (w - 1) / 2) < 0.6:
                return SOUL if y % 5 else mix(SOUL, (255, 255, 255), 0.4)  # glowing rune fuller
            if x == 0 or x == w - 1:
                return BLADE_L
            c = BLADE if H(x, y, 60) % 11 else mix(BLADE, (120, 60, 40), 0.5)
            return c
        return BLADE_L

    def blade_glow(face, x, y, w, h):
        if face in ("front", "back") and abs(x - (w - 1) / 2) < 0.6:
            return SOUL if (y // 3) % 3 else (200, 250, 255)
        return None
    m.box("sword", -1, -2, -1, 2, 7, 2, {"*": lambda f_, x, y, w, h: (40, 28, 26) if y % 2 else (60, 42, 34)})  # grip
    m.box("sword", -1.5, 5, -1.5, 3, 2, 3, gold(61, GOLD_L))                        # pommel
    m.box("sword", -6, -4, -1.5, 12, 2, 3, gold(62))                                 # crossguard
    m.box("sword", -7, -5, -1, 2, 2, 2, gold(63))                                    # quillon ends
    m.box("sword", 5, -5, -1, 2, 2, 2, gold(64))
    m.box("sword", -1.5, -6, -1.5, 3, 2, 3, {"front": lambda f_, x, y, w, h: SOUL if x == 1 else GOLD_D, "*": gold(65)},
          glow={"front": lambda f_, x, y, w, h: SOUL if x == 1 else None})
    m.box("sword", -2.5, -40, -0.5, 5, 34, 1, blade, glow=blade_glow)
    m.box("sword", -1.5, -43, -0.5, 3, 3, 1, blade, glow=blade_glow)                # tapering tip
    m.box("sword", -0.5, -44, -0.5, 1, 1, 1, BLADE_L)

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3, 0, -3, 6, 11, 6, plate(70 + sx, rim=None))
        m.box(leg, -3, 9, -3.5, 6, 3, 2, gold(71 + sx))                              # knee cop
        if sx < 0:   # right greave broken away: bare tibia and a twisted strap
            m.box(shin, -1.5, 0, -1.5, 3, 9, 3, bone(72))
            m.box(shin, -2.5, 3, -2.5, 5, 1, 5, (70, 46, 36))
            m.box(shin, -2.5, 6, -2.5, 5, 3, 5, plate(73, rim=None))
        else:
            m.box(shin, -2.5, 0, -2.5, 5, 9, 5, plate(74))
        m.box(shin, -3, 8, -5, 6, 3, 8, plate(75 + sx))                               # sabaton

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.2)
    idle.rot("torso", (0, (0, 0, 0)), (1.6, (2.5, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (-3, 5, 0)), (2.2, (2, -4, 0)), (3.2, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (1.6, (5, 0, -2)), (3.2, (0, 0, 0)))
    idle.rot("cape_low", (0, (0, 0, 0)), (1.2, (6, 0, 0)), (2.4, (-2, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.6, (-3, 0, -2)), (3.2, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    for leg, sgn in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (22 * sgn, 0, 0)), (0.8, (-22 * sgn, 0, 0)), (1.6, (22 * sgn, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.4, (28, 0, 0)), (0.8, (0, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (1.2, (28, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_l", (0, (-14, 0, 0)), (0.8, (14, 0, 0)), (1.6, (-14, 0, 0)))
    walk.rot("arm_r", (0, (4, 0, 0)), (0.8, (-4, 0, 0)), (1.6, (4, 0, 0)))
    walk.rot("torso", (0, (0, -4, 0)), (0.8, (0, 4, 0)), (1.6, (0, -4, 0)))
    walk.rot("cape", (0, (10, 0, 0)), (0.8, (14, 0, 0)), (1.6, (10, 0, 0)))
    walk.rot("cape_low", (0, (8, 0, 0)), (0.8, (14, 0, 0)), (1.6, (8, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.4, (0, -1.2, 0)), (0.8, (0, 0, 0)), (1.2, (0, -1.2, 0)), (1.6, (0, 0, 0)))
    _actions(m)
    _emit_blades(m)
    return m


def blade_keys(a, keys, extra_l=None):
    """Sword-arm keyframes from (t, arm_x, forearm_x, blade_angle[, interp]) in absolute degrees.

    blade_angle is the blade direction in the side view, in the world: 0 = straight up, 90 = forward,
    180 = down, -90 = backward. The torso's pitch at each key is compensated (see _emit_blades), and the
    off-hand arm follows the right arm's raise so both hands share the grip."""
    a._blade = (keys, extra_l)


def _emit_blades(m):
    for a in m.anims.values():
        if not hasattr(a, "_blade"):
            continue
        keys, extra_l = a._blade
        arm, fore, sword, arm_l = [], [], [], []
        for k in keys:
            t, ax, fx, phi = k[:4]
            it = k[4] if len(k) > 4 else "smooth"
            pitch = a.sample(t).get("torso", {}).get("rotation", (0, 0, 0))[0] + 7  # 7 = torso rest lean
            sx = phi - ax - fx - pitch
            arm.append((t, (ax - ARM, 0, 0), it))
            fore.append((t, (fx - FORE, 0, 0), it))
            sword.append((t, (sx - SWORD, 0, 0), it))
            arm_l.append((t, (ax - ARM, 0, 0), it))
        a.rot("arm_r", *arm)
        a.rot("forearm_r", *fore)
        a.rot("sword", *sword)
        if extra_l is None:
            a.rot("arm_l", *arm_l)


REST = (ARM, FORE, ARM + FORE + SWORD + 7)


def _actions(m):
    R = REST
    # cleave: the greatsword swung up behind the crown with both hands (0.9 s), brought straight down
    a = m.anim("cleave", 1.6)
    blade_keys(a, [(0, *R), (0.75, -165, -45, -80), (0.9, -170, -50, -90), (1.0, -60, -15, 122, "linear"),
                   (1.25, -58, -15, 120), (1.6, *R)])
    a.rot("torso", (0, (0, 0, 0)), (0.75, (-14, 0, 0)), (0.9, (-16, 0, 0)), (1.0, (24, 0, 0), "linear"), (1.25, (22, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-12, 0, 0)), (1.0, (6, 0, 0)), (1.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.9, (0, 0, 2)), (1.0, (0, -2, -4), "linear"), (1.25, (0, -2, -4)), (1.6, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.9, (8, 0, 0)), (1.0, (-30, 0, 0), "linear"), (1.25, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.0, (25, 0, 0), "linear"), (1.25, (25, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.0, (18, 0, 0), "linear"), (1.25, (18, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.9, (8, 0, 0)), (1.05, (-12, 0, 0)), (1.3, (-18, 0, 0)), (1.6, (0, 0, 0)))

    # sweep: wound up with the whole body turned right (0.6 s), a flat, wide cut right to left
    a = m.anim("sweep", 1.4)
    blade_keys(a, [(0, *R), (0.55, -75, -10, 95), (0.95, -75, -10, 95), (1.4, *R)])
    a.rot("torso", (0, (0, 0, 0)), (0.55, (0, -55, 0)), (0.6, (0, -58, 0)), (0.8, (6, 60, 0), "linear"), (0.95, (6, 58, 0)), (1.4, (0, 0, 0)))
    a.rot("bone", (0, (0, 0, 0)), (0.6, (0, -20, 0)), (0.8, (0, 25, 0), "linear"), (0.95, (0, 25, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (0, 40, 0)), (0.8, (0, -30, 0)), (1.4, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.6, (0, 0, 15)), (0.85, (10, 0, -20)), (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, -1.5, 0)), (0.8, (0, -1.5, -2)), (1.4, (0, 0, 0)))

    # charge: sword drawn back to the hip, a crouch (0.8 s), then a running thrust held for 0.5 s
    a = m.anim("charge", 1.8)
    blade_keys(a, [(0, *R), (0.7, 15, -75, 92), (0.8, 18, -78, 92), (0.88, -85, -5, 92, "linear"),
                   (1.3, -85, -5, 95), (1.8, *R)])
    a.rot("torso", (0, (0, 0, 0)), (0.8, (10, -30, 0)), (0.88, (25, 10, 0), "linear"), (1.3, (25, 10, 0)), (1.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.8, (0, -3, 3)), (0.88, (0, -1, -6), "linear"), (1.3, (0, -1, -6)), (1.8, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (-25, 0, 0)), (0.88, (-40, 0, 0), "linear"), (1.3, (-40, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (0.88, (20, 0, 0)), (1.3, (20, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (25, 0, 0)), (0.88, (35, 0, 0), "linear"), (1.3, (35, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.8, (5, 0, 0)), (0.9, (40, 0, 0)), (1.3, (35, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("cape_low", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (1.3, (15, 0, 0)), (1.8, (0, 0, 0)))

    # slam: greatsword raised point-down over the head (1.1 s), plunged into the floor, then wrenched out
    a = m.anim("slam", 2.0)
    blade_keys(a, [(0, *R), (0.9, -165, -10, 178), (1.1, -168, -10, 180), (1.2, -75, -5, 180, "linear"),
                   (1.6, -75, -5, 180), (2.0, *R)])
    a.rot("torso", (0, (0, 0, 0)), (1.1, (-14, 0, 0)), (1.2, (28, 0, 0), "linear"), (1.6, (26, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.2, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (1.1, (0, 2, 0)), (1.2, (0, -5, -2), "linear"), (1.6, (0, -5, -2)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.2, (-55, 0, 0), "linear"), (1.6, (-55, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.2, (60, 0, 0), "linear"), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.2, (25, 0, 0), "linear"), (1.6, (25, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.2, (55, 0, 0), "linear"), (1.6, (55, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.1, (8, 0, 0)), (1.25, (-12, 0, 0)), (1.6, (-22, 0, 0)), (2.0, (0, 0, 0)))

    # rend: crouched with the blade trailing low behind (1.0 s), a rising cut that ends pointing at the sky
    a = m.anim("rend", 2.0)
    blade_keys(a, [(0, *R), (0.85, 35, -10, -150), (1.0, 38, -10, -155), (1.12, -165, -20, -15, "linear"),
                   (1.5, -165, -20, -15), (2.0, *R)])
    a.rot("torso", (0, (0, 0, 0)), (0.85, (14, -35, 0)), (1.0, (16, -38, 0)), (1.12, (-18, 25, 0), "linear"), (1.5, (-18, 25, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (10, 30, 0)), (1.12, (-25, -20, 0)), (1.5, (-25, -20, 0)), (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (1.0, (0, -4, 2)), (1.12, (0, 1, -3), "linear"), (1.5, (0, 1, -3)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.0, (30, 0, 0)), (1.12, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.0, (-40, 0, 0)), (1.12, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.0, (45, 0, 0)), (1.12, (15, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.0, (10, 0, 10)), (1.2, (35, 0, -10)), (2.0, (0, 0, 0)))

    # summon: the sword planted point-down before him, both hands on the pommel, the crown lifted to call
    a = m.anim("summon", 2.0)
    blade_keys(a, [(0, *R), (0.6, -70, -20, 178), (1.0, -62, -18, 180), (1.6, -62, -18, 180), (2.0, *R)])
    a.rot("head", (0, (0, 0, 0)), (0.6, (-10, 0, 0)), (1.0, (-35, 0, 0)), (1.6, (-35, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.6, (6, 0, 0)), (1.0, (-10, 0, 0)), (1.6, (-10, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.3, (15, 0, 0)), (1.6, (5, 0, 0)), (2.0, (0, 0, 0)))

    # leap: deep crouch (0.7 s), launch with the sword hauled overhead, smash down on landing (1.3 s)
    a = m.anim("leap", 1.8)
    blade_keys(a, [(0, *R), (0.6, -20, -60, 150), (0.7, -25, -60, 150), (0.95, -170, -45, -90),
                   (1.2, -172, -48, -95), (1.3, -60, -15, 122, "linear"), (1.45, -58, -15, 120), (1.8, *R)])
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, -5, 0)), (0.7, (0, -5, 0)), (0.85, (0, 4, 0), "linear"), (1.2, (0, 3, 0)),
          (1.3, (0, -3, 0), "linear"), (1.45, (0, -3, 0)), (1.8, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.7, (20, 0, 0)), (0.95, (-15, 0, 0)), (1.2, (-18, 0, 0)), (1.3, (26, 0, 0), "linear"),
          (1.45, (24, 0, 0)), (1.8, (0, 0, 0)))
    for leg, shin in (("leg_r", "shin_r"), ("leg_l", "shin_l")):
        a.rot(leg, (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (0.7, (-40, 0, 0)), (0.85, (10, 0, 0)), (1.2, (-30, 0, 0)), (1.3, (-35, 0, 0)),
              (1.45, (-35, 0, 0)), (1.8, (0, 0, 0)))
        a.rot(shin, (0, (0, 0, 0)), (0.6, (60, 0, 0)), (0.7, (60, 0, 0)), (0.85, (5, 0, 0)), (1.2, (50, 0, 0)), (1.3, (55, 0, 0)),
              (1.45, (55, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.7, (5, 0, 0)), (0.95, (45, 0, 0)), (1.2, (30, 0, 0)), (1.35, (-5, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("cape_low", (0, (0, 0, 0)), (0.95, (25, 0, 0)), (1.35, (-10, 0, 0)), (1.8, (0, 0, 0)))

    # spin: blade swung out to the side (0.6 s), two full turns (0.6-1.4 s), stumble out of it
    a = m.anim("spin", 1.8)
    blade_keys(a, [(0, *R), (0.5, -85, -5, 92), (1.4, -85, -5, 92), (1.8, *R)])
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (0, 0, 55)), (1.4, (0, 0, 55)), (1.8, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (0, -40, 0)), (0.6, (0, -45, 0)), (0.7, (0, 0, 0)), (1.4, (0, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("bone", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.601, (0, 720, 0), "linear"), (1.4, (0, 0, 0), "linear"), (1.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, -2, 0)), (1.4, (0, -2, 0)), (1.8, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (0.8, (60, 0, 0)), (1.4, (60, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("cape_low", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (1.4, (20, 0, 0)), (1.8, (0, 0, 0)))

    # roar: phase two; the sword raised to the sky, the off hand clenched, crown thrown back
    a = m.anim("roar", 2.4)
    blade_keys(a, [(0, *R), (0.5, -170, -10, -5), (1.9, -170, -10, -5), (2.4, *R)], extra_l=True)
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-10, -24, -50)), (1.9, (-10, -24, -50)), (2.4, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.9, (-40, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-18, 0, 0)), (1.9, (-18, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.5, (25, 0, 0)), (1.2, (35, 0, 5)), (1.9, (25, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("cape_low", (0, (0, 0, 0)), (0.5, (15, 0, 0)), (1.2, (25, 0, 0)), (1.9, (15, 0, 0)), (2.4, (0, 0, 0)))

    # stagger: posture broken, he drops to one knee leaning on the planted sword
    a = m.anim("stagger", 2.0)
    blade_keys(a, [(0, *R), (0.3, -55, -25, 128), (1.6, -55, -25, 128), (2.0, *R)])
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -9, 2)), (1.6, (0, -9, 2)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-75, 0, 0)), (1.6, (-75, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.6, (80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (1.6, (25, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (65, 0, 0)), (1.6, (65, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.3, (22, 0, 0)), (1.6, (22, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.6, (20, 0, 0)), (2.0, (0, 0, 0)))
