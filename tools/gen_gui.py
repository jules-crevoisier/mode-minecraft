#!/usr/bin/env python3
"""Generate the Wayfarers GUI theme (brass, riveted iron and parchment) as GUI-atlas sprites.

Sprites land in assets/wayfarers/textures/gui/sprites/ (referenced in Java as wayfarers:<name>) with
nine-slice .mcmeta files, so every panel/button scales cleanly to any size. ``--mockup`` also renders
build/previews/gui/*.png mockups of the screens with the real sprites, for review.
"""
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "src", "main", "resources", "assets", "wayfarers", "textures", "gui", "sprites")
PREVIEW = os.path.join(ROOT, "build", "previews", "gui")


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# --- palette (tools/STYLE_STEAMPUNK.md) ---------------------------------------------------------------
BRASS_HI = hexc("F1D48A")
BRASS_LT = hexc("D9B25E")
BRASS = hexc("B58A45")
BRASS_DK = hexc("7C5A2B")
BRASS_SH = hexc("4E3819")
IRON = hexc("2B2320")
IRON_LT = hexc("3E3430")
IRON_DK = hexc("17120F")
SOOT = hexc("0F0C0A")
PARCH = hexc("E3D0A8")
PARCH_DK = hexc("C9B184")
PARCH_EDGE = hexc("A88D5E")
INK = hexc("3B2A1A")
AMBER = hexc("FFB347")
AETHER = hexc("3FD0FF")
TEAL = hexc("2EE6C5")
VERDIGRIS = hexc("43B3AE")


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


class Sprite:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.im.load()
        self.w, self.h = w, h

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def frame(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.set(x, y0, c)
            self.set(x, y1, c)
        for y in range(y0, y1 + 1):
            self.set(x0, y, c)
            self.set(x1, y, c)

    def bevel(self, x0, y0, x1, y1, hi, lo):
        for x in range(x0, x1 + 1):
            self.set(x, y0, hi)
            self.set(x, y1, lo)
        for y in range(y0, y1 + 1):
            self.set(x0, y, hi)
            self.set(x1, y, lo)

    def rivet(self, x, y):
        self.set(x, y, BRASS_HI)
        self.set(x + 1, y, BRASS_LT)
        self.set(x, y + 1, BRASS_LT)
        self.set(x + 1, y + 1, BRASS_SH)

    def save(self, name, nine=None, stretch=False):
        path = os.path.join(OUT, name + ".png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.im.save(path)
        if nine is not None:
            meta = {"gui": {"scaling": {"type": "nine_slice", "width": self.w, "height": self.h,
                                        "border": nine, "stretch_inner": stretch}}}
            with open(path + ".mcmeta", "w") as f:
                json.dump(meta, f, indent=2)
        return self


def brass_band(s, x0, y0, x1, y1, width):
    """A bevelled brass band ``width`` px thick just inside the given rectangle."""
    for i in range(width):
        t = i / max(1, width - 1)
        hi = mix(BRASS_HI, BRASS, t)
        lo = mix(BRASS_DK, BRASS, t * 0.6)
        s.bevel(x0 + i, y0 + i, x1 - i, y1 - i, hi, lo)


def parchment_fill(s, x0, y0, x1, y1, seed):
    rng = random.Random(seed)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n = rng.random()
            c = PARCH if n > 0.18 else mix(PARCH, PARCH_DK, 0.5 + rng.random() * 0.5)
            if rng.random() < 0.025:
                c = mix(c, PARCH_EDGE, 0.5)
            s.set(x, y, c)


def iron_fill(s, x0, y0, x1, y1, seed, base=IRON):
    rng = random.Random(seed)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n = rng.random()
            s.set(x, y, base if n > 0.2 else mix(base, IRON_LT if n > 0.1 else IRON_DK, 0.6))


# --- sprites ------------------------------------------------------------------------------------------------
def panel():
    """Main window: soot outline, riveted brass frame, inner shadow, parchment. 64x64, border 9."""
    s = Sprite(64, 64)
    parchment_fill(s, 9, 9, 54, 54, 1)
    s.frame(0, 0, 63, 63, SOOT)
    iron_fill(s, 1, 1, 62, 62, 2)
    parchment_fill(s, 9, 9, 54, 54, 1)
    brass_band(s, 2, 2, 61, 61, 4)
    s.frame(6, 6, 57, 57, IRON_DK)
    s.frame(7, 7, 56, 56, IRON)
    s.bevel(8, 8, 55, 55, PARCH_EDGE, mix(PARCH, PARCH_DK, 0.3))
    for x, y in ((3, 3), (59, 3), (3, 59), (59, 59)):
        s.rivet(x, y)
    for x in range(14, 50, 12):
        s.rivet(x, 3)
        s.rivet(x, 59)
    for y in range(14, 50, 12):
        s.rivet(3, y)
        s.rivet(59, y)
    return s.save("panel", nine=9)


def inset():
    """Dark iron well for lists and slots. 32x32, border 4."""
    s = Sprite(32, 32)
    iron_fill(s, 0, 0, 31, 31, 3, base=hexc("221B18"))
    s.bevel(0, 0, 31, 31, IRON_DK, BRASS_DK)
    s.bevel(1, 1, 30, 30, SOOT, IRON_LT)
    return s.save("inset", nine=4)


def parchment_card():
    """Small parchment card with a thin brass edge. 32x32, border 4."""
    s = Sprite(32, 32)
    parchment_fill(s, 0, 0, 31, 31, 4)
    s.frame(0, 0, 31, 31, BRASS_DK)
    s.bevel(1, 1, 30, 30, hexc("F3E6C6"), PARCH_EDGE)
    return s.save("card", nine=4)


def button(name, hi, lo, text_glow=None):
    """Brass plate button 40x20, border 4."""
    s = Sprite(40, 20)
    for y in range(20):
        t = y / 19
        c = mix(hi, lo, t)
        for x in range(40):
            s.set(x, y, c)
    s.frame(0, 0, 39, 19, SOOT)
    s.bevel(1, 1, 38, 18, mix(hi, (255, 255, 255, 255), 0.35), mix(lo, SOOT, 0.4))
    s.rivet(2, 2)
    s.rivet(36, 2)
    s.rivet(2, 16)
    s.rivet(36, 16)
    if text_glow:
        s.bevel(1, 1, 38, 18, text_glow, text_glow)
    return s.save(name, nine=4)


def rows():
    for name, fill, edge in (("row", None, None), ("row_hover", hexc("FFFFFF", 28), hexc("D9B25E", 120)),
                             ("row_selected", hexc("B58A45", 70), BRASS_LT)):
        s = Sprite(32, 16)
        if fill:
            s.rect(0, 0, 31, 15, fill)
        if edge:
            s.frame(0, 0, 31, 15, edge)
        s.save(name, nine=2)


def title_plate():
    """Engraved brass name plate 64x18, border 6."""
    s = Sprite(64, 18)
    for y in range(18):
        c = mix(BRASS_LT, BRASS_DK, y / 17)
        for x in range(64):
            s.set(x, y, c)
    s.frame(0, 0, 63, 17, SOOT)
    s.bevel(1, 1, 62, 16, BRASS_HI, BRASS_SH)
    s.rect(3, 3, 60, 14, mix(BRASS, BRASS_DK, 0.25))
    s.bevel(3, 3, 60, 14, BRASS_SH, BRASS_HI)
    s.rivet(1, 7)
    s.rivet(61, 7)
    return s.save("title_plate", nine=6)


def scroll():
    s = Sprite(6, 16)
    s.rect(0, 0, 5, 15, BRASS)
    s.bevel(0, 0, 5, 15, BRASS_HI, BRASS_SH)
    s.set(2, 7, BRASS_SH)
    s.set(3, 7, BRASS_SH)
    s.set(2, 9, BRASS_SH)
    s.set(3, 9, BRASS_SH)
    s.save("scroll_thumb", nine=2)
    t = Sprite(6, 16)
    t.rect(0, 0, 5, 15, IRON_DK)
    t.bevel(0, 0, 5, 15, SOOT, IRON_LT)
    t.save("scroll_track", nine=2)


def icon(name, art, colors):
    """16x16 icon from a character map."""
    s = Sprite(16, 16)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch in colors:
                s.set(x, y, colors[ch])
    s.save("icon/" + name)


GLOBE = [
    "................",
    ".....oooooo.....",
    "...oohhggggoo...",
    "..ohhggwwggggo..",
    "..ohgggwwwgbbo..",
    ".ohggggwwbbbbbo.",
    ".ogggbbbbbbggbo.",
    ".ogggbbbbbgggbo.",
    ".obbbbbbbgggggo.",
    ".obbggbbbbggbbo.",
    ".obgggbbbbbbbbo.",
    "..obggbbbggbbo..",
    "..obbbbbgggbdo..",
    "...oobbbbbddo...",
    ".....oooooo.....",
    "................",
]
STAR = [
    "................",
    ".......oo.......",
    "......ohho......",
    "......ohyo......",
    ".....ohyyyo.....",
    "oooooohyyyoooooo",
    "ohhhhhyyyyyyyydo",
    ".ohyyyyyyyyyydo.",
    "..ohyyyyyyyydo..",
    "...oyyyyyyydo...",
    "...ohyyyyyydo...",
    "..ohyyydyyyydo..",
    "..oyyddoodyyyo..",
    ".oyddo....odydo.",
    ".odo........odo.",
    "................",
]
PIN = [
    "................",
    ".....oooooo.....",
    "....ohhrrrro....",
    "...ohrrrrrrro...",
    "...orrrwwrrro...",
    "...orrwwwwrro...",
    "...orrwwwwrro...",
    "...orrrwwrrdo...",
    "....orrrrrddo...",
    ".....orrrddo....",
    "......orddo.....",
    "......ordo......",
    ".......oo.......",
    "................",
    "................",
    "................",
]
QUILL = [
    "................",
    "............oo..",
    "...........owwo.",
    "..........owwwo.",
    ".........owwwo..",
    "........owwwwo..",
    ".......owwwwo...",
    "......owwwwo....",
    ".....owwwwo.....",
    "....oowwwo......",
    "....obbwo.......",
    "...obbbo........",
    "...obbo.........",
    "..obo...........",
    ".oo.............",
    "................",
]
EYE = [
    "................",
    "................",
    "................",
    "....oooooooo....",
    "..oohhppppppoo..",
    ".ohppppggppppdo.",
    "ohpppgggggppppdo",
    "opppggkkkggpppdo",
    "opppggkkkggpppdo",
    "ohpppgggggppppdo",
    ".ohppppggppppdo.",
    "..oopppppppdoo..",
    "....oooooooo....",
    "................",
    "................",
    "................",
]


CHECK = [
    "................",
    "................",
    "............ooo.",
    "...........oggo.",
    "..........oggdo.",
    ".........oggdo..",
    "..ooo...oggdo...",
    ".oggo..oggdo....",
    ".odggooggdo.....",
    "..odgggggdo.....",
    "...odgggdo......",
    "....odgdo.......",
    ".....odo........",
    "......o.........",
    "................",
    "................",
]
LOCK = [
    "................",
    ".....oooooo.....",
    "....ossssssо....",
    "....os....so....",
    "....os....so....",
    "...oooooooooo...",
    "...obbbbbbbbo...",
    "...obhhhhhhbo...",
    "...obhbkkbhbo...",
    "...obhbkkbhbo...",
    "...obhhkkhhbo...",
    "...obhhhhhhbo...",
    "...obbbbbbbbo...",
    "...oooooooooo...",
    "................",
    "................",
]
HOURGLASS = [
    "................",
    "...oooooooooo...",
    "...obbbbbbbbo...",
    "....oyyyyyyo....",
    "....oyyyyyyo....",
    ".....oyyyyo.....",
    "......oyyo......",
    ".......oo.......",
    "......o..o......",
    ".....o.yy.o.....",
    "....o.yyyy.o....",
    "....oyyyyyyo....",
    "...obbbbbbbbo...",
    "...oooooooooo...",
    "................",
    "................",
]
ORB = [
    "................",
    "................",
    "......oooo......",
    ".....ohhggo.....",
    "....ohhgggyo....",
    "...ohggggyyyo...",
    "...ohgggyyyyo...",
    "...oggggyyyyo...",
    "...oggyyyyydo...",
    "....oyyyyydo....",
    ".....oyyddo.....",
    "......oooo......",
    "................",
    "................",
    "................",
    "................",
]
FLAG = [
    "................",
    "..oo............",
    "..owoooooooo....",
    "..owrrrrrrrro...",
    "..owrrhhrrrro...",
    "..owrrrrrrro....",
    "..owrrrrrrrro...",
    "..owoooooooo....",
    "..ow............",
    "..ow............",
    "..ow............",
    "..ow............",
    ".owwo...........",
    ".oooo...........",
    "................",
    "................",
]


def icons():
    icon("done", CHECK, {"o": SOOT, "g": hexc("7CE35A"), "d": hexc("2F8A2A")})
    icon("lock", [r.replace("о", "o") for r in LOCK], {"o": SOOT, "s": hexc("A8A8B0"), "b": hexc("B58A45"),
                                                       "h": hexc("D9B25E"), "k": hexc("2B1B0C")})
    icon("progress", HOURGLASS, {"o": SOOT, "b": hexc("7C5A2B"), "y": hexc("F6C343")})
    icon("xp", ORB, {"o": SOOT, "h": hexc("F4FFB0"), "g": hexc("B6F24A"), "y": hexc("6FD02A"), "d": hexc("3E7E14")})
    icon("track", FLAG, {"o": SOOT, "w": hexc("C9B184"), "r": hexc("E0483B"), "h": hexc("FF9A8A")})
    icon("overworld", GLOBE, {"o": SOOT, "h": hexc("BFF1FF"), "g": hexc("4FAE4A"), "w": hexc("E8F6FF"),
                              "b": hexc("2F7FD8"), "d": hexc("1C4F8F")})
    icon("nether", GLOBE, {"o": SOOT, "h": hexc("FFD18A"), "g": hexc("F36A1D"), "w": hexc("FFE07A"),
                           "b": hexc("8E1E1E"), "d": hexc("4E0E0E")})
    icon("end", EYE, {"o": SOOT, "h": hexc("E9D7FF"), "p": hexc("B98BE8"), "g": hexc("2EBF8F"),
                      "k": hexc("0B2E24"), "d": hexc("6B3FA0")})
    icon("pin", STAR, {"o": SOOT, "h": hexc("FFF4B0"), "y": hexc("F6C343"), "d": hexc("B07D1A")})
    icon("pin_off", STAR, {"o": hexc("1A1512", 160), "h": hexc("7A6E60", 160), "y": hexc("5A4F45", 160),
                           "d": hexc("3A322C", 160)})
    icon("here", PIN, {"o": SOOT, "h": hexc("FFC9B8"), "r": hexc("E0483B"), "w": hexc("FFF4E8"),
                       "d": hexc("8E1E1E")})
    icon("rename", QUILL, {"o": SOOT, "w": hexc("F4F1E8"), "b": hexc("3B2A1A")})


# --- mockup ---------------------------------------------------------------------------------------------------
def nine(img_path, w, h, border):
    src = Image.open(img_path).convert("RGBA")
    sw, sh = src.size
    b = border
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def tile(box, dst):
        piece = src.crop(box)
        pw, ph = piece.size
        x0, y0, x1, y1 = dst
        for yy in range(y0, y1, ph):
            for xx in range(x0, x1, pw):
                out.alpha_composite(piece.crop((0, 0, min(pw, x1 - xx), min(ph, y1 - yy))), (xx, yy))

    tile((0, 0, b, b), (0, 0, b, b))
    tile((sw - b, 0, sw, b), (w - b, 0, w, b))
    tile((0, sh - b, b, sh), (0, h - b, b, h))
    tile((sw - b, sh - b, sw, sh), (w - b, h - b, w, h))
    tile((b, 0, sw - b, b), (b, 0, w - b, b))
    tile((b, sh - b, sw - b, sh), (b, h - b, w - b, h))
    tile((0, b, b, sh - b), (0, b, b, h - b))
    tile((sw - b, b, sw, sh - b), (w - b, b, w, h - b))
    tile((b, b, sw - b, sh - b), (b, b, w - b, h - b))
    return out


def sp(name):
    return os.path.join(OUT, name + ".png")


class Mock:
    """Draws at GUI scale 1 then upscales 3x, like Minecraft at GUI scale 3."""

    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), hexc("4A6A3A"))
        self.d = ImageDraw.Draw(self.im)
        try:
            self.font = ImageFont.truetype("/mnt/skills/examples/canvas-design/canvas-fonts/PixelifySans-Medium.ttf", 9)
        except OSError:
            self.font = ImageFont.load_default()

    def nine(self, name, x, y, w, h, border):
        self.im.alpha_composite(nine(sp(name), w, h, border), (x, y))

    def icon(self, name, x, y):
        self.im.alpha_composite(Image.open(sp("icon/" + name)).convert("RGBA"), (x, y))

    def text(self, s, x, y, c, shadow=True, center=False, right=False):
        w = self.d.textlength(s, font=self.font)
        if center:
            x -= w / 2
        if right:
            x -= w
        if shadow:
            self.d.text((x + 1, y + 1), s, font=self.font, fill=(0, 0, 0, 140))
        self.d.text((x, y), s, font=self.font, fill=c)

    def save(self, name):
        os.makedirs(PREVIEW, exist_ok=True)
        big = self.im.resize((self.im.width * 3, self.im.height * 3), Image.NEAREST)
        big.save(os.path.join(PREVIEW, name + ".png"))


def mockup_waystones():
    W, H = 300, 210
    m = Mock(W + 40, H + 40)
    ox, oy = 20, 20
    m.nine("panel", ox, oy, W, H, 9)
    m.nine("title_plate", ox + W // 2 - 70, oy - 4, 140, 18, 6)
    m.text("Pierres de passage", ox + W // 2, oy, hexc("2B1B0C"), shadow=False, center=True)
    lx, ly, lw, lh = ox + 12, oy + 30, 172, H - 44
    m.nine("inset", lx, ly - 14, lw, 13, 4)
    m.text("Rechercher...", lx + 5, ly - 12, hexc("8C7B66"), shadow=False)
    m.nine("inset", lx, ly, lw, lh, 4)
    rows_ = [("here", "Avant-poste de la Guilde", "ici", "overworld", True, False),
             ("overworld", "Ferme du Nord", "312 m", "overworld", False, True),
             ("overworld", "Monastère des cimes", "1,4 km", "overworld", False, True),
             ("overworld", "Plaines (1204, -88)", "640 m", "overworld", False, False),
             ("nether", "Bastion de basalte", "Nether", "nether", False, False),
             ("end", "Nid du vide", "End", "end", False, False)]
    for i, (ic, name, dist, dim, here, pinned) in enumerate(rows_):
        ry = ly + 4 + i * 20
        if i == 1:
            m.nine("row_selected", lx + 3, ry, lw - 12, 19, 2)
        elif i == 3:
            m.nine("row_hover", lx + 3, ry, lw - 12, 19, 2)
        m.icon(ic, lx + 6, ry + 2)
        m.text(name, lx + 25, ry + 4, hexc("F3E3C0") if not here else hexc("9FE6FF"))
        m.text(dist, lx + lw - 30, ry + 4, hexc("B9A98E"), right=True)
        m.icon("pin" if pinned else "pin_off", lx + lw - 27, ry + 2)
    m.nine("scroll_track", lx + lw - 9, ly + 3, 6, lh - 6, 2)
    m.nine("scroll_thumb", lx + lw - 9, ly + 3, 6, 40, 2)
    # details card
    cx, cy, cw, ch = lx + lw + 8, oy + 16, W - lw - 32, H - 30
    m.nine("card", cx, cy, cw, ch, 4)
    m.icon("overworld", cx + cw // 2 - 8, cy + 6)
    m.text("Ferme du Nord", cx + cw // 2, cy + 26, INK, shadow=False, center=True)
    m.text("Overworld", cx + cw // 2, cy + 38, hexc("6E5A40"), shadow=False, center=True)
    m.text("X 412  Y 71  Z -980", cx + cw // 2, cy + 52, hexc("6E5A40"), shadow=False, center=True)
    m.text("à 312 m", cx + cw // 2, cy + 64, hexc("6E5A40"), shadow=False, center=True)
    m.nine("button_hover", cx + 6, cy + 86, cw - 12, 22, 4)
    m.text("Voyager", cx + cw // 2, cy + 92, hexc("FFFFFF"), center=True)
    m.nine("button", cx + 6, cy + 112, cw - 12, 18, 4)
    m.text("Épingler", cx + cw // 2, cy + 116, hexc("FFF4DC"), center=True)
    m.nine("button", cx + 6, cy + 134, cw - 12, 18, 4)
    m.text("Renommer", cx + cw // 2, cy + 138, hexc("FFF4DC"), center=True)
    m.save("waystones")


SORT_G = [
    "..........",
    ".kkkkkkk..",
    "..........",
    ".kkkkk....",
    "..........",
    ".kkk....k.",
    ".......kkk",
    ".k.....kkk",
    "........k.",
    "..........",
]
TAKE_G = [
    "....kk....",
    "....kk....",
    "....kk....",
    "....kk....",
    ".kkkkkkkk.",
    "..kkkkkk..",
    "...kkkk...",
    "....kk....",
    ".........",
    "kkkkkkkkkk",
]
DEPOSIT_G = [
    "kkkkkkkkkk",
    "..........",
    "....kk....",
    "...kkkk...",
    "..kkkkkk..",
    ".kkkkkkkk.",
    "....kk....",
    "....kk....",
    "....kk....",
    "....kk....",
]
NEARBY_G = [
    "..........",
    ".kkkkkkkk.",
    ".k......k.",
    ".kkkkkkkk.",
    ".k..kk..k.",
    ".k......k.",
    ".kkkkkkkk.",
    "..........",
    "k.k.k.k.k.",
    "..........",
]


def small_buttons():
    for name, hi, lo in (("button_small", BRASS_LT, BRASS_DK), ("button_small_hover", BRASS_HI, BRASS)):
        b = Sprite(12, 12)
        for y in range(12):
            c = mix(hi, lo, y / 11)
            for x in range(12):
                b.set(x, y, c)
        b.frame(0, 0, 11, 11, SOOT)
        b.bevel(1, 1, 10, 10, mix(hi, (255, 255, 255, 255), 0.35), mix(lo, SOOT, 0.4))
        b.save(name, nine=3)
    for name, art in (("sort", SORT_G), ("take", TAKE_G), ("deposit", DEPOSIT_G), ("nearby", NEARBY_G)):
        g = Sprite(10, 10)
        for y, row in enumerate(art):
            for x, ch in enumerate(row):
                if ch == "k":
                    g.set(x, y, hexc("2B1B0C"))
        g.save("glyph/" + name)


def bars():
    b = Sprite(16, 6)
    b.rect(0, 0, 15, 5, IRON_DK)
    b.bevel(0, 0, 15, 5, SOOT, IRON_LT)
    b.save("bar_back", nine=2)
    f = Sprite(16, 6)
    for y in range(6):
        c = mix(hexc("F6D77A"), hexc("B5832A"), y / 5)
        for x in range(16):
            f.set(x, y, c)
    f.save("bar_fill", nine=1)
    g = Sprite(16, 6)
    for y in range(6):
        c = mix(hexc("A6F07A"), hexc("3E9A2A"), y / 5)
        for x in range(16):
            g.set(x, y, c)
    g.save("bar_done", nine=1)


def mockup_quests():
    W, H = 384, 228
    m = Mock(W + 40, H + 40)
    ox, oy = 20, 20
    m.nine("panel", ox, oy, W, H, 9)
    m.nine("title_plate", ox + W // 2 - 60, oy - 5, 120, 18, 6)
    m.text("Journal de quêtes", ox + W // 2, oy - 1, hexc("2B1B0C"), shadow=False, center=True)
    chapters = [("Premiers pas", 8, 8), ("Explorateur", 9, 27), ("Profondeurs", 3, 17), ("Nether", 0, 15), ("End", 0, 14)]
    for i, (name, d, t) in enumerate(chapters):
        x, y = ox + 12, oy + 22 + i * 34
        m.nine("inset", x, y, 104, 30, 4)
        if i == 1:
            m.nine("row_selected", x + 2, y + 2, 100, 26, 2)
        m.icon("overworld" if i < 3 else ("nether" if i == 3 else "end"), x + 4, y + 4)
        m.text(name, x + 23, y + 4, hexc("F6C343") if i == 1 else hexc("F3E3C0"))
        m.nine("bar_back", x + 23, y + 18, 74, 6, 2)
        fill = int(72 * d / t)
        if fill:
            m.nine("bar_done" if d == t else "bar_fill", x + 24, y + 19, fill, 4, 1)
    lx, ly = ox + 122, oy + 22
    m.nine("inset", lx, ly, 132, H - 34, 4)
    qs = [("Avant-poste de la Guilde", "done"), ("Tour de guet en ruine", "done"), ("Monastère des cimes", "progress"),
          ("Le Sonneur de Glas", "lock"), ("Oasis du désert", None), ("Bibliothèque oubliée", None),
          ("Camp de bandits", "done"), ("Phare côtier", None)]
    for i, (q, st) in enumerate(qs):
        ry = ly + 3 + i * 22
        if i == 2:
            m.nine("row_selected", lx + 3, ry, 120, 21, 2)
        m.icon("overworld", lx + 5, ry + 2)
        col = hexc("A6F07A") if st == "done" else hexc("7E7262") if st == "lock" else hexc("F3E3C0")
        m.text(q[:17], lx + 24, ry + 6, col)
        if st:
            m.icon(st, lx + 105, ry + 2)
        if i == 2:
            m.icon("track", lx + 89, ry + 2)
    cx, cy, cw, ch = ox + 260, oy + 18, W - 272, H - 28
    m.nine("card", cx, cy, cw, ch, 4)
    m.icon("overworld", cx + cw // 2 - 8, cy + 6)
    m.text("Monastère des cimes", cx + cw // 2, cy + 26, INK, shadow=False, center=True)
    for i, l in enumerate(["Trouve le monastère", "perché sur les cimes", "enneigées et sonne", "sa grande cloche."]):
        m.text(l, cx + 5, cy + 40 + i * 9, hexc("6E5A40"), shadow=False)
    m.text("Objectifs : 1 / 2", cx + 5, cy + 82, INK, shadow=False)
    m.nine("bar_back", cx + 5, cy + 92, cw - 10, 6, 2)
    m.nine("bar_fill", cx + 6, cy + 93, (cw - 12) // 2, 4, 1)
    m.text("Récompenses", cx + 5, cy + ch - 52, INK, shadow=False)
    m.icon("xp", cx + 5, cy + ch - 42)
    m.text("100", cx + 21, cy + ch - 37, hexc("3E7E14"), shadow=False)
    m.icon("pin", cx + 45, cy + ch - 42)
    m.nine("button_hover", cx + 6, cy + ch - 26, cw - 12, 20, 4)
    m.text("Ne plus suivre", cx + cw // 2, cy + ch - 21, hexc("FFFFFF"), center=True)
    m.save("quests")


def mockup_guide(shots=(("wonders", 0), ("wonders", 1), ("brass_golem", 0), ("keys", 0), ("chisel", 1)), lang="fr"):
    """The Wayfarer's Manual (GuideScreen) at its smallest size (384 x 232), one PNG per (page, sheet): the page
    split into sheets by wf.guide.layout(), which mirrors GuideScreen.paginate() with Minecraft's glyph advances.
    Text is drawn glyph by glyph on those advances, so line breaks and lengths match the game."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wf import guide
    S = 3
    W, H = 384, guide.BOOK_H
    li = 1 if lang == "fr" else 0
    pages = {p[0]: p for p in guide.PAGES}
    cats = [(c, t[li]) for c, _i, t in guide.CATEGORIES]
    toc = []
    for c, ct in cats:
        toc.append(("cat", c, ct))
        toc += [("page", p[0], p[3][li]) for p in guide.PAGES if p[1] == c]
    try:
        ttf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except OSError:
        ttf = ImageFont.load_default()
    item_dir = os.path.join(ROOT, "src", "main", "resources", "assets", "wayfarers", "textures", "item")
    total = sum(len(guide.layout(p[3][li], [x[li] for x in p[4]], bool(p[5]), lang=li)) for p in guide.PAGES)
    for pid, part in shots:
        _pid, _cat, icon_id, titles, paras, items = pages[pid]
        sheets, compact = guide.layout(titles[li], [x[li] for x in paras], bool(items), lang=li, with_header=True)
        part = min(part, len(sheets) - 1)
        m = Mock(W + 40, H + 40)
        ox, oy = 20, 20
        m.nine("panel", ox, oy, W, H, 9)
        m.nine("title_plate", ox + W // 2 - 60, oy - 5, 120, 18, 6)
        tx, ty, tw, th = ox + 14, oy + 24, 120, H - 36
        m.nine("inset", tx, ty, tw, th, 4)
        rows_ = (th - 6) // 11
        sel = [i for i, r in enumerate(toc) if r[1] == pid and r[0] == "page"][0]
        scroll = max(0, min(len(toc) - rows_, sel - rows_ // 2))
        px, pw = ox + 142, W - 156
        card_bottom = oy + H - 36
        m.nine("card", px, oy + 18, pw, card_bottom - oy - 18, 4)
        m.nine("scroll_track", tx + tw - 9, ty + 3, 6, th - 6, 2)
        thumb = max(12, (th - 6) * rows_ // len(toc))
        m.nine("scroll_thumb", tx + tw - 9, ty + 3 + (th - 6 - thumb) * scroll // max(1, len(toc) - rows_), 6, thumb, 2)
        if scroll <= sel < scroll + rows_:
            m.nine("row_selected", tx + 3, ty + 4 + (sel - scroll) * 11 - 1, tw - 12, 11, 2)
        last = part == len(sheets) - 1
        m.nine("button", px + 4, oy + H - 32, 60, 18, 4)
        m.nine("button" if total > 1 else "button_disabled", px + pw - 64, oy + H - 32, 60, 18, 4)
        texts = []  # (x, y, text, colour, shadow) at GUI scale 1

        def icon_at(rid, x, y, scale=1):
            name = rid.split(":")[1]
            path = os.path.join(item_dir, name + ".png")
            if rid.startswith("wayfarers:") and os.path.exists(path):
                im = Image.open(path).convert("RGBA").crop((0, 0, 16, 16)).resize((16 * scale, 16 * scale), Image.NEAREST)
                m.im.alpha_composite(im, (x, y))
            else:
                m.d.rectangle((x + 1, y + 1, x + 16 * scale - 2, y + 16 * scale - 2), outline=(110, 90, 64, 255))
                texts.append((x + 2, y + 4 * scale, name[:3], (110, 90, 64, 255), False))

        if part == 0 and not compact:
            icon_at(icon_id, px + pw // 2 - 16, oy + 24, 2)
            title_lines = guide.wrap(titles[li], pw - 12)
            y = oy + 60
            for t in title_lines:
                texts.append((px + pw // 2 - guide.text_width(t) // 2, y, t, INK, False))
                y += 10
            body = oy + 60 + len(title_lines) * 10 + 4
        else:
            icon_at(icon_id, px + 6, oy + 23)
            title_lines = guide.wrap(titles[li] + (" " + guide.UI["guide.wayfarers.continued"][li] if part else ""), pw - 52)
            y = oy + 25
            for t in title_lines:
                texts.append((px + 26, y, t, INK, False))
                y += 10
            body = oy + 25 + max(1, len(title_lines)) * 10 + 6
        if len(sheets) > 1:
            s = f"{part + 1}/{len(sheets)}"
            texts.append((px + pw - 6 - guide.text_width(s), oy + (25 if part or compact else 23), s, hexc("6E5A40"), False))
        y = body
        for line in sheets[part]:
            if line is None:
                y += guide.PARA_GAP
            else:
                texts.append((px + 7, y, line, hexc("6E5A40"), False))
                y += guide.TEXT_LINE
        if part == 0 and items:
            for i, rid in enumerate(items):
                icon_at(rid, px + 7 + i * 20, card_bottom - 22)
        for i in range(rows_):
            if scroll + i >= len(toc):
                break
            kind, _id, label = toc[scroll + i]
            yy = ty + 4 + i * 11 + 1
            if kind == "cat":
                texts.append((tx + 5, yy, label, hexc("F6C343"), True))
            else:
                while guide.text_width(label) > tw - 24 and len(label) > 1:
                    label = label[:-4] + "..."
                texts.append((tx + 12, yy, label, hexc("9FE6FF") if i + scroll == sel else hexc("F3E3C0"), True))
        texts.append((ox + W // 2 - guide.text_width("Manuel du Voyageur") // 2, oy, "Manuel du Voyageur", hexc("2B1B0C"), False))
        texts.append((px + 34 - 3, oy + H - 27, "<", hexc("FFF4DC"), True))
        nxt = ">" if last else guide.UI["guide.wayfarers.more"][li]
        texts.append((px + pw - 34 - guide.text_width(nxt) // 2, oy + H - 27, nxt, hexc("FFF4DC"), True))
        pg = f"{sum(len(guide.layout(p[3][li], [x[li] for x in p[4]], bool(p[5]), lang=li)) for p in guide.PAGES[:guide.PAGES.index(pages[pid])]) + part + 1} / {total}"
        texts.append((px + pw // 2 - guide.text_width(pg) // 2, oy + H - 27, pg, hexc("6E5A40"), False))
        big = m.im.resize((m.im.width * S, m.im.height * S), Image.NEAREST)
        d = ImageDraw.Draw(big)
        for x, y, s, c, shadow in texts:
            cx = x
            for ch in s:
                if shadow:
                    d.text(((cx + 1) * S, (y + 1) * S - 3), ch, font=ttf, fill=(0, 0, 0, 160))
                d.text((cx * S, y * S - 3), ch, font=ttf, fill=c)
                cx += guide.char_width(ch)
        os.makedirs(PREVIEW, exist_ok=True)
        big.save(os.path.join(PREVIEW, f"guide_{pid}_{part + 1}.png"))


def main():
    panel()
    inset()
    parchment_card()
    button("button", BRASS_LT, BRASS_DK)
    button("button_hover", BRASS_HI, BRASS, text_glow=None)
    button("button_disabled", hexc("6B625A"), hexc("3A332E"))
    rows()
    title_plate()
    scroll()
    icons()
    bars()
    small_buttons()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wf import worldmap  # minimap / world map frames, markers and glyphs
    worldmap.sprites(sys.modules[__name__])
    if "--mockup" in sys.argv:
        worldmap.mockups(sys.modules[__name__])
        mockup_waystones()
        mockup_quests()
        mockup_guide()
    print("gui sprites written to", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
