package com.brasshaven.item;

import com.brasshaven.registry.ModDataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

/** Slows on every hit; the third consecutive hit freezes the target solid. */
public class FrostBladeItem extends TooltipItem {
    public FrostBladeItem(Properties properties) {
        super(properties);
    }

    @Override
    public void hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        super.hurtEnemy(stack, target, attacker);
        target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
        int hits = stack.getOrDefault(ModDataComponents.FROST_HITS.get(), 0) + 1;
        if (hits >= 3) {
            hits = 0;
            target.setTicksFrozen(target.getTicksRequiredToFreeze() + 160);
            target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 4));
            if (attacker.level() instanceof ServerLevel level) {
                level.sendParticles(ParticleTypes.SNOWFLAKE, target.getX(), target.getY() + 1, target.getZ(), 30, 0.4, 0.6, 0.4, 0.05);
                level.playSound(null, target, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 0.8F, 1.6F);
            }
        }
        stack.set(ModDataComponents.FROST_HITS.get(), hits);
    }
}
