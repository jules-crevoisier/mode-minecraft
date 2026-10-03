"""The Jade Jaguar (Le Jaguar de jade): placeholder model, replaced by the real creature."""
from ..models import Model, speckle


def build():
    m = Model("jade_jaguar", seed=4, shadow=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -24, 0))
    m.part("head", "body", pivot=(0, -24, 0))
    m.box("body", -8, -24, -5, 16, 24, 10, speckle((120, 120, 120), 0.08, 1))
    m.box("bone", -6, -24, -4, 12, 24, 8, speckle((90, 90, 90), 0.08, 2))
    m.box("head", -5, -10, -5, 10, 10, 10, speckle((150, 150, 150), 0.08, 3))
    idle = m.anim("idle", 2.0)
    idle.rot("head", (0, (0, 0, 0)), (1.0, (-4, 0, 0)), (2.0, (0, 0, 0)))
    return m
