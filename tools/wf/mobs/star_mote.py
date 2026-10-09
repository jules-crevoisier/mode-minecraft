"""Star Mote (Poussière d'astre): the little star sparks a Star Mote Swarm-Caller calls down, about 0.4 block.

Silhouette idea: a single spark of starlight with a crystal body. A tiny faceted cube of pale quartz turned on its
corner, six short spikes sticking out of it like a child's drawing of a star, a white-hot point in the middle and two
flickering facet "wings" that beat fast. It zips around its prey and darts into it.
"""
from ..models import Model
from ..texgen import mix
from . import star_mote_caller as S

STAR = S.STAR
STAR_C = S.STAR_C


def build():
    m = Model("star_mote", seed=1237, shadow=0.15, walk_speed=1.6, walk_scale=0.5)
    m.part("bone", pivot=(0, 24, 0))
    m.part("core", "bone", pivot=(0, -6, 0))
    m.part("star", "core", pivot=(0, 0, 0), rot=(45, 45, 0))
    m.part("wing_r", "core", pivot=(-1.5, -1, 0.5), rot=(0, 0, 20))
    m.part("wing_l", "core", pivot=(1.5, -1, 0.5), rot=(0, 0, -20))
    m.part("trail", "core", pivot=(0, 0, 2))

    m.box("star", -1.5, -1.5, -1.5, 3, 3, 3, S.facets(1), glow={"*": lambda f_, x, y, w, h: STAR if (x, y) == (1, 1) else None})
    for (x, y, z, w, h, d) in ((-0.5, -3.5, -0.5, 1, 2, 1), (-0.5, 1.5, -0.5, 1, 2, 1), (-3.5, -0.5, -0.5, 2, 1, 1),
                               (1.5, -0.5, -0.5, 2, 1, 1), (-0.5, -0.5, -3.5, 1, 1, 2), (-0.5, -0.5, 1.5, 1, 1, 2)):
        m.box("star", x, y, z, w, h, d, S.facets(2, 0.6), glow=lambda f_, x, y, w, h: STAR_C)
    wing = {"*": lambda f_, x, y, w, h: (*mix(STAR_C, (255, 255, 255), 0.3 * (x % 2)), 170)}
    m.box("wing_r", -3, -1, 0, 3, 2, 0, wing, glow=wing)
    m.box("wing_l", 0, -1, 0, 3, 2, 0, wing, glow=wing)
    for i in range(3):
        m.box("trail", -0.5, -0.5, i * 1.5, 1, 1, 1, STAR_C if i else STAR, glow=STAR_C if i else STAR)

    idle = m.anim("idle", 1.2)
    idle.rot("star", (0, (0, 0, 0), "linear"), (0.6, (0, 180, 0), "linear"), (1.2, (0, 360, 0), "linear"))
    idle.pos("core", (0, (0, 0, 0)), (0.3, (0, 1, 0)), (0.6, (0, 0, 0)), (0.9, (0, 1, 0)), (1.2, (0, 0, 0)))
    idle.rot("wing_r", (0, (0, 0, 0)), (0.1, (0, 0, -50)), (0.2, (0, 0, 0)), (0.3, (0, 0, -50)), (0.4, (0, 0, 0)),
             (0.5, (0, 0, -50)), (0.6, (0, 0, 0)), (0.7, (0, 0, -50)), (0.8, (0, 0, 0)), (0.9, (0, 0, -50)), (1.0, (0, 0, 0)),
             (1.1, (0, 0, -50)), (1.2, (0, 0, 0)))
    idle.rot("wing_l", (0, (0, 0, 0)), (0.1, (0, 0, 50)), (0.2, (0, 0, 0)), (0.3, (0, 0, 50)), (0.4, (0, 0, 0)),
             (0.5, (0, 0, 50)), (0.6, (0, 0, 0)), (0.7, (0, 0, 50)), (0.8, (0, 0, 0)), (0.9, (0, 0, 50)), (1.0, (0, 0, 0)),
             (1.1, (0, 0, 50)), (1.2, (0, 0, 0)))
    idle.scale("trail", (0, (1, 1, 1)), (0.6, (1, 1, 1.4)), (1.2, (1, 1, 1)))

    walk = m.anim("walk", 0.6)
    walk.rot("core", (0, (20, 0, 0)), (0.3, (24, 0, 0)), (0.6, (20, 0, 0)))
    walk.scale("trail", (0, (1, 1, 1.6)), (0.3, (1, 1, 2.0)), (0.6, (1, 1, 1.6)))

    # dart: it pulls back and spins up, the point flaring (0.4 s telegraph), then darts into its prey (hits at 0.4 s =
    # 8 ticks)
    a = m.anim("dart", 0.9)
    a.pos("core", (0, (0, 0, 0)), (0.35, (0, 1, 3)), (0.4, (0, 1, 3.5)), (0.48, (0, -1, -5), "linear"), (0.6, (0, -1, -5)),
          (0.9, (0, 0, 0)))
    a.rot("star", (0, (0, 0, 0)), (0.4, (0, 720, 0)), (0.6, (0, 900, 0)), (0.9, (0, 1080, 0)))
    a.scale("star", (0, (1, 1, 1)), (0.35, (1.35, 1.35, 1.35)), (0.4, (1.4, 1.4, 1.4)), (0.5, (0.9, 0.9, 0.9)), (0.9, (1, 1, 1)))
    a.scale("trail", (0, (1, 1, 1)), (0.4, (1, 1, 0.5)), (0.48, (1, 1, 3), "linear"), (0.9, (1, 1, 1)))
    return m
