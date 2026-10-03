package com.wayfarers.item;

import com.wayfarers.util.QuestBook;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/** Opens the quest journal: the guild's progress through the five chapters of the quest line. */
public class WayfarerAtlasItem extends TooltipItem {
    public WayfarerAtlasItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (player instanceof ServerPlayer serverPlayer) {
            com.wayfarers.network.WayfarersNet.toPlayer(serverPlayer, QuestBook.snapshot(serverPlayer, true));
            level.playSound(null, player, SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }
}
