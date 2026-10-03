"""Skeleton Knight (Chevalier squelette): a tall, gaunt skeleton in rusted half-plate and a kettle helm, a
tattered crimson tabard, a kite shield on the left arm and a longsword in the right hand; its eye sockets
burn with a cold blue light.

Also hosts the paint helpers shared by the other bone creatures of agent_g1 (crypt_crawler, grave_knight,
bone_matriarch import them from here)."""
from ..models import Model
from ..texgen import mix, mul

BONE = (222, 212, 184)
BONE_D = (160, 148, 118)
BONE_DD = (92, 82, 64)
STEEL = (118, 118, 122)
STEEL_D = (64, 64, 70)
RUST = (150, 82, 42)
RUST_D = (96, 50, 28)
RED = (128, 30, 34)
RED_D = (78, 18, 24)
GOLD = (220, 176, 70)
GOLD_D = (150, 104, 38)
EYE = (130, 230, 255)
SOCKET = (18, 14, 16)


def H(x, y, seed):
    """Deterministic hash in 0..65535."""
    return ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791) ^ ((x + 3 * y) * 2654435761)) & 0xFFFF


def bone(seed=0, base=BONE, dark=BONE_D, cracks=True):
    """Weathered bone: soft grain, darker knobbly ends, a few hairline cracks."""
    def f(face, x, y, w, h):
        r = H(x, y, seed)
        c = mul(base, 1 + ((r % 100) / 100 - 0.5) * 0.10)
        if face in ("front", "back", "left", "right") and h > 3 and (y == 0 or y == h - 1):
            c = mix(c, dark, 0.35)
        if cracks and (x * 2 + y + seed) % 9 == 0 and r % 3 == 0:
            c = mix(c, BONE_DD, 0.6)
        if face == "bottom":
            c = mix(c, dark, 0.3)
        return c
    return f


def ribs(seed=0, gap=SOCKET):
    """Ribcage: horizontal bone bars with dark gaps, a spine in the middle of the back."""
    b = bone(seed, cracks=False)

    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return b(face, x, y, w, h)
        if face == "back" and abs(x - (w - 1) / 2) < 1:
            return mix(BONE, BONE_D, 0.3)
        if y % 2 == 1:
            return gap
        if face == "front" and abs(x - (w - 1) / 2) < 0.6:
            return BONE_D  # sternum
        return b(face, x, y, w, h)
    return f


def rust_plate(seed=0, base=STEEL, rim=STEEL_D, rust=RUST, amount=0.32, rivets=True):
    """Rusted armour plate: dark rim with rivets, steel with rust blotches and run-off streaks."""
    def f(face, x, y, w, h):
        edge = x == 0 or y == 0 or x == w - 1 or y == h - 1
        if rim is not None and edge and w > 2 and h > 2:
            if rivets and y == 0 and x % 3 == 1 and face != "bottom":
                return mix(base, (230, 220, 200), 0.35)
            return rim
        fine = (H(x, y, seed + 7) % 100) / 100
        coarse = (H(x // 3, y // 3, seed) % 100) / 100
        c = mul(base, 1 + (fine - 0.5) * 0.14)
        if face == "top":
            c = mul(c, 1.08)
        if coarse < amount:
            c = mix(c, rust, 0.45 + 0.35 * fine)
        elif face in ("front", "back", "left", "right") and H(x, 1, seed) % 6 == 0 and y > 1:
            c = mix(c, RUST_D, 0.35 + 0.02 * y)  # rust run-off streak
        return c
    return f


def cloth(seed=0, base=RED, dark=RED_D, trim=GOLD_D, ragged=3, emblem=None):
    """Tattered cloth: woven threads, folds, a trim band on top and a torn, transparent hem."""
    def f(face, x, y, w, h):
        if ragged and face in ("front", "back", "left", "right") and h > 4:
            if y >= h - 1 - (H(x, 0, seed) % ragged):
                return None
            if H(x, y, seed + 3) % 29 == 0 and y > 2:
                return None  # moth holes
        if trim is not None and y == 0 and face in ("front", "back"):
            return trim
        c = base if x % 2 else mul(base, 0.92)
        if (x + seed) % 4 == 0:
            c = mix(c, dark, 0.55)  # fold shadow
        if emblem is not None:
            e = emblem(face, x, y, w, h)
            if e is not None:
                c = e
        if face in ("front", "back") and y > h * 0.6:
            c = mix(c, (60, 48, 40), 0.25)  # dirt toward the hem
        return c
    return f


def skull_face(seed=0, eye=EYE, base=BONE, wide=False):
    """Front of a skull: two deep sockets with a glowing pupil, a nose cavity, cheek shadows."""
    b = bone(seed, base, cracks=False)

    def sockets(w):
        c = (w - 1) / 2
        off = 2 if w <= 7 else 2.5 if w <= 9 else 3
        return {int(c - off + 0.5), int(c - off - 0.5) + 0, int(c + off - 0.5), int(c + off + 0.5)}

    def f(face, x, y, w, h):
        eyes_y = (h * 3) // 7
        xs = sockets(w)
        if y in (eyes_y, eyes_y + 1) and x in xs:
            return eye if y == eyes_y else SOCKET
        if y == eyes_y - 1 and x in xs:
            return mix(base, BONE_DD, 0.55)  # brow ridge shadow
        if y == eyes_y + 2 and abs(x - (w - 1) / 2) < 0.6:
            return SOCKET  # nose cavity
        if y == h - 1 and x % 2 == 0:
            return mix(base, BONE_D, 0.5)  # upper teeth
        return b(face, x, y, w, h)

    def g(face, x, y, w, h):
        if y == (h * 3) // 7 and x in sockets(w):
            return eye
        return None
    return f, g


def teeth(base=BONE):
    def f(face, x, y, w, h):
        if face == "front" and y == 0:
            return base if x % 2 == 0 else SOCKET
        return bone(5, base, cracks=False)(face, x, y, w, h)
    return f


def build():
    m = Model("skeleton_knight", seed=21, shadow=0.55, walk_speed=1.1, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -14, 0))
    m.part("torso", "hips", pivot=(0, -2, 0), rot=(6, 0, 0))
    m.part("head", "torso", pivot=(0, -13, -0.5), rot=(-6, 0, 0))
    m.part("jaw", "head", pivot=(0, -1, -1))
    m.part("tabard", "torso", pivot=(0, -6, -3.2), rot=(-6, 0, 0))
    m.part("tabard_back", "torso", pivot=(0, -6, 3.2), rot=(-6, 0, 0))
    m.part("arm_r", "torso", pivot=(-5.5, -11.5, 0), rot=(-8, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(0, 7, 0), rot=(-30, 0, 0))
    m.part("sword", "forearm_r", pivot=(0, 7, -0.5), rot=(70, 0, 25))
    m.part("arm_l", "torso", pivot=(5.5, -11.5, 0), rot=(-10, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0, 7, 0), rot=(-60, 0, 0))
    m.part("shield", "forearm_l", pivot=(0, 3, -2.5), rot=(60, -10, 0))
    m.part("leg_r", "bone", pivot=(-2.2, -14, 0))
    m.part("shin_r", "leg_r", pivot=(0, 7, 0))
    m.part("leg_l", "bone", pivot=(2.2, -14, 0))
    m.part("shin_l", "leg_l", pivot=(0, 7, 0))

    # ------------------------------------------------------------------ body
    m.box("hips", -3, -2, -2, 6, 3, 4, bone(1))                                   # pelvis
    m.box("hips", -4, -1, -3, 8, 3, 6, rust_plate(2, amount=0.4), grow=0.1)       # faulds (armoured skirt)
    m.box("torso", -1, -6, 0, 2, 6, 2, bone(3))                                   # lumbar spine
    m.box("torso", -3.5, -8, -2.5, 7, 3, 5, ribs(4))                              # lower ribs, bare
    # breastplate: dented, rusted, with a raised ridge down the middle
    m.box("torso", -4.5, -14, -3, 9, 7, 6, {"front": rust_plate(5, amount=0.36), "*": rust_plate(6, amount=0.3)})
    m.box("torso", -0.5, -13, -3.6, 1, 6, 1, rust_plate(7, STEEL, None, amount=0.2))
    m.box("torso", -4.5, -15, -2.5, 9, 1, 5, bone(8))                             # collarbones
    m.box("torso", -1, -16, -1, 2, 2, 2, bone(9))                                 # neck
    # tabard: crimson with a pale bone chevron, torn hem; front and back panels
    chev = lambda face, x, y, w, h: (200, 190, 160) if face == "front" and abs(abs(x - (w - 1) / 2) - (y - 2) * 0.7) < 0.7 and 2 <= y <= 6 else None  # noqa: E731
    m.box("tabard", -3, 0, -0.5, 6, 13, 1, {"front": cloth(1, emblem=chev), "back": cloth(2), "*": RED_D})
    m.box("tabard_back", -3, 0, -0.5, 6, 12, 1, {"back": cloth(3), "front": cloth(4), "*": RED_D})

    # head: skull, a hinged jaw and a dented kettle helm with a wide brim
    face, glow = skull_face(10)
    m.box("head", -3, -7, -3.5, 6, 6, 6, {"front": face, "*": bone(11)}, glow={"front": glow})
    m.box("jaw", -2.5, 0, -2.5, 5, 2, 4, teeth())
    m.box("head", -3.5, -8.5, -4, 7, 3, 7, rust_plate(12, amount=0.45))
    m.box("head", -5, -6, -5.5, 10, 1, 10, rust_plate(13, amount=0.35, rivets=False))
    m.box("head", -0.5, -9.5, -1, 1, 1, 3, rust_plate(14, STEEL, None, amount=0.5))  # crest ridge

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -2.5, -2.5, -2.5, 5, 4, 5, rust_plate(20 + sx, amount=0.4))   # pauldron
        m.box(arm, -2.6 if sx < 0 else -2.4, 1.5, -2.6, 5, 1, 5, rust_plate(22 + sx, STEEL_D, None, amount=0.5))
        m.box(arm, -1, 0, -1, 2, 7, 2, bone(23 + sx))                             # humerus
        m.box(fore, -0.9, 0, -0.9, 2, 7, 2, bone(24 + sx))                        # radius/ulna
        m.box(fore, -1.5, 2, -1.5, 3, 4, 3, rust_plate(25 + sx, amount=0.35))     # vambrace
        m.box(fore, -1, 6.5, -1.2, 2, 2, 2, bone(26 + sx, BONE_D))                # bony fist

    # longsword: leather grip, a curved crossguard, a notched and rust-pitted blade
    blade = lambda face, x, y, w, h: (mix(STEEL, (210, 210, 215), 0.55) if x == 0 or face in ("left", "right") else  # noqa: E731
                                      RUST if H(x, y, 31) % 7 == 0 else mix(STEEL, (180, 180, 186), 0.3))
    m.box("sword", -0.5, -1, -0.5, 1, 4, 1, (70, 46, 32))                         # grip
    m.box("sword", -0.5, 3, -0.5, 1, 1, 1, GOLD_D)                                # pommel
    m.box("sword", -2.5, -2, -1, 5, 1, 2, rust_plate(32, STEEL_D, None, amount=0.5))
    m.box("sword", -1, -17, -0.5, 2, 15, 1, blade)
    m.box("sword", -0.5, -18, -0.5, 1, 1, 1, mix(STEEL, (210, 210, 215), 0.4))    # tip

    # kite shield: wide top, tapering point, faded crimson with a bone chevron and a rusted rim
    def field(face, x, y, w, h):
        if face != "front":
            return (78, 56, 40) if face == "back" else STEEL_D
        if x == 0 or x == w - 1:
            return rust_plate(40, STEEL_D, None, amount=0.6)(face, x, y, w, h)
        if abs(abs(x - (w - 1) / 2) - (y * 0.55)) < 0.75 and y < 7:
            return (206, 196, 168)
        c = RED if (x + y) % 5 else RED_D
        if H(x, y, 41) % 13 == 0:
            c = (70, 54, 44)  # chipped paint, bare wood
        return c
    m.box("shield", -4, -5, -1, 8, 6, 1, {"front": field, "*": field})
    m.box("shield", -3, 1, -1, 6, 2, 1, {"front": lambda f_, x, y, w, h: field(f_, x + 1, y + 6, w + 2, h), "*": field})
    m.box("shield", -2, 3, -1, 4, 2, 1, {"front": lambda f_, x, y, w, h: field(f_, x + 2, y + 8, w + 4, h), "*": field})
    m.box("shield", -1, 5, -1, 2, 1, 1, rust_plate(42, STEEL_D, None, amount=0.6))
    m.box("shield", -4.5, -5.5, -1.2, 9, 1, 1, rust_plate(43, STEEL, None, amount=0.5))  # rim on top
    m.box("shield", -1, -2, -1.7, 2, 2, 1, rust_plate(44, STEEL, None, amount=0.4))      # boss

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -1, 0, -1, 2, 7, 2, bone(50 + sx))                              # femur
        m.box(leg, -1.5, 0, -2, 3, 4, 3, rust_plate(51 + sx, amount=0.4))          # cuisse
        m.box(leg, -1.2, 5.5, -1.8, 2, 2, 2, rust_plate(52 + sx, STEEL, None, amount=0.3))  # knee cop
        m.box(shin, -0.8, 0, -0.8, 2, 7, 2, bone(53 + sx))                         # tibia
        m.box(shin, -1.5, 1, -1.6, 3, 4, 2, rust_plate(54 + sx, amount=0.45))      # greave (front half)
        m.box(shin, -1.5, 5, -3, 3, 2, 4, rust_plate(55 + sx, STEEL_D, (40, 40, 44), amount=0.5))  # sabaton

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.4)
    idle.rot("torso", (0, (0, 0, 0)), (1.2, (2.5, 2, 0)), (2.4, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (-3, 6, 2)), (1.6, (2, -4, 0)), (2.4, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (0.3, (14, 0, 0)), (0.5, (0, 0, 0)), (0.7, (10, 0, 0)), (0.9, (0, 0, 0)), (2.4, (0, 0, 0)))
    idle.rot("tabard", (0, (0, 0, 0)), (1.2, (-5, 0, 2)), (2.4, (0, 0, 0)))
    idle.rot("tabard_back", (0, (0, 0, 0)), (1.2, (5, 0, -2)), (2.4, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.2, (-3, 0, 2)), (2.4, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    for leg, sgn in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (28 * sgn, 0, 0)), (0.6, (-28 * sgn, 0, 0)), (1.2, (28 * sgn, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.3, (35, 0, 0)), (0.6, (0, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.9, (35, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("arm_r", (0, (-20, 0, 0)), (0.6, (14, 0, 0)), (1.2, (-20, 0, 0)))
    walk.rot("arm_l", (0, (6, 0, 0)), (0.6, (-6, 0, 0)), (1.2, (6, 0, 0)))
    walk.rot("torso", (0, (0, -5, 0)), (0.6, (0, 5, 0)), (1.2, (0, -5, 0)))
    walk.rot("tabard", (0, (-14, 0, 0)), (0.6, (-6, 0, 0)), (1.2, (-14, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.3, (0, 0.8, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.8, 0)), (1.2, (0, 0, 0)))

    # slash: sword hauled up over the right shoulder (0.6 s telegraph), a diagonal cut down, recover
    a = m.anim("slash", 1.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-160, 20, -20)), (0.6, (-165, 25, -25)), (0.72, (-30, -20, 10), "linear"),
          (0.9, (-25, -20, 10)), (1.2, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (0.6, (-45, 0, 0)), (0.72, (20, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-8, 25, 0)), (0.6, (-10, 28, 0)), (0.72, (14, -24, 0), "linear"),
          (0.9, (12, -20, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-6, -15, 0)), (0.72, (6, 15, 0)), (1.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.55, (25, 0, 0)), (0.75, (0, 0, 0)), (1.2, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, 0, 1.5)), (0.72, (0, 0, -3), "linear"), (0.9, (0, 0, -3)), (1.2, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (12, 0, 0)), (0.72, (-25, 0, 0), "linear"), (0.9, (-25, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (-10, 0, 0)), (0.72, (18, 0, 0), "linear"), (1.2, (0, 0, 0)))

    # guard: shield up in front of the chest, crouched behind it, sword ready; lowered at the end
    a = m.anim("guard", 2.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (-40, 35, 0)), (1.8, (-40, 35, 0)), (2.0, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.2, (-10, 0, 0)), (1.8, (-10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shield", (0, (0, 0, 0)), (0.2, (60, 0, 0)), (1.8, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-35, 0, 15)), (1.8, (-35, 0, 15)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.2, (10, -8, 0)), (1.0, (12, -8, 0)), (1.8, (10, -8, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.2, (-8, 8, 0)), (1.8, (-8, 8, 0)), (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.2, (0, -1.5, 0)), (1.8, (0, -1.5, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.2, (20, 0, 0)), (1.8, (20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.2, (25, 0, 0)), (1.8, (25, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.2, (-30, 0, 0)), (1.8, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.2, (30, 0, 0)), (1.8, (30, 0, 0)), (2.0, (0, 0, 0)))

    # bash: shield drawn back with a twist (0.45 s), rammed forward, recover
    a = m.anim("bash", 1.0)
    a.rot("torso", (0, (0, 0, 0)), (0.4, (-4, 30, 0)), (0.45, (-4, 32, 0)), (0.55, (14, -25, 0), "linear"),
          (0.7, (12, -22, 0)), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-30, 30, 0)), (0.45, (-30, 32, 0)), (0.55, (-80, -10, 0), "linear"),
          (0.7, (-78, -10, 0)), (1.0, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.45, (-40, 0, 0)), (0.55, (0, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("shield", (0, (0, 0, 0)), (0.45, (0, 0, 0)), (0.55, (-50, 20, 0), "linear"), (0.7, (-50, 20, 0)), (1.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.45, (0, 0, 2)), (0.55, (0, 0, -5), "linear"), (0.7, (0, 0, -5)), (1.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.45, (10, 0, 0)), (0.55, (-30, 0, 0), "linear"), (0.7, (-30, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.45, (-10, 0, 0)), (0.55, (20, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.45, (20, 0, 0)), (0.6, (0, 0, 0)), (1.0, (0, 0, 0)))
    return m
