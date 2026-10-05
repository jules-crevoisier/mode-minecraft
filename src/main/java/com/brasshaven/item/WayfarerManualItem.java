package com.brasshaven.item;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.loading.FMLEnvironment;

/** Opens the Wayfarer's Manual, the in-game guide to every system of the mod. */
public class WayfarerManualItem extends TooltipItem {
    public WayfarerManualItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (level.isClientSide() && FMLEnvironment.dist == Dist.CLIENT) {
            com.brasshaven.client.ClientHooks.openGuide(null);
            player.playSound(SoundEvents.BOOK_PAGE_TURN, 1.0F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }
}
