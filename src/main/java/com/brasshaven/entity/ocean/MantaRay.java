package com.brasshaven.entity.ocean;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.TryFindWaterGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.animal.fish.WaterAnimal;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Raie manta (Manta Ray): a peaceful giant (3.5 blocks from wing tip to wing tip) of warm and temperate seas. It
 * glides in wide, slow curves with its wings beating in a travelling wave, and every now and then, close to the
 * surface, it breaches: bursts out of the water nose first and belly-flops back in a splash.
 */
public class MantaRay extends WaterAnimal implements AnimatedMob {
    public static final float WIDTH = 2.2F;
    public static final float HEIGHT = 0.6F;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int breachCooldown = 600;

    public MantaRay(EntityType<? extends WaterAnimal> type, Level level) {
        super(type, level);
        this.moveControl = new SmoothSwimmingMoveControl<>(this, 20, 6, 0.02F, 0.1F, true);
        this.lookControl = new SmoothSwimmingLookControl(this, 6);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 30.0).add(Attributes.MOVEMENT_SPEED, 0.9);
    }

    /** Near the surface (down to 20 blocks below sea level), with water above and below. */
    public static boolean checkSpawnRules(EntityType<? extends MantaRay> type, LevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        int sea = level.getSeaLevel();
        return pos.getY() <= sea - 2 && pos.getY() >= sea - 20 && level.getFluidState(pos).is(FluidTags.WATER)
                && level.getFluidState(pos.below()).is(FluidTags.WATER) && level.getFluidState(pos.above()).is(FluidTags.WATER);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new TryFindWaterGoal(this));
        goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        goalSelector.addGoal(2, new BreachGoal(this));
        goalSelector.addGoal(4, new RandomSwimmingGoal(this, 1.0, 30));
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WaterBoundPathNavigation(this, level);
    }

    @Override
    protected void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
        moveRelative(getSpeed(), input);
        move(MoverType.SELF, getDeltaMovement());
        setDeltaMovement(getDeltaMovement().scale(0.9));
    }

    @Override
    public int getMaxHeadXRot() {
        return 1;
    }

    @Override
    public int getMaxHeadYRot() {
        return 1;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (breachCooldown > 0) {
            breachCooldown--;
        }
    }

    // ------------------------------------------------------------------ sounds: almost silent, a soft swish

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.DOLPHIN_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.DOLPHIN_DEATH;
    }

    @Override
    protected SoundEvent getSwimSound() {
        return SoundEvents.DOLPHIN_SWIM;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.6F;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MantaRay.TICKS;
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (!handleActionEvent(this, id)) {
            super.handleEntityEvent(id);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            tickActionStates(this);
        }
    }

    @Override
    public net.minecraft.world.phys.AABB cullingBox(net.minecraft.world.phys.AABB hitbox) {
        return hitbox.inflate(1.0, 0.5, 1.0);
    }

    /** Close under the surface, now and then: a leap out of the water and a big splash on the way back. */
    static final class BreachGoal extends Goal {
        private final MantaRay manta;
        private int tick;

        BreachGoal(MantaRay manta) {
            this.manta = manta;
            setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (manta.breachCooldown > 0 || !manta.isInWater() || manta.random.nextInt(40) != 0) {
                return false;
            }
            BlockPos pos = manta.blockPosition();
            // 1 to 4 blocks below the surface, deep water below
            for (int up = 1; up <= 4; up++) {
                if (manta.level().getBlockState(pos.above(up)).isAir()) {
                    return manta.level().getFluidState(pos.below(3)).is(FluidTags.WATER);
                }
                if (!manta.level().getFluidState(pos.above(up)).is(FluidTags.WATER)) {
                    return false;
                }
            }
            return false;
        }

        @Override
        public boolean canContinueToUse() {
            return tick < MobAnims.MantaRay.TICKS[MobAnims.MantaRay.BREACH];
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void start() {
            tick = 0;
            manta.getNavigation().stop();
            AnimatedMob.playAction(manta, MobAnims.MantaRay.BREACH);
            float yaw = manta.getYRot() * Mth.DEG_TO_RAD;
            manta.setDeltaMovement(-Mth.sin(yaw) * 0.45, 1.05, Mth.cos(yaw) * 0.45);
        }

        @Override
        public void tick() {
            tick++;
            if (!(manta.level() instanceof ServerLevel level)) {
                return;
            }
            if (tick == 4 || tick == 22 && manta.isInWater()) {
                level.sendParticles(ParticleTypes.SPLASH, manta.getX(), manta.getY() + 0.3, manta.getZ(), 40, 1.2, 0.2, 1.2, 0.3);
                level.sendParticles(ParticleTypes.BUBBLE, manta.getX(), manta.getY(), manta.getZ(), 20, 1.0, 0.3, 1.0, 0.1);
                level.playSound(null, manta, tick == 4 ? SoundEvents.DOLPHIN_JUMP : SoundEvents.GENERIC_SPLASH,
                        SoundSource.NEUTRAL, 1.2F, 0.6F);
            }
        }

        @Override
        public void stop() {
            manta.breachCooldown = 900 + manta.random.nextInt(1200);
        }
    }
}
