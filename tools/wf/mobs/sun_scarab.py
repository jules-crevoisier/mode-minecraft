"""Sun Scarab (Scarabée solaire): the sacred beetle of the Sun-Engine Ziggurat, about 1.5 blocks long, 1 block tall.

Silhouette idea: Khepri's beetle grown to the size of a dog. A heavy, domed scarab whose wing-cases shine iridescent
teal-green shading to violet at the edges, rimmed and inlaid with gold and lapis bands like temple jewellery. A broad
golden shield over its thorax carries an upright sun disc of hammered gold with a glowing orange heart and rays,
held up by a short horn. Its head is a flat toothed rake for digging, with curved bronze mandibles; six spurred
legs, the front pair broad shovels. It dives into the sand, travels under it and erupts beneath its prey, and in
daylight its bite burns like the sun.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

SHELL = (40, 124, 112)
SHELL_L = (96, 206, 172)
SHELL_D = (22, 70, 72)
VIOLET = (94, 64, 146)
GOLD = (216, 172, 62)
GOLD_L = (250, 222, 128)
GOLD_D = (142, 102, 32)
LAPIS = (42, 72, 164)
LAPIS_L = (88, 120, 214)
BRONZE = (150, 96, 46)
BRONZE_D = (92, 56, 26)
LEG = (36, 34, 30)
LEG_L = (74, 66, 54)
SUN = (255, 150, 30)
SUN_L = (255, 228, 120)
EYE = (255, 196, 60)


def elytron(seed=0, side=1):
    """A wing-case: iridescent teal with a lit crest, violet toward the outer edge, a gold rim along the seam and the
    outer edge, a lapis band across it, fine rows of punctures."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SHELL_D
        if face == "top":
            inner = x == (0 if side > 0 else w - 1)
            if inner:
                return GOLD_L if y % 3 == 0 else GOLD                                         # the seam
            if y in (h // 2, h // 2 + 1):
                return LAPIS_L if x % 2 else LAPIS                                            # lapis inlay band
            t = abs(x - (0 if side > 0 else w - 1)) / max(1, w - 1)
            c = mix(SHELL_L, SHELL, min(1.0, t * 1.4))
            c = mix(c, VIOLET, max(0.0, t - 0.55) * 1.6)
            if (x + y) % 2 == 0 and y % 3 == 1:
                c = mul(c, 0.82)                                                              # puncture rows
            return c
        if y == 0:
            return GOLD
        if y == h - 1:
            return GOLD_D
        c = mix(mix(SHELL, SHELL_L, 0.25), VIOLET, 0.15 + 0.3 * y / max(1, h))
        if face in ("left", "right") and (x // 2) % 2 == 0 and y == 1:
            c = SHELL_L
        return c
    return f


def gold(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        c = GOLD_L if (x + y + seed) % 6 == 0 else GOLD
        if face != "top" and y == h - 1:
            c = GOLD_D
        if K.h(x, y, seed) % 13 == 0:
            c = mix(c, BRONZE, 0.5)
        return c
    return f


def sun_disc(face, x, y, w, h):
    """The sun disc: a gold ring, rays engraved toward an orange heart."""
    if face not in ("front", "back"):
        return GOLD_D
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if r > cx + 0.6:
        return None
    if r > cx - 0.6:
        return GOLD_L if y < cy else GOLD
    if r < 1.6:
        return SUN_L
    if r < 2.6:
        return SUN
    return GOLD_D if (x + y) % 2 else GOLD


def sun_glow(face, x, y, w, h):
    if face not in ("front", "back"):
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if r < 1.6:
        return SUN_L
    if r < 2.6:
        return SUN
    return None


def leg(seed=0, spur=False):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return LEG_L
        if spur and y % 2 == 0 and face in ("front", "back"):
            return GOLD_D
        return LEG_L if x == 0 else LEG
    return f


LEGS = (("f", -4.5, -40), ("m", -0.5, 0), ("b", 3.5, 35))


def build():
    m = Model("sun_scarab", seed=1249, shadow=0.75, walk_speed=1.4, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -8, 0))
    m.part("head", "body", pivot=(0, 0, -6))
    m.part("mand_r", "head", pivot=(-2.5, 1.5, -4.5), rot=(0, 20, 0))
    m.part("mand_l", "head", pivot=(2.5, 1.5, -4.5), rot=(0, -20, 0))
    m.part("sun", "body", pivot=(0, -4.5, -3.5))
    m.part("elytra_r", "body", pivot=(-0.2, -4.5, -0.5))
    m.part("elytra_l", "body", pivot=(0.2, -4.5, -0.5))
    m.part("wing_r", "body", pivot=(-1, -4, 1), scale=(0.02, 1, 0.02))
    m.part("wing_l", "body", pivot=(1, -4, 1), scale=(0.02, 1, 0.02))
    for key, z, yaw in LEGS:
        for side, sx in (("r", -1), ("l", 1)):
            up = f"leg_{key}{side}"
            m.part(up, "body", pivot=(4.5 * sx, 1.5, z), rot=(0, yaw * -sx, 66 * -sx))
            m.part(f"shin_{key}{side}", up, pivot=(0, 5, 0), rot=(0, 0, 60 * sx))

    # ------------------------------------------------------------------ thorax: a golden shield
    m.box("body", -5, -4, -6, 10, 7, 7, gold(1))
    m.box("body", -5.5, -4.5, -6.5, 11, 2, 6, {"top": lambda f_, x, y, w, h: LAPIS if x in (2, w - 3) else (GOLD_L if y == 0 else GOLD),
                                               "*": gold(2)})
    m.box("body", -4.5, 1, -5, 9, 2, 13, {"*": BRONZE_D, "bottom": LEG})                       # the belly plates
    # the sun disc on its horn
    m.box("sun", -0.5, -2, -0.5, 1, 3, 1, gold(3))
    m.box("sun", -4.5, -10.5, 0, 9, 9, 1, sun_disc, glow={"*": sun_glow})
    m.box("sun", -1, -2.5, -1, 2, 1, 2, GOLD_D)

    # ------------------------------------------------------------------ the domed wing-cases
    for side, sx in (("r", -1), ("l", 1)):
        e = f"elytra_{side}"
        x0 = -5.5 if sx < 0 else 0
        m.box(e, x0, 0, 0, 5.5 if False else 5, 6, 12, elytron(10 + sx, sx))
        m.box(e, (-4.5 if sx < 0 else 0), -1, 1, 4, 1, 10, elytron(12 + sx, sx))               # the dome's crown
        m.box(e, (-4 if sx < 0 else 0.5), 4, 11.5, 3.5 if False else 3, 2, 1, elytron(14 + sx, sx))   # rounded tail end
        # membranous hind wings folded under the case (spread during the eruption)
        m.box(f"wing_{side}", (-10 if sx < 0 else 0), 0, 0, 10, 0, 12,
              {"*": lambda f_, x, y, w, h: (210, 190, 140, 150) if (x + y) % 5 else (120, 90, 50, 200)})

    # ------------------------------------------------------------------ head: a toothed rake, bronze mandibles
    def face(f_, x, y, w, h):
        if f_ == "front" and y == 1 and x in (1, w - 2):
            return EYE
        return gold(20)(f_, x, y, w, h)
    m.box("head", -3.5, -2.5, -4, 7, 4, 4, {"front": face, "*": gold(21)},
          glow={"front": lambda f_, x, y, w, h: EYE if y == 1 and x in (1, w - 2) else None, "*": None})
    m.box("head", -4.5, 1, -5.5, 9, 1, 3, {"front": lambda f_, x, y, w, h: GOLD_L if x % 2 == 0 else BRONZE_D, "*": BRONZE})
    for tx in (-4, -2, 0, 2, 4):
        m.box("head", tx - 0.5, 1, -6, 1, 1, 1, GOLD_L)                                           # rake teeth
    for side, sx in (("r", -1), ("l", 1)):
        mand = f"mand_{side}"
        m.box(mand, -0.5, 0, -3, 1, 1, 3, {"*": BRONZE, "top": GOLD})
        m.box(mand, (0.5 if sx < 0 else -1.5), 0, -4, 1, 1, 1, BRONZE_D)                         # the hooked tip

    # ------------------------------------------------------------------ legs: spurred, the front pair shovels
    for key, z, yaw in LEGS:
        for side, sx in (("r", -1), ("l", 1)):
            up, sh = f"leg_{key}{side}", f"shin_{key}{side}"
            m.box(up, -1, 0, -1, 2, 5, 2, leg(sum(map(ord, up)) % 5))
            m.box(sh, -0.5, 0, -0.5, 1, 6, 1, leg(sum(map(ord, sh)) % 5, spur=True))
            if key == "f":
                m.box(sh, -1.5, 3, -1, 3, 3, 1, {"*": BRONZE, "front": GOLD})                    # digging shovel
            else:
                m.box(sh, -1, 2, -0.5, 1, 1, 1, GOLD_D)                                           # spur

    _anims(m)
    return m


def _gait(a, length, swing, lift):
    half = length / 2
    for key, _z, _yaw in LEGS:
        for side, sx in (("r", -1), ("l", 1)):
            phase = (key in ("f", "b")) == (side == "r")
            s = 1 if phase else -1
            a.rot(f"leg_{key}{side}", (0, (0, swing * s, 0)), (half / 2, (0, 0, lift * sx * (s > 0))),
                  (half, (0, -swing * s, 0)), (half * 1.5, (0, 0, lift * sx * (s < 0))), (length, (0, swing * s, 0)))


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, -0.4, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (0, 10, 0)), (1.6, (-4, -8, 0)), (3.0, (0, 0, 0)))
    idle.rot("mand_r", (0, (0, 0, 0)), (0.4, (0, 18, 0)), (0.6, (0, 0, 0)), (2.0, (0, 0, 0)), (2.2, (0, 18, 0)), (2.4, (0, 0, 0)),
             (3.0, (0, 0, 0)))
    idle.rot("mand_l", (0, (0, 0, 0)), (0.4, (0, -18, 0)), (0.6, (0, 0, 0)), (2.0, (0, 0, 0)), (2.2, (0, -18, 0)), (2.4, (0, 0, 0)),
             (3.0, (0, 0, 0)))
    idle.rot("sun", (0, (0, 0, 0)), (1.5, (0, 0, 4)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 0.7)
    _gait(walk, 0.7, 22, 16)
    walk.pos("body", (0, (0, 0, 0)), (0.175, (0, 0.5, 0)), (0.35, (0, 0, 0)), (0.525, (0, 0.5, 0)), (0.7, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, 3)), (0.35, (0, 0, -3)), (0.7, (0, 0, 3)))
    walk.rot("head", (0, (0, -5, 0)), (0.35, (0, 5, 0)), (0.7, (0, -5, 0)))

    # bite: the head rears back and the mandibles spread wide (0.45 s telegraph; in daylight the sun disc flares), then
    # snap shut on the prey (at 0.45 s = 9 ticks)
    a = m.anim("bite", 0.9)
    a.rot("head", (0, (0, 0, 0)), (0.4, (-24, 0, 0)), (0.45, (-26, 0, 0)), (0.52, (18, 0, 0), "linear"), (0.65, (14, 0, 0)),
          (0.9, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.4, (0, 50, 0)), (0.45, (0, 52, 0)), (0.5, (0, -16, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.4, (0, -50, 0)), (0.45, (0, -52, 0)), (0.5, (0, 16, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (-8, 0, 0)), (0.52, (8, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.4, (0, 1, 2)), (0.52, (0, -0.5, -3), "linear"), (0.65, (0, -0.5, -3)), (0.9, (0, 0, 0)))
    a.scale("sun", (0, (1, 1, 1)), (0.4, (1.2, 1.2, 1.2)), (0.55, (1, 1, 1)))
    for side, s in (("r", -1), ("l", 1)):
        a.rot(f"leg_f{side}", (0, (0, 0, 0)), (0.4, (-30, 0, 20 * s)), (0.52, (10, 0, 0)), (0.9, (0, 0, 0)))

    # burrow: digs in nose first, front shovels flinging sand, and sinks out of sight (1.0 s)
    a = m.anim("burrow", 1.0)
    a.rot("body", (0, (0, 0, 0)), (0.3, (24, 0, 0)), (1.0, (30, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, -2, 0)), (1.0, (0, -16, 0), "linear"))
    for side, s in (("r", -1), ("l", 1)):
        a.rot(f"leg_f{side}", (0, (0, 0, 0)), (0.15, (-50, 0, 0)), (0.3, (40, 0, 0)), (0.45, (-50, 0, 0)), (0.6, (40, 0, 0)),
              (0.75, (-50, 0, 0)), (0.9, (40, 0, 0)), (1.0, (0, 0, 0)))
        a.rot(f"leg_m{side}", (0, (0, 0, 0)), (0.2, (0, 30, 0)), (0.4, (0, -30, 0)), (0.6, (0, 30, 0)), (0.8, (0, -30, 0)), (1.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.0, (20, 0, 0)))

    # erupt: still under the sand while it shudders upward (0.6 s telegraph: the sand boils over it), then it bursts
    # out under the prey (at 0.6 s = 12 ticks), wing-cases flung open, and drops back on its legs
    a = m.anim("erupt", 1.5)
    a.pos("body", (0, (0, -16, 0)), (0.5, (0, -13, 0)), (0.6, (0, -12, 0)), (0.72, (0, 8, 0), "linear"), (0.9, (0, 6, 0)),
          (1.15, (0, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("body", (0, (-40, 0, 0)), (0.6, (-50, 0, 0)), (0.72, (-30, 0, 0)), (1.15, (0, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("elytra_r", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.72, (-20, -10, -60), "linear"), (1.1, (-20, -10, -60)), (1.4, (0, 0, 0)))
    a.rot("elytra_l", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.72, (-20, 10, 60), "linear"), (1.1, (-20, 10, 60)), (1.4, (0, 0, 0)))
    for side in ("r", "l"):
        a.scale(f"wing_{side}", (0, (1, 1, 1)), (0.6, (1, 1, 1)), (0.72, (1.98, 1, 1.98), "linear"), (1.1, (1.98, 1, 1.98)),
                (1.3, (1, 1, 1)))
    a.rot("wing_r", (0, (0, 0, 0)), (0.72, (0, 0, -20)), (0.8, (0, 0, 10)), (0.9, (0, 0, -20)), (1.0, (0, 0, 10)), (1.1, (0, 0, -10)),
          (1.3, (0, 0, 0)))
    a.rot("wing_l", (0, (0, 0, 0)), (0.72, (0, 0, 20)), (0.8, (0, 0, -10)), (0.9, (0, 0, 20)), (1.0, (0, 0, -10)), (1.1, (0, 0, 10)),
          (1.3, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 40, 0)), (0.72, (0, 50, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_l", (0, (0, -40, 0)), (0.72, (0, -50, 0)), (1.0, (0, 0, 0)))
    for key, _z, _yaw in LEGS:
        for side, s in (("r", -1), ("l", 1)):
            a.rot(f"leg_{key}{side}", (0, (0, 0, 0)), (0.72, (0, 0, 30 * s)), (1.0, (0, 0, -10 * s)), (1.3, (0, 0, 0)))
