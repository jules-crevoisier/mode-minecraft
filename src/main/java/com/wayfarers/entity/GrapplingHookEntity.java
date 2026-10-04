package com.wayfarers.entity;

import com.wayfarers.event.GadgetEvents;
import com.wayfarers.item.GrapplingHookItem;
import com.wayfarers.registry.ModEntities;
import com.wayfarers.registry.ModItems;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * The claw of the Grappling Hook. It flies straight up to {@link #RANGE} blocks; when it bites a block it stays
 * there and its owner is reeled in.
 *
 * <p>Player movement is client-authoritative, so the pull is applied by the owner's own client (this entity also
 * ticks there, with its owner known from the spawn packet), which keeps it smooth in multiplayer. The server only
 * decides when the pull ends (arrival, sneak, re-use, timeout, hook item put away) and cancels fall damage.
 */
public class GrapplingHookEntity extends ThrowableItemProjectile {
    public static final double RANGE = 32.0;
    private static final EntityDataAccessor<Boolean> DATA_ANCHORED = SynchedEntityData.defineId(GrapplingHookEntity.class,
            EntityDataSerializers.BOOLEAN);
    private static final double SPEED = 2.6;
    private static final int MAX_FLIGHT_TICKS = (int) Math.ceil(RANGE / SPEED) + 1;
    private static final int MAX_PULL_TICKS = 60;
    /** The owner's client gives the final hop below this distance; the server, a little later, frees the claw. */
    private static final double ARRIVED = 2.2;

    private int flightTicks;
    private int pullTicks;
    /** Client only: the local owner reached the claw and got the final hop. */
    private boolean arrived;

    public GrapplingHookEntity(EntityType<? extends GrapplingHookEntity> type, Level level) {
        super(type, level);
        setItem(clawStack());
    }

    public GrapplingHookEntity(Level level, LivingEntity owner) {
        super(ModEntities.GRAPPLING_HOOK.get(), owner, level, clawStack());
    }

    /** The hook item tagged "claw": its item model then shows only the claw (see tools/wf/gadgets.py). */
    public static ItemStack clawStack() {
        ItemStack stack = new ItemStack(ModItems.GRAPPLING_HOOK.get());
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of("claw"), List.of()));
        return stack;
    }

    public void launch(Player owner) {
        shootFromRotation(owner, owner.getXRot(), owner.getYRot(), 0.0F, (float) SPEED, 0.0F);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.GRAPPLING_HOOK.get();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ANCHORED, false);
    }

    public boolean isAnchored() {
        return getEntityData().get(DATA_ANCHORED);
    }

    @Override
    protected double getDefaultGravity() {
        return 0.0;
    }

    @Override
    protected boolean canHitEntity(Entity entity) {
        return false;
    }

    public @Nullable Player playerOwner() {
        return getOwner() instanceof Player player ? player : null;
    }

    @Override
    public void tick() {
        if (!isAnchored()) {
            super.tick();
            if (level() instanceof ServerLevel && !isRemoved() && !isAnchored()) {
                flightTicks++;
                Player owner = playerOwner();
                if (owner == null || !owner.isAlive() || flightTicks > MAX_FLIGHT_TICKS
                        || distanceToSqr(owner) > (RANGE + 2) * (RANGE + 2)) {
                    release(true);
                }
            }
            return;
        }
        setDeltaMovement(Vec3.ZERO);
        Player owner = playerOwner();
        if (level().isClientSide()) {
            if (owner != null && owner.isLocalPlayer()) {
                pullClient(owner);
            }
            return;
        }
        if (owner == null) {
            discard();
            return;
        }
        pullTicks++;
        Vec3 to = position().subtract(owner.getX(), owner.getY() + owner.getBbHeight() * 0.5, owner.getZ());
        if (!owner.isAlive() || owner.level() != level() || owner.isShiftKeyDown() || !GrapplingHookItem.isHolding(owner)
                || pullTicks > MAX_PULL_TICKS || to.length() > RANGE + 8 || to.length() < ARRIVED + 0.2) {
            release(false);
            return;
        }
        // no fall damage while reeled in, nor for the arc right after it
        owner.resetFallDistance();
        GadgetEvents.softLanding(owner, 60);
    }

    /** Reels the local owner towards the claw; a small hop at the end helps to climb onto ledges. */
    private void pullClient(Player owner) {
        if (arrived || owner.isShiftKeyDown()) {
            return;
        }
        Vec3 to = position().subtract(owner.getX(), owner.getY() + owner.getBbHeight() * 0.5, owner.getZ());
        double dist = to.length();
        if (dist < ARRIVED) {
            arrived = true;
            Vec3 v = owner.getDeltaMovement();
            owner.setDeltaMovement(v.x * 0.5, Math.max(v.y, 0.62), v.z * 0.5);
            return;
        }
        double speed = Mth.clamp(dist * 0.22, 0.5, 1.25);
        Vec3 target = to.scale(speed / dist);
        owner.setDeltaMovement(owner.getDeltaMovement().lerp(target, 0.45));
        owner.resetFallDistance();
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        if (!(level() instanceof ServerLevel level) || isAnchored()) {
            return;
        }
        setPos(hit.getLocation());
        setDeltaMovement(Vec3.ZERO);
        getEntityData().set(DATA_ANCHORED, true);
        level.playSound(null, getX(), getY(), getZ(), SoundEvents.CHAIN_HIT, SoundSource.PLAYERS, 1.0F, 0.8F);
        level.playSound(null, getX(), getY(), getZ(), SoundEvents.TRIDENT_HIT_GROUND, SoundSource.PLAYERS, 0.7F, 1.3F);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, level.getBlockState(hit.getBlockPos())),
                getX(), getY(), getZ(), 10, 0.15, 0.15, 0.15, 0.1);
        Player owner = playerOwner();
        if (owner != null) {
            level.playSound(null, owner.getX(), owner.getY(), owner.getZ(), SoundEvents.CROSSBOW_LOADING_END.value(),
                    SoundSource.PLAYERS, 0.8F, 0.7F);
        }
    }

    /** Ends the hook: winds the chain back and starts the item cooldown. */
    public void release(boolean missed) {
        if (!(level() instanceof ServerLevel level) || isRemoved()) {
            return;
        }
        Player owner = playerOwner();
        if (owner != null) {
            level.playSound(null, owner.getX(), owner.getY(), owner.getZ(), SoundEvents.FISHING_BOBBER_RETRIEVE,
                    SoundSource.PLAYERS, 0.8F, missed ? 0.7F : 1.0F);
            owner.getCooldowns().addCooldown(new ItemStack(ModItems.GRAPPLING_HOOK.get()), missed ? 10 : 20);
        }
        discard();
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    /** The hook a player currently has out in this level, if any. */
    public static @Nullable GrapplingHookEntity find(ServerLevel level, Player player) {
        List<GrapplingHookEntity> hooks = level.getEntitiesOfClass(GrapplingHookEntity.class,
                player.getBoundingBox().inflate(RANGE + 16), hook -> hook.getOwner() == player && !hook.isRemoved());
        return hooks.isEmpty() ? null : hooks.get(0);
    }
}
