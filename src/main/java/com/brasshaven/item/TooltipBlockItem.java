package com.brasshaven.item;

import net.minecraft.ChatFormatting;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.block.Block;

import java.util.function.Consumer;

public class TooltipBlockItem extends BlockItem {
    public TooltipBlockItem(Block block, Properties properties) {
        super(block, properties);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
                                Consumer<Component> builder, TooltipFlag flag) {
        super.appendHoverText(stack, context, display, builder, flag);
        String key = getBlock().getDescriptionId() + ".desc";
        if (Language.getInstance().has(key)) {
            builder.accept(Component.translatable(key).withStyle(ChatFormatting.GRAY));
        }
        // longer explanations come as extra lines: .desc2, .desc3
        for (int i = 2; Language.getInstance().has(key + i); i++) {
            builder.accept(Component.translatable(key + i).withStyle(ChatFormatting.GRAY));
        }
    }
}
