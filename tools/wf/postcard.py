"""Postcards of the world overhaul's biomes (tools/world_preview.py --postcards): a 96 x 96 block sample of a biome,
drawn isometrically on the biome's fog colour, so its look can be judged without starting the game.

  * terrain: the pack's own density functions (wf/dfeval.py), solid where max(sloped_cheese, extra_terrain) > 0
    (no caves), water below sea level;
  * top blocks: the pack's surface rule, interpreted here (SurfaceRules: sequence / condition / block / bandlands,
    and the biome, stone_depth, water, y_above, noise_threshold, steep, not, vertical_gradient conditions);
  * decoration: the biome's own feature list. Our features follow their placed-feature JSON (count, rarity,
    sink) and draw the real things (the natural object templates of wf/worldobjects.py, boulders, fallen logs,
    lava springs and pools, hot springs...); vanilla trees and plant patches are imitated with simple shapes.

A judging aid, not a replica: the noises are statistically the game's ones, not a real seed's, and vanilla
features are approximations.
"""
import json
import math
import os
import random

import numpy as np

from . import render3d
from . import terrain as T
from .biomes import BIOMES

NS = "wayfarers"
SEA = 63
N = 96                         # postcard size in blocks (6 x 6 chunks)

# vanilla surface noises used by surface rules (NoiseData)
SURFACE_NOISES = {
    "minecraft:surface": (-6, [1, 1, 1]), "minecraft:surface_secondary": (-6, [1, 1, 0, 1]),
    "minecraft:surface_swamp": (-2, [1]), "minecraft:gravel": (-8, [1, 1, 1, 1]),
    "minecraft:powder_snow": (-6, [1, 1, 1, 1]), "minecraft:calcite": (-9, [1, 1, 1, 1]),
    "minecraft:packed_ice": (-7, [1, 1, 1, 1]), "minecraft:ice": (-4, [1, 1, 1, 1]),
    "minecraft:clay_bands_offset": (-8, [1]),
}
DEFAULT_GRASS, DEFAULT_FOLIAGE = "#79c05a", "#59ae30"


def _hash(*a):
    return random.Random(":".join(map(str, a)))


# ------------------------------------------------------------------ terrain
class Area:
    """A 96 x 96 sample at (x0, z0) (chunk-aligned), with one block of margin for the neighbour tests."""

    def __init__(self, ev, data_dir, x0, z0, biome_at):
        self.ev, self.x0, self.z0 = ev, x0, z0
        for k, v in SURFACE_NOISES.items():
            ev.noise_params.setdefault(k, v)
        self.xs = np.arange(x0 - 1, x0 + N + 1, dtype=np.float64)
        self.zs = np.arange(z0 - 1, z0 + N + 1, dtype=np.float64)
        ev.begin(self.xs[None, :, None], 0.0, self.zs[:, None, None])
        shape = (len(self.zs), len(self.xs))
        est = T.y_of(np.broadcast_to(ev.ev(T.DF + "terrain"), shape + (1,))[..., 0])
        spire = np.broadcast_to(ev.ev(T.DF + "spire_region"), shape + (1,))[..., 0]
        self.ylo = int(max(T.MIN_Y + 1, est.min() - 40))
        self.yhi = int(min(T.TOP_Y - 1, est.max() + 70 + (115 if spire.max() > 0.05 else 0)))
        self.ys = np.arange(self.ylo, self.yhi + 1, dtype=np.float64)
        solid = np.zeros(shape + (len(self.ys),), bool)
        for k in range(0, len(self.ys), 48):
            y = self.ys[k:k + 48]
            ev.begin(self.xs[None, :, None], y[None, None, :], self.zs[:, None, None])
            d = np.maximum(ev.ev(T.DF + "sloped_cheese"), ev.ev(T.DF + "extra_terrain"))
            solid[..., k:k + 48] = np.broadcast_to(d, shape + (len(y),)) > 0
        self.solid = solid                                         # [z, x, y]
        anyv = solid.any(axis=2)
        top = len(self.ys) - 1 - np.argmax(solid[..., ::-1], axis=2)
        self.top = np.where(anyv, self.ylo + top, self.ylo - 1)    # highest solid block (WORLD_SURFACE_WG - 1)
        self.biome = biome_at(self.xs, self.zs)                     # [z, x] biome ids (without namespace)
        self._noise = {}
        # the preliminary surface (noise router's find_top_surface: ~8 blocks under the 2D terrain height, on an
        # 8-block grid), sampled at the chunk corners and interpolated like SurfaceRules.Context.getMinSurfaceLevel
        gx = np.arange(x0 // 16 * 16 - 16, x0 + N + 32, 16, dtype=np.float64)
        gz = np.arange(z0 // 16 * 16 - 16, z0 + N + 32, 16, dtype=np.float64)
        ev.begin(gx[None, :, None], 0.0, gz[:, None, None])
        g = T.y_of(np.broadcast_to(ev.ev(T.DF + "terrain"), (len(gz), len(gx), 1))[..., 0])
        g = np.floor((g - 8.0) / 8.0) * 8.0
        fx = (self.xs - gx[0]) / 16.0
        fz = (self.zs - gz[0]) / 16.0
        ix, iz = np.floor(fx).astype(int), np.floor(fz).astype(int)
        tx, tz = (fx - ix)[None, :], (fz - iz)[:, None]
        c00, c10 = g[iz[:, None], ix[None, :]], g[iz[:, None], ix[None, :] + 1]
        c01, c11 = g[iz[:, None] + 1, ix[None, :]], g[iz[:, None] + 1, ix[None, :] + 1]
        self.prelim = np.floor((c00 * (1 - tx) + c10 * tx) * (1 - tz) + (c01 * (1 - tx) + c11 * tx) * tz)

    def noise2d(self, nid):
        if nid not in self._noise:
            n = self.ev.noise(nid)
            x = self.xs[None, :]
            z = self.zs[:, None]
            self._noise[nid] = np.broadcast_to(n(x * 1.0, 0.0 * x, z * 1.0), (len(self.zs), len(self.xs)))
        return self._noise[nid]

    def in_area(self, x, z):
        return 0 <= x - self.x0 < N and 0 <= z - self.z0 < N

    def idx(self, x, z):
        return z - self.z0 + 1, x - self.x0 + 1

    def height(self, x, z):
        return int(self.top[self.idx(x, z)])

    def biome_of(self, x, z):
        return self.biome[self.idx(x, z)]


# ------------------------------------------------------------------ surface rule interpreter
def _clay_bands():
    """A badlands band table like SurfaceSystem.generateBands: terracotta with runs of colours."""
    rng = random.Random(7)
    bands = ["terracotta"] * 192
    for colour, runs, width in (("orange_terracotta", 30, 1), ("yellow_terracotta", 12, 2),
                                ("brown_terracotta", 12, 2), ("red_terracotta", 12, 2),
                                ("white_terracotta", 6, 3), ("light_gray_terracotta", 6, 1)):
        for _ in range(runs):
            y = rng.randint(0, 191)
            for k in range(rng.randint(1, width)):
                bands[(y + k) % 192] = colour
    return bands


CLAY_BANDS = _clay_bands()


class Surface:
    def __init__(self, area, rule):
        self.a, self.rule = area, rule
        sd = area.noise2d("minecraft:surface")
        jitter = np.vectorize(lambda x, z: _hash("sd", x, z).random() * 0.25)(
            area.xs[None, :].astype(int), area.zs[:, None].astype(int))
        self.surface_depth = (sd * 2.75 + 3.0 + jitter).astype(int)
        self.secondary = area.noise2d("minecraft:surface_secondary")
        h = area.top
        steep = np.zeros_like(h, bool)
        steep[1:-1, :] |= h[2:, :] >= h[:-2, :] + 4               # z + 1 at least 4 above z - 1
        steep[:, 1:-1] |= h[:, :-2] >= h[:, 2:] + 4               # x - 1 at least 4 above x + 1
        self.steep = steep

    def block(self, iz, ix, y, above, water):
        self.ctx = (iz, ix, y, above, water)
        st = self._run(self.rule)
        if st is None:
            return ("minecraft:stone", {})
        return (st["Name"], dict(st.get("Properties", {})))

    def _run(self, r):
        t = r["type"][10:]
        if t == "sequence":
            for s in r["sequence"]:
                v = self._run(s)
                if v is not None:
                    return v
            return None
        if t == "condition":
            return self._run(r["then_run"]) if self._cond(r["if_true"]) else None
        if t == "block":
            return r["result_state"]
        if t == "bandlands":
            iz, ix, y, _, _ = self.ctx
            off = int(round(self.a.noise2d("minecraft:clay_bands_offset")[iz, ix] * 4.0))
            return {"Name": "minecraft:" + CLAY_BANDS[(y + off + 192) % 192]}
        raise ValueError(f"surface rule {t}")

    def _anchor(self, a):
        if "absolute" in a:
            return a["absolute"]
        if "above_bottom" in a:
            return T.MIN_Y + a["above_bottom"]
        return T.TOP_Y - 1 - a["below_top"]

    def _cond(self, c):
        t = c["type"].split(":")[1]
        iz, ix, y, above, water = self.ctx
        if t == "biome":
            return f"{NS}:{self.a.biome[iz, ix]}" in c["biome_is"]
        if t == "not":
            return not self._cond(c["invert"])
        if t == "stone_depth":
            if c["surface_type"] == "ceiling":
                return False
            j = self.surface_depth[iz, ix] if c["add_surface_depth"] else 0
            r = c["secondary_depth_range"]
            k = 0 if r == 0 else int((self.secondary[iz, ix] + 1.0) / 2.0 * r)
            return above <= 1 + c["offset"] + j + k
        if t == "water":
            if water is None:
                return True
            return y + (above if c["add_stone_depth"] else 0) >= \
                water + c["offset"] + self.surface_depth[iz, ix] * c["surface_depth_multiplier"]
        if t == "y_above":
            return y + (above if c["add_stone_depth"] else 0) >= \
                self._anchor(c["anchor"]) + self.surface_depth[iz, ix] * c["surface_depth_multiplier"]
        if t == "noise_threshold":
            v = self.a.noise2d(c["noise"])[iz, ix]
            return c["min_threshold"] <= v <= c["max_threshold"]
        if t == "steep":
            return bool(self.steep[iz, ix])
        if t == "above_preliminary_surface":
            return y >= self.a.prelim[iz, ix] + self.surface_depth[iz, ix] - 8
        if t == "vertical_gradient":
            lo, hi = self._anchor(c["true_at_and_below"]), self._anchor(c["false_at_and_above"])
            if y <= lo:
                return True
            if y >= hi:
                return False
            return _hash(c["random_name"], ix, y, iz).random() < (hi - y) / (hi - lo)
        return False                            # hole, temperature: not used on our land surfaces


# ------------------------------------------------------------------ simple trees and plants (vanilla stand-ins)
def _leaves(scene, x, y, z, leaves):
    scene.setdefault((x, y, z), leaves)


def tree_spruce(scene, rng, x, y, z, log="spruce_log", leaves=("minecraft:spruce_leaves", {}), h=None, snow=False):
    h = h or rng.randint(7, 11)
    for k in range(h):
        scene[(x, y + k, z)] = (f"minecraft:{log}", {"axis": "y"})
    r = rng.randint(2, 3)
    top = y + h
    for k in range(h - 2):
        yy = top - k
        rad = min(r, (k + 1) // 2) if k % 2 == 0 else max(0, min(r, (k + 1) // 2) - 1)
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if abs(dx) + abs(dz) <= rad + (1 if rad > 1 else 0) and (dx, dz) != (0, 0) or k == 0:
                    _leaves(scene, x + dx, yy, z + dz, leaves)
                    if snow and (x + dx, yy + 1, z + dz) not in scene:
                        scene[(x + dx, yy + 1, z + dz)] = ("minecraft:snow", {})
    scene[(x, top, z)] = leaves


def tree_mega_spruce(scene, rng, x, y, z):
    h = rng.randint(20, 30)
    for k in range(h):
        for dx in (0, 1):
            for dz in (0, 1):
                scene[(x + dx, y + k, z + dz)] = ("minecraft:spruce_log", {"axis": "y"})
    leaves = ("minecraft:spruce_leaves", {})
    crown = rng.randint(12, 17)
    for k in range(crown):
        yy = y + h - k
        rad = int(1 + (k / crown) * 4.5)
        for dx in range(-rad, rad + 2):
            for dz in range(-rad, rad + 2):
                if (dx - 0.5) ** 2 + (dz - 0.5) ** 2 <= (rad + 0.3) ** 2:
                    _leaves(scene, x + dx, yy, z + dz, leaves)
    scene[(x, y + h + 1, z)] = leaves


def tree_oak(scene, rng, x, y, z, log="oak_log", leaves=("minecraft:oak_leaves", {}), h=None, r=2):
    h = h or rng.randint(4, 6)
    for k in range(h):
        scene[(x, y + k, z)] = (f"minecraft:{log}" if ":" not in log else log, {"axis": "y"})
    for dy in range(-2, 2):
        rad = r if dy < 0 else r - 1
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                if abs(dx) == rad and abs(dz) == rad and (dy >= 0 or rng.random() < 0.5):
                    continue
                _leaves(scene, x + dx, y + h + dy, z + dz, leaves)


def tree_dark_oak(scene, rng, x, y, z, leaves):
    h = rng.randint(6, 8)
    for k in range(h):
        for dx in (0, 1):
            for dz in (0, 1):
                scene[(x + dx, y + k, z + dz)] = ("minecraft:dark_oak_log", {"axis": "y"})
    for dy in range(-1, 2):
        rad = 3 if dy < 1 else 2
        for dx in range(-rad, rad + 2):
            for dz in range(-rad, rad + 2):
                if (dx - 0.5) ** 2 + (dz - 0.5) ** 2 <= (rad + 0.6) ** 2:
                    _leaves(scene, x + dx, y + h + dy, z + dz, leaves)


def tree_acacia(scene, rng, x, y, z, leaves):
    h = rng.randint(5, 7)
    dx = rng.choice([-1, 1])
    for k in range(h):
        scene[(x + (dx if k > h - 3 else 0), y + k, z)] = ("minecraft:acacia_log", {"axis": "y"})
    cx = x + dx
    for ddx in range(-3, 4):
        for ddz in range(-3, 4):
            if abs(ddx) + abs(ddz) <= 4:
                _leaves(scene, cx + ddx, y + h, z + ddz, leaves)
            if abs(ddx) + abs(ddz) <= 2:
                _leaves(scene, cx + ddx, y + h + 1, z + ddz, leaves)


def huge_mushroom(scene, rng, x, y, z):
    red = rng.random() < 0.5
    h = rng.randint(5, 8)
    for k in range(h):
        scene[(x, y + k, z)] = ("minecraft:mushroom_stem", {})
    cap = "minecraft:red_mushroom_block" if red else "minecraft:brown_mushroom_block"
    r = 2 if red else 3
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if abs(dx) == r and abs(dz) == r:
                continue
            scene[(x + dx, y + h, z + dz)] = (cap, {})
            if red and (abs(dx) == r or abs(dz) == r):
                for k in range(1, 3):
                    scene[(x + dx, y + h - k, z + dz)] = (cap, {})


# where saplings survive (the #minecraft:dirt tag) and where plants are scattered
TREE_GROUND = ("grass_block", "dirt", "podzol", "coarse_dirt", "mud", "moss_block", "rooted_dirt", "mycelium")
PLANT_GROUND = ("grass_block", "dirt", "podzol", "coarse_dirt", "mud", "moss_block", "sand", "red_sand",
                "crimson_nylium", "mycelium", "white_concrete_powder", "terracotta", "snow_block", "rooted_dirt")


# ------------------------------------------------------------------ the decoration
class Decorator:
    def __init__(self, area, data_dir, terrain_blocks):
        self.a, self.data = area, data_dir
        self.terrain = terrain_blocks                       # (x, y, z) -> (name, props), the exposed surface
        self.scene = {}                                     # decoration, drawn over the terrain
        self.objects = None
        self.log = {}

    # --- helpers
    def ground(self, x, z):
        """(y of the first air above the ground, the ground block name)."""
        y = self.a.height(x, z)
        b = self.terrain.get((x, y, z), ("minecraft:stone", {}))[0]
        return y + 1, b

    def dry(self, x, z):
        return self.a.height(x, z) >= SEA

    def put(self, x, y, z, b):
        if self.a.in_area(x, z):
            self.scene[(x, y, z)] = b

    def tint(self, kind, x, z):
        b = BIOMES.get(self.a.biome_of(x, z), {})
        col = (b.get("grass") if kind == "grass" else b.get("foliage")) or \
            (DEFAULT_GRASS if kind == "grass" else DEFAULT_FOLIAGE)
        return col.lstrip("#")

    def leaves(self, name, x, z):
        if name in ("minecraft:spruce_leaves", "minecraft:birch_leaves", "minecraft:cherry_leaves") or \
                not name.startswith("minecraft:"):
            return (name, {})
        return (f"postcard:{name.split(':')[1]}#{self.tint('foliage', x, z)}", {})

    def _placed(self, fid):
        ns, path = fid.split(":")
        p = os.path.join(self.data, ns, "worldgen", "placed_feature", path + ".json")
        return json.load(open(p)) if os.path.exists(p) else None

    def _configured(self, ref):
        if isinstance(ref, dict):
            return ref
        ns, path = ref.split(":")
        for base in (self.data, os.path.join(self.data, "..", "..", "data")):
            p = os.path.join(base, ns, "worldgen", "configured_feature", path + ".json")
            if os.path.exists(p):
                return json.load(open(p))
        return {"type": ref}

    def templates(self):
        if self.objects is None:
            from . import worldobjects
            self.objects = {f"wayfarers:{bp.name}": bp for _, _, bp in worldobjects.blueprints()}
        return self.objects

    # --- placement: the positions a placed feature gets in a chunk
    def positions(self, placement, rng, cx, cz):
        n = 1
        sink = 0
        need_dry = False
        for m in placement:
            t = m["type"].split(":")[1]
            if t == "count":
                c = m["count"]
                n = c if isinstance(c, int) else rng.randint(c["min_inclusive"], c["max_inclusive"])
            elif t == "rarity_filter":
                n = 1 if rng.random() < 1.0 / m["chance"] else 0
            elif t == "random_offset":
                ys = m["y_spread"]
                sink = ys if isinstance(ys, int) else 0
            elif t == "surface_water_depth_filter":
                need_dry = m["max_water_depth"] == 0
        out = []
        for _ in range(n):
            x, z = cx + rng.randint(0, 15), cz + rng.randint(0, 15)
            if need_dry and not self.dry(x, z):
                continue
            out.append((x, self.a.height(x, z) + 1 + sink, z))
        return out

    # --- run the features of every biome present in each chunk
    def run(self, seed):
        for cz in range(self.a.z0, self.a.z0 + N, 16):
            for cx in range(self.a.x0, self.a.x0 + N, 16):
                present = sorted({self.a.biome_of(x, z) for x in range(cx, cx + 16, 4) for z in range(cz, cz + 16, 4)})
                for bid in present:
                    bj = json.load(open(os.path.join(self.data, NS, "worldgen", "biome", bid + ".json")))
                    for step in bj["features"]:
                        for fid in step:
                            rng = _hash(seed, fid, cx, cz)
                            self.feature(fid, rng, cx, cz, bid)

    def feature(self, fid, rng, cx, cz, bid):
        placed = self._placed(fid)
        if placed is not None and fid.startswith(NS):
            conf = self._configured(placed["feature"])
            for x, y, z in self.positions(placed["placement"], rng, cx, cz):
                if self.a.biome_of(x, z) == bid:
                    self.ours(fid, conf, rng, x, y, z)
            return
        spec = VANILLA.get(fid.split(":")[1])
        if spec is None:
            return
        count, fn = spec
        n = int(count) + (1 if rng.random() < count - int(count) else 0)
        for _ in range(n):
            x, z = cx + rng.randint(0, 15), cz + rng.randint(0, 15)
            if self.a.biome_of(x, z) != bid:
                continue
            fn(self, rng, x, z)
            self.log[fid] = self.log.get(fid, 0) + 1

    def ours(self, fid, conf, rng, x, y, z):
        t = conf.get("type", "").split(":")[-1]
        self.log[fid] = self.log.get(fid, 0) + 1
        if t == "template":
            ids = [e["data"]["id"] for e in conf["config"]["templates"]]
            bp = self.templates().get(rng.choice(ids))
            if bp is None:
                return
            turn = rng.randint(0, 3)
            for (bx, by, bz), (name, props, _) in bp.blocks.items():
                for _ in range(turn):
                    bx, bz = -bz, bx
                if name == "minecraft:water" or name.endswith("air"):
                    pass
                self.put(x + bx, y + by, z + bz, (name, props))
        elif t == "block_blob":
            st = conf["config"]["state"]
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    for dz in range(-1, 2):
                        if abs(dx) + abs(dy) + abs(dz) <= 2 and rng.random() < 0.85:
                            self.put(x + dx, y + dy, z + dz, (st["Name"], {}))
        elif t == "fallen_tree":
            log = conf["config"]["trunk_provider"]["state"]["Name"]
            ln = rng.randint(5, 9)
            ax = rng.choice(["x", "z"])
            self.put(x, y, z, (log, {"axis": "y"}))
            for k in range(2, 2 + ln):
                px, pz = (x + k, z) if ax == "x" else (x, z + k)
                if self.a.in_area(px, pz):
                    gy, _ = self.ground(px, pz)
                    self.put(px, gy, pz, (log, {"axis": ax}))
        elif t == "spring_feature":
            self.lava_stream(rng, x, y, z)
        elif t == "lake":
            self.lava_pool(rng, x, z)
        elif t == "simple_block":
            st = conf["config"]["to_place"]["state"]
            if st["Name"].endswith("amethyst_cluster"):
                gy, g = self.ground(x, z)
                self.put(x, gy, z, (st["Name"], {}))
            else:
                gy, _ = self.ground(x, z)
                self.put(x, gy, z, (st["Name"], dict(st.get("Properties", {}))))
        elif t == "tree" or fid.split(":")[1] in ("glowwood", "glowwood_sparse", "rustwood", "rustwood_sparse"):
            self.our_tree(fid, conf, rng, x, z)

    def our_tree(self, fid, conf, rng, x, z):
        gy, g = self.ground(x, z)
        if g.split(":")[1] not in TREE_GROUND and "rust" not in fid:
            return
        name = fid.split(":")[1]
        if "giant_spruce" in name:
            tree_mega_spruce(self.scene, rng, x, gy, z)
        elif "autumn_spruce" in name:
            tree_spruce(self.scene, rng, x, gy, z, leaves=self.leaves("minecraft:oak_leaves", x, z),
                        h=rng.randint(7, 10))
        elif "autumn_oak" in name:
            tree_oak(self.scene, rng, x, gy, z, leaves=self.leaves("minecraft:oak_leaves", x, z))
        elif "rustwood" in name:
            tree_oak(self.scene, rng, x, gy, z, log="wayfarers:rustwood_log",
                     leaves=("wayfarers:rustwood_leaves", {}), h=rng.randint(5, 7))
        elif "glowwood" in name:
            tree_oak(self.scene, rng, x, gy, z, log="wayfarers:glowwood_log",
                     leaves=("wayfarers:glowwood_leaves", {}), h=rng.randint(5, 8))

    def lava_stream(self, rng, x, y, z):
        """SpringFeature at (x, y, z) (2 blocks under the surface): rock above and below, exactly one open side
        (rock_count 4 counts the block below; open = the neighbour column is lower than y), then the flow running
        down the hillside."""
        if not self.a.in_area(x, z):
            return
        s, ylo = self.a.solid, self.a.ylo
        iz, ix = self.a.idx(x, z)
        k = y - ylo
        if not (0 < k < s.shape[2] - 1 and s[iz, ix, k + 1] and s[iz, ix, k - 1]):
            return
        side = [(dx, dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if not s[iz + dz, ix + dx, k]]
        if len(side) != 1:
            return
        self.put(x, y, z, ("minecraft:lava", {}))
        px, pz, steps = x + side[0][0], z + side[0][1], 0
        if self.a.in_area(px, pz):                          # the fall down the open side
            for yy in range(self.a.height(px, pz) + 1, y + 1):
                self.put(px, yy, pz, ("minecraft:lava", {}))
        self.log["lava springs that run"] = self.log.get("lava springs that run", 0) + 1
        while steps < 40:
            cand = [(px + dx, pz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if self.a.in_area(px + dx, pz + dz)]
            if not cand:
                break
            nx, nz = min(cand, key=lambda p: (self.a.height(*p), rng.random()))
            if self.a.height(nx, nz) >= self.a.height(px, pz):
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):      # spreads a little on the flat
                    if self.a.in_area(px + dx, pz + dz) and self.a.height(px + dx, pz + dz) == self.a.height(px, pz):
                        self.put(px + dx, self.a.height(px, pz) + 1, pz + dz, ("minecraft:lava", {}))
                break
            px, pz = nx, nz
            self.put(px, self.a.height(px, pz) + 1, pz, ("minecraft:lava", {}))
            steps += 1

    def lava_pool(self, rng, x, z):
        if not self.a.in_area(x, z):
            return
        r = rng.uniform(2.5, 5.0)
        y = self.a.height(x, z)
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                d = math.hypot(dx, dz * 1.2)
                px, pz = x + dx, z + dz
                if not self.a.in_area(px, pz):
                    continue
                if d <= r:
                    self.put(px, y, pz, ("minecraft:lava", {}))
                    for k in range(1, 8):
                        self.scene[(px, y + k, pz)] = ("minecraft:air", {})
                elif d <= r + 1:
                    self.put(px, y, pz, ("minecraft:blackstone", {}))

    # --- vanilla stand-ins
    def patch(self, rng, x, z, block, tries=24, spread=4, on=PLANT_GROUND, tall=False, water=False):
        for _ in range(tries):
            px, pz = x + rng.randint(-spread, spread), z + rng.randint(-spread, spread)
            if not self.a.in_area(px, pz):
                continue
            gy, g = self.ground(px, pz)
            if water:
                if self.a.height(px, pz) < SEA - 1 and self.a.height(px, pz) > SEA - 4:
                    self.put(px, SEA, pz, (f"minecraft:{block}", {}))
                continue
            if gy <= SEA or g.split(":")[1] not in on or (px, gy, pz) in self.scene:
                continue
            b = block
            if block in ("short_grass", "fern", "tall_grass", "large_fern", "sugar_cane"):
                b = f"postcard:{block}#{self.tint('grass', px, pz)}"
            else:
                b = f"minecraft:{block}"
            self.put(px, gy, pz, (b, {}))
            if tall:
                self.put(px, gy + 1, pz, (b, {}))

    def tree(self, rng, x, z, kind):
        gy, g = self.ground(x, z)
        if gy <= SEA or g.split(":")[1] not in TREE_GROUND:
            return
        if kind == "spruce":
            tree_spruce(self.scene, rng, x, gy, z)
        elif kind == "snowy_spruce":
            tree_spruce(self.scene, rng, x, gy, z, snow=True)
        elif kind == "mega_spruce":
            tree_mega_spruce(self.scene, rng, x, gy, z)
        elif kind == "oak":
            tree_oak(self.scene, rng, x, gy, z, leaves=self.leaves("minecraft:oak_leaves", x, z))
        elif kind == "birch":
            tree_oak(self.scene, rng, x, gy, z, log="birch_log", leaves=("minecraft:birch_leaves", {}),
                     h=rng.randint(5, 8))
        elif kind == "dark_oak":
            if rng.random() < 0.08:
                huge_mushroom(self.scene, rng, x, gy, z)
            else:
                tree_dark_oak(self.scene, rng, x, gy, z, self.leaves("minecraft:dark_oak_leaves", x, z))
        elif kind == "acacia":
            tree_acacia(self.scene, rng, x, gy, z, self.leaves("minecraft:acacia_leaves", x, z))
        elif kind == "jungle":
            tree_oak(self.scene, rng, x, gy, z, log="jungle_log", leaves=self.leaves("minecraft:jungle_leaves", x, z),
                     h=rng.randint(6, 12), r=3)
        elif kind == "cherry":
            tree_oak(self.scene, rng, x, gy, z, log="cherry_log", leaves=("minecraft:cherry_leaves", {}), r=3)


def _t(kind, count):
    return count, lambda d, rng, x, z: d.tree(rng, x, z, kind)


def _mix(count, *kinds):
    return count, lambda d, rng, x, z: d.tree(rng, x, z, rng.choice(kinds))


def _p(block, count, **kw):
    return count, lambda d, rng, x, z: d.patch(rng, x, z, block, **kw)


# vanilla placed features: (count per chunk, stand-in)
VANILLA = {
    "trees_taiga": _mix(10, "spruce", "spruce", "spruce"), "trees_old_growth_spruce_taiga": _mix(10, "mega_spruce", "spruce", "spruce"),
    "trees_old_growth_pine_taiga": _mix(10, "mega_spruce", "spruce"), "trees_snowy": _t("snowy_spruce", 0.1),
    "trees_grove": _t("snowy_spruce", 10), "trees_windswept_hills": _mix(0.1, "spruce", "oak"),
    "dark_forest_vegetation": _t("dark_oak", 16), "trees_plains": _t("oak", 0.05),
    "trees_savanna": _t("acacia", 1), "trees_jungle": _t("jungle", 25), "trees_birch_and_oak_leaf_litter": _mix(10, "oak", "birch"),
    "birch_tall": _t("birch", 10), "trees_flower_forest": _mix(6, "oak", "birch"), "trees_cherry": _t("cherry", 10),
    "trees_swamp": _t("oak", 2), "jungle_bush": _t("oak", 1),
    "patch_grass_taiga": _p("short_grass", 7), "patch_grass_savanna": _p("short_grass", 20),
    "patch_grass_jungle": _p("fern", 25), "patch_grass_forest": _p("short_grass", 2), "patch_grass_plain": _p("short_grass", 5),
    "patch_tall_grass_2": _p("tall_grass", 7, tall=True), "patch_large_fern": _p("large_fern", 5, tall=True),
    "patch_dead_bush_2": _p("dead_bush", 2, tries=6), "patch_dead_bush_badlands": _p("dead_bush", 20, tries=4),
    "patch_dry_grass_desert": _p("dead_bush", 3, tries=6), "patch_dry_grass_badlands": _p("dead_bush", 3, tries=6),
    "patch_sugar_cane_swamp": _p("sugar_cane", 10, tries=8, tall=True), "patch_sugar_cane": _p("sugar_cane", 5, tries=8),
    "patch_waterlily": _p("lily_pad", 4, water=True), "brown_mushroom_old_growth": _p("brown_mushroom", 3, tries=6),
    "red_mushroom_old_growth": _p("red_mushroom", 3, tries=6), "patch_berry_common": _p("sweet_berry_bush", 1, tries=8),
    "forest_flowers": _p("poppy", 3, tries=8), "flower_meadow": _p("cornflower", 4, tries=10),
    "patch_cactus_desert": _p("cactus", 1, tries=3, tall=True),
    "forest_rock": (2, lambda d, rng, x, z: d.ours("forest_rock", {"type": "block_blob", "config": {
        "state": {"Name": "minecraft:mossy_cobblestone"}}}, rng, x, d.ground(x, z)[0] - 1, z)),
}


# ------------------------------------------------------------------ the scene
def build(ev, data_dir, x0, z0, biome_at, seed=1):
    """The terrain (exposed blocks, with the surface rule applied) and the decoration of a 96 x 96 sample."""
    a = Area(ev, data_dir, x0, z0, biome_at)
    rule = json.load(open(os.path.join(data_dir, NS, "worldgen", "noise_settings", "overworld.json")))["surface_rule"]
    surf = Surface(a, rule)
    s = a.solid
    nz, nx, ny = s.shape
    # the blocks to draw: solid ones next to air (or on the sample's sides), above the diorama's base
    base_k = max(0, int(a.top[1:-1, 1:-1].min()) - a.ylo - 8)
    exposed = np.zeros_like(s)
    exposed[..., :-1] |= ~s[..., 1:]
    exposed[1:, :, :] |= ~s[:-1]
    exposed[:-1, :, :] |= ~s[1:]
    exposed[:, 1:, :] |= ~s[:, :-1]
    exposed[:, :-1, :] |= ~s[:, 1:]
    exposed[1, :, :] = exposed[-2, :, :] = True
    exposed[:, 1, :] = exposed[:, -2, :] = True
    exposed &= s
    exposed[:, :, :base_k] = False
    exposed[0], exposed[-1], exposed[:, 0], exposed[:, -1] = False, False, False, False
    # stone depth above (1 at the top of each solid run) and the water above each run
    above = np.zeros(s.shape, np.int32)
    run = np.zeros((nz, nx), np.int32)
    for k in range(ny - 1, -1, -1):
        run = np.where(s[..., k], run + 1, 0)
        above[..., k] = run
    blocks = {}
    for iz, ix, k in zip(*np.nonzero(exposed)):
        y = a.ylo + int(k)
        top_y = y + int(above[iz, ix, k]) - 1
        water = SEA if top_y < SEA - 1 and not s[iz, ix, min(ny - 1, top_y - a.ylo + 1)] else None
        blocks[(int(a.xs[ix]), y, int(a.zs[iz]))] = surf.block(iz, ix, y, int(above[iz, ix, k]), water)
    # water surface
    for iz in range(1, nz - 1):
        for ix in range(1, nx - 1):
            if a.top[iz, ix] < SEA - 1:
                blocks[(int(a.xs[ix]), SEA - 1, int(a.zs[iz]))] = ("minecraft:water", {})
    deco = Decorator(a, data_dir, blocks)
    deco.run(seed)
    for p, b in deco.scene.items():
        if b[0] == "minecraft:air":
            blocks.pop(p, None)
        else:
            blocks[p] = b
    return a, blocks, deco.log


def _tinted(name):
    """Register an icon for 'postcard:<block>#<rrggbb>': the vanilla icon recoloured (leaves, grass)."""
    from PIL import Image, ImageOps
    key = ("postcard", name, ())
    if key in render3d._icons:
        return
    base, col = name.split("#")
    src = render3d.icon(f"minecraft:{base}")
    rgb = tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))
    gray = ImageOps.grayscale(src.convert("RGB"))
    alpha = src.split()[3]
    mean = max(1.0, float(np.asarray(gray, float)[np.asarray(alpha) > 0].mean()))
    g = np.asarray(gray, float) / mean * 0.9
    out = np.clip(g[..., None] * np.array(rgb, float)[None, None, :], 0, 255).astype(np.uint8)
    img = Image.fromarray(out, "RGB").convert("RGBA")
    img.putalpha(alpha)
    render3d._icons[key] = img


def render(blocks, path, bg, grass_tint=None, max_side=1800):
    """Draw the scene (grass tops recoloured with the biome's grass colour)."""
    from PIL import Image
    out = {}
    for (x, y, z), (name, props) in blocks.items():
        if name.startswith("postcard:"):
            _tinted(name.split(":", 1)[1])
        out[(x, y, z)] = (name, props, None)
    if grass_tint:
        key = ("minecraft", "grass_block", ())
        saved = render3d._icons.pop(key, None)
        src = render3d.icon("minecraft:grass_block").copy()
        px = src.load()
        rgb = tuple(int(grass_tint.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        for yy in range(16):
            for xx in range(32):
                r, g, b, al = px[xx, yy]
                if al and abs(xx - 16) * 0.5 + abs(yy - 8) <= 8:       # the top face
                    lum = (r + g + b) / 3.0 / 120.0
                    px[xx, yy] = tuple(int(min(255, c * lum)) for c in rgb) + (al,)
        render3d._icons[key] = src
    mx = min(p[0] for p in out)
    mz = min(p[2] for p in out)
    my = min(p[1] for p in out)
    norm = {(x - mx, y - my, z - mz): b for (x, y, z), b in out.items()}
    rgb = tuple(int(bg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    render3d.render(norm, path, max_side=max_side, bg=rgb + (255,))
    if grass_tint:
        render3d._icons.pop(("minecraft", "grass_block", ()), None)
        if saved is not None:
            render3d._icons[("minecraft", "grass_block", ())] = saved
    return Image
