"""crypt_crawler: placeholder model, replaced by the real creature."""
from ..models import Model, speckle


def build():
    m = Model("crypt_crawler", seed=7, shadow=0.6)
    m.part("bone", pivot=(0, 24, 0))
    m.part("head", "bone", pivot=(0, -20, 0))
    m.box("bone", -4, -20, -3, 8, 20, 6, speckle((120, 120, 120), 0.08, 1))
    m.box("head", -4, -8, -4, 8, 8, 8, speckle((150, 150, 150), 0.08, 3))
    idle = m.anim("idle", 2.0)
    idle.rot("head", (0, (0, 0, 0)), (1.0, (-4, 0, 0)), (2.0, (0, 0, 0)))
    return m
