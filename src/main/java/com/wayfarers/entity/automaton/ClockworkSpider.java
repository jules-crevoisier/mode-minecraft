package com.wayfarers.entity.automaton;

import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
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
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WallClimberNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.EnumSet;

/**
 * Araignée-horloge (Clockwork Spider): a small, fast brass automaton of the badlands, the savanna highlands and the
 * Clockwork Citadel, with a wind-up key turning on its back.
 * <ul>
 *     <li>Weak alone (14 health, 3 damage) but quick (speed 0.36) and usually in packs; climbs walls like a spider
 *     and takes no fall damage.</li>
 *     <li><b>Bite</b> (within 1.7 blocks): rears up for 5 ticks, then snaps its copper pincers.</li>
 *     <li><b>Leap</b> (3 to 8 blocks, on the ground, every 4-5 s): winds its key for 7 ticks and springs at the
 *     target; the first contact in flight deals 1.5x damage.</li>
 *     <li>Ticks quietly like a clock; dies in a burst of sparks and loose cogs.</li>
 * </ul>
 */
public class ClockworkSpider extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 0.6F;
    private static final EntityDataAccessor<Boolean> DATA_CLIMBING = SynchedEntityData.defineId(ClockworkSpider.class, EntityDataSerializers.BOOLEAN);
    private static final int BITE_IMPACT = 5;     // 0.25 s, matches clockwork_spider.py
    private static final int LEAP_LAUNCH = 7;     // 0.35 s

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int action = -1;
    private int actionTimer;
    private boolean actionHit;
    private int biteCooldown;
    private int leapCooldown = 30;

    public ClockworkSpider(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 4;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.36)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new SpiderAttackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, BrassGolem.class, true));
    }

    // ------------------------------------------------------------------ climbing (as vanilla Spider)

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_CLIMBING, false);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WallClimberNavigation(this, level);
    }

    @Override
    public boolean onClimbable() {
        return entityData.get(DATA_CLIMBING);
    }

    @Override
    public void makeStuckInBlock(BlockState state, Vec3 speedMultiplier) {
        if (!state.is(Blocks.COBWEB)) {
            super.makeStuckInBlock(state, speedMultiplier);
        }
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ClockworkSpider.TICKS;
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
            if (random.nextInt(40) == 0) {
                level().addParticle(ParticleTypes.WHITE_SMOKE, getX(), getY() + 0.5, getZ(), 0, 0.03, 0);
            }
        } else {
            entityData.set(DATA_CLIMBING, horizontalCollision);
        }
    }

    // ------------------------------------------------------------------ sounds: ticking brass and grinding springs

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.NOTE_BLOCK_HAT.value();
    }

    @Override
    public int getAmbientSoundInterval() {
        return 60;
    }

    @Override
    protected float getSoundVolume() {
        return 0.5F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.COPPER_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.COPPER_GOLEM_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SPIDER_STEP, 0.12F, 1.6F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.5F;
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.3, getZ(), 14, 0.3, 0.2, 0.3, 0.15);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.3, getZ(), 4, 0.2, 0.1, 0.2, 0.02);
            level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 0.8F, 1.4F);
        }
    }

    // ------------------------------------------------------------------ attacks

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        if (leapCooldown > 0) {
            leapCooldown--;
        }
    }

    private void startAction(int anim) {
        action = anim;
        actionTimer = 0;
        actionHit = false;
        AnimatedMob.playAction(this, anim);
    }

    private void tickAction(ServerLevel level, LivingEntity target) {
        int t = actionTimer++;
        if (action == MobAnims.ClockworkSpider.BITE) {
            if (t == BITE_IMPACT && target.isAlive() && distanceToSqr(target) <= 2.1 * 2.1) {
                level.playSound(null, this, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 0.7F, 1.8F);
                doHurtTarget(level, target);
            }
        } else if (action == MobAnims.ClockworkSpider.LEAP) {
            if (t < LEAP_LAUNCH) {
                getNavigation().stop();
                if (t % 2 == 0) {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.6, getZ() + 0.0, 2, 0.1, 0.1, 0.1, 0.05);
                }
                if (t == 1) {
                    level.playSound(null, this, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 0.8F, 1.6F);
                }
            } else if (t == LEAP_LAUNCH) {
                Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
                double d = Math.max(0.1, to.length());
                Vec3 v = to.scale(Math.min(1.3, 0.25 + d * 0.15) / d);
                setDeltaMovement(v.x, 0.42, v.z);
                hurtMarked = true;
                level.playSound(null, this, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 0.6F, 1.8F);
                level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 0.1, getZ(), 4, 0.2, 0.05, 0.2, 0.02);
            } else if (!actionHit && target.isAlive() && distanceToSqr(target) <= 1.6 * 1.6) {
                actionHit = true;
                float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.5F;
                if (target.hurtServer(level, damageSources().mobAttack(this), dmg)) {
                    Vec3 push = getDeltaMovement().multiply(1, 0, 1).normalize().scale(0.4);
                    target.push(push.x, 0.15, push.z);
                    target.hurtMarked = true;
                }
                setDeltaMovement(getDeltaMovement().multiply(0.2, 1, 0.2));
            }
        }
        if (actionTimer >= actionTicks()[action]) {
            action = -1;
        }
    }

    /** Scuttle in (climbing if needed), bite in reach, leap from mid range. */
    static final class SpiderAttackGoal extends Goal {
        private final ClockworkSpider spider;
        private int repath;

        SpiderAttackGoal(ClockworkSpider spider) {
            this.spider = spider;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = spider.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            spider.action = -1;
            spider.getNavigation().stop();
        }

        @Override
        public void tick() {
            LivingEntity target = spider.getTarget();
            if (target == null || !(spider.level() instanceof ServerLevel level)) {
                return;
            }
            spider.getLookControl().setLookAt(target, 30.0F, 30.0F);
            if (spider.action >= 0) {
                if (spider.action == MobAnims.ClockworkSpider.BITE) {
                    spider.getNavigation().stop();
                }
                spider.tickAction(level, target);
                return;
            }
            double dist = Math.sqrt(spider.distanceToSqr(target));
            if (dist <= 1.7 && spider.biteCooldown == 0) {
                spider.biteCooldown = 16;
                spider.getNavigation().stop();
                spider.startAction(MobAnims.ClockworkSpider.BITE);
                return;
            }
            if (dist >= 3.0 && dist <= 8.0 && spider.onGround() && spider.leapCooldown == 0
                    && Math.abs(target.getY() - spider.getY()) < 2.5 && spider.hasLineOfSight(target)) {
                spider.leapCooldown = 80 + spider.getRandom().nextInt(25);
                spider.getNavigation().stop();
                float yaw = (float) (Mth.atan2(target.getZ() - spider.getZ(), target.getX() - spider.getX()) * Mth.RAD_TO_DEG) - 90.0F;
                spider.setYRot(yaw);
                spider.yBodyRot = yaw;
                spider.startAction(MobAnims.ClockworkSpider.LEAP);
                return;
            }
            if (--repath <= 0) {
                repath = 5;
                spider.getNavigation().moveTo(target, 1.2);
            }
        }
    }
}
