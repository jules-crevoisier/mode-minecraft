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
 * Pillard du ciel (Sky Raider): the wind pirate of the Sky Isles, on clockwork ornithopter wings.
 * <ul>
 *     <li>Circles 4 to 7 blocks above its prey and rakes it with its talons when it comes close (lands at 6 ticks).</li>
 *     <li><b>Snatch</b> (a player, 4 to 16 blocks, every 12 s): hovers still and <b>shrieks</b> for 15 ticks (wings wide,
 *     a clear warning), then dives. If it catches its prey, it lifts it (Levitation for up to 1.5 s, about 4 blocks up)
 *     and lets go: hit it, or sneak, and it lets go at once.</li>
 *     <li>A dive that misses ends in a crash: the raider lies <b>stunned</b> on the ground for 1.6 s and takes 50% more
 *     damage. Punish it.</li>
 * </ul>
 */
public class SkyRaider extends ActionMonster {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 1.4F;
    private static final int SCREECH = 15;   // 0.75 s, matches sky_raider.py
    private static final int SWIPE_HIT = 6;  // 0.3 s
    private static final int HOLD_MAX = 30;

    private int snatchCooldown = 120;
    private int swipeCooldown;
    private int stunned;
    private int holding;
    private @Nullable LivingEntity held;

    public SkyRaider(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 9;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ARMOR, 1.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FLYING_SPEED, 0.15)
                .add(Attributes.FOLLOW_RANGE, 32.0);
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
        if (stunned > 0) {
            super.travel(input);
        } else {
            travelFlying(input, getSpeed());
        }
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
        goalSelector.addGoal(2, new RaiderGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 16.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SkyRaider.TICKS;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.PHANTOM_AMBIENT;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.25F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PILLAGER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PHANTOM_DEATH;
    }

    // ------------------------------------------------------------------ grabbing and letting go

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (stunned > 0) {
            damage *= 1.5F;
        }
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && held != null) {
            release(level);
        }
        return hurt;
    }

    private void grab(ServerLevel level, LivingEntity t) {
        held = t;
        holding = HOLD_MAX;
        t.addEffect(new MobEffectInstance(MobEffects.LEVITATION, HOLD_MAX, 3), this);
        doHurtTarget(level, t);
        begin(MobAnims.SkyRaider.CARRY);
        level.playSound(null, this, SoundEvents.PHANTOM_BITE, SoundSource.HOSTILE, 1.0F, 1.2F);
    }

    private void release(ServerLevel level) {
        if (held != null) {
            held.removeEffect(MobEffects.LEVITATION);
            level.sendParticles(ParticleTypes.CLOUD, held.getX(), held.getY() + 1.0, held.getZ(), 6, 0.3, 0.2, 0.3, 0.02);
        }
        held = null;
        holding = 0;
        snatchCooldown = 240;
        setDeltaMovement(getDeltaMovement().add(0, 0.4, 0));
    }

    @Override
    public void die(DamageSource source) {
        if (held != null && level() instanceof ServerLevel sl) {
            release(sl);
        }
        super.die(source);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (snatchCooldown > 0) {
            snatchCooldown--;
        }
        if (swipeCooldown > 0) {
            swipeCooldown--;
        }
        if (stunned > 0 && --stunned == 0) {
            setNoGravity(true);
            setDeltaMovement(0, 0.35, 0);
        }
        if (held != null) {
            LivingEntity h = held;
            if (!h.isAlive() || --holding <= 0 || h.isShiftKeyDown() || distanceToSqr(h) > 16.0
                    || h instanceof Player p && (p.isCreative() || p.isSpectator())) {
                release(level);
            } else {
                // hover just above the prey, wings beating
                Vec3 above = h.position().add(0, h.getBbHeight() + 0.2, 0);
                setDeltaMovement(above.subtract(position()).scale(0.5));
                if (holding % 10 == 0) {
                    begin(MobAnims.SkyRaider.CARRY);
                    level.playSound(null, this, SoundEvents.PHANTOM_FLAP, SoundSource.HOSTILE, 1.0F, 1.3F);
                }
            }
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(6) == 0 && !onGround()) {
            level().addParticle(ParticleTypes.CLOUD, getRandomX(0.8), getY() + 0.8, getRandomZ(0.8), 0, -0.05, 0);
        }
    }

    /** Circle above the prey, rake it, shriek and dive to snatch it; crash when the dive misses. */
    static final class RaiderGoal extends Goal {
        private final SkyRaider r;
        private float orbit;
        private int diving;
        private Vec3 diveAt = Vec3.ZERO;

        RaiderGoal(SkyRaider r) {
            this.r = r;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = r.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return r.action >= 0 || diving > 0 || r.stunned > 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void start() {
            orbit = r.random.nextFloat() * Mth.TWO_PI;
        }

        @Override
        public void stop() {
            diving = 0;
            r.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(r.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = r.getTarget();
            if (r.stunned > 0 || r.held != null) {
                r.getNavigation().stop();
                if (r.action >= 0) {
                    r.step();
                }
                return;
            }
            if (diving > 0) {
                tickDive(level, t);
                return;
            }
            if (r.action == MobAnims.SkyRaider.SCREECH) {
                int k = r.step();
                r.getNavigation().stop();
                r.setDeltaMovement(r.getDeltaMovement().scale(0.5).add(0, 0.01, 0));
                if (t != null) {
                    r.getLookControl().setLookAt(t, 60.0F, 60.0F);
                    diveAt = t.position().add(0, t.getBbHeight() * 0.6, 0);
                }
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.CLOUD, r.getX(), r.getY() + 0.7, r.getZ(), 3, 0.6, 0.2, 0.6, 0.02);
                }
                if (k == SCREECH) {
                    diving = 24;
                    level.playSound(null, r, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 1.4F, 1.1F);
                }
                return;
            }
            if (r.action >= 0) {
                int a = r.action;
                int k = r.step();
                if (a == MobAnims.SkyRaider.SWIPE && k == SWIPE_HIT && t != null && t.isAlive()
                        && r.getBoundingBox().inflate(1.2).intersects(t.getBoundingBox())) {
                    r.doHurtTarget(level, t);
                }
                return;
            }
            if (t == null) {
                return;
            }
            r.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(r.distanceToSqr(t));
            boolean sees = r.getSensing().hasLineOfSight(t);
            if (dist < 2.4 && r.swipeCooldown == 0) {
                r.swipeCooldown = 25;
                r.begin(MobAnims.SkyRaider.SWIPE);
                return;
            }
            if (t instanceof Player && dist >= 4.0 && dist <= 16.0 && sees && r.snatchCooldown == 0) {
                r.snatchCooldown = 240;
                r.begin(MobAnims.SkyRaider.SCREECH);
                level.playSound(null, r, SoundEvents.PHANTOM_AMBIENT, SoundSource.HOSTILE, 2.0F, 1.6F);
                return;
            }
            // circle above the prey
            if (r.tickCount % 10 == 0 || r.getNavigation().isDone()) {
                orbit += 0.4F;
                double rad = dist > 14 || !sees ? 3.0 : 6.0;
                double h = 4.0 + r.random.nextDouble() * 3.0;
                r.getNavigation().moveTo(t.getX() + Mth.cos(orbit) * rad, t.getY() + h, t.getZ() + Mth.sin(orbit) * rad, 1.1);
            }
        }

        private void tickDive(ServerLevel level, @Nullable LivingEntity t) {
            diving--;
            r.getNavigation().stop();
            Vec3 to = diveAt.subtract(r.position());
            if (to.length() > 0.5) {
                r.setDeltaMovement(to.normalize().scale(1.0));
            }
            if (diving % 2 == 0) {
                level.sendParticles(ParticleTypes.CLOUD, r.getX(), r.getY() + 0.6, r.getZ(), 2, 0.1, 0.1, 0.1, 0.01);
            }
            if (t != null && t.isAlive() && r.getBoundingBox().inflate(0.5).intersects(t.getBoundingBox())) {
                diving = 0;
                if (t instanceof Player p && (p.isCreative() || p.isSpectator())) {
                    return;
                }
                r.grab(level, t);
                return;
            }
            if (to.length() < 0.8 || r.onGround() || r.horizontalCollision || diving == 0) {
                // missed: crash
                diving = 0;
                r.stunned = 32;
                r.setNoGravity(false);
                r.setDeltaMovement(0, -0.3, 0);
                r.begin(MobAnims.SkyRaider.STUNNED);
                level.playSound(null, r, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.6F);
                level.sendParticles(ParticleTypes.POOF, r.getX(), r.getY() + 0.3, r.getZ(), 10, 0.4, 0.2, 0.4, 0.05);
            }
        }
    }
}
