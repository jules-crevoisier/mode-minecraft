package com.wayfarers.entity.ocean;

import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
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
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Baleine à bosse (Humpback Whale): rare and peaceful, in the deep oceans only. Ten blocks long, it cruises slowly,
 * rises every two minutes or so to blow (a spout of spray at the surface) and sings: long, low calls heard from far
 * away. Hurt, it just swims off faster.
 */
public class Whale extends WaterAnimal implements AnimatedMob {
    public static final float WIDTH = 3.2F;
    public static final float HEIGHT = 2.4F;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int breathTimer;
    private int songCooldown;

    public Whale(EntityType<? extends WaterAnimal> type, Level level) {
        super(type, level);
        this.moveControl = new SmoothSwimmingMoveControl<>(this, 10, 3, 0.02F, 0.1F, true);
        this.lookControl = new SmoothSwimmingLookControl(this, 4);
        this.breathTimer = 1200 + random.nextInt(1800);
        this.songCooldown = 200 + random.nextInt(600);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 120.0).add(Attributes.MOVEMENT_SPEED, 0.55)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
    }

    /** Deep water only: at least 8 blocks below sea level, with water above and below. */
    public static boolean checkSpawnRules(EntityType<? extends Whale> type, LevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        int sea = level.getSeaLevel();
        return pos.getY() <= sea - 8 && pos.getY() >= sea - 30 && level.getFluidState(pos).is(FluidTags.WATER)
                && level.getFluidState(pos.below(2)).is(FluidTags.WATER) && level.getFluidState(pos.above(3)).is(FluidTags.WATER);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new TryFindWaterGoal(this));
        goalSelector.addGoal(1, new PanicGoal(this, 1.5));
        goalSelector.addGoal(2, new SurfaceGoal(this));
        goalSelector.addGoal(5, new RandomSwimmingGoal(this, 0.8, 60));
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
    public boolean isPushable() {
        return false;
    }

    @Override
    public AABB cullingBox(AABB hitbox) {
        return hitbox.inflate(5.0, 1.5, 5.0);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        if (breathTimer > 0) {
            breathTimer--;
        }
        if (--songCooldown <= 0 && isInWater()) {
            songCooldown = 900 + random.nextInt(1500);
            AnimatedMob.playAction(this, MobAnims.Whale.SING);
            // a long low call, heard from far away
            float pitch = 0.5F + random.nextFloat() * 0.15F;
            level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_AMBIENT, SoundSource.NEUTRAL, 4.0F, pitch * 0.6F);
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_DIDGERIDOO.value(), SoundSource.NEUTRAL, 3.0F, pitch);
            level.sendParticles(ParticleTypes.NOTE, getX(), getY() + 2.5, getZ(), 3, 1.5, 0.5, 1.5, 0.6);
        }
    }

    // ------------------------------------------------------------------ sounds

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
        return SoundEvents.ELDER_GUARDIAN_DEATH;
    }

    @Override
    protected SoundEvent getSwimSound() {
        return SoundEvents.DOLPHIN_SWIM;
    }

    @Override
    public float getVoicePitch() {
        return 0.4F;
    }

    @Override
    protected float getSoundVolume() {
        return 2.0F;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Whale.TICKS;
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

    /** Every couple of minutes: rise to the surface and blow a spout of spray. */
    static final class SurfaceGoal extends Goal {
        private final Whale whale;
        private int tick;
        private boolean blown;

        SurfaceGoal(Whale whale) {
            this.whale = whale;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return whale.breathTimer <= 0 && whale.isInWater();
        }

        @Override
        public boolean canContinueToUse() {
            return tick < 300 && !(blown && tick > 60);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void start() {
            tick = 0;
            blown = false;
        }

        @Override
        public void tick() {
            tick++;
            if (!(whale.level() instanceof ServerLevel level)) {
                return;
            }
            BlockPos top = whale.blockPosition();
            int depth = 0;
            while (depth < 40 && whale.level().getFluidState(top.above()).is(FluidTags.WATER)) {
                top = top.above();
                depth++;
            }
            double headY = whale.getY() + whale.getBbHeight();
            if (!blown && headY >= top.getY() - 0.2) {
                blown = true;
                tick = 1;
                AnimatedMob.playAction(whale, MobAnims.Whale.SPOUT);
                level.playSound(null, whale, SoundEvents.GENERIC_SPLASH, SoundSource.NEUTRAL, 2.0F, 0.5F);
                level.playSound(null, whale, SoundEvents.BUBBLE_COLUMN_UPWARDS_INSIDE, SoundSource.NEUTRAL, 2.0F, 0.6F);
            }
            if (blown) {
                whale.setDeltaMovement(whale.getDeltaMovement().multiply(0.8, 0.5, 0.8));
                if (tick < 30 && tick % 2 == 0) {
                    float yaw = whale.yBodyRot * Mth.DEG_TO_RAD;
                    double bx = whale.getX() - Mth.sin(yaw) * 1.2;
                    double bz = whale.getZ() + Mth.cos(yaw) * 1.2;
                    for (int i = 0; i < 6; i++) {
                        level.sendParticles(ParticleTypes.SPLASH, bx, top.getY() + 1.0 + i * 0.5, bz, 6, 0.25, 0.25, 0.25, 0.05);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, bx, top.getY() + 3.5, bz, 2, 0.4, 0.3, 0.4, 0.02);
                }
            } else {
                whale.getNavigation().stop();
                whale.setDeltaMovement(whale.getDeltaMovement().add(0, 0.012, 0));
            }
        }

        @Override
        public void stop() {
            whale.breathTimer = 1800 + whale.random.nextInt(1800);
        }
    }
}
