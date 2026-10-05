package com.brasshaven.item;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Sword with a forward dash: crosses ravines, closes gaps, escapes fights. */
public class CartographerBladeItem extends AbilityItem {
    public CartographerBladeItem(Properties properties) {
        super(properties, 50, 1);
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        dash(player);
        player.hurtMarked = true;
        level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 0.5, player.getZ(), 15, 0.3, 0.2, 0.3, 0.02);
        level.playSound(null, player, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.0F, 1.4F);
        return true;
    }

    @Override
    protected void activateClient(Player player, ItemStack stack) {
        dash(player);
    }

    private static void dash(Player player) {
        Vec3 look = player.getLookAngle();
        Vec3 flat = new Vec3(look.x, 0, look.z).normalize();
        player.setDeltaMovement(flat.x * 1.7, 0.35 + Math.max(0, look.y) * 0.5, flat.z * 1.7);
        player.resetFallDistance();
    }
}
