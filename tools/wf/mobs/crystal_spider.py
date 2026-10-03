"""The Crystal Matriarch (La Matriarche de cristal): an enormous geode spider, low and wide (legs span
over four blocks), whose carapace has grown into amethyst and lithite.

Silhouette idea: eight long jointed legs splayed like a crown around a low body, and a bulbous abdomen
bristling with a ridge of glowing crystal spires (the tallest a teal lithite shard). A cluster of eight
glowing eyes, amethyst-tipped fangs, crystal shards growing at every knee.
"""
from ..models import Model
from ..texgen import mix, mul

CHITIN = (54, 40, 72)
CHITIN_L = (104, 80, 136)
CHITIN_D = (22, 16, 30)
SHEEN = (120, 92, 160)
HAIR = (104, 88, 120)
AME = (168, 104, 226)
AME_L = (226, 186, 255)
AME_D = (104, 56, 160)
LIT = (78, 226, 206)
LIT_L = (196, 255, 246)
LIT_D = (28, 134, 136)
EYE = (120, 255, 236)
EYE_V = (220, 150, 255)


def _n(x, y, seed):
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


# ---------------------------------------------------------------- paint helpers
def carapace(seed=0, rim=True):
    """Glossy chitin: dark violet-black with a lit sheen band near the top, plate rims and pits."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return CHITIN_D
        if face == "top":
            if rim and (x == 0 or y == 0 or x == w - 1 or y == h - 1):
                return CHITIN_L
            # a glossy highlight streak along the spine and pits
            if abs(x - w // 2) <= 1:
                return mix(CHITIN_L, SHEEN, 0.4)
            c = mul(CHITIN, 1.15 - 0.2 * abs(x - w / 2) / max(1, w / 2))
            return mul(c, 0.8) if _n(x, y, seed) < 0.06 else c
        if rim and y == 0:
            return CHITIN_L
        if rim and y == h - 1:
            return CHITIN_D
        k = 1.12 - 0.35 * (y / max(1, h))
        c = mul(CHITIN, k)
        if y == 1 and h > 4:
            c = mix(c, SHEEN, 0.35)
        return mul(c, 0.82) if _n(x, y, seed) < 0.07 else c
    return f


def segments(rows, seed=0):
    """Abdomen: chitin segments with lit leading edges; the glow layer draws crystal veins."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return CHITIN_D
        if face == "top":
            u = y % rows
            c = mul(CHITIN, 1.12 - 0.05 * u)
            if u == 0:
                c = CHITIN_L
            if abs(x - w // 2) <= 1 and u != 0:
                c = mix(c, SHEEN, 0.3)
            return c
        u = y % rows
        c = mul(CHITIN, 1.1 - 0.06 * u)
        if u == 0:
            c = mix(CHITIN_L, SHEEN, 0.3)
        if _n(x, y, seed) < 0.05:
            c = mul(c, 0.8)
        return c
    return f


def vein_glow(seed=0, top_pattern=True):
    """Crystal veins under the abdomen plates: a branching teal-violet hourglass on top, sparse cracks on the sides."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return None
        if face == "top" and top_pattern:
            cx = (w - 1) / 2
            t = y / max(1, h - 1)
            half = 1.0 + 3.5 * abs(t - 0.5) * 2       # hourglass: narrow waist, wide ends
            if abs(abs(x - cx) - half) < 0.7:
                return LIT if t < 0.5 else AME_L
            if abs(x - cx) < 0.6 and 0.3 < t < 0.7:
                return LIT_L
            return None
        if face in ("left", "right", "back", "front"):
            # crystal light leaking through a few plate seams, in runs, with bright nodes
            if y % 5 == 4 and _n(x // 3, y, seed) > 0.5:
                return LIT if (x // 3 + y) % 2 else AME
            if y % 5 == 2 and x % 7 == (seed + y) % 7:
                return LIT_L
        return None
    return f


def crystal(base, light, dark, seed=0):
    """A faceted shard: lit front facet with an edge highlight, darker side and back facets."""
    def f(face, x, y, w, h):
        if face == "top":
            return light
        if face == "bottom":
            return dark
        tone = {"front": 1.0, "left": 0.86, "right": 0.78, "back": 0.66}[face]
        c = mul(base, tone + 0.18 * (1 - y / max(1, h)))
        if x == 0 and face in ("front", "left"):
            c = light                                  # bright facet edge
        if x == w - 1:
            c = mix(c, dark, 0.5)
        if (y + x * 3 + seed) % 7 == 0:
            c = mix(c, light, 0.45)                     # internal flaw catching light
        return c
    return f


def crystal_glow(base, light, dark, seed=0):
    """Emissive facets (kept shaded so the shard keeps its volume in the dark)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return None
        if face == "top":
            return light
        tone = {"front": 1.0, "left": 0.82, "right": 0.72, "back": 0.6}[face]
        c = mul(base, tone + 0.15 * (1 - y / max(1, h)))
        if x == 0 and face in ("front", "left"):
            c = light
        return c
    return f


def leg_paint(seed=0, joint_rows=()):
    """Spindly chitin legs: banded joints, bristles, a lighter dorsal ridge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return CHITIN_D
        if face == "top":
            return mix(CHITIN_L, SHEEN, 0.3) if y == h // 2 else CHITIN_L if _n(x, y, seed) < 0.15 else CHITIN
        # side faces run along the leg (x is along the length on front/back faces)
        along = x
        if along in joint_rows or along == 0:
            return mix(CHITIN_L, AME_D, 0.4)
        c = mul(CHITIN, 1.15 - 0.3 * (y / max(1, h)))
        if _n(along, y, seed) < 0.12:
            c = HAIR                                    # bristles
        return c
    return f


def eyes_face(face, x, y, w, h):
    """Front of the head: two great eyes, six smaller ones, a chitin brow."""
    pts = _eye_pts(w)
    if (x, y) in pts:
        return pts[(x, y)]
    if y == 0:
        return CHITIN_L
    return mul(CHITIN, 1.05 - 0.04 * y)


def _eye_pts(w):
    """Eight eyes: two great 3x3 eyes (white-hot pupils), two medium above, four small at the sides."""
    cx = w // 2
    pts = {}
    for x0 in (cx - 5, cx + 2):
        for ox in range(3):
            for oy in range(3):
                pts[(x0 + ox, 3 + oy)] = (240, 255, 252) if (ox, oy) == (1, 1) else EYE if oy > 0 else mix(EYE, (40, 120, 120), 0.4)
    for x0 in (cx - 3, cx + 1):
        for ox in range(2):
            pts[(x0 + ox, 1)] = EYE_V
    for dx, dy in ((-7, 3), (6, 3), (-7, 6), (6, 6)):
        pts[(cx + dx, dy)] = EYE_V
    return pts


def eyes_glow(face, x, y, w, h):
    return _eye_pts(w).get((x, y))


# ---------------------------------------------------------------- the model
LEGS = (  # (pivot z on the thorax, spread yaw for the right side, lift, knee bend)
    (-9, -42, 40, -112),
    (-4, -14, 36, -106),
    (1, 14, 36, -106),
    (6, 40, 40, -112),
)
L1, L2 = 22, 29


def build():
    m = Model("crystal_spider", seed=91, shadow=2.2, walk_speed=1.6, walk_scale=1.0)

    # ------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -15, 0))
    m.part("head", "body", pivot=(0, 0, -12))
    m.part("fang_r", "head", pivot=(-3.5, 2, -7), rot=(-10, 0, 8))
    m.part("fang_l", "head", pivot=(3.5, 2, -7), rot=(-10, 0, -8))
    m.part("palp_r", "head", pivot=(-6, 2, -6), rot=(-30, 20, 0))
    m.part("palp_l", "head", pivot=(6, 2, -6), rot=(-30, -20, 0))
    m.part("abdomen", "body", pivot=(0, -2, 9), rot=(-6, 0, 0))

    # ------------------------------------------------------------ thorax and head
    m.box("body", -9, -6, -12, 18, 10, 22, {"*": carapace(1), "front": carapace(1)})
    m.box("body", -7, -9, -10, 14, 3, 17, carapace(2))                       # raised carapace shield
    m.box("body", -6, 4, -8, 12, 2, 14, CHITIN_D)                            # sternum
    m.box("head", -8, -6, -9, 16, 10, 10, {"front": eyes_face, "*": carapace(3)}, glow={"front": eyes_glow})
    m.box("head", -6, -8, -8, 12, 2, 7, carapace(4))                         # brow ridge
    m.box("head", -1, -11, -8, 2, 4, 2, crystal(LIT, LIT_L, LIT_D, 5), glow=crystal_glow(LIT, LIT_L, LIT_D, 5))  # brow gem
    for side, sx in (("r", -1), ("l", 1)):
        fang, palp = f"fang_{side}", f"palp_{side}"
        m.box(fang, -2, 0, -3, 4, 7, 4, carapace(5 + sx))
        m.box(fang, -1.5, 6, -4.5, 3, 4, 3, crystal(AME, AME_L, AME_D, 6), glow=crystal_glow(AME, AME_L, AME_D))
        m.box(fang, -1, 9, -6, 2, 2, 3, crystal(AME_L, (255, 240, 255), AME, 7), glow=crystal_glow(AME_L, (255, 240, 255), AME))
        m.box(palp, -1, 0, -1, 2, 8, 2, leg_paint(8, (3,)))

    # ------------------------------------------------------------ abdomen: a rounded, segmented sac crowned with crystal spires
    m.box("abdomen", -13, -8, 2, 26, 17, 26, {"*": segments(5, 10)}, glow=vein_glow(12, False))
    m.box("abdomen", -11, -12, 3, 22, 4, 24, segments(4, 21), glow=vein_glow(22))          # upper tier
    m.box("abdomen", -8, -14, 6, 16, 2, 19, segments(4, 13), glow=vein_glow(14))           # dorsal dome
    m.box("abdomen", -10, -6, -1, 20, 13, 3, segments(4, 15))                              # front cap (pedicel)
    m.box("abdomen", -11, -7, 28, 22, 14, 3, {"*": segments(4, 16), "back": carapace(11)}, glow=vein_glow(23, False))
    m.box("abdomen", -8, -4, 31, 16, 9, 2, {"*": segments(3, 24), "back": carapace(25)})    # rear dome
    m.box("abdomen", -15, -5, 6, 2, 12, 18, segments(4, 17), glow=vein_glow(18, False))     # flanks
    m.box("abdomen", 13, -5, 6, 2, 12, 18, segments(4, 19), glow=vein_glow(20, False))
    for x, y in ((-3, 1), (1, 1), (-1, 3)):                                                 # spinnerets
        m.box("abdomen", x, y, 33, 2, 2, 3, {"*": CHITIN_L, "back": AME_D})
    clusters = [  # (pivot in abdomen space, rot of the cluster, [(w, length, x, z, rx, rz, kind)])
        ((0, -14, 14), (-10, 0, 0), [(6, 24, 0, 0, 0, 0, "lit"), (4, 15, -3, 2, 10, -22, "ame"), (4, 13, 3, 2, 14, 24, "ame"),
                                     (3, 9, 0, -3, -26, 0, "lit")]),
        ((-7, -13, 8), (-20, 0, -28), [(4, 16, 0, 0, 0, 0, "ame"), (3, 9, 2, 1, 0, 30, "lit")]),
        ((7, -13, 9), (-16, 0, 30), [(4, 18, 0, 0, 0, 0, "ame"), (3, 10, -2, 1, 0, -30, "ame")]),
        ((-6, -13, 22), (24, 0, -22), [(5, 14, 0, 0, 0, 0, "lit"), (3, 8, 2, -1, -20, 20, "ame")]),
        ((6, -13, 21), (18, 0, 24), [(4, 13, 0, 0, 0, 0, "ame"), (2, 7, -2, 1, 0, -35, "lit")]),
        ((-13, -6, 15), (0, 0, -60), [(3, 10, 0, 0, 0, 0, "ame"), (2, 6, 0, 2, 20, 10, "lit")]),
        ((13, -6, 13), (-8, 0, 58), [(3, 11, 0, 0, 0, 0, "lit"), (2, 6, 0, -2, -25, -10, "ame")]),
        ((0, -12, 28), (50, 0, 0), [(4, 10, 0, 0, 0, 0, "ame"), (2, 6, 2, 0, 0, 30, "lit")]),
    ]
    k = 0
    for ci, (piv, rot, shards) in enumerate(clusters):
        root = f"cluster_{ci}"
        m.part(root, "abdomen", pivot=piv, rot=rot)
        m.box(root, -3.5, -2, -3.5, 7, 3, 7, carapace(30 + ci, rim=False))                # chitin socket
        for (wd, ln, x, z, rx, rz, kind) in shards:
            base, light, dark = (LIT, LIT_L, LIT_D) if kind == "lit" else (AME, AME_L, AME_D)
            name = f"shard_{k}"
            m.part(name, root, pivot=(x, -1, z), rot=(rx, 0, rz))
            o = -wd / 2
            m.box(name, o, -ln, o, wd, ln, wd, crystal(base, light, dark, k), glow=crystal_glow(base, light, dark, k))
            tw = max(1, wd - 2)
            m.box(name, -tw / 2, -ln - 3, -tw / 2, tw, 3, tw, crystal(light, (255, 255, 255), base, k + 1),
                  glow=crystal_glow(light, (255, 255, 255), base, k + 1))
            k += 1
    # a few small clusters on the thorax shield
    for i, (x, z, rz, rx, ln) in enumerate(((-5, -6, 30, -20, 6), (5, -5, -28, -15, 7), (0, 3, 0, 25, 5))):
        name = f"thorax_shard_{i}"
        m.part(name, "body", pivot=(x, -8, z), rot=(rx, 0, rz))
        kind = (AME, AME_L, AME_D) if i % 2 == 0 else (LIT, LIT_L, LIT_D)
        m.box(name, -1, -ln, -1, 2, ln, 2, crystal(*kind, 40 + i), glow=crystal_glow(*kind, 40 + i))

    # ------------------------------------------------------------ eight jointed legs (femur + tibia), crystal knees
    for i, (z, yaw, lift, bend) in enumerate(LEGS):
        for side, sx in (("r", -1), ("l", 1)):
            leg, knee = f"leg_{side}{i}", f"knee_{side}{i}"
            m.part(leg, "body", pivot=(8 * sx, 0, z), rot=(0, yaw * -sx if sx > 0 else yaw, -lift * sx))
            m.part(knee, leg, pivot=(L1 * sx, 0, 0), rot=(0, 0, -bend * sx))
            if sx < 0:
                m.box(leg, -L1, -2.5, -2.5, L1, 5, 5, leg_paint(50 + i, (L1 - 3,)))
                m.box(knee, -15, -2, -2, 15, 4, 4, leg_paint(60 + i, (7,)))
                m.box(knee, -L2, -1.5, -1.5, L2 - 15, 3, 3, leg_paint(70 + i, ()))
                m.box(knee, -L2 - 3, -1, -1, 3, 2, 2, crystal(AME, AME_L, AME_D, 80 + i), glow=crystal_glow(AME, AME_L, AME_D))
            else:
                m.box(leg, 0, -2.5, -2.5, L1, 5, 5, leg_paint(50 + i, (2,)))
                m.box(knee, 0, -2, -2, 15, 4, 4, leg_paint(60 + i, (7,)))
                m.box(knee, 15, -1.5, -1.5, L2 - 15, 3, 3, leg_paint(70 + i, ()))
                m.box(knee, L2, -1, -1, 3, 2, 2, crystal(AME, AME_L, AME_D, 80 + i), glow=crystal_glow(AME, AME_L, AME_D))
            # a crystal shard growing on the knee joint (outer legs only, alternating colours)
            if i in (0, 3) or (i + (sx > 0)) % 2 == 0:
                kind = (LIT, LIT_L, LIT_D) if (i + sx) % 2 else (AME, AME_L, AME_D)
                m.box(knee, -1.5, -7, -1.5, 3, 5, 3, crystal(*kind, 90 + i), glow=crystal_glow(*kind, 90 + i))

    anims(m)
    return m


def anims(m):
    Z = (0, 0, 0)

    def legs(a, fn):
        """fn(i, side, sx) -> list of (t, leg_rot, knee_rot[, interp]) keyframes."""
        for i in range(4):
            for side, sx in (("r", -1), ("l", 1)):
                ks = fn(i, side, sx)
                if not ks:
                    continue
                a.rot(f"leg_{side}{i}", *[(k[0], k[1], *k[3:]) for k in ks])
                a.rot(f"knee_{side}{i}", *[(k[0], k[2], *k[3:]) for k in ks])

    # ------------------------------------------------------------ idle: the abdomen breathes, fangs clack, legs twitch
    a = m.anim("idle", 3.0)
    a.rot("abdomen", (0, Z), (1.5, (-4, 0, 0)), (3.0, Z))
    a.scale("abdomen", (0, (1, 1, 1)), (1.5, (1.03, 1.04, 1.02)), (3.0, (1, 1, 1)))
    a.rot("fang_r", (0, Z), (0.4, (0, 0, -12)), (0.6, Z), (1.8, Z), (2.0, (0, 0, -10)), (2.2, Z), (3.0, Z))
    a.rot("fang_l", (0, Z), (0.4, (0, 0, 12)), (0.6, Z), (1.8, Z), (2.0, (0, 0, 10)), (2.2, Z), (3.0, Z))
    a.rot("palp_r", (0, Z), (0.8, (-15, 0, 0)), (1.6, Z), (3.0, Z))
    a.rot("palp_l", (0, Z), (1.4, Z), (2.2, (-15, 0, 0)), (3.0, Z))
    a.rot("leg_r0", (0, Z), (1.0, (0, 0, 6)), (1.3, Z), (3.0, Z))
    a.rot("leg_l0", (0, Z), (2.0, Z), (2.3, (0, 0, -6)), (2.6, Z), (3.0, Z))
    a.pos("body", (0, Z), (1.5, (0, -0.6, 0)), (3.0, Z))

    # ------------------------------------------------------------ walk: alternating tetrapod gait (legs lift and swing)
    a = m.anim("walk", 1.0)

    def walk_keys(i, side, sx):
        group = (i + (0 if sx < 0 else 1)) % 2
        ph = 0.0 if group == 0 else 0.5
        swing = 16
        lift = 14 * -sx                              # positive lift raises the leg (z axis, mirrored)
        y0 = (0, swing * (1 if group == 0 else -1), 0)
        keys = []
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            u = (t + ph) % 1.0
            sw = swing * (1 - 4 * abs(u - 0.5)) if True else 0   # -swing..swing triangle
            up = lift if u < 0.5 and 0.1 < u < 0.4 else 0
            keys.append((t, (0, sw * -sx, up), (0, 0, 0)))
        keys[-1] = (1.0, keys[0][1], keys[0][2])
        return keys
    legs(a, walk_keys)
    a.pos("body", (0, Z), (0.25, (0, 0.8, 0)), (0.5, Z), (0.75, (0, 0.8, 0)), (1.0, Z))
    a.rot("abdomen", (0, (0, 3, 0)), (0.5, (0, -3, 0)), (1.0, (0, 3, 0)))

    # ------------------------------------------------------------ stab: rears up, the front legs lifted high, stab down at 0.65 s
    a = m.anim("stab", 1.3)
    a.rot("body", (0, Z), (0.55, (-22, 0, 0)), (0.65, (8, 0, 0), "linear"), (0.9, (8, 0, 0)), (1.3, Z))
    a.pos("body", (0, Z), (0.55, (0, 5, 3)), (0.65, (0, -2, -3), "linear"), (0.9, (0, -2, -3)), (1.3, Z))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"leg_{side}0", (0, Z), (0.55, (0, -15 * -sx, 70 * -sx)), (0.65, (0, -5 * -sx, 10 * -sx), "linear"),
              (0.9, (0, -5 * -sx, 10 * -sx)), (1.3, Z))
        a.rot(f"knee_{side}0", (0, Z), (0.55, (0, 0, 40 * -sx)), (0.65, (0, 0, -25 * -sx), "linear"), (0.9, (0, 0, -25 * -sx)), (1.3, Z))
        a.rot(f"leg_{side}1", (0, Z), (0.55, (0, 10 * -sx, 35 * -sx)), (0.65, Z), (1.3, Z))
        a.rot(f"leg_{side}3", (0, Z), (0.55, (0, 0, -20 * -sx)), (0.65, Z), (1.3, Z))
    a.rot("fang_r", (0, Z), (0.55, (-30, 0, -25)), (0.65, (10, 0, 10)), (1.3, Z))
    a.rot("fang_l", (0, Z), (0.55, (-30, 0, 25)), (0.65, (10, 0, -10)), (1.3, Z))
    a.rot("abdomen", (0, Z), (0.55, (20, 0, 0)), (0.65, (-6, 0, 0)), (1.3, Z))

    # ------------------------------------------------------------ pounce: crouch low (0.7 s), spring forward, land, recover
    a = m.anim("pounce", 1.9)
    a.pos("body", (0, Z), (0.65, (0, -6, 3)), (0.7, (0, -6, 3)), (0.95, (0, 8, -2)), (1.3, (0, -3, 0)), (1.5, (0, -3, 0)), (1.9, Z))
    a.rot("body", (0, Z), (0.65, (8, 0, 0)), (0.95, (-18, 0, 0)), (1.3, (6, 0, 0)), (1.9, Z))
    for i in range(4):
        for side, sx in (("r", -1), ("l", 1)):
            fwd = i < 2
            a.rot(f"leg_{side}{i}", (0, Z), (0.65, (0, 0, -18 * -sx)), (0.95, (0, (-25 if fwd else 25) * -sx, 30 * -sx)),
                  (1.3, (0, 0, -10 * -sx)), (1.9, Z))
            a.rot(f"knee_{side}{i}", (0, Z), (0.65, (0, 0, -20 * -sx)), (0.95, (0, 0, 35 * -sx)), (1.3, Z), (1.9, Z))
    a.rot("fang_r", (0, Z), (0.7, (-20, 0, -30)), (1.3, (10, 0, 5)), (1.9, Z))
    a.rot("fang_l", (0, Z), (0.7, (-20, 0, 30)), (1.3, (10, 0, -5)), (1.9, Z))

    # ------------------------------------------------------------ web: rears, the abdomen arches over her back, sprays a web at 0.6 s
    a = m.anim("web", 1.4)
    a.rot("body", (0, Z), (0.5, (-18, 0, 0)), (0.6, (-6, 0, 0), "linear"), (1.0, (-6, 0, 0)), (1.4, Z))
    a.pos("body", (0, Z), (0.5, (0, 4, 2)), (0.6, (0, 2, 0)), (1.4, Z))
    a.rot("abdomen", (0, Z), (0.5, (62, 0, 0)), (0.6, (48, 0, 0), "linear"), (1.0, (48, 0, 0)), (1.4, Z))
    a.rot("fang_r", (0, Z), (0.5, (-35, 0, -30)), (0.6, (-35, 0, -30)), (1.4, Z))
    a.rot("fang_l", (0, Z), (0.5, (-35, 0, 30)), (0.6, (-35, 0, 30)), (1.4, Z))
    a.rot("head", (0, Z), (0.5, (-15, 0, 0)), (0.6, (8, 0, 0), "linear"), (1.4, Z))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"leg_{side}0", (0, Z), (0.5, (0, 15 * -sx, 40 * -sx)), (1.0, (0, 15 * -sx, 40 * -sx)), (1.4, Z))

    # ------------------------------------------------------------ spikes: rears and drives both front legs into the floor (0.8 s)
    a = m.anim("spikes", 1.6)
    a.rot("body", (0, Z), (0.65, (-28, 0, 0)), (0.8, (12, 0, 0), "linear"), (1.15, (10, 0, 0)), (1.6, Z))
    a.pos("body", (0, Z), (0.65, (0, 7, 4)), (0.8, (0, -3, -3), "linear"), (1.15, (0, -3, -3)), (1.6, Z))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"leg_{side}0", (0, Z), (0.65, (0, -12 * -sx, 85 * -sx)), (0.8, (0, -10 * -sx, -5 * -sx), "linear"),
              (1.15, (0, -10 * -sx, -5 * -sx)), (1.6, Z))
        a.rot(f"knee_{side}0", (0, Z), (0.65, (0, 0, 50 * -sx)), (0.8, (0, 0, -20 * -sx), "linear"), (1.15, (0, 0, -20 * -sx)), (1.6, Z))
        a.rot(f"leg_{side}1", (0, Z), (0.65, (0, 15 * -sx, 60 * -sx)), (0.8, (0, -5 * -sx, 0)), (1.15, (0, -5 * -sx, 0)), (1.6, Z))
        a.rot(f"knee_{side}1", (0, Z), (0.65, (0, 0, 30 * -sx)), (0.8, (0, 0, -15 * -sx)), (1.6, Z))
    a.rot("abdomen", (0, Z), (0.65, (30, 0, 0)), (0.8, (-10, 0, 0), "linear"), (1.6, Z))
    a.scale("abdomen", (0, (1, 1, 1)), (0.65, (1.08, 1.1, 1.05)), (0.8, (0.96, 0.95, 0.98)), (1.6, (1, 1, 1)))

    # ------------------------------------------------------------ shards: the abdomen lifts and shudders, then fires (0.7 s)
    a = m.anim("shards", 1.5)
    a.rot("abdomen", (0, Z), (0.45, (38, 0, 0)), (0.55, (42, 0, 4)), (0.62, (42, 0, -4)), (0.7, (25, 0, 0), "linear"),
          (1.0, (25, 0, 0)), (1.5, Z))
    a.scale("abdomen", (0, (1, 1, 1)), (0.6, (1.1, 1.1, 1.1)), (0.7, (0.95, 0.95, 0.95), "linear"), (1.0, (1, 1, 1)), (1.5, (1, 1, 1)))
    a.rot("body", (0, Z), (0.45, (8, 0, 0)), (0.7, (-4, 0, 0)), (1.5, Z))
    a.pos("body", (0, Z), (0.45, (0, -2, 0)), (0.7, (0, 0, 2)), (1.5, Z))

    # ------------------------------------------------------------ storm (phase 2): rears up high, screeching; the crystals flare
    a = m.anim("storm", 2.0)
    a.rot("body", (0, Z), (0.8, (-38, 0, 0)), (0.9, (-34, 0, 0)), (1.5, (-34, 0, 0)), (2.0, Z))
    a.pos("body", (0, Z), (0.8, (0, 9, 5)), (1.5, (0, 9, 5)), (2.0, Z))
    a.rot("abdomen", (0, Z), (0.8, (40, 0, 0)), (1.5, (40, 0, 0)), (2.0, Z))
    a.scale("abdomen", (0, (1, 1, 1)), (0.9, (1.12, 1.12, 1.12)), (1.0, (1.05, 1.05, 1.05)), (1.5, (1.1, 1.1, 1.1)), (2.0, (1, 1, 1)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"leg_{side}0", (0, Z), (0.8, (0, -10 * -sx, 75 * -sx)), (1.5, (0, -10 * -sx, 75 * -sx)), (2.0, Z))
        a.rot(f"knee_{side}0", (0, Z), (0.8, (0, 0, 60 * -sx)), (1.5, (0, 0, 60 * -sx)), (2.0, Z))
        a.rot(f"leg_{side}1", (0, Z), (0.8, (0, 20 * -sx, 50 * -sx)), (1.5, (0, 20 * -sx, 50 * -sx)), (2.0, Z))
    a.rot("fang_r", (0, Z), (0.8, (-40, 0, -35)), (1.5, (-40, 0, -35)), (2.0, Z))
    a.rot("fang_l", (0, Z), (0.8, (-40, 0, 35)), (1.5, (-40, 0, 35)), (2.0, Z))

    # ------------------------------------------------------------ brood (phase 2): the abdomen pulses, spiderlings pour out (0.6 s)
    a = m.anim("brood", 1.4)
    a.rot("abdomen", (0, Z), (0.5, (-12, 0, 0)), (0.6, (6, 0, 0), "linear"), (1.0, (6, 0, 0)), (1.4, Z))
    a.scale("abdomen", (0, (1, 1, 1)), (0.25, (1.12, 1.08, 1.12)), (0.4, (0.96, 0.96, 0.96)), (0.5, (1.15, 1.12, 1.15)),
            (0.6, (0.9, 0.9, 0.95), "linear"), (1.0, (1, 1, 1)), (1.4, (1, 1, 1)))
    a.pos("body", (0, Z), (0.5, (0, -3, 0)), (0.6, (0, -1, 0)), (1.4, Z))

    # ------------------------------------------------------------ skitter (phase 2): body low, legs blur, a dash at 0.5 s
    a = m.anim("skitter", 1.5)
    a.pos("body", (0, Z), (0.45, (0, -4, 0)), (1.0, (0, -4, 0)), (1.5, Z))
    a.rot("body", (0, Z), (0.45, (6, 0, 0)), (1.0, (6, 0, 0)), (1.5, Z))

    def skitter_keys(i, side, sx):
        group = (i + (0 if sx < 0 else 1)) % 2
        s = 1 if group == 0 else -1
        keys = [(0, Z, Z), (0.45, (0, 0, -12 * -sx), Z)]
        t = 0.5
        while t < 1.0:
            keys.append((round(t, 3), (0, 22 * s * -sx, 10 * -sx), (0, 0, 10 * -sx), "linear"))
            s = -s
            t += 0.1
        keys.append((1.5, Z, Z))
        return keys
    legs(a, skitter_keys)

    # ------------------------------------------------------------ roar: rears up on four legs, fangs spread, crystals flare
    a = m.anim("roar", 2.4)
    a.rot("body", (0, Z), (0.5, (-40, 0, 0)), (1.9, (-40, 0, 0)), (2.4, Z))
    a.pos("body", (0, Z), (0.5, (0, 10, 6)), (1.9, (0, 10, 6)), (2.4, Z))
    a.rot("abdomen", (0, Z), (0.5, (45, 0, 0)), (1.9, (45, 0, 0)), (2.4, Z))
    a.scale("abdomen", (0, (1, 1, 1)), (0.5, (1.1, 1.1, 1.1)), (1.2, (1.15, 1.15, 1.15)), (1.9, (1.1, 1.1, 1.1)), (2.4, (1, 1, 1)))
    for side, sx in (("r", -1), ("l", 1)):
        for i, up in ((0, 80), (1, 55)):
            a.rot(f"leg_{side}{i}", (0, Z), (0.5, (0, -10 * -sx, up * -sx)), (1.2, (0, -18 * -sx, (up + 10) * -sx)),
                  (1.9, (0, -10 * -sx, up * -sx)), (2.4, Z))
            a.rot(f"knee_{side}{i}", (0, Z), (0.5, (0, 0, 50 * -sx)), (1.9, (0, 0, 50 * -sx)), (2.4, Z))
    a.rot("fang_r", (0, Z), (0.5, (-40, 0, -40)), (1.9, (-40, 0, -40)), (2.4, Z))
    a.rot("fang_l", (0, Z), (0.5, (-40, 0, 40)), (1.9, (-40, 0, 40)), (2.4, Z))

    # ------------------------------------------------------------ stagger: legs buckle, the body crashes down and rocks
    a = m.anim("stagger", 2.0)
    a.pos("body", (0, Z), (0.25, (0, -8, 0)), (1.6, (0, -8, 0)), (2.0, Z))
    a.rot("body", (0, Z), (0.25, (6, 0, 8)), (0.8, (6, 0, -5)), (1.6, (6, 0, 6)), (2.0, Z))
    for i in range(4):
        for side, sx in (("r", -1), ("l", 1)):
            a.rot(f"leg_{side}{i}", (0, Z), (0.25, (0, 0, 25 * -sx)), (1.6, (0, 0, 25 * -sx)), (2.0, Z))
            a.rot(f"knee_{side}{i}", (0, Z), (0.25, (0, 0, -30 * -sx)), (1.6, (0, 0, -30 * -sx)), (2.0, Z))
    a.rot("fang_r", (0, Z), (0.25, (20, 0, 20)), (1.6, (20, 0, 20)), (2.0, Z))
    a.rot("fang_l", (0, Z), (0.25, (20, 0, -20)), (1.6, (20, 0, -20)), (2.0, Z))
