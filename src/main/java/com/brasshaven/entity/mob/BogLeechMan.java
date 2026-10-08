package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Homme-sangsue (Bog Leech-Man): the lurker under the walkways of the Mire Stilt-City (model
 * tools/wf/mobs/bog_leech_man.py).
 * <ul>
 *     <li>Breathes water and swims fast (no water path penalty); it waits in the water for its prey.</li>
 *     <li><b>Leap and latch</b> (3 to 8 blocks, every 6 s, from the ground or the water): it sinks low and flares its
 *     mouth (12 ticks, bubbles boil around it in water), then springs. If it reaches its prey in flight it
 *     <b>latches on</b>: it clings to the prey's front for up to 3 s, slowing it, and drinks at 20, 40 and 60 ticks
 *     (2 damage each, healing itself as much). Two blows from the prey tear it off.</li>
 *     <li><b>Claw rake</b> (within 2.3 blocks, every 1.5 s): the claw drawn back over the shoulder, lands at 8 ticks.</li>
 * </ul>
 */
public class BogLeechMan extends ActionMonster {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 1.8F;
    private static final int CLAW_HIT = 8;       // 0.4 s, matches bog_leech_man.py
    private static final int LEAP_LAUNCH = 12;   // 0.6 s
    private static final int LEAP_END = 26;      // 1.3 s
    private static final float DRAIN = 2.0F;

    private int clawCooldown = 10;
    private int leapCooldown = 40;
    private @Nullable LivingEntity latched;
    private int tornHits;

    public BogLeechMan(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 9;
        setPathfindingMalus(PathType.WATER, 0.0F);
        setPathfindingMalus(PathType.WATER_BORDER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new LeechGoal(this));
        goalSelector.addGoal(5, new RandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BogLeechMan.TICKS;
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public void travel(Vec3 input) {
        if (isInWater() && isEffectiveAi()) {
            moveRelative(0.04F, input);                                     // slick as an eel in the water
        }
        super.travel(input);
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ the latch

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (latched != null) {
            if (source.is(DamageTypes.IN_WALL) || source.is(DamageTypes.CRAMMING)) {
                return false;                                               // clinging to the prey in a tight spot
            }
            if (source.getEntity() == latched && ++tornHits >= 2) {
                release(level, true);
            }
        }
        return super.hurtServer(level, source, amount);
    }

    private void latchOn(ServerLevel level, LivingEntity t) {
        latched = t;
        tornHits = 0;
        begin(MobAnims.BogLeechMan.LATCH);
        level.playSound(null, t, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.2F, 0.6F);
        level.playSound(null, t, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 0.8F, 1.4F);
    }

    private void release(ServerLevel level, boolean thrown) {
        LivingEntity t = latched;
        latched = null;
        if (action == MobAnims.BogLeechMan.LATCH) {
            action = -1;
            level.broadcastEntityEvent(this, STOP_EVENT);
        }
        if (t != null) {
            Vec3 away = position().subtract(t.position()).multiply(1, 0, 1);
            away = away.lengthSqr() < 1.0E-4 ? forward().scale(-1) : away.normalize();
            setDeltaMovement(away.x * (thrown ? 0.6 : 0.3), 0.3, away.z * (thrown ? 0.6 : 0.3));
            hurtMarked = true;
            level.playSound(null, this, SoundEvents.SLIME_JUMP, SoundSource.HOSTILE, 1.0F, 0.6F);
        }
    }

    /** Server, every tick while latched: cling to the prey's front, drink on the gulps of the animation. */
    private void tickLatch(ServerLevel level, int k) {
        LivingEntity t = latched;
        if (t == null) {
            return;
        }
        if (k < 0 || !t.isAlive() || distanceToSqr(t) > 4.0 * 4.0 || t instanceof Player p && (p.isCreative() || p.isSpectator())) {
            release(level, false);
            return;
        }
        Vec3 look = t.getLookAngle().multiply(1, 0, 1);
        look = look.lengthSqr() < 1.0E-4 ? Vec3.ZERO : look.normalize();
        Vec3 at = t.position().add(look.scale(t.getBbWidth() * 0.5 + 0.35)).add(0, Math.max(0, t.getBbHeight() - 1.6), 0);
        setPos(at.x, at.y, at.z);
        setDeltaMovement(Vec3.ZERO);
        lookAt(t, 180.0F, 90.0F);
        yBodyRot = getYRot();
        t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 10, 1), this);
        if (k == 19 || k == 39 || k == 59) {
            if (t.hurtServer(level, damageSources().mobAttack(this), DRAIN)) {
                heal(DRAIN);
                level.sendParticles(ParticleTypes.DAMAGE_INDICATOR, t.getX(), t.getY() + t.getBbHeight() * 0.6, t.getZ(),
                        3, 0.2, 0.2, 0.2, 0.1);
                level.playSound(null, this, SoundEvents.HONEY_DRINK.value(), SoundSource.HOSTILE, 1.0F, 0.5F);
            }
        }
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (clawCooldown > 0) {
            clawCooldown--;
        }
        if (leapCooldown > 0) {
            leapCooldown--;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(8) == 0) {
            level().addParticle(ParticleTypes.DRIPPING_WATER, getRandomX(0.5), getY() + 1.0 + random.nextDouble() * 0.6,
                    getRandomZ(0.5), 0, 0, 0);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.FROG_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.FROG_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SLIME_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SLIME_SQUISH_SMALL, 0.4F, 0.7F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.55F;
    }

    /** Lurk, leap, latch and drink; rake up close. */
    static final class LeechGoal extends Goal {
        private final BogLeechMan b;
        private int repath;

        LeechGoal(BogLeechMan b) {
            this.b = b;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = b.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return b.action >= 0 || b.latched != null || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            b.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(b.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = b.getTarget();
            if (b.latched != null) {
                b.getNavigation().stop();
                b.tickLatch(level, b.step());
                return;
            }
            if (b.action >= 0) {
                int a = b.action;
                int k = b.step();
                if (a == MobAnims.BogLeechMan.CLAW) {
                    b.getNavigation().stop();
                    if (k == CLAW_HIT) {
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.8F, 0.9F);
                        if (t != null && t.isAlive() && b.distanceToSqr(t) <= 2.7 * 2.7 && inFront(t, 0.2)) {
                            if (t.hurtServer(level, b.damageSources().mobAttack(b), (float) b.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                                t.addEffect(new MobEffectInstance(MobEffects.POISON, 40, 0), b);
                            }
                        }
                    }
                } else if (a == MobAnims.BogLeechMan.LEAP) {
                    leap(level, t, k);
                }
                return;
            }
            if (t == null) {
                return;
            }
            b.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(b.distanceToSqr(t));
            if (dist >= 3.0 && dist <= 8.0 && b.leapCooldown == 0 && (b.onGround() || b.isInWater())
                    && b.getSensing().hasLineOfSight(t)) {
                b.leapCooldown = 120;
                b.begin(MobAnims.BogLeechMan.LEAP);
                level.playSound(null, b, SoundEvents.FROG_LONG_JUMP, SoundSource.HOSTILE, 1.0F, 0.5F);
                return;
            }
            if (dist <= 2.3 && b.clawCooldown == 0) {
                b.clawCooldown = 30;
                b.begin(MobAnims.BogLeechMan.CLAW);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                b.getNavigation().moveTo(t, b.isInWater() ? 1.4 : 1.05);
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.5 || to.normalize().dot(b.forward()) >= minDot;
        }

        private void leap(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                return;
            }
            if (k < LEAP_LAUNCH) {
                b.getNavigation().stop();
                if (t != null) {
                    b.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (b.isInWater()) {
                    level.sendParticles(ParticleTypes.BUBBLE, b.getX(), b.getY() + 0.6, b.getZ(), 4, 0.4, 0.3, 0.4, 0.05);
                    level.sendParticles(ParticleTypes.SPLASH, b.getX(), b.getY() + 1.2, b.getZ(), 3, 0.4, 0.1, 0.4, 0.05);
                } else if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.ITEM_SLIME, b.getX(), b.getY() + 0.2, b.getZ(), 2, 0.3, 0.05, 0.3, 0.02);
                }
                return;
            }
            if (k == LEAP_LAUNCH) {
                if (t == null) {
                    return;
                }
                Vec3 to = t.position().subtract(b.position());
                Vec3 flat = to.multiply(1, 0, 1);
                double d = Math.max(0.1, flat.length());
                double speed = Math.min(1.4, 0.25 + d * 0.15);
                Vec3 v = flat.scale(speed / d);
                double up = 0.42 + Math.max(0, to.y) * 0.1 + (b.isInWater() ? 0.35 : 0.0);
                b.setDeltaMovement(v.x, up, v.z);
                b.hurtMarked = true;
                level.playSound(null, b, b.isInWater() ? SoundEvents.PLAYER_SPLASH : SoundEvents.SLIME_JUMP, SoundSource.HOSTILE, 1.0F, 0.6F);
                if (b.isInWater()) {
                    level.sendParticles(ParticleTypes.SPLASH, b.getX(), b.getY() + 1.0, b.getZ(), 20, 0.5, 0.2, 0.5, 0.2);
                }
                return;
            }
            if (k <= LEAP_END && t != null && t.isAlive() && b.distanceToSqr(t) <= 1.7 * 1.7
                    && !(t instanceof Player p && (p.isCreative() || p.isSpectator()))) {
                if (t.hurtServer(level, b.damageSources().mobAttack(b), (float) b.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                    b.latchOn(level, t);
                }
            }
        }
    }

    /** Entity event: the latch was torn off early, stop its animation on every client. */
    private static final byte STOP_EVENT = 99;

    @Override
    public void handleEntityEvent(byte id) {
        if (id == STOP_EVENT) {
            for (var s : actionStates()) {
                s.stop();
            }
            return;
        }
        super.handleEntityEvent(id);
    }

    @Override
    public boolean isPushable() {
        return latched == null && super.isPushable();
    }
}
