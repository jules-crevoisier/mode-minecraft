"""The Abyssal Diver (Le Scaphandrier des abysses): the champion of the Abyssal Station, about 3.8 blocks tall.

Silhouette idea: the station's chief diver fused with his armoured diving suit. A hulking brass hard-hat suit: a huge
round helmet whose front porthole glows a deep bioluminescent teal (grille bars across it, two little side ports),
sitting in a riveted brass corselet with lead chest weights; a weathered canvas suit under it, patched and salt-
stained; on his back a pair of copper pressure tanks with a gauge, ribbed air hoses snaking from them to the back of
the helmet and to the drill. His RIGHT arm ends in a giant spiral drill on a brass motor housing; his LEFT holds a
rivet gun with a drum magazine and a barbed harpoon in its barrel. Lead boots, a weight belt. Barnacles crust the
helmet, the shoulders and the boots; strands of kelp hang from the belt, the tanks and one pauldron.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

CANVAS = (146, 128, 100)        # the weathered canvas suit
CANVAS_L = (184, 166, 132)
CANVAS_D = (100, 86, 66)
SALT = (214, 210, 196)
RUBBER = (46, 44, 50)
RUBBER_L = (76, 74, 82)
LEAD = (88, 92, 102)
LEAD_L = (132, 136, 146)
LEAD_D = (56, 58, 68)
STEEL = (196, 202, 210)
STEEL_L = (240, 244, 250)
STEEL_D = (110, 116, 126)
BARN = (216, 208, 188)          # barnacles
BARN_D = (146, 136, 116)
KELP = (74, 124, 52)
KELP_L = (118, 166, 72)
KELP_D = (44, 82, 34)
GLOW = (80, 255, 214)           # bioluminescent teal
GLOW_L = (200, 255, 240)
GLOW_D = (24, 150, 140)


# ---------------------------------------------------------------- paint
def worn(base, seed, verd=0.12):
    """Sea-worn metal: verdigris patches creeping over a plate paint."""
    def f(face, x, y, w, h):
        c = base(face, x, y, w, h) if callable(base) else base
        if face != "bottom" and B.n(x // 2, y // 2, seed) < verd:
            return mix(c, B.VERD, 0.55)
        return c
    return f


def canvas(seed=0, seams=()):
    """The canvas suit: woven grain, stitched seams on ``seams`` rows, salt stains, a darker wet hem."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return CANVAS_D
        if y in seams:
            return CANVAS_D if x % 2 else mul(CANVAS_D, 1.2)
        r = B.n(x, y, seed)
        c = CANVAS_L if r > 0.86 else (CANVAS if r > 0.2 else mul(CANVAS, 0.9))
        if (x + y) % 4 == 0:
            c = mul(c, 0.94)                                                            # the weave
        if B.n(x // 3, y // 3, seed + 3) < 0.1:
            c = mix(c, SALT, 0.45)                                                      # salt stains
        if h > 4 and y >= h - 2:
            c = mul(c, 0.82)
        return c
    return f


def helmet(face, x, y, w, h):
    """The helmet's brass: bright, a lit band on top, verdigris in the hollows, a row of bolts round its middle."""
    if face == "bottom":
        return B.BRASS_D
    base = B.brass(31, grad=0.3)(face, x, y, w, h)
    if face != "top" and y == h // 2 and x % 3 == 1:
        return B.BRASS_L                                                                # bolts
    return worn(base, 33, 0.1)(face, x, y, w, h)


def porthole(face, x, y, w, h):
    """The front porthole (10 x 10): a thick brass bezel, a cross of grille bars, glowing teal glass."""
    if face != "front":
        return B.BRASS_D
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if d > 4.9:
        return None if d > 5.4 else B.BRASS_D
    if d > 3.7:
        return B.BRASS_L if y < cy else B.BRASS
    if x == w // 2 - 1 or y == h // 2 - 1:
        return B.BRASS_D                                                                # the grille
    return GLOW_L if (x, y) in ((2, 2), (2, 3), (3, 2)) else GLOW


def porthole_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if d > 3.7 or x == w // 2 - 1 or y == h // 2 - 1:
        return None
    return GLOW_L if (x, y) in ((2, 2), (2, 3), (3, 2)) else GLOW


def sideport(face, x, y, w, h):
    """A small side port (on the left/right face): bezel and dim teal glass."""
    if face not in ("left", "right"):
        return B.BRASS_D
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS
    return GLOW_D if (x + y) % 3 else GLOW


def sideport_glow(face, x, y, w, h):
    if face not in ("left", "right") or x in (0, w - 1) or y in (0, h - 1):
        return None
    return GLOW_D if (x + y) % 3 else GLOW


def corselet(face, x, y, w, h):
    """The breastplate the helmet sits in: brass, a ring of wing-nut bolts along its top edge."""
    if face == "top":
        return B.BRASS_L if (x + y) % 4 == 0 else B.BRASS
    if face == "bottom":
        return B.BRASS_DD
    if y == 1 and x % 4 == 1:
        return B.BRASS_L
    return worn(B.brass(41, grad=0.25), 43, 0.14)(face, x, y, w, h)


def lead(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return LEAD_L
        if face == "bottom":
            return LEAD_D
        r = B.n(x, y, seed)
        c = LEAD if r > 0.25 else LEAD_D
        if y == 0:
            c = LEAD_L
        return c
    return f


def boot(face, x, y, w, h):
    """The lead boots: heavy grey lead, a brass strap two rows down, darker soles."""
    if face == "bottom":
        return LEAD_D
    if face == "top":
        return LEAD_L if (x + y) % 3 else LEAD
    if y == 2:
        return B.BRASS if x % 3 else B.BRASS_L
    return lead(51)(face, x, y, w, h)


def tank(face, x, y, w, h):
    """A pressure tank: copper with brass hoops, the top domed bright."""
    if face == "top":
        return B.COPPER_L
    if face == "bottom":
        return B.COPPER_D
    if y % 5 == 4:
        return B.BRASS_L if x % 3 == 1 else B.BRASS
    k = 1.15 if x == w // 2 else (0.8 if x in (0, w - 1) else 1.0)
    return worn(mul(B.COPPER, k + (B.n(x, y, 61) - 0.5) * 0.08), 63, 0.1)(face, x, y, w, h)


def hose(face, x, y, w, h):
    """A ribbed rubber air hose."""
    return RUBBER_L if (x + y) % 2 == 0 and face != "bottom" else RUBBER


def motor(face, x, y, w, h):
    """The drill's motor housing: brass with dark cooling slots on the sides."""
    if face in ("top", "bottom"):
        return B.BRASS_D
    if 2 <= y <= h - 3 and x % 2 == 1 and 1 <= x <= w - 2:
        return B.SOOT
    return worn(B.brass(71), 73, 0.12)(face, x, y, w, h)


def drill(face, x, y, w, h):
    """A drill stage: steel with a spiral flute (diagonal stripes), a bright cutting edge."""
    if face == "top":
        return STEEL
    if face == "bottom":
        return STEEL_D
    k = (x + y) % 4
    if k == 0:
        return STEEL_D
    if k == 1:
        return STEEL_L
    return STEEL


def gun(face, x, y, w, h):
    """The rivet gun's body: dark iron with brass bands."""
    if face in ("top", "bottom"):
        return B.IRON_D
    if y % 4 == 0:
        return B.BRASS
    return B.iron(81)(face, x, y, w, h)


def drum(face, x, y, w, h):
    """The rivet drum: brass, the rivet heads showing round its face."""
    if face in ("left", "right"):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d < 1.0:
            return B.BRASS_D
        return B.COPPER_L if (x + y) % 2 == 0 and d < 2.6 else B.BRASS
    return B.brass(83)(face, x, y, w, h)


def barnacle(face, x, y, w, h):
    """A cluster of barnacles: chalky cones, a dark mouth on top."""
    if face == "top":
        return B.SOOT if (x, y) == (w // 2, h // 2) else BARN
    return BARN if (x + y) % 2 else BARN_D


def kelp(seed=0):
    """A hanging strand of kelp (a plane): a ribbon with a wavy edge, transparent round it."""
    def f(face, x, y, w, h):
        if face not in ("front", "back", "left", "right"):
            return None
        sx = (w - 1) / 2 + ((y + seed) % 6 - 2.5) * 0.35
        half = 0.8 + ((y + seed) % 5 == 0) * 0.8
        if abs(x - sx) > half:
            return None
        return KELP_L if abs(x - sx) < 0.4 else (KELP if (x + y) % 3 else KELP_D)
    return f


def belt(face, x, y, w, h):
    """The weight belt: dark leather with a brass buckle at the front."""
    if face == "front" and w // 2 - 2 <= x <= w // 2 + 1:
        return B.BRASS_L if y in (0, h - 1) or x in (w // 2 - 2, w // 2 + 1) else B.BRASS_D
    return B.MAHOGANY_D if (x + y) % 5 else B.MAHOGANY


# ---------------------------------------------------------------- build
def build():
    m = Model("abyss_diver", seed=937, shadow=1.5, walk_speed=0.65, walk_scale=0.75, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -24, 0))
    m.part("chest", "hips", pivot=(0, -2, 0), rot=(8, 0, 0))
    m.part("head", "chest", pivot=(0, -18, 0), rot=(-6, 0, 0))
    m.part("tanks", "chest", pivot=(0, -10, 7))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5 * sx, -24, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 12, 0))
        m.part(f"arm_{side}", "chest", pivot=(12 * sx, -15, 0), rot=(-8, 0, 10 * -sx))
    m.part("fore_r", "arm_r", pivot=(0, 11, 0), rot=(-62, 0, 0))
    m.part("drill", "fore_r", pivot=(0, 10, 0))
    m.part("fore_l", "arm_l", pivot=(0, 11, 0), rot=(-56, 0, 0))
    m.part("gun", "fore_l", pivot=(0, 7, 0))

    # ---- legs: canvas, brass knee pads, lead boots with brass toe caps
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3.5, -1, -3.5, 7, 13, 7, canvas(10 + sx, seams=(5,)))
        m.box(leg, -3, 9, -4.5, 6, 3, 2, B.brass(12 + sx))                             # the knee pad
        m.box(shin, -3, 0, -3, 6, 6, 6, canvas(14 + sx))
        m.box(shin, -4.5, 5, -5.5, 9, 7, 11, boot)                                     # the lead boot
        m.box(shin, -4, 8, -6.5, 8, 4, 1, B.brass(16 + sx))                            # the toe cap
        m.box(shin, -4 if sx < 0 else 1, 4, 2, 3, 1, 3, barnacle)                      # barnacles on the heel
        m.box(shin, 2 * sx - 1, 4, -5, 2, 1, 2, barnacle)

    # ---- hips: the weight belt and its lead weights, kelp hanging from it
    m.box("hips", -10, -3, -7, 20, 5, 14, belt)
    for x in (-9, -4, 1, 6):
        m.box("hips", x, -2, -8, 3, 4, 1, lead(20 + x))                                # lead weights on the belt
    m.box("hips", -6, 2, -7.2, 3, 9, 0, kelp(1))
    m.box("hips", 4, 2, 7.2, 3, 11, 0, kelp(4))

    # ---- the chest: canvas suit, the brass corselet, lead chest weights, barnacles
    m.box("chest", -10, -18, -7, 20, 18, 14, canvas(30, seams=(8, 14)))
    m.box("chest", -8, -6, -7.6, 16, 6, 1, canvas(31))                                 # a patch over the belly
    m.box("chest", -11, -21, -8, 22, 7, 16, corselet)
    m.box("chest", -6, -15, -8.8, 12, 5, 1, lead(32))                                  # the front chest weight
    m.box("chest", -6, -15, 8, 12, 4, 1, lead(33))                                     # and the back one
    m.box("chest", 6, -22, -6, 3, 1, 3, barnacle)                                      # barnacles on the corselet
    m.box("chest", -10, -22, 2, 2, 1, 2, barnacle)

    # ---- the helmet: a big round brass ball, the glowing porthole, side ports, the air valve, barnacles
    m.box("head", -7, -14, -7, 14, 14, 14, helmet)
    m.box("head", -8, -12, -6, 16, 10, 12, helmet)                                     # round it out
    m.box("head", -6, -12, -8, 12, 10, 16, helmet)
    m.box("head", -5, -15, -5, 10, 1, 10, helmet)
    m.box("head", -5, -12, -8.6, 10, 10, 1, porthole, glow=porthole_glow)
    m.box("head", -8.6, -10, -2.5, 1, 5, 5, sideport, glow=sideport_glow)
    m.box("head", 7.6, -10, -2.5, 1, 5, 5, sideport, glow=sideport_glow)
    m.box("head", -1.5, -17, -1.5, 3, 2, 3, B.brass(35))                               # the top valve
    m.box("head", -2.5, -18, -0.5, 5, 1, 1, B.BRASS_D)                                 # its wheel
    m.box("head", -2, -9, 7.5, 4, 4, 3, B.brass(36))                                   # the air elbow at the back
    m.box("head", 2, -15, -4, 3, 2, 3, barnacle)
    m.box("head", -6, -14, 1, 2, 2, 3, barnacle)
    m.box("head", 5, -5, 5, 2, 2, 2, barnacle)

    # ---- the tanks on his back, the hoses to the helmet and to the drill, a gauge, kelp
    m.box("tanks", -8, -8, 0, 7, 17, 7, tank)
    m.box("tanks", 1, -8, 0, 7, 17, 7, tank)
    m.box("tanks", -7, -10, 1, 5, 2, 5, B.brass(45))                                   # the tank valves
    m.box("tanks", 2, -10, 1, 5, 2, 5, B.brass(46))
    m.box("tanks", -2, -4, 7, 4, 4, 1, B.gauge())
    m.box("tanks", -1, -12, 2, 2, 2, 3, hose)                                          # the hose up to the helmet
    m.box("tanks", -1, -14, 0, 2, 3, 2, hose)
    m.box("tanks", -12, -6, 2, 4, 2, 2, hose)                                          # and round to the drill arm
    m.box("tanks", -13, -6, -2, 2, 7, 2, hose)
    m.box("tanks", 3, 9, 3.6, 3, 9, 0, kelp(7))
    m.box("tanks", -6, 0, 7.2, 2, 2, 1, barnacle)

    # ---- the drill arm (right): canvas upper arm, a brass pauldron, the motor housing and the spiral drill
    m.box("arm_r", -4, -2, -4, 8, 13, 8, canvas(50, seams=(6,)))
    m.box("arm_r", -5, -4, -5, 10, 6, 10, worn(B.brass(51), 52, 0.15))                  # the pauldron
    m.box("arm_r", -3, -5, -3, 3, 1, 3, barnacle)
    m.box("arm_r", -5.2, 2, -2, 0, 10, 4, kelp(9))                                     # kelp off the pauldron
    m.box("fore_r", -4.5, 0, -4.5, 9, 10, 9, motor)
    m.box("fore_r", -5, 8, -5, 10, 2, 10, B.brass(53))                                 # the chuck collar
    m.box("drill", -5, 0, -5, 10, 5, 10, drill)
    m.box("drill", -4, 5, -4, 8, 6, 8, drill)
    m.box("drill", -3, 11, -3, 6, 6, 6, drill)
    m.box("drill", -2, 17, -2, 4, 5, 4, drill)
    m.box("drill", -1, 22, -1, 2, 4, 2, drill)
    m.box("drill", -0.5, 26, -0.5, 1, 2, 1, STEEL_L)
    m.box("drill", -5.6, 2, -1, 1, 7, 2, STEEL_D)                                      # the flute's ridges
    m.box("drill", 4.6, 6, -1, 1, 7, 2, STEEL_D)
    m.box("drill", -1, 12, -3.6, 2, 6, 1, STEEL_D)

    # ---- the gun arm (left): canvas, a pauldron, the rivet gun with its drum and the harpoon in the barrel
    m.box("arm_l", -3.5, -2, -3.5, 7, 13, 7, canvas(60, seams=(6,)))
    m.box("arm_l", -4.5, -4, -4.5, 9, 6, 9, worn(B.brass(61), 62, 0.15))
    m.box("arm_l", 1, -5, 0, 2, 1, 3, barnacle)
    m.box("fore_l", -3, 0, -3, 6, 8, 6, canvas(63))
    m.box("fore_l", -3.5, 5, -3.5, 7, 2, 7, B.MAHOGANY_D)                              # the glove's cuff
    m.box("gun", -3, 0, -3, 6, 10, 6, gun)
    m.box("gun", 3, 1, -3, 4, 6, 6, drum)                                              # the rivet drum
    m.box("gun", -1.5, 10, -1.5, 3, 6, 3, B.iron(64))                                  # the barrel
    m.box("gun", -2, 14, -2, 4, 1, 4, B.BRASS)                                         # its muzzle ring
    m.box("gun", -0.5, 16, -0.5, 1, 4, 1, STEEL)                                       # the harpoon in it
    m.box("gun", -1.5, 18, -0.5, 3, 1, 1, STEEL_L)                                     # its barbs
    m.box("gun", -1, 0, 3, 2, 3, 3, hose)                                              # the air line to the gun

    _anims(m)
    _relative(m)
    return m


def _relative(m):
    """The keys above are written as absolute poses; the engine adds them to the rest pose, so take the rest off."""
    for a in m.anims.values():
        chans = []
        for part, target, frames in a.channels:
            rest = m.parts[part].rot
            if target == "rotation" and any(rest):
                frames = [(t, tuple(v[i] - rest[i] for i in range(3)), k) for t, v, k in frames]
            chans.append((part, target, frames))
        a.channels = chans


def _spin(t0, t1, rate, start=0.0, step=0.1):
    """Linear keys turning the drill about its axis from ``t0`` to ``t1`` at ``rate`` degrees a second."""
    out = []
    t = t0
    a = start
    while t < t1 - 1e-6:
        out.append((round(t, 3), (0, round(a, 1), 0), "linear"))
        dt = min(step, t1 - t)
        t += dt
        a += rate * dt
    out.append((round(t1, 3), (0, round(a, 1), 0), "linear"))
    return out, a


def _spins(*segments):
    """Chains spin segments (t0, t1, rate) into one key list, ending on a whole turn so the rest pose matches."""
    keys = []
    a = 0.0
    for t0, t1, rate in segments:
        k, a = _spin(t0, t1, rate, a)
        keys += k if not keys else k[1:]
    if keys:
        t, rot, _ = keys[-1]
        keys[-1] = (t, (0, round(a / 360.0) * 360.0, 0), "linear")
    return keys


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, 0.6, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (-6, 0, 0)), (1.5, (-4, 5, 0)), (3.0, (-6, 0, 0)))
    idle.scale("tanks", (0, (1, 1, 1)), (1.5, (1.04, 1.02, 1.04)), (3.0, (1, 1, 1)))
    idle.rot("drill", *_spins((0, 3.0, 240)))
    idle.rot("gun", (0, (0, 0, 0)), (1.5, (-4, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (18, 0, 0)), (1.0, (-18, 0, 0)), (2.0, (18, 0, 0)))
    walk.rot("leg_l", (0, (-18, 0, 0)), (1.0, (18, 0, 0)), (2.0, (-18, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (14, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (8, 5, 3)), (1.0, (8, -5, -3)), (2.0, (8, 5, 3)))
    walk.rot("arm_l", (0, (2, 0, -10)), (1.0, (-18, 0, -10)), (2.0, (2, 0, -10)))
    walk.rot("arm_r", (0, (-18, 0, 10)), (1.0, (2, 0, 10)), (2.0, (-18, 0, 10)))

    # thrust (22 / 12 / 16): the drill drawn back spinning up, a crouch (1.1 s); he lunges down the lane (1.1-1.3 s),
    # the drill at full reach at 1.3 s
    a = m.anim("thrust", 2.5)
    a.rot("arm_r", (0, (-8, 0, 10)), (1.0, (34, 24, 24)), (1.1, (36, 24, 24)), (1.2, (-92, 0, 6), "linear"),
          (1.7, (-88, 0, 6)), (2.5, (-8, 0, 10)))
    a.rot("fore_r", (0, (-62, 0, 0)), (1.0, (-70, 0, 0)), (1.2, (0, 0, 0), "linear"), (1.7, (0, 0, 0)),
          (2.5, (-62, 0, 0)))
    a.rot("drill", *_spins((0, 0.5, 300), (0.5, 1.1, 900), (1.1, 1.8, 1500), (1.8, 2.5, 500)))
    a.rot("chest", (0, (8, 0, 0)), (1.1, (14, 26, 0)), (1.2, (30, -8, 0), "linear"), (1.7, (26, -6, 0)),
          (2.5, (8, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, -3, 0)), (1.2, (0, 0, 0), "linear"), (1.7, (0, -1, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.1, (-26, 0, 0)), (1.3, (-38, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.1, (18, 0, 0)), (1.3, (28, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.1, (36, 0, 0)), (1.3, (10, 0, 0)), (2.5, (0, 0, 0)))

    # grind (16 / 30 / 14): the drill raised level in front of him, howling up to speed (0.8 s), then held out grinding
    # (0.8-2.3 s, hits at 0.8, 1.3 and 1.8 s), shuddering
    a = m.anim("grind", 3.0)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.7, (-80, 6, 10)), (0.8, (-82, 0, 10)), (1.0, (-78, 4, 10)),
          (1.2, (-83, -4, 10)), (1.4, (-78, 4, 10)), (1.6, (-83, -4, 10)), (1.8, (-78, 4, 10)), (2.0, (-83, -4, 10)),
          (2.3, (-80, 0, 10)), (3.0, (-8, 0, 10)))
    a.rot("fore_r", (0, (-62, 0, 0)), (0.8, (-6, 0, 0)), (2.3, (-6, 0, 0)), (3.0, (-62, 0, 0)))
    a.rot("drill", *_spins((0, 0.8, 900), (0.8, 2.3, 1800), (2.3, 3.0, 600)))
    a.rot("chest", (0, (8, 0, 0)), (0.8, (18, -10, 0)), (1.1, (20, -8, 2)), (1.5, (19, -10, -2)), (1.9, (20, -8, 2)),
          (2.3, (18, -10, 0)), (3.0, (8, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-16, 0, 0)), (2.3, (-16, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (2.3, (14, 0, 0)), (3.0, (0, 0, 0)))

    # rivets (20 / 24 / 14): the rivet gun levelled (1.0 s), three volleys at 1.0, 1.5 and 2.0 s, each kicking it up
    a = m.anim("rivets", 2.9)
    a.rot("arm_l", (0, (-8, 0, -10)), (0.9, (-84, -8, -6)), (1.0, (-86, -8, -6)), (1.05, (-100, -8, -6), "linear"),
          (1.3, (-86, -8, -6)), (1.5, (-86, -8, -6)), (1.55, (-100, -8, -6), "linear"), (1.8, (-86, -8, -6)),
          (2.0, (-86, -8, -6)), (2.05, (-100, -8, -6), "linear"), (2.3, (-86, -8, -6)), (2.9, (-8, 0, -10)))
    a.rot("fore_l", (0, (-56, 0, 0)), (0.9, (-4, 0, 0)), (2.3, (-4, 0, 0)), (2.9, (-56, 0, 0)))
    a.rot("chest", (0, (8, 0, 0)), (0.9, (6, -18, 0)), (2.3, (6, -18, 0)), (2.9, (8, 0, 0)))
    a.rot("head", (0, (-6, 0, 0)), (0.9, (-4, -12, 0)), (2.3, (-4, -12, 0)), (2.9, (-6, 0, 0)))
    a.scale("gun", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.05, (1.1, 0.92, 1.1), "linear"), (1.2, (1, 1, 1)),
            (1.5, (1, 1, 1)), (1.55, (1.1, 0.92, 1.1), "linear"), (1.7, (1, 1, 1)), (2.0, (1, 1, 1)),
            (2.05, (1.1, 0.92, 1.1), "linear"), (2.2, (1, 1, 1)), (2.9, (1, 1, 1)))

    # slam (24 / 12 / 16): both arms heaved overhead, the suit swelling (1.2 s); he comes down with everything on the
    # floor at 1.2 s and stays bent over the crater until 1.8 s
    a = m.anim("slam", 2.6)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-8, 0, 10 * sz)), (1.1, (-160, 0, 18 * sz)), (1.2, (-164, 0, 16 * sz)),
              (1.26, (-40, 0, 12 * sz), "linear"), (1.8, (-40, 0, 12 * sz)), (2.6, (-8, 0, 10 * sz)))
    a.rot("fore_r", (0, (-62, 0, 0)), (1.2, (-10, 0, 0)), (1.26, (-20, 0, 0), "linear"), (2.6, (-62, 0, 0)))
    a.rot("fore_l", (0, (-56, 0, 0)), (1.2, (-10, 0, 0)), (1.26, (-20, 0, 0), "linear"), (2.6, (-56, 0, 0)))
    a.rot("chest", (0, (8, 0, 0)), (1.2, (-16, 0, 0)), (1.26, (34, 0, 0), "linear"), (1.8, (30, 0, 0)), (2.6, (8, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.2, (0, 2, 0)), (1.26, (0, -4, 0), "linear"), (1.8, (0, -4, 0)), (2.6, (0, 0, 0)))
    a.scale("tanks", (0, (1, 1, 1)), (1.2, (1.12, 1.06, 1.12)), (1.26, (0.96, 1, 0.96), "linear"), (2.6, (1, 1, 1)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"leg_{s}", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.26, (-24, 0, 6 * sz), "linear"), (1.8, (-24, 0, 6 * sz)),
              (2.6, (0, 0, 0)))
        a.rot(f"shin_{s}", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.26, (30, 0, 0), "linear"), (1.8, (30, 0, 0)),
              (2.6, (0, 0, 0)))

    # harpoon (20 / 14 / 14): the gun levelled, the drum turning (1.0 s); the harpoon fires at 1.0 s with a big kick and
    # he hauls on the line (1.1-1.7 s)
    a = m.anim("harpoon", 2.4)
    a.rot("arm_l", (0, (-8, 0, -10)), (0.9, (-86, -6, -6)), (1.0, (-88, -6, -6)), (1.06, (-112, -6, -6), "linear"),
          (1.2, (-90, -6, -6)), (1.7, (-40, 0, -10)), (2.4, (-8, 0, -10)))
    a.rot("fore_l", (0, (-56, 0, 0)), (0.9, (-4, 0, 0)), (1.2, (-4, 0, 0)), (1.7, (-70, 0, 0)), (2.4, (-56, 0, 0)))
    a.rot("chest", (0, (8, 0, 0)), (0.9, (6, -20, 0)), (1.2, (4, -20, 0)), (1.7, (-10, 10, 0)), (2.4, (8, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.7, (16, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.7, (-14, 0, 0)), (2.4, (0, 0, 0)))

    # silt (18 / 10 / 14): he hunches over his valves, the tanks swelling (0.9 s); the silt bursts out of the suit at
    # 0.9 s, his arms thrown wide
    a = m.anim("silt", 2.1)
    a.rot("chest", (0, (8, 0, 0)), (0.9, (26, 0, 0)), (0.96, (-12, 0, 0), "linear"), (1.5, (-8, 0, 0)), (2.1, (8, 0, 0)))
    a.rot("head", (0, (-6, 0, 0)), (0.9, (16, 0, 0)), (0.96, (-20, 0, 0), "linear"), (2.1, (-6, 0, 0)))
    a.scale("tanks", (0, (1, 1, 1)), (0.9, (1.18, 1.08, 1.18)), (0.96, (0.92, 0.98, 0.92), "linear"), (2.1, (1, 1, 1)))
    a.rot("arm_r", (0, (-8, 0, 10)), (0.9, (-30, 20, -10)), (0.96, (-40, 0, 60), "linear"), (1.5, (-36, 0, 56)),
          (2.1, (-8, 0, 10)))
    a.rot("arm_l", (0, (-8, 0, -10)), (0.9, (-30, -20, 10)), (0.96, (-40, 0, -60), "linear"), (1.5, (-36, 0, -56)),
          (2.1, (-8, 0, -10)))

    # call (phase 2, 20 / 10 / 16): he bangs the drill housing on his helmet three times (0.3, 0.6, 0.9 s), the signal
    # to his crew; at 1.0 s he flings the arm out
    a = m.anim("call", 2.3)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.2, (-150, 0, -30)), (0.3, (-140, 0, -40)), (0.45, (-150, 0, -26)),
          (0.6, (-140, 0, -40)), (0.75, (-150, 0, -26)), (0.9, (-140, 0, -40)), (1.0, (-100, 0, 50)),
          (1.6, (-96, 0, 50)), (2.3, (-8, 0, 10)))
    a.rot("head", (0, (-6, 0, 0)), (0.3, (0, 0, 8)), (0.6, (0, 0, 8)), (0.9, (0, 0, 8)), (1.0, (-16, 0, 0)),
          (2.3, (-6, 0, 0)))

    # groan (phase 3, 40 / 20 / 20): the drill raised high, howling (2.0 s); he drives it down at 2.0 s and leans on it
    # while the hull groans, until 3.0 s
    a = m.anim("groan", 4.0)
    a.rot("arm_r", (0, (-8, 0, 10)), (1.6, (-170, 0, 6)), (2.0, (-174, 0, 6)), (2.06, (-30, 0, 4), "linear"),
          (3.0, (-30, 0, 4)), (4.0, (-8, 0, 10)))
    a.rot("fore_r", (0, (-62, 0, 0)), (2.0, (-10, 0, 0)), (2.06, (-30, 0, 0), "linear"), (3.0, (-30, 0, 0)),
          (4.0, (-62, 0, 0)))
    a.rot("drill", *_spins((0, 2.0, 1200), (2.0, 3.0, 2000), (3.0, 4.0, 600)))
    a.rot("arm_l", (0, (-8, 0, -10)), (2.0, (-20, 0, -40)), (3.0, (-20, 0, -40)), (4.0, (-8, 0, -10)))
    a.rot("chest", (0, (8, 0, 0)), (2.0, (-14, 0, 0)), (2.06, (36, 0, 0), "linear"), (3.0, (32, 0, 0)), (4.0, (8, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (2.0, (0, 1, 0)), (2.06, (0, -5, 0), "linear"), (3.0, (0, -5, 0)), (4.0, (0, 0, 0)))
    for s in ("r", "l"):
        a.rot(f"leg_{s}", (0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.06, (-30, 0, 0), "linear"), (3.0, (-30, 0, 0)),
              (4.0, (0, 0, 0)))
        a.rot(f"shin_{s}", (0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.06, (40, 0, 0), "linear"), (3.0, (40, 0, 0)),
              (4.0, (0, 0, 0)))

    # overcharge (phase 3, 30 / 10 / 16): he stands tall, arms spread, the tanks swelling, the porthole blazing
    # (1.5 s); at 1.5 s the overload bursts out of him and he hunches forward, crackling
    a = m.anim("overcharge", 2.8)
    a.rot("arm_r", (0, (-8, 0, 10)), (1.4, (-24, 0, 64)), (1.5, (-26, 0, 66)), (1.56, (-60, 0, 14), "linear"),
          (2.8, (-8, 0, 10)))
    a.rot("arm_l", (0, (-8, 0, -10)), (1.4, (-24, 0, -64)), (1.5, (-26, 0, -66)), (1.56, (-60, 0, -14), "linear"),
          (2.8, (-8, 0, -10)))
    a.rot("head", (0, (-6, 0, 0)), (1.5, (-28, 0, 0)), (1.56, (10, 0, 0), "linear"), (2.8, (-6, 0, 0)))
    a.rot("chest", (0, (8, 0, 0)), (1.5, (-12, 0, 0)), (1.56, (24, 0, 0), "linear"), (2.8, (8, 0, 0)))
    a.scale("tanks", (0, (1, 1, 1)), (1.5, (1.2, 1.1, 1.2)), (1.56, (0.95, 1, 0.95), "linear"), (2.8, (1, 1, 1)))
    a.rot("drill", *_spins((0, 1.5, 1000), (1.5, 2.8, 1600)))

    # roar (phase two): arms wide, the helmet thrown back, the drill howling
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, (8, 0, 0)), (0.5, (-14, 0, 0)), (1.6, (-12, 0, 0)), (2.0, (8, 0, 0)))
    a.rot("head", (0, (-6, 0, 0)), (0.5, (-30, 0, 0)), (1.6, (-28, 0, 0)), (2.0, (-6, 0, 0)))
    a.rot("arm_r", (0, (-8, 0, 10)), (0.5, (-60, 0, 70)), (1.6, (-64, 0, 72)), (2.0, (-8, 0, 10)))
    a.rot("arm_l", (0, (-8, 0, -10)), (0.5, (-60, 0, -70)), (1.6, (-64, 0, -72)), (2.0, (-8, 0, -10)))
    a.rot("drill", *_spins((0, 2.0, 1440)))

    # stagger: the suit loses pressure, he sinks to one knee leaning on the drill, the helmet lolling
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (8, 0, 0)), (0.3, (30, 0, 6)), (1.6, (32, 0, 6)), (2.0, (8, 0, 0)))
    a.rot("head", (0, (-6, 0, 0)), (0.3, (20, 0, -12)), (1.6, (20, 0, -12)), (2.0, (-6, 0, 0)))
    a.rot("arm_r", (0, (-8, 0, 10)), (0.3, (-30, 0, 10)), (1.6, (-30, 0, 10)), (2.0, (-8, 0, 10)))
    a.scale("tanks", (0, (1, 1, 1)), (0.3, (0.9, 0.96, 0.9)), (1.6, (0.9, 0.96, 0.9)), (2.0, (1, 1, 1)))
