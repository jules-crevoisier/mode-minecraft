"""Entity model DSL: parts, cubes, automatic UV packing, painted textures and keyframe animations.

A model written here becomes three things (see tools/gen_models.py):
  * a Java ``EntityModel`` with ``createBodyLayer()`` and baked ``AnimationDefinition``s,
  * a texture (and an optional emissive "glow" texture) painted face by face,
  * preview renders (tools/wf/model_render.py) so the shape can be judged without the game.

Coordinates are Minecraft *model space*, in pixels (16 = one block):
  * ``+x`` is the creature's LEFT, ``-x`` its right,
  * ``-y`` is UP (y grows downward), the ground is ``y = 24`` for parts hung on the root,
  * ``-z`` is FORWARD (the face looks toward -z).
Use ``m.part("body", pivot=(0, 24, 0))`` for the root bone (pivot on the ground) and give its
children negative y offsets, exactly like the vanilla Warden model.

Rotations are in degrees here (converted to radians in Java). Part rotation order is Minecraft's:
x first, then y, then z (``Quaternionf.rotationZYX(z, y, x)``).

Animations: ``idle`` (looping, always playing) and ``walk`` (looping, driven by walking speed) are
special; every other animation is an *action* triggered by the entity (attacks, roars, deaths) and
gets an index in declaration order. Rotation keyframes are degrees added to the rest pose, position
keyframes are pixels with y pointing UP (vanilla ``posVec`` flips it), scale keyframes are factors.
"""
import random

from .png import Canvas
from .texgen import mix, mul

FACES = ("down", "up", "west", "north", "east", "south")
# readable aliases: "top" is the visual top (model -y), "front" faces -z, "right" is -x (the creature's right)
ALIAS = {"top": "down", "bottom": "up", "right": "west", "front": "north", "left": "east", "back": "south"}
NAMES = {v: k for k, v in ALIAS.items()}
SHADE = {"top": 1.12, "bottom": 0.72, "front": 1.0, "back": 0.86, "left": 0.92, "right": 0.92}
FACE_ID = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _face_rects(u, v, w, h, d):
    """Texture rectangles of a cube's faces (Minecraft's standard unwrap), keyed by readable name."""
    return {
        "top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h), "back": (u + d + w + d, v + d, w, h),
    }


class Cube:
    def __init__(self, part, origin, size, paint, glow, grow, seed):
        self.part = part
        self.origin = origin  # min corner relative to the part pivot (pixels)
        self.size = size      # integer w, h, d
        self.paint = paint
        self.glow = glow
        self.grow = grow
        self.seed = seed
        self.uv = None

    @property
    def uv_size(self):
        w, h, d = self.size
        return 2 * (w + d), h + d


class Part:
    def __init__(self, name, parent, pivot, rot, scale):
        self.name = name
        self.parent = parent
        self.pivot = pivot
        self.rot = rot
        self.scale = scale
        self.cubes = []
        self.children = []


class Anim:
    def __init__(self, name, length, loop):
        self.name = name
        self.length = length
        self.loop = loop
        self.channels = []  # (part, target, [(t, (x, y, z), interp)])

    def _channel(self, target, part, keys):
        frames = []
        for k in keys:
            t, vec = k[0], k[1]
            interp = k[2] if len(k) > 2 else "smooth"
            if interp not in ("smooth", "linear"):
                raise ValueError(f"{self.name}/{part}: interpolation must be 'smooth' or 'linear'")
            frames.append((float(t), tuple(float(c) for c in vec), interp))
        frames.sort(key=lambda f: f[0])
        self.channels.append((part, target, frames))
        return self

    def rot(self, part, *keys):
        """Rotation keyframes: (time_s, (x_deg, y_deg, z_deg)[, 'linear'|'smooth'])."""
        return self._channel("rotation", part, keys)

    def pos(self, part, *keys):
        """Position keyframes in pixels, y pointing UP: (time_s, (x, y, z)[, interp])."""
        return self._channel("position", part, keys)

    def scale(self, part, *keys):
        """Scale keyframes as factors (1 = unchanged): (time_s, (sx, sy, sz)[, interp])."""
        return self._channel("scale", part, keys)

    def sample(self, t):
        """Offsets at time t (seconds) exactly as KeyframeAnimation computes them.

        Returns {part: {"rotation": (rx, ry, rz) degrees, "position": (x, y_up, z), "scale": (dx, dy, dz)}}.
        """
        if self.loop and self.length > 0:
            t = t % self.length
        out = {}
        for part, target, frames in self.channels:
            idx = 0
            for i, f in enumerate(frames):  # first index with t <= timestamp, minus one
                if t <= f[0]:
                    idx = i
                    break
            else:
                idx = len(frames)
            prev = max(0, idx - 1)
            nxt = min(len(frames) - 1, prev + 1)
            if nxt != prev:
                alpha = min(1.0, max(0.0, (t - frames[prev][0]) / (frames[nxt][0] - frames[prev][0])))
            else:
                alpha = 0.0
            if frames[nxt][2] == "linear":
                a, b = frames[prev][1], frames[nxt][1]
                vec = tuple(a[i] + (b[i] - a[i]) * alpha for i in range(3))
            else:
                p0 = frames[max(0, prev - 1)][1]
                p1, p2 = frames[prev][1], frames[nxt][1]
                p3 = frames[min(len(frames) - 1, nxt + 1)][1]
                vec = tuple(_catmull(alpha, p0[i], p1[i], p2[i], p3[i]) for i in range(3))
            if target == "scale":
                vec = tuple(c - 1.0 for c in vec)
            slot = out.setdefault(part, {})
            prev_vec = slot.get(target, (0.0, 0.0, 0.0))
            slot[target] = tuple(prev_vec[i] + vec[i] for i in range(3))
        return out


def _catmull(a, p0, p1, p2, p3):
    return 0.5 * (2 * p1 + (p2 - p0) * a + (2 * p0 - 5 * p1 + 4 * p2 - p3) * a * a
                  + (3 * p1 - p0 - 3 * p2 + p3) * a * a * a)


class Model:
    """A creature model. ``name`` is the entity id (snake_case)."""

    def __init__(self, name, seed=1, shadow=0.6, walk_speed=1.0, walk_scale=1.0, head="head", render="entityCutout",
                 variants=None, glow_pulse=0.0):
        self.name = name
        # RenderTypes factory of the model ("entityTranslucent" for see-through jellies)
        self.render = render
        # texture variants: the module's build(variant) repaints the same cubes; variant 0 is <name>.png, the others
        # <name>_<variant>.png, picked by AnimatedMob.modelVariant()
        self.variants = list(variants or [])
        # > 0: the glow layer pulses (alpha 0.55..1 at this angular speed per tick)
        self.glow_pulse = glow_pulse
        self.seed = seed
        self.shadow = shadow
        self.walk_speed = walk_speed
        self.walk_scale = walk_scale
        self.head = head  # part that follows the look direction (None to disable)
        self.parts = {}
        self.roots = []
        self.anims = {}
        self.tex_size = None
        self._cube_seed = seed * 1000

    # ---------------------------------------------------------------- building
    def part(self, name, parent=None, pivot=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        if name in self.parts or name == "root":
            raise ValueError(f"{self.name}: duplicate or reserved part name '{name}'")
        p = Part(name, self.parts[parent] if parent else None, tuple(pivot), tuple(rot), tuple(scale))
        self.parts[name] = p
        if p.parent:
            p.parent.children.append(p)
        else:
            self.roots.append(p)
        return name

    def box(self, part, x, y, z, w, h, d, paint, glow=None, grow=0.0):
        """Add a cube to ``part``: min corner (x, y, z) relative to the pivot, integer size w x h x d.

        ``paint``/``glow``: an RGB tuple, a function ``f(face, x, y, w, h) -> rgb | rgba | None`` (face is
        one of top/bottom/front/back/left/right, x/y are texel coordinates inside that face), or a dict
        mapping face names (or "side" for the four sides, "*" for the rest) to either of those.
        """
        for v in (w, h, d):
            if int(v) != v or v < 0:
                raise ValueError(f"{self.name}/{part}: cube sizes must be non-negative integers, got {(w, h, d)}")
        self._cube_seed += 1
        self.parts[part].cubes.append(Cube(self.parts[part], (x, y, z), (int(w), int(h), int(d)),
                                           paint, glow, grow, self._cube_seed))

    def anim(self, name, length, loop=False):
        if name in self.anims:
            raise ValueError(f"{self.name}: duplicate animation '{name}'")
        a = Anim(name, float(length), loop or name in ("idle", "walk"))
        self.anims[name] = a
        return a

    @property
    def actions(self):
        return [a for n, a in self.anims.items() if n not in ("idle", "walk")]

    def all_cubes(self):
        out = []

        def walk(p):
            out.extend(p.cubes)
            for c in p.children:
                walk(c)
        for r in self.roots:
            walk(r)
        return out

    # ---------------------------------------------------------------- UV packing
    def pack(self):
        """Shelf-pack every cube's unwrap into the smallest power-of-two texture that fits."""
        cubes = sorted(self.all_cubes(), key=lambda c: (-c.uv_size[1], -c.uv_size[0]))
        for width in (32, 64, 128, 256, 512, 1024):
            x = y = shelf = 0
            ok = True
            for c in cubes:
                cw, ch = c.uv_size
                if cw > width:
                    ok = False
                    break
                if x + cw > width:
                    x, y, shelf = 0, y + shelf, 0
                c.uv = (x, y)
                x += cw
                shelf = max(shelf, ch)
            height = y + shelf
            if ok and height <= width:
                h = 16
                while h < height:
                    h *= 2
                self.tex_size = (width, h)
                return self.tex_size
        raise ValueError(f"{self.name}: model too big to pack into a 1024 texture")

    # ---------------------------------------------------------------- textures
    def _paint_layer(self, which):
        tw, th = self.tex_size
        cv = Canvas(tw, th)
        any_px = False
        for c in self.all_cubes():
            spec = c.paint if which == "paint" else c.glow
            if spec is None:
                continue
            rng = random.Random(c.seed)
            w, h, d = c.size
            for face, (fx, fy, fw, fh) in _face_rects(c.uv[0], c.uv[1], w, h, d).items():
                fn = _face_spec(spec, face)
                if fn is None:
                    continue
                for yy in range(fh):
                    for xx in range(fw):
                        col = fn(face, xx, yy, fw, fh) if callable(fn) else fn
                        if col is None:
                            continue
                        if which == "paint":
                            f = SHADE[face] * (1 + rng.uniform(-0.045, 0.045))
                            if face not in ("top", "bottom") and (yy == fh - 1) and fh > 2:
                                f *= 0.86  # contact shadow along the bottom edge of every side
                            rgb = mul(col[:3], f)
                        else:
                            rgb = tuple(col[:3])
                        a = col[3] if len(col) > 3 else 255
                        cv.set(fx + xx, fy + yy, (*rgb, a))
                        any_px = True
        return cv if any_px else None

    def textures(self):
        if self.tex_size is None:
            self.pack()
        return self._paint_layer("paint"), self._paint_layer("glow")


def _face_spec(spec, face):
    if isinstance(spec, dict):
        if face in spec:
            return spec[face]
        if face in ("front", "back", "left", "right") and "side" in spec:
            return spec["side"]
        return spec.get("*")
    return spec


# ---------------------------------------------------------------- paint helpers
def speckle(base, var=0.08, seed=0, dark=None, freq=5):
    """Base colour with deterministic speckle and optional darker blotches."""
    def f(face, x, y, w, h):
        r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791) ^ (FACE_ID[face] * 2654435761)) & 0xFFFF
        k = 1 + ((r % 1000) / 1000 - 0.5) * 2 * var
        c = mul(base, k)
        if dark and r % freq == 0:
            c = mix(c, dark, 0.5)
        return c
    return f


def bands(rows, axis="y"):
    """Stripes along the face: rows = [(count, colour_or_fn), ...] from top (or left)."""
    def f(face, x, y, w, h):
        pos = y if axis == "y" else x
        acc = 0
        for n, c in rows:
            acc += n
            if pos < acc:
                return c(face, x, y, w, h) if callable(c) else c
        last = rows[-1][1]
        return last(face, x, y, w, h) if callable(last) else last
    return f


def framed(inner, rim, width=1):
    """Plate with a darker/lighter rim (armour plates, panels)."""
    def f(face, x, y, w, h):
        if x < width or y < width or x >= w - width or y >= h - width:
            return rim(face, x, y, w, h) if callable(rim) else rim
        return inner(face, x, y, w, h) if callable(inner) else inner
    return f


def only(faces, spec):
    """Paint only the given faces (others transparent)."""
    def f(face, x, y, w, h):
        if face not in faces:
            return None
        return spec(face, x, y, w, h) if callable(spec) else spec
    return f


def dots(points, colour, fallback=None):
    """Explicit texels on given faces: points = {(face, x, y), ...}."""
    pts = set(points)

    def f(face, x, y, w, h):
        if (face, x, y) in pts:
            return colour
        if fallback is None:
            return None
        return fallback(face, x, y, w, h) if callable(fallback) else fallback
    return f
