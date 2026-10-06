package com.brasshaven.entity.automaton;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Drone à vapeur (Steam Drone): a flying copper boiler with two rotors and a rivet gun. It hunts at night in the
 * badlands and the savanna highlands, and in the dark of the Undercity.
 * <ul>
 *     <li>Hovers without gravity (vanilla {@link FlyingMoveControl}, like the allay), keeps 6 to 11 blocks from its
 *     prey and 3 to 5 blocks above it, slowly circling.</li>
 *     <li><b>Rivet</b> (4 to 18 blocks, line of sight, every 2-3 s): steadies for 6 ticks, then fires a hot rivet
 *     (3 damage, a second one 30% of the time).</li>
 *     <li><b>Dive</b> (3 to 14 blocks, every 8 s): rises and rears up for 10 ticks, then plunges at the spot where
 *     its prey stood: 5 damage and a knock-back on contact, then climbs back up.</li>
 *     <li>Puffs steam from its smokestack; dies in a small burst of smoke and sparks (no block damage).</li>
 * </ul>
 */
public class SteamDrone extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.8F;
    public static final float HEIGHT = 1.35F; // covers the boiler and smokestack of the model
    private static final int SHOOT_WINDUP = 6;    // 0.3 s, matches steam_drone.py
    private static final int DIVE_WINDUP = 10;    // 0.5 s

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int shootCooldown = 40;
    private int diveCooldown = 100;

    public SteamDrone(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 6;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 18.0)
                .add(Attributes.ARMOR, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FLYING_SPEED, 0.14)
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
        goalSelector.addGoal(2, new DroneAttackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, BrassGolem.class, true));
    }

    // ------------------------------------------------------------------ sounds: hissing steam and whirring rotors

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.FIRE_EXTINGUISH;
    }

    @Override
    protected float getSoundVolume() {
        return 0.4F;
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
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.3F;
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.5, getZ(), 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.5, getZ(), 10, 0.3, 0.3, 0.3, 0.03);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.5, getZ(), 16, 0.3, 0.3, 0.3, 0.2);
            level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.5F, 1.7F);
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (shootCooldown > 0) {
            shootCooldown--;
        }
        if (diveCooldown > 0) {
            diveCooldown--;
        }
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SteamDrone.TICKS;
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
            // steam puffs from the smokestack (behind and above the boiler)
            if (random.nextInt(4) == 0) {
                float yaw = yBodyRot * Mth.DEG_TO_RAD;
                double bx = Mth.sin(yaw) * 0.2;
                double bz = -Mth.cos(yaw) * 0.2;
                level().addParticle(random.nextInt(3) == 0 ? ParticleTypes.SMOKE : ParticleTypes.WHITE_SMOKE,
                        getX() + bx, getY() + 1.35, getZ() + bz, 0, 0.04, 0);
            }
        }
    }

    // ------------------------------------------------------------------ brain

    private Vec3 facing() {
        float r = getYRot() * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    private void fireRivet(ServerLevel level, LivingEntity t, double spread) {
        Vec3 muzzle = position().add(facing().scale(0.45)).add(0, 0.25, 0);
        Vec3 aim = new Vec3(t.getX(), t.getY(0.5), t.getZ()).subtract(muzzle);
        HotRivetEntity rivet = new HotRivetEntity(level, this, false, 3.0F);
        rivet.setPos(muzzle.x, muzzle.y, muzzle.z);
        rivet.shoot(aim.x, aim.y, aim.z, 1.4F, (float) spread);
        level.addFreshEntity(rivet);
        level.sendParticles(ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 3, 0.05, 0.05, 0.05, 0.02);
        level.playSound(null, this, SoundEvents.DISPENSER_LAUNCH, SoundSource.HOSTILE, 0.8F, 1.6F);
        level.playSound(null, this, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 0.4F, 1.9F);
    }

    /** Circle above the prey, shoot rivets, sometimes dive at it. */
    static final class DroneAttackGoal extends Goal {
        private final SteamDrone d;
        private int action = -1;
        private int tick;
        private boolean doubleShot;
        private boolean hit;
        private Vec3 diveAt = Vec3.ZERO;
        private float orbit;
        /** The last orbit point had no path: a failed path also reads as "done", so wait for the next scheduled try. */
        private boolean noPath;

        DroneAttackGoal(SteamDrone d) {
            this.d = d;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = d.getTarget();
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
        public void start() {
            orbit = d.random.nextFloat() * Mth.TWO_PI;
        }

        @Override
        public void stop() {
            action = -1;
            d.getNavigation().stop();
        }

        private void begin(int which) {
            action = which;
            tick = 0;
            hit = false;
            d.getNavigation().stop();
            AnimatedMob.playAction(d, which);
        }

        @Override
        public void tick() {
            if (!(d.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = d.getTarget();
            if (action == MobAnims.SteamDrone.SHOOT) {
                int k = tick++;
                d.setDeltaMovement(d.getDeltaMovement().scale(0.7));
                if (t != null) {
                    d.getLookControl().setLookAt(t, 60.0F, 60.0F);
                    if (k == SHOOT_WINDUP || doubleShot && k == SHOOT_WINDUP + 4) {
                        d.fireRivet(level, t, k == SHOOT_WINDUP ? 2.0 : 5.0);
                    }
                }
                if (k >= MobAnims.SteamDrone.TICKS[MobAnims.SteamDrone.SHOOT]) {
                    action = -1;
                    d.shootCooldown = 40 + d.random.nextInt(21);
                }
                return;
            }
            if (action == MobAnims.SteamDrone.DIVE) {
                tickDive(level, t);
                return;
            }
            if (t == null) {
                return;
            }
            d.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(d.distanceToSqr(t));
            boolean sees = d.getSensing().hasLineOfSight(t);
            if (dist >= 3.0 && dist <= 14.0 && d.diveCooldown == 0 && sees) {
                diveAt = t.position().add(0, t.getBbHeight() * 0.5, 0);
                begin(MobAnims.SteamDrone.DIVE);
                level.playSound(null, d, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.0F, 0.6F);
                return;
            }
            if (dist >= 4.0 && dist <= 18.0 && d.shootCooldown == 0 && sees) {
                doubleShot = d.random.nextFloat() < 0.3F;
                begin(MobAnims.SteamDrone.SHOOT);
                level.playSound(null, d, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 0.8F, 1.4F);
                return;
            }
            // circle 6 to 11 blocks away, 3 to 5 blocks above the prey
            if (d.tickCount % 10 == 0 || (d.getNavigation().isDone() && !noPath)) {
                orbit += 0.35F;
                double r = dist > 12 || !sees ? 4.0 : 8.0;
                double h = 3.0 + d.random.nextDouble() * 2.0;
                noPath = !d.getNavigation().moveTo(t.getX() + Mth.cos(orbit) * r, t.getY() + h, t.getZ() + Mth.sin(orbit) * r, 1.0);
            }
        }

        private void tickDive(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            d.getNavigation().stop();
            if (k < DIVE_WINDUP) {
                d.setDeltaMovement(0, 0.06, 0);
                if (t != null) {
                    diveAt = t.position().add(0, t.getBbHeight() * 0.5, 0);
                    d.getLookControl().setLookAt(t, 60.0F, 60.0F);
                }
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.CLOUD, d.getX(), d.getY() + 1.2, d.getZ(), 2, 0.2, 0.1, 0.2, 0.02);
                }
            } else if (k < DIVE_WINDUP + 14) {
                Vec3 to = diveAt.subtract(d.position());
                if (to.length() > 0.6) {
                    d.setDeltaMovement(to.normalize().scale(0.8));
                }
                if (!hit && t != null && t.isAlive() && d.getBoundingBox().inflate(0.4).intersects(t.getBoundingBox())) {
                    hit = true;
                    if (d.doHurtTarget(level, t)) {
                        Vec3 push = d.getDeltaMovement().multiply(1, 0, 1).normalize().scale(0.7);
                        t.push(push.x, 0.25, push.z);
                        t.hurtMarked = true;
                    }
                    level.playSound(null, d, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.8F);
                    d.setDeltaMovement(d.getDeltaMovement().scale(-0.4).add(0, 0.4, 0));
                }
                if (k % 2 == 0) {
                    level.sendParticles(ParticleTypes.WHITE_SMOKE, d.getX(), d.getY() + 0.6, d.getZ(), 2, 0.1, 0.1, 0.1, 0.01);
                }
            } else {
                d.setDeltaMovement(d.getDeltaMovement().scale(0.6).add(0, 0.05, 0));   // pull up
            }
            if (k >= MobAnims.SteamDrone.TICKS[MobAnims.SteamDrone.DIVE]) {
                action = -1;
                d.diveCooldown = 160;
            }
        }
    }
}
