"""World blocks: the two woods of the world overhaul (Glowwood, Rustwood).

One table drives the Java registration (GeneratedWorldBlocks.java), textures, models, blockstates, recipes, loot,
tags and translations, like metals.py. The three new stones (marble, rust rock, blue slate) are plain building
blocks and live in decor.py (stairs, slabs and walls come with it); their surface rules and veins are in
biomes.py / worldfeatures.py.

Woods use vanilla's oak BlockSetType / WoodType (sounds, door rules), so no custom set has to be registered; no signs
or boats. Trees: data/wayfarers/worldgen/configured_feature/<wood>_tree.json (always loaded, the saplings grow
them); the overhaul's placed features plant them in the biomes.
"""
from . import texgen_world as W

NS = "wayfarers"

# palette keys: bark (log side), bark_dark, bark_light, wood (stripped/planks), wood_dark, wood_light, ring (log end),
# leaf, leaf_light, leaf_dark, speck (glow specks or None)
WOODS = {
    "glowwood": dict(
        en="Glowwood", fr="bois-lueur",
        bark=(196, 202, 196), bark_dark=(120, 132, 134), bark_light=(226, 232, 226), lichen=((112, 214, 200), 5),
        wood=(178, 206, 200), wood_dark=(120, 156, 156), wood_light=(212, 234, 226), ring=(150, 186, 182),
        leaf=(66, 166, 146), leaf_light=(124, 214, 188), leaf_dark=(30, 98, 96), speck=((186, 255, 226), 4),
        leaf_light_level=6, particle=0xFF5FD8C8,
        color_bark="TERRACOTTA_WHITE", color_wood="COLOR_LIGHT_GRAY", color_leaves="COLOR_CYAN",
        door_window=(150, 236, 220), door_bands=None,
        tree=dict(trunk="fancy", height=(8, 6, 0)),
        sapling_recipe=["minecraft:oak_sapling", "minecraft:glow_berries", "minecraft:glowstone_dust"],
    ),
    "rustwood": dict(
        en="Rustwood", fr="bois rouillé",
        bark=(92, 50, 40), bark_dark=(52, 28, 24), bark_light=(128, 72, 52), lichen=((176, 92, 46), 7),
        wood=(160, 82, 54), wood_dark=(104, 50, 34), wood_light=(194, 112, 74), ring=(132, 64, 42),
        leaf=(196, 104, 44), leaf_light=(236, 156, 72), leaf_dark=(128, 60, 30), speck=None,
        leaf_light_level=0, particle=0xFFC8682C,
        color_bark="TERRACOTTA_BROWN", color_wood="TERRACOTTA_RED", color_leaves="COLOR_ORANGE",
        door_window=None, door_bands=(86, 84, 88),
        tree=dict(trunk="forking", height=(5, 2, 2)),
        sapling_recipe=["minecraft:acacia_sapling", "minecraft:raw_iron"],
    ),
}

# block id suffix order (creative tab order)
KINDS = ["log", "wood", "stripped_log", "stripped_wood", "planks", "stairs", "slab", "fence", "fence_gate", "door",
         "trapdoor", "button", "pressure_plate", "leaves", "sapling"]


def block_id(w, kind):
    if kind.startswith("stripped_"):
        return f"stripped_{w}_{kind[9:]}"
    return f"{w}_{kind}"


def ids(w):
    return {block_id(w, k): k for k in KINDS}


def all_block_ids():
    return [b for w in WOODS for b in ids(w)]


def names(w, kind):
    d = WOODS[w]
    en, fr = d["en"], d["fr"]
    Fr = fr[0].upper() + fr[1:]
    return {
        "log": (f"{en} Log", f"Bûche de {fr}"),
        "wood": (f"{en} Bark", f"Écorce de {fr}"),
        "stripped_log": (f"Stripped {en} Log", f"Bûche de {fr} écorcée"),
        "stripped_wood": (f"Stripped {en}", f"{Fr} écorcé"),
        "planks": (f"{en} Planks", f"Planches de {fr}"),
        "stairs": (f"{en} Stairs", f"Escalier en {fr}"),
        "slab": (f"{en} Slab", f"Dalle en {fr}"),
        "fence": (f"{en} Fence", f"Barrière en {fr}"),
        "fence_gate": (f"{en} Fence Gate", f"Portillon en {fr}"),
        "door": (f"{en} Door", f"Porte en {fr}"),
        "trapdoor": (f"{en} Trapdoor", f"Trappe en {fr}"),
        "button": (f"{en} Button", f"Bouton en {fr}"),
        "pressure_plate": (f"{en} Pressure Plate", f"Plaque de pression en {fr}"),
        "leaves": (f"{en} Leaves", f"Feuilles de {fr}"),
        "sapling": (f"{en} Sapling", f"Pousse de {fr}"),
    }[kind]


def lang():
    en, fr = {}, {}
    for w in WOODS:
        for bid, kind in ids(w).items():
            en[f"block.{NS}.{bid}"], fr[f"block.{NS}.{bid}"] = names(w, kind)
    return en, fr


# ------------------------------------------------------------------ textures
def textures():
    """{"block/<name>" | "item/<name>": Canvas}."""
    out = {}
    for i, (w, d) in enumerate(WOODS.items()):
        s = 300 + i * 20
        B = "block/"
        out[B + f"{w}_log"] = W.bark(d["bark"], d["bark_dark"], d["bark_light"], seed=s, ridge=d["lichen"])
        out[B + f"{w}_log_top"] = W.log_top(d["wood_light"], d["ring"], d["bark"], d["bark_dark"], seed=s + 1)
        out[B + f"stripped_{w}_log"] = W.stripped_side(d["wood"], d["wood_dark"], seed=s + 2)
        out[B + f"stripped_{w}_log_top"] = W.log_top(d["wood_light"], d["ring"], d["wood"], d["wood_dark"], seed=s + 3)
        out[B + f"{w}_planks"] = W.planks(d["wood"], d["wood_dark"], d["wood_light"], seed=s + 4)
        out[B + f"{w}_leaves"] = W.leaves(d["leaf"], d["leaf_light"], d["leaf_dark"], seed=s + 5, specks=d["speck"])
        out[B + f"{w}_sapling"] = W.sapling(d["bark_dark"], d["leaf"], d["leaf_light"], d["leaf_dark"], seed=s + 6,
                                            specks=d["speck"])
        for half in ("top", "bottom"):
            out[B + f"{w}_door_{half}"] = W.door(d["wood"], d["wood_dark"], d["wood_dark"], d["wood_light"], half,
                                                 seed=s + 7, window=d["door_window"], bands=d["door_bands"])
        out[B + f"{w}_trapdoor"] = W.trapdoor(d["wood"], d["wood_dark"], d["wood_dark"], d["wood_light"], seed=s + 8,
                                              holes=d["door_window"] is not None)
        out[f"item/{w}_door"] = W.door_item(d["wood"], d["wood_dark"], d["wood_dark"], d["wood_light"], seed=s + 7,
                                            window=d["door_window"], bands=d["door_bands"])
    return out


# ------------------------------------------------------------------ Java
def _signed(argb):
    return argb - (1 << 32) if argb >= 1 << 31 else argb


def java():
    L = ["package com.wayfarers.generated;", "",
         "import com.wayfarers.Wayfarers;",
         "import com.wayfarers.block.WoodBlocks;",
         "import com.wayfarers.registry.ModBlocks;",
         "import com.wayfarers.registry.ModItems;",
         "import net.minecraft.core.Direction;",
         "import net.minecraft.core.particles.ColorParticleOption;",
         "import net.minecraft.core.particles.ParticleTypes;",
         "import net.minecraft.core.registries.Registries;",
         "import net.minecraft.resources.ResourceKey;",
         "import net.minecraft.world.item.BlockItem;",
         "import net.minecraft.world.item.DoubleHighBlockItem;",
         "import net.minecraft.world.item.Item;",
         "import net.minecraft.world.level.block.Block;",
         "import net.minecraft.world.level.block.ButtonBlock;",
         "import net.minecraft.world.level.block.DoorBlock;",
         "import net.minecraft.world.level.block.PressurePlateBlock;",
         "import net.minecraft.world.level.block.RotatedPillarBlock;",
         "import net.minecraft.world.level.block.SaplingBlock;",
         "import net.minecraft.world.level.block.SoundType;",
         "import net.minecraft.world.level.block.TrapDoorBlock;",
         "import net.minecraft.world.level.block.grower.TreeGrower;",
         "import net.minecraft.world.level.block.state.BlockBehaviour;",
         "import net.minecraft.world.level.block.state.properties.BlockSetType;",
         "import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;",
         "import net.minecraft.world.level.block.state.properties.WoodType;",
         "import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;",
         "import net.minecraft.world.level.material.MapColor;",
         "import net.minecraft.world.level.material.PushReaction;",
         "import net.minecraftforge.registries.RegistryObject;", "",
         "import java.util.ArrayList;",
         "import java.util.List;",
         "import java.util.Optional;",
         "import java.util.function.Function;",
         "import java.util.function.Supplier;", "",
         "/** GENERATED by tools/gen_java.py from tools/wf/worldblocks.py — do not edit by hand. */",
         "public final class GeneratedWorldBlocks {",
         "    /** Block items in creative-tab order. */",
         "    public static final List<RegistryObject<Item>> ITEMS = new ArrayList<>();", ""]
    C = "GeneratedWorldBlocks."
    for w, d in WOODS.items():
        W_ = w.upper()
        wood, bark, leaves = d["color_wood"], d["color_bark"], d["color_leaves"]
        L.append(f'    /** Grows {NS}:{w}_tree (data/{NS}/worldgen/configured_feature), also planted by the world overhaul. */')
        L.append(f'    public static final TreeGrower {W_}_GROWER = new TreeGrower("{NS}_{w}", Optional.empty(), '
                 f'Optional.of(feature("{w}_tree")), Optional.empty());')
        for bid, kind in ids(w).items():
            K = bid.upper()
            P = "() -> BlockBehaviour.Properties.of()"
            if kind in ("log", "wood"):
                top = wood if kind == "log" else bark
                stripped = C + block_id(w, "stripped_" + kind).upper()
                e = f'block("{bid}", p -> new WoodBlocks.Log({stripped}, p), () -> log(MapColor.{top}, MapColor.{bark}))'
            elif kind in ("stripped_log", "stripped_wood"):
                e = f'block("{bid}", p -> new WoodBlocks.Log(null, p), () -> log(MapColor.{wood}, MapColor.{wood}))'
            elif kind == "planks":
                e = (f'block("{bid}", WoodBlocks.Planks::new, {P}.mapColor(MapColor.{wood})'
                     f'.instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F).sound(SoundType.WOOD).ignitedByLava())')
            elif kind == "stairs":
                e = (f'block("{bid}", p -> new WoodBlocks.Stairs({C}{W_}_PLANKS.get().defaultBlockState(), p), '
                     f'() -> BlockBehaviour.Properties.ofFullCopy({C}{W_}_PLANKS.get()))')
            elif kind == "slab":
                e = f'block("{bid}", WoodBlocks.Slab::new, () -> BlockBehaviour.Properties.ofFullCopy({C}{W_}_PLANKS.get()))'
            elif kind == "fence":
                e = (f'block("{bid}", WoodBlocks.Fence::new, {P}.mapColor(MapColor.{wood})'
                     f'.forceSolidOn().instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F).sound(SoundType.WOOD)'
                     f'.ignitedByLava())')
            elif kind == "fence_gate":
                e = (f'block("{bid}", p -> new WoodBlocks.FenceGate(WoodType.OAK, p), {P}'
                     f'.mapColor(MapColor.{wood}).forceSolidOn().instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F)'
                     f'.ignitedByLava())')
            elif kind == "door":
                e = (f'door("{bid}", p -> new DoorBlock(BlockSetType.OAK, p), {P}'
                     f'.mapColor(MapColor.{wood}).instrument(NoteBlockInstrument.BASS).strength(3.0F).noOcclusion()'
                     f'.ignitedByLava().pushReaction(PushReaction.DESTROY))')
            elif kind == "trapdoor":
                e = (f'block("{bid}", p -> new TrapDoorBlock(BlockSetType.OAK, p), {P}'
                     f'.mapColor(MapColor.{wood}).instrument(NoteBlockInstrument.BASS).strength(3.0F).noOcclusion()'
                     f'.isValidSpawn((s, l, p, t) -> false).ignitedByLava())')
            elif kind == "button":
                e = (f'block("{bid}", p -> new ButtonBlock(BlockSetType.OAK, 30, p), {P}'
                     f'.noCollision().strength(0.5F).pushReaction(PushReaction.DESTROY))')
            elif kind == "pressure_plate":
                e = (f'block("{bid}", p -> new PressurePlateBlock(BlockSetType.OAK, p), {P}'
                     f'.mapColor(MapColor.{wood}).forceSolidOn().instrument(NoteBlockInstrument.BASS).noCollision()'
                     f'.strength(0.5F).ignitedByLava().pushReaction(PushReaction.DESTROY))')
            elif kind == "leaves":
                e = (f'block("{bid}", p -> new WoodBlocks.Leaves(0.01F, ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, '
                     f'{_signed(d["particle"])}), p), () -> leaves(MapColor.{leaves}, {d["leaf_light_level"]}))')
            else:  # sapling
                light = 3 if d["leaf_light_level"] else 0
                e = (f'block("{bid}", p -> new SaplingBlock({W_}_GROWER, p), {P}'
                     f'.mapColor(MapColor.PLANT).noCollision().randomTicks().instabreak().sound(SoundType.GRASS)'
                     f'.pushReaction(PushReaction.DESTROY).lightLevel(s -> {light}))')
            L.append(f"    public static final RegistryObject<Block> {K} = {e};")
        L.append("")
    L += [
        "    /** Forces class initialisation so every block/item is queued on the deferred registers. */",
        "    public static void init() {}", "",
        "    private static ResourceKey<ConfiguredFeature<?, ?>> feature(String name) {",
        "        return ResourceKey.create(Registries.CONFIGURED_FEATURE, Wayfarers.id(name));",
        "    }", "",
        "    /** Like vanilla Blocks.logProperties: end colour on the Y axis, bark colour on the sides. */",
        "    private static BlockBehaviour.Properties log(MapColor top, MapColor side) {",
        "        return BlockBehaviour.Properties.of()",
        "                .mapColor(s -> s.getValue(RotatedPillarBlock.AXIS) == Direction.Axis.Y ? top : side)",
        "                .instrument(NoteBlockInstrument.BASS).strength(2.0F).sound(SoundType.WOOD).ignitedByLava();",
        "    }", "",
        "    /** Like vanilla Blocks.leavesProperties, plus an optional glow. */",
        "    private static BlockBehaviour.Properties leaves(MapColor color, int light) {",
        "        return BlockBehaviour.Properties.of().mapColor(color).strength(0.2F).randomTicks().sound(SoundType.GRASS)",
        "                .noOcclusion().isValidSpawn((s, l, p, t) -> false).isSuffocating((s, l, p) -> false)",
        "                .isViewBlocking((s, l, p) -> false).ignitedByLava().pushReaction(PushReaction.DESTROY)",
        "                .isRedstoneConductor((s, l, p) -> false).lightLevel(s -> light);",
        "    }", "",
        "    private static RegistryObject<Block> block(String name, Function<BlockBehaviour.Properties, Block> factory,",
        "                                               Supplier<BlockBehaviour.Properties> props) {",
        "        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name,",
        "                () -> factory.apply(props.get().setId(ModBlocks.BLOCKS.key(name))));",
        "        ITEMS.add(ModItems.ITEMS.register(name, () -> new BlockItem(block.get(),",
        "                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix())));",
        "        return block;",
        "    }", "",
        "    /** A door: its item places both halves (vanilla DoubleHighBlockItem). */",
        "    private static RegistryObject<Block> door(String name, Function<BlockBehaviour.Properties, Block> factory,",
        "                                              Supplier<BlockBehaviour.Properties> props) {",
        "        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name,",
        "                () -> factory.apply(props.get().setId(ModBlocks.BLOCKS.key(name))));",
        "        ITEMS.add(ModItems.ITEMS.register(name, () -> new DoubleHighBlockItem(block.get(),",
        "                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix())));",
        "        return block;",
        "    }", "",
        "    private GeneratedWorldBlocks() {}",
        "}", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ assets (models, blockstates, item definitions)
def assets(write, item_definition, stairs_blockstate):
    """Vanilla's block model templates and blockstate layouts (26.2 BlockModelGenerators) for every wood block."""
    T = f"{NS}:block/"

    def M(n):
        return T + n

    def model(name, parent, **textures):
        write(f"models/block/{name}.json", {"parent": f"minecraft:block/{parent}",
                                            "textures": {k: T + v for k, v in textures.items()}})

    def simple(bid):
        write(f"blockstates/{bid}.json", {"variants": {"": {"model": M(bid)}}})

    for w in WOODS:
        planks = f"{w}_planks"
        for kind in ("log", "wood", "stripped_log", "stripped_wood"):
            bid = block_id(w, kind)
            side = block_id(w, "stripped_log" if "stripped" in kind else "log")
            end = side + "_top" if kind.endswith("log") else side
            model(bid, "cube_column", end=end, side=side)
            model(bid + "_horizontal", "cube_column_horizontal", end=end, side=side)
            write(f"blockstates/{bid}.json", {"variants": {
                "axis=y": {"model": M(bid)},
                "axis=z": {"model": M(bid + "_horizontal"), "x": 90},
                "axis=x": {"model": M(bid + "_horizontal"), "x": 90, "y": 90}}})
            item_definition(bid, M(bid))
        model(planks, "cube_all", all=planks)
        simple(planks)
        item_definition(planks, M(planks))
        # stairs and slab
        tex3 = dict(bottom=planks, top=planks, side=planks)
        st = f"{w}_stairs"
        for suffix, parent in (("", "stairs"), ("_inner", "inner_stairs"), ("_outer", "outer_stairs")):
            model(st + suffix, parent, **tex3)
        write(f"blockstates/{st}.json", stairs_blockstate(M(st)))
        item_definition(st, M(st))
        sl = f"{w}_slab"
        model(sl, "slab", **tex3)
        model(sl + "_top", "slab_top", **tex3)
        write(f"blockstates/{sl}.json", {"variants": {"type=bottom": {"model": M(sl)}, "type=top": {"model": M(sl + "_top")},
                                                      "type=double": {"model": M(planks)}}})
        item_definition(sl, M(sl))
        # fence (createFence)
        fe = f"{w}_fence"
        for suffix, parent in (("_post", "fence_post"), ("_side", "fence_side"), ("_inventory", "fence_inventory")):
            model(fe + suffix, parent, texture=planks)
        parts = [{"apply": {"model": M(fe + "_post")}}]
        for direction, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
            apply = {"model": M(fe + "_side"), "uvlock": True}
            if y:
                apply["y"] = y
            parts.append({"when": {direction: "true"}, "apply": apply})
        write(f"blockstates/{fe}.json", {"multipart": parts})
        item_definition(fe, M(fe + "_inventory"))
        # fence gate (createFenceGate with ROTATION_HORIZONTAL_FACING_ALT, uv-locked like every wooden gate)
        fg = f"{w}_fence_gate"
        for suffix, parent in (("", "template_fence_gate"), ("_open", "template_fence_gate_open"),
                               ("_wall", "template_fence_gate_wall"), ("_wall_open", "template_fence_gate_wall_open")):
            model(fg + suffix, parent, texture=planks)
        variants = {}
        for facing, y in (("south", 0), ("west", 90), ("north", 180), ("east", 270)):
            for in_wall in ("false", "true"):
                for opened in ("false", "true"):
                    suffix = ("_wall" if in_wall == "true" else "") + ("_open" if opened == "true" else "")
                    v = {"model": M(fg + suffix), "uvlock": True}
                    if y:
                        v["y"] = y
                    variants[f"facing={facing},in_wall={in_wall},open={opened}"] = v
        write(f"blockstates/{fg}.json", {"variants": variants})
        item_definition(fg, M(fg))
        # door (createDoor)
        do = f"{w}_door"
        for part in ("bottom_left", "bottom_left_open", "bottom_right", "bottom_right_open",
                     "top_left", "top_left_open", "top_right", "top_right_open"):
            model(f"{do}_{part}", f"door_{part}", top=do + "_top", bottom=do + "_bottom")
        variants = {}
        rot = {"east": 0, "south": 90, "west": 180, "north": 270}
        for facing in ("east", "south", "west", "north"):
            for half, h in (("lower", "bottom"), ("upper", "top")):
                for hinge in ("left", "right"):
                    for opened in ("false", "true"):
                        y = rot[facing]
                        if opened == "true":
                            y = (y + (90 if hinge == "left" else 270)) % 360
                        v = {"model": M(f"{do}_{h}_{hinge}" + ("_open" if opened == "true" else ""))}
                        if y:
                            v["y"] = y
                        variants[f"facing={facing},half={half},hinge={hinge},open={opened}"] = v
        write(f"blockstates/{do}.json", {"variants": variants})
        write(f"models/item/{do}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{do}"}})
        item_definition(do, f"{NS}:item/{do}")
        # trapdoor (createOrientableTrapdoor)
        td = f"{w}_trapdoor"
        for suffix, parent in (("_bottom", "template_orientable_trapdoor_bottom"),
                               ("_top", "template_orientable_trapdoor_top"),
                               ("_open", "template_orientable_trapdoor_open")):
            model(td + suffix, parent, texture=td)
        variants = {}
        yrot = {"north": 0, "south": 180, "east": 90, "west": 270}
        for facing in ("north", "south", "east", "west"):
            for half in ("bottom", "top"):
                for opened in ("false", "true"):
                    y, x = yrot[facing], 0
                    if opened == "true" and half == "top":
                        x, y = 180, (y + 180) % 360
                    v = {"model": M(td + ("_open" if opened == "true" else f"_{half}"))}
                    if x:
                        v["x"] = x
                    if y:
                        v["y"] = y
                    variants[f"facing={facing},half={half},open={opened}"] = v
        write(f"blockstates/{td}.json", {"variants": variants})
        item_definition(td, M(td + "_bottom"))
        # button (createButton)
        bu = f"{w}_button"
        for suffix, parent in (("", "button"), ("_pressed", "button_pressed"), ("_inventory", "button_inventory")):
            model(bu + suffix, parent, texture=planks)
        variants = {}
        floor_y = {"north": 0, "east": 90, "south": 180, "west": 270}
        ceiling_y = {"south": 0, "west": 90, "north": 180, "east": 270}
        for face in ("floor", "wall", "ceiling"):
            for facing in ("north", "east", "south", "west"):
                for powered in ("false", "true"):
                    v = {"model": M(bu + ("_pressed" if powered == "true" else ""))}
                    x, y = {"floor": (0, floor_y[facing]), "wall": (90, floor_y[facing]),
                            "ceiling": (180, ceiling_y[facing])}[face]
                    if x:
                        v["x"] = x
                    if y:
                        v["y"] = y
                    if face == "wall":
                        v["uvlock"] = True
                    variants[f"face={face},facing={facing},powered={powered}"] = v
        write(f"blockstates/{bu}.json", {"variants": variants})
        item_definition(bu, M(bu + "_inventory"))
        # pressure plate
        pp = f"{w}_pressure_plate"
        model(pp, "pressure_plate_up", texture=planks)
        model(pp + "_down", "pressure_plate_down", texture=planks)
        write(f"blockstates/{pp}.json", {"variants": {"powered=false": {"model": M(pp)},
                                                      "powered=true": {"model": M(pp + "_down")}}})
        item_definition(pp, M(pp))
        # leaves: already coloured, so cube_all (vanilla's leaves model tints them with the biome foliage colour)
        le = f"{w}_leaves"
        model(le, "cube_all", all=le)
        simple(le)
        item_definition(le, M(le))
        # sapling: cross model, flat item
        sa = f"{w}_sapling"
        model(sa, "cross", cross=sa)
        simple(sa)
        write(f"models/item/{sa}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": T + sa}})
        item_definition(sa, f"{NS}:item/{sa}")


# ------------------------------------------------------------------ data (trees, recipes, loot, tags)
def _state(name, **props):
    st = {"Name": name}
    if props:
        st["Properties"] = {k: str(v).lower() for k, v in props.items()}
    return st


def _simple(state):
    return {"type": "minecraft:simple_state_provider", "state": state}


BELOW_TRUNK = {"type": "minecraft:rule_based_state_provider", "rules": [{
    "if_true": {"type": "minecraft:not", "predicate": {"type": "minecraft:matching_block_tag",
                                                         "tag": "minecraft:cannot_replace_below_tree_trunk"}},
    "then": {"type": "minecraft:simple_state_provider", "state": {"Name": "minecraft:dirt"}}}]}


def tree_feature(w):
    """Configured tree of a wood: Glowwood grows like a fancy oak, Rustwood forks like an acacia."""
    d = WOODS[w]
    base, a, b = d["tree"]["height"]
    log = _simple(_state(f"{NS}:{w}_log", axis="y"))
    leaves = _simple(_state(f"{NS}:{w}_leaves", distance=7, persistent=False, waterlogged=False))
    if d["tree"]["trunk"] == "fancy":
        trunk = {"type": "minecraft:fancy_trunk_placer", "base_height": base, "height_rand_a": a, "height_rand_b": b}
        foliage = {"type": "minecraft:fancy_foliage_placer", "radius": 2, "offset": 4, "height": 4}
        size = {"type": "minecraft:two_layers_feature_size", "limit": 0, "lower_size": 0, "upper_size": 0,
                "min_clipped_height": 4}
    else:
        trunk = {"type": "minecraft:forking_trunk_placer", "base_height": base, "height_rand_a": a, "height_rand_b": b}
        foliage = {"type": "minecraft:acacia_foliage_placer", "radius": 2, "offset": 0}
        size = {"type": "minecraft:two_layers_feature_size", "limit": 1, "lower_size": 0, "upper_size": 2}
    return {"type": "minecraft:tree", "config": {
        "trunk_provider": log, "trunk_placer": trunk, "foliage_provider": leaves, "foliage_placer": foliage,
        "minimum_size": size, "decorators": [], "ignore_vines": True, "below_trunk_provider": BELOW_TRUNK}}


SILK_OR_SHEARS = {"condition": "minecraft:any_of", "terms": [
    {"condition": "minecraft:match_tool", "predicate": {"items": "minecraft:shears"}},
    {"condition": "minecraft:match_tool", "predicate": {"predicates": {"minecraft:enchantments": [
        {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}]}


def _loot(bid, kind, w):
    me = f"{NS}:{bid}"
    if kind == "leaves":  # vanilla createLeavesDrops: the leaves with shears or silk touch, else a sapling, sticks
        return [
            {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{"type": "minecraft:alternatives", "children": [
                {"type": "minecraft:item", "name": me, "conditions": [SILK_OR_SHEARS]},
                {"type": "minecraft:item", "name": f"{NS}:{w}_sapling", "conditions": [
                    {"condition": "minecraft:survives_explosion"},
                    {"condition": "minecraft:table_bonus", "enchantment": "minecraft:fortune",
                     "chances": [0.05, 0.0625, 0.083333336, 0.1]}]}]}]},
            {"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:inverted", "term": SILK_OR_SHEARS}],
             "entries": [{"type": "minecraft:item", "name": "minecraft:stick",
                          "conditions": [{"condition": "minecraft:table_bonus", "enchantment": "minecraft:fortune",
                                          "chances": [0.02, 0.022222223, 0.025, 0.033333335, 0.1]}],
                          "functions": [{"function": "minecraft:set_count", "add": False,
                                         "count": {"type": "minecraft:uniform", "min": 1.0, "max": 2.0}},
                                        {"function": "minecraft:explosion_decay"}]}]}]
    pool = {"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
            "entries": [{"type": "minecraft:item", "name": me}]}
    if kind == "door":  # only the lower half drops the door
        pool["conditions"].append({"condition": "minecraft:block_state_property", "block": me,
                                   "properties": {"half": "lower"}})
    if kind == "slab":
        pool["entries"][0]["functions"] = [{"function": "minecraft:set_count", "count": 2.0, "add": False, "conditions": [
            {"condition": "minecraft:block_state_property", "block": me, "properties": {"type": "double"}}]}]
    return [pool]


TAGS = {  # kind -> vanilla tags (block and item tags of the same name, unless listed in BLOCK_ONLY)
    "log": ["logs_that_burn", "overworld_natural_logs"], "wood": ["logs_that_burn"],
    "stripped_log": ["logs_that_burn"], "stripped_wood": ["logs_that_burn"], "planks": ["planks"],
    "stairs": ["wooden_stairs"], "slab": ["wooden_slabs"], "fence": ["wooden_fences"], "fence_gate": ["fence_gates"],
    "door": ["wooden_doors"], "trapdoor": ["wooden_trapdoors"], "button": ["wooden_buttons"],
    "pressure_plate": ["wooden_pressure_plates"], "leaves": ["leaves"], "sapling": ["saplings"],
}
BLOCK_ONLY = {"overworld_natural_logs"}


def data(write):
    """Writes the woods' trees, recipes and loot; returns {tag file under data/: [values]} to merge."""
    tags = {}

    def tag(rel, value):
        tags.setdefault(rel, []).append(value)

    def shaped(name, pattern, key, count, category="building", group=None):
        r = {"type": "minecraft:crafting_shaped", "category": category, "pattern": pattern, "key": key,
             "result": {"id": f"{NS}:{name}", "count": count}}
        if group:
            r["group"] = group
        write(f"{NS}/recipe/{name}.json", r)

    for w, d in WOODS.items():
        write(f"{NS}/worldgen/configured_feature/{w}_tree.json", tree_feature(w))
        for bid, kind in ids(w).items():
            me = f"{NS}:{bid}"
            write(f"{NS}/loot_table/blocks/{bid}.json", {"type": "minecraft:block", "pools": _loot(bid, kind, w),
                                                        "random_sequence": f"{NS}:blocks/{bid}"})
            for t in TAGS[kind]:
                tag(f"minecraft/tags/block/{t}.json", me)
                if t not in BLOCK_ONLY:
                    tag(f"minecraft/tags/item/{t}.json", me)
            tool = "hoe" if kind == "leaves" else None if kind == "sapling" else "axe"
            if tool:
                tag(f"minecraft/tags/block/mineable/{tool}.json", me)
        logs = [f"{NS}:{block_id(w, k)}" for k in ("log", "wood", "stripped_log", "stripped_wood")]
        write(f"{NS}/tags/item/{w}_logs.json", {"values": logs})
        write(f"{NS}/tags/block/{w}_logs.json", {"values": logs})
        P, S = f"{NS}:{w}_planks", "minecraft:stick"
        write(f"{NS}/recipe/{w}_planks.json", {"type": "minecraft:crafting_shapeless", "category": "building",
                                              "group": "planks", "ingredients": [f"#{NS}:{w}_logs"],
                                              "result": {"id": P, "count": 4}})
        shaped(f"{w}_wood", ["##", "##"], {"#": f"{NS}:{w}_log"}, 3, group="bark")
        shaped(f"stripped_{w}_wood", ["##", "##"], {"#": f"{NS}:stripped_{w}_log"}, 3, group="bark")
        shaped(f"{w}_stairs", ["#  ", "## ", "###"], {"#": P}, 4, group="wooden_stairs")
        shaped(f"{w}_slab", ["###"], {"#": P}, 6, group="wooden_slab")
        shaped(f"{w}_fence", ["W#W", "W#W"], {"W": P, "#": S}, 3, category="misc", group="wooden_fence")
        shaped(f"{w}_fence_gate", ["#W#", "#W#"], {"W": P, "#": S}, 1, category="redstone", group="wooden_fence_gate")
        shaped(f"{w}_door", ["##", "##", "##"], {"#": P}, 3, category="redstone", group="wooden_door")
        shaped(f"{w}_trapdoor", ["###", "###"], {"#": P}, 2, category="redstone", group="wooden_trapdoor")
        shaped(f"{w}_pressure_plate", ["##"], {"#": P}, 1, category="redstone", group="wooden_pressure_plate")
        write(f"{NS}/recipe/{w}_button.json", {"type": "minecraft:crafting_shapeless", "category": "redstone",
                                              "group": "wooden_button", "ingredients": [P],
                                              "result": {"id": f"{NS}:{w}_button", "count": 1}})
        # a sapling from vanilla ones, so the trees can be grown in any world (with or without the overhaul)
        write(f"{NS}/recipe/{w}_sapling.json", {"type": "minecraft:crafting_shapeless", "category": "misc",
                                               "ingredients": d["sapling_recipe"],
                                               "result": {"id": f"{NS}:{w}_sapling", "count": 1}})
    stone_data(write)
    return tags


# ------------------------------------------------------------------ stones (blocks in decor.py)
# base stone -> its other forms, in the order the stonecutter offers them (each form cuts into the later ones)
STONE_SETS = {
    "marble": ["polished_marble", "marble_bricks", "marble_pillar", "chiseled_marble"],
    "rust_rock": ["polished_rust_rock", "rust_rock_bricks"],
    "blue_slate": ["polished_blue_slate", "blue_slate_bricks", "blue_slate_tiles"],
}
# the raw stone from vanilla blocks, for worlds without the overhaul: (pattern, key, count)
STONE_CRAFT = {
    "marble": (["CD", "DC"], {"C": "minecraft:calcite", "D": "minecraft:diorite"}, 4),
    "rust_rock": ([" G ", "GIG", " G "], {"G": "minecraft:granite", "I": "minecraft:iron_nugget"}, 4),
    "blue_slate": ([" D ", "DLD", " D "], {"D": "minecraft:cobbled_deepslate", "L": "minecraft:lapis_lazuli"}, 4),
}


def stone_data(write):
    """Crafting and stonecutter recipes between the forms of each stone (decor_data already cuts every block into
    its own stairs, slab and wall)."""
    from . import decor

    def cut(src, dst, count=1):
        write(f"{NS}/recipe/{dst}_from_{src}_stonecutting.json", {
            "type": "minecraft:stonecutting", "ingredient": f"{NS}:{src}", "result": {"id": f"{NS}:{dst}", "count": count}})

    def shaped(name, pattern, key, count):
        write(f"{NS}/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "building",
                                          "pattern": pattern, "key": key, "result": {"id": f"{NS}:{name}", "count": count}})

    for base, forms in STONE_SETS.items():
        pattern, key, count = STONE_CRAFT[base]
        shaped(base, pattern, key, count)
        chain = [base] + forms
        for i, src in enumerate(chain):
            for dst in chain[i + 1:]:
                cut(src, dst)
                for v in decor.DECOR[dst]["variants"]:
                    cut(src, decor.variant_id(dst, v), 2 if v == "slab" else 1)
        polished = forms[0]
        shaped(polished, ["##", "##"], {"#": f"{NS}:{base}"}, 4)
        for form in forms[1:]:
            if form.endswith("_bricks"):
                shaped(form, ["##", "##"], {"#": f"{NS}:{polished}"}, 4)
            elif form.endswith("_tiles"):
                shaped(form, ["##", "##"], {"#": f"{NS}:{chain[2]}"}, 4)
            elif form.endswith("_pillar"):
                shaped(form, ["#", "#"], {"#": f"{NS}:{polished}"}, 2)
            elif form.startswith("chiseled_"):
                shaped(form, ["#", "#"], {"#": f"{NS}:{decor.variant_id(polished, 'slab')}"}, 1)
