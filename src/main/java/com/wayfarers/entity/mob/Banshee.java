package com.wayfarers.entity.mob;

import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
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
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Banshee: a floating spectral woman of the Lithite Well. She hovers without gravity (vanilla
 * {@link FlyingMoveControl} + {@link FlyingPathNavigation}, like the allay) and drifts slowly toward her prey.
 * <ul>
 *     <li><b>Wail</b> (3 to 9 blocks, every 6 s): 16-tick wind-up with a soul-particle cone on the ground, then a
 *     scream in an 8-block, 70 degree cone: 3 magic damage, Slowness II 4 s, Weakness 5 s, strong knockback.</li>
 *     <li><b>Claw</b> (under 2.6 blocks): 12-tick raise, rake for the attack damage (5) and a light push.</li>
 * </ul>
 */
public class Banshee extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 2.1F;
    private static final int WAIL_WINDUP = 16;
    private static final int CLAW_WINDUP = 12;
    private static final double WAIL_RANGE = 8.0;
    private static final double WAIL_HALF_ANGLE = 35.0;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int wailCooldown = 40;
    private int clawCooldown;

    public Banshee(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 10, true);
        this.xpReward = 8;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.FLYING_SPEED, 0.11)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    public void travel(Vec3 input) {
        travelFlying(input, getSpeed());
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new HauntGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.VEX_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.VEX_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.GHAST_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.75F;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (wailCooldown > 0) {
            wailCooldown--;
        }
        if (clawCooldown > 0) {
            clawCooldown--;
        }
        if (tickCount % 7 == 0) {
            level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 0.3, getZ(), 1, 0.2, 0.1, 0.2, 0.01);
        }
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Banshee.TICKS;
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

    // ------------------------------------------------------------------ helpers

    private static boolean isVictim(LivingEntity e, Monster self) {
        if (e == self || !e.isAlive()) {
            return false;
        }
        if (e instanceof Player p) {
            return !p.isCreative() && !p.isSpectator();
        }
        return !(e instanceof Enemy);
    }

    private void face(LivingEntity t, float maxTurn) {
        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * Mth.RAD_TO_DEG) - 90.0F;
        float y = Mth.approachDegrees(getYRot(), yaw, maxTurn);
        setYRot(y);
        yBodyRot = y;
        yHeadRot = y;
    }

    private void hold(float yaw) {
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
        setDeltaMovement(getDeltaMovement().scale(0.6));
    }

    private Vec3 facing(float yaw) {
        float r = yaw * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    /** Ground telegraph of the wail: the outline of the cone in soul particles. */
    private void drawCone(ServerLevel level, float yaw) {
        double floor = Math.floor(getY() - 0.6);
        for (double a = -WAIL_HALF_ANGLE; a <= WAIL_HALF_ANGLE; a += 7) {
            Vec3 d = facing(yaw + (float) a);
            for (double r : new double[]{3.0, 5.5, WAIL_RANGE}) {
                if (r < WAIL_RANGE && Math.abs(a) < WAIL_HALF_ANGLE - 1) {
                    continue;
                }
                level.sendParticles(ParticleTypes.SOUL, getX() + d.x * r, floor + 1.15, getZ() + d.z * r, 1, 0, 0, 0, 0);
            }
        }
    }

    private void wail(ServerLevel level, float yaw) {
        Vec3 fwd = facing(yaw);
        double cos = Math.cos(Math.toRadians(WAIL_HALF_ANGLE));
        Vec3 eye = getEyePosition();
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(eye, eye).inflate(WAIL_RANGE + 1),
                e -> isVictim(e, this))) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > WAIL_RANGE + e.getBbWidth() / 2 || (d > 0.8 && to.normalize().dot(fwd) < cos) || !hasLineOfSight(e)) {
                continue;
            }
            if (e.hurtServer(level, damageSources().indirectMagic(this, this), 3.0F)) {
                Vec3 push = d > 0.01 ? to.normalize().scale(1.1) : fwd;
                e.push(push.x, 0.35, push.z);
                e.hurtMarked = true;
            }
            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1), this);
            e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 0), this);
        }
        for (int i = 1; i <= 4; i++) {
            Vec3 p = eye.add(fwd.scale(i * 1.8));
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y - 0.3, p.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y - 0.4, p.z, 4, 0.4 * i, 0.3, 0.4 * i, 0.02);
        }
        level.playSound(null, this, SoundEvents.GHAST_SCREAM, SoundSource.HOSTILE, 1.6F, 1.35F);
        level.playSound(null, this, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    // ------------------------------------------------------------------ brain

    /** Drift toward the target at head height, rake when close, wail from mid range. */
    static final class HauntGoal extends Goal {
        private final Banshee b;
        private int action = -1;
        private int tick;
        private float yaw;

        HauntGoal(Banshee b) {
            this.b = b;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = b.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            action = -1;
            b.getNavigation().stop();
        }

        private void begin(int which) {
            action = which;
            tick = 0;
            yaw = b.getYRot();
            b.getNavigation().stop();
            AnimatedMob.playAction(b, which);
        }

        @Override
        public void tick() {
            LivingEntity t = b.getTarget();
            if (!(b.level() instanceof ServerLevel level)) {
                return;
            }
            if (action == MobAnims.Banshee.WAIL) {
                tickWail(level, t);
                return;
            }
            if (action == MobAnims.Banshee.CLAW) {
                tickClaw(level, t);
                return;
            }
            if (t == null) {
                return;
            }
            b.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(b.distanceToSqr(t));
            if (dist < 2.6 && b.clawCooldown == 0) {
                b.face(t, 180.0F);
                begin(MobAnims.Banshee.CLAW);
                b.playSound(SoundEvents.VEX_CHARGE, 1.0F, 0.7F);
                return;
            }
            if (dist >= 3.0 && dist <= 9.0 && b.wailCooldown == 0 && b.hasLineOfSight(t)) {
                b.face(t, 180.0F);
                begin(MobAnims.Banshee.WAIL);
                b.playSound(SoundEvents.GHAST_WARN, 1.2F, 1.5F);
                return;
            }
            if (dist > 1.8 && b.tickCount % 8 == 0) {
                b.getNavigation().moveTo(t.getX(), t.getY() + 0.5, t.getZ(), 1.0);
            } else if (dist <= 1.8) {
                b.getNavigation().stop();
            }
        }

        private void tickWail(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            if (k < 9 && t != null) {
                b.face(t, 12.0F);
                yaw = b.getYRot();
            }
            b.hold(yaw);
            if (k < WAIL_WINDUP) {
                if (k % 3 == 0) {
                    b.drawCone(level, yaw);
                }
                level.sendParticles(ParticleTypes.SCULK_SOUL, b.getX(), b.getEyeY(), b.getZ(), 1, 0.3, 0.3, 0.3, 0.01);
            } else if (k == WAIL_WINDUP) {
                b.wail(level, yaw);
            }
            if (k >= MobAnims.Banshee.TICKS[MobAnims.Banshee.WAIL]) {
                action = -1;
                b.wailCooldown = 120;
            }
        }

        private void tickClaw(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            if (k < 8 && t != null) {
                b.face(t, 20.0F);
                yaw = b.getYRot();
            }
            b.hold(yaw);
            if (k == CLAW_WINDUP) {
                Vec3 fwd = b.facing(yaw);
                b.setDeltaMovement(fwd.scale(0.35));
                if (t != null && b.distanceToSqr(t) < 3.2 * 3.2) {
                    Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                    if (to.length() < 0.8 || to.normalize().dot(fwd) > 0.3) {
                        if (b.doHurtTarget(level, t)) {
                            t.push(fwd.x * 0.5, 0.15, fwd.z * 0.5);
                            t.hurtMarked = true;
                        }
                    }
                }
                Vec3 p = b.position().add(fwd.scale(1.4));
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 1, 0, 0, 0, 0);
                level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.8F, 1.4F);
            }
            if (k >= MobAnims.Banshee.TICKS[MobAnims.Banshee.CLAW]) {
                action = -1;
                b.clawCooldown = 16;
            }
        }
    }
}
