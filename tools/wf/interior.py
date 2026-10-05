"""Lived-in interiors, yards and residents for structure blueprints.

Builders draw walls, floors and the set pieces; this module fills what is left so rooms do not look
empty, without hand-placing every barrel:

  find_rooms(bp, region)          floor-level rooms: roofed air cells over a solid floor, one set per level
  decorate(bp, theme, ...)        furniture along the walls, a table in the middle, rugs, shelves and
                                  banners on the walls, lights under the ceiling (ruins get cobwebs,
                                  rubble and moss instead)
  populate(bp, residents, ...)    villagers with their job-site block, a bed each and a bell to meet at
  yard(bp, area, y, theme, ...)   props on open ground outside: hay, crates, carts, woodpiles, wells,
                                  crop patches, garden beds, signposts, lamp posts, benches
  villager / quest_npc / wandering_trader / iron_golem / brass_golem    template entities (26.2 NBT)

Every placement keeps the room walkable: a piece of furniture only goes on a free cell against a wall,
never next to a door, ladder, stair or opening, and only if every free cell of the room can still reach
every other one (flood fill after each piece). Nothing is placed where an entity already stands.

Entity notes (checked against the 26.2 sources):
  * Villager: ``VillagerData`` = {type, profession, level} (VillagerData.CODEC); a level >= 2 with Xp > 0
    keeps the profession even before the job site is claimed (ResetProfession only fires at level 1 and
    0 xp). Villagers never despawn (removeWhenFarAway is false); PersistenceRequired is set anyway.
    A STRUCTURE spawn makes them claim the nearest matching job site at once.
  * Wandering trader: DespawnDelay 0 = never leaves.
  * Item frames and paintings are NOT used: their ``block_pos`` is absolute and a template copy logs
    "Block-attached entity at invalid position" (an ERROR the CI smoke test rejects).
"""
import math
import random

from .blueprint import DIRS, HORIZONTAL, OPPOSITE, CW, CCW, with_props, is_solid
from . import support

AIR = {"minecraft:air", "minecraft:cave_air"}
WATER = {"minecraft:water"}
W = "brasshaven:"

# blocks a player walks over/through at foot level (they still count as part of the room)
LOW_PASSABLE = ("carpet", "pressure_plate", "rail", "button", "torch", "flower", "short_grass", "fern",
                "moss_carpet", "leaf_litter", "petals", "snow", "candle", "cobweb", "redstone_wire", "lily_pad",
                "seagrass", "sea_pickle", "dead_bush", "mist_gate")
# next to these the floor stays free (people climb, walk through or open them)
ACCESS = ("_door", "ladder", "_stairs", "_trapdoor", "_fence_gate", "scaffolding", "vine", "mist_gate",
          "boss_seal", "jigsaw", "spawner", "_bed", "nether_portal", "end_portal", "waystone")
LIGHTS = ("lantern", "torch", "glowstone", "sea_lantern", "shroomlight", "froglight", "end_rod", "lamp",
          "chandelier", "jack_o_lantern", "beacon", "magma_block", "lava", "fire", "campfire", "candle",
          "glow_lichen", "lithite", "starlight", "conduit", "aether_conduit", "amethyst_cluster", "crying_obsidian",
          "respawn_anchor", "brewing_stand")
FLOWERS = ("poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip", "white_tulip",
           "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley", "fern", "azalea_bush",
           "flowering_azalea_bush", "red_mushroom", "brown_mushroom", "cactus", "spruce_sapling", "oak_sapling")
YAW = {"south": 0.0, "west": 90.0, "north": 180.0, "east": 270.0}


def _short(name):
    return name.split(":", 1)[1] if name else ""


def _dirvec(d):
    return DIRS[d][0], DIRS[d][2]


# ====================================================================== rooms
class Room:
    """Floor cells (x, z) at level ``y`` (the first air layer above the floor)."""

    def __init__(self, y, cells, free, heads, bp):
        self.y = y
        self.cells = cells          # every walkable cell of the room
        self.free = set(free)       # empty cells furniture may go in (still empty)
        self.heads = heads          # (x, z) -> number of air blocks from y up to the ceiling
        self.occupied = set()
        self.tall = set()           # cells holding something two blocks tall (armor stands): nothing above
        self.keep = set()
        self.walls = {}             # (x, z) -> [dirs with an obstruction at y and y + 1]
        self.full_walls = {}        # (x, z) -> [dirs with a sturdy wall face at y + 1 and y + 2]
        xs = [c[0] for c in cells]
        zs = [c[1] for c in cells]
        self.box = (min(xs), min(zs), max(xs), max(zs))
        self.bp = bp

    @property
    def area(self):
        return len(self.cells)

    @property
    def width(self):
        return min(self.box[2] - self.box[0], self.box[3] - self.box[1]) + 1

    def centre(self):
        cx = sum(c[0] for c in self.cells) / len(self.cells)
        cz = sum(c[1] for c in self.cells) / len(self.cells)
        return min(self.cells, key=lambda c: (c[0] - cx) ** 2 + (c[1] - cz) ** 2)

    def head(self, c):
        return self.heads.get(c, 2)

    def walkable(self):
        return self.cells - self.occupied

    def connected_without(self, extra):
        """Would the room stay in one piece (and keep every access cell) if ``extra`` cells were filled?"""
        extra = set(extra)
        if extra & self.keep:
            return False
        left = self.cells - self.occupied - extra
        if not left:
            return False
        start = next(iter(sorted(self.keep & left))) if self.keep & left else min(left)
        seen = {start}
        stack = [start]
        while stack:
            x, z = stack.pop()
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, z + dz)
                if n in left and n not in seen:
                    seen.add(n)
                    stack.append(n)
        return len(seen) == len(left)

    def take(self, cells):
        for c in cells:
            self.occupied.add(c)
            self.free.discard(c)
        mark = getattr(self.bp, "_decor_cells", None)
        if mark is None:
            mark = self.bp._decor_cells = set()
        for c in cells:
            mark.add((c[0], self.y, c[1]))


def _checker(bp, ground=0, void_solid=False):
    """Unset cells (structure void) keep the terrain: rock at or below ``ground`` (everywhere when
    ``void_solid``: structures carved underground), open air above it."""
    return support.Checker(bp.blocks, support.Context(ground=None if void_solid else ground, unset_solid=void_solid))


def _air_at(bp, chk, p):
    b = bp.blocks.get(p)
    if b is None:
        return not chk.terrain(p)
    return b[0] in AIR or (bp.underwater and b[0] in WATER)


def _is_air(bp, p):
    b = bp.blocks.get(p)
    if b is None:
        return False
    return b[0] in AIR or (bp.underwater and b[0] in WATER)


def _low_passable(bp, p):
    b = bp.blocks.get(p)
    if b is None:
        return False
    s = _short(b[0])
    return any(h in s for h in LOW_PASSABLE) and not s.endswith("_block") and "lantern" not in s


def _entity_cells(bp):
    out = set()
    for (x, y, z), _ in bp.entities:
        out.add((int(math.floor(x)), int(math.floor(y)), int(math.floor(z))))
    return out


def find_rooms(bp, region=None, min_area=9, min_width=3, roof_scan=40, sky_ok=False, void_solid=False, ground=0):
    """Rooms of ``bp`` inside ``region`` ((x0, y0, z0), (x1, y1, z1)): connected floor cells at one level
    that have a roof somewhere above (``sky_ok`` also accepts open courtyards). Unset cells count as air
    above ``ground`` and as rock below it; ``void_solid``: unset cells are always rock (underground
    structures carved out of the terrain)."""
    chk = _checker(bp, ground, void_solid)
    ents = _entity_cells(bp)
    seals = [(p, (d or {}).get("radius")) for p, (n, _, d) in bp.blocks.items() if n == "brasshaven:boss_seal"]
    pts = set()
    for p, (name, props, data) in bp.blocks.items():
        if name in AIR or (bp.underwater and name in WATER) or _low_passable(bp, p):
            pts.add(p)
        elif chk.full(p, "up"):
            q = (p[0], p[1] + 1, p[2])
            if q not in bp.blocks:
                pts.add(q)
    cand = {}
    for p in pts:
        if region and not all(region[0][i] <= p[i] <= region[1][i] for i in range(3)):
            continue
        x, y, z = p
        air = _air_at(bp, chk, p)
        if not air and not _low_passable(bp, p):
            continue
        if not _air_at(bp, chk, (x, y + 1, z)):
            continue
        if not chk.full((x, y - 1, z), "up"):
            continue
        h = 1
        roofed = False
        for yy in range(y + 1, y + roof_scan + 1):
            q = (x, yy, z)
            if _air_at(bp, chk, q):
                h += 1
                continue
            roofed = True
            break
        if not roofed and not sky_ok:
            continue
        cand[(x, y, z)] = (air and p not in ents, h)
    rooms = []
    seen = set()
    for p in sorted(cand, key=lambda q: (q[1], q[0], q[2])):
        if p in seen:
            continue
        y = p[1]
        comp, stack = [], [p]
        seen.add(p)
        while stack:
            c = stack.pop()
            comp.append(c)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + dx, y, c[2] + dz)
                if n in cand and n not in seen:
                    seen.add(n)
                    stack.append(n)
        if len(comp) < min_area:
            continue
        cells = {(c[0], c[2]) for c in comp}
        free = {(c[0], c[2]) for c in comp if cand[c][0]}
        heads = {(c[0], c[2]): cand[c][1] for c in comp}
        room = Room(y, cells, free, heads, bp)
        room.chk = chk
        if room.width < min_width:
            continue
        if any(seal_r is not None and math.dist((sx, sy, sz), (room.centre()[0], y, room.centre()[1])) <
               int(getattr(seal_r, "value", seal_r)) + 6 for (sx, sy, sz), seal_r in seals):
            continue
        _classify(bp, room, chk)
        rooms.append(room)
    return rooms


def _classify(bp, room, chk):
    y = room.y
    for (x, z) in room.cells:
        walls, full = [], []
        access = False
        for d in HORIZONTAL:
            dx, dz = _dirvec(d)
            n = (x + dx, z + dz)
            nb = bp.blocks.get((n[0], y, n[1]))
            nb_up = bp.blocks.get((n[0], y + 1, n[1]))
            low = bp.blocks.get((n[0], y - 1, n[1]))
            for b in (nb, nb_up, low):
                if b and any(h in _short(b[0]) for h in ACCESS):
                    access = True
            if n in room.cells:
                continue
            if chk.passable((n[0], y, n[1])):
                access = True  # an opening: doorway, drop, open side, corridor
                continue
            if chk.passable((n[0], y + 1, n[1])):
                access = True  # a step up: someone may climb there
                continue
            walls.append(d)
            if chk.full((n[0], y + 1, n[1]), OPPOSITE[d]) and chk.full((n[0], y + 2, n[1]), OPPOSITE[d]):
                full.append(d)
        if walls:
            room.walls[(x, z)] = walls
        if full:
            room.full_walls[(x, z)] = full
        if access:
            room.keep.add((x, z))
    # the cell in front of an access cell stays free too (two-wide clearance at doors and stairs)
    grow = set()
    for (x, z) in room.keep:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in room.cells and n not in room.walls:
                grow.add(n)
    if len(room.keep | grow) < room.area * 0.6:
        room.keep |= grow


# ====================================================================== furniture pieces
class Ctx:
    def __init__(self, bp, room, theme, rng, loot=None):
        self.bp, self.room, self.theme, self.rng, self.loot = bp, room, theme, rng, loot
        self.y = room.y
        self.wood = theme.get("wood", "spruce")
        self.loot_left = theme.get("loot_barrels", 0) if loot else 0

    def at(self, c, dy=0):
        return (c[0], self.y + dy, c[1])

    def set(self, c, dy, spec, data=None):
        self.bp.set(c[0], self.y + dy, c[1], spec, data)

    def air(self, c, dy):
        return _air_at(self.bp, self.room.chk, self.at(c, dy))

    def wet(self):
        return self.bp.underwater


def _top(ctx, c, choices):
    """Something small on top of a piece of furniture (if there is head room)."""
    if ctx.room.head(c) < 3 or not ctx.air(c, 1) or not choices:
        return
    pick = ctx.rng.choice(choices)
    if pick:
        ctx.set(c, 1, pick)


def _tops(ctx):
    t = ctx.theme.get("tops")
    if t is not None:
        return t
    if ctx.wet():
        return [None, None, "sea_pickle[pickles=2,waterlogged=true]"]
    pots = [f"potted_{f}" for f in FLOWERS[:12]]
    return [None, None, "candle[candles=2,lit=true,waterlogged=false]", "lantern[hanging=false,waterlogged=false]",
            ctx.rng.choice(pots), ctx.rng.choice(pots)]


def p_barrel(ctx, c, d):
    data = None
    if ctx.loot_left > 0 and ctx.rng.random() < 0.35:
        ctx.loot_left -= 1
        from . import nbt
        data = {"LootTable": nbt.String(ctx.loot)}
    ctx.set(c, 0, ("minecraft:barrel", {"facing": "up", "open": "false"}), data)
    _top(ctx, c, _tops(ctx))
    return [c]


def p_crates(ctx, c, d):
    ctx.set(c, 0, "barrel[facing=up,open=false]")
    if ctx.room.head(c) >= 3 and ctx.air(c, 1):
        ctx.set(c, 1, f"barrel[facing={OPPOSITE[d]},open=false]")
        if ctx.room.head(c) >= 4 and ctx.rng.random() < 0.4 and ctx.air(c, 2):
            ctx.set(c, 2, "barrel[facing=up,open=false]")
    return [c]


def p_bookshelf(ctx, c, d):
    h = min(ctx.room.head(c) - 1, 3 if ctx.theme.get("tall_shelves") else 2)
    for dy in range(max(1, h)):
        ctx.set(c, dy, "bookshelf" if ctx.rng.random() < 0.85 else
                f"chiseled_bookshelf[facing={OPPOSITE[d]},slot_0_occupied=true,slot_1_occupied=false,"
                f"slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    if ctx.room.head(c) > h + 1 and ctx.rng.random() < 0.3:
        ctx.set(c, max(1, h), "candle[candles=1,lit=true,waterlogged=false]")
    return [c]


def _faced(name):
    def place(ctx, c, d):
        ctx.set(c, 0, f"{name}[facing={OPPOSITE[d]}]")
        return [c]
    return place


def _plain(name, top=False):
    def place(ctx, c, d):
        ctx.set(c, 0, name)
        if top:
            _top(ctx, c, _tops(ctx))
        return [c]
    return place


def p_lectern(ctx, c, d):
    ctx.set(c, 0, f"lectern[facing={OPPOSITE[d]},has_book=false,powered=false]")
    return [c]


def p_grindstone(ctx, c, d):
    ctx.set(c, 0, f"grindstone[face=floor,facing={CW[d]}]")
    return [c]


def p_anvil(ctx, c, d):
    ctx.set(c, 0, f"{ctx.rng.choice(['anvil', 'anvil', 'chipped_anvil'])}[facing={CW[d]}]")
    return [c]


def p_smithing(ctx, c, d):
    ctx.set(c, 0, "smithing_table")
    return [c]


def p_cauldron(ctx, c, d):
    ctx.set(c, 0, "water_cauldron[level=3]" if not ctx.wet() else "cauldron")
    return [c]


def p_brewing(ctx, c, d):
    ctx.set(c, 0, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    return [c]


def p_pot(ctx, c, d):
    ctx.set(c, 0, f"decorated_pot[cracked={'true' if ctx.theme.get('ruined') else 'false'},facing={OPPOSITE[d]},"
                  f"waterlogged=false]")
    return [c]


def p_plant(ctx, c, d):
    ctx.set(c, 0, f"potted_{ctx.rng.choice(FLOWERS)}")
    return [c]


def p_hay(ctx, c, d):
    ctx.set(c, 0, "hay_block[axis=y]")
    if ctx.room.head(c) >= 3 and ctx.rng.random() < 0.5 and ctx.air(c, 1):
        ctx.set(c, 1, f"hay_block[axis={'x' if d in ('north', 'south') else 'z'}]")
    return [c]


def p_produce(ctx, c, d):
    ctx.set(c, 0, ctx.rng.choice(["pumpkin", "melon", "hay_block[axis=y]", "carved_pumpkin[facing=" + OPPOSITE[d] + "]"]))
    return [c]


def p_workbench(ctx, c, d):
    ctx.set(c, 0, ctx.rng.choice(["crafting_table", "crafting_table", f"loom[facing={OPPOSITE[d]}]",
                                  "fletching_table", "cartography_table"]))
    _top(ctx, c, [None, None, "candle[candles=1,lit=true,waterlogged=false]"] if not ctx.wet() else [None])
    return [c]


def p_kitchen(ctx, c, d):
    ctx.set(c, 0, ctx.rng.choice([f"smoker[facing={OPPOSITE[d]},lit=false]", f"furnace[facing={OPPOSITE[d]},lit=false]",
                                  "barrel[facing=up,open=false]", "water_cauldron[level=3]", "composter[level=4]"]))
    return [c]


def p_armor_stand(ctx, c, d):
    ctx.bp.entity(c[0], ctx.y, c[1], {"id": "minecraft:armor_stand", "Rotation": [YAW[OPPOSITE[d]], 0.0]})
    ctx.room.tall.add(c)
    return [c]


def p_bed(ctx, c, d):
    """Head against the wall, foot one cell into the room."""
    dx, dz = _dirvec(OPPOSITE[d])
    foot = (c[0] + dx, c[1] + dz)
    if foot not in ctx.room.free or not ctx.room.connected_without([c, foot]):
        return None
    color = ctx.rng.choice(ctx.theme.get("beds", ["red", "white", "light_blue", "brown", "green"]))
    ctx.bp.bed(foot[0], ctx.y, foot[1], d, color)
    side = (c[0] + _dirvec(CW[d])[0], c[1] + _dirvec(CW[d])[1])
    cells = [c, foot]
    if side in ctx.room.free and side not in ctx.room.keep and side in ctx.room.walls and \
            ctx.room.connected_without(cells + [side]) and not ctx.wet():
        ctx.set(side, 0, "barrel[facing=up,open=false]")
        _top(ctx, side, ["candle[candles=1,lit=true,waterlogged=false]", "lantern[hanging=false,waterlogged=false]"])
        cells.append(side)
    return cells


def p_skull(ctx, c, d):
    ctx.set(c, 0, f"skeleton_skull[powered=false,rotation={ctx.rng.randint(0, 15)}]")
    return [c]


def p_bones(ctx, c, d):
    ctx.set(c, 0, f"bone_block[axis={ctx.rng.choice('xyz')}]")
    return [c]


def p_cobweb(ctx, c, d):
    ctx.set(c, 0, "cobweb")
    return [c]


def p_rubble(ctx, c, d):
    stone = ctx.theme.get("rubble", ["cobblestone", "mossy_cobblestone", "andesite", "gravel"])
    ctx.set(c, 0, ctx.rng.choice(stone))
    if ctx.room.head(c) >= 3 and ctx.rng.random() < 0.45 and ctx.air(c, 1):
        ctx.set(c, 1, ctx.rng.choice(["cobblestone_slab[type=bottom,waterlogged=false]",
                                      "mossy_cobblestone_slab[type=bottom,waterlogged=false]",
                                      "stone_brick_slab[type=bottom,waterlogged=false]"]))
    return [c]


def p_candles(ctx, c, d):
    ctx.set(c, 0, f"candle[candles={ctx.rng.randint(2, 4)},lit=true,waterlogged=false]")
    return [c]


def p_machine(ctx, c, d):
    """Steampunk: a gauge cabinet with a pipe or gear on top."""
    ctx.set(c, 0, ctx.rng.choice([W + "gear_panel", W + "pressure_gauge", W + "copper_pipes"]))
    top = ctx.rng.choice([W + "copper_pipe[axis=y]", W + "pressure_gauge", None])
    if top and ctx.room.head(c) >= 3 and ctx.air(c, 1):
        ctx.set(c, 1, top)
    return [c]


def p_mahogany(ctx, c, d):
    ctx.set(c, 0, W + "mahogany_table")
    _top(ctx, c, [None, "candle[candles=3,lit=true,waterlogged=false]", "potted_fern"])
    return [c]


def p_shulker(ctx, c, d):
    ctx.set(c, 0, f"{ctx.rng.choice(['purple', 'magenta', 'black'])}_shulker_box[facing=up]")
    return [c]


def p_end_rod(ctx, c, d):
    ctx.set(c, 0, "purpur_pillar[axis=y]")
    if ctx.room.head(c) >= 3 and ctx.air(c, 1):
        ctx.set(c, 1, "end_rod[facing=up]")
    return [c]


def p_gold(ctx, c, d):
    ctx.set(c, 0, ctx.rng.choice(["gold_block", "raw_gold_block", "gilded_blackstone", "barrel[facing=up,open=false]"]))
    _top(ctx, c, [None, "soul_lantern[hanging=false,waterlogged=false]", "candle[candles=2,lit=true,waterlogged=false]"])
    return [c]


def p_blackstone(ctx, c, d):
    ctx.set(c, 0, ctx.rng.choice(["polished_blackstone_bricks", "chiseled_polished_blackstone",
                                  "cracked_polished_blackstone_bricks"]))
    _top(ctx, c, [None, "soul_lantern[hanging=false,waterlogged=false]", "skeleton_skull[powered=false,rotation=4]"])
    return [c]


def p_coral(ctx, c, d):
    ctx.set(c, 0, f"{ctx.rng.choice(['tube', 'brain', 'bubble', 'fire', 'horn'])}_coral_block")
    _top(ctx, c, [None, "sea_pickle[pickles=3,waterlogged=true]"])
    return [c]


def p_sea_pickle(ctx, c, d):
    ctx.set(c, 0, f"sea_pickle[pickles={ctx.rng.randint(1, 4)},waterlogged=true]")
    return [c]


def p_moss(ctx, c, d):
    ctx.set(c, 0, "moss_carpet")
    return [c]


PIECES = {
    "barrel": p_barrel, "crates": p_crates, "bookshelf": p_bookshelf, "lectern": p_lectern,
    "grindstone": p_grindstone, "anvil": p_anvil, "smithing": p_smithing, "cauldron": p_cauldron,
    "brewing": p_brewing, "pot": p_pot, "plant": p_plant, "hay": p_hay, "produce": p_produce,
    "workbench": p_workbench, "kitchen": p_kitchen, "armor_stand": p_armor_stand, "bed": p_bed,
    "skull": p_skull, "bones": p_bones, "cobweb": p_cobweb, "rubble": p_rubble, "candles": p_candles,
    "machine": p_machine, "mahogany": p_mahogany, "shulker": p_shulker, "end_rod": p_end_rod,
    "gold": p_gold, "blackstone": p_blackstone, "coral": p_coral, "sea_pickle": p_sea_pickle, "moss": p_moss,
    "furnace": _faced("furnace"), "smoker": _faced("smoker"), "blast_furnace": _faced("blast_furnace"),
    "loom": _faced("loom"), "stonecutter": _faced("stonecutter"),
    "crafting": _plain("crafting_table", top=True), "fletching": _plain("fletching_table", top=True),
    "cartography": _plain("cartography_table", top=True), "composter": _plain("composter[level=5]"),
    "chiseled": lambda ctx, c, d: (ctx.set(c, 0, f"chiseled_bookshelf[facing={OPPOSITE[d]},slot_0_occupied=true,"
                                                 f"slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,"
                                                 f"slot_4_occupied=true,slot_5_occupied=false]"), [c])[1],
}


# ====================================================================== themes
# floor: weighted pieces along the walls; wall: decorations on the walls (above head height or above
# furniture); centre: what stands in the middle; rugs: carpet colours; ceiling: hanging light
THEMES = {
    "home": dict(floor={"barrel": 3, "crates": 2, "bookshelf": 2, "workbench": 2, "plant": 2, "pot": 1, "bed": 2,
                        "kitchen": 1, "chiseled": 1},
                 wall={"shelf": 3, "banner": 1}, centre="table", rugs=["red", "brown", "light_gray", "orange"],
                 density=0.45, ceiling="lantern"),
    "hall": dict(floor={"barrel": 2, "crates": 2, "pot": 2, "plant": 2, "armor_stand": 1, "bookshelf": 1,
                        "workbench": 1},
                 wall={"banner": 3, "shelf": 1}, centre="table", rugs=["red", "blue", "green"], density=0.3,
                 ceiling="chandelier"),
    "barracks": dict(floor={"bed": 4, "barrel": 2, "armor_stand": 2, "crates": 1, "grindstone": 1},
                     wall={"banner": 2, "shelf": 1}, centre="table", rugs=["gray", "blue"], density=0.5,
                     ceiling="lantern"),
    "kitchen": dict(floor={"kitchen": 4, "barrel": 3, "crates": 2, "produce": 2, "cauldron": 1, "smoker": 1},
                    wall={"shelf": 3}, centre="table", rugs=["brown"], density=0.55, ceiling="lantern",
                    shelf_items=["bread", "apple", "cooked_beef", "carrot", "baked_potato", "honey_bottle", "potato"]),
    "library": dict(floor={"bookshelf": 6, "chiseled": 2, "lectern": 1, "plant": 1, "barrel": 1},
                    wall={"shelf": 2, "banner": 1}, centre="table", rugs=["red", "green", "blue"], density=0.6,
                    ceiling="chandelier", tall_shelves=True,
                    shelf_items=["book", "writable_book", "enchanted_book", "paper", "map", "feather", "ink_sac"]),
    "chapel": dict(floor={"candles": 3, "plant": 2, "pot": 1, "lectern": 1, "bookshelf": 1, "brewing": 1},
                   wall={"banner": 2, "shelf": 1}, centre="pews", rugs=["red", "purple"], density=0.35,
                   ceiling="chandelier", shelf_items=["candle", "glass_bottle", "book", "glowstone_dust"]),
    "workshop": dict(floor={"workbench": 3, "smithing": 2, "anvil": 1, "grindstone": 1, "barrel": 2, "crates": 2,
                            "stonecutter": 1, "blast_furnace": 1, "furnace": 1},
                     wall={"shelf": 3, "banner": 1}, centre="table", rugs=["gray", "brown"], density=0.5,
                     ceiling="lantern", shelf_items=["iron_ingot", "copper_ingot", "shears", "compass", "clock",
                                                     "iron_chain", "iron_pickaxe", "bucket"]),
    "forge": dict(floor={"anvil": 2, "smithing": 2, "blast_furnace": 2, "grindstone": 1, "barrel": 2, "crates": 2,
                         "cauldron": 1},
                  wall={"shelf": 2, "banner": 1}, centre=None, rugs=[], density=0.45, ceiling="lantern",
                  shelf_items=["iron_ingot", "gold_ingot", "iron_sword", "iron_helmet", "coal", "raw_iron"]),
    "storage": dict(floor={"crates": 5, "barrel": 4, "hay": 2, "produce": 1, "pot": 1},
                    wall={"shelf": 1}, centre=None, rugs=[], density=0.6, ceiling="lantern"),
    "lab": dict(floor={"brewing": 3, "cauldron": 2, "bookshelf": 2, "barrel": 2, "lectern": 1, "workbench": 1,
                       "plant": 1},
                wall={"shelf": 3}, centre="table", rugs=["purple", "cyan"], density=0.45, ceiling="lantern",
                shelf_items=["glass_bottle", "potion", "redstone", "glowstone_dust", "blaze_powder", "nether_wart",
                             "spider_eye", "amethyst_shard"]),
    "steampunk": dict(floor={"machine": 3, "mahogany": 2, "workbench": 2, "crates": 2, "barrel": 1, "bookshelf": 1,
                             "plant": 1, "blast_furnace": 1},
                      wall={"cog": 2, "valve": 1, "brass_shelf": 2, "banner": 1}, centre="mahogany",
                      rugs=["red", "brown", "orange"], density=0.45, ceiling="edison",
                      shelf_items=["clock", "compass", "copper_ingot", "spyglass", "redstone", "book"]),
    "nether": dict(floor={"gold": 3, "blackstone": 2, "barrel": 2, "crates": 1, "pot": 1, "skull": 1},
                   wall={"banner": 2, "shelf": 1}, centre=None, rugs=["red", "black", "yellow"], density=0.4,
                   ceiling="soul_lantern", wood="crimson",
                   shelf_items=["gold_ingot", "gold_nugget", "golden_apple", "crimson_fungus", "quartz"],
                   banners=["red", "black", "yellow"]),
    "end": dict(floor={"end_rod": 2, "shulker": 2, "bookshelf": 2, "lectern": 1, "pot": 1},
                wall={"shelf": 1, "banner": 1}, centre=None, rugs=["purple", "magenta"], density=0.35,
                ceiling="end_rod", wood="warped",
                shelf_items=["ender_pearl", "chorus_fruit", "popped_chorus_fruit", "book", "ender_eye"],
                banners=["purple", "magenta", "black"]),
    "camp": dict(floor={"barrel": 3, "crates": 3, "hay": 2, "bed": 2, "workbench": 1, "grindstone": 1},
                 wall={"banner": 1}, centre=None, rugs=["brown", "gray"], density=0.4, ceiling="lantern"),
    "mine": dict(floor={"crates": 3, "barrel": 2, "rubble": 2, "workbench": 1, "furnace": 1, "anvil": 1},
                 wall={"shelf": 1}, centre=None, rugs=[], density=0.3, ceiling="lantern",
                 shelf_items=["iron_pickaxe", "torch", "coal", "raw_iron", "raw_copper", "bread"]),
    # abandoned places: dust, webs, rubble, moss, broken pots; few rugs, no new lights
    "ruin": dict(floor={"rubble": 4, "cobweb": 3, "barrel": 1, "pot": 2, "moss": 3, "skull": 1, "crates": 1,
                        "bookshelf": 1},
                 wall={"vine": 3, "web": 2}, centre=None, rugs=[], density=0.35, ceiling=None, ruined=True,
                 loot_barrels=2, tops=[None, None, None, "candle[candles=1,lit=false,waterlogged=false]"]),
    "crypt": dict(floor={"skull": 2, "bones": 2, "candles": 3, "cobweb": 3, "rubble": 2, "pot": 2},
                  wall={"web": 3, "vine": 1}, centre=None, rugs=[], density=0.3, ceiling=None, ruined=True,
                  loot_barrels=1, tops=[None, None, "candle[candles=1,lit=true,waterlogged=false]"]),
    "wreck": dict(floor={"barrel": 3, "crates": 2, "pot": 2, "sea_pickle": 3, "coral": 1},
                  wall={}, centre=None, rugs=[], density=0.35, ceiling=None, ruined=True, loot_barrels=1,
                  tops=[None, None, "sea_pickle[pickles=2,waterlogged=true]"]),
}


# ====================================================================== decorate
def decorate(bp, theme, seed=0, region=None, density=None, loot=None, rooms=None, min_area=9, max_rooms=None,
             rugs=True, lights=True, centre=True, walls=True, skip_decorated=True, sky_ok=False, ground=0,
             void_solid=False):
    """Furnish every room of ``bp`` (inside ``region``) in ``theme`` (a THEMES key or dict).
    Returns the rooms that were decorated."""
    T = dict(THEMES[theme]) if isinstance(theme, str) else dict(theme)
    rng = random.Random(f"{bp.name}:{seed}:{theme if isinstance(theme, str) else 'custom'}")
    rooms = rooms if rooms is not None else find_rooms(bp, region, min_area=min_area, sky_ok=sky_ok, ground=ground,
                                                       void_solid=void_solid)
    rooms.sort(key=lambda r: -r.area)
    if max_rooms:
        rooms = rooms[:max_rooms]
    done = []
    marked = getattr(bp, "_decor_cells", set())
    for room in rooms:
        if skip_decorated and sum(1 for c in room.cells if (c[0], room.y, c[1]) in marked) > room.area * 0.2:
            continue
        ctx = Ctx(bp, room, T, rng, loot)
        dens = density if density is not None else T.get("density", 0.4)
        if centre and T.get("centre") and room.area >= 30:
            _centre(ctx, T["centre"])
        _along_walls(ctx, T, dens)
        if walls:
            _wall_decor(ctx, T)
        if rugs and T.get("rugs") and room.area >= 20:
            _rug(ctx, T["rugs"])
        if lights and T.get("ceiling"):
            _ceiling_lights(ctx, T["ceiling"])
        if T.get("ruined"):
            _upper_webs(ctx)
        done.append(room)
    return done


def _wall_cells(ctx):
    room = ctx.room
    cells = [c for c in room.walls if c in room.free and c not in room.keep]
    ctx.rng.shuffle(cells)
    # corners first: a crate in a corner never narrows a passage
    cells.sort(key=lambda c: -len(room.walls[c]))
    return cells


def _along_walls(ctx, T, dens):
    room = ctx.room
    cells = _wall_cells(ctx)
    target = int(len(cells) * dens)
    weights = T["floor"]
    names = sorted(weights)
    placed = 0
    for c in cells:
        if placed >= target:
            break
        if c not in room.free:
            continue
        # leave every other wall cell open so the room reads as furnished, not filled
        if any((c[0] + dx, c[1] + dz) in room.occupied for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))\
                and ctx.rng.random() < 0.55:
            continue
        if not room.connected_without([c]):
            continue
        d = ctx.rng.choice(room.walls[c])
        name = ctx.rng.choices(names, [weights[n] for n in names])[0]
        cells_used = PIECES[name](ctx, c, d)
        if not cells_used:
            continue
        room.take(cells_used)
        placed += 1


def _free_block(room, c0, w, d):
    cells = [(c0[0] + i, c0[1] + j) for i in range(w) for j in range(d)]
    return cells if all(c in room.free and c not in room.keep and c not in room.walls for c in cells) else None


def _centre(ctx, kind):
    room = ctx.room
    cx, cz = room.centre()
    wood = ctx.wood
    if kind == "pews":
        return
    # find a 3x3 free block near the centre: table in the middle, chairs on its sides
    best = None
    for r in range(0, 4):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cells = _free_block(room, (cx + dx - 1, cz + dz - 1), 3, 3)
                if cells:
                    best = (cx + dx, cz + dz)
                    break
            if best:
                break
        if best:
            break
    if not best:
        return
    tx, tz = best
    long_x = (room.box[2] - room.box[0]) >= (room.box[3] - room.box[1])
    table = [(tx, tz)]
    if room.area >= 80:
        extra = (tx + 1, tz) if long_x else (tx, tz + 1)
        if _free_block(room, (extra[0] - 1, extra[1] - 1), 3, 3):
            table.append(extra)
    chairs = []
    for t in table:
        for d in HORIZONTAL:
            dx, dz = _dirvec(d)
            ch = (t[0] + dx, t[1] + dz)
            if ch not in table and ch not in [c for c, _ in chairs]:
                chairs.append((ch, d))  # the chair stands on side d of the table
    ctx.rng.shuffle(chairs)
    chairs = chairs[:max(2, len(chairs) - 2)]
    used = table + [c for c, _ in chairs]
    if not room.connected_without(used):
        chairs = chairs[:2]
        used = table + [c for c, _ in chairs]
        if not room.connected_without(used):
            return
    for t in table:
        if kind == "mahogany":
            ctx.set(t, 0, W + "mahogany_table")
        else:
            ctx.set(t, 0, f"{wood}_fence")
            ctx.set(t, 1, ctx.rng.choice([f"{wood}_pressure_plate", f"{wood}_pressure_plate",
                                          "candle[candles=3,lit=true,waterlogged=false]"])
                    if not ctx.wet() else f"{wood}_pressure_plate")
    for ch, side in chairs:
        if kind == "mahogany":
            # the chair model's seat opens to its facing: towards the table
            ctx.set(ch, 0, f"{W}mahogany_chair[facing={OPPOSITE[side]}]")
        else:
            # a stair seat: backrest (the tall half, on its facing side) away from the table
            ctx.bp.stairs(ch[0], ctx.y, ch[1], f"{wood}_stairs", side)
    room.take(used)


def _rug(ctx, colours):
    """A rug in the middle of the room: at most 7 x 5, bordered, only where the floor is still clear."""
    room = ctx.room
    x0, z0, x1, z1 = room.box
    w, d = x1 - x0 + 1, z1 - z0 + 1
    if w < 5 or d < 5:
        return
    if w > d:
        rw, rd = min(7, max(3, w - 4)), min(5, max(3, d - 4))
    else:
        rw, rd = min(5, max(3, w - 4)), min(7, max(3, d - 4))
    cx, cz = room.centre()
    best = None
    for r in range(0, 4):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                rect = [(cx + dx - rw // 2 + i, cz + dz - rd // 2 + j) for i in range(rw) for j in range(rd)]
                ok = sum(1 for c in rect if c in room.free) / len(rect)
                if ok >= 0.85 and all(c in room.cells for c in rect):
                    best = rect
                    break
            if best:
                break
        if best:
            break
    if not best:
        return
    colour = ctx.rng.choice(colours)
    edge = ctx.rng.choice([c for c in ("white", "yellow", "black", "light_gray", "orange") if c != colour])
    xs = [c[0] for c in best]
    zs = [c[1] for c in best]
    for c in best:
        if c in room.free and ctx.air(c, 0) and ctx.air(c, 1):
            border = c[0] in (min(xs), max(xs)) or c[1] in (min(zs), max(zs))
            ctx.set(c, 0, f"{edge if border else colour}_carpet")
            room.free.discard(c)


def _wall_decor(ctx, T):
    room = ctx.room
    wall = T.get("wall") or {}
    if not wall:
        return
    names = sorted(wall)
    # never above an entity (armor stand, villager) or a block we did not place
    cells = sorted(c for c in room.full_walls if c not in room.keep and c not in room.tall
                   and (c in room.free or c in room.occupied))
    ctx.rng.shuffle(cells)
    budget = max(1, len(cells) // 4)
    used_heights = set()
    for c in cells:
        if budget <= 0:
            break
        d = ctx.rng.choice(room.full_walls[c])
        occupied = c in room.occupied
        # above furniture: at y + 1; above an empty cell: at y + 2 (over the heads)
        dy = 1 if occupied else 2
        if room.head(c) < dy + 1 or not ctx.air(c, dy):
            continue
        if any((c[0] + a, c[1] + b, dy) in used_heights for a in (-1, 0, 1) for b in (-1, 0, 1)):
            continue
        kind = ctx.rng.choices(names, [wall[n] for n in names])[0]
        if not _wall_piece(ctx, c, d, dy, kind, T):
            continue
        used_heights.add((c[0], c[1], dy))
        budget -= 1


def _shelf_items(ctx, T):
    from . import nbt
    pool = T.get("shelf_items") or ["book", "candle", "flower_pot", "clock", "bread", "glass_bottle", "paper"]
    items = []
    for slot in range(3):
        if ctx.rng.random() < 0.75:
            items.append(nbt.Compound({"Slot": nbt.Byte(slot), "id": nbt.String("minecraft:" + ctx.rng.choice(pool)),
                                       "count": nbt.Int(ctx.rng.randint(1, 3))}))
    return {"Items": nbt.List(items, nbt.Compound)} if items else None


def _wall_piece(ctx, c, d, dy, kind, T):
    out = OPPOSITE[d]
    wet = ctx.wet()
    if kind == "banner":
        if dy < 2 or wet:
            return False
        colour = ctx.rng.choice(T.get("banners", ["red", "blue", "green", "yellow", "white", "black", "cyan"]))
        ctx.set(c, dy, f"{colour}_wall_banner[facing={out}]")
        return True
    if kind == "shelf":
        if wet:
            return False
        ctx.set(c, dy, f"{T.get('shelf_wood', ctx.wood)}_shelf[facing={out},powered=false,side_chain=unconnected,"
                       f"waterlogged=false]", _shelf_items(ctx, T))
        return True
    if kind == "brass_shelf":
        ctx.set(c, dy, f"{W}wall_shelf[facing={out}]")
        return True
    if kind == "cog":
        ctx.set(c, dy, f"{W}wall_cog[facing={out}]")
        return True
    if kind == "valve":
        ctx.set(c, dy, f"{W}valve_wheel[facing={out}]")
        return True
    if kind == "vine":
        for k in range(0, min(3, ctx.room.head(c) - 1)):
            yy = ctx.room.head(c) - 1 - k
            dx, dz = _dirvec(d)
            if yy < 1 or not ctx.air(c, yy) or not ctx.room.chk.full((c[0] + dx, ctx.y + yy, c[1] + dz), OPPOSITE[d]):
                break
            ctx.set(c, yy, f"vine[{d}=true]")
        return True
    if kind == "web":
        top = ctx.room.head(c) - 1
        if top >= 2 and ctx.air(c, top) and ctx.room.chk.full(ctx.at(c, top + 1), "down"):
            ctx.set(c, top, "cobweb")
            return True
        return False
    if kind == "torch":
        ctx.set(c, dy, f"wall_torch[facing={out}]")
        return True
    return False


def _upper_webs(ctx):
    """Cobwebs in the upper corners of abandoned rooms."""
    room = ctx.room
    for c, ds in sorted(room.walls.items()):
        if len(ds) >= 2 and c not in room.keep and ctx.rng.random() < 0.6:
            top = room.head(c) - 1
            if top >= 2 and ctx.air(c, top) and not ctx.wet() and room.chk.full(ctx.at(c, top + 1), "down"):
                ctx.set(c, top, "cobweb")


def _light_level(ctx):
    room = ctx.room
    n = 0
    x0, z0, x1, z1 = room.box
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for dy in range(-1, max(room.head((x, z)), 3) + 1):
                b = ctx.bp.blocks.get((x, ctx.y + dy, z))
                if b and any(h in _short(b[0]) for h in LIGHTS) and b[1].get("lit", "true") != "false":
                    n += 1
    return n


def _ceiling_lights(ctx, kind):
    room = ctx.room
    want = max(1, room.area // 45) - _light_level(ctx)
    if want <= 0:
        return
    chk = _checker(ctx.bp)
    inner = [c for c in sorted(room.cells) if c not in room.walls and room.head(c) >= 4]
    ctx.rng.shuffle(inner)
    placed = []
    for c in inner:
        if want <= 0:
            break
        if any(abs(c[0] - p[0]) + abs(c[1] - p[1]) < 6 for p in placed):
            continue
        h = room.head(c)
        if h > 12:
            continue
        ceil = (c[0], ctx.y + h, c[1])
        if not chk.center(ceil, "down"):
            continue
        low = max(2, h - 3) if kind != "chandelier" else max(3, h - 3)
        for yy in range(low + 1, h):
            ctx.set(c, yy, "iron_chain[axis=y,waterlogged=false]")
        if kind == "chandelier" and h >= 5 and not ctx.wet():
            # a lantern with four candle arms on chains
            ctx.set(c, low, "lantern[hanging=true,waterlogged=false]")
            for d in HORIZONTAL:
                dx, dz = _dirvec(d)
                n = (c[0] + dx, c[1] + dz)
                if all(ctx.air(n, yy) for yy in range(low, h)) and chk.center((n[0], ctx.y + h, n[1]), "down"):
                    for yy in range(low + 2, h):
                        ctx.set(n, yy, "iron_chain[axis=y,waterlogged=false]")
                    ctx.set(n, low + 1, "lantern[hanging=true,waterlogged=false]")
        else:
            spec = {"lantern": "lantern[hanging=true,waterlogged=false]",
                    "soul_lantern": "soul_lantern[hanging=true,waterlogged=false]",
                    "edison": W + "hanging_edison_lamp",
                    "end_rod": "end_rod[facing=down]",
                    "chandelier": "lantern[hanging=true,waterlogged=false]"}[kind]
            if kind == "edison":
                for yy in range(low, h):
                    ctx.set(c, yy, "air")
                ctx.set(c, h - 1, spec)
            elif kind == "end_rod":
                for yy in range(low, h):
                    ctx.set(c, yy, "air")
                ctx.set(c, h - 1, spec)
            else:
                ctx.set(c, low, spec)
        placed.append(c)
        want -= 1


# ====================================================================== entities
def villager(bp, x, y, z, profession, vtype="plains", level=2, facing=None, baby=False):
    """A villager that keeps its profession and never despawns (template entity, 26.2 NBT)."""
    from . import nbt
    lvl = max(1, min(5, level))
    xp = {1: 0, 2: 10, 3: 70, 4: 150, 5: 250}[lvl]
    data = {
        "id": "minecraft:villager",
        "PersistenceRequired": True,
        "NoAI": False,
        "VillagerData": {"type": f"minecraft:{vtype}", "profession": f"minecraft:{profession}", "level": lvl},
        "Xp": xp,
        "Rotation": nbt.List([nbt.Float(YAW.get(facing, 0.0)), nbt.Float(0.0)], nbt.Float),
    }
    if baby:
        data["Age"] = -24000
    bp.entity(x, y, z, data)
    _log_npc(bp, f"villager:{profession}")


def quest_npc(bp, x, y, z, role, facing=None):
    """A quest giver (brasshaven:wayfarer_npc, roles and contracts in wf/npcs.py): it stays where it is placed,
    cannot be hurt by players and never despawns. Its name and home are set by the game when it spawns."""
    from . import nbt, npcs
    if role not in npcs.ROLES:
        raise ValueError(f"unknown NPC role {role}")
    bp.entity(x, y, z, {"id": "brasshaven:wayfarer_npc", "Role": role, "PersistenceRequired": True,
                        "Rotation": nbt.List([nbt.Float(YAW.get(facing, 0.0)), nbt.Float(0.0)], nbt.Float)})
    _log_npc(bp, f"npc:{role}")


def quest_npc_in(bp, role, region=None, seed=0, ground=0, void_solid=False, rooms=None):
    """Put a quest giver on a free floor cell of the biggest room of ``region``, near its middle, away from doors
    and stairs and without cutting the room in two. Raises when there is no room for it."""
    rooms = rooms if rooms is not None else find_rooms(bp, region, ground=ground, void_solid=void_solid)
    rng = random.Random(f"{bp.name}:npc:{role}:{seed}")
    for room in sorted(rooms, key=lambda r: -r.area):
        cx, cz = room.centre()
        cells = [c for c in room.free - room.keep - room.occupied
                 if _air_at(bp, room.chk, (c[0], room.y, c[1])) and _air_at(bp, room.chk, (c[0], room.y + 1, c[1]))
                 and _air_at(bp, room.chk, (c[0], room.y + 2, c[1]))]
        cells.sort(key=lambda c: (abs(c[0] - cx) + abs(c[1] - cz), rng.random()))
        for c in cells:
            if room.connected_without([c]):
                facing = min(HORIZONTAL, key=lambda d: (c[0] + _dirvec(d)[0] * 3 - cx) ** 2 +
                             (c[1] + _dirvec(d)[1] * 3 - cz) ** 2) if (c[0], c[1]) != (cx, cz) else "south"
                quest_npc(bp, c[0], room.y, c[1], role, facing=facing)
                room.take([c])
                return (c[0], room.y, c[1])
    raise ValueError(f"{bp.name}: no room for the {role} in {region}")


def wandering_trader(bp, x, y, z, facing=None):
    from . import nbt
    bp.entity(x, y, z, {"id": "minecraft:wandering_trader", "PersistenceRequired": True, "DespawnDelay": 0,
                        "Rotation": nbt.List([nbt.Float(YAW.get(facing, 0.0)), nbt.Float(0.0)], nbt.Float)})
    _log_npc(bp, "wandering_trader")


def iron_golem(bp, x, y, z):
    bp.entity(x, y, z, {"id": "minecraft:iron_golem", "PersistenceRequired": True, "PlayerCreated": False})
    _log_npc(bp, "iron_golem")


def brass_golem(bp, x, y, z):
    """The mod's Brass Golem, guarding the spot it stands on (Guarding with no GuardPos: it guards where
    it is placed, see BrassGolem.anchor)."""
    bp.entity(x, y, z, {"id": "brasshaven:brass_golem", "PersistenceRequired": True, "Guarding": True})
    _log_npc(bp, "brass_golem")


def crowd(bp, data, count, region=None, seed=0, ground=0, void_solid=False, label=None):
    """Put ``count`` copies of the entity ``data`` (an NBT dict with "id") on free floor cells of the rooms of
    ``region``, away from doors and stairs. Returns the cells used."""
    rng = random.Random(f"{bp.name}:crowd:{seed}:{data.get('id')}")
    rooms = find_rooms(bp, region, ground=ground, void_solid=void_solid)
    cells = [(c[0], r.y, c[1]) for r in rooms for c in sorted(r.free - r.keep)
             if _air_at(bp, r.chk, (c[0], r.y, c[1])) and _air_at(bp, r.chk, (c[0], r.y + 1, c[1]))]
    rng.shuffle(cells)
    used = []
    for (x, y, z) in cells:
        if len(used) >= count:
            break
        if any(abs(x - a) + abs(z - b) < 4 and y == yy for a, yy, b in used):
            continue
        d = dict(data)
        d["Rotation"] = [float(rng.choice([0, 90, 180, 270])), 0.0]
        bp.entity(x, y, z, d)
        _log_npc(bp, label or data["id"].split(":")[1])
        used.append((x, y, z))
    return used


def open_spot(bp, at, ground=0, void_solid=False, height=3, reach=8):
    """The nearest cell to ``at`` with a sturdy floor and ``height`` passable cells above it (somewhere for a
    golem to stand). Falls back to ``at``."""
    chk = _checker(bp, ground, void_solid)
    x0, y0, z0 = at
    best = None
    for r in range(reach + 1):
        for dy in (0, 1, -1, 2, -2):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if max(abs(dx), abs(dz)) != r:
                        continue
                    p = (x0 + dx, y0 + dy, z0 + dz)
                    if not chk.full((p[0], p[1] - 1, p[2]), "up"):
                        continue
                    if all(chk.passable((p[0], p[1] + k, p[2])) and bp.get(p[0], p[1] + k, p[2]) in
                           (None, "minecraft:air", "minecraft:cave_air") for k in range(height)):
                        best = p
                        break
                if best:
                    return best
    return at


def _log_npc(bp, what):
    log = getattr(bp, "npcs", None)
    if log is None:
        log = bp.npcs = []
    log.append(what)


# ====================================================================== residents
JOB_SITE = {
    "librarian": lambda d: f"lectern[facing={d},has_book=false,powered=false]",
    "cleric": lambda d: "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=false]",
    "armorer": lambda d: f"blast_furnace[facing={d},lit=false]",
    "toolsmith": lambda d: "smithing_table",
    "weaponsmith": lambda d: f"grindstone[face=floor,facing={CW[OPPOSITE[d]]}]",
    "cartographer": lambda d: "cartography_table",
    "farmer": lambda d: "composter[level=3]",
    "fisherman": lambda d: f"barrel[facing={d},open=false]",
    "fletcher": lambda d: "fletching_table",
    "leatherworker": lambda d: "water_cauldron[level=3]",
    "mason": lambda d: f"stonecutter[facing={d}]",
    "shepherd": lambda d: f"loom[facing={d}]",
    "butcher": lambda d: f"smoker[facing={d},lit=false]",
}


def populate(bp, residents, region=None, vtype="plains", seed=0, rooms=None, beds=True, bell=None, guard=None,
             bed_colour=None, ground=0, void_solid=False):
    """Settle ``residents`` (list of professions, or (profession, level) pairs) in the rooms of ``region``:
    each gets its job-site block against a wall, a bed nearby and stands in the room. ``bell`` (x, y, z):
    a floor bell as meeting point. ``guard``: ("iron"|"brass", (x, y, z)). Returns the villager spots."""
    rng = random.Random(f"{bp.name}:residents:{seed}")
    rooms = rooms if rooms is not None else find_rooms(bp, region, ground=ground, void_solid=void_solid)
    rooms = [r for r in rooms if r.area >= 9]
    rooms.sort(key=lambda r: -r.area)
    spots = []
    if bell:
        bx, by, bz = bell
        bp.set(bx, by, bz, "bell[attachment=floor,facing=north,powered=false]")
    if guard:
        kind, at = guard
        gx, gy, gz = open_spot(bp, at, ground=ground, void_solid=void_solid)
        (brass_golem if kind == "brass" else iron_golem)(bp, gx, gy, gz)
    if not rooms:
        return spots
    beds_before = _count_beds(bp) if beds else 0
    for i, res in enumerate(residents):
        prof, lvl = (res if isinstance(res, tuple) else (res, 2))
        placed = False
        for k in range(len(rooms)):
            room = rooms[(i + k) % len(rooms)]
            spot = _settle_one(bp, room, prof, lvl, vtype, rng, beds, bed_colour)
            if spot:
                spots.append(spot)
                placed = True
                break
        if not placed:
            # no wall left anywhere: the villager still moves in (it keeps its profession at level >= 2)
            room = rooms[i % len(rooms)]
            free = sorted(room.free - room.occupied)
            if free:
                c = rng.choice(free)
                villager(bp, c[0], room.y, c[1], prof, vtype, lvl)
                spots.append((c[0], room.y, c[1]))
    if beds:
        # a bed for everyone: those whose room had no wall left for one sleep in another room of the region
        missing = len(spots) - (_count_beds(bp) - beds_before)
        for _ in range(max(0, missing)):
            if not _extra_bed(bp, rooms, rng, bed_colour):
                break
    return spots


def _count_beds(bp):
    return sum(1 for b in bp.blocks.values() if b[0].endswith("_bed") and b[1].get("part") == "head")


def _extra_bed(bp, rooms, rng, bed_colour):
    """One more bed against any free wall of ``rooms`` (biggest first); False when none fits."""
    for room in rooms:
        ctx = Ctx(bp, room, {"beds": [bed_colour] if bed_colour else ["red", "white", "light_blue", "lime"]}, rng)
        for c in sorted(c for c in room.walls if c in room.free and c not in room.keep):
            for d in room.walls[c]:
                got = p_bed(ctx, c, d)
                if got:
                    room.take(got)
                    return True
    return False


def _settle_one(bp, room, prof, lvl, vtype, rng, beds, bed_colour):
    ctx = Ctx(bp, room, {"beds": [bed_colour] if bed_colour else ["red", "white", "light_blue", "lime", "yellow"]},
              rng)
    cells = [c for c in room.walls if c in room.free and c not in room.keep]
    rng.shuffle(cells)
    cells.sort(key=lambda c: -len(room.walls[c]))
    job = None
    for c in cells:
        if room.connected_without([c]):
            d = rng.choice(room.walls[c])
            spec = JOB_SITE[prof](OPPOSITE[d])
            ctx.set(c, 0, spec)
            room.take([c])
            job = c
            break
    if job is None:
        return None
    if beds:
        for c in sorted(cells, key=lambda c: abs(c[0] - job[0]) + abs(c[1] - job[1])):
            if c in room.free and c not in room.keep:
                d = rng.choice(room.walls[c])
                # the head against any wall of that cell (the first pick first)
                got = None
                for dd in [d] + [w for w in room.walls[c] if w != d]:
                    got = p_bed(ctx, c, dd)
                    if got:
                        break
                if got:
                    room.take(got)
                    break
    # stand next to the job site
    stand = sorted((c for c in room.free if c not in room.occupied),
                   key=lambda c: abs(c[0] - job[0]) + abs(c[1] - job[1]))
    stand = [c for c in stand if _air_at(bp, room.chk, (c[0], room.y, c[1]))
             and _air_at(bp, room.chk, (c[0], room.y + 1, c[1]))]
    if not stand:
        return None
    c = stand[0]
    facing = None
    for d in HORIZONTAL:
        dx, dz = _dirvec(d)
        if (c[0] + dx, c[1] + dz) == job:
            facing = d
    villager(bp, c[0], room.y, c[1], prof, vtype, lvl, facing=facing)
    room.free.discard(c)  # nothing else goes where somebody stands
    return (c[0], room.y, c[1])


# ====================================================================== outside: yards and props
GROUND = {"grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "moss_block", "sand", "red_sand",
          "snow_block", "mud", "packed_mud", "pale_moss_block", "mycelium", "soul_soil", "crimson_nylium",
          "warped_nylium", "end_stone", "netherrack", "terracotta"}
SOFT = ("short_grass", "fern", "dandelion", "poppy", "cornflower", "azure_bluet", "oxeye_daisy", "allium",
        "tulip", "leaf_litter", "petals", "wildflowers", "dry_grass", "bush", "snow")


def _yard_ok(bp, x, y, z, roof=10):
    """Open ground at (x, y, z): nothing built there or above, explicitly set soil below."""
    b = bp.blocks.get((x, y, z))
    if b is not None and b[0] not in AIR and not any(s in _short(b[0]) for s in SOFT):
        return False
    below = bp.blocks.get((x, y - 1, z))
    if below is None or _short(below[0]) not in GROUND:
        return False
    for yy in range(y + 1, y + roof):
        bb = bp.blocks.get((x, yy, z))
        if bb is not None and bb[0] not in AIR and not any(s in _short(bb[0]) for s in SOFT):
            return False
    return True


def _ring_clear(bp, cells, y, ring=1):
    """No building, path or prop within ``ring`` of the footprint (keeps walkways open)."""
    fp = set(cells)
    for (x, z) in cells:
        for dx in range(-ring, ring + 1):
            for dz in range(-ring, ring + 1):
                q = (x + dx, z + dz)
                if q in fp:
                    continue
                if not _yard_ok(bp, q[0], y, q[1], roof=4):
                    return False
    return True


def _clear_soft(bp, x, y, z):
    b = bp.blocks.get((x, y, z))
    if b and any(s in _short(b[0]) for s in SOFT):
        if b[1].get("half") == "lower":
            bp.blocks.pop((x, y + 1, z), None)
        bp.set(x, y, z, "air")


def y_hay(bp, x, y, z, rng, d):
    cells = [(x, z), (x + 1, z)] if d in ("east", "west") else [(x, z), (x, z + 1)]
    ax = "x" if d in ("east", "west") else "z"
    for (a, b) in cells:
        bp.set(a, y, b, f"hay_block[axis={ax}]")
    bp.set(cells[0][0], y + 1, cells[0][1], "hay_block[axis=y]")
    return cells


def y_crates(bp, x, y, z, rng, d):
    cells = [(x, z), (x + 1, z), (x, z + 1)]
    for i, (a, b) in enumerate(cells):
        bp.set(a, y, b, "barrel[facing=up,open=false]" if i else "barrel[facing=north,open=false]")
    bp.set(x, y + 1, z, "barrel[facing=up,open=false]")
    if rng.random() < 0.5:
        bp.set(x + 1, y + 1, z, "lantern[hanging=false,waterlogged=false]")
    return cells


def y_woodpile(bp, x, y, z, rng, d, log="spruce_log"):
    ax = "x" if d in ("east", "west") else "z"
    cells = [(x, z), (x + 1, z), (x + 2, z)] if ax == "z" else [(x, z), (x, z + 1), (x, z + 2)]
    for a, b in cells:
        bp.set(a, y, b, f"{log}[axis={ax}]")
    for a, b in cells[:2]:
        bp.set(a, y + 1, b, f"{log}[axis={ax}]")
    if rng.random() < 0.6:
        e = cells[2]
        bp.set(e[0], y + 1, e[1], "spruce_slab[type=bottom,waterlogged=false]")
    return cells


def y_cart(bp, x, y, z, rng, d, wood="spruce"):
    """A hand cart: plank bed on two wheels, a shaft in front, a load on top."""
    if d in ("east", "west"):
        bed = [(x, z), (x + 1, z)]
        wheels = [((x, z - 1), "north"), ((x, z + 1), "south")]
        shaft = (x + 2, z) if d == "east" else (x - 1, z)
    else:
        bed = [(x, z), (x, z + 1)]
        wheels = [((x - 1, z), "west"), ((x + 1, z), "east")]
        shaft = (x, z + 2) if d == "south" else (x, z - 1)
    for a, b in bed:
        bp.set(a, y, b, f"{wood}_slab[type=top,waterlogged=false]")
    for (a, b), f in wheels:
        # an open trapdoor facing f stands against the side opposite f: the cart side
        bp.set(a, y, b, f"dark_oak_trapdoor[facing={f},half=bottom,open=true,powered=false,waterlogged=false]")
    bp.set(shaft[0], y, shaft[1], f"{wood}_fence")
    load = rng.choice(["hay_block[axis=y]", "barrel[facing=up,open=false]", "pumpkin", "melon",
                       "composter[level=8]"])
    bp.set(bed[0][0], y + 1, bed[0][1], load)
    return bed + [w for w, _ in wheels] + [shaft]


def y_well(bp, x, y, z, rng, d, stone="cobblestone", roof="spruce"):
    cells = [(x + a, z + b) for a in range(3) for b in range(3)]
    for (a, b) in cells:
        for yy in range(y - 4, y):
            bp.set(a, yy, b, stone)
        bp.set(a, y, b, "mossy_cobblestone" if rng.random() < 0.4 else stone)
    for yy in range(y - 3, y + 1):
        bp.set(x + 1, yy, z + 1, "water[level=0]")
    for a, b in ((x, z), (x + 2, z), (x, z + 2), (x + 2, z + 2)):
        bp.set(a, y + 1, b, f"{roof}_fence")
        bp.set(a, y + 2, b, f"{roof}_fence")
    for a in range(3):
        for b in range(3):
            bp.set(x + a, y + 3, z + b, f"{roof}_slab[type=bottom,waterlogged=false]")
    bp.set(x + 1, y + 3, z + 1, f"{roof}_planks")
    bp.set(x + 1, y + 2, z + 1, "iron_chain[axis=y,waterlogged=false]")
    return cells


def y_crops(bp, x, y, z, rng, d, w=5, l=6):
    """A small field: farmland rows with a water channel in the middle and a fence-post border."""
    crop = rng.choice(["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]", "wheat[age=5]"])
    cells = []
    mid = x + w // 2
    for a in range(x, x + w):
        for b in range(z, z + l):
            cells.append((a, b))
            if a == mid:
                bp.set(a, y - 1, b, "water[level=0]")
                bp.set(a, y - 2, b, "dirt")
                if b in (z, z + l - 1):
                    bp.set(a, y - 1, b, "oak_log[axis=z]")
            else:
                bp.set(a, y - 1, b, "farmland[moisture=7]")
                bp.set(a, y, b, crop)
    return cells


def y_garden(bp, x, y, z, rng, d):
    cells = [(x + a, z + b) for a in range(3) for b in range(2)]
    for (a, b) in cells:
        bp.set(a, y - 1, b, "coarse_dirt" if rng.random() < 0.3 else "podzol")
        bp.set(a, y, b, rng.choice(["rose_bush[half=lower]", "peony[half=lower]", "lilac[half=lower]",
                                    "poppy", "cornflower", "allium", "oxeye_daisy", "sweet_berry_bush[age=3]"]))
        top = bp.blocks[(a, y, b)]
        if top[1].get("half") == "lower":
            bp.set(a, y + 1, b, (top[0], dict(top[1], half="upper")))
    return cells


def y_signpost(bp, x, y, z, rng, d, wood="spruce"):
    bp.set(x, y, z, f"{wood}_fence")
    bp.set(x, y + 1, z, f"{wood}_fence")
    rot = {"south": 0, "west": 4, "north": 8, "east": 12}[d]
    bp.set(x, y + 2, z, f"{wood}_sign[rotation={rot},waterlogged=false]")
    return [(x, z)]


def y_lamp(bp, x, y, z, rng, d, post="spruce_fence", soul=False):
    for yy in range(y, y + 3):
        bp.set(x, yy, z, post)
    bp.set(x, y + 3, z, f"{'soul_' if soul else ''}lantern[hanging=false,waterlogged=false]")
    return [(x, z)]


def y_bench(bp, x, y, z, rng, d, wood="spruce"):
    """Two stair seats with trapdoor arm rests, facing ``d``."""
    if d in ("north", "south"):
        seats = [(x, z), (x + 1, z)]
        arms = [((x - 1, z), "west"), ((x + 2, z), "east")]
    else:
        seats = [(x, z), (x, z + 1)]
        arms = [((x, z - 1), "north"), ((x, z + 2), "south")]
    for a, b in seats:
        bp.stairs(a, y, b, f"{wood}_stairs", OPPOSITE[d])
    for (a, b), f in arms:
        bp.set(a, y, b, f"{wood}_trapdoor[facing={f},half=bottom,open=true,powered=false,waterlogged=false]")
    return seats + [a for a, _ in arms]


def y_campfire(bp, x, y, z, rng, d, wood="spruce"):
    """Campfire ringed by log seats."""
    bp.set(x + 1, y, z + 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    seats = []
    for a, b, ax in ((x, z + 1, "z"), (x + 2, z + 1, "z"), (x + 1, z, "x"), (x + 1, z + 2, "x")):
        if rng.random() < 0.8:
            bp.set(a, y, b, f"stripped_{wood}_log[axis={ax}]")
            seats.append((a, b))
    return [(x + 1, z + 1)] + seats


def y_smithy(bp, x, y, z, rng, d):
    cells = [(x, z), (x + 1, z)]
    bp.set(x, y, z, f"anvil[facing={'east' if d in ('north', 'south') else 'north'}]")
    bp.set(x + 1, y, z, "smithing_table")  # (a floor grindstone needs a sturdy block: grass does not count)
    return cells


def y_banner(bp, x, y, z, rng, d, colour="red", post="spruce_fence"):
    for yy in range(y, y + 3):
        bp.set(x, yy, z, post)
    bp.set(x, y + 3, z, f"{colour}_banner[rotation={rng.randint(0, 15)}]")
    return [(x, z)]


YARD = {
    "farm": {"hay": 3, "crates": 2, "cart": 2, "woodpile": 2, "crops": 3, "garden": 2, "lamp": 1, "bench": 1,
             "well": 1, "signpost": 1},
    "village": {"hay": 1, "crates": 2, "cart": 2, "woodpile": 2, "garden": 3, "lamp": 2, "bench": 2, "well": 1,
                "signpost": 1, "crops": 1},
    "camp": {"hay": 2, "crates": 3, "cart": 1, "woodpile": 3, "campfire": 2, "smithy": 1, "banner": 1},
    "garden": {"garden": 4, "bench": 2, "lamp": 2},
    "harbour": {"crates": 4, "cart": 2, "hay": 1, "lamp": 2, "bench": 1, "woodpile": 1, "signpost": 1},
    "ruin": {"woodpile": 1, "crates": 1, "cart": 1},
}
YARD_FNS = {"hay": (y_hay, 2), "crates": (y_crates, 2), "woodpile": (y_woodpile, 3), "cart": (y_cart, 3),
            "well": (y_well, 3), "crops": (y_crops, 6), "garden": (y_garden, 3), "signpost": (y_signpost, 1),
            "lamp": (y_lamp, 1), "bench": (y_bench, 4), "campfire": (y_campfire, 3), "smithy": (y_smithy, 2),
            "banner": (y_banner, 1)}


def _footprint(kind, x, z, d):
    if kind == "hay":
        return [(x, z), (x + 1, z)] if d in ("east", "west") else [(x, z), (x, z + 1)]
    if kind == "crates":
        return [(x, z), (x + 1, z), (x, z + 1)]
    if kind == "woodpile":
        return [(x, z), (x + 1, z), (x + 2, z)] if d in ("north", "south") else [(x, z), (x, z + 1), (x, z + 2)]
    if kind == "cart":
        if d in ("east", "west"):
            return [(x - 1, z), (x, z), (x + 1, z), (x + 2, z), (x, z - 1), (x, z + 1)]
        return [(x, z - 1), (x, z), (x, z + 1), (x, z + 2), (x - 1, z), (x + 1, z)]
    if kind in ("well", "campfire"):
        return [(x + a, z + b) for a in range(3) for b in range(3)]
    if kind == "crops":
        return [(x + a, z + b) for a in range(5) for b in range(6)]
    if kind == "garden":
        return [(x + a, z + b) for a in range(3) for b in range(2)]
    if kind == "bench":
        return [(x - 1, z), (x, z), (x + 1, z), (x + 2, z)] if d in ("north", "south") else \
            [(x, z - 1), (x, z), (x, z + 1), (x, z + 2)]
    if kind == "smithy":
        return [(x, z), (x + 1, z)]
    return [(x, z)]


def yard(bp, area, y, theme="village", count=8, seed=0, ring=1, avoid=()):
    """Scatter ``count`` props of ``theme`` (a YARD key or {kind: weight}) on open soil inside
    ``area`` (x0, z0, x1, z1) at level ``y`` (the first block above the ground). ``avoid``: extra (x, z)
    cells to keep free (paths, gates). Returns the kinds placed."""
    weights = YARD[theme] if isinstance(theme, str) else theme
    rng = random.Random(f"{bp.name}:yard:{seed}:{area}")
    x0, z0, x1, z1 = area
    spots = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]
    rng.shuffle(spots)
    names = sorted(weights)
    avoid = set(avoid)
    # never on someone's feet (villagers and quest givers placed before the yard)
    avoid |= {(ex, ez) for ex, ey, ez in _entity_cells(bp) if y - 1 <= ey <= y + 2}
    taken = set()
    placed = []
    singles = {"well": 0, "crops": 0}
    for (x, z) in spots:
        if len(placed) >= count:
            break
        kind = rng.choices(names, [weights[n] for n in names])[0]
        if kind in singles:
            if singles[kind] >= (1 if kind == "well" else 2):
                continue
        d = rng.choice(HORIZONTAL)
        fp = _footprint(kind, x, z, d)
        if any(c in taken or c in avoid for c in fp):
            continue
        if not all(_yard_ok(bp, a, y, b) for a, b in fp):
            continue
        if not _ring_clear(bp, fp, y, ring + (1 if kind in ("well", "crops", "campfire") else 0)):
            continue
        for a, b in fp:
            _clear_soft(bp, a, y, b)
        fn = YARD_FNS[kind][0]
        fn(bp, x, y, z, rng, d)
        for a, b in fp:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    taken.add((a + dx, b + dz))
        if kind in singles:
            singles[kind] += 1
        placed.append(kind)
    return placed
