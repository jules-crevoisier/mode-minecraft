"""The Hollow Cantor (Le Chantre creux): the choirmaster of the Echo Cathedral, about 3.5 blocks tall.

Silhouette idea: a gaunt hooded choirmaster whose ribcage is an organ chest, with a fan of organ pipes rising behind
his hood. A tall, thin figure in a ragged slate cassock that frays away above the floor (he seems to glide); high, bony
shoulders under a yoke of tarnished brass and a crimson stole embroidered with brass notes; the chest is an open cage
of deepslate ribs round a dark cavity in which seven small brass pipes glow with a pale echo-light. The head is a deep
pointed hood with nothing inside it but darkness and a faint ring of light, like a sound hole. Behind the shoulders, five
tarnished organ pipes fan out above the hood. Long, thin arms with long brass fingers: his RIGHT hand holds a long
conductor's baton that ends in a tuning fork (an amethyst resonator at the yoke), his LEFT hand is raised in a
conductor's gesture.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

CLOTH = (44, 46, 58)           # slate cassock
CLOTH_L = (70, 72, 88)
CLOTH_D = (28, 28, 38)
CLOTH_DD = (18, 18, 26)
STOLE = (110, 30, 42)          # crimson stole
STOLE_L = (150, 52, 60)
STOLE_D = (70, 18, 28)
TB = (156, 122, 64)            # tarnished brass
TB_L = (212, 178, 104)
TB_D = (100, 74, 36)
VERD = (78, 150, 132)          # verdigris
VERD_D = (48, 104, 92)
DS = (66, 66, 78)              # deepslate
DS_L = (98, 98, 112)
DS_D = (42, 42, 52)
DS_DD = (28, 28, 36)
VOID = (6, 6, 10)
ECHO = (150, 236, 230)         # the pale echo-light
ECHO_D = (60, 140, 150)
AMETHYST = (178, 120, 236)
AMETHYST_L = (226, 190, 255)
STEEL = (176, 178, 190)
STEEL_L = (220, 222, 232)


# ---------------------------------------------------------------- paint
def cassock(seed=0, ragged=0):
    """Slate cloth: soft vertical folds, darker toward the bottom, a frayed edge (``ragged`` texels of tatters)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return CLOTH_DD
        if face == "top":
            return CLOTH_L if (x + y) % 5 == 0 else CLOTH
        if ragged:
            cut = h - 1 - int(B.n(x // 2, 0, seed) * ragged)
            if y > cut:
                return None
            if y == cut:
                return CLOTH_DD
        fold = (x + int(B.n(x // 3, 1, seed) * 2)) % 5
        c = (CLOTH_L, CLOTH, CLOTH, CLOTH_D, CLOTH)[fold]
        c = mul(c, 1.05 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if B.n(x, y // 3, seed + 3) < 0.04:
            c = mix(c, (120, 120, 130), 0.35)                  # dust caught in the weave
        return c
    return f


def stole(seed=0):
    """A crimson stole with a brass border and little brass notes stitched down it."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STOLE_D
        if x in (0, w - 1) and w > 1:
            return TB_D
        if y == h - 1:
            return TB if x % 2 else TB_D                       # the fringe
        if w >= 2 and y % 6 == 2:
            return TB_L                                        # a note head
        if w >= 2 and y % 6 in (0, 1) and x == w - 1 - (w > 2):
            return TB                                          # its stem
        return mul(STOLE, 1.0 + (B.n(x, y, seed) - 0.5) * 0.12) if (x + y // 4) % 3 else STOLE_L
    return f


def tbrass(seed=0, verd=0.22):
    """Tarnished brass: a brass plate darkened by age with patches of verdigris."""
    base = B.plate(TB, TB_D, TB_L, seed=seed)

    def f(face, x, y, w, h):
        c = base(face, x, y, w, h)
        if c is None:
            return None
        r = B.n(x // 2, y // 2, seed + 13)
        if r < verd:
            return mix(c, VERD if B.n(x, y, seed) > 0.4 else VERD_D, 0.7)
        return c
    return f


def deepslate(seed=0, cracked=0.12):
    """Deepslate: dark blue-grey tiles with a lit top row, mortar lines and cracks."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return DS_DD
        r = B.n(x, y, seed)
        c = mul(DS, 0.9 + r * 0.22)
        if (y % 4 == 3) or ((x + (y // 4) * 2) % 5 == 4):
            c = DS_D                                           # mortar
        if B.n(x // 2, y // 2, seed + 5) < cracked and r > 0.5:
            c = DS_DD                                          # a crack
        if face == "top" or y == 0:
            c = mix(c, DS_L, 0.5)
        return c
    return f


def rib(seed=0):
    """A deepslate rib bound with a brass band at its middle."""
    ds = deepslate(seed, cracked=0.05)

    def f(face, x, y, w, h):
        if w > 4 and abs(x - w // 2) <= 0:
            return TB_L if y == 0 else TB
        return ds(face, x, y, w, h)
    return f


def cavity(face, x, y, w, h):
    """The dark inside of the organ chest, faintly lit from below."""
    k = y / max(1, h - 1)
    return mix(VOID, ECHO_D, 0.12 + 0.25 * k)


def cavity_glow(face, x, y, w, h):
    if face != "front":
        return None
    k = y / max(1, h - 1)
    return mix(VOID, ECHO_D, 0.2 + 0.4 * k) if k > 0.5 else None


def small_pipe(seed=0):
    """A small flue pipe: tarnished brass with a dark mouth near its foot, lit inside."""
    def f(face, x, y, w, h):
        if face == "top":
            return VOID
        if face == "front" and h - 4 <= y <= h - 3:
            return ECHO if y == h - 3 else ECHO_D               # the mouth
        if y == 0:
            return TB_L
        return mix(TB, VERD, 0.35) if B.n(x, y, seed) < 0.18 else (TB_L if y % 5 == 1 else TB)
    return f


def small_pipe_glow(face, x, y, w, h):
    if face == "front" and h - 4 <= y <= h - 3:
        return ECHO if y == h - 3 else ECHO_D
    if face == "top":
        return ECHO_D
    return None


def great_pipe(seed=0):
    """An organ pipe behind his shoulders: tarnished brass, a copper collar, a dark lip and a glowing mouth."""
    def f(face, x, y, w, h):
        if face == "top":
            return VOID
        if face == "bottom":
            return TB_D
        if face == "front" and 3 <= y <= 4:
            return VOID if y == 3 else ECHO_D                   # the mouth, near the top
        if face == "front" and y == 5:
            return TB_D                                         # the lip under it
        if y == 0:
            return TB_L
        if y % 7 == 6:
            return B.COPPER_D if x % 2 else B.COPPER
        k = 1.12 if x == w // 2 else (0.82 if x in (0, w - 1) else 1.0)
        c = mul(TB, k + (B.n(x, y, seed) - 0.5) * 0.08)
        if B.n(x // 2, y // 3, seed + 2) < 0.2:
            c = mix(c, VERD, 0.55)
        return c
    return f


def great_pipe_glow(face, x, y, w, h):
    if face == "front" and y == 4:
        return ECHO
    if face == "top":
        return ECHO_D
    return None


def hood(seed=0):
    """The hood's cloth: like the cassock, darker under the brim."""
    cl = cassock(seed)

    def f(face, x, y, w, h):
        return cl(face, x, y, w, h)
    return f


def hood_face(face, x, y, w, h):
    """The front of the hood: nothing inside but darkness, and a faint ring of echo-light far back (a sound hole)."""
    if face != "front":
        return cassock(70)(face, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2 + 1
    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if 2.4 <= d <= 3.3:
        return ECHO_D
    if d < 1.0:
        return mix(VOID, ECHO_D, 0.45)
    return VOID


def hood_face_glow(face, x, y, w, h):
    if face != "front":
        return None
    c = hood_face(face, x, y, w, h)
    if c == ECHO_D:
        return ECHO
    if c != VOID:
        return ECHO_D
    return None


def brim(face, x, y, w, h):
    return CLOTH_DD if face in ("bottom", "back") else (TB_D if y == 0 and face == "front" else CLOTH_D)


def bone_arm(seed=0):
    """A long thin forearm: deepslate bone sheathed in tarnished brass splints."""
    ds = deepslate(seed, cracked=0.05)

    def f(face, x, y, w, h):
        if y % 6 == 0:
            return TB_L if face != "bottom" else TB_D
        return ds(face, x, y, w, h)
    return f


def finger(face, x, y, w, h):
    return TB_L if y == 0 else (TB if y % 2 else TB_D)


def shaft(face, x, y, w, h):
    """The baton: black-lacquered wood ringed with brass every 8 texels."""
    if face in ("top", "bottom"):
        return TB_D
    if y % 8 == 0:
        return TB_L
    return mul((34, 26, 30), 1.2 if x == w // 2 else 1.0)


def tine(face, x, y, w, h):
    """A tine of the tuning fork: polished steel with a pale echo glint."""
    if face == "top":
        return STEEL_L
    return STEEL_L if (y % 5 == 1) else STEEL


def tine_glow(face, x, y, w, h):
    return ECHO_D if y % 5 == 1 and face != "bottom" else None


def resonator(face, x, y, w, h):
    return AMETHYST_L if (x + y) % 2 == 0 else AMETHYST


def bell_paint(face, x, y, w, h):
    if face == "bottom":
        return VOID
    return TB_L if y == 0 else (TB if (x + y) % 3 else TB_D)


# ---------------------------------------------------------------- build
def build():
    m = Model("hollow_cantor", seed=847, shadow=1.0, walk_speed=0.8, walk_scale=0.6, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -24, 0))
    m.part("skirt", "hips", pivot=(0, 0, 0))
    m.part("hem", "skirt", pivot=(0, 16, 0))
    m.part("chest", "hips", pivot=(0, -1, 0), rot=(4, 0, 0))
    m.part("cape", "chest", pivot=(0, -17, 3.5), rot=(6, 0, 0))
    m.part("pipes", "chest", pivot=(0, -13, 4.5), rot=(-8, 0, 0))
    m.part("neck", "chest", pivot=(0, -17, -0.5))
    m.part("head", "neck", pivot=(0, -2, 0), rot=(6, 0, 0))
    m.part("arm_r", "chest", pivot=(-7.5, -16, 0), rot=(-8, 0, 30))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-14, 0, 2))
    m.part("baton", "fore_r", pivot=(0, 14, -0.5), rot=(22, 0, -26))
    m.part("arm_l", "chest", pivot=(7.5, -16, 0), rot=(-28, 0, -14))
    m.part("fore_l", "arm_l", pivot=(0, 13, 0), rot=(-100, 0, 20))

    # ---- the cassock: two tiers and a frayed hem that never quite reaches the floor
    m.box("skirt", -5, 0, -4, 10, 9, 8, cassock(10))
    m.box("skirt", -6.5, 8, -5, 13, 9, 10, cassock(11))
    m.box("hem", -8.5, 0, -7, 17, 8, 14, cassock(12, ragged=4))
    m.box("skirt", -5.5, -1.5, -4.5, 11, 2, 9, tbrass(13, verd=0.1))                 # the cincture
    m.box("skirt", -1.5, -2, -5.2, 3, 3, 1, B.dial(rim=TB, face_c=DS_D, marks=ECHO, numerals=8))
    m.box("skirt", 4.5, 0.5, -3.5, 1, 9, 1, TB_D)                                    # a cord with a small bell
    m.box("skirt", 4, 9.5, -4, 2, 2, 2, bell_paint)

    # ---- the torso: a cage of deepslate ribs round the organ chest, brass yoke, the stole
    m.box("chest", -5, -18, 1, 10, 18, 3, deepslate(20))                              # the spine plate
    m.box("chest", -4.5, -16, -3, 9, 14, 4, cavity, glow=cavity_glow)                 # the dark organ chest
    heights = (5, 7, 9, 11, 9, 7, 5)
    for i, hgt in enumerate(heights):                                                 # seven small flue pipes
        x = -3.5 + i
        m.box("chest", x, -3 - hgt, -3.4, 1, hgt, 1, small_pipe(30 + i), glow=small_pipe_glow)
    for k, y in enumerate((-15, -12, -9, -6)):                                        # the ribs, bound in brass
        m.box("chest", -5.5, y, -4.4, 11, 1, 1, rib(40 + k))
        m.box("chest", -5.5, y, -4, 1, 1, 5, deepslate(44 + k))
        m.box("chest", 4.5, y, -4, 1, 1, 5, deepslate(48 + k))
    m.box("chest", -0.5, -17, -4.8, 1, 13, 1, tbrass(52, verd=0.3))                   # the sternum
    m.box("chest", -4.5, -3, -4, 9, 3, 5, deepslate(53))                              # the floor of the chest
    m.box("chest", -8, -19, -3.5, 16, 3, 7, tbrass(54))                               # the brass yoke
    m.box("chest", -9, -18.5, -3, 3, 4, 6, tbrass(55))                                # bony shoulder caps
    m.box("chest", 6, -18.5, -3, 3, 4, 6, tbrass(56))
    m.box("chest", -7, -17, -4.9, 2, 24, 1, stole(57))                                # the stole, both sides
    m.box("chest", 5, -17, -4.9, 2, 24, 1, stole(58))
    m.box("cape", -7, 0, 0, 14, 22, 1, cassock(60, ragged=6))                        # the tattered cape
    m.box("neck", -1.5, -2, -1.5, 3, 3, 3, deepslate(61))

    # ---- the hood: a deep, pointed cowl with nothing inside
    m.box("head", -5, -11, -5, 10, 11, 10, hood_face, glow=hood_face_glow)
    m.box("head", -5.5, -11.5, -6.5, 11, 1, 2, brim)                                  # the brim, standing proud
    m.box("head", -5.5, -11, -6.5, 1, 11, 2, brim)
    m.box("head", 4.5, -11, -6.5, 1, 11, 2, brim)
    m.box("head", -4, -14, -3, 8, 3, 7, hood(62))                                     # the point, falling back
    m.box("head", -2.5, -16, 0, 5, 2, 5, hood(63))
    m.box("head", -1.5, -17, 3, 3, 2, 3, hood(64))
    m.box("head", -6, -2, -5.5, 12, 3, 11, cassock(65))                               # the cowl round the neck

    # ---- the organ pipes fanning up behind the hood
    for i, (x, hgt, rz) in enumerate(((-9, 15, -20), (-5, 20, -9), (-1, 25, 0), (3, 20, 9), (7, 15, 20))):
        p = f"pipe_{i}"
        m.part(p, "pipes", pivot=(x + 1, 0, 1), rot=(0, 0, rz))
        m.box(p, -1.5, -hgt, -1.5, 3, hgt, 3, great_pipe(70 + i), glow=great_pipe_glow)
        m.box(p, -2, -hgt - 1, -2, 4, 1, 4, tbrass(76 + i, verd=0.3))                    # the flared cap
        m.box(p, -2, -2, -2, 4, 2, 4, tbrass(81 + i))                                    # the foot in its socket

    # ---- right arm: a thin sleeve, a long bony forearm, brass fingers round the baton-fork
    m.box("arm_r", -1.5, -1, -1.5, 3, 13, 3, cassock(90))
    m.box("fore_r", -1, 0, -1, 2, 12, 2, bone_arm(91))
    m.box("fore_r", -2, -0.5, -2, 4, 5, 4, cassock(92, ragged=2))                   # the bell cuff
    m.box("fore_r", -1.5, 11, -1.5, 3, 3, 3, tbrass(93, verd=0.1))
    for k in range(3):
        m.box("fore_r", -1.5 + k, 14, -2, 1, 4, 1, finger)
    m.box("baton", -0.5, -30, -0.5, 1, 34, 1, shaft)                                  # the baton
    m.box("baton", -1, -1, -1, 2, 5, 2, tbrass(94))                                   # its grip
    m.box("baton", -1, 4, -1, 2, 2, 2, bell_paint)                                    # a little bell for a pommel
    m.box("baton", -2.5, -32, -0.5, 5, 2, 1, tbrass(95, verd=0.1))                    # the fork's yoke
    m.box("baton", -1, -33.5, -1, 2, 2, 2, resonator, glow=resonator)                 # the amethyst resonator
    m.box("baton", -2.5, -44, -0.5, 1, 12, 1, tine, glow=tine_glow)                   # the two tines
    m.box("baton", 1.5, -44, -0.5, 1, 12, 1, tine, glow=tine_glow)

    # ---- left arm: raised, the long fingers spread in a conductor's gesture
    m.box("arm_l", -1.5, -1, -1.5, 3, 13, 3, cassock(100))
    m.box("fore_l", -1, 0, -1, 2, 12, 2, bone_arm(101))
    m.box("fore_l", -2, -0.5, -2, 4, 5, 4, cassock(102, ragged=2))
    m.box("fore_l", -1.5, 11, -1.5, 3, 2, 3, tbrass(103, verd=0.1))
    for k, (x, z) in enumerate(((-1.5, -1.5), (-0.5, -1.8), (0.5, -1.5), (1.2, -0.6))):
        m.box("fore_l", x, 13, z, 1, 5 - (k == 3) * 2, 1, finger)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("hips", (0, (0, 0, 0)), (2.0, (0, 1.0, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.3, (4, 12, 3)), (2.7, (-2, -10, -2)), (4.0, (0, 0, 0)))
    idle.scale("pipes", (0, (1, 1, 1)), (2.0, (1.04, 1.05, 1.04)), (4.0, (1, 1, 1)))
    idle.rot("cape", (0, (0, 0, 0)), (2.0, (6, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("hem", (0, (0, 0, 0)), (2.0, (3, 4, 0)), (4.0, (0, 0, 0)))
    idle.rot("fore_l", (0, (0, 0, 0)), (1.0, (-8, 0, 6)), (2.0, (4, 0, -2)), (3.0, (-8, 0, 6)), (4.0, (0, 0, 0)))
    idle.rot("baton", (0, (0, 0, 0)), (2.0, (-4, 0, 2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.4)
    walk.pos("hips", (0, (0, 0, 0)), (0.6, (0, 0.8, 0)), (1.2, (0, 0, 0)), (1.8, (0, 0.8, 0)), (2.4, (0, 0, 0)))
    walk.rot("skirt", (0, (6, 4, 0)), (1.2, (6, -4, 0)), (2.4, (6, 4, 0)))
    walk.rot("hem", (0, (10, -3, 0)), (1.2, (10, 3, 0)), (2.4, (10, -3, 0)))
    walk.rot("cape", (0, (14, 0, 0)), (1.2, (18, 0, 0)), (2.4, (14, 0, 0)))
    walk.rot("chest", (0, (4, -4, 0)), (1.2, (4, 4, 0)), (2.4, (4, -4, 0)))
    walk.rot("arm_r", (0, (-4, 0, 0)), (1.2, (4, 0, 0)), (2.4, (-4, 0, 0)))

    # baton: the upbeat (the baton raised over his right shoulder, 0.7 s = 14 ticks), the downbeat sweep at 0.7 s, the
    # backswing half a second later (1.2 s)
    a = m.anim("baton", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-150, 0, 30)), (0.7, (-156, 0, 34)), (0.78, (-60, 30, -40), "linear"),
          (1.1, (-66, 40, -46)), (1.2, (-80, -40, 40), "linear"), (1.6, (-70, -30, 30)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 25, 0)), (0.78, (8, -25, 0), "linear"), (1.1, (6, -28, 0)),
          (1.2, (6, 25, 0), "linear"), (1.6, (4, 18, 0)), (2.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-8, 10, 0)), (0.78, (6, -10, 0), "linear"), (1.2, (6, 10, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-10, 0, -30)), (1.2, (-10, 0, -40)), (2.3, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.78, (20, 0, -10)), (1.2, (20, 0, 10)), (2.3, (0, 0, 0)))

    # shriek: the hood thrown back, the pipes swelling (1.1 s = 22 ticks), then the scream thrust forward; he holds it
    # for 0.6 s
    a = m.anim("shriek", 2.4)
    a.rot("head", (0, (0, 0, 0)), (1.0, (-35, 0, 0)), (1.1, (-38, 0, 0)), (1.16, (18, 0, 0), "linear"),
          (1.7, (16, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-14, 0, 0)), (1.16, (16, 0, 0), "linear"), (1.7, (14, 0, 0)),
          (2.4, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (1.1, (1.15, 1.2, 1.15)), (1.16, (0.9, 0.85, 0.9), "linear"),
            (1.7, (0.95, 0.95, 0.95)), (2.4, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.1, (20, 0, 40)), (1.16, (-20, 0, 60), "linear"), (1.7, (-18, 0, 56)),
          (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (20, 0, -30)), (1.16, (-20, 0, -60), "linear"), (1.7, (-18, 0, -56)),
          (2.4, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.16, (10, 0, 0)), (1.3, (40, 0, 0)), (1.7, (36, 0, 0)), (2.4, (0, 0, 0)))

    # toll: the baton-fork raised overhead in both hands (0.9 s = 18 ticks), driven into the floor
    a = m.anim("toll", 2.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-170, 0, -10)), (0.9, (-176, 0, -12)), (0.96, (-50, 0, -6), "linear"),
          (1.9, (-50, 0, -6)), (2.6, (0, 0, 0)))
    a.rot("baton", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (0.96, (34, 0, 8), "linear"), (1.9, (34, 0, 8)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-160, 0, 20)), (0.9, (-166, 0, 22)), (0.96, (-60, 0, 30), "linear"),
          (1.9, (-60, 0, 30)), (2.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-12, 0, 0)), (0.96, (22, 0, 0), "linear"), (1.9, (20, 0, 0)),
          (2.6, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, 1, 0)), (0.96, (0, -3, 0), "linear"), (1.9, (0, -3, 0)), (2.6, (0, 0, 0)))

    # cadence: he leans in, the baton levelled like a lance (0.8 s = 16 ticks), and glides along the line
    a = m.anim("cadence", 2.1)
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 15, 0)), (0.8, (-8, 18, 0)), (0.86, (24, 0, 0), "linear"),
          (1.4, (22, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-70, 20, 20)), (0.8, (-74, 22, 22)), (0.86, (-95, 0, 4), "linear"),
          (1.4, (-95, 0, 4)), (2.1, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.86, (0, 0, 0)), (1.0, (18, 0, 0)), (1.4, (16, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.86, (0, 0, 0)), (1.0, (12, 0, 0)), (1.4, (10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.86, (6, 0, 0)), (1.0, (40, 0, 0)), (1.4, (36, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (20, 0, -20)), (0.86, (40, 0, -30), "linear"), (2.1, (0, 0, 0)))

    # resonance: the fork struck on the left palm (0.5 s), then raised high, ringing (1.2 s = 24 ticks), held trembling
    # while the floor resonates
    a = m.anim("resonance", 3.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-60, 0, -40)), (0.5, (-64, 0, -44)), (1.1, (-150, 0, -10)),
          (1.2, (-156, 0, -12)), (1.26, (-170, 0, -6), "linear"), (2.9, (-168, 0, -6)), (3.7, (0, 0, 0)))
    a.rot("baton", (0, (0, 0, 0)), (1.26, (0, 0, 0)), (1.5, (0, 0, 3)), (1.7, (0, 0, -3)), (1.9, (0, 0, 3)),
          (2.1, (0, 0, -3)), (2.3, (0, 0, 3)), (2.5, (0, 0, -3)), (2.9, (0, 0, 0)), (3.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-60, 0, 40)), (0.5, (-64, 0, 44)), (1.2, (-40, 0, 30)),
          (2.9, (-40, 0, 30)), (3.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-20, 0, 0)), (2.9, (-22, 0, 0)), (3.7, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (1.2, (1.1, 1.1, 1.1)), (2.9, (1.12, 1.12, 1.12)), (3.7, (1, 1, 1)))

    # silence: a long finger raised to the empty hood, "hush" (1.0 s = 20 ticks), then the hand swept out over the hall
    a = m.anim("silence", 1.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-150, 0, 40)), (1.0, (-156, 0, 44)), (1.06, (-80, 0, -60), "linear"),
          (1.4, (-80, 0, -60)), (1.9, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (1.0, (-44, 0, 0)), (1.06, (40, 0, 0), "linear"),
          (1.4, (40, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (14, 0, 0)), (1.06, (-10, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (1.06, (-6, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -2, 0)), (1.06, (0, 1, 0), "linear"), (1.9, (0, 0, 0)))

    # choir: both arms raised to his unseen choir (1.1 s = 22 ticks), the downbeat calls the echo choristers
    a = m.anim("choir", 2.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-140, 0, 40)), (0.8, (-120, 0, 30)), (1.1, (-160, 0, 50)),
          (1.16, (-90, 0, 70), "linear"), (1.6, (-90, 0, 70)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-140, 0, -40)), (0.8, (-120, 0, -30)), (1.1, (-160, 0, -50)),
          (1.16, (-90, 0, -70), "linear"), (1.6, (-90, 0, -70)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-24, 0, 0)), (1.16, (-30, 0, 0), "linear"), (1.6, (-26, 0, 0)),
          (2.2, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (1.1, (1.12, 1.15, 1.12)), (1.16, (0.95, 0.95, 0.95), "linear"),
            (2.2, (1, 1, 1)))

    # fugue: the baton traces the opening phrase (1.0 s = 20 ticks), then three downbeats 0.6 s apart, a voice each
    a = m.anim("fugue", 3.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-120, -20, 20)), (0.9, (-150, 0, 10)), (1.0, (-156, 0, 10)),
          (1.06, (-80, 0, 10), "linear"), (1.5, (-150, 0, 10)), (1.6, (-156, 0, 10)), (1.66, (-80, 0, 10), "linear"),
          (2.1, (-150, 0, 10)), (2.2, (-156, 0, 10)), (2.26, (-80, 0, 10), "linear"), (3.0, (-80, 0, 10)),
          (3.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-8, 10, 0)), (1.06, (8, -6, 0), "linear"), (1.6, (-6, 0, 0)),
          (1.66, (8, 0, 0), "linear"), (2.2, (-6, -10, 0)), (2.26, (8, 6, 0), "linear"), (3.0, (6, 0, 0)),
          (3.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-100, 0, -30)), (3.0, (-100, 0, -30)), (3.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (3.0, (-10, 0, 0)), (3.7, (0, 0, 0)))

    # organ (phase 3, guarded): he rises off the floor, arms spread, the pipes swelling (2.0 s = 40 ticks), then the
    # great chord: the cathedral's organ answers him
    a = m.anim("organ", 4.0)
    a.pos("hips", (0, (0, 0, 0)), (1.6, (0, 6, 0)), (2.0, (0, 7, 0)), (2.06, (0, 4, 0), "linear"), (3.2, (0, 3, 0)),
          (4.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-60, 0, 70)), (2.0, (-70, 0, 80)), (2.06, (-150, 0, 40), "linear"),
          (3.2, (-150, 0, 40)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-60, 0, -70)), (2.0, (-70, 0, -80)), (2.06, (-150, 0, -40), "linear"),
          (3.2, (-150, 0, -40)), (4.0, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (2.0, (1.3, 1.35, 1.3)), (2.06, (1.1, 1.0, 1.1), "linear"),
            (3.2, (1.15, 1.15, 1.15)), (4.0, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-36, 0, 0)), (2.06, (-40, 0, 0), "linear"), (3.2, (-30, 0, 0)),
          (4.0, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.6, (0, 30, 0)), (2.0, (-10, 40, 0)), (2.06, (16, 60, 0), "linear"),
          (3.2, (8, 30, 0)), (4.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (2.0, (30, 0, 0)), (2.06, (60, 0, 0), "linear"), (3.2, (40, 0, 0)), (4.0, (0, 0, 0)))

    # requiem (phase 3): he plays the air like a keyboard, arms lowered before him (1.0 s = 20 ticks), then pounds
    # out the chords for 2.5 s while rows of pipe blasts march over the floor
    a = m.anim("requiem", 4.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-80, 0, 10)), (1.0, (-86, 0, 10)), (1.06, (-50, 0, 10), "linear"),
          (1.36, (-80, 0, 10)), (1.66, (-50, 0, 10)), (1.96, (-80, 0, 10)), (2.26, (-50, 0, 10)),
          (2.56, (-80, 0, 10)), (2.86, (-50, 0, 10)), (3.5, (-60, 0, 10)), (4.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-60, 0, -10)), (1.0, (-56, 0, -10)), (1.06, (-86, 0, -10), "linear"),
          (1.36, (-50, 0, -10)), (1.66, (-80, 0, -10)), (1.96, (-50, 0, -10)), (2.26, (-80, 0, -10)),
          (2.56, (-50, 0, -10)), (2.86, (-80, 0, -10)), (3.5, (-60, 0, -10)), (4.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (3.5, (12, 0, 0)), (4.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (12, 0, 0)), (3.5, (14, 0, 0)), (4.3, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (1.0, (1.1, 1.1, 1.1)), (1.06, (1.2, 1.25, 1.2), "linear"),
            (1.66, (1.05, 1.05, 1.05)), (1.96, (1.2, 1.25, 1.2)), (2.56, (1.05, 1.05, 1.05)),
            (2.86, (1.2, 1.25, 1.2)), (3.5, (1.05, 1.05, 1.05)), (4.3, (1, 1, 1)))

    # roar (phase two): arms flung wide, the empty hood thrown back, every pipe swelling
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-40, 0, 70)), (1.6, (-44, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-60, 0, -80)), (1.6, (-64, 0, -84)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-36, 0, 0)), (1.6, (-32, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (0.5, (1.25, 1.3, 1.25)), (1.6, (1.2, 1.25, 1.2)), (2.0, (1, 1, 1)))

    # stagger: he sags, leaning on the baton, the hood lolling
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, 8)), (1.6, (32, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (30, 0, -14)), (1.6, (30, 0, -14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-30, 0, 10)), (1.6, (-30, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (20, 0, -10)), (1.6, (20, 0, -10)), (2.0, (0, 0, 0)))
    a.scale("pipes", (0, (1, 1, 1)), (0.3, (0.92, 0.9, 0.92)), (1.6, (0.92, 0.9, 0.92)), (2.0, (1, 1, 1)))
