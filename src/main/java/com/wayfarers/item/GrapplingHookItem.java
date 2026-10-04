package com.wayfarers.item;

import com.wayfarers.entity.GrapplingHookEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Grappling Hook: use to fire the claw up to 32 blocks; once it bites a block you are reeled in. Sneak or use
 * again to let go. No fall damage while reeled in. The cooldown starts when the chain comes back.
 */
public class GrapplingHookItem extends GadgetItem {
    public GrapplingHookItem(Properties properties) {
        super(properties);
    }

    public static boolean isHolding(Player player) {
        return player.getMainHandItem().getItem() instanceof GrapplingHookItem
                || player.getOffhandItem().getItem() instanceof GrapplingHookItem;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        GrapplingHookEntity out = GrapplingHookEntity.find(server, player);
        if (out != null) {
            out.release(false);
            return InteractionResult.SUCCESS;
        }
        GrapplingHookEntity hook = new GrapplingHookEntity(level, player);
        hook.launch(player);
        level.addFreshEntity(hook);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.CROSSBOW_SHOOT, SoundSource.PLAYERS,
                1.0F, 0.6F);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FISHING_BOBBER_THROW, SoundSource.PLAYERS,
                0.6F, 0.5F);
        stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
        return InteractionResult.SUCCESS;
    }
}
