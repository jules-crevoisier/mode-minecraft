"""The Bone Matriarch (La Matriarche d'os): a giant scorpion-spider queen of sand-bleached bone, about three
blocks wide. A great human skull wearing a striped gold-and-lapis royal headdress with a cobra crest, two
crushing pincers, six long jointed legs, a carapace inlaid with lapis and gold, and a segmented bone tail
curled high over her back, ending in a gilded sting that glows."""
from ..models import Model
from ..texgen import mix, mul
from .skeleton_knight import SOCKET, H

SAND = (226, 204, 156)
SAND_D = (172, 142, 98)
SAND_DD = (110, 86, 56)
LAPIS = (40, 74, 172)
LAPIS_D = (24, 42, 108)
GOLD = (234, 188, 72)
GOLD_L = (255, 226, 132)
GOLD_D = (156, 108, 38)
AMBER = (255, 196, 84)
VENOM = (170, 255, 120)


def sbone(seed=0, base=SAND, dark=SAND_D):
    """Sun-bleached bone: warm sand tones, grain lines, darker ends and undersides, sand caught in cracks."""
    def f(face, x, y, w, h):
        r = H(x, y, seed)
        c = mul(base, 1 + ((r % 100) / 100 - 0.5) * 0.10)
        if face == "bottom":
            return mix(c, dark, 0.45)
        if face in ("front", "back", "left", "right") and h > 3 and y >= h - 1:
            c = mix(c, dark, 0.4)
        if (x * 3 + y * 2 + seed) % 13 == 0 and r % 2 == 0:
            c = mix(c, SAND_DD, 0.55)  # crack
        if face == "top":
            c = mul(c, 1.04)
        return c
    return f


def inlaid(seed=0, rim=GOLD_D, pattern="bands"):
    """Bone plate inlaid with lapis and gold: a gold rim and Egyptian-style bands or chevrons."""
    b = sbone(seed)

    def f(face, x, y, w, h):
        edge = x == 0 or y == 0 or x == w - 1 or y == h - 1
        if edge and w > 3 and h > 3 and face != "bottom":
            if face == "top" or y == 0:
                return GOLD if H(x, y, seed) % 7 else GOLD_L
            return rim if y == h - 1 else GOLD
        if face == "bottom":
            return b(face, x, y, w, h)
        if pattern == "bands":
            k = y % 6
            if k == 2:
                return LAPIS
            if k == 3:
                return GOLD if x % 3 else LAPIS_D
        elif pattern == "chevron":
            cx = (w - 1) / 2
            k = (y + int(abs(x - cx))) % 7
            if k == 0:
                return LAPIS
            if k == 1:
                return GOLD
        return b(face, x, y, w, h)
    return f


def nemes(seed=0):
    """Royal headdress cloth: horizontal gold and lapis stripes."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        c = GOLD if (y // 1) % 3 != 2 else LAPIS
        if face == "top":
            c = GOLD if x % 3 != 2 else LAPIS
        if H(x, y, seed) % 17 == 0:
            c = mix(c, GOLD_L, 0.5)
        return c
    return f


def build():
    m = Model("bone_matriarch", seed=55, shadow=2.0, walk_speed=1.0, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -14, 0))
    m.part("head", "body", pivot=(0, -3, -8))
    m.part("jaw", "head", pivot=(0, 0, -3))
    # tail: five segments curling up and over the back, then the sting
    m.part("tail1", "body", pivot=(0, -4, 8), rot=(38, 0, 0))
    m.part("tail2", "tail1", pivot=(0, 0, 7), rot=(36, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 0, 7), rot=(34, 0, 0))
    m.part("tail4", "tail3", pivot=(0, 0, 6.5), rot=(32, 0, 0))
    m.part("tail5", "tail4", pivot=(0, 0, 6), rot=(28, 0, 0))
    m.part("sting", "tail5", pivot=(0, 0, 5.5), rot=(20, 0, 0))

    # ------------------------------------------------------------------ body
    m.box("body", -9, -6, -8, 18, 8, 16, {"top": inlaid(1, pattern="chevron"), "*": inlaid(2)})   # carapace
    m.box("body", -7, 2, -6, 14, 3, 12, {"side": lambda f_, x, y, w, h: SOCKET if x % 3 == 2 else sbone(3)(f_, x, y, w, h),
                                          "*": sbone(3, SAND_D, SAND_DD)})                         # rib underside
    m.box("body", -6, -8, -6, 12, 2, 13, inlaid(4))                                                # raised dorsal plate
    for i, z in enumerate((-5, -1, 3)):
        m.box("body", -0.5, -10 - (i % 2), z, 1, 2 + (i % 2), 2, {"*": sbone(5 + i), "top": GOLD})  # dorsal spines
    m.box("body", -10, -4, -7, 1, 4, 14, inlaid(9, pattern="bands"))                              # side rims
    m.box("body", 9, -4, -7, 1, 4, 14, inlaid(10, pattern="bands"))

    # head: a great skull, amber eyes, a nemes headdress with lappets and a gold cobra
    def face(f_, x, y, w, h):
        if y in (4, 5) and x in (2, 3, 6, 7):
            return AMBER if y == 4 else SOCKET
        if y == 3 and x in (2, 3, 6, 7):
            return SAND_DD
        if y == 6 and x in (4, 5):
            return SOCKET
        if y == h - 1:
            return SAND if x % 2 == 0 else SOCKET
        if y < 2:
            return LAPIS if x % 2 else GOLD  # headdress brow band
        return sbone(20)(f_, x, y, w, h)

    def face_glow(f_, x, y, w, h):
        return AMBER if y == 4 and x in (2, 3, 6, 7) else None
    m.box("head", -5, -9, -9, 10, 9, 9, {"front": face, "*": sbone(21)}, glow={"front": face_glow})
    m.box("head", -6, -10, -8, 12, 3, 9, nemes(22))                                              # headdress crown
    m.box("head", -6.5, -8, -6, 2, 12, 5, nemes(23))                                              # lappets
    m.box("head", 4.5, -8, -6, 2, 12, 5, nemes(24))
    m.box("head", -4, -9, 0, 8, 10, 2, nemes(25))                                                 # back flap
    m.box("head", -1, -14, -9.5, 2, 4, 2, {"*": GOLD, "front": lambda f_, x, y, w, h: VENOM if y == 1 else GOLD},
          glow={"front": lambda f_, x, y, w, h: VENOM if y == 1 else None})                       # cobra
    m.box("head", -2, -11, -10, 4, 2, 1, GOLD)                                                   # cobra hood
    m.box("jaw", -4, 0, -6, 8, 3, 6, {"front": lambda f_, x, y, w, h: SAND if (y == 0 and x % 2 == 0) else
                                      SOCKET if y == 0 else sbone(26)(f_, x, y, w, h), "*": sbone(26)})
    m.box("jaw", -1.5, 3, -5, 3, 4, 2, nemes(27))                                                 # pharaoh's beard

    # ------------------------------------------------------------------ pincers
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, claw, pinch = f"arm_{side}", f"fore_{side}", f"claw_{side}", f"pinch_{side}"
        m.part(arm, "body", pivot=(7 * sx, -1, -7), rot=(-14, -42 * sx, 0))
        m.part(fore, arm, pivot=(0, 0, -11), rot=(6, 50 * sx, 0))
        m.part(claw, fore, pivot=(0, 0, -10), rot=(0, -10 * sx, 0))
        m.part(pinch, claw, pivot=(-3 * sx, 0, -7), rot=(0, -12 * sx, 0))
        m.box(arm, -2, -2, -11, 4, 4, 11, sbone(30 + sx))
        m.box(arm, -2.5, -2.5, -2, 5, 5, 4, inlaid(31 + sx, pattern=None))                        # shoulder knob
        m.box(fore, -2, -2, -10, 4, 4, 10, {"top": inlaid(32 + sx), "*": sbone(33 + sx)})
        m.box(fore, -2.5, -2.5, -1.5, 5, 5, 3, sbone(34 + sx, SAND_D))                            # elbow
        m.box(claw, -4.5, -3.5, -8, 9, 7, 8, {"top": inlaid(35 + sx, pattern="chevron"), "*": inlaid(36 + sx)})
        # fixed finger on the outside, movable finger on the inside (serrated with dark teeth)
        serr = lambda f_, x, y, w, h, s=37 + sx: SOCKET if (f_ in ("left", "right") and y == h - 1 and x % 2 == 0) else sbone(s)(f_, x, y, w, h)  # noqa: E731
        m.box(claw, (1 if sx < 0 else -4), -2.5, -17, 3, 5, 9, serr)
        m.box(claw, (1.5 if sx < 0 else -3.5), -1.5, -19, 2, 3, 2, GOLD_D)
        m.box(pinch, -1.5, -2, -9, 3, 4, 9, serr)
        m.box(pinch, -1, -1.5, -11, 2, 3, 2, GOLD_D)

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        for i, (z, yaw) in enumerate(((-3, 22), (2, -2), (6.5, -28))):
            leg, foot = f"leg_{side}{i}", f"foot_{side}{i}"
            m.part(leg, "body", pivot=(8.5 * sx, -1, z), rot=(0, yaw * sx, -34 * sx))
            m.part(foot, leg, pivot=(14 * sx, 0, 0), rot=(0, 0, 20 * sx))
            m.box(leg, 0 if sx > 0 else -14, -1.5, -1.5, 14, 3, 3, {"top": inlaid(50 + i, pattern="bands"), "*": sbone(51 + i)})
            m.box(leg, (12 if sx > 0 else -15), -2, -2, 3, 4, 4, inlaid(54 + i, pattern=None))     # knee
            m.box(foot, -1, 0, -1, 2, 19, 2, {"side": lambda f_, x, y, w, h, s=57 + i: (LAPIS if y in (2, 3) else GOLD if y == 4
                                                                                      else sbone(s)(f_, x, y, w, h)),
                                              "*": sbone(57 + i)})
            m.box(foot, -0.5, 19, -0.5, 1, 4, 1, SAND_DD)

    # ------------------------------------------------------------------ tail
    sizes = ((7, 6, 7), (6, 6, 7), (6, 5, 6.5), (5, 5, 6), (4, 4, 5.5))
    for i, (w, hgt, ln) in enumerate(sizes):
        part = f"tail{i + 1}"
        m.box(part, -w / 2, -hgt / 2, 0, w, hgt, int(round(ln)), {"top": inlaid(70 + i, pattern="bands"), "*": sbone(71 + i)})
        m.box(part, -0.5, -hgt / 2 - 1.5, 1, 1, 2, 2, {"*": sbone(76 + i), "top": GOLD})               # vertebral spike
    m.box("sting", -2.5, -2.5, 0, 5, 5, 5, {"*": GOLD, "top": nemes(80), "side": nemes(81)})        # venom bulb
    m.box("sting", -1, -1, 5, 2, 2, 4, {"*": GOLD_D, "top": GOLD})
    m.box("sting", -0.5, -0.5, 9, 1, 1, 3, VENOM, glow=VENOM)                                       # glowing barb

    _anims(m)
    return m


TAIL = ("tail1", "tail2", "tail3", "tail4", "tail5", "sting")


def _anims(m):
    legs = [(f"leg_{s}{i}", f"foot_{s}{i}", sx, i) for s, sx in (("r", -1), ("l", 1)) for i in range(3)]

    idle = m.anim("idle", 3.0)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, 0.8, 0)), (3.0, (0, 0, 0)))
    idle.rot("tail1", (0, (0, 0, 0)), (1.5, (-4, 6, 0)), (3.0, (0, 0, 0)))
    idle.rot("tail3", (0, (0, 0, 0)), (1.5, (5, -4, 0)), (3.0, (0, 0, 0)))
    idle.rot("sting", (0, (0, 0, 0)), (0.75, (8, 0, 0)), (1.5, (0, 0, 0)), (2.25, (8, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (4, -6, 0)), (2.0, (-3, 6, 0)), (3.0, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.2, (10, 0, 0)), (1.6, (0, 0, 0)), (3.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        idle.rot(f"pinch_{side}", (0, (0, 0, 0)), (0.4, (0, -18 * sx, 0)), (0.7, (0, 0, 0)), (1.9, (0, 0, 0)),
                 (2.2, (0, -14 * sx, 0)), (2.5, (0, 0, 0)), (3.0, (0, 0, 0)))
        idle.rot(f"arm_{side}", (0, (0, 0, 0)), (1.5, (-4, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    for leg, foot, sx, i in legs:
        group = (i + (0 if sx > 0 else 1)) % 2
        sw = 14 * (1 if group == 0 else -1)
        lift = -12 * sx
        if group == 0:
            walk.rot(leg, (0, (0, sw * sx, 0)), (0.3, (0, 0, lift)), (0.6, (0, -sw * sx, 0)), (1.2, (0, sw * sx, 0)))
        else:
            walk.rot(leg, (0, (0, sw * sx, 0)), (0.6, (0, -sw * sx, 0)), (0.9, (0, 0, lift)), (1.2, (0, sw * sx, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.8, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.8, 0)), (1.2, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, -2)), (0.6, (0, 0, 2)), (1.2, (0, 0, -2)))
    walk.rot("tail1", (0, (0, 6, 0)), (0.6, (0, -6, 0)), (1.2, (0, 6, 0)))
    walk.rot("tail3", (0, (0, -5, 0)), (0.6, (0, 5, 0)), (1.2, (0, -5, 0)))
    walk.rot("arm_r", (0, (-4, 0, 0)), (0.6, (4, 0, 0)), (1.2, (-4, 0, 0)))
    walk.rot("arm_l", (0, (4, 0, 0)), (0.6, (-4, 0, 0)), (1.2, (4, 0, 0)))

    # pincer combo: right claw cocked open (0.6 s) and snapped shut, then the left claw (0.95 s)
    a = m.anim("pincer", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-25, 30, 0)), (0.6, (-28, 32, 0)), (0.68, (5, -30, 0), "linear"), (0.9, (5, -25, 0)), (1.6, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.6, (0, 15, 0)), (0.68, (0, -15, 0), "linear"), (1.6, (0, 0, 0)))
    a.rot("pinch_r", (0, (0, 0, 0)), (0.5, (0, 45, 0)), (0.6, (0, 48, 0)), (0.68, (0, -5, 0), "linear"), (1.0, (0, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-15, -20, 0)), (0.85, (-30, -34, 0)), (0.95, (5, 30, 0), "linear"), (1.15, (5, 25, 0)), (1.6, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.85, (0, -15, 0)), (0.95, (0, 15, 0), "linear"), (1.6, (0, 0, 0)))
    a.rot("pinch_l", (0, (0, 0, 0)), (0.7, (0, -40, 0)), (0.85, (0, -48, 0)), (0.95, (0, 5, 0), "linear"), (1.2, (0, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (-6, -12, 0)), (0.68, (4, 10, 0), "linear"), (0.85, (-4, 12, 0)), (0.95, (4, -12, 0), "linear"),
          (1.15, (3, -10, 0)), (1.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 0, 2)), (0.68, (0, 0, -3), "linear"), (0.95, (0, 0, -4), "linear"), (1.6, (0, 0, 0)))

    # sting: the tail drawn back and coiled (0.9 s), then whipped forward far over the head, recover
    a = m.anim("sting", 1.6)
    _sting(a, 0.0, 0.9, 1.15, 1.6)
    a.rot("body", (0, (0, 0, 0)), (0.9, (-6, 0, 0)), (0.98, (8, 0, 0), "linear"), (1.15, (6, 0, 0)), (1.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.9, (0, 0, 2)), (0.98, (0, 0, -3), "linear"), (1.15, (0, 0, -3)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (0.98, (12, 0, 0)), (1.6, (0, 0, 0)))

    # burrow: legs dig and she sinks out of sight (0.8 s), stays hidden, bursts up at 2.0 s, recovers
    a = m.anim("burrow", 3.0)
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, 2, 0)), (0.8, (0, -34, 0)), (1.95, (0, -34, 0)), (2.1, (0, 6, 0), "linear"),
          (2.35, (0, 2, 0)), (2.6, (0, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (-12, 0, 0)), (0.8, (20, 0, 0)), (1.95, (20, 0, 0)), (2.1, (-25, 0, 0), "linear"),
          (2.4, (-10, 0, 0)), (3.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (0.8, (-10, 0, 0)), (1.95, (0, 0, 0)), (2.1, (-50, 30 * sx, 0)),
              (2.4, (-40, 25 * sx, 0)), (3.0, (0, 0, 0)))
        a.rot(f"pinch_{side}", (0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.1, (0, -40 * sx, 0)), (2.5, (0, -30 * sx, 0)), (3.0, (0, 0, 0)))
    for leg, foot, sx, i in legs:
        ph = 0.12 * i
        a.rot(leg, (0, (0, 0, 0)), (0.15 + ph, (0, 25 * sx, -20 * sx)), (0.35 + ph, (0, -20 * sx, 10 * sx)), (0.6 + ph, (0, 20 * sx, -15 * sx)),
              (0.9 + ph, (0, 0, 0)), (2.0, (0, 0, 0)), (2.1, (0, 0, -30 * sx)), (2.5, (0, 0, -10 * sx)), (3.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.1, (35, 0, 0)), (2.5, (30, 0, 0)), (3.0, (0, 0, 0)))

    # spray: head thrown back, jaw shut (0.7 s); then the jaw gapes and she sprays sand, sweeping her head
    a = m.anim("spray", 2.1)
    a.rot("head", (0, (0, 0, 0)), (0.6, (-30, 0, 0)), (0.7, (-32, 0, 0)), (0.78, (15, -20, 0), "linear"), (1.1, (15, 20, 0)),
          (1.5, (12, -15, 0)), (2.1, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.7, (0, 0, 0)), (0.78, (45, 0, 0), "linear"), (1.5, (45, 0, 0)), (1.7, (0, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.7, (-12, 0, 0)), (0.78, (6, 0, 0), "linear"), (1.5, (6, 0, 0)), (2.1, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.7, (0, 1, 2)), (0.78, (0, -1, -2), "linear"), (1.5, (0, -1, -2)), (2.1, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.7, (-20, 25 * sx, 0)), (0.8, (10, 35 * sx, 0)), (1.5, (10, 35 * sx, 0)), (2.1, (0, 0, 0)))

    # sweep: the tail cocked to her right (0.7 s), then swept round in a wide flat arc behind and beside her
    a = m.anim("sweep", 1.4)
    a.rot("tail1", (0, (0, 0, 0)), (0.6, (-25, 45, 0)), (0.7, (-27, 48, 0)), (0.88, (-25, -70, 0), "linear"), (1.0, (-22, -65, 0)), (1.4, (0, 0, 0)))
    a.rot("tail2", (0, (0, 0, 0)), (0.7, (-25, 0, 0)), (0.88, (-25, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("tail3", (0, (0, 0, 0)), (0.7, (-20, 0, 0)), (0.88, (-20, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (0, 20, 0)), (0.7, (0, 22, 0)), (0.88, (0, -30, 0), "linear"), (1.0, (0, -28, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (0, -20, 0)), (0.88, (0, 20, 0)), (1.4, (0, 0, 0)))

    # summon: rears up on her hind legs, pincers spread, a silent scream (1.0 s), slams back down
    a = m.anim("summon", 2.0)
    a.rot("body", (0, (0, 0, 0)), (0.7, (-28, 0, 0)), (0.95, (-30, 0, 0)), (1.05, (6, 0, 0), "linear"), (1.4, (4, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.7, (0, 5, 3)), (0.95, (0, 6, 3)), (1.05, (0, -2, 0), "linear"), (1.4, (0, -1, 0)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (40, 0, 0)), (1.4, (40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-20, 0, 0)), (1.05, (10, 0, 0)), (2.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.7, (-40, 40 * sx, 0)), (0.95, (-45, 45 * sx, 0)), (1.05, (10, 10 * sx, 0), "linear"),
              (1.4, (8, 8 * sx, 0)), (2.0, (0, 0, 0)))
        a.rot(f"pinch_{side}", (0, (0, 0, 0)), (0.7, (0, -45 * sx, 0)), (1.0, (0, -45 * sx, 0)), (1.1, (0, 0, 0)), (2.0, (0, 0, 0)))
    for leg, foot, sx, i in legs:
        if i == 0:
            a.rot(leg, (0, (0, 0, 0)), (0.7, (0, 15 * sx, -40 * sx)), (0.95, (0, 15 * sx, -45 * sx)), (1.05, (0, 0, 5 * sx), "linear"), (2.0, (0, 0, 0)))
    a.rot("tail1", (0, (0, 0, 0)), (0.7, (25, 0, 0)), (1.05, (-10, 0, 0)), (2.0, (0, 0, 0)))

    # double sting: a first strike at 0.8 s, the tail re-coils, and a second delayed strike at 1.5 s
    a = m.anim("double_sting", 2.25)
    _sting(a, 0.0, 0.8, 0.95, None, recoil=(1.3, 1.5, 1.7, 2.25))
    a.rot("body", (0, (0, 0, 0)), (0.8, (-6, 0, 0)), (0.88, (8, 0, 0), "linear"), (1.3, (-8, 8, 0)), (1.5, (-8, 10, 0)),
          (1.58, (10, -8, 0), "linear"), (1.7, (8, -8, 0)), (2.25, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.88, (12, 0, 0)), (1.3, (-8, 0, 0)), (1.58, (12, 0, 0)), (2.25, (0, 0, 0)))

    # roar: phase two; rears up, jaw wide, pincers raised high and snapping, tail rattling
    a = m.anim("roar", 2.4)
    a.rot("body", (0, (0, 0, 0)), (0.5, (-25, 0, 0)), (1.9, (-25, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, 5, 2)), (1.9, (0, 5, 2)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-25, 0, 0)), (1.9, (-25, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (45, 0, 0)), (1.9, (45, 0, 0)), (2.4, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.5, (-55, 35 * sx, 0)), (1.9, (-55, 35 * sx, 0)), (2.4, (0, 0, 0)))
        a.rot(f"pinch_{side}", (0, (0, 0, 0)), (0.5, (0, -40 * sx, 0)), (0.8, (0, 0, 0)), (1.1, (0, -40 * sx, 0)), (1.4, (0, 0, 0)),
              (1.7, (0, -40 * sx, 0)), (2.4, (0, 0, 0)))
    a.rot("tail4", (0, (0, 0, 0)), (0.5, (0, 10, 0)), (0.7, (0, -10, 0)), (0.9, (0, 10, 0)), (1.1, (0, -10, 0)), (1.3, (0, 10, 0)),
          (1.5, (0, -10, 0)), (1.9, (0, 0, 0)), (2.4, (0, 0, 0)))

    # stagger: legs buckle, the body crashes down, the tail droops
    a = m.anim("stagger", 2.0)
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, -7, 0)), (1.6, (0, -7, 0)), (2.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (8, 0, 6)), (1.6, (8, 0, 6)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 10, 0)), (1.6, (20, 10, 0)), (2.0, (0, 0, 0)))
    for t, d in (("tail1", -35), ("tail2", -30), ("tail3", -30), ("tail4", -25), ("tail5", -20)):
        a.rot(t, (0, (0, 0, 0)), (0.3, (d, 0, 0)), (1.6, (d, 0, 0)), (2.0, (0, 0, 0)))
    for leg, foot, sx, i in legs:
        a.rot(leg, (0, (0, 0, 0)), (0.3, (0, 0, 22 * sx)), (1.6, (0, 0, 22 * sx)), (2.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (1.6, (25, 0, 0)), (2.0, (0, 0, 0)))


def _sting(a, t0, hit, hold, end, recoil=None):
    """Tail strike: coil back until ``hit``, whip forward (linear), hold, then rest at ``end`` or recoil
    into a second strike: recoil = (coil_t, hit2, hold2, end)."""
    coil = {"tail1": (-28, 0, 0), "tail2": (12, 0, 0), "tail3": (12, 0, 0), "tail4": (10, 0, 0), "tail5": (12, 0, 0), "sting": (15, 0, 0)}
    # solved numerically: the barb ends ~1 block ahead of the skull, pointing forward and down
    strike = {"tail1": (89, 0, 0), "tail2": (2, 0, 0), "tail3": (-18, 0, 0), "tail4": (-33, 0, 0), "tail5": (-16, 0, 0), "sting": (-3, 0, 0)}
    for p in TAIL:
        keys = [(t0, (0, 0, 0)), (hit - 0.12, tuple(c * 0.9 for c in coil[p])), (hit, coil[p]), (hit + 0.08, strike[p], "linear"),
                (hold, strike[p])]
        if recoil is None:
            keys.append((end, (0, 0, 0)))
        else:
            c_t, hit2, hold2, end2 = recoil
            keys += [(c_t, tuple(c * 0.9 for c in coil[p])), (hit2, coil[p]), (hit2 + 0.08, strike[p], "linear"),
                     (hold2, strike[p]), (end2, (0, 0, 0))]
        a.rot(p, *keys)
