"""Overworld structures (group C): watchtower, bandit fort, rune henge, polar observatory,
galleon wreck, sunken temple and the dwarven mining settlement.

Every builder is split by area (comments) and uses the arch kit + the small helpers below.
"""
import math
import random

from .. import arch
from .. import interior as I
from .. import residents
from ..arch import Palette, slab, stair
from ..blueprint import OPPOSITE, Blueprint, family, with_props
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD
from . import lair_rune_colossus

FLOWERS = ["short_grass", "short_grass", "short_grass", "fern", "poppy", "dandelion", "oxeye_daisy",
           "azure_bluet", "cornflower", "bush", "leaf_litter[facing=north,segment_amount=3]"]


# ============================================================ shared helpers
def _toward(dx, dz):
    """Horizontal direction of the vector (dx, dz) (dominant axis)."""
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def log(spec, axis="y"):
    return with_props(spec, axis=axis)


def ring_cells(cx, cz, r0, r1):
    """Cells whose distance to the centre is in (r0, r1]."""
    out = []
    R = int(r1) + 2
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if r0 < d <= r1:
                out.append((x, z))
    return out


def ring(bp, cx, y, cz, r0, r1, spec):
    pal = arch.as_pal(spec)
    for x, z in ring_cells(cx, cz, r0, r1):
        bp.set(x, y, z, pal.pick(x, y, z))


def ring_stairs(bp, cx, y, cz, r, stairs_block, half="top", inward=True):
    """1-thick ring of stairs facing the centre (corbels with half='top', slopes with 'bottom')."""
    for x, z in ring_cells(cx, cz, r - 0.5, r + 0.5):
        f = _toward(cx - x, cz - z)
        bp.set(x, y, z, stair(stairs_block, f if inward else OPPOSITE[f], half))


def radial_cut(bp, cx, cz, ang, y0, y1, r0, r1, width=1, spec="air"):
    """Opening through a round wall along angle `ang` (degrees)."""
    a = math.radians(ang)
    ux, uz = math.cos(a), math.sin(a)
    px, pz = -uz, ux
    offs = [0] if width == 1 else [-0.5, 0.5] if width == 2 else [-1, 0, 1]
    t = r0
    while t <= r1:
        for w in offs:
            x, z = round(cx + ux * t + px * w), round(cz + uz * t + pz * w)
            for y in range(y0, y1 + 1):
                bp.set(x, y, z, spec)
        t += 0.25


def at_angle(cx, cz, ang, r):
    a = math.radians(ang)
    return round(cx + math.cos(a) * r), round(cz + math.sin(a) * r)


def ground_patch(bp, cx, cz, rx, rz, seed, top=None, y=0, noise=0.18):
    """Irregular ground layer (grass with patches) that the structure sits on."""
    rng = random.Random(seed)
    top = top or Palette({"grass_block[snowy=false]": 8, "coarse_dirt": 1, "moss_block": 1}, seed=seed, scale=4)
    top = arch.as_pal(top)
    for x in range(cx - rx - 2, cx + rx + 3):
        for z in range(cz - rz - 2, cz + rz + 3):
            a = math.atan2(z - cz, x - cx)
            wob = 1 + noise * math.sin(a * 3 + seed) + noise * 0.6 * math.cos(a * 5 + seed * 2)
            if ((x - cx) / (rx * wob)) ** 2 + ((z - cz) / (rz * wob)) ** 2 <= 1 + rng.uniform(-0.04, 0.04):
                bp.set(x, y, z, top.pick(x, y, z), keep=True)


def skirt(bp, y=0, depth=6, spread=3, seed=0, top="grass_block[snowy=false]", soil="dirt", rock="stone",
          rubble=("cobblestone", "mossy_cobblestone", "andesite")):
    arch.terrain_skirt(bp, arch.footprint_of(bp, y), y, depth=depth, spread=spread, seed=seed, top=top,
                       soil=soil, rock=rock, rubble=rubble)


def path_line(bp, pts, y, pal, width=2, seed=0, chance=0.9):
    rng = random.Random(seed)
    pal = arch.as_pal(pal)
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(z1 - z0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            z = round(z0 + (z1 - z0) * i / n)
            for dx in range(-(width // 2), width - width // 2):
                for dz in range(-(width // 2), width - width // 2):
                    if rng.random() < chance:
                        bp.set(x + dx, y, z + dz, pal.pick(x + dx, y, z + dz))


def scatter_plants(bp, x0, z0, x1, z1, y, density, seed, plants, on=("minecraft:grass_block", "minecraft:moss_block",
                                                                     "minecraft:coarse_dirt", "minecraft:podzol")):
    rng = random.Random(seed)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if bp.get(x, y, z) is None and bp.get(x, y - 1, z) in on and rng.random() < density:
                bp.set(x, y, z, rng.choice(plants))


def snow_cover(bp, region, seed=0, chance=0.85):
    """Snow layers on every exposed top surface inside region."""
    rng = random.Random(seed)
    (x0, y0, z0), (x1, y1, z1) = region
    tops = {}
    for (x, y, z), b in bp.blocks.items():
        if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1 and b[0] != "minecraft:air":
            if (x, z) not in tops or y > tops[(x, z)]:
                tops[(x, z)] = y
    for (x, z), y in tops.items():
        name, props, _ = bp.blocks[(x, y, z)]
        short = name.split(":")[1]
        if bp.get(x, y + 1, z) not in (None, "minecraft:air"):
            continue
        if not (short.endswith(("planks", "_block", "stone", "bricks", "tiles", "ice", "_log", "dirt", "wool",
                                "cobblestone", "andesite", "slab", "stairs", "gravel")) or "grass_block" in short):
            continue
        if short.endswith("slab") and props.get("type") != "top":
            continue
        if short.endswith("stairs") and props.get("half") != "top":
            continue
        if rng.random() < chance:
            bp.set(x, y + 1, z, f"snow[layers={rng.choice([1, 1, 2, 2, 3])}]")


# ------------------------------------------------------------ laying a built section on its side
_DROP = ("ladder", "lantern", "chain", "pane", "fence", "torch", "bed", "door", "carpet", "candle", "bell",
         "campfire", "banner", "vine", "lectern", "table", "barrel", "chest", "rod", "button", "wall",
         "cartography", "hay", "flower", "pot", "skull", "head", "anvil", "grindstone", "crafting", "bars")


def _full_of(name):
    ns, short = name.split(":")
    for wood in ("spruce", "oak", "dark_oak", "birch"):
        if short in (f"{wood}_stairs", f"{wood}_slab"):
            return f"{ns}:{wood}_planks"
    short = short.replace("brick_stairs", "bricks").replace("tile_stairs", "tiles").replace("_stairs", "")
    short = short.replace("brick_slab", "bricks").replace("tile_slab", "tiles").replace("_slab", "")
    return f"{ns}:{short}"


def lay_down(src, dst, y_range, x0, ground_y, z_shift=0, keep=None):
    """Rotate the part of `src` with y in y_range so its vertical axis points east (+x), as if it fell.

    Local (x, y, z) -> world (x0 + y - y_range[0], ground_y + x, z + z_shift). Stairs/slabs become
    full blocks, fragile blocks are dropped, logs are re-axed."""
    for (x, y, z), (name, props, data) in src.blocks.items():
        if not (y_range[0] <= y <= y_range[1]) or (keep and not keep(x, y, z)):
            continue
        short = name.split(":")[1]
        if name == "minecraft:air":
            spec = "air"
        elif family(name) == "stairs" or short.endswith("_slab"):
            spec = _full_of(name)
        elif any(k in short for k in _DROP):
            spec = "air"
        elif "axis" in props:
            spec = (name, dict(props, axis={"y": "x", "x": "y"}.get(props["axis"], props["axis"])))
        else:
            spec = (name, dict(props))
        dst.set(x0 + (y - y_range[0]), ground_y + x, z + z_shift, spec)


# ============================================================ 1. Ruined watchtower
TW_WALL = Palette({"stone_bricks": 7, "cracked_stone_bricks": 2, "tuff_bricks": 2, "andesite": 1,
                   "mossy_stone_bricks": 1}, seed=11, scale=2.6)
TW_BASE = Palette({"cobblestone": 3, "mossy_cobblestone": 2, "stone": 2, "andesite": 1}, seed=12, scale=2.2)
TW_TRIM = "polished_tuff"
TW_TRIM_ST = "polished_tuff_stairs"
TW_ROOF = "brasshaven:slate_roof_tiles"
TW_ROOF_ST = "brasshaven:slate_roof_tile_stairs"
TW_IN, TW_OUT = 4.5, 6.5     # interior radius / outer wall radius
TW_FLOORS = (9, 18, 27)
TW_EAVE = 38


def _tower_upright(bp, ruined):
    """The complete tower (centre 0,0): batter base, banded shaft, spiral stair, rooms, conical roof."""
    # foundation and battered base
    for y in range(-6, 0):
        for x, z in ring_cells(0, 0, -1, 7.5 + (1 if y < -3 else 0)):
            bp.set(x, y, z, TW_BASE.pick(x, y, z), keep=True)
    for y in (0, 1):
        ring(bp, 0, y, 0, TW_IN, 7.5, TW_BASE)
    ring_stairs(bp, 0, 2, 0, 7, "stone_brick_stairs", half="bottom")
    for x, z in ring_cells(0, 0, -1, TW_IN):
        bp.set(x, 0, z, "spruce_planks" if (x + z) % 5 else "cobblestone")
    # shaft
    for y in range(2, TW_EAVE):
        ring(bp, 0, y, 0, TW_IN, TW_OUT, TW_WALL)
        for x, z in ring_cells(0, 0, -1, TW_IN):
            bp.set(x, y, z, "air")
    # string courses: flush polished band + corbelled drip course
    for fy in TW_FLOORS:
        ring(bp, 0, fy, 0, TW_IN, TW_OUT, TW_TRIM)
        ring_stairs(bp, 0, fy, 0, 7, TW_TRIM_ST, half="top")
    # floors with a beam
    for fy in TW_FLOORS:
        for x, z in ring_cells(0, 0, -1, TW_IN):
            bp.set(x, fy, z, "spruce_planks")
        for x in range(-4, 5):
            bp.set(x, fy, 0, log("stripped_dark_oak_log", "x"))
    # windows: slit windows on the lower floors, tall arched windows in the lookout room
    slits = [(2, 4, 200), (2, 4, 320), (11, 13, 30), (11, 13, 150), (11, 13, 260), (20, 22, 90), (20, 22, 210),
             (20, 22, 330), (5, 7, 30)]
    for y0, y1, ang in slits:
        radial_cut(bp, 0, 0, ang, y0, y1, 4.2, 7.6)
        if not ruined:
            radial_cut(bp, 0, 0, ang, y0, y1, 5.6, 5.6, spec="iron_bars")
        x, z = at_angle(0, 0, ang, 7.0)
        bp.set(x, y1 + 1, z, TW_TRIM)
    for ang in (0, 90, 180, 270):
        radial_cut(bp, 0, 0, ang + 45, 30, 34, 4.2, 7.6, width=2)
        if not ruined:
            radial_cut(bp, 0, 0, ang + 45, 30, 34, 5.4, 5.4, width=2, spec="glass_pane")
        x, z = at_angle(0, 0, ang + 45, 6.8)
        bp.set(x, 29, z, stair(TW_TRIM_ST, _toward(-x, -z), "top"))
        for dy in (35,):
            x, z = at_angle(0, 0, ang + 45, 6.6)
            bp.set(x, dy, z, TW_TRIM)
    # entrance (south): 2-wide arched opening through the battered wall, double door, steps
    for x in (-1, 0):
        for z in range(4, 8):
            for y in range(1, 4):
                bp.set(x, y, z, "air")
        bp.set(x, 3, 6, stair(TW_TRIM_ST, "east" if x == -1 else "west", "top"))
        bp.set(x, 4, 7, TW_TRIM)
        bp.set(x, 3, 7, stair(TW_TRIM_ST, "east" if x == -1 else "west", "top"))
    for x in (-2, 1):
        for y in range(1, 5):
            bp.set(x, y, 7, TW_TRIM)
    bp.set(-1, 5, 7, "chiseled_tuff")
    bp.set(0, 5, 7, "chiseled_tuff")
    if not ruined:
        bp.door(-1, 1, 5, "south", "spruce", hinge="left")
        bp.door(0, 1, 5, "south", "spruce", hinge="right")
        bp.lantern(-2, 3, 8)
        bp.set(-2, 2, 8, "air")
        bp.wall_torch(-3, 3, 7, "south")
        bp.wall_torch(2, 3, 7, "south")
    for i, z in enumerate((8, 9)):
        for x in range(-2, 2):
            bp.set(x, -i, z, stair("stone_brick_stairs", "north"))
            bp.set(x, -i - 1, z, "cobblestone")
    # spiral stair hugging the wall
    k = 0
    while True:
        y = 1 + k // 2
        if y > TW_EAVE - 2:
            break
        ang = 135 + k * 24
        for rr in (4.0, 3.0):
            x, z = at_angle(0, 0, ang, rr)
            bp.set(x, y, z, slab("stone_brick_slab", "bottom" if k % 2 == 0 else "top"))
            for c in range(1, 4):
                n = bp.get(x, y + c, z)
                if n and ("planks" in n or "log" in n):
                    bp.set(x, y + c, z, "air")
        k += 1
    # ---- rooms
    # ground floor: store room
    bp.barrel(-3, 1, -1, "up")
    bp.barrel(-3, 2, -1, "north")
    bp.barrel(-3, 1, 0, "up")
    bp.set(3, 1, -1, "crafting_table")
    bp.set(3, 1, 0, "smithing_table")
    bp.entity(2, 1, 2, {"id": "minecraft:armor_stand", "Rotation": [45.0, 0.0]})
    # cellar hatch (secret: covered by a moss carpet in the ruin)
    bp.set(-1, 0, -2, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    # floor 1: guard room
    bp.table(0, 10, 0, "spruce_pressure_plate", "spruce_fence")
    bp.table(1, 10, 0, "spruce_pressure_plate", "spruce_fence")
    bp.stairs(0, 10, 1, "spruce_stairs", "north")
    bp.stairs(1, 10, -1, "spruce_stairs", "south")
    bp.set(-2, 10, 2, "fletching_table")
    bp.barrel(2, 10, 2, "up", None if ruined else LOOT + "watchtower")
    # floor 2: quarters
    bp.bed(-2, 19, -1, "south", "red")
    bp.bed(2, 19, -1, "south", "red")
    bp.chest(0, 19, -2, "south", LOOT + "watchtower")
    bp.set(0, 19, 2, "red_carpet")
    bp.set(-1, 19, 2, "red_carpet")
    # floor 3: lookout room
    bp.set(-1, 28, -2, "cartography_table")
    bp.set(1, 28, -2, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(0, 28, 2, "bell[attachment=floor,facing=north,powered=false]")
    bp.chest(2, 28, 1, "west", LOOT + "watchtower")
    for fy in TW_FLOORS:
        arch.hanging_lantern(bp, 0, fy - 1, 0, chain=2)
    # ---- roof: flared eave, corbels, steep slate cone with finial
    ring_stairs(bp, 0, TW_EAVE - 1, 0, 7, TW_TRIM_ST, half="top")
    for x, z in ring_cells(0, 0, -1, 7.5):
        bp.set(x, TW_EAVE, z, "dark_oak_planks" if math.hypot(x, z) > TW_OUT else "spruce_planks")
    ring_stairs(bp, 0, TW_EAVE, 0, 8, TW_ROOF_ST, half="bottom")
    ring_stairs(bp, 0, TW_EAVE - 1, 0, 8, "dark_oak_stairs", half="top", inward=False)
    top = arch.spire(bp, 0, 0, TW_EAVE + 1, 7, TW_ROOF, TW_ROOF_ST, steep=2)
    # small lucarnes on the cone (one per side)
    for ang in (0, 90, 180, 270):
        x, z = at_angle(0, 0, ang, 6)
        f = _toward(x, z)
        px, pz = (0, 1) if f in ("east", "west") else (1, 0)
        for s in (-1, 0, 1):
            for y in (TW_EAVE + 2, TW_EAVE + 3):
                bp.set(x + px * s, y, z + pz * s, "dark_oak_planks" if s else "air")
            bp.set(x + px * s, TW_EAVE + 4, z + pz * s, stair(TW_ROOF_ST, OPPOSITE[f]) if s == 0 else
                   stair(TW_ROOF_ST, _toward(-px * s, -pz * s)))
        bp.set(x, TW_EAVE + 2, z, "glass_pane")
        bp.set(x, TW_EAVE + 3, z, "glass_pane")
        bp.set(x, TW_EAVE + 5, z, slab("brasshaven:slate_roof_tile_slab"))
    bp.set(0, top - 1, 0, "brasshaven:slate_roof_tiles")
    arch.hanging_lantern(bp, 0, TW_EAVE - 1, 0, chain=3)
    return top


def _curtain_x(bp, x0, x1, z0, h_of, rng, ruined, crenel_min=7):
    """3-thick curtain wall along x (z0..z0+2) with walk, crenels and buttresses on the north side."""
    for x in range(min(x0, x1), max(x0, x1) + 1):
        h = h_of(x)
        for z in range(z0, z0 + 3):
            for y in range(-3, h + 1):
                bp.set(x, y, z, TW_BASE.pick(x, y, z) if y <= 1 else TW_WALL.pick(x, y, z))
        if h >= crenel_min:
            for z in (z0, z0 + 2):
                bp.set(x, h + 1, z, TW_WALL.pick(x, h + 1, z))
                if x % 2 == 0:
                    bp.set(x, h + 2, z, TW_WALL.pick(x, h + 2, z))
                    bp.set(x, h + 3, z, slab("stone_brick_slab"))
            bp.set(x, h, z0 + 1, "stone_bricks")
        if x % 6 == 0 and h >= 3:
            arch.buttress(bp, "north", z0, x, 0, min(h, 6), "stone_bricks", "stone_brick_stairs", depth=2)


def _curtain_z(bp, z0, z1, x0, h_of, rng, crenel_min=7):
    for z in range(min(z0, z1), max(z0, z1) + 1):
        h = h_of(z)
        for x in range(x0, x0 + 3):
            for y in range(-3, h + 1):
                bp.set(x, y, z, TW_BASE.pick(x, y, z) if y <= 1 else TW_WALL.pick(x, y, z))
        if h >= crenel_min:
            for x in (x0, x0 + 2):
                bp.set(x, h + 1, z, TW_WALL.pick(x, h + 1, z))
                if z % 2 == 0:
                    bp.set(x, h + 2, z, TW_WALL.pick(x, h + 2, z))
                    bp.set(x, h + 3, z, slab("stone_brick_slab"))


def _guardhouse(bp, ruined, rng):
    """Small stone guardhouse with a timber upper floor (x -19..-10, z 3..10)."""
    x0, x1, z0, z1 = -19, -10, 3, 10
    bp.fill(x0, -4, z0, x1, -1, z1, "cobblestone", keep=True)
    bp.room(x0, 0, z0, x1, 5, z1, TW_WALL.pick(0, 0, 0), floor="spruce_planks")
    for y in range(0, 6):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                bp.set(x, y, z, TW_WALL.pick(x, y, z) if y > 1 else TW_BASE.pick(x, y, z))
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                bp.set(x, y, z, TW_WALL.pick(x, y, z) if y > 1 else TW_BASE.pick(x, y, z))
    for x in (x0, x1):
        for z in (z0, z1):
            for y in range(0, 6):
                bp.set(x, y, z, TW_TRIM if y % 2 else "tuff_bricks")
    # floor band + timber upper storey
    for x in range(x0 - 1, x1 + 2):
        bp.set(x, 5, z0 - 1, stair(TW_TRIM_ST, "south", "top"))
        bp.set(x, 5, z1 + 1, stair(TW_TRIM_ST, "north", "top"))
    for z in range(z0, z1 + 1):
        bp.set(x0 - 1, 5, z, stair(TW_TRIM_ST, "east", "top"))
        bp.set(x1 + 1, 5, z, stair(TW_TRIM_ST, "west", "top"))
    bp.fill(x0 + 1, 5, z0 + 1, x1 - 1, 5, z1 - 1, "spruce_planks")
    for y in range(6, 9):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                post = x in (x0, x1) or (x - x0) % 3 == 0
                bp.set(x, y, z, log("dark_oak_log") if post else "spruce_planks")
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                post = z in (z0, z1) or (z - z0) % 3 == 0
                bp.set(x, y, z, log("dark_oak_log") if post else "spruce_planks")
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                bp.set(x, y, z, "air")
    for x in range(x0, x1 + 1):
        bp.set(x, 9, z0, log("dark_oak_log", "x"))
        bp.set(x, 9, z1, log("dark_oak_log", "x"))
    for x in range(x0 + 2, x1 - 1, 3):
        for z in (z0, z1):
            bp.set(x, 7, z, "glass_pane")
            bp.set(x + 1, 7, z, "glass_pane")
    arch.steep_roof(bp, x0, z0, x1, z1, 10, TW_ROOF_ST, axis="x", overhang=1, fill="spruce_planks",
                    under="dark_oak_stairs", ridge=slab("brasshaven:slate_roof_tile_slab"))
    # chimney on the west gable
    for y in range(1, 16):
        bp.set(x0 - 1, y, 6, "cobblestone" if y < 6 else "bricks")
        bp.set(x0 - 1, y, 7, "cobblestone" if y < 6 else "bricks")
    bp.set(x0 - 1, 16, 6, "cobblestone_wall")
    bp.set(x0 - 1, 16, 7, "cobblestone_wall")
    # door (east side, facing the tower) + windows
    bp.set(x1, 1, 7, "air")
    bp.set(x1, 2, 7, "air")
    bp.set(x1, 3, 7, TW_TRIM)
    if not ruined:
        bp.door(x1, 1, 7, "east", "spruce")
    bp.set(x1 + 1, 0, 7, stair("stone_brick_stairs", "west"))
    for z in (5, 9):
        bp.set(x1, 2, z, "glass_pane" if not ruined else "air")
        bp.set(x1 + 1, 1, z, stair(TW_TRIM_ST, "west", "top"))
    for x in (-16, -13):
        bp.set(x, 2, z1, "glass_pane" if not ruined else "air")
        bp.set(x, 3, z1, "glass_pane" if not ruined else "air")
        bp.set(x, 1, z1 + 1, stair(TW_TRIM_ST, "north", "top"))
    # interior: fireplace, bunks, table, rack
    bp.set(x0 + 1, 1, 6, "campfire[lit=false,signal_fire=false,waterlogged=false,facing=east]")
    bp.set(x0 + 1, 1, 7, "campfire[lit=false,signal_fire=false,waterlogged=false,facing=east]")
    bp.set(x0 + 1, 2, 6, "air")
    bp.fill(x0 + 1, 3, 5, x0 + 1, 4, 8, "bricks")
    bp.bed(-17, 1, 4, "south", "brown")
    bp.bed(-15, 1, 4, "south", "brown")
    bp.table(-14, 1, 8, "spruce_pressure_plate", "spruce_fence")
    bp.stairs(-15, 1, 8, "spruce_stairs", "east")
    bp.stairs(-13, 1, 8, "spruce_stairs", "west")
    bp.barrel(-12, 1, 4, "up", LOOT + "watchtower")
    bp.barrel(-11, 1, 4, "up")
    bp.set(-11, 2, 4, "barrel[facing=north,open=false]")
    bp.ladder(-11, 1, 9, 5, "north")
    bp.set(-11, 5, 9, "ladder[facing=north,waterlogged=false]")
    bp.lantern(-14, 4, 6, hanging=True)
    # loft
    bp.bed(-17, 6, 5, "east", "red")
    bp.barrel(-17, 6, 8, "up")
    if ruined:
        # roof caved in on the east half; upper floor burnt through
        for (x, y, z) in list(bp.blocks):
            if x0 - 2 <= x <= x1 + 2 and z0 - 2 <= z <= z1 + 2 and y >= 6:
                cut = 9 + (x - x0) * -0.9 + rng.uniform(-1.5, 1.5)
                if x > -15 and y > cut + 4 or (x > -13 and y >= 6 and rng.random() < 0.65):
                    bp.set(x, y, z, "air")
        for x in range(-14, x1):
            for z in range(z0 + 1, z1):
                if rng.random() < 0.45:
                    bp.set(x, 5, z, "air")
        bp.line((-15, 6, 4), (-11, 1, 6), log("dark_oak_log", "x"))
        bp.line((-14, 9, 9), (-11, 2, 8), log("dark_oak_log", "x"))
        for _ in range(14):
            x, z = rng.randint(-14, x1 - 1), rng.randint(z0 + 1, z1 - 1)
            if bp.get(x, 1, z) in (None, "minecraft:air"):
                bp.set(x, 1, z, rng.choice(["cobblestone", "brasshaven:slate_roof_tiles", "stone_bricks",
                                            "spruce_slab[type=bottom,waterlogged=false]"]))


def watchtower(ruined):
    def build(bp):
        rng = random.Random(77 if ruined else 78)
        full = Blueprint("tower_full")
        top = _tower_upright(full, ruined)

        # broken skyline: low on the east (where the top fell), high on the west
        def h_break(x, z):
            a = math.atan2(z, x)
            return min(36, 25 + 11 * (1 - math.cos(a)) / 2 + ((x * 7 + z * 13) % 5) * 0.6)

        # ---- ground, paths, curtain walls, guardhouse
        if ruined:
            ground_patch(bp, 3, 3, 31, 22, seed=5)
        else:
            ground_patch(bp, -2, 0, 22, 18, seed=5)
        path_line(bp, [(-1, 9), (-1, 16), (-4, 21)], 0, Palette({"dirt_path": 3, "coarse_dirt": 2, "gravel": 1},
                                                              seed=4), width=3, seed=1, chance=0.8)
        path_line(bp, [(-2, 12), (-9, 8)], 0, Palette({"dirt_path": 3, "coarse_dirt": 1}, seed=4), width=2,
                  seed=2, chance=0.75)

        if ruined:
            west_h = lambda x: max(1, round(10 - max(0, (-x - 9)) * 0.75 + rng.uniform(-1.2, 1.2)))
            north_h = lambda z: max(0, round(7 - max(0, (-z - 8)) * 0.9 + rng.uniform(-1.5, 1.0)))
        else:
            west_h = lambda x: 10 if x > -18 else 10 - (-18 - x) * 2
            north_h = lambda z: 8 if z > -15 else 8 - (-15 - z) * 2
        _curtain_x(bp, -21, -6, -1, west_h, rng, ruined)
        _curtain_z(bp, -17, -6, -1, north_h, rng)
        _guardhouse(bp, ruined, rng)

        # ---- the tower itself
        if ruined:
            for (x, y, z), b in full.blocks.items():
                d = math.hypot(x, z)
                if y <= 24 or (d > TW_IN and y <= h_break(x, z)) or (d <= TW_IN and y <= 27):
                    bp.blocks[(x, y, z)] = b
            # broken top floor remnant hanging on the west side
            for x, z in ring_cells(0, 0, -1, TW_IN):
                if x < -1:
                    bp.set(x, 27, z, "spruce_planks")
                elif x < 2 and (x + z) % 3 == 0:
                    bp.set(x, 27, z, "air")
            bp.chest(-3, 28, 1, "east", LOOT + "watchtower")
            # ---- the fallen top, broken into three pieces lying east
            lay_down(full, bp, (26, 34), x0=9, ground_y=5, z_shift=1,
                     keep=lambda x, y, z: y > 26 + ((x * 5 + z * 3) % 4) * 0.7)
            lay_down(full, bp, (35, 42), x0=20, ground_y=5, z_shift=3)
            lay_down(full, bp, (46, top), x0=20, ground_y=1, z_shift=17)
            for (x, y, z) in list(bp.blocks):
                if x >= 8 and y <= 0 and bp.get(x, y, z) == "minecraft:air":
                    bp.set(x, y, z, rng.choice(["coarse_dirt", "gravel", "cobblestone", "dirt"]))
            for x in range(8, 34):
                for z in range(-8, 26):
                    if bp.get(x, 1, z) == "minecraft:air" and bp.get(x, 0, z) not in (None, "minecraft:air") \
                            and rng.random() < 0.3:
                        bp.set(x, 1, z, rng.choice(["cobblestone", "stone_brick_slab[type=bottom,waterlogged=false]",
                                                    "moss_carpet", "mossy_cobblestone"]))
            bp.decay(0.05, protect=("ladder",), region=((19, 1, -8), (36, 16, 26)))
            bp.chest(14, 1, 1, "west", LOOT + "watchtower")
            # rubble scree around the foot of the tower and between the pieces
            for _ in range(140):
                a = rng.uniform(-1.4, 1.4)
                r = rng.uniform(6.5, 13)
                x, z = round(math.cos(a) * r), round(math.sin(a) * r)
                y = 1
                while bp.get(x, y, z) not in (None, "minecraft:air") and y < 4:
                    y += 1
                if bp.get(x, y - 1, z) not in (None, "minecraft:air"):
                    bp.set(x, y, z, rng.choice(["cobblestone", "mossy_cobblestone", "stone_bricks",
                                                "cracked_stone_bricks", "tuff_bricks",
                                                "stone_brick_slab[type=bottom,waterlogged=false]"]))
            # slate debris where the roof shattered
            for _ in range(70):
                x, z = rng.randint(14, 32), rng.randint(8, 24)
                if bp.get(x, 1, z) is None:
                    bp.set(x, 1, z, rng.choice(["brasshaven:slate_roof_tiles", "brasshaven:slate_roof_tile_slab"
                                                "[type=bottom,waterlogged=false]", "dark_oak_planks"]))
            # cellar under the tower: hidden hatch under moss, spawner guards the hoard
            bp.set(-1, 1, -2, "moss_carpet")
        else:
            bp.paste(full, 0, 0, 0)
            bp.set(-3, 1, 3, "lantern[hanging=false,waterlogged=false]")

        # ---- cellar
        for y in range(-6, 0):
            for x, z in ring_cells(0, 0, -1, TW_IN):
                bp.set(x, y, z, "air" if y > -6 else "cobblestone")
        ring(bp, 0, -6, 0, TW_IN, 6.5, TW_BASE)
        bp.ladder(-1, -5, -2, -1, "south")
        bp.set(-1, -5, -3, "cobblestone")
        bp.fill(-1, -5, -3, -1, -1, -3, "cobblestone")
        bp.chest(3, -5, 0, "west", LOOT + "watchtower")
        bp.barrel(3, -5, 1, "up")
        bp.barrel(3, -5, -1, "up")
        bp.set(2, -5, 2, "cobweb")
        bp.set(-3, -2, 2, "cobweb")
        bp.set(-2, -5, 2, "skeleton_skull[rotation=6]")
        bp.lantern(0, -1, 0, hanging=True, soul=True)
        if ruined:
            bp.spawner(0, -5, 1, MOB["ruin_walker"])

        # ---- campfire remains + log seats by the guardhouse
        bp.set(-5, 1, 13, f"campfire[lit={'false' if ruined else 'true'},signal_fire=false,waterlogged=false,facing=north]")
        for x, z in ((-6, 13), (-4, 13), (-5, 12), (-5, 14)):
            bp.set(x, 0, z, "cobblestone")
        bp.set(-8, 1, 13, log("spruce_log", "z"))
        bp.set(-8, 1, 14, log("spruce_log", "z"))
        bp.set(-5, 1, 16, log("spruce_log", "x"))
        bp.set(-4, 1, 16, log("spruce_log", "x"))
        bp.set(-2, 1, 13, "cauldron")

        # ---- landscaping: trees, bushes, flowers
        arch.big_oak(bp, -25, 1, -9, h=9, seed=3, crown=5)
        arch.oak(bp, 7, 1, -12, h=6, seed=4)
        arch.oak(bp, -24, 1, 12, h=5, seed=5)
        arch.birch(bp, 10 if not ruined else -2, 1, 13 if not ruined else 21, h=7, seed=6)
        for x, z, r in ((-8, -7, 1), (6, 9, 1), (-21, 5, 1), (4, -8, 1)):
            arch.bush(bp, x, 1, z, r=r)
        arch.boulder(bp, 13, 1, -8, r=2, seed=2)
        skirt(bp, 0, depth=6, spread=3, seed=8)
        scatter_plants(bp, -32, -24, 36, 30, 1, 0.22, 9, FLOWERS)
        # ---- ageing: moss, vines, overgrowth
        arch.moss_on(bp, ((-40, -8, -40), (40, 60, 40)), chance=0.22 if ruined else 0.08, seed=10)
        arch.vines_on(bp, ((-40, 2, -40), (40, 30, 40)), chance=0.05 if ruined else 0.015, seed=11, max_len=7)
        if ruined:
            for (x, y, z), b in list(bp.blocks.items()):
                if b[0] in ("minecraft:stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:tuff_bricks",
                            "minecraft:cobblestone", "minecraft:mossy_cobblestone") and y >= 3 \
                        and bp.get(x, y + 1, z) is None and rng.random() < 0.35:
                    bp.set(x, y + 1, z, rng.choice(["moss_carpet", "moss_carpet", "short_grass", "fern"]))
        # ---- interiors: a garrison still at its post, or the dust of one long gone
        if ruined:
            I.decorate(bp, "ruin", seed=1, loot=LOOT + "watchtower")
        else:
            I.decorate(bp, "barracks", seed=1)
            I.yard(bp, (-32, -24, 36, 30), 1, {"hay": 2, "crates": 2, "woodpile": 2, "cart": 1, "lamp": 1},
                   count=6, seed=1)
    return build


register(StructureDef(
    "ruined_watchtower", "overworld",
    ["#minecraft:is_forest", "plains", "#minecraft:is_hill", "#minecraft:is_taiga", "windswept_hills",
     "meadow", "savanna_plateau", "stony_peaks"],
    [Piece("tower_ruined", watchtower(True), 3), Piece("tower_intact", watchtower(False), 1, processors="aging")],
    spacing=24, separation=8, processors="ruin",
    # bandits squat the old towers (wf/denizens.py): marksmen on the walls, a few undead in the cellars
    spawns=[("brasshaven:bandit_marksman", 6, 1, 1), ("minecraft:skeleton", 8, 1, 2), ("minecraft:zombie", 8, 1, 2)],
    creatures=[("bandit_marksman", 2)],
    title_fr="Tour de guet en ruine", title_en="Ruined Watchtower"))


# ============================================================ 2. Bandit camp (fortified)
BC_R = 18


def _bc_radius(a):
    return BC_R + 1.3 * math.sin(3 * a + 0.4) + 0.8 * math.cos(2 * a)


def _tent(bp, x0, z0, length, half_w, colors, ridge_y=None, open_end="south", rng=None, inside=None):
    """A-frame canvas tent, ridge along z from z0 to z0+length-1. Stripes alternate along z."""
    h = ridge_y or half_w + 1
    z1 = z0 + length - 1
    for z in range(z0, z1 + 1):
        col = colors[(z - z0) % len(colors)]
        for dx in range(-half_w, half_w + 1):
            top = h - abs(dx)
            bp.set(x0 + dx, top, z, f"{col}_wool")
            for y in range(1, top):
                bp.set(x0 + dx, y, z, "air")
            bp.set(x0 + dx, 0, z, "spruce_planks" if abs(dx) < half_w else "coarse_dirt")
        bp.set(x0 - half_w - 1, 0, z, "coarse_dirt")
        bp.set(x0 + half_w + 1, 0, z, "coarse_dirt")
    # ridge pole + end posts
    for z in range(z0 - 1, z1 + 2):
        bp.set(x0, h + 1, z, log("stripped_spruce_log", "z"))
    for z in (z0 - 1, z1 + 1):
        for y in range(1, h + 1):
            bp.set(x0, y, z, "spruce_fence")
    # closed back gable, half-open front flaps
    back = z1 if open_end == "south" else z0
    front = z0 if open_end == "south" else z1
    for dx in range(-half_w + 1, half_w):
        for y in range(1, h - abs(dx)):
            bp.set(x0 + dx, y, back, f"{colors[0]}_wool")
    for dx in (-half_w + 1, half_w - 1):
        bp.set(x0 + dx, 1, front, f"{colors[-1]}_wool")
    # guy ropes: fence pegs
    for dz in (z0, z1):
        bp.set(x0 - half_w - 1, 1, dz, "spruce_fence")
        bp.set(x0 + half_w + 1, 1, dz, "spruce_fence")
    for z in range(z0 + 1, z1):
        bp.set(x0, 1, z, "brown_carpet")


def solid_pyramid(bp, x0, z0, x1, z1, y, stairs_block, fill):
    """Pyramid roof of stairs with a solid core (no see-through gaps from below)."""
    while x0 <= x1 and z0 <= z1:
        if x0 == x1 or z0 == z1:
            bp.fill(x0, y, z0, x1, y, z1, slab(stairs_block.replace("_stairs", "_slab")))
            return y
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    f = "south" if z == z0 else "north" if z == z1 else "east" if x == x0 else "west"
                    bp.set(x, y, z, stair(stairs_block, f))
                else:
                    bp.set(x, y, z, fill)
        x0, x1, z0, z1, y = x0 + 1, x1 - 1, z0 + 1, z1 - 1, y + 1
    return y


def _bc_watchtower(bp, x0, z0, banner):
    """4x4 log watchtower with a covered platform at y=9."""
    x1, z1 = x0 + 3, z0 + 3
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for y in range(-2, 13):
            bp.set(x, y, z, log("spruce_log"))
    # cross bracing
    for y0 in (2, 6):
        for x in range(x0 + 1, x1):
            bp.set(x, y0, z0, log("stripped_spruce_log", "x"))
            bp.set(x, y0, z1, log("stripped_spruce_log", "x"))
        for z in range(z0 + 1, z1):
            bp.set(x0, y0, z, log("stripped_spruce_log", "z"))
            bp.set(x1, y0, z, log("stripped_spruce_log", "z"))
    bp.line((x0 + 1, 3, z0), (x1 - 1, 5, z0), "spruce_fence")
    bp.line((x0, 3, z0 + 1), (x0, 5, z1 - 1), "spruce_fence")
    # platform (overhanging) + parapet
    bp.fill(x0 - 1, 9, z0 - 1, x1 + 1, 9, z1 + 1, "spruce_planks")
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
                bp.set(x, 10, z, "spruce_fence")
                bp.set(x, 8, z, stair("spruce_stairs", _toward(x0 + 1.5 - x, z0 + 1.5 - z), "top"))
    for x in range(x0, x1 + 1):
        for z in (z0 - 1, z1 + 1):
            bp.set(x, 11, z, "air")
    # roof
    solid_pyramid(bp, x0 - 2, z0 - 2, x1 + 2, z1 + 2, 13, "dark_oak_stairs", "dark_oak_planks")
    bp.set(x0 + 1, 17, z0 + 1, "spruce_fence")
    bp.set(x0 + 1, 18, z0 + 1, "spruce_fence")
    bp.set(x0 + 1, 19, z0 + 1, f"{banner}_banner[rotation=0]")
    # ladder inside + hatch
    bp.ladder(x0 + 1, 1, z0 + 1, 9, "south")
    bp.set(x0 + 1, 0, z0 + 1, "spruce_planks")
    bp.lantern(x0 + 2, 12, z0 + 2, hanging=True)
    bp.set(x0 + 2, 10, z1, "barrel[facing=up,open=false]")
    bp.set(x1, 10, z0 + 2, "target[power=0]")


def _bc_wagon(bp, x0, z0, rng):
    """Stolen merchant cart (x0..x0+2, z0..z0+5) with canvas cover, cargo and wheels."""
    for z in range(z0, z0 + 6):
        for x in range(x0, x0 + 3):
            bp.set(x, 1, z, slab("spruce_slab", "top"))
        bp.set(x0 - 1, 2, z, "spruce_fence" if z not in (z0, z0 + 5) else "spruce_planks")
        bp.set(x0 + 3, 2, z, "spruce_fence" if z not in (z0, z0 + 5) else "spruce_planks")
    for z in (z0 + 1, z0 + 4):
        bp.set(x0 - 1, 1, z, log("dark_oak_log", "x"))
        bp.set(x0 + 3, 1, z, log("dark_oak_log", "x"))
    # canvas hoops over the back
    for z in range(z0 + 2, z0 + 6):
        for x, y in ((x0 - 1, 3), (x0 + 3, 3), (x0 - 1, 4), (x0 + 3, 4), (x0, 5), (x0 + 1, 5), (x0 + 2, 5)):
            bp.set(x, y, z, "white_wool" if z % 2 else "light_gray_wool")
    # cargo
    bp.barrel(x0, 2, z0 + 4, "up", LOOT + "bandit_camp")
    bp.set(x0 + 2, 2, z0 + 4, "barrel[facing=east,open=false]")
    bp.set(x0 + 1, 2, z0 + 5, "hay_block[axis=x]")
    bp.set(x0 + 2, 2, z0 + 2, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    bp.set(x0, 2, z0 + 1, "chest[facing=south,type=single,waterlogged=false]")
    # shafts
    for z in range(z0 - 3, z0):
        bp.set(x0, 1, z, "spruce_fence")
        bp.set(x0 + 2, 1, z, "spruce_fence")
    bp.set(x0 + 1, 1, z0 - 3, log("stripped_spruce_log", "x"))


def bandit_camp(bp):
    rng = random.Random(41)
    # ---- ground: trampled earth inside, meadow outside
    ground_patch(bp, 0, 1, BC_R + 9, BC_R + 9, seed=7)
    inner = Palette({"coarse_dirt": 4, "dirt_path": 2, "podzol": 2, "gravel": 1, "rooted_dirt": 1}, seed=3, scale=2.5)
    for x in range(-BC_R - 3, BC_R + 4):
        for z in range(-BC_R - 3, BC_R + 4):
            d = math.hypot(x, z)
            if d < _bc_radius(math.atan2(z, x)) - 0.5 and rng.random() < 0.9:
                bp.set(x, 0, z, inner.pick(x, 0, z))
    path_line(bp, [(0, BC_R), (1, BC_R + 6), (-2, BC_R + 11)], 0,
              Palette({"dirt_path": 3, "coarse_dirt": 2}, seed=2), width=3, seed=3, chance=0.85)

    # ---- palisade of sharpened logs, inner rail + wall-walk segments
    posts = []
    for x in range(-BC_R - 4, BC_R + 5):
        for z in range(-BC_R - 4, BC_R + 5):
            a = math.atan2(z, x)
            r = _bc_radius(a)
            d = math.hypot(x, z)
            if r - 0.5 < d <= r + 0.5:
                if abs(x) <= 2 and z > 0:
                    continue  # gate
                posts.append((x, z, a))
    for x, z, a in posts:
        h = 5 + (x * 7 + z * 13) % 3
        for y in range(-3, h + 1):
            bp.set(x, y, z, log("spruce_log" if (x + z) % 4 else "stripped_spruce_log"))
        bp.set(x, h + 1, z, "spruce_fence")
        if (x * 3 + z) % 5 == 0:
            bp.set(x, h + 2, z, "spruce_fence")
    for x, z, a in posts:
        # horizontal rail + walkway on the inside, every post ring cell one step in
        ix, iz = round(x - math.cos(a) * 1.2), round(z - math.sin(a) * 1.2)
        if bp.get(ix, 3, iz) is None:
            bp.set(ix, 3, iz, slab("spruce_slab", "top"))
            if (ix + iz) % 4 == 0:
                bp.set(ix, 1, iz, "spruce_fence")
                bp.set(ix, 2, iz, "spruce_fence")
    # ---- gate: log lintel, banners, open gate leaves
    gz = round(_bc_radius(math.pi / 2))
    for x in (-3, 3):
        for y in range(-3, 9):
            bp.set(x, y, gz, log("dark_oak_log"))
        bp.set(x, 9, gz, "skeleton_skull[rotation=0]")
    for x in range(-3, 4):
        bp.set(x, 7, gz, log("dark_oak_log", "x"))
    bp.set(0, 8, gz, log("dark_oak_log", "x"))
    bp.set(-1, 8, gz, stair("dark_oak_stairs", "east"))
    bp.set(1, 8, gz, stair("dark_oak_stairs", "west"))
    for x in (-2, 2):
        bp.set(x, 6, gz + 1, "black_wall_banner[facing=south]")
        bp.set(x, 6, gz - 1, "red_wall_banner[facing=north]")
    # swung-open gate leaves (fence walls)
    for i in range(1, 4):
        for y in range(1, 5):
            bp.set(-3 + 0, y, gz - i, "spruce_fence" if y < 4 else "spruce_planks")
            bp.set(3, y, gz - i, "spruce_fence" if y < 4 else "spruce_planks")
    for x in range(-2, 3):
        for y in range(1, 7):
            bp.set(x, y, gz, "air")
    # ---- twin watchtowers flanking the gate
    _bc_watchtower(bp, -7, gz - 5, "black")
    _bc_watchtower(bp, 4, gz - 5, "red")
    bp.barrel(-5, 10, gz - 4, "up", LOOT + "bandit_camp")

    # ---- central bonfire with roasting spit and log benches
    for x, z in ring_cells(0, 0, -1, 2.6):
        bp.set(x, 0, z, rng.choice(["cobblestone", "mossy_cobblestone", "stone"]))
    for x, z in ring_cells(0, 0, 1.6, 2.6):
        bp.set(x, 1, z, rng.choice(["cobblestone_slab[type=bottom,waterlogged=false]", "stone_slab[type=bottom,waterlogged=false]"]))
    for x, z in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
        bp.set(x, 1, z, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.set(0, 0, 0, "hay_block[axis=y]")
    bp.set(0, 1, 0, "campfire[lit=true,signal_fire=true,waterlogged=false,facing=north]")
    for x in (-2, 2):
        bp.set(x, 2, 0, "spruce_fence")
        bp.set(x, 3, 0, "spruce_fence")
    for x in range(-1, 2):
        bp.set(x, 4, 0, "spruce_fence" if x else "iron_chain[axis=x,waterlogged=false]")
    for x, z, ax in ((-5, -1, "z"), (-5, 0, "z"), (-5, 1, "z"), (5, -1, "z"), (5, 0, "z"), (5, 1, "z"),
                     (-1, -5, "x"), (0, -5, "x"), (1, -5, "x")):
        bp.set(x, 1, z, log("stripped_spruce_log", ax))
    bp.set(-1, 1, 5, stair("spruce_stairs", "north"))
    bp.set(1, 1, 5, stair("spruce_stairs", "north"))
    # hidden ambush: pillager spawner under a trapdoor next to the fire
    bp.spawner(0, -1, 5, "minecraft:pillager")
    bp.set(0, -2, 5, "cobblestone")
    bp.set(0, 0, 5, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for x, z in ((-1, 4), (1, 4), (-1, 6), (1, 6), (0, 4), (0, 6)):
        bp.set(x, -1, z, "dirt")

    # ---- leader's tent (north): big striped pavilion with porch
    _tent(bp, 0, -15, 8, 4, ["red", "white"], ridge_y=6, open_end="south")
    for z in (-16, -7):
        for y in range(1, 8):
            bp.set(0, y, z, log("dark_oak_log"))
        bp.set(0, 8, z, "spruce_fence")
        bp.set(0, 9, z, "red_banner[rotation=8]" if z > -10 else "black_banner[rotation=0]")
    for x in (-3, 3):
        for y in range(1, 4):
            bp.set(x, y, -6, "spruce_fence")
    for x in range(-4, 5):
        bp.set(x, 4, -6, "red_wool" if x % 2 else "white_wool")
        bp.set(x, 4, -7, "red_wool" if x % 2 else "white_wool")
        for y in range(1, 4):
            if bp.get(x, y, -7) and "wool" in bp.get(x, y, -7):
                bp.set(x, y, -7, "air")
    bp.bed(-2, 1, -13, "south", "red")
    bp.chest(2, 1, -14, "south", LOOT + "bandit_camp")
    bp.set(3, 1, -14, "gold_block")
    bp.set(3, 1, -13, "barrel[facing=up,open=false]")
    bp.set(-3, 1, -10, "lectern[facing=east,has_book=false,powered=false]")
    bp.table(1, 1, -10, "spruce_pressure_plate", "spruce_fence")
    bp.stairs(2, 1, -10, "spruce_stairs", "west")
    bp.set(1, 2, -10, "candle[candles=3,lit=true,waterlogged=false]")
    for x in range(-2, 3):
        for z in range(-12, -8):
            if bp.get(x, 1, z) in (None, "minecraft:air", "minecraft:brown_carpet"):
                bp.set(x, 1, z, "red_carpet")
    # secret: the chief's personal stash, buried under the rug
    bp.chest(-1, 0, -12, "south", LOOT + "bandit_camp")
    bp.set(-1, -1, -12, "dirt")
    arch.hanging_lantern(bp, 0, 5, -11, chain=1)
    bp.lantern(-3, 1, -7)
    bp.lantern(3, 1, -7)

    # ---- small sleeping tents
    _tent(bp, -12, -9, 5, 2, ["brown", "brown", "light_gray"], ridge_y=3, open_end="south")
    _tent(bp, -14, -1, 5, 2, ["green", "brown"], ridge_y=3, open_end="south")
    _tent(bp, 12, -10, 6, 2, ["light_gray", "white"], ridge_y=3, open_end="south")
    for x, z, col in ((-12, -8, "brown"), (-14, 0, "green"), (12, -9, "white")):
        bp.bed(x, 1, z + 1, "north", col)

    # ---- prisoner cages (east) + gibbet
    for cx, cz in ((12, 2), (12, 7)):
        bp.fill(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, "cobblestone")
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                if x != cx or z != cz:
                    for y in (1, 2):
                        bp.set(x, y, z, "iron_bars")
                bp.set(x, 3, z, slab("spruce_slab", "bottom"))
        for x, z in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
            for y in (1, 2):
                bp.set(x, y, z, log("spruce_log"))
        bp.set(cx, 1, cz, "air")
        bp.set(cx - 1, 1, cz, "iron_bars")
    bp.set(12, 1, 2, "cobweb")
    bp.set(12, 1, 7, "skeleton_skull[rotation=3]")
    bp.set(10, 1, 7, "iron_bars")
    # gibbet: post, arm, chain and a hanging cage
    for y in range(1, 9):
        bp.set(8, y, 11, log("dark_oak_log"))
    for x in (9, 10):
        bp.set(x, 8, 11, log("dark_oak_log", "x"))
    bp.chain(10, 6, 11, 7)
    bp.set(10, 5, 11, "iron_bars")
    bp.set(10, 4, 11, "iron_bars")
    bp.set(10, 3, 11, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")

    # ---- loot pile of stolen goods (north-east, by the leader's tent) under a canvas lean-to
    lx, lz = 7, -12
    bp.chest(lx + 1, 1, lz, "south", LOOT + "bandit_camp")
    for x, z in ((lx, lz), (lx + 2, lz), (lx, lz + 1), (lx + 2, lz + 2), (lx + 3, lz + 1)):
        bp.barrel(x, 1, z, "up")
    bp.set(lx + 2, 2, lz, "barrel[facing=north,open=false]")
    bp.set(lx + 1, 1, lz + 2, "hay_block[axis=x]")
    bp.set(lx + 1, 2, lz + 1, "decorated_pot[facing=south,waterlogged=false,cracked=true]")
    bp.set(lx + 3, 1, lz + 2, "gold_block")
    bp.set(lx, 2, lz, "raw_iron_block")
    for x in range(lx - 1, lx + 5):
        bp.set(x, 4, lz - 1, "brown_wool")
        bp.set(x, 4, lz, "brown_wool")
        bp.set(x, 4, lz + 1, "brown_wool")
        bp.set(x, 3, lz + 2, "brown_wool")
        bp.set(x, 3, lz + 3, slab("spruce_slab", "top"))
    for x in (lx - 1, lx + 4):
        for y in (1, 2):
            bp.set(x, y, lz + 3, "spruce_fence")

    # ---- stolen cart (south-west, inside the gate)
    _bc_wagon(bp, -12, 7, rng)
    bp.chest(-12, 2, 8, "south", LOOT + "bandit_camp")

    # ---- target practice (west)
    for z in (-6, -3):
        bp.set(-8, 1, z, "hay_block[axis=y]")
        bp.set(-8, 2, z, "target[power=0]")
    bp.set(-7, 1, 2, "fletching_table")
    bp.set(-7, 1, 3, "grindstone[face=floor,facing=east]")
    bp.set(-7, 1, 4, "anvil[facing=north]")
    for y in (1, 2, 3):
        bp.set(-2, y, -7, "spruce_fence" if y < 3 else "carved_pumpkin[facing=south]")
    bp.set(-4, 1, -3, "spruce_fence")
    bp.set(-4, 2, -3, "hay_block[axis=y]")
    bp.set(-4, 3, -3, "carved_pumpkin[facing=east]")
    bp.set(-5, 2, -3, "spruce_fence")
    bp.set(-3, 2, -3, "spruce_fence")
    bp.entity(-7, 1, -1, {"id": "minecraft:armor_stand", "Rotation": [90.0, 0.0]})
    # weapon rack and torches
    for z in range(-1, 2):
        bp.set(-10, 1, z + 4, "spruce_fence")
    for x, z in ((-6, 7), (6, -5), (-9, -11), (9, 0), (-3, 10), (3, 10)):
        bp.set(x, 1, z, "spruce_fence")
        bp.set(x, 2, z, "spruce_fence")
        bp.lantern(x, 3, z)

    # ---- mess canopy by the fire: tables, cooking pot, smoker
    for x, z in ((4, 4), (9, 4), (4, 8), (9, 8)):
        for y in range(1, 5):
            bp.set(x, y, z, log("spruce_log"))
    for x in range(3, 11):
        for z in range(3, 10):
            dz = min(z - 3, 9 - z)
            bp.set(x, 5 + min(dz, 2), z, "brown_wool" if (x % 2) else "orange_wool")
    for x in range(5, 9):
        bp.set(x, 1, 6, slab("spruce_slab", "top"))
        bp.set(x, 1, 5, stair("spruce_stairs", "south"))
        bp.set(x, 1, 7, stair("spruce_stairs", "north"))
    bp.set(6, 2, 6, "candle[candles=2,lit=true,waterlogged=false]")
    bp.set(4, 1, 6, "smoker[facing=west,lit=true]")
    bp.set(4, 1, 7, "cauldron")
    bp.set(9, 1, 6, "barrel[facing=up,open=false]")
    arch.hanging_lantern(bp, 6, 6, 6, chain=1)
    # hay stack and feed trough by the cart
    for x, z in ((-14, 5), (-15, 5), (-14, 4)):
        bp.set(x, 1, z, "hay_block[axis=y]")
    bp.set(-14, 2, 5, "hay_block[axis=x]")
    bp.set(-9, 1, 13, "composter[level=4]")
    # cheval-de-frise: crossed sharpened stakes outside the gate
    for x in (-9, -6, 6, 9):
        z = gz + 3
        bp.set(x, 1, z, log("stripped_spruce_log", "x"))
        bp.set(x - 1, 2, z, "spruce_fence")
        bp.set(x + 1, 2, z, "spruce_fence")
        bp.set(x, 2, z, "spruce_fence")
        bp.set(x - 1, 1, z, "spruce_fence")
        bp.set(x + 1, 1, z, "spruce_fence")

    # ---- outside: chopped stumps, log piles, spruces, bushes
    for x, z in ((-22, 10), (-20, 14), (22, 8), (19, -16), (-16, -19), (6, -22)):
        if bp.get(x, 0, z) is None:
            continue
        bp.set(x, 1, z, log("spruce_log"))
        bp.set(x, 2, z, slab("spruce_slab", "bottom"))
    for z in range(17, 21):
        bp.set(13, 1, z, log("spruce_log", "z"))
        bp.set(14, 1, z, log("spruce_log", "z"))
        if z < 20:
            bp.set(13, 2, z, log("spruce_log", "z"))
    for x, z, h in ((-24, -6, 11), (23, -6, 9), (-12, -24, 12), (16, 20, 8), (-19, 20, 10), (24, 14, 8)):
        arch.spruce(bp, x, 1, z, h=h, seed=x * z)
    for x, z in ((-21, 4), (20, 2), (-6, -21), (9, 21), (-8, 22)):
        arch.bush(bp, x, 1, z, leaves="spruce_leaves", r=1)
    skirt(bp, 0, depth=5, spread=3, seed=9)
    scatter_plants(bp, -30, -30, 30, 30, 1, 0.25, 6, FLOWERS + ["fern", "fern"])
    # bandits' clutter: crates of stolen goods, bedrolls, hay, woodpiles (a hostile camp: no villagers)
    I.decorate(bp, "camp", seed=1, sky_ok=False)
    I.yard(bp, (-22, -22, 22, 22), 1, "camp", count=7, seed=1)


register(StructureDef(
    "bandit_camp", "overworld", ["plains", "savanna", "#minecraft:is_taiga", "sparse_jungle", "meadow"],
    [Piece("camp", bandit_camp)], spacing=26, separation=9, processors="none",
    spawns=[("minecraft:pillager", 10, 1, 3), ("brasshaven:bandit_marksman", 8, 1, 2)],
    creatures=[("bandit_marksman", 3)],
    title_fr="Campement de bandits", title_en="Bandit Camp"))


# ============================================================ 3. Rune circle (henge + crypt)
RC_STONE = Palette({"stone": 4, "tuff": 3, "andesite": 2, "mossy_cobblestone": 1, "cobblestone": 1}, seed=21, scale=2.2)
RC_LINTEL = Palette({"tuff_bricks": 3, "stone": 2, "tuff": 2, "mossy_stone_bricks": 1}, seed=22, scale=2.5)
RUNE = "brasshaven:carved_guild_stone"
RUNE_LAMP = "brasshaven:rune_lamp"


def _oriented_box(bp, ang, r, hu, hv, y0, y1, spec, taper=0.0, rng=None):
    """Upright stone block centred at angle/radius: hu = half width along the tangent, hv = half depth
    along the radius. `taper` narrows the top. Returns the set of (x, z) cells covered at y0."""
    a = math.radians(ang)
    cx, cz = math.cos(a) * r, math.sin(a) * r
    pal = arch.as_pal(spec)
    cells = set()
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        hu_y = hu - taper * t
        for x in range(math.floor(cx - hu - hv - 1), math.ceil(cx + hu + hv + 2)):
            for z in range(math.floor(cz - hu - hv - 1), math.ceil(cz + hu + hv + 2)):
                u = (x - cx) * -math.sin(a) + (z - cz) * math.cos(a)
                v = (x - cx) * math.cos(a) + (z - cz) * math.sin(a)
                if abs(u) <= hu_y + 0.01 and abs(v) <= hv + 0.01:
                    bp.set(x, y, z, pal.pick(x, y, z))
                    if y == y0:
                        cells.add((x, z))
    return cells


def _inner_face(ang, r, y, cells):
    """The cell of a stone closest to the centre (for runes / lamps)."""
    return min(cells, key=lambda c: (math.hypot(c[0], c[1]), abs(math.degrees(math.atan2(c[1], c[0])) - ang)))


def rune_circle(bp):
    rng = random.Random(23)
    # ---- ground: meadow, processional ring and southern avenue
    ground_patch(bp, 0, 2, 22, 24, seed=31, top=Palette({"grass_block[snowy=false]": 9, "moss_block": 2,
                                                         "coarse_dirt": 1}, seed=3, scale=3))
    for x, z in ring_cells(0, 0, 11.6, 13.4):
        bp.set(x, 0, z, rng.choice(["gravel", "coarse_dirt", "mossy_cobblestone", "dirt_path", "dirt_path"]))
    path_line(bp, [(0, 13), (0, 25)], 0, Palette({"dirt_path": 3, "gravel": 1, "coarse_dirt": 1}, seed=5),
              width=3, seed=4)
    for z in range(17, 26, 3):
        for x in (-4, 4):
            h = rng.randint(1, 3)
            for y in range(-1, h + 1):
                bp.set(x, y, z, RC_STONE.pick(x, y, z))
            bp.set(x, h + 1, z, "moss_carpet")

    # ---- outer sarsen ring: 24 uprights with a curved lintel ring
    R_OUT, H_OUT = 15, 6
    n = 24
    fallen = {5, 13, 19}
    no_lintel = {4, 5, 12, 13, 18, 19, 20}
    for i in range(n):
        ang = i * 360 / n + 7.5
        if i in fallen:
            # toppled stone lying outward
            a = math.radians(ang)
            for k in range(2, 8):
                for w in (-0.5, 0.5):
                    x = round(math.cos(a) * (R_OUT + k) - math.sin(a) * w)
                    z = round(math.sin(a) * (R_OUT + k) + math.cos(a) * w)
                    bp.set(x, 1, z, RC_STONE.pick(x, 1, z))
                    bp.set(x, 0, z, "stone")
            continue
        cells = _oriented_box(bp, ang, R_OUT, 1.1, 0.8, -3, H_OUT, RC_STONE, taper=0.2)
        fx, fz = _inner_face(ang, R_OUT, 2, cells)
        if i % 4 == 0:
            bp.set(fx, 3, fz, RUNE_LAMP)
        elif i % 4 == 2:
            bp.set(fx, 2, fz, RUNE)
    for i in range(n):
        if i in no_lintel or (i + 1) % n in no_lintel:
            continue
        a0 = i * 360 / n + 7.5 - 4.5
        a1 = (i + 1) * 360 / n + 7.5 + 4.5
        for x, z in ring_cells(0, 0, R_OUT - 0.75, R_OUT + 0.75):
            a = math.degrees(math.atan2(z, x)) % 360
            if a0 % 360 <= a <= a1 % 360 or (a1 % 360 < a0 % 360 and (a >= a0 % 360 or a <= a1 % 360)):
                bp.set(x, H_OUT + 1, z, RC_LINTEL.pick(x, H_OUT + 1, z))
    # a broken lintel leaning against its stone
    a = math.radians(4.5 * 15 + 7.5)
    for k in range(5):
        x = round(math.cos(a) * (R_OUT - 2 - k * 0.4) - math.sin(a) * (k - 2))
        z = round(math.sin(a) * (R_OUT - 2 - k * 0.4) + math.cos(a) * (k - 2))
        bp.set(x, 1 + k // 2, z, RC_LINTEL.pick(x, 1, z))

    # ---- bluestone ring: small dressed stones with runes
    for i in range(16):
        ang = i * 22.5 + 11
        if 80 < ang < 100:
            continue
        h = 2 if i % 2 else 3
        cells = _oriented_box(bp, ang, 11.5, 0.6, 0.5, -1, h, Palette({"tuff": 2, "polished_tuff": 1, "andesite": 1},
                                                                     seed=i))
        if i % 4 == 0:
            fx, fz = _inner_face(ang, 11.5, 1, cells)
            bp.set(fx, h, fz, RUNE)

    # ---- inner horseshoe of five great trilithons (opening south)
    tri = [(270, 13), (228, 11), (312, 11), (188, 9), (352, 9)]
    for ang, h in tri:
        a = math.radians(ang)
        tx, tz = -math.sin(a), math.cos(a)
        cx, cz = math.cos(a) * 9.5, math.sin(a) * 9.5
        for side in (-1.6, 1.6):
            sx, sz = cx + tx * side, cz + tz * side
            sang = math.degrees(math.atan2(sz, sx))
            sr = math.hypot(sx, sz)
            cells = _oriented_box(bp, sang, sr, 1.1, 1.2, -3, h, RC_STONE, taper=0.3)
            fx, fz = _inner_face(sang, sr, 3, cells)
            bp.set(fx, 5, fz, RUNE_LAMP)
            bp.set(fx, 4, fz, RUNE)
        _oriented_box(bp, ang, 9.5, 3.4, 1.1, h + 1, h + 1, RC_LINTEL)
        # glowing tenon studs on top
        x, z = round(cx), round(cz)
        bp.set(x, h + 2, z, "moss_carpet")
    # ---- the stepped dais and altar
    dais = Palette({"polished_tuff": 3, "tuff_bricks": 2, "stone_bricks": 1}, seed=24, scale=2)
    for r, y, st in ((7, 1, "polished_tuff_stairs"), (5, 2, "tuff_brick_stairs"), (3, 3, "polished_tuff_stairs")):
        for yy in range(-2, y):
            for x, z in ring_cells(0, 0, -1, r + 0.5):
                bp.set(x, yy, z, dais.pick(x, yy, z), keep=yy < 0)
        for x, z in ring_cells(0, 0, -1, r - 0.5):
            bp.set(x, y, z, dais.pick(x, y, z))
        ring_stairs(bp, 0, y, 0, r, st, half="bottom")
    for x, z in ring_cells(0, 0, -1, 2.5):
        bp.set(x, 3, z, "brasshaven:polished_guild_stone" if (x + z) % 2 else "chiseled_tuff")
    # altar block with rune, crystal and candles
    bp.set(0, 4, 0, RUNE)
    bp.set(-1, 4, 0, stair("brasshaven:polished_guild_stone_stairs", "east"))
    bp.set(1, 4, 0, stair("brasshaven:polished_guild_stone_stairs", "west"))
    bp.set(0, 5, 0, "amethyst_cluster[facing=up,waterlogged=false]")
    for x, z in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bp.set(x, 4, z, f"candle[candles={2 + (x + z) % 2},lit=true,waterlogged=false]")
    bp.set(0, 4, -2, "lectern[facing=south,has_book=false,powered=false]")
    # rune pillars at the four diagonals of the dais
    for ang in (45, 135, 225, 315):
        x, z = at_angle(0, 0, ang, 6.4)
        bp.set(x, 1, z, "brasshaven:polished_guild_stone")
        bp.set(x, 2, z, "brasshaven:guild_brick_wall")
        bp.set(x, 3, z, "brasshaven:guild_brick_wall")
        bp.set(x, 4, z, RUNE_LAMP)
        bp.set(x, 5, z, slab("brasshaven:polished_guild_stone_slab"))

    # ---- the crypt: break the southern step of the dais to find the shaft
    cy = -11
    bp.room(-7, cy, -7, 7, cy + 7, 7, "deepslate_bricks", floor="deepslate_tiles", ceiling="deepslate_bricks")
    bp.fill(-8, cy - 1, -8, 8, cy + 8, 8, "stone", keep=True)
    for x in (-7, -3, 3, 7):
        for z in (-7, 7):
            for y in range(cy + 1, cy + 7):
                bp.set(x, y, z, "tuff_bricks")
    for z in (-3, 3):
        for x in (-7, 7):
            for y in range(cy + 1, cy + 7):
                bp.set(x, y, z, "tuff_bricks")
    for x in range(-6, 7):
        for z in range(-6, 7):
            if abs(x) == abs(z) or x == 0 or z == 0:
                bp.set(x, cy, z, "polished_deepslate")
    # vaulted ceiling: corbel rings
    for x in range(-6, 7):
        for z in (-6, 6):
            bp.set(x, cy + 6, z, stair("deepslate_brick_stairs", "north" if z < 0 else "south", "top"))
    for z in range(-5, 6):
        for x in (-6, 6):
            bp.set(x, cy + 6, z, stair("deepslate_brick_stairs", "west" if x < 0 else "east", "top"))
    for x in range(-5, 6):
        bp.set(x, cy + 6, 0, "polished_deepslate")
    # shaft + ladder under the south step
    for y in range(cy + 1, 1):
        bp.set(0, y, 7, "air")
        bp.set(0, y, 8, "deepslate_bricks" if y < cy + 8 else "stone")
        bp.set(0, y, 7, "ladder[facing=north,waterlogged=false]")
    bp.set(0, 1, 7, stair("polished_tuff_stairs", "north"))
    # central sarcophagus + guardian spawner + reliquary chest
    bp.fill(-1, cy + 1, -3, 1, cy + 1, 1, "polished_deepslate")
    bp.fill(-1, cy + 2, -3, 1, cy + 2, 1, slab("polished_deepslate_slab"))
    bp.set(0, cy + 2, -3, "skeleton_skull[rotation=8]")
    bp.set(0, cy + 2, -1, RUNE)
    bp.chest(0, cy + 1, -6, "south", LOOT + "rune_circle")
    bp.spawner(0, cy + 1, 3, MOB["ruin_walker"])
    # burial niches with skulls and candles in the side walls
    for z in (-5, -1, 1, 5):
        for x in (-7, 7):
            if abs(z) == 1:
                continue
            bp.set(x, cy + 2, z, "air")
            bp.set(x, cy + 3, z, "air")
            bp.set(x, cy + 2, z, "skeleton_skull[rotation=4]" if x < 0 else "skeleton_skull[rotation=12]")
            bp.set(x, cy + 3, z, "candle[candles=1,lit=true,waterlogged=false]")
            bp.set(x + (1 if x < 0 else -1), cy + 1, z, "polished_deepslate_slab[type=bottom,waterlogged=false]")
    for x, z in ((-7, 0), (7, 0)):
        bp.set(x, cy + 3, z, RUNE_LAMP)
        bp.set(x, cy + 2, z, RUNE)
        bp.set(x, cy + 4, z, RUNE)
    bp.barrel(-5, cy + 1, -5, "up", LOOT + "rune_circle")
    bp.set(5, cy + 1, -5, "decorated_pot[facing=south,waterlogged=false,cracked=true]")
    bp.set(5, cy + 1, 5, "cobweb")
    bp.set(-5, cy + 5, 4, "cobweb")
    arch.hanging_lantern(bp, -3, cy + 5, -3, chain=1, soul=True)
    arch.hanging_lantern(bp, 3, cy + 5, 3, chain=1, soul=True)

    # ---- nature: moss on stones, lichen, flowers, a lone hawthorn
    arch.moss_on(bp, ((-30, 0, -30), (30, 20, 30)), chance=0.18, seed=5,
                 mapping={"minecraft:stone": "mossy_cobblestone", "minecraft:cobblestone": "mossy_cobblestone",
                          "minecraft:tuff_bricks": "mossy_stone_bricks", "minecraft:andesite": "mossy_cobblestone"})
    for (x, y, z), b in list(bp.blocks.items()):
        if y >= 2 and b[0] in ("minecraft:stone", "minecraft:tuff", "minecraft:mossy_cobblestone", "minecraft:andesite",
                               "minecraft:tuff_bricks", "minecraft:mossy_stone_bricks") \
                and bp.get(x, y + 1, z) is None and rng.random() < 0.3:
            bp.set(x, y + 1, z, rng.choice(["moss_carpet", "moss_carpet", "short_grass"]))
    arch.vines_on(bp, ((-30, 2, -30), (30, 14, 30)), chance=0.015, seed=6, max_len=4)
    arch.big_oak(bp, -20, 1, -13, h=7, seed=8, crown=4)
    arch.bush(bp, 18, 1, -10, leaves="azalea_leaves", r=1)
    arch.bush(bp, -17, 1, 12, leaves="flowering_azalea_leaves", r=1)
    arch.boulder(bp, 19, 1, 9, r=2, seed=3)
    skirt(bp, 0, depth=5, spread=3, seed=12)
    scatter_plants(bp, -26, -26, 26, 28, 1, 0.3, 9,
                   FLOWERS + ["allium", "lily_of_the_valley", "pink_petals[facing=east,flower_amount=4]",
                              "wildflowers[facing=north,flower_amount=3]", "red_mushroom", "brown_mushroom"])
    lair_rune_colossus.build(bp)     # rune well, gallery of guardians, grace and the rune vault (y -30)
    I.decorate(bp, "crypt", seed=1, loot=LOOT + "rune_circle")
    # the rune wardens: two clerics who tend the stones live in a lodge on the meadow, door towards the circle
    site = residents.free_site(bp, (-24, -24, 24, 26), 0, 7, 5, margin=1)
    if site is None:
        raise ValueError("rune_circle: no room for the wardens' lodge")
    lx, lz = site
    door = "west" if lx > 0 else "east"
    lodge_r = residents.lodge(bp, lx, 0, lz, door=door, w=7, d=5, wood="spruce", residents_=[("cleric", 3), ("cleric", 2)],
                              vtype="plains", seed=1, bed_colour="white")
    I.decorate(bp, "home", seed=2, region=lodge_r)


register(StructureDef(
    "rune_circle", "overworld",
    ["plains", "meadow", "#minecraft:is_taiga", "windswept_hills", "cherry_grove", "sunflower_plains",
     "snowy_plains"],
    [Piece("circle", rune_circle)], spacing=22, separation=7, processors="none", peaceful=True,
    title_fr="Cercle de pierres runiques", title_en="Rune Circle"))


# ============================================================ 4. Ice observatory (polar research outpost)
IO_DRUM = Palette({"deepslate_bricks": 5, "polished_deepslate": 2, "cracked_deepslate_bricks": 1}, seed=41, scale=2.5)
IO_DOME = Palette({"snow_block": 7, "white_concrete": 2, "calcite": 1}, seed=42, scale=3.0)
IO_SNOW = Palette({"snow_block": 7, "grass_block[snowy=true]": 2, "packed_ice": 1}, seed=43, scale=3.5)


def snowy_roofs(bp, region, seed=0, chance=0.7):
    """Drifted snow on sloped roofs: exposed wooden roof stairs/slabs turn into white quartz ones."""
    rng = random.Random(seed)
    (x0, y0, z0), (x1, y1, z1) = region
    for (x, y, z), (name, props, data) in list(bp.blocks.items()):
        if not (x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1):
            continue
        if name in ("minecraft:spruce_stairs", "minecraft:dark_oak_stairs") and props.get("half", "bottom") == "bottom" \
                and bp.get(x, y + 1, z) in (None, "minecraft:air") and ((x * 3 + z * 5 + y) % 7 or rng.random() < chance):
            bp.blocks[(x, y, z)] = ("minecraft:smooth_quartz_stairs", dict(props), data)
        elif name == "minecraft:spruce_slab" and props.get("type") == "bottom" and bp.get(x, y + 1, z) is None:
            bp.blocks[(x, y, z)] = ("minecraft:smooth_quartz_slab", dict(props), data)


def _io_hut(bp, x0, z0, w, d, door, rng, kind):
    """Timber research hut on a stone plinth: log frame, plank infill, steep snowy roof, stove chimney."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    bp.fill(x0 - 1, -3, z0 - 1, x1 + 1, 0, z1 + 1, "cobblestone", keep=True)
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            bp.set(x, 0, z, "stone_bricks" if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1) else "spruce_planks")
    for y in range(1, 5):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                post = corner or (edge and ((x - x0) % 3 == 0 if z in (z0, z1) else (z - z0) % 3 == 0))
                if post:
                    bp.set(x, y, z, log("dark_oak_log"))
                elif edge:
                    bp.set(x, y, z, "spruce_planks" if y != 4 else log("stripped_spruce_log", "x" if z in (z0, z1) else "z"))
                else:
                    bp.set(x, y, z, "air")
    # windows with shutters
    for x in range(x0 + 1, x1, 3):
        for z, f in ((z0, "north"), (z1, "south")):
            if bp.get(x, 2, z) == "minecraft:spruce_planks" and bp.get(x + 1, 2, z) == "minecraft:spruce_planks":
                bp.set(x + 1, 2, z, "glass_pane")
                bp.set(x + 1, 3, z, "glass_pane")
                oz = -1 if f == "north" else 1
                bp.set(x + 1, 1, z + oz, stair("spruce_stairs", OPPOSITE[f], "top"))
    for z in range(z0 + 1, z1, 3):
        for x, f in ((x0, "west"), (x1, "east")):
            if bp.get(x, 2, z + 1) == "minecraft:spruce_planks":
                bp.set(x, 2, z + 1, "glass_pane")
                bp.set(x, 3, z + 1, "glass_pane")
    # roof along x, snow on top later
    arch.steep_roof(bp, x0, z0, x1, z1, 5, "spruce_stairs", axis="x", overhang=1, fill="spruce_planks",
                    under="dark_oak_stairs", ridge=slab("spruce_slab"))
    bp.fill(x0 + 1, 5, z0 + 1, x1 - 1, 5, z1 - 1, "air")
    # door
    if door == "south":
        dx = (x0 + x1) // 2
        bp.door(dx, 1, z1, "south", "spruce")
        bp.set(dx, 0, z1 + 1, "spruce_planks")
        bp.set(dx, 0, z1 + 2, stair("spruce_stairs", "north"))
        bp.set(dx - 1, 3, z1 + 1, "lantern[hanging=false,waterlogged=false]")
        bp.set(dx - 1, 2, z1 + 1, "spruce_fence")
        bp.set(dx - 1, 1, z1 + 1, "spruce_fence")
    # stove + chimney
    cx = x1 - 1
    bp.set(cx, 1, z0 + 1, "blast_furnace[facing=south,lit=true]")
    for y in range(2, 11):
        bp.set(cx, y, z0, "bricks")
    bp.set(cx, 11, z0, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.set(cx, 2, z0 + 1, "bricks")
    bp.set(cx, 3, z0 + 1, "bricks")
    bp.lantern((x0 + x1) // 2, 4, (z0 + z1) // 2, hanging=True)
    if kind == "bunk":
        bp.bed(x0 + 1, 1, z0 + 1, "south", "light_blue")
        bp.bed(x0 + 1, 3, z0 + 1, "south", "blue")
        bp.fill(x0 + 1, 2, z0 + 1, x0 + 1, 2, z0 + 2, slab("spruce_slab", "top"))
        bp.set(x0 + 2, 1, z0 + 1, "barrel[facing=up,open=false]")
        bp.chest(x0 + 1, 1, z1 - 1, "east", LOOT + "ice_observatory")
        bp.table(x1 - 2, 1, z1 - 1, "spruce_pressure_plate", "spruce_fence")
        bp.stairs(x1 - 3, 1, z1 - 1, "spruce_stairs", "east")
        bp.set(x1 - 1, 1, z1 - 1, "white_carpet")
    else:
        bp.set(x0 + 1, 1, z0 + 1, "cartography_table")
        bp.set(x0 + 2, 1, z0 + 1, "lectern[facing=south,has_book=false,powered=false]")
        bp.set(x0 + 3, 1, z0 + 1, "bookshelf")
        bp.set(x0 + 3, 2, z0 + 1, "bookshelf")
        bp.set(x0 + 1, 1, z1 - 1, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        bp.set(x0 + 2, 1, z1 - 1, "smithing_table")
        bp.barrel(x1 - 1, 1, z1 - 1, "up", LOOT + "ice_observatory")
        bp.set(x1 - 1, 2, z1 - 1, "barrel[facing=north,open=false]")


def _io_mast(bp, x0, z0, h):
    """Lattice radio mast: tapering iron frame, cross bracing, beacon lamp and lightning rod."""
    for y in range(1, h + 1):
        s = 2 if y < h * 0.4 else 1 if y < h * 0.8 else 0
        for x, z in ((x0 - s, z0 - s), (x0 + s, z0 - s), (x0 - s, z0 + s), (x0 + s, z0 + s)):
            bp.set(x, y, z, "iron_bars" if s else "polished_deepslate_wall")
        if s and y % 4 == 0:
            for k in range(-s, s + 1):
                for x, z in ((x0 + k, z0 - s), (x0 + k, z0 + s), (x0 - s, z0 + k), (x0 + s, z0 + k)):
                    bp.set(x, y, z, "iron_bars")
        if s == 2 and y % 4 == 2:
            bp.set(x0, y, z0 - 2, "iron_bars")
            bp.set(x0, y, z0 + 2, "iron_bars")
    for x in range(x0 - 2, x0 + 3):
        for z in range(z0 - 2, z0 + 3):
            bp.set(x, 0, z, "polished_deepslate")
    bp.set(x0, h + 1, z0, "redstone_lamp[lit=true]")
    bp.set(x0, h + 2, z0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(x0, h + 3, z0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for f, (dx, dz) in (("east", (1, 0)), ("west", (-1, 0)), ("north", (0, -1)), ("south", (0, 1))):
        bp.set(x0 + dx, h - 2, z0 + dz, f"lightning_rod[facing={f},powered=false,waterlogged=false]")
    # dish-like copper bulb array mid-height
    bp.set(x0 + 2, int(h * 0.55), z0, "copper_bulb[lit=true,powered=false]")
    bp.set(x0 - 2, int(h * 0.55), z0, "copper_bulb[lit=true,powered=false]")
    # equipment box at the foot
    bp.fill(x0 + 3, 1, z0 - 1, x0 + 4, 2, z0 + 1, "exposed_cut_copper")
    bp.set(x0 + 3, 3, z0, "lever[face=floor,facing=east,powered=false]")
    bp.set(x0 + 4, 1, z0 + 1, "iron_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")


def ice_observatory(bp):
    rng = random.Random(44)
    # ---- snowy ground, terrace and paths
    ground_patch(bp, 0, 2, 27, 24, seed=45, top=IO_SNOW)
    terrace = Palette({"stone_bricks": 4, "polished_andesite": 2, "cracked_stone_bricks": 1}, seed=46)
    for x, z in ring_cells(0, 0, -1, 12.5):
        bp.set(x, 0, z, terrace.pick(x, 0, z))
    ring_stairs(bp, 0, 0, 0, 13, "stone_brick_stairs", half="bottom")
    path_line(bp, [(0, 13), (0, 18), (-12, 20)], 0, Palette({"gravel": 2, "snow_block": 2, "light_gray_concrete_powder": 1}, seed=7),
              width=3, seed=5)
    path_line(bp, [(0, 18), (13, 21)], 0, Palette({"gravel": 2, "snow_block": 2, "light_gray_concrete_powder": 1}, seed=7),
              width=2, seed=6)
    path_line(bp, [(8, -8), (15, -14)], 0, Palette({"gravel": 1, "snow_block": 2}, seed=8), width=2, seed=7)

    # ---- the drum: dark deepslate with pilasters, windows, plinth and cornice
    R = 10
    DH = 8  # drum height
    for y in range(1, DH + 1):
        ring(bp, 0, y, 0, R - 1.5, R, IO_DRUM)
        for x, z in ring_cells(0, 0, -1, R - 1.5):
            bp.set(x, y, z, "air")
    ring_stairs(bp, 0, 1, 0, R + 1, "polished_deepslate_stairs", half="bottom")
    ring_stairs(bp, 0, DH, 0, R + 1, "polished_deepslate_stairs", half="top")
    ring(bp, 0, DH - 3, 0, R - 1.5, R, "polished_deepslate")
    for k in range(12):
        ang = k * 30
        x, z = at_angle(0, 0, ang, R + 0.7)
        for y in range(1, DH + 1):
            bp.set(x, y, z, "polished_deepslate")
        wa = ang + 15
        if 75 < wa < 105:
            continue
        radial_cut(bp, 0, 0, wa, 2, 4, R - 2, R + 0.4)
        radial_cut(bp, 0, 0, wa, 2, 4, R - 1, R - 1, spec="light_blue_stained_glass_pane")
        radial_cut(bp, 0, 0, wa, 6, 7, R - 2, R + 0.4)
        radial_cut(bp, 0, 0, wa, 6, 7, R - 1, R - 1, spec="light_blue_stained_glass_pane")
        x, z = at_angle(0, 0, wa, R + 0.6)
        bp.set(x, 1, z, stair("polished_deepslate_stairs", _toward(-x, -z), "top"))
    for x, z in ring_cells(0, 0, -1, R - 1.5):
        bp.set(x, 0, z, "spruce_planks" if (x * x + z * z) % 7 else "dark_oak_planks")

    # ---- the dome with blue-ice ribs and a copper-framed observation slit (north)
    DY = DH + 1
    arch.dome(bp, 0, DY, 0, R, IO_DOME, ribs="blue_ice", oculus=False, rib_count=8)
    for (x, y, z) in list(bp.blocks):
        if y >= DY + 2 and z <= 1 and bp.get(x, y, z) in ("minecraft:snow_block", "minecraft:packed_ice",
                                                    "minecraft:white_concrete", "minecraft:calcite",
                                                    "minecraft:blue_ice"):
            if abs(x) <= 1:
                bp.set(x, y, z, "air")
            elif abs(x) == 2:
                bp.set(x, y, z, "waxed_cut_copper")
    for x in (-1, 0, 1):
        bp.set(x, DY + R, 2, "waxed_cut_copper")
    bp.set(0, DY + R + 1, 2, "waxed_cut_copper")
    bp.set(0, DY + R + 2, 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ---- the great copper telescope on its pier
    for x, z in ring_cells(0, 0, -1, 3.5):
        bp.set(x, 1, z, "polished_deepslate")
    ring_stairs(bp, 0, 1, 0, 4, "polished_deepslate_stairs", half="bottom")
    bp.fill(-1, 2, 0, 1, 3, 2, "polished_deepslate")
    bp.set(0, 4, 1, "chiseled_copper")
    tube = []
    t = 0
    while True:
        y = 5 + t * 0.66
        z = 2 - t * 0.66
        tube.append((round(y), round(z)))
        if math.hypot(y - DY, z) > R + 3.5:
            break
        t += 1
    for i, (y, z) in enumerate(tube):
        for x in (-1, 0, 1):
            bp.set(x, y, z, "waxed_cut_copper" if i % 4 else "waxed_copper_block")
        bp.set(0, y + 1, z, "waxed_cut_copper")
        bp.set(0, y - 1, z, "waxed_cut_copper")
    ly, lz = tube[-1]
    bp.set(0, ly, lz - 1, "light_blue_stained_glass")
    for x in (-1, 1):
        bp.set(x, ly, lz - 1, "waxed_copper_block")
    bp.set(0, 5, 3, "waxed_copper_block")
    bp.set(0, 4, 3, "lever[face=floor,facing=south,powered=false]")
    bp.set(1, 6, 3, "lightning_rod[facing=east,powered=false,waterlogged=false]")

    # ---- observatory furnishings
    for ang in range(0, 360, 20):
        if 60 < ang < 120 or 240 < ang < 300:
            continue
        x, z = at_angle(0, 0, ang, R - 2)
        bp.set(x, 1, z, "bookshelf")
        bp.set(x, 2, z, "bookshelf" if ang % 40 else "chiseled_bookshelf[facing=north,slot_0_occupied=true,"
                                                       "slot_1_occupied=false,slot_2_occupied=true,slot_3_occupied=true,"
                                                       "slot_4_occupied=false,slot_5_occupied=true]")
    for x, z, f in ((-6, -3, "east"), (6, -3, "west")):
        bp.set(x, 1, z, "cartography_table")
        bp.set(x, 1, z + 1, f"lectern[facing={f},has_book=false,powered=false]")
        bp.stairs(x + (1 if f == "east" else -1), 1, z, "spruce_stairs", OPPOSITE[f])
    bp.chest(-6, 1, 3, "east", LOOT + "ice_observatory")
    bp.set(6, 1, 3, "smoker[facing=west,lit=true]")
    bp.set(6, 1, 4, "barrel[facing=up,open=false]")
    for x, z in ((-4, 4), (4, 4), (-4, -4), (4, -4)):
        arch.hanging_lantern(bp, x, DH - 1, z, chain=2)
    # gallery ring at the drum top with railing + ladder
    for x, z in ring_cells(0, 0, R - 3.5, R - 1.5):
        bp.set(x, DH - 1, z, slab("spruce_slab", "top"))
    for x, z in ring_cells(0, 0, R - 4.5, R - 3.5):
        if bp.get(x, DH, z) in (None, "minecraft:air"):
            bp.set(x, DH, z, "spruce_fence")
    bp.ladder(-7, 1, -4, DH - 1, "east")
    bp.set(-8, 1, -4, "polished_deepslate")
    for x in range(-7, -5):
        bp.set(x, DH, -4, "air")

    # ---- southern vestibule with a steep roof
    for z in range(8, 14):
        for x in range(-3, 4):
            edge = x in (-3, 3) or z == 13
            for y in range(1, 6):
                if edge:
                    bp.set(x, y, z, log("dark_oak_log") if (x in (-3, 3) and z in (8, 13)) or (y == 5) else "spruce_planks")
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, 0, z, "spruce_planks")
    arch.steep_roof(bp, -3, 8, 3, 13, 6, "spruce_stairs", axis="z", overhang=1, fill="spruce_planks",
                    under="dark_oak_stairs", ridge=slab("spruce_slab"))
    bp.fill(-2, 6, 8, 2, 6, 12, "air")
    for x in (-1, 0, 1):
        for y in (1, 2, 3):
            for z in (8, 9):
                bp.set(x, y, z, "air")
    bp.door(0, 1, 13, "south", "spruce")
    bp.set(-1, 3, 14, "lantern[hanging=false,waterlogged=false]")
    bp.set(-1, 2, 14, "spruce_fence")
    bp.set(-1, 1, 14, "spruce_fence")
    for x in (-3, 3):
        bp.set(x, 3, 11, "glass_pane")
        bp.set(x, 2, 11, "glass_pane")
    bp.set(-2, 1, 12, "barrel[facing=up,open=false]")
    bp.set(2, 1, 12, "spruce_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    bp.set(2, 1, 10, "lantern[hanging=false,waterlogged=false]")
    bp.set(0, 0, 14, stair("stone_brick_stairs", "north"))

    # ---- basement laboratory (hatch beside the pier)
    ly0 = -7
    bp.room(-7, ly0, -6, 7, -1, 6, "packed_ice", floor="polished_deepslate", ceiling="spruce_planks")
    bp.fill(-8, ly0 - 1, -7, 8, 0, 7, "stone", keep=True)
    for x in (-7, 7):
        for z in (-6, -2, 2, 6):
            for y in range(ly0 + 1, -1):
                bp.set(x, y, z, log("stripped_spruce_log"))
    for x in range(-6, 7):
        for z in range(-5, 6):
            if (x + z) % 2 == 0:
                bp.set(x, ly0, z, "blue_ice")
    bp.set(-5, 0, 4, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    bp.ladder(-5, ly0 + 1, 4, -1, "north")
    bp.fill(-5, ly0 + 1, 5, -5, -1, 5, "packed_ice")
    # specimen tanks: blue ice and a frozen creature in glass
    for x in (-3, 0, 3):
        bp.set(x, ly0 + 1, -5, "polished_deepslate")
        bp.set(x, ly0 + 2, -5, "light_blue_stained_glass")
        bp.set(x, ly0 + 3, -5, "light_blue_stained_glass")
        bp.set(x, ly0 + 4, -5, "polished_deepslate_slab[type=bottom,waterlogged=false]")
    bp.set(0, ly0 + 2, -5, "blue_ice")
    bp.set(-3, ly0 + 2, -5, "packed_ice")
    bp.set(3, ly0 + 2, -5, "snow_block")
    bp.bookshelf_wall(-6, ly0 + 1, 5, -2, ly0 + 2, 5, 0.1)
    bp.set(5, ly0 + 1, 5, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    bp.set(4, ly0 + 1, 5, "cauldron")
    bp.set(6, ly0 + 1, 5, "enchanting_table")
    bp.chest(6, ly0 + 1, 0, "west", LOOT + "ice_observatory_lab")
    bp.chest(6, ly0 + 1, -1, "west", LOOT + "ice_observatory")
    bp.set(6, ly0 + 1, 1, "barrel[facing=up,open=false]")
    for z in (-2, 2):
        bp.set(0, ly0 + 1, z, "spruce_fence")
        bp.set(0, ly0 + 2, z, "spruce_pressure_plate")
    bp.set(1, ly0 + 1, 2, "lectern[facing=west,has_book=false,powered=false]")
    bp.spawner(-3, ly0 + 1, 0, "minecraft:stray")
    bp.set(-6, ly0 + 1, -5, "powder_snow")
    bp.set(-6, ly0 + 1, -4, "powder_snow")
    for x, z in ((-3, -2), (3, 2)):
        bp.lantern(x, -2, z, hanging=True, soul=True)

    # ---- research huts
    _io_hut(bp, -20, 3, 9, 7, "south", rng, "bunk")
    _io_hut(bp, 12, 6, 8, 7, "south", rng, "lab")
    # ---- radio mast with its equipment box
    _io_mast(bp, 16, -15, 24)

    # ---- sled with crates, firewood and supply cache
    for x in range(-9, -4):
        bp.set(x, 1, 17, slab("spruce_slab", "bottom"))
        bp.set(x, 1, 19, slab("spruce_slab", "bottom"))
    for x in range(-9, -4):
        bp.set(x, 1, 18, slab("spruce_slab", "bottom"))
    bp.set(-4, 1, 17, "spruce_fence")
    bp.set(-4, 1, 19, "spruce_fence")
    bp.set(-4, 2, 17, "spruce_fence")
    bp.set(-4, 2, 19, "spruce_fence")
    bp.set(-4, 2, 18, "spruce_fence")
    bp.barrel(-8, 2, 18, "up", LOOT + "ice_observatory")
    bp.set(-7, 2, 18, "barrel[facing=east,open=false]")
    bp.set(-8, 2, 17, "white_carpet")
    bp.set(-6, 2, 18, "chest[facing=south,type=single,waterlogged=false]")
    for x, z in ((-23, 12), (-22, 12), (-23, 13)):
        bp.set(x, 1, z, log("spruce_log", "z"))
    bp.set(-22, 2, 12, log("spruce_log", "z"))
    for x, z in ((19, 14), (20, 14), (19, 15)):
        bp.barrel(x, 1, z, "up")
    bp.set(19, 2, 14, "barrel[facing=north,open=false]")
    # ---- lamp posts along the path
    for x, z in ((3, 15), (-6, 20), (10, 20), (-3, 15)):
        for y in (1, 2, 3):
            bp.set(x, y, z, "spruce_fence")
        bp.lantern(x, 4, z)

    # ---- landscape: snowy spruces, ice spikes, drifts
    for x, z, h in ((-24, -8, 12), (-18, -17, 9), (22, 4, 10), (-25, 4, 8), (6, -22, 11), (-8, -21, 8)):
        arch.spruce(bp, x, 1, z, h=h, seed=x + z)
    for x, z, h in ((23, -4, 8), (-14, -13, 6)):
        for y in range(1, h + 1):
            bp.set(x, y, z, "packed_ice")
            if y < h - 2:
                for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    bp.set(x + dx, y, z + dz, "packed_ice")
        bp.set(x, h + 1, z, "packed_ice")
    skirt(bp, 0, depth=6, spread=3, seed=13, top="snow_block", soil="dirt", rock="stone",
          rubble=("packed_ice", "stone", "andesite"))
    snow_cover(bp, ((-40, 1, -40), (40, 40, 40)), seed=3, chance=0.8)
    snowy_roofs(bp, ((-40, 1, -40), (40, 40, 40)), seed=4)
    for x, z in ring_cells(0, 0, -1, R - 1.5):
        if bp.get(x, 1, z) == "minecraft:snow":
            bp.remove(x, 1, z)
    # ---- the wintering scholars: an astronomer-cartographer, a librarian, a cleric brewing in the lab
    # (on the surface: the cellar lab below keeps its stray spawner)
    I.populate(bp, [("cartographer", 3), "librarian", "cleric", "fletcher"], region=((-60, 1, -60), (60, 60, 60)),
               vtype="snow", seed=1)
    I.decorate(bp, dict(I.THEMES["lab"], rugs=["light_blue", "white", "blue"]), seed=1, region=((-60, -30, -60),
                                                                                                (60, 0, 60)))
    I.decorate(bp, dict(I.THEMES["home"], rugs=["light_blue", "white", "gray"]), seed=2)


register(StructureDef(
    "ice_observatory", "overworld",
    ["snowy_plains", "ice_spikes", "snowy_taiga", "grove", "snowy_slopes", "frozen_peaks"],
    [Piece("observatory", ice_observatory)], spacing=28, separation=9, processors="none", peaceful=True,
    title_fr="Observatoire polaire", title_en="Ice Observatory"))


# ============================================================ 5. Galleon wreck (ocean floor)
GL_L = 46          # hull length (stern z=0 -> bow z=GL_L)
GL_W = 8.2         # max half-beam
GL_DECKS = {"hold": 1, "gun": 5, "main": 9, "fore": 12, "quarter": 13, "poop": 17}
GL_LOW = Palette({"dark_oak_planks": 6, "spruce_planks": 1}, seed=51, scale=2.2)
GL_MID = Palette({"spruce_planks": 4, "dark_oak_planks": 1}, seed=52, scale=2.5)
CORALS = ("tube", "brain", "bubble", "fire", "horn")


def _gl_plan(z):
    if z < 0 or z > GL_L:
        return 0.0
    if z < 14:
        return 0.78 + 0.22 * math.sin(math.pi / 2 * z / 14)
    t = (z - 14) / (GL_L - 14)
    return max(0.0, math.cos(math.pi / 2 * t ** 1.3))


def _gl_section(y):
    if y <= 0:
        return 0.15
    if y <= 8:
        return min(1.0, 0.22 + 0.78 * math.sqrt(y / 8))
    if y <= 11:
        return 1.0
    return 1.0 - (y - 11) * 0.05


def _gl_top(z):
    if z <= 6:
        return 19
    if z <= 13:
        return 15
    if z >= 36:
        return 13 + (1 if z > 41 else 0)
    if z >= 28:
        return 11 + (1 if z > 32 else 0)
    return 11


def _gl_inside(x, y, z):
    if not (0 <= z <= GL_L) or y < 0 or y > _gl_top(z):
        return False
    w = GL_W * _gl_plan(z) * _gl_section(y)
    return abs(x) <= w + 0.45


def _gl_outer_x(y, z, side):
    xs = [x for x in range(-10, 11) if _gl_inside(x, y, z) and (x > 0) == (side > 0) and x != 0]
    return max(xs, key=abs) if xs else None


def _gl_sail(s, rng, x0, x1, y_top, y_bot, z):
    for x in range(x0, x1 + 1):
        bottom = y_bot + (1 if rng.random() < 0.35 else 0) + (1 if abs(x - (x0 + x1) / 2) > (x1 - x0) / 2 - 1 else 0)
        for y in range(bottom, y_top + 1):
            if rng.random() < 0.8:
                s.set(x, y, z, "white_wool" if rng.random() < 0.75 else "light_gray_wool")


def _gl_ship(rng):
    s = Blueprint("galleon_ship")
    # ---- hull shell, by bands: dark lower hull, lighter gun-deck band, wales, dark bulwarks
    for z in range(-1, GL_L + 2):
        for y in range(0, 21):
            for x in range(-10, 11):
                if not _gl_inside(x, y, z):
                    continue
                shell = not all(_gl_inside(x + dx, y + dy, z + dz)
                                for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)))
                if shell:
                    if y in (4, 8):
                        spec = log("stripped_dark_oak_log", "z")
                    elif 5 <= y <= 7:
                        spec = GL_MID.pick(x, y, z)
                    else:
                        spec = GL_LOW.pick(x, y, z)
                    s.set(x, y, z, spec)
                else:
                    s.set(x, y, z, "air")
    # protruding wales (rub rails) for depth
    for z in range(1, GL_L):
        for y in (4, 8):
            for side in (-1, 1):
                xo = _gl_outer_x(y, z, side)
                if xo is not None and abs(xo) >= 2:
                    s.set(xo + side, y, z, stair("dark_oak_stairs", "west" if side > 0 else "east", "top"))
    # keel + rudder + stern post
    for z in range(-1, GL_L + 1):
        s.set(0, -1, z, log("dark_oak_log", "z"))
    for y in range(0, 12):
        s.set(0, y, -1, "dark_oak_planks")
    s.set(0, 12, -1, slab("dark_oak_slab"))
    # ---- decks
    def deck(y, z0, z1, spec="spruce_planks"):
        for z in range(z0, z1 + 1):
            for x in range(-10, 11):
                if _gl_inside(x, y, z) and s.get(x, y, z) == "minecraft:air":
                    s.set(x, y, z, spec)
    deck(GL_DECKS["gun"], 1, GL_L - 3)
    deck(GL_DECKS["main"], 0, GL_L - 1)
    deck(GL_DECKS["quarter"], 0, 13)
    deck(GL_DECKS["poop"], 0, 6, "dark_oak_planks")
    deck(GL_DECKS["fore"], 36, GL_L)
    # deck planking seams + hatches
    for z in range(16, 34, 6):
        for x in (-1, 0, 1):
            s.set(x, 9, z, "dark_oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
            s.set(x, 5, z + 2, "air")
    # rails on top of every bulwark
    for z in range(0, GL_L + 1):
        t = _gl_top(z)
        for side in (-1, 1):
            xo = _gl_outer_x(t, z, side)
            if xo is not None:
                s.set(xo, t + 1, z, "dark_oak_fence")
    # ---- bulkheads: stern castle front, poop front, forecastle back (with doors and windows)
    for y in range(10, 13):
        for x in range(-7, 8):
            if _gl_inside(x, y, 14):
                s.set(x, y, 14, "dark_oak_planks" if abs(x) % 3 else log("stripped_dark_oak_log"))
    for x in (-1, 0):
        s.set(x, 10, 14, "air")
        s.set(x, 11, 14, "air")
    for x in (-4, 3):
        s.set(x, 11, 14, "glass_pane")
    for y in range(14, 17):
        for x in range(-6, 7):
            if _gl_inside(x, y, 7):
                s.set(x, y, 7, "dark_oak_planks" if abs(x) % 3 else log("stripped_dark_oak_log"))
    s.set(0, 14, 7, "air")
    s.set(0, 15, 7, "air")
    for x in (-3, 3):
        s.set(x, 15, 7, "glass_pane")
    for y in range(10, 12):
        for x in range(-6, 7):
            if _gl_inside(x, y, 36):
                s.set(x, y, 36, "dark_oak_planks")
    s.set(0, 10, 36, "air")
    s.set(0, 11, 36, "air")
    # stair from main deck to quarterdeck
    for k in range(4):
        s.set(-5, 10 + k, 15 + k, stair("dark_oak_stairs", "north"))
    # ---- stern: transom windows, gilded trim, gallery balcony, lanterns
    for y in (10, 11, 14, 15):
        for x in range(-5, 6, 2):
            if s.get(x, y, 0) and _gl_inside(x, y, 0):
                s.set(x, y, 0, "glass_pane")
    for x in range(-6, 7):
        if _gl_inside(x, 13, 0):
            s.set(x, 13, -1, slab("dark_oak_slab", "top"))
            s.set(x, 14, -1, "dark_oak_fence")
        s.set(x, 17, -1, stair("dark_oak_stairs", "south", "top"))
    for x in (-6, 6):
        s.set(x, 18, 0, "gold_block")
    for y in range(12, 19):
        s.set(0, y, -1, log("stripped_dark_oak_log") if y != 16 else "gold_block")
    for x in (-5, 5):
        s.set(x, 20, 1, "dark_oak_fence")
        s.set(x, 21, 1, "lantern[hanging=false,waterlogged=false]")
    # quarter galleries (bay windows on both sides of the stern)
    for side in (-1, 1):
        for z in range(2, 6):
            for y in range(13, 17):
                xo = _gl_outer_x(y, z, side)
                if xo is None:
                    continue
                s.set(xo + side, y, z, "glass_pane" if y in (14, 15) and z in (3, 4) else "dark_oak_planks")
            s.set((_gl_outer_x(13, z, side) or 0) + side, 12, z,
                  stair("dark_oak_stairs", "west" if side > 0 else "east", "top"))
    # ---- gun ports with anvil cannons (gun deck) + deck guns
    for z in range(11, 37, 4):
        for side in (-1, 1):
            xo = _gl_outer_x(6, z, side)
            if xo is None:
                continue
            s.set(xo, 6, z, "air")
            s.set(xo - side, 6, z, "anvil[facing=north]")
            s.set(xo, 7, z, log("stripped_dark_oak_log", "z"))
    for z in (18, 26, 31):
        for side in (-1, 1):
            xo = _gl_outer_x(10, z, side)
            if xo is None:
                continue
            s.set(xo, 10, z, "air")
            s.set(xo - side, 10, z, "anvil[facing=north]")
            s.set(xo - 2 * side, 10, z, "dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    # ---- masts, yards and torn sails
    masts = [(9, 33, [(22, 5), (29, 4)]), (38, 39, [(20, 7), (28, 6), (35, 4)])]
    for mz, top, yards in masts:
        for y in range(0, top + 1):
            s.set(0, y, mz, log("stripped_dark_oak_log"))
        for yy, half in yards:
            for x in range(-half, half + 1):
                s.set(x, yy, mz, log("spruce_log", "x"))
            _gl_sail(s, rng, -half + 1, half - 1, yy - 1, yy - (7 if half > 5 else 5), mz + 1)
        s.set(0, top + 1, mz, "spruce_fence")
    # crow's nest on the foremast
    for x in range(-1, 2):
        for z in range(37, 40):
            s.set(x, 30, z, slab("spruce_slab", "top") if (x, z) != (0, 38) else log("stripped_dark_oak_log"))
    for x in range(-2, 3):
        for z in range(36, 41):
            if abs(x) == 2 or z in (36, 40):
                s.set(x, 31, z, "spruce_fence")
                s.set(x, 30, z, slab("spruce_slab", "top"))
    # main mast stump, splintered
    for y in range(0, 15):
        s.set(0, y, 24, log("stripped_dark_oak_log"))
    s.set(1, 15, 24, log("stripped_dark_oak_log"))
    s.set(0, 15, 24, "spruce_fence")
    # bowsprit + jib
    s.line((0, 13, GL_L - 2), (0, 18, GL_L + 7), log("stripped_dark_oak_log", "z"))
    for k in range(1, 5):
        for y in range(13 + k, 13 + k + 3):
            if rng.random() < 0.7:
                s.set(0, y - 2, GL_L - 2 + k * 2, "white_wool")
    s.set(0, 9, GL_L + 1, "gold_block")
    s.set(0, 10, GL_L + 1, log("dark_oak_log", "z"))
    # ---- captain's cabin (quarterdeck level, z 1..6)
    s.chest(-4, 14, 2, "east", LOOT + "galleon_captain")
    s.set(4, 14, 2, "cartography_table")
    s.set(3, 14, 2, "lectern[facing=west,has_book=false,powered=false]")
    s.bed(-4, 14, 4, "east", "red")
    s.table(0, 14, 3, "dark_oak_pressure_plate", "dark_oak_fence")
    s.stairs(1, 14, 3, "dark_oak_stairs", "west")
    s.set(0, 14, 5, "red_carpet")
    s.set(-1, 14, 5, "red_carpet")
    arch.chandelier(s, 0, 16, 3)
    # officers' mess under it (main deck level)
    s.table(-2, 10, 8, "spruce_pressure_plate", "spruce_fence")
    s.table(2, 10, 8, "spruce_pressure_plate", "spruce_fence")
    s.set(4, 10, 5, "barrel[facing=up,open=false]")
    s.bed(-5, 10, 4, "south", "blue")
    # ---- cargo hold: barrels, crates, gold, drowned spawner
    for z in range(15, 33, 3):
        for side in (-1, 1):
            xo = _gl_outer_x(2, z, side)
            if xo is None:
                continue
            s.barrel(xo - side, 1, z, "up", LOOT + "galleon_cargo" if z in (21, 27) and side < 0 else None)
            if rng.random() < 0.6:
                s.barrel(xo - side, 2, z, "north")
            s.barrel(xo - 2 * side, 1, z, "up")
    s.chest(0, 1, 30, "south", LOOT + "galleon_cargo")
    s.chest(0, 1, 12, "north", LOOT + "galleon_cargo")
    for x, z in ((-1, 20), (1, 21), (0, 19)):
        s.set(x, 1, z, "gold_block")
    s.set(0, 2, 20, "raw_gold_block")
    s.spawner(0, 1, 25, "minecraft:drowned")
    s.spawner(0, 6, 16, "minecraft:drowned")
    for y in range(1, 5):
        s.set(-2, y, 34, "ladder[facing=south,waterlogged=false]")
        s.set(-2, y + 4, 34, "ladder[facing=south,waterlogged=false]")
    for y in range(1, 9):
        s.set(-2, y, 33, "spruce_planks")
    s.set(-2, 5, 34, "ladder[facing=south,waterlogged=false]")
    s.set(-2, 9, 34, "air")
    for z in (12, 20, 28, 34):
        s.lantern(3, 4, z, hanging=True)
        s.lantern(-3, 8, z, hanging=True)
    return s


def galleon(bp):
    bp.underwater = True
    rng = random.Random(55)
    ship = _gl_ship(rng)
    # ---- damage: a torn breach on the starboard side, a caved-in deck
    for (x, y, z) in list(ship.blocks):
        if x > 0 and 16 <= z <= 25 and y <= 8:
            d = ((z - 20.5) / 4.8) ** 2 + ((y - 3.5) / 4.2) ** 2
            if d < 1 + rng.uniform(-0.25, 0.15) and x >= 3:
                ship.set(x, y, z, "air")
        if 19 <= z <= 24 and y == 9 and rng.random() < 0.7:
            ship.set(x, y, z, "air")
    # open-air spaces above the decks stay unset (the sea fills them); enclosed spaces get water
    for (x, y, z), b in list(ship.blocks.items()):
        if b[0] == "minecraft:air" and all(ship.get(x, yy, z) in (None, "minecraft:air") for yy in range(y + 1, 42)):
            ship.remove(x, y, z)
    bp.paste(ship, 0, -2, 0)
    # ---- seabed: sand and gravel, silt drifted against and inside the hull
    bed = Palette({"sand": 6, "gravel": 2, "clay": 1}, seed=56, scale=3)
    ground_patch(bp, 4, 22, 26, 36, seed=57, top=bed)
    for (x, y, z), b in list(bp.blocks.items()):
        if y in (-2, -1) and b[0] in ("minecraft:air", "minecraft:water"):
            bp.set(x, y, z, "sand")
    for z in range(-2, GL_L + 2):
        for x in range(-11, 12):
            if bp.get(x, 0, z) is None and any(bp.get(x + dx, 0, z) not in (None, "minecraft:sand", "minecraft:gravel",
                                                                             "minecraft:clay")
                                                for dx in (-2, -1, 1, 2)):
                bp.set(x, 0, z, "sand")
    # ---- the fallen main mast lying on the seabed with its yard, sail and crow's nest
    bp.line((5, 1, 24), (27, 1, 33), log("stripped_dark_oak_log", "x"))
    bp.line((6, 1, 23), (16, 1, 27), log("stripped_dark_oak_log", "x"))
    bp.line((17, 1, 23), (12, 1, 36), log("spruce_log", "z"))
    for _ in range(45):
        t = rng.uniform(0.2, 0.9)
        x = round(17 + (12 - 17) * t + rng.randint(1, 4))
        z = round(23 + (36 - 23) * t + rng.randint(-1, 1))
        y = 1 if bp.get(x, 1, z) is None else 2
        bp.set(x, y, z, "white_wool" if rng.random() < 0.7 else "light_gray_wool")
    for x, z in ((24, 31), (25, 31), (26, 32), (24, 33), (25, 34), (26, 34)):
        bp.set(x, 2, z, "spruce_fence")
    bp.set(25, 1, 32, slab("spruce_slab"))
    # spilled cargo through the breach
    for x, z in ((9, 18), (11, 21), (10, 23), (13, 19), (8, 26)):
        bp.barrel(x, 1, z, rng.choice(["up", "east", "north"]))
    bp.chest(12, 1, 22, "west", LOOT + "galleon_cargo")
    bp.set(10, 1, 20, "gold_block")
    for x, z in ((14, 17), (12, 25), (9, 28)):
        bp.set(x, 1, z, rng.choice(["dark_oak_planks", "spruce_slab[type=bottom,waterlogged=false]"]))
    # ---- marine life: corals on the hull, fans, pickles, kelp forest, seagrass
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] in ("minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:stripped_dark_oak_wood") \
                and y <= 6 and rng.random() < 0.12:
            exposed = any(bp.get(x + dx, y, z + dz) is None for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if exposed:
                bp.set(x, y, z, f"{rng.choice(CORALS)}_coral_block")
    for (x, y, z), b in list(bp.blocks.items()):
        if y > 9 or not ("planks" in b[0] or "coral_block" in b[0]) or rng.random() > 0.08:
            continue
        for f, (dx, dz) in (("east", (1, 0)), ("west", (-1, 0)), ("south", (0, 1)), ("north", (0, -1))):
            if bp.get(x + dx, y, z + dz) is None:
                bp.set(x + dx, y, z + dz, f"{rng.choice(CORALS)}_coral_wall_fan[facing={f},waterlogged=true]")
                break
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] in ("minecraft:spruce_planks", "minecraft:dark_oak_planks") and bp.get(x, y + 1, z) is None \
                and rng.random() < 0.05:
            bp.set(x, y + 1, z, f"sea_pickle[pickles={rng.randint(1, 4)},waterlogged=true]")
    for _ in range(110):
        x, z = rng.randint(-24, 30), rng.randint(-14, 58)
        if bp.get(x, 0, z) in ("minecraft:sand", "minecraft:gravel") and bp.get(x, 1, z) is None:
            if rng.random() < 0.45:
                h = rng.randint(4, 16)
                for y in range(1, h + 1):
                    if bp.get(x, y, z) is not None:
                        break
                    bp.set(x, y, z, "kelp_plant" if y < h else "kelp[age=24]")
            else:
                bp.set(x, 1, z, rng.choice(["seagrass", "seagrass", f"{rng.choice(CORALS)}_coral[waterlogged=true]",
                                            f"{rng.choice(CORALS)}_coral_fan[waterlogged=true]"]))
    for x, z in ((-12, 8), (-14, 30), (18, 44), (-9, 50), (20, 6)):
        arch.boulder(bp, x, 1, z, r=2, blocks=("stone", "andesite", "gravel", "tube_coral_block"), seed=x * z)
    skirt(bp, 0, depth=5, spread=3, seed=21, top="sand", soil="sand", rock="sandstone",
          rubble=("gravel", "stone", "clay"))
    I.decorate(bp, "wreck", seed=1, loot=LOOT + "galleon_cargo")


register(StructureDef(
    "galleon_wreck", "overworld", ["#minecraft:is_ocean", "#minecraft:is_beach"],
    [Piece("galleon", galleon)], spacing=30, separation=10, heightmap="OCEAN_FLOOR_WG",
    adaptation="none", processors="none",
    spawns=[("brasshaven:barnacle_crab", 8, 1, 2), ("minecraft:drowned", 8, 1, 2)], creatures=[("barnacle_crab", 3)],
    title_fr="Épave de galion", title_en="Galleon Wreck"))


# ============================================================ 6. Sunken temple (ocean floor)
ST_BRICK = Palette({"prismarine_bricks": 6, "prismarine": 2, "dark_prismarine": 1}, seed=61, scale=2.5)
ST_FLOOR = Palette({"prismarine_bricks": 5, "prismarine": 3}, seed=62, scale=3)


def _st_column(bp, x, z, y0, h, broken=False, rng=None):
    """Cross-shaped prismarine column: stepped base, fluted shaft, lantern capital."""
    top = y0 + h
    if broken:
        top = y0 + max(2, int(h * rng.uniform(0.3, 0.7)))
    for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x + dx, y0, z + dz, "dark_prismarine")
    for dx, dz in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        bp.set(x + dx, y0, z + dz, stair("dark_prismarine_stairs", _toward(-dx, 0) if dx else "north"))
    for y in range(y0 + 1, top + 1):
        bp.set(x, y, z, "prismarine_bricks" if y % 3 else "dark_prismarine")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + dx, y, z + dz, "prismarine_wall" if y < top else "prismarine")
    if broken:
        bp.set(x, top + 1, z, "prismarine_slab[type=bottom,waterlogged=true]")
        return top
    # capital
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(x + dx, top + 1, z + dz, "dark_prismarine")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x + 2 * dx, top + 1, z + 2 * dz, stair("dark_prismarine_stairs", _toward(-dx, -dz), "top"))
    bp.set(x, top + 1, z, "sea_lantern")
    return top + 1


def _st_statue(bp, x, z, y, facing):
    """Robed guardian statue holding a trident, on a stepped plinth."""
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(x + dx, y, z + dz, "dark_prismarine")
            bp.set(x + dx, y + 1, z + dz, stair("prismarine_brick_stairs", _toward(-dx, -dz)) if dx or dz
                   else "dark_prismarine")
    bp.set(x, y + 1, z, "dark_prismarine")
    # robe, torso, shoulders, head
    bp.set(x, y + 2, z, "prismarine_bricks")
    bp.set(x, y + 3, z, "prismarine_bricks")
    bp.set(x, y + 4, z, "prismarine")
    px, pz = (1, 0) if facing in ("north", "south") else (0, 1)
    for s in (-1, 1):
        bp.set(x + px * s, y + 4, z + pz * s, stair("prismarine_stairs", _toward(-px * s, -pz * s), "top"))
    bp.set(x, y + 5, z, "prismarine_bricks")
    bp.set(x, y + 6, z, "dark_prismarine_slab[type=bottom,waterlogged=true]")
    fx, fz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
    bp.set(x + fx, y + 5, z + fz, "sea_lantern")  # glowing face
    # trident: rod in the right hand, prongs on top
    tx, tz = x + px * 2, z + pz * 2
    for yy in range(y + 2, y + 7):
        bp.set(tx, yy, tz, "lightning_rod[facing=up,powered=false,waterlogged=true]")
    bp.set(tx, y + 7, tz, "prismarine_wall")
    bp.set(tx, y + 8, tz, "lightning_rod[facing=up,powered=false,waterlogged=true]")


def sunken_temple(bp):
    bp.underwater = True
    rng = random.Random(63)
    # ---- seabed and three-stepped platform
    ground_patch(bp, 0, 3, 31, 34, seed=64, top=Palette({"sand": 6, "gravel": 2, "clay": 1}, seed=65, scale=3))
    for lvl, (h, y) in enumerate(((22, 0), (18, 1), (14, 2))):
        for x in range(-h, h + 1):
            for z in range(-h, h + 1):
                edge = max(abs(x), abs(z)) == h
                bp.set(x, y, z, "dark_prismarine" if edge else ST_FLOOR.pick(x, y, z))
                for yy in range(-4, y):
                    bp.set(x, yy, z, ST_BRICK.pick(x, yy, z), keep=True)
        for k in range(-h, h + 1):
            for x, z, f in ((k, -h - 1, "south"), (k, h + 1, "north"), (-h - 1, k, "east"), (h + 1, k, "west")):
                if bp.get(x, y, z) is None or y > 0:
                    bp.set(x, y, z, stair("prismarine_brick_stairs", f))
    # floor patterns: dark rays and lantern studs
    for x in range(-13, 14):
        for z in range(-13, 14):
            if (x == z or x == -z or x == 0 or z == 0) and max(abs(x), abs(z)) > 9:
                bp.set(x, 2, z, "dark_prismarine")
    for x, z in ((-13, -13), (13, -13), (-13, 13), (13, 13), (0, -17), (-17, 0), (17, 0)):
        bp.set(x, 2 if max(abs(x), abs(z)) <= 14 else 1, z, "sea_lantern")
    # ---- peristyle around the upper terrace (some columns broken)
    cols = []
    for k in range(-12, 13, 4):
        cols += [(k, -12), (k, 12), (-12, k), (12, k)]
    cols = sorted(set(cols))
    broken = {(-12, -4), (-8, 12), (12, 4), (4, -12), (12, -12), (-12, 8), (8, 12)}
    tops = {}
    for x, z in cols:
        if (x, z) in ((-4, 12), (0, 12), (4, 12)):
            continue  # entrance gap
        tops[(x, z)] = _st_column(bp, x, z, 3, 8, broken=(x, z) in broken, rng=rng)
    # architrave on intact runs
    for line in ([(k, -12) for k in range(-12, 13, 4)], [(-12, k) for k in range(-12, 13, 4)],
                 [(12, k) for k in range(-12, 13, 4)]):
        for a, b in zip(line, line[1:]):
            if tops.get(a) == 12 and tops.get(b) == 12:
                for t in range(5):
                    x = a[0] + (b[0] - a[0]) * t // 4
                    z = a[1] + (b[1] - a[1]) * t // 4
                    bp.set(x, 13, z, "prismarine_bricks")
                    bp.set(x, 14, z, slab("dark_prismarine_slab"))
    # fallen column drums on the terrace
    for x, z, ax in ((-9, -5, "x"), (9, 6, "z"), (5, -9, "x")):
        for k in range(3):
            xx, zz = (x + k, z) if ax == "x" else (x, z + k)
            bp.set(xx, 3, zz, "prismarine_bricks" if k != 1 else "dark_prismarine")

    # weather the peristyle before the (better preserved) rotunda is built
    bp.decay(0.03, protect=("sea_lantern",), region=((-22, 4, -22), (22, 20, 22)))

    # ---- the rotunda: solid cella with four arched doors, 8-column peristyle, ribbed dome
    for x, z in ring_cells(0, 0, -1, 11.5):
        d = math.hypot(x, z)
        bp.set(x, 2, z, "dark_prismarine" if d > 10.5 or 5.5 < d <= 6.5 else ST_FLOOR.pick(x, 2, z))
    for y in range(3, 12):
        ring(bp, 0, y, 0, 5.5, 6.5, ST_BRICK)
        for x, z in ring_cells(0, 0, -1, 5.5):
            bp.set(x, y, z, "air")
    ring(bp, 0, 3, 0, 5.5, 6.5, "dark_prismarine")
    ring(bp, 0, 11, 0, 5.5, 6.5, "dark_prismarine")
    for ang in (0, 90, 180, 270):
        radial_cut(bp, 0, 0, ang, 3, 7, 4.8, 7.2, width=3)
        for side in (-1, 1):
            a = math.radians(ang)
            x = round(math.cos(a) * 6 - math.sin(a) * side * 1)
            z = round(math.sin(a) * 6 + math.cos(a) * side * 1)
            bp.set(x, 7, z, stair("prismarine_brick_stairs", _toward(math.sin(a) * side, -math.cos(a) * side), "top"))
        x, z = at_angle(0, 0, ang, 6.6)
        bp.set(x, 8, z, "sea_lantern")
    for ang in (45, 135, 225, 315):
        radial_cut(bp, 0, 0, ang, 6, 8, 4.8, 7.2)
        radial_cut(bp, 0, 0, ang, 6, 8, 6, 6, spec="prismarine_wall")
    for k in range(8):
        x, z = at_angle(0, 0, k * 45 + 22.5, 9.6)
        _st_column(bp, x, z, 3, 8)
    ring(bp, 0, 12, 0, 6.4, 11.4, "dark_prismarine")
    ring(bp, 0, 13, 0, 8.4, 11.4, "prismarine_bricks")
    ring_stairs(bp, 0, 13, 0, 12, "dark_prismarine_stairs", half="top")
    ring_stairs(bp, 0, 14, 0, 11, "prismarine_brick_stairs", half="bottom")
    # drum lifting the dome above the colonnade
    RR, DY = 7, 17
    for y in range(13, DY):
        ring(bp, 0, y, 0, 5.5, 7.4, ST_BRICK)
        for x, z in ring_cells(0, 0, -1, 5.5):
            bp.set(x, y, z, "air")
    ring(bp, 0, DY - 1, 0, 5.5, 7.4, "dark_prismarine")
    ring_stairs(bp, 0, DY - 1, 0, 8, "dark_prismarine_stairs", half="top")
    for k in range(8):
        ang = k * 45 + 22.5
        radial_cut(bp, 0, 0, ang, 14, 15, 5, 7.6)
        radial_cut(bp, 0, 0, ang, 14, 15, 6.5, 6.5, spec="prismarine_wall")
        x, z = at_angle(0, 0, k * 45, 7.6)
        for y in range(13, DY - 1):
            bp.set(x, y, z, "dark_prismarine")
    arch.dome(bp, 0, DY, 0, RR, Palette({"dark_prismarine": 4, "prismarine_bricks": 1}, seed=66, scale=2.5),
              ribs="prismarine_bricks", oculus=False, rib_count=8)
    for k in range(8):
        for t in (25, 50):
            a, tt = math.radians(k * 45), math.radians(t)
            bp.set(round(math.cos(a) * math.cos(tt) * (RR + 0.6)), DY + round(math.sin(tt) * (RR + 0.6)),
                   round(math.sin(a) * math.cos(tt) * (RR + 0.6)), "sea_lantern")
    bp.disk(0, DY + RR, 0, 1, "sea_lantern")
    bp.set(0, DY + RR + 1, 0, "gold_block")
    bp.set(0, DY + RR + 2, 0, "lightning_rod[facing=up,powered=false,waterlogged=true]")
    arch.chandelier(bp, 0, DY + RR - 1, 0, candles=False)
    # ---- conduit shrine: pedestal + complete prismarine frame (activates when the player arrives)
    cy = 8
    for y in range(3, cy - 2):
        bp.set(0, y, 0, "dark_prismarine")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(dx, 3, dz, "dark_prismarine" if dx or dz else "sea_lantern")
    for a in range(-2, 3):
        for b in range(-2, 3):
            if max(abs(a), abs(b)) == 2:
                bp.set(a, cy + b, 0, "prismarine_bricks" if (a + b) % 2 else "dark_prismarine")   # xy ring
                bp.set(0, cy + b, a, "prismarine_bricks" if (a + b) % 2 else "dark_prismarine")   # zy ring
                bp.set(a, cy, b, "prismarine" if (a + b) % 2 else "sea_lantern")                  # xz ring
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(dx, cy + dy, dz, "air")
    bp.set(0, cy - 2, 0, "dark_prismarine")
    bp.set(0, cy, 0, "conduit[waterlogged=true]")
    # offerings around the shrine
    bp.chest(-3, 3, -3, "south", LOOT + "sunken_temple")
    bp.chest(3, 3, -3, "south", LOOT + "sunken_temple")
    for x, z in ((-3, 3), (3, 3), (-4, 0), (4, 0)):
        bp.set(x, 3, z, "decorated_pot[facing=south,waterlogged=true,cracked=false]")
    bp.set(0, 3, -4, "gold_block")
    bp.spawner(0, 3, 9, "minecraft:drowned")

    # ---- processional avenue from the south: column pairs, statues, lantern posts
    for z in (17, 21):
        for x in (-6, 6):
            _st_column(bp, x, z, 1, 6, broken=(x, z) == (6, 21), rng=rng)
    for x, z, f in ((-9, 9, "south"), (9, 9, "south"), (-9, -9, "north"), (9, -9, "north")):
        _st_statue(bp, x, z, 3, f)
    for x, z in ((-3, 24), (3, 24)):
        _st_statue(bp, x, z, 0, "south")

    # ---- corner obelisks (one toppled) on the lower terrace
    for (ox, oz), fallen in (((-19, -19), False), ((19, -19), False), ((-19, 19), False), ((19, 19), True)):
        if fallen:
            for k in range(11):
                for w in (0, 1):
                    bp.set(ox - 2 - k, 1, oz - 2 - k + w, "dark_prismarine" if k % 4 else "prismarine_bricks")
            for x in (ox, ox + 1):
                for z in (oz, oz + 1):
                    bp.set(x, 1, z, "dark_prismarine")
                    bp.set(x, 2, z, "prismarine_bricks")
            continue
        for x in (ox - 1, ox, ox + 1):
            for z in (oz - 1, oz, oz + 1):
                bp.set(x, 1, z, "dark_prismarine")
        for y in range(2, 17):
            w = 1 if y < 13 else 0
            for x in range(ox, ox + 1 + w):
                for z in range(oz, oz + 1 + w):
                    bp.set(x, y, z, "prismarine_bricks" if y % 5 else "dark_prismarine")
        bp.set(ox, 17, oz, "sea_lantern")
        bp.set(ox, 18, oz, "prismarine_wall")

    # ---- hidden vault under the rotunda (break the cracked tile north of the pedestal)
    vy = -7
    bp.room(-5, vy, -5, 5, -1, 5, "dark_prismarine", floor="prismarine_bricks", ceiling="prismarine_bricks")
    for y in range(vy + 1, 3):
        bp.set(0, y, -3, "air")
    bp.set(0, 2, -3, "prismarine_slab[type=top,waterlogged=true]")
    bp.ladder(0, vy + 1, -3, 1, "south")
    bp.fill(0, vy + 1, -4, 0, 1, -4, "prismarine_bricks")
    bp.chest(-4, vy + 1, 0, "east", LOOT + "sunken_temple")
    bp.chest(4, vy + 1, 0, "west", LOOT + "sunken_temple")
    bp.fill(-1, vy + 1, 3, 1, vy + 1, 4, "gold_block")
    bp.spawner(0, vy + 1, 1, "minecraft:drowned")
    for x, z in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.set(x, vy + 1, z, "sea_lantern")
    bp.set(0, vy + 1, -4, "dark_prismarine")

    # ---- weathering: sand drifts, missing blocks, coral gardens, kelp forest
    for _ in range(70):
        x, z = rng.randint(-22, 22), rng.randint(-22, 22)
        for y in (1, 2, 3, 4):
            if bp.get(x, y, z) is None and bp.get(x, y - 1, z) not in (None, "minecraft:air"):
                if rng.random() < 0.5:
                    bp.set(x, y, z, "sand" if y < 4 else "prismarine_slab[type=bottom,waterlogged=true]")
                break
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] in ("minecraft:prismarine_bricks", "minecraft:prismarine") and rng.random() < 0.04 \
                and bp.get(x, y + 1, z) is None:
            bp.set(x, y + 1, z, f"sea_pickle[pickles={rng.randint(1, 4)},waterlogged=true]")
    # coral gardens on the lower terrace and the seabed
    for _ in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(19, 30)
        cx, cz = round(math.cos(a) * r), round(math.sin(a) * r) + 3
        col = rng.choice(CORALS)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if dx * dx + dz * dz > 4 + rng.randint(-1, 1):
                    continue
                x, z = cx + dx, cz + dz
                y = 1
                while bp.get(x, y, z) not in (None, "minecraft:water") and y < 4:
                    y += 1
                if bp.get(x, y - 1, z) is None:
                    continue
                if rng.random() < 0.35:
                    bp.set(x, y, z, f"{col}_coral_block")
                    if rng.random() < 0.5:
                        bp.set(x, y + 1, z, f"{rng.choice(CORALS)}_coral_fan[waterlogged=true]")
                else:
                    bp.set(x, y, z, rng.choice([f"{col}_coral[waterlogged=true]", f"{col}_coral_fan[waterlogged=true]",
                                                "seagrass", f"sea_pickle[pickles=3,waterlogged=true]"]))
    for _ in range(90):
        x, z = rng.randint(-32, 32), rng.randint(-30, 38)
        if max(abs(x), abs(z)) > 23 and bp.get(x, 0, z) in ("minecraft:sand", "minecraft:gravel", "minecraft:clay") \
                and bp.get(x, 1, z) is None:
            h = rng.randint(5, 18)
            for y in range(1, h + 1):
                bp.set(x, y, z, "kelp_plant" if y < h else "kelp[age=20]")
    skirt(bp, 0, depth=5, spread=3, seed=31, top="sand", soil="sand", rock="sandstone",
          rubble=("gravel", "prismarine", "clay"))
    I.decorate(bp, "wreck", seed=1, loot=LOOT + "sunken_temple")


register(StructureDef(
    "sunken_temple", "overworld", ["#minecraft:is_ocean"], [Piece("temple", sunken_temple)],
    spacing=30, separation=10, heightmap="OCEAN_FLOOR_WG", adaptation="beard_box", processors="none",
    spawns=[("brasshaven:barnacle_crab", 8, 1, 2), ("minecraft:drowned", 8, 1, 2)], creatures=[("barnacle_crab", 4)],
    title_fr="Temple englouti", title_en="Sunken Temple"))


# ============================================================ 7. Dwarven mine (hillside settlement + galleries)
DM_STONE = Palette({"stone_bricks": 4, "cobblestone": 2, "andesite": 1, "cracked_stone_bricks": 1}, seed=71, scale=2.5)
DM_ROCK = Palette({"stone": 5, "andesite": 2, "tuff": 2, "cobblestone": 1}, seed=72, scale=3)
DM_ROOF = "brasshaven:crimson_roof_tile_stairs"
DM_UP = 4            # upper terrace height
SHAFT = (0, -10)     # shaft centre (x, z)
DEPTH = 32           # hall floor at y = -DEPTH
ORES = ["iron_ore", "iron_ore", "coal_ore", "coal_ore", "copper_ore", "gold_ore", "redstone_ore", "lapis_ore",
        "diamond_ore", "emerald_ore"]


def _dm_timber_house(bp, x0, z0, w, d, floors, rng, roof_axis="x"):
    """Stone ground floor + timber-framed upper floor(s) with packed-mud infill and a terracotta roof."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    bp.fill(x0, -4, z0, x1, -1, z1, "cobblestone", keep=True)
    top = 4 * floors
    for y in range(0, top + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                if y == 0 or y % 4 == 0:
                    bp.set(x, y, z, ("spruce_planks" if y else "cobblestone") if not edge else
                           (DM_STONE.pick(x, y, z) if y == 0 else log("dark_oak_log", "x" if z in (z0, z1) else "z")))
                elif y < 4:
                    bp.set(x, y, z, (DM_STONE.pick(x, y, z) if not corner else "polished_andesite") if edge else "air")
                elif edge:
                    post = corner or (z in (z0, z1) and (x - x0) % 3 == 0) or (x in (x0, x1) and (z - z0) % 3 == 0)
                    brace = (y % 4 == 2) and not post
                    bp.set(x, y, z, log("dark_oak_log") if post else ("packed_mud" if not brace else
                                                                     log("stripped_dark_oak_log", "x" if z in (z0, z1) else "z")))
                else:
                    bp.set(x, y, z, "air")
    # jettied overhang: corbels under the first timber floor
    for x in range(x0, x1 + 1):
        bp.set(x, 3, z0 - 1, stair("spruce_stairs", "south", "top"))
        bp.set(x, 3, z1 + 1, stair("spruce_stairs", "north", "top"))
    # windows (ground: framed stone; upper: shuttered)
    for x in range(x0 + 2, x1 - 1, 3):
        for z, f in ((z0, "north"), (z1, "south")):
            bp.set(x, 2, z, "glass_pane")
            for fy in range(4, top, 4):
                bp.set(x, fy + 2, z, "glass_pane")
                bp.set(x + 1 if x + 1 < x1 else x, fy + 2, z, "glass_pane")
                oz = -1 if f == "north" else 1
                bp.set(x, fy + 1, z + oz, stair("spruce_stairs", OPPOSITE[f], "top"))
    for z in range(z0 + 2, z1 - 1, 3):
        for x in (x0, x1):
            bp.set(x, 2, z, "glass_pane")
            for fy in range(4, top, 4):
                bp.set(x, fy + 2, z, "glass_pane")
    ridge = arch.steep_roof(bp, x0, z0, x1, z1, top + 1, DM_ROOF, axis=roof_axis, overhang=1, steep=1,
                            fill="spruce_planks", under="dark_oak_stairs",
                            ridge=slab("brasshaven:crimson_roof_tile_slab"),
                            dormers=1 if (w if roof_axis == "x" else d) >= 9 else 0, dormer_stairs=DM_ROOF,
                            dormer_wall="spruce_planks")
    return top, ridge


def _dm_gallery(bp, hy, start, direction, length, rng, end_loot=True, vault=False):
    """Timbered mine gallery: 3 wide, 3 tall, rails, posts and caps every 4, lanterns, ore veins."""
    dx, dz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[direction]
    px, pz = -dz, dx
    sx, sz = start
    axis = "x" if dx else "z"
    shape = "east_west" if dx else "north_south"
    for k in range(length):
        cx, cz = sx + dx * k, sz + dz * k
        # rock shell (visible in cut views, seals caves), then the void
        for w in range(-2, 3):
            for y in range(hy - 1, hy + 4):
                x, z = cx + px * w, cz + pz * w
                bp.set(x, y, z, DM_ROCK.pick(x, y, z), keep=True)
        for w in (-1, 0, 1):
            x, z = cx + px * w, cz + pz * w
            for y in range(hy, hy + 3):
                bp.set(x, y, z, "air")
            bp.set(x, hy - 1, z, rng.choice(["gravel", "cobbled_deepslate", "stone", "andesite"]))
        bp.set(cx, hy, cz, f"rail[shape={shape},waterlogged=false]")
        if k % 4 == 0:
            for w in (-1, 1):
                x, z = cx + px * w, cz + pz * w
                bp.set(x, hy, z, log("spruce_log"))
                bp.set(x, hy + 1, z, log("spruce_log"))
            for w in (-1, 0, 1):
                x, z = cx + px * w, cz + pz * w
                bp.set(x, hy + 2, z, log("spruce_log", "z" if axis == "x" else "x"))
            if k % 8 == 0:
                bp.lantern(cx, hy + 1, cz, hanging=True)
                bp.set(cx, hy + 2, cz, log("spruce_log", "z" if axis == "x" else "x"))
        elif k % 4 in (1, 3):
            for w in (-1, 1):
                x, z = cx + px * w, cz + pz * w
                f = _toward(-px * w, -pz * w)
                bp.set(x, hy + 2, z, stair("spruce_stairs", OPPOSITE[f], "top"))
        # ore veins: small clusters in the walls and ceiling
        if rng.random() < 0.35:
            ore = rng.choice(ORES)
            w = rng.choice((-2, 2))
            for _ in range(rng.randint(2, 4)):
                x = cx + px * w + dx * rng.randint(0, 1)
                z = cz + pz * w + dz * rng.randint(0, 1)
                bp.set(x, hy + rng.randint(0, 2), z, ore)
        if rng.random() < 0.08:
            bp.set(cx + px, hy + 2, cz + pz, "cobweb")
        if rng.random() < 0.05:
            bp.set(cx - px * 2, hy + 1, cz - pz * 2, "brasshaven:lithite_block")
    # side alcove with a collapsed section and an ore pile near the end
    ax, az = sx + dx * (length // 2) + px * 2, sz + dz * (length // 2) + pz * 2
    for y in range(hy, hy + 2):
        bp.set(ax, y, az, "air")
        bp.set(ax + dx, y, az + dz, "air")
    bp.set(ax, hy, az, "raw_iron_block" if rng.random() < 0.5 else "coal_block")
    bp.set(ax + dx, hy, az + dz, "barrel[facing=up,open=false]")
    ex, ez = sx + dx * (length - 1), sz + dz * (length - 1)
    for w in (-1, 0, 1):
        x, z = ex + px * w, ez + pz * w
        bp.set(x, hy, z, "gravel")
        bp.set(x, hy + 1, z, "gravel" if w else "air")
    if vault:
        # secret: dig through the collapse to find the foreman's sealed strongroom
        for k in range(1, 5):
            for w in (-1, 0, 1):
                for y in range(hy - 1, hy + 4):
                    x, z = ex + dx * k + px * w, ez + dz * k + pz * w
                    if k == 4 or y in (hy - 1, hy + 3) or abs(w) == 1 and k in (1, 4):
                        bp.set(x, y, z, "deepslate_bricks")
                    elif k > 1:
                        bp.set(x, y, z, "air")
                    else:
                        bp.set(x, y, z, "gravel")
        vx, vz = ex + dx * 2, ez + dz * 2
        bp.set(vx + px, hy, vz + pz, "brasshaven:lithite_block")
        bp.set(vx - px, hy, vz - pz, "raw_gold_block")
        bp.chest(vx + dx, hy, vz + dz, _toward(-dx, -dz), LOOT + "dwarven_mine")
        bp.lantern(vx, hy + 2, vz, hanging=True)
        bp.set(vx, hy + 3, vz, "deepslate_bricks")
    elif end_loot:
        bx, bz = ex - dx * 2 + px, ez - dz * 2 + pz
        bp.chest(bx, hy, bz, _toward(-dx, -dz), LOOT + "dwarven_mine")
    bp.entity(sx + dx * 6, hy, sz + dz * 6, {"id": "minecraft:chest_minecart" if direction == "north"
                                             else "minecraft:minecart"})
    return ex, ez


def dwarven_mine(bp):
    rng = random.Random(73)
    sxx, szz = SHAFT
    # ---- the hillside: one heightmap for the upper terrace and the slope rising behind it,
    # falling away on the sides and at the back so it blends into any terrain
    hill_top = Palette({"grass_block[snowy=false]": 8, "stone": 2, "coarse_dirt": 1, "andesite": 1}, seed=75, scale=4.5)
    yard = Palette({"coarse_dirt": 3, "gravel": 2, "dirt_path": 2, "packed_mud": 1}, seed=76, scale=2)
    for x in range(-34, 35):
        for z in range(-44, -3):
            core = DM_UP
            if z <= -13:
                core += 15 * math.sin(math.pi * min(1.0, (-12 - z) / 30)) * max(0.0, 1 - (x / 31) ** 2)
                core += math.sin(x * 0.4) * 1.0 + math.cos(z * 0.5) * 0.7
            fall = max(0, abs(x) - 24) * 1.1 + max(0, -36 - z) * 1.3
            h = round(core - fall)
            if h < 0:
                continue
            is_yard = z >= -17 and abs(x) <= 24 and h == DM_UP
            for y in range(-3, h + 1):
                if y == h:
                    bp.set(x, y, z, yard.pick(x, y, z) if is_yard else hill_top.pick(x, y, z))
                elif h - y < 3:
                    bp.set(x, y, z, "dirt")
                else:
                    bp.set(x, y, z, DM_ROCK.pick(x, y, z))
    # ---- retaining wall with buttresses and a stair down to the lower terrace
    for x in range(-24, 25):
        for y in range(-3, DM_UP + 1):
            bp.set(x, y, -3, DM_STONE.pick(x, y, -3))
        bp.set(x, DM_UP + 1, -3, "cobblestone_wall" if x % 2 else "stone_brick_wall")
        if x % 6 == 0 and abs(x) > 3:
            arch.buttress(bp, "south", -3, x, 0, DM_UP + 1, "stone_bricks", "stone_brick_stairs", depth=2)
    for i in range(DM_UP + 1):
        z, y = -3 + i, DM_UP - i
        for x in range(-2, 3):
            bp.set(x, y, z, stair("stone_brick_stairs", "north"))
            for yy in range(-2, y):
                bp.set(x, yy, z, "cobblestone")
            for yy in range(y + 1, DM_UP + 2):
                bp.set(x, yy, z, "air")
        for x in (-3, 3):
            for yy in range(-2, y + 2):
                bp.set(x, yy, z, DM_STONE.pick(x, yy, z))
    for x in (-3, 3):
        bp.set(x, DM_UP + 2, -3, "lantern[hanging=false,waterlogged=false]")

    # ---- shaft collar, headframe (A-frame with back-stays), sheave wheel, cage and cable
    for x in range(sxx - 4, sxx + 5):
        for z in range(szz - 4, szz + 5):
            bp.set(x, DM_UP, z, "spruce_planks" if max(abs(x - sxx), abs(z - szz)) > 1 else "air")
    for x in range(sxx - 2, sxx + 3):
        for z in range(szz - 2, szz + 3):
            if max(abs(x - sxx), abs(z - szz)) == 2:
                bp.set(x, DM_UP + 1, z, "spruce_fence")
    bp.set(sxx, DM_UP + 1, szz + 2, "spruce_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
    HT = DM_UP + 20
    legs = [((sxx - 3, szz - 3), (sxx - 1, szz - 1)), ((sxx + 3, szz - 3), (sxx + 1, szz - 1)),
            ((sxx - 3, szz + 3), (sxx - 1, szz + 1)), ((sxx + 3, szz + 3), (sxx + 1, szz + 1))]
    for (bx, bz), (tx, tz) in legs:
        bp.line((bx, DM_UP + 1, bz), (tx, HT, tz), log("stripped_spruce_log"))
        bp.set(bx, DM_UP + 1, bz, "stone_bricks")
    for y in range(DM_UP + 6, HT, 5):
        f = (y - DM_UP - 1) / (HT - DM_UP - 1)
        r = round(3 - 2 * f)
        for k in range(-r, r + 1):
            for (x, z, ax) in ((sxx + k, szz - r, "x"), (sxx + k, szz + r, "x"), (sxx - r, szz + k, "z"),
                               (sxx + r, szz + k, "z")):
                bp.set(x, y, z, log("spruce_log", ax))
    # back-stays to the hillside
    for x in (sxx - 2, sxx + 2):
        bp.line((x, HT - 2, szz - 1), (x, DM_UP + 6, szz - 11), log("spruce_log", "z"))
    # head platform, roof and the sheave wheel (in the x-y plane)
    bp.fill(sxx - 2, HT, szz - 2, sxx + 2, HT, szz + 2, "spruce_planks")
    for x in range(sxx - 2, sxx + 3):
        for z in range(szz - 2, szz + 3):
            if max(abs(x - sxx), abs(z - szz)) == 2:
                bp.set(x, HT + 1, z, "spruce_fence")
    wy = HT + 4
    for a in range(0, 360, 15):
        x = sxx + round(math.cos(math.radians(a)) * 3)
        y = wy + round(math.sin(math.radians(a)) * 3)
        bp.set(x, y, szz, log("stripped_dark_oak_log", "z"))
    for a in range(0, 360, 45):
        x = sxx + round(math.cos(math.radians(a)) * 1.6)
        y = wy + round(math.sin(math.radians(a)) * 1.6)
        bp.set(x, y, szz, "dark_oak_fence")
    bp.set(sxx, wy, szz, "iron_block")
    for z in (szz - 1, szz + 1):
        bp.set(sxx, wy, z, log("dark_oak_log", "z"))
        for y in range(HT + 1, wy):
            bp.set(sxx, y, z, log("spruce_log"))
    bp.chain(sxx + 3, DM_UP + 4, szz, wy - 1)
    bp.set(sxx + 3, DM_UP + 3, szz, "iron_bars")
    bp.fill(sxx + 2, HT, szz, sxx + 3, HT, szz, "air")
    # cage hanging in the shaft
    for y in range(DM_UP - 2, DM_UP):
        for x in range(sxx - 1, sxx + 2):
            for z in range(szz - 1, szz + 2):
                if (x, z) != (sxx, szz):
                    bp.set(x, y, z, "iron_bars")
    bp.set(sxx, DM_UP - 3, szz, "iron_block")
    bp.chain(sxx, DM_UP - 1, szz, HT - 1)
    bp.set(sxx, DM_UP - 2, szz, "air")
    # ---- winding house (west of the shaft) with the winch drum
    wh = Blueprint("winding_house")
    _dm_timber_house(wh, -16, -15, 8, 7, 1, rng, roof_axis="z")
    wh.door(-9, 1, -12, "east", "spruce")
    wh.set(-14, 1, -12, log("stripped_spruce_log", "x"))
    wh.set(-13, 1, -12, log("stripped_spruce_log", "x"))
    wh.set(-12, 1, -12, "grindstone[face=floor,facing=east]")
    wh.set(-15, 1, -12, "iron_block")
    wh.set(-15, 1, -14, "barrel[facing=up,open=false]")
    wh.set(-15, 1, -10, "lectern[facing=east,has_book=false,powered=false]")
    wh.lantern(-12, 3, -12, hanging=True)
    bp.paste(wh, 0, DM_UP, 0)
    bp.set(-8, DM_UP, -12, stair("spruce_stairs", "west"))

    # ---- shaft: timber-lined, ladder, landing lights, down to the great hall
    for y in range(-DEPTH, DM_UP):
        for x in range(sxx - 2, sxx + 3):
            for z in range(szz - 2, szz + 3):
                edge = max(abs(x - sxx), abs(z - szz)) == 2
                if edge:
                    corner = abs(x - sxx) == 2 and abs(z - szz) == 2
                    bp.set(x, y, z, log("spruce_log") if corner or y % 6 == 0 else "spruce_planks")
                elif y < DM_UP - 3:
                    bp.set(x, y, z, "air")
    bp.ladder(sxx, -DEPTH + 1, szz - 1, DM_UP, "south")
    for y in range(-DEPTH + 5, DM_UP - 3, 7):
        bp.lantern(sxx + 1, y, szz + 1, hanging=False)
        bp.set(sxx + 1, y - 1, szz + 1, slab("spruce_slab", "top"))

    # ---- rails from the shaft head to the tailings tip (east)
    for x in range(sxx + 3, 21):
        bp.set(x, DM_UP + 1, szz, "rail[shape=east_west,waterlogged=false]")
        bp.set(x, DM_UP, szz, "spruce_planks")
    for x in range(17, 22):
        for z in (szz - 1, szz + 1):
            bp.set(x, DM_UP, z, "spruce_planks")
    bp.set(21, DM_UP + 1, szz, "spruce_fence")
    bp.entity(9, DM_UP + 1, szz, {"id": "minecraft:minecart"})
    bp.entity(14, DM_UP + 1, szz, {"id": "minecraft:chest_minecart"})
    # trestle supports where the tip overhangs the terrace edge
    for x in (18, 20):
        for y in range(-2, DM_UP):
            bp.set(x, y, szz - 1, log("spruce_log"))
            bp.set(x, y, szz + 1, log("spruce_log"))
    # tailings pile spilling down to the lower terrace
    for x in range(14, 34):
        for z in range(-16, 8):
            d = math.hypot((x - 22) / 1.2, z - (szz + 4))
            h = round(DM_UP + 2 - d * 0.55 + rng.uniform(-0.4, 0.4))
            for y in range(-2, h + 1):
                if bp.get(x, y, z) is None or y > DM_UP:
                    bp.set(x, y, z, rng.choice(["gravel", "gravel", "andesite", "cobblestone", "tuff", "coarse_dirt"]))
    # ore bin + sorting table on the terrace
    for x in range(5, 9):
        for z in (szz - 4, szz - 3):
            bp.barrel(x, DM_UP + 1, z, "up")
    bp.set(6, DM_UP + 2, szz - 4, "raw_iron_block")
    bp.set(7, DM_UP + 2, szz - 4, "coal_block")
    bp.set(5, DM_UP + 1, szz + 3, "raw_copper_block")
    bp.set(6, DM_UP + 1, szz + 3, "raw_iron_block")
    bp.set(6, DM_UP + 2, szz + 3, "raw_gold_block")
    bp.barrel(8, DM_UP + 1, szz + 3, "up")
    # lamp posts on the terrace
    for x, z in ((-6, -6), (6, -6), (-20, -6), (12, -15)):
        for y in range(DM_UP + 1, DM_UP + 4):
            bp.set(x, y, z, "spruce_fence")
        bp.lantern(x, DM_UP + 4, z)

    # ---- lower terrace: bunkhouse (west), smithy (east), plaza with a waystone
    ground_patch(bp, 0, 4, 30, 24, seed=74)
    path_line(bp, [(0, -2), (0, 14), (-3, 26)], 0, Palette({"dirt_path": 3, "gravel": 2, "coarse_dirt": 1}, seed=3),
              width=3, seed=8)
    path_line(bp, [(0, 7), (-9, 7)], 0, Palette({"dirt_path": 3, "gravel": 1}, seed=3), width=2, seed=9)
    path_line(bp, [(0, 7), (9, 7)], 0, Palette({"dirt_path": 3, "gravel": 1}, seed=3), width=2, seed=10)
    btop, bridge = _dm_timber_house(bp, -21, 2, 12, 8, 2, rng, roof_axis="x")
    bp.door(-15, 1, 9, "south", "spruce")
    bp.set(-15, 0, 10, stair("stone_brick_stairs", "north"))
    for x in (-20, -18, -16):
        bp.bed(x, 1, 3, "south", "brown")
        bp.bed(x, 5, 3, "south", "red")
    bp.set(-12, 1, 3, "barrel[facing=up,open=false]")
    bp.table(-12, 1, 6, "spruce_pressure_plate", "spruce_fence")
    bp.stairs(-13, 1, 6, "spruce_stairs", "east")
    bp.stairs(-11, 1, 6, "spruce_stairs", "west")
    bp.set(-20, 1, 8, "furnace[facing=east,lit=true]")
    bp.set(-20, 1, 7, "smoker[facing=east,lit=false]")
    bp.barrel(-20, 5, 8, "up")
    bp.set(-12, 5, 8, "crafting_table")
    for x in range(-19, -16):
        bp.set(x, 4, 7, "air")
    for i in range(3):
        bp.stairs(-17 + i, 1 + i, 7, "spruce_stairs", "east")
    bp.lantern(-15, 3, 5, hanging=True)
    bp.lantern(-15, 7, 5, hanging=True)
    for y in range(1, bridge + 3):
        bp.set(-21, y, 5, "bricks" if y > 3 else "cobblestone")
        bp.set(-22, y, 5, "bricks" if y > 3 else "cobblestone")
    bp.set(-22, bridge + 3, 5, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    # smithy: open-fronted forge hall under a timber roof
    sx0, sx1, sz0, sz1 = 7, 17, 2, 10
    bp.fill(sx0, -3, sz0, sx1, 0, sz1, "cobblestone")
    for x in range(sx0, sx1 + 1):
        for z in range(sz0, sz1 + 1):
            bp.set(x, 0, z, "polished_andesite" if (x + z) % 2 else "stone_bricks")
    for x, z in ((sx0, sz0), (sx1, sz0), (sx0, sz1), (sx1, sz1), (sx0 + 5, sz1), (sx0 + 5, sz0)):
        for y in range(1, 6):
            bp.set(x, y, z, log("dark_oak_log"))
    for x in range(sx0, sx1 + 1):
        for y in range(1, 5):
            bp.set(x, y, sz0, DM_STONE.pick(x, y, sz0) if x not in (sx0, sx1, sx0 + 5) else log("dark_oak_log"))
        bp.set(x, 5, sz1, log("dark_oak_log", "x"))
        bp.set(x, 5, sz0, log("dark_oak_log", "x"))
    for z in range(sz0, sz1 + 1):
        for y in range(1, 5):
            bp.set(sx1, y, z, DM_STONE.pick(sx1, y, z) if z not in (sz0, sz1) else log("dark_oak_log"))
        bp.set(sx0, 5, z, log("dark_oak_log", "z"))
        bp.set(sx1, 5, z, log("dark_oak_log", "z"))
    arch.steep_roof(bp, sx0, sz0, sx1, sz1, 6, DM_ROOF, axis="x", overhang=1, fill="spruce_planks",
                    under="dark_oak_stairs", ridge=slab("brasshaven:crimson_roof_tile_slab"))
    # forge: stone hearth with magma glow, chimney, anvils, quench trough
    bp.fill(sx1 - 3, 1, sz0 + 1, sx1 - 1, 1, sz0 + 2, "bricks")
    bp.set(sx1 - 2, 1, sz0 + 1, "magma_block")
    bp.set(sx1 - 2, 2, sz0 + 1, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=south]")
    for y in range(3, 14):
        for x in (sx1 - 3, sx1 - 2, sx1 - 1):
            if y > 3 and x != sx1 - 2:
                continue
            bp.set(x, y, sz0 + 1, "bricks")
    bp.set(sx1 - 2, 3, sz0 + 1, "air")
    bp.set(sx1 - 2, 14, sz0 + 1, "bricks")
    bp.set(sx1 - 3, 2, sz0 + 1, "blast_furnace[facing=south,lit=true]")
    bp.set(sx1 - 1, 2, sz0 + 1, "blast_furnace[facing=south,lit=true]")
    bp.set(sx0 + 3, 1, sz0 + 4, "anvil[facing=east]")
    bp.set(sx0 + 2, 1, sz0 + 6, "smithing_table")
    bp.set(sx0 + 4, 1, sz0 + 6, "grindstone[face=floor,facing=north]")
    bp.set(sx1 - 1, 1, sz1 - 2, "water_cauldron[level=3]")
    bp.set(sx1 - 1, 1, sz1 - 1, "cauldron")
    bp.chest(sx1 - 1, 1, sz0 + 4, "west", LOOT + "dwarven_mine")
    bp.barrel(sx0 + 1, 1, sz0 + 1, "up")
    bp.set(sx0 + 1, 1, sz0 + 2, "iron_block")
    bp.entity(sx0 + 2, 1, sz0 + 1, {"id": "minecraft:armor_stand", "Rotation": [180.0, 0.0]})
    arch.hanging_lantern(bp, sx0 + 3, 5, sz0 + 5, chain=1)
    arch.hanging_lantern(bp, sx0 + 8, 5, sz0 + 5, chain=1)
    # plaza: waystone on a dais, ore carts, crates
    for x, z in ring_cells(0, 7, -1, 2.5):
        bp.set(x, 0, z, "polished_andesite")
    ring_stairs(bp, 0, 0, 7, 3, "stone_brick_stairs", half="bottom")
    bp.set(0, 1, 7, MOD["waystone"])
    for x, z in ((-3, 12), (4, 12)):
        for y in (1, 2, 3):
            bp.set(x, y, z, "spruce_fence")
        bp.lantern(x, 4, z)
    for x, z in ((3, 14), (4, 14), (3, 15)):
        bp.barrel(x, 1, z, "up")
    bp.set(4, 2, 14, "barrel[facing=north,open=false]")
    for z in range(13, 18):
        bp.set(-5, 1, z, f"rail[shape=north_south,waterlogged=false]")
    bp.entity(-5, 1, 15, {"id": "minecraft:minecart"})
    bp.set(-5, 1, 18, "spruce_fence")
    # ---- trees, bushes, flowers, terrain skirt
    for x, z, h in ((-27, 12, 10), (24, 16, 9), (-26, -2, 11), (-8, -30, 9), (12, -28, 8), (-20, -26, 10),
                    (-14, -36, 9), (17, -36, 11), (3, -40, 8), (26, -20, 9), (-29, -14, 8)):
        y0 = 1
        while bp.get(x, y0, z) not in (None, "minecraft:air"):
            y0 += 1
        arch.spruce(bp, x, y0, z, h=h, seed=x * 3 + z)
    for x, z in ((-24, 6), (22, 2), (10, 19)):
        arch.bush(bp, x, 1, z, leaves="spruce_leaves", r=1)
    for x, z in ((-6, -24), (9, -21), (-18, -33), (21, -30)):
        y0 = 1
        while bp.get(x, y0, z) not in (None, "minecraft:air"):
            y0 += 1
        arch.boulder(bp, x, y0, z, r=2, blocks=("stone", "andesite", "mossy_cobblestone", "tuff"), seed=x - z)
    skirt(bp, 0, depth=6, spread=3, seed=15)
    scatter_plants(bp, -32, -2, 32, 30, 1, 0.22, 11, FLOWERS)

    # ---- underground: the great hall
    hy = -DEPTH
    hx, hz = sxx, szz
    bp.fill(hx - 9, hy - 2, hz - 9, hx + 9, hy + 7, hz + 9, "deepslate", keep=True)
    bp.room(hx - 8, hy - 1, hz - 8, hx + 8, hy + 6, hz + 8, "deepslate_bricks", floor="polished_deepslate",
            ceiling="deepslate_tiles")
    for x in range(hx - 7, hx + 8):
        for z in range(hz - 7, hz + 8):
            if (x + z) % 4 == 0:
                bp.set(x, hy - 1, z, "deepslate_tiles")
    for x, z in ((hx - 5, hz - 5), (hx + 5, hz - 5), (hx - 5, hz + 5), (hx + 5, hz + 5)):
        for y in range(hy, hy + 6):
            bp.set(x, y, z, "polished_deepslate" if y % 3 else "chiseled_deepslate")
        for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + ddx, hy + 5, z + ddz, stair("deepslate_brick_stairs", _toward(-ddx, -ddz), "top"))
        bp.lantern(x, hy + 4, z + (1 if z < hz else -1), hanging=True)
    # ladder landing (the shaft opens into the ceiling)
    for x in range(hx - 1, hx + 2):
        for z in range(hz - 1, hz + 2):
            bp.set(x, hy + 6, z, "air")
    bp.fill(hx - 1, hy, hz - 2, hx + 1, hy + 5, hz - 2, "spruce_planks")
    bp.ladder(hx, hy, hz - 1, hy + 6, "south")
    # dwarven statues flanking the north gallery, forge corner, long table
    for x in (hx - 3, hx + 3):
        bp.set(x, hy, hz - 7, "polished_deepslate")
        bp.set(x, hy + 1, hz - 7, "deepslate_bricks")
        bp.set(x, hy + 2, hz - 7, "deepslate_tiles")
        bp.set(x, hy + 3, hz - 7, "brasshaven:lithite_block")
        bp.set(x, hy + 4, hz - 7, slab("deepslate_tile_slab"))
        bp.set(x - 1, hy + 2, hz - 7, stair("deepslate_tile_stairs", "east", "top"))
        bp.set(x + 1, hy + 2, hz - 7, stair("deepslate_tile_stairs", "west", "top"))
    bp.set(hx + 7, hy, hz - 7, "blast_furnace[facing=west,lit=false]")
    bp.set(hx + 7, hy, hz - 6, "anvil[facing=north]")
    bp.set(hx + 7, hy, hz - 5, "smithing_table")
    for z in range(hz + 2, hz + 6):
        bp.table(hx - 6, hy, z, "spruce_pressure_plate", "spruce_fence")
        bp.stairs(hx - 7, hy, z, "spruce_stairs", "east")
        bp.stairs(hx - 5, hy, z, "spruce_stairs", "west")
    bp.chest(hx - 7, hy, hz - 3, "east", LOOT + "dwarven_mine")
    bp.set(hx - 7, hy, hz - 7, "crafting_table")
    bp.set(hx + 6, hy, hz + 6, "barrel[facing=up,open=false]")
    bp.set(hx + 7, hy, hz + 6, "barrel[facing=up,open=false]")
    arch.chandelier(bp, hx, hy + 5, hz + 3)
    # ---- the four galleries
    _dm_gallery(bp, hy, (hx + 9, hz), "east", 20, rng, vault=True)
    _dm_gallery(bp, hy, (hx - 9, hz), "west", 20, rng)
    _dm_gallery(bp, hy, (hx, hz + 9), "south", 18, rng)
    _dm_gallery(bp, hy, (hx, hz - 9), "north", 18, rng)
    for x, z in ((hx + 8, hz), (hx - 8, hz), (hx, hz + 8), (hx, hz - 8)):
        for y in range(hy, hy + 3):
            for w in (-1, 0, 1):
                bp.set(x + (w if x == hx else 0), y, z + (w if z == hz else 0), "air")
    bp.spawner(hx, hy, hz + 20, "minecraft:cave_spider")
    bp.spawner(hx - 20, hy, hz, MOB["ruin_walker"])
    # ---- the dwarves who came back to the mine (wf/denizens.py) work up top; the deep galleries below belong to the
    # monsters
    surface = ((-60, 1, -60), (60, 60, 60))
    I.populate(bp, ["smith", "miner", "miner", "gemcutter"], region=surface, seed=1,
               bell=None, guard=("dwarf", (2, DM_UP + 1, -12)), folk="dwarf")
    I.decorate(bp, "workshop", seed=1, region=surface)
    I.decorate(bp, "mine", seed=2, region=((-80, -80, -80), (80, 0, 80)), loot=LOOT + "dwarven_mine")
    I.yard(bp, (-30, -30, 30, 30), DM_UP + 1, {"crates": 3, "cart": 2, "woodpile": 2, "hay": 1, "lamp": 1},
           count=6, seed=1)
    I.yard(bp, (-30, -30, 30, 30), 1, {"crates": 2, "cart": 2, "woodpile": 2, "smithy": 1}, count=4, seed=2)


register(StructureDef(
    "dwarven_mine", "overworld",
    ["#minecraft:is_mountain", "#minecraft:is_hill", "#minecraft:is_badlands", "windswept_hills",
     "windswept_gravelly_hills", "#minecraft:is_taiga"],
    [Piece("mine", dwarven_mine)], spacing=30, separation=10, adaptation="beard_thin", peaceful=True,
    title_fr="Mine naine abandonnée", title_en="Abandoned Dwarven Mine"))
