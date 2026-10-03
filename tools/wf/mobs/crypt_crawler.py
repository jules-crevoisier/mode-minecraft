"""Crypt Crawler (Rampant des cryptes): a low, wide horror of fused bones. A human skull grown into a
spider's head with two hooked mandibles and four sickly green eyes, a horizontal ribcage for a body with a
ridge of vertebrae, a knotted bone abdomen, and eight long jointed bone legs. It climbs walls and pounces."""
from ..models import Model
from ..texgen import mix, mul
from .skeleton_knight import BONE, BONE_D, BONE_DD, SOCKET, H, bone

GLOW = (196, 255, 110)
MOSS = (96, 116, 70)
GRIME = (84, 74, 58)


def old_bone(seed=0, base=BONE, dark=BONE_D):
    """Grave-stained bone: bone with moss and grime blotches gathered on the lower half."""
    b = bone(seed, base, dark)

    def f(face, x, y, w, h):
        c = b(face, x, y, w, h)
        r = H(x // 2, y // 2, seed + 11) % 100
        low = face in ("front", "back", "left", "right") and y > h / 2
        if face == "bottom" or (low and r < 35):
            c = mix(c, GRIME, 0.45)
        elif face == "top" and r < 12:
            c = mix(c, MOSS, 0.5)
        return c
    return f


def shin(seed=0):
    """Leg bone darkening toward the claw, with a band of dried sinew under the knee."""
    b = old_bone(seed)

    def f(face, x, y, w, h):
        c = b(face, x, y, w, h)
        if face in ("front", "back", "left", "right"):
            if y in (1, 2):
                return mix((110, 62, 52), GRIME, 0.3 * (y - 1))
            c = mix(c, BONE_DD, min(0.7, max(0.0, (y - h * 0.45) / h)))
        return c
    return f


def ribcage(seed=0):
    """Horizontal ribcage: ribs run across the body (bands along z), dark gaps, a spine on top."""
    b = old_bone(seed)

    def f(face, x, y, w, h):
        if face in ("front", "back"):
            if face == "front":
                return mix(BONE_D, GRIME, 0.3) if (x + y) % 3 else BONE_DD
            return b(face, x, y, w, h)
        if face == "top":
            if abs(x - (w - 1) / 2) < 1:
                return mix(BONE, BONE_D, 0.25)  # spine
            return b(face, x, y, w, h) if y % 3 != 2 else SOCKET
        if face == "bottom":
            return SOCKET if y % 3 == 2 else mix(BONE_D, GRIME, 0.4)
        # sides: x runs along the body
        if x % 3 == 2:
            return SOCKET
        if y == h - 1:
            return mix(BONE_D, GRIME, 0.5)
        return b(face, x, y, w, h)
    return f


def build():
    m = Model("crypt_crawler", seed=33, shadow=0.9, walk_speed=1.6, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -8, 0))
    m.part("abdomen", "body", pivot=(0, -1, 6), rot=(-12, 0, 0))
    m.part("head", "body", pivot=(0, -1, -6))
    m.part("mand_r", "head", pivot=(-3, 0.5, -5), rot=(0, -15, 0))
    m.part("mand_l", "head", pivot=(3, 0.5, -5), rot=(0, 15, 0))

    # ribcage body with a ridge of vertebral spikes
    m.box("body", -5, -4, -6, 10, 6, 12, ribcage(1))
    for i, z in enumerate((-5, -2, 1, 4)):
        m.box("body", -0.5, -6 - (i % 2), z, 1, 2 + (i % 2), 2, old_bone(2 + i))
    m.box("body", -3, 2, -4, 6, 1, 8, mix(BONE_D, GRIME, 0.4))  # sternum plate underneath

    # abdomen: a knot of fused pelvis bones and a short segmented tail
    m.box("abdomen", -4, -3, 0, 8, 6, 7, {"back": lambda f_, x, y, w, h: SOCKET if (x in (2, 5) and 2 <= y <= 3)
                                         else old_bone(7)(f_, x, y, w, h), "*": old_bone(7)})
    m.box("abdomen", -2.5, -2, 7, 5, 4, 3, old_bone(8))
    m.box("abdomen", -1.5, -1, 10, 3, 3, 3, old_bone(9))
    m.box("abdomen", -0.5, -0.5, 13, 1, 2, 3, old_bone(10, BONE_D))

    # skull head: brow over four sockets (two great, two small), cheekbones, gaping nasal hole
    def face(f_, x, y, w, h):
        if y == 2 and x in (1, 2, 5, 6):
            return GLOW
        if y == 3 and x in (1, 2, 5, 6):
            return SOCKET
        if y == 1 and x in (0, 7):
            return GLOW
        if y == 4 and x in (3, 4):
            return SOCKET
        if y == 5:
            return BONE if x % 2 == 0 else SOCKET
        if y == 0:
            return mix(BONE, BONE_D, 0.4)
        return old_bone(12)(f_, x, y, w, h)

    def face_glow(f_, x, y, w, h):
        if (y == 2 and x in (1, 2, 5, 6)) or (y == 1 and x in (0, 7)):
            return GLOW
        return None
    m.box("head", -4, -4, -6, 8, 6, 7, {"front": face, "*": old_bone(13)}, glow={"front": face_glow})
    m.box("head", -4.5, -5, -6.5, 9, 2, 4, old_bone(14, BONE_D))   # heavy brow ridge
    m.box("head", -3, 2, -5, 6, 1, 5, {"front": lambda f_, x, y, w, h: BONE if x % 2 == 0 else SOCKET,
                                        "*": old_bone(15)})            # lower teeth row
    # mandibles: hooked bone pincers curving inward
    for side, sx in (("r", -1), ("l", 1)):
        part = f"mand_{side}"
        m.box(part, -1, -1, -5, 2, 2, 6, old_bone(16 + sx))
        m.box(part, -1 - sx * 1.5, -1, -7, 2, 2, 2, old_bone(17 + sx, BONE_D))
        m.box(part, -0.5 - sx * 2.5, -0.5, -8, 1, 1, 2, BONE_DD)  # hooked tip

    # eight legs, four a side, splayed fore and aft
    for side, sx in (("r", -1), ("l", 1)):
        for i, (z, yaw) in enumerate(((-4.5, 38), (-1.5, 13), (1.5, -12), (4.5, -36))):
            leg = f"leg_{side}{i}"
            foot = f"foot_{side}{i}"
            m.part(leg, "body", pivot=(4.5 * sx, -1, z), rot=(0, yaw * sx, -38 * sx))
            m.part(foot, leg, pivot=(9 * sx, 0, 0), rot=(0, 0, 24 * sx))
            m.box(leg, 0 if sx > 0 else -9, -1, -1, 9, 2, 2, old_bone(40 + i * 2 + (sx > 0)))
            m.box(leg, (7 if sx > 0 else -9), -1.5, -1.5, 2, 3, 3, old_bone(60 + i, BONE_D))   # knee knob
            m.box(foot, -1, 0, -1, 2, 10, 2, shin(50 + i * 2 + (sx > 0)))
            m.box(foot, -0.5, 10, -0.5, 1, 4, 1, mix(BONE_DD, GRIME, 0.3))                     # claw tip

    # ------------------------------------------------------------------ animations
    legs = [(f"leg_{s}{i}", f"foot_{s}{i}", sx) for s, sx in (("r", -1), ("l", 1)) for i in range(4)]

    idle = m.anim("idle", 2.0)
    idle.pos("body", (0, (0, 0, 0)), (1.0, (0, 0.6, 0)), (2.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (4, -6, 3)), (1.4, (-3, 6, -2)), (2.0, (0, 0, 0)))
    idle.rot("mand_r", (0, (0, 0, 0)), (0.2, (0, -18, 0)), (0.4, (0, 0, 0)), (0.6, (0, -14, 0)), (0.8, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("mand_l", (0, (0, 0, 0)), (0.2, (0, 18, 0)), (0.4, (0, 0, 0)), (0.6, (0, 14, 0)), (0.8, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("abdomen", (0, (0, 0, 0)), (1.0, (-5, 4, 0)), (2.0, (0, 0, 0)))

    # walk: alternating tetrapod gait (L0 R1 L2 R3 against R0 L1 R2 L3), legs swing fore/aft and lift
    walk = m.anim("walk", 0.8)
    for leg, foot, sx in legs:
        i = int(leg[-1])
        phase = (i + (0 if sx > 0 else 1)) % 2
        sw = 16 * (1 if phase == 0 else -1)
        lift = -14 * sx
        if phase == 0:
            walk.rot(leg, (0, (0, sw * sx, 0)), (0.2, (0, 0, lift)), (0.4, (0, -sw * sx, 0)), (0.8, (0, sw * sx, 0)))
        else:
            walk.rot(leg, (0, (0, sw * sx, 0)), (0.4, (0, -sw * sx, 0)), (0.6, (0, 0, lift)), (0.8, (0, sw * sx, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.2, (0, 0.6, 0)), (0.4, (0, 0, 0)), (0.6, (0, 0.6, 0)), (0.8, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, -2)), (0.4, (0, 0, 2)), (0.8, (0, 0, -2)))
    walk.rot("abdomen", (0, (0, 6, 0)), (0.4, (0, -6, 0)), (0.8, (0, 6, 0)))

    # bite: rear back with mandibles spread (0.3 s), snap forward, recover
    a = m.anim("bite", 0.8)
    a.rot("head", (0, (0, 0, 0)), (0.25, (-28, 0, 0)), (0.3, (-30, 0, 0)), (0.38, (18, 0, 0), "linear"), (0.5, (14, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (-10, 0, 0)), (0.38, (6, 0, 0), "linear"), (0.8, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, 1, 2)), (0.38, (0, -0.5, -3), "linear"), (0.5, (0, -0.5, -3)), (0.8, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.3, (0, -45, 0)), (0.38, (0, 20, 0), "linear"), (0.5, (0, 15, 0)), (0.8, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.3, (0, 45, 0)), (0.38, (0, -20, 0), "linear"), (0.5, (0, -15, 0)), (0.8, (0, 0, 0)))
    for leg, foot, sx in legs:
        if leg.endswith("0"):
            a.rot(leg, (0, (0, 0, 0)), (0.3, (0, 0, -25 * sx)), (0.38, (0, 10 * sx, 5 * sx), "linear"), (0.8, (0, 0, 0)))

    # pounce: crouch low (0.4 s), spring with the front legs flung up and the mandibles open, land
    a = m.anim("pounce", 1.2)
    a.pos("bone", (0, (0, 0, 0)), (0.35, (0, -3, 2)), (0.4, (0, -3, 2)), (0.5, (0, 3, -4), "linear"), (0.85, (0, 2, -4)),
          (0.95, (0, -1.5, -2)), (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (8, 0, 0)), (0.5, (-22, 0, 0), "linear"), (0.85, (-8, 0, 0)), (0.95, (6, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (12, 0, 0)), (0.5, (-15, 0, 0), "linear"), (0.85, (-10, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("abdomen", (0, (0, 0, 0)), (0.4, (-10, 0, 0)), (0.5, (20, 0, 0), "linear"), (0.95, (0, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.4, (0, -40, 0)), (0.85, (0, -40, 0)), (0.95, (0, 15, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.4, (0, 40, 0)), (0.85, (0, 40, 0)), (0.95, (0, -15, 0), "linear"), (1.2, (0, 0, 0)))
    for leg, foot, sx in legs:
        i = int(leg[-1])
        if i < 2:   # front legs reach up and forward
            a.rot(leg, (0, (0, 0, 0)), (0.4, (0, 0, 14 * sx)), (0.5, (0, 25 * sx, -45 * sx), "linear"), (0.85, (0, 25 * sx, -40 * sx)),
                  (0.95, (0, 0, 10 * sx)), (1.2, (0, 0, 0)))
            a.rot(foot, (0, (0, 0, 0)), (0.5, (0, 0, -30 * sx), "linear"), (0.85, (0, 0, -25 * sx)), (1.2, (0, 0, 0)))
        else:       # hind legs push back
            a.rot(leg, (0, (0, 0, 0)), (0.4, (0, 0, 18 * sx)), (0.5, (0, -30 * sx, -5 * sx), "linear"), (0.85, (0, -25 * sx, -10 * sx)),
                  (0.95, (0, 0, 8 * sx)), (1.2, (0, 0, 0)))
    return m
