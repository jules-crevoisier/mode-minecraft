package com.wayfarers.entity;

import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.jetbrains.annotations.Nullable;

/**
 * Rôdeur des ruines (Ruin Walker): a moss-grown stone sentinel of the overworld ruins. Slow and tough; it
 * wakes with a shake when it spots prey ({@code awaken}), then pounds with a telegraphed two-handed slam
 * whose blows weaken. Model: tools/wf/mobs/ruin_walker.py.
 */
public class RuinWalker extends Monster implements AnimatedMob {
    /** Slam impact: 0.7 s into the animation (MobAnims.RuinWalker.SLAM). */
    private static final int SLAM_HIT = 14;
    /** Time it stands still while waking up (the awaken animation, 1.8 s). */
    private static final int AWAKEN_TICKS = 30;
    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int slamTicks;
    private int busyTicks;
    private int lastAwaken = -1000;
    private boolean hadTarget;

    public RuinWalker(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 36.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.21)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.5)
                .add(Attributes.FOLLOW_RANGE, 35.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new SlamGoal());
        goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractVillager.class, false));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, true));
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        LivingEntity target = getTarget();
        if (busyTicks > 0) {
            busyTicks--;
        }
        // a dormant sentinel shakes itself awake when it first spots prey
        if (target != null && !hadTarget && slamTicks == 0 && tickCount - lastAwaken > 200) {
            lastAwaken = tickCount;
            busyTicks = AWAKEN_TICKS;
            AnimatedMob.playAction(this, MobAnims.RuinWalker.AWAKEN);
            playSound(SoundEvents.GRINDSTONE_USE, 1.0F, 0.5F);
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, getBlockStateOn()),
                    getX(), getY() + 1.4, getZ(), 30, 0.5, 0.6, 0.5, 0.05);
        }
        hadTarget = target != null;
        if (slamTicks > 0 && --slamTicks == 0) {
            slamImpact(level);
        }
    }

    private void startSlam() {
        slamTicks = SLAM_HIT;
        AnimatedMob.playAction(this, MobAnims.RuinWalker.SLAM);
        playSound(SoundEvents.IRON_GOLEM_ATTACK, 1.0F, 0.6F);
    }

    /** Both fists hit the ground in front: the target is struck if it stayed in reach. */
    private void slamImpact(ServerLevel level) {
        double rad = Math.toRadians(getYRot());
        double fx = getX() - Math.sin(rad) * 1.2;
        double fz = getZ() + Math.cos(rad) * 1.2;
        BlockState ground = level.getBlockState(BlockPos.containing(fx, getY() - 0.5, fz));
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground.isAir() ? getBlockStateOn() : ground),
                fx, getY() + 0.1, fz, 40, 0.6, 0.1, 0.6, 0.15);
        playSound(SoundEvents.STONE_BREAK, 1.4F, 0.6F);
        LivingEntity target = getTarget();
        if (target != null && target.isAlive()
                && getBoundingBox().inflate(1.3, 0.5, 1.3).intersects(target.getBoundingBox())
                && getSensing().hasLineOfSight(target)) {
            swing(InteractionHand.MAIN_HAND);
            doHurtTarget(level, target);
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 0), this);
            living.push(0.0, 0.25, 0.0);
        }
        return hit;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.GRINDSTONE_USE;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 240;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.IRON_GOLEM_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.6F, 0.8F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.7F;
    }

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.RuinWalker.TICKS;
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

    /** Melee chase that winds up a slam instead of hitting instantly, and stands rooted while it does. */
    private final class SlamGoal extends MeleeAttackGoal {
        SlamGoal() {
            super(RuinWalker.this, 1.0, false);
        }

        @Override
        public void tick() {
            if (slamTicks > 0 || busyTicks > 0) {
                mob.getNavigation().stop();
                LivingEntity target = mob.getTarget();
                if (target != null) {
                    mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
                }
                return;
            }
            super.tick();
        }

        @Override
        protected void checkAndPerformAttack(LivingEntity target) {
            if (canPerformAttack(target)) {
                resetAttackCooldown();
                startSlam();
            }
        }
    }
}
