package com.wayfarers.item;

import com.wayfarers.util.Targets;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Slams the ground: damages and hurls back every hostile creature around (never other players). */
public class TelluricHammerItem extends AbilityItem {
    public TelluricHammerItem(Properties properties) {
        super(properties, 70, 2);
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        double radius = 5.5;
        for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
                e -> Targets.foe(player, e))) {
            Vec3 push = target.position().subtract(player.position()).normalize().scale(1.4);
            target.hurtServer(level, level.damageSources().playerAttack(player), 7.0F);
            target.push(push.x, 0.55, push.z);
            target.hurtMarked = true;
        }
        BlockParticleOption dust = new BlockParticleOption(ParticleTypes.BLOCK, level.getBlockState(player.blockPosition().below()));
        for (int ring = 1; ring <= 5; ring++) {
            for (int a = 0; a < 360; a += 20) {
                double x = player.getX() + Math.cos(Math.toRadians(a)) * ring;
                double z = player.getZ() + Math.sin(Math.toRadians(a)) * ring;
                level.sendParticles(dust, x, player.getY() + 0.1, z, 2, 0.1, 0.1, 0.1, 0.1);
            }
        }
        level.sendParticles(ParticleTypes.EXPLOSION, player.getX(), player.getY(), player.getZ(), 1, 0, 0, 0, 0);
        level.playSound(null, player, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.8F, 0.7F);
        return true;
    }
}
