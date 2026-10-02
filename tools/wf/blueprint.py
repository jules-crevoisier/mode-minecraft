"""Blueprint: a voxel builder that exports Minecraft structure templates (.nbt).

Coordinates follow Minecraft: x = east, y = up, z = south.

Only positions that are explicitly set are written to the template. Anything
left unset is a "structure void" and keeps the terrain. Use ``clear`` (air) for
rooms that must be emptied.
"""
import math
import random

from . import nbt

# Structure templates are stored with the 1.20.1 data version; the game runs
# them through DataFixerUpper on load, so they upgrade cleanly to newer versions.
DATA_VERSION = 3465

DIRS = {
    "north": (0, 0, -1),
    "south": (0, 0, 1),
    "west": (-1, 0, 0),
    "east": (1, 0, 0),
    "up": (0, 1, 0),
    "down": (0, -1, 0),
}
HORIZONTAL = ["north", "east", "south", "west"]
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}
CCW = {"north": "west", "west": "south", "south": "east", "east": "north"}
CW = {v: k for k, v in CCW.items()}
AXIS = {"north": "z", "south": "z", "east": "x", "west": "x", "up": "y", "down": "y"}


def parse_block(spec):
    """'oak_stairs[facing=north]' -> ('minecraft:oak_stairs', {'facing': 'north'})"""
    if isinstance(spec, tuple):
        return spec
    props = {}
    if "[" in spec:
        name, rest = spec.split("[", 1)
        rest = rest.rstrip("]")
        for kv in rest.split(","):
            if kv:
                k, v = kv.split("=")
                props[k.strip()] = v.strip()
    else:
        name = spec
    if ":" not in name:
        name = "minecraft:" + name
    return name, props


def block_str(name, props):
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]"


def with_props(spec, **props):
    name, p = parse_block(spec)
    p = dict(p)
    p.update({k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in props.items()})
    return name, p


# Blocks that do not count as solid neighbours for fences/panes/walls.
NON_SOLID_HINTS = (
    "air", "torch", "lantern", "flower", "grass", "fern", "carpet", "slab", "stairs", "door",
    "sign", "button", "pressure_plate", "rail", "ladder", "vine", "chain", "candle", "bed",
    "pot", "banner", "head", "skull", "sapling", "mushroom", "chest", "lever", "cobweb",
    "water", "lava", "fire", "leaves", "azalea", "dripleaf", "kelp", "seagrass", "coral",
    "trapdoor", "anvil", "lectern", "campfire", "bell", "end_rod", "amethyst_cluster",
    "bud", "pickle", "scaffolding", "snow", "brewing", "cauldron", "glass_pane", "bars",
    "fence", "wall", "hopper", "composter", "grindstone", "stonecutter", "dead_bush", "bush",
    "berry", "roots", "fungus", "sprouts", "spore", "lily", "moss_carpet", "hay", "path",
    "farmland", "enchanting", "frame", "rod", "pointed_dripstone", "lichen", "sculk_vein",
    "web", "egg", "conduit", "beacon",
)


SOLID_EXCEPTIONS = {
    "glass", "tinted_glass", "hay_block", "moss_block", "bookshelf", "chiseled_bookshelf",
    "mushroom_stem", "red_mushroom_block", "brown_mushroom_block", "snow_block",
}


def is_solid(name):
    short = name.split(":")[1]
    if short in SOLID_EXCEPTIONS or short.endswith("_planks"):
        return True
    if short.endswith("_glass") and "pane" not in short:
        return True
    if family(name) is not None:
        return False
    return not any(h in short for h in NON_SOLID_HINTS)


def family(name):
    short = name.split(":")[1]
    if short.endswith("glass_pane") or short == "iron_bars":
        return "pane"
    if short.endswith("_fence_gate"):
        return "gate"
    if short.endswith("_fence"):
        return "nether_fence" if short == "nether_brick_fence" else "fence"
    if short.endswith("_wall") and not short.endswith("wall_torch") and "wall_" not in short:
        return "wall"
    if short.endswith("_stairs"):
        return "stairs"
    return None


class Blueprint:
    def __init__(self, name, seed=0):
        self.name = name
        self.blocks = {}  # (x, y, z) -> (name, props, nbt or None)
        self.entities = []
        self.rng = random.Random(f"{name}:{seed}")
        self.underwater = False  # clear() fills with water and blocks get waterlogged

    # ------------------------------------------------------------ primitives
    def set(self, x, y, z, spec, data=None, keep=False):
        if keep and (x, y, z) in self.blocks:
            return
        name, props = parse_block(spec)
        self.blocks[(x, y, z)] = (name, dict(props), data)

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0] if b else None

    def remove(self, x, y, z):
        self.blocks.pop((x, y, z), None)

    def fill(self, x0, y0, z0, x1, y1, z1, spec, keep=False):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, spec, keep=keep)

    def clear(self, x0, y0, z0, x1, y1, z1):
        self.fill(x0, y0, z0, x1, y1, z1, "water[level=0]" if self.underwater else "air")

    def replace(self, x0, y0, z0, x1, y1, z1, old, new):
        oname = parse_block(old)[0]
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    if self.get(x, y, z) == oname:
                        self.set(x, y, z, new)

    def walls(self, x0, y0, z0, x1, y1, z1, spec):
        """Four vertical walls of a box (no floor, no ceiling)."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, z0, spec)
                self.set(x, y, z1, spec)
            for z in range(z0, z1 + 1):
                self.set(x0, y, z, spec)
                self.set(x1, y, z, spec)

    def room(self, x0, y0, z0, x1, y1, z1, wall, floor=None, ceiling=None, corner=None):
        """Walls + floor + ceiling with the inside cleared to air."""
        self.clear(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y1 - 1, z1 - 1)
        self.walls(x0, y0, z0, x1, y1, z1, wall)
        if floor:
            self.fill(x0, y0, z0, x1, y0, z1, floor)
        if ceiling:
            self.fill(x0, y1, z0, x1, y1, z1, ceiling)
        if corner:
            for cx in (x0, x1):
                for cz in (z0, z1):
                    self.fill(cx, y0, cz, cx, y1, cz, corner)

    def pillar(self, x, y0, z, y1, spec):
        self.fill(x, y0, z, x, y1, z, spec)

    def foundation(self, x0, z0, x1, z1, y, spec, depth=6):
        """Solid footing that extends below the structure into the ground."""
        self.fill(x0, y - depth, z0, x1, y - 1, z1, spec, keep=True)

    def disk(self, cx, y, cz, r, spec, hollow=False, thickness=1.0):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.35 and (not hollow or d > r - thickness + 0.35 - 1e-9):
                    self.set(x, y, z, spec)

    def cylinder(self, cx, y0, cz, y1, r, spec, hollow=True, clear_inside=True):
        for y in range(y0, y1 + 1):
            if hollow and clear_inside:
                self.disk(cx, y, cz, r - 1, "air")
            self.disk(cx, y, cz, r, spec, hollow=hollow)

    def sphere(self, cx, cy, cz, r, spec, hollow=False, half=None):
        for x in range(cx - r - 1, cx + r + 2):
            for y in range(cy - r - 1, cy + r + 2):
                if half == "top" and y < cy:
                    continue
                if half == "bottom" and y > cy:
                    continue
                for z in range(cz - r - 1, cz + r + 2):
                    d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                    if d <= r + 0.4 and (not hollow or d > r - 0.6):
                        self.set(x, y, z, spec)

    def blob(self, cx, cy, cz, rx, ry, rz, spec, noise=0.25, top_spec=None, half=None):
        """Irregular ellipsoid, useful for floating islands and rocks."""
        for x in range(cx - rx - 1, cx + rx + 2):
            for y in range(cy - ry - 1, cy + ry + 2):
                if half == "bottom" and y > cy:
                    continue
                for z in range(cz - rz - 1, cz + rz + 2):
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                    if d <= 1 + self.rng.uniform(-noise, noise) * 0.5:
                        self.set(x, y, z, spec)
        if top_spec:
            top = {}
            for (x, y, z) in list(self.blocks):
                if self.get(x, y, z) == parse_block(spec)[0]:
                    if (x, z) not in top or y > top[(x, z)]:
                        top[(x, z)] = y
            for (x, z), y in top.items():
                self.set(x, y, z, top_spec)

    def line(self, p0, p1, spec):
        (x0, y0, z0), (x1, y1, z1) = p0, p1
        n = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1)
        for i in range(n + 1):
            t = i / n
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t), spec)

    # ------------------------------------------------------------ roofs
    def gable_roof(self, x0, z0, x1, z1, y, stairs, ridge_axis="x", overhang=1, fill=None, ridge=None):
        """Classic pitched roof. ridge_axis='x' means the ridge runs east-west."""
        if ridge_axis == "x":
            lo, hi = z0 - overhang, z1 + overhang
            a0, a1 = x0 - overhang, x1 + overhang
        else:
            lo, hi = x0 - overhang, x1 + overhang
            a0, a1 = z0 - overhang, z1 + overhang
        layer = 0
        while lo + layer <= hi - layer:
            yy = y + layer
            for a in range(a0, a1 + 1):
                if lo + layer == hi - layer:
                    p = (a, yy, lo + layer) if ridge_axis == "x" else (lo + layer, yy, a)
                    self.set(*p, ridge or stairs.replace("_stairs", "_slab") + "[type=bottom]")
                    continue
                if ridge_axis == "x":
                    self.set(a, yy, lo + layer, with_props(stairs, facing="south", half="bottom"))
                    self.set(a, yy, hi - layer, with_props(stairs, facing="north", half="bottom"))
                else:
                    self.set(lo + layer, yy, a, with_props(stairs, facing="east", half="bottom"))
                    self.set(hi - layer, yy, a, with_props(stairs, facing="west", half="bottom"))
            # gable ends + inner fill under the slope
            if fill:
                for b in range(lo + layer + 1, hi - layer):
                    for a in (x0, x1) if ridge_axis == "x" else (z0, z1):
                        p = (a, yy, b) if ridge_axis == "x" else (b, yy, a)
                        self.set(*p, fill)
            layer += 1
        return y + layer - 1

    def pyramid_roof(self, x0, z0, x1, z1, y, stairs, overhang=1, cap=None):
        lo_x, hi_x, lo_z, hi_z = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
        yy = y
        while lo_x <= hi_x and lo_z <= hi_z:
            if lo_x == hi_x or lo_z == hi_z:
                self.fill(lo_x, yy, lo_z, hi_x, yy, hi_z, cap or stairs.replace("_stairs", "_slab"))
                break
            for x in range(lo_x, hi_x + 1):
                self.set(x, yy, lo_z, with_props(stairs, facing="south", half="bottom"))
                self.set(x, yy, hi_z, with_props(stairs, facing="north", half="bottom"))
            for z in range(lo_z + 1, hi_z):
                self.set(lo_x, yy, z, with_props(stairs, facing="east", half="bottom"))
                self.set(hi_x, yy, z, with_props(stairs, facing="west", half="bottom"))
            lo_x, hi_x, lo_z, hi_z, yy = lo_x + 1, hi_x - 1, lo_z + 1, hi_z - 1, yy + 1
        return yy

    def cone_roof(self, cx, y, cz, r, stairs, cap=None, block=None):
        """Round tower roof made of stairs facing the centre."""
        yy = y
        rr = r
        while rr >= 1:
            for x in range(cx - rr - 1, cx + rr + 2):
                for z in range(cz - rr - 1, cz + rr + 2):
                    d = math.hypot(x - cx, z - cz)
                    if rr - 0.65 < d <= rr + 0.35:
                        dx, dz = cx - x, cz - z
                        if abs(dx) >= abs(dz):
                            facing = "east" if dx > 0 else "west"
                        else:
                            facing = "south" if dz > 0 else "north"
                        self.set(x, yy, z, with_props(stairs, facing=facing, half="bottom"))
                    elif d <= rr - 0.65 and block:
                        self.set(x, yy, z, block)
            yy += 1
            rr -= 1
        self.set(cx, yy, cz, cap or block or stairs.replace("_stairs", "_planks"))
        return yy

    # ------------------------------------------------------------ furniture & details
    def door(self, x, y, z, facing, wood="oak", hinge="left", open_=False):
        name = wood if wood.endswith("_door") else f"{wood}_door"
        for half, dy in (("lower", 0), ("upper", 1)):
            self.set(x, y + dy, z, with_props(name, facing=facing, half=half, hinge=hinge,
                                              open=open_, powered=False))

    def bed(self, x, y, z, facing, color="red"):
        dx, _, dz = DIRS[facing]
        self.set(x, y, z, with_props(f"{color}_bed", facing=facing, part="foot", occupied=False))
        self.set(x + dx, y, z + dz, with_props(f"{color}_bed", facing=facing, part="head", occupied=False))

    def chest(self, x, y, z, facing, loot=None, kind="chest"):
        data = {"LootTable": nbt.String(loot)} if loot else None
        props = {"facing": facing}
        if kind in ("chest", "trapped_chest"):
            props.update(type="single", waterlogged="false")
        self.set(x, y, z, (f"minecraft:{kind}", props), data)

    def barrel(self, x, y, z, facing="up", loot=None):
        data = {"LootTable": nbt.String(loot)} if loot else None
        self.set(x, y, z, ("minecraft:barrel", {"facing": facing, "open": "false"}), data)

    def spawner(self, x, y, z, entity):
        data = {
            # empty custom rules = any light level, so lit rooms still get their encounter
            "SpawnData": {"entity": {"id": nbt.String(entity)}, "custom_spawn_rules": nbt.Compound({})},
            "Delay": nbt.Short(20),
            "MinSpawnDelay": nbt.Short(200),
            "MaxSpawnDelay": nbt.Short(600),
            "SpawnCount": nbt.Short(3),
            "MaxNearbyEntities": nbt.Short(5),
            "RequiredPlayerRange": nbt.Short(14),
            "SpawnRange": nbt.Short(4),
        }
        self.set(x, y, z, "spawner", data)

    def lantern(self, x, y, z, hanging=False, soul=False):
        self.set(x, y, z, with_props("soul_lantern" if soul else "lantern", hanging=hanging, waterlogged=False))

    def wall_torch(self, x, y, z, facing, soul=False):
        self.set(x, y, z, with_props("soul_wall_torch" if soul else "wall_torch", facing=facing))

    def ladder(self, x, y0, z, y1, facing):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, with_props("ladder", facing=facing, waterlogged=False))

    def chain(self, x, y0, z, y1):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, with_props("chain", axis="y", waterlogged=False))

    def stairs(self, x, y, z, spec, facing, half="bottom"):
        self.set(x, y, z, with_props(spec, facing=facing, half=half, shape="straight", waterlogged=False))

    def slab(self, x, y, z, spec, type_="bottom"):
        self.set(x, y, z, with_props(spec, type=type_, waterlogged=False))

    def log(self, x, y, z, spec, axis="y"):
        self.set(x, y, z, with_props(spec, axis=axis))

    def table(self, x, y, z, top="oak_pressure_plate", leg="oak_fence"):
        self.set(x, y, z, leg)
        self.set(x, y + 1, z, top)

    def chair(self, x, y, z, stairs, facing):
        self.stairs(x, y, z, stairs, facing)

    def bookshelf_wall(self, x0, y0, z0, x1, y1, z1, chance_empty=0.0):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, "bookshelf" if self.rng.random() >= chance_empty else "oak_planks")

    def spiral_stairs(self, cx, cz, y0, y1, r, step_spec, center=None):
        """Spiral staircase around a central column, quarter turn every few steps."""
        ring = []
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if (x, z) != (cx, cz) and max(abs(x - cx), abs(z - cz)) == r:
                    ring.append((x, z))
        ring.sort(key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
        for y in range(y0, y1 + 1):
            if center:
                self.set(cx, y, cz, center)
        i = 0
        for y in range(y0, y1 + 1):
            for _ in range(2):
                x, z = ring[i % len(ring)]
                self.slab(x, y, z, step_spec, "bottom" if _ == 0 else "top")
                i += 1

    def window(self, x, y, z, axis, spec="glass_pane", height=2, shutters=None):
        for dy in range(height):
            self.set(x, y + dy, z, spec)

    def arch(self, x0, y0, z, x1, spec, axis="x", height=3):
        """Simple rounded arch opening along x (or z) with stairs at the top corners."""
        w = abs(x1 - x0)
        for i in range(w + 1):
            a = min(x0, x1) + i
            p = (a, y0 + height, z) if axis == "x" else (z, y0 + height, a)
            self.set(*p, spec)

    def scatter(self, positions, spec, chance):
        for p in positions:
            if self.rng.random() < chance:
                self.set(*p, spec)

    def weather(self, rules, chance=0.18, region=None):
        """Deterministic aging: rules maps block id -> list of replacement ids."""
        rules = {parse_block(k)[0]: v for k, v in rules.items()}
        for pos, (name, props, data) in list(self.blocks.items()):
            if region and not all(region[0][i] <= pos[i] <= region[1][i] for i in range(3)):
                continue
            if name in rules and self.rng.random() < chance:
                repl = self.rng.choice(rules[name])
                rname, rprops = parse_block(repl)
                merged = dict(props)
                merged.update(rprops)
                self.blocks[pos] = (rname, merged, data)

    def decay(self, chance, protect=(), region=None):
        """Remove random blocks to make ruins (never removes protected ids)."""
        protect = {parse_block(p)[0] for p in protect} | {"minecraft:chest", "minecraft:spawner",
                                                         "minecraft:barrel", "minecraft:jigsaw"}
        for pos, (name, props, data) in list(self.blocks.items()):
            if name in protect or name == "minecraft:air":
                continue
            if region and not all(region[0][i] <= pos[i] <= region[1][i] for i in range(3)):
                continue
            above = self.blocks.get((pos[0], pos[1] + 1, pos[2]))
            exposed = above is None or above[0] == "minecraft:air"
            if self.rng.random() < chance * (2.0 if exposed else 0.5):
                self.blocks[pos] = ("minecraft:air", {}, None)

    def jigsaw(self, x, y, z, orientation, name, target, pool, final_state="minecraft:air", joint="rollable"):
        data = {
            "name": nbt.String(name),
            "target": nbt.String(target),
            "pool": nbt.String(pool),
            "final_state": nbt.String(final_state),
            "joint": nbt.String(joint),
        }
        self.set(x, y, z, ("minecraft:jigsaw", {"orientation": orientation}), data)

    def entity(self, x, y, z, nbt_data):
        self.entities.append(((x, y, z), nbt_data))

    # ------------------------------------------------------------ transforms
    def paste(self, other, ox, oy, oz):
        for (x, y, z), b in other.blocks.items():
            self.blocks[(x + ox, y + oy, z + oz)] = b

    # ------------------------------------------------------------ shape resolution
    def _neighbor(self, pos, d):
        dx, dy, dz = DIRS[d]
        return self.blocks.get((pos[0] + dx, pos[1] + dy, pos[2] + dz))

    def resolve_shapes(self):
        """Compute connection/shape properties the game would normally derive."""
        if self.underwater:
            for pos, (name, props, data) in list(self.blocks.items()):
                if name == "minecraft:air":
                    self.blocks[pos] = ("minecraft:water", {"level": "0"}, None)
                elif props.get("waterlogged") == "false":
                    props = dict(props)
                    props["waterlogged"] = "true"
                    self.blocks[pos] = (name, props, data)
        for pos, (name, props, data) in list(self.blocks.items()):
            fam = family(name)
            if fam in ("pane", "fence", "nether_fence", "wall"):
                conns = {}
                for d in HORIZONTAL:
                    n = self._neighbor(pos, d)
                    c = False
                    if n:
                        nf = family(n[0])
                        if fam == "pane":
                            c = nf == "pane" or nf == "wall" or is_solid(n[0])
                        elif fam in ("fence", "nether_fence"):
                            c = nf == fam or nf == "gate" or is_solid(n[0])
                        else:
                            c = nf in ("wall", "pane", "fence") or nf == "gate" or is_solid(n[0])
                    conns[d] = c
                props = dict(props)
                if fam == "wall":
                    for d in HORIZONTAL:
                        props[d] = "low" if conns[d] else "none"
                    straight = (conns["north"] and conns["south"] and not conns["east"] and not conns["west"]) or \
                               (conns["east"] and conns["west"] and not conns["north"] and not conns["south"])
                    above = self._neighbor(pos, "up")
                    props["up"] = "false" if straight and not (above and above[0] != "minecraft:air") else "true"
                else:
                    for d in HORIZONTAL:
                        props[d] = "true" if conns[d] else "false"
                props.setdefault("waterlogged", "false")
                self.blocks[pos] = (name, props, data)
        for pos, (name, props, data) in list(self.blocks.items()):
            if family(name) == "stairs" and "facing" in props:
                props = dict(props)
                props["shape"] = self._stair_shape(pos, props)
                props.setdefault("waterlogged", "false")
                props.setdefault("half", "bottom")
                self.blocks[pos] = (name, props, data)

    def _stair_info(self, pos, d):
        n = self._neighbor(pos, d)
        if n and family(n[0]) == "stairs" and "facing" in n[1]:
            return n[1]["facing"], n[1].get("half", "bottom")
        return None

    def _can_take_shape(self, pos, facing, half, d):
        info = self._stair_info(pos, d)
        return info is None or info[0] != facing or info[1] != half

    def _stair_shape(self, pos, props):
        facing, half = props["facing"], props.get("half", "bottom")
        front = self._stair_info(pos, facing)
        if front and front[1] == half:
            d1 = front[0]
            if AXIS[d1] != AXIS[facing] and self._can_take_shape(pos, facing, half, OPPOSITE[d1]):
                return "outer_left" if d1 == CCW[facing] else "outer_right"
        back = self._stair_info(pos, OPPOSITE[facing])
        if back and back[1] == half:
            d2 = back[0]
            if AXIS[d2] != AXIS[facing] and self._can_take_shape(pos, facing, half, d2):
                return "inner_left" if d2 == CCW[facing] else "inner_right"
        return "straight"

    # ------------------------------------------------------------ export
    def bounds(self):
        xs = [p[0] for p in self.blocks]
        ys = [p[1] for p in self.blocks]
        zs = [p[2] for p in self.blocks]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def normalized(self):
        """Return (size, blocks dict) translated so the minimum corner is at 0,0,0."""
        (mx, my, mz), (Mx, My, Mz) = self.bounds()
        blocks = {(x - mx, y - my, z - mz): b for (x, y, z), b in self.blocks.items()}
        ents = [((x - mx, y - my, z - mz), d) for (x, y, z), d in self.entities]
        return (Mx - mx + 1, My - my + 1, Mz - mz + 1), blocks, ents, (mx, my, mz)

    def to_nbt(self):
        self.resolve_shapes()
        size, blocks, ents, _ = self.normalized()
        palette, index = [], {}
        out_blocks = []
        # Sort for deterministic output; block entities are emitted last like vanilla.
        for pos in sorted(blocks, key=lambda p: (blocks[p][2] is not None, p[1], p[2], p[0])):
            name, props, data = blocks[pos]
            key = block_str(name, props)
            if key not in index:
                index[key] = len(palette)
                entry = {"Name": nbt.String(name)}
                if props:
                    entry["Properties"] = nbt.Compound({k: nbt.String(v) for k, v in sorted(props.items())})
                palette.append(nbt.Compound(entry))
            b = {"pos": nbt.List([nbt.Int(c) for c in pos], nbt.Int), "state": nbt.Int(index[key])}
            if data is not None:
                b["nbt"] = nbt.wrap(data)
            out_blocks.append(nbt.Compound(b))
        entities = []
        for (x, y, z), d in ents:
            entities.append(nbt.Compound({
                "pos": nbt.List([nbt.Double(x + 0.5), nbt.Double(float(y)), nbt.Double(z + 0.5)], nbt.Double),
                "blockPos": nbt.List([nbt.Int(x), nbt.Int(y), nbt.Int(z)], nbt.Int),
                "nbt": nbt.wrap(d),
            }))
        return nbt.Compound({
            "DataVersion": nbt.Int(DATA_VERSION),
            "size": nbt.List([nbt.Int(s) for s in size], nbt.Int),
            "palette": nbt.List(palette, nbt.Compound),
            "blocks": nbt.List(out_blocks, nbt.Compound),
            "entities": nbt.List(entities, nbt.Compound),
        })

    def save(self, path):
        nbt.save(path, self.to_nbt())
