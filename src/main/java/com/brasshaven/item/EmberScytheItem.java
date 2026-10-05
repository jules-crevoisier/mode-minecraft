package com.brasshaven.item;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Sets enemies on fire; in the Nether every hit also heals the wielder. */
public class EmberScytheItem extends TooltipItem {
    public EmberScytheItem(Properties properties) {
        super(properties);
    }

    @Override
    public void hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        super.hurtEnemy(stack, target, attacker);
        target.igniteForSeconds(5.0F);
        if (attacker.level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.FLAME, target.getX(), target.getY() + 1, target.getZ(), 12, 0.3, 0.5, 0.3, 0.03);
            if (level.dimension() == Level.NETHER) {
                attacker.heal(2.0F);
                level.sendParticles(ParticleTypes.HEART, attacker.getX(), attacker.getY() + 2, attacker.getZ(), 1, 0, 0, 0, 0);
            }
        }
    }
}
