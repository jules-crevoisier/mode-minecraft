package com.wayfarers.entity;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.Level;

/** Hunter of the outer End islands: blinks next to its prey whenever it gets away. */
public class VoidStalker extends WayfarerZombie {
    public VoidStalker(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Zombie.createAttributes()
                .add(Attributes.SPAWN_REINFORCEMENTS_CHANCE, 0.0)
                .add(Attributes.MAX_HEALTH, 36.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.SCALE, 1.25);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        LivingEntity target = getTarget();
        if (target != null && tickCount % 60 == 0 && distanceToSqr(target) > 36) {
            double angle = random.nextDouble() * Math.PI * 2;
            double x = target.getX() + Math.cos(angle) * 2.5;
            double z = target.getZ() + Math.sin(angle) * 2.5;
            level.sendParticles(ParticleTypes.PORTAL, getX(), getY() + 1, getZ(), 30, 0.3, 0.8, 0.3, 0.2);
            if (randomTeleport(x, target.getY(), z, true)) {
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1, getZ(), 30, 0.3, 0.8, 0.3, 0.1);
            }
        }
    }
}
