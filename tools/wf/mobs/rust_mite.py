"""Rust Mite (Mite de rouille): the brood of the Rust Mite Swarm-Mother, a quarter of a block long.

Silhouette idea: a flake of rust that learned to run. A flat oval shell of orange-brown rust scales, a tiny dark iron
head with snapping hooked mandibles and two glowing ember eyes, six needle legs that blur when it scuttles.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K
from .rust_mite_mother import RUST, RUST_L, RUST_D, IRON, IRON_D, PORE, PORE_L, FLAKE, rust, iron


def build():
    m = Model("rust_mite", seed=983, shadow=0.25, walk_speed=2.6, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -2, 0))
    m.part("head", "body", pivot=(0, 0, -2.5))
    m.part("mand_r", "head", pivot=(-0.7, 0.5, -1.5), rot=(0, 15, 0))
    m.part("mand_l", "head", pivot=(0.7, 0.5, -1.5), rot=(0, -15, 0))
    for i, (z, yaw) in enumerate(((-1.5, -30), (0, 0), (1.5, 30))):
        for side, sx in (("r", -1), ("l", 1)):
            m.part(f"leg{i}{side}", "body", pivot=(1.5 * sx, 0.5, z), rot=(0, yaw * -sx, 60 * -sx))

    m.box("body", -2, -1.5, -2.5, 4, 2, 5, rust(1))
    m.box("body", -1.5, -2, -2, 3, 1, 4, rust(2, scales=False))
    m.box("body", -0.5, -2.5, -1, 1, 1, 2, {"*": RUST_D, "top": FLAKE})
    m.box("head", -1, -1, -1.5, 2, 2, 2, iron(3))
    m.box("head", -1, -1.2, -1.6, 2, 1, 1, {"front": lambda f, x, y, w, h: PORE, "*": IRON_D},
          glow={"front": lambda f, x, y, w, h: PORE_L, "*": None})
    for side in ("r", "l"):
        m.box(f"mand_{side}", -0.5, -0.5, -1.5, 1, 1, 2, {"*": IRON_D, "top": IRON})
    for i in range(3):
        for side in ("r", "l"):
            m.box(f"leg{i}{side}", -0.5, 0, -0.5, 1, 3, 1, {"*": IRON, "bottom": IRON_D})

    idle = m.anim("idle", 1.2)
    idle.rot("mand_r", (0, (0, 0, 0)), (0.2, (0, 20, 0)), (0.4, (0, 0, 0)), (1.2, (0, 0, 0)))
    idle.rot("mand_l", (0, (0, 0, 0)), (0.2, (0, -20, 0)), (0.4, (0, 0, 0)), (1.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (0, 14, 0)), (1.2, (0, 0, 0)))

    walk = m.anim("walk", 0.3)
    for i in range(3):
        for side, sx in (("r", -1), ("l", 1)):
            s = 1 if (i + (side == "r")) % 2 else -1
            walk.rot(f"leg{i}{side}", (0, (0, 30 * s, 0)), (0.15, (0, -30 * s, 0)), (0.3, (0, 30 * s, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.075, (0, 0.3, 0)), (0.15, (0, 0, 0)), (0.225, (0, 0.3, 0)), (0.3, (0, 0, 0)))

    # bite: rears and spreads its mandibles (0.25 s), then lunges and snaps (at 0.25 s = 5 ticks)
    a = m.anim("bite", 0.5)
    a.rot("body", (0, (0, 0, 0)), (0.2, (-20, 0, 0)), (0.27, (10, 0, 0), "linear"), (0.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.2, (0, 0.5, 0.5)), (0.27, (0, 0, -1), "linear"), (0.5, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.2, (0, 45, 0)), (0.27, (0, -10, 0), "linear"), (0.5, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.2, (0, -45, 0)), (0.27, (0, 10, 0), "linear"), (0.5, (0, 0, 0)))
    return m
