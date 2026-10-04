"""Software renderer for wf.models: textured, posed, z-buffered previews of entity models.

It reproduces Minecraft's cube geometry and UV mapping (ModelPart.Cube / Polygon) and the keyframe
maths (KeyframeAnimation), so what you see here is what the game draws, minus lighting subtleties.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .models import _face_rects

BG = (22, 24, 32)
GRID = (52, 56, 70)


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], float)


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], float)


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float)


def _t(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def _s(x, y, z):
    return np.diag([x, y, z, 1.0])


def sample_pose(model, t=0.0, action=None, action_t=0.0, walk=0.0):
    """Merged offsets: idle at t, optional walk cycle at ``walk`` seconds, optional action at action_t."""
    merged = {}

    def add(offs):
        for part, targets in offs.items():
            slot = merged.setdefault(part, {})
            for k, v in targets.items():
                p = slot.get(k, (0.0, 0.0, 0.0))
                slot[k] = tuple(p[i] + v[i] for i in range(3))
    if "idle" in model.anims:
        add(model.anims["idle"].sample(t))
    if walk and "walk" in model.anims:
        add(model.anims["walk"].sample(walk))
    if action:
        add(model.anims[action].sample(action_t))
    return merged


def _polygons(cube):
    """The cube's six faces as (4 model-space vertices, 4 uv pairs, readable face name), like ModelPart."""
    w, h, d = cube.size
    g = cube.grow
    x0, y0, z0 = (cube.origin[i] - g for i in range(3))
    x1, y1, z1 = cube.origin[0] + w + g, cube.origin[1] + h + g, cube.origin[2] + d + g
    t0, t1, t2, t3 = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
    l0, l1, l2, l3 = (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
    u, v = cube.uv
    u0, u1, u2, u22 = u, u + d, u + d + w, u + d + w + w
    u3, u4 = u + d + w + d, u + d + w + d + w
    v0, v1, v2 = v, v + d, v + d + h

    def poly(verts, a0, b0, a1, b1, name):
        uvs = [(a1, b0), (a0, b0), (a0, b1), (a1, b1)]
        return verts, uvs, name
    return [
        poly([l1, l0, t0, t1], u1, v0, u2, v1, "top"),
        poly([t2, t3, l3, l2], u2, v1, u22, v0, "bottom"),
        poly([t0, l0, l3, t3], u0, v1, u1, v2, "right"),
        poly([t1, t0, t3, t2], u1, v1, u2, v2, "front"),
        poly([l1, t1, t2, l2], u2, v1, u3, v2, "left"),
        poly([l0, l1, l2, l3], u3, v1, u4, v2, "back"),
    ]


def build_faces(model, offsets):
    """World-space faces (y up, blocks) for the model in a pose."""
    faces = []

    def walk(part, parent_m):
        off = offsets.get(part.name, {})
        r = off.get("rotation", (0, 0, 0))
        p = off.get("position", (0, 0, 0))
        s = off.get("scale", (0, 0, 0))
        rx, ry, rz = (math.radians(part.rot[i] + r[i]) for i in range(3))
        px, py, pz = part.pivot[0] + p[0], part.pivot[1] - p[1], part.pivot[2] + p[2]
        m = parent_m @ _t(px, py, pz) @ _rz(rz) @ _ry(ry) @ _rx(rx) @ _s(*(part.scale[i] + s[i] for i in range(3)))
        for cube in part.cubes:
            for verts, uvs, name in _polygons(cube):
                pts = np.array([[*vv, 1.0] for vv in verts]) @ m.T
                faces.append((pts[:, :3], uvs, name))
        for c in part.children:
            walk(c, m)
    # entity renderer: lift by 1.501 blocks, scale(-1, -1, 1) and a 180 degree turn -> world = (x, -y, -z)
    root_m = _t(0, 1.501, 0) @ _s(1 / 16, -1 / 16, -1 / 16)
    for r in model.roots:
        walk(r, root_m)
    return faces


def render(model, tex, glow, offsets, size=420, yaw=28, pitch=18, ppb=None, ground=True, label=None):
    """Render the posed model. ``ppb`` = pixels per block (auto-fit when None)."""
    faces = build_faces(model, offsets)
    if not faces:
        raise ValueError(f"{model.name}: no cubes")
    cy, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def view(pts):
        x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
        # yaw: turn the model so we see its front (+z world) and a bit of its left side
        xr = x * cy + z * sy_
        zr = -x * sy_ + z * cy
        yr = y * cp - zr * sp
        zz = y * sp + zr * cp
        return np.stack([xr, yr, zz], axis=1)

    allv = np.concatenate([view(f[0]) for f in faces])
    minx, maxx = allv[:, 0].min(), allv[:, 0].max()
    miny, maxy = allv[:, 1].min(), allv[:, 1].max()
    if ppb is None:
        ppb = 0.82 * size / max(maxx - minx, maxy - miny, 1.0)
    ox = size / 2 - (minx + maxx) / 2 * ppb
    oy = size / 2 + (miny + maxy) / 2 * ppb

    img = np.zeros((size, size, 3), float)
    img[:] = BG
    zbuf = np.full((size, size), -1e9)

    if ground:
        canvas = Image.new("RGB", (size, size), BG)
        dr = ImageDraw.Draw(canvas)
        for i in range(-4, 5):
            for a, b in (((i, 0, -4), (i, 0, 4)), ((-4, 0, i), (4, 0, i))):
                pa = view(np.array([a], float))[0]
                pb = view(np.array([b], float))[0]
                dr.line([(ox + pa[0] * ppb, oy - pa[1] * ppb), (ox + pb[0] * ppb, oy - pb[1] * ppb)], fill=GRID)
        img[:] = np.asarray(canvas, float)

    tex_a = np.asarray(tex, float) if tex is not None else None
    glow_a = np.asarray(glow, float) if glow is not None else None
    th, tw = tex_a.shape[:2]
    light = np.array([-0.45, 0.75, 0.5])
    light /= np.linalg.norm(light)

    translucent = getattr(model, "render", "") == "entityTranslucent"
    passes = [("opaque", faces)]
    if translucent:  # see-through texels blended back to front over the opaque ones, like the game does
        passes.append(("blend", sorted(faces, key=lambda f: float(view(f[0])[:, 2].mean()))))
    for mode, flist in passes:
        for pts, uvs, name in flist:
            v = view(pts)
            n = np.cross(v[1] - v[0], v[3] - v[0])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n /= nn
            shade = 0.5 + 0.5 * max(0.0, float(abs(n @ light)))
            sx = ox + v[:, 0] * ppb
            syy = oy - v[:, 1] * ppb
            for tri in ((0, 1, 2), (0, 2, 3)):
                _raster(img, zbuf, tex_a, glow_a, tw, th,
                        sx[list(tri)], syy[list(tri)], v[list(tri), 2], [uvs[i] for i in tri], shade,
                        mode if translucent else None)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if label:
        dr = ImageDraw.Draw(out)
        dr.text((6, 4), label, fill=(220, 220, 230), font=_font())
    return out


def _raster(img, zbuf, tex, glow, tw, th, xs, ys, zs, uvs, shade, mode=None):
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
    alpha = texel[..., 3]
    if mode == "opaque":
        mask = inside & (alpha >= 250) & (z > sub_z)
    elif mode == "blend":
        mask = inside & (alpha >= 8) & (alpha < 250) & (z > sub_z)
    else:
        mask = inside & (alpha >= 128) & (z > sub_z)
    if not mask.any():
        return
    col = texel[..., :3] * shade
    if glow is not None:
        gl = glow[vi, ui]
        lit = gl[..., 3] >= 128
        col = np.where(lit[..., None], np.maximum(col, gl[..., :3]), col)
    sub_img = img[y0:y1 + 1, x0:x1 + 1]
    if mode == "blend":
        a = (alpha / 255.0)[..., None]
        sub_img[mask] = (col * a + sub_img * (1 - a))[mask]
        return
    sub_img[mask] = col[mask]
    sub_z[mask] = z[mask]


_FONT = None


def _font():
    global _FONT
    if _FONT is None:
        try:
            _FONT = ImageFont.truetype("DejaVuSans.ttf", 13)
        except OSError:
            _FONT = ImageFont.load_default()
    return _FONT


def to_pil(canvas):
    if canvas is None:
        return None
    im = Image.new("RGBA", (canvas.w, canvas.h))
    im.putdata([px for row in canvas.px for px in row])
    return im


def sheet(model, tex, glow, path, size=360):
    """Preview sheet: front / side / back at rest, then a strip of key poses for every action."""
    tex_i, glow_i = to_pil(tex), to_pil(glow)
    rest = sample_pose(model, 0.0)
    views = [render(model, tex_i, glow_i, rest, size, yaw=y, label=lbl)
             for y, lbl in ((28, "front"), (90, "right side"), (208, "back"))]
    # a common scale so every pose reads at the same size as the rest pose
    faces = build_faces(model, rest)
    allp = np.concatenate([f[0] for f in faces])
    extent = max(np.ptp(allp[:, 0]), np.ptp(allp[:, 1]), np.ptp(allp[:, 2]), 1.0)
    ppb = 0.62 * size / extent
    rows = [views]
    strips = []
    if getattr(model, "preview_idle", False) and "idle" in model.anims:
        strips.append(("idle", "idle", model.anims["idle"].length))
    if "walk" in model.anims:
        strips.append(("walk", "walk", model.anims["walk"].length))
    for a in model.actions:
        strips.append((a.name, a.name, a.length))
    for title, name, length in strips:
        row = []
        for i in range(5):
            tt = length * i / 4
            if name == "walk":
                pose = sample_pose(model, tt, walk=tt or 1e-3)
            elif name == "idle":
                pose = sample_pose(model, tt)
            else:
                pose = sample_pose(model, tt, action=name, action_t=tt)
            row.append(render(model, tex_i, glow_i, pose, size * 2 // 3, yaw=40, ppb=ppb * 2 / 3,
                              label=f"{title} {tt:.2f}s"))
        rows.append(row)
    width = max(sum(im.width for im in r) for r in rows)
    height = sum(max(im.height for im in r) for r in rows)
    out = Image.new("RGB", (width, height), BG)
    y = 0
    for r in rows:
        x = 0
        for im in r:
            out.paste(im, (x, y))
            x += im.width
        y += max(im.height for im in r)
    out.save(path)
    return path


def texture_preview(model, tex, glow, path, scale=4):
    """The painted texture (and glow layer) with UV islands outlined, for debugging the unwrap."""
    t = to_pil(tex)
    im = Image.new("RGBA", t.size, (40, 40, 48, 255))
    im.alpha_composite(t)
    if glow is not None:
        im.alpha_composite(to_pil(glow))
    im = im.resize((t.width * scale, t.height * scale), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    for c in model.all_cubes():
        w, h, d = c.size
        for _, (fx, fy, fw, fh) in _face_rects(c.uv[0], c.uv[1], w, h, d).items():
            if fw and fh:
                dr.rectangle([fx * scale, fy * scale, (fx + fw) * scale - 1, (fy + fh) * scale - 1], outline=(255, 0, 255, 90))
    im.save(path)
    return path
