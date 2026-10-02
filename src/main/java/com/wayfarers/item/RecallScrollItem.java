package com.wayfarers.item;

import com.wayfarers.data.WayfarersData;
import com.wayfarers.util.Waystones;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import java.util.Comparator;
import java.util.Map;

/** Single-use scroll: teleports to the nearest waystone of the current dimension. */
public class RecallScrollItem extends AbilityItem {
    public RecallScrollItem(Properties properties) {
        super(properties, 40, 0);
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        if (!(player instanceof net.minecraft.server.level.ServerPlayer serverPlayer)) {
            return false;
        }
        var dim = level.dimension().identifier();
        var nearest = WayfarersData.get(level.getServer()).sortedWaystones().stream()
                .filter(e -> e.getValue().dimension().equals(dim))
                .min(Comparator.comparingDouble((Map.Entry<String, WayfarersData.Waystone> e) ->
                        e.getValue().pos().distSqr(player.blockPosition())));
        if (nearest.isEmpty() || !Waystones.warp(serverPlayer, nearest.get().getKey())) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.none").withStyle(ChatFormatting.GRAY));
            return false;
        }
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        return true;
    }
}
