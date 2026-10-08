package com.brasshaven.colossal;

import com.brasshaven.item.BrassTooltip;
import com.brasshaven.item.TooltipItem;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.List;

/**
 * A piece of a vault armour set: the Brasshaven tooltip with the set's 2-piece and 4-piece bonuses (the ones the
 * viewer already has lit up) and, with Shift, the structure it comes from.
 */
public class ColossalArmorItem extends TooltipItem {
    private final ColossalSet set;

    public ColossalArmorItem(Properties properties, ColossalSet set) {
        super(properties);
        this.set = set;
    }

    public ColossalSet set() {
        return set;
    }

    @Override
    public void facts(ItemStack stack, List<Component> facts, List<Component> details) {
        int worn = wornByViewer();
        facts.add(BrassTooltip.heading(Component.translatable("tooltip.brasshaven.colossal.set", worn)));
        String base = "tooltip.brasshaven.colossal." + set.prefix();
        line(facts, "tooltip.brasshaven.colossal.two", base + ".two", worn >= 2);
        line(facts, "tooltip.brasshaven.colossal.four", base + ".four", worn >= 4);
        details.add(BrassTooltip.detail(Component.translatable("tooltip.brasshaven.relic",
                Component.translatable("tooltip.brasshaven.relic." + set.structure))));
    }

    /** "2 pieces: ..." wrapped like every Brasshaven rule; brighter once the viewer has that many pieces on. */
    private static void line(List<Component> out, String frame, String bonus, boolean active) {
        Language lang = Language.getInstance();
        String text = lang.getOrDefault(frame).replace("%s", lang.getOrDefault(bonus));
        for (String l : BrassTooltip.wrap(text)) {
            out.add(active ? BrassTooltip.rule(l) : BrassTooltip.detail(Component.literal(l)));
        }
    }

    /** Pieces of this set the local player wears (tooltips are only built on the client; 0 elsewhere). */
    private int wornByViewer() {
        return FMLEnvironment.dist == Dist.CLIENT ? ColossalClient.worn(set) : 0;
    }
}
