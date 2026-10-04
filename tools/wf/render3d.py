"""Textured isometric renderer (needs Pillow). Uses the official 26.2 block item icons
(npm package `minecraft-textures`) so previews look like the game, and synthesizes
icons for Wayfarers blocks from their own 16x16 textures.

Projection matches the inventory icon: a block is 28 px wide, top face 14 px tall,
side faces 16 px tall. Block (x, y, z) has its top-face centre at
    (ox + (x - z) * 14, oy + (x + z) * 7 - y * 16).
"""
import json
import os

from PIL import Image, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.path.join(ROOT, "build", "icon_cache")
MOD_TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "wayfarers", "textures", "block")
_ICON_DIRS = [
    os.environ.get("MC_TEXTURES", ""),
    "/tmp/claude-0/-home-user-mode-minecraft/56f1bf77-a458-5793-adc7-375815e90045/scratchpad/mctex/package/dist/textures",
    os.path.join(ROOT, "build", "minecraft-textures", "package", "dist", "textures"),
]

# 1.20 template names -> 26.2 names
RENAMED = {"chain": "iron_chain", "grass": "short_grass"}
# blocks without an item of their own: the icon of the closest item
ICON_ALIASES = {"farmland": "dirt", "sweet_berry_bush": "sweet_berries", "carrots": "carrot", "potatoes": "potato",
                "beetroots": "beetroot", "melon_stem": "melon_seeds", "pumpkin_stem": "pumpkin_seeds",
                "cocoa": "cocoa_beans", "water_cauldron": "cauldron"}
# blocks whose icon is not useful (flat sprites) or missing: solid colour fallbacks
FLUIDS = {"water": (40, 80, 200, 150), "lava": (240, 110, 20, 255), "bubble_column": (40, 80, 200, 150)}
SKIP = {"air", "structure_void", "jigsaw", "cave_air", "void_air", "barrier", "light"}

_icons = {}
_manifest = None


def _manifest_map():
    global _manifest
    if _manifest is None:
        _manifest = {}
        for d in _ICON_DIRS:
            if d and os.path.exists(os.path.join(d, "manifest", "26.2.json")):
                m = json.load(open(os.path.join(d, "manifest", "26.2.json")))
                for it in m["items"]:
                    _manifest[it["id"]] = os.path.join(d, "assets", it["texture"])
                break
    return _manifest


def _affine_face(tex, kind, shade):
    """Project a 16x16 texture onto one face of the 32x32 icon geometry."""
    tex = tex.convert("RGBA").resize((16, 16), Image.NEAREST)
    if kind == "top":
        # X = 16 + (u - v) * 14/16, Y = 1 + (u + v) * 7/16
        a = 16 / 28.0
        b = 16 / 14.0
        data = (a, b, -16 * a - b, -a, b, 16 * a - b)
    elif kind == "left":
        # X = 2 + u * 14/16, Y = 8 + u * 7/16 + v
        data = (16 / 14.0, 0, -2 * 16 / 14.0, -0.5, 1, -8 + 1.0)
    else:
        # X = 16 + u * 14/16, Y = 15 - u * 7/16 + v
        data = (16 / 14.0, 0, -16 * 16 / 14.0, 0.5, 1, -15 - 8 + 0.0)
    face = tex.transform((32, 32), Image.AFFINE, data, resample=Image.NEAREST)
    mask = Image.new("L", (32, 32), 0)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(mask)
    if kind == "top":
        dr.polygon([(16, 1), (30, 8), (16, 15), (2, 8)], fill=255)
    elif kind == "left":
        dr.polygon([(2, 8), (16, 15), (16, 31), (2, 24)], fill=255)
    else:
        dr.polygon([(16, 15), (30, 8), (30, 24), (16, 31)], fill=255)
    face = ImageEnhance.Brightness(face).enhance(shade)
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    out.paste(face, (0, 0), Image.composite(face.split()[3], Image.new("L", (32, 32), 0), mask))
    return out


def _decor_base(name):
    try:
        from . import decor
    except ImportError:
        return None
    for bid, d in decor.DECOR.items():
        for v in d["variants"]:
            if decor.variant_id(bid, v) == name:
                return bid
    return None


def _colorize(template_id, color_src):
    """Vanilla shape icon (e.g. oak stairs) recoloured with the average colours of a mod icon."""
    path = _manifest_map().get(template_id)
    if not path or color_src is None:
        return None
    from PIL import ImageOps
    shape = Image.open(path).convert("RGBA")
    src = color_src.convert("RGBA").resize((1, 1), Image.BOX).getpixel((0, 0))
    gray = ImageOps.grayscale(shape)
    avg = max(1, sum(gray.getdata()) / max(1, len(gray.getdata())))
    out = Image.new("RGBA", shape.size, (0, 0, 0, 0))
    px = out.load()
    sp = shape.load()
    gp = gray.load()
    for y in range(shape.size[1]):
        for x in range(shape.size[0]):
            a = sp[x, y][3]
            if a:
                f = gp[x, y] / 110.0
                px[x, y] = (min(255, int(src[0] * f)), min(255, int(src[1] * f)), min(255, int(src[2] * f)), a)
    return out


def _mod_icon(name):
    base = _decor_base(name)
    if base and name.endswith(("_stairs", "_wall")):
        cube = _mod_icon(base)
        tmpl = "minecraft:stone_brick_stairs" if name.endswith("_stairs") else "minecraft:stone_brick_wall"
        return _colorize(tmpl, cube) or cube
    base = base or name
    for suffix in ("_stairs", "_slab", "_wall"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    cands = [(base + "_top", base + "_side"), (base, base), (base + "_side", base + "_side"),
             (base + "s", base + "s")]
    for top, side in cands:
        tp, sp = os.path.join(MOD_TEX, top + ".png"), os.path.join(MOD_TEX, side + ".png")
        if os.path.exists(tp) and os.path.exists(sp):
            t, s = Image.open(tp), Image.open(sp)
            icon = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            icon.alpha_composite(_affine_face(s, "left", 0.82))
            icon.alpha_composite(_affine_face(s, "right", 0.62))
            icon.alpha_composite(_affine_face(t, "top", 1.0))
            if name.endswith("_slab"):
                cut = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
                cut.paste(icon.crop((0, 0, 32, 24)), (0, 8))
                icon = cut
            return icon
    return None


def _flat_icon(rgba):
    icon = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(icon)
    r, g, b, a = rgba
    dr.polygon([(2, 8), (16, 15), (16, 31), (2, 24)], fill=(int(r * .8), int(g * .8), int(b * .8), a))
    dr.polygon([(16, 15), (30, 8), (30, 24), (16, 31)], fill=(int(r * .6), int(g * .6), int(b * .6), a))
    dr.polygon([(16, 1), (30, 8), (16, 15), (2, 8)], fill=rgba)
    return icon


def _face_colors(img):
    """Average colour of the top / left / right regions of a cube icon."""
    px = img.load()
    regions = {"top": [], "left": [], "right": []}
    for y in range(32):
        for x in range(32):
            p = px[x, y]
            if p[3] < 128:
                continue
            if abs(x - 16) / 14 + abs(y - 8) / 7 <= 1:
                regions["top"].append(p)
            elif x < 16:
                regions["left"].append(p)
            else:
                regions["right"].append(p)
    out = {}
    for k, v in regions.items():
        if v:
            out[k] = tuple(sum(c[i] for c in v) // len(v) for i in range(3)) + (255,)
    top = out.get("top", (128, 128, 128, 255))
    out.setdefault("left", tuple(int(c * .8) for c in top[:3]) + (255,))
    out.setdefault("right", tuple(int(c * .6) for c in top[:3]) + (255,))
    return out


def _boxes_icon(colors, boxes):
    """Draw axis-aligned sub-boxes (u0,v0,w0,u1,v1,w1 in 0..1) with flat shaded faces."""
    from PIL import ImageDraw
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)

    def P(u, v, w):
        return (16 + (u - w) * 14, 1 + (u + w) * 7 + (1 - v) * 16)

    for (u0, v0, w0, u1, v1, w1) in sorted(boxes, key=lambda b: (b[0] + b[3]) + (b[2] + b[5]) + (b[1] + b[4])):
        dr.polygon([P(u0, v0, w1), P(u1, v0, w1), P(u1, v1, w1), P(u0, v1, w1)], fill=colors["left"])
        dr.polygon([P(u1, v0, w0), P(u1, v0, w1), P(u1, v1, w1), P(u1, v1, w0)], fill=colors["right"])
        dr.polygon([P(u0, v1, w0), P(u1, v1, w0), P(u1, v1, w1), P(u0, v1, w1)], fill=colors["top"])
    return img


def _is_furniture(name):
    try:
        from . import furniture
    except ImportError:
        return False
    return name in furniture.FURNITURE


def _furniture_icon(name, props):
    """Mod furniture (wf/furniture.py): its model boxes, each in the average colour of its texture, turned to
    the block's facing/axis."""
    try:
        from . import furniture
    except ImportError:
        return None
    f = furniture.FURNITURE.get(name)
    if not f:
        return None
    from PIL import ImageDraw
    props = props or {}
    turn = {"north": 0, "east": 1, "south": 2, "west": 3}.get(props.get("facing", "north"), 0)
    axis = props.get("axis", "y")
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cache = {}

    def colour(tex):
        if tex not in cache:
            p = os.path.join(MOD_TEX, tex + ".png")
            c = Image.open(p).convert("RGBA").resize((1, 1), Image.BOX).getpixel((0, 0)) if os.path.exists(p) \
                else (150, 120, 60, 255)
            cache[tex] = c[:3] + (255,)
        return cache[tex]

    def shade(c, k):
        return (int(c[0] * k), int(c[1] * k), int(c[2] * k), 255)

    def P(u, v, w):
        return (16 + (u - w) * 14, 1 + (u + w) * 7 + (1 - v) * 16)

    boxes = []
    for x0, y0, z0, x1, y1, z1, tex in f["boxes"]:
        b = [x0 / 16, y0 / 16, z0 / 16, x1 / 16, y1 / 16, z1 / 16]
        if axis == "x":
            b = [b[1], b[0], b[2], b[4], b[3], b[5]]
        elif axis == "z":
            b = [b[0], b[2], b[1], b[3], b[5], b[4]]
        for _ in range(turn):  # clockwise quarter turns seen from above: (x, z) -> (1 - z, x)
            b = [1 - b[5], b[1], b[0], 1 - b[2], b[4], b[3]]
        boxes.append((b, colour(tex)))
    for (u0, v0, w0, u1, v1, w1), c in sorted(boxes, key=lambda e: sum(e[0])):
        dr.polygon([P(u0, v0, w1), P(u1, v0, w1), P(u1, v1, w1), P(u0, v1, w1)], fill=shade(c, 0.82))
        dr.polygon([P(u1, v0, w0), P(u1, v0, w1), P(u1, v1, w1), P(u1, v1, w0)], fill=shade(c, 0.62))
        dr.polygon([P(u0, v1, w0), P(u1, v1, w0), P(u1, v1, w1), P(u0, v1, w1)], fill=c)
    return img


def _shaped_icon(name, props, base_icon):
    colors = _face_colors(base_icon)
    if name.endswith("_slab"):
        t = (props or {}).get("type", "bottom")
        if t == "double":
            return base_icon
        return _boxes_icon(colors, [(0, 0.5, 0, 1, 1, 1)] if t == "top" else [(0, 0, 0, 1, 0.5, 1)])
    if name.endswith("_stairs"):
        f = (props or {}).get("facing", "north")
        top = (props or {}).get("half", "bottom") == "top"
        main = (0, 0.5, 0, 1, 1, 1) if top else (0, 0, 0, 1, 0.5, 1)
        vv = (0, 0.5) if top else (0.5, 1)
        step = {"north": (0, vv[0], 0, 1, vv[1], 0.5), "south": (0, vv[0], 0.5, 1, vv[1], 1),
                "west": (0, vv[0], 0, 0.5, vv[1], 1), "east": (0.5, vv[0], 0, 1, vv[1], 1)}[f]
        return _boxes_icon(colors, [main, step])
    return base_icon


def icon(block_id, props=None):
    ns0, name0 = block_id.split(":")
    if name0.endswith(("_stairs", "_slab")) and props:
        k = (ns0, name0, tuple(sorted(props.items())), "shaped")
        if k not in _icons:
            base_name = name0
            if ns0 == "wayfarers":
                base = _decor_base(name0)
                cube = _mod_icon(base) if base else None
            else:
                full = {"_stairs": "", "_slab": ""}
                cand = [name0.rsplit("_", 1)[0], name0.rsplit("_", 1)[0] + "s", name0.rsplit("_", 1)[0] + "_planks",
                        name0.rsplit("_", 1)[0].replace("brick", "bricks"), name0.rsplit("_", 1)[0].replace("tile", "tiles")]
                cube = None
                for c in cand:
                    p = _manifest_map().get(f"minecraft:{c}")
                    if p and os.path.exists(p):
                        cube = Image.open(p).convert("RGBA")
                        break
                if cube is None:
                    p = _manifest_map().get(block_id)
                    cube = Image.open(p).convert("RGBA") if p and os.path.exists(p) else _flat_icon((150, 150, 150, 255))
            _icons[k] = _shaped_icon(name0, props, cube) if cube is not None else _flat_icon((200, 0, 200, 255))
        return _icons[k]
    return _icon(block_id, props)


def _icon(block_id, props=None):
    ns, name = block_id.split(":")
    name = RENAMED.get(name, name)
    keep_props = name.endswith("_slab") or (ns == "wayfarers" and _is_furniture(name))
    key = (ns, name, tuple(sorted((props or {}).items())) if keep_props else ())
    if key in _icons:
        return _icons[key]
    img = None
    if name.endswith("glass_pane") or name in ("glass", "tinted_glass") or name.endswith("stained_glass"):
        src = name.replace("_pane", "") if name.endswith("glass_pane") else name
        p = _manifest_map().get(f"minecraft:{src}")
        if p and os.path.exists(p):
            img = Image.open(p).convert("RGBA")
            alpha = img.split()[3].point(lambda a: int(a * 0.55))
            img.putalpha(alpha)
            _icons[key] = img
            return img
    if name in FLUIDS:
        rgba = FLUIDS[name]
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(img).polygon([(16, 1), (30, 8), (16, 15), (2, 8)], fill=rgba)
    elif ns == "wayfarers":
        img = _furniture_icon(name, props) or _mod_icon(name)
    else:
        path = _manifest_map().get(f"minecraft:{name}")
        if path is None:
            # blocks without an item (e.g. wall_torch, potted_x, *_plant): try the base item
            for alt in (ICON_ALIASES.get(name, name), name.replace("wall_", ""), name.replace("potted_", ""),
                        name.replace("_plant", ""), name.replace("_cauldron", "") if "cauldron" in name else name):
                path = _manifest_map().get(f"minecraft:{alt}")
                if path:
                    break
        if path and os.path.exists(path):
            img = Image.open(path).convert("RGBA")
    if img is None:
        img = _flat_icon((200, 0, 200, 255))
    if name.endswith("_slab") and props and props.get("type") == "top" and ns == "minecraft":
        shifted = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        shifted.paste(img.crop((0, 8, 32, 32)), (0, 0))
        img = shifted
    _icons[key] = img
    return img


OPAQUE_HINTS = ("slab", "stairs", "fence", "wall", "pane", "bars", "glass", "leaves", "door", "trapdoor", "torch",
                "lantern", "chain", "flower", "grass", "fern", "carpet", "rail", "ladder", "vine", "sign", "button",
                "plate", "water", "lava", "candle", "rod", "pot", "head", "skull", "banner", "bed", "chest", "campfire",
                "cluster", "bud", "coral", "kelp", "sapling", "mushroom", "roots", "web", "snow", "cauldron",
                "railing", "_pipe", "cog", "valve", "shelf", "chandelier", "chair", "table", "hanging")


def _opaque(name):
    return not any(h in name for h in OPAQUE_HINTS)


def rotate(blocks, quarter):
    """Rotate a normalized block dict by quarter turns around Y (to view other faces)."""
    if quarter % 4 == 0:
        return blocks
    turn = {"north": "east", "east": "south", "south": "west", "west": "north"}
    out = {}
    for (x, y, z), b in blocks.items():
        name, props, nbt = b
        if props and ("facing" in props or "axis" in props):
            props = dict(props)
            for _ in range(quarter % 4):
                x, z = -z, x
                if props.get("facing") in turn:
                    props["facing"] = turn[props["facing"]]
                if props.get("axis") in ("x", "z"):
                    props["axis"] = "z" if props["axis"] == "x" else "x"
            b = (name, props, nbt)
        else:
            for _ in range(quarter % 4):
                x, z = -z, x
        out[(x, y, z)] = b
    mx = min(p[0] for p in out)
    mz = min(p[2] for p in out)
    return {(x - mx, y, z - mz): b for (x, y, z), b in out.items()}


def render(blocks, path, max_y=None, scale=1.0, max_side=2400, bg=(24, 26, 34, 255), angle=0):
    """blocks: dict (x,y,z) -> (name, props, nbt) normalized. Writes a PNG. angle = quarter turns."""
    blocks = rotate(blocks, angle)
    vis = {p: b for p, b in blocks.items()
           if b[0].split(":")[1] not in SKIP and (max_y is None or p[1] <= max_y)}
    if not vis:
        return
    xs = [p[0] for p in vis]
    ys = [p[1] for p in vis]
    zs = [p[2] for p in vis]
    X, Y, Z = max(xs) + 1, max(ys) + 1, max(zs) + 1
    W = (X + Z) * 14 + 40
    H = (X + Z) * 7 + Y * 16 + 60
    canvas = Image.new("RGBA", (W, H), bg)
    ox, oy = Z * 14 + 20, Y * 16 + 30
    opaque = {p for p, b in vis.items() if _opaque(b[0].split(":")[1])}
    order = sorted(vis, key=lambda p: ((p[0] + p[2]) * 0.612 + p[1] * 0.5, p[1]))
    for (x, y, z) in order:
        if (x + 1, y, z) in opaque and (x, y + 1, z) in opaque and (x, y, z + 1) in opaque:
            continue
        name, props, _ = vis[(x, y, z)]
        img = icon(name, props)
        cx = ox + (x - z) * 14
        cy = oy + (x + z) * 7 - y * 16
        canvas.alpha_composite(img, (cx - 16, cy - 8))
    bbox = canvas.split()[3].getbbox()
    canvas = canvas.crop((max(0, bbox[0] - 10), max(0, bbox[1] - 10), min(W, bbox[2] + 10), min(H, bbox[3] + 10))) \
        if bbox else canvas
    w, h = canvas.size
    f = min(scale, max_side / max(w, h))
    if f != 1.0:
        canvas = canvas.resize((max(1, int(w * f)), max(1, int(h * f))), Image.LANCZOS)
    canvas.save(path)
