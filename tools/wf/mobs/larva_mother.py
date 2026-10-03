"""The Larva Mother (La Mère-Larve): champion of the Void Crypt, a bloated void-grub queen (about 3 blocks wide,
4.5 long). Her front half rears up like a striking caterpillar to show a round lamprey maw ringed with teeth and
six hooked mandibles; behind her chitin-plated segments drags an enormous pale egg sac, veined and full of
glowing eggs, ending in an ovipositor. Violet light-pods bulge along her flanks.

Animations (impact -> Java wind-up ticks): bite 0.7 s (14), slam 0.9 s (18), burrow (sinks 0-0.8 s, hidden,
erupts at 1.6 s = 32), spit 0.8 s (16), birth 0.8 s (16), roll (curl 0.8 s = 16, rolls until 2.0 s), roar,
stagger.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from .void_larva import CHITIN, CHITIN_D, CHITIN_L, GLOW, GLOW_HOT, LIP, THROAT, TOOTH, segment, spot_glow

SAC = (164, 134, 188)
SAC_D = (104, 74, 136)
VEIN = (96, 52, 128)
EGG = (226, 160, 255)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


def _eggs(face, w, h, seed):
    """Egg centres on a face (a loose grid, jittered)."""
    pts = []
    step = 7
    for gy in range(3, h - 2, step):
        for gx in range(3 + (gy // step) % 2 * 3, w - 2, step):
            r = _h(gx, gy, seed, FACE_N[face])
            if r % 4 == 0:
                continue                                # irregular clutch
            pts.append((gx + r % 3 - 1, gy + (r >> 3) % 3 - 1, 1 + (r >> 6) % 2))
    return pts


def sac(seed=0):
    """Egg sac membrane: pale lilac with branching dark veins and the shadows of eggs inside."""
    def f(face, x, y, w, h):
        r = _h(x, y, seed, FACE_N[face])
        t = y / max(1, h - 1)
        c = mix(SAC, SAC_D, 0.25 + 0.5 * t) if face != "top" else mix(SAC, (220, 200, 236), 0.3)
        if face == "bottom":
            return SAC_D
        for ex, ey, er in _eggs(face, w, h, seed):
            d = math.hypot(x - ex, y - ey)
            if d <= er + 0.4:
                return mix(EGG, SAC_D, 0.35 if d > er - 0.6 else 0.0)
            if d <= er + 1.3:
                c = mix(c, SAC_D, 0.4)                 # the egg's shadow in the membrane
        vx = (x + int(3 * math.sin(y * 0.5 + seed))) % 9
        if vx == 0 or (vx == 1 and r % 3 == 0):
            c = mix(c, VEIN, 0.55)                     # veins
        if r % 37 == 0:
            c = mix(c, (240, 230, 250), 0.5)           # wet gloss
        return c
    return f


def sac_glow(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return None
        for ex, ey, er in _eggs(face, w, h, seed):
            d = math.hypot(x - ex, y - ey)
            if d <= er - 0.6:
                return GLOW_HOT
            if d <= er + 0.4:
                return (*GLOW, 150)
            if d <= er + 1.3:
                return (*GLOW, 35)
        return None
    return f


def big_maw(face, x, y, w, h):
    """Front of the head (w=h=18): lips, two rings of teeth, a deep throat with a glowing core."""
    if face != "front":
        return segment(80, spots=False)(face, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    ang = math.atan2(y - cy, x - cx)
    if r > 8.4:
        return CHITIN_D
    if r > 7.2:
        return LIP if (int((ang + math.pi) * 6) % 2) else mix(LIP, CHITIN_D, 0.4)
    if r > 5.6:
        return TOOTH if int((ang + math.pi) / (2 * math.pi) * 16) % 2 == 0 else (70, 24, 80)
    if r > 4.6:
        return (90, 30, 100)
    if r > 3.4:
        return TOOTH if int((ang + math.pi) / (2 * math.pi) * 12 + 0.5) % 2 == 0 else (40, 10, 50)
    if r > 1.8:
        return THROAT
    return (120, 40, 160)


def big_maw_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r <= 1.8:
        return GLOW_HOT
    if r <= 3.4:
        return (*GLOW, 140 - int((r - 1.8) * 50))
    return None


def pod(face, x, y, w, h):
    return mix(GLOW, (120, 60, 170), 0.35 if (x in (0, w - 1) or y in (0, h - 1)) else 0.0)


def pod_glow(face, x, y, w, h):
    edge = x in (0, w - 1) or y in (0, h - 1)
    return (*GLOW, 150) if edge else GLOW_HOT


def leg_paint(face, x, y, w, h):
    return CHITIN_D if y >= h - 2 else (CHITIN if (y // 2) % 2 else mix(CHITIN, CHITIN_L, 0.3))


def plate(seed=0):
    """A broad dorsal plate: dark chitin with a lit violet rim and a glowing seam light."""
    def f(face, x, y, w, h):
        if face == "top":
            if x in (0, w - 1) or y in (0, h - 1):
                return CHITIN_L
            c = mix(CHITIN, CHITIN_L, 0.2)
            if y == h // 2:
                c = mix(c, CHITIN_D, 0.5)
            if _h(x, y, seed) % 19 == 0:
                c = mix(c, (170, 140, 220), 0.4)
            return c
        return CHITIN_L if y == 0 else CHITIN_D
    return f


def build():
    m = Model("larva_mother", seed=97, shadow=2.0, walk_speed=0.7, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("core", "bone", pivot=(0, -14, 2))
    m.part("body", "core", pivot=(0, 0, 0))
    m.part("thorax", "core", pivot=(0, -2, -8), rot=(-22, 0, 0))
    m.part("neck", "thorax", pivot=(0, -2, -11), rot=(-30, 0, 0))
    m.part("head", "neck", pivot=(0, -1, -7), rot=(34, 0, 0))
    m.part("abdomen", "core", pivot=(0, -1, 8))
    m.part("sac", "abdomen", pivot=(0, -1, 13), rot=(6, 0, 0))
    m.part("ovi", "sac", pivot=(0, 3, 22), rot=(-10, 0, 0))
    mands = []
    for i in range(6):
        ang = i * 60
        ring = f"mring{i}"
        m.part(ring, "head", pivot=(0, 0, -7), rot=(0, 0, ang))
        name = f"mand{i}"
        m.part(name, ring, pivot=(0, -8, 0), rot=(28, 0, 0))
        mands.append(name)
    legs = []
    for i, (parent, z, y) in enumerate((("thorax", -8, 6), ("thorax", -3, 6), ("body", -4, 8), ("body", 4, 8))):
        for side, sx in (("r", -1), ("l", 1)):
            name = f"leg{i}_{side}"
            m.part(name, parent, pivot=(sx * (10 if parent == "thorax" else 12), y, z), rot=(0, 0, -40 * sx))
            legs.append((name, sx, i))

    # body segments with plates, glow spots and light-pods
    m.box("body", -12, -10, -8, 24, 20, 16, segment(1), glow=spot_glow(1))
    m.box("body", -11, -12, -7, 22, 2, 14, plate(2), glow=spot_glow(2))
    m.box("thorax", -10, -9, -11, 20, 17, 11, segment(3), glow=spot_glow(3))
    m.box("thorax", -9, -11, -10, 18, 2, 9, plate(4), glow=spot_glow(4))
    m.box("neck", -8, -8, -8, 16, 14, 8, segment(5), glow=spot_glow(5))
    m.box("neck", -7, -10, -7, 14, 2, 6, plate(6))
    m.box("head", -9, -9, -7, 18, 18, 7, big_maw, glow=big_maw_glow)
    m.box("head", -7, -11, -6, 14, 2, 5, plate(7))
    m.box("abdomen", -13, -11, 0, 26, 22, 14, segment(8), glow=spot_glow(8))
    m.box("abdomen", -12, -13, 1, 24, 2, 12, plate(9), glow=spot_glow(9))
    for part, x, y, z, s in (("body", -14, -4, -4, 5), ("body", 9, -4, 1, 5), ("abdomen", -15, -5, 3, 6),
                             ("abdomen", 9, -5, 6, 6), ("thorax", -12, -3, -8, 4), ("thorax", 8, -3, -6, 4),
                             ("abdomen", -4, -15, 4, 4)):
        m.box(part, x, y, z, s, s, s, pod, glow=pod_glow)
    # the egg sac, its ovipositor
    # an ellipsoid of overlapping boxes: wide band, tall band, long band, and a core
    m.box("sac", -16, -9, 4, 32, 17, 15, sac(10), glow=sac_glow(10))
    m.box("sac", -11, -15, 4, 22, 29, 15, sac(12), glow=sac_glow(12))
    m.box("sac", -12, -10, 0, 24, 19, 23, sac(13), glow=sac_glow(13))
    m.box("sac", -14, -13, 2, 28, 25, 19, sac(14), glow=sac_glow(14))
    m.box("ovi", -4, -4, 0, 8, 8, 5, segment(11, spots=False))
    m.box("ovi", -2, -2, 5, 4, 4, 3, {"back": GLOW, "*": CHITIN_L}, glow={"back": GLOW_HOT})
    # mandibles: a hooked ring around the maw
    for i, name in enumerate(mands):
        m.box(name, -1.5, -1, -9, 3, 2, 9, lambda f_, x, y, w, h: TOOTH if f_ == "front" else
              mix(CHITIN_L, TOOTH, 0.3 + 0.5 * (1 - y / max(1, h - 1))) if f_ in ("top", "bottom") else (92, 64, 120))
        m.box(name, -1, 0.5, -11, 2, 2, 2, TOOTH)
    for name, sx, i in legs:
        m.box(name, -1.5, 0, -1.5, 3, 9, 3, leg_paint)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.0)
    idle.scale("sac", (0, (1, 1, 1)), (1.5, (1.05, 1.04, 1.03)), (3.0, (1, 1, 1)))
    idle.scale("abdomen", (0, (1, 1, 1)), (0.75, (1.03, 1.03, 1.0)), (1.5, (1, 1, 1)), (3.0, (1, 1, 1)))
    idle.rot("neck", (0, (0, 0, 0)), (1.5, (-4, 6, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (3, -4, 3)), (2.2, (0, 4, -3)), (3.0, (0, 0, 0)))
    idle.rot("thorax", (0, (0, 0, 0)), (1.5, (-2, 0, 0)), (3.0, (0, 0, 0)))
    for k, name in enumerate(mands):
        t0 = 0.2 + (k % 3) * 0.25
        idle.rot(name, (0, (0, 0, 0)), (t0, (-12, 0, 0)), (t0 + 0.2, (0, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    for k, (part, amp) in enumerate((("thorax", 6), ("neck", 5), ("abdomen", 6), ("sac", 8))):
        ph = k * 0.2
        keys = [(t, (round(2 * math.sin(2 * math.pi * (t / 2.0 + ph + 0.25)), 2),
                     round(amp * math.sin(2 * math.pi * (t / 2.0 + ph)), 2), 0)) for t in (0, 0.5, 1.0, 1.5, 2.0)]
        walk.rot(part, *keys)
    walk.pos("core", (0, (0, 0, 0)), (0.5, (0, 1, 0)), (1.0, (0, 0, 0)), (1.5, (0, 1, 0)), (2.0, (0, 0, 0)))
    for name, sx, i in legs:
        ph = 0.5 * (i % 2) + (0.25 if sx > 0 else 0)
        walk.rot(name, *[(t, (round(30 * math.sin(2 * math.pi * (t / 2.0 + ph)), 2), 0, 0)) for t in (0, 0.5, 1.0, 1.5, 2.0)])

    def mand_keys(a, keys):
        for name in mands:
            a.rot(name, *keys)

    # bite: rear back with the maw yawning (0.7 s / 14 ticks), lunge and snap, recover
    a = m.anim("bite", 1.4)
    a.rot("neck", (0, (0, 0, 0)), (0.65, (-28, 0, 0)), (0.75, (34, 0, 0), "linear"), (1.0, (30, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("thorax", (0, (0, 0, 0)), (0.65, (-12, 0, 0)), (0.75, (14, 0, 0), "linear"), (1.0, (12, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.65, (-10, 0, 0)), (0.75, (6, 0, 0)), (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.65, (0, 0, 4)), (0.75, (0, 0, -10), "linear"), (1.0, (0, 0, -10)), (1.4, (0, 0, 0)))
    mand_keys(a, [(0, (0, 0, 0)), (0.65, (-45, 0, 0)), (0.75, (40, 0, 0), "linear"), (1.0, (35, 0, 0)), (1.4, (0, 0, 0))])

    # slam: the whole front rears high (0.9 s / 18 ticks), crashes down, slow recovery
    a = m.anim("slam", 1.8)
    a.rot("thorax", (0, (0, 0, 0)), (0.85, (-50, 0, 0)), (0.95, (22, 0, 0), "linear"), (1.3, (20, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.85, (-15, 0, 0)), (0.95, (25, 0, 0), "linear"), (1.3, (22, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.85, (-10, 0, 0)), (0.95, (4, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("sac", (0, (0, 0, 0)), (0.85, (12, 0, 0)), (0.95, (-6, 0, 0)), (1.8, (0, 0, 0)))
    a.pos("core", (0, (0, 0, 0)), (0.85, (0, 4, 2)), (0.95, (0, -3, -3), "linear"), (1.3, (0, -3, -3)), (1.8, (0, 0, 0)))
    mand_keys(a, [(0, (0, 0, 0)), (0.85, (-40, 0, 0)), (0.95, (20, 0, 0)), (1.8, (0, 0, 0))])

    # burrow: nose-dive into the floor (0-0.8 s), hidden, bursts out reared at 1.6 s (32 ticks)
    a = m.anim("burrow", 2.4)
    a.rot("thorax", (0, (0, 0, 0)), (0.4, (35, 0, 0)), (0.8, (45, 0, 0)), (1.55, (-50, 0, 0)), (1.65, (-50, 0, 0)),
          (2.0, (-25, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (1.55, (-20, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("core", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (0.8, (30, 0, 0)), (1.55, (-20, 0, 0)), (2.0, (-8, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("core", (0, (0, 0, 0)), (0.4, (0, -10, -4)), (0.8, (0, -46, -6)), (1.5, (0, -46, 0)), (1.65, (0, 8, 0), "linear"),
          (1.9, (0, 3, 0)), (2.4, (0, 0, 0)))
    mand_keys(a, [(0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.65, (-50, 0, 0)), (2.0, (-30, 0, 0)), (2.4, (0, 0, 0))])

    # spit: head drawn up, the sac contracting (0.8 s / 16 ticks), a forward heave with the maw wide
    a = m.anim("spit", 1.6)
    a.rot("neck", (0, (0, 0, 0)), (0.75, (-38, 0, 0)), (0.85, (14, 0, 0), "linear"), (1.15, (10, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thorax", (0, (0, 0, 0)), (0.75, (-16, 0, 0)), (0.85, (6, 0, 0), "linear"), (1.6, (0, 0, 0)))
    a.scale("sac", (0, (1, 1, 1)), (0.75, (1.12, 1.1, 1.08)), (0.85, (0.88, 0.9, 0.92), "linear"), (1.2, (0.95, 0.95, 0.95)),
            (1.6, (1, 1, 1)))
    a.scale("neck", (0, (1, 1, 1)), (0.75, (1.12, 1.12, 1.0)), (0.85, (1, 1, 1)), (1.6, (1, 1, 1)))
    mand_keys(a, [(0, (0, 0, 0)), (0.75, (-20, 0, 0)), (0.85, (-55, 0, 0), "linear"), (1.15, (-50, 0, 0)), (1.6, (0, 0, 0))])

    # birth: the abdomen lifts and the sac squeezes eggs out of the ovipositor (0.8 s / 16 ticks)
    a = m.anim("birth", 1.8)
    a.rot("abdomen", (0, (0, 0, 0)), (0.6, (-14, 0, 0)), (1.2, (-12, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("sac", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (1.2, (-14, 0, 0)), (1.8, (0, 0, 0)))
    a.scale("sac", (0, (1, 1, 1)), (0.6, (1.16, 1.14, 1.12)), (0.8, (0.86, 0.88, 0.9), "linear"), (1.0, (1.06, 1.05, 1.04)),
            (1.2, (0.9, 0.92, 0.94)), (1.8, (1, 1, 1)))
    a.scale("ovi", (0, (1, 1, 1)), (0.7, (1.0, 1.0, 1.0)), (0.8, (1.5, 1.5, 1.3), "linear"), (1.0, (1.0, 1.0, 1.0)),
            (1.2, (1.4, 1.4, 1.2)), (1.8, (1, 1, 1)))
    a.rot("neck", (0, (0, 0, 0)), (0.6, (-25, 0, 0)), (1.2, (-25, 0, 0)), (1.8, (0, 0, 0)))
    mand_keys(a, [(0, (0, 0, 0)), (0.6, (-35, 0, 0)), (1.2, (-35, 0, 0)), (1.8, (0, 0, 0))])

    # roll: curl into a ball (0.8 s / 16 ticks), roll forward twice, uncurl. The spin ends on -720 degrees, which is
    # the rest orientation again (like the Drowned Warden's whirl).
    a = m.anim("roll", 2.6)
    a.rot("thorax", (0, (0, 0, 0)), (0.7, (70, 0, 0)), (2.0, (70, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.7, (60, 0, 0)), (2.0, (60, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("abdomen", (0, (0, 0, 0)), (0.7, (-45, 0, 0)), (2.0, (-45, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("sac", (0, (0, 0, 0)), (0.7, (-55, 0, 0)), (2.0, (-55, 0, 0)), (2.6, (0, 0, 0)))
    a.pos("core", (0, (0, 0, 0)), (0.7, (0, 14, 0)), (2.0, (0, 14, 0)), (2.6, (0, 0, 0)))
    a.rot("core", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (1.4, (-360, 0, 0), "linear"), (2.0, (-720, 0, 0), "linear"),
          (2.6, (-720, 0, 0)))

    # roar: phase change - she rears to full height, mandibles flared, the sac swelling
    a = m.anim("roar", 2.4)
    a.rot("thorax", (0, (0, 0, 0)), (0.6, (-45, 0, 0)), (1.9, (-45, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.6, (-25, 0, 0)), (1.9, (-25, 0, 0)), (2.4, (0, 0, 0)))
    a.scale("sac", (0, (1, 1, 1)), (0.6, (1.12, 1.1, 1.08)), (1.9, (1.12, 1.1, 1.08)), (2.4, (1, 1, 1)))
    mand_keys(a, [(0, (0, 0, 0)), (0.6, (-55, 0, 0)), (1.9, (-55, 0, 0)), (2.4, (0, 0, 0))])

    # stagger: the front collapses, the head on the floor, legs flailing
    a = m.anim("stagger", 2.5)
    a.rot("thorax", (0, (0, 0, 0)), (0.35, (26, 0, 8)), (2.0, (26, 0, 8)), (2.5, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.35, (30, 0, 0)), (2.0, (30, 0, 0)), (2.5, (0, 0, 0)))
    a.pos("core", (0, (0, 0, 0)), (0.35, (0, -4, 0)), (2.0, (0, -4, 0)), (2.5, (0, 0, 0)))
    for name, sx, i in legs:
        a.rot(name, (0, (0, 0, 0)), (0.5, (30, 0, 20 * sx)), (0.9, (-30, 0, 20 * sx)), (1.3, (30, 0, 20 * sx)),
              (1.7, (-30, 0, 20 * sx)), (2.5, (0, 0, 0)))
    return m
