package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.block.AltarBlock;
import com.wayfarers.block.GraveBlock;
import com.wayfarers.block.GuildTerminalBlock;
import com.wayfarers.block.SortingChestBlock;
import com.wayfarers.block.WaystoneBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.function.Function;

public final class ModBlocks {
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, Wayfarers.MODID);

    public static final RegistryObject<Block> WAYSTONE = register("waystone", WaystoneBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3.0F, 1200.0F)
                    .sound(SoundType.STONE).noOcclusion().lightLevel(s -> 7));
    public static final RegistryObject<Block> SORTING_CHEST = register("sorting_chest", SortingChestBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.5F).sound(SoundType.WOOD));
    public static final RegistryObject<Block> GUILD_TERMINAL = register("guild_terminal", GuildTerminalBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.5F).sound(SoundType.WOOD).lightLevel(s -> 5));
    public static final RegistryObject<Block> GRAVE = register("grave", GraveBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(-1.0F, 3600000.0F)
                    .sound(SoundType.STONE).noOcclusion());
    public static final RegistryObject<Block> SEALED_BARS = register("sealed_bars", Block::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(-1.0F, 3600000.0F)
                    .sound(SoundType.METAL).noOcclusion());
    public static final RegistryObject<Block> WARDEN_ALTAR = register("warden_altar",
            p -> new AltarBlock(p, AltarBlock.Boss.DROWNED_WARDEN),
            BlockBehaviour.Properties.of().mapColor(MapColor.WARPED_WART_BLOCK).strength(-1.0F, 3600000.0F)
                    .sound(SoundType.STONE).lightLevel(s -> 10));
    public static final RegistryObject<Block> VOID_ALTAR = register("void_altar",
            p -> new AltarBlock(p, AltarBlock.Boss.VOID_WARDEN),
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE).strength(-1.0F, 3600000.0F)
                    .sound(SoundType.STONE).lightLevel(s -> 10));
    public static final RegistryObject<Block> LITHITE_ORE = register("lithite_ore", Block::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3.0F, 3.0F)
                    .requiresCorrectToolForDrops().lightLevel(s -> 3));
    public static final RegistryObject<Block> DEEPSLATE_LITHITE_ORE = register("deepslate_lithite_ore", Block::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.DEEPSLATE).strength(4.5F, 3.0F)
                    .sound(SoundType.DEEPSLATE).requiresCorrectToolForDrops().lightLevel(s -> 3));

    private static <B extends Block> RegistryObject<B> register(String name, Function<BlockBehaviour.Properties, B> factory,
                                                               BlockBehaviour.Properties props) {
        return BLOCKS.register(name, () -> factory.apply(props.setId(BLOCKS.key(name))));
    }

    private ModBlocks() {}
}
