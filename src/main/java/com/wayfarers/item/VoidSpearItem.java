package com.wayfarers.item;

import com.wayfarers.util.Targets;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Comparator;
import java.util.Optional;

/** Blinks behind the creature the player is looking at and strikes it in the back. */
public class VoidSpearItem extends AbilityItem {
    private static final double RANGE = 24.0;

    public VoidSpearItem(Properties properties) {
        super(properties, 60, 1);
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        Vec3 eye = player.getEyePosition();
        // stop at the first wall: no striking (or blinking) through blocks
        HitResult wall = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(RANGE)),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
        Vec3 end = wall.getType() == HitResult.Type.MISS ? eye.add(player.getLookAngle().scale(RANGE)) : wall.getLocation();
        AABB sweep = new AABB(eye, end).inflate(1.0);
        Optional<LivingEntity> target = level.getEntitiesOfClass(LivingEntity.class, sweep,
                        e -> Targets.foe(player, e)
                                && e.getBoundingBox().inflate(0.3).clip(eye, end).isPresent())
                .stream()
                .min(Comparator.comparingDouble(e -> e.distanceToSqr(player)));
        if (target.isEmpty()) {
            noTarget(player);
            return false;
        }
        LivingEntity t = target.get();
        Vec3 behind = t.position().add(t.getLookAngle().multiply(1, 0, 1).normalize().scale(-1.6));
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, player.getX(), player.getY() + 1, player.getZ(), 30, 0.3, 0.6, 0.3, 0.05);
        Vec3 dest = new Vec3(behind.x, t.getY(), behind.z);
        if (level.noCollision(player, player.getBoundingBox().move(dest.subtract(player.position())))) {
            player.teleportTo(dest.x, dest.y, dest.z);
        }
        player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, t.getEyePosition());
        t.hurtServer(level, level.damageSources().playerAttack(player), 9.0F);
        level.sendParticles(ParticleTypes.PORTAL, t.getX(), t.getY() + 1, t.getZ(), 40, 0.4, 0.6, 0.4, 0.2);
        level.playSound(null, player, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 1.0F, 1.3F);
        return true;
    }
}
