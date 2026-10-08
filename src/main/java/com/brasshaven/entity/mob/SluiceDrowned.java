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
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Noyé de l'écluse (Sluice Drowned): the drowned lock-keeper of the Great Aqueduct (model tools/wf/mobs/sluice_drowned.py).
 * <ul>
 *     <li>Breathes and walks under water as well as on stone (no water path penalty, swims faster).</li>
 *     <li><b>Boat-hook cast</b> (3.5 to 7.5 blocks, in sight, every 7 s): the hook raised and whirled over his hat, water
 *     flying off it, cast at 16 ticks: a prey still in front of him and in sight is hooked, hurt a little and hauled to
 *     his feet (slowed for 2 s). Break the line of sight or sidestep during the whirl.</li>
 *     <li><b>Spike jab</b> (within 3 blocks, every 1.5 s): the pole drawn back along his arm, lands at 9 ticks.</li>
 *     <li><b>Low sweep</b> (within 3.2 blocks, every 5 s): the hook swung out wide behind him, lands at 13 ticks: hits
 *     everything in a wide arc in front and knocks it off its feet (pushed aside, heavily slowed for 2 s).</li>
 * </ul>
 */
public class SluiceDrowned extends ActionMonster {
    public static final float WIDTH = 0.65F;
    public static final float HEIGHT = 2.0F;
    private static final int JAB_HIT = 9;      // 0.45 s, matches sluice_drowned.py
    private static final int HOOK_CAST = 16;   // 0.8 s
    private static final int SWEEP_HIT = 13;   // 0.65 s

    private int jabCooldown = 10;
    private int hookCooldown = 60;
    private int sweepCooldown = 60;

    public SluiceDrowned(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 9;
        setPathfindingMalus(PathType.WATER, 0.0F);
        setPathfindingMalus(PathType.WATER_BORDER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 28.0)
                .add(Attributes.ARMOR, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new SluiceGoal(this));
        goalSelector.addGoal(5, new RandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SluiceDrowned.TICKS;
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

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (jabCooldown > 0) {
            jabCooldown--;
        }
        if (hookCooldown > 0) {
            hookCooldown--;
        }
        if (sweepCooldown > 0) {
            sweepCooldown--;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(5) == 0) {
            level().addParticle(ParticleTypes.DRIPPING_WATER, getRandomX(0.5), getY() + 1.2 + random.nextDouble() * 0.7,
                    getRandomZ(0.5), 0, 0, 0);
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
        playSound(SoundEvents.DROWNED_STEP, 0.5F, 0.8F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.85F;
    }

    /** Hook from afar, jab and sweep up close. */
    static final class SluiceGoal extends Goal {
        private final SluiceDrowned d;
        private int repath;

        SluiceGoal(SluiceDrowned d) {
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
                if (t != null && k >= 0 && k < HOOK_CAST && a == MobAnims.SluiceDrowned.HOOK) {
                    d.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (a == MobAnims.SluiceDrowned.JAB && k == JAB_HIT) {
                    level.playSound(null, d, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 0.9F, 0.8F);
                    if (t != null && t.isAlive() && d.distanceToSqr(t) <= 3.4 * 3.4 && inFront(t, 0.3)) {
                        if (t.hurtServer(level, d.damageSources().mobAttack(d), (float) d.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                            Vec3 push = d.toward(t).scale(0.5);
                            t.push(push.x, 0.1, push.z);
                            t.hurtMarked = true;
                        }
                    }
                } else if (a == MobAnims.SluiceDrowned.HOOK) {
                    if (k > 0 && k < HOOK_CAST && k % 2 == 0) {
                        // the telegraph: water flung off the whirling hook above his hat
                        double ang = k * 0.8;
                        Vec3 p = d.position().add(Math.cos(ang) * 0.9, 2.6, Math.sin(ang) * 0.9);
                        level.sendParticles(ParticleTypes.SPLASH, p.x, p.y, p.z, 4, 0.1, 0.1, 0.1, 0.05);
                        if (k % 6 == 0) {
                            level.playSound(null, d, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.5F, 1.6F);
                        }
                    }
                    if (k == HOOK_CAST) {
                        cast(level, t);
                    }
                } else if (a == MobAnims.SluiceDrowned.SWEEP && k == SWEEP_HIT) {
                    sweep(level);
                }
                return;
            }
            if (t == null) {
                return;
            }
            d.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(d.distanceToSqr(t));
            boolean sees = d.getSensing().hasLineOfSight(t);
            if (dist >= 3.5 && dist <= 7.5 && sees && d.hookCooldown == 0) {
                d.hookCooldown = 140;
                d.begin(MobAnims.SluiceDrowned.HOOK);
                level.playSound(null, d, SoundEvents.FISHING_BOBBER_THROW, SoundSource.HOSTILE, 1.0F, 0.6F);
                return;
            }
            if (dist <= 3.2 && d.sweepCooldown == 0 && d.random.nextInt(3) == 0) {
                d.sweepCooldown = 100;
                d.jabCooldown = Math.max(d.jabCooldown, 20);
                d.begin(MobAnims.SluiceDrowned.SWEEP);
                return;
            }
            if (dist <= 3.0 && d.jabCooldown == 0) {
                d.jabCooldown = 30;
                d.begin(MobAnims.SluiceDrowned.JAB);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                // keeps a pole's length away: no need to hug the prey
                if (dist > 2.6) {
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

        private void cast(ServerLevel level, @Nullable LivingEntity t) {
            level.playSound(null, d, SoundEvents.FISHING_BOBBER_THROW, SoundSource.HOSTILE, 1.2F, 0.5F);
            Vec3 from = d.position().add(0, 1.4, 0);
            if (t == null || !t.isAlive() || d.distanceToSqr(t) > 8.5 * 8.5 || !inFront(t, 0.55)
                    || !d.getSensing().hasLineOfSight(t) || t instanceof Player p && (p.isCreative() || p.isSpectator())) {
                // a miss: the hook splashes down where the prey stood
                Vec3 end = from.add(d.forward().scale(6.0));
                line(level, from, end);
                level.sendParticles(ParticleTypes.SPLASH, end.x, end.y - 1.0, end.z, 12, 0.3, 0.1, 0.3, 0.1);
                return;
            }
            Vec3 to = t.position().add(0, t.getBbHeight() * 0.5, 0);
            line(level, from, to);
            float dmg = (float) d.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.5F;
            t.hurtServer(level, d.damageSources().mobAttack(d), dmg);
            // haul: a yank that lands the prey about a block in front of him
            Vec3 pull = d.position().subtract(t.position()).multiply(1, 0, 1);
            double len = pull.length();
            if (len > 1.5) {
                Vec3 v = pull.normalize().scale(Math.min(1.7, 0.25 + len * 0.2));
                t.setDeltaMovement(v.x, 0.38, v.z);
                t.hurtMarked = true;
            }
            t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), d);
            level.playSound(null, t, SoundEvents.FISHING_BOBBER_RETRIEVE, SoundSource.HOSTILE, 1.2F, 0.7F);
            level.playSound(null, t, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 0.8F, 1.2F);
        }

        private void line(ServerLevel level, Vec3 a, Vec3 b) {
            Vec3 step = b.subtract(a);
            int n = Math.max(2, (int) (step.length() * 2));
            for (int i = 0; i <= n; i++) {
                Vec3 p = a.add(step.scale(i / (double) n));
                level.sendParticles(ParticleTypes.FISHING, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
            }
        }

        private void sweep(ServerLevel level) {
            level.playSound(null, d, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.3F, 0.6F);
            Vec3 fwd = d.forward();
            for (int i = -4; i <= 4; i++) {
                double a = i * 0.3;
                Vec3 dir = new Vec3(fwd.x * Math.cos(a) - fwd.z * Math.sin(a), 0, fwd.x * Math.sin(a) + fwd.z * Math.cos(a));
                Vec3 p = d.position().add(dir.scale(2.5));
                level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 0.3, p.z, 4, 0.2, 0.05, 0.2, 0.05);
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 0.4, p.z, 1, 0, 0, 0, 0);
            }
            float dmg = (float) d.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.8F;
            Vec3 side = new Vec3(fwd.z, 0, -fwd.x);                         // swept from his right to his left
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, d.getBoundingBox().inflate(3.5, 0.5, 3.5),
                    e -> e != d && e.isAlive() && !(e instanceof SluiceDrowned))) {
                if (d.distanceToSqr(e) > 3.6 * 3.6 || !inFront(e, -0.1)) {
                    continue;
                }
                if (e.hurtServer(level, d.damageSources().mobAttack(d), dmg)) {
                    e.push(side.x * 0.7, 0.25, side.z * 0.7);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 3), d);
                }
            }
        }
    }
}
