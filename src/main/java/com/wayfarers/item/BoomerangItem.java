package com.wayfarers.item;

import com.wayfarers.entity.BoomerangEntity;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

public class BoomerangItem extends TooltipItem {
    public BoomerangItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide()) {
            BoomerangEntity boomerang = new BoomerangEntity(level, player, stack.copyWithCount(1));
            boomerang.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 1.6F, 0.5F);
            level.addFreshEntity(boomerang);
            level.playSound(null, player, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.8F, 1.8F);
            stack.shrink(1);
        }
        return InteractionResult.SUCCESS;
    }
}
