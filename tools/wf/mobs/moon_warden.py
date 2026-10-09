"""The Moon Warden (La Gardienne de la lune): the champion of the Hollow Moon, about 3.6 blocks tall.

Silhouette idea: an elegant celestial automaton that levitates over the core platform. A slender porcelain-white body
in gold trim, a narrow waist, a glowing moonstone in the chest; a round face that is a moon-phase dial (a gold bezel
round a night sky, the moon disc inside it lit to the phase she is in); behind her head a gold halo and an orrery:
thin brass arms carrying small planets that keep turning round her head. Very long arms in porcelain and gold that end
in astrolabe blades (a pierced gold astrolabe disc at the wrist, a long pale blade under it). A flowing cloak of purpur
and starfield (a dark sky full of glowing stars) from her shoulders, a skirt of the same flaring to a hem that never
touches the ground: four end-rod thrusters under it hold her up.

Texture variants (``modelVariant()``, one per moon phase shown on the dial): full, waning, new, waxing, and the
eclipse of phase 3 (a black disc in a burning gold corona).
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

VARIANTS = ["full", "waning", "new", "waxing", "eclipse"]

PORC = (234, 230, 224)
PORC_L = (252, 250, 246)
PORC_D = (190, 184, 180)
GOLD = (226, 184, 82)
GOLD_L = (255, 228, 140)
GOLD_D = (160, 116, 42)
SKY = (30, 22, 60)
SKY_D = (14, 10, 34)
PURP = (146, 94, 170)
PURP_L = (190, 140, 210)
PURP_D = (88, 54, 116)
STAR = (255, 250, 222)
STAR_B = (176, 206, 255)
MOON = (232, 238, 255)
MOON_L = (255, 255, 255)
MOON_D = (52, 54, 86)
CORONA = (255, 186, 84)
CORONA_L = (255, 236, 170)
ROD = (248, 244, 236)
PLANETS = [(204, 150, 70), (186, 112, 58), (72, 168, 156), (150, 170, 220)]


# ---------------------------------------------------------------- paint
def porcelain(seed=0, trim_rows=(), trim_cols=()):
    """Glazed porcelain: soft white with a cool shade at the edges, gold inlay lines on the given rows/columns."""
    def f(face, x, y, w, h):
        if y in trim_rows or (face in ("front", "back") and x in trim_cols):
            return GOLD_L if (x + y) % 4 == 0 else GOLD
        if face == "bottom":
            return PORC_D
        edge = x in (0, w - 1)
        r = B.n(x, y, seed)
        base = PORC_L if r > 0.85 else (PORC if r > 0.12 else mix(PORC, PORC_D, 0.5))
        return mix(base, PORC_D, 0.45) if edge and face != "top" else base
    return f


def gold(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face == "top" or y == 0:
            return GOLD_L if r > 0.4 else GOLD
        if face == "bottom":
            return GOLD_D
        return GOLD if r > 0.25 else GOLD_D
    return f


def starfield(seed=0, hem=None, edge_gold=False):
    """A night sky: deep violet-blue, purpur along the hem rows, scattered stars (they glow, see ``stars_glow``)."""
    def f(face, x, y, w, h):
        if hem is not None and y >= h - hem:
            return GOLD if (y == h - 1 and x % 2 == 0) else (PURP_L if (x + y) % 3 == 0 else PURP)
        if edge_gold and face in ("front", "back") and x in (0, w - 1):
            return GOLD
        r = B.n(x, y, seed)
        if r > 0.94:
            return STAR if B.n(x, y, seed + 3) > 0.4 else STAR_B
        q = B.n(x // 3, y // 3, seed + 7)
        base = mix(SKY_D, PURP_D, 0.25 + 0.5 * q * (y / max(1, h)))
        return mix(base, SKY, 0.4) if r > 0.6 else base
    return f


def stars_glow(seed=0, hem=None):
    def f(face, x, y, w, h):
        if hem is not None and y >= h - hem:
            return None
        if B.n(x, y, seed) > 0.94:
            return STAR if B.n(x, y, seed + 3) > 0.4 else STAR_B
        return None
    return f


def _disc(x, y, w, h):
    cx, cy = (w - 1) / 2, (h - 1) / 2
    return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5, x - cx, y - cy


def _lit(variant, dx, dy, r):
    """Whether a point of the moon disc (radius r, offset dx, dy from its centre) is lit in this phase."""
    if variant in ("new", "eclipse"):
        return False
    if variant in (None, "full"):
        return True
    # crescents: a second disc of the same radius, shifted, covers the dark part
    shift = r * 1.1
    sx = shift if variant == "waxing" else -shift
    return ((dx + sx) ** 2 + dy ** 2) ** 0.5 > r


def dial(variant):
    """The face: a moon-phase dial (12 x 12): a gold bezel with hour ticks round a night sky, the moon disc in the
    middle lit to the phase. Round: everything outside the bezel is cut away."""
    def f(face, x, y, w, h):
        d, dx, dy = _disc(x, y, w, h)
        R = w / 2
        if face != "front":
            return (GOLD_D if face == "back" else None) if d <= R else None
        if d > R:
            return None
        if d > R - 1.2:
            return GOLD_L if (x + y) % 3 == 0 else GOLD
        mr = R - 2.6
        if d <= mr:
            if variant == "eclipse":
                return (8, 6, 14) if d < mr - 0.4 else CORONA_L
            if _lit(variant, dx, dy, mr):
                return MOON_L if (dx < -0.5 and dy < -0.5 and d < mr - 1.2) else MOON
            return MOON_D if d > mr - 0.8 else mix(MOON_D, SKY_D, 0.4)
        if variant == "eclipse" and d <= mr + 1.0:
            return CORONA
        if abs(dx) < 0.6 or abs(dy) < 0.6:
            return GOLD_D                                                              # the hour ticks
        return STAR if B.n(x, y, 17) > 0.9 else SKY
    return f


def dial_glow(variant):
    def f(face, x, y, w, h):
        if face != "front":
            return None
        d, dx, dy = _disc(x, y, w, h)
        R = w / 2
        mr = R - 2.6
        if variant == "eclipse":
            if mr - 0.4 <= d <= mr + 1.0:
                return CORONA_L if d <= mr else CORONA
            return None
        if d <= mr and _lit(variant, dx, dy, mr):
            return MOON
        if mr < d <= R - 1.2 and B.n(x, y, 17) > 0.9:
            return STAR
        return None
    return f


def moonstone(face, x, y, w, h):
    if face != "front":
        return GOLD_D
    d, dx, dy = _disc(x, y, w, h)
    if d > w / 2 - 0.6:
        return GOLD
    return MOON_L if dx < 0 and dy < 0 else STAR_B


def moonstone_glow(face, x, y, w, h):
    if face != "front":
        return None
    d, _, _ = _disc(x, y, w, h)
    return (MOON_L if d < 1.0 else STAR_B) if d <= w / 2 - 0.6 else None


def blade(face, x, y, w, h):
    """The astrolabe blade: pale moon-steel with a bright edge and a gold spine, star notches along it."""
    if face == "top":
        return GOLD
    if face == "bottom":
        return MOON
    if face in ("front", "back"):
        if x == 0:
            return GOLD
        if x == w - 1:
            return MOON_L
        return STAR_B if y % 5 == 2 else mix(MOON, PORC_D, 0.25)
    return MOON_L if face == "right" else GOLD_D


def blade_glow(face, x, y, w, h):
    if face in ("front", "back") and 0 < x < w - 1 and y % 5 == 2:
        return STAR_B
    return None


def astrolabe(face, x, y, w, h):
    """The wrist disc: a pierced gold astrolabe, a ring of star pointers round a pale centre."""
    if face not in ("front", "back"):
        return GOLD_D
    d, dx, dy = _disc(x, y, w, h)
    R = w / 2
    if d > R:
        return None
    if d > R - 1.0:
        return GOLD_L if (x + y) % 2 else GOLD
    if d < 1.0:
        return MOON_L
    return GOLD if (abs(dx) < 0.6 or abs(dy) < 0.6 or abs(abs(dx) - abs(dy)) < 0.6) else None


def astrolabe_glow(face, x, y, w, h):
    if face not in ("front", "back"):
        return None
    d, _, _ = _disc(x, y, w, h)
    return MOON_L if d < 1.0 else None


def thruster(face, x, y, w, h):
    return ROD if face != "bottom" else STAR


def planet(c):
    def f(face, x, y, w, h):
        if face == "top" or (x == 0 and y == 0):
            return mul(c, 1.25)
        return c if (x + y) % 3 else mul(c, 0.75)
    return f


# ---------------------------------------------------------------- build
def build(variant=None):
    variant = variant or "full"
    m = Model("moon_warden", seed=1213, shadow=1.0, walk_speed=0.6, walk_scale=0.5, variants=VARIANTS,
              glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -24, 0))
    m.part("skirt", "body", pivot=(0, -2, 0))
    m.part("hem", "skirt", pivot=(0, 12, 0))
    m.part("chest", "body", pivot=(0, -4, 0))
    m.part("head", "chest", pivot=(0, -16, 0))
    m.part("halo", "head", pivot=(0, -9, 3))
    m.part("orrery", "head", pivot=(0, -9, 4))
    m.part("orrery2", "head", pivot=(0, -9, 5))
    m.part("cape", "chest", pivot=(0, -15, 4), rot=(6, 0, 0))
    m.part("cape_lo", "cape", pivot=(0, 18, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_{side}", "chest", pivot=(7 * sx, -15, 0), rot=(-4, 0, 2 * -sx))
        m.part(f"fore_{side}", f"arm_{side}", pivot=(0, 10, 0), rot=(-34, 0, 0))
        m.part(f"blade_{side}", f"fore_{side}", pivot=(0, 10, 0))

    # ---- the skirt of starfield over purpur, in three flaring tiers; the hem floats 3 px over the ground
    m.box("skirt", -6, 0, -4.5, 12, 8, 9, starfield(5), glow=stars_glow(5))
    m.box("skirt", -6.5, -0.5, -5, 13, 1, 10, gold(6))                                  # the waist band
    m.box("skirt", -7.5, 6, -5.5, 15, 7, 11, starfield(7, hem=1), glow=stars_glow(7, hem=1))
    m.box("hem", -9, 0, -6.5, 18, 10, 13, starfield(9, hem=2), glow=stars_glow(9, hem=2))
    m.box("hem", -9.5, 9, -7, 19, 1, 14, gold(10))                                      # the gold hem
    for (x, z) in ((-7, -5), (6, -5), (-7, 4), (6, 4)):                                 # end-rod thrusters
        m.box("hem", x, 10, z, 1, 3, 1, thruster, glow=ROD)
        m.box("hem", x - 0.5, 10, z - 0.5, 2, 1, 2, GOLD_D)

    # ---- the slender porcelain torso: a narrow waist, a gold-trimmed bodice, the moonstone, the shoulders
    m.box("chest", -4.5, -6, -3, 9, 6, 6, porcelain(20, trim_rows=(0,)))                # the waist
    m.box("chest", -5.5, -14, -3.5, 11, 8, 7, porcelain(21, trim_rows=(7,), trim_cols=(5,)))   # the bodice
    m.box("chest", -1.5, -12, -4.1, 3, 3, 1, moonstone, glow=moonstone_glow)
    m.box("chest", -6, -16, -4, 12, 2, 8, gold(22))                                     # the collar yoke
    m.box("chest", -10, -17, -3, 5, 3, 6, porcelain(23, trim_rows=(2,)))                # the shoulders
    m.box("chest", 5, -17, -3, 5, 3, 6, porcelain(24, trim_rows=(2,)))
    m.box("chest", -9.5, -18, -2.5, 4, 1, 5, GOLD_L)                                    # gold caps on them
    m.box("chest", 5.5, -18, -2.5, 4, 1, 5, GOLD_L)
    m.box("chest", -3, -15, 3.2, 6, 10, 1, gold(25))                                    # the spine plate

    # ---- the head: a neck, the moon-phase dial with a gold drum behind it, three small crown points
    m.box("head", -1.5, -3, -1.5, 3, 3, 3, GOLD_D)
    m.box("head", -6, -15, -1.5, 12, 12, 1, dial(variant), glow=dial_glow(variant))
    m.box("head", -5, -14, -0.5, 10, 10, 2, gold(31))                                   # the drum
    m.box("head", -4, -15, -0.5, 8, 12, 2, gold(32))
    m.box("head", -6, -13, -0.5, 12, 8, 2, gold(33))
    m.box("head", -0.5, -18, -1, 1, 3, 1, GOLD_L)                                       # crown points
    m.box("head", -3.5, -17, -1, 1, 2, 1, GOLD)
    m.box("head", 2.5, -17, -1, 1, 2, 1, GOLD)

    # ---- the halo (a gold ring of r 10 round the dial, behind it) and the orrery arms with their planets
    import math
    for k in range(20):
        a = math.radians(k * 18)
        m.box("halo", round(math.cos(a) * 10 - 1, 1), round(math.sin(a) * 10 - 1, 1), 0, 2, 2, 1,
              GOLD_L if k % 5 == 0 else GOLD, glow=GOLD_L if k % 5 == 0 else None)
    m.box("orrery", 0, -0.5, 0, 14, 1, 1, GOLD_D)                                       # arm to the brass planet
    m.box("orrery", 13, -2, -1, 3, 3, 3, planet(PLANETS[0]))
    m.box("orrery", -8, -0.5, 0, 8, 1, 1, GOLD_D)                                       # arm to the copper one
    m.box("orrery", -10, -1.5, -0.5, 2, 2, 2, planet(PLANETS[1]))
    m.box("orrery2", -0.5, -12, 0, 1, 12, 1, GOLD_D)                                    # arm up to the verdigris
    m.box("orrery2", -1.5, -15, -1, 3, 3, 3, planet(PLANETS[2]))
    m.box("orrery2", -0.5, 0, 0, 1, 6, 1, GOLD_D)                                       # a short arm down
    m.box("orrery2", -1, 6, -0.5, 2, 2, 2, planet(PLANETS[3]), glow=PLANETS[3])
    m.box("orrery", -1, -1, -0.5, 2, 2, 2, GOLD_L, glow=GOLD_L)                         # the hub

    # ---- the cloak from her shoulders: starfield inside purpur edges, two panels that sway
    m.box("cape", -8, 0, 0, 16, 18, 1, starfield(40, edge_gold=True), glow=stars_glow(40))
    m.box("cape_lo", -9, 0, 0, 18, 20, 1, starfield(41, hem=2, edge_gold=True), glow=stars_glow(41, hem=2))
    m.box("cape", -8.5, -1, -0.5, 17, 2, 2, gold(42))                                   # the clasp bar

    # ---- the arms: porcelain upper arms and forearms in gold rings, astrolabes at the wrists, long blades
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, bl = f"arm_{side}", f"fore_{side}", f"blade_{side}"
        m.box(arm, -1.5, -1, -1.5, 3, 11, 3, porcelain(50 + sx))
        m.box(arm, -2, 8.5, -2, 4, 2, 4, gold(52 + sx))                                 # the elbow ring
        m.box(fore, -1.5, 0, -1.5, 3, 10, 3, porcelain(54 + sx, trim_rows=(4,)))
        m.box(bl, -3.5, -2, -0.5, 7, 7, 1, astrolabe, glow=astrolabe_glow)              # the wrist astrolabe
        m.box(bl, -1, -1, -1, 2, 2, 2, GOLD_L)                                          # its pivot
        m.box(bl, -1, 4, -0.5, 2, 15, 1, blade, glow=blade_glow)                        # the long blade
        m.box(bl, -0.5, 19, -0.5, 1, 3, 1, MOON_L)                                      # its point

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("body", (0, (0, 0, 0)), (2.0, (0, -1.2, 0)), (4.0, (0, 0, 0)))             # the hover bob
    idle.rot("hem", (0, (0, 0, 0)), (1.0, (3, 0, 2)), (2.0, (0, 0, 0)), (3.0, (-3, 0, -2)), (4.0, (0, 0, 0)))
    idle.rot("cape_lo", (0, (6, 0, 0)), (2.0, (14, 0, 3)), (4.0, (6, 0, 0)))
    idle.rot("halo", (0, (0, 0, 0)), (4.0, (0, 0, 90), "linear"))
    idle.rot("orrery", (0, (0, 0, 0)), (4.0, (0, 0, -360), "linear"))
    idle.rot("orrery2", (0, (0, 0, 0)), (4.0, (0, 0, 360), "linear"))
    idle.rot("arm_r", (0, (-4, 0, 2)), (2.0, (-8, 0, 4)), (4.0, (-4, 0, 2)))
    idle.rot("arm_l", (0, (-4, 0, -2)), (2.0, (-8, 0, -4)), (4.0, (-4, 0, -2)))

    walk = m.anim("walk", 2.0)
    walk.rot("body", (0, (8, 0, 0)), (1.0, (10, 0, 0)), (2.0, (8, 0, 0)))               # she glides, leaning in
    walk.rot("cape_lo", (0, (20, 0, 0)), (1.0, (28, 0, 0)), (2.0, (20, 0, 0)))
    walk.rot("hem", (0, (14, 0, 0)), (1.0, (18, 0, 0)), (2.0, (14, 0, 0)))

    # sweep (18 / 14 / 14): the right blade drawn back across her body (0.9 s) and swept round her front at 0.9 s;
    # she turns and the left blade sweeps back the other way at 1.3 s
    a = m.anim("sweep", 2.3)
    a.rot("arm_r", (0, (-4, 0, 2)), (0.8, (-80, -60, -20)), (0.9, (-82, -64, -20)), (0.98, (-80, 60, 40), "linear"),
          (1.5, (-70, 50, 30)), (2.3, (-4, 0, 2)))
    a.rot("arm_l", (0, (-4, 0, -2)), (0.8, (-50, 30, 10)), (1.2, (-82, 64, 20)), (1.3, (-82, 64, 20)),
          (1.38, (-80, -60, -40), "linear"), (1.8, (-70, -50, -30)), (2.3, (-4, 0, -2)))
    a.rot("fore_r", (0, (-34, 0, 0)), (0.9, (-6, 0, 0)), (2.3, (-34, 0, 0)))
    a.rot("fore_l", (0, (-34, 0, 0)), (1.3, (-6, 0, 0)), (2.3, (-34, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, -30, 0)), (0.98, (0, 24, 0), "linear"), (1.3, (0, 26, 0)),
          (1.38, (0, -22, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.98, (0, 0, 8)), (1.38, (0, 0, -8)), (2.3, (0, 0, 0)))

    # orbit (24 / 30 / 14): she spreads her arms and the orrery spins up (1.2 s); at 1.2 s the planets leave the halo
    # and fly out along their spirals while she holds the pose
    a = m.anim("orbit", 3.4)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.1, (-30, 0, 80 * sz)), (1.2, (-30, 0, 84 * sz)),
              (1.26, (-50, 0, 96 * sz), "linear"), (2.7, (-46, 0, 92 * sz)), (3.4, (-4, 0, 2 * sz)))
    a.rot("orrery", (0, (0, 0, 0)), (1.2, (0, 0, -540)), (2.7, (0, 0, -720)), (3.4, (0, 0, -720)))
    a.rot("orrery2", (0, (0, 0, 0)), (1.2, (0, 0, 360)), (2.7, (0, 0, 540)), (3.4, (0, 0, 720)))
    a.scale("orrery", (0, (1, 1, 1)), (1.2, (1.3, 1.3, 1.3)), (1.26, (0.4, 0.4, 0.4), "linear"), (2.7, (0.6, 0.6, 0.6)),
            (3.4, (1, 1, 1)))
    a.scale("orrery2", (0, (1, 1, 1)), (1.2, (1.3, 1.3, 1.3)), (1.26, (0.4, 0.4, 0.4), "linear"), (2.7, (0.6, 0.6, 0.6)),
            (3.4, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-14, 0, 0)), (2.7, (-12, 0, 0)), (3.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (1.2, (0, -3, 0)), (2.7, (0, -3, 0)), (3.4, (0, 0, 0)))

    # well (28 / 20 / 14): both blades crossed and pointed at the marked spot (1.4 s); the well opens at 1.4 s and
    # draws everything in, she closes her fists and it bursts at 2.2 s
    a = m.anim("well", 3.1)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.3, (-80, 20 * sz, -10 * sz)), (1.4, (-84, 22 * sz, -10 * sz)),
              (1.5, (-70, -10 * sz, 10 * sz)), (2.1, (-60, -30 * sz, 20 * sz)), (2.2, (-62, -32 * sz, 20 * sz)),
              (2.26, (-100, 30 * sz, -20 * sz), "linear"), (3.1, (-4, 0, 2 * sz)))
    a.rot("chest", (0, (0, 0, 0)), (1.4, (12, 0, 0)), (2.2, (-8, 0, 0)), (2.26, (16, 0, 0), "linear"), (3.1, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (1.4, (0.8, 0.8, 0.8)), (2.2, (0.6, 0.6, 0.6)), (2.26, (1.3, 1.3, 1.3), "linear"),
            (3.1, (1, 1, 1)))

    # flip (22 / 10 / 16): she raises both blades, palms up, the dial tilting back (1.1 s); at 1.1 s she flings them
    # up and gravity flips in the marked rings
    a = m.anim("flip", 2.4)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.0, (-40, 0, 30 * sz)), (1.1, (-42, 0, 30 * sz)),
              (1.16, (-170, 0, 20 * sz), "linear"), (1.8, (-160, 0, 20 * sz)), (2.4, (-4, 0, 2 * sz)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.16, (-30, 0, 0), "linear"), (2.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (1.1, (0, 2, 0)), (1.16, (0, -4, 0), "linear"), (1.8, (0, -3, 0)), (2.4, (0, 0, 0)))

    # shade (new moon, 24 / 40 / 14): she folds the cloak round her and bows, the dial dark (1.2 s); at 1.2 s she
    # throws the cloak open and her shadows dash out along their lines
    a = m.anim("shade", 3.9)
    a.rot("cape", (0, (6, 0, 0)), (1.1, (-30, 0, 0)), (1.2, (-32, 0, 0)), (1.26, (40, 0, 0), "linear"),
          (3.2, (30, 0, 0)), (3.9, (6, 0, 0)))
    a.rot("cape_lo", (0, (6, 0, 0)), (1.2, (-20, 0, 0)), (1.26, (30, 0, 0), "linear"), (3.9, (6, 0, 0)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.1, (-60, -40 * sz, -20 * sz)), (1.2, (-62, -42 * sz, -20 * sz)),
              (1.26, (-40, 50 * sz, 70 * sz), "linear"), (3.2, (-36, 46 * sz, 66 * sz)), (3.9, (-4, 0, 2 * sz)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (24, 0, 0)), (1.26, (-10, 0, 0), "linear"), (3.2, (-8, 0, 0)), (3.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (20, 0, 0)), (1.26, (-10, 0, 0), "linear"), (3.9, (0, 0, 0)))

    # radiance (full moon, 30 / 30 / 14): she rises with her arms wide, the halo swelling (1.5 s); at 1.5 s the full
    # moon flares and the radiant ring runs out over the platform
    a = m.anim("radiance", 3.7)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.4, (-20, 0, 110 * sz)), (1.5, (-22, 0, 112 * sz)),
              (1.56, (-10, 0, 70 * sz), "linear"), (3.0, (-12, 0, 74 * sz)), (3.7, (-4, 0, 2 * sz)))
    a.scale("halo", (0, (1, 1, 1)), (1.5, (1.5, 1.5, 1.5)), (1.56, (1.8, 1.8, 1.8), "linear"), (3.0, (1.3, 1.3, 1.3)),
            (3.7, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-24, 0, 0)), (1.56, (6, 0, 0), "linear"), (3.7, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (1.5, (0, -6, 0)), (1.56, (0, -4, 0), "linear"), (3.0, (0, -4, 0)), (3.7, (0, 0, 0)))

    # comet (phase 2, 30 / 10 / 18): she rises with the blades held high together (1.5 s), dives at 1.5 s and drives
    # them into the marked spot at 1.75 s
    a = m.anim("comet", 2.9)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.4, (-176, 0, -12 * sz)), (1.5, (-178, 0, -12 * sz)),
              (1.75, (-70, 0, -10 * sz), "linear"), (2.3, (-64, 0, -8 * sz)), (2.9, (-4, 0, 2 * sz)))
    a.rot("body", (0, (0, 0, 0)), (1.5, (-10, 0, 0)), (1.75, (30, 0, 0), "linear"), (2.3, (20, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("cape_lo", (0, (6, 0, 0)), (1.5, (10, 0, 0)), (1.75, (70, 0, 0), "linear"), (2.9, (6, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.5, (6, 0, 0)), (1.75, (30, 0, 0), "linear"), (2.9, (0, 0, 0)))

    # summon (phase 2, 20 / 10 / 16): one blade raised to the core, the orrery turning fast (1.0 s); the void opens
    # at 1.0 s
    a = m.anim("summon", 2.3)
    a.rot("arm_r", (0, (-4, 0, 2)), (0.9, (-170, 0, 10)), (1.0, (-172, 0, 10)), (1.06, (-150, 0, 30), "linear"),
          (1.6, (-150, 0, 30)), (2.3, (-4, 0, 2)))
    a.rot("arm_l", (0, (-4, 0, -2)), (1.0, (-30, 0, -50)), (1.6, (-30, 0, -50)), (2.3, (-4, 0, -2)))
    a.rot("orrery", (0, (0, 0, 0)), (1.0, (0, 0, -360)), (2.3, (0, 0, -360)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-26, 0, 0)), (1.6, (-24, 0, 0)), (2.3, (0, 0, 0)))

    # eclipse (phase 3, 40 / 20 / 20): she rises, arms crossed over the dial, the halo closing round her (2.0 s);
    # at 2.0 s she throws her arms open: the core dims and the dark ring runs out
    a = m.anim("eclipse", 4.0)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-4, 0, 2 * sz)), (1.9, (-120, -60 * sz, 0)), (2.0, (-122, -62 * sz, 0)),
              (2.06, (-30, 40 * sz, 100 * sz), "linear"), (3.2, (-30, 36 * sz, 96 * sz)), (4.0, (-4, 0, 2 * sz)))
    a.scale("halo", (0, (1, 1, 1)), (2.0, (0.5, 0.5, 0.5)), (2.06, (2.0, 2.0, 2.0), "linear"), (3.2, (1.4, 1.4, 1.4)),
            (4.0, (1, 1, 1)))
    a.pos("body", (0, (0, 0, 0)), (2.0, (0, -7, 0)), (2.06, (0, -3, 0), "linear"), (3.2, (0, -3, 0)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (14, 0, 0)), (2.06, (-20, 0, 0), "linear"), (4.0, (0, 0, 0)))
    a.rot("cape_lo", (0, (6, 0, 0)), (2.0, (0, 0, 0)), (2.06, (50, 0, 0), "linear"), (4.0, (6, 0, 0)))

    # roar (phase two): she flares up, arms and cloak flung wide, the orrery spinning wild
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (-4, 0, 2)), (0.5, (-40, 0, 100)), (1.6, (-44, 0, 104)), (2.0, (-4, 0, 2)))
    a.rot("arm_l", (0, (-4, 0, -2)), (0.5, (-40, 0, -100)), (1.6, (-44, 0, -104)), (2.0, (-4, 0, -2)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-26, 0, 0)), (1.6, (-24, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cape", (0, (6, 0, 0)), (0.5, (50, 0, 0)), (1.6, (46, 0, 0)), (2.0, (6, 0, 0)))
    a.rot("orrery", (0, (0, 0, 0)), (2.0, (0, 0, -720)))
    a.scale("halo", (0, (1, 1, 1)), (0.5, (1.5, 1.5, 1.5)), (1.6, (1.5, 1.5, 1.5)), (2.0, (1, 1, 1)))
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, -4, 0)), (1.6, (0, -4, 0)), (2.0, (0, 0, 0)))

    # stagger: her thrusters sputter, she sinks to the floor, the dial drooping, the halo tilting
    a = m.anim("stagger", 2.0)
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, 3, 0)), (1.6, (0, 3, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 8)), (1.6, (28, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, -14)), (1.6, (24, 0, -14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-4, 0, 2)), (0.3, (10, 0, 4)), (1.6, (10, 0, 4)), (2.0, (-4, 0, 2)))
    a.rot("arm_l", (0, (-4, 0, -2)), (0.3, (-20, 0, -30)), (1.6, (-20, 0, -30)), (2.0, (-4, 0, -2)))
    a.rot("halo", (0, (0, 0, 0)), (0.3, (30, 0, 20)), (1.6, (30, 0, 20)), (2.0, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.3, (-10, 0, 6)), (1.6, (-10, 0, 6)), (2.0, (0, 0, 0)))
