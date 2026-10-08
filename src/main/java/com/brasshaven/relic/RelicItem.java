package com.brasshaven.relic;

import com.brasshaven.item.BrassTooltip;
import com.brasshaven.item.TooltipItem;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/** A relic armour piece or accessory: the Brasshaven tooltip plus the structure it comes from. */
public class RelicItem extends TooltipItem {
    private final String structure;

    public RelicItem(Properties properties, String structure) {
        super(properties);
        this.structure = structure;
    }

    @Override
    public void facts(ItemStack stack, List<Component> facts, List<Component> details) {
        details.add(origin(structure));
    }

    /** "Relic of the Glacier Hall" (tooltip.brasshaven.relic.<structure>, tools/wf/relics.py). */
    static Component origin(String structure) {
        return BrassTooltip.detail(Component.translatable("tooltip.brasshaven.relic",
                Component.translatable("tooltip.brasshaven.relic." + structure)));
    }
}
