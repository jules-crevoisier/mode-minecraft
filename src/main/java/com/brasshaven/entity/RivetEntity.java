package com.brasshaven.entity;

import com.brasshaven.registry.ModEntities;
import com.brasshaven.registry.ModItems;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** A hot rivet fired by the Rivet Gun: fast, nearly flat, hits once. Never hits its shooter or the shooter's pets. */
public class RivetEntity extends ThrowableItemProjectile {
    public static final float DAMAGE = 5.0F;
    private static final int MAX_AGE = 60;
    private int age;

    public RivetEntity(EntityType<? extends RivetEntity> type, Level level) {
        super(type, level);
    }

    public RivetEntity(Level level, LivingEntity owner) {
        super(ModEntities.RIVET.get(), owner, level, new ItemStack(ModItems.RIVET.get()));
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.RIVET.get();
    }

    @Override
    protected double getDefaultGravity() {
        return 0.01;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            if (!isRemoved() && tickCount > 1) {
                level().addParticle(ParticleTypes.SMOKE, getX(), getY(), getZ(), 0.0, 0.0, 0.0);
            }
        } else if (++age > MAX_AGE) {
            discard();
        }
    }

    @Override
    protected boolean canHitEntity(Entity entity) {
        Entity owner = getOwner();
        if (entity == owner || (entity instanceof OwnableEntity pet && owner != null && pet.getOwner() == owner)) {
            return false;
        }
        return super.canHitEntity(entity);
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        Entity target = hit.getEntity();
        if (target.hurtServer(level, damageSources().thrown(this, getOwner()), DAMAGE) && target instanceof LivingEntity living) {
            Vec3 push = getDeltaMovement().multiply(1.0, 0.0, 1.0).normalize().scale(0.25);
            living.push(push.x, 0.05, push.z);
        }
        level.playSound(null, getX(), getY(), getZ(), SoundEvents.TRIDENT_HIT, SoundSource.PLAYERS, 0.6F, 1.6F);
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, level.getBlockState(hit.getBlockPos())),
                    getX(), getY(), getZ(), 6, 0.05, 0.05, 0.05, 0.08);
            level.sendParticles(ParticleTypes.CRIT, getX(), getY(), getZ(), 4, 0.05, 0.05, 0.05, 0.15);
            level.playSound(null, getX(), getY(), getZ(), SoundEvents.CHAIN_HIT, SoundSource.PLAYERS, 0.7F, 1.7F);
        }
    }

    @Override
    protected void onHit(HitResult hit) {
        super.onHit(hit);
        if (!level().isClientSide()) {
            discard();
        }
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }
}
