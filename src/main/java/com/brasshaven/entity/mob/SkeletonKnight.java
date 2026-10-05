package com.brasshaven.entity.mob;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.EnumSet;

/**
 * Chevalier squelette (Skeleton Knight): a tall skeleton in rusted half-plate with a kite shield and a longsword.
 * <ul>
 *     <li><b>Slash</b> (in reach, 2.9 blocks): the sword is hauled over the shoulder for 0.6 s (animation + a rattle),
 *     then cuts down: full attack damage if the target is still in front and within 3.2 blocks.</li>
 *     <li><b>Guard</b>: when a player stands in front of it within 8 blocks (always when the player draws a bow, else
 *     now and then), it raises its shield for 2 s and advances slowly: frontal damage is cut by 80%
 *     (a blow over 10 damage breaks the guard). Hits from behind or the sides go through.</li>
 *     <li><b>Shield bash</b> (1 in 3 attacks, or as a riposte while guarding): 0.45 s wind-up, then a shove for 60% damage,
 *     strong knockback and Slowness II for 2 s.</li>
 * </ul>
 */
public class SkeletonKnight extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 2.35F;

    private static final int SLASH_IMPACT = 12;   // 0.6 s, matches skeleton_knight.py
    private static final int BASH_IMPACT = 9;     // 0.45 s
    private static final int GUARD_TICKS = 40;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int action = -1;
    private int actionTimer;
    private boolean actionHit;
    private int guardTicks;
    private int attackCooldown;
    private int bashCooldown = 40;
    private int guardCooldown = 40;

    public SkeletonKnight(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 34.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.3)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new KnightCombatGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SkeletonKnight.TICKS;
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

    // ------------------------------------------------------------------ sounds

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.SKELETON_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return guardTicks > 0 ? SoundEvents.SHIELD_BLOCK.value() : SoundEvents.SKELETON_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SKELETON_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SKELETON_STEP, 0.2F, 0.8F);
    }

    // ------------------------------------------------------------------ guard

    public boolean isGuarding() {
        return guardTicks > 0;
    }

    /** True when the damage comes from within ~70 degrees of where the knight faces. */
    private boolean isFrontal(DamageSource source) {
        Vec3 from = source.getSourcePosition();
        if (from == null) {
            return false;
        }
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        if (to.lengthSqr() < 1.0E-4) {
            return false;
        }
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 fwd = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
        return to.normalize().dot(fwd) >= 0.35;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guardTicks > 0 && isFrontal(source) && !source.is(DamageTypeTags.BYPASSES_SHIELD)) {
            boolean heavy = amount > 10.0F;
            amount *= 0.2F;
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 1.0F, 0.8F + random.nextFloat() * 0.2F);
            Vec3 p = position().add(forwardVec().scale(0.6));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.3, p.z, 8, 0.25, 0.3, 0.25, 0.2);
            if (heavy) { // a heavy blow knocks the shield aside
                guardTicks = 0;
                guardCooldown = 80;
                level.playSound(null, this, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 1.0F, 0.7F);
            }
        }
        return super.hurtServer(level, source, amount);
    }

    private Vec3 forwardVec() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (attackCooldown > 0) {
            attackCooldown--;
        }
        if (bashCooldown > 0) {
            bashCooldown--;
        }
        if (guardCooldown > 0) {
            guardCooldown--;
        }
        if (guardTicks > 0) {
            guardTicks--;
        }
    }

    private void startAction(int anim) {
        action = anim;
        actionTimer = 0;
        actionHit = false;
        guardTicks = 0;
        AnimatedMob.playAction(this, anim);
    }

    private boolean inFront(LivingEntity target, double reach, double minDot) {
        Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
        double d = to.length();
        return d <= reach + target.getBbWidth() / 2 && (d < 0.6 || to.normalize().dot(forwardVec()) >= minDot);
    }

    /** Ticks the slash or bash in progress; returns false when no action is running. */
    private boolean tickAction(ServerLevel level, LivingEntity target) {
        if (action < 0) {
            return false;
        }
        int t = actionTimer++;
        if (action == MobAnims.SkeletonKnight.SLASH) {
            if (t == SLASH_IMPACT && !actionHit) {
                actionHit = true;
                level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.0F, 0.7F);
                Vec3 p = position().add(forwardVec().scale(1.5));
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.1, p.z, 1, 0, 0, 0, 0);
                if (target.isAlive() && inFront(target, 3.2, 0.2)) {
                    doHurtTarget(level, target);
                }
            }
        } else if (action == MobAnims.SkeletonKnight.BASH) {
            if (t == BASH_IMPACT && !actionHit) {
                actionHit = true;
                level.playSound(null, this, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 0.8F, 1.2F);
                if (target.isAlive() && inFront(target, 2.6, 0.3)) {
                    float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.6F;
                    if (target.hurtServer(level, damageSources().mobAttack(this), dmg)) {
                        Vec3 push = forwardVec().scale(1.3);
                        target.push(push.x, 0.35, push.z);
                        target.hurtMarked = true;
                        target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                    }
                }
            }
        }
        int len = actionTicks()[action];
        if (actionTimer >= len) {
            action = -1;
        }
        return true;
    }

    /** Melee AI: approach, guard when faced, slash in reach, bash now and then. */
    static final class KnightCombatGoal extends Goal {
        private final SkeletonKnight knight;
        private int repath;

        KnightCombatGoal(SkeletonKnight knight) {
            this.knight = knight;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = knight.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return canUse() || knight.action >= 0;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            knight.getNavigation().stop();
        }

        @Override
        public void tick() {
            LivingEntity target = knight.getTarget();
            if (target == null || !(knight.level() instanceof ServerLevel level)) {
                return;
            }
            knight.getLookControl().setLookAt(target, 30.0F, 30.0F);
            if (knight.action >= 0) {
                knight.getNavigation().stop();
                if (knight.action == MobAnims.SkeletonKnight.SLASH && knight.actionTimer < SLASH_IMPACT) {
                    knight.getLookControl().setLookAt(target, 12.0F, 30.0F); // tracks slowly during the wind-up
                }
                knight.tickAction(level, target);
                return;
            }
            double dist = Math.sqrt(knight.distanceToSqr(target));
            if (knight.guardTicks > 0) {
                // shield up: advance slowly, riposte with a bash when the foe comes close
                if (dist < 2.6 && knight.bashCooldown == 0 && knight.getRandom().nextInt(6) == 0) {
                    knight.bashCooldown = 70;
                    knight.attackCooldown = 25;
                    knight.startAction(MobAnims.SkeletonKnight.BASH);
                } else if (dist > 2.2 && --repath <= 0) {
                    repath = 8;
                    knight.getNavigation().moveTo(target, 0.45);
                }
                return;
            }
            if (dist <= 2.9 && knight.attackCooldown == 0) {
                knight.getNavigation().stop();
                if (knight.bashCooldown == 0 && knight.getRandom().nextInt(3) == 0) {
                    knight.bashCooldown = 80;
                    knight.attackCooldown = 25;
                    knight.startAction(MobAnims.SkeletonKnight.BASH);
                } else {
                    knight.attackCooldown = 34;
                    knight.startAction(MobAnims.SkeletonKnight.SLASH);
                    level.playSound(null, knight, SoundEvents.SKELETON_AMBIENT, SoundSource.HOSTILE, 1.0F, 0.6F);
                }
                return;
            }
            boolean faced = target instanceof Player && knight.inFront(target, 8.0, 0.5) && target.hasLineOfSight(knight);
            if (faced && knight.guardCooldown == 0 && dist > 2.0
                    && (target.isUsingItem() || knight.getRandom().nextInt(30) == 0)) {
                knight.guardCooldown = 90;
                knight.startAction(MobAnims.SkeletonKnight.GUARD);
                knight.action = -1;          // guarding is a stance, not a blocking action
                knight.guardTicks = GUARD_TICKS;
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                knight.getNavigation().moveTo(target, dist > 6 ? 1.1 : 1.0);
            }
        }
    }
}
