package com.brasshaven.item;

import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

import java.util.List;
import java.util.function.Consumer;

/**
 * Base item with the Brasshaven tooltip ({@link BrassTooltip}): flavour, rules (".desc", ".desc2"...), key facts and
 * "Hold Shift for details". Subclasses add their numbers in {@link #facts}.
 */
public class TooltipItem extends Item implements BrassTooltip.Styled, BrassTooltip.Facts {
    public TooltipItem(Properties properties) {
        super(properties);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
                                Consumer<Component> builder, TooltipFlag flag) {
        super.appendHoverText(stack, context, display, builder, flag);
        BrassTooltip.append(stack, builder);
    }

    @Override
    public void facts(ItemStack stack, List<Component> facts, List<Component> details) {
    }
}
