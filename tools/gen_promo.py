#!/usr/bin/env python3
"""Store-page art for CurseForge / Modrinth: a square project icon, a wide banner and a gallery of in-game
screenshots, into build/promo/. Built from the structure renders of the wiki (build/wiki/img/s, run gen_wiki.py
first) and the CI client screenshots (previews release)."""
import math
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from gen_logo import BRASS, BRASS_DARK, INK, gear, gradient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build", "promo")
RENDERS = os.path.join(ROOT, "build", "wiki", "img", "s")
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PREVIEWS = "https://github.com/jules-crevoisier/mode-minecraft/releases/download/previews-ccr-127dc262-tsdn10/"
SHOTS = ["mega_structure", "hud_minimap", "world_map", "guild_terminal", "machine_harvester", "quest_journal",
         "talent_tree", "creatures", "waystone", "manual_welcome"]


def cutout(name, height):
    """A structure render with its flat background removed, scaled to `height`."""
    img = Image.open(os.path.join(RENDERS, name + ".webp")).convert("RGBA")
    bg = img.getpixel((0, 0))
    px = img.load()
    mask = Image.new("L", img.size, 0)
    mp = mask.load()
    for y in range(img.height):
        for x in range(img.width):
            if sum(abs(a - b) for a, b in zip(px[x, y][:3], bg[:3])) > 30:
                mp[x, y] = 255
    img.putalpha(mask.filter(ImageFilter.MinFilter(3)))
    img = img.crop(img.getchannel("A").getbbox())
    w = round(img.width * height / img.height)
    return img.resize((w, height), Image.LANCZOS)


def backdrop(size):
    w, h = size
    img = gradient(size, (46, 38, 34), (12, 11, 12)).convert("RGBA")
    deco = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(deco)
    for cx, cy, r, t, a in [(0.08, 0.85, 0.42, 14, 26), (0.92, 0.12, 0.25, 10, 20), (0.55, 1.05, 0.3, 12, 16)]:
        gear(d, cx * w, cy * h, r * h, t, (233, 186, 82, a))
    return Image.alpha_composite(img, deco)


def glow(img, box, colour=(255, 179, 71, 90), blur=40):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=colour)
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(blur)))


def frame(img, width):
    d = ImageDraw.Draw(img)
    w, h = img.size
    d.rectangle([0, 0, w - 1, h - 1], outline=BRASS_DARK, width=width)
    d.rectangle([width, width, w - 1 - width, h - 1 - width], outline=(90, 62, 26), width=max(1, width // 3))
    r = width * 2
    for x, y in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]:  # rivets
        d.ellipse([x - width * 0.7, y - width * 0.7, x + width * 0.7, y + width * 0.7], fill=BRASS)


def icon(s=512):
    img = backdrop((s, s))
    img = glow(img, [s * 0.1, s * 0.15, s * 0.9, s * 0.95], blur=60)
    c = cutout("clockwork_citadel", int(s * 0.78))
    if c.width > s * 0.94:
        c = c.resize((int(s * 0.94), int(c.height * s * 0.94 / c.width)), Image.LANCZOS)
    img.alpha_composite(c, ((s - c.width) // 2, s - c.height - int(s * 0.05)))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(SERIF, int(s * 0.17))
    text = "B"
    tw = d.textlength(text, font=f)
    x, y = s * 0.07, s * 0.03
    d.text((x + 4, y + 5), text, font=f, fill=INK)
    d.text((x, y), text, font=f, fill=BRASS)
    frame(img, max(4, s // 64))
    return img.convert("RGB")


def banner(w=1920, h=640):
    img = backdrop((w, h))
    img = glow(img, [w * 0.35, h * 0.05, w * 1.05, h * 1.1], blur=90)
    picks = [("clockwork_citadel", 0.95, 0.63), ("sylvan_palace", 0.62, 0.88)]
    for name, scale, xf in picks:
        try:
            c = cutout(name, int(h * scale))
        except FileNotFoundError:
            continue
        img.alpha_composite(c, (int(w * xf - c.width / 2), h - c.height - int(h * 0.03)))
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for x in range(int(w * 0.42)):  # darken behind the title
        a = int(200 * (1 - x / (w * 0.42)) ** 1.4)
        sd.line([(x, 0), (x, h)], fill=(12, 10, 10, a))
    img = Image.alpha_composite(img, shade)
    d = ImageDraw.Draw(img)
    title = ImageFont.truetype(SERIF, 130)
    sub = ImageFont.truetype(SERIF, 38)
    small = ImageFont.truetype(SANS, 28)
    d.text((86, 150), "Brasshaven", font=title, fill=INK)
    d.text((80, 144), "Brasshaven", font=title, fill=BRASS)
    d.line([(84, 300), (700, 300)], fill=BRASS_DARK, width=4)
    d.text((84, 320), "Steampunk adventure for Minecraft", font=sub, fill=(232, 214, 180))
    d.text((84, 390), "Mega-structures · machines · quests · magic\nautomatons · shared server map",
           font=small, fill=(200, 184, 150), spacing=10)
    d.text((84, h - 80), "Forge 26.2", font=small, fill=BRASS)
    frame(img, 8)
    return img.convert("RGB")


def gallery():
    out = os.path.join(OUT, "gallery")
    os.makedirs(out, exist_ok=True)
    got = []
    for name in SHOTS:
        dest = os.path.join(out, f"{name}.png")
        try:
            urllib.request.urlretrieve(PREVIEWS + f"brasshaven-shot-{name}.png", dest)
            got.append(name)
        except OSError as e:
            print(f"skip {name}: {e}")
    return got


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icon().save(os.path.join(OUT, "icon_512.png"))
    banner().save(os.path.join(OUT, "banner_1920x640.png"))
    shots = gallery()
    print(f"wrote build/promo: icon_512.png, banner_1920x640.png, {len(shots)} screenshots")
