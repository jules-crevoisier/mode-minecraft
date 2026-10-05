package com.brasshaven.entity;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
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
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * Garde de basalte (Basalt Guard): an armoured warden of the basalt fortresses. It chops with a long golden
 * axe (wound up over the shoulder) and, every third swing, cleaves in a wide arc that hits everything in
 * front of it; its blows wither. Model: tools/wf/mobs/basalt_guard.py.
 *
 * <p>The golden axe is still equipped in the main hand (its attack bonus, enchantments and drop chance
 * apply as before), but the generated model renderer does not draw held items: the axe is part of the
 * model, so the guard never picks up other weapons.
 */
public class BasaltGuard extends Monster implements AnimatedMob {
    /** Chop impact: 0.65 s into the animation (MobAnims.BasaltGuard.CHOP). */
    private static final int CHOP_HIT = 13;
    /** Cleave impact: 0.8 s into the animation (MobAnims.BasaltGuard.CLEAVE). */
    private static final int CLEAVE_HIT = 16;
    private static final double CLEAVE_RADIUS = 3.2;
    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int swingTicks;
    private boolean cleaving;
    private int swings;

    public BasaltGuard(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        setPathfindingMalus(PathType.LAVA, 8.0F);
    }

    /** Base damage 4 + the golden axe's bonus, as for the wither skeleton it used to be. */
    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 44.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new AxeGoal());
        goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractPiglin.class, true));
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty,
                                                  EntitySpawnReason reason, @Nullable SpawnGroupData data) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
        populateDefaultEquipmentSlots(level.getRandom(), difficulty);
        setCanPickUpLoot(false);
        return result;
    }

    @Override
    protected void populateDefaultEquipmentSlots(RandomSource random, DifficultyInstance difficulty) {
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.GOLDEN_AXE));
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (swingTicks > 0 && --swingTicks == 0) {
            if (cleaving) {
                cleaveImpact(level);
            } else {
                chopImpact(level);
            }
        }
    }

    private void startSwing(LivingEntity target) {
        swings++;
        cleaving = swings % 3 == 0 && distanceToSqr(target) < CLEAVE_RADIUS * CLEAVE_RADIUS;
        swingTicks = cleaving ? CLEAVE_HIT : CHOP_HIT;
        AnimatedMob.playAction(this, cleaving ? MobAnims.BasaltGuard.CLEAVE : MobAnims.BasaltGuard.CHOP);
        playSound(SoundEvents.WITHER_SKELETON_AMBIENT, 1.0F, 0.6F);
    }

    private void chopImpact(ServerLevel level) {
        LivingEntity target = getTarget();
        if (target != null && target.isAlive()
                && getBoundingBox().inflate(1.4, 0.5, 1.4).intersects(target.getBoundingBox())
                && getSensing().hasLineOfSight(target)) {
            swing(InteractionHand.MAIN_HAND);
            doHurtTarget(level, target);
            playSound(SoundEvents.PLAYER_ATTACK_STRONG, 1.0F, 0.7F);
        }
        Vec3 front = position().add(getLookAngle().multiply(1.3, 0.0, 1.3));
        level.sendParticles(ParticleTypes.LAVA, front.x, getY() + 0.2, front.z, 4, 0.3, 0.1, 0.3, 0.0);
    }

    /** A wide sweep: every creature (except other guards) within reach in front of the guard is hit. */
    private void cleaveImpact(ServerLevel level) {
        Vec3 look = getLookAngle().multiply(1.0, 0.0, 1.0).normalize();
        swing(InteractionHand.MAIN_HAND);
        playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 1.4F, 0.6F);
        for (int i = -2; i <= 2; i++) {
            double a = Math.atan2(look.z, look.x) + i * 0.5;
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, getX() + Math.cos(a) * 2.0, getY() + 1.1,
                    getZ() + Math.sin(a) * 2.0, 1, 0.0, 0.0, 0.0, 0.0);
            level.sendParticles(ParticleTypes.FLAME, getX() + Math.cos(a) * 2.2, getY() + 1.0,
                    getZ() + Math.sin(a) * 2.2, 3, 0.2, 0.2, 0.2, 0.01);
        }
        for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class,
                getBoundingBox().inflate(CLEAVE_RADIUS, 1.0, CLEAVE_RADIUS),
                e -> e != this && e.isAlive() && !(e instanceof BasaltGuard))) {
            Vec3 to = victim.position().subtract(position()).multiply(1.0, 0.0, 1.0);
            boolean inFront = to.lengthSqr() < 0.01 || to.normalize().dot(look) > -0.2;
            boolean hostile = victim == getTarget() || victim instanceof Player;
            if (inFront && hostile && distanceToSqr(victim) < CLEAVE_RADIUS * CLEAVE_RADIUS + 1.0) {
                if (doHurtTarget(level, victim)) {
                    victim.push(look.x * 0.5, 0.15, look.z * 0.5);
                }
            }
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.WITHER, 200), this);
        }
        return hit;
    }

    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        return !effect.is(MobEffects.WITHER) && super.canBeAffected(effect);
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.WITHER_SKELETON_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.WITHER_SKELETON_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.WITHER_SKELETON_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.NETHERITE_BLOCK_STEP, 0.5F, 0.7F);
    }

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BasaltGuard.TICKS;
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

    /** Melee chase that winds up a chop (or a cleave) and stands its ground until the blow lands. */
    private final class AxeGoal extends MeleeAttackGoal {
        AxeGoal() {
            super(BasaltGuard.this, 1.1, false);
        }

        @Override
        public void tick() {
            if (swingTicks > 0) {
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
                startSwing(target);
            }
        }
    }
}
