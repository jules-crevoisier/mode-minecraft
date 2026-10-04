"""A numpy evaluator for density-function JSON (26.2 format), used by tools/world_preview.py.

It runs the pack's own JSON, so the preview shows the shapes the game will build. The noises are ports of
ImprovedNoise / PerlinNoise / NormalNoise (same octaves, amplitudes and value factors) seeded from the noise name,
so they are statistically the game's noises, not the same values. old_blended_noise (base_3d_noise) keeps only
its significant octaves. Caches and interpolation are no-ops; blending is off (blend_alpha 1, blend_offset 0).

Arrays broadcast: x and z have shape (nz, nx, 1), y has shape (1, 1, ny) (or are scalars), so a 2D function
stays 2D until it meets y.
"""
import hashlib
import json
import os

import numpy as np

GRAD = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
                 [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1], [1, 1, 0], [0, -1, 1], [-1, 1, 0], [0, -1, -1]],
                dtype=np.float64)

# vanilla noise parameters (NoiseData.bootstrap, 26.2)
VANILLA_NOISES = {
    "temperature": (-10, [1.5, 0, 1, 0, 0, 0]), "vegetation": (-8, [1, 1, 0, 0, 0, 0]),
    "continentalness": (-9, [1, 1, 2, 2, 2, 1, 1, 1, 1]), "erosion": (-9, [1, 1, 0, 1, 1]),
    "ridge": (-7, [1, 2, 1, 0, 0, 0]), "offset": (-3, [1, 1, 1, 0]),
    "aquifer_barrier": (-3, [1]), "aquifer_fluid_level_floodedness": (-7, [1]), "aquifer_lava": (-1, [1]),
    "aquifer_fluid_level_spread": (-5, [1]), "pillar": (-7, [1, 1]), "pillar_rareness": (-8, [1]),
    "pillar_thickness": (-8, [1]), "spaghetti_2d": (-7, [1]), "spaghetti_2d_elevation": (-8, [1]),
    "spaghetti_2d_modulator": (-11, [1]), "spaghetti_2d_thickness": (-11, [1]), "spaghetti_3d_1": (-7, [1]),
    "spaghetti_3d_2": (-7, [1]), "spaghetti_3d_rarity": (-11, [1]), "spaghetti_3d_thickness": (-8, [1]),
    "spaghetti_roughness": (-5, [1]), "spaghetti_roughness_modulator": (-8, [1]), "cave_entrance": (-7, [0.4, 0.5, 1]),
    "cave_layer": (-8, [1]), "cave_cheese": (-8, [0.5, 1, 2, 1, 2, 1, 0, 2, 0]), "ore_veininess": (-8, [1]),
    "ore_vein_a": (-7, [1]), "ore_vein_b": (-7, [1]), "ore_gap": (-5, [1]), "noodle": (-8, [1]),
    "noodle_thickness": (-8, [1]), "noodle_ridge_a": (-7, [1]), "noodle_ridge_b": (-7, [1]),
    "jagged": (-16, [1] * 16), "surface": (-6, [1, 1, 1]),
}


def _seed(name, seed):
    return int.from_bytes(hashlib.sha256(f"{seed}:{name}".encode()).digest()[:8], "little")


class Improved:
    def __init__(self, rng):
        self.o = rng.random(3) * 256.0
        p = rng.permutation(256).astype(np.int64)
        self.p = np.concatenate([p, p])

    def __call__(self, x, y, z):
        x = x + self.o[0]
        y = y + self.o[1]
        z = z + self.o[2]
        xf, yf, zf = np.floor(x), np.floor(y), np.floor(z)
        xr, yr, zr = x - xf, y - yf, z - zf
        xi = xf.astype(np.int64) & 255
        yi = yf.astype(np.int64) & 255
        zi = zf.astype(np.int64) & 255
        p = self.p
        x0, x1 = p[xi], p[xi + 1]
        xy00, xy01 = p[(x0 + yi) & 255], p[(x0 + yi + 1) & 255]
        xy10, xy11 = p[(x1 + yi) & 255], p[(x1 + yi + 1) & 255]

        def g(h, dx, dy, dz):
            gr = GRAD[h & 15]
            return gr[..., 0] * dx + gr[..., 1] * dy + gr[..., 2] * dz
        d000 = g(p[(xy00 + zi) & 255], xr, yr, zr)
        d100 = g(p[(xy10 + zi) & 255], xr - 1, yr, zr)
        d010 = g(p[(xy01 + zi) & 255], xr, yr - 1, zr)
        d110 = g(p[(xy11 + zi) & 255], xr - 1, yr - 1, zr)
        d001 = g(p[(xy00 + zi + 1) & 255], xr, yr, zr - 1)
        d101 = g(p[(xy10 + zi + 1) & 255], xr - 1, yr, zr - 1)
        d011 = g(p[(xy01 + zi + 1) & 255], xr, yr - 1, zr - 1)
        d111 = g(p[(xy11 + zi + 1) & 255], xr - 1, yr - 1, zr - 1)

        def s(t):
            return t * t * t * (t * (t * 6 - 15) + 10)
        a, b, c = s(xr), s(yr), s(zr)
        x00 = d000 + a * (d100 - d000)
        x10 = d010 + a * (d110 - d010)
        x01 = d001 + a * (d101 - d001)
        x11 = d011 + a * (d111 - d011)
        y0 = x00 + b * (x10 - x00)
        y1 = x01 + b * (x11 - x01)
        return y0 + c * (y1 - y0)


class Perlin:
    def __init__(self, rng, first, amps):
        n = len(amps)
        self.first, self.amps = first, amps
        self.levels = [Improved(rng) if a != 0 else None for a in amps]
        self.low_value = 2.0 ** (n - 1) / (2.0 ** n - 1.0)

    def __call__(self, x, y, z):
        v = 0.0
        f = 2.0 ** self.first
        vf = self.low_value
        for a, lv in zip(self.amps, self.levels):
            if lv is not None:
                v = v + a * lv(x * f, y * f, z * f) * vf
            f *= 2.0
            vf /= 2.0
        return v


class Normal:
    def __init__(self, name, first, amps, seed):
        rng = np.random.default_rng(_seed(name, seed))
        self.a = Perlin(rng, first, amps)
        self.b = Perlin(rng, first, amps)
        nz = [i for i, a in enumerate(amps) if a != 0]
        span = max(nz) - min(nz)
        self.k = (1.0 / 6.0) / (0.1 * (1.0 + 1.0 / (span + 1)))

    def __call__(self, x, y, z):
        f = 1.0181268882175227
        return (self.a(x, y, z) + self.b(x * f, y * f, z * f)) * self.k


class Blended:
    """old_blended_noise with its significant octaves only."""

    def __init__(self, seed, xz_scale, y_scale, xz_factor, y_factor):
        rng = np.random.default_rng(_seed("blended", seed))
        self.xzm, self.ym = 684.412 * xz_scale, 684.412 * y_scale
        self.xzf, self.yf = xz_factor, y_factor
        self.main = [(2.0 ** -i, Improved(rng)) for i in range(3, 8)]
        self.lo = [(2.0 ** -i, Improved(rng)) for i in range(10, 16)]
        self.hi = [(2.0 ** -i, Improved(rng)) for i in range(10, 16)]

    def __call__(self, x, y, z):
        lx, ly, lz = x * self.xzm, y * self.ym, z * self.xzm
        mx, my, mz = lx / self.xzf, ly / self.yf, lz / self.xzf
        main = sum(n(mx * p, my * p, mz * p) / p for p, n in self.main)
        f = np.clip((main / 10.0 + 1.0) / 2.0, 0.0, 1.0)
        lo = sum(n(lx * p, ly * p, lz * p) / p for p, n in self.lo)
        hi = sum(n(lx * p, ly * p, lz * p) / p for p, n in self.hi)
        return (lo / 512.0 + f * (hi - lo) / 512.0) / 128.0


# ------------------------------------------------------------------ vanilla registered functions (NoiseRouterData)
def _n(nid, xz=1.0, y=1.0):
    return {"type": "minecraft:noise", "noise": nid, "xz_scale": xz, "y_scale": y}


def _op(t, a, b):
    return {"type": f"minecraft:{t}", "argument1": a, "argument2": b}


def _u(t, a):
    return {"type": f"minecraft:{t}", "argument": a}


def _mapped(nid, xz, y, lo, hi):
    return _op("add", (lo + hi) / 2, _op("mul", (hi - lo) / 2, _n(nid, xz, y)))


def _yg(a, b, c, d):
    return {"type": "minecraft:y_clamped_gradient", "from_y": a, "to_y": b, "from_value": c, "to_value": d}


def _rc(i, lo, hi, a, b):
    return {"type": "minecraft:range_choice", "input": i, "min_inclusive": lo, "max_exclusive": hi,
            "when_in_range": a, "when_out_of_range": b}


def _rarity(mod, nid, th, rs):
    fns = [_op("mul", r, _n(nid, 1.0 / r, 1.0 / r)) for r in rs]
    return _u("abs", {"type": "minecraft:interval_select", "input": mod, "thresholds": th, "functions": fns})


def _shifted(nid):
    return {"type": "minecraft:shifted_noise", "noise": nid, "xz_scale": 0.25, "y_scale": 0.0,
            "shift_x": "minecraft:shift_x", "shift_y": 0.0, "shift_z": "minecraft:shift_z"}


def vanilla_functions():
    y = _yg(-4064, 4062, -4064, 4062)
    rough = _op("mul", _mapped("minecraft:spaghetti_roughness_modulator", 1, 1, 0.0, -0.1),
                _op("add", _u("abs", _n("minecraft:spaghetti_roughness")), -0.4))
    rar3 = _n("minecraft:spaghetti_3d_rarity", 2.0, 1.0)
    sp3 = {"type": "minecraft:clamp", "min": -1.0, "max": 1.0, "input": _op("add", _op(
        "max", _rarity(rar3, "minecraft:spaghetti_3d_1", [-0.5, 0.0, 0.5], [0.75, 1.0, 1.5, 2.0]),
        _rarity(rar3, "minecraft:spaghetti_3d_2", [-0.5, 0.0, 0.5], [0.75, 1.0, 1.5, 2.0])),
        _mapped("minecraft:spaghetti_3d_thickness", 1, 1, -0.065, -0.088))}
    big = _op("add", _op("add", _n("minecraft:cave_entrance", 0.75, 0.5), 0.37), _yg(-10, 30, 0.3, 0.0))
    entrances = _op("min", big, _op("add", "minecraft:overworld/caves/spaghetti_roughness_function", sp3))
    thick = _mapped("minecraft:spaghetti_2d_thickness", 2.0, 1.0, -0.6, -1.3)
    sp2 = _rarity(_n("minecraft:spaghetti_2d_modulator", 2.0, 1.0), "minecraft:spaghetti_2d",
                  [-0.75, -0.5, 0.5, 0.75], [0.5, 0.75, 1.0, 2.0, 3.0])
    elev = _mapped("minecraft:spaghetti_2d_elevation", 1.0, 0.0, 0.0, -8.0)
    sloped = _u("abs", _op("add", elev, _yg(-64, 320, 8.0, -40.0)))
    layer = _u("cube", _op("add", sloped, thick))
    spaghetti_2d = {"type": "minecraft:clamp", "min": -1.0, "max": 1.0,
                    "input": _op("max", _op("add", sp2, _op("mul", 0.083, thick)), layer)}

    def ylim(fn, lo, hi, out):
        return _rc(y, lo, hi + 1, fn, out)
    toggle = ylim(_n("minecraft:noodle", 1, 1), -60, 320, -1.0)
    nthick = ylim(_mapped("minecraft:noodle_thickness", 1, 1, -0.05, -0.1), -60, 320, 0.0)
    ra = ylim(_n("minecraft:noodle_ridge_a", 2.6666666666666665, 2.6666666666666665), -60, 320, 0.0)
    rb = ylim(_n("minecraft:noodle_ridge_b", 2.6666666666666665, 2.6666666666666665), -60, 320, 0.0)
    noodle = _rc(toggle, -1000000.0, 0.0, 64.0,
                 _op("add", nthick, _op("mul", 1.5, _op("max", _u("abs", ra), _u("abs", rb)))))
    pillars = _op("mul", _op("add", _op("mul", _n("minecraft:pillar", 25.0, 0.3), 2.0),
                             _mapped("minecraft:pillar_rareness", 1, 1, 0.0, -2.0)),
                  _u("cube", _mapped("minecraft:pillar_thickness", 1, 1, 0.0, 1.1)))
    ridges = "minecraft:overworld/ridges"
    return {
        "minecraft:y": y,
        "minecraft:zero": 0.0,
        "minecraft:shift_x": {"type": "minecraft:shift_a", "argument": "minecraft:offset"},
        "minecraft:shift_z": {"type": "minecraft:shift_b", "argument": "minecraft:offset"},
        "minecraft:overworld/continents": _shifted("minecraft:continentalness"),
        "minecraft:overworld/erosion": _shifted("minecraft:erosion"),
        "minecraft:overworld/ridges": _shifted("minecraft:ridge"),
        "minecraft:overworld/ridges_folded": _op("mul", _op("add", _u("abs", _op("add", _u("abs", ridges),
                                                                              -0.6666666666666666)),
                                                            -0.3333333333333333), -3.0),
        "minecraft:overworld/base_3d_noise": {"type": "minecraft:old_blended_noise", "xz_scale": 0.25,
                                              "y_scale": 0.125, "xz_factor": 80.0, "y_factor": 160.0,
                                              "smear_scale_multiplier": 8.0},
        "minecraft:overworld/caves/spaghetti_roughness_function": rough,
        "minecraft:overworld/caves/entrances": entrances,
        "minecraft:overworld/caves/spaghetti_2d": spaghetti_2d,
        "minecraft:overworld/caves/noodle": noodle,
        "minecraft:overworld/caves/pillars": pillars,
    }


# ------------------------------------------------------------------ the evaluator
class Evaluator:
    def __init__(self, functions, noises, seed=0):
        """functions: id -> JSON (ours and vanilla), noises: id -> (firstOctave, amplitudes)."""
        self.functions = dict(vanilla_functions())
        self.functions.update(functions)
        self.noise_params = {f"minecraft:{k}": v for k, v in VANILLA_NOISES.items()}
        self.noise_params.update(noises)
        self.seed = seed
        self._noises = {}
        self._blended = None
        self.memo = {}

    @classmethod
    def from_pack(cls, data_dir, seed=0):
        fns, noises = {}, {}
        for ns in os.listdir(data_dir):
            base = os.path.join(data_dir, ns, "worldgen")
            for kind, out in (("density_function", fns), ("noise", noises)):
                root = os.path.join(base, kind)
                for dirpath, _, files in os.walk(root):
                    for f in files:
                        if f.endswith(".json"):
                            rel = os.path.relpath(os.path.join(dirpath, f), root)[:-5].replace(os.sep, "/")
                            j = json.load(open(os.path.join(dirpath, f)))
                            out[f"{ns}:{rel}"] = j if kind == "density_function" else (j["firstOctave"], j["amplitudes"])
        return cls(fns, noises, seed)

    def noise(self, nid):
        if nid not in self._noises:
            first, amps = self.noise_params[nid]
            self._noises[nid] = Normal(nid, first, amps, self.seed)
        return self._noises[nid]

    def begin(self, x, y, z):
        """Set the sample positions (broadcastable arrays) and clear the per-region cache."""
        self.x, self.y, self.z = x, y, z
        self.memo = {}

    def ev(self, node):
        if isinstance(node, (int, float)):
            return float(node)
        if isinstance(node, str):
            if node not in self.memo:
                self.memo[node] = self.ev(self.functions[node])
            return self.memo[node]
        t = node["type"].split(":")[1]
        if t in ("add", "mul", "min", "max"):
            a, b = self.ev(node["argument1"]), self.ev(node["argument2"])
            return {"add": np.add, "mul": np.multiply, "min": np.minimum, "max": np.maximum}[t](a, b)
        if t in ("flat_cache", "cache_2d", "cache_once", "cache_all_in_cell", "interpolated", "blend_density"):
            return self.ev(node["argument"])
        if t in ("abs", "square", "cube", "half_negative", "quarter_negative", "invert", "squeeze"):
            v = self.ev(node["argument"])
            if t == "abs":
                return np.abs(v)
            if t == "square":
                return v * v
            if t == "cube":
                return v * v * v
            if t == "half_negative":
                return np.where(v > 0, v, v * 0.5)
            if t == "quarter_negative":
                return np.where(v > 0, v, v * 0.25)
            if t == "invert":
                return 1.0 / v
            c = np.clip(v, -1.0, 1.0)
            return c / 2.0 - c * c * c / 24.0
        if t == "clamp":
            return np.clip(self.ev(node["input"]), node["min"], node["max"])
        if t == "constant":
            return float(node["argument"])
        if t == "y_clamped_gradient":
            y0, y1, v0, v1 = node["from_y"], node["to_y"], node["from_value"], node["to_value"]
            return v0 + (v1 - v0) * np.clip((self.y - y0) / (y1 - y0), 0.0, 1.0)
        if t == "noise":
            n = self.noise(node["noise"])
            ys = node["y_scale"]
            return n(self.x * node["xz_scale"], self.y * ys if ys else 0.0, self.z * node["xz_scale"])
        if t == "shifted_noise":
            n = self.noise(node["noise"])
            sx, sz = self.ev(node["shift_x"]), self.ev(node["shift_z"])
            sy = self.ev(node["shift_y"])
            ys = node["y_scale"]
            return n(self.x * node["xz_scale"] + sx, (self.y * ys if ys else 0.0) + sy, self.z * node["xz_scale"] + sz)
        if t in ("shift_a", "shift_b", "shift"):
            n = self.noise(node["argument"])
            if t == "shift_a":
                return n(self.x * 0.25, 0.0, self.z * 0.25) * 4.0
            if t == "shift_b":
                return n(self.z * 0.25, self.x * 0.25, 0.0) * 4.0
            return n(self.x * 0.25, self.y * 0.25, self.z * 0.25) * 4.0
        if t == "range_choice":
            v = self.ev(node["input"])
            inside = (v >= node["min_inclusive"]) & (v < node["max_exclusive"])
            if np.all(inside):
                return self.ev(node["when_in_range"])
            if not np.any(inside):
                return self.ev(node["when_out_of_range"])
            return np.where(inside, self.ev(node["when_in_range"]), self.ev(node["when_out_of_range"]))
        if t == "interval_select":
            v = self.ev(node["input"])
            th = node["thresholds"]
            out = self.ev(node["functions"][-1])
            for i in reversed(range(len(th))):
                out = np.where(v < th[i], self.ev(node["functions"][i]), out)
            return out
        if t == "spline":
            return self.spline(node["spline"])
        if t == "old_blended_noise":
            if self._blended is None:
                self._blended = Blended(self.seed, node["xz_scale"], node["y_scale"], node["xz_factor"], node["y_factor"])
            return self._blended(self.x, self.y, self.z)
        if t == "blend_alpha":
            return 1.0
        if t in ("blend_offset", "beardifier"):
            return 0.0
        if t == "find_top_surface":
            return 0.0
        raise ValueError(f"density function type {t} not supported by the preview")

    def spline(self, sp):
        if isinstance(sp, (int, float)):
            return float(sp)
        c = self.ev(sp["coordinate"])
        pts = sp["points"]
        locs = np.array([p["location"] for p in pts])
        ders = np.array([p["derivative"] for p in pts])
        vals = [self.spline(p["value"]) for p in pts]
        c = np.asarray(c, dtype=np.float64)
        shape = np.broadcast_shapes(c.shape, *[np.shape(v) for v in vals])
        c = np.broadcast_to(c, shape)
        vals = [np.broadcast_to(v, shape) for v in vals]
        i = np.searchsorted(locs, c, side="right") - 1
        out = np.empty(shape)
        lo = i < 0
        if lo.any():
            out[lo] = vals[0][lo] + ders[0] * (c[lo] - locs[0])
        n = len(pts) - 1
        hi = i >= n
        if hi.any():
            out[hi] = vals[n][hi] + ders[n] * (c[hi] - locs[n])
        for k in range(n):
            m = i == k
            if not m.any():
                continue
            x1, x2 = locs[k], locs[k + 1]
            t = (c[m] - x1) / (x2 - x1)
            y1, y2 = vals[k][m], vals[k + 1][m]
            a = ders[k] * (x2 - x1) - (y2 - y1)
            b = -ders[k + 1] * (x2 - x1) + (y2 - y1)
            out[m] = y1 + t * (y2 - y1) + t * (1 - t) * (a + t * (b - a))
        return out
