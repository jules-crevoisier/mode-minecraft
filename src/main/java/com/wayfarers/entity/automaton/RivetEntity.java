package com.wayfarers.entity.automaton;

import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.registry.ModEntities;
import com.wayfarers.registry.ModItems;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * A hot rivet (drawn as a brass nugget) fired by Steam Drones, or a spinning brass cog (drawn as a brass gear)
 * thrown by the Grand Clockmaker. Flies almost straight (light gravity), hurts the first creature it hits, sparks
 * on impact and is gone. It never hurts its own side: automatons and bosses ignore each other's shots.
 */
public class RivetEntity extends ThrowableItemProjectile {
    private float damage = 4.0F;
    private int life;

    public RivetEntity(EntityType<? extends RivetEntity> type, Level level) {
        super(type, level);
    }

    /** A rivet (brass nugget) or a cog (brass gear) shot by {@code owner} for {@code damage}. */
    public RivetEntity(Level level, LivingEntity owner, boolean cog, float damage) {
        super(ModEntities.RIVET.get(), owner, level, new ItemStack(cog ? ModItems.BRASS_GEAR.get() : com.wayfarers.generated.GeneratedMetals.BRASS_NUGGET.get()));
        this.damage = damage;
    }

    @Override
    protected Item getDefaultItem() {
        return com.wayfarers.generated.GeneratedMetals.BRASS_NUGGET.get();
    }

    @Override
    protected double getDefaultGravity() {
        return 0.01;
    }

    @Override
    public void tick() {
        super.tick();
        if (level() instanceof ServerLevel level) {
            if (++life > 100) {
                discard();
                return;
            }
            if (life % 2 == 0) {
                level.sendParticles(ParticleTypes.SMOKE, getX(), getY(), getZ(), 1, 0, 0, 0, 0);
            }
        } else if (random.nextInt(3) == 0) {
            level().addParticle(ParticleTypes.ELECTRIC_SPARK, getX(), getY(), getZ(), 0, 0, 0);
        }
    }

    @Override
    protected boolean canHitEntity(Entity entity) {
        Entity owner = getOwner();
        if (owner != null && isSameSide(owner, entity)) {
            return false;
        }
        return super.canHitEntity(entity);
    }

    /** Automatons, their boss and its minions never shoot each other. */
    private static boolean isSameSide(Entity owner, Entity other) {
        boolean ownerHostile = owner instanceof Enemy || owner instanceof WayfarerBoss;
        boolean otherHostile = other instanceof Enemy || other instanceof WayfarerBoss;
        return ownerHostile && otherHostile;
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        if (level() instanceof ServerLevel level) {
            Entity target = hit.getEntity();
            target.hurtServer(level, damageSources().thrown(this, getOwner()), damage);
        }
    }

    @Override
    protected void onHit(HitResult hit) {
        super.onHit(hit);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY(), getZ(), 8, 0.15, 0.15, 0.15, 0.1);
            level.sendParticles(ParticleTypes.SMOKE, getX(), getY(), getZ(), 3, 0.1, 0.1, 0.1, 0.01);
            level.playSound(null, getX(), getY(), getZ(), SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 0.6F, 1.6F);
            discard();
        }
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putFloat("Damage", damage);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        damage = input.getFloatOr("Damage", 4.0F);
    }
}
