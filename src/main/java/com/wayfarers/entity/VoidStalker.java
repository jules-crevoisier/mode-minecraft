package com.wayfarers.entity;

import com.wayfarers.generated.MobAnims;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
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
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

/**
 * Traqueur du vide (Void Stalker): a lanky hunter of the outer End islands. Whenever its prey gets away it
 * folds into a thin line and blinks next to it ({@code blink}); up close it scythes with both long arms
 * ({@code rake}). Model: tools/wf/mobs/void_stalker.py.
 */
public class VoidStalker extends Monster implements AnimatedMob {
    /** Rake impact: 0.55 s into the animation (MobAnims.VoidStalker.RAKE). */
    private static final int RAKE_HIT = 11;
    /** Teleport moment: 0.4 s into the blink animation, when the body has collapsed to a line. */
    private static final int BLINK_AT = 8;
    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int rakeTicks;
    private int blinkTicks;

    public VoidStalker(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 36.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new RakeGoal());
        goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        LivingEntity target = getTarget();
        if (target != null && blinkTicks == 0 && rakeTicks == 0 && tickCount % 60 == 0 && distanceToSqr(target) > 36) {
            blinkTicks = BLINK_AT;
            AnimatedMob.playAction(this, MobAnims.VoidStalker.BLINK);
            playSound(SoundEvents.ENDERMAN_STARE, 0.6F, 1.6F);
        }
        if (blinkTicks > 0 && --blinkTicks == 0 && target != null && target.isAlive()) {
            blinkTo(level, target);
        }
        if (rakeTicks > 0 && --rakeTicks == 0) {
            if (target != null && target.isAlive()
                    && getBoundingBox().inflate(1.4, 0.5, 1.4).intersects(target.getBoundingBox())
                    && getSensing().hasLineOfSight(target)) {
                swing(InteractionHand.MAIN_HAND);
                doHurtTarget(level, target);
            }
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1.4, getZ(), 10, 0.5, 0.4, 0.5, 0.02);
        }
    }

    /** Collapse into nothing and reappear beside the prey. */
    private void blinkTo(ServerLevel level, LivingEntity target) {
        double angle = random.nextDouble() * Math.PI * 2;
        double x = target.getX() + Math.cos(angle) * 2.5;
        double z = target.getZ() + Math.sin(angle) * 2.5;
        level.sendParticles(ParticleTypes.PORTAL, getX(), getY() + 1, getZ(), 30, 0.3, 0.8, 0.3, 0.2);
        if (randomTeleport(x, target.getY(), z, true)) {
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1, getZ(), 30, 0.3, 0.8, 0.3, 0.1);
            playSound(SoundEvents.ENDERMAN_TELEPORT, 1.0F, 0.8F);
        }
    }

    private void startRake() {
        rakeTicks = RAKE_HIT;
        AnimatedMob.playAction(this, MobAnims.VoidStalker.RAKE);
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.ENDERMAN_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.ENDERMAN_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.ENDERMAN_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.8F;
    }

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.VoidStalker.TICKS;
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

    /** Melee chase with a wound-up rake; it holds still while blinking or raking. */
    private final class RakeGoal extends MeleeAttackGoal {
        RakeGoal() {
            super(VoidStalker.this, 1.1, false);
        }

        @Override
        public void tick() {
            if (blinkTicks > 0 || rakeTicks > 0) {
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
                startRake();
            }
        }
    }
}
