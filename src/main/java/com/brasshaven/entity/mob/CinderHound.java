package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
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
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Molosse de cendre (Cinder Hound): the pack hunter of the Nether fortresses, foundries and chain bridges.
 * <ul>
 *     <li><b>Howl</b>: when it finds prey (then at most every 20 s) it sits back and howls; every hound within 16 blocks
 *     takes the same prey and runs faster (Speed II) for 6 s.</li>
 *     <li><b>Charge</b> (4 to 10 blocks, every 6 s): it crouches for 12 ticks, then bolts in a straight line for half a
 *     second, leaving a <b>trail of fire</b> that burns whoever stands in it for 3 s. Contact deals 1.3x damage and
 *     sets the prey on fire. Step aside.</li>
 *     <li><b>Bite</b> (within 2 blocks, lands at 5 ticks): sets the prey on fire.</li>
 *     <li>Immune to fire; bursts into embers when it dies (burns whoever stands next to it, no block damage).</li>
 * </ul>
 */
public class CinderHound extends ActionMonster {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 1.0F;
    private static final int HOWL_AT = 10;        // 0.5 s, matches cinder_hound.py
    private static final int CHARGE_GO = 12;      // 0.6 s
    private static final int CHARGE_END = 22;
    private static final int BITE_HIT = 5;        // 0.25 s

    /** Burning trail points: x, y, z, ticks left. */
    private final List<double[]> trail = new ArrayList<>();
    private int howlCooldown;
    private int chargeCooldown = 60;
    private int biteCooldown;
    private boolean chargeHit;
    private Vec3 chargeDir = Vec3.ZERO;

    public CinderHound(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 7;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.33)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new PackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.CinderHound.TICKS;
    }

    // ------------------------------------------------------------------ fire

    private void burnTrail(ServerLevel level) {
        if (trail.isEmpty()) {
            return;
        }
        List<LivingEntity> near = level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(14.0),
                e -> e.isAlive() && !(e instanceof CinderHound) && !e.fireImmune());
        for (int i = trail.size() - 1; i >= 0; i--) {
            double[] p = trail.get(i);
            if (--p[3] <= 0) {
                trail.remove(i);
                continue;
            }
            if (((int) p[3]) % 5 == 0) {
                level.sendParticles(ParticleTypes.FLAME, p[0], p[1] + 0.1, p[2], 2, 0.2, 0.05, 0.2, 0.01);
            }
            for (LivingEntity e : near) {
                if (Math.abs(e.getX() - p[0]) < 0.8 && Math.abs(e.getZ() - p[2]) < 0.8 && Math.abs(e.getY() - p[1]) < 1.2) {
                    if (e.getRemainingFireTicks() < 20) {
                        e.setRemainingFireTicks(60);
                    }
                }
            }
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 0.5, getZ(), 12, 0.4, 0.3, 0.4, 0.1);
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 0.5, getZ(), 30, 0.6, 0.4, 0.6, 0.06);
            level.playSound(null, this, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 1.0F, 0.8F);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(2.0),
                    e -> e != this && e.isAlive() && !e.fireImmune())) {
                e.setRemainingFireTicks(Math.max(e.getRemainingFireTicks(), 40));
            }
        }
        trail.clear();
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (howlCooldown > 0) {
            howlCooldown--;
        }
        if (chargeCooldown > 0) {
            chargeCooldown--;
        }
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        burnTrail(level);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(5) == 0) {
            level().addParticle(ParticleTypes.SMALL_FLAME, getRandomX(0.5), getY() + 0.6 + random.nextDouble() * 0.4,
                    getRandomZ(0.5), 0, 0.02, 0);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.HOGLIN_AMBIENT;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.35F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.HOGLIN_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.HOGLIN_DEATH;
    }

    /** Howl for the pack, charge in a line of fire, bite. */
    static final class PackGoal extends Goal {
        private final CinderHound h;
        private int repath;
        private @Nullable LivingEntity howledAt;

        PackGoal(CinderHound h) {
            this.h = h;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = h.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return h.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            h.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(h.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = h.getTarget();
            if (h.action >= 0) {
                int a = h.action;
                int k = h.step();
                if (a == MobAnims.CinderHound.HOWL) {
                    h.getNavigation().stop();
                    if (k == HOWL_AT) {
                        howl(level, t);
                    }
                } else if (a == MobAnims.CinderHound.CHARGE) {
                    charge(level, t, k);
                } else if (a == MobAnims.CinderHound.BITE) {
                    h.getNavigation().stop();
                    if (k == BITE_HIT && t != null && t.isAlive() && h.distanceToSqr(t) <= 2.6 * 2.6 && h.doHurtTarget(level, t)) {
                        t.setRemainingFireTicks(Math.max(t.getRemainingFireTicks(), 60));
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            h.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (howledAt != t && h.howlCooldown == 0) {
                howledAt = t;
                h.howlCooldown = 400;
                h.begin(MobAnims.CinderHound.HOWL);
                return;
            }
            double dist = Math.sqrt(h.distanceToSqr(t));
            if (dist <= 2.0 && h.biteCooldown == 0) {
                h.biteCooldown = 18;
                h.begin(MobAnims.CinderHound.BITE);
                return;
            }
            if (dist >= 4.0 && dist <= 10.0 && h.chargeCooldown == 0 && h.onGround() && h.getSensing().hasLineOfSight(t)
                    && Math.abs(t.getY() - h.getY()) < 2.0) {
                h.chargeCooldown = 120;
                h.chargeHit = false;
                h.begin(MobAnims.CinderHound.CHARGE);
                level.playSound(null, h, SoundEvents.HOGLIN_ANGRY, SoundSource.HOSTILE, 1.0F, 1.2F);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                h.getNavigation().moveTo(t, 1.1);
            }
        }

        private void howl(ServerLevel level, @Nullable LivingEntity t) {
            level.playSound(null, h, SoundEvents.HOGLIN_ANGRY, SoundSource.HOSTILE, 2.0F, 0.6F);
            level.playSound(null, h, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 0.6F, 1.9F);
            level.sendParticles(ParticleTypes.FLAME, h.getX(), h.getY() + 1.2, h.getZ(), 14, 0.3, 0.4, 0.3, 0.05);
            for (CinderHound o : level.getEntitiesOfClass(CinderHound.class, h.getBoundingBox().inflate(16.0), CinderHound::isAlive)) {
                o.addEffect(new MobEffectInstance(MobEffects.SPEED, 120, 1), h);
                if (t != null && o.getTarget() == null) {
                    o.setTarget(t);
                }
            }
        }

        private void charge(ServerLevel level, @Nullable LivingEntity t, int k) {
            h.getNavigation().stop();
            if (k < CHARGE_GO) {
                if (t != null) {
                    h.getLookControl().setLookAt(t, 60.0F, 60.0F);
                    h.chargeDir = h.toward(t);
                    float yaw = (float) (Mth.atan2(h.chargeDir.z, h.chargeDir.x) * Mth.RAD_TO_DEG) - 90.0F;
                    h.setYRot(yaw);
                    h.yBodyRot = yaw;
                }
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.SMOKE, h.getX(), h.getY() + 0.2, h.getZ(), 3, 0.3, 0.05, 0.3, 0.02);
                }
                return;
            }
            if (k > CHARGE_END) {
                h.setDeltaMovement(h.getDeltaMovement().multiply(0.5, 1, 0.5));
                return;
            }
            if (h.horizontalCollision) {
                return;
            }
            h.setDeltaMovement(h.chargeDir.x * 0.75, h.getDeltaMovement().y, h.chargeDir.z * 0.75);
            if (k % 2 == 0 && h.onGround()) {
                h.trail.add(new double[] {h.getX(), h.getY(), h.getZ(), 60});
                level.sendParticles(ParticleTypes.FLAME, h.getX(), h.getY() + 0.1, h.getZ(), 4, 0.2, 0.05, 0.2, 0.02);
            }
            if (!h.chargeHit && t != null && t.isAlive() && h.getBoundingBox().inflate(0.3).intersects(t.getBoundingBox())) {
                h.chargeHit = true;
                float dmg = (float) h.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.3F;
                if (t.hurtServer(level, h.damageSources().mobAttack(h), dmg)) {
                    t.setRemainingFireTicks(Math.max(t.getRemainingFireTicks(), 60));
                    t.push(h.chargeDir.x * 0.8, 0.3, h.chargeDir.z * 0.8);
                    t.hurtMarked = true;
                }
            }
        }
    }
}
