"""Rift Sentinel (Sentinelle de la faille): the floating warden of the End archives, observatories and wrecks.

Silhouette idea: a lighthouse of the void. A tall tapering obsidian obelisk floating above the ground, girdled by
pale end-stone bands and split by violet cracks, with a single violet eye under heavy stone lids in its middle. Four
tall rune tablets orbit it like the hands of a clock (tilted outward, so the outline is a wide diamond), a ring of
crystal shards turns the other way below, and a cluster of crystal spikes hangs from its foot. It charges a tether
beam (the lids open wide, the tablets lock in front of the eye) that drags its prey toward it, and blinks away when
hurt.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

OBS = (36, 28, 52)
OBS_D = (20, 14, 30)
OBS_L = (76, 62, 104)
END = (214, 212, 158)
END_D = (150, 146, 100)
END_L = (240, 238, 196)
PURPUR = (170, 120, 170)
PURPUR_D = (112, 74, 118)
PURPUR_L = (206, 160, 206)
EYE = (220, 110, 255)
EYE_L = (255, 220, 255)
EYE_D = (130, 50, 170)
RUNE = (210, 160, 255)
CRYSTAL = (232, 214, 255)
CRYSTAL_D = (170, 130, 230)


def crack(x, y, w, h, seed):
    """A thin violet crack zig-zagging down a face (one per face, its column chosen by the seed)."""
    if w < 4 or h < 4:
        return False
    cx = 1 + K.h(seed, w) % (w - 2)
    return x == cx + ((y + seed) // 3) % 2 - (1 if ((y + seed) // 3) % 4 == 3 else 0) and 1 <= y <= h - 2


def obsidian(seed=0, cracks=True, trim=None):
    """Polished obsidian: dark blocks with lighter bevels on the top edge, faint glints, darker underside, a glowing
    crack on the sides and an optional end-stone trim on the given rows (negative counts from the bottom)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return OBS_D
        if face == "top":
            if x in (0, w - 1) or y in (0, h - 1):
                return OBS_L
            return mul(OBS, 1.15)
        if trim and (y in trim or y - h in trim):
            return END_L if (y in trim and y == min(trim)) else (END if x % 3 else END_D)
        if cracks and crack(x, y, w, h, seed + K.h(face == "front", face == "left")):
            return EYE_D
        if y == 0:
            return OBS_L
        if x in (0, w - 1):
            return mul(OBS, 0.78)
        r = K.h(x, y, seed) % 100
        c = mul(OBS, 1.06 - 0.3 * y / max(1, h))
        if r < 18:
            c = OBS_D
        elif r > 95:
            c = mix(OBS_L, EYE, 0.35)                                           # a glint
        return c
    return f


def obsidian_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if crack(x, y, w, h, seed + K.h(face == "front", face == "left")):
            return EYE
        return None
    return f


def endstone(seed=0):
    """An end-stone band: pale, lit along the top, a dark groove along the bottom, small purpur studs."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return END_D
        if face == "top":
            return END_L
        if y == 0:
            return END_L
        if y == h - 1:
            return END_D
        if x % 4 == 2 and h > 2:
            return PURPUR
        return mul(END, 0.96 + (K.h(x, y, seed) % 10) / 100)
    return f


def glyph(x, y, w, h, seed):
    """A rune: a stem down the middle and two crossbars and dots placed by the seed."""
    if not (2 <= x <= w - 3 and 2 <= y <= h - 3):
        return False
    cx = w // 2
    a = 2 + seed % 3
    b = h - 4 - seed % 2
    return (x == cx) or (y == a and abs(x - cx) <= 1 + seed % 2) or (y == b and (x - cx) * (1 if seed % 2 else -1) in (0, 1, 2)) \
        or (y == (a + b) // 2 and x == cx + (2 if seed % 2 else -2))


def tablet(seed=0):
    """A purpur rune tablet: a pale end-stone frame, a sunken purpur field and a glowing glyph."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return END_D if face != "top" else END
        if x in (0, w - 1) or y in (0, h - 1):
            return END_L if y == 0 else END_D
        if glyph(x, y, w, h, seed):
            return RUNE
        if x in (1, w - 2) or y in (1, h - 2):
            return PURPUR_D
        return mul(PURPUR, 1.05 - 0.18 * y / h) if (x + y) % 4 else mul(PURPUR, 0.88)
    return f


def tablet_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("front", "back") and glyph(x, y, w, h, seed):
            return RUNE
        return None
    return f


def crystal(face, x, y, w, h):
    if face == "top":
        return CRYSTAL
    if face == "bottom":
        return CRYSTAL_D
    if x == 0:
        return mix(CRYSTAL, (255, 255, 255), 0.4)
    return CRYSTAL if (x + y) % 3 else CRYSTAL_D


def crystal_glow(face, x, y, w, h):
    return mix(CRYSTAL, EYE, 0.35) if face != "bottom" else None


def build():
    m = Model("rift_sentinel", seed=411, shadow=0.4, walk_speed=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -14, 0))
    m.part("crown", "body", pivot=(0, -11, 0))
    m.part("head", "body", pivot=(0, -6, 0))
    m.part("lid_t", "head", pivot=(0, -4, -3.5))
    m.part("lid_b", "head", pivot=(0, 4, -3.5))
    m.part("ring", "body", pivot=(0, -6, 0))
    m.part("shards", "body", pivot=(0, 4, 0))
    m.part("spike", "body", pivot=(0, 4, 0))

    # ------------------------------------------------------------------ the obelisk: foot, plinth, waist, crown
    m.box("body", -5, -2, -5, 10, 6, 10, obsidian(1, trim=(1,)), glow=obsidian_glow(1))
    m.box("body", -5.5, -3, -5.5, 11, 2, 11, endstone(2))                          # end-stone girdle
    m.box("body", -4, 4, -4, 8, 2, 8, obsidian(3, cracks=False))                    # the foot, stepping in
    m.box("body", -4.5, -10.5, -4.5, 9, 2, 9, endstone(4))                         # band over the eye
    # four corner pilasters framing the eye (the obelisk's silhouette stays square from every side)
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.box("body", 3 * sx - 1 + (0.5 if sx > 0 else -0.5), -9, 3 * sz - 1 + (0.5 if sz > 0 else -0.5), 2, 7, 2,
                  obsidian(5 + sx + sz, cracks=False))
    m.box("crown", -3.5, -5, -3.5, 7, 5, 7, obsidian(6), glow=obsidian_glow(6))
    m.box("crown", -2.5, -8, -2.5, 5, 3, 5, obsidian(7, trim=(-1,)))
    m.box("crown", -1.5, -10, -1.5, 3, 2, 3, endstone(8))
    m.box("crown", -1, -14, -1, 2, 4, 2, crystal, glow=crystal_glow)               # the lamp crystal
    m.box("crown", -0.5, -16, -0.5, 1, 2, 1, CRYSTAL, glow={"*": EYE_L})

    # ------------------------------------------------------------------ the eye (the "head": it looks at its prey)
    def eye_block(f_, x, y, w, h):
        if f_ == "front":
            cx, cy = (w - 1) / 2, (h - 1) / 2
            r = ((x - cx) ** 2 + ((y - cy) * 1.2) ** 2) ** 0.5
            if r < 0.9:
                return (24, 0, 34)                                               # the pupil (a slit)
            if abs(x - cx) < 0.6 and r < 2.6:
                return (24, 0, 34)
            if r < 2.7:
                return EYE_L if (x < cx and y < cy) else EYE                     # the iris, lit from the top left
            if r < 3.4:
                return EYE_D
            return mul(OBS_D, 0.9)
        return obsidian(9, cracks=False)(f_, x, y, w, h)

    def eye_glow(f_, x, y, w, h):
        if f_ != "front":
            return None
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = ((x - cx) ** 2 + ((y - cy) * 1.2) ** 2) ** 0.5
        if r < 0.9 or (abs(x - cx) < 0.6 and r < 2.6):
            return None
        if r < 2.7:
            return EYE_L if (x < cx and y < cy) else EYE
        if r < 3.4:
            return EYE_D
        return None
    m.box("head", -3, -3.5, -3, 6, 7, 6, eye_block, glow=eye_glow)
    # heavy stone lids above and below the eye: they slide shut to blink, wide open to fire
    m.box("lid_t", -3.5, -1.5, -2, 7, 2, 2, obsidian(10, cracks=False, trim=(0,)))
    m.box("lid_b", -3.5, -0.5, -2, 7, 2, 2, obsidian(11, cracks=False, trim=(-1,)))

    # ------------------------------------------------------------------ the crystal cluster under it
    m.box("spike", -2.5, 2, -2.5, 5, 2, 5, obsidian(12, cracks=False))
    m.box("spike", -1, 4, -1, 2, 6, 2, crystal, glow=crystal_glow)
    m.part("spike_a", "spike", pivot=(-1.5, 4, 0), rot=(0, 0, 22))
    m.box("spike_a", -0.5, 0, -0.5, 1, 4, 1, crystal, glow=crystal_glow)
    m.part("spike_b", "spike", pivot=(1.5, 4, 0.5), rot=(-14, 0, -18))
    m.box("spike_b", -0.5, 0, -0.5, 1, 3, 1, crystal, glow=crystal_glow)

    # a ring of three crystal shards turning against the tablets
    for i, yaw in enumerate((30, 150, 270)):
        p = m.part(f"shard{i}", "shards", pivot=(0, 0, 0), rot=(0, yaw, 0))
        m.box(p, -0.5, -1.5 + i * 0.5, -7.5, 1, 3, 1, crystal, glow=crystal_glow)

    # ------------------------------------------------------------------ four orbiting rune tablets, tilted outward
    for i, yaw in enumerate((45, 135, 225, 315)):
        holder = f"arm{i}"
        m.part(holder, "ring", pivot=(0, 0, 0), rot=(0, yaw, 0))
        tab = f"tab{i}"
        m.part(tab, holder, pivot=(0, -1, -12), rot=(-14, 0, 0))
        m.box(tab, -2.5, -6, -0.5, 5, 12, 1, tablet(i), glow=tablet_glow(i))
        m.box(tab, -1.5, -7, -1, 3, 1, 2, endstone(20 + i))                      # capstone
        m.box(tab, -0.5, 6, -0.5, 1, 2, 1, crystal, glow=crystal_glow)            # a hanging drop of crystal

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.rot("ring", (0, (0, 0, 0), "linear"), (4.0, (0, 90, 0), "linear"))     # a quarter turn: loops seamlessly
    idle.rot("shards", (0, (0, 0, 0), "linear"), (4.0, (0, -120, 0), "linear"))
    idle.pos("body", (0, (0, 0, 0)), (2.0, (0, 1.6, 0)), (4.0, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, 0)), (1.0, (1.5, 0, 1)), (3.0, (-1.5, 0, -1)), (4.0, (0, 0, 0)))
    idle.pos("crown", (0, (0, 0, 0)), (2.2, (0, 0.8, 0)), (4.0, (0, 0, 0)))    # the crown floats a hair apart
    idle.rot("crown", (0, (0, 0, 0)), (2.0, (0, 12, 0)), (4.0, (0, 0, 0)))
    idle.rot("spike", (0, (0, 0, 0)), (2.0, (4, 0, -4)), (4.0, (0, 0, 0)))
    # the eye scans and blinks once
    idle.rot("head", (0, (0, 0, 0)), (1.2, (0, 16, 0)), (1.8, (0, 16, 0)), (2.8, (0, -14, 0)), (3.4, (0, -14, 0)),
             (4.0, (0, 0, 0)))
    idle.pos("lid_t", (0, (0, 0, 0)), (2.9, (0, 0, 0)), (3.0, (0, -3.5, 0), "linear"), (3.15, (0, 0, 0)), (4.0, (0, 0, 0)))
    idle.pos("lid_b", (0, (0, 0, 0)), (2.9, (0, 0, 0)), (3.0, (0, 3.5, 0), "linear"), (3.15, (0, 0, 0)), (4.0, (0, 0, 0)))
    for i in range(4):
        t = 0.4 + i * 0.5
        idle.pos(f"tab{i}", (0, (0, 0, 0)), (t, (0, 1.5, 0)), (t + 1.6, (0, -1, 0)), (4.0, (0, 0, 0)))
        idle.rot(f"tab{i}", (0, (0, 0, 0)), (t, (-5, 0, 3)), (t + 1.6, (4, 0, -3)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("body", (0, (10, 0, 0)), (0.8, (12, 0, 0)), (1.6, (10, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.8, (0, 1, 0)), (1.6, (0, 0, 0)))
    walk.rot("spike", (0, (-14, 0, 0)), (0.8, (-20, 0, 0)), (1.6, (-14, 0, 0)))  # the crystals trail behind
    for i in range(4):
        walk.pos(f"tab{i}", (0, (0, 0, 0)), (0.8, (0, 0, 1.2)), (1.6, (0, 0, 0)))
    walk.rot("crown", (0, (-4, 0, 0)), (0.8, (-6, 0, 0)), (1.6, (-4, 0, 0)))

    # charge: the lids grind open, the tablets swing round in front of the eye and lean in, the obelisk rears back
    # as the beam builds (1.0 s = 20 ticks), then it snaps forward and fires
    a = m.anim("charge", 1.4)
    for i, yaw in enumerate((45, 135, 225, 315)):
        tgt = (-36, -12, 12, 36)[i]
        a.rot(f"arm{i}", (0, (0, 0, 0)), (0.55, (0, -yaw + tgt, 0)), (1.0, (0, -yaw + tgt, 0)), (1.4, (0, 0, 0)))
        a.rot(f"tab{i}", (0, (0, 0, 0)), (0.55, (14, 0, 0)), (0.95, (18, 0, 0)), (1.0, (-10, 0, 0), "linear"),
              (1.4, (0, 0, 0)))
        a.pos(f"tab{i}", (0, (0, 0, 0)), (0.55, (0, 0, 3)), (0.95, (0, 0, 3.5)), (1.05, (0, 0, -1.5), "linear"),
              (1.4, (0, 0, 0)))
    a.pos("lid_t", (0, (0, 0, 0)), (0.4, (0, 1.6, 0)), (1.0, (0, 1.8, 0)), (1.4, (0, 0, 0)))
    a.pos("lid_b", (0, (0, 0, 0)), (0.4, (0, -1.6, 0)), (1.0, (0, -1.8, 0)), (1.4, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.9, (1.15, 1.15, 1.15)), (1.0, (0.9, 0.9, 0.9), "linear"), (1.4, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.9, (-12, 0, 0)), (1.0, (8, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.9, (0, 2, 1)), (1.0, (0, 1, -1), "linear"), (1.4, (0, 0, 0)))
    a.rot("crown", (0, (0, 0, 0)), (0.9, (0, 90, 0)), (1.0, (0, 100, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("shards", (0, (0, 0, 0)), (1.0, (0, 540, 0)), (1.4, (0, 0, 0)))

    # blink: the lids slam shut, it folds in on itself (gone at 0.25 s) and unfolds where it reappears
    a = m.anim("blink", 0.6)
    a.scale("body", (0, (1, 1, 1)), (0.1, (1.1, 0.9, 1.1)), (0.25, (0.1, 1.4, 0.1), "linear"), (0.35, (0.1, 1.4, 0.1)),
            (0.6, (1, 1, 1)))
    a.rot("ring", (0, (0, 0, 0), "linear"), (0.6, (0, 720, 0), "linear"))
    a.pos("lid_t", (0, (0, 0, 0)), (0.08, (0, -3.5, 0), "linear"), (0.45, (0, -3.5, 0)), (0.6, (0, 0, 0)))
    a.pos("lid_b", (0, (0, 0, 0)), (0.08, (0, 3.5, 0), "linear"), (0.45, (0, 3.5, 0)), (0.6, (0, 0, 0)))

    # shove: the tablets are drawn in tight and the eye squints (anticipation), then they slam outward to push away
    # whoever is too close (at 0.3 s = 6 ticks)
    a = m.anim("shove", 0.8)
    for i in range(4):
        a.pos(f"tab{i}", (0, (0, 0, 0)), (0.25, (0, 0, 4)), (0.3, (0, 0, -7), "linear"), (0.5, (0, 0, -6)), (0.8, (0, 0, 0)))
        a.rot(f"tab{i}", (0, (0, 0, 0)), (0.25, (12, 0, 0)), (0.3, (-30, 0, 0), "linear"), (0.5, (-26, 0, 0)),
              (0.8, (0, 0, 0)))
    a.pos("lid_t", (0, (0, 0, 0)), (0.25, (0, -1.6, 0)), (0.3, (0, 1.8, 0), "linear"), (0.8, (0, 0, 0)))
    a.pos("lid_b", (0, (0, 0, 0)), (0.25, (0, 1.6, 0)), (0.3, (0, -1.8, 0), "linear"), (0.8, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.25, (0.85, 0.85, 0.85)), (0.3, (1.2, 1.2, 1.2), "linear"), (0.8, (1, 1, 1)))
    a.pos("body", (0, (0, 0, 0)), (0.25, (0, -1, 0)), (0.3, (0, 1.5, 0), "linear"), (0.8, (0, 0, 0)))
