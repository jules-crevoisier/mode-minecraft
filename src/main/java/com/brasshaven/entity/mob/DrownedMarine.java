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
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Fusilier noyé (Drowned Marine): a marine of the Dreadnought Wreck still on watch (model tools/wf/mobs/drowned_marine.py).
 * <ul>
 *     <li>Breathes and walks under water as well as on deck (no water path penalty, swims faster).</li>
 *     <li><b>Aimed shot</b> (6 to 20 blocks, in sight, once per engagement, then again after 15 s): shoulders the rifle
 *     while a trail of bubbles (smoke out of the water) runs from the muzzle to his prey; the aim <b>locks at 15
 *     ticks</b> (a click and a spark at the muzzle), the shot cracks at 20 along that line: heavy damage to the first
 *     creature on it. Step aside after the click.</li>
 *     <li><b>Bayonet charge</b> (3 to 12 blocks, right after a shot or every 5 s): levels the bayonet and drops into a
 *     crouch for 10 ticks, then runs straight along the locked line for 16 ticks: the first creature in his way is
 *     run through and thrown back; he stops at a wall.</li>
 *     <li><b>Bayonet thrust</b> (within 3 blocks, every 1.3 s): draws the rifle back along his side, lands at 9 ticks.</li>
 * </ul>
 */
public class DrownedMarine extends ActionMonster {
    public static final float WIDTH = 0.65F;
    public static final float HEIGHT = 2.0F;
    private static final int SHOT_LOCK = 15;
    private static final int SHOT_FIRE = 20;     // 1.0 s, matches drowned_marine.py
    private static final int CHARGE_GO = 10;     // 0.5 s
    private static final int CHARGE_END = 26;
    private static final int THRUST_HIT = 9;     // 0.45 s
    private static final double SHOT_RANGE = 24.0;

    private int shotCooldown = 20;
    private int chargeCooldown = 60;
    private int thrustCooldown = 10;
    private boolean chargeHit;
    private Vec3 aim = Vec3.ZERO;
    private Vec3 chargeDir = Vec3.ZERO;

    public DrownedMarine(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 10;
        setPathfindingMalus(PathType.WATER, 0.0F);
        setPathfindingMalus(PathType.WATER_BORDER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.ARMOR, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MarineGoal(this));
        goalSelector.addGoal(5, new RandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.DrownedMarine.TICKS;
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public void travel(Vec3 input) {
        if (isInWater() && isEffectiveAi()) {
            moveRelative(0.02F, input);                                     // a drowned man knows the water
        }
        super.travel(input);
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** The rifle's muzzle: right shoulder height, a little ahead. */
    private Vec3 muzzle() {
        Vec3 fwd = forward();
        Vec3 right = new Vec3(-fwd.z, 0, fwd.x);
        return position().add(fwd.scale(0.9)).add(right.scale(0.2)).add(0, 1.55, 0);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (shotCooldown > 0) {
            shotCooldown--;
        }
        if (chargeCooldown > 0) {
            chargeCooldown--;
        }
        if (thrustCooldown > 0) {
            thrustCooldown--;
        }
        if (getTarget() == null && shotCooldown > 40) {
            shotCooldown = 40;                                              // a new engagement: the first shot comes quick
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(5) == 0) {
            level().addParticle(isInWater() ? ParticleTypes.BUBBLE : ParticleTypes.DRIPPING_WATER, getRandomX(0.5),
                    getY() + 1.2 + random.nextDouble() * 0.7, getRandomZ(0.5), 0, 0, 0);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return isInWater() ? SoundEvents.DROWNED_AMBIENT_WATER : SoundEvents.DROWNED_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return isInWater() ? SoundEvents.DROWNED_HURT_WATER : SoundEvents.DROWNED_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return isInWater() ? SoundEvents.DROWNED_DEATH_WATER : SoundEvents.DROWNED_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.DROWNED_STEP, 0.5F, 0.9F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.8F;
    }

    /** One careful shot, then the bayonet. */
    static final class MarineGoal extends Goal {
        private final DrownedMarine d;
        private int repath;

        MarineGoal(DrownedMarine d) {
            this.d = d;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = d.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return d.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            d.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(d.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = d.getTarget();
            if (d.action >= 0) {
                int a = d.action;
                int k = d.step();
                d.getNavigation().stop();
                if (a == MobAnims.DrownedMarine.SHOT) {
                    shot(level, t, k);
                } else if (a == MobAnims.DrownedMarine.CHARGE) {
                    charge(level, t, k);
                } else if (a == MobAnims.DrownedMarine.THRUST) {
                    if (t != null && k < THRUST_HIT) {
                        d.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    }
                    if (k == THRUST_HIT) {
                        level.playSound(null, d, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 0.8F, 1.2F);
                        if (t != null && t.isAlive() && d.distanceToSqr(t) <= 3.4 * 3.4 && inFront(t, 0.3)) {
                            d.doHurtTarget(level, t);
                        }
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            d.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(d.distanceToSqr(t));
            boolean sees = d.getSensing().hasLineOfSight(t);
            if (dist >= 6.0 && dist <= 20.0 && sees && d.shotCooldown == 0) {
                d.shotCooldown = 300;
                d.aim = t.getEyePosition().add(0, -0.3, 0);
                d.begin(MobAnims.DrownedMarine.SHOT);
                level.playSound(null, d, SoundEvents.CROSSBOW_LOADING_START.value(), SoundSource.HOSTILE, 1.0F, 0.6F);
                return;
            }
            if (dist >= 3.0 && dist <= 12.0 && sees && d.chargeCooldown == 0) {
                d.chargeCooldown = 100;
                d.chargeDir = d.toward(t);
                d.begin(MobAnims.DrownedMarine.CHARGE);
                level.playSound(null, d, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.6F);
                return;
            }
            if (dist <= 3.0 && d.thrustCooldown == 0) {
                d.thrustCooldown = 26;
                d.begin(MobAnims.DrownedMarine.THRUST);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                if (dist > 2.4) {
                    d.getNavigation().moveTo(t, d.isInWater() ? 1.3 : 1.0);
                } else {
                    d.getNavigation().stop();
                }
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(d.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.5 || to.normalize().dot(d.forward()) >= minDot;
        }

        private void shot(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                d.chargeCooldown = 0;                                       // the shot is gone: now the bayonet
                return;
            }
            if (k <= SHOT_LOCK && t != null && t.isAlive()) {
                d.aim = t.getEyePosition().add(0, -0.3, 0);
                d.getLookControl().setLookAt(t, 30.0F, 30.0F);
            }
            Vec3 from = d.muzzle();
            Vec3 dir = d.aim.subtract(from);
            dir = dir.lengthSqr() < 1.0E-4 ? d.forward() : dir.normalize();
            if (k < SHOT_FIRE) {
                // the telegraph: a trail of bubbles (smoke in the air) along the aim, every other tick
                if (k >= 6 && k % 2 == 0) {
                    double len = Math.min(SHOT_RANGE, from.distanceTo(d.aim));
                    int n = Math.max(3, (int) (len * 1.2));
                    for (int i = 1; i <= n; i++) {
                        Vec3 p = from.add(dir.scale(len * i / n));
                        boolean wet = level.getFluidState(BlockPos.containing(p)).isSource() || d.isInWater();
                        level.sendParticles(wet ? ParticleTypes.BUBBLE : ParticleTypes.SMOKE, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
                    }
                }
                if (k == SHOT_LOCK) {
                    level.playSound(null, d, SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.HOSTILE, 1.2F, 0.8F);
                    level.sendParticles(ParticleTypes.CRIT, from.x, from.y, from.z, 6, 0.05, 0.05, 0.05, 0.1);
                }
                return;
            }
            if (k == SHOT_FIRE) {
                Vec3 end = from.add(dir.scale(SHOT_RANGE));
                HitResult hit = level.clip(new ClipContext(from, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, d));
                if (hit.getType() != HitResult.Type.MISS) {
                    end = hit.getLocation();
                }
                LivingEntity victim = null;
                double best = Double.MAX_VALUE;
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(from, end).inflate(0.5),
                        e -> e != d && e.isAlive() && !(e instanceof DrownedMarine))) {
                    var clip = e.getBoundingBox().inflate(0.2).clip(from, end);
                    if (clip.isPresent() && clip.get().distanceToSqr(from) < best) {
                        best = clip.get().distanceToSqr(from);
                        victim = e;
                    }
                }
                Vec3 stop = victim != null ? from.add(dir.scale(Math.sqrt(best))) : end;
                level.playSound(null, d, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 1.6F, 0.6F);
                level.playSound(null, d, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.5F, 1.9F);
                level.sendParticles(ParticleTypes.LARGE_SMOKE, from.x, from.y, from.z, 5, 0.1, 0.1, 0.1, 0.02);
                level.sendParticles(ParticleTypes.FLAME, from.x, from.y, from.z, 3, 0.05, 0.05, 0.05, 0.02);
                double len = stop.distanceTo(from);
                int n = Math.max(3, (int) (len * 2));
                for (int i = 1; i <= n; i++) {
                    Vec3 p = from.add(dir.scale(len * i / n));
                    level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
                }
                if (victim != null) {
                    victim.hurtServer(level, d.damageSources().mobProjectile(d, d), (float) d.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.4F);
                } else {
                    level.sendParticles(ParticleTypes.SMOKE, stop.x, stop.y, stop.z, 6, 0.1, 0.1, 0.1, 0.02);
                }
            }
        }

        private void charge(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                return;
            }
            if (k < CHARGE_GO) {
                if (t != null && t.isAlive()) {
                    d.chargeDir = d.toward(t);
                    d.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (k % 3 == 0) {
                    level.sendParticles(d.isInWater() ? ParticleTypes.BUBBLE : ParticleTypes.SPLASH, d.getX(), d.getY() + 0.2, d.getZ(), 4,
                            0.3, 0.1, 0.3, 0.05);
                }
                if (k == 0) {
                    d.chargeHit = false;
                }
                return;
            }
            if (k < CHARGE_END && !d.chargeHit) {
                double speed = d.isInWater() ? 0.45 : 0.55;
                Vec3 v = d.chargeDir.scale(speed);
                d.setDeltaMovement(v.x, d.getDeltaMovement().y, v.z);
                float yaw = (float) (Mth.atan2(d.chargeDir.z, d.chargeDir.x) * Mth.RAD_TO_DEG) - 90.0F;
                d.setYRot(yaw);
                d.yBodyRot = yaw;
                d.setYHeadRot(yaw);
                if (k % 2 == 0) {
                    level.sendParticles(d.isInWater() ? ParticleTypes.BUBBLE : ParticleTypes.SPLASH, d.getX(), d.getY() + 0.3, d.getZ(), 3,
                            0.2, 0.1, 0.2, 0.05);
                }
                if (k % 5 == 0) {
                    level.playSound(null, d, SoundEvents.DROWNED_STEP, SoundSource.HOSTILE, 1.0F, 0.7F);
                }
                if (d.horizontalCollision && k > CHARGE_GO + 2) {
                    d.chargeHit = true;                                     // ran into a wall
                    level.playSound(null, d, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 0.6F, 0.8F);
                    return;
                }
                Vec3 tip = d.position().add(d.chargeDir.scale(0.9));
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(tip, tip).inflate(0.8, 1.0, 0.8),
                        e -> e != d && e.isAlive() && !(e instanceof DrownedMarine))) {
                    if (e.hurtServer(level, d.damageSources().mobAttack(d), (float) d.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.5F)) {
                        e.push(d.chargeDir.x * 1.2, 0.35, d.chargeDir.z * 1.2);
                        e.hurtMarked = true;
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 1), d);
                        level.playSound(null, e, SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 1.0F, 0.8F);
                    }
                    d.chargeHit = true;
                    d.setDeltaMovement(d.getDeltaMovement().multiply(0.2, 1, 0.2));
                    break;
                }
            }
        }
    }
}
