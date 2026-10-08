#!/usr/bin/env python3
"""Coherence / pathing audit of every Brasshaven structure blueprint (read-only: no template is written).

Each piece is built exactly like ``tools/gen_structures.py`` builds it (builder, creatures, foundation and skirt,
shape resolution, ``wf/support.py`` auto-repair), then checked as a player would experience it:

  walk     a 2-block-tall player (1.8 standing, 1.5 sneaking) flood-fills the piece from its entrances (the terrain
           ring around a surface piece, else the largest walkable area): 0.6 step-up, 1.25 jump, ladders/vines/
           scaffolding/water climbable, doors/gates/trapdoors openable, falls up to 22 blocks (any into water).
           Covered air volumes (rooms) with a floor that nobody can enter, loot/spawners/boss seals/workstations out
           of reach (4.5 blocks, line of sight), doors that open into a wall or a pocket, areas you drop into and
           cannot leave.
  headroom 1-block gaps that need crawling to get somewhere, sneak-only spots (< 1.8), 2-block ceilings in tall
           halls (a beam or lamp hanging into the walkway).
  stairs   staircases with a head-bump, a top that lands under a ceiling or into a wall, a bottom against a wall,
           upside-down or backwards steps; ladders that end under a ceiling or have no landing.
  support  what wf/support.py still finds after its repair (floating torches, half doors...), beds missing a half,
           doorways blocked by leaves or blocks, chests that cannot open (solid block on the lid), floating masses.

Usage:
    python3 tools/audit_structures.py                  # every structure + the village pieces
    python3 tools/audit_structures.py --only guild_outpost sky_isles
    python3 tools/audit_structures.py --only villages
    python3 tools/audit_structures.py --cache build/audit/cache   # reuse built blueprints (delete to rebuild)

Writes build/audit/structures.txt (readable, sorted by severity) and build/audit/structures.json, and prints one
line per piece. Coordinates are blueprint coordinates (the ones the generators use; the template's origin is the
blueprint's minimum corner, given per piece). ``origin`` names the generator call that placed the block at the
issue (innermost helper < structure builder).
"""
import argparse
import collections
import json
import os
import pickle
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, ".."))

from wf import blueprint as B  # noqa: E402

# ------------------------------------------------------------------ generator tracing
# Every Blueprint.set remembers the generator call that made it: the innermost frame outside blueprint.py and the
# innermost frame of a structure module (wf/structures/*, wf/dungeon.py, wf/village.py ...).
_GEN_FILES = ("dungeon.py", "village.py", "megakit.py", "interior.py", "arch.py", "foundation.py", "denizens.py",
              "ocean.py", "furniture.py")
_orig_set = B.Blueprint.set
_orig_paste = B.Blueprint.paste


def _caller():
    f = sys._getframe(2)
    inner = None
    depth = 0
    while f is not None and depth < 14:
        co = f.f_code
        fn = co.co_filename
        if not fn.endswith("blueprint.py") and not fn.endswith("audit_structures.py"):
            if inner is None:
                inner = (co, f.f_lineno)
            if "structures" + os.sep in fn:
                return inner if inner[0] is co else (inner[0], inner[1], co, f.f_lineno)
        f = f.f_back
        depth += 1
    return inner


def _traced_set(self, x, y, z, spec, data=None, keep=False):
    if keep and (x, y, z) in self.blocks:
        return
    _orig_set(self, x, y, z, spec, data, keep)
    tr = self.__dict__.get("_trace")
    if tr is None:
        tr = self._trace = {}
    tr[(x, y, z)] = _caller()


def _traced_paste(self, other, ox, oy, oz):
    _orig_paste(self, other, ox, oy, oz)
    otr = other.__dict__.get("_trace")
    if otr:
        tr = self.__dict__.setdefault("_trace", {})
        for (x, y, z), t in otr.items():
            tr[(x + ox, y + oy, z + oz)] = t


B.Blueprint.set = _traced_set
B.Blueprint.paste = _traced_paste


def _fmt_trace(t):
    if not t:
        return ""
    parts = []
    for i in range(0, len(t), 2):
        co, line = t[i], t[i + 1]
        mod = os.path.splitext(os.path.basename(co.co_filename))[0]
        parts.append(f"{mod}.{co.co_name}:{line}")
    return " < ".join(parts)


import gen_structures as G  # noqa: E402  (registers every structure, applies wf/placement.py overrides)
from wf import defs, support  # noqa: E402

# ------------------------------------------------------------------ collision model (1/16 block units)
SWIM, CLIMB, LAVA, OPEN, HAZ, STAIRHI, SURF3, SURF16 = 1, 2, 4, 8, 16, 32, 64, 128
NONE = (-1, -1, 0)
FULL = (0, 16, 0)

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:structure_void"}
NOCOLL_EXACT = {
    "lever", "redstone_wire", "tripwire", "tripwire_hook", "cobweb", "fire", "soul_fire", "light", "short_grass",
    "tall_grass", "fern", "large_fern", "dead_bush", "seagrass", "tall_seagrass", "kelp", "kelp_plant", "glow_lichen",
    "sculk_vein", "sugar_cane", "wheat", "carrots", "potatoes", "beetroots", "nether_wart", "sweet_berry_bush",
    "pitcher_plant", "pitcher_crop", "torchflower", "torchflower_crop", "open_eyeblossom", "closed_eyeblossom",
    "hanging_roots", "spore_blossom", "pale_hanging_moss", "leaf_litter", "frogspawn", "small_dripleaf",
    "crimson_roots", "warped_roots", "nether_sprouts", "bush", "firefly_bush", "short_dry_grass", "tall_dry_grass",
    "cactus_flower", "wildflowers", "pink_petals", "lily_of_the_valley", "cornflower", "dandelion", "poppy",
    "blue_orchid", "allium", "azure_bluet", "oxeye_daisy", "wither_rose", "sunflower", "lilac", "rose_bush", "peony",
    "red_mushroom", "brown_mushroom", "crimson_fungus", "warped_fungus", "cocoa", "powder_snow", "end_portal",
    "end_gateway", "nether_portal", "melon_stem", "pumpkin_stem", "attached_melon_stem", "attached_pumpkin_stem",
    "big_dripleaf_stem", "glow_anemone", "structure_void", "redstone_wall_torch", "comparator", "repeater",
}
NOCOLL_SUFFIX = ("torch", "_sign", "_banner", "_button", "pressure_plate", "rail", "_sapling", "_tulip", "_coral",
                 "_coral_fan", "_coral_wall_fan", "_propagule")
CLIMBABLE = {"ladder", "vine", "scaffolding", "weeping_vines", "weeping_vines_plant", "twisting_vines",
             "twisting_vines_plant", "cave_vines", "cave_vines_plant"}
PARTIAL = {  # (lo, hi) of the collision box
    "enchanting_table": (0, 12), "stonecutter": (0, 9), "daylight_detector": (0, 6), "cake": (0, 8),
    "sea_pickle": (0, 6), "turtle_egg": (0, 7), "sniffer_egg": (0, 16), "conduit": (5, 11), "big_dripleaf": (11, 15),
    "soul_sand": (0, 14), "mud": (0, 14), "dirt_path": (0, 15), "farmland": (0, 15), "lily_pad": (0, 1),
    "chest": (0, 14), "trapped_chest": (0, 14), "ender_chest": (0, 14), "lectern": (0, 14), "brewing_stand": (0, 14),
    "amethyst_cluster": (0, 7), "large_amethyst_bud": (0, 5), "medium_amethyst_bud": (0, 4),
    "small_amethyst_bud": (0, 3), "heavy_core": (0, 8), "decorated_pot": (0, 16), "waystone": (0, 16),
    "candle_cake": (0, 8),
}
HAZARDS = {"campfire", "soul_campfire", "magma_block", "cactus", "sweet_berry_bush", "lava_cauldron", "fire",
           "soul_fire", "wither_rose", "powder_snow"}

LOOT = {"chest", "trapped_chest", "barrel", "spawner", "boss_seal", "decorated_pot",
        "black_shulker_box", "magenta_shulker_box", "purple_shulker_box", "ender_chest"}
WORKSTATIONS = {"lectern", "crafting_table", "furnace", "smoker", "blast_furnace", "anvil", "chipped_anvil",
                "damaged_anvil", "brewing_stand", "enchanting_table", "cartography_table", "fletching_table",
                "smithing_table", "loom", "grindstone", "stonecutter", "jukebox", "bell", "cauldron",
                "water_cauldron", "lava_cauldron", "composter", "beehive", "waystone", "note_block",
                "auto_harvester", "block_breaker", "block_placer", "compacting_crate", "vacuum_hopper", "sprinkler",
                "redstone_timer", "entity_detector", "wireless_receiver", "wireless_transmitter", "beacon"}
LIGHTS = ("torch", "lantern", "candle", "chandelier", "edison_lamp", "rune_lamp", "ember_lamp", "campfire",
          "sea_lantern", "glowstone", "shroomlight", "froglight", "end_rod", "copper_bulb", "redstone_lamp")
SWITCHES = ("_button", "lever", "pressure_plate", "target", "tripwire_hook", "detector_rail", "redstone_torch",
            "entity_detector", "daylight_detector")


def _furniture_shapes():
    try:
        from wf import furniture
    except Exception:  # pragma: no cover
        return {}
    out = {}
    for fid, f in furniture.FURNITURE.items():
        boxes = f.get("shape") or [b[:6] for b in f["boxes"]]
        out[fid] = (int(min(b[1] for b in boxes)), int(min(24, max(b[4] for b in boxes))))
    return out


MOD_SHAPES = _furniture_shapes()
# 2-3 px thick on one edge of their cell: a player still fits beside them (a railing guards an edge, it does not
# fill the cell)
THIN = {"brass_railing", "wall_cog", "valve_wheel"}
_SHAPES = {}


def shape(name, props):
    key = (name, tuple(sorted(props.items())))
    s = _SHAPES.get(key)
    if s is None:
        s = _SHAPES[key] = _shape(name, props)
    return s


def _shape(name, props):
    """(lo, hi, flags) of the collision of one block state in 1/16 units (lo = -1: nothing collides)."""
    if name in AIR:
        return NONE
    s = name.split(":", 1)[1]
    wl = SWIM if props.get("waterlogged") == "true" else 0
    if s in ("water", "bubble_column"):
        return (-1, -1, SWIM)
    if s == "lava":
        return (-1, -1, LAVA)
    if s == "mist_gate":
        return FULL if props.get("sealed") == "true" else NONE
    if s.endswith("_door") or s.endswith("_fence_gate"):
        return (-1, -1, OPEN | wl)
    if s.endswith("_trapdoor"):
        if props.get("open") == "true":
            return (-1, -1, OPEN | wl)
        return (-1, -1, OPEN | wl | (SURF16 if props.get("half") == "top" else SURF3))
    if s in CLIMBABLE:
        return (-1, -1, CLIMB | wl | (SURF16 if s == "scaffolding" else 0))
    if s.endswith("_slab"):
        t = props.get("type", "bottom")
        return ((0, 8, wl) if t == "bottom" else (8, 16, wl) if t == "top" else (0, 16, wl))
    if s.endswith("_stairs"):
        return (0, 8, wl | STAIRHI) if props.get("half", "bottom") == "bottom" else (8, 16, wl)
    if s.endswith("carpet"):
        return (0, 1, 0)
    if s == "snow":
        n = int(props.get("layers", "1"))
        return NONE if n <= 1 else (0, (n - 1) * 2, 0)
    if s in THIN:
        return (-1, -1, wl)
    if s in MOD_SHAPES:
        lo, hi = MOD_SHAPES[s]
        return (lo, hi, wl)
    fam = B.family(name)
    if fam in ("fence", "nether_fence", "wall"):
        return (0, 24, wl)
    if fam == "pane" or s.endswith("_bars"):
        return (0, 16, wl)
    if s in NOCOLL_EXACT or s.endswith(NOCOLL_SUFFIX) or (s.endswith("_roots") and s != "mangrove_roots"
                                                          and s != "muddy_mangrove_roots"):
        return (-1, -1, wl | (HAZ if s in HAZARDS else 0))
    if s.endswith("_bed"):
        return (0, 9, 0)
    if s in PARTIAL:
        lo, hi = PARTIAL[s]
        return (lo, hi, wl)
    if s.endswith("lantern") and s != "sea_lantern":
        return (1, 10, wl) if props.get("hanging") == "true" else (0, 9, wl)
    if s.startswith("potted_") or s == "flower_pot":
        return (0, 6, 0)
    if s.endswith("candle"):
        return (0, 6, wl)
    if s.endswith("_wall_head") or s.endswith("_wall_skull"):
        return (4, 12, 0)
    if s.endswith("_head") or s.endswith("_skull"):
        return (0, 8, 0)
    if s.endswith("campfire"):
        return (0, 7, wl | HAZ)
    if s == "cactus":
        return (0, 15, HAZ)
    return (0, 16, wl | (HAZ if s in HAZARDS else 0))


def short(name):
    return name.split(":", 1)[1]


# ------------------------------------------------------------------ the voxel world of one piece
BIG = 1 << 20
FALL_CAP = 22 * 16


class World:
    def __init__(self, blocks, ctx, water_unset, margin=4):
        self.blocks = blocks
        self.ctx = ctx
        (mx, my, mz), (Mx, My, Mz) = _bounds(blocks)
        self.bmin, self.bmax = (mx, my, mz), (Mx, My, Mz)
        self.m = margin
        self.o = np.array([mx - margin, my - 2, mz - margin])
        self.shape = (Mx - mx + 1 + 2 * margin, My - my + 1 + 2 + 5, Mz - mz + 1 + 2 * margin)
        NX, NY, NZ = self.shape
        lo = np.full(self.shape, -1, np.int8)
        hi = np.full(self.shape, -1, np.int8)
        fl = np.zeros(self.shape, np.uint8)
        self.terrain = np.zeros(self.shape, bool)
        if ctx.unset_solid:
            self.terrain[:] = True
        elif ctx.ground is not None:
            gy = ctx.ground - self.o[1]
            if gy >= 0:
                self.terrain[:, :gy + 1, :] = True
        known = np.zeros(self.shape, bool)
        pos = np.array(list(blocks.keys()), dtype=np.int64).reshape(-1, 3) - self.o
        vals = np.array([shape(b[0], b[1]) for b in blocks.values()], dtype=np.int64).reshape(-1, 3)
        xs, ys, zs = pos[:, 0], pos[:, 1], pos[:, 2]
        known[xs, ys, zs] = True
        self.terrain &= ~known
        if water_unset and ctx.ground is not None and not ctx.unset_solid:
            # sea water around an ocean-floor piece: only the margin ring and the cells next to the piece are
            # modelled (enough to swim in and around; the open sea above would only cost time)
            gy = max(ctx.ground - self.o[1] + 1, 0)
            near = known.copy()
            for _ in range(2):
                near = Audit._dilate(near)
            ring = np.zeros(self.shape, bool)
            ring[:margin] = ring[-margin:] = True
            ring[:, :, :margin] = ring[:, :, -margin:] = True
            sea = (near | ring) & ~known
            sea[:, :gy, :] = False
            fl[sea] |= SWIM
        lo[self.terrain] = 0
        hi[self.terrain] = 16
        lo[xs, ys, zs] = vals[:, 0]
        hi[xs, ys, zs] = vals[:, 1]
        fl[xs, ys, zs] = vals[:, 2]
        self.lo, self.hi, self.fl, self.known = lo, hi, fl, known
        # climbable trapdoors: a trapdoor right above a ladder works as a ladder
        lad = (fl & CLIMB) != 0
        trap = ((fl & OPEN) != 0) & ((fl & (SURF3 | SURF16)) != 0)
        above_lad = np.zeros_like(lad)
        above_lad[:, 1:, :] = lad[:, :-1, :]
        fl[trap & above_lad] |= CLIMB
        self.obst = hi >= 0

    def idx(self, p):
        return (p[0] - self.o[0], p[1] - self.o[1], p[2] - self.o[2])

    def bp(self, i, y, k):
        return (int(i + self.o[0]), int(y + self.o[1]), int(k + self.o[2]))

    def inside(self, i, y, k):
        NX, NY, NZ = self.shape
        return 0 <= i < NX and 0 <= y < NY and 0 <= k < NZ

    def name_at(self, p):
        b = self.blocks.get(p)
        if b is not None:
            return short(b[0])
        q = self.idx(p)
        if self.inside(*q) and self.terrain[q]:
            return "terrain"
        return "air"


def _bounds(blocks):
    a = np.array(list(blocks.keys()))
    return tuple(int(v) for v in a.min(0)), tuple(int(v) for v in a.max(0))


# ------------------------------------------------------------------ standing nodes and moves
class Graph:
    """Standing positions: per column every surface a player can stand on (feet height H in 1/16), with its
    clearance (open height above, to the next collision) and the flags of the feet cell."""

    def __init__(self, W):
        self.W = W
        NX, NY, NZ = W.shape
        lo, hi, fl, obst = W.lo, W.hi, W.fl, W.obst
        special = (fl & (STAIRHI | SURF3 | SURF16 | CLIMB | SWIM)) != 0
        H_, C_, F_, X_, Z_ = [], [], [], [], []
        col_start = np.zeros(NX * NZ, np.int64)
        col_count = np.zeros(NX * NZ, np.int64)
        n = 0
        top_limit = 16 * (NY - 1)
        for i in range(NX):
            lo_i, hi_i, fl_i, ob_i, sp_i = lo[i], hi[i], fl[i], obst[i], special[i]
            for k in range(NZ):
                ys = np.flatnonzero(ob_i[:, k])
                if len(ys):
                    A = ys * 16 + lo_i[ys, k]
                    Bt = ys * 16 + hi_i[ys, k]
                    Bm = np.maximum.accumulate(Bt)
                    brk = np.flatnonzero(A[1:] > Bm[:-1])
                    SA = A[np.r_[0, brk + 1]]
                    SB = Bm[np.r_[brk, len(ys) - 1]]
                    cand = set(SB.tolist())
                else:
                    SA = SB = np.zeros(0, np.int64)
                    cand = set()
                sp = np.flatnonzero(sp_i[:, k])
                for y in sp.tolist():
                    f = int(fl_i[y, k])
                    if f & STAIRHI:
                        cand.add(16 * y + 16)
                    if f & SURF3:
                        cand.add(16 * y + 3)
                    if f & SURF16:
                        cand.add(16 * y + 16)
                    if f & (CLIMB | SWIM):
                        cand.add(16 * y)
                start = n
                if cand:
                    SAl = SA.tolist()
                    SBl = SB.tolist()
                    for H in sorted(cand):
                        if H >= top_limit:
                            continue
                        j = np.searchsorted(SA, H, "left")
                        if j > 0 and SBl[j - 1] > H:
                            continue  # inside a collision box
                        ceil = SAl[j] if j < len(SAl) else BIG
                        y = H // 16
                        f = int(fl_i[y, k]) if 0 <= y < NY else 0
                        if f & LAVA:
                            continue
                        # flags of the feet cell + those of the cell holding the surface (stairs/trapdoors)
                        clr = ceil - H
                        if clr < 10:
                            continue
                        H_.append(H)
                        C_.append(clr)
                        F_.append(f)
                        X_.append(i)
                        Z_.append(k)
                        n += 1
                col_start[i * NZ + k] = start
                col_count[i * NZ + k] = n - start
        self.H = np.array(H_, np.int64)
        self.C = np.array(C_, np.int64)
        self.F = np.array(F_, np.int64)
        self.X = np.array(X_, np.int64)
        self.Z = np.array(Z_, np.int64)
        self.col = self.X * NZ + self.Z
        self.col_start, self.col_count = col_start, col_count
        self.N = n
        self.swim = (self.F & SWIM) != 0
        self.climb = (self.F & (CLIMB | SWIM)) != 0
        self.need = np.where(self.swim, 10, 24)
        self.valid = self.C >= self.need  # crawl nodes (10..24 high) exist only for the relaxed walk
        self.Y = self.H // 16

    def node_bp(self, n):
        return self.W.bp(self.X[n], self.Y[n], self.Z[n])

    # -------------------------------------------------------------- edges
    def edges(self, relaxed=False):
        """(src, dst) of every move. relaxed: 1-block gaps (crawl) and 2-block steps (no stairs) allowed."""
        NX, NY, NZ = self.W.shape
        N = self.N
        H, C, need = self.H, self.C, self.need
        if relaxed:
            need = np.full(N, 10)
        upcap = 36 if relaxed else 20
        ok_node = C >= need
        K = 1 << 22
        key = self.col * K + H  # sorted (columns in order, H ascending inside)
        srcs, dsts = [], []
        allnodes = np.arange(N)
        for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xi, zk = self.X + di, self.Z + dk
            inb = (xi >= 0) & (xi < NX) & (zk >= 0) & (zk < NZ) & ok_node
            src0 = allnodes[inb]
            c2 = (xi * NZ + zk)[inb]
            Hn = H[inb]
            # landing: the highest node at or below Hn in the next column
            land = np.searchsorted(key, c2 * K + Hn, "right") - 1
            okl = (land >= 0)
            land_c = np.where(okl, land, 0)
            okl &= self.col[land_c] == c2
            Hm, Cm = H[land_c], C[land_c]
            nm = need[land_c]
            okl &= (Hm + Cm >= Hn + nm) & (Cm >= nm) & ((Hn - Hm <= FALL_CAP) | self.swim[land_c])
            srcs.append(src0[okl])
            dsts.append(land_c[okl])
            # up moves: nodes with Hn < Hm <= Hn + upcap
            a = np.searchsorted(key, c2 * K + Hn, "right")
            b = np.searchsorted(key, c2 * K + Hn + upcap, "right")
            cnt = b - a
            tot = int(cnt.sum())
            if tot:
                rs = np.repeat(np.arange(len(src0)), cnt)
                offs = np.cumsum(cnt) - cnt
                m = a[rs] + np.arange(tot) - offs[rs]
                s = src0[rs]
                dH = H[m] - H[s]
                okm = (C[s] >= dH + need[m]) & (C[m] >= need[m]) & (dH > 0)
                srcs.append(s[okm])
                dsts.append(m[okm])
        # same column: next node up / down in the same open segment
        same = (np.r_[self.col[1:] == self.col[:-1], False])
        s = allnodes[same]
        m = s + 1
        seg = H[s] + C[s] == H[m] + C[m]
        dH = H[m] - H[s]
        upok = seg & ok_node[s] & ok_node[m] & ((dH <= 9) | (self.climb[s] & (dH <= 16)))
        srcs.append(s[upok])
        dsts.append(m[upok])
        dnok = seg & ok_node[s] & ok_node[m]
        srcs.append(m[dnok])
        dsts.append(s[dnok])
        src = np.concatenate(srcs)
        dst = np.concatenate(dsts)
        return src, dst

    @staticmethod
    def csr(src, dst, N):
        order = np.argsort(src, kind="stable")
        s, d = src[order], dst[order]
        indptr = np.zeros(N + 1, np.int64)
        np.add.at(indptr, s + 1, 1)
        return np.cumsum(indptr), d, order


def bfs(indptr, nbr, seeds, N):
    seen = np.zeros(N, bool)
    seeds = np.unique(seeds)
    seen[seeds] = True
    frontier = seeds
    while len(frontier):
        starts, ends = indptr[frontier], indptr[frontier + 1]
        cnt = ends - starts
        tot = int(cnt.sum())
        if not tot:
            break
        rs = np.repeat(np.arange(len(frontier)), cnt)
        offs = np.cumsum(cnt) - cnt
        nb = nbr[starts[rs] + np.arange(tot) - offs[rs]]
        nb = np.unique(nb[~seen[nb]])
        seen[nb] = True
        frontier = nb
    return seen


def bfs_gateway(indptr, nbr, eid, extra_mask, seeds_mask):
    """BFS from every node of seeds_mask over strict+relaxed edges; each node reached gets the id of the first
    relaxed edge on its path (gate[n] = edge id, -1 for seeds)."""
    N = len(seeds_mask)
    gate = np.full(N, -2, np.int64)
    gate[seeds_mask] = -1
    frontier = np.flatnonzero(seeds_mask)
    while len(frontier):
        starts, ends = indptr[frontier], indptr[frontier + 1]
        cnt = ends - starts
        tot = int(cnt.sum())
        if not tot:
            break
        rs = np.repeat(np.arange(len(frontier)), cnt)
        offs = np.cumsum(cnt) - cnt
        j = starts[rs] + np.arange(tot) - offs[rs]
        nb = nbr[j]
        new = gate[nb] == -2
        nb, j, rs = nb[new], j[new], rs[new]
        if not len(nb):
            break
        parent_gate = gate[frontier[rs]]
        g = np.where(parent_gate >= 0, parent_gate, np.where(extra_mask[eid[j]], eid[j], -1))
        # first writer wins
        uniq, first = np.unique(nb, return_index=True)
        gate[uniq] = g[first]
        frontier = uniq
    return gate


def components(src, dst, N, mask=None):
    """Connected components of the undirected graph (label = smallest node id), by min-label propagation."""
    lab = np.arange(N)
    if mask is not None:
        keep = mask[src] & mask[dst]
        src, dst = src[keep], dst[keep]
    while True:
        old = lab.copy()
        m = np.minimum(lab[src], lab[dst])
        np.minimum.at(lab, src, m)
        np.minimum.at(lab, dst, m)
        lab = lab[lab]
        lab = lab[lab]
        if np.array_equal(lab, old):
            return lab


# ------------------------------------------------------------------ helpers
def label_cells(mask):
    """6-connected components of a 3D bool mask (Python BFS on flat indices). Returns (labels flat int32, count)."""
    NX, NY, NZ = mask.shape
    m = mask.copy()
    m[0, :, :] = m[-1, :, :] = False
    m[:, 0, :] = m[:, -1, :] = False
    m[:, :, 0] = m[:, :, -1] = False
    flat = m.ravel()
    lab = np.full(flat.shape, -1, np.int32)
    labl = lab  # numpy writes
    cells = np.flatnonzero(flat)
    mb = bytearray(flat.tobytes())
    offs = (1, -1, NZ, -NZ, NY * NZ, -NY * NZ)
    seen = bytearray(len(mb))
    count = 0
    out = {}
    for c in cells.tolist():
        if seen[c]:
            continue
        seen[c] = 1
        comp = [c]
        dq = [c]
        while dq:
            v = dq.pop()
            for o in offs:
                w = v + o
                if mb[w] and not seen[w]:
                    seen[w] = 1
                    comp.append(w)
                    dq.append(w)
        out[count] = comp
        count += 1
    for lid, comp in out.items():
        labl[np.array(comp)] = lid
    return lab.reshape(mask.shape), count


def cluster_points(points, gap=2):
    """Group points (x, y, z) that lie within ``gap`` (Chebyshev) of each other."""
    pts = sorted(set(points))
    idx = {p: i for i, p in enumerate(pts)}
    parent = list(range(len(pts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    rng = range(-gap, gap + 1)
    for p in pts:
        for dx in rng:
            for dy in rng:
                for dz in rng:
                    q = (p[0] + dx, p[1] + dy, p[2] + dz)
                    if q in idx:
                        ra, rb = find(idx[p]), find(idx[q])
                        if ra != rb:
                            parent[ra] = rb
    groups = collections.defaultdict(list)
    for p in pts:
        groups[find(idx[p])].append(p)
    return list(groups.values())


SEV_RANK = {"error": 0, "warn": 1, "info": 2}


class Audit:
    def __init__(self, sid, piece, blocks, ctx, water_unset, trace, mode, data=None):
        self.sid, self.piece = sid, piece
        self.blocks = blocks
        self.ctx = ctx
        self.trace = trace or {}
        self.mode = mode
        self.data = data or {}
        self.issues = []
        self.t0 = time.time()
        self.W = World(blocks, ctx, water_unset)
        self.G = Graph(self.W)

    # -------------------------------------------------------------- reporting
    def add(self, sev, cat, pos, msg, weight=0, positions=None, origin_pos=None):
        op = origin_pos if origin_pos is not None else pos
        self.issues.append({
            "severity": sev, "category": cat, "pos": list(pos), "msg": msg, "weight": int(min(weight, 150)),
            "count": len(positions) if positions else 1,
            "positions": [list(p) for p in (positions or [])[:8]],
            "origin": self.trace.get(tuple(op), "") if op is not None else "",
        })

    def origin_near(self, p, r=1):
        """Trace of the block at p, else of the closest traced block around it."""
        if tuple(p) in self.trace:
            return tuple(p)
        best = None
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    q = (p[0] + dx, p[1] + dy, p[2] + dz)
                    if q in self.trace and q in self.blocks and self.blocks[q][0] not in AIR:
                        d = abs(dx) + abs(dy) + abs(dz)
                        if best is None or d < best[0]:
                            best = (d, q)
        return best[1] if best else tuple(p)

    # -------------------------------------------------------------- walk
    def walk(self):
        G, W = self.G, self.W
        N = G.N
        if N == 0:
            self.reach = self.back = np.zeros(0, bool)
            return
        src, dst = G.edges()
        self.src, self.dst = src, dst
        self.f_indptr, self.f_nbr, _ = Graph.csr(src, dst, N)
        self.r_indptr, self.r_nbr, _ = Graph.csr(dst, src, N)
        NX, NY, NZ = W.shape
        m = W.m
        if self.mode in ("surface", "ocean"):
            edge = (G.X < m) | (G.X >= NX - m) | (G.Z < m) | (G.Z >= NZ - m)
            seeds = np.flatnonzero(edge & G.valid)
            self.seed_kind = "terrain ring around the piece"
        else:
            seeds = np.zeros(0, np.int64)
        if len(seeds) == 0:
            lab = components(src, dst, N, mask=G.valid)
            lab = np.where(G.valid, lab, -1)
            vals, counts = np.unique(lab[lab >= 0], return_counts=True)
            main = vals[np.argmax(counts)] if len(vals) else -1
            seeds = np.flatnonzero(lab == main)
            self.seed_kind = f"largest walkable area ({len(seeds)} spots)"
        self.seeds = seeds
        self.reach = bfs(self.f_indptr, self.f_nbr, seeds, N) & G.valid
        self.back = bfs(self.r_indptr, self.r_nbr, seeds, N) & G.valid
        # relaxed walk: which unreached nodes a crawl gap or a missing step would open
        rsrc, rdst = G.edges(relaxed=True)
        allsrc = np.concatenate([src, rsrc])
        alldst = np.concatenate([dst, rdst])
        strict_n = len(src)
        extra = np.r_[np.zeros(strict_n, bool), np.ones(len(rsrc), bool)]
        ip, nb, order = Graph.csr(allsrc, alldst, N)
        eid = order  # position in allsrc/alldst of each CSR slot
        gate = bfs_gateway(ip, nb, eid, extra, self.reach)
        self.gate, self.allsrc, self.alldst = gate, allsrc, alldst
        # the same backwards: which relaxed move would let a trapped player climb back out
        rip, rnb, rorder = Graph.csr(alldst, allsrc, N)
        self.rgate = bfs_gateway(rip, rnb, rorder, extra, self.back)

    def gate_reason(self, e):
        G = self.G
        s, d = self.allsrc[e], self.alldst[e]
        dH = (G.H[d] - G.H[s]) / 16
        pos = G.node_bp(d)
        if dH > 1.25:
            return pos, f"a {dH:.1f}-block step with no stair/ladder (from {G.node_bp(s)})"
        h = min(G.C[d], G.C[s])
        if dH < 0 and h >= 24:
            return pos, (f"a {-dH:.1f}-block drop from {G.node_bp(s)} through a closed hatch/opening too tight "
                         f"to fall through, with no ladder reaching back up")
        if h < 24:
            return pos, f"a gap only {h / 16:.2f} blocks high (crawl only) next to {G.node_bp(s)}"
        return pos, (f"a {dH:.1f}-block step up from {G.node_bp(s)} with only {G.C[s] / 16:.1f} blocks of headroom "
                     f"to jump")

    # -------------------------------------------------------------- rooms
    def rooms(self):
        W, G = self.W, self.G
        air = (~W.obst) & ((W.fl & OPEN) == 0)
        ob = W.obst
        covered = np.zeros_like(ob)
        covered[:, :-1, :] = np.flip(np.logical_or.accumulate(np.flip(ob[:, 1:, :], axis=1), axis=1), axis=1)
        mask = air & covered
        if self.mode in ("surface", "ocean"):
            # outside the piece's box is terrain, not rooms
            m = W.m
            mask[:m] = mask[-m:] = False
            mask[:, :, :m] = mask[:, :, -m:] = False
        lab, count = label_cells(mask)
        self.room_lab = lab
        NX, NY, NZ = W.shape
        # nodes per room (feet cell)
        ny = np.clip(G.Y, 0, NY - 1)
        node_room = lab[G.X, ny, G.Z]
        self.node_room = node_room
        rooms = []
        vols = np.bincount(lab[lab >= 0].ravel(), minlength=count) if count else np.zeros(0, int)
        floor_ok = G.valid & (node_room >= 0)
        floors = np.bincount(node_room[floor_ok], minlength=count) if count else np.zeros(0, int)
        reached = np.bincount(node_room[floor_ok & self.reach], minlength=count) if count else np.zeros(0, int)
        self.room_stats = (vols, floors, reached)
        return count

    def room_contents(self, rid):
        W = self.W
        cells = np.argwhere(self.room_lab == rid)
        found = collections.Counter()
        where = {}
        seen = set()
        for c in cells:
            for d in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (int(c[0] + d[0]), int(c[1] + d[1]), int(c[2] + d[2]))
                if q in seen:
                    continue
                seen.add(q)
                p = W.bp(*q)
                b = self.blocks.get(p)
                if b is None:
                    continue
                s = short(b[0])
                kind = None
                if s in LOOT:
                    kind = "loot"
                elif s in WORKSTATIONS or s.endswith("_bed") or s.endswith("_shelf"):
                    kind = "furniture"
                elif any(h in s for h in LIGHTS):
                    kind = "light"
                elif s.endswith("carpet") or s.startswith("potted_") or s.endswith("_banner") or "chair" in s \
                        or "table" in s:
                    kind = "decor"
                if kind:
                    found[(kind, s)] += 1
                    where.setdefault(kind, p)
        return found, where

    # -------------------------------------------------------------- checks
    def check_rooms(self):
        G, W = self.G, self.W
        count = self.rooms()
        vols, floors, reached = self.room_stats
        self.metrics_rooms = {"rooms": 0, "rooms_reached": 0, "room_volume": 0, "room_volume_reached": 0}
        reach_pos = None
        self.unreached_rooms = set()
        for rid in range(count):
            if vols[rid] < 8 or floors[rid] == 0:
                continue
            self.metrics_rooms["rooms"] += 1
            self.metrics_rooms["room_volume"] += int(vols[rid])
            if reached[rid]:
                self.metrics_rooms["rooms_reached"] += 1
                self.metrics_rooms["room_volume_reached"] += int(vols[rid])
                continue
            nodes = np.flatnonzero((self.node_room == rid) & G.valid)
            found, where = self.room_contents(rid)
            kinds = {k for k, _ in found}
            what = ", ".join(f"{n}x {s}" for (k, s), n in sorted(found.items(), key=lambda t: -t[1])[:6])
            pos = G.node_bp(nodes[len(nodes) // 2])
            cells = np.argwhere(self.room_lab == rid)
            lo_c, hi_c = W.bp(*cells.min(0)), W.bp(*cells.max(0))
            gates = self.gate[nodes]
            why = ""
            gpos = None
            ok = gates[gates >= 0]
            if len(ok):
                vals, cnts = np.unique(ok, return_counts=True)
                gpos, reason = self.gate_reason(vals[np.argmax(cnts)])
                why = f"; opened only by {reason} at {gpos}"
            else:
                if reach_pos is None:
                    rp = np.flatnonzero(self.reach)
                    reach_pos = np.stack([G.X[rp], G.Y[rp], G.Z[rp]], 1) if len(rp) else np.zeros((0, 3))
                if len(reach_pos):
                    c = np.array(W.idx(pos))
                    d = np.abs(reach_pos - c).sum(1)
                    j = int(np.argmin(d))
                    why = f"; sealed (nearest reachable spot {W.bp(*reach_pos[j])}, {int(d[j])} blocks away)"
            if "loot" in kinds or "furniture" in kinds:
                sev, w = "error", 50 + 10 * sum(n for (k, s), n in found.items() if k == "loot")
            elif kinds or floors[rid] >= 20:
                sev, w = "warn", 10 + int(floors[rid] // 10)
            else:
                sev, w = "info", 0
            label = "furnished room" if sev == "error" else ("room" if kinds else "enclosed void")
            self.unreached_rooms.add(rid)
            walls = self.wall_origin(cells)
            if walls:
                why += f"; walls by {walls}"
            self.add(sev, "unreachable-room", pos,
                     f"{label} not reachable: {int(vols[rid])} air cells, {int(floors[rid])} floor spots, box "
                     f"{lo_c}..{hi_c}" + (f"; holds {what}" if what else "") + why,
                     weight=w, origin_pos=self.origin_near(where.get("loot") or where.get("furniture")
                                                          or gpos or pos, 2))

    def wall_origin(self, cells):
        W = self.W
        cnt = collections.Counter()
        for c in cells[:: max(1, len(cells) // 300)]:
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (int(c[0] + d[0]), int(c[1] + d[1]), int(c[2] + d[2]))
                if W.inside(*q) and W.obst[q] and W.known[q]:
                    t = self.trace.get(W.bp(*q))
                    if t:
                        cnt[t.split(" < ")[-1]] += 1
        return cnt.most_common(1)[0][0] if cnt else ""

    def in_unreached_room(self, p):
        W = self.W
        i, y, k = W.idx(p)
        for d in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            q = (i + d[0], y + d[1], k + d[2])
            if W.inside(*q) and int(self.room_lab[q]) in self.unreached_rooms:
                return True
        return False

    def check_hatches(self):
        W = self.W
        for p, (name, props, _) in self.blocks.items():
            s = short(name)
            if not s.endswith("_trapdoor") or props.get("open") == "true":
                continue
            below = W.idx((p[0], p[1] - 1, p[2]))
            above = (p[0], p[1] + 1, p[2])
            ai = W.idx(above)
            if not (W.fl[below] & CLIMB):
                continue
            if W.lo[ai] >= 0:
                self.add("error", "hatch", p, f"{s} over a ladder is covered by {W.name_at(above)} at {above}: "
                         "the hatch cannot be used", weight=40, origin_pos=above)

    def reachable_from(self, p, anywhere=False):
        """Can a reachable player (anywhere: a player standing on any valid spot) touch/open block p (reach 4.5,
        line of sight)?"""
        G, W = self.G, self.W
        attr = "_acols" if anywhere else "_rcols"
        if not hasattr(self, attr):
            rcols = collections.defaultdict(list)
            for n in np.flatnonzero(G.valid if anywhere else self.reach).tolist():
                rcols[(int(G.X[n]), int(G.Z[n]))].append(n)
            setattr(self, attr, rcols)
        cols = getattr(self, attr)
        ci, cy, ck = W.idx(p)
        best = None
        cands = []
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                for n in cols.get((ci + dx, ck + dz), ()):
                    ex, ez = G.X[n] + 0.5, G.Z[n] + 0.5
                    ey = G.H[n] / 16 + (1.62 if G.C[n] >= 29 else 1.27)
                    qx = min(max(ex, ci), ci + 1)
                    qy = min(max(ey, cy), cy + 1)
                    qz = min(max(ez, ck), ck + 1)
                    d = ((ex - qx) ** 2 + (ey - qy) ** 2 + (ez - qz) ** 2) ** 0.5
                    if d <= 4.5:
                        cands.append((d, (ex, ey, ez), (qx, qy, qz), n))
                    if best is None or d < best[0]:
                        best = (d, n)
        cands.sort()
        for d, e, q, n in cands[:40]:
            if self.los(e, (ci, cy, ck)):
                return True, n
        return False, (best[1] if best else None)

    def los(self, e, cell):
        W = self.W
        tx, ty, tz = cell[0] + 0.5, cell[1] + 0.5, cell[2] + 0.5
        # aim at the closest face centre of the target
        best = None
        for fx, fy, fz in ((-0.5, 0, 0), (0.5, 0, 0), (0, -0.5, 0), (0, 0.5, 0), (0, 0, -0.5), (0, 0, 0.5)):
            q = (tx + fx * 0.98, ty + fy * 0.98, tz + fz * 0.98)
            d = (q[0] - e[0]) ** 2 + (q[1] - e[1]) ** 2 + (q[2] - e[2]) ** 2
            if best is None or d < best[0]:
                best = (d, q)
        for target in (best[1], (tx, ty, tz)):
            dx, dy, dz = target[0] - e[0], target[1] - e[1], target[2] - e[2]
            L = (dx * dx + dy * dy + dz * dz) ** 0.5
            steps = max(2, int(L / 0.2))
            blocked = False
            for s in range(1, steps):
                t = s / steps
                x, y, z = e[0] + dx * t, e[1] + dy * t, e[2] + dz * t
                c = (int(np.floor(x)), int(np.floor(y)), int(np.floor(z)))
                if c == tuple(cell):
                    break
                if not W.inside(*c):
                    continue
                lo = W.lo[c]
                if lo < 0:
                    continue
                fy = (y - c[1]) * 16
                if lo <= fy <= W.hi[c] and not (W.fl[c] & OPEN):
                    blocked = True
                    break
            if not blocked:
                return True
        return False

    def check_interactables(self):
        W, G = self.W, self.G
        loot = []
        for p, (name, props, data) in self.blocks.items():
            s = short(name)
            if s in LOOT or s in WORKSTATIONS or s.endswith("_bed") and props.get("part") == "head":
                loot.append((p, s, props))
        self.metrics_loot = {"loot": 0, "loot_reached": 0}
        groups = collections.defaultdict(list)
        cutoff = collections.defaultdict(list)
        for p, s, props in loot:
            is_loot = s in LOOT
            if is_loot:
                self.metrics_loot["loot"] += 1
            ok, n = self.reachable_from(p)
            if not ok and self.in_unreached_room(p):
                continue  # reported with its room
            if ok:
                if is_loot:
                    self.metrics_loot["loot_reached"] += 1
            elif s != "boss_seal":
                if self.reachable_from(p, anywhere=True)[0]:
                    cutoff[(s, is_loot)].append(p)
                else:
                    groups[(s, is_loot)].append(p)
            if s in ("chest", "trapped_chest"):
                above = (p[0], p[1] + 1, p[2])
                b = self.blocks.get(above)
                q = W.idx(above)
                if b is not None or (W.inside(*q) and W.terrain[q]):
                    an = short(b[0]) if b else "terrain"
                    full = b is None or (shape(b[0], b[1])[:2] == (0, 16) and not any(
                        h in an for h in ("glass", "leaves", "ice", "pane", "bars", "slab", "stairs", "chest",
                                          "glowstone", "sea_lantern", "beacon", "spawner", "lamp", "froglight",
                                          "shroomlight")) and B.is_solid(b[0]))
                    if full:
                        self.add("error", "chest-blocked", p, f"{s} cannot open: solid {an} sits on its lid",
                                 weight=40, origin_pos=p)
            if s == "spawner":
                if not self.spawner_space(p):
                    self.add("error", "spawner-dead", p, "spawner has no open 2-high floor within 4 blocks: "
                             "nothing can spawn", weight=45)
            if s == "boss_seal":
                r = self.data.get(p, {}).get("radius", 16)
                if not self.near_reach(p, r):
                    self.add("error", "boss-unreachable", p,
                             f"boss seal: no reachable spot within its wake radius {r}: the boss never wakes",
                             weight=150)
        # walled in: no standing spot anywhere can touch it
        for (s, is_loot), ps in groups.items():
            for cl in cluster_points(ps, gap=3):
                p = cl[0]
                if s == "spawner":
                    sev, w, what = "error", 45, "spawner walled in: no standing spot can reach it to break it"
                elif is_loot:
                    sev, w, what = "error", 60 + 5 * len(cl), f"{s} walled in: no standing spot within 4.5 blocks " \
                                                              f"with line of sight"
                else:
                    sev, w, what = "warn", 12 + len(cl), f"{s} walled in (cannot be used)"
                self.add(sev, "walled-in", p, what + (f" x{len(cl)}" if len(cl) > 1 else ""),
                         weight=w, positions=cl, origin_pos=p)
        # usable from somewhere, but that somewhere is cut off (the blocked-passage/one-way issues say why)
        loot_cut = [(s, p) for (s, il), ps in cutoff.items() if il for p in ps]
        other_cut = [(s, p) for (s, il), ps in cutoff.items() if not il for p in ps]
        for items, sev, label in ((loot_cut, "error", "loot"), (other_cut, "warn", "workstations/beds")):
            if not items:
                continue
            kinds = collections.Counter(s for s, _ in items)
            pts = [p for _, p in items]
            what = ", ".join(f"{n}x {k}" for k, n in kinds.most_common())
            self.add(sev, "cut-off-" + ("loot" if label == "loot" else "furniture"), pts[0],
                     f"{len(items)} {label} in areas no path reaches ({what}); see blocked-passage/one-way",
                     weight=(40 + 3 * len(items)) if label == "loot" else 10 + len(items), positions=pts,
                     origin_pos=pts[0])

    def near_reach(self, p, r):
        G, W = self.G, self.W
        rp = np.flatnonzero(self.reach)
        if not len(rp):
            return False
        c = np.array(W.idx(p))
        d2 = (G.X[rp] - c[0]) ** 2 + (G.Y[rp] - c[1]) ** 2 + (G.Z[rp] - c[2]) ** 2
        return bool((d2 <= r * r).any())

    def spawner_space(self, p):
        W = self.W
        ci, cy, ck = W.idx(p)
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                for dy in (-1, 0, 1):
                    q = (ci + dx, cy + dy, ck + dz)
                    q1 = (q[0], q[1] + 1, q[2])
                    qb = (q[0], q[1] - 1, q[2])
                    if not (W.inside(*q1) and W.inside(*qb)):
                        continue
                    if W.lo[q] < 0 and W.lo[q1] < 0 and (W.hi[qb] >= 8 or W.fl[q] & SWIM):
                        return True
        return False

    def check_doors(self):
        W, G = self.W, self.G
        for p, (name, props, _) in self.blocks.items():
            s = short(name)
            if not s.endswith("_door") or props.get("half") != "lower":
                continue
            f = props.get("facing")
            if not f:
                continue
            ci, cy, ck = W.idx(p)
            door_nodes = self.nodes_at(ci, ck, 16 * cy - 16, 16 * cy + 9)
            door_reached = any(self.reach[n] for n in door_nodes)
            for side in (f, B.OPPOSITE[f]):
                dx, _, dz = B.DIRS[side]
                q = (p[0] + dx, p[1], p[2] + dz)
                qi = W.idx(q)
                ns = self.nodes_at(qi[0], qi[2], 16 * cy - 16, 16 * cy + 9)
                if not ns:
                    q1 = (q[0], q[1] + 1, q[2])
                    qd = (q[0], q[1] - 1, q[2])
                    bl = [W.name_at(q), W.name_at(q1)]
                    if all(x == "air" for x in bl) or (W.lo[qi] < 0 and W.lo[W.idx(q1)] < 0):
                        what = f"no floor (below: {W.name_at(qd)})"
                        ws = 10
                    else:
                        what = f"blocked by {bl[0]} / {bl[1]}"
                        ws = 30
                    sev = "error" if door_reached or ws == 30 else "warn"
                    self.add(sev, "door", p, f"{s} opens onto nothing usable on its {side} side: {what}",
                             weight=ws + (10 if door_reached else 0), origin_pos=p)
                    continue
                if door_reached and not any(self.reach[n] for n in ns):
                    pass  # the room behind is reported by the room check
                size = self.pocket(ns[0], exclude_col=(ci, ck), limit=12)
                if size < 4:
                    self.add("error" if door_reached else "warn", "door", p,
                             f"{s} opens into a dead-end pocket of {size} spot(s) on its {side} side "
                             f"({W.name_at((q[0] + dx, q[1], q[2] + dz))} beyond)", weight=25, origin_pos=p)
            if s == "iron_door" and not self.has_switch(p):
                self.add("error", "door", p, "iron door with no button/lever/plate next to it: cannot be opened",
                         weight=35, origin_pos=p)

    def has_switch(self, p):
        for dx in range(-2, 3):
            for dy in range(-1, 3):
                for dz in range(-2, 3):
                    b = self.blocks.get((p[0] + dx, p[1] + dy, p[2] + dz))
                    if b and any(short(b[0]).endswith(h) or short(b[0]) == h for h in SWITCHES):
                        return True
        return False

    def nodes_at(self, i, k, h0, h1):
        G = self.G
        NX, NY, NZ = self.W.shape
        if not (0 <= i < NX and 0 <= k < NZ):
            return []
        c = i * NZ + k
        a = G.col_start[c]
        return [n for n in range(a, a + G.col_count[c]) if h0 <= G.H[n] <= h1 and G.valid[n]]

    def pocket(self, start, exclude_col, limit=12):
        G = self.G
        NZ = self.W.shape[2]
        ex = exclude_col[0] * NZ + exclude_col[1]
        seen = {start}
        stack = [start]
        while stack and len(seen) < limit:
            n = stack.pop()
            for ip, nb in ((self.f_indptr, self.f_nbr), (self.r_indptr, self.r_nbr)):
                for m in nb[ip[n]:ip[n + 1]].tolist():
                    if m not in seen and G.col[m] != ex and G.valid[m]:
                        seen.add(m)
                        stack.append(m)
        return len(seen)

    def check_headroom(self):
        G, W = self.G, self.W
        r = self.reach & ~G.swim
        # sneak-only spots on the walk
        sneak = np.flatnonzero(r & (G.C >= 24) & (G.C < 29))
        pts = [G.node_bp(n) for n in sneak.tolist()]
        for cl in cluster_points(pts, gap=1):
            if len(cl) < 3:
                continue  # a lone low spot (under a lamp, a shelf) is walked around
            p = cl[0]
            n = sneak[pts.index(p)]
            ceil = (p[0], int((G.H[n] + G.C[n]) // 16 + W.o[1]), p[2])
            self.add("warn", "headroom", p, f"only {G.C[n] / 16:.2f} blocks of headroom: players must sneak "
                     f"({len(cl)} spot(s); ceiling {W.name_at(ceil)} at {ceil})", weight=8 + min(len(cl), 10),
                     positions=cl, origin_pos=self.origin_near(ceil))
        # 2-block ceilings inside tall halls
        if not hasattr(self, "node_room"):
            return
        vols, floors, reached = self.room_stats
        rn = np.flatnonzero(r & (self.node_room >= 0))
        if not len(rn):
            return
        rooms = self.node_room[rn]
        for rid in np.unique(rooms).tolist():
            ns = rn[rooms == rid]
            if len(ns) < 80:
                continue
            med = np.median(np.minimum(G.C[ns], 16 * 12))
            if med < 80:
                continue
            low = ns[(G.C[ns] >= 29) & (G.C[ns] < 40)]
            if not len(low):
                continue
            pts = [G.node_bp(n) for n in low.tolist()]
            for cl in cluster_points(pts, gap=1):
                if len(cl) < 3:
                    continue
                p = cl[0]
                n = low[pts.index(p)]
                ceil = (p[0], int((G.H[n] + G.C[n]) // 16 + W.o[1]), p[2])
                self.add("warn", "low-ceiling", p,
                         f"hall ceiling ~{med / 16:.0f} blocks but only {G.C[n] / 16:.1f} here ({len(cl)} spot(s)): "
                         f"{W.name_at(ceil)} at {ceil} hangs into the walkway", weight=4 + min(len(cl), 8),
                         positions=cl, origin_pos=self.origin_near(ceil))

    def check_gaps(self):
        """Crawl gaps / missing steps that keep the player out of an area (not already a room)."""
        G = self.G
        unreached = G.valid & ~self.reach & (self.gate >= 0)
        if not unreached.any():
            return
        by_gate = collections.Counter(self.gate[unreached].tolist())
        rooms_with_error = {tuple(i["pos"]) for i in self.issues if i["category"] == "unreachable-room"}
        cov = unreached & (G.C < BIG // 2)
        by_gate_cov = collections.Counter(self.gate[cov].tolist())
        for e, n in by_gate.most_common():
            if n < 6:
                continue
            nc = by_gate_cov.get(e, 0)
            gpos, reason = self.gate_reason(e)
            if nc >= 40:
                sev = "error"
            elif nc >= 12:
                sev = "warn"
            else:
                sev = "info"
            where = f"{n} standing spots ({nc} under a roof)" if nc < n else f"{n} standing spots (all under a roof)"
            self.add(sev, "blocked-passage", gpos, f"{where} are cut off by {reason}",
                     weight=20 + min(nc // 8, 110), origin_pos=self.origin_near(gpos, 2))

    def check_oneway(self):
        G = self.G
        trap = self.reach & ~self.back & ~G.swim
        idx = np.flatnonzero(trap)
        if not len(idx):
            return
        lab = components(self.src, self.dst, G.N, mask=trap)
        vals, counts = np.unique(lab[idx], return_counts=True)
        for v, c in zip(vals.tolist(), counts.tolist()):
            if c < 6:
                continue
            ns = idx[lab[idx] == v]
            # covered spots only (open roofs you drop onto are not traps of the design)
            covered = ns[G.C[ns] < BIG // 2]
            if len(covered) < 6:
                continue
            p = G.node_bp(ns[0])
            g = self.rgate[ns]
            g = g[g >= 0]
            top = ns[np.argmax(G.H[ns])]
            why, gpos = f"no stair/ladder back up (climbing stops at {G.node_bp(top)})", None
            if len(g):
                vals, cnts = np.unique(g, return_counts=True)
                gpos, reason = self.gate_reason(vals[np.argmax(cnts)])
                why = f"the way back is blocked by {reason} at {gpos}"
            sev = "error" if len(covered) >= 40 else "warn"
            self.add(sev, "one-way", gpos or p, f"{c} spots ({len(covered)} under a roof) can be dropped into but "
                     f"never left: {why}", weight=20 + min(len(covered) // 8, 120),
                     origin_pos=self.origin_near(gpos or p, 2))

    def check_stairs(self):
        G, W = self.G, self.W
        blocks = self.blocks
        stairs = {p: b for p, b in blocks.items() if short(b[0]).endswith("_stairs") and "facing" in b[1]}
        reach_cols = set()
        rn = np.flatnonzero(self.reach)
        for n in rn.tolist():
            reach_cols.add((int(G.X[n]), int(G.Y[n]), int(G.Z[n])))
        self.reach_cells = reach_cols

        def on_walk(p):
            i, y, k = W.idx(p)
            return any(self.reach[n] for n in self.nodes_at(i, k, 16 * y + 8, 16 * y + 16))

        # staircase runs: same facing, each step one up and one forward
        done = set()
        runs = []
        for p, (name, props, _) in stairs.items():
            if p in done:
                continue
            f = props["facing"]
            dx, _, dz = B.DIRS[f]
            prev = (p[0] - dx, p[1] - 1, p[2] - dz)
            if prev in stairs and stairs[prev][1]["facing"] == f and stairs[prev][1].get("half") == props.get("half"):
                continue
            run = [p]
            q = p
            while True:
                nq = (q[0] + dx, q[1] + 1, q[2] + dz)
                b = stairs.get(nq)
                if not b or b[1]["facing"] != f or b[1].get("half") != props.get("half"):
                    break
                run.append(nq)
                q = nq
            for r in run:
                done.add(r)
            if len(run) >= 2:
                runs.append((run, f, props.get("half", "bottom")))
        head, top_bad, bottom_bad, upside = [], [], [], []
        def covered(r):
            i, y, k = W.idx(r)
            return bool(W.obst[i, y + 3:y + 15, k].any())

        def flat_floor(q, y):
            """A plain floor spot (on a full block, not a stair/slab/leaves) in column q at feet level y."""
            qi = W.idx((q[0], y, q[2]))
            if not any(G.valid[n] for n in self.nodes_at(qi[0], qi[2], 16 * qi[1] - 1, 16 * qi[1] + 2)):
                return False
            b = blocks.get((q[0], y - 1, q[2]))
            if b is None:
                return bool(W.terrain[qi[0], qi[1] - 1, qi[2]])
            sb = short(b[0])
            return not sb.endswith(("_stairs", "_slab", "_leaves")) and W.lo[qi[0], qi[1] - 1, qi[2]] == 0

        def starts_on_floor(bot, f):
            for d in B.HORIZONTAL:
                if d == f:
                    continue
                dx, _, dz = B.DIRS[d]
                if flat_floor((bot[0] + dx, 0, bot[2] + dz), bot[1]):
                    return True
            return False

        for run, f, half in runs:
            used = sum(1 for r in run if on_walk(r))
            if used == 0:
                continue
            if sum(1 for r in run if covered(r)) * 2 < len(run):
                continue  # open-air slopes: roofs, terraces
            dx, _, dz = B.DIRS[f]
            top = run[-1]
            land_ok = flat_floor((top[0] + dx, 0, top[2] + dz), top[1] + 1)
            if not starts_on_floor(run[0], f) and not land_ok:
                continue  # neither end is a floor: a roof slope or a decoration, not a staircase
            if half == "top":
                if used >= 2:
                    upside.append((run[0], len(run)))
                continue
            for r in run:
                if not on_walk(r):
                    continue
                c1 = W.idx((r[0], r[1] + 1, r[2]))
                c2 = W.idx((r[0], r[1] + 2, r[2]))
                if W.lo[c1] >= 0 or (W.lo[c2] >= 0 and W.lo[c2] < 13):
                    # standing on the back of the step needs y+1..y+2.8 open
                    blk = (r[0], r[1] + 1, r[2]) if W.lo[c1] >= 0 else (r[0], r[1] + 2, r[2])
                    head.append((r, blk))
            top = run[-1]
            land = (top[0] + dx, top[1] + 1, top[2] + dz)
            li = W.idx(land)
            ns = self.nodes_at(li[0], li[2], 16 * li[1] - 4, 16 * li[1] + 9)
            if not ns and on_walk(top) and len(run) >= 3:
                top_bad.append((top, land))
        for cl in cluster_points([h[0] for h in head], gap=2):
            blk = dict(head)[cl[0]]
            self.add("error", "stairs", cl[0], f"head bump on a used staircase: {W.name_at(blk)} at {blk} leaves "
                     f"less than 1.8 blocks above the step ({len(cl)} step(s))", weight=30 + len(cl),
                     positions=cl, origin_pos=blk)
        for top, land in top_bad:
            l1 = (land[0], land[1] + 1, land[2])
            l0 = (land[0], land[1] - 1, land[2])
            li = W.idx(land)
            up = [n for n in self.nodes_at(li[0], li[2], 16 * li[1] + 10, 16 * li[1] + 20) if self.reach[n]]
            if up:
                self.add("warn", "stairs", top, f"staircase is one step short: the top step at {top} is a full "
                         f"block below the floor at {land} (players must jump)", weight=14, origin_pos=top)
                continue
            if W.lo[li] < 0 and W.lo[W.idx(l0)] < 0:
                why = f"no floor at the landing {land} ({W.name_at(l0)} under it): a step is missing"
            elif W.lo[li] >= 0:
                why = f"runs into {W.name_at(land)} at {land}"
            else:
                why = f"lands under {W.name_at(l1)} at {l1} (no headroom)"
            self.add("error", "stairs", top, f"staircase top step leads nowhere: {why}", weight=35,
                     origin_pos=top)
        for bot, foot in bottom_bad:
            self.add("warn", "stairs", bot, f"staircase bottom starts against {W.name_at(foot)} at {foot}",
                     weight=15, origin_pos=bot)
        for p, n in upside:
            self.add("warn", "stairs", p, f"{n} upside-down stairs used as steps: every step needs a jump",
                     weight=12, origin_pos=p)
        # backwards steps: diagonal runs whose majority faces the climb direction but some face away
        for p, (name, props, _) in stairs.items():
            if props.get("half", "bottom") != "bottom" or not on_walk(p):
                continue
            for d in B.HORIZONTAL:
                if d == props["facing"]:
                    continue
                dx, _, dz = B.DIRS[d]
                a = stairs.get((p[0] - dx, p[1] - 1, p[2] - dz))
                c = stairs.get((p[0] + dx, p[1] + 1, p[2] + dz))
                if a and c and a[1].get("facing") == d and c[1].get("facing") == d and \
                        a[1].get("half", "bottom") == "bottom" and c[1].get("half", "bottom") == "bottom":
                    self.add("error", "stairs", p, f"step faces {props['facing']} in a staircase climbing {d}",
                             weight=30, origin_pos=p)
        self.check_ladders()

    def check_ladders(self):
        W, G = self.W, self.G
        lad = {p for p, b in self.blocks.items() if short(b[0]) == "ladder"}
        tops = [p for p in lad if (p[0], p[1] + 1, p[2]) not in lad]
        for t in tops:
            # length of the column
            n = 1
            while (t[0], t[1] - n, t[2]) in lad:
                n += 1
            if n < 3:
                continue
            ti = W.idx(t)
            # the climber's node at the top ladder cell
            ns = self.nodes_at(ti[0], ti[2], 16 * ti[1], 16 * ti[1])
            if not ns:
                continue
            node = ns[0]
            if not self.reach[node]:
                continue
            exits = self.f_nbr[self.f_indptr[node]:self.f_indptr[node + 1]]
            up_ok = any(G.H[m] > G.H[node] and G.col[m] != G.col[node] for m in exits.tolist())
            if up_ok:
                continue
            above = (t[0], t[1] + 1, t[2])
            if W.lo[W.idx(above)] >= 0:
                self.add("error", "ladder", t, f"{n}-rung ladder ends under {W.name_at(above)}: no hatch",
                         weight=30, origin_pos=t)
            else:
                self.add("error", "ladder", t, f"{n}-rung ladder top has no landing to step onto",
                         weight=25, origin_pos=t)

    def check_support(self):
        for kind, p, msg in support.check(self.blocks, self.ctx):
            sev = "error" if kind in ("door",) else "warn"
            self.add(sev, f"support:{kind}", p, msg, weight=20 if sev == "error" else 6, origin_pos=p)
        for p, (name, props, _) in self.blocks.items():
            s = short(name)
            if s.endswith("_bed") and "facing" in props:
                f = props["facing"]
                dx, _, dz = B.DIRS[f]
                other = (p[0] + dx, p[1], p[2] + dz) if props.get("part") == "foot" else (p[0] - dx, p[1], p[2] - dz)
                b = self.blocks.get(other)
                want = "head" if props.get("part") == "foot" else "foot"
                if not b or b[0] != name or b[1].get("part") != want or b[1].get("facing") != f:
                    self.add("error", "support:bed", p, f"{s} {props.get('part')} without its {want}", weight=20,
                             origin_pos=p)
            if s.endswith("_door") and props.get("half") == "lower" and "facing" in props:
                f = props["facing"]
                for side in (f, B.OPPOSITE[f]):
                    dx, _, dz = B.DIRS[side]
                    for dy in (0, 1):
                        q = (p[0] + dx, p[1] + dy, p[2] + dz)
                        b = self.blocks.get(q)
                        if b and ("_leaves" in b[0] or short(b[0]) in ("cobweb",)):
                            self.add("error", "door", p, f"doorway blocked by {short(b[0])} at {q}", weight=30,
                                     origin_pos=q)

    def check_floating(self):
        """Masses (> 12 blocks, smaller ones are wf/support.py's) that touch neither terrain nor the main body."""
        if self.mode == "sky":
            return
        W = self.W
        mask = W.known & (W.obst | ((W.fl & (CLIMB | OPEN | SURF3 | SURF16)) != 0))
        for p, b in self.blocks.items():  # rails, carpets' neighbours, plates... everything placed but air/fluids
            if b[0] not in AIR and short(b[0]) not in ("water", "lava", "bubble_column"):
                mask[W.idx(p)] = True
        anchored = W.terrain.copy()
        anchored = self._dilate(anchored) & mask
        prev = -1
        it = 0
        while True:
            cnt = int(anchored.sum())
            if cnt == prev or it > 400:
                break
            prev = cnt
            anchored = self._dilate(anchored) & mask
            anchored = self._dilate(anchored) & mask
            it += 2
        loose = mask & ~anchored
        if not loose.any():
            return
        lab, count = label_cells(loose)
        sizes = np.bincount(lab[lab >= 0].ravel(), minlength=count)
        for lid in range(count):
            if sizes[lid] <= 12:
                continue
            cells = np.argwhere(lab == lid)
            p = W.bp(*cells[0])
            names = collections.Counter(short(self.blocks[W.bp(*c)][0]) for c in cells[:400]
                                        if W.bp(*c) in self.blocks)
            what = ", ".join(n for n, _ in names.most_common(4))
            self.add("warn" if sizes[lid] < 200 else "info", "floating", p,
                     f"{int(sizes[lid])} blocks hang in the air touching nothing ({what})", weight=5,
                     origin_pos=p)

    @staticmethod
    def _dilate(a):
        out = a.copy()
        out[1:] |= a[:-1]
        out[:-1] |= a[1:]
        b = out.copy()
        b[:, 1:] |= out[:, :-1]
        b[:, :-1] |= out[:, 1:]
        c = b.copy()
        c[:, :, 1:] |= b[:, :, :-1]
        c[:, :, :-1] |= b[:, :, 1:]
        return c

    # -------------------------------------------------------------- run
    def run(self):
        self.walk()
        G, W = self.G, self.W
        if G.N == 0:
            return self.summary()
        self.check_rooms()
        self.check_interactables()
        self.check_doors()
        self.check_hatches()
        self.check_gaps()
        self.check_oneway()
        self.check_headroom()
        self.check_stairs()
        self.check_support()
        self.check_floating()
        return self.summary()

    def summary(self):
        W, G = self.W, self.G
        (mx, my, mz), (Mx, My, Mz) = W.bmin, W.bmax
        cols = W.known.any(axis=1)
        covered_nodes = G.valid & (G.C < BIG // 2) if G.N else np.zeros(0, bool)
        mr = getattr(self, "metrics_rooms", {"rooms": 0, "rooms_reached": 0, "room_volume": 0,
                                               "room_volume_reached": 0})
        ml = getattr(self, "metrics_loot", {"loot": 0, "loot_reached": 0})
        reach = getattr(self, "reach", np.zeros(G.N, bool))
        self.issues.sort(key=lambda i: (SEV_RANK[i["severity"]], -i["weight"]))
        return {
            "structure": self.sid, "piece": self.piece, "mode": self.mode,
            "entrance": getattr(self, "seed_kind", ""),
            "template_origin": [mx, my, mz],
            "size": [Mx - mx + 1, My - my + 1, Mz - mz + 1],
            "footprint_columns": int(cols.sum()),
            "height": My - my + 1,
            "blocks": len(self.blocks),
            "walk_spots": int(G.valid.sum()) if G.N else 0,
            "walk_spots_reached": int(reach.sum()),
            "covered_spots": int(covered_nodes.sum()),
            "covered_spots_reached": int((covered_nodes & reach).sum()),
            **mr, **ml,
            "seconds": round(time.time() - self.t0, 2),
            "issues": self.issues,
        }


# ------------------------------------------------------------------ building the pieces
def mode_for(sdef, ctx):
    if ctx.unset_solid:
        return "underground"
    if ctx.ground is not None and not ctx.sky:
        return "ocean" if sdef is not None and sdef.height is None and sdef.heightmap == "OCEAN_FLOOR_WG" \
            else "surface"
    return "sky"


def built_pieces(only, cache):
    """Yield (sid, piece, blocks, ctx, water_unset, trace, mode, data) like gen_structures builds them."""
    for sdef in defs.STRUCTURES:
        if only and sdef.id not in only:
            continue
        pools = {"start": sdef.pieces}
        pools.update(sdef.extra_pools)
        for pool_name, pieces in pools.items():
            for piece in pieces:
                start = pool_name == "start"
                path = os.path.join(cache, f"{sdef.id}__{piece.name}.pkl") if cache else None
                if path and os.path.exists(path):
                    with open(path, "rb") as f:
                        yield pickle.load(f)
                    continue
                bp = G.build_piece(sdef, piece, start=start)
                ctx = support.context_for(sdef) if start else support.Context(unset_solid=True)
                bp.resolve_shapes()
                support.repair(bp, ctx)
                mode = mode_for(sdef, ctx)
                rec = _record(sdef.id, piece.name, bp, ctx, mode == "ocean", mode)
                if path:
                    _save(path, rec)
                yield rec
    if not only or "villages" in only:
        from wf import village
        for tid, bp, kind in village.build_all():
            path = tid.split(":", 1)[1]
            cp = os.path.join(cache, "village__" + path.replace("/", "__") + ".pkl") if cache else None
            if cp and os.path.exists(cp):
                with open(cp, "rb") as f:
                    yield pickle.load(f)
                continue
            ctx = support.Context(ground=0)
            bp.resolve_shapes()
            support.repair(bp, ctx)
            rec = _record("villages", path, bp, ctx, False, "surface")
            if cp:
                _save(cp, rec)
            yield rec


def _record(sid, piece, bp, ctx, water_unset, mode):
    trace = {p: _fmt_trace(t) for p, t in bp.__dict__.get("_trace", {}).items()}
    data = {}
    for p, b in bp.blocks.items():
        if b[0] == "brasshaven:boss_seal" and b[2]:
            try:
                data[p] = {"radius": int(b[2]["radius"].value if hasattr(b[2]["radius"], "value")
                                         else b[2]["radius"])}
            except Exception:
                data[p] = {"radius": 16}
    blocks = {p: (b[0], dict(b[1]), None) for p, b in bp.blocks.items()}
    return {"sid": sid, "piece": piece, "blocks": blocks, "ctx": vars(ctx).copy(), "water_unset": water_unset,
            "trace": trace, "mode": mode, "data": data}


def _save(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(rec, f, protocol=pickle.HIGHEST_PROTOCOL)


def audit_record(rec):
    ctx = support.Context(**rec["ctx"])
    return Audit(rec["sid"], rec["piece"], rec["blocks"], ctx, rec["water_unset"], rec["trace"], rec["mode"],
                 rec["data"])


# ------------------------------------------------------------------ output
def pct(a, b):
    return f"{100.0 * a / b:5.1f}%" if b else "   - "


def summary_line(r):
    errs = sum(1 for i in r["issues"] if i["severity"] == "error")
    warns = sum(1 for i in r["issues"] if i["severity"] == "warn")
    name = f"{r['structure']}/{r['piece']}"
    sx, sy, sz = r["size"]
    return (f"{name:44s} {r['mode'][:4]:4s} {sx:3d}x{sz:3d} h{sy:3d}  rooms {r['rooms_reached']:3d}/{r['rooms']:<3d} "
            f"vol {pct(r['room_volume_reached'], r['room_volume'])}  covered-walk "
            f"{pct(r['covered_spots_reached'], r['covered_spots'])}  loot {r['loot_reached']:3d}/{r['loot']:<3d} "
            f"E{errs:3d} W{warns:3d}")


def write_reports(results, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "structures.json"), "w", encoding="utf-8") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "pieces": results}, f, indent=1)
    allissues = []
    for r in results:
        for i in r["issues"]:
            allissues.append((SEV_RANK[i["severity"]], -i["weight"], f"{r['structure']}/{r['piece']}", i))
    allissues.sort(key=lambda t: (t[0], t[1], t[2]))
    with open(os.path.join(out_dir, "structures.txt"), "w", encoding="utf-8") as f:
        f.write("Brasshaven structure audit (tools/audit_structures.py)\n")
        f.write("Coordinates are blueprint coordinates; template origin = blueprint minimum corner (per piece).\n\n")
        f.write("== Summary ==\n")
        f.write("piece                                        mode  size    height rooms reached/total, room volume "
                "reached, covered walk spots reached, loot reachable, errors, warnings\n")
        for r in results:
            f.write(summary_line(r) + "\n")
        f.write("\n== Most serious issues (all pieces) ==\n")
        for _, _, name, i in allissues[:80]:
            f.write(_fmt_issue(name, i))
        f.write("\n== Per piece ==\n")
        for r in results:
            f.write(f"\n--- {r['structure']}/{r['piece']}  ({r['mode']}, entrance: {r['entrance']}, template origin "
                    f"{tuple(r['template_origin'])}, {r['blocks']} blocks, {r['seconds']}s)\n")
            f.write(f"    walk spots reached {r['walk_spots_reached']}/{r['walk_spots']}, covered "
                    f"{r['covered_spots_reached']}/{r['covered_spots']}, rooms {r['rooms_reached']}/{r['rooms']}, "
                    f"room volume {r['room_volume_reached']}/{r['room_volume']}, loot {r['loot_reached']}/"
                    f"{r['loot']}\n")
            for i in r["issues"]:
                f.write(_fmt_issue("", i))


def _fmt_issue(name, i):
    pos = tuple(i["pos"])
    more = ""
    if i["count"] > 1 and i["positions"]:
        more = " also " + " ".join(str(tuple(p)) for p in i["positions"][1:5])
    who = f" [{i['origin']}]" if i["origin"] else ""
    head = f"{name} " if name else "    "
    return f"{head}{i['severity'].upper():5s} {i['category']:18s} {pos} {i['msg']}{more}{who}\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", help="structure ids (and/or 'villages')")
    ap.add_argument("--cache", help="directory to keep built blueprints between runs (delete it to rebuild)")
    ap.add_argument("--no-villages", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "audit"))
    args = ap.parse_args()
    only = set(args.only) if args.only else None
    if args.no_villages and not only:
        only = {s.id for s in defs.STRUCTURES}
    results = []
    for rec in built_pieces(only, args.cache):
        a = audit_record(rec)
        r = a.run()
        results.append(r)
        print(summary_line(r), flush=True)
    write_reports(results, args.out)
    e = sum(1 for r in results for i in r["issues"] if i["severity"] == "error")
    w = sum(1 for r in results for i in r["issues"] if i["severity"] == "warn")
    print(f"{len(results)} pieces audited: {e} errors, {w} warnings -> {os.path.relpath(args.out, ROOT)}/"
          f"structures.txt / structures.json")


if __name__ == "__main__":
    main()
