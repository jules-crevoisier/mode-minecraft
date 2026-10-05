package com.brasshaven.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * An item with a right-click ability: handles the cooldown, durability and the client/server
 * split so subclasses only implement {@link #activate}.
 */
public abstract class AbilityItem extends TooltipItem {
    private final int cooldownTicks;
    private final int durabilityCost;

    protected AbilityItem(Properties properties, int cooldownTicks, int durabilityCost) {
        super(properties);
        this.cooldownTicks = cooldownTicks;
        this.durabilityCost = durabilityCost;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getCooldowns().isOnCooldown(stack)) {
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel serverLevel) {
            if (!activate(serverLevel, player, stack)) {
                return InteractionResult.FAIL;
            }
            if (durabilityCost > 0 && stack.isDamageableItem()) {
                stack.hurtAndBreak(durabilityCost, player, hand.asEquipmentSlot());
            }
            // only the server starts the cooldown (it syncs to the client), so a refused ability shows none
            player.getCooldowns().addCooldown(stack, cooldownTicks);
        } else {
            activateClient(player, stack);
        }
        return InteractionResult.SUCCESS;
    }

    /** Server-side effect. Return false to cancel (no cooldown, no durability). */
    protected abstract boolean activate(ServerLevel level, Player player, ItemStack stack);

    /** Tells the player why the ability did nothing (shown above the hotbar). */
    protected static void noTarget(Player player) {
        if (player instanceof ServerPlayer sp) {
            sp.sendOverlayMessage(Component.translatable("message.brasshaven.ability.no_target").withStyle(ChatFormatting.GRAY));
        }
    }

    /** Optional client-side prediction (e.g. movement) so abilities feel instant. */
    protected void activateClient(Player player, ItemStack stack) {}
}
