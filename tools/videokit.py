"""Drawing kit of the presentation videos (tools/make_video.py): assets, the brass and parchment look of the mod,
text, Ken Burns, clips, the simulated cursor. Everything is a pure function of its arguments, so a frame is a pure
function of time and the videos rebuild identically."""
import functools
import json
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIDEO = os.path.join(ROOT, "build", "video")
SRC = os.path.join(VIDEO, "src")
CLIPS = os.environ.get("BRASSHAVEN_VIDEO_CLIPS") or os.path.join(VIDEO, "clips")
WORK = os.path.join(VIDEO, "work")
RENDERS = os.path.join(ROOT, "build", "wiki", "img", "s")
MODELS = os.path.join(ROOT, "build", "previews", "models")
GUI = os.path.join(ROOT, "build", "previews", "gui")

W, H, FPS = 1920, 1080, 30

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# the mod's palette (tools/gen_logo.py, tools/STYLE_STEAMPUNK.md)
BRASS = (233, 186, 82)
BRASS_DARK = (138, 96, 36)
BRASS_DEEP = (90, 62, 26)
INK = (24, 20, 18)
CREAM = (242, 234, 216)
PARCHMENT = (215, 195, 161)
COPPER = (184, 115, 51)
VERDIGRIS = (67, 179, 174)
AMBER = (255, 179, 71)
AETHER = (63, 208, 255)
BG_TOP = (46, 38, 34)
BG_BOTTOM = (12, 11, 12)
DIP = (14, 12, 12)


# ------------------------------------------------------------------ easing

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(u):
    u = clamp(u)
    return 0.5 - 0.5 * math.cos(math.pi * u)


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def ease_in(u):
    u = clamp(u)
    return u ** 3


def back_out(u, s=1.4):
    u = clamp(u) - 1
    return u * u * ((s + 1) * u + s) + 1


def lerp(a, b, u):
    return a + (b - a) * u


def window(t, t0, t1, fin=0.3, fout=0.3):
    """0 -> 1 over [t0, t0 + fin], 1 until t1 - fout, then back to 0 at t1."""
    if t < t0 or t > t1:
        return 0.0
    a = ease((t - t0) / fin) if fin > 0 else 1.0
    b = ease((t1 - t) / fout) if fout > 0 else 1.0
    return min(a, b)


# ------------------------------------------------------------------ fonts and text

@functools.lru_cache(maxsize=None)
def font(path, size):
    return ImageFont.truetype(path, size)


def french(text):
    """Non-breaking spaces before the French double punctuation, so a line never starts with ':' or '!'."""
    for p in (":", "!", "?", ";", "»"):
        text = text.replace(" " + p, " " + p)
    return text.replace("« ", "« ")


def wrap(text, fnt, width):
    lines = []
    for para in french(text).split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            trial = (line + " " + w).strip()
            if fnt.getlength(trial) <= width or not line:
                line = trial
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines


def words(text):
    return len([w for w in text.replace("\n", " ").split(" ") if w.strip() and w.strip() not in ":;!?·—-«»…"])


@functools.lru_cache(maxsize=256)
def text_sprite(text, path, size, fill=CREAM, shadow=True, width=None, spacing=1.18, align="left", stroke=0):
    """Text on transparency (wrapped to width), with a soft drop shadow."""
    fnt = font(path, size)
    lines = wrap(text, fnt, width) if width else [french(text)]
    lh = int(size * spacing)
    tw = int(max(fnt.getlength(l) for l in lines)) + 8 + stroke * 2
    th = lh * (len(lines) - 1) + int(size * 1.25) + 8
    pad = 24 if shadow else 0
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        for i, l in enumerate(lines):
            x = pad + _ax(fnt, l, tw, align)
            d.text((x + 3, pad + i * lh + 4), l, font=fnt, fill=(0, 0, 0, 200), stroke_width=stroke)
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        x = pad + _ax(fnt, l, tw, align)
        d.text((x, pad + i * lh), l, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=INK)
    return img


def _ax(fnt, line, width, align):
    if align == "center":
        return (width - fnt.getlength(line)) / 2
    if align == "right":
        return width - fnt.getlength(line)
    return 0


@functools.lru_cache(maxsize=64)
def brass_title(text, size, sweep_key=0):
    """Big serif title in brass: vertical metal gradient, dark outline and a cast shadow."""
    fnt = font(SERIF_BOLD, size)
    tw = int(fnt.getlength(text)) + 40
    th = int(size * 1.35) + 40
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).text((20, 14), text, font=fnt, fill=255)
    grad = np.zeros((th, tw, 3), np.float32)
    ys = np.linspace(0, 1, th)[:, None]
    top, mid, bot = np.array((255, 226, 140)), np.array(BRASS), np.array((150, 104, 40))
    g = np.where(ys < 0.5, top + (mid - top) * (ys / 0.5), mid + (bot - mid) * ((ys - 0.5) / 0.5))
    grad[:] = g[:, None, :] if g.ndim == 2 else g
    metal = Image.fromarray(grad.astype(np.uint8), "RGB").convert("RGBA")
    metal.putalpha(mask)
    out = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((26, 24), text, font=fnt, fill=(0, 0, 0, 230))
    out = Image.alpha_composite(out, shadow.filter(ImageFilter.GaussianBlur(7)))
    edge = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(edge).text((20 + 6, 14 + 8), text, font=fnt, fill=INK + (255,))
    out = Image.alpha_composite(out, edge)
    out.alpha_composite(metal, (0, 0))
    return out


def sweep(sprite, u, width=0.12, strength=0.75):
    """A light band crossing a brass sprite (u from 0 to 1), clipped to the sprite's alpha."""
    if u <= 0 or u >= 1:
        return sprite
    w, h = sprite.size
    x = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.35
    c = lerp(-0.2, 1.2, u) * (w + h * 0.35)
    band = np.clip(1 - np.abs(x - c) / (width * w), 0, 1) ** 2 * strength
    a = np.asarray(sprite.getchannel("A"), np.float32) / 255.0
    light = Image.new("RGBA", (w, h), (255, 248, 220, 0))
    light.putalpha(Image.fromarray((band * a * 255).astype(np.uint8), "L"))
    return Image.alpha_composite(sprite, light)


# ------------------------------------------------------------------ the brass look

def gradient(size, top=BG_TOP, bottom=BG_BOTTOM):
    w, h = size
    t = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t
    return Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8), "RGB")


@functools.lru_cache(maxsize=16)
def gear_sprite(radius, teeth, colour, alpha, hole=0.36):
    s = int(radius * 2 + 8)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = s / 2
    pts = []
    for i in range(teeth * 4):
        a = i / (teeth * 4) * math.tau
        rr = radius if (i // 2) % 2 == 0 else radius * 0.84
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=colour + (alpha,))
    d.ellipse([cx - radius * 0.66, cy - radius * 0.66, cx + radius * 0.66, cy + radius * 0.66], fill=(0, 0, 0, 0))
    d.ellipse([cx - radius * 0.62, cy - radius * 0.62, cx + radius * 0.62, cy + radius * 0.62], fill=colour + (alpha // 2,))
    for k in range(5):
        a = k / 5 * math.tau
        d.line([(cx, cy), (cx + math.cos(a) * radius * 0.62, cy + math.sin(a) * radius * 0.62)], fill=colour + (alpha,),
               width=max(2, int(radius * 0.09)))
    d.ellipse([cx - radius * hole * 0.5, cy - radius * hole * 0.5, cx + radius * hole * 0.5, cy + radius * hole * 0.5],
              fill=(0, 0, 0, 0))
    return img


@functools.lru_cache(maxsize=4)
def backdrop_base():
    img = gradient((W, H)).convert("RGBA")
    # warm light from the upper right, vignette at the corners
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.exp(-(((xx - W * 0.7) / (W * 0.45)) ** 2 + ((yy - H * 0.35) / (H * 0.6)) ** 2))
    vign = np.clip(1 - (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2) * 0.35, 0.55, 1)
    arr = np.asarray(img, np.float32)
    arr[..., :3] = arr[..., :3] * vign[..., None] + np.array([90, 62, 26]) * (glow[..., None] * 0.55)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def backdrop(t, gears=True):
    """The dark brass backdrop with three slowly turning gears."""
    img = backdrop_base().copy()
    if gears:
        for (gx, gy, r, teeth, a, speed) in ((0.08, 0.86, 380, 14, 24, 6), (0.93, 0.14, 230, 10, 20, -9),
                                             (0.58, 1.06, 300, 12, 16, 7)):
            g = gear_sprite(r, teeth, BRASS, a).rotate(t * speed, resample=Image.BICUBIC)
            img.alpha_composite(g, (int(gx * W - g.width / 2), int(gy * H - g.height / 2)))
    return img


@functools.lru_cache(maxsize=128)
def plate(w, h, alpha=226, border=True, radius=14):
    """A dark riveted plate with a brass frame: the panel behind captions and cards."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([8, 10, w - 4, h - 2], radius, fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, w - 8, h - 10], radius, fill=(24, 19, 16, alpha))
    if border:
        d.rounded_rectangle([4, 4, w - 8, h - 10], radius, outline=BRASS_DARK + (255,), width=4)
        d.rounded_rectangle([11, 11, w - 15, h - 17], max(2, radius - 6), outline=BRASS_DEEP + (200,), width=2)
        for x, y in ((18, 18), (w - 22, 18), (18, h - 24), (w - 22, h - 24)):
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=BRASS + (255,))
            d.ellipse([x - 2, y - 3, x + 1, y], fill=(255, 240, 190, 255))
    return img


@functools.lru_cache(maxsize=64)
def kicker_sprite(text, colour=BRASS):
    """Small brass caps label above a caption ("TOUCHE J")."""
    return text_sprite(text.upper(), SANS_BOLD, 26, fill=colour, shadow=False)


@functools.lru_cache(maxsize=256)
def caption_sprite(text, kicker=None, width=1240, size=42):
    body = text_sprite(text, SANS_BOLD if size < 40 else SANS, size, fill=CREAM, shadow=False, width=width)
    k = kicker_sprite(kicker) if kicker else None
    pw = max(body.width, k.width if k else 0) + 72
    ph = body.height + (k.height + 2 if k else 0) + 40
    img = plate(pw, ph).copy()
    y = 22
    if k:
        img.alpha_composite(k, (36, y))
        y += k.height + 2
    img.alpha_composite(body, (34, y))
    return img


def place_caption(frame, t, t0, t1, text, kicker=None, pos="bottom", width=1240, size=42):
    """A caption that slides up into place, stays settled, then fades; returns nothing if out of its window."""
    if t < t0 or t > t1:
        return
    spr = caption_sprite(text, kicker, width, size)
    u_in = ease_out((t - t0) / 0.35)
    u_out = ease((t1 - t) / 0.3)
    a = min(u_in, u_out)
    if a <= 0.01:
        return
    x = (W - spr.width) // 2
    y = H - spr.height - 54 if pos == "bottom" else 60 if pos == "top" else (H - spr.height) // 2
    y += int((1 - u_in) * 40)
    paste(frame, spr, x, y, a)


def paste(frame, sprite, x, y, alpha=1.0):
    if alpha <= 0:
        return
    if alpha < 0.999:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(sprite, (int(round(x)), int(round(y))))


@functools.lru_cache(maxsize=64)
def keycap(label, size=96, sub=None, wide=1.0):
    """A brass keyboard key with its letter; sub is the AZERTY letter when it differs."""
    w, h = int(size * wide), size
    img = Image.new("RGBA", (w + 12, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 10, w + 4, h + 12], 14, fill=(70, 48, 20, 255))
    d.rounded_rectangle([4, 4, w + 4, h + 4], 14, fill=BRASS_DARK + (255,))
    d.rounded_rectangle([10, 8, w - 2, h - 4], 10, fill=(214, 168, 76, 255))
    d.rounded_rectangle([10, 8, w - 2, h // 2], 10, fill=(232, 192, 104, 255))
    fnt = font(SERIF_BOLD, int(size * (0.5 if len(label) <= 2 else 0.3)))
    tw = fnt.getlength(label)
    d.text(((w + 8 - tw) / 2, h * 0.16), label, font=fnt, fill=INK + (255,))
    if sub:
        f2 = font(SANS_BOLD, int(size * 0.17))
        s = "AZERTY " + sub
        d.text(((w + 8 - f2.getlength(s)) / 2, h * 0.70), s, font=f2, fill=(70, 40, 10, 255))
    return img


# ------------------------------------------------------------------ cursor

@functools.lru_cache(maxsize=4)
def cursor_sprite(scale=1.0):
    s = 3 * scale
    pts = [(0, 0), (0, 17), (4.5, 13), (7.5, 20), (10, 19), (7, 12.5), (12.5, 12.5)]
    img = Image.new("RGBA", (int(16 * s) + 12, int(22 * s) + 12), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x * s + 7, y * s + 8) for x, y in pts], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(img)
    d.polygon([(x * s + 3, y * s + 3) for x, y in pts], fill=CREAM + (255,), outline=INK + (255,), width=max(2, int(s)))
    return img


def draw_cursor(frame, x, y, press_age=None, scale=1.0):
    """The cursor tip at (x, y); press_age (seconds since the last click) draws a brass ripple."""
    if press_age is not None and 0 <= press_age < 0.5:
        u = press_age / 0.5
        r = 10 + 46 * ease_out(u)
        ring = Image.new("RGBA", (int(r * 2 + 8), int(r * 2 + 8)), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([4, 4, r * 2 + 4, r * 2 + 4], outline=AMBER + (int(230 * (1 - u)),), width=5)
        frame.alpha_composite(ring, (int(x - r - 4), int(y - r - 4)))
    spr = cursor_sprite(scale)
    if press_age is not None and 0 <= press_age < 0.14:
        spr = spr.resize((int(spr.width * 0.9), int(spr.height * 0.9)), Image.BICUBIC)
    frame.alpha_composite(spr, (int(x - 3), int(y - 3)))


class CursorPath:
    """Simulated cursor over a still: keyframes (t, x, y) in frame pixels and click times."""

    def __init__(self, keys, clicks=(), show=(0.0, 1e9)):
        self.keys = sorted(keys)
        self.clicks = sorted(clicks)
        self.show = show

    def at(self, t):
        if not self.keys or t < self.show[0] or t > self.show[1]:
            return None
        k = self.keys
        if t <= k[0][0]:
            return k[0][1], k[0][2]
        for (t0, x0, y0), (t1, x1, y1) in zip(k, k[1:]):
            if t0 <= t <= t1:
                u = ease((t - t0) / max(1e-6, t1 - t0))
                return lerp(x0, x1, u), lerp(y0, y1, u)
        return k[-1][1], k[-1][2]

    def press_age(self, t):
        ages = [t - c for c in self.clicks if c <= t]
        return min(ages) if ages else None

    def draw(self, frame, t):
        p = self.at(t)
        if p:
            draw_cursor(frame, p[0], p[1], self.press_age(t))


class TrackCursor:
    """The cursor recorded by the showcase driver: [t, x, y, pressed] in clip seconds and window pixels."""

    def __init__(self, track, window, speed=1.0, offset=0.0, size=(W, H)):
        self.track = [(float(e[0]), float(e[1]), float(e[2]), int(e[3])) for e in track]
        self.sx = size[0] / float(window[0])
        self.sy = size[1] / float(window[1])
        self.speed = speed
        self.offset = offset
        self.presses = [e[0] for a, e in zip([(0, 0, 0, 0)] + self.track, self.track) if e[3] == 1 and a[3] == 0]

    def draw(self, frame, t):
        ct = self.offset + t * self.speed
        prev = None
        for e in self.track:
            if e[0] > ct:
                break
            prev = e
        if prev is None or prev[1] < 0:
            return
        nxt = next((e for e in self.track if e[0] > ct), None)
        x, y = prev[1], prev[2]
        if nxt and nxt[1] >= 0 and nxt[0] - prev[0] < 0.2:
            u = (ct - prev[0]) / max(1e-6, nxt[0] - prev[0])
            x, y = lerp(prev[1], nxt[1], u), lerp(prev[2], nxt[2], u)
        ages = [(ct - p) / self.speed for p in self.presses if p <= ct]
        draw_cursor(frame, x * self.sx, y * self.sy, min(ages) if ages else None)

    def clicks(self):
        return [(p - self.offset) / self.speed for p in self.presses]


# ------------------------------------------------------------------ images

@functools.lru_cache(maxsize=64)
def load(path, mode="RGBA"):
    return Image.open(path).convert(mode)


def exists(path):
    return path and os.path.exists(path)


def shot(name):
    """A CI client screenshot (build/video/src/shot-<name>.png, see make_video.py --fetch)."""
    p = os.path.join(SRC, f"shot-{name}.png")
    return p if os.path.exists(p) else None


@functools.lru_cache(maxsize=32)
def cutout(name, height=None):
    """A structure render of the wiki with its flat background keyed out (cached in build/video/work)."""
    os.makedirs(WORK, exist_ok=True)
    cache = os.path.join(WORK, f"cut-{name}.png")
    if os.path.exists(cache):
        img = Image.open(cache).convert("RGBA")
    else:
        src = Image.open(os.path.join(RENDERS, name + ".webp")).convert("RGB")
        arr = np.asarray(src, np.int32)
        bg = np.median(np.concatenate([arr[:6].reshape(-1, 3), arr[-6:].reshape(-1, 3),
                                       arr[:, :6].reshape(-1, 3), arr[:, -6:].reshape(-1, 3)]), axis=0)
        dist = np.abs(arr - bg[None, None, :]).sum(axis=2)
        mask = Image.fromarray(np.where(dist > 34, 255, 0).astype(np.uint8), "L")
        mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
        img = src.convert("RGBA")
        img.putalpha(mask)
        img = img.crop(mask.getbbox())
        img.save(cache)
    if height:
        img = img.resize((round(img.width * height / img.height), height), Image.LANCZOS)
    return img


def render_exists(name):
    return os.path.exists(os.path.join(RENDERS, name + ".webp"))


@functools.lru_cache(maxsize=32)
def model_view(name, view=0):
    """The front view of a creature's model sheet (build/previews/models, tools/gen_models.py), on its own floor."""
    img = load(os.path.join(MODELS, name + ".png"))
    return img.crop((view * 360, 24, view * 360 + 360, 360))


@functools.lru_cache(maxsize=32)
def model_frames(name, row):
    """One animation row of a model sheet: five frames of 240 x 216."""
    img = load(os.path.join(MODELS, name + ".png"))
    y = 360 + row * 240 + 24
    return [img.crop((i * 240, y, i * 240 + 240, y + 216)) for i in range(5)]


def kenburns(img, t, dur, z0=1.0, z1=1.08, c0=(0.5, 0.5), c1=(0.5, 0.5), size=(W, H)):
    """A slow zoom and pan over an image, filling `size` (cover), sub-pixel smooth."""
    u = ease(t / dur) if dur > 0 else 0
    z = lerp(z0, z1, u)
    cx, cy = lerp(c0[0], c1[0], u), lerp(c0[1], c1[1], u)
    sw, sh = img.size
    ow, oh = size
    cover = max(ow / sw, oh / sh)
    scale = cover * z
    vw, vh = ow / scale, oh / scale
    x0 = clamp(cx * sw - vw / 2, 0, sw - vw)
    y0 = clamp(cy * sh - vh / 2, 0, sh - vh)
    return img.transform(size, Image.AFFINE, (1 / scale, 0, x0, 0, 1 / scale, y0), resample=Image.BICUBIC)


def fit(img, box_w, box_h):
    s = min(box_w / img.width, box_h / img.height)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


def framed(img, border=8):
    """A screenshot in a brass frame with a soft shadow."""
    w, h = img.size
    out = Image.new("RGBA", (w + border * 2 + 30, h + border * 2 + 30), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([14, 18, w + border * 2 + 14, h + border * 2 + 18], fill=(0, 0, 0, 170))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, w + border * 2 - 1, h + border * 2 - 1], fill=BRASS_DARK + (255,))
    d.rectangle([3, 3, w + border * 2 - 4, h + border * 2 - 4], outline=BRASS + (255,), width=2)
    out.paste(img.convert("RGBA"), (border, border))
    return out


# ------------------------------------------------------------------ clips (real footage)

def scenes_index():
    p = os.path.join(CLIPS, "brasshaven-showcase-scenes.json")
    if not os.path.exists(p):
        return {}, None
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for s in data.get("scenes", []):
        path = os.path.join(CLIPS, s["clip"])
        if os.path.exists(path) and s.get("duration", 0) > 1.0:
            out[s["name"]] = dict(s, path=path)
    return out, data.get("window") or [1280, 720]


class ClipReader:
    """Sequential RGB frames of a clip at 1920x1080 / 30 fps, from `start` seconds, played `speed` times faster."""

    def __init__(self, path, start=0.0, speed=1.0, size=(W, H)):
        self.size = size
        vf = f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},scale={size[0]}:{size[1]}:flags=lanczos"
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last = None

    def next(self):
        w, h = self.size
        buf = self.proc.stdout.read(w * h * 3)
        if len(buf) == w * h * 3:
            self.last = Image.frombytes("RGB", (w, h), buf).convert("RGBA")
        elif self.last is None:
            self.last = Image.new("RGBA", (w, h), DIP + (255,))
        return self.last.copy()

    def close(self):
        try:
            self.proc.stdout.close()
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass
