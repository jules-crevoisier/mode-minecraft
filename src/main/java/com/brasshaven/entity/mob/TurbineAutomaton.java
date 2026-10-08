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
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.HashSet;
import java.util.Set;

/**
 * Automate à turbine (Turbine Automaton): the maintenance machine of the Dam of the Drowned Valley (model
 * tools/wf/mobs/turbine_automaton.py).
 * <ul>
 *     <li><b>Spin-up dash</b> (5 to 14 blocks, in sight, every 8 s): crouches while its rotor spins faster and faster
 *     and steam screams out of both stacks (18 ticks; the heading locks at 15), then dashes straight ahead for 0.7 s:
 *     everything in its path is battered aside (1.4x damage). If it rams a wall it stops dead, dazed for a second.</li>
 *     <li><b>Paddle slam</b> (within 2.8 blocks, every 2.5 s): both paddles raised high, lands at 12 ticks: 1.2x damage
 *     and a short slowness.</li>
 *     <li><b>Scalding vent</b> (within 3.5 blocks, every 9 s): sinks onto its haunches, arms wide, the chest rattling,
 *     vents at 14 ticks: everything around is scalded and blown back.</li>
 *     <li><b>Boiler burst</b>: when it dies, its boiler bursts: a cloud of steam that hurts and pushes everything
 *     within 3 blocks.</li>
 *     <li>A machine: never drowns, slow to knock back.</li>
 * </ul>
 */
public class TurbineAutomaton extends ActionMonster {
    public static final float WIDTH = 0.95F;
    public static final float HEIGHT = 1.9F;
    private static final int SLAM_HIT = 12;      // 0.6 s, matches turbine_automaton.py
    private static final int DASH_LOCK = 15;
    private static final int DASH_LAUNCH = 18;   // 0.9 s
    private static final int DASH_END = 32;      // 1.6 s
    private static final int VENT_AT = 14;       // 0.7 s

    private int slamCooldown = 10;
    private int dashCooldown = 80;
    private int ventCooldown = 100;
    private int dazed;
    private Vec3 dashDir = Vec3.ZERO;
    private final Set<Integer> dashHit = new HashSet<>();

    public TurbineAutomaton(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 12;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new TurbineGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.TurbineAutomaton.TICKS;
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    private void steamFromStacks(ServerLevel level, int count, double speed) {
        Vec3 back = forward().scale(-0.25);
        Vec3 side = new Vec3(-back.z, 0, back.x).normalize().scale(0.2);
        for (int s = -1; s <= 1; s += 2) {
            Vec3 p = position().add(back).add(side.scale(s)).add(0, 2.0, 0);
            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y, p.z, count, 0.05, 0.05, 0.05, speed);
        }
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (slamCooldown > 0) {
            slamCooldown--;
        }
        if (dashCooldown > 0) {
            dashCooldown--;
        }
        if (ventCooldown > 0) {
            ventCooldown--;
        }
        if (dazed > 0) {
            dazed--;
            if (dazed % 4 == 0) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 1.6, getZ(), 3, 0.3, 0.2, 0.3, 0.05);
            }
        }
        if (tickCount % 30 == 0 && action < 0) {
            steamFromStacks(level, 1, 0.01);
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            // the boiler bursts
            level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.5F);
            level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.4F, 0.6F);
            level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 1.0, getZ(), 2, 0.3, 0.3, 0.3, 0.0);
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 1.0, getZ(), 60, 1.2, 0.8, 1.2, 0.08);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 1.0, getZ(), 20, 0.5, 0.5, 0.5, 0.3);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(3.0),
                    e -> e != this && e.isAlive() && !(e instanceof TurbineAutomaton))) {
                double d = Math.sqrt(distanceToSqr(e));
                if (d > 3.2) {
                    continue;
                }
                if (e.hurtServer(level, damageSources().onFire(), (float) (7.0 - d * 1.2))) {
                    Vec3 push = e.position().subtract(position()).multiply(1, 0, 1);
                    push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(0.9);
                    e.push(push.x, 0.35, push.z);
                    e.hurtMarked = true;
                }
            }
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.IRON_GOLEM_STEP;
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
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.6F, 1.3F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.2F;
    }

    /** Close in for slams and vents; spin up and dash from mid range. */
    static final class TurbineGoal extends Goal {
        private final TurbineAutomaton m;
        private int repath;

        TurbineGoal(TurbineAutomaton m) {
            this.m = m;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = m.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return m.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            m.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(m.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = m.getTarget();
            if (m.action >= 0) {
                int a = m.action;
                int k = m.step();
                m.getNavigation().stop();
                if (a == MobAnims.TurbineAutomaton.SLAM && k == SLAM_HIT) {
                    slam(level, t);
                } else if (a == MobAnims.TurbineAutomaton.DASH) {
                    dash(level, t, k);
                } else if (a == MobAnims.TurbineAutomaton.VENT) {
                    if (k > 0 && k < VENT_AT) {
                        if (k % 3 == 0) {
                            level.sendParticles(ParticleTypes.CLOUD, m.getX(), m.getY() + 0.9, m.getZ(), 2, 0.4, 0.3, 0.4, 0.01);
                            level.playSound(null, m, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 0.8F, 0.6F + k * 0.04F);
                        }
                    } else if (k == VENT_AT) {
                        vent(level);
                    }
                }
                return;
            }
            if (t == null || m.dazed > 0) {
                m.getNavigation().stop();
                return;
            }
            m.getLookControl().setLookAt(t, 20.0F, 30.0F);
            double dist = Math.sqrt(m.distanceToSqr(t));
            if (dist <= 3.5 && m.ventCooldown == 0 && m.random.nextInt(4) == 0) {
                m.ventCooldown = 180;
                m.slamCooldown = Math.max(m.slamCooldown, 20);
                m.begin(MobAnims.TurbineAutomaton.VENT);
                return;
            }
            if (dist <= 2.8 && m.slamCooldown == 0) {
                m.slamCooldown = 50;
                m.begin(MobAnims.TurbineAutomaton.SLAM);
                return;
            }
            if (dist >= 5.0 && dist <= 14.0 && m.dashCooldown == 0 && m.onGround() && m.getSensing().hasLineOfSight(t)) {
                m.dashCooldown = 160;
                m.dashHit.clear();
                m.begin(MobAnims.TurbineAutomaton.DASH);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                m.getNavigation().moveTo(t, 1.05);
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(m.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.5 || to.normalize().dot(m.forward()) >= minDot;
        }

        private void slam(ServerLevel level, @Nullable LivingEntity t) {
            level.playSound(null, m, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.7F, 0.7F);
            Vec3 p = m.position().add(m.forward().scale(1.4));
            level.sendParticles(ParticleTypes.POOF, p.x, p.y + 0.2, p.z, 8, 0.4, 0.05, 0.4, 0.03);
            if (t != null && t.isAlive() && m.distanceToSqr(t) <= 3.1 * 3.1 && inFront(t, 0.2)) {
                float dmg = (float) m.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.2F;
                if (t.hurtServer(level, m.damageSources().mobAttack(m), dmg)) {
                    t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 1), m);
                    Vec3 push = m.toward(t).scale(0.4);
                    t.push(push.x, 0.15, push.z);
                    t.hurtMarked = true;
                }
            }
        }

        private void dash(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                return;
            }
            if (k < DASH_LAUNCH) {
                // the telegraph: the rotor screams, steam pours from the stacks, harder and harder
                if (t != null && k <= DASH_LOCK) {
                    m.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    Vec3 to = t.position().subtract(m.position()).multiply(1, 0, 1);
                    m.dashDir = to.lengthSqr() < 1.0E-4 ? m.forward() : to.normalize();
                    m.setYRot((float) (Mth.atan2(m.dashDir.z, m.dashDir.x) * Mth.RAD_TO_DEG) - 90.0F);
                    m.yBodyRot = m.getYRot();
                }
                if (k % 2 == 0) {
                    m.steamFromStacks(level, 1 + k / 6, 0.02 + k * 0.004);
                }
                if (k % 4 == 0) {
                    level.playSound(null, m, SoundEvents.MINECART_RIDING, SoundSource.HOSTILE, 0.6F, 0.6F + k * 0.06F);
                }
                return;
            }
            if (k == DASH_LAUNCH) {
                level.playSound(null, m, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.0F, 0.5F);
                level.playSound(null, m, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 1.0F, 0.6F);
            }
            if (k > DASH_END) {
                return;
            }
            if (k == DASH_END || (k > DASH_LAUNCH + 1 && m.horizontalCollision)) {
                if (m.horizontalCollision) {
                    // rammed a wall: stops dead, dazed
                    level.playSound(null, m, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 0.5F);
                    level.sendParticles(ParticleTypes.CRIT, m.getX(), m.getY() + 1.0, m.getZ(), 12, 0.4, 0.4, 0.4, 0.2);
                    m.dazed = 20;
                }
                m.setDeltaMovement(m.getDeltaMovement().multiply(0.1, 1, 0.1));
                m.actionTick = Math.max(m.actionTick, DASH_END + 1);
                return;
            }
            Vec3 v = m.dashDir.scale(0.72);
            m.setDeltaMovement(v.x, m.getDeltaMovement().y, v.z);
            m.hurtMarked = true;
            level.sendParticles(ParticleTypes.CLOUD, m.getX(), m.getY() + 0.3, m.getZ(), 2, 0.3, 0.1, 0.3, 0.01);
            float dmg = (float) m.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.4F;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, m.getBoundingBox().inflate(0.4, 0.2, 0.4),
                    e -> e != m && e.isAlive() && !(e instanceof TurbineAutomaton))) {
                if (!m.dashHit.add(e.getId())) {
                    continue;
                }
                if (e.hurtServer(level, m.damageSources().mobAttack(m), dmg)) {
                    e.push(m.dashDir.x * 1.3, 0.45, m.dashDir.z * 1.3);
                    e.hurtMarked = true;
                    level.playSound(null, e, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 1.0F, 0.9F);
                }
            }
        }

        private void vent(ServerLevel level) {
            level.playSound(null, m, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.4F);
            level.playSound(null, m, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 1.2F, 0.7F);
            for (int i = 0; i < 24; i++) {
                double ang = i * Math.PI * 2 / 24;
                Vec3 dir = new Vec3(Math.cos(ang), 0, Math.sin(ang));
                Vec3 p = m.position().add(dir.scale(0.8)).add(0, 0.8, 0);
                level.sendParticles(ParticleTypes.CLOUD, p.x, p.y, p.z, 0, dir.x, 0.05, dir.z, 0.35);
            }
            level.sendParticles(ParticleTypes.CLOUD, m.getX(), m.getY() + 1.0, m.getZ(), 30, 1.5, 0.6, 1.5, 0.05);
            float dmg = (float) m.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.8F;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, m.getBoundingBox().inflate(3.5, 1.0, 3.5),
                    e -> e != m && e.isAlive() && !(e instanceof TurbineAutomaton))) {
                if (m.distanceToSqr(e) > 3.6 * 3.6) {
                    continue;
                }
                if (e.hurtServer(level, m.damageSources().onFire(), dmg)) {
                    Vec3 push = m.toward(e).scale(1.0);
                    e.push(push.x, 0.3, push.z);
                    e.hurtMarked = true;
                }
            }
        }
    }
}
