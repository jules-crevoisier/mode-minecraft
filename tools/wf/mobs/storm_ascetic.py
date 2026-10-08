"""The Storm Ascetic (L'Ascète des tempêtes): the hermit of the summit of Pilgrim's Ascent, who has meditated so long
under the great bell that the storm answers him. About 4.7 blocks tall (5.4 with his staff).

Silhouette idea: a gaunt, hunched old monk leaning on a staff taller than himself, the staff crowned by a ring of
bronze with jangling rings that crackle with lightning; a great round straw hat hangs flat on his back like a shield,
and nine prayer beads as big as fists orbit his chest. Asymmetry: his right shoulder and arm are bare, bony and
scarred by a glowing lightning-fern; the saffron robe is thrown over the left shoulder only, its huge left sleeve
streams in the wind. A long white beard and two prayer streamers blow sideways from him, as if he stood in a gale.

The same geometry gives ``storm_illusion``: his mirror images in phase 2, a paler, slightly see-through copy.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

INDIGO = (70, 78, 104)
INDIGO_D = (42, 46, 66)
SAFFRON = (214, 138, 46)
SAFFRON_D = (150, 84, 26)
SAFFRON_L = (240, 182, 92)
SKIN = (186, 146, 112)
SKIN_D = (132, 98, 72)
SKIN_L = (212, 178, 144)
BEARD = (236, 234, 226)
BEARD_D = (180, 182, 184)
WOOD = (96, 66, 42)
WOOD_D = (60, 40, 26)
WOOD_L = (132, 96, 62)
BRONZE = (184, 132, 62)
BRONZE_L = (236, 196, 120)
BRONZE_D = (110, 72, 32)
VERDI = (88, 160, 140)
STRAW = (206, 176, 104)
STRAW_D = (150, 120, 62)
STRAW_L = (232, 210, 146)
BEAD = (196, 182, 150)
BEAD_L = (232, 222, 196)
BOLT = (176, 226, 255)
BOLT_L = (246, 252, 255)
WRAP = (210, 200, 176)

# the illusion's paint: a cold, pale copy
GHOST = (170, 210, 240)


# ---------------------------------------------------------------- paint
def robe(base, dark, seed=0, hem=None):
    """Weathered cloth in wind-pressed folds, frayed and darker toward the hem."""
    def f(face, x, y, w, h):
        c = K.cloth(base, dark, seed=seed)(face, x, y, w, h)
        if face not in ("top", "bottom"):
            t = y / max(1, h - 1)
            c = mul(c, 1.03 - 0.16 * t)
            if hem is not None and y >= h - 2:
                c = hem if (x + seed) % 3 else mul(hem, 0.8)
            if y == h - 1 and K.h(x, seed) % 4 == 0:
                return None                          # frayed hem
        return c
    return f


def skin(seed=0, ribs=False):
    """Weathered old skin; ``ribs`` draws the ribs of a starved chest on the front."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        c = mul(SKIN, 1.04 - 0.1 * y / max(1, h) + ((K.h(x, y, seed) % 100) / 100 - 0.5) * 0.06)
        if ribs and face in ("front", "right") and y > 3 and y % 3 == 0 and 0 < x < w - 1:
            c = mul(c, 0.78)
        if K.h(x, y, seed + 3) % 29 == 0:
            c = mul(c, 0.86)                         # liver spots
        return c
    return f


def scar_glow(seed=0, amount=0.16):
    """The lightning-fern scar: branching lines of pale light."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if (x + y // 2 + seed) % 4 == 0 and K.h(x // 2, y, seed) % 100 < amount * 300:
            return BOLT
        if (x * 3 + y + seed) % 9 == 0 and K.h(x, y, seed + 1) % 100 < amount * 200:
            return BOLT_L
        return None
    return f


def wood(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WOOD_L if (x + y) % 2 else WOOD
        c = WOOD if (x + K.h(y // 5, seed)) % 3 else WOOD_D
        if K.h(x, y, seed) % 17 == 0:
            c = WOOD_L
        return c
    return f


def bronze(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return BRONZE_L
        if face == "bottom":
            return BRONZE_D
        c = mul(BRONZE, 1.12 - 0.3 * y / max(1, h))
        if K.h(x, y, seed) % 9 == 0:
            c = VERDI
        return c
    return f


def straw(seed=0):
    """Woven straw: concentric rings on the top, a woven pattern on the sides."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            d = int(math.hypot(x - w / 2, y - h / 2))
            c = STRAW if d % 2 else STRAW_L
            if face == "bottom":
                c = mul(c, 0.78)
            return c
        return STRAW_D if (x + y) % 2 else STRAW
    return f


def beard(seed=0):
    def f(face, x, y, w, h):
        c = K.hair(BEARD, seed)(face, x, y, w, h)
        if y > h * 0.7:
            c = mix(c, BEARD_D, 0.4)
        return c
    return f


def face_paint(f, x, y, w, h):
    """A gaunt old face: shaved crown, white brows over glowing pale eyes, deep cheeks, a hooked nose."""
    if f == "top":
        return mul(SKIN_L, 1.0 if (x + y) % 3 else 0.94)
    if f == "bottom":
        return SKIN_D
    if f != "front":
        return skin(70)(f, x, y, w, h)
    if y == 3 and 0 < x < w - 1:
        return BEARD                                  # the brows
    if y == 4 and x in (1, 2, w - 3, w - 2):
        return BOLT if x in (2, w - 3) else SKIN_D    # eyes in deep sockets
    if y == 5 and x in (1, w - 2):
        return SKIN_D                                 # hollow cheeks
    if x == w // 2 and y in (4, 5):
        return SKIN_D if y == 5 else SKIN_L           # the nose
    return skin(71)(f, x, y, w, h)


def face_glow(f, x, y, w, h):
    if f == "front" and y == 4 and x in (2, w - 3):
        return BOLT_L
    return None


def bead_paint(f, x, y, w, h):
    if f == "top":
        return BEAD_L
    if y == 0 or y == h - 1:
        return BRONZE_D                               # dark wood caps where the cord passes
    return BEAD if (x + y) % 3 else BEAD_L


def bead_glow(f, x, y, w, h):
    if f in ("front", "back", "left", "right") and x == w // 2 and y == h // 2:
        return BOLT                                   # a carved syllable lit by the storm
    return None


def ghostly(spec):
    """The illusion's version of a paint: pale storm-blue, a little see-through."""
    def conv(c):
        if c is None:
            return None
        lum = (c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11) / 255
        rgb = mix(mul(GHOST, 0.45 + 0.7 * lum), (255, 255, 255), 0.08)
        return (*rgb[:3], 196)

    def resolve(face):
        s = spec
        if isinstance(s, dict):
            if face in s:
                s = s[face]
            elif face in ("front", "back", "left", "right") and "side" in s:
                s = s["side"]
            else:
                s = s.get("*")
        return s

    def f(face, x, y, w, h):
        s = resolve(face)
        if s is None:
            return None
        return conv(s(face, x, y, w, h) if callable(s) else s)
    return f


# ---------------------------------------------------------------- model
def build():
    return _build("storm_ascetic", ghost=False)


def build_illusion():
    return _build("storm_illusion", ghost=True)


def _build(name, ghost):
    m = Model(name, seed=733, shadow=1.0 if not ghost else 0.4, walk_speed=0.8, walk_scale=0.8,
              render="entityTranslucent" if ghost else "entityCutout", glow_pulse=0.0 if not ghost else 0.12)
    if ghost:
        plain = m.box

        def box(part, x, y, z, w, h, d, paint, glow=None, grow=0.0):
            g = None
            if glow is not None:
                g = glow
            return plain(part, x, y, z, w, h, d, ghostly(paint), glow=g, grow=grow)
        m.box = box

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -36, 0))
    m.part("leg_r", "bone", pivot=(-3, -36, 0), rot=(-4, 0, 2))
    m.part("shin_r", "leg_r", pivot=(0, 17, 0), rot=(8, 0, 0))
    m.part("leg_l", "bone", pivot=(3, -36, 0), rot=(4, 0, -2))
    m.part("shin_l", "leg_l", pivot=(0, 17, 0), rot=(6, 0, 0))
    m.part("chest", "hips", pivot=(0, -2, 0), rot=(18, 0, 0))            # the hunch
    m.part("neck", "chest", pivot=(0, -20, -1), rot=(-8, 0, 0))
    m.part("head", "neck", pivot=(0, -2, -1), rot=(-14, 0, 0))
    m.part("beard", "head", pivot=(0, -1, -4), rot=(-6, 0, 0))
    m.part("beard_tip", "beard", pivot=(0, 10, 0.5), rot=(10, 0, 8))
    m.part("hat", "chest", pivot=(0, -12, 5), rot=(-74, 0, 6))            # the straw hat hung on his back
    m.part("streamer_r", "hips", pivot=(-3, -2, 4), rot=(30, 0, 18))
    m.part("streamer_l", "hips", pivot=(3, -2, 4), rot=(40, 0, -10))
    m.part("arm_r", "chest", pivot=(-7, -18, 0), rot=(-18, 0, 20))
    m.part("fore_r", "arm_r", pivot=(-0.5, 13, 0), rot=(-34, 0, 0))
    m.part("staff", "fore_r", pivot=(0, 14, -0.5), rot=(34, 0, -24))
    m.part("arm_l", "chest", pivot=(7, -18, 0), rot=(-26, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0.5, 13, 0), rot=(-60, 0, 0))
    m.part("sleeve_l", "arm_l", pivot=(2, 4, 0), rot=(10, 0, -6))
    m.part("orbit", "bone", pivot=(0, -44, 0))

    # ------------------------------------------------------------------ legs: robe over the thighs, wrapped shins, bare feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2.5, 0, -3, 5, 18, 6, robe(INDIGO, INDIGO_D, 3 + sx, hem=INDIGO_D))
        m.box(shin, -1.5, 0, -1.5, 3, 16, 3, skin(10 + sx))
        m.box(shin, -2, 2, -2, 4, 6, 4, {"*": lambda f_, x, y, w, h: WRAP if (x + y) % 3 else mul(WRAP, 0.8)})
        m.box(shin, -2, 15, -4.5, 4, 2, 6, skin(12 + sx))                 # bare, long-toed feet

    # ------------------------------------------------------------------ the robe: indigo under-robe, saffron sash
    m.box("hips", -6, -3, -3.5, 12, 6, 7, robe(INDIGO, INDIGO_D, 5))
    m.box("hips", -6.5, -1, -4, 13, 2, 8, {"*": lambda f_, x, y, w, h: SAFFRON if x % 4 else SAFFRON_D})   # belt
    m.box("hips", -5, 1, -4.2, 4, 12, 1, robe(SAFFRON, SAFFRON_D, 6))                                    # front flap
    m.box("hips", 1.5, 1, 3.6, 5, 14, 1, robe(INDIGO, INDIGO_D, 7))                                     # back flap
    m.box("streamer_r", -1, 0, 0, 2, 16, 0, {"*": robe(SAFFRON, SAFFRON_D, 8)})
    m.box("streamer_l", -1, 0, 0, 2, 12, 0, {"*": robe(WRAP, mul(WRAP, 0.75), 9)})

    # ------------------------------------------------------------------ chest: a starved, bare right side; saffron over the left
    m.box("chest", -6, -20, -3, 12, 20, 6, skin(20, ribs=True), glow=scar_glow(20, 0.06))
    m.box("chest", -0.5, -20.5, -3.5, 7, 21, 7, robe(SAFFRON, SAFFRON_D, 21), grow=0.2)           # the robe over the left half
    m.part("sash", "chest", pivot=(0, -10, 0), rot=(0, 0, 38))
    m.box("sash", -1.5, -12, -4, 3, 24, 8, robe(SAFFRON_L, SAFFRON, 22))              # its diagonal fold
    m.box("chest", -7, -21, -2.5, 4, 3, 5, skin(23))                                      # the bony right shoulder
    m.box("chest", 3, -22, -3, 5, 3, 6, robe(SAFFRON, SAFFRON_D, 24))                     # the robe's left shoulder
    # a string of small beads round the neck
    for k in range(5):
        m.box("chest", -4 + 2 * k, -18 + abs(k - 2), -3.8, 1, 1, 1, bead_paint)

    # ------------------------------------------------------------------ neck, head and beard
    m.box("neck", -1.5, -3, -1.5, 3, 4, 3, skin(30))
    m.box("head", -3.5, -8, -4, 7, 8, 7, face_paint, glow=face_glow)
    m.box("head", -0.5, -3.5, -5, 1, 2, 1, skin(31))                                      # hooked nose
    m.box("head", -4.4, -5, -1, 1, 3, 2, skin(32))                                        # big old ears
    m.box("head", 3.4, -5, -1, 1, 3, 2, skin(33))
    m.box("head", -1, -10, -0.5, 2, 2, 2, {"*": beard(34)})                               # topknot
    m.box("head", -1.5, -8.5, -1, 3, 1, 3, {"*": BRONZE})                                 # its bronze ring
    m.box("head", -4, -4.6, -4.4, 3, 1, 1, beard(35))                                     # wild brows
    m.box("head", 1, -4.6, -4.4, 3, 1, 1, beard(36))
    m.box("head", -3.6, -3, 0, 1, 4, 4, beard(37))                                        # side whiskers
    m.box("head", 2.6, -3, 0, 1, 4, 4, beard(38))
    m.box("beard", -3, 0, -1, 6, 10, 3, beard(39))
    m.box("beard", -2.5, -2, -1.4, 5, 2, 1, beard(40))                                    # moustache
    m.box("beard_tip", -2, 0, -1, 4, 9, 2, beard(41))
    m.box("beard_tip", -1, 9, -0.6, 2, 4, 1, beard(42))

    # ------------------------------------------------------------------ the great straw hat on his back (a round kasa)
    m.box("hat", -11, -1, -6, 22, 2, 12, straw(50))
    m.box("hat", -6, -1, -11, 12, 2, 22, straw(51))
    m.box("hat", -9, -1, -9, 18, 2, 18, straw(52))
    m.box("hat", -6, -3, -6, 12, 2, 12, straw(53))
    m.box("hat", -3, -5, -3, 6, 2, 6, straw(54))
    m.box("hat", -1, -6, -1, 2, 1, 2, {"*": BRONZE})                                      # the finial
    m.box("hat", -9.5, 0.5, -1, 19, 1, 2, {"*": lambda f_, x, y, w, h: SAFFRON_D})       # the tie

    # ------------------------------------------------------------------ right arm: bare, bony, the lightning scar
    m.box("arm_r", -2, -1, -2, 4, 14, 4, skin(60), glow=scar_glow(60, 0.22))
    m.box("fore_r", -1.5, 0, -1.5, 3, 13, 3, skin(61), glow=scar_glow(61, 0.18))
    m.box("fore_r", -2, 4, -2, 4, 3, 4, {"*": lambda f_, x, y, w, h: WRAP if (x + y) % 2 else mul(WRAP, 0.8)})
    m.box("fore_r", -2, 12, -2, 4, 4, 4, skin(62))                                        # gnarled fist
    # the staff: a long gnarled haft, a ring of bronze at the top with four jangling rings, crackling
    m.box("staff", -1, -66, -1, 2, 86, 2, wood(70))
    m.box("staff", -1.5, -20, -1.5, 3, 3, 3, bronze(71))                                  # collar above the grip
    m.box("staff", -1.5, 18, -1.5, 3, 3, 3, bronze(72))                                   # the ferrule
    m.box("staff", -1.5, -70, -1.5, 3, 4, 3, bronze(73))
    for k, a in enumerate(range(0, 360, 30)):
        x = 6 * math.sin(math.radians(a))
        y = -76 - 6 * math.cos(math.radians(a))
        m.box("staff", round(x * 2) / 2 - 1, round(y * 2) / 2 - 1, -1, 2, 2, 2, bronze(74 + k),
              glow={"front": BOLT, "back": BOLT} if k % 3 == 0 else None)
    m.box("staff", -0.5, -82, -0.5, 1, 12, 1, {"*": BOLT_L}, glow=BOLT_L)                  # a spike of lightning through it
    for k, (x, y) in enumerate(((-6, -75), (6, -75), (-4, -71), (4, -71))):
        m.part(f"jingle_{k}", "staff", pivot=(x, y, 0))
        m.box(f"jingle_{k}", -1, 0, -0.5, 2, 3, 1, bronze(90 + k), glow={"front": BOLT} if k < 2 else None)

    # ------------------------------------------------------------------ left arm: the huge saffron sleeve, a hand in prayer
    m.box("arm_l", -2.5, -1, -2.5, 5, 13, 5, robe(SAFFRON, SAFFRON_D, 80))
    m.box("sleeve_l", -1, 0, -3.5, 5, 19, 7, robe(SAFFRON, SAFFRON_D, 81, hem=SAFFRON_D))  # it streams below the arm
    m.box("fore_l", -1.5, 0, -1.5, 3, 12, 3, skin(82))
    m.box("fore_l", -1.5, 11, -2.5, 3, 5, 2, skin(83))                                    # open palm, fingers up
    m.box("fore_l", -2, 2, -2, 4, 3, 4, robe(SAFFRON, SAFFRON_D, 84))                     # cuff

    # ------------------------------------------------------------------ nine prayer beads orbiting his chest
    n = 9
    for k in range(n):
        a = k * 2 * math.pi / n
        m.part(f"bead_{k}", "orbit", pivot=(round(17 * math.cos(a), 1), 0, round(17 * math.sin(a), 1)))
        size = 4 if k else 5                                                              # the guru bead is bigger
        m.box(f"bead_{k}", -size / 2, -size / 2, -size / 2, size, size, size, bead_paint, glow=bead_glow)
        if k == 0:
            m.box(f"bead_{k}", -1, 2.5, -1, 2, 5, 2, {"*": SAFFRON})                      # its tassel
            m.box(f"bead_{k}", -1.5, 7, -1.5, 3, 2, 3, {"*": SAFFRON_D})

    _anims(m)
    return m


BEAD_R = 17


def spread(a, *keys):
    """The bead ring widening or tightening: keys (t, (factor, _, factor)[, interp]) move every bead radially (scaling
    the orbit part itself would squash the beads)."""
    for k in range(9):
        ang = k * 2 * math.pi / 9
        bx, bz = BEAD_R * math.cos(ang), BEAD_R * math.sin(ang)
        frames = []
        for key in keys:
            f = key[1][0]
            frames.append((key[0], ((f - 1) * bx, 0, (f - 1) * bz)) + tuple(key[2:]))
        a.pos(f"bead_{k}", *frames)


def _anims(m):
    sides = (("r", -1), ("l", 1))
    beads = [f"bead_{k}" for k in range(9)]

    idle = m.anim("idle", 6.0)
    idle.rot("orbit", (0, (0, 0, 0), "linear"), (6.0, (0, 360, 0), "linear"))
    for k, b in enumerate(beads):
        s = 1 if k % 2 else -1
        idle.pos(b, (0, (0, 0, 0)), (1.5, (0, 1.5 * s, 0)), (3.0, (0, 0, 0)), (4.5, (0, -1.5 * s, 0)), (6.0, (0, 0, 0)))
    idle.rot("chest", (0, (0, 0, 0)), (3.0, (-3, 0, 0)), (6.0, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (1.5, (4, 0, 8)), (3.0, (0, 0, 2)), (4.5, (6, 0, 10)), (6.0, (0, 0, 0)))
    idle.rot("beard_tip", (0, (0, 0, 0)), (1.5, (6, 0, 12)), (3.0, (0, 0, 4)), (4.5, (8, 0, 14)), (6.0, (0, 0, 0)))
    idle.rot("sleeve_l", (0, (0, 0, 0)), (1.0, (-10, 0, -8)), (2.5, (4, 0, 2)), (4.0, (-12, 0, -10)), (6.0, (0, 0, 0)))
    idle.rot("streamer_r", (0, (0, 0, 0)), (1.0, (14, 0, 10)), (2.5, (-6, 0, -4)), (4.0, (16, 0, 12)), (6.0, (0, 0, 0)))
    idle.rot("streamer_l", (0, (0, 0, 0)), (1.2, (12, 0, 8)), (2.8, (-4, 0, -6)), (4.4, (14, 0, 10)), (6.0, (0, 0, 0)))
    for k in range(4):
        idle.rot(f"jingle_{k}", (0, (0, 0, 0)), (0.75 + 0.2 * k, (0, 0, 14)), (2.0 + 0.2 * k, (0, 0, -12)),
                 (3.5, (0, 0, 10)), (6.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (2.0, (0, 8, 0)), (3.0, (0, 8, 0)), (4.5, (0, -6, 0)), (6.0, (0, 0, 0)))

    # walk: a long, slow, swaying pilgrim's stride, planting the staff
    walk = m.anim("walk", 1.6)
    for side, sx in sides:
        ph = 0 if side == "r" else 0.8
        walk.rot(f"leg_{side}", (0, (24 * (1 if ph else -1), 0, 0)), (0.8, (24 * (-1 if ph else 1), 0, 0)),
                 (1.6, (24 * (1 if ph else -1), 0, 0)))
        walk.rot(f"shin_{side}", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (0.8, (0, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_r", (0, (14, 0, 0)), (0.8, (-14, 0, 0)), (1.6, (14, 0, 0)))
    walk.rot("arm_l", (0, (-10, 0, 0)), (0.8, (10, 0, 0)), (1.6, (-10, 0, 0)))
    walk.rot("chest", (0, (0, 0, 3)), (0.8, (0, 0, -3)), (1.6, (0, 0, 3)))
    walk.pos("hips", (0, (0, 0, 0)), (0.4, (0, 1.0, 0)), (0.8, (0, 0, 0)), (1.2, (0, 1.0, 0)), (1.6, (0, 0, 0)))
    walk.rot("sleeve_l", (0, (-18, 0, 0)), (0.8, (-26, 0, 0)), (1.6, (-18, 0, 0)))

    # staff (combo): the staff swung back over his right shoulder (0.7 s = 14 ticks), a wide sweep to his left at
    # 0.7 s, drawn back, then a long thrust at 1.2 s (the second hit, active tick 10), recovery to 2.1 s
    a = m.anim("staff", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-96, -70, -20)), (0.7, (-98, -74, -20)), (0.78, (-80, 64, -20), "linear"),
          (0.95, (-78, 66, -20)), (1.12, (-40, 20, -10)), (1.2, (-80, 0, -6), "linear"), (1.5, (-80, 0, -6)),
          (2.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.5, (34, 0, 0)), (1.12, (34, 0, 0)), (1.2, (34, 0, 0)), (1.5, (34, 0, 0)),
          (2.1, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.5, (110, 0, 16)), (1.5, (110, 0, 16)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, -36, 0)), (0.78, (8, 38, 0), "linear"), (0.95, (8, 38, 0)),
          (1.12, (-4, -10, 0)), (1.2, (14, 4, 0), "linear"), (1.5, (14, 4, 0)), (2.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.12, (0, 0, 2)), (1.2, (0, -1, -5), "linear"), (1.5, (0, -1, -5)), (2.1, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.12, (10, 0, 0)), (1.2, (-24, 0, 0), "linear"), (1.5, (-24, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.12, (-6, 0, 0)), (1.2, (20, 0, 0), "linear"), (1.5, (20, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("orbit", (0, (0, 0, 0)), (0.7, (0, -60, 0)), (0.78, (0, 40, 0), "linear"), (2.1, (0, 0, 0)))
    a.rot("sleeve_l", (0, (0, 0, 0)), (0.7, (-30, 0, -20)), (0.78, (20, 0, 10), "linear"), (2.1, (0, 0, 0)))

    # vault (gap closer): he plants the staff and crouches (1.0 s = 20 ticks, a ring follows you), vaults over in an
    # arc for 0.5 s and lands on the ring at 1.45 s (active tick 9) with the staff driven down; recovery to 2.3 s
    a = m.anim("vault", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-150, 0, 10)), (1.0, (-152, 0, 10)), (1.25, (-170, 0, 0)),
          (1.45, (-60, 0, 0), "linear"), (1.8, (-60, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.0, (-30, 0, 16)), (1.45, (30, 0, 16), "linear"), (1.8, (30, 0, 16)), (2.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -6, 0)), (1.0, (0, -6, 0)), (1.2, (0, 4, 0)), (1.45, (0, -7, 0), "linear"),
          (1.8, (0, -7, 0)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (26, 0, 0)), (1.2, (-14, 0, 0)), (1.45, (34, 0, 0), "linear"), (1.8, (30, 0, 0)),
          (2.3, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.9, (-40, 0, 0)), (1.2, (-70, 0, 6 * sx)), (1.45, (-50, 0, 0), "linear"),
              (1.8, (-50, 0, 0)), (2.3, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.9, (60, 0, 0)), (1.2, (80, 0, 0)), (1.45, (70, 0, 0), "linear"),
              (1.8, (70, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("sleeve_l", (0, (0, 0, 0)), (1.2, (-60, 0, -30)), (1.45, (10, 0, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("beard", (0, (0, 0, 0)), (1.2, (-40, 0, 0)), (1.45, (20, 0, 0), "linear"), (2.3, (0, 0, 0)))

    # gust: the left palm thrust out (0.9 s = 18 ticks, the cone and the warning ring drawn), then held for 1.2 s while
    # the wind pours from it; recovery to 2.7 s
    a = m.anim("gust", 2.7)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-40, -40, -50)), (0.9, (-42, -42, -52)), (0.98, (-88, 0, 0), "linear"),
          (2.1, (-86, 0, 2)), (2.7, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (-30, 0, 0)), (0.98, (60, 0, 0), "linear"), (2.1, (60, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-4, 30, 0)), (0.98, (10, -20, 0), "linear"), (2.1, (10, -20, 0)), (2.7, (0, 0, 0)))
    a.rot("sleeve_l", (0, (0, 0, 0)), (0.9, (-20, 0, -10)), (0.98, (-70, 0, -10), "linear"), (2.1, (-76, 0, -14)),
          (2.7, (0, 0, 0)))
    a.rot("beard", (0, (0, 0, 0)), (0.98, (-50, 0, 0), "linear"), (2.1, (-54, 0, 6)), (2.7, (0, 0, 0)))
    a.rot("beard_tip", (0, (0, 0, 0)), (0.98, (-30, 0, 0), "linear"), (2.1, (-34, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("streamer_r", (0, (0, 0, 0)), (0.98, (-60, 0, 0), "linear"), (2.1, (-66, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("streamer_l", (0, (0, 0, 0)), (0.98, (-60, 0, 0), "linear"), (2.1, (-64, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.98, (16, 0, 0), "linear"), (2.1, (16, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.98, (-22, 0, 0), "linear"), (2.1, (-22, 0, 0)), (2.7, (0, 0, 0)))

    # lightning: the staff raised to the sky in both hands (1.1 s = 22 ticks, rings follow then lock), brought down:
    # the bolts fall at 1.1 s (a second volley at 1.8 s in phase 2); recovery to 2.8 s
    a = m.anim("lightning", 2.8)
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-170, 0, 6)), (1.1, (-172, 0, 6)), (1.16, (-140, 0, 6), "linear"),
          (1.65, (-165, 0, 6)), (1.8, (-135, 0, 6), "linear"), (2.2, (-135, 0, 6)), (2.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (34, 0, 0)), (2.2, (34, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.0, (160, 0, 16)), (2.2, (160, 0, 16)), (2.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-150, 0, -30)), (1.1, (-152, 0, -30)), (1.16, (-60, 0, -40), "linear"),
          (2.2, (-60, 0, -40)), (2.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-24, 0, 0)), (1.1, (-26, 0, 0)), (1.16, (10, 0, 0), "linear"),
          (2.2, (10, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.16, (6, 0, 0), "linear"), (2.8, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (1.0, (0, 14, 0)), (1.16, (0, 4, 0), "linear"), (2.2, (0, 4, 0)), (2.8, (0, 0, 0)))
    spread(a, (0, (1, 1, 1)), (1.0, (0.7, 1, 0.7)), (1.16, (1.3, 1, 1.3), "linear"), (2.2, (1.2, 1, 1.2)),
            (2.8, (1, 1, 1)))

    # beads: the left palm raised, the beads spin faster and lift (0.8 s = 16 ticks), then are flung out one by one in a
    # spiral (1.6 s) and drawn back; recovery to 2.9 s
    a = m.anim("beads", 2.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-150, 0, -24)), (0.8, (-152, 0, -26)), (0.88, (-90, -10, 4), "linear"),
          (2.4, (-88, -10, 4)), (2.9, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.88, (14, 0, 0), "linear"), (2.4, (14, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("orbit", (0, (0, 0, 0)), (0.8, (0, 400, 0)), (2.4, (0, 1300, 0)), (2.9, (0, 1440, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (0.8, (0, 6, 0)), (2.4, (0, 6, 0)), (2.9, (0, 0, 0)))
    spread(a, (0, (1, 1, 1)), (0.8, (0.8, 1, 0.8)), (1.0, (2.2, 1, 2.2)), (2.1, (2.2, 1, 2.2)), (2.4, (1, 1, 1)),
            (2.9, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-10, 16, 0)), (0.88, (6, -12, 0), "linear"), (2.4, (6, -12, 0)), (2.9, (0, 0, 0)))
    a.rot("sleeve_l", (0, (0, 0, 0)), (0.8, (-40, 0, -20)), (2.4, (-30, 0, -14)), (2.9, (0, 0, 0)))

    # spin (anti-hug): the staff whirled round him at waist height (0.6 s = 12 ticks, a ring at 4.5 blocks), one full
    # turn at 0.6 s; recovery to 1.5 s
    a = m.anim("spin", 1.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-80, -50, -30)), (0.6, (-82, -54, -30)), (0.66, (-82, 60, -30), "linear"),
          (0.9, (-80, 60, -30)), (1.5, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.5, (34, 0, 0)), (0.9, (34, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.5, (100, 0, 16)), (0.9, (100, 0, 16)), (1.5, (0, 0, 0)))
    a.rot("hips", (0, (0, 0, 0)), (0.5, (0, -40, 0)), (0.6, (0, -44, 0)), (0.75, (0, 316, 0), "linear"),
          (0.9, (0, 320, 0)), (1.5, (0, 360, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.5, (0, -3, 0)), (0.9, (0, -3, 0)), (1.5, (0, 0, 0)))
    a.rot("sleeve_l", (0, (0, 0, 0)), (0.6, (-20, 0, -40)), (0.75, (-40, 0, -70), "linear"), (1.5, (0, 0, 0)))

    # mirror (phase 2): he whirls in a column of wind (1.0 s = 20 ticks, three rings drawn round you), vanishes and
    # reappears with two mirror images at 1.0 s; recovery to 1.7 s
    a = m.anim("mirror", 1.7)
    a.rot("hips", (0, (0, 0, 0)), (1.0, (0, 720, 0)), (1.05, (0, 720, 0)), (1.7, (0, 720, 0)))
    a.scale("hips", (0, (1, 1, 1)), (0.9, (0.8, 1.1, 0.8)), (1.0, (0.3, 1.4, 0.3), "linear"),
            (1.08, (1.1, 0.95, 1.1), "linear"), (1.7, (1, 1, 1)))
    spread(a, (0, (1, 1, 1)), (0.9, (0.5, 1, 0.5)), (1.0, (0.2, 1, 0.2), "linear"), (1.1, (1.4, 1, 1.4), "linear"),
            (1.7, (1, 1, 1)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-100, 0, -10)), (1.08, (-60, 0, -60), "linear"), (1.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 30)), (1.08, (-40, 0, 40), "linear"), (1.7, (0, 0, 0)))

    # tempest (phase 2 combo): staff back (0.8 s = 16 ticks); sweep at 0.8 s, backhand at 1.3 s (tick 10), overhead
    # slam down a line at 1.9 s (tick 22); recovery to 3.1 s
    a = m.anim("tempest", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-96, -70, -20)), (0.8, (-98, -74, -20)), (0.88, (-80, 64, -20), "linear"),
          (1.2, (-84, 70, -20)), (1.3, (-90, -60, -20), "linear"), (1.6, (-150, -10, 0)), (1.8, (-172, 0, 0)),
          (1.9, (-50, 0, 0), "linear"), (2.4, (-50, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.6, (34, 0, 0)), (2.4, (34, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.6, (110, 0, 16)), (1.4, (110, 0, 16)), (1.8, (60, 0, 16)), (1.9, (40, 0, 16)),
          (2.4, (40, 0, 16)), (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, -36, 0)), (0.88, (8, 38, 0), "linear"), (1.2, (8, 40, 0)),
          (1.3, (6, -34, 0), "linear"), (1.8, (-22, 0, 0)), (1.9, (30, 0, 0), "linear"), (2.4, (28, 0, 0)), (3.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.8, (0, 2, 0)), (1.9, (0, -6, -3), "linear"), (2.4, (0, -6, -3)), (3.1, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.8, (0, 0, 0)), (1.9, (-34, 0, 0), "linear"), (2.4, (-34, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.8, (0, 0, 0)), (1.9, (24, 0, 0), "linear"), (2.4, (24, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("sleeve_l", (0, (0, 0, 0)), (0.8, (-30, 0, -20)), (0.88, (20, 0, 10), "linear"), (1.3, (-30, 0, -20), "linear"),
          (1.9, (30, 0, 10), "linear"), (3.1, (0, 0, 0)))

    # cyclone (phase 2): the staff whirled overhead (1.0 s = 20 ticks), the wind drawing you in for 1.0 s, then hurled
    # out as a ring at 2.0 s (active tick 20); recovery to 3.2 s
    a = m.anim("cyclone", 3.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-168, 0, 10)), (2.0, (-170, 0, 10)), (2.06, (-100, 0, 40), "linear"),
          (2.5, (-100, 0, 40)), (3.2, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.9, (-90, 0, 0)), (2.0, (-90, 0, 0)), (2.5, (-40, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.3, (0, 0, 0), "linear"), (0.9, (0, 720, 0), "linear"), (2.0, (0, 2160, 0), "linear"),
          (2.5, (0, 2520, 0)), (3.2, (0, 2520, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-60, 0, -60)), (2.0, (-60, 0, -60)), (2.06, (-90, 0, -90), "linear"),
          (2.5, (-90, 0, -90)), (3.2, (0, 0, 0)))
    a.rot("orbit", (0, (0, 0, 0)), (2.0, (0, 1080, 0)), (2.06, (0, 1100, 0), "linear"), (3.2, (0, 1440, 0)))
    spread(a, (0, (1, 1, 1)), (1.0, (0.7, 1, 0.7)), (2.0, (0.6, 1, 0.6)), (2.06, (2.0, 1, 2.0), "linear"),
            (2.6, (1.2, 1, 1.2)), (3.2, (1, 1, 1)))
    a.rot("beard", (0, (0, 0, 0)), (1.0, (-20, 0, 30)), (2.0, (-20, 0, -30)), (2.06, (-60, 0, 0), "linear"), (3.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (2.0, (-14, 0, 0)), (2.06, (10, 0, 0), "linear"), (3.2, (0, 0, 0)))

    # toll (phase 3, invulnerable): he kneels and lifts the staff to the bell (2.0 s = 40 ticks), strikes the floor:
    # the great bell answers at 2.0 s; recovery to 3.2 s
    a = m.anim("toll", 3.2)
    a.pos("hips", (0, (0, 0, 0)), (0.6, (0, -12, 0)), (2.0, (0, -12, 0)), (2.08, (0, -14, 0), "linear"), (2.6, (0, -12, 0)),
          (3.2, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.6, (-80 if side == "r" else -10, 0, 0)), (2.6, (-80 if side == "r" else -10, 0, 0)),
              (3.2, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.6, (80 if side == "r" else 90, 0, 0)), (2.6, (80 if side == "r" else 90, 0, 0)),
              (3.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.8, (-172, 0, 4)), (2.0, (-176, 0, 4)), (2.08, (-70, 0, 4), "linear"),
          (2.6, (-70, 0, 4)), (3.2, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.8, (160, 0, 16)), (2.0, (160, 0, 16)), (2.08, (30, 0, 16), "linear"), (2.6, (30, 0, 16)), (3.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-70, 30, 0)), (2.6, (-70, 30, 0)), (3.2, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.8, (-60, 0, 0)), (2.6, (-60, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-36, 0, 0)), (2.0, (-40, 0, 0)), (2.08, (10, 0, 0), "linear"), (3.2, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (1.8, (0, 20, 0)), (2.08, (0, -10, 0), "linear"), (3.2, (0, 0, 0)))
    spread(a, (0, (1, 1, 1)), (1.8, (0.5, 1, 0.5)), (2.08, (2.2, 1, 2.2), "linear"), (3.2, (1, 1, 1)))

    # thunder (phase 3): the staff raised (1.0 s = 20 ticks), the bell tolls three times (at 1.0, 1.65 and 2.3 s:
    # active ticks 0, 13, 26) and a ring of thunder rolls out each time; recovery to 3.8 s
    a = m.anim("thunder", 3.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-168, 0, 6)), (1.0, (-170, 0, 6)), (1.06, (-130, 0, 6), "linear"),
          (1.6, (-168, 0, 6)), (1.65, (-130, 0, 6), "linear"), (2.25, (-168, 0, 6)), (2.3, (-120, 0, 6), "linear"),
          (3.0, (-120, 0, 6)), (3.8, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.9, (160, 0, 16)), (3.0, (160, 0, 16)), (3.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (34, 0, 0)), (3.0, (34, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-120, 0, -60)), (3.0, (-120, 0, -60)), (3.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-34, 0, 0)), (3.0, (-30, 0, 0)), (3.8, (0, 0, 0)))
    spread(a, (0, (1, 1, 1)), (1.0, (1.6, 1, 1.6)), (1.06, (1.0, 1, 1.0), "linear"), (1.65, (1.6, 1, 1.6)),
            (1.71, (1.0, 1, 1.0), "linear"), (2.3, (1.6, 1, 1.6)), (2.36, (1.0, 1, 1.0), "linear"), (3.8, (1, 1, 1)))

    # roar (phase 2): staff and palm raised, head thrown back, the storm answers
    a = m.anim("roar", 2.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-160, 0, 20)), (2.0, (-164, 0, 22)), (2.4, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.5, (160, 0, 16)), (2.0, (160, 0, 16)), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-120, 0, -60)), (2.0, (-124, 0, -64)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (2.0, (-36, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (2.0, (-18, 0, 0)), (2.4, (0, 0, 0)))
    spread(a, (0, (1, 1, 1)), (0.5, (1.6, 1, 1.6)), (2.0, (1.6, 1, 1.6)), (2.4, (1, 1, 1)))
    a.rot("orbit", (0, (0, 0, 0)), (2.4, (0, 720, 0)))
    a.rot("beard", (0, (0, 0, 0)), (0.5, (-50, 0, 10)), (2.0, (-46, 0, -10)), (2.4, (0, 0, 0)))

    # stagger: winded, he sags onto his staff, the beads dropping
    a = m.anim("stagger", 2.4)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -7, 0)), (2.0, (0, -7, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, -8)), (2.0, (32, 0, -8)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 10)), (2.0, (26, 0, 10)), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (20, 0, -10)), (2.0, (20, 0, -10)), (2.4, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.3, (-30, 0, 0)), (2.0, (-30, 0, 0)), (2.4, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (2.0, (50, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (0.3, (0, -14, 0)), (2.0, (0, -14, 0)), (2.4, (0, 0, 0)))
