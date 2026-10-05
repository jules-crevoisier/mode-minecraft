package com.brasshaven.entity;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.attribute.EnvironmentAttributes;
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
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.jetbrains.annotations.Nullable;

/**
 * Spectre des cartes (Map Wraith): a fast paper ghost haunting libraries and outposts. It hovers on a skirt
 * of page strips, rakes with its quill fingers (blinding and confusing), bursts into fluttering pages when
 * struck ({@code scatter}) and burns in daylight. Model: tools/wf/mobs/map_wraith.py.
 */
public class MapWraith extends Monster implements AnimatedMob {
    /** Rake impact: 0.5 s into the animation (MobAnims.MapWraith.RAKE). */
    private static final int RAKE_HIT = 10;
    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int rakeTicks;

    public MapWraith(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.FOLLOW_RANGE, 35.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new RakeGoal());
        goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.9));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractVillager.class, false));
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level() instanceof ServerLevel level) {
            if (isAlive() && isInSunlight(level)) {
                igniteForSeconds(8.0F);
            }
            if (tickCount % 10 == 0) {
                level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1, getZ(), 3, 0.3, 0.5, 0.3, 0.0);
            }
        }
    }

    /** Same test as the vanilla undead daylight burn (which only applies to the burn_in_daylight tag). */
    private boolean isInSunlight(ServerLevel level) {
        if (!level.environmentAttributes().getValue(EnvironmentAttributes.MONSTERS_BURN, position())) {
            return false;
        }
        float brightness = getLightLevelDependentMagicValue();
        BlockPos eyes = BlockPos.containing(getX(), getEyeY(), getZ());
        boolean shielded = isInWaterOrRain() || isInPowderSnow || wasInPowderSnow;
        return brightness > 0.5F && random.nextFloat() * 30.0F < (brightness - 0.4F) * 2.0F && !shielded
                && level.canSeeSky(eyes);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (rakeTicks > 0 && --rakeTicks == 0) {
            LivingEntity target = getTarget();
            if (target != null && target.isAlive()
                    && getBoundingBox().inflate(1.1, 0.5, 1.1).intersects(target.getBoundingBox())
                    && getSensing().hasLineOfSight(target)) {
                swing(InteractionHand.MAIN_HAND);
                doHurtTarget(level, target);
            }
            level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY() + 1.0, getZ(), 6, 0.4, 0.3, 0.4, 0.02);
        }
    }

    private void startRake() {
        rakeTicks = RAKE_HIT;
        AnimatedMob.playAction(this, MobAnims.MapWraith.RAKE);
        playSound(SoundEvents.VEX_CHARGE, 0.8F, 0.8F);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0), this);
            living.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 80, 0), this);
        }
        return hit;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && isAlive() && rakeTicks == 0 && !source.is(DamageTypeTags.IS_FIRE)) {
            AnimatedMob.playAction(this, MobAnims.MapWraith.SCATTER);
            level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1.0, getZ(), 20, 0.5, 0.6, 0.5, 0.05);
            playSound(SoundEvents.BOOK_PAGE_TURN, 1.0F, 0.7F);
        }
        return hurt;
    }

    /** A hovering paper ghost does not take fall damage. */
    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.BOOK_PAGE_TURN;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.VEX_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.VEX_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        // it hovers: no footsteps
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.75F;
    }

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MapWraith.TICKS;
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

    /** Melee chase whose hit lands at the end of the rake animation; the wraith keeps drifting meanwhile. */
    private final class RakeGoal extends MeleeAttackGoal {
        RakeGoal() {
            super(MapWraith.this, 1.0, false);
        }

        @Override
        protected void checkAndPerformAttack(LivingEntity target) {
            if (rakeTicks == 0 && canPerformAttack(target)) {
                resetAttackCooldown();
                startRake();
            }
        }
    }
}
