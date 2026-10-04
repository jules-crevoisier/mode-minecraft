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

Biome statistics (2D only, ~15 s a seed): the share of the land each biome takes on 8192 x 8192 blocks around 0,0
for several seeds, checked against the targets (every land biome 1-8% on average, the SHOWCASE biomes 3-6%, none
above 10% on any seed), the distance /locate needs for each biome, and the land biomes within 1500 blocks of spawn:
  build/world_preview/stats.txt, stats_relief_<seed>.png, stats_biomes_<seed>.png (1 px = step blocks)

  python3 tools/world_preview.py --stats [--seeds 1 2 3] [--stats-size 8192] [--stats-step 16]

Postcards (needs Pillow): an isometric render of a 96 x 96 sample of each showcase biome (the window where it covers
the most ground) with its surface blocks and decoration (wf/postcard.py), on the biome's fog colour:
  build/world_preview/postcard_<biome>.png, postcards.txt

  python3 tools/world_preview.py --postcards [BIOME ...] [--seed 1]
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


def biome_lookup(points, cl, depth=None, names=None):
    """Climate.ParameterList: the point nearest to the sampled parameters (surface: depth 0)."""
    keys = ["temperature", "humidity", "continentalness", "erosion", "weirdness"]
    vals = [cl["t"], cl["h"], cl["c"], cl["e"], cl["w"]]
    names = names or sorted({p["biome"] for p in points})
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
    dep = np.zeros(vals[0].size) if depth is None else np.broadcast_to(depth, vals[0].shape).ravel()
    flat = np.stack([v.ravel() for v in vals] + [dep], axis=1).astype(np.float32)
    if depth is None:
        # the 5 climate axes are cut by the points' bounds into cells whose nearest point is the same for every
        # sample inside: find it once per cell (at the cell's centre), then look the samples up
        edges, centres = [], []
        for j in range(5):
            e = np.unique(np.concatenate([lo[:, j], hi[:, j]]))
            edges.append(e)
            centres.append(np.concatenate([[e[0] - 0.01], (e[:-1] + e[1:]) / 2, [e[-1] + 0.01]]))
        cells = np.stack([np.searchsorted(edges[j], flat[:, j], side="right") for j in range(5)], axis=1)
        uniq, inv = np.unique(cells, axis=0, return_inverse=True)
        centre = np.stack([centres[j][uniq[:, j]] for j in range(5)] + [np.zeros(len(uniq))], axis=1)
        table = _nearest(centre.astype(np.float32), lo, hi, bid)
        return table[inv.ravel()].reshape(vals[0].shape), names
    return _nearest(flat, lo, hi, bid).reshape(vals[0].shape), names


def _nearest(flat, lo, hi, bid, chunk=512):
    best = np.zeros(flat.shape[0], np.int32)
    for s in range(0, flat.shape[0], chunk):
        f = flat[s:s + chunk]
        acc = np.zeros((f.shape[0], lo.shape[0]), np.float32)
        for j in range(lo.shape[1]):
            d = np.maximum(0, np.maximum(lo[None, :, j] - f[:, j, None], f[:, j, None] - hi[None, :, j]))
            acc += d * d
        best[s:s + chunk] = bid[np.argmin(acc, axis=1)]
    return best


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


# ------------------------------------------------------------------ biome-share statistics (2D, fast)
# the Dregora-like biomes the overhaul is judged on: 3-6% of the land each
SHOWCASE = ["crimson_mire", "volcanic_highlands", "ashen_wastes", "alpine_peaks", "pale_dunes", "geyser_basin",
            "rimefrost_fjords", "aetherblight_grove"]


def biome_kinds():
    """Our biome id -> 'cave', 'water' (oceans, rivers, the mushroom isles), 'shore' (beaches) or 'land'."""
    from wf import biomes as B
    out = {}
    for bid, b in B.BIOMES.items():
        if b["cave"]:
            out[bid] = "cave"
        elif b["mobs"] in ("ocean", "cold_ocean", "frozen_ocean", "warm_ocean", "mushroom", "river"):
            out[bid] = "water"
        elif b["surface"] in ("beach", "snowy_beach", "basalt"):
            out[bid] = "shore"
        else:
            out[bid] = "land"
    return out


def climate_2d(ev, xs, zs, extra=()):
    """The five climate values (and the 2D terrain height in blocks) on a grid, tile by tile."""
    out = {k: np.zeros((len(zs), len(xs))) for k in ("t", "h", "c", "e", "w", "y") + tuple(extra)}
    weird = T.WEIRD if T.WEIRD in ev.functions else "minecraft:overworld/ridges"      # (older packs)
    ids = {"t": T.TEMP, "h": T.VEG, "c": T.CONT, "e": T.EROS, "w": weird, "y": T.DF + "terrain"}
    ids.update({k: T.DF + k for k in extra})
    tile = 256
    for tz in range(0, len(zs), tile):
        for tx in range(0, len(xs), tile):
            x = xs[None, tx:tx + tile, None].astype(np.float64)
            z = zs[tz:tz + tile, None, None].astype(np.float64)
            ev.begin(x, 0.0, z)
            for k, fid in ids.items():
                v = np.broadcast_to(ev.ev(fid), (z.shape[0], x.shape[1], 1))[..., 0]
                out[k][tz:tz + tile, tx:tx + tile] = v
    out["y"] = T.y_of(out["y"])
    return out


def run_stats(seeds, size, step, locate_size=12800, locate_step=64, near=1500):
    """Per-seed biome shares of the land on size x size blocks around 0,0, the nearest spot of every biome
    (what /locate biome finds within its 6400 radius) and the distinct land biomes within `near` blocks of spawn.
    Writes build/world_preview/stats.txt."""
    global SEED
    kinds = biome_kinds()
    lines = [f"biome shares of the land (ground above sea level), {size}x{size} around 0,0, step {step}; "
             f"seeds {' '.join(map(str, seeds))}", ""]
    dim = json.load(open(os.path.join(DATA, "minecraft", "dimension", "overworld.json")))
    points = dim["generator"]["biome_source"]["biomes"]
    names = sorted({p["biome"] for p in points})
    surf = [p for p in points if (lambda d: d if isinstance(d, (int, float)) else d[0])(p["parameters"]["depth"]) <= 0.0]
    shares, nearest, near_count, extra = {}, {}, {}, {}
    for seed in seeds:
        SEED = seed
        ev, _, _ = load_pack()
        t0 = time.time()
        n = size // step
        xs = -size // 2 + np.arange(n) * step + step // 2
        cl = climate_2d(ev, xs, xs, extra=tuple(k for k in ("mire_mask", "fjord_mask") if T.DF + k in ev.functions))
        bmap, _ = biome_lookup(surf, cl, names=names)
        land = cl["y"] >= SEA + 0.5
        cnt = np.bincount(bmap[land].ravel(), minlength=len(names))
        shares[seed] = cnt / max(1, land.sum())
        # water features: inland water (below sea level, continentalness above the coast) and the river biomes
        inland = (cl["y"] < SEA + 0.5) & (cl["c"] > -0.11)
        # where that water comes from: river lines (|weirdness| < 0.05), mires, fjords, else lakes
        river = np.abs(cl["w"]) < 0.05
        mire = cl.get("mire_mask", np.zeros_like(cl["y"])) > 0.5
        fjord = cl.get("fjord_mask", np.zeros_like(cl["y"])) > 0.5
        lakes = inland & ~river & ~mire & ~fjord
        # buildable ground: dry land whose height varies by at most 6 blocks over 48 x 48 blocks (3 x 3 samples
        # at step 16; the 2D height, without the 3D noise)
        yy = np.pad(cl["y"], 1, mode="edge")
        win = np.stack([yy[1 + dz:yy.shape[0] - 1 + dz, 1 + dx:yy.shape[1] - 1 + dx]
                        for dz in (-1, 0, 1) for dx in (-1, 0, 1)])
        flat = land & (win.max(0) - win.min(0) <= 6 * step / 16.0) & (win.min(0) >= SEA + 0.5)
        extra[seed] = (100 * land.mean(), 100 * inland.mean(), 100 * (inland & river).mean(),
                       100 * (inland & mire).mean(), 100 * (inland & fjord).mean(), 100 * lakes.mean(),
                       100 * flat.sum() / max(1, land.sum()))
        # quick maps from the 2D height (no 3D noise, caves or spires): relief and biomes
        shade = hillshade(cl["y"], step)[..., None]
        rel = relief_colour(cl["y"]) * np.where(land[..., None], shade, 0.92)
        write_png(os.path.join(OUT, f"stats_relief_{seed}.png"), np.clip(rel, 0, 255).astype(np.uint8))
        cols = biome_colours(names)
        pal = np.array([cols[nm] for nm in names], float)
        bio = pal[bmap] * (0.45 + 0.55 * shade)
        bio[~land] = bio[~land] * 0.4 + np.array([30, 70, 150]) * 0.6
        write_png(os.path.join(OUT, f"stats_biomes_{seed}.png"), np.clip(bio, 0, 255).astype(np.uint8))
        # biomes near spawn
        zz, xx = np.meshgrid(xs, xs, indexing="ij")
        disc = (xx * xx + zz * zz <= near * near) & land
        c2 = np.bincount(bmap[disc].ravel(), minlength=len(names))
        near_count[seed] = sorted(names[i].split(":")[1] for i in range(len(names))
                                  if c2[i] >= 0.003 * disc.sum() and kinds.get(names[i].split(":")[1]) == "land")
        # /locate: the nearest sample of each biome on a coarser, larger grid (surface, and caves at y 0 and -40)
        m = locate_size // locate_step
        lx = -locate_size // 2 + np.arange(m) * locate_step
        cl2 = climate_2d(ev, lx, lx)
        bm2, _ = biome_lookup(surf, cl2, names=names)
        zz, xx = np.meshgrid(lx, lx, indexing="ij")
        dist = np.sqrt(xx * xx + zz * zz)
        best = np.full(len(names), np.inf)
        for layer in [bm2] + [_cave_layer(ev, points, names, lx, cl2, y) for y in (0, -40)]:
            for i in range(len(names)):
                m_ = layer == i
                if m_.any():
                    best[i] = min(best[i], dist[m_].min())
        nearest[seed] = best
        print(f"  seed {seed}: {time.time() - t0:.0f}s", flush=True)
    rows = []
    for i, nm in enumerate(names):
        bid = nm.split(":")[1]
        sh = [100 * shares[s][i] for s in seeds]
        far = max(nearest[s][i] for s in seeds)
        rows.append((kinds.get(bid, "?"), -np.mean(sh), bid, sh, far))
    rows.sort()
    bad = []
    for kind, _, bid, sh, far in rows:
        tag = "SHOWCASE" if bid in SHOWCASE else ""
        lo_, hi_ = (3.0, 6.0) if bid in SHOWCASE else (1.0, 8.0)
        flag = ""
        # the target is on the mean over the seeds (one 8192-block sample holds only a few climate cycles, so a
        # single seed can be off by 2x); no biome may take more than 10% of any sample
        if kind == "land" and (max(sh) > 10.0 or not lo_ <= np.mean(sh) <= hi_):
            flag = "  <-- out of range"
            bad.append(bid)
        if far > 6400:
            flag += "  <-- NOT LOCATABLE (6400)"
            bad.append(bid)
        lines.append(f"{kind:5s} {bid:24s} " + " ".join(f"{v:5.2f}%" for v in sh) + f"   mean {np.mean(sh):5.2f}%"
                     f"   locate max {far:6.0f}  {tag}{flag}")
    lines.append("")
    for s in seeds:
        e = extra[s]
        lines.append(f"seed {s}: land {e[0]:.1f}%, inland water {e[1]:.2f}% of the area (rivers {e[2]:.2f}, mires "
                     f"{e[3]:.2f}, fjords {e[4]:.2f}, lakes {e[5]:.2f}), flat dry land {e[6]:.1f}% of the land; "
                     f"{len(near_count[s])} land biomes within {near} blocks of spawn: {' '.join(near_count[s])}")
    lines.append(f"out of range: {len(set(bad))} {' '.join(sorted(set(bad)))}")
    open(os.path.join(OUT, "stats.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def _cave_layer(ev, points, names, lx, cl, y):
    x = lx[None, :, None].astype(np.float64)
    z = lx[:, None, None].astype(np.float64)
    ev.begin(x, float(y), z)
    depth = np.broadcast_to(ev.ev(T.DF + "depth"), (len(lx), len(lx), 1))[..., 0]
    bm, _ = biome_lookup(points, cl, depth=depth, names=names)
    return bm


# ------------------------------------------------------------------ postcards (wf/postcard.py)
RELIEF_LOVERS = {"alpine_peaks": 2.0, "volcanic_highlands": 1.0, "ashen_wastes": 0.6, "rimefrost_fjords": 0.6}


def find_sites(ev, wanted, size=6144, step=16):
    """For each wanted biome: the chunk-aligned 96 x 96 window where it covers the most ground (mountain biomes
    also favour relief). Returns {biome: (x0, z0, cover)}."""
    dim = json.load(open(os.path.join(DATA, "minecraft", "dimension", "overworld.json")))
    points = dim["generator"]["biome_source"]["biomes"]
    surf = [p for p in points if (lambda d: d if isinstance(d, (int, float)) else d[0])(p["parameters"]["depth"]) <= 0.0]
    n = size // step
    xs = -size // 2 + np.arange(n) * step
    cl = climate_2d(ev, xs, xs)
    bmap, names = biome_lookup(surf, cl)
    land = cl["y"] >= SEA + 1
    w = 96 // step

    def box(a):
        c = np.pad(np.cumsum(np.cumsum(a, 0), 1), ((1, 0), (1, 0)))
        return c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]
    hs = box(cl["y"]) / (w * w)
    rough = np.sqrt(np.maximum(box(cl["y"] ** 2) / (w * w) - hs ** 2, 0))
    out = {}
    for bid in wanted:
        nm = f"{T.NS}:{bid}"
        if nm not in names:
            continue
        cover = box(((bmap == names.index(nm)) & land).astype(float)) / (w * w)
        dist = np.hypot(*np.meshgrid(xs[:len(cover)], xs[:len(cover)], indexing="ij")) / size
        score = cover + RELIEF_LOVERS.get(bid, 0.0) * np.minimum(rough / 40.0, 1.0) * (cover > 0.6) - 0.05 * dist
        i, j = np.unravel_index(np.argmax(score), score.shape)
        x0 = int(xs[j]) // 16 * 16
        z0 = int(xs[i]) // 16 * 16
        out[bid] = (x0, z0, float(cover[i, j]))
    return out


def run_postcards(seed, wanted, sites=None):
    from wf import biomes as B
    from wf import postcard
    global SEED
    SEED = seed
    ev, _, dim = load_pack()
    points = dim["generator"]["biome_source"]["biomes"]
    surf = [p for p in points if (lambda d: d if isinstance(d, (int, float)) else d[0])(p["parameters"]["depth"]) <= 0.0]
    names = sorted({p["biome"] for p in points})

    def biome_at(xs, zs):
        cl = climate_2d(ev, xs.astype(np.int64), zs.astype(np.int64))
        bm, _ = biome_lookup(surf, cl, names=names)
        return np.array([n.split(":")[1] for n in names], dtype=object)[bm]
    t0 = time.time()
    sites = sites or find_sites(ev, wanted)
    lines = []
    for bid in wanted:
        if bid not in sites:
            continue
        x0, z0, cover = sites[bid]
        a, blocks, log = postcard.build(ev, DATA, x0, z0, biome_at, seed)
        b = B.BIOMES[bid]
        path = os.path.join(OUT, f"postcard_{bid}.png")
        postcard.render(blocks, path, b["fog"], grass_tint=b["grass"])
        here = sorted(set(a.biome[1:-1, 1:-1].ravel()))
        lines.append(f"postcard_{bid}.png: x {x0}..{x0 + 96} z {z0}..{z0 + 96} (seed {seed}), {100 * cover:.0f}% "
                     f"{bid}, ground y {a.top[1:-1, 1:-1].min()}..{a.top[1:-1, 1:-1].max()}, biomes {' '.join(here)}; "
                     + ", ".join(f"{k.split(':')[-1]} {v}" for k, v in sorted(log.items())))
        print(lines[-1], f"({time.time() - t0:.0f}s)", flush=True)
    open(os.path.join(OUT, "postcards.txt"), "w").write("\n".join(lines) + "\n")


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
    global SEED, DATA
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", action="store_true", help="only render the natural objects (needs Pillow)")
    ap.add_argument("--size", type=int, default=4096)
    ap.add_argument("--step", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--center", type=int, nargs=2, default=(0, 0))
    ap.add_argument("--sections-only", action="store_true")
    ap.add_argument("--stats", action="store_true", help="only the biome-share statistics (2D, fast)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--stats-size", type=int, default=8192)
    ap.add_argument("--stats-step", type=int, default=16)
    ap.add_argument("--pack", help="another pack's data directory (e.g. an older version, to compare)")
    ap.add_argument("--postcards", nargs="*", metavar="BIOME",
                    help="isometric 96x96 renders of the showcase biomes (or of the biomes named), needs Pillow")
    args = ap.parse_args()
    SEED = args.seed
    if args.pack:
        DATA = os.path.abspath(args.pack)
    os.makedirs(OUT, exist_ok=True)
    if args.objects:
        render_objects()
        return
    if args.stats:
        run_stats(args.seeds, args.stats_size, args.stats_step)
        return
    if args.postcards is not None:
        run_postcards(args.seed, args.postcards or SHOWCASE)
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
