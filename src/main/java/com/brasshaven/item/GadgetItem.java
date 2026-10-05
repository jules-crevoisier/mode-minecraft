package com.brasshaven.item;

import net.minecraft.ChatFormatting;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

import java.util.function.Consumer;

/** A steam gadget (tools/wf/gadgets.py): its tooltip has up to three lines, ".desc", ".desc2" and ".desc3". */
public class GadgetItem extends TooltipItem {
    public GadgetItem(Properties properties) {
        super(properties);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
                                Consumer<Component> builder, TooltipFlag flag) {
        super.appendHoverText(stack, context, display, builder, flag);
        for (int i = 2; i <= 3; i++) {
            String key = getDescriptionId() + ".desc" + i;
            if (Language.getInstance().has(key)) {
                builder.accept(Component.translatable(key).withStyle(ChatFormatting.GRAY));
            }
        }
    }
}
