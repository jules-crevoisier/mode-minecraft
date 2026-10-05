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
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.Optional;

/**
 * Sentinelle de la faille (Rift Sentinel): the floating warden of the End archives, observatories, wrecks and gardens.
 * <ul>
 *     <li>Hovers 6 to 12 blocks from its prey, its rune tablets orbiting its single eye.</li>
 *     <li><b>Tether beam</b> (every 4 s, line of sight): the tablets lock in front of the eye and a dotted line of light
 *     points at the prey for 20 ticks (the aim is locked at 14 ticks: step out of the line). Then the beam fires: 5
 *     magic damage and the prey is <b>dragged</b> toward the sentinel (deadly near the void). Blocks stop the beam.</li>
 *     <li><b>Shove</b> (within 2.5 blocks, lands at 6 ticks): the tablets slam outward and push the prey away.</li>
 *     <li><b>Blink</b>: after three hits within 8 s it folds in on itself and reappears up to 10 blocks away.</li>
 * </ul>
 */
public class RiftSentinel extends ActionMonster {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 2.3F;
    private static final int AIM_LOCK = 14;
    private static final int FIRE = 20;       // 1.0 s, matches rift_sentinel.py
    private static final int SHOVE_HIT = 6;   // 0.3 s
    private static final int BLINK_AT = 5;    // 0.25 s

    private int beamCooldown = 60;
    private int shoveCooldown;
    private int hits;
    private int hitWindow;
    private boolean blinkQueued;
    private Vec3 aim = Vec3.ZERO;

    public RiftSentinel(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 10, true);
        this.xpReward = 10;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.FLYING_SPEED, 0.1)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
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
        goalSelector.addGoal(2, new SentinelGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.5));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 16.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.RiftSentinel.TICKS;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && isAlive()) {
            hits = hitWindow > 0 ? hits + 1 : 1;
            hitWindow = 160;
            if (hits >= 3) {
                hits = 0;
                blinkQueued = true;
            }
        }
        return hurt;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (beamCooldown > 0) {
            beamCooldown--;
        }
        if (shoveCooldown > 0) {
            shoveCooldown--;
        }
        if (hitWindow > 0) {
            hitWindow--;
        }
    }

    private Vec3 eye() {
        return position().add(0, 1.4, 0);
    }

    private void blink(ServerLevel level) {
        Vec3 from = position();
        for (int i = 0; i < 12; i++) {
            double x = getX() + (random.nextDouble() - 0.5) * 20.0;
            double y = getY() + random.nextInt(7) - 2;
            double z = getZ() + (random.nextDouble() - 0.5) * 20.0;
            if (randomTeleport(x, y, z, false)) {
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, from.x, from.y + 1.0, from.z, 30, 0.4, 0.8, 0.4, 0.05);
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1.0, getZ(), 30, 0.4, 0.8, 0.4, 0.05);
                level.playSound(null, from.x, from.y, from.z, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.0F, 0.7F);
                return;
            }
        }
    }

    private void fireBeam(ServerLevel level, @Nullable LivingEntity t) {
        Vec3 from = eye();
        Vec3 dir = aim.subtract(from).normalize();
        Vec3 to = from.add(dir.scale(18.0));
        HitResult wall = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (wall.getType() != HitResult.Type.MISS) {
            to = wall.getLocation();
        }
        double len = from.distanceTo(to);
        for (double d = 0; d < len; d += 0.5) {
            Vec3 p = from.add(dir.scale(d));
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
            if (((int) (d * 2)) % 3 == 0) {
                level.sendParticles(ParticleTypes.WITCH, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
        level.playSound(null, this, SoundEvents.SHULKER_SHOOT, SoundSource.HOSTILE, 1.4F, 0.6F);
        level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 0.8F, 1.6F);
        if (t == null || !t.isAlive()) {
            return;
        }
        Optional<Vec3> hit = t.getBoundingBox().inflate(0.3).clip(from, to);
        if (hit.isPresent()) {
            if (t.hurtServer(level, damageSources().indirectMagic(this, this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                Vec3 pull = position().subtract(t.position()).multiply(1, 0, 1);
                double d = pull.length();
                if (d > 0.1) {
                    pull = pull.scale(Math.min(1.6, 0.35 + d * 0.12) / d);
                    t.setDeltaMovement(t.getDeltaMovement().add(pull.x, 0.35, pull.z));
                    t.hurtMarked = true;
                }
            }
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(4) == 0) {
            level().addParticle(ParticleTypes.PORTAL, getRandomX(0.6), getY() + random.nextDouble() * 2.0, getRandomZ(0.6),
                    (random.nextDouble() - 0.5) * 0.4, -0.2, (random.nextDouble() - 0.5) * 0.4);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.AMETHYST_BLOCK_CHIME;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SHULKER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SHULKER_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.8F;
    }

    /** Keep a distance, charge the tether beam, shove the close ones, blink when cornered. */
    static final class SentinelGoal extends Goal {
        private final RiftSentinel s;
        private float orbit;

        SentinelGoal(RiftSentinel s) {
            this.s = s;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = s.getTarget();
            return t != null && t.isAlive() || s.blinkQueued;
        }

        @Override
        public boolean canContinueToUse() {
            return s.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            s.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(s.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = s.getTarget();
            if (s.blinkQueued && s.action != MobAnims.RiftSentinel.BLINK) {
                s.blinkQueued = false;
                s.begin(MobAnims.RiftSentinel.BLINK);
                return;
            }
            if (s.action >= 0) {
                int a = s.action;
                int k = s.step();
                s.getNavigation().stop();
                s.setDeltaMovement(s.getDeltaMovement().scale(0.6));
                if (a == MobAnims.RiftSentinel.BLINK && k == BLINK_AT) {
                    s.blink(level);
                } else if (a == MobAnims.RiftSentinel.CHARGE) {
                    if (t != null && k <= AIM_LOCK) {
                        s.aim = t.position().add(0, t.getBbHeight() * 0.55, 0);
                        s.getLookControl().setLookAt(t, 60.0F, 60.0F);
                    }
                    if (k < FIRE && k % 2 == 0) {
                        // the telegraph: a dotted line of light toward the (locked) aim
                        Vec3 from = s.eye();
                        Vec3 dir = s.aim.subtract(from);
                        double len = Math.min(18.0, dir.length());
                        dir = dir.normalize();
                        for (double d = 1.0; d < len; d += 1.5) {
                            Vec3 p = from.add(dir.scale(d));
                            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
                        }
                    }
                    if (k == FIRE) {
                        s.fireBeam(level, t);
                    }
                } else if (a == MobAnims.RiftSentinel.SHOVE && k == SHOVE_HIT && t != null && t.isAlive()
                        && s.distanceToSqr(t) <= 3.2 * 3.2) {
                    if (s.doHurtTarget(level, t)) {
                        Vec3 push = s.toward(t).scale(1.4);
                        t.push(push.x, 0.4, push.z);
                        t.hurtMarked = true;
                    }
                    level.playSound(null, s, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.HOSTILE, 1.2F, 0.6F);
                }
                return;
            }
            if (t == null || !t.isAlive()) {
                return;
            }
            s.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(s.distanceToSqr(t));
            boolean sees = s.getSensing().hasLineOfSight(t);
            if (dist <= 2.5 && s.shoveCooldown == 0) {
                s.shoveCooldown = 40;
                s.begin(MobAnims.RiftSentinel.SHOVE);
                return;
            }
            if (dist <= 18.0 && sees && s.beamCooldown == 0) {
                s.beamCooldown = 80;
                s.aim = t.position().add(0, t.getBbHeight() * 0.55, 0);
                s.begin(MobAnims.RiftSentinel.CHARGE);
                level.playSound(null, s, SoundEvents.GUARDIAN_ATTACK, SoundSource.HOSTILE, 1.0F, 1.5F);
                return;
            }
            if (s.tickCount % 15 == 0 || s.getNavigation().isDone()) {
                orbit += 0.3F;
                double r = dist > 14.0 || !sees ? 4.0 : 9.0;
                s.getNavigation().moveTo(t.getX() + Mth.cos(orbit) * r, t.getY() + 2.5, t.getZ() + Mth.sin(orbit) * r, 1.0);
            }
        }
    }
}
