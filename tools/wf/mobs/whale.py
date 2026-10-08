"""Humpback Whale (Baleine à bosse): huge, rare and peaceful, in the deep oceans. It cruises slowly, surfaces to
blow, and sings. Built at half scale (root scale 2).

Silhouette idea: a long, heavy spindle that reads from far away. A flat, gently down-sloping rostrum studded with
knobby tubercles over a deep, bulging lower jaw (the white pleated throat that balloons when it sings), the body
thickest just behind the very long white pectoral fins (three joints each, knobbed along the leading edge), a small
dorsal fin on a hump two thirds of the way back, a tall, laterally flattened tail stock and wide swept-back flukes
with a notched, scalloped trailing edge. Countershaded slate-blue over white, with pale rake scars and barnacle
clusters on the chin, the knobs and the fin edges.

Actions: sing (the throat swells, fins spread, a slow roll), spout (the head breaks the surface, the blowhole flares,
the back arches and the flukes lift).
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

BACK = (44, 56, 74)
BACK_L = (66, 82, 104)
SIDE = (84, 98, 118)
BELLY = (226, 230, 232)
BELLY_D = (188, 194, 204)
GROOVE = (140, 148, 162)
SCAR = (150, 162, 176)
BARNACLE = (214, 208, 190)
BARNACLE_D = (128, 118, 104)
EYE = (14, 14, 20)
MOUTH = (26, 28, 36)


def blot(x, y, seed, sx=4, sy=3):
    """Low-frequency mottling in [0, 1): flat patches of a few texels, not per-texel noise."""
    return (K.h(x // sx, y // sy, seed) % 100) / 100.0


def _u(face, x, w):
    """Distance from the front (-z) end along a side face."""
    return x if face == "left" else w - 1 - x


def barnacle(x, y, seed, density):
    """Barnacles grow in tight clusters: a cluster cell is picked by the seed, then a 2 x 2 rosette with a dark
    centre is drawn inside it."""
    if density <= 0:
        return None
    cx, cy = x // 4, y // 4
    if K.h(cx, cy, seed, 77) % 100 >= density * 100:
        return None
    ox, oy = K.h(cx, cy, seed, 5) % 3, K.h(cx, cy, seed, 6) % 3
    lx, ly = x % 4 - ox, y % 4 - oy
    if (lx, ly) in ((0, 0), (1, 0), (0, 1)):
        return BARNACLE
    if (lx, ly) == (1, 1):
        return BARNACLE_D
    return None


def hide(seed, belly=0.62, pleats=False, barnacles=0.0, scars=True):
    """Countershaded skin: dark slate back with a soft lighter streak along the spine, flanks fading to blue-grey,
    a crisp wavy line to the white belly (long pleat grooves on the throat), pale rake scars and barnacle clusters."""
    def f(face, x, y, w, h):
        if face == "top":
            b = barnacle(x, y, seed, barnacles * 0.6)
            if b:
                return b
            spine = abs(x - (w - 1) / 2) < max(1.0, w / 8)
            c = mix(BACK, BACK_L, 0.35 if spine else 0.12 * blot(x, y, seed))
            return c
        if face == "bottom":
            if pleats:
                return GROOVE if x % 2 == 0 else BELLY
            return mix(BELLY, BELLY_D, 0.4 * blot(x, y, seed))
        if face in ("front", "back"):
            v = y / max(1, h - 1)
            return BELLY if v > belly + 0.06 else mix(BACK, SIDE, min(1.0, v * 1.3))
        u = _u(face, x, w)
        v = y / max(1, h - 1)
        edge = belly + 0.06 * math.sin(u * 0.7 + seed)
        if v > edge:
            if pleats and y % 2 == 1:
                return GROOVE
            return BELLY if v > edge + 0.12 else BELLY_D
        b = barnacle(u, y, seed + 1, barnacles)
        if b:
            return b
        c = mix(BACK, SIDE, min(1.0, (v / max(0.1, edge)) ** 1.3))
        c = mix(c, BACK_L, 0.12 * blot(u, y, seed + 2, 5, 3))
        # rake scars: two short parallel pale scratches, slanting down toward the tail, on some flanks only
        if scars and w >= 10 and h >= 8 and K.h(seed, 3) % 3 != 0:
            s0 = 2 + K.h(seed, face == "left") % max(1, w - 10)
            r0 = 1 + K.h(seed, 4) % max(1, int(h * edge) - 4)
            du = u - s0
            if 0 <= du < 6 and y - r0 - du // 3 in (0, 2):
                c = mix(c, SCAR, 0.6)
        return c
    return f


def fin(seed, tip=False):
    """Pectoral fin: slate on top fading to white toward the tip, a white scalloped leading edge, white below."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BELLY if (x + seed) % 5 else BELLY_D
        if face == "top":
            lead = y >= h - 1                                               # the front edge (-z)
            if lead:
                return BELLY if x % 2 == 0 else BELLY_D
            t = x / max(1, w - 1)
            if seed % 2 == 0:
                t = 1 - t                                                   # the -x fin: tip is at x = 0
            t = t * 0.5 + (0.5 if tip else 0.0)
            c = mix(BACK, BELLY, max(0.0, t - 0.25) * 1.3)
            if blot(x, y, seed, 3, 2) < 0.25:
                c = mix(c, BELLY, 0.45)                                     # pale blotches
            return c
        if face == "front":
            return BELLY
        return mix(SIDE, BELLY, 0.5)
    return f


def fluke(side):
    """Half of the flukes: slate on top with a lit leading edge, white with dark marks below, scalloped trailing
    edge cut into the back rows; ``side`` is -1 or 1 (which end is the tip)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            back = y                                                         # y = 0 is the trailing (+z) edge
            tipu = x if side < 0 else w - 1 - x                               # distance from the tip
            if back == 0 and (x % 3 == 1 or tipu < 2):
                return None
            if back == 1 and tipu == 0:
                return None
            if face == "bottom":
                return BELLY if K.h(x // 3, y // 2, 7 + side) % 4 else (60, 70, 86)
            return BACK_L if y == h - 1 else mix(BACK, BACK_L, 0.2 * blot(x, y, 8))
        return BACK
    return f


def wave(anim, part, length, amp, phase=0.0, base=(0, 0, 0), kind="rot", n=8):
    """A seamless sine loop on ``part``: base + amp * sin(2 pi (t / length + phase))."""
    keys = []
    for i in range(n + 1):
        t = length * i / n
        s = math.sin(2 * math.pi * (i / n + phase))
        keys.append((round(t, 4), tuple(round(base[k] + amp[k] * s, 3) for k in range(3))))
    getattr(anim, kind)(part, *keys)


def build():
    m = Model("whale", seed=191, shadow=3.0, head=None, walk_speed=0.5, walk_scale=0.6)
    m.preview_idle = True

    m.part("bone", pivot=(0, 24, 0), scale=(2, 2, 2))
    m.part("body", "bone", pivot=(0, -8, 0))
    m.part("head", "body", pivot=(0, -1, -17), rot=(3, 0, 0))
    m.part("jaw", "head", pivot=(0, 1, -1))
    m.part("tail1", "body", pivot=(0, -1, 10))
    m.part("tail2", "tail1", pivot=(0, 0, 10))
    m.part("flukes", "tail2", pivot=(0, 0, 9))
    m.part("fluke_r", "flukes", pivot=(-1, 0, 1), rot=(0, -14, 0))
    m.part("fluke_l", "flukes", pivot=(1, 0, 1), rot=(0, 14, 0))

    # ---- torso: an octagonal cross-section (a wide box and a tall box), thickest behind the fins
    m.box("body", -8, -6, -18, 16, 12, 16, hide(1, belly=0.6, barnacles=0.03))
    m.box("body", -6.5, -7.5, -17, 13, 15, 14, hide(2, belly=0.6))
    m.box("body", -7, -5.5, -3, 14, 11, 13, hide(3, belly=0.62))
    m.box("body", -5.5, -6.5, -3, 11, 13, 12, hide(4, belly=0.62))
    m.box("body", -7.5, 2, -18, 15, 5, 14, hide(5, belly=0.0, pleats=True, scars=False))   # pleated chest

    # ---- head: a flat rostrum sloping down to the snout, knobby tubercles, the splash guard and blowholes
    m.box("head", -6, -6, -9, 12, 6, 10, hide(10, belly=0.95, barnacles=0.05, scars=False))
    m.box("head", -5, -5, -15, 10, 5, 7, hide(11, belly=0.95, barnacles=0.08, scars=False))
    m.box("head", -3.5, -4, -19, 7, 4, 5, hide(12, belly=0.95, barnacles=0.12, scars=False))
    for i, (x, z) in enumerate(((-2, -18), (1.5, -17), (-1, -15), (2.5, -14), (-3, -12), (0.5, -11), (-2, -8),
                                (3, -7))):
        m.box("head", x - 0.5, -5 if z < -15 else -6 if z < -9 else -7, z, 1, 1, 1,
              {"top": BARNACLE if i % 3 == 0 else BACK_L, "*": BACK})
    m.box("head", -2, -7, -4, 4, 1, 4, {"top": lambda f_, x, y, w, h: MOUTH if (x in (1, 2) and y in (1, 2))
                                        else BACK_L, "*": BACK})               # splash guard with the twin blowhole
    # the deep lower jaw: wider than the rostrum, pleated white throat, barnacles crusted on the chin
    def jaw_side(f_, x, y, w, h):
        if y == 0:
            return MOUTH                                                     # the long mouth line
        return hide(13, belly=0.35, pleats=True, barnacles=0.15, scars=False)(f_, x, y, w, h)
    m.box("jaw", -6.5, -1, -18, 13, 7, 19, {"left": jaw_side, "right": jaw_side,
                                          "front": hide(14, belly=0.55, barnacles=0.3, scars=False),
                                          "*": hide(13, belly=0.35, pleats=True, scars=False)})
    m.box("jaw", -5, 1, -20, 10, 4, 3, hide(15, belly=0.2, barnacles=0.4, scars=False))
    for sx in (-1, 1):
        # small eye just above the corner of the mouth, a pale lid around it
        m.box("head", 5.6 if sx > 0 else -6.6, -2, -3, 1, 2, 2,
              {"side": lambda f_, x, y, w, h: EYE if (y == 1 and x == 0) or (y == 1 and f_ == "right" and x == 1)
               else SIDE, "*": SIDE})

    # ---- pectoral fins: very long, three joints, swept back and down, knobbed leading edge
    for side, sx in (("r", -1), ("l", 1)):
        root, mid, tip = f"fin_{side}", f"fin_{side}_mid", f"fin_{side}_tip"
        m.part(root, "body", pivot=(7 * sx, 4, -12), rot=(0, 38 * sx, 9 * sx))
        m.part(mid, root, pivot=(9 * sx, 0, 0), rot=(0, 8 * sx, 4 * sx))
        m.part(tip, mid, pivot=(9 * sx, 0, 0), rot=(0, 10 * sx, 4 * sx))
        seed = 20 + (sx > 0)
        m.box(root, 0 if sx > 0 else -9, -1, -3.5, 9, 2, 7, fin(seed))
        m.box(mid, 0 if sx > 0 else -9, -1, -3, 9, 2, 6, fin(seed))
        m.box(tip, 0 if sx > 0 else -8, -0.5, -2.5, 8, 1, 5, fin(seed, tip=True))
        for i, part in enumerate((root, root, mid, mid, tip)):
            xx = (2 + (i % 2) * 4) * sx - (1 if sx < 0 else 0)
            m.box(part, xx, -1 if part != tip else -0.5, -4.5 + (i >= 2) * 0.5 + (i == 4) * 0.5, 1, 1, 1,
                  {"top": BARNACLE if i == 1 else BELLY, "*": BELLY})            # leading-edge knobs

    # ---- tail stock: tall and laterally flattened, a small dorsal fin on a hump, then the flukes
    m.box("tail1", -5.5, -5, 0, 11, 10, 11, hide(30, belly=0.68))
    m.box("tail1", -4.5, -6, 0, 9, 12, 10, hide(31, belly=0.68))
    m.box("tail1", -1.5, -8, 1, 3, 2, 6, {"*": BACK, "top": BACK_L})              # the hump
    m.box("tail1", -0.5, -10, 3, 1, 2, 4, {"*": BACK, "top": BACK_L})             # the little dorsal fin
    m.box("tail2", -3, -4, 0, 6, 8, 10, hide(32, belly=0.72, scars=False))
    m.box("tail2", -0.5, -5, 1, 1, 1, 8, {"*": BACK, "top": BACK_L})              # the keel along the top
    m.box("flukes", -2, -1.5, -1, 4, 3, 4, hide(33, belly=0.7, scars=False))
    m.box("fluke_r", -14, -1, -1, 14, 2, 8, fluke(-1))
    m.box("fluke_l", 0, -1, -1, 14, 2, 8, fluke(1))

    _anims(m)
    return m


def _anims(m):
    # idle: a slow travelling wave from the head to the flukes (each joint lags the one before), fins sculling with
    # the tips trailing, the throat breathing
    L = 4.0
    idle = m.anim("idle", L)
    wave(idle, "body", L, (1.5, 0, 0.6), 0.0)
    wave(idle, "body", L, (0, 0.5, 0), 0.0, kind="pos")
    wave(idle, "head", L, (-1.5, 0, 0), 0.08)
    wave(idle, "tail1", L, (5, 0, 0), 0.15)
    wave(idle, "tail2", L, (8, 0, 0), 0.27)
    wave(idle, "flukes", L, (14, 0, 0), 0.4)
    wave(idle, "fluke_r", L, (0, 0, 5), 0.5)
    wave(idle, "fluke_l", L, (0, 0, -5), 0.5)
    wave(idle, "jaw", L, (0.03, 0.05, 0), 0.25, base=(1, 1, 1), kind="scale")
    for side, sx in (("r", -1), ("l", 1)):
        wave(idle, f"fin_{side}", L, (5, 0, 5 * sx), 0.0)
        wave(idle, f"fin_{side}_mid", L, (0, 0, 5 * sx), 0.12)
        wave(idle, f"fin_{side}_tip", L, (0, 0, 7 * sx), 0.24)

    # swim: stronger, faster strokes, the flukes doing the work; fins tucked back
    W = 3.0
    walk = m.anim("walk", W)
    wave(walk, "body", W, (-2, 0, 0), 0.0)
    wave(walk, "tail1", W, (6, 0, 0), 0.12)
    wave(walk, "tail2", W, (10, 0, 0), 0.24)
    wave(walk, "flukes", W, (18, 0, 0), 0.36)
    wave(walk, "head", W, (1.5, 0, 0), 0.0)
    for side, sx in (("r", -1), ("l", 1)):
        wave(walk, f"fin_{side}", W, (0, 0, 4 * sx), 0.0, base=(0, -8 * sx, -4 * sx))
        wave(walk, f"fin_{side}_tip", W, (0, 0, 6 * sx), 0.2)

    # sing: the throat swells, fins open wide, the head lifts and the whale rolls slowly onto its side and back
    a = m.anim("sing", 4.0)
    a.rot("body", (0, (0, 0, 0)), (1.2, (-6, 0, 18)), (2.8, (-6, 0, 18)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-6, 0, 0)), (2.0, (-8, 0, 0)), (2.8, (-6, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("jaw", (0, (1, 1, 1)), (1.0, (1.06, 1.22, 1.02)), (1.6, (1.04, 1.12, 1.0)), (2.2, (1.07, 1.26, 1.02)),
            (2.8, (1.04, 1.12, 1.0)), (4.0, (1, 1, 1)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"fin_{side}", (0, (0, 0, 0)), (1.2, (0, -25 * sx, -30 * sx)), (2.8, (0, -25 * sx, -35 * sx)),
              (4.0, (0, 0, 0)))
        a.rot(f"fin_{side}_tip", (0, (0, 0, 0)), (1.4, (0, 0, -14 * sx)), (2.4, (0, 0, -4 * sx)), (3.2, (0, 0, -12 * sx)),
              (4.0, (0, 0, 0)))
    a.rot("tail1", (0, (0, 0, 0)), (1.5, (6, 0, 0)), (2.5, (-4, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("flukes", (0, (0, 0, 0)), (1.5, (14, 0, 0)), (2.5, (-10, 0, 0)), (4.0, (0, 0, 0)))

    # spout: the head breaks the surface, the blowhole flares (the jaw tucks), then the back arches over and the
    # flukes lift as it rolls back under
    a = m.anim("spout", 2.0)
    a.rot("body", (0, (0, 0, 0)), (0.6, (-7, 0, 0)), (1.4, (4, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-6, 0, 0)), (0.8, (-4, 0, 0)), (1.4, (5, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("jaw", (0, (1, 1, 1)), (0.5, (1, 0.94, 1)), (0.9, (1, 1.04, 1)), (2.0, (1, 1, 1)))
    a.rot("tail1", (0, (0, 0, 0)), (0.6, (8, 0, 0)), (1.4, (-8, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("tail2", (0, (0, 0, 0)), (0.8, (6, 0, 0)), (1.5, (-10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("flukes", (0, (0, 0, 0)), (0.9, (6, 0, 0)), (1.6, (-16, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (2.0, (0, 0, 0)))
