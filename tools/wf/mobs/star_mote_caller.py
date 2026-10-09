"""Star Mote Swarm-Caller (Appeleur d'astres): a floating star crystal of the Starfall Library, about 1 block tall.

Silhouette idea: a shard of a fallen star that kept a little of its sky. A long, double-pointed crystal spindle of
pale starlight quartz, turned on its corner like a diamond, hovering at head height with nothing under it but a
trickle of sparks. Its facets are pale cyan fading to violet at the tips, with a cold white star burning in its
heart behind a single clear facet (its eye). Four small satellite shards circle it on a slow ring and a thin brass
astrolabe band, left from the library's instruments, girdles its middle. It turns its shards toward its prey and
fires short beams of starlight, flares to call two star motes down once, and throws back anyone who comes too near.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

QUARTZ = (190, 234, 248)
QUARTZ_L = (240, 252, 255)
QUARTZ_D = (120, 176, 226)
VIOLET = (142, 110, 210)
VIOLET_D = (82, 62, 140)
STAR = (255, 255, 236)
STAR_C = (170, 230, 255)
BRASS = (196, 160, 72)
BRASS_D = (124, 94, 40)
BRASS_L = (240, 210, 130)


def facets(seed=0, tip=0.0):
    """Faceted crystal: diagonal facet bands lit on one side, darker on the other, a bright ridge line between them;
    ``tip`` (0..1) tints the face toward violet (the points)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            c = QUARTZ_L if face == "top" else QUARTZ_D
            return mix(c, VIOLET, tip * 0.8)
        band = (x + y + K.h(seed, face == "front")) // 3 % 3
        c = (QUARTZ_L, QUARTZ, QUARTZ_D)[band]
        if (x + y) % 3 == 0 and band == 0:
            c = (255, 255, 255)                                                                # the ridge glint
        c = mix(c, VIOLET, min(0.85, tip * (0.6 + 0.4 * y / max(1, h))))
        return c
    return f


def heart_glow(face, x, y, w, h):
    """The star in its heart, seen through the clear front and back facets."""
    if face not in ("front", "back"):
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    dx, dy = abs(x - cx), abs(y - cy)
    if dx < 0.6 and dy < 0.6 or (dx < 0.6 and dy < 2.1) or (dy < 0.6 and dx < 2.1):
        return STAR
    if dx + dy < 2.2:
        return STAR_C
    return None


def build():
    m = Model("star_mote_caller", seed=1231, shadow=0.35, walk_speed=0.6, walk_scale=0.4)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("core", "bone", pivot=(0, -16, 0))
    m.part("crystal", "core", pivot=(0, 0, 0), rot=(0, 45, 0))
    m.part("band", "core", pivot=(0, 0, 0))
    m.part("orbit", "core", pivot=(0, 0, 0))
    for i in range(4):
        m.part(f"ring{i}", "orbit", pivot=(0, 0, 0), rot=(0, 45 + i * 90, 0))
        m.part(f"shard{i}", f"ring{i}", pivot=(0, 0, -8), rot=(14, 0, 0))
    m.part("sparks", "core", pivot=(0, 9, 0))

    # ------------------------------------------------------------------ the spindle
    m.box("crystal", -3, -4, -3, 6, 8, 6, facets(1), glow={"*": heart_glow})
    m.box("crystal", -2, -7, -2, 4, 3, 4, facets(2, 0.4))
    m.box("crystal", -1, -10, -1, 2, 3, 2, facets(3, 0.9))
    m.box("crystal", -2, 4, -2, 4, 3, 4, facets(4, 0.4))
    m.box("crystal", -1, 7, -1, 2, 3, 2, facets(5, 0.9))
    m.box("crystal", -0.5, -11, -0.5, 1, 1, 1, STAR, glow=STAR)                                # the points burn white
    m.box("crystal", -0.5, 10, -0.5, 1, 1, 1, STAR, glow=STAR)

    # the brass astrolabe band round its middle, with engraved hour marks
    def band(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return BRASS_D
        return BRASS_L if x % 3 == 0 else (BRASS if y == 0 else BRASS_D)
    m.box("band", -4.5, -0.5, -4.5, 9, 1, 9, band)
    m.box("band", -0.5, -1.5, -5, 1, 3, 1, {"*": BRASS, "front": BRASS_L})                    # the pointer

    # ------------------------------------------------------------------ the four satellite shards
    for i in range(4):
        sh = f"shard{i}"
        m.box(sh, -0.5, -3, -0.5, 1, 6, 1, facets(10 + i, 0.3), glow={"*": lambda f_, x, y, w, h: STAR_C if y in (0, h - 1) else None})
        m.box(sh, -1, -1.5, -1, 2, 3, 2, facets(14 + i, 0.1))

    # sparks trickling under it
    for i, (x, y, z) in enumerate(((-1, 1, 0), (1, 3, -1), (0, 5, 1), (-0.5, 7, -0.5))):
        m.box("sparks", x, y, z, 1, 1, 1, STAR_C if i % 2 else STAR, glow=STAR_C if i % 2 else STAR)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("core", (0, (0, 0, 0)), (2.0, (0, 1.5, 0)), (4.0, (0, 0, 0)))
    idle.rot("crystal", (0, (0, 0, 0), "linear"), (1.0, (0, 90, 0), "linear"), (2.0, (0, 180, 0), "linear"),
             (3.0, (0, 270, 0), "linear"), (4.0, (0, 360, 0), "linear"))
    idle.rot("orbit", (0, (0, 0, 0), "linear"), (2.0, (0, -180, 0), "linear"), (4.0, (0, -360, 0), "linear"))
    idle.rot("band", (0, (0, 0, 4)), (2.0, (0, 0, -4)), (4.0, (0, 0, 4)))
    idle.pos("sparks", (0, (0, 0, 0)), (1.0, (0, -1.5, 0)), (1.01, (0, 1, 0), "linear"), (2.0, (0, 0, 0)),
             (3.0, (0, -1.5, 0)), (3.01, (0, 1, 0), "linear"), (4.0, (0, 0, 0)))
    for i in range(4):
        idle.pos(f"shard{i}", (0, (0, 0, 0)), (1.0 + i * 0.5, (0, 1.0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("core", (0, (14, 0, 0)), (0.8, (18, 0, 0)), (1.6, (14, 0, 0)))                   # drifting nose-first
    walk.pos("core", (0, (0, 0, 0)), (0.8, (0, 0.8, 0)), (1.6, (0, 0, 0)))

    # beam: the satellite shards swing round in front of it and point at the prey while the heart brightens (0.75 s
    # telegraph), then a short beam (fired at 0.75 s = 15 ticks)
    a = m.anim("beam", 1.3)
    for i in range(4):
        # each ring turns so its shard ends up ahead of the core, the shard tips forward like a lens
        start = 45 + i * 90
        target = (-20, 20, -8, 8)[i]
        a.rot(f"ring{i}", (0, (0, 0, 0)), (0.5, (0, target - start, 0)), (1.0, (0, target - start, 0)), (1.3, (0, 0, 0)))
        a.rot(f"shard{i}", (0, (0, 0, 0)), (0.5, (76, 0, 0)), (0.75, (80, 0, 0)), (0.8, (60, 0, 0)), (1.0, (76, 0, 0)), (1.3, (0, 0, 0)))
        a.pos(f"shard{i}", (0, (0, 0, 0)), (0.5, (0, (-1.5, 1.5, 1.5, -1.5)[i] + 0.5, 0)), (1.0, (0, (-1.5, 1.5, 1.5, -1.5)[i] + 0.5, 0)),
              (1.3, (0, 0, 0)))
    a.rot("core", (0, (0, 0, 0)), (0.6, (-12, 0, 0)), (0.75, (-14, 0, 0)), (0.8, (10, 0, 0), "linear"), (1.0, (6, 0, 0)), (1.3, (0, 0, 0)))
    a.pos("core", (0, (0, 0, 0)), (0.75, (0, 0, 1.5)), (0.8, (0, 0, 3), "linear"), (1.3, (0, 0, 0)))
    a.scale("crystal", (0, (1, 1, 1)), (0.7, (1.08, 1.08, 1.08)), (0.75, (1.12, 1.12, 1.12)), (0.82, (0.94, 0.94, 0.94)),
            (1.3, (1, 1, 1)))

    # call: the shards fly far out on a widening ring and the crystal swells and flares (1.0 s telegraph), then two
    # motes are called down (at 1.0 s = 20 ticks)
    a = m.anim("call", 1.7)
    a.rot("orbit", (0, (0, 0, 0)), (1.0, (0, 540, 0)), (1.2, (0, 600, 0)), (1.7, (0, 720, 0)))
    for i in range(4):
        a.pos(f"shard{i}", (0, (0, 0, 0)), (0.8, (0, 3, 6)), (1.0, (0, 4, 7)), (1.1, (0, 0, -2), "linear"), (1.7, (0, 0, 0)))
        a.rot(f"shard{i}", (0, (0, 0, 0)), (0.8, (-50, 0, 0)), (1.0, (-60, 0, 0)), (1.7, (0, 0, 0)))
    a.scale("crystal", (0, (1, 1, 1)), (0.8, (1.25, 1.25, 1.25)), (0.95, (1.35, 1.35, 1.35)), (1.0, (1.4, 1.4, 1.4)),
            (1.1, (0.85, 0.85, 0.85), "linear"), (1.7, (1, 1, 1)))
    a.pos("core", (0, (0, 0, 0)), (1.0, (0, 3, 0)), (1.7, (0, 0, 0)))
    a.rot("band", (0, (0, 0, 0)), (1.0, (30, 0, 20)), (1.7, (0, 0, 0)))

    # pulse: the crystal draws in tight, the shards hugging it (0.6 s telegraph), then a nova that throws back anyone
    # close (at 0.6 s = 12 ticks)
    a = m.anim("pulse", 1.1)
    a.scale("crystal", (0, (1, 1, 1)), (0.55, (0.72, 0.72, 0.72)), (0.6, (0.7, 0.7, 0.7)), (0.66, (1.4, 1.4, 1.4), "linear"),
            (0.8, (1.2, 1.2, 1.2)), (1.1, (1, 1, 1)))
    for i in range(4):
        a.pos(f"shard{i}", (0, (0, 0, 0)), (0.55, (0, 0, 4)), (0.6, (0, 0, 4.5)), (0.66, (0, 0, -6), "linear"), (0.8, (0, 0, -5)),
              (1.1, (0, 0, 0)))
    a.rot("band", (0, (0, 0, 0)), (0.55, (0, 0, 0)), (0.66, (0, 0, 20)), (1.1, (0, 0, 0)))
    a.pos("core", (0, (0, 0, 0)), (0.55, (0, -1, 0)), (0.66, (0, 1.5, 0), "linear"), (1.1, (0, 0, 0)))
