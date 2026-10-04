#!/usr/bin/env python3
"""Draw the mod's logo (mods list) and pack icon from the Clockwork Citadel preview render.
Needs Pillow and build/previews/clockwork_citadel__citadel.png (run gen_structures.py first)."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
BRASS, BRASS_DARK, INK = (233, 186, 82), (138, 96, 36), (24, 20, 18)


def citadel(height):
    img = Image.open(os.path.join(ROOT, "build", "previews", "clockwork_citadel__citadel.png")).convert("RGBA")
    bg = img.getpixel((0, 0))
    mask = Image.new("L", img.size, 0)
    px, mp = img.load(), mask.load()
    for y in range(img.height):
        for x in range(img.width):
            if sum(abs(a - b) for a, b in zip(px[x, y][:3], bg[:3])) > 24:
                mp[x, y] = 255
            r, g, b = px[x, y][:3]
            if r > 150 and b > 150 and g < 90:  # the preview renderer's "unknown block" magenta: mod pipes
                px[x, y] = (184 * r // 255, 115 * r // 255, 51 * r // 255, 255)
    img.putalpha(mask)
    img = img.crop(mask.getbbox())
    w = round(img.width * height / img.height)
    return img.resize((w, height), Image.LANCZOS)


def gradient(size, top, bottom):
    g = Image.new("RGB", size)
    d = ImageDraw.Draw(g)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        d.line([(0, y), (size[0], y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g


def gear(draw, cx, cy, r, teeth, fill):
    import math
    pts = []
    for i in range(teeth * 4):
        a = i / (teeth * 4) * math.tau
        rr = r if (i // 2) % 2 == 0 else r * 0.82
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    draw.polygon(pts, fill=fill)
    draw.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=(0, 0, 0, 0))


def logo():
    w, h = 480, 192
    img = gradient((w, h), (38, 32, 30), (16, 14, 14)).convert("RGBA")
    deco = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gear(ImageDraw.Draw(deco), 70, 150, 90, 12, (233, 186, 82, 28))
    gear(ImageDraw.Draw(deco), 210, 30, 50, 9, (233, 186, 82, 20))
    img = Image.alpha_composite(img, deco)
    c = citadel(h - 8)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([w - c.width - 30, 30, w + 10, h + 40], fill=(255, 179, 71, 70))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(24)))
    img.alpha_composite(c, (w - c.width - 4, h - c.height))
    d = ImageDraw.Draw(img)
    title = ImageFont.truetype(FONT, 50)
    sub = ImageFont.truetype(FONT, 15)
    d.text((24 + 2, 52 + 3), "Wayfarers", font=title, fill=INK)
    d.text((24, 52), "Wayfarers", font=title, fill=BRASS)
    d.line([(26, 116), (264, 116)], fill=BRASS_DARK, width=2)
    d.text((26, 126), "explore · build · fight together", font=sub, fill=(215, 195, 161))
    d.rectangle([0, 0, w - 1, h - 1], outline=BRASS_DARK, width=3)
    return img.convert("RGB")


def icon():
    s = 128
    img = gradient((s, s), (52, 44, 40), (18, 16, 16)).convert("RGBA")
    c = citadel(s - 6)
    img.alpha_composite(c, ((s - c.width) // 2, s - c.height))
    ImageDraw.Draw(img).rectangle([0, 0, s - 1, s - 1], outline=BRASS_DARK, width=3)
    return img.convert("RGB")


if __name__ == "__main__":
    logo().save(os.path.join(RES, "logo.png"))
    icon().save(os.path.join(RES, "pack.png"))
    print("wrote logo.png and pack.png")
