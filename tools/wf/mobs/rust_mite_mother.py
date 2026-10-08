"""Rust Mite Swarm-Mother (Mère des mites de rouille): the brood-tick nesting in the Fallen Colossus, about 1 block long.

Silhouette idea: a tick that ate a giant. A small, armoured fore-body of dark pitted iron with two hooked chelicerae
and a pair of feeler palps, eight short jointed legs, and behind it an enormous swollen abdomen of flaking rust
scales, ridged like a pine cone, pocked with brood pores that glow a dull forge-orange. Two or three of her young
cling on top of her back. She bites through armour, spits gobbets of rust and, once, lets her swollen brood burst out.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

RUST = (156, 78, 38)
RUST_L = (206, 120, 62)
RUST_D = (98, 44, 22)
FLAKE = (186, 150, 110)
IRON = (62, 56, 56)
IRON_L = (110, 102, 98)
IRON_D = (34, 30, 30)
PORE = (255, 140, 50)
PORE_L = (255, 210, 120)
PORE_D = (60, 22, 10)
VERD = (90, 140, 120)


def rust(seed=0, scales=True):
    """Flaking rust: overlapping scales (a lit lower lip on each), pits, pale flakes lifting off."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return RUST_D
        if scales and face != "top":
            row = y // 2
            off = (row % 2) * 2
            lip = y % 2 == 1
            c = RUST if not lip else RUST_L
            if (x + off) % 4 == 0:
                c = RUST_D                                                                 # the gap between scales
        else:
            c = RUST if (x + y) % 3 else RUST_L
        r = K.h(x, y, seed) % 29
        if r == 0:
            c = FLAKE
        elif r == 1:
            c = mul(c, 0.6)
        elif r == 2:
            c = mix(c, VERD, 0.35)
        return c
    return f


def iron(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        c = IRON_L if (face == "top" and (x + y) % 4 == 0) or (face != "top" and y == 0) else IRON
        if K.h(x, y, seed) % 7 == 0:
            c = mix(c, RUST, 0.5)                                                          # rust bleeding through pits
        return c
    return f


def pores(seed=0, every=3):
    """Brood pores on the abdomen: dark rimmed holes with an ember inside."""
    def is_pore(face, x, y, w, h):
        return face != "bottom" and w > 2 and h > 2 and 0 < x < w - 1 and 0 < y < h - 1 and \
            (x + (y // every) * 2 + seed) % (every + 1) == 0 and y % every == 1

    def f(face, x, y, w, h):
        if is_pore(face, x, y, w, h):
            return PORE
        if is_pore(face, x - 1, y, w, h) or is_pore(face, x + 1, y, w, h):
            return PORE_D
        return rust(seed)(face, x, y, w, h)

    def g(face, x, y, w, h):
        return (PORE_L if K.h(x, y, seed) % 3 == 0 else PORE) if is_pore(face, x, y, w, h) else None
    return f, g


def leg(seed=0):
    def f(face, x, y, w, h):
        if y == h - 1:
            return IRON_D
        return IRON if (y + seed) % 3 else RUST_D
    return f


def build():
    m = Model("rust_mite_mother", seed=977, shadow=0.6, walk_speed=1.8, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -4, -3))
    m.part("head", "body", pivot=(0, -0.5, -3.5))
    m.part("chel_r", "head", pivot=(-1, 1, -3.5), rot=(10, 10, 0))
    m.part("chel_l", "head", pivot=(1, 1, -3.5), rot=(10, -10, 0))
    m.part("palp_r", "head", pivot=(-2, 0, -3), rot=(-20, 20, 0))
    m.part("palp_l", "head", pivot=(2, 0, -3), rot=(-20, -20, 0))
    m.part("abdomen", "body", pivot=(0, -1, 2.5), rot=(-8, 0, 0))
    m.part("young1", "abdomen", pivot=(-2, -8.5, 4), rot=(0, 30, 6))
    m.part("young2", "abdomen", pivot=(2.5, -7.5, 8), rot=(10, -50, -8))
    LEGS = [(-2.5, -35), (-0.8, -10), (0.8, 10), (2.5, 35)]
    for i, (z, yaw) in enumerate(LEGS):
        for side, sx in (("r", -1), ("l", 1)):
            m.part(f"leg{i}{side}", "body", pivot=(3 * sx, 0.5, z), rot=(0, yaw * -sx, 105 * -sx))
            m.part(f"shin{i}{side}", f"leg{i}{side}", pivot=(0, 4, 0), rot=(0, 0, 75 * sx))

    # fore-body and head: dark pitted iron
    m.box("body", -3, -2, -3.5, 6, 4, 7, iron(1))
    m.box("body", -2.5, -2.5, -3, 5, 1, 6, iron(2))
    m.box("head", -2, -1.5, -3.5, 4, 3, 4, iron(3))
    for x in (-1.5, 0.5):
        m.box("head", x, -2, -3.6, 1, 1, 1, {"*": IRON_D, "front": PORE}, glow={"front": PORE_L, "*": None})  # two tiny eyes
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"chel_{side}", -0.5, -0.5, -3, 1, 1, 3, iron(4 + sx))
        m.box(f"chel_{side}", -0.5 - 0.6 * sx, 0, -3.5, 1, 1, 1, IRON_D)                        # hooked fang
        m.box(f"palp_{side}", -0.5, -0.5, -3, 1, 1, 3, leg(6 + sx))

    # the swollen abdomen: a rust pine-cone with glowing brood pores
    pf, pg = pores(10)
    pf2, pg2 = pores(11, every=2)
    m.box("abdomen", -5, -6, 0.5, 10, 6, 10, pf, glow=pg)                                    # the widest band
    m.box("abdomen", -4, -8, 1.5, 8, 9, 8, pf2, glow=pg2)                                     # the round core
    m.box("abdomen", -3, -9, 2.5, 6, 1, 6, rust(14, scales=False))                            # the crown of the hump
    m.box("abdomen", -5.5, -5, 2, 1, 4, 7, rust(12))                                          # flank ridges
    m.box("abdomen", 4.5, -5, 2, 1, 4, 7, rust(13))
    m.box("abdomen", -3.5, -5, 10.5, 7, 5, 1, pf2, glow=pg2)                                  # the rear cap
    m.box("abdomen", -1, -3, 11.5, 2, 2, 1, PORE_D)                                              # the brood vent
    for i, z in enumerate((2, 5, 8)):
        m.box("abdomen", -0.5, -10, z + 1, 1, 1, 1, {"*": RUST_D, "top": FLAKE})                     # a ridge of spikes

    # two of her young riding on top
    for yp in ("young1", "young2"):
        m.box(yp, -1, -1, -1.5, 2, 1, 3, rust(20, scales=False))
        m.box(yp, -0.5, -1, -2, 1, 1, 1, IRON)
        for lz in (-1, 0.5):
            m.box(yp, -1.5, -0.5, lz, 3, 1, 1, IRON_D)

    for i, (z, yaw) in enumerate(LEGS):
        for side in ("r", "l"):
            m.box(f"leg{i}{side}", -0.5, 0, -0.5, 1, 4, 1, leg(i))
            m.box(f"leg{i}{side}", -0.8, 3, -0.8, 1, 1, 1, RUST_D, grow=0.3)
            m.box(f"shin{i}{side}", -0.5, 0, -0.5, 1, 4, 1, leg(i + 3))

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 2.0)
    idle.scale("abdomen", (0, (1, 1, 1)), (1.0, (1.05, 1.06, 1.04)), (2.0, (1, 1, 1)))
    idle.rot("palp_r", (0, (0, 0, 0)), (0.5, (14, -10, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("palp_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (14, 10, 0)), (2.0, (0, 0, 0)))
    idle.rot("young1", (0, (0, 0, 0)), (1.0, (0, 30, 0)), (2.0, (0, 0, 0)))
    idle.rot("young2", (0, (0, 0, 0)), (1.0, (0, -24, 0)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 0.5)
    for i in range(4):
        for side, sx in (("r", -1), ("l", 1)):
            s = 1 if (i + (side == "r")) % 2 else -1
            walk.rot(f"leg{i}{side}", (0, (0, 24 * s, 0)), (0.125, (0, 0, 16 * -sx * (s > 0))), (0.25, (0, -24 * s, 0)),
                     (0.375, (0, 0, 16 * -sx * (s < 0))), (0.5, (0, 24 * s, 0)))
    walk.rot("abdomen", (0, (0, 4, 2)), (0.25, (0, -4, -2)), (0.5, (0, 4, 2)))
    walk.pos("body", (0, (0, 0, 0)), (0.125, (0, 0.3, 0)), (0.25, (0, 0, 0)), (0.375, (0, 0.3, 0)), (0.5, (0, 0, 0)))

    # bite: the fore-body rears a little and the chelicerae spread (0.3 s), then snap shut on the prey (at 0.3 s = 6
    # ticks)
    a = m.anim("bite", 0.6)
    a.rot("body", (0, (0, 0, 0)), (0.25, (-14, 0, 0)), (0.32, (10, 0, 0), "linear"), (0.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.25, (0, 0.5, 1)), (0.32, (0, 0, -1.5), "linear"), (0.6, (0, 0, 0)))
    a.rot("chel_r", (0, (0, 0, 0)), (0.25, (0, 40, 0)), (0.32, (0, -16, 0), "linear"), (0.6, (0, 0, 0)))
    a.rot("chel_l", (0, (0, 0, 0)), (0.25, (0, -40, 0)), (0.32, (0, 16, 0), "linear"), (0.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.25, (-12, 0, 0)), (0.32, (8, 0, 0)), (0.6, (0, 0, 0)))

    # spit: the abdomen pumps three times, the fore-body rearing higher each time (0.6 s telegraph), then a gobbet of
    # rust is spat (at 0.6 s = 12 ticks)
    a = m.anim("spit", 1.0)
    a.scale("abdomen", (0, (1, 1, 1)), (0.15, (0.92, 0.92, 0.95)), (0.25, (1.08, 1.08, 1.04)), (0.35, (0.9, 0.9, 0.94)),
            (0.45, (1.1, 1.1, 1.05)), (0.55, (0.88, 0.88, 0.92)), (0.65, (1.12, 1.12, 1.06)), (1.0, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.55, (-26, 0, 0)), (0.62, (6, 0, 0), "linear"), (0.8, (4, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("abdomen", (0, (0, 0, 0)), (0.55, (24, 0, 0)), (0.62, (-6, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (-10, 0, 0)), (0.62, (14, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("chel_r", (0, (0, 0, 0)), (0.55, (0, 30, 0)), (0.62, (0, 46, 0)), (1.0, (0, 0, 0)))
    a.rot("chel_l", (0, (0, 0, 0)), (0.55, (0, -30, 0)), (0.62, (0, -46, 0)), (1.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.55, (0, 1, 1)), (0.62, (0, 0, -1), "linear"), (1.0, (0, 0, 0)))

    # brood: she plants all eight legs and her abdomen swells and shudders, the pores flaring (1.0 s telegraph), then it
    # bursts open and her young spill out (at 1.0 s = 20 ticks)
    a = m.anim("brood", 1.6)
    a.scale("abdomen", (0, (1, 1, 1)), (0.3, (1.1, 1.12, 1.08)), (0.4, (1.06, 1.08, 1.04)), (0.6, (1.22, 1.26, 1.16)),
            (0.7, (1.16, 1.2, 1.12)), (0.9, (1.34, 1.38, 1.26)), (1.0, (1.36, 1.4, 1.28)), (1.08, (0.86, 0.84, 0.9), "linear"),
            (1.3, (0.92, 0.9, 0.94)), (1.6, (1, 1, 1)))
    a.rot("abdomen", (0, (0, 0, 0)), (0.5, (0, 0, 4)), (0.6, (0, 0, -4)), (0.7, (0, 0, 5)), (0.8, (0, 0, -5)), (0.9, (0, 0, 6)),
          (1.0, (-10, 0, 0)), (1.1, (14, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.9, (8, 0, 0)), (1.08, (-10, 0, 0)), (1.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.9, (0, -1, 0)), (1.08, (0, 0.5, 0)), (1.6, (0, 0, 0)))
    for i in range(4):
        for side, sx in (("r", -1), ("l", 1)):
            a.rot(f"leg{i}{side}", (0, (0, 0, 0)), (0.3, (0, 0, -16 * -sx)), (1.0, (0, 0, -18 * -sx)), (1.1, (0, 0, 10 * -sx)),
                  (1.6, (0, 0, 0)))
    for yp in ("young1", "young2"):
        a.pos(yp, (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (0, 4, 0), "linear"), (1.3, (0, 2, 0)), (1.6, (0, 0, 0)))
        a.scale(yp, (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.08, (0.01, 0.01, 0.01), "linear"), (1.5, (0.01, 0.01, 0.01)),
                (1.6, (1, 1, 1)))
