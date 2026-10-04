#!/usr/bin/env python3
"""Offline preview of the world overhaul's terrain and biomes (needs numpy; not part of generate_all).

Evaluates the pack's own density functions (src/main/resources/worldgen_pack) with tools/wf/dfeval.py and draws:
  build/world_preview/relief.png      shaded relief, 4096 x 4096 blocks around 0,0 (1 px = 8 blocks)
  build/world_preview/biomes.png      the surface biomes over the relief
  build/world_preview/height.png      height bands (every 32 blocks), skylands outlined in white
  build/world_preview/section_*.png   vertical cross-sections 1024 blocks long (1 px = 2 blocks), caves included
  build/world_preview/legend.txt      biome colours, height statistics, biome shares

The noises are the game's noises (same octaves and amplitudes) with other random values, so shapes and sizes are
right but this is not the map of any real seed.

  python3 tools/world_preview.py [--size 4096] [--step 8] [--seed 1] [--center X Z] [--sections-only]
"""
import argparse
import colorsys
import hashlib
import json
import os
import struct
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wf import dfeval  # noqa: E402
from wf import terrain as T  # noqa: E402

ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "src", "main", "resources", "worldgen_pack", "data")
OUT = os.path.join(ROOT, "build", "world_preview")
SEA = 63


def write_png(path, rgb):
    """rgb: (h, w, 3) uint8."""
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def load_pack():
    ev = dfeval.Evaluator.from_pack(DATA, seed=SEED)
    settings = json.load(open(os.path.join(DATA, "wayfarers", "worldgen", "noise_settings", "overworld.json")))
    dim = json.load(open(os.path.join(DATA, "minecraft", "dimension", "overworld.json")))
    return ev, settings, dim


# ------------------------------------------------------------------ surface heights
def surface(ev, xs, zs, ys):
    """Top surface y (float) of the terrain without caves, and of the ground alone (no spires/skylands)."""
    x = xs[None, :, None].astype(np.float64)
    z = zs[:, None, None].astype(np.float64)
    y = ys[None, None, :].astype(np.float64)
    ev.begin(x, y, z)
    ground = np.broadcast_to(ev.ev(T.DF + "sloped_cheese"), (len(zs), len(xs), len(ys)))
    extra = np.broadcast_to(ev.ev(T.DF + "extra_terrain"), ground.shape)
    every = np.maximum(ground, extra)
    top = ys[-1] + 1.0

    def top_of(d):
        solid = d > 0
        rev = solid[..., ::-1]
        idx = np.argmax(rev, axis=2)
        anyv = rev.any(axis=2)
        k = len(ys) - 1 - idx                     # highest solid level
        k1 = np.minimum(k + 1, len(ys) - 1)
        d0 = np.take_along_axis(d, k[..., None], 2)[..., 0]
        d1 = np.take_along_axis(d, k1[..., None], 2)[..., 0]
        frac = np.where(k1 > k, d0 / np.maximum(d0 - d1, 1e-9), 0.0)
        h = ys[k] + frac * (ys[k1] - ys[k])
        return np.where(anyv, h, ys[0]), np.where(anyv, h, top)
    h_all, _ = top_of(every)
    h_ground, _ = top_of(ground)
    return h_all, h_ground


def climate(ev, xs, zs):
    x = xs[None, :, None].astype(np.float64)
    z = zs[:, None, None].astype(np.float64)
    ev.begin(x, 0.0, z)
    out = {}
    for k, fid in (("t", T.TEMP), ("h", T.VEG), ("c", T.CONT), ("e", T.EROS), ("w", T.WEIRD)):
        out[k] = np.broadcast_to(ev.ev(fid), (len(zs), len(xs), 1))[..., 0].copy()
    out["region_spire"] = np.broadcast_to(ev.ev(T.DF + "spire_region"), (len(zs), len(xs), 1))[..., 0].copy()
    out["region_sky"] = np.broadcast_to(ev.ev(T.DF + "skyland_region"), (len(zs), len(xs), 1))[..., 0].copy()
    out["region_fjord"] = np.broadcast_to(ev.ev(T.DF + "fjord_mask"), (len(zs), len(xs), 1))[..., 0].copy()
    return out


def biome_lookup(points, cl):
    """Climate.ParameterList: the point nearest to the sampled parameters (surface: depth 0)."""
    keys = ["temperature", "humidity", "continentalness", "erosion", "weirdness"]
    vals = [cl["t"], cl["h"], cl["c"], cl["e"], cl["w"]]
    names = sorted({p["biome"] for p in points})
    idx_of = {n: i for i, n in enumerate(names)}
    lo = np.zeros((len(points), 6), np.float32)
    hi = np.zeros((len(points), 6), np.float32)
    bid = np.zeros(len(points), np.int32)
    for i, p in enumerate(points):
        for j, k in enumerate(keys + ["depth"]):
            v = p["parameters"][k]
            a, b = (v, v) if isinstance(v, (int, float)) else v
            lo[i, j], hi[i, j] = a, b
        bid[i] = idx_of[p["biome"]]
    flat = np.stack([v.ravel() for v in vals] + [np.zeros(vals[0].size)], axis=1).astype(np.float32)
    best = np.zeros(flat.shape[0], np.int32)
    for s in range(0, flat.shape[0], 2048):
        f = flat[s:s + 2048, None, :]
        d = np.maximum(0, np.maximum(lo[None] - f, f - hi[None]))
        best[s:s + 2048] = bid[np.argmin((d * d).sum(axis=2), axis=1)]
    return best.reshape(vals[0].shape), names


# ------------------------------------------------------------------ colours
def biome_colours(names):
    sys.path.insert(0, HERE)
    from wf import biomes as B
    out = {}
    for n in names:
        bid = n.split(":")[1]
        b = B.BIOMES.get(bid, {})
        c = b.get("grass") or b.get("water") or "#808080"
        if b.get("surface") in ("desert", "beach", "snowy_beach"):
            c = "#e3d29a" if b["surface"] != "snowy_beach" else "#e8eef5"
        if b.get("surface") in ("badlands", "cogwork", "rust", "brass_mesa"):
            c = {"badlands": "#c46a34", "cogwork": "#a8743c", "rust": "#9c4a2a", "brass_mesa": "#c8a046"}[b["surface"]]
        if b.get("surface") in ("peaks", "glacier", "snow_slopes", "snowy_grass"):
            c = {"peaks": "#f2f6fb", "glacier": "#bfe3f5", "snow_slopes": "#dfe8f1", "snowy_grass": "#cfdccf"}[b["surface"]]
        if b.get("surface") in ("spires", "ember"):
            c = "#9a9590" if b["surface"] == "spires" else "#4a3c3a"
        r, g, bl = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, bl / 255)
        jitter = (int(hashlib.md5(bid.encode()).hexdigest()[:4], 16) / 65535 - 0.5) * 0.12
        r, g, bl = colorsys.hls_to_rgb((hh + jitter) % 1.0, ll, min(1.0, ss * 1.1))
        out[n] = (int(r * 255), int(g * 255), int(bl * 255))
    return out


def hillshade(h, step):
    gy, gx = np.gradient(h, step)
    slope = np.arctan(np.hypot(gx, gy) * 1.6)
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(315), np.radians(42)
    s = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    return np.clip(s, 0.15, 1.0)


def relief_colour(h):
    stops = [(-64, (20, 40, 90)), (20, (30, 70, 140)), (55, (60, 120, 190)), (SEA, (90, 160, 210)),
             (SEA + 0.01, (200, 190, 140)), (70, (110, 160, 80)), (100, (80, 135, 60)), (140, (120, 130, 80)),
             (180, (140, 120, 95)), (220, (130, 125, 120)), (260, (200, 200, 205)), (320, (250, 252, 255))]
    ys = np.array([s[0] for s in stops], float)
    out = np.zeros(h.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(h, ys, [s[1][c] for s in stops])
    return out


# ------------------------------------------------------------------ cross-sections
def section(ev, settings, x0, z0, x1, z1, step=2):
    n = int(max(abs(x1 - x0), abs(z1 - z0)) / step)
    t = np.linspace(0, 1, n)
    xs = (x0 + (x1 - x0) * t)[None, :, None]
    zs = (z0 + (z1 - z0) * t)[None, :, None]
    ys = np.arange(T.MIN_Y, T.TOP_Y, step, dtype=np.float64)[None, None, :]
    ev.begin(xs, ys, zs)
    final = np.broadcast_to(ev.ev(settings["noise_router"]["final_density"]), (1, n, ys.shape[2]))[0]
    ground = np.broadcast_to(ev.ev(T.DF + "sloped_cheese"), (1, n, ys.shape[2]))[0] > 0
    river = np.broadcast_to(ev.ev(T.DF + "underground_river_line"), (1, n, 1))[0, :, 0]
    solid = final > 0                                     # (n, ny)
    yv = ys[0, 0]
    ny = len(yv)
    k = np.arange(ny)[None, :]
    top = np.where(ground.any(1), ny - 1 - np.argmax(ground[:, ::-1], axis=1), -1)[:, None]
    above = k > top
    # the first solid block under air: grass (or sand under water), snow up high
    surf = solid & np.roll(~solid, -1, axis=1) & (k < ny - 1)
    yy = np.broadcast_to(yv[None, :], solid.shape)
    img = np.zeros((n, ny, 3), np.uint8)
    img[:] = (125, 120, 115)
    img[solid & (yy < 0)] = (70, 70, 80)
    img[surf & (yy > SEA + 1)] = (90, 150, 60)
    img[surf & (yy <= SEA + 1)] = (200, 190, 140)
    img[surf & (yy > 230)] = (240, 244, 250)
    img[~solid & above] = (190, 220, 245)
    img[~solid & above & (yy <= SEA)] = (70, 130, 200)
    cave = ~solid & ~above
    img[cave] = (25, 22, 28)
    tunnel = cave & (yy >= T.RIVER_Y - 2) & (yy <= T.RIVER_Y + 16) & (river[:, None] < 0.06)
    img[tunnel] = (40, 90, 170)
    img[cave & (yy <= -54)] = (200, 80, 20)
    img = img.transpose(1, 0, 2)[::-1].copy()
    for y in (SEA, 0, 128, 256, 320):
        r = len(yv) - 1 - int((y - T.MIN_Y) / step)
        img[r, ::8] = (255, 255, 255)
    return img


GROUND_OF = {"thorn": "mud", "arch": "tuff", "crystal": "gravel", "hoodoo": "white_concrete_powder",
             "hot_spring": "calcite", "flat_mushroom": "crimson_nylium", "ash_column": "tuff"}


def render_objects():
    """Isometric renders of every natural object (all variants side by side on a strip of their biome's ground)."""
    from wf import render3d, worldobjects
    from wf.blueprint import Blueprint
    by_kind = {}
    for kind, i, bp in worldobjects.blueprints():
        by_kind.setdefault(kind, []).append(bp)
    for kind, bps in by_kind.items():
        scene = Blueprint(f"preview/{kind}")
        x = 0
        for bp in bps:
            (mx, my, mz), (Mx, My, Mz) = bp.bounds()
            for (bx, by, bz), b in bp.blocks.items():
                scene.blocks[(bx - mx + x, by - my, bz - mz)] = b
            x += Mx - mx + 4
        (mx, my, mz), (Mx, My, Mz) = scene.bounds()
        for gx in range(mx - 2, Mx + 3):
            for gz in range(mz - 2, Mz + 3):
                for gy in (0, 1):                       # the feet are buried 2 blocks
                    scene.blocks.setdefault((gx, gy, gz), (f"minecraft:{GROUND_OF[kind]}", {}, None))
        _, blocks, _, _ = scene.normalized()
        render3d.render(blocks, os.path.join(OUT, f"objects_{kind}.png"), max_side=1600)
        print("objects:", kind)


def main():
    global SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", action="store_true", help="only render the natural objects (needs Pillow)")
    ap.add_argument("--size", type=int, default=4096)
    ap.add_argument("--step", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--center", type=int, nargs=2, default=(0, 0))
    ap.add_argument("--sections-only", action="store_true")
    args = ap.parse_args()
    SEED = args.seed
    os.makedirs(OUT, exist_ok=True)
    if args.objects:
        render_objects()
        return
    ev, settings, dim = load_pack()
    t0 = time.time()
    cx, cz = args.center
    n = args.size // args.step
    xs_all = cx - args.size // 2 + np.arange(n) * args.step
    zs_all = cz - args.size // 2 + np.arange(n) * args.step
    ys = np.arange(-8, T.TOP_Y, 8, dtype=np.float64)
    legend = []
    if not args.sections_only:
        H = np.zeros((n, n))
        G = np.zeros((n, n))
        CL = {k: np.zeros((n, n)) for k in ("t", "h", "c", "e", "w", "region_spire", "region_sky", "region_fjord")}
        tile = 128
        for tz in range(0, n, tile):
            for tx in range(0, n, tile):
                xs, zs = xs_all[tx:tx + tile], zs_all[tz:tz + tile]
                h, g = surface(ev, xs, zs, ys)
                H[tz:tz + tile, tx:tx + tile] = h
                G[tz:tz + tile, tx:tx + tile] = g
                cl = climate(ev, xs, zs)
                for k in CL:
                    CL[k][tz:tz + tile, tx:tx + tile] = cl[k]
            print(f"  rows {tz + tile}/{n}  {time.time() - t0:.0f}s", flush=True)
        np.savez_compressed(os.path.join(OUT, "heights.npz"), H=H, G=G, **CL)
        points = [p for p in dim["generator"]["biome_source"]["biomes"]]
        surf_points = [p for p in points if (lambda d: (d if isinstance(d, (int, float)) else d[0]) <= 0.0)(p["parameters"]["depth"])]
        bmap, names = biome_lookup(surf_points, CL)
        cols = biome_colours(names)
        shade = hillshade(G, args.step)[..., None]
        water = G < SEA
        rel = relief_colour(G) * shade
        rel[water] = relief_colour(G)[water] * 0.92
        sky = (H - G) > 12
        write_png(os.path.join(OUT, "relief.png"), np.clip(rel, 0, 255).astype(np.uint8))
        pal = np.array([cols[nm] for nm in names], float)
        bio = pal[bmap] * (0.35 + 0.65 * shade)
        bio[water] = bio[water] * 0.55 + np.array([30, 70, 150]) * 0.45
        write_png(os.path.join(OUT, "biomes.png"), np.clip(bio, 0, 255).astype(np.uint8))
        bands = (np.floor(H / 32) % 2)[..., None]
        hb = relief_colour(H) * (0.82 + 0.18 * bands) * hillshade(H, args.step)[..., None]
        edge = sky & ~(np.roll(sky, 1, 0) & np.roll(sky, -1, 0) & np.roll(sky, 1, 1) & np.roll(sky, -1, 1))
        hb[edge] = (255, 255, 255)
        write_png(os.path.join(OUT, "height.png"), np.clip(hb, 0, 255).astype(np.uint8))
        land = ~water
        legend.append(f"area {args.size}x{args.size} around {cx},{cz}, seed {args.seed}, step {args.step}")
        legend.append(f"ocean {100 * water.mean():.1f}%  land {100 * land.mean():.1f}%")
        pct = np.percentile(G[land], [10, 25, 50, 75, 90, 99, 99.9]) if land.any() else []
        legend.append("land height percentiles 10/25/50/75/90/99/99.9: " + " ".join(f"{p:.0f}" for p in pct))
        legend.append(f"max ground {G.max():.0f}, max with spires/skylands {H.max():.0f}, skyland area {100 * sky.mean():.2f}%")
        legend.append(f"above y 200: {100 * (G > 200).mean():.2f}%, above 260: {100 * (G > 260).mean():.2f}%, "
                      f"above 300: {100 * (G > 300).mean():.3f}%")
        legend.append("")
        counts = np.bincount(bmap.ravel(), minlength=len(names))
        for i in np.argsort(-counts):
            m = bmap == i
            hh = G[m]
            legend.append(f"{names[i]:34s} {100 * counts[i] / bmap.size:5.2f}%  colour {cols[names[i]]}  "
                          f"height med {np.median(hh) if m.any() else 0:.0f} max {hh.max() if m.any() else 0:.0f}")
        # sections: through the highest point, through skylands, through a canyon, through the coast
        def at(idx):
            zi, xi = np.unravel_index(idx, G.shape)
            return xs_all[xi], zs_all[zi]
        picks = {"peak": at(np.argmax(G))}
        sk = sky & (CL["region_sky"] > 0.1)
        if sk.any():
            picks["skylands"] = at(np.argmax(np.where(sk, H - G, -1)))
        canyon = (CL["e"] > -0.36) & (CL["e"] < -0.2) & (np.abs(CL["w"]) < 0.03) & (CL["c"] > 0.1)
        if canyon.any():
            picks["canyon"] = at(np.argmax(canyon))
        spire = CL["region_spire"] > 0.4
        if spire.any():
            picks["spires"] = at(np.argmax(np.where(spire, H, -1)))
        fj = (CL["region_fjord"] > 0.9) & (np.abs(CL["c"] + 0.12) < 0.04)
        if fj.any():
            picks["fjords"] = at(np.argmax(fj))
        isl = (CL["t"] > 0.6) & (CL["c"] < -0.3) & (CL["c"] > -0.45) & (G > SEA)
        if isl.any():
            picks["archipelago"] = at(np.argmax(isl))
        json.dump({k: [int(v[0]), int(v[1])] for k, v in picks.items()}, open(os.path.join(OUT, "picks.json"), "w"))
    else:
        picks = {k: tuple(v) for k, v in json.load(open(os.path.join(OUT, "picks.json"))).items()}
    for name, (px, pz) in picks.items():
        img = section(ev, settings, px - 512, pz, px + 512, pz)
        write_png(os.path.join(OUT, f"section_{name}.png"), img)
        legend.append(f"section_{name}.png: x {px - 512}..{px + 512} at z {pz}")
    if legend:
        open(os.path.join(OUT, "legend.txt" if not args.sections_only else "sections.txt"), "w").write("\n".join(legend) + "\n")
    print("\n".join(legend[:8]))
    print(f"done in {time.time() - t0:.0f}s -> {OUT}")


SEED = 1
if __name__ == "__main__":
    main()
