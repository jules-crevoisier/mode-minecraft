package com.wayfarers.entity;

import com.wayfarers.registry.ModEntities;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/** End mini-boss guarding its nest: blinks around, levitates its foes, calls Void Stalkers. */
public class VoidWarden extends BossZombie {
    public VoidWarden(EntityType<? extends Zombie> type, Level level) {
        super(type, level, BossEvent.BossBarColor.PURPLE);
    }

    public static AttributeSupplier.Builder attributes() {
        return Zombie.createAttributes()
                .add(Attributes.SPAWN_REINFORCEMENTS_CHANCE, 0.0)
                .add(Attributes.MAX_HEALTH, 220.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.SCALE, 1.7);
    }

    @Override
    protected void bossTick(ServerLevel level, int phase) {
        LivingEntity target = getTarget();
        if (target != null && tickCount % (phase == 3 ? 50 : 100) == 0) {
            double angle = random.nextDouble() * Math.PI * 2;
            level.sendParticles(ParticleTypes.PORTAL, getX(), getY() + 1, getZ(), 50, 0.5, 1.0, 0.5, 0.3);
            randomTeleport(target.getX() + Math.cos(angle) * 4, target.getY(), target.getZ() + Math.sin(angle) * 4, true);
        }
        if (tickCount % 200 == 0) {
            for (Player player : nearbyPlayers(level, 12.0)) {
                player.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 50, 0));
            }
            level.playSound(null, this, SoundEvents.ILLUSIONER_CAST_SPELL, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
        if (phase >= 2 && tickCount % 400 == 0) {
            for (int i = 0; i < phase; i++) {
                VoidStalker stalker = ModEntities.VOID_STALKER.get().create(level, EntitySpawnReason.MOB_SUMMONED);
                if (stalker != null) {
                    stalker.snapTo(getX() + random.nextInt(5) - 2, getY(), getZ() + random.nextInt(5) - 2, getYRot(), 0);
                    stalker.setTarget(target);
                    level.addFreshEntity(stalker);
                }
            }
        }
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.WITCH, getX(), getY() + 1.5, getZ(), 2, 0.5, 1.0, 0.5, 0.01);
        }
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 200, 2.0, 2.0, 2.0, 0.2);
    }
}
