"""Furniture and steampunk fittings with real 3D shapes. One table drives the block models (cuboid elements),
blockstates, collision shapes (Java), textures, recipes, loot, tags and translations.

Boxes are (x0, y0, z0, x1, y1, z1, texture) in pixels, drawn for a block facing north. Mounts:
  none   - no rotation (chandeliers, lamps, tables)
  player - front turned towards the player (chairs)
  away   - turned the way the player looks (railings: the rail sits on the far edge)
  wall   - stuck to the clicked wall, which is behind it at z = 16 (shelves, cogs, valves)
  axis   - a pillar along x, y or z like a log (pipes)
"""
from . import texgen_steam as S

TEXTURES = {
    "f_mahogany": lambda: S.plain_wood(S.MAHOGANY, seed=70),
    "f_brass": lambda: S.smooth_metal(S.BRASS, seed=71),
    "f_copper": lambda: S.smooth_metal(S.COPPER, seed=72),
    "f_iron": lambda: S.smooth_metal(S.DARK_IRON, seed=73),
    "f_bulb": lambda: S.glow_bulb(S.AMBER, (255, 250, 220), seed=74),
    "f_chain": lambda: S.chain(S.DARK_IRON),
    "f_wax": lambda: S.wax(S.CREAM, seed=75),
    "f_leather": lambda: S.tufted_leather(S.LEATHER, S.BRASS, seed=76),
    "f_red": lambda: S.smooth_metal((150, 36, 30), seed=77),
}


def _legs(h, inset=1, size=2, tex="f_mahogany"):
    a, b = inset, 16 - inset - size
    return [(x, 0, z, x + size, h, z + size, tex) for x in (a, b) for z in (a, b)]


FURNITURE = {
    "mahogany_table": dict(
        en="Mahogany Table", fr="Table en acajou", mount="none", sound="WOOD", color="COLOR_BROWN", tool="axe",
        boxes=[(0, 13, 0, 16, 16, 16, "f_mahogany"), (1, 12, 1, 15, 13, 15, "f_brass")] + _legs(12),
        recipe=(["SSS", "P P"], {"S": "wayfarers:mahogany_panelling_slab", "P": "stick"}, 1)),
    "mahogany_chair": dict(
        en="Mahogany Chair", fr="Chaise en acajou", mount="player", sound="WOOD", color="COLOR_BROWN", tool="axe",
        boxes=[(2, 7, 2, 14, 9, 14, "f_mahogany"), (3, 9, 3, 13, 10, 13, "f_leather"),
               (2, 9, 12, 14, 22, 14, "f_mahogany"), (3, 12, 11, 13, 20, 12, "f_leather"),
               (2, 22, 12, 14, 23, 14, "f_brass")] + _legs(7, inset=2),
        shape=[(2, 0, 2, 14, 10, 14), (2, 10, 12, 14, 23, 14)],
        recipe=(["P  ", "PLP", "S S"], {"P": "wayfarers:mahogany_panelling", "L": "leather", "S": "stick"}, 2)),
    "wall_shelf": dict(
        en="Wall Shelf", fr="Étagère murale", mount="wall", sound="WOOD", color="COLOR_BROWN", tool="axe",
        boxes=[(0, 7, 8, 16, 9, 16, "f_mahogany"), (1, 3, 14, 3, 7, 16, "f_brass"), (13, 3, 14, 15, 7, 16, "f_brass"),
               (1, 5, 12, 3, 7, 14, "f_brass"), (13, 5, 12, 15, 7, 14, "f_brass")],
        shape=[(0, 3, 8, 16, 9, 16)],
        recipe=(["SSS", "N N"], {"S": "wayfarers:mahogany_panelling_slab", "N": "wayfarers:brass_nugget"}, 2)),
    "brass_chandelier": dict(
        en="Brass Chandelier", fr="Lustre en laiton", mount="none", sound="METAL", color="GOLD", light=15,
        boxes=[(7, 9, 7, 9, 16, 9, "f_chain"), (6, 8, 6, 10, 10, 10, "f_brass"),
               (2, 6, 2, 14, 7, 3, "f_brass"), (2, 6, 13, 14, 7, 14, "f_brass"),
               (2, 6, 3, 3, 7, 13, "f_brass"), (13, 6, 3, 14, 7, 13, "f_brass"),
               (3, 7, 7.5, 13, 8, 8.5, "f_brass"), (7.5, 7, 3, 8.5, 8, 13, "f_brass")]
              + [(x, 7, z, x + 2, 11, z + 2, "f_wax") for x, z in ((2, 7), (12, 7), (7, 2), (7, 12))]
              + [(x + 0.5, 11, z + 0.5, x + 1.5, 12, z + 1.5, "f_bulb") for x, z in ((2, 7), (12, 7), (7, 2), (7, 12))],
        shape=[(2, 6, 2, 14, 16, 14)],
        recipe=([" C ", "NTN", " N "], {"C": "wayfarers:brass_nugget", "N": "wayfarers:brass_ingot", "T": "candle"}, 1)),
    "hanging_edison_lamp": dict(
        en="Hanging Edison Lamp", fr="Lampe Edison suspendue", mount="none", sound="GLASS", color="COLOR_ORANGE", light=15,
        boxes=[(7.5, 9, 7.5, 8.5, 16, 8.5, "f_iron"), (6, 8, 6, 10, 9, 10, "f_brass"), (6.5, 3, 6.5, 9.5, 8, 9.5, "f_bulb"),
               (7, 2, 7, 9, 3, 9, "f_bulb")],
        shape=[(6, 2, 6, 10, 16, 10)],
        recipe=(["N", "L"], {"N": "iron_nugget", "L": "wayfarers:edison_lamp"}, 2)),
    "copper_pipe": dict(
        en="Copper Pipe", fr="Tuyau en cuivre", mount="axis", sound="COPPER", color="COLOR_ORANGE",
        boxes=[(5, 0, 5, 11, 16, 11, "f_copper"), (4, 0, 4, 12, 2, 12, "f_brass"), (4, 14, 4, 12, 16, 12, "f_brass")],
        shape=[(4, 0, 4, 12, 16, 12)],
        # a row, not a column: three copper ingots in a column are the vanilla lightning rod
        recipe=(["CCC"], {"C": "copper_ingot"}, 6)),
    "brass_railing": dict(
        en="Brass Railing", fr="Garde-corps en laiton", mount="away", sound="METAL", color="GOLD",
        boxes=[(0, 14, 0, 16, 16, 2, "f_brass"), (0, 6, 0.5, 16, 7, 1.5, "f_iron")]
              + [(x, 0, 0.5, x + 1, 14, 1.5, "f_iron") for x in (1, 5, 10, 14)],
        shape=[(0, 0, 0, 16, 16, 2)],
        recipe=(["BBB", "N N"], {"B": "wayfarers:brass_ingot", "N": "iron_nugget"}, 6)),
    "wall_cog": dict(
        en="Wall Cog", fr="Engrenage mural", mount="wall", sound="METAL", color="GOLD",
        boxes=[(2, 2, 15, 14, 14, 16, "f_brass"), (6, 0, 15, 10, 16, 16, "f_brass"), (0, 6, 15, 16, 10, 16, "f_brass"),
               (3, 3, 14.5, 13, 13, 15, "f_copper"), (6, 6, 13.5, 10, 10, 14.5, "f_iron")],
        shape=[(0, 0, 13, 16, 16, 16)],
        # a Brass Gear framed by nuggets (an ingot there would be the Brass Gear's own recipe)
        recipe=([" N ", "NGN", " N "], {"N": "wayfarers:brass_nugget", "G": "wayfarers:brass_gear"}, 2)),
    "valve_wheel": dict(
        en="Steam Valve", fr="Vanne à vapeur", mount="wall", sound="METAL", color="COLOR_RED",
        boxes=[(3, 3, 13, 13, 4, 14, "f_red"), (3, 12, 13, 13, 13, 14, "f_red"), (3, 4, 13, 4, 12, 14, "f_red"),
               (12, 4, 13, 13, 12, 14, "f_red"), (7.5, 4, 13, 8.5, 12, 14, "f_iron"), (4, 7.5, 13, 12, 8.5, 14, "f_iron"),
               (7, 7, 13, 9, 9, 16, "f_brass"), (5, 5, 15, 11, 11, 16, "f_copper")],
        shape=[(3, 3, 13, 13, 13, 16)],
        recipe=(["R", "C"], {"R": "red_dye", "C": "wayfarers:copper_pipe"}, 1)),
}


def textures():
    return {f"block/{name}": fn() for name, fn in TEXTURES.items()}


def _shape(f):
    return f.get("shape") or [b[:6] for b in f["boxes"]]


def model(fid):
    f = FURNITURE[fid]
    used = sorted({b[6] for b in f["boxes"]})
    elements = []
    for x0, y0, z0, x1, y1, z1, tex in f["boxes"]:
        elements.append({"from": [x0, y0, z0], "to": [x1, y1, z1],
                         "faces": {face: {"texture": f"#{tex}"} for face in ("north", "south", "east", "west", "up", "down")}})
    return {"parent": "minecraft:block/block", "render_type": "minecraft:cutout", "ambientocclusion": False,
            "textures": {"particle": f"wayfarers:block/{used[0]}", **{t: f"wayfarers:block/{t}" for t in used}},
            "elements": elements}


def blockstate(fid):
    m = f"wayfarers:block/{fid}"
    mount = FURNITURE[fid]["mount"]
    if mount == "none":
        return {"variants": {"": {"model": m}}}
    if mount == "axis":
        return {"variants": {"axis=y": {"model": m}, "axis=z": {"model": m, "x": 90},
                             "axis=x": {"model": m, "x": 90, "y": 90}}}
    rot = {"north": 0, "east": 90, "south": 180, "west": 270}
    return {"variants": {f"facing={d}": {"model": m, **({"y": r} if r else {})} for d, r in rot.items()}}


def lang():
    en, fr = {}, {}
    for fid, f in FURNITURE.items():
        en[f"block.wayfarers.{fid}"], fr[f"block.wayfarers.{fid}"] = f["en"], f["fr"]
    return en, fr


def _num(v):
    return f"{float(v)}"


def java():
    L = [
        "package com.wayfarers.generated;",
        "",
        "import com.wayfarers.block.FurnitureBlock;",
        "import com.wayfarers.item.TooltipBlockItem;",
        "import com.wayfarers.registry.ModBlocks;",
        "import com.wayfarers.registry.ModItems;",
        "import net.minecraft.world.item.Item;",
        "import net.minecraft.world.level.block.Block;",
        "import net.minecraft.world.level.block.SoundType;",
        "import net.minecraft.world.level.block.state.BlockBehaviour;",
        "import net.minecraft.world.level.material.MapColor;",
        "import net.minecraftforge.registries.RegistryObject;",
        "",
        "/** GENERATED by tools/gen_java.py from tools/wf/furniture.py — do not edit by hand. */",
        "public final class GeneratedFurniture {",
    ]
    for fid, f in FURNITURE.items():
        boxes = ", ".join("{" + ", ".join(_num(v) for v in b) + "}" for b in _shape(f))
        L.append(f'    public static final RegistryObject<Block> {fid.upper()} = furniture("{fid}", FurnitureBlock.Mount.'
                 f'{f["mount"].upper()}, MapColor.{f["color"]}, SoundType.{f["sound"]}, {f.get("light", 0)},')
        L.append(f"            new double[][] {{{boxes}}});")
    L += [
        "",
        "    private GeneratedFurniture() {}",
        "",
        "    /** Forces class initialisation so every block/item is queued on the deferred registers. */",
        "    public static void init() {}",
        "",
        "    private static RegistryObject<Block> furniture(String name, FurnitureBlock.Mount mount, MapColor color, SoundType sound,",
        "                                                   int light, double[][] boxes) {",
        "        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name, () -> FurnitureBlock.create(BlockBehaviour.Properties.of()",
        "                .mapColor(color).sound(sound).strength(1.5F, 3.0F).noOcclusion().lightLevel(s -> light)",
        "                .setId(ModBlocks.BLOCKS.key(name)), mount, boxes));",
        "        ModItems.ALL.add(ModItems.ITEMS.register(name, () -> new TooltipBlockItem(block.get(),",
        "                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix())));",
        "        return block;",
        "    }",
        "}",
        "",
    ]
    return "\n".join(L)
