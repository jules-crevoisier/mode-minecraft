"""Shared steampunk paint for the automatons (tools/STYLE_STEAMPUNK.md): brass, copper, dark iron, cream dials,
amber and aether glow, riveted plates, see-through cogs and clock faces.

Not a creature: the automaton models (clockwork_spider, steam_drone, brass_golem, grand_clockmaker) import it.
"""
import math

from ..texgen import mix, mul

# ---------------------------------------------------------------- palette
BRASS = (190, 150, 70)
BRASS_L = (240, 206, 120)
BRASS_D = (124, 90, 40)
BRASS_DD = (78, 54, 24)
COPPER = (186, 112, 58)
COPPER_L = (228, 156, 96)
COPPER_D = (118, 64, 34)
VERD = (72, 168, 156)
VERD_D = (44, 112, 106)
IRON = (58, 52, 52)
IRON_L = (96, 88, 84)
IRON_D = (34, 30, 30)
SOOT = (24, 21, 22)
CREAM = (222, 204, 168)
CREAM_D = (176, 156, 122)
AMBER = (255, 178, 70)
AMBER_L = (255, 230, 160)
AMBER_D = (210, 110, 30)
AETHER = (70, 214, 255)
AETHER_L = (200, 248, 255)
MAHOGANY = (108, 62, 42)
MAHOGANY_D = (70, 38, 26)
LEATHER = (112, 38, 32)
GLASS = (150, 196, 200)


def n(x, y, seed):
    """Deterministic hash noise in [0, 1)."""
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


def _call(c, face, x, y, w, h):
    return c(face, x, y, w, h) if callable(c) else c


# ---------------------------------------------------------------- metal plates
def plate(base=BRASS, rim=None, hi=None, rivet=None, seed=0, grad=0.22, rivet_step=0, worn=0.05):
    """A riveted metal plate: lit top edge, darker rim, vertical light gradient, faint wear, rivets in the corners
    (and every ``rivet_step`` texels along the top and bottom rows)."""
    rim = rim or mul(base, 0.62)
    hi = hi or mix(base, (255, 245, 220), 0.35)
    rivet = rivet or mix(base, (255, 245, 220), 0.5)

    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(base, 0.7)
        if face == "top":
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                return mix(base, hi, 0.5)
            return mul(base, 1.08 + (n(x, y, seed) - 0.5) * 0.06)
        if w > 2 and h > 2:
            if y == 0:
                return hi
            if x == 0 or x == w - 1 or y == h - 1:
                return rim
        if w > 4 and h > 4 and y in (1, h - 2) and (x in (1, w - 2) or (rivet_step and x % rivet_step == 1)):
            return rivet
        k = 1 + grad * (0.5 - y / max(1, h)) + (n(x, y, seed) - 0.5) * 0.07
        c = mul(base, k)
        if n(x // 2, y // 2, seed + 7) < worn:
            c = mul(c, 0.84)
        return c
    return f


def brass(seed=0, **kw):
    return plate(BRASS, BRASS_D, BRASS_L, seed=seed, **kw)


def copper(seed=0, **kw):
    return plate(COPPER, COPPER_D, COPPER_L, seed=seed, **kw)


def iron(seed=0, **kw):
    return plate(IRON, IRON_D, IRON_L, rivet=BRASS, seed=seed, **kw)


def rod(base=IRON, seed=0):
    """A round bar: a light streak down the middle of each side, dark edges."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 1.1 if face == "top" else 0.7)
        if w <= 1:
            return mul(base, 1.0 + (n(x, y, seed) - 0.5) * 0.08)
        k = 1.2 if x == w // 2 else (0.8 if x in (0, w - 1) else 1.0)
        return mul(base, k + (n(x, y, seed) - 0.5) * 0.06)
    return f


def bands(base, band, every=3, seed=0):
    """Horizontal hoops (a boiler, a barrel): darker band every ``every`` texels, with rivets on the bands."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 1.08 if face == "top" else 0.7)
        if y % every == every - 1:
            return mix(band, BRASS_L, 0.4) if x % 3 == 1 else band
        k = 1.12 - 0.22 * ((y % every) / every) + (n(x, y, seed) - 0.5) * 0.06
        return mul(base, k)
    return f


def soot(base=IRON, seed=0, amount=0.35):
    """Sooty metal: darker toward the top (smokestacks, exhausts)."""
    def f(face, x, y, w, h):
        if face == "top":
            return SOOT
        k = y / max(1, h - 1)
        c = mix(SOOT, base, min(1.0, k + 0.2))
        if n(x, y, seed) < amount * 0.3:
            c = mul(c, 0.8)
        return c
    return f


# ---------------------------------------------------------------- see-through cogs and dials
def cog_mask(x, y, w, h, teeth=8, hub=0.0, phase=0.0, spokes=0):
    """True when texel (x, y) of a w x h face is part of a cog: a disc with ``teeth`` square teeth, an optional
    hub hole of radius ``hub`` (fraction of the radius) and ``spokes`` cut-out windows."""
    cx, cy = (w - 1) / 2, (h - 1) / 2
    dx, dy = x - cx, y - cy
    r = math.hypot(dx, dy)
    outer = min(w, h) / 2
    body = outer * 0.74
    a = math.atan2(dy, dx) + phase
    tooth = (a / (2 * math.pi) * teeth) % 1.0
    if r > outer + 0.05:
        return False
    if r > body + 0.15 and not (0.2 <= tooth <= 0.75):
        return False
    if hub and r < outer * hub:
        return False
    if spokes and outer * (hub + 0.15) < r < body - 1.0:
        s = (a / (2 * math.pi) * spokes) % 1.0
        if 0.25 < s < 0.75:
            return False
    return True


def cog(base=BRASS, dark=None, teeth=8, hub=0.25, spokes=0, phase=0.0, edges=False, faces=("front", "back")):
    """Paint for a flat cog (a w x h x 1 cube): only the cog's shape is opaque on the front and back, the rest is
    see-through (cutout). The edge faces stay transparent unless ``edges``. For a cog standing sideways (a 1 x h x d
    cube) pass ``faces=("left", "right")``; lying flat (w x 1 x d), ``faces=("top", "bottom")``."""
    dark = dark or mul(base, 0.6)

    def f(face, x, y, w, h):
        if face in faces:
            if not cog_mask(x, y, w, h, teeth, hub, phase, spokes):
                return None
            cx, cy = (w - 1) / 2, (h - 1) / 2
            r = math.hypot(x - cx, y - cy)
            outer = min(w, h) / 2
            if r > outer * 0.74:
                return mix(base, BRASS_L, 0.25) if y < cy else mul(base, 0.85)   # teeth, lit from above
            if hub and r < outer * (hub + 0.18):
                return dark                                                     # hub ring
            if abs(r - outer * 0.6) < 0.6:
                return mul(base, 0.78)                                          # rim groove
            return mul(base, 1.08 - 0.18 * (y / max(1, h)))
        if not edges:
            return None
        return mul(base, 0.7)
    return f


def dial(rim=BRASS, face_c=CREAM, marks=IRON, hub=BRASS_D, numerals=12):
    """A clock face on the front of a square cube: brass rim, cream face, hour marks; other faces brass."""
    def f(face, x, y, w, h):
        if face != "front":
            return plate(rim, BRASS_D, BRASS_L)(face, x, y, w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        outer = min(w, h) / 2
        if r > outer + 0.3:
            return mul(rim, 0.7)                                  # corners: dark brass bezel
        if r > outer - 1.1:
            return mix(rim, BRASS_L, 0.35) if dy < 0 else rim     # rim
        if r < 1.0:
            return hub
        ang = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
        step = 360 / numerals
        k = min(ang % step, step - ang % step)
        if r > outer - 2.3 and k * math.pi / 180 * r < 0.55:
            return marks                                          # hour marks
        return mul(face_c, 1.04 - 0.12 * (y / max(1, h)) + (n(x, y, 3) - 0.5) * 0.04)
    return f


def lens(core=AMBER, rim=BRASS, glass=AMBER_L):
    """A round glowing lens on the front face (paint): rim, coloured glass, a white glint."""
    def f(face, x, y, w, h):
        if face != "front":
            return plate(rim, BRASS_D, BRASS_L)(face, x, y, w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = math.hypot(x - cx, y - cy)
        outer = min(w, h) / 2
        if r > outer - _rim_width(w) and w > 2:
            return rim
        if x == int(cx - 0.5) and y == int(cy - 0.5) and w > 2:
            return glass
        return core
    return f


def _rim_width(w):
    """Rim thickness of a round lens: only the corners on small lenses, a full ring on big ones."""
    return 0.3 if w <= 4 else 0.6


def lens_glow(core=AMBER, glass=AMBER_L, rim_px=True):
    """Glow layer for :func:`lens`: everything inside the rim shines."""
    def f(face, x, y, w, h):
        if face != "front":
            return None
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = math.hypot(x - cx, y - cy)
        outer = min(w, h) / 2
        if rim_px and r > outer - _rim_width(w) and w > 2:
            return None
        if x == int(cx - 0.5) and y == int(cy - 0.5) and w > 2:
            return glass
        return core
    return f


def grate(frame=IRON, slot=SOOT, fire=None):
    """A furnace grate on the front face: vertical bars; ``fire`` paints the slots (use the same as glow)."""
    def f(face, x, y, w, h):
        if face != "front":
            return iron()(face, x, y, w, h)
        if x == 0 or y == 0 or x == w - 1 or y == h - 1:
            return mix(frame, BRASS, 0.5)
        if x % 2 == 0:
            return frame
        return fire or slot
    return f


def grate_glow(fire=AMBER, hot=AMBER_L):
    def f(face, x, y, w, h):
        if face != "front" or x == 0 or y == 0 or x == w - 1 or y == h - 1 or x % 2 == 0:
            return None
        return hot if y >= h - 2 else fire
    return f


def only_front(spec, rest):
    """``spec`` on the front face, ``rest`` everywhere else."""
    def f(face, x, y, w, h):
        return _call(spec if face == "front" else rest, face, x, y, w, h)
    return f


def gauge(rim=BRASS, needle=(170, 30, 30)):
    """A tiny pressure gauge (front face): cream dial and a red needle."""
    def f(face, x, y, w, h):
        if face != "front":
            return plate(rim, BRASS_D, BRASS_L)(face, x, y, w, h)
        if x in (0, w - 1) or y in (0, h - 1):
            return rim
        if (x - 1, y - 1) in ((1, 0), (0, 0)) or (w <= 3 and x == 1 and y == 1):
            return needle
        return CREAM
    return f


KEY_BOW = [".###...###.",
           "#####.#####",
           "##..###..##",
           "##..###..##",
           "#####.#####",
           ".###...###."]


def key_bow(light=BRASS_L, mid=BRASS, dark=BRASS_D, rows=KEY_BOW):
    """A wind-up key's figure-of-eight bow: two rings joined at the stem, pixel art on an 11 x 6 x 1 cube (the flat
    faces carry the shape, the thin edges follow it)."""
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            xx = x if face == "front" else w - 1 - x
            if rows[y][xx] != "#":
                return None
            if y == 0 or rows[y - 1][xx] != "#":
                return light
            return dark if y == h - 1 or (y + 1 < h and rows[y + 1][xx] != "#") else mid
        if face in ("top", "bottom"):
            return mid if rows[0 if face == "top" else -1][x] == "#" else None
        return dark if rows[y][0] == "#" else None
    return f
