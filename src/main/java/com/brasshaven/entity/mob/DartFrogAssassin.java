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
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Grenouille assassine de la canopée (Canopy Dart-Frog Assassin): the poison killer of the Canopy Temple-City (model
 * tools/wf/mobs/dart_frog_assassin.py). Takes no fall damage.
 * <ul>
 *     <li><b>Platform leap</b> (prey more than 7 blocks away or 2 or more blocks above or below it, every 4 s; and now
 *     and then on its own, from platform to platform): sinks into a deep crouch for 10 ticks, then leaps on an arc to a
 *     free floor cell next to its prey; landing within 1.5 blocks of anyone hurts and poisons them.</li>
 *     <li><b>Poison tongue lash</b> (3 to 7 blocks, in sight, every 3 s): its throat sac balloons and the head rears
 *     back, the aim <b>locks at 9 ticks</b> and the tongue whips out at 12 along that line (7.5 blocks): Poison II for
 *     5 s and a little damage to the first creature it touches.</li>
 *     <li><b>Sticky slap</b> (within 2.2 blocks, every 1 s): the hand raised high, slaps down at 7 ticks: hurts and
 *     poisons briefly.</li>
 * </ul>
 */
public class DartFrogAssassin extends ActionMonster {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 1.5F;
    private static final int LASH_LOCK = 9;
    private static final int LASH_HIT = 12;      // 0.6 s, matches dart_frog_assassin.py
    private static final int LEAP_AT = 10;       // 0.5 s
    private static final int SLAP_HIT = 7;       // 0.35 s
    private static final double LASH_RANGE = 7.5;

    private int lashCooldown = 30;
    private int leapCooldown = 40;
    private int slapCooldown;
    private int idleLeap = 200;
    private boolean leaping;
    private @Nullable Vec3 landAt;
    private Vec3 aim = Vec3.ZERO;

    public DartFrogAssassin(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new FrogGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.DartFrogAssassin.TICKS;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    private Vec3 mouth() {
        return position().add(forward().scale(0.5)).add(0, 1.2, 0);
    }

    /** A free floor cell (solid below, two air cells) near ``around`` within ``r`` blocks, closest to it; or null. */
    private @Nullable Vec3 landingNear(Vec3 around, int r, double minFromSelf) {
        Level level = level();
        BlockPos c = BlockPos.containing(around);
        Vec3 best = null;
        double bestD = Double.MAX_VALUE;
        for (BlockPos p : BlockPos.betweenClosed(c.offset(-r, -3, -r), c.offset(r, 3, r))) {
            BlockPos below = p.below();
            if (level.getBlockState(below).getCollisionShape(level, below).isEmpty()
                    || !level.getBlockState(p).getCollisionShape(level, p).isEmpty()
                    || !level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()
                    || !level.getFluidState(p).isEmpty()) {
                continue;
            }
            Vec3 v = Vec3.atBottomCenterOf(p);
            if (v.distanceTo(position()) < minFromSelf) {
                continue;
            }
            double d = v.distanceToSqr(around) + random.nextDouble() * 0.5;
            if (d < bestD) {
                bestD = d;
                best = v;
            }
        }
        return best;
    }

    private void launch(Vec3 to) {
        Vec3 d = to.subtract(position());
        double flat = Math.sqrt(d.x * d.x + d.z * d.z);
        double g = 0.08;
        int ticks = Mth.clamp((int) (flat / 0.55), 8, 24);
        double vy = (d.y + 0.5 * g * ticks * ticks) / ticks;
        setDeltaMovement(d.x / ticks, Math.min(1.4, vy), d.z / ticks);
        hurtMarked = true;
        leaping = true;
        setYRot((float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90.0F);
        yBodyRot = getYRot();
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (lashCooldown > 0) {
            lashCooldown--;
        }
        if (leapCooldown > 0) {
            leapCooldown--;
        }
        if (slapCooldown > 0) {
            slapCooldown--;
        }
        if (leaping) {
            // a frog in the air keeps its arc (the move control would brake it)
            if (tickCount % 2 == 0) {
                level.sendParticles(ParticleTypes.ITEM_SLIME, getX(), getY() + 0.5, getZ(), 1, 0.1, 0.1, 0.1, 0.0);
            }
            if (onGround() && getDeltaMovement().y <= 0.0) {
                leaping = false;
                land(level);
            }
        } else if (getTarget() == null && action < 0 && onGround() && --idleLeap <= 0) {
            // now and then: a hop to another platform
            idleLeap = 160 + random.nextInt(200);
            Vec3 spot = position().add(random.nextGaussian() * 6, random.nextInt(7) - 3, random.nextGaussian() * 6);
            Vec3 to = landingNear(spot, 2, 3.0);
            if (to != null && to.distanceTo(position()) < 10.0) {
                landAt = to;
                begin(MobAnims.DartFrogAssassin.LEAP);
            }
        }
        if (action == MobAnims.DartFrogAssassin.LEAP && getTarget() == null) {
            int k = actionTick;
            if (k == LEAP_AT && landAt != null) {
                launch(landAt);
                level.playSound(null, this, SoundEvents.FROG_LONG_JUMP, SoundSource.HOSTILE, 1.0F, 0.8F);
            }
            if (step() < 0) {
                landAt = null;
            }
        }
    }

    private void land(ServerLevel level) {
        level.playSound(null, this, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.0F, 0.8F);
        level.sendParticles(ParticleTypes.ITEM_SLIME, getX(), getY() + 0.2, getZ(), 10, 0.5, 0.1, 0.5, 0.05);
        float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.2F;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(1.2, 0.8, 1.2),
                e -> e != this && e.isAlive() && !(e instanceof DartFrogAssassin))) {
            if (distanceToSqr(e) > 1.5 * 1.5 + 0.5) {
                continue;
            }
            if (e.hurtServer(level, damageSources().mobAttack(this), dmg)) {
                e.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), this);
            }
        }
    }

    // ------------------------------------------------------------------ sounds: croaks and wet slaps

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
        return SoundEvents.FROG_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.FROG_STEP, 0.4F, 0.8F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.75F;
    }

    /** Leap to its prey's level, lash from range, slap up close. */
    static final class FrogGoal extends Goal {
        private final DartFrogAssassin f;
        private int repath;

        FrogGoal(DartFrogAssassin f) {
            this.f = f;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = f.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return (f.action >= 0 && f.getTarget() != null) || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            f.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(f.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = f.getTarget();
            if (f.action >= 0) {
                int a = f.action;
                int k = f.step();
                if (!f.leaping) {
                    f.getNavigation().stop();
                }
                if (a == MobAnims.DartFrogAssassin.LASH) {
                    lash(level, t, k);
                } else if (a == MobAnims.DartFrogAssassin.LEAP) {
                    if (k >= 0 && k < LEAP_AT && k % 3 == 0) {
                        level.sendParticles(ParticleTypes.ITEM_SLIME, f.getX(), f.getY() + 0.1, f.getZ(), 2, 0.3, 0.0, 0.3, 0.0);
                    }
                    if (k == LEAP_AT) {
                        Vec3 to = t != null && t.isAlive() ? f.landingNear(t.position(), 2, 1.5) : null;
                        if (to == null) {
                            to = f.landAt;
                        }
                        if (to != null) {
                            f.launch(to);
                            level.playSound(null, f, SoundEvents.FROG_LONG_JUMP, SoundSource.HOSTILE, 1.0F, 0.8F);
                        }
                    }
                } else if (a == MobAnims.DartFrogAssassin.SLAP) {
                    if (t != null && k < SLAP_HIT) {
                        f.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    }
                    if (k == SLAP_HIT) {
                        level.playSound(null, f, SoundEvents.SLIME_ATTACK, SoundSource.HOSTILE, 1.0F, 1.0F);
                        if (t != null && t.isAlive() && f.distanceToSqr(t) <= 2.8 * 2.8 && inFront(t, 0.2) && f.doHurtTarget(level, t)) {
                            t.addEffect(new MobEffectInstance(MobEffects.POISON, 40, 0), f);
                        }
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            f.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(f.distanceToSqr(t));
            double dy = Math.abs(t.getY() - f.getY());
            boolean sees = f.getSensing().hasLineOfSight(t);
            if (f.onGround() && !f.leaping && f.leapCooldown == 0 && (dist > 7.0 || dy >= 2.0) && dist <= 16.0
                    && f.landingNear(t.position(), 2, 1.5) != null) {
                f.leapCooldown = 80;
                f.landAt = null;
                f.begin(MobAnims.DartFrogAssassin.LEAP);
                level.playSound(null, f, SoundEvents.FROG_AMBIENT, SoundSource.HOSTILE, 1.0F, 0.6F);
                return;
            }
            if (dist <= 2.2 && f.slapCooldown == 0) {
                f.slapCooldown = 20;
                f.begin(MobAnims.DartFrogAssassin.SLAP);
                return;
            }
            if (dist >= 3.0 && dist <= 7.0 && sees && f.lashCooldown == 0) {
                f.lashCooldown = 60;
                f.aim = t.getEyePosition().add(0, -0.5, 0);
                f.begin(MobAnims.DartFrogAssassin.LASH);
                level.playSound(null, f, SoundEvents.FROG_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.5F);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                f.getNavigation().moveTo(t, 1.1);
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(f.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.6 || to.normalize().dot(f.forward()) >= minDot;
        }

        private void lash(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                return;
            }
            if (k <= LASH_LOCK && t != null && t.isAlive()) {
                f.aim = t.getEyePosition().add(0, -0.5, 0);
                f.getLookControl().setLookAt(t, 30.0F, 30.0F);
            }
            if (k < LASH_HIT) {
                // the telegraph: the throat sac swelling, slime dripping from the gaping mouth
                if (k % 2 == 0) {
                    Vec3 m = f.mouth();
                    level.sendParticles(ParticleTypes.ITEM_SLIME, m.x, m.y - 0.2, m.z, 2, 0.1, 0.05, 0.1, 0.0);
                }
                if (k == LASH_LOCK) {
                    level.playSound(null, f, SoundEvents.FROG_TONGUE, SoundSource.HOSTILE, 0.6F, 0.6F);
                }
                return;
            }
            if (k == LASH_HIT) {
                level.playSound(null, f, SoundEvents.FROG_TONGUE, SoundSource.HOSTILE, 1.4F, 1.0F);
                Vec3 from = f.mouth();
                Vec3 dir = f.aim.subtract(from);
                dir = dir.lengthSqr() < 1.0E-4 ? f.forward() : dir.normalize();
                Vec3 end = from.add(dir.scale(LASH_RANGE));
                HitResult hit = level.clip(new ClipContext(from, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, f));
                if (hit.getType() != HitResult.Type.MISS) {
                    end = hit.getLocation();
                }
                LivingEntity victim = null;
                double best = Double.MAX_VALUE;
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(from, end).inflate(0.6),
                        e -> e != f && e.isAlive() && !(e instanceof DartFrogAssassin))) {
                    var clip = e.getBoundingBox().inflate(0.3).clip(from, end);
                    if (clip.isPresent() && clip.get().distanceToSqr(from) < best) {
                        best = clip.get().distanceToSqr(from);
                        victim = e;
                    }
                }
                Vec3 tip = victim != null ? from.add(dir.scale(Math.sqrt(best))) : end;
                Vec3 step = tip.subtract(from);
                int n = Math.max(3, (int) (step.length() * 3));
                for (int i = 1; i <= n; i++) {
                    Vec3 p = from.add(step.scale(i / (double) n));
                    level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
                }
                if (victim != null && victim.hurtServer(level, f.damageSources().mobAttack(f), 3.0F)) {
                    victim.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 1), f);
                    level.sendParticles(ParticleTypes.ITEM_SLIME, tip.x, tip.y, tip.z, 8, 0.2, 0.2, 0.2, 0.05);
                }
            }
        }
    }
}
