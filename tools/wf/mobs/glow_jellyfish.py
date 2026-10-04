"""Glow Jellyfish (Méduse lumineuse): a see-through bell that pulses and drifts, trailing tentacles and frilly oral
arms; a glowing four-leaf core shows through the bell.

Four colour variants (rose, azure, amber, violet) repaint the same cubes; the bell is translucent (render type
entityTranslucent) and the glow layer breathes slowly.
"""
import math

from ..models import Model
from ..texgen import mix, mul

VARIANTS = {
    # bell, rim/light, glow, tentacle
    "rose": ((232, 110, 186), (255, 206, 238), (255, 140, 214), (250, 186, 226)),
    "azure": ((84, 176, 255), (196, 238, 255), (110, 232, 255), (170, 224, 255)),
    "amber": ((255, 168, 64), (255, 232, 168), (255, 206, 92), (255, 214, 150)),
    "violet": ((156, 104, 255), (222, 202, 255), (196, 150, 255), (206, 184, 255)),
}
ORDER = ["rose", "azure", "amber", "violet"]


def _n(x, y, seed):
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


def bell(base, light, alpha, seed, rim=False):
    """Translucent bell: lighter toward the rim, faint radial canals, a few bright spots."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return (*mul(base, 0.7), alpha - 40)
        if face == "top":
            c = mix(base, light, 0.15 + 0.25 * _n(x, y, seed))
            if (x + y) % 4 == 0:
                c = mix(c, light, 0.45)
            return (*c, alpha)
        k = y / max(1, h - 1)
        c = mix(base, light, 0.15 + 0.45 * k if rim else 0.1 + 0.2 * k)
        if x % 3 == 1:
            c = mix(c, light, 0.35)  # radial canals
        if rim and y == h - 1:
            c = light
        return (*c, alpha + (30 if rim and y == h - 1 else 0))
    return f


def frill(light, alpha):
    """Scalloped skirt under the rim (sides only)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        c = mix(light, (255, 255, 255), 0.25)
        return (*c, alpha) if x % 2 == 0 else (*light, alpha - 40)
    return f


def build(variant=None):
    variant = variant or ORDER[0]
    base, light, glow, tent = VARIANTS[variant]
    tent = mix(tent, base, 0.35)
    m = Model("glow_jellyfish", seed=97, shadow=0.3, head=None, render="entityTranslucent",
              variants=ORDER, glow_pulse=0.11)
    m.preview_idle = True

    m.part("body", pivot=(0, 24, 0))
    m.part("bell", "body", pivot=(0, -12, 0))
    m.part("skirt", "body", pivot=(0, -12, 0))
    m.part("arms", "skirt", pivot=(0, 0, 0))

    # ---- the bell: a dome of one-pixel rings (widest at the rim), translucent
    profile = [12, 12, 12, 11, 11, 10, 9, 7, 5]
    for k, wd in enumerate(profile):
        top = k == len(profile) - 1
        inner = profile[k + 1] if not top else 0
        paint = bell(mix(base, light, 0.25) if top else base, light, 165 if top else 112 + k * 3, k + 1, rim=k == 0)

        def ring(face, x, y, w, h, paint=paint, inner=inner, k=k):
            # only the visible annulus of each ring's top; undersides hidden, except the rim's (the subumbrella)
            if face == "top" and inner:
                lo = (w - inner) / 2
                if lo <= x < w - lo and lo <= y < h - lo:
                    return None
            if face == "bottom":
                return (*mix(base, light, 0.2), 70) if k == 0 else None
            return paint(face, x, y, w, h)

        def leaf(face, x, y, w, h, wd=wd):
            # the four glowing gonads of a moon jelly, seen through the crown from above
            if face != "top":
                return None
            cx, cy = x - (w - 1) / 2, y - (h - 1) / 2
            r, a = math.hypot(cx, cy), math.atan2(cy, cx)
            petal = 0.5 + 0.5 * math.cos(2 * a)  # four lobes
            if wd <= 9 and 0.6 < r < 1.2 + 2.2 * petal * (wd / 9):
                return (*glow, 255)
            return None
        m.box("bell", -wd / 2, -1 - k, -wd / 2, wd, 1, wd, ring, glow=leaf if k >= 6 else None)
    # glowing four-leaf core seen through the bell
    core = (*mix(glow, (255, 255, 255), 0.35), 255)
    m.box("bell", -2, -4, -2, 4, 2, 4, {"*": core, "top": (*mix(glow, (255, 255, 255), 0.6), 255)},
          glow={"*": (*glow, 255), "top": (*mix(glow, (255, 255, 255), 0.5), 255)})
    for dx, dz in ((-2, -2), (1, -2), (-2, 1), (1, 1)):
        m.box("bell", dx, -4.5, dz, 1, 1, 1, (*light, 255), glow=(*mix(glow, (255, 255, 255), 0.4), 255))
    # glowing dots along the rim
    m.box("bell", -6, -0.6, -6, 12, 0, 12,
          lambda f, x, y, w, h: None if f not in ("top", "bottom") or (x + y) % 3 or x in range(1, w - 1) and y in range(1, h - 1) else (*light, 230),
          glow=lambda f, x, y, w, h: None if f not in ("top", "bottom") or (x + y) % 3 or x in range(1, w - 1) and y in range(1, h - 1) else (*glow, 255))

    # ---- scalloped skirt under the rim
    m.box("skirt", -6, 0, -6, 12, 1, 12, frill(light, 170))

    # ---- oral arms: two crossed frilly ribbons
    def ribbon(seed):
        def f(face, x, y, w, h):
            if face in ("top", "bottom"):
                return None
            # wavy frilled edges: the left and right borders bulge on alternate pairs of rows
            wave = ((y + seed) // 2) % 2
            if (x == 0 and wave) or (x == w - 1 and not wave):
                return None
            c = mix(base, light, 0.25 + 0.5 * (y / max(1, h - 1)))
            if x in (0, w - 1):
                c = mix(c, light, 0.5)
            return (*c, 205)
        return f
    m.box("arms", -2, 0, 0, 4, 11, 0, ribbon(0))
    m.box("arms", 0, 0, -2, 0, 11, 4, ribbon(1))
    m.box("arms", -1, 0, -1, 2, 2, 2, (*mix(base, light, 0.5), 210))

    # ---- ten tentacles around the rim, three segments each, curling slightly, glowing tips
    N = 10

    def strand(tip):
        def f(face, x, y, w, h):
            if face in ("top", "bottom"):
                return (*tent, 220)
            if tip and y >= h - 2:
                return (*light, 255)
            return (*tent, 205 if (y + x) % 3 else 165)
        return f
    tips =lambda f, x, y, w, h: (*glow, 255) if f not in ("top", "bottom") and y >= h - 2 else None
    for i in range(N):
        a = math.tau * (i + 0.5) / N
        sx, sz = math.cos(a), math.sin(a)
        tx, tz = round(sx * 4.8, 1), round(sz * 4.8, 1)
        s1, s2, s3 = f"t{i}a", f"t{i}b", f"t{i}c"
        curl = 6 if i % 2 else -5
        m.part(s1, "skirt", pivot=(tx, 0.5, tz), rot=(round(sz * 8, 1), 0, round(-sx * 8, 1)))
        m.part(s2, s1, pivot=(0, 5, 0), rot=(round(-sz * 6 + curl * sx, 1), 0, round(sx * 6 + curl * sz, 1)))
        m.part(s3, s2, pivot=(0, 5, 0), rot=(round(-sz * 4 - curl * sx, 1), 0, round(sx * 4 - curl * sz, 1)))
        m.box(s1, -0.5, 0, -0.5, 1, 5, 1, strand(False))
        m.box(s2, -0.5, 0, -0.5, 1, 5, 1, strand(False))
        m.box(s3, -0.5, 0, -0.5, 1, 4 + (i % 3) * 2, 1, strand(True), glow=tips)

    # ------------------------------------------------------------------ animations
    L = 2.4
    idle = m.anim("idle", L)
    # pulse: the bell squeezes, shoots up, overshoots and relaxes
    idle.scale("bell", (0, (1, 1, 1)), (0.35, (0.8, 1.14, 0.8)), (0.85, (1.07, 0.92, 1.07)), (1.5, (1, 1, 1)),
               (L, (1, 1, 1)))
    lift = ((0, (0, 0, 0)), (0.45, (0, 1.6, 0)), (1.5, (0, 0.6, 0)), (L, (0, 0, 0)))
    idle.pos("bell", *lift)
    idle.pos("skirt", (0, (0, 0, 0)), (0.55, (0, 1.3, 0)), (1.6, (0, 0.6, 0)), (L, (0, 0, 0)))
    idle.scale("skirt", (0, (1, 1, 1)), (0.35, (0.82, 1, 0.82)), (0.85, (1.06, 1, 1.06)), (1.5, (1, 1, 1)),
               (L, (1, 1, 1)))
    idle.rot("arms", (0, (0, 0, 0)), (0.6, (4, 20, -3)), (1.4, (-3, 40, 4)), (L, (0, 0, 0)))
    for i in range(N):
        a = math.tau * (i + 0.5) / N
        sx, sz = math.cos(a), math.sin(a)
        ph = (i * 0.37) % 1.0 * 0.3

        def out(k):
            return (round(sz * k, 2), 0, round(-sx * k, 2))
        # flare out while the bell squeezes, then trail inward as it rises, and drift back (a wave down the strand)
        idle.rot(f"t{i}a", (0, out(2)), (0.3 + ph * 0.5, out(14)), (0.9 + ph, out(-6)), (1.7 + ph, out(1)), (L, out(2)))
        idle.rot(f"t{i}b", (0, out(1)), (0.45 + ph * 0.5, out(-4)), (1.1 + ph, out(-8)), (1.9 + ph * 0.5, out(4)),
                 (L, out(1)))
        idle.rot(f"t{i}c", (0, out(-2)), (0.6 + ph * 0.5, out(-6)), (1.3 + ph, out(8)), (2.1, out(-3)), (L, out(-2)))
    return m
