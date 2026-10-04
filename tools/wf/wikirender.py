"""Renderers used by tools/gen_wiki.py (needs Pillow + numpy).

* ``voxel_frames``  - flat-shaded turntable of a structure (any yaw), painter's algorithm per block.
* ``JsonModels``    - loads Wayfarers block/item JSON models (parents, vanilla cube templates, elements)
                      and renders them textured at any angle (inventory icons, furniture and 3D held items).
* ``mob_frames``    - turntable of an entity model (wf.models) through wf.model_render, idle animation playing.
* ``save_gif``      - shared-palette animated GIF.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from . import model_render
from . import render3d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets")
BG = (24, 27, 31)


# ---------------------------------------------------------------------------------------------- GIF
def save_gif(frames, path, ms=90, colors=192):
    """frames: RGB images of the same size. One palette for the whole animation (no flicker)."""
    w, h = frames[0].size
    step = max(1, len(frames) // 6)
    picks = frames[::step]
    mosaic = Image.new("RGB", (w, h * len(picks)))
    for i, f in enumerate(picks):
        mosaic.paste(f, (0, i * h))
    pal = mosaic.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    # keep the background exactly BG, so the GIF melts into the page's display case (no lighter rectangle)
    p = pal.getpalette()[:3 * colors]
    near = min(range(len(p) // 3), key=lambda i: sum((p[3 * i + k] - BG[k]) ** 2 for k in range(3)))
    p[3 * near:3 * near + 3] = list(BG)
    pal.putpalette(p)
    out = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out[0].save(path, save_all=True, append_images=out[1:], duration=ms, loop=0, optimize=False, disposal=1)


# ---------------------------------------------------------------------------------------------- voxels
_COLORS = {}
SMALL_HINTS = ("torch", "flower", "sapling", "fern", "grass", "bush", "button", "lever", "rail", "candle", "pickle",
               "mushroom", "roots", "vine", "lichen", "carpet", "pressure_plate", "tripwire", "lantern", "chain",
               "bars", "pane", "fence", "wall", "rod", "pot", "skull", "head", "banner", "sign", "kelp", "seagrass",
               "coral", "bud", "dripleaf", "azalea", "petals", "web", "ladder", "snow", "sprouts", "string", "furnace_minecart")
SKIP = render3d.SKIP | {"water", "bubble_column", "light", "moving_piston", "piston_head", "fire", "soul_fire"}


_JM = None


def _mod_block_icon(name):
    """Inventory-like icon of a wayfarers block from its blockstate's first model (furniture, pipes...)."""
    global _JM
    if _JM is None:
        _JM = JsonModels()
    bid = name.split(":")[1]
    ref = None
    bs = os.path.join(ASSETS, "wayfarers", "blockstates", bid + ".json")
    if os.path.exists(bs):
        d = json.load(open(bs, encoding="utf-8"))
        if "variants" in d and d["variants"]:
            v = next(iter(d["variants"].values()))
            ref = (v[0] if isinstance(v, list) else v).get("model")
        elif "multipart" in d and d["multipart"]:
            a = d["multipart"][0]["apply"]
            ref = (a[0] if isinstance(a, list) else a).get("model")
    if ref is None:
        ref = _JM.item_model(bid)[0]
    if ref is None:
        return None
    md = _JM.load(ref)
    if md["kind"] != "elements":
        return None
    return _JM.render(md, size=32)


def _block_colors(name, props):
    key = name
    if key not in _COLORS:
        try:
            ic = render3d.icon(name, None)
            if name.startswith("wayfarers:"):
                px = ic.convert("RGBA").resize((1, 1), Image.BOX).getpixel((0, 0))
                if px[0] > 150 and px[2] > 150 and px[1] < 60:  # render3d's magenta "missing" icon
                    ic = _mod_block_icon(name) or ic
            fc = render3d._face_colors(ic)
            top = np.array(fc["top"][:3], float)
            side = np.array(fc["left"][:3], float) / 0.82
            side = np.clip(side, 0, 255)
        except Exception:
            top = side = np.array((150, 150, 150), float)
        _COLORS[key] = (top, side)
    return _COLORS[key]


def _is_small(n):
    return any(h in n for h in SMALL_HINTS)


def _opaque(n):
    return render3d._opaque(n) and not _is_small(n)


DIRS = np.array([(0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)], float)
# unit-cube corners of each face (counter-clockwise seen from outside)
FACE_CORNERS = {
    0: [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
    1: [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)],
    2: [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)],
    3: [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
    4: [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)],
    5: [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
}


def _prepare(blocks, max_y=None, water=False):
    items = []
    for (x, y, z), (name, props, _nbt) in blocks.items():
        n = name.split(":")[1]
        if n in SKIP or (max_y is not None and y > max_y):
            continue
        items.append((x, y, z, name, n, props))
    if not items:
        return None
    occ = {(x, y, z) for x, y, z, name, n, props in items if _opaque(n)}
    faces = []  # (bx, by, bz, small, dir, r, g, b)
    rng = np.random.default_rng(7)
    for x, y, z, name, n, props in items:
        small = _is_small(n)
        top, side = _block_colors(name, props)
        j = 1.0 + (((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) % 17 - 8) / 160.0
        for d in range(6):
            dx, dy, dz = DIRS[d].astype(int)
            if not small and (x + dx, y + dy, z + dz) in occ:
                continue
            c = top if d in (0, 1) else side
            faces.append((x, y, z, 1 if small else 0, d, *(np.clip(c * j, 0, 255))))
    del rng
    return np.array(faces, float)


def voxel_frames(blocks, n=16, size=360, pitch=28, ss=2, max_y=None, start_yaw=35, bg=BG, yaws=None):
    """Turntable of a block dict {(x,y,z): (name, props, nbt)}. Returns n RGB images size x size."""
    F = _prepare(blocks, max_y)
    if F is None:
        return [Image.new("RGB", (size, size), bg)] * n
    pos = F[:, :3]
    small = F[:, 3]
    dirs = F[:, 4].astype(int)
    cols = F[:, 5:8]
    lo, hi = pos.min(0), pos.max(0) + 1
    centre = (lo + hi) / 2
    # corners of every face, in world space
    corner_off = np.array([FACE_CORNERS[d] for d in range(6)], float)  # 6x4x3
    co = corner_off[dirs]  # Nx4x3
    sm = small[:, None, None]
    co = np.where(sm > 0, 0.25 + co * 0.5, co)
    co[:, :, 1] = np.where(small[:, None] > 0, corner_off[dirs][:, :, 1] * 0.6, co[:, :, 1])
    world = pos[:, None, :] + co - centre  # Nx4x3
    normals = DIRS[dirs]
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    S = size * ss
    # scale: fit the bounding sphere in the frame for every yaw
    ext = np.linalg.norm((hi - lo)[[0, 2]]) / 2
    height = (hi - lo)[1]
    span_x = 2 * ext
    span_y = height * cp + 2 * ext * sp
    ppb = 0.94 * S / max(span_x, span_y, 1)
    light = np.array([-0.55, 0.45, 0.70])
    light /= np.linalg.norm(light)
    frames = []
    yaw_list = yaws if yaws is not None else [start_yaw + 360.0 * k / n for k in range(n)]
    for yaw in yaw_list:
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

        def view(p):
            x, y, z = p[..., 0], p[..., 1], p[..., 2]
            xr = x * ca + z * sa
            zr = -x * sa + z * ca
            yr = y * cp - zr * sp
            zz = y * sp + zr * cp
            return np.stack([xr, yr, zz], -1)
        nv = view(normals)
        vis = nv[:, 2] > 1e-6
        v = view(world[vis])
        depth = v.mean(1)[:, 2] + nv[vis][:, 2] * 0.01
        order = np.argsort(depth)
        shade = 0.58 + 0.42 * np.clip(nv[vis] @ light, 0, 1)
        shade = np.where(nv[vis][:, 1] > 0.5, 1.0, shade)
        c = np.clip(cols[vis] * shade[:, None], 0, 255).astype(int)
        px = S / 2 + v[:, :, 0] * ppb
        py = S / 2 - v[:, :, 1] * ppb + (height * cp * ppb) * 0.0
        # vertical centring: centre of the projected bounding box of all corners
        allx, ally = px, py
        dy = S / 2 - (ally.min() + ally.max()) / 2
        dx = S / 2 - (allx.min() + allx.max()) / 2
        img = Image.new("RGB", (S, S), bg)
        dr = ImageDraw.Draw(img)
        pts = np.stack([px + dx, py + dy], -1)[order].round(1).tolist()
        cl = c[order].tolist()
        for p, col in zip(pts, cl):
            dr.polygon([tuple(q) for q in p], fill=tuple(col))
        frames.append(img.resize((size, size), Image.LANCZOS) if ss != 1 else img)
    return frames


def crop_frames(frames, pad=6, bg=BG):
    """Crop a list of frames to the union of their non-background bounding boxes."""
    box = None
    for f in frames:
        diff = Image.eval(f.convert("RGB"), lambda v: v)
        a = np.asarray(diff).astype(int)
        mask = (np.abs(a - np.array(bg)).sum(-1) > 12)
        ys, xs = np.nonzero(mask)
        if len(xs) == 0:
            continue
        b = (xs.min(), ys.min(), xs.max(), ys.max())
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    if box is None:
        return frames
    w, h = frames[0].size
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(w, box[2] + pad + 1), min(h, box[3] + pad + 1))
    return [f.crop(box) for f in frames]


# ---------------------------------------------------------------------------------------------- JSON models
CUBE = (0, 0, 0, 16, 16, 16)
TEMPLATES = {
    "block/cube_all": [(CUBE, {f: "#all" for f in ("up", "down", "north", "south", "east", "west")})],
    "block/cube_column": [(CUBE, {"up": "#end", "down": "#end", "north": "#side", "south": "#side", "east": "#side", "west": "#side"})],
    "block/cube_column_horizontal": [(CUBE, {"up": "#side", "down": "#side", "north": "#end", "south": "#end", "east": "#side", "west": "#side"})],
    "block/cube_bottom_top": [(CUBE, {"up": "#top", "down": "#bottom", "north": "#side", "south": "#side", "east": "#side", "west": "#side"})],
    "block/orientable": [(CUBE, {"up": "#top", "down": "#top", "north": "#front", "south": "#side", "east": "#side", "west": "#side"})],
    "block/orientable_with_bottom": [(CUBE, {"up": "#top", "down": "#bottom", "north": "#front", "south": "#side", "east": "#side", "west": "#side"})],
    "block/cube": [(CUBE, {f: "#" + f for f in ("up", "down", "north", "south", "east", "west")})],
    "block/cube_mirrored_all": [(CUBE, {f: "#all" for f in ("up", "down", "north", "south", "east", "west")})],
    "block/slab": [((0, 0, 0, 16, 8, 16), {"up": "#top", "down": "#bottom", "north": "#side", "south": "#side", "east": "#side", "west": "#side"})],
    "block/slab_top": [((0, 8, 0, 16, 16, 16), {"up": "#top", "down": "#bottom", "north": "#side", "south": "#side", "east": "#side", "west": "#side"})],
    "block/stairs": [((0, 0, 0, 16, 8, 16), {"up": "#top", "down": "#bottom", "north": "#side", "south": "#side", "east": "#side", "west": "#side"}),
                     ((8, 8, 0, 16, 16, 16), {"up": "#top", "down": "#bottom", "north": "#side", "south": "#side", "east": "#side", "west": "#side"})],
    "block/wall_inventory": [((4, 0, 4, 12, 16, 12), {f: "#wall" for f in ("up", "down", "north", "south", "east", "west")}),
                             ((5, 0, 0, 11, 13, 16), {f: "#wall" for f in ("up", "down", "north", "south", "east", "west")})],
    "block/leaves": [(CUBE, {f: "#all" for f in ("up", "down", "north", "south", "east", "west")})],
}
FLAT = ("item/generated", "item/handheld", "item/handheld_rod", "builtin/generated")


def _pick_model(node, context, depth=0):
    """Model reference an item definition (items/<id>.json "model" node) shows in a display context: follows
    select (display_context cases, else the fallback), range_dispatch (first entry), condition and composite."""
    if not isinstance(node, dict) or depth > 8:
        return None
    t = node.get("type", "").split(":")[-1]
    if t == "model":
        return node.get("model")
    if t == "select":
        if node.get("property", "").endswith("display_context"):
            for case in node.get("cases", []):
                when = case.get("when", [])
                if context in (when if isinstance(when, list) else [when]):
                    return _pick_model(case.get("model"), context, depth + 1)
        if node.get("fallback"):
            return _pick_model(node["fallback"], context, depth + 1)
        cases = node.get("cases", [])
        return _pick_model(cases[0].get("model"), context, depth + 1) if cases else None
    if t == "range_dispatch":
        entries = node.get("entries", [])
        if entries:
            return _pick_model(entries[0].get("model"), context, depth + 1)
        return _pick_model(node.get("fallback"), context, depth + 1)
    if t == "condition":
        return _pick_model(node.get("on_false") or node.get("on_true"), context, depth + 1)
    if t == "composite":
        models = node.get("models", [])
        return _pick_model(models[0], context, depth + 1) if models else None
    return _pick_model(node.get("fallback") or node.get("model"), context, depth + 1) if isinstance(
        node.get("fallback") or node.get("model"), dict) else node.get("model") if isinstance(node.get("model"), str) else None


def _strip(ref):
    return ref.split(":", 1)[1] if ":" in ref else ref


def _tex_path(ref):
    ns, path = (ref.split(":", 1) if ":" in ref else ("minecraft", ref))
    return os.path.join(ASSETS, ns, "textures", path + ".png")


class JsonModels:
    """Resolve and render the mod's JSON models."""

    def __init__(self):
        self._tex = {}

    # -- loading
    def load(self, ref):
        """-> dict(kind='flat'|'elements'|'missing', textures={}, elements=[...], layer0=ref)"""
        textures, elements, chain = {}, None, []
        cur = ref
        for _ in range(12):
            ns = cur.split(":", 1)[0] if ":" in cur else "minecraft"
            path = os.path.join(ASSETS, ns, "models", _strip(cur) + ".json")
            if ns != "wayfarers" or not os.path.exists(path):
                chain.append(_strip(cur))
                break
            data = json.load(open(path, encoding="utf-8"))
            for k, v in data.get("textures", {}).items():
                textures.setdefault(k, v)
            if elements is None and "elements" in data:
                elements = data["elements"]
            if "parent" not in data:
                cur = None
                break
            cur = data["parent"]
        parent = chain[-1] if chain else None
        if elements is None and parent in TEMPLATES:
            elements = [{"from": list(b[:3]), "to": list(b[3:]), "faces": {f: {"texture": t} for f, t in faces.items()}}
                        for b, faces in TEMPLATES[parent]]
        if elements is None and parent in FLAT:
            return dict(kind="flat", textures=textures, layer0=textures.get("layer0"))
        if elements is None:
            if textures:
                tex = next(iter(textures.values()))
                elements = [{"from": [0, 0, 0], "to": [16, 16, 16],
                             "faces": {f: {"texture": "#__any"} for f in ("up", "down", "north", "south", "east", "west")}}]
                textures["__any"] = tex
            else:
                return dict(kind="missing", textures={})
        return dict(kind="elements", textures=textures, elements=elements)

    def item_model(self, item_id):
        """Model reference used in the inventory (gui) for wayfarers:<item_id>, and the 3D one if any."""
        path = os.path.join(ASSETS, "wayfarers", "items", item_id + ".json")
        if not os.path.exists(path):
            return None, None
        d = json.load(open(path, encoding="utf-8"))["model"]
        gui = _pick_model(d, "gui")
        hand = _pick_model(d, "thirdperson_righthand")
        return gui, (hand if hand != gui else None)

    def texture(self, ref):
        if ref not in self._tex:
            p = _tex_path(ref)
            if os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                if im.height > im.width:  # animated strip: first frame
                    im = im.crop((0, 0, im.width, im.width))
            else:
                im = Image.new("RGBA", (16, 16), (200, 0, 200, 255))
            self._tex[ref] = im
        return self._tex[ref]

    def _resolve(self, textures, t, depth=0):
        while t and t.startswith("#") and depth < 10:
            t = textures.get(t[1:])
            depth += 1
        return t

    # -- geometry
    def faces(self, model):
        """[(corners 4x3 in block pixels, uvs 4x2 in texels, texture ref, normal)]"""
        out = []
        for el in model["elements"]:
            x1, y1, z1 = el["from"]
            x2, y2, z2 = el["to"]
            rot = el.get("rotation")
            for face, spec in el.get("faces", {}).items():
                ref = self._resolve(model["textures"], spec.get("texture", ""))
                if not ref:
                    continue
                tex = self.texture(ref)
                tw, th = tex.size
                # corners in order: (start-u,start-v) (end-u,start-v) (end-u,end-v) (start-u,end-v)
                if face == "north":
                    c = [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)]
                    duv = (16 - x2, 16 - y2, 16 - x1, 16 - y1)
                elif face == "south":
                    c = [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)]
                    duv = (x1, 16 - y2, x2, 16 - y1)
                elif face == "west":
                    c = [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)]
                    duv = (z1, 16 - y2, z2, 16 - y1)
                elif face == "east":
                    c = [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)]
                    duv = (16 - z2, 16 - y2, 16 - z1, 16 - y1)
                elif face == "up":
                    c = [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)]
                    duv = (x1, z1, x2, z2)
                elif face == "down":
                    c = [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)]
                    duv = (x1, 16 - z2, x2, 16 - z1)
                else:
                    continue
                u0, v0, u1, v1 = spec.get("uv", duv)
                uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
                r = int(spec.get("rotation", 0)) // 90 % 4
                uv = uv[r:] + uv[:r] if r else uv
                uv = [(u * tw / 16.0, v * th / 16.0) for u, v in uv]
                pts = np.array(c, float)
                if rot:
                    o = np.array(rot.get("origin", (8, 8, 8)), float)
                    a = math.radians(float(rot.get("angle", 0)))
                    ca, sa = math.cos(a), math.sin(a)
                    ax = rot.get("axis", "y")
                    q = pts - o
                    if ax == "y":
                        q = np.stack([q[:, 0] * ca + q[:, 2] * sa, q[:, 1], -q[:, 0] * sa + q[:, 2] * ca], 1)
                    elif ax == "x":
                        q = np.stack([q[:, 0], q[:, 1] * ca - q[:, 2] * sa, q[:, 1] * sa + q[:, 2] * ca], 1)
                    else:
                        q = np.stack([q[:, 0] * ca - q[:, 1] * sa, q[:, 0] * sa + q[:, 1] * ca, q[:, 2]], 1)
                    pts = q + o
                out.append((pts, uv, ref))
        return out

    # -- rendering
    def render(self, model, size=64, yaw=135, pitch=30, ppb=None, bg=None, ss=1, centre=None, fit=1.0):
        """Textured orthographic render. bg None -> transparent RGBA."""
        faces = self.faces(model)
        S = size * ss
        img = np.zeros((S, S, 3), float)
        alpha = np.zeros((S, S), float)
        zbuf = np.full((S, S), -1e9)
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        if centre is None:
            centre = np.array((8.0, 8.0, 8.0))

        def view(p):
            p = (p - centre) / 16.0
            x, y, z = p[:, 0], p[:, 1], p[:, 2]
            xr = x * cy + z * sy
            zr = -x * sy + z * cy
            return np.stack([xr, y * cp - zr * sp, y * sp + zr * cp], 1)
        if ppb is None:
            allv = np.concatenate([view(f[0]) for f in faces]) if faces else np.zeros((1, 3))
            span = max(np.ptp(allv[:, 0]), np.ptp(allv[:, 1]), 0.25)
            ppb = fit * 0.9 * S / span
            off = np.array([-(allv[:, 0].min() + allv[:, 0].max()) / 2, -(allv[:, 1].min() + allv[:, 1].max()) / 2])
        else:
            ppb = ppb * ss
            off = np.zeros(2)
        light = np.array([-0.35, 0.8, 0.5])
        light /= np.linalg.norm(light)
        for pts, uv, ref in faces:
            v = view(pts)
            n = np.cross(v[1] - v[0], v[3] - v[0])
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            n /= nn
            # MC-like fixed face shading: top bright, sides darker
            shade = 0.55 + 0.45 * max(0.0, float(n @ light))
            tex = np.asarray(self.texture(ref), float)
            th, tw = tex.shape[:2]
            sx = S / 2 + (v[:, 0] + off[0]) * ppb
            sy_ = S / 2 - (v[:, 1] + off[1]) * ppb
            for tri in ((0, 1, 2), (0, 2, 3)):
                _raster_rgba(img, alpha, zbuf, tex, tw, th, sx[list(tri)], sy_[list(tri)], v[list(tri), 2],
                             [uv[i] for i in tri], shade)
        rgba = np.dstack([np.clip(img, 0, 255), alpha * 255]).astype(np.uint8)
        out = Image.fromarray(rgba, "RGBA")
        if ss != 1:
            out = out.resize((size, size), Image.LANCZOS)
        if bg is not None:
            base = Image.new("RGBA", out.size, bg + (255,))
            base.alpha_composite(out)
            out = base.convert("RGB")
        return out


def _raster_rgba(img, alpha, zbuf, tex, tw, th, xs, ys, zs, uvs, shade):
    h, w = zbuf.shape
    x0, x1 = int(max(0, math.floor(xs.min()))), int(min(w - 1, math.ceil(xs.max())))
    y0, y1 = int(max(0, math.floor(ys.min()))), int(min(h - 1, math.ceil(ys.max())))
    if x1 < x0 or y1 < y0:
        return
    area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
    if abs(area) < 1e-9:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    w0 = ((xs[1] - gx) * (ys[2] - gy) - (xs[2] - gx) * (ys[1] - gy)) / area
    w1 = ((xs[2] - gx) * (ys[0] - gy) - (xs[0] - gx) * (ys[2] - gy)) / area
    w2 = 1 - w0 - w1
    eps = -1e-6
    inside = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
    if not inside.any():
        return
    z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
    u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
    vv = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
    ui = np.clip(np.floor(u).astype(int), 0, tw - 1)
    vi = np.clip(np.floor(vv).astype(int), 0, th - 1)
    texel = tex[vi, ui]
    sub_z = zbuf[y0:y1 + 1, x0:x1 + 1]
    mask = inside & (texel[..., 3] >= 128) & (z > sub_z)
    if not mask.any():
        return
    col = texel[..., :3] * shade
    sub = img[y0:y1 + 1, x0:x1 + 1]
    sub[mask] = col[mask]
    alpha[y0:y1 + 1, x0:x1 + 1][mask] = 1.0
    sub_z[mask] = z[mask]


# ---------------------------------------------------------------------------------------------- mobs
def mob_frames(model, tex, glow, n=20, size=240, ss=2, pitch=12, start_yaw=20, bg=BG):
    """Turntable of a wf.models.Model with its idle animation; common scale for every frame."""
    tex_i, glow_i = model_render.to_pil(tex), model_render.to_pil(glow)
    rest = model_render.sample_pose(model, 0.0)
    faces = model_render.build_faces(model, rest)
    allp = np.concatenate([f[0] for f in faces])
    ext_xz = max(np.linalg.norm(allp[:, [0, 2]], axis=1).max() * 2, 0.5)
    ext_y = np.ptp(allp[:, 1])
    S = size * ss
    ppb = 0.97 * S / max(ext_xz, ext_y * math.cos(math.radians(pitch)) + ext_xz * math.sin(math.radians(pitch)), 0.5)
    idle_len = model.anims["idle"].length if "idle" in model.anims else 2.0
    frames = []
    for k in range(n):
        t = idle_len * k / n * max(1, round(2.0 / max(idle_len, 0.1)))
        pose = model_render.sample_pose(model, t % max(idle_len, 1e-3))
        im = model_render.render(model, tex_i, glow_i, pose, size=S, yaw=start_yaw + 360.0 * k / n, pitch=pitch,
                                 ppb=ppb, ground=False)
        arr = np.asarray(im).copy()
        bgm = (arr == np.array(model_render.BG)).all(-1)
        arr[bgm] = bg
        im = Image.fromarray(arr)
        frames.append(im.resize((size, size), Image.LANCZOS) if ss != 1 else im)
    return frames


def mob_still(model, tex, glow, size=64, yaw=30, pitch=10):
    """Small transparent portrait (inventory-like) for the icon atlas."""
    tex_i, glow_i = model_render.to_pil(tex), model_render.to_pil(glow)
    im = model_render.render(model, tex_i, glow_i, model_render.sample_pose(model, 0.0), size=size * 2, yaw=yaw,
                             pitch=pitch, ground=False)
    arr = np.asarray(im)
    a = (~(arr == np.array(model_render.BG)).all(-1)).astype(np.uint8) * 255
    out = Image.fromarray(np.dstack([arr, a]), "RGBA").resize((size, size), Image.LANCZOS)
    return out


_PATCHED = False


def patch_render3d():
    """render3d draws a magenta cube for mod blocks it cannot build from textures (furniture, railings, pipes...):
    give it an icon rendered from the block's own JSON model instead."""
    global _PATCHED
    if _PATCHED:
        return
    original = render3d._mod_icon

    def mod_icon(name):
        icon = original(name)
        if icon is None:
            try:
                icon = _mod_block_icon("wayfarers:" + name)
            except Exception:  # noqa: BLE001
                icon = None
        return icon
    render3d._mod_icon = mod_icon
    _PATCHED = True
