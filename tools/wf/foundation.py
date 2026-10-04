"""Hidden foundations for surface structures.

A heightmap-projected structure is placed at the terrain height sampled at its centre only, and the
vanilla "beard" that would raise or carve terrain around it only acts within ~12 blocks of the
template's lowest layer. On a slope (or for templates with a deep cellar) the downhill side therefore
floats. This pass extends every column that touches the ground layer downwards with a plausible
foundation (soil under grass, the floor's own stone under buildings, posts under posts), only through
structure-void cells, so it never changes anything the builder placed and is invisible on flat land.
"""
from .blueprint import parse_block

AIR = {"minecraft:air", "minecraft:cave_air"}
SOIL_TOP = {"grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "mycelium", "dirt_path", "farmland",
            "moss_block", "mud", "packed_mud", "snow_block", "pale_moss_block"}
SAND = {"sand": "sandstone", "red_sand": "red_sandstone", "suspicious_sand": "sandstone", "gravel": "stone",
        "suspicious_gravel": "stone"}
POSTS = ("_log", "_wood", "_fence", "_wall", "iron_chain", "iron_bars")
LIQUID = {"minecraft:water", "minecraft:lava"}


def _short(name):
    return name.split(":", 1)[1]


def _column_material(name, props):
    """What to put under a ground-layer block: (material for the first few blocks, material below)."""
    s = _short(name)
    if s in SOIL_TOP:
        return ("minecraft:dirt", {}), ("minecraft:stone", {})
    if s in SAND:
        return ("minecraft:" + SAND[s], {}), ("minecraft:stone", {})
    if name in LIQUID:
        return ("minecraft:clay", {}), ("minecraft:stone", {})
    if any(s.endswith(p) for p in POSTS):
        keep = {k: v for k, v in props.items() if k == "axis"}
        return (name, keep), (name, keep)
    if s.endswith(("_stairs", "_slab", "_trapdoor", "_carpet", "_pressure_plate", "_button")) or "door" in s:
        return None
    if s.endswith("_planks"):
        return ("minecraft:cobblestone", {}), ("minecraft:stone", {})
    return (name, {k: v for k, v in props.items() if k == "axis"}), ("minecraft:stone", {})


SKIRT_THEMES = {
    # ground theme -> (top, soil, rock)
    "sand": ("minecraft:sand", "minecraft:sand", "minecraft:sandstone"),
    "snow": ("minecraft:snow_block", "minecraft:dirt", "minecraft:stone"),
    "grass": ("minecraft:grass_block", "minecraft:dirt", "minecraft:stone"),
    "end": ("minecraft:end_stone", "minecraft:end_stone", "minecraft:end_stone"),
}


def _theme(bp, ground):
    counts = {}
    for (x, y, z), (name, _, _) in bp.blocks.items():
        if y != ground or name in AIR:
            continue
        s = _short(name)
        kind = "sand" if s in SAND or s.endswith("sandstone") else "snow" if s in ("snow_block", "powder_snow") \
            else "grass" if s in SOIL_TOP else None
        if kind:
            counts[kind] = counts.get(kind, 0) + 1
    return max(counts, key=counts.get) if counts else "grass"


def add_skirt(bp, ground=0, spread=4, depth=10, seed=0, theme=None):
    """Stair-step skirt: a bank of earth around the ground-layer footprint, one block lower per block outwards
    (top at ``ground - d`` at distance d, so it is invisible under flat ground and only shows where the terrain
    falls away from the structure), thick near the walls and thinning outwards. It meets the hidden foundations
    under the footprint, so a structure on a slope stands on a natural mound instead of a sheer wall. Void cells
    only, like the foundations. Returns the number of blocks added."""
    import math
    import random
    rng = random.Random(seed)
    fp = {(x, z) for (x, y, z), (name, _, _) in bp.blocks.items() if y == ground and name not in AIR}
    if not fp:
        return 0
    top, soil, rock = SKIRT_THEMES[theme or _theme(bp, ground)]
    ring = {}
    for (x, z) in fp:
        for dx in range(-spread, spread + 1):
            for dz in range(-spread, spread + 1):
                p = (x + dx, z + dz)
                if p in fp:
                    continue
                d = math.hypot(dx, dz)
                if d <= spread + 0.5 and d < ring.get(p, 99):
                    ring[p] = d
    added = 0
    for (x, z), d in sorted(ring.items()):
        step = max(1, int(round(d + rng.uniform(-0.35, 0.35))))
        if step > spread:
            continue
        y_top = ground - step
        bottom = ground - max(step + 1, depth - 2 * step)
        for y in range(y_top, bottom - 1, -1):
            if (x, y, z) in bp.blocks:
                break  # something built (a cellar wall): it carries the bank from here
            k = y_top - y
            mat = rock if y == bottom and k > 0 else top if k == 0 else soil if k < 3 else rock  # rests on rock
            bp.blocks[(x, y, z)] = (mat, _top_props(mat) if k == 0 else {}, None)
            added += 1
    return added


def _top_props(name):
    return {"snowy": "false"} if name == "minecraft:grass_block" else {}


def add_foundations(bp, ground=0, depth=12, soil_depth=3):
    """Extend columns that stand on the ground layer down to ``ground - depth`` (void cells only).
    Returns the number of blocks added."""
    cols = {}
    for (x, y, z), (name, props, _) in bp.blocks.items():
        if y != ground or name in AIR:
            continue
        cols[(x, z)] = (name, props)
    added = 0
    for (x, z), (name, props) in cols.items():
        mats = _column_material(name, props)
        if not mats:
            # a stair/slab on the ground layer: support it with the block below if there is one, else stone
            mats = (("minecraft:stone", {}), ("minecraft:stone", {}))
        top, below = mats
        for k in range(1, depth + 1):
            p = (x, ground - k, z)
            if p in bp.blocks:
                break  # reached something built (cellar, crypt): it carries the column from here
            m = top if k <= soil_depth else below
            bp.blocks[p] = (m[0], dict(m[1]), None)
            added += 1
    return added
