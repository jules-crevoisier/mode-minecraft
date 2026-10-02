package com.wayfarers.entity;

import com.wayfarers.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Boss of the Sunken Citadel.
 * Phase 1: calls drowned minions. Phase 2: tidal slams. Phase 3: enraged, drags players into a whirlpool.
 */
public class DrownedWarden extends BossZombie {
    public DrownedWarden(EntityType<? extends Zombie> type, Level level) {
        super(type, level, BossEvent.BossBarColor.BLUE);
    }

    public static AttributeSupplier.Builder attributes() {
        return Zombie.createAttributes()
                .add(Attributes.SPAWN_REINFORCEMENTS_CHANCE, 0.0)
                .add(Attributes.MAX_HEALTH, 320.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.SCALE, 2.2);
    }

    @Override
    protected void bossTick(ServerLevel level, int phase) {
        if (tickCount % 300 == 0) {
            summonMinions(level, phase == 3 ? 3 : 2);
        }
        if (phase >= 2 && tickCount % 140 == 0) {
            tidalSlam(level);
        }
        if (phase == 3 && tickCount % 90 == 0) {
            whirlpool(level);
        }
        if (tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.BUBBLE_POP, getX(), getY() + 2, getZ(), 6, 0.6, 1.2, 0.6, 0.02);
        }
    }

    @Override
    protected void onPhaseChange(ServerLevel level, int phase) {
        level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 0.8F);
        if (phase == 3) {
            addEffect(new MobEffectInstance(MobEffects.SPEED, 20 * 600, 1));
            addEffect(new MobEffectInstance(MobEffects.STRENGTH, 20 * 600, 0));
        }
    }

    private void summonMinions(ServerLevel level, int count) {
        for (int i = 0; i < count; i++) {
            Mob minion = EntityTypes.DROWNED.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (minion == null) {
                continue;
            }
            double angle = random.nextDouble() * Math.PI * 2;
            minion.snapTo(getX() + Math.cos(angle) * 3, getY(), getZ() + Math.sin(angle) * 3, getYRot(), 0);
            minion.setTarget(getTarget());
            level.addFreshEntity(minion);
            level.sendParticles(ParticleTypes.SPLASH, minion.getX(), minion.getY() + 1, minion.getZ(), 30, 0.4, 0.6, 0.4, 0.1);
        }
    }

    private void tidalSlam(ServerLevel level) {
        for (Player player : nearbyPlayers(level, 8.0)) {
            Vec3 push = player.position().subtract(position()).normalize().scale(1.6);
            player.hurtServer(level, damageSources().mobAttack(this), 7.0F);
            player.push(push.x, 0.6, push.z);
            player.hurtMarked = true;
            player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1));
        }
        for (int a = 0; a < 360; a += 15) {
            level.sendParticles(ParticleTypes.SPLASH, getX() + Math.cos(Math.toRadians(a)) * 4, getY() + 0.2,
                    getZ() + Math.sin(Math.toRadians(a)) * 4, 6, 0.2, 0.1, 0.2, 0.2);
        }
        level.playSound(null, this, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    private void whirlpool(ServerLevel level) {
        for (Player player : nearbyPlayers(level, 16.0)) {
            Vec3 pull = position().subtract(player.position()).normalize().scale(0.9);
            player.push(pull.x, 0.1, pull.z);
            player.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.NAUTILUS, getX(), getY() + 1, getZ(), 80, 4.0, 1.0, 4.0, 0.5);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
    }
}
