package com.wayfarers.entity;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.Level;

/** Fast paper ghost haunting libraries and outposts; its touch blinds and confuses. Burns in daylight. */
public class MapWraith extends WayfarerZombie {
    public MapWraith(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Zombie.createAttributes()
                .add(Attributes.SPAWN_REINFORCEMENTS_CHANCE, 0.0)
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.33)
                .add(Attributes.SCALE, 0.8);
    }

    @Override
    protected boolean isSunSensitive() {
        return true;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0), this);
            living.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 80, 0), this);
        }
        return hit;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level() instanceof ServerLevel level && tickCount % 10 == 0) {
            level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1, getZ(), 3, 0.3, 0.5, 0.3, 0.0);
        }
    }
}
