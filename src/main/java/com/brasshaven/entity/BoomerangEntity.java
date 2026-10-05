package com.brasshaven.entity;

import com.brasshaven.registry.ModEntities;
import com.brasshaven.registry.ModItems;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;

/** Flies straight, hits once, then homes back to its thrower and returns to their inventory. */
public class BoomerangEntity extends ThrowableItemProjectile {
    private static final int OUTBOUND_TICKS = 14;
    private int flightTicks;
    private boolean returning;

    public BoomerangEntity(EntityType<? extends BoomerangEntity> type, Level level) {
        super(type, level);
    }

    public BoomerangEntity(Level level, LivingEntity owner, ItemStack stack) {
        super(ModEntities.BOOMERANG.get(), owner, level, stack);
        setOwner(owner);
        setItem(stack);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.BOOMERANG.get();
    }

    @Override
    protected double getDefaultGravity() {
        return 0.0;
    }

    @Override
    public void tick() {
        super.tick();
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        flightTicks++;
        if (flightTicks > OUTBOUND_TICKS) {
            returning = true;
        }
        Entity owner = getOwner();
        if (flightTicks > 400 || owner == null || !owner.isAlive() || owner.level() != level) {
            dropSelf(level);
            return;
        }
        if (returning) {
            noPhysics = true;
            Vec3 toOwner = owner.getEyePosition().subtract(position());
            if (toOwner.length() < 1.6) {
                giveBack(level, owner);
            } else {
                setDeltaMovement(toOwner.normalize().scale(1.1));
            }
        }
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        Entity target = hit.getEntity();
        if (returning || target == getOwner() || !(level() instanceof ServerLevel level)) {
            return;
        }
        target.hurtServer(level, damageSources().thrown(this, getOwner()), 6.0F);
        returning = true;
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        returning = true;
    }

    private void giveBack(ServerLevel level, Entity owner) {
        ItemStack stack = getItem().copy();
        if (!(owner instanceof Player player) || !player.getInventory().add(stack)) {
            owner.spawnAtLocation(level, stack);
        }
        discard();
    }

    private void dropSelf(ServerLevel level) {
        spawnAtLocation(level, getItem().copy());
        discard();
    }
}
