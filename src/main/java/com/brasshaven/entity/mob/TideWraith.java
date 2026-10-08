package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
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
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Spectre des marées (Tide Wraith): the drowned ghost of the Tidal Abbey (model tools/wf/mobs/tide_wraith.py,
 * drawn see-through).
 * <ul>
 *     <li>Floats a little above the ground and <b>phases through water</b>: it moves through water as fast as through
 *     air (faster, even), never drowns, currents do not push it, and while it is in water every blow but magic passes
 *     through it. Lure it onto dry stone.</li>
 *     <li><b>Rake</b> (within 2.4 blocks, every 1.5 s): the claw drawn back high, lands at 7 ticks: damage and a short
 *     slowness.</li>
 *     <li><b>Undertow hook</b> (2 to 6 blocks, every 7 s): it spreads both arms and gapes, then lunges at 16 ticks; a
 *     prey it touches is <b>hooked</b> and dragged for 3 s toward the nearest water (or away with it), taking a little
 *     damage; hitting the wraith breaks the hold.</li>
 *     <li><b>Sink and rise</b> (every 10 s when its prey is far, or after three hits): it folds down into a swirl (the
 *     spot it will come out of bubbles first) and rises again 2.5 blocks behind its prey at 16 ticks.</li>
 * </ul>
 */
public class TideWraith extends ActionMonster {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 2.0F;
    private static final int RAKE_HIT = 7;       // 0.35 s, matches tide_wraith.py
    private static final int GRAB_LUNGE = 16;    // 0.8 s
    private static final int SINK_AT = 16;       // 0.8 s
    private static final int DRAG_TICKS = 60;

    private int rakeCooldown;
    private int grabCooldown = 60;
    private int sinkCooldown = 100;
    private int hits;
    private int hitWindow;
    private boolean sinkQueued;
    private @Nullable LivingEntity hooked;
    private int dragTicks;
    private @Nullable Vec3 dragTo;
    private Vec3 riseAt = Vec3.ZERO;

    public TideWraith(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 9;
        setNoGravity(true);
        setPathfindingMalus(PathType.WATER, 0.0F);
        setPathfindingMalus(PathType.WATER_BORDER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FLYING_SPEED, 0.32)
                .add(Attributes.FOLLOW_RANGE, 24.0);
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
        travelFlying(input, getSpeed() * (isInWater() ? 1.6F : 1.0F));
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(2, new WraithGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.TideWraith.TICKS;
    }

    // ------------------------------------------------------------------ phasing

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean magic = source.is(DamageTypes.MAGIC) || source.is(DamageTypes.INDIRECT_MAGIC);
        if (hooked != null && source.getEntity() == hooked) {
            release(level);                                   // any blow from the hooked prey breaks the hold
        }
        if ((isInWater() || action == MobAnims.TideWraith.SINK) && !magic && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            level.sendParticles(ParticleTypes.BUBBLE, getX(), getY() + 1.0, getZ(), 12, 0.3, 0.5, 0.3, 0.05);
            level.playSound(null, this, SoundEvents.BUBBLE_COLUMN_UPWARDS_INSIDE, SoundSource.HOSTILE, 1.0F, 1.4F);
            return false;
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && isAlive()) {
            hits = hitWindow > 0 ? hits + 1 : 1;
            hitWindow = 120;
            if (hits >= 3 && sinkCooldown < 140) {
                hits = 0;
                sinkQueued = true;
            }
        }
        return hurt;
    }

    private void release(ServerLevel level) {
        if (hooked != null) {
            level.playSound(null, hooked, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.0F, 1.0F);
        }
        hooked = null;
        dragTicks = 0;
        dragTo = null;
    }

    /** The nearest water block surface within 8 blocks of the wraith, or null. */
    private @Nullable Vec3 nearestWater(ServerLevel level) {
        BlockPos me = blockPosition();
        BlockPos best = null;
        double bestD = Double.MAX_VALUE;
        for (BlockPos p : BlockPos.betweenClosed(me.offset(-8, -4, -8), me.offset(8, 3, 8))) {
            if (level.getFluidState(p).is(FluidTags.WATER)) {
                double d = p.distSqr(me);
                if (d < bestD) {
                    bestD = d;
                    best = p.immutable();
                }
            }
        }
        return best == null ? null : Vec3.atCenterOf(best);
    }

    private void tickDrag(ServerLevel level) {
        if (hooked == null) {
            return;
        }
        if (!hooked.isAlive() || dragTicks <= 0 || hooked.distanceToSqr(this) > 6.0 * 6.0
                || hooked instanceof Player p && (p.isCreative() || p.isSpectator())) {
            release(level);
            return;
        }
        dragTicks--;
        Vec3 goal = dragTo != null ? dragTo : position().add(toward(hooked).scale(-4.0));
        Vec3 move = goal.subtract(position());
        if (move.lengthSqr() > 1.0) {
            move = move.normalize().scale(0.18);
            setDeltaMovement(move.x, move.y * 0.5, move.z);
        } else {
            setDeltaMovement(getDeltaMovement().scale(0.5));
        }
        // the prey is reeled in to the claws, a step in front of the wraith
        Vec3 front = position().add(toward(hooked).scale(1.1));
        Vec3 pull = front.subtract(hooked.position());
        hooked.setDeltaMovement(pull.x * 0.35, Math.max(-0.2, Math.min(0.15, pull.y * 0.3)), pull.z * 0.35);
        hooked.hurtMarked = true;
        if (dragTicks % 15 == 0) {
            hooked.hurtServer(level, damageSources().mobAttack(this), 1.5F);
            hooked.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 2), this);
        }
        if (dragTicks % 3 == 0) {
            Vec3 m = position().add(hooked.position()).scale(0.5);
            level.sendParticles(ParticleTypes.SPLASH, m.x, m.y + 1.0, m.z, 3, 0.2, 0.2, 0.2, 0.0);
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (rakeCooldown > 0) {
            rakeCooldown--;
        }
        if (grabCooldown > 0) {
            grabCooldown--;
        }
        if (sinkCooldown > 0) {
            sinkCooldown--;
        }
        if (hitWindow > 0) {
            hitWindow--;
        }
        tickDrag(level);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            if (random.nextInt(3) == 0) {
                level().addParticle(isInWater() ? ParticleTypes.BUBBLE : ParticleTypes.FALLING_WATER,
                        getRandomX(0.5), getY() + 0.2 + random.nextDouble() * 1.4, getRandomZ(0.5), 0, -0.02, 0);
            }
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.DROWNED_AMBIENT_WATER;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.DROWNED_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.DROWNED_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.75F;
    }

    /** Rake, hook and drag, sink and rise behind the prey. */
    static final class WraithGoal extends Goal {
        private final TideWraith w;
        private int repath;

        WraithGoal(TideWraith w) {
            this.w = w;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = w.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return w.action >= 0 || w.hooked != null || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            w.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(w.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = w.getTarget();
            if (w.sinkQueued && w.action < 0 && w.hooked == null && t != null) {
                w.sinkQueued = false;
                startSink(level, t);
                return;
            }
            if (w.action >= 0) {
                int a = w.action;
                int k = w.step();
                if (a == MobAnims.TideWraith.RAKE) {
                    w.getNavigation().stop();
                    if (k == RAKE_HIT && t != null && t.isAlive() && w.distanceToSqr(t) <= 2.8 * 2.8 && w.doHurtTarget(level, t)) {
                        t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0), w);
                    }
                } else if (a == MobAnims.TideWraith.GRAB) {
                    grab(level, t, k);
                } else if (a == MobAnims.TideWraith.SINK) {
                    w.getNavigation().stop();
                    w.setDeltaMovement(Vec3.ZERO);
                    if (k > 0 && k < SINK_AT && k % 2 == 0) {
                        level.sendParticles(ParticleTypes.BUBBLE_POP, w.riseAt.x, w.riseAt.y + 0.2, w.riseAt.z, 6, 0.4, 0.1, 0.4, 0.02);
                        level.sendParticles(ParticleTypes.SPLASH, w.riseAt.x, w.riseAt.y + 0.1, w.riseAt.z, 6, 0.4, 0.05, 0.4, 0.0);
                    }
                    if (k == SINK_AT) {
                        Vec3 from = w.position();
                        w.teleportTo(w.riseAt.x, w.riseAt.y, w.riseAt.z);
                        level.sendParticles(ParticleTypes.SPLASH, from.x, from.y + 0.5, from.z, 20, 0.4, 0.4, 0.4, 0.1);
                        w.begin(MobAnims.TideWraith.RISE);
                        level.playSound(null, w, SoundEvents.PLAYER_SPLASH_HIGH_SPEED, SoundSource.HOSTILE, 1.0F, 0.7F);
                        if (t != null) {
                            w.getLookControl().setLookAt(t, 180.0F, 90.0F);
                        }
                    }
                } else if (a == MobAnims.TideWraith.RISE) {
                    w.getNavigation().stop();
                    if (t != null) {
                        w.getLookControl().setLookAt(t, 60.0F, 60.0F);
                    }
                }
                return;
            }
            if (w.hooked != null) {
                w.getNavigation().stop();
                return;
            }
            if (t == null || !t.isAlive()) {
                return;
            }
            w.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(w.distanceToSqr(t));
            boolean sees = w.getSensing().hasLineOfSight(t);
            if (dist <= 2.4 && w.rakeCooldown == 0) {
                w.rakeCooldown = 30;
                w.begin(MobAnims.TideWraith.RAKE);
                return;
            }
            if (sees && dist >= 2.0 && dist <= 6.0 && w.grabCooldown == 0) {
                w.grabCooldown = 140;
                w.begin(MobAnims.TideWraith.GRAB);
                level.playSound(null, w, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 1.4F, 0.5F);
                return;
            }
            if (w.sinkCooldown == 0 && (dist > 10.0 || !sees)) {
                startSink(level, t);
                return;
            }
            if (--repath <= 0 || w.getNavigation().isDone()) {
                repath = 10;
                w.getNavigation().moveTo(t.getX(), t.getY() + 0.4, t.getZ(), 1.0);
            }
        }

        private void startSink(ServerLevel level, LivingEntity t) {
            // come out 2.5 blocks behind the prey, on a free spot
            float yaw = t.getYRot() * Mth.DEG_TO_RAD;
            Vec3 back = new Vec3(Mth.sin(yaw), 0, -Mth.cos(yaw));
            for (double d : new double[] {2.5, 1.8, 3.2}) {
                Vec3 p = t.position().add(back.scale(d)).add(0, 0.3, 0);
                if (level.noCollision(w, w.getDimensions(w.getPose()).makeBoundingBox(p))) {
                    w.riseAt = p;
                    w.sinkCooldown = 200;
                    w.begin(MobAnims.TideWraith.SINK);
                    level.playSound(null, w, SoundEvents.PLAYER_SPLASH, SoundSource.HOSTILE, 1.0F, 0.6F);
                    return;
                }
            }
            w.sinkCooldown = 40;
        }

        private void grab(ServerLevel level, @Nullable LivingEntity t, int k) {
            w.getNavigation().stop();
            if (k < GRAB_LUNGE) {
                w.setDeltaMovement(w.getDeltaMovement().scale(0.5));
                if (t != null) {
                    w.getLookControl().setLookAt(t, 60.0F, 60.0F);
                }
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.FALLING_WATER, w.getX(), w.getY() + 1.6, w.getZ(), 6, 0.6, 0.2, 0.6, 0.0);
                }
                return;
            }
            if (k == GRAB_LUNGE && t != null) {
                Vec3 d = t.position().add(0, 0.4, 0).subtract(w.position());
                if (d.lengthSqr() > 1.0E-3) {
                    d = d.normalize().scale(0.9);
                    w.setDeltaMovement(d);
                }
                level.playSound(null, w, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.2F, 0.6F);
            }
            if (k >= GRAB_LUNGE && k <= GRAB_LUNGE + 5 && w.hooked == null && t != null && t.isAlive()
                    && w.getBoundingBox().inflate(0.9).intersects(t.getBoundingBox())) {
                if (t.hurtServer(level, w.damageSources().mobAttack(w), (float) w.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                    w.hooked = t;
                    w.dragTicks = DRAG_TICKS;
                    w.dragTo = w.nearestWater(level);
                    level.playSound(null, t, SoundEvents.FISHING_BOBBER_RETRIEVE, SoundSource.HOSTILE, 1.4F, 0.6F);
                }
            }
        }
    }
}
