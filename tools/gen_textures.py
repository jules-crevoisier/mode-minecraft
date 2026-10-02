#!/usr/bin/env python3
"""Generate every Wayfarers texture: item sprites, block faces, armor layers, mob skins.

Everything is procedural / hand-drawn ASCII so the repository needs no binary art
sources. Run with --sheet to also write a contact sheet to build/previews.
"""
import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf.png import Canvas  # noqa: E402
from wf.sprites import ACCENTS, HANDLES, MATERIALS, SHAPES  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "wayfarers", "textures")

# item id -> (shape, material, handle, accent)
ITEMS = {
    # progression materials
    "map_fragment": ("fragment", "map", "wood", "ink"),
    "lithite_shard": ("shard", "lithite", "wood", "emerald"),
    "ancient_ember": ("ember", "ember", "wood", "ember"),
    "void_shard": ("shard", "void", "wood", "amethyst"),
    "warden_scale": ("scale", "warden", "wood", "sapphire"),
    "void_heart": ("heart", "void", "wood", "amethyst"),
    # explorer utilities
    "wayfarer_atlas": ("book", "leather", "gold", "gold"),
    "structure_compass": ("compass", "gold", "dark", "ruby"),
    "travel_backpack": ("backpack", "leather", "dark", "gold"),
    "magnet_ring": ("ring", "iron", "wood", "ruby"),
    "recall_scroll": ("scroll", "map", "wood", "sapphire"),
    # weapons
    "cartographer_blade": ("sword", "cartographer", "wood", "emerald"),
    "telluric_hammer": ("hammer", "lithite", "wood", "emerald"),
    "storm_staff": ("staff", "storm", "dark", "sapphire"),
    "ember_scythe": ("scythe", "ember", "blaze", "ember"),
    "void_spear": ("spear", "void", "purpur", "amethyst"),
    "boomerang": ("boomerang", "leather", "wood", "gold"),
    "frost_blade": ("blade", "frost", "bone", "ice"),
    "light_staff": ("staff", "light", "gold", "gold"),
    # tools
    "excavator_pickaxe": ("pickaxe", "lithite", "wood", "emerald"),
    "lumber_axe": ("axe", "iron", "wood", "gold"),
}
for prefix, mat, acc in (("explorer", "map", "emerald"), ("ember", "ember", "gold"), ("void", "void", "amethyst")):
    for piece in ("helmet", "chestplate", "leggings", "boots"):
        ITEMS[f"{prefix}_{piece}"] = (piece, mat, "wood", acc)

# spawn eggs: (base colour, spot colour)
EGGS = {
    "ruin_walker": ((120, 116, 100), (70, 110, 60)),
    "map_wraith": ((226, 214, 170), (90, 70, 40)),
    "basalt_guard": ((60, 58, 64), (230, 110, 40)),
    "void_stalker": ((40, 20, 60), (190, 110, 240)),
    "drowned_warden": ((40, 120, 120), (120, 230, 210)),
    "void_warden": ((24, 12, 40), (250, 120, 255)),
}


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def render_sprite(shape, mat, handle, accent):
    light, mid, dark, outline = MATERIALS[mat]
    hl, hd = HANDLES[handle]
    gl, gd = ACCENTS[accent]
    pal = {"o": outline, "a": light, "b": mid, "c": dark, "h": hl, "H": hd, "g": gl, "G": gd,
           "w": (255, 255, 255)}
    cv = Canvas(16, 16)
    rows = SHAPES[shape].strip("\n").split("\n")
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                cv.set(x, y, pal[ch])
    return cv


def egg(base, spots):
    cv = Canvas(16, 16)
    rows = SHAPES["egg"].strip("\n").split("\n")
    pal = {"o": shade(base, 0.4), "a": shade(base, 1.2), "b": base, "c": shade(base, 0.7),
           "g": spots, "G": shade(spots, 0.7)}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                cv.set(x, y, pal.get(ch, base))
    return cv


# ------------------------------------------------------------------ block textures
def noise_tile(base, var=14, seed=0, size=16):
    rng = random.Random(seed)
    cv = Canvas(size, size)
    for y in range(size):
        for x in range(size):
            d = rng.randint(-var, var)
            cv.set(x, y, tuple(max(0, min(255, v + d)) for v in base))
    return cv


def bricks(cv, mortar, rows=4):
    h = 16 // rows
    for r in range(rows):
        y = r * h
        for x in range(16):
            cv.set(x, y, mortar)
        off = 0 if r % 2 == 0 else 4
        for x in range(off, 16, 8):
            for yy in range(y, y + h):
                cv.set(x, yy, mortar)


def frame(cv, c, inset=0):
    for i in range(inset, 16 - inset):
        cv.set(i, inset, c)
        cv.set(i, 15 - inset, c)
        cv.set(inset, i, c)
        cv.set(15 - inset, i, c)


def rune(cv, color, seed):
    rng = random.Random(seed)
    x, y = 7, 3
    for _ in range(14):
        cv.set(x, y, color)
        dx, dy = rng.choice([(0, 1), (1, 0), (-1, 0), (0, 1), (1, 1), (-1, 1)])
        x = max(4, min(11, x + dx))
        y = max(3, min(12, y + dy))


def block_textures():
    out = {}
    stone = (118, 118, 124)
    # waystone
    side = noise_tile(stone, 10, 1)
    bricks(side, (80, 80, 86), rows=2)
    rune(side, (120, 230, 255), 7)
    frame(side, (70, 70, 76))
    out["waystone_side"] = side
    top = noise_tile((150, 150, 156), 8, 2)
    frame(top, (90, 90, 96))
    for i in range(5, 11):
        top.set(i, 7, (140, 240, 255))
        top.set(7, i, (140, 240, 255))
    out["waystone_top"] = top
    # sorting chest (crate)
    wood = (156, 112, 66)
    s = noise_tile(wood, 10, 3)
    for y in (0, 5, 10, 15):
        for x in range(16):
            s.set(x, y, (96, 64, 34))
    frame(s, (70, 46, 22))
    for i in range(16):
        s.set(i, i, (110, 76, 40))
    # sorting arrows emblem
    for x, y in ((6, 6), (7, 6), (8, 6), (9, 6), (8, 5), (8, 7), (6, 9), (7, 9), (8, 9), (9, 9), (7, 8), (7, 10)):
        s.set(x, y, (255, 214, 90))
    out["sorting_chest_side"] = s
    t = noise_tile(wood, 10, 4)
    frame(t, (70, 46, 22))
    frame(t, (200, 170, 70), 2)
    out["sorting_chest_top"] = t
    # guild terminal
    g = noise_tile((96, 86, 76), 8, 5)
    frame(g, (50, 44, 40))
    g.rect(3, 3, 12, 10, (40, 70, 60))
    for x in range(4, 12):
        for y in range(4, 10):
            if (x * 3 + y * 5) % 7 == 0:
                g.set(x, y, (120, 240, 180))
    g.rect(4, 12, 11, 13, (200, 170, 70))
    out["guild_terminal_front"] = g
    gs = noise_tile((96, 86, 76), 8, 6)
    frame(gs, (50, 44, 40))
    out["guild_terminal_side"] = gs
    # grave
    gr = noise_tile((140, 140, 140), 12, 7)
    frame(gr, (90, 90, 90))
    for y in range(4, 12):
        gr.set(7, y, (70, 70, 70))
        gr.set(8, y, (70, 70, 70))
    for x in range(5, 11):
        gr.set(x, 6, (70, 70, 70))
    out["grave"] = gr
    # sealed bars
    sb = Canvas(16, 16)
    for x in (1, 5, 9, 13):
        for y in range(16):
            sb.set(x, y, (60, 150, 140))
            sb.set(x + 1, y, (30, 90, 90))
    for y in (2, 13):
        for x in range(16):
            sb.set(x, y, (40, 110, 110))
    out["sealed_bars"] = sb
    # altars
    wa = noise_tile((50, 110, 100), 10, 8)
    bricks(wa, (30, 70, 70), 4)
    rune(wa, (160, 255, 230), 11)
    out["warden_altar_side"] = wa
    wt = noise_tile((60, 130, 120), 10, 9)
    frame(wt, (30, 70, 70))
    for a in range(0, 360, 20):
        wt.set(8 + round(4 * math.cos(math.radians(a))), 8 + round(4 * math.sin(math.radians(a))), (180, 255, 240))
    out["warden_altar_top"] = wt
    va = noise_tile((40, 22, 58), 10, 10)
    bricks(va, (20, 10, 32), 4)
    rune(va, (240, 140, 255), 13)
    out["void_altar_side"] = va
    vt = noise_tile((52, 30, 74), 10, 12)
    frame(vt, (20, 10, 32))
    for a in range(0, 360, 20):
        vt.set(8 + round(4 * math.cos(math.radians(a))), 8 + round(4 * math.sin(math.radians(a))), (250, 170, 255))
    out["void_altar_top"] = vt
    # ores
    for name, base, seed in (("lithite_ore", stone, 14), ("deepslate_lithite_ore", (72, 72, 78), 15)):
        o = noise_tile(base, 12, seed)
        rng = random.Random(seed)
        for _ in range(5):
            x, y = rng.randint(2, 12), rng.randint(2, 12)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                o.set(x + dx, y + dy, (90, 220, 200) if (dx + dy) % 2 == 0 else (40, 150, 150))
        out[name] = o
    return out


# ------------------------------------------------------------------ armor layers (64x32 humanoid UVs)
def armor_layer(mat, accent, legs=False):
    light, mid, dark, outline = MATERIALS[mat]
    gl, gd = ACCENTS[accent]
    cv = Canvas(64, 32)
    rng = random.Random(f"{mat}{legs}")

    def box(u, v, w, h, d, base):
        # unfolded cube: top/bottom row then 4 sides
        for (x0, y0, ww, hh) in ((u + d, v, w, d), (u + d + w, v, w, d), (u, v + d, d, h),
                                 (u + d, v + d, w, h), (u + d + w, v + d, d, h), (u + d + w + d, v + d, w, h)):
            for y in range(y0, y0 + hh):
                for x in range(x0, x0 + ww):
                    f = 1.0 + rng.uniform(-0.06, 0.06)
                    edge = x in (x0, x0 + ww - 1) or y in (y0, y0 + hh - 1)
                    cv.set(x, y, shade(dark if edge else base, f))

    if legs:
        box(0, 16, 4, 12, 4, mid)      # legs
        box(16, 16, 8, 12, 4, mid)     # waist (body region)
        for x in range(20, 28):
            cv.set(x, 20, gl)
    else:
        box(0, 0, 8, 8, 8, mid)        # head
        box(16, 16, 8, 12, 4, light)   # body
        box(40, 16, 4, 12, 4, mid)     # arms
        box(0, 16, 4, 12, 4, mid)      # boots / legs
        for x in range(8, 16):
            cv.set(x, 8, gl)          # helmet band
        for y in range(21, 27):
            cv.set(23, y, gd)
            cv.set(24, y, gl)
        # visor gap on the helmet front
        for x in range(10, 14):
            cv.set(x, 12, (0, 0, 0, 0))
    return cv


# ------------------------------------------------------------------ mob skins
def humanoid_skin(w, h, skin, cloth, accent, eyes, seed, hat=None):
    """Fills the standard player-style UV layout (works for zombie/drowned 64x64, skeleton 64x32)."""
    rng = random.Random(seed)
    cv = Canvas(w, h)

    def region(x0, y0, x1, y1, c, var=10):
        for y in range(y0, min(y1, h)):
            for x in range(x0, min(x1, w)):
                d = rng.randint(-var, var)
                cv.set(x, y, tuple(max(0, min(255, v + d)) for v in c))

    region(0, 0, 32, 16, skin)          # head
    region(16, 16, 40, 32, cloth)       # body
    region(40, 16, 56, 32, skin)        # right arm
    region(0, 16, 16, 32, cloth)        # right leg
    if h >= 64:
        region(16, 48, 32, 64, cloth)   # left leg
        region(32, 48, 48, 64, skin)    # left arm
    # face on head front (8..15, 8..15)
    for x in (9, 10):
        cv.set(x, 12, eyes)
    for x in (13, 14):
        cv.set(x, 12, eyes)
    for x in range(10, 14):
        cv.set(x, 14, shade(skin, 0.5))
    # belt / trim
    for x in range(16, 40):
        cv.set(x, 26, accent)
    if hat:
        region(32, 0, 64, 8, hat, 6)
        region(40, 8, 48, 10, hat, 6)
    return cv


def mob_textures():
    from wf import skins
    return {f"entity/{name}": fn() for name, fn in skins.SKINS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    args = ap.parse_args()
    written = {}
    for name, (shape, mat, handle, accent) in ITEMS.items():
        written[f"item/{name}"] = render_sprite(shape, mat, handle, accent)
    for mob, (base, spots) in EGGS.items():
        written[f"item/{mob}_spawn_egg"] = egg(base, spots)
    for name, cv in block_textures().items():
        written[f"block/{name}"] = cv
    for prefix, mat, acc in (("explorer", "map", "emerald"), ("ember", "ember", "gold"), ("void", "void", "amethyst")):
        written[f"entity/equipment/humanoid/{prefix}"] = armor_layer(mat, acc)
        written[f"entity/equipment/humanoid_leggings/{prefix}"] = armor_layer(mat, acc, legs=True)
    written.update(mob_textures())
    from wf import decor
    for bid, d in decor.DECOR.items():
        names = decor.texture_names(bid)
        for face, fn in d["tex"].items():
            written[f"block/{names[face]}"] = fn()
    for rel, cv in written.items():
        path = os.path.join(TEX, rel + ".png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cv.save(path)
    print(f"{len(written)} textures written")
    if args.sheet:
        icons = [cv for rel, cv in written.items() if cv.w == 16]
        cols = 12
        sheet = Canvas(cols * 36, ((len(icons) + cols - 1) // cols) * 36, (40, 42, 50, 255))
        for i, cv in enumerate(icons):
            ox, oy = (i % cols) * 36 + 2, (i // cols) * 36 + 2
            for y in range(16):
                for x in range(16):
                    p = cv.get(x, y)
                    if p[3]:
                        sheet.rect(ox + x * 2, oy + y * 2, ox + x * 2 + 1, oy + y * 2 + 1, p)
        os.makedirs(os.path.join(ROOT, "build", "previews"), exist_ok=True)
        sheet.save(os.path.join(ROOT, "build", "previews", "textures_sheet.png"))


if __name__ == "__main__":
    main()
