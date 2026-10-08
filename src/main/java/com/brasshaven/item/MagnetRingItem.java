package com.brasshaven.item;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Worn in a ring slot and enabled (shown by the enchantment glint), it pulls items and XP orbs to its wearer. */
public class MagnetRingItem extends TooltipItem {

    public MagnetRingItem(Properties properties) {
        super(properties);
    }

    public static boolean isEnabled(ItemStack stack) {
        return Boolean.TRUE.equals(stack.get(DataComponents.ENCHANTMENT_GLINT_OVERRIDE));
    }

    public static void toggle(Player player, ItemStack stack) {
        boolean on = !isEnabled(stack);
        stack.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, on);
        player.sendSystemMessage(Component.translatable(on ? "message.brasshaven.magnet.on" : "message.brasshaven.magnet.off")
                .withStyle(on ? ChatFormatting.GREEN : ChatFormatting.GRAY));
        player.level().playSound(null, player, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.7F, on ? 1.4F : 0.8F);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (!level.isClientSide()) {
            toggle(player, player.getItemInHand(hand));
        }
        return InteractionResult.SUCCESS;
    }

    /**
     * Pulls the items and XP orbs around a player to them (server option items.magnetRange). Only a ring worn in an
     * accessory slot and switched on does this (accessory/AccessoryEvents).
     */
    public static void pull(Player player, ServerLevel level) {
        if (player.isSpectator() || !player.isAlive()) {
            return;
        }
        double range = com.brasshaven.config.BrasshavenConfig.MAGNET_RANGE.get(); // server option (items.magnetRange)
        if (range <= 0) {
            return;
        }
        for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, player.getBoundingBox().inflate(range),
                e -> e.isAlive() && !e.hasPickUpDelay())) {
            item.setPos(player.getX(), player.getY() + 0.2, player.getZ());
        }
        for (ExperienceOrb orb : level.getEntitiesOfClass(ExperienceOrb.class, player.getBoundingBox().inflate(range))) {
            orb.setPos(player.getX(), player.getY() + 0.2, player.getZ());
        }
    }
}
