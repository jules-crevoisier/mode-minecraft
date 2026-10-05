"""Wayfarers pieces for the vanilla villages and pillager outposts.

Vanilla villages are jigsaw structures whose pools live in ``data/minecraft/worldgen/template_pool/village/<type>``.
We override those pool files with copies that keep every vanilla element and weight (``wf/vanilla_pools.py`` reads
them from the 26.2 sources) and add our pieces, built here in each village's own materials with steampunk touches:

  town_centers  a plaza with a Waystone, a notice board, a meeting bell, lamps, benches and flower beds
  houses        the Wayfarers' Inn (guild hall), a tinkerer's workshop, a watchtower, market stalls, an orchard,
                a cottage and a manor, a well corner (street furniture)
  streets       a lamp-lined avenue
  decor         a brass street lamp and a signpost (1 x 1, they stand on the street side like the vanilla lamps)

Outposts get a steam siege engine and a barricade in ``pillager_outpost/features``.

Jigsaw conventions (vanilla 1.14 village data, upgraded by JigsawPropertiesFix: name = target = the old
``attachement_type``; checked against the server jar by tools/ci_smoke.py):
  * a street connects to a house through a street jigsaw whose target is ``minecraft:building_entrance``: our
    houses face north, their entrance jigsaw (name ``minecraft:building_entrance``, pool ``minecraft:empty``,
    orientation north_up) sits at walking level on the template's north edge, the path under it;
  * streets join streets through ``minecraft:street`` jigsaws (the plaza's four exits, the avenue's two ends);
  * decorations stand on an upward street jigsaw targeting ``minecraft:bottom``: ours have a downward
    ``minecraft:bottom`` jigsaw at their base, like the feature elements (FeaturePoolElement);
  * golems, cats and loose villagers come from the vanilla pools through upward ``minecraft:bottom`` jigsaws.

Coordinates: x east, y up, z south, y = 0 is the ground layer, walking level y = 1, the street is to the north
(z < 0). Rigid pieces attached to a street get the right ground level from the jigsaw (the beard flattens the
terrain at the walking level) and carry a foundation below y = 0; the plaza (the start piece) says its ground
depth through ``wayfarers:grounded_single`` (com.wayfarers.world.GroundedPoolElement).
"""
import copy
import math
import random

from . import arch as A
from . import interior as I
from . import nbt
from .arch import Palette
from .blueprint import Blueprint, OPPOSITE, with_props

W = "wayfarers:"
TYPES = ["plains", "desert", "savanna", "snowy", "taiga"]
ENTRANCE = "minecraft:building_entrance"
STREET = "minecraft:street"
BOTTOM = "minecraft:bottom"
# the outpost feature plates' upward jigsaws target minecraft:feature (checked against the server jar in CI)
FEATURE = "minecraft:feature"
EMPTY = "minecraft:empty"
GROUNDED = W + "grounded_single"

EDISON = W + "edison_lamp"
HANG_EDISON = W + "hanging_edison_lamp"
IRON_WALL = W + "dark_iron_plating_wall"
IRON = W + "dark_iron_plating"
BRASS = W + "brass_plating"
BRASS_SLAB = W + "brass_plating_slab"
BRASS_STAIRS = W + "brass_plating_stairs"
GEAR = W + "gear_panel"
GAUGE = W + "pressure_gauge"
PIPES = W + "copper_pipes"
SMOKE = W + "smokestack_bricks"
SMOKE_WALL = W + "smokestack_brick_wall"
MAHOGANY = W + "mahogany_panelling"


def stair(spec, facing, half="bottom"):
    return A.stair(spec, facing, half)


def slab(spec, kind="bottom"):
    return A.slab(spec, kind)


def col(spec):
    """A post block standing upright (logs and pillars get axis=y)."""
    s = spec.split("[")[0]
    if s.endswith(("_log", "_wood", "_stem", "_hyphae", "basalt", "quartz_pillar", "marble_pillar")):
        return with_props(spec, axis="y")
    return spec


def axis_of(spec, axis):
    s = spec.split("[")[0]
    if s.endswith(("_log", "_wood", "_stem", "_hyphae", "basalt", "quartz_pillar", "marble_pillar")):
        return with_props(spec, axis=axis)
    return spec


def leaves(spec):
    return with_props(spec, persistent=True, distance=1, waterlogged=False)


# ====================================================================== styles
class Style:
    def __init__(self, key, **kw):
        self.key = key
        self.__dict__.update(kw)
        self.R = self.roof

    def fence(self):
        return f"{self.wood}_fence"

    def planks(self):
        return f"{self.wood}_planks"

    def stairs(self):
        return f"{self.wood}_stairs"

    def slab(self):
        return f"{self.wood}_slab"

    def trapdoor(self, facing, half="bottom", open_=True):
        return f"{self.wood}_trapdoor[facing={facing},half={half},open={str(open_).lower()},powered=false," \
               f"waterlogged=false]"

    def gate(self, facing):
        return f"{self.wood}_fence_gate[facing={facing},in_wall=false,open=false,powered=false]"


STYLES = {
    "plains": Style(
        "plains", vtype="plains", wood="oak", post="oak_log", beam="stripped_oak_log",
        plinth=Palette({"cobblestone": 3, "stone_bricks": 3, "andesite": 1}, seed=11),
        floor="spruce_planks", wall=Palette({"oak_planks": 1}), upper=Palette({"calcite": 5, "white_terracotta": 1}, seed=3),
        roof=(W + "guild_roof_tiles", W + "guild_roof_tile_stairs", W + "guild_roof_tile_slab"), flat=False,
        pane="glass_pane", metal=(BRASS, BRASS_STAIRS, BRASS_SLAB),
        pave=Palette({"stone_bricks": 4, "polished_andesite": 2, "cobblestone": 1, "andesite": 1}, seed=5),
        accent_pave="polished_andesite", path=Palette({"dirt_path": 4, "gravel": 1, "coarse_dirt": 1}, seed=7),
        ground="grass_block[snowy=false]", planter="moss_block", lamp_base="polished_andesite",
        flowers=["poppy", "dandelion", "cornflower", "azure_bluet", "oxeye_daisy", "allium", "red_tulip"],
        tree="oak", tree_log="oak_log", tree_leaves="oak_leaves", fruit="flowering_azalea_leaves",
        awnings=["red", "white", "yellow", "blue"], banner="blue", bed="red",
        crops=["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]"],
        sign="oak", residents=["farmer", "shepherd", "fletcher", "mason", "leatherworker"]),
    "desert": Style(
        "desert", vtype="desert", wood="jungle", post="cut_sandstone", beam="smooth_sandstone",
        plinth=Palette({"cut_sandstone": 3, "sandstone": 2}, seed=12),
        floor="smooth_sandstone", wall=Palette({"smooth_sandstone": 4, "sandstone": 2, "cut_sandstone": 1}, seed=4),
        upper=Palette({"smooth_sandstone": 4, "sandstone": 1}, seed=8),
        roof=("smooth_sandstone", "smooth_sandstone_stairs", "smooth_sandstone_slab"), flat=True,
        dome=(W + "copper_tiles", W + "copper_tile_stairs", W + "copper_tile_slab"),
        pane="glass_pane", metal=(W + "copper_plating", W + "copper_plating_stairs", W + "copper_plating_slab"),
        pave=Palette({"smooth_sandstone": 4, "cut_sandstone": 2, "sandstone": 1}, seed=6),
        accent_pave="cut_red_sandstone", path=Palette({"smooth_sandstone": 3, "sandstone": 2}, seed=9),
        ground="sand", planter="coarse_dirt", lamp_base="cut_sandstone",
        flowers=["dead_bush", "orange_tulip", "red_tulip", "allium", "dead_bush", "short_dry_grass"],
        tree="palm", tree_log="jungle_log", tree_leaves="jungle_leaves", fruit="jungle_leaves",
        awnings=["orange", "white", "cyan", "red"], banner="orange", bed="orange",
        crops=["wheat[age=7]", "beetroots[age=3]", "potatoes[age=7]", "carrots[age=7]"],
        sign="jungle", residents=["farmer", "leatherworker", "mason", "cleric", "fletcher"]),
    "savanna": Style(
        "savanna", vtype="savanna", wood="acacia", post="acacia_log", beam="stripped_acacia_log",
        plinth=Palette({"cobblestone": 2, "terracotta": 2, "granite": 1}, seed=13),
        floor="acacia_planks", wall=Palette({"acacia_planks": 1}),
        upper=Palette({"orange_terracotta": 4, "terracotta": 1}, seed=5),
        roof=(W + "crimson_roof_tiles", W + "crimson_roof_tile_stairs", W + "crimson_roof_tile_slab"), flat=False,
        pane="glass_pane", metal=(W + "copper_plating", W + "copper_plating_stairs", W + "copper_plating_slab"),
        pave=Palette({"terracotta": 2, "packed_mud": 3, "mud_bricks": 2, "smooth_red_sandstone": 1}, seed=7),
        accent_pave="mud_bricks", path=Palette({"dirt_path": 4, "coarse_dirt": 2}, seed=10),
        ground="grass_block[snowy=false]", planter="rooted_dirt", lamp_base="terracotta",
        flowers=["dandelion", "orange_tulip", "red_tulip", "poppy", "short_dry_grass", "allium"],
        tree="acacia", tree_log="acacia_log", tree_leaves="acacia_leaves", fruit="acacia_leaves",
        awnings=["orange", "yellow", "red", "lime"], banner="orange", bed="yellow",
        crops=["wheat[age=7]", "melon_stem[age=7]", "carrots[age=7]", "potatoes[age=7]"],
        sign="acacia", residents=["farmer", "shepherd", "butcher", "leatherworker", "fletcher"]),
    "snowy": Style(
        "snowy", vtype="snow", wood="spruce", post="stripped_spruce_log", beam="spruce_log",
        plinth=Palette({W + "blue_slate_bricks": 3, W + "polished_blue_slate": 1, "stone_bricks": 1}, seed=14),
        floor="spruce_planks", wall=Palette({"spruce_planks": 1}),
        upper=Palette({"spruce_planks": 3, "stripped_spruce_wood[axis=y]": 1}, seed=6),
        roof=(W + "slate_roof_tiles", W + "slate_roof_tile_stairs", W + "slate_roof_tile_slab"), flat=False,
        pane="glass_pane", metal=(IRON, W + "dark_iron_plating_stairs", W + "dark_iron_plating_slab"),
        pave=Palette({W + "blue_slate_bricks": 3, W + "polished_blue_slate": 2, "stone_bricks": 1}, seed=8),
        accent_pave=W + "polished_blue_slate", path=Palette({"dirt_path": 3, "gravel": 2}, seed=11),
        ground="grass_block[snowy=false]", planter="podzol", lamp_base=W + "polished_blue_slate",
        flowers=["fern", "lily_of_the_valley", "cornflower", "azure_bluet", "fern"],
        tree="spruce", tree_log="spruce_log", tree_leaves="spruce_leaves", fruit="spruce_leaves",
        awnings=["light_blue", "white", "blue", "cyan"], banner="light_blue", bed="light_blue",
        crops=["carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]", "wheat[age=7]"],
        sign="spruce", residents=["fisherman", "shepherd", "librarian", "armorer", "butcher"]),
    "taiga": Style(
        "taiga", vtype="taiga", wood="spruce", post="spruce_log", beam="stripped_spruce_log",
        plinth=Palette({"cobblestone": 3, "mossy_cobblestone": 2, "stone": 1}, seed=15),
        floor="spruce_planks", wall=Palette({"spruce_planks": 1}),
        upper=Palette({"stripped_spruce_wood[axis=y]": 2, "spruce_planks": 1}, seed=9),
        roof=("spruce_planks", "spruce_stairs", "spruce_slab"), flat=False,
        pane="glass_pane", metal=(W + "verdigris_plating", W + "verdigris_plating_stairs", W + "verdigris_plating_slab"),
        pave=Palette({"cobblestone": 3, "mossy_cobblestone": 2, "stone_bricks": 2, "mossy_stone_bricks": 1}, seed=9),
        accent_pave="mossy_stone_bricks", path=Palette({"dirt_path": 3, "coarse_dirt": 2, "podzol": 1}, seed=12),
        ground="grass_block[snowy=false]", planter="podzol", lamp_base="mossy_cobblestone",
        flowers=["fern", "lily_of_the_valley", "poppy", "cornflower", "sweet_berry_bush[age=3]"],
        tree="spruce", tree_log="spruce_log", tree_leaves="spruce_leaves", fruit="spruce_leaves",
        awnings=["green", "brown", "white", "orange"], banner="green", bed="green",
        crops=["pumpkin_stem[age=7]", "potatoes[age=7]", "carrots[age=7]", "wheat[age=7]"],
        sign="spruce", residents=["farmer", "fletcher", "leatherworker", "butcher", "shepherd"]),
}

# ====================================================================== sign texts (translated in-game)
SIGNS = {
    "inn": ("The Wayfarer's Rest", "Le Repos du Voyageur"),
    "inn2": ("Beds - Hot meals", "Lits - Repas chauds"),
    "notice": ("NOTICE BOARD", "AVIS ET ANNONCES"),
    "wanted": ("WANTED: gears", "ON CHERCHE : rouages"),
    "reward": ("Reward: emeralds", "Récompense : émeraudes"),
    "guild": ("Wayfarers' Guild", "Guilde des Voyageurs"),
    "waystone": ("Waystone ->", "Pierre de voyage ->"),
    "market": ("Market <-", "<- Marché"),
    "tinker": ("Tinkerer", "Bricoleur"),
    "tinker2": ("Repairs - Gadgets", "Réparations - Gadgets"),
    "lost": ("Lost: a brass cat", "Perdu : un chat en laiton"),
    "bell": ("Ring for the council", "Sonnez pour le conseil"),
    "post": ("Guild Post", "Relais de la Guilde"),
    "post2": ("Contracts - Bounties", "Contrats - Primes"),
}


def sign_key(k):
    return f"sign.wayfarers.village.{k}"


def lang():
    en, fr = {}, {}
    for k, (e, f) in SIGNS.items():
        en[sign_key(k)], fr[sign_key(k)] = e, f
    return en, fr


def sign_data(lines):
    """Block-entity NBT of a sign showing the SIGNS keys ``lines`` (centred lines, up to 4)."""
    lines = list(lines)
    pad = (4 - len(lines)) // 2
    front = [None] * pad + lines
    msgs = []
    for k in front + [None] * (4 - len(front)):
        msgs.append(nbt.Compound({"text": nbt.String("")}) if k is None else
                    nbt.Compound({"translate": nbt.String(sign_key(k)), "fallback": nbt.String(SIGNS[k][0])}))
    text = {"messages": nbt.List(msgs, nbt.Compound), "color": nbt.String("black"),
            "has_glowing_text": nbt.Byte(0)}
    blank = {"messages": nbt.List([nbt.Compound({"text": nbt.String("")})] * 4, nbt.Compound),
             "color": nbt.String("black"), "has_glowing_text": nbt.Byte(0)}
    return {"front_text": text, "back_text": blank, "is_waxed": nbt.Byte(1)}


def wall_sign(bp, st, x, y, z, facing, lines):
    bp.set(x, y, z, f"{st.sign}_wall_sign[facing={facing},waterlogged=false]", sign_data(lines))


def hanging_sign(bp, st, x, y, z, facing, lines):
    """A hanging sign under a beam; ``facing`` is the side its front text faces (rotation of the board)."""
    rot = {"south": 0, "west": 4, "north": 8, "east": 12}[facing]
    bp.set(x, y, z, f"{st.sign}_hanging_sign[attached=false,rotation={rot},waterlogged=false]", sign_data(lines))


# ====================================================================== jigsaws
def entrance(bp, st, x, z=0, y=1, path=True):
    """The street connector: north-facing building entrance at walking level, path under it."""
    bp.jigsaw(x, y, z, "north_up", ENTRANCE, ENTRANCE, EMPTY, final_state="minecraft:air", joint="aligned")
    if path:
        bp.set(x, y - 1, z, st.path.pick(x, y - 1, z))


def street_exit(bp, st, x, y, z, facing, pool):
    bp.jigsaw(x, y, z, f"{facing}_up", STREET, STREET, pool, final_state="minecraft:air", joint="aligned")


def spawn_point(bp, x, y, z, pool):
    """Upward jigsaw a vanilla pool hangs a mob template on (golem, cat, villager), like the vanilla meeting points."""
    bp.jigsaw(x, y, z, "up_north", BOTTOM, BOTTOM, pool, final_state="minecraft:air", joint="rollable")


def decor_base(bp, final_state):
    bp.jigsaw(0, 0, 0, "down_south", BOTTOM, EMPTY, EMPTY, final_state=final_state, joint="rollable")


# ====================================================================== small kit
def pos(face, line, u, out):
    return A._pos(face, line, u, out)


def walls(bp, st, x0, z0, x1, z1, y0, y1, infill, posts=True, post_every=4, beam=True):
    """Hollow storey: walls x0..x1 / z0..z1 from y0 to y1, inside cleared, log posts and a beam course on top."""
    bp.clear(x0 + 1, y0, z0 + 1, x1 - 1, y1, z1 - 1)
    A.wall_pal(bp, x0, y0, z0, x1, y1, z1, infill)
    if posts:
        xs = sorted(set([x0, x1] + list(range(x0, x1 + 1, post_every))))
        zs = sorted(set([z0, z1] + list(range(z0, z1 + 1, post_every))))
        for x in xs:
            for z in (z0, z1):
                bp.fill(x, y0, z, x, y1, z, col(st.post))
        for z in zs:
            for x in (x0, x1):
                bp.fill(x, y0, z, x, y1, z, col(st.post))
    if beam:
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                bp.set(x, y1, z, axis_of(st.beam, "x"))
        for z in range(z0 + 1, z1):
            for x in (x0, x1):
                bp.set(x, y1, z, axis_of(st.beam, "z"))


def floor(bp, x0, z0, x1, z1, y, spec):
    pal = A.as_pal(spec)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, pal.pick(x, y, z))


def window(bp, st, face, line, u, y, h=2, w=1, shutters=True, box=True, glass=None):
    """Window of ``w`` x ``h`` panes in the wall plane ``line`` facing ``face`` (u = left column), with open
    shutters and a planter under it."""
    for k in range(w):
        for dy in range(h):
            x, z = pos(face, line, u + k, 0)
            bp.set(x, y + dy, z, glass or st.pane)
    if shutters:
        for uu in (u - 1, u + w):
            x, z = pos(face, line, uu, 1)
            for dy in range(h):
                bp.set(x, y + dy, z, st.trapdoor(face, "bottom", True))
    if box:
        rng = random.Random(f"{bp.name}:{face}:{line}:{u}:{y}")
        for k in range(w):
            x, z = pos(face, line, u + k, 1)
            bp.set(x, y - 1, z, st.planter)
            bp.set(x, y, z, rng.choice(st.flowers))


def door(bp, st, face, line, u, y, double=False):
    """Door (or double door) in the wall plane, opening onto ``face``."""
    for k in range(2 if double else 1):
        x, z = pos(face, line, u + k, 0)
        bp.set(x, y, z, "air")
        bp.set(x, y + 1, z, "air")
        hinge = "left" if k == 0 else "right"
        bp.door(x, y, z, face, st.wood, hinge=hinge)


def chimney(bp, x, z, y0, y1, body, cap=None, smoke=True):
    """A solid chimney column with a smoking top (campfire on a hay bale inside the stack)."""
    for y in range(y0, y1 + 1):
        bp.set(x, y, z, A.as_pal(body).pick(x, y, z))
    if smoke:
        bp.set(x, y1 + 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    elif cap:
        bp.set(x, y1 + 1, z, cap)


def brass_lamp(bp, st, x, y, z, h=3, base=True):
    """Brass street lamp: stone foot, dark iron post, Edison lamp under a brass cap."""
    if base:
        bp.set(x, y, z, st.lamp_base)
        y += 1
    for yy in range(y, y + h - 1):
        bp.set(x, yy, z, IRON_WALL)
    bp.set(x, y + h - 1, z, EDISON)
    bp.set(x, y + h, z, slab(BRASS_SLAB))


def lamp_bracket(bp, face, line, u, y):
    """A hanging Edison lamp on a short iron arm out of a wall."""
    x, z = pos(face, line, u, 1)
    bp.set(x, y + 1, z, IRON_WALL)
    bp.set(x, y, z, HANG_EDISON)


def planter(bp, st, x, y, z, rng):
    bp.set(x, y, z, st.planter)
    bp.set(x, y + 1, z, rng.choice(st.flowers))


def flower_bed(bp, st, x0, z0, x1, z1, y, rng, edge=True):
    """Raised bed: planter soil one block up, flowers on it, a stair/slab kerb in the plinth stone."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            border = x in (x0, x1) or z in (z0, z1)
            if edge and border:
                bp.set(x, y, z, A.as_pal(st.plinth).pick(x, y, z))
                if rng.random() < 0.5:
                    bp.set(x, y + 1, z, rng.choice(st.flowers))
                    bp.set(x, y, z, st.planter)
            else:
                bp.set(x, y, z, st.planter)
                bp.set(x, y + 1, z, rng.choice(st.flowers))
    _fix_tall(bp)


def _fix_tall(bp):
    for p, (name, props, data) in list(bp.blocks.items()):
        if props.get("half") == "lower" and name.split(":")[1] in ("rose_bush", "peony", "lilac", "tall_grass",
                                                                    "large_fern", "sunflower"):
            bp.set(p[0], p[1] + 1, p[2], (name, dict(props, half="upper")))


def bench(bp, st, x, y, z, facing, length=2):
    """Stair seats facing ``facing`` with trapdoor arm rests (along the axis across ``facing``)."""
    I.y_bench(bp, x, y, z, None, facing, wood=st.wood)


def tree(bp, st, x, y, z, seed=0, h=None, lean=None):
    rng = random.Random(seed)
    if st.tree == "oak":
        A.oak(bp, x, y, z, h=h or rng.randint(4, 5), seed=seed, log=st.tree_log, leaves=st.tree_leaves)
        for _ in range(4):
            dx, dy, dz = rng.randint(-2, 2), rng.randint(3, 5), rng.randint(-2, 2)
            p = (x + dx, y + dy, z + dz)
            if bp.get(*p) == "minecraft:" + st.tree_leaves:
                bp.set(*p, leaves(st.fruit))
    elif st.tree == "spruce":
        A.spruce(bp, x, y, z, h=h or rng.randint(6, 7), seed=seed, log=st.tree_log, leaves=st.tree_leaves)
    elif st.tree == "acacia":
        acacia(bp, x, y, z, rng, h or rng.randint(4, 5), lean)
    else:
        palm(bp, x, y, z, rng, h or rng.randint(5, 6))


def acacia(bp, x, y, z, rng, h, lean=None):
    lv = leaves("acacia_leaves")
    for i in range(h - 2):
        bp.set(x, y + i, z, col("acacia_log"))
    dx, dz = lean or rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    tx, tz = x, z
    for i in range(h - 2, h):
        tx, tz = tx + dx, tz + dz
        bp.set(tx, y + i, tz, col("acacia_log"))
    top = y + h
    for ddx in range(-3, 4):
        for ddz in range(-3, 4):
            if abs(ddx) + abs(ddz) <= 4:
                bp.set(tx + ddx, top, tz + ddz, lv, keep=True)
            if abs(ddx) + abs(ddz) <= 2:
                bp.set(tx + ddx, top + 1, tz + ddz, lv, keep=True)


def palm(bp, x, y, z, rng, h):
    lv = leaves("jungle_leaves")
    for i in range(h):
        bp.set(x, y + i, z, col("jungle_log"))
    top = y + h
    bp.set(x, top, z, lv)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in (1, 2):
            bp.set(x + dx * k, top, z + dz * k, lv)
        bp.set(x + dx * 3, top - 1, z + dz * 3, lv)
    for dx, dz in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        bp.set(x + dx, top, z + dz, lv)
        bp.set(x + dx * 2, top - 1, z + dz * 2, lv)
    if rng.random() < 0.7:
        bp.set(x + 1, top - 1, z, "cocoa[age=2,facing=west]")


def roof(bp, st, x0, z0, x1, z1, y, axis="x", overhang=1, gable=None, steep=1.0):
    from .structures.overworld_a import roof as gable_roof
    return gable_roof(bp, x0, z0, x1, z1, y, st.R, axis=axis, overhang=overhang, steep=steep,
                      gable=gable or st.upper, under=st.stairs(), hollow=True)


def flat_roof(bp, st, x0, z0, x1, z1, y, parapet=True):
    """Desert roof: a slab deck over beams, a crenellated parapet, a spout on each side."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, y, z, A.as_pal(st.plinth).pick(x, y, z) if edge else "smooth_sandstone")
    if parapet:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    if (x + z) % 2 == 0 or (x in (x0, x1) and z in (z0, z1)):
                        bp.set(x, y + 1, z, "cut_sandstone")
                    else:
                        bp.set(x, y + 1, z, slab("smooth_sandstone_slab"))
    return y + 1


def dome(bp, st, cx, cz, y, r):
    """Small copper onion dome (desert) with a brass finial."""
    full, sts, sl = st.dome
    for dy in range(r + 1):
        rr = r * math.cos(math.asin(min(1.0, dy / (r + 0.5))))
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= rr + 0.3:
                    bp.set(x, y + dy, z, full if d > rr - 1.2 else "air", keep=d <= rr - 1.2)
    top = y + r + 1
    bp.set(cx, top, cz, BRASS)
    bp.set(cx, top + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return top


def awning(bp, st, x0, x1, z, y, depth=2, facing="north"):
    """Striped wool awning over a door or a stall, ``depth`` rows out from ``z`` towards ``facing``."""
    a, b = st.awnings[0], st.awnings[1]
    for x in range(x0, x1 + 1):
        colour = a if (x - x0) % 2 == 0 else b
        for k in range(depth):
            bp.set(x, y, z - k if facing == "north" else z + k, f"{colour}_wool")


def notice_board(bp, st, x, y, z, facing, lines=(("notice",), ("wanted", "reward"), ("lost",))):
    """Notice board of three signs on a plank board between two posts, with a little roof. ``(x, z)`` is the
    left post (seen from the front), the board runs three blocks to its right; ``facing`` = reading side."""
    along = {"south": (1, 0), "north": (-1, 0), "east": (0, -1), "west": (0, 1)}[facing]
    back = {"south": (0, -1), "north": (0, 1), "east": (-1, 0), "west": (1, 0)}[facing]
    cells = [(x + along[0] * k, z + along[1] * k) for k in range(5)]
    for k, (cx, cz) in enumerate(cells):
        if k in (0, 4):
            bp.fill(cx, y, cz, cx, y + 2, cz, col(st.post))
        else:
            bp.set(cx, y, cz, "air")
            bp.fill(cx, y + 1, cz, cx, y + 2, cz, st.planks())
        bp.set(cx, y + 3, cz, slab(st.slab(), "bottom") if k in (0, 4) else st.planks())
        bx, bz = cx + back[0], cz + back[1]
        bp.set(bx, y + 3, bz, stair(st.stairs(), facing))
        fx, fz = cx - back[0], cz - back[1]
        bp.set(fx, y + 3, fz, stair(st.stairs(), OPPOSITE[facing]))
    for k, ls in zip((1, 2, 3), lines):
        cx, cz = cells[k]
        fx, fz = cx - back[0], cz - back[1]
        wall_sign(bp, st, fx, y + 2 - (1 if k == 2 else 0), fz, facing, ls)
    # a lantern on the board's side
    return cells


def villager_at(bp, st, x, y, z, prof, job=None, job_pos=None, level=2, facing=None):
    if job and job_pos:
        bp.set(*job_pos, job)
    I.villager(bp, x, y, z, prof, st.vtype, level, facing=facing)


def foundation(bp, depth=5):
    from .foundation import add_foundations
    add_foundations(bp, 0, depth=depth, soil_depth=2)


# ====================================================================== shared house parts
def ground(bp, st, x0, z0, x1, z1, keep=True):
    """Ground layer (y = 0) under a yard: the style's soil."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, 0, z, st.ground, keep=keep)


def path(bp, st, x, z0, z1, width=1):
    for z in range(z0, z1 + 1):
        for dx in range(width):
            bp.set(x + dx, 0, z, st.path.pick(x + dx, 0, z))


def base(bp, st, x0, z0, x1, z1):
    """Ground floor slab: plinth stone under the walls, the floor inside."""
    floor(bp, x0, z0, x1, z1, 0, st.plinth)
    floor(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 0, st.floor)


def plinth_course(bp, st, x0, z0, x1, z1, y0, y1):
    """Stone lower course of the walls."""
    pal = A.as_pal(st.plinth)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                bp.set(x, y, z, pal.pick(x, y, z))
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                bp.set(x, y, z, pal.pick(x, y, z))


def front_garden(bp, st, x0, x1, z0, z1, door_x, rng, width=1, lamps=True, fence=True):
    """The strip between the street and the facade: soil, a path to the door, flowers, a picket fence and
    brass lamps by the gate."""
    ground(bp, st, x0, z0, x1, z1)
    path(bp, st, door_x, z0, z1, width)
    for x in range(x0, x1 + 1):
        if door_x <= x < door_x + width:
            continue
        for z in range(z0 + 1, z1 + 1):
            if rng.random() < 0.55 and bp.get(x, 1, z) is None:
                if not st.ground.startswith("grass_block"):
                    bp.set(x, 0, z, st.planter)
                bp.set(x, 1, z, rng.choice(st.flowers))
        if fence:
            bp.set(x, 1, z0, st.fence())
    if lamps:
        for x in (door_x - 1, door_x + width):
            if x0 <= x <= x1:
                bp.remove(x, 1, z0)
                brass_lamp(bp, st, x, 1, z0, h=3, base=False)
    _fix_tall(bp)


def porch_deck(bp, st, x0, x1, z0, z1, y, posts):
    """Porch roof as a balcony: plank deck on posts, brass railing along the open sides."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, slab(st.slab(), "top"))
    for x in posts:
        bp.fill(x, 1, z0, x, y - 1, z0, col(st.post))
        bp.set(x, y, z0, st.planks())
    for x in range(x0, x1 + 1):
        bp.set(x, y + 1, z0, W + "brass_railing[facing=north]")
    for z in range(z0 + 1, z1 + 1):
        bp.set(x0, y + 1, z, W + "brass_railing[facing=west]")
        bp.set(x1, y + 1, z, W + "brass_railing[facing=east]")


def stairs_up(bp, st, x0, z, y0, n, facing="east"):
    """A straight flight of ``n`` stairs climbing towards ``facing`` from (x0, y0, z), planks under it."""
    dx = 1 if facing == "east" else -1
    for i in range(n):
        x = x0 + dx * i
        bp.set(x, y0 + i, z, stair(st.stairs(), facing))
        for yy in range(y0, y0 + i):
            bp.set(x, yy, z, st.planks())


def residents(bp, st, n, seed, region=None, beds=True, extra=()):
    rng = random.Random(f"{bp.name}:who:{seed}")
    who = list(extra) + [rng.choice(st.residents) for _ in range(n)]
    return I.populate(bp, who, region=region, vtype=st.vtype, seed=seed, beds=beds, bed_colour=st.bed)


# ====================================================================== houses
def cottage(bp, st):
    """Cottage: one tall room under a street-facing gable, shuttered windows with flower boxes, a smoking
    chimney and a fenced front garden."""
    rng = random.Random(bp.name)
    x0, z0, x1, z1 = 1, 3, 9, 10
    base(bp, st, x0, z0, x1, z1)
    walls(bp, st, x0, z0, x1, z1, 1, 4, st.wall)
    plinth_course(bp, st, x0, z0, x1, z1, 1, 1)
    if st.flat:
        ridge = flat_roof(bp, st, x0, z0, x1, z1, 5)
        awning(bp, st, x0 + 2, x1 - 2, z0 - 1, 4, depth=1)
    else:
        ridge = roof(bp, st, x0, z0, x1, z1, 5, axis="z")
        window(bp, st, "north", z0, 5, 6, h=2, box=False, shutters=False)
        window(bp, st, "south", z1, 5, 6, h=2, box=False, shutters=False)
    door(bp, st, "north", z0, 5, 1)
    for u in (3, 7):
        window(bp, st, "north", z0, u, 2)
        window(bp, st, "south", z1, u, 2)
    for u in (5, 8):
        window(bp, st, "west", x0, u, 2)
        window(bp, st, "east", x1, u, 2)
    chimney(bp, 7, z1, 1, ridge + 1, st.plinth)
    lamp_bracket(bp, "north", z0, 4, 3)
    front_garden(bp, st, x0, x1, 0, 2, 5, rng)
    entrance(bp, st, 5)
    residents(bp, st, 1, 1)
    I.decorate(bp, "home", seed=2)


def manor(bp, st):
    """Two-storey manor: stone ground floor, a balcony porch with a brass railing, a staircase, two bedrooms
    upstairs, a gable roof with a chimney (a flat roof and a copper dome in the desert)."""
    rng = random.Random(bp.name)
    x0, z0, x1, z1 = 1, 4, 13, 12
    base(bp, st, x0, z0, x1, z1)
    walls(bp, st, x0, z0, x1, z1, 1, 5, st.wall)
    plinth_course(bp, st, x0, z0, x1, z1, 1, 2)
    floor(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 5, st.planks())
    walls(bp, st, x0, z0, x1, z1, 6, 9, st.upper)
    # ground floor: hall | kitchen, staircase along the back wall
    bp.fill(8, 1, z0 + 1, 8, 4, z1 - 1, st.planks())
    door(bp, st, "east", 8, 7, 1)
    stairs_up(bp, st, 2, z1 - 1, 1, 5, "east")
    for x in (4, 5):
        bp.set(x, 5, z1 - 1, "air")
    # upstairs: two bedrooms
    bp.fill(8, 6, z0 + 1, 8, 8, z1 - 1, st.planks())
    door(bp, st, "east", 8, 9, 6)
    # porch with a balcony
    floor(bp, 4, 2, 10, 3, 0, st.plinth)
    porch_deck(bp, st, 4, 10, 2, 3, 5, posts=(4, 10))
    door(bp, st, "north", z0, 7, 1)
    door(bp, st, "north", z0, 7, 6)
    bp.set(7, 4, 3, HANG_EDISON)
    if st.flat:
        ridge = flat_roof(bp, st, x0, z0, x1, z1, 10)
        dome(bp, st, 10, 8, 11, 2)
    else:
        ridge = roof(bp, st, x0, z0, x1, z1, 10, axis="x")
        window(bp, st, "west", x0, 8, 11, h=2, box=False, shutters=False)
        window(bp, st, "east", x1, 8, 11, h=2, box=False, shutters=False)
    for u in (3, 11):
        window(bp, st, "north", z0, u, 2)
        window(bp, st, "north", z0, u, 7)
        window(bp, st, "south", z1, u, 7)
    window(bp, st, "south", z1, 10, 2)
    for u in (6, 10):
        window(bp, st, "west", x0, u, 2)
        window(bp, st, "east", x1, u, 2)
        window(bp, st, "west", x0, u, 7, box=False)
        window(bp, st, "east", x1, u, 7, box=False)
    chimney(bp, x1, 8, 1, ridge + 1, st.plinth)
    for x in range(x0, x1 + 1):
        if bp.get(x, 5, z0) and bp.get(x, 5, z0).endswith(("_log", "smooth_sandstone")):
            bp.set(x, 5, z0, st.metal[0])
    front_garden(bp, st, x0, x1, 0, 1, 7, rng)
    entrance(bp, st, 7)
    residents(bp, st, 2, 1)
    I.decorate(bp, "home", seed=2)


def inn(bp, st):
    """The Wayfarers' Inn, a guild hall: tavern with a bar, a hearth, tables and brass chandeliers on the ground
    floor, a landing and three bedrooms upstairs, a balcony porch with the hanging signs, banners and lamps."""
    rng = random.Random(bp.name)
    x0, z0, x1, z1 = 1, 4, 16, 14
    base(bp, st, x0, z0, x1, z1)
    walls(bp, st, x0, z0, x1, z1, 1, 5, st.wall)
    plinth_course(bp, st, x0, z0, x1, z1, 1, 2)
    floor(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 5, st.planks())
    walls(bp, st, x0, z0, x1, z1, 6, 9, st.upper)
    for x in range(x0, x1 + 1):
        bp.set(x, 5, z0, st.metal[0])
    # --- tavern
    door(bp, st, "north", z0, 8, 1, double=True)
    stairs_up(bp, st, 2, z0 + 1, 1, 5, "east")
    for x in (4, 5):
        bp.set(x, 5, z0 + 1, "air")
    # bar counter (mahogany) with the innkeeper behind it
    for x in range(12, 16):
        bp.set(x, 1, 10, MAHOGANY)
        bp.set(x, 2, 10, rng.choice(["air", "air", "candle[candles=2,lit=true,waterlogged=false]",
                                     "potted_red_tulip"]))
    for x in range(12, 16):
        if x != 14:
            bp.barrel(x, 1, 13, "up")
        bp.set(x, 3, 13, W + "wall_shelf[facing=north]")
    bp.set(14, 1, 13, "smoker[facing=north,lit=true]")
    I.villager(bp, 13, 1, 12, "butcher", st.vtype, 3, facing="north")
    # hearth on the west wall, the chimney goes up through the gable
    for z in (8, 10):
        bp.fill(2, 1, z, 2, 2, z, SMOKE)
    bp.set(2, 1, 9, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
    bp.set(2, 2, 9, "air")
    for z in (8, 9, 10):
        bp.set(2, 3, z, SMOKE)
    bp.set(2, 4, 9, SMOKE)
    # tables with chairs, chandeliers
    for tx, tz in ((6, 8), (6, 12), (10, 7)):
        bp.set(tx, 1, tz, W + "mahogany_table")
        bp.set(tx, 2, tz, "candle[candles=3,lit=true,waterlogged=false]")
        for dx, dz, f in ((-1, 0, "east"), (1, 0, "west"), (0, -1, "south"), (0, 1, "north")):
            if bp.get(tx + dx, 1, tz + dz) in (None, "minecraft:air"):
                bp.set(tx + dx, 1, tz + dz, W + f"mahogany_chair[facing={f}]")
    for cx, cz in ((6, 10), (11, 7)):
        bp.set(cx, 4, cz, W + "brass_chandelier")
    bp.set(9, 3, z1, GEAR)
    wall_sign(bp, st, 9, 2, z1 - 1, "north", ("guild",))
    I.wandering_trader(bp, 9, 1, 9, facing="south")
    # --- upstairs: landing to the north, three bedrooms to the south
    bp.fill(x0 + 1, 6, 9, x1 - 1, 8, 9, st.planks())
    for x in (7, 11):
        bp.fill(x, 6, 10, x, 8, z1 - 1, st.planks())
    for x in (4, 9, 13):
        door(bp, st, "north", 9, x, 6)
    # --- porch, signs and banners
    floor(bp, 2, 2, 15, 3, 0, st.plinth)
    porch_deck(bp, st, 2, 15, 2, 3, 5, posts=(2, 6, 11, 15))
    for x in (2, 15):
        bp.set(x, 3, 1, f"{st.banner}_wall_banner[facing=north]")
    hanging_sign(bp, st, 8, 4, 2, "north", ("inn", "inn2"))
    hanging_sign(bp, st, 9, 4, 2, "north", ("guild",))
    bp.set(4, 4, 3, HANG_EDISON)
    bp.set(13, 4, 3, HANG_EDISON)
    for x in (8, 9):
        bp.set(x, 4, z0, GEAR)
    bp.set(7, 3, z0, GAUGE)
    bp.set(10, 3, z0, GAUGE)
    # windows
    for u in (12, 14):
        window(bp, st, "north", z0, u, 2)
    for u in (3, 5, 12, 14):
        window(bp, st, "north", z0, u, 7)
    for u in (3, 5, 9, 13, 15):
        window(bp, st, "south", z1, u, 7)
    for u in (6, 12):
        window(bp, st, "east", x1, u, 2)
        window(bp, st, "east", x1, u, 7)
        window(bp, st, "west", x0, u, 7)
    window(bp, st, "west", x0, 12, 2)
    if st.flat:
        ridge = flat_roof(bp, st, x0, z0, x1, z1, 10)
        dome(bp, st, 9, 9, 11, 3)
    else:
        ridge = roof(bp, st, x0, z0, x1, z1, 10, axis="x")
        window(bp, st, "west", x0, 8, 11, h=2, w=2, box=False, shutters=False)
        window(bp, st, "east", x1, 8, 11, h=2, w=2, box=False, shutters=False)
    chimney(bp, x0, 9, 1, ridge + 1, SMOKE)
    for y in range(1, ridge - 2):
        if bp.get(0, y, 11) is None:
            bp.set(0, y, 11, W + "copper_pipe[axis=y]")
    bp.set(0, 3, 10, W + "valve_wheel[facing=west]")
    front_garden(bp, st, x0, x1, 0, 1, 8, rng, width=2)
    entrance(bp, st, 8)
    residents(bp, st, 0, 1, region=((x0, 6, z0), (x1, 9, z1)), extra=[("cartographer", 3), ("librarian", 2)])
    # a Scholar of the guild, travelling from inn to inn, hands out contracts in the tavern (wf/npcs.py)
    I.quest_npc_in(bp, "scholar", region=((x0, 1, z0), (x1, 1, z1)), seed=1)
    I.decorate(bp, dict(I.THEMES["hall"], floor={"barrel": 3, "crates": 1, "plant": 2, "pot": 1}), seed=3,
               region=((x0, 1, z0), (x1, 1, z1)), centre=False, lights=False)
    I.decorate(bp, "home", seed=4, region=((x0, 6, z0), (x1, 6, z1)))


def guild_post(bp, st):
    """The Guild Post: a small office of the Wayfarers' Guild where a Guild Agent hands out contracts across a
    counter, between a map table and a lectern of ledgers, under the guild's banners; couriers sleep upstairs."""
    rng = random.Random(bp.name)
    x0, z0, x1, z1 = 1, 3, 10, 10
    base(bp, st, x0, z0, x1, z1)
    walls(bp, st, x0, z0, x1, z1, 1, 4, st.wall)
    plinth_course(bp, st, x0, z0, x1, z1, 1, 1)
    floor(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 5, st.planks())
    walls(bp, st, x0, z0, x1, z1, 5, 7, st.upper, post_every=3)
    for x in range(x0, x1 + 1):
        bp.set(x, 4, z0, st.metal[0])
    door(bp, st, "north", z0, 5, 1, double=True)
    for u in (3, 8):
        window(bp, st, "north", z0, u, 2)
        window(bp, st, "north", z0, u, 6, box=False)
        window(bp, st, "south", z1, u, 6, box=False)
    window(bp, st, "west", x0, 5, 2)
    window(bp, st, "west", x0, 8, 2)
    window(bp, st, "east", x1, 8, 2)
    window(bp, st, "south", z1, 4, 2)
    if st.flat:
        ridge = flat_roof(bp, st, x0, z0, x1, z1, 8)
    else:
        ridge = roof(bp, st, x0, z0, x1, z1, 8, axis="x")
    chimney(bp, x1, 9, 1, ridge + 1, st.plinth)
    # the counter across the hall, the agent behind it, the guild's maps and ledgers around
    for x in range(2, 10):
        if x not in (5, 6):
            bp.set(x, 1, 7, MAHOGANY)
    bp.set(3, 2, 7, "candle[candles=2,lit=true,waterlogged=false]")
    bp.set(8, 2, 7, "potted_fern")
    bp.set(2, 1, 9, "cartography_table")
    bp.set(9, 1, 9, "lectern[facing=north,has_book=false,powered=false]")
    bp.set(2, 1, 4, "barrel[facing=up,open=false]")
    bp.set(2, 2, 4, "potted_" + rng.choice(["red_tulip", "cornflower", "fern"]))
    I.quest_npc(bp, 4, 1, 8, "guild_agent", facing="north")
    for x in (3, 8):
        bp.set(x, 3, z1 - 1, f"{st.banner}_wall_banner[facing=north]")
    wall_sign(bp, st, 6, 3, z1 - 1, "north", ("post", "post2"))
    bp.set(5, 4, 5, HANG_EDISON)
    # a ladder up to the couriers' bunk room
    bp.ladder(9, 1, 5, 5, "west")
    # outside: a path, flowers and brass lamps, the sign over the door
    front_garden(bp, st, x0, x1, 0, 2, 5, rng, width=2, fence=False)
    wall_sign(bp, st, 4, 3, z0 - 1, "north", ("post", "post2"))
    entrance(bp, st, 5)
    residents(bp, st, 0, 1, region=((x0, 5, z0), (x1, 7, z1)), extra=[("cartographer", 2)])
    I.decorate(bp, "home", seed=3, region=((x0, 6, z0), (x1, 6, z1)))


def workshop(bp, st):
    """Tinkerer's workshop: tall hall with big windows and a double door, gears and gauges on the facade, a
    copper boiler and a banded smokestack outside; workbenches, machines and two craftsmen inside."""
    rng = random.Random(bp.name)
    x0, z0, x1, z1 = 1, 3, 10, 12
    base(bp, st, x0, z0, x1, z1)
    walls(bp, st, x0, z0, x1, z1, 1, 6, st.wall)
    plinth_course(bp, st, x0, z0, x1, z1, 1, 2)
    door(bp, st, "north", z0, 5, 1, double=True)
    for u in (2, 8):
        window(bp, st, "north", z0, u, 2, h=3, w=1, shutters=False, box=False)
    for u in (5, 9):
        window(bp, st, "west", x0, u, 2, h=3, w=2, shutters=False, box=False)
        window(bp, st, "east", x1, u, 2, h=3, w=2, shutters=False, box=False)
    window(bp, st, "south", z1, 4, 2, h=3, w=3, shutters=False, box=False)
    for x in range(x0, x1 + 1):
        bp.set(x, 6, z0, st.metal[0])
    for x in (5, 6):
        bp.set(x, 4, z0, GEAR)
    for x in (4, 7):
        bp.set(x, 4, z0, GAUGE)
    wall_sign(bp, st, 5, 3, z0 - 1, "north", ("tinker", "tinker2"))
    if st.flat:
        flat_roof(bp, st, x0, z0, x1, z1, 7)
        ridge = dome(bp, st, 5, 8, 8, 2)
    else:
        ridge = roof(bp, st, x0, z0, x1, z1, 7, axis="z")
        for x in (5, 6):
            bp.set(x, 9, z0, GEAR)
            bp.set(x, 9, z1, st.pane)
    # smokestack (2 x 2) with brass bands
    top = ridge + 3
    for y in range(0, top + 1):
        for x in (11, 12):
            for z in (9, 10):
                bp.set(x, y, z, st.metal[0] if y in (5, top - 2) else SMOKE)
    bp.set(11, top, 9, "hay_block[axis=y]")
    bp.set(11, top + 1, 9, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x, z in ((12, 9), (11, 10), (12, 10)):
        bp.set(x, top + 1, z, SMOKE_WALL)
    # copper boiler with a gauge and a valve, piped into the wall
    floor(bp, 11, 3, 12, 11, 0, st.plinth)
    for y in range(1, 4):
        for x in (11, 12):
            for z in (4, 5, 6):
                bp.set(x, y, z, W + "copper_plating")
    for x in (11, 12):
        for z in (4, 5, 6):
            bp.set(x, 4, z, slab(W + "copper_plating_slab"))
    bp.set(12, 2, 4, GAUGE)
    bp.set(11, 2, 3, W + "valve_wheel[facing=north]")
    bp.set(10, 3, 5, PIPES)
    for z in (7, 8):
        bp.set(11, 1, z, W + "copper_pipe[axis=z]")
    # inside: craftsmen, then the steampunk furnishing
    I.populate(bp, [("toolsmith", 3), ("armorer", 2)], vtype=st.vtype, seed=1, beds=False)
    I.quest_npc_in(bp, "tinkerer", seed=1)
    I.decorate(bp, "steampunk", seed=2)
    ground(bp, st, x0, 0, x1, 2)
    path(bp, st, 5, 0, 2, 2)
    I.y_crates(bp, 1, 1, 1, rng, "north")
    I.y_cart(bp, 9, 1, 1, rng, "east", wood=st.wood)
    entrance(bp, st, 5)


def watchtower(bp, st):
    """Watchtower: stone base, timber lookout storey, an overhanging platform with a brass telescope and the
    alarm bell under a pyramid roof, a ladder all the way up, a fletcher on guard at the foot."""
    x0, z0, x1, z1 = 2, 3, 6, 7
    base(bp, st, x0, z0, x1, z1)
    walls(bp, st, x0, z0, x1, z1, 1, 5, st.plinth, posts=False, beam=False)
    walls(bp, st, x0, z0, x1, z1, 6, 10, st.upper)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                bp.set(x, 5, z, st.metal[0])
    door(bp, st, "north", z0, 4, 1)
    # floors with a ladder hole, the platform
    for y in (5, 10):
        floor(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, y, st.planks())
    floor(bp, x0 - 1, z0 - 1, x1 + 1, z1 + 1, 11, st.planks())
    bp.ladder(4, 1, z1 - 1, 11, "north")
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
                bp.set(x, 12, z, st.fence())
    for x, z in ((x0 - 1, z0 - 1), (x1 + 1, z0 - 1), (x0 - 1, z1 + 1), (x1 + 1, z1 + 1)):
        bp.fill(x, 12, z, x, 14, z, IRON_WALL)
    # pyramid roof over a beam that carries the bell
    for x in range(x0 - 1, x1 + 2):
        bp.set(x, 15, 5, axis_of(st.beam, "x"))
    bp.pyramid_roof(x0 - 1, z0 - 1, x1 + 1, z1 + 1, 15, st.R[1], overhang=1, cap=st.R[0])
    peak = 15
    while bp.get(4, peak, 5) is not None and peak < 30:
        peak += 1
    bp.set(4, peak, 5, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(4, 14, 5, "bell[attachment=ceiling,facing=north,powered=false]")
    # brass telescope on a post at the front
    bp.set(4, 12, z0 - 1, IRON_WALL)
    bp.set(4, 13, z0 - 1, W + "copper_pipe[axis=z]")
    # lamps on the base, slits and windows
    lamp_bracket(bp, "north", z0, 2, 3)
    lamp_bracket(bp, "north", z0, 6, 3)
    for face, line in (("west", x0), ("east", x1)):
        u = 5
        window(bp, st, face, line, u, 3, h=1, shutters=False, box=False)
        window(bp, st, face, line, u, 7, h=2, box=False)
    window(bp, st, "north", z0, 4, 7, h=2, box=False)
    # the guard at the foot
    bp.set(3, 1, z1 - 1, "fletching_table")
    I.villager(bp, 5, 1, 5, "fletcher", st.vtype, 2, facing="north")
    ground(bp, st, 0, 0, 8, 9)
    path(bp, st, 4, 0, 2)
    bp.set(1, 1, 1, "hay_block[axis=y]")
    bp.set(1, 2, 1, "target[power=0]")
    bp.barrel(7, 1, 1, "up")
    entrance(bp, st, 4)


TRADES = {
    "farmer": ("composter[level=5]", ["pumpkin", "melon", "hay_block[axis=y]", "carved_pumpkin[facing=north]"]),
    "fisherman": ("barrel[facing=up,open=false]", ["barrel[facing=up,open=false]", "dried_kelp_block",
                                                   "water_cauldron[level=3]"]),
    "shepherd": ("loom[facing=north]", ["white_wool", "light_gray_wool", "brown_wool"]),
    "butcher": ("smoker[facing=north,lit=false]", ["hay_block[axis=y]", "barrel[facing=up,open=false]"]),
    "leatherworker": ("water_cauldron[level=3]", ["barrel[facing=up,open=false]", "brown_wool"]),
    "mason": ("stonecutter[facing=north]", ["chiseled_stone_bricks", "polished_andesite", "bricks"]),
}
MARKET = {"plains": ["farmer", "shepherd", "butcher"], "desert": ["farmer", "leatherworker", "mason"],
          "savanna": ["farmer", "butcher", "shepherd"], "snowy": ["fisherman", "farmer", "shepherd"],
          "taiga": ["farmer", "fisherman", "leatherworker"]}


def market(bp, st):
    """Market: three striped stalls with their traders and goods around a paved square, a cart, crates,
    brass lamps and a bench."""
    rng = random.Random(bp.name)
    floor(bp, 0, 0, 14, 10, 0, st.pave)
    for i, ((a, b), prof) in enumerate(zip([(1, 4), (5, 9), (10, 13)], MARKET[st.key])):
        job, goods = TRADES[prof]
        for x in (a, b):
            for z in (6, 9):
                bp.fill(x, 1, z, x, 3, z, st.fence())
        c1, c2 = st.awnings[(2 * i) % 4], st.awnings[(2 * i + 1) % 4]
        for x in range(a, b + 1):
            for z in range(5, 10):
                bp.set(x, 4, z, f"{c1 if (x - a) % 2 == 0 else c2}_wool")
        for x in range(a + 1, b):
            if (x - a) % 2:
                bp.set(x, 1, 6, slab(st.slab(), "top"))
                bp.set(x, 2, 6, rng.choice(["potted_red_tulip", "potted_cornflower", "potted_fern",
                                            "candle[candles=2,lit=true,waterlogged=false]"]))
            else:
                bp.set(x, 1, 6, rng.choice(goods))
            bp.set(x, 1, 9, rng.choice(goods))
        bp.set(a + 1, 1, 9, job)
        I.villager(bp, a + 2 if b - a > 3 else a + 1, 1, 8 if b - a > 3 else 7, prof, st.vtype, 2, facing="north")
    for x in (1, 13):
        brass_lamp(bp, st, x, 1, 2, h=3)
    I.y_cart(bp, 3, 1, 3, rng, "east", wood=st.wood)
    I.y_crates(bp, 11, 1, 2, rng, "north")
    I.y_bench(bp, 7, 1, 3, rng, "south", wood=st.wood)
    entrance(bp, st, 7, path=False)


def orchard(bp, st):
    """Fenced orchard and kitchen garden: fruit trees, a crop patch with its water channel and a scarecrow
    (a greenhouse in the snow), flower beds with a beehive (a cactus bed in the desert), a farmer at the
    composter, a brass lamp."""
    rng = random.Random(bp.name)
    ground(bp, st, 0, 1, 12, 12, keep=False)
    for x in range(0, 13):
        for z in range(1, 13):
            if x in (0, 12) or z in (1, 12):
                bp.set(x, 1, z, st.fence())
    bp.set(6, 1, 1, st.gate("north"))
    path(bp, st, 6, 0, 11)
    for x in range(1, 12):
        bp.set(x, 0, 7, st.path.pick(x, 0, 7))
    for x in range(7, 12):
        for z in range(2, 7):
            if x == 9:
                bp.set(x, 0, z, "water[level=0]")
                continue
            bp.set(x, 0, z, "farmland[moisture=7]")
            bp.set(x, 1, z, st.crops[(x + z) % len(st.crops)])
    if st.key == "snowy":
        for x in range(7, 12):
            for z in range(2, 7):
                if x in (7, 11) or z in (2, 6):
                    bp.fill(x, 1, z, x, 3, z, "glass")
                bp.set(x, 4, z, "glass")
        for x, z in ((7, 2), (11, 2), (7, 6), (11, 6)):
            bp.fill(x, 1, z, x, 4, z, col(st.post))
        bp.set(7, 0, 4, st.planks())
        bp.set(8, 0, 4, st.planks())
        bp.set(8, 1, 4, "air")
        bp.door(7, 1, 4, "west", st.wood)
        bp.set(9, 4, 4, IRON)
        bp.set(9, 3, 4, "lantern[hanging=true,waterlogged=false]")
    else:
        bp.set(11, 0, 2, st.ground)
        bp.set(11, 1, 2, st.fence())
        bp.set(11, 2, 2, "hay_block[axis=y]")
        bp.set(11, 3, 2, "carved_pumpkin[facing=north]")
    for x in range(1, 6):
        for z in (2, 3, 5, 6):
            if st.key == "desert":
                bp.set(x, 0, z, "sand")
                if (x + z) % 2 == 0:
                    bp.fill(x, 1, z, x, 2, z, "cactus[age=0]")
                elif rng.random() < 0.5:
                    bp.set(x, 1, z, "dead_bush")
                continue
            bp.set(x, 0, z, st.planter)
            bp.set(x, 1, z, rng.choice(st.flowers))
    bp.set(3, 1, 4, st.fence())
    bp.set(3, 2, 4, "beehive[facing=south,honey_level=3]")
    tree(bp, st, 3, 1, 10, seed=len(st.key) * 7)
    tree(bp, st, 10, 1, 10, seed=len(st.key) * 7 + 3)
    bp.set(8, 1, 11, "composter[level=6]")
    I.villager(bp, 8, 1, 9, "farmer", st.vtype, 2, facing="south")
    bp.set(11, 1, 8, "hay_block[axis=y]")
    bp.barrel(1, 1, 8, "up")
    brass_lamp(bp, st, 5, 1, 8, h=3, base=True)
    _fix_tall(bp)
    entrance(bp, st, 6)


def well_corner(bp, st):
    """Well corner (street furniture): a roofed well, two benches facing it, brass lamps, planters and a
    signpost to the waystone."""
    rng = random.Random(bp.name)
    floor(bp, 0, 0, 8, 7, 0, st.pave)
    stone = {"plains": "cobblestone", "desert": "cut_sandstone", "savanna": "terracotta",
             "snowy": W + "blue_slate_bricks", "taiga": "mossy_cobblestone"}[st.key]
    I.y_well(bp, 3, 1, 3, rng, "north", stone=stone, roof=st.wood)
    bp.set(4, 4, 4, st.metal[0])
    for x, f in ((1, "east"), (7, "west")):
        I.y_bench(bp, x, 1, 3, rng, f, wood=st.wood)
    for x in (1, 7):
        brass_lamp(bp, st, x, 1, 7, h=3)
    for x in (0, 8):
        for z in (5, 6, 7):
            planter(bp, st, x, 1, z, rng)
    bp.set(2, 1, 1, st.fence())
    bp.set(2, 2, 1, f"{st.sign}_sign[rotation=8,waterlogged=false]", sign_data(("waystone", "market")))
    entrance(bp, st, 4, path=False)


# ====================================================================== town centre
def plaza(bp, st):
    """Town centre: a paved square around a Waystone on a metal dais, a notice board with the meeting bell,
    four brass lamps, flower beds with trees and benches; four streets leave from the middle of its sides."""
    rng = random.Random(bp.name)
    n, c = 19, 9
    for x in range(n):
        for z in range(n):
            d = math.hypot(x - c, z - c)
            bp.set(x, 0, z, st.accent_pave if 4.4 < d < 5.4 else st.pave.pick(x, 0, z))
    for x in range(c - 1, c + 2):
        for z in range(c - 1, c + 2):
            if (x, z) == (c, c):
                bp.set(x, 1, z, st.metal[0])
            else:
                f = "south" if z < c else "north" if z > c else "east" if x < c else "west"
                bp.set(x, 1, z, stair(st.metal[1], f))
    bp.set(c, 2, c, W + "waystone")
    for x, z in ((c - 3, c - 3), (c + 3, c - 3), (c - 3, c + 3), (c + 3, c + 3)):
        brass_lamp(bp, st, x, 1, z, h=4)
    notice_board(bp, st, 2, 1, 6, "east")
    I.quest_npc(bp, 4, 1, 5, "guild_agent", facing="west")   # reads the board out to passers-by
    bp.set(4, 1, 2, st.metal[0])
    bp.set(4, 2, 2, "bell[attachment=floor,facing=east,powered=false]")
    wall_sign(bp, st, 5, 1, 2, "east", ("bell",))
    flower_bed(bp, st, 12, 2, 16, 6, 0, rng)
    tree(bp, st, 14, 1, 4, seed=3, lean=(-1, 0))
    flower_bed(bp, st, 2, 12, 6, 16, 0, rng)
    tree(bp, st, 4, 1, 14, seed=4, lean=(0, -1))
    for x, z, f in ((12, 13, "west"), (14, 12, "north")):
        I.y_bench(bp, x, 1, z, rng, f, wood=st.wood)
    for x, z in ((16, 16), (15, 16), (16, 15)):
        bp.barrel(x, 1, z, "up")
    bp.set(16, 2, 16, "potted_" + rng.choice(["red_tulip", "cornflower", "fern", "dandelion"]))
    pool = f"minecraft:village/{st.key}/streets"
    street_exit(bp, st, c, 1, 0, "north", pool)
    street_exit(bp, st, c, 1, n - 1, "south", pool)
    street_exit(bp, st, 0, 1, c, "west", pool)
    street_exit(bp, st, n - 1, 1, c, "east", pool)
    spawn_point(bp, 14, 1, 9, "minecraft:village/common/iron_golem")
    spawn_point(bp, 11, 1, 15, "minecraft:village/common/cats")
    spawn_point(bp, 7, 1, 11, f"minecraft:village/{st.key}/villagers")
    spawn_point(bp, 12, 1, 7, f"minecraft:village/{st.key}/villagers")
    _fix_tall(bp)


# ====================================================================== streets and decor
def avenue(bp, st):
    """A straight street lined with brass lamps and planters, two house plots on each side."""
    rng = random.Random(bp.name)
    L = 12
    for x in range(L):
        for z in (2, 3, 4):
            bp.set(x, 0, z, st.path.pick(x, 0, z))
        for z in (1, 5):
            bp.set(x, 0, z, st.ground)
    pool = f"minecraft:village/{st.key}/houses"
    for x in (3, 8):
        for z in (1, 5):
            bp.set(x, 0, z, st.path.pick(x, 0, z))
        bp.jigsaw(x, 1, 0, "north_up", ENTRANCE, ENTRANCE, pool, final_state="minecraft:air", joint="aligned")
        bp.jigsaw(x, 1, 6, "south_up", ENTRANCE, ENTRANCE, pool, final_state="minecraft:air", joint="aligned")
    for x, z in ((1, 1), (10, 5)):
        brass_lamp(bp, st, x, 1, z, h=3)
    hedge = leaves(st.fruit if st.key == "plains" else st.tree_leaves)
    for x in range(L):
        for z in (1, 5):
            if bp.get(x, 1, z) is not None or x in (3, 8):
                continue
            if x in (5, 6) or (z == 1 and x == 11) or (z == 5 and x == 0):
                bp.set(x, 0, z, st.planter)
                bp.set(x, 1, z, hedge)
            elif rng.random() < 0.6:
                planter(bp, st, x, 0, z, rng)
    streets = f"minecraft:village/{st.key}/streets"
    street_exit(bp, st, 0, 1, 3, "west", streets)
    street_exit(bp, st, L - 1, 1, 3, "east", streets)
    _fix_tall(bp)


def _state(spec):
    return spec if ":" in spec.split("[")[0] else "minecraft:" + spec


def lamp_decor(bp, st):
    """Brass street lamp for the decor pool (1 x 1, stands on the street side)."""
    decor_base(bp, _state(st.lamp_base))
    for y in (1, 2):
        bp.set(0, y, 0, IRON_WALL)
    bp.set(0, 3, 0, EDISON)
    bp.set(0, 4, 0, slab(BRASS_SLAB))


def signpost_decor(bp, st):
    """Signpost pointing to the waystone and the market (decor pool, 1 x 1)."""
    post = _state(st.post)
    decor_base(bp, post + "[axis=y]" if post.endswith("_log") else post)
    bp.set(0, 1, 0, st.fence())
    bp.set(0, 2, 0, st.fence())
    bp.set(0, 3, 0, f"{st.sign}_sign[rotation=0,waterlogged=false]", sign_data(("waystone", "market")))


# ====================================================================== pillager outposts
OUTPOST_GROUND = Palette({"coarse_dirt": 3, "gravel": 1, "dirt": 2}, seed=21)


def feature_base(bp, x, z):
    """Outpost features hang on the feature plate's upward jigsaw: a downward ``minecraft:feature`` jigsaw at
    walking level, ground layer under it."""
    bp.jigsaw(x, 1, z, "down_south", FEATURE, EMPTY, EMPTY, final_state="minecraft:air", joint="rollable")


def siege_engine(bp):
    """Steam siege ballista: a dark iron deck on cog wheels, a copper boiler with a smoking stack, the bow and
    its bolt, a loot barrel and the raiders' banner."""
    floor(bp, 0, 0, 6, 8, 0, OUTPOST_GROUND)
    for z in (2, 6):
        for x in range(1, 6):
            bp.set(x, 1, z, axis_of("dark_oak_log", "x"))
        bp.set(0, 1, z, W + "wall_cog[facing=west]")
        bp.set(6, 1, z, W + "wall_cog[facing=east]")
    for x in range(1, 6):
        for z in range(1, 8):
            edge = x in (1, 5) or z in (1, 7)
            bp.set(x, 2, z, IRON if edge else "dark_oak_planks")
    # boiler and stack
    for x in (2, 3, 4):
        for z in (5, 6):
            for y in (3, 4):
                bp.set(x, y, z, W + "copper_plating")
            bp.set(x, 5, z, slab(W + "copper_plating_slab"))
    bp.set(3, 4, 5, GAUGE)
    bp.set(3, 5, 6, SMOKE)
    bp.set(3, 6, 6, SMOKE)
    bp.set(3, 7, 6, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # ballista: stock, bow arms, bolt, crank
    for z in range(1, 5):
        bp.set(3, 3, z, axis_of("dark_oak_log", "z"))
    for x in (1, 2, 4, 5):
        bp.set(x, 3, 1, "dark_oak_fence")
    bp.set(1, 3, 2, "iron_chain[axis=z,waterlogged=false]")
    bp.set(5, 3, 2, "iron_chain[axis=z,waterlogged=false]")
    bp.set(3, 3, 0, "end_rod[facing=north]")
    bp.set(2, 3, 4, W + "valve_wheel[facing=west]")
    bp.set(4, 3, 4, W + "valve_wheel[facing=east]")
    # loot and banner
    bp.barrel(5, 3, 7, "up", loot="minecraft:chests/pillager_outpost")
    bp.fill(6, 1, 8, 6, 2, 8, "dark_oak_fence")
    bp.set(6, 3, 8, "gray_banner[rotation=8]")
    feature_base(bp, 3, 4)


def barricade(bp):
    """Raiders' barricade: dark oak posts crowned with copper spikes, fence panels and riveted iron plates,
    braces behind, a target and hay for the archers."""
    floor(bp, 0, 0, 8, 3, 0, OUTPOST_GROUND)
    for x in range(0, 9):
        if x % 2 == 0:
            bp.fill(x, 1, 1, x, 2, 1, col("dark_oak_log"))
            bp.set(x, 3, 1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        else:
            bp.fill(x, 1, 1, x, 2, 1, IRON if x in (3, 5) else "dark_oak_fence")
    for x in (0, 4, 8):
        bp.set(x, 1, 2, stair("dark_oak_stairs", "north"))
    for x in (1, 7):
        bp.set(x, 1, 0, "dark_oak_fence")
    bp.set(2, 1, 3, "target[power=0]")
    bp.set(6, 1, 3, "hay_block[axis=y]")
    feature_base(bp, 4, 3)


# ====================================================================== registry and pools
# (name, builder, pool, weight, kind); weight None = scaled on the vanilla pool (see weights())
PIECES = [
    ("plaza", plaza, "town_centers", None, "start"),
    ("inn", inn, "houses", 5, "house"),
    ("guild_post", guild_post, "houses", 6, "house"),
    ("workshop", workshop, "houses", 4, "house"),
    ("watchtower", watchtower, "houses", 3, "house"),
    ("market", market, "houses", 4, "house"),
    ("orchard", orchard, "houses", 4, "house"),
    ("cottage", cottage, "houses", 5, "house"),
    ("manor", manor, "houses", 3, "house"),
    ("well_corner", well_corner, "houses", 3, "house"),
    ("avenue", avenue, "streets", 3, "street"),
    ("brass_lamp", lamp_decor, "decor", None, "decor"),
    ("signpost", signpost_decor, "decor", None, "decor"),
]
OUTPOST = [("siege_engine", siege_engine, 2), ("barricade", barricade, 2)]
FOUNDATION_DEPTH = 5
PROCESSORS = W + "village"


def template_id(vtype, name):
    return f"{W}village/{vtype}/{name}"


def build_all():
    """Yield (template id, blueprint, kind) for every piece of every village type, then the outpost pieces."""
    for vt in TYPES:
        st = STYLES[vt]
        for name, builder, pool, weight, kind in PIECES:
            bp = Blueprint(f"village/{vt}/{name}")
            builder(bp, st)
            if kind in ("house", "start"):
                foundation(bp, FOUNDATION_DEPTH + (1 if kind == "start" else 0))
            yield template_id(vt, name), bp, kind
    for name, builder, weight in OUTPOST:
        bp = Blueprint(f"pillager_outpost/{name}")
        builder(bp)
        foundation(bp, 3)
        yield f"{W}pillager_outpost/{name}", bp, "feature"


def check(bp, kind):
    """Jigsaw sanity of a piece (problems as strings): houses have one entrance at walking level on their north
    edge with nothing further north, the plaza and the avenue leave through their box edges, decorations hang on
    one downward ``minecraft:bottom`` jigsaw, outpost features on one downward ``minecraft:feature`` jigsaw."""
    out = []
    (x0, y0, z0), (x1, y1, z1) = bp.bounds()
    jig = [(p, b[1]["orientation"], b[2]) for p, b in bp.blocks.items() if b[0] == "minecraft:jigsaw"]

    def val(d, k):
        return getattr(d[k], "value", d[k])

    ent = [(p, o) for p, o, d in jig if val(d, "name") == ENTRANCE and val(d, "pool") == EMPTY]
    exits = [(p, o) for p, o, d in jig if val(d, "name") == STREET]
    downs = [(p, o) for p, o, d in jig if o.startswith("down_")]
    if kind == "house":
        if len(ent) != 1:
            out.append(f"{len(ent)} building entrances (want 1)")
        for (x, y, z), o in ent:
            if o != "north_up" or y != 1 or z != z0:
                out.append(f"entrance at {(x, y, z)} {o}: must face north on the north edge (z = {z0}) at y = 1")
            if (x, 0, z) not in bp.blocks:
                out.append(f"nothing under the entrance at {(x, 0, z)}")
    if kind in ("start", "street"):
        want = 4 if kind == "start" else 2
        if len(exits) != want:
            out.append(f"{len(exits)} street exits (want {want})")
        edge = {"north": lambda p: p[2] == z0, "south": lambda p: p[2] == z1, "west": lambda p: p[0] == x0,
                "east": lambda p: p[0] == x1}
        for p, o in exits:
            if not edge[o.split("_")[0]](p):
                out.append(f"street exit {p} {o} is not on its edge of the box")
    if kind in ("decor", "feature"):
        if len(downs) != 1:
            out.append(f"{len(downs)} downward jigsaws (want 1)")
        if kind == "decor" and (x0, z0) != (x1, z1):
            out.append("decoration wider than 1 x 1 (it has to fit beside the street)")
    return out


def _total(pool):
    return sum(e["weight"] for e in pool["elements"]
               if "/zombie/" not in e["element"].get("location", ""))


def weights(vanilla, vt, pool, name, weight):
    if weight is not None:
        return weight
    total = _total(vanilla[f"minecraft:village/{vt}/{pool}"])
    if pool == "town_centers":
        return max(1, round(total / 3))       # about one village in four starts on our plaza
    if name == "brass_lamp":
        return max(2, round(total * 0.3))
    return max(1, round(total * 0.1))


def element(vanilla, vt, name, kind, grounds):
    tid = template_id(vt, name)
    if kind == "start":
        return {"element_type": GROUNDED, "location": tid, "processors": PROCESSORS, "projection": "rigid",
                "ground_level_delta": grounds[tid]}
    if kind == "street":
        street = vanilla[f"minecraft:village/{vt}/streets"]["elements"][0]["element"]
        return {"element_type": "minecraft:single_pool_element", "location": tid,
                "processors": copy.deepcopy(street["processors"]), "projection": "terrain_matching"}
    return {"element_type": "minecraft:single_pool_element", "location": tid,
            "processors": PROCESSORS if kind == "house" else W + "none", "projection": "rigid"}


def pools(grounds):
    """{pool id: pool JSON} for every vanilla pool we extend: the vanilla elements untouched, ours appended.
    ``grounds``: template id -> ground_level_delta of the start pieces."""
    from . import vanilla_pools
    vanilla = vanilla_pools.load()
    out = {}
    for vt in TYPES:
        for name, builder, pool, weight, kind in PIECES:
            pid = f"minecraft:village/{vt}/{pool}"
            data = out.setdefault(pid, copy.deepcopy(vanilla[pid]))
            data["elements"].append({"weight": weights(vanilla, vt, pool, name, weight),
                                     "element": element(vanilla, vt, name, kind, grounds)})
    pid = "minecraft:pillager_outpost/features"
    data = out.setdefault(pid, copy.deepcopy(vanilla[pid]))
    for name, builder, weight in OUTPOST:
        data["elements"].append({"weight": weight, "element": {
            "element_type": "minecraft:single_pool_element", "location": f"{W}pillager_outpost/{name}",
            "processors": W + "none", "projection": "rigid"}})
    return out
