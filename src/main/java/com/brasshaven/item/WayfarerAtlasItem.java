package com.brasshaven.item;

import com.brasshaven.util.QuestBook;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Opens the quest journal: the guild's progress through the five chapters of the quest line. Sneak-use opens the
 * world map instead (client side; the map is also on the M key). Before the first step of the progression ladder is
 * done, it also marks the way to the nearest Guild Outpost again ({@link com.brasshaven.util.Progression}).
 */
public class WayfarerAtlasItem extends TooltipItem {
    public WayfarerAtlasItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (player.isShiftKeyDown()) {
            if (level.isClientSide() && net.minecraftforge.fml.loading.FMLEnvironment.dist == net.minecraftforge.api.distmarker.Dist.CLIENT) {
                com.brasshaven.client.ClientHooks.openWorldMap();
            } else if (!level.isClientSide()) {
                level.playSound(null, player, SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0F, 0.8F);
            }
            return InteractionResult.SUCCESS;
        }
        if (player instanceof ServerPlayer serverPlayer) {
            com.brasshaven.network.BrasshavenNet.toPlayer(serverPlayer, QuestBook.snapshot(serverPlayer, true));
            level.playSound(null, player, SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0F, 1.0F);
            // until the first Guild Agent is met, the Atlas also shows the way to the nearest Guild Outpost again
            com.brasshaven.util.Progression.atlasUsed(serverPlayer);
        }
        return InteractionResult.SUCCESS;
    }
}
