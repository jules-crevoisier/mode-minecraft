package com.brasshaven.item;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** A burst of dawn light: repels and reveals monsters, heals friends nearby. Great in caves. */
public class LightStaffItem extends AbilityItem {
    public LightStaffItem(Properties properties) {
        super(properties, 100, 1);
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(9.0), LivingEntity::isAlive)) {
            if (e instanceof Player friend) {
                friend.heal(4.0F);
                friend.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 80, 0));
            } else if (e instanceof Enemy) {
                Vec3 push = e.position().subtract(player.position()).normalize().scale(1.8);
                e.push(push.x, 0.4, push.z);
                e.hurtMarked = true;
                e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 300, 0));
                e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 200, 1));
            }
        }
        level.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY() + 1, player.getZ(), 120, 3.0, 1.5, 3.0, 0.08);
        level.playSound(null, player, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.0F, 1.5F);
        return true;
    }
}
