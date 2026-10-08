"""Paint helpers shared by the peoples of the places (dwarves, sylvans, monks) and the bandits (tools/wf/denizens.py).

Every helper returns a face painter ``f(face, x, y, w, h) -> rgb | None``. ``role_only(role, wanted, spec)`` paints a
piece of gear only on the texture variants of the roles that carry it: every variant keeps the same cubes (the model
pipeline requires it), the gear of the other roles is left transparent.
"""
from ..texgen import mix, mul


def h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


def call(c, face, x, y, w, hh):
    return c(face, x, y, w, hh) if callable(c) else c


def role_only(role, wanted, spec):
    """``spec`` on the variants whose role is in ``wanted`` (a string or a tuple), transparent on the others."""
    wanted = (wanted,) if isinstance(wanted, str) else tuple(wanted)

    def f(face, x, y, w, hh):
        if role not in wanted:
            return None
        s = spec
        if isinstance(s, dict):
            s = s.get(face, s.get("side") if face in ("front", "back", "left", "right") else None)
            s = s if s is not None or face in spec else spec.get("*")
        return call(s, face, x, y, w, hh) if s is not None else None
    return f


def cloth(base, dark, seed=0, trim=None, trim_rows=(), hem=None):
    """Woven cloth hanging in soft vertical folds (a dark fold line, a lit crest), lit along the top edge, shadowed
    along the bottom, ``trim`` on the given rows (negative counts from the bottom) and a darker, dirtier hem on the
    lowest row."""
    def f(face, x, y, w, hh):
        if face in ("top", "bottom"):
            c = base if (x + y + seed) % 4 else dark
            return mul(c, 1.0 if face == "top" else 0.8)
        k = (x + h(seed, x // 3)) % 4
        c = dark if k == 0 else (mix(base, (255, 255, 255), 0.07) if k == 2 else base)
        if h(x, y, seed) % 23 == 0:
            c = mix(c, dark, 0.5)
        if y == 0 and hh > 3:
            c = mix(c, (255, 255, 255), 0.08)
        elif y == hh - 1 and hh > 3:
            c = mul(c, 0.86)
        if trim is not None and (y in trim_rows or (y - hh) in trim_rows):
            return trim
        if hem is not None and y == hh - 1:
            return hem
        return c
    return f


def leather(base, seed=0, stitch=None):
    """Worn leather: soft blotches, scuffed lighter edges, an optional stitch line down the middle of the sides."""
    def f(face, x, y, w, hh):
        r = h(x // 2, y // 2, seed) % 100
        c = mul(base, 0.92 + r / 800)
        if h(x, y, seed + 5) % 17 == 0:
            c = mix(c, (230, 210, 180), 0.18)
        if face not in ("top", "bottom") and (x == 0 or x == w - 1):
            c = mul(c, 0.86)
        if stitch is not None and face in ("front", "back") and x == w // 2 and y % 2 == 0:
            c = stitch
        return c
    return f


def chainmail(base=(150, 152, 160), dark=(78, 80, 90), seed=0):
    """Riveted rings: a checker of light rings and dark gaps, a little rust."""
    def f(face, x, y, w, hh):
        if face in ("top", "bottom"):
            return mul(base, 0.85)
        ring = (x + (y % 2)) % 2 == 0
        c = base if ring else dark
        if ring and y % 2 == 0:
            c = mix(c, (235, 236, 240), 0.25)
        if h(x, y, seed) % 23 == 0:
            c = mix(c, (150, 82, 42), 0.5)
        return c
    return f


def steel(base=(150, 154, 162), rim=(84, 86, 96), hi=(222, 226, 232), seed=0, rivets=True):
    """Polished steel plate: lit top row, dark rim, a vertical sheen, rivets on the top corners."""
    def f(face, x, y, w, hh):
        if face == "bottom":
            return mul(base, 0.7)
        if face == "top":
            return mix(base, hi, 0.3)
        if w > 2 and hh > 2:
            if y == 0:
                return hi
            if x == 0 or x == w - 1 or y == hh - 1:
                return rim
            if rivets and w > 4 and y == 1 and x in (1, w - 2):
                return mix(hi, base, 0.3)
        k = 1.0 + 0.18 * (0.5 - y / max(1, hh)) + (0.12 if x == w // 3 else 0.0)
        c = mul(base, k)
        if h(x, y, seed) % 29 == 0:
            c = mul(c, 0.86)
        return c
    return f


def wood(base=(124, 86, 52), dark=(84, 56, 34), seed=0, vertical=True):
    """Planks or a haft: grain lines along the length, a few knots."""
    def f(face, x, y, w, hh):
        if face in ("top", "bottom"):
            return mul(base, 0.95) if (x + y) % 2 else mul(dark, 1.05)
        along = x if vertical else y
        c = base if (along + h(along, 0, seed)) % 3 else mix(base, dark, 0.6)
        if h(x, y, seed + 9) % 31 == 0:
            c = dark
        return c
    return f


def skin(base, seed=0):
    def f(face, x, y, w, hh):
        if face == "bottom":
            return mul(base, 0.82)
        return base if (x + y + seed) % 7 else mul(base, 0.95)
    return f


def hair(base, seed=0, streak=None):
    """Hair or fur: vertical strands of three tones."""
    def f(face, x, y, w, hh):
        r = h(x, seed) % 3
        c = (base, mul(base, 0.84), mix(base, (255, 240, 210), 0.14))[r]
        if streak is not None and h(x, y // 3, seed + 1) % 7 == 0:
            c = streak
        if face == "bottom":
            c = mul(c, 0.8)
        return c
    return f


def braid(base, ring=None, seed=0):
    """A braid: alternating diagonal strands, with a metal ring every few rows."""
    def f(face, x, y, w, hh):
        if ring is not None and y % 4 == 3:
            return ring
        c = base if (x + y) % 2 else mul(base, 0.8)
        if face == "bottom":
            c = mul(c, 0.8)
        return c
    return f


def glowing(core, light):
    """Glow texels: the core with a lighter middle (eyes, lamps, embers)."""
    def f(face, x, y, w, hh):
        if w > 2 and hh > 2 and 0 < x < w - 1 and 0 < y < hh - 1:
            return light
        return core
    return f
