#!/usr/bin/env python3
"""Art review contact sheets: every item / block texture at 8x nearest-neighbour, labelled.

    python3 tools/art_sheet.py                 # build/previews/art_item_1.png ... art_block_N.png
    python3 tools/art_sheet.py --kind item --out /some/dir --tag before
    python3 tools/art_sheet.py --kind held       # 3D in-hand models (needs gen_textures + gen_assets first)

Each tile sits on the inventory-slot grey, with a 1x copy in the corner (how the sprite really reads at
16x16). Animated strips show their first frame; numbered animation frames (pocket_watch_03...) are skipped
except frame 00. Needs Pillow (preview tool only, the generators themselves stay dependency free).
"""
import argparse
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "wayfarers", "textures")
SCALE = 8
COLS = 8
ROWS = 5
SLOT = (139, 139, 139)
PAD = 6
LABEL_H = 14


def textures(kind):
    folder = os.path.join(TEX, kind)
    names = sorted(f[:-4] for f in os.listdir(folder) if f.endswith(".png"))
    out = []
    for n in names:
        m = re.match(r"(.*)_(\d\d)$", n)
        if m and m.group(2) != "00":
            continue
        out.append((n, os.path.join(folder, n + ".png")))
    return out


def tile(path):
    im = Image.open(path).convert("RGBA")
    if im.height > im.width:          # animation strip: first frame
        im = im.crop((0, 0, im.width, im.width))
    if im.width != 16:
        im = im.resize((16, 16), Image.NEAREST)
    return im


def sheet(entries, title):
    cell_w = 16 * SCALE + PAD * 2
    cell_h = 16 * SCALE + PAD * 2 + LABEL_H
    rows = (len(entries) + COLS - 1) // COLS
    img = Image.new("RGBA", (COLS * cell_w, rows * cell_h + 18), (36, 34, 40, 255))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((4, 3), title, fill=(230, 220, 190), font=font)
    for i, (name, path) in enumerate(entries):
        cx, cy = (i % COLS) * cell_w, (i // COLS) * cell_h + 18
        d.rectangle((cx + PAD - 2, cy + PAD - 2, cx + PAD + 16 * SCALE + 1, cy + PAD + 16 * SCALE + 1), fill=SLOT + (255,))
        t = tile(path)
        big = t.resize((16 * SCALE, 16 * SCALE), Image.NEAREST)
        img.alpha_composite(big, (cx + PAD, cy + PAD))
        # 1x and 2x copies in the bottom-right corner on slot grey
        small = (cx + PAD + 16 * SCALE - 50, cy + PAD + 16 * SCALE - 34)
        d.rectangle((small[0] - 1, small[1] - 1, small[0] + 50, small[1] + 34), fill=SLOT + (255,), outline=(60, 60, 60))
        img.alpha_composite(t, (small[0] + 1, small[1] + 9))
        img.alpha_composite(t.resize((32, 32), Image.NEAREST), (small[0] + 18, small[1] + 1))
        label = name if len(name) <= 22 else name[:21] + "~"
        d.text((cx + PAD, cy + PAD + 16 * SCALE + 2), label, fill=(240, 236, 220), font=font)
    return img


def held_sheet(out, tag, only=None):
    """The 3D in-hand models of wf/held3d.py and the gadgets, each with its inventory sprite, from two angles."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wf import held3d, wikirender as W
    from wf.gadgets import MODELS_3D
    J = W.JsonModels()
    ids = [i for i in list(held3d.HELD) + list(MODELS_3D) if not only or i in only]
    cell, cols = (300, 4) if only else (200, 6)
    for p in range(0, len(ids), 24):
        chunk = ids[p:p + 24]
        rows = (len(chunk) + cols - 1) // cols
        img = Image.new("RGBA", (cols * cell, rows * (cell // 2 + 30) + 18), (36, 34, 40, 255))
        d = ImageDraw.Draw(img)
        d.text((4, 3), f"3D held models {p + 1}-{p + len(chunk)} / {len(ids)}  {tag}", fill=(230, 220, 190))
        for i, iid in enumerate(chunk):
            cx, cy = (i % cols) * cell, (i // cols) * (cell // 2 + 30) + 18
            md = J.load(f"wayfarers:item/{iid}_3d")
            for k, yaw in enumerate((135, 45)):
                r = J.render(md, size=cell // 2 - 4, yaw=yaw, pitch=22, bg=(52, 54, 66), ss=2)
                img.paste(r, (cx + 2 + k * (cell // 2 - 2), cy + 2))
            spr = Image.open(os.path.join(TEX, "item", iid + ".png")).convert("RGBA")
            if spr.height > spr.width:
                spr = spr.crop((0, 0, spr.width, spr.width))
            d.rectangle((cx + 2, cy + 2, cx + 35, cy + 35), fill=SLOT + (255,))
            img.alpha_composite(spr.resize((32, 32), Image.NEAREST), (cx + 3, cy + 3))
            d.text((cx + 4, cy + cell // 2 + 2), iid[:30], fill=(240, 236, 220))
        name = os.path.join(out, f"art_held{'_' + tag if tag else ''}_{p // 24 + 1}.png")
        img.save(name)
        print(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("item", "block", "held", "all"), default="all")
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "previews"))
    ap.add_argument("--tag", default="")
    ap.add_argument("--only", default="", help="comma separated names (exact) to put on a single sheet")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.kind in ("held", "all"):
        held_sheet(args.out, args.tag, set(args.only.split(",")) if args.only else None)
        if args.kind == "held":
            return
    kinds = ("item", "block") if args.kind == "all" else (args.kind,)
    per = COLS * ROWS
    for kind in kinds:
        entries = textures(kind)
        if args.only:
            want = set(args.only.split(","))
            entries = [e for e in entries if e[0] in want]
        for p in range(0, len(entries), per):
            n = p // per + 1
            name = f"art_{kind}{'_' + args.tag if args.tag else ''}_{n}.png"
            sheet(entries[p:p + per], f"{kind} textures {p + 1}-{min(len(entries), p + per)} / {len(entries)}  {args.tag}").save(
                os.path.join(args.out, name))
            print(os.path.join(args.out, name))


if __name__ == "__main__":
    main()
