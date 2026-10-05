package com.wayfarers.registry;

import com.wayfarers.item.TooltipBlockItem;
import com.wayfarers.social.ContractMenu;
import com.wayfarers.social.PostMenu;
import com.wayfarers.social.SocialBlock;
import com.wayfarers.social.TradeMenu;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.common.extensions.IForgeMenuType;
import net.minecraftforge.network.IContainerFactory;
import net.minecraftforge.registries.RegistryObject;

import java.util.function.Function;

/**
 * Multiplayer features (com.wayfarers.social): the Pneumatic Post and the Contract Board, and the three menus (trade,
 * post, board). Names, models, textures and recipes come from tools/wf/social.py.
 */
public final class ModSocial {
    // ---- blocks
    public static final RegistryObject<Block> PNEUMATIC_POST = block("pneumatic_post", SocialBlock::post,
            BlockBehaviour.Properties.of().mapColor(MapColor.GOLD).strength(2.0F, 6.0F).sound(SoundType.COPPER)
                    .noOcclusion().requiresCorrectToolForDrops());
    public static final RegistryObject<Block> CONTRACT_BOARD_BLOCK = block("contract_board", SocialBlock::board,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.5F, 3.0F).sound(SoundType.WOOD).noOcclusion());

    // ---- menus
    public static final RegistryObject<MenuType<TradeMenu>> TRADE = menu("trade", TradeMenu::new);
    public static final RegistryObject<MenuType<PostMenu>> POST = menu("pneumatic_post",
            (id, inv, buf) -> new PostMenu(id, inv, buf.readBlockPos()));
    public static final RegistryObject<MenuType<ContractMenu>> CONTRACT_BOARD = menu("contract_board",
            (id, inv, buf) -> new ContractMenu(id, inv, buf.readBlockPos()));

    private ModSocial() {}

    /** Forces class initialisation so every entry is queued on the deferred registers. */
    public static void init() {}

    private static RegistryObject<Block> block(String name, Function<BlockBehaviour.Properties, Block> factory,
                                               BlockBehaviour.Properties props) {
        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name, () -> factory.apply(props.setId(ModBlocks.BLOCKS.key(name))));
        RegistryObject<Item> item = ModItems.ITEMS.register(name, () -> new TooltipBlockItem(block.get(),
                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix()));
        ModItems.ALL.add(item);
        return block;
    }

    private static <M extends AbstractContainerMenu> RegistryObject<MenuType<M>> menu(String name, IContainerFactory<M> factory) {
        return ModMenus.MENUS.register(name, () -> IForgeMenuType.create(factory));
    }
}
