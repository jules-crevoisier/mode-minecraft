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
 * Sentinelle de magma (Magma-forged Sentry): the halberdier of the Caldera Ringwall (model
 * tools/wf/mobs/magma_sentry.py). It keeps its prey at the end of its halberd.
 * <ul>
 *     <li><b>Reach thrust</b> (2.5 to 4.5 blocks, every 3 s): the halberd levelled and drawn back while a line of
 *     smoke marks its aim (locked at 10 ticks), lands at 15 ticks: hits along a 4.8-block line, 1.3x damage, sets on
 *     fire. Step out of the line.</li>
 *     <li><b>Fissure slam</b> (3 to 8 blocks, every 7 s): the halberd raised over the helm, the aim locked at 14
 *     ticks, lands at 20 ticks: a line of fire runs 8 blocks along the ground from the blade, one block per tick,
 *     burning whoever stands on it.</li>
 *     <li><b>Haft shove</b> (within 2.5 blocks, every 2.5 s): a quick butt-stroke at 6 ticks that throws the prey back
 *     to halberd range; otherwise it steps back to keep its distance.</li>
 *     <li>Immune to fire, hard to knock back, slow.</li>
 * </ul>
 */
public class MagmaSentry extends ActionMonster {
    public static final float WIDTH = 0.8F;
    public static final float HEIGHT = 2.4F;
    private static final int THRUST_LOCK = 10;
    private static final int THRUST_HIT = 15;   // 0.75 s, matches magma_sentry.py
    private static final int SLAM_LOCK = 14;
    private static final int SLAM_HIT = 20;     // 1.0 s
    private static final int SHOVE_HIT = 6;     // 0.3 s
    private static final int FISSURE_LEN = 8;

    private int thrustCooldown = 30;
    private int slamCooldown = 80;
    private int shoveCooldown;
    private Vec3 aim = Vec3.ZERO;
    /** The running fissure: origin, direction, next step (-1: none) and who it already burnt. */
    private Vec3 fissureFrom = Vec3.ZERO;
    private Vec3 fissureDir = Vec3.ZERO;
    private int fissureStep = -1;
    private final Set<Integer> fissureHit = new HashSet<>();

    public MagmaSentry(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 12;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.21)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new SentryGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MagmaSentry.TICKS;
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    private void faceDir(Vec3 d) {
        float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90.0F;
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
    }

    // ------------------------------------------------------------------ the fissure

    private void tickFissure(ServerLevel level) {
        if (fissureStep < 0) {
            return;
        }
        if (fissureStep >= FISSURE_LEN) {
            fissureStep = -1;
            fissureHit.clear();
            return;
        }
        Vec3 p = fissureFrom.add(fissureDir.scale(1.5 + fissureStep));
        // follow the ground a little: up or down one block
        BlockPos bp = BlockPos.containing(p.x, p.y + 0.5, p.z);
        if (level.getBlockState(bp).isSolid()) {
            p = p.add(0, 1, 0);
        } else if (!level.getBlockState(bp.below()).isSolid()) {
            p = p.add(0, -1, 0);
        }
        fissureFrom = new Vec3(fissureFrom.x, p.y, fissureFrom.z);
        level.sendParticles(ParticleTypes.LAVA, p.x, p.y + 0.1, p.z, 3, 0.3, 0.05, 0.3, 0.0);
        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.2, p.z, 10, 0.35, 0.3, 0.35, 0.03);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y + 0.4, p.z, 2, 0.2, 0.2, 0.2, 0.01);
        if (fissureStep % 2 == 0) {
            level.playSound(null, p.x, p.y, p.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.6F, 0.6F + fissureStep * 0.05F);
        }
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new net.minecraft.world.phys.AABB(
                p.x - 0.9, p.y - 0.5, p.z - 0.9, p.x + 0.9, p.y + 1.6, p.z + 0.9),
                e -> e != this && e.isAlive() && !(e instanceof MagmaSentry))) {
            if (fissureHit.add(e.getId()) && e.hurtServer(level, damageSources().onFire(), 6.0F)) {
                e.setRemainingFireTicks(Math.max(e.getRemainingFireTicks(), 80));
                e.push(0, 0.35, 0);
                e.hurtMarked = true;
            }
        }
        fissureStep++;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (thrustCooldown > 0) {
            thrustCooldown--;
        }
        if (slamCooldown > 0) {
            slamCooldown--;
        }
        if (shoveCooldown > 0) {
            shoveCooldown--;
        }
        tickFissure(level);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(4) == 0) {
            // sparks breathing out of the shoulder chimneys
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            double sx = Mth.cos(yaw) * 0.38;
            double sz = Mth.sin(yaw) * 0.38;
            double side = random.nextBoolean() ? 1 : -1;
            level().addParticle(random.nextInt(3) == 0 ? ParticleTypes.FLAME : ParticleTypes.SMOKE,
                    getX() + sx * side, getY() + 2.45, getZ() + sz * side, 0, 0.05, 0);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.BLAZE_BURN;
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
        playSound(SoundEvents.NETHERITE_BLOCK_STEP, 0.6F, 0.6F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.8F;
    }

    /** Keep the prey at halberd range: thrust, slam a line of fire, shove away the ones that get too close. */
    static final class SentryGoal extends Goal {
        private final MagmaSentry s;
        private int repath;

        SentryGoal(MagmaSentry s) {
            this.s = s;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = s.getTarget();
            return t != null && t.isAlive();
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
            if (s.action >= 0) {
                int a = s.action;
                int k = s.step();
                s.getNavigation().stop();
                if (a == MobAnims.MagmaSentry.THRUST) {
                    thrust(level, t, k);
                } else if (a == MobAnims.MagmaSentry.SLAM) {
                    slam(level, t, k);
                } else if (a == MobAnims.MagmaSentry.SHOVE && k == SHOVE_HIT && t != null && t.isAlive()
                        && s.distanceToSqr(t) <= 2.9 * 2.9) {
                    float dmg = (float) s.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.6F;
                    if (t.hurtServer(level, s.damageSources().mobAttack(s), dmg)) {
                        Vec3 push = s.toward(t).scale(1.6);
                        t.push(push.x, 0.3, push.z);
                        t.hurtMarked = true;
                    }
                    level.playSound(null, s, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.4F);
                }
                return;
            }
            if (t == null) {
                return;
            }
            s.getLookControl().setLookAt(t, 20.0F, 30.0F);
            double dist = Math.sqrt(s.distanceToSqr(t));
            boolean sees = s.getSensing().hasLineOfSight(t);
            if (dist <= 2.5) {
                if (s.shoveCooldown == 0) {
                    s.shoveCooldown = 50;
                    s.begin(MobAnims.MagmaSentry.SHOVE);
                    return;
                }
                // step back to halberd range
                Vec3 away = s.position().subtract(t.position()).multiply(1, 0, 1).normalize().scale(3.0);
                if (--repath <= 0) {
                    repath = 10;
                    s.getNavigation().moveTo(s.getX() + away.x, s.getY(), s.getZ() + away.z, 1.0);
                }
                return;
            }
            if (sees && dist <= 4.5 && s.thrustCooldown == 0) {
                s.thrustCooldown = 60;
                s.aim = t.position();
                s.begin(MobAnims.MagmaSentry.THRUST);
                level.playSound(null, s, SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.HOSTILE, 1.2F, 0.6F);
                return;
            }
            if (sees && dist >= 3.0 && dist <= 8.0 && s.slamCooldown == 0 && Math.abs(t.getY() - s.getY()) < 2.0) {
                s.slamCooldown = 140;
                s.aim = t.position();
                s.begin(MobAnims.MagmaSentry.SLAM);
                level.playSound(null, s, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.0F, 0.5F);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                if (dist > 4.0) {
                    s.getNavigation().moveTo(t, 1.0);
                } else {
                    s.getNavigation().stop();
                }
            }
        }

        /** Telegraph a dotted line of smoke toward the aim while it can still turn, then strike along it. */
        private void aimLine(ServerLevel level, double len) {
            Vec3 dir = s.aim.subtract(s.position()).multiply(1, 0, 1);
            if (dir.lengthSqr() < 1.0E-4) {
                return;
            }
            dir = dir.normalize();
            for (double d = 1.0; d <= len; d += 1.0) {
                Vec3 p = s.position().add(dir.scale(d));
                level.sendParticles(ParticleTypes.SMOKE, p.x, p.y + 0.15, p.z, 1, 0.05, 0.02, 0.05, 0.0);
            }
        }

        private void thrust(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (t != null && k <= THRUST_LOCK) {
                s.aim = t.position();
            }
            Vec3 dir = s.aim.subtract(s.position()).multiply(1, 0, 1);
            if (dir.lengthSqr() > 1.0E-4) {
                s.faceDir(dir.normalize());
            }
            if (k < THRUST_HIT && k % 3 == 0) {
                aimLine(level, 4.8);
            }
            if (k != THRUST_HIT) {
                return;
            }
            level.playSound(null, s, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 1.2F, 0.6F);
            Vec3 d = s.forward();
            for (double x = 1.0; x <= 4.8; x += 0.5) {
                Vec3 p = s.position().add(d.scale(x));
                level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.4, p.z, 1, 0.02, 0.02, 0.02, 0.0);
            }
            float dmg = (float) s.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.3F;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, s.getBoundingBox().inflate(5.0, 1.0, 5.0),
                    e -> e != s && e.isAlive() && !(e instanceof MagmaSentry))) {
                Vec3 to = e.position().subtract(s.position());
                double along = to.x * d.x + to.z * d.z;
                double across = Math.abs(to.x * d.z - to.z * d.x);
                if (along > 0.3 && along <= 4.8 + e.getBbWidth() / 2 && across <= 0.6 + e.getBbWidth() / 2
                        && Math.abs(to.y) < 2.2 && e.hurtServer(level, s.damageSources().mobAttack(s), dmg)) {
                    e.setRemainingFireTicks(Math.max(e.getRemainingFireTicks(), 60));
                    e.push(d.x * 0.6, 0.15, d.z * 0.6);
                    e.hurtMarked = true;
                }
            }
        }

        private void slam(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (t != null && k <= SLAM_LOCK) {
                s.aim = t.position();
            }
            Vec3 dir = s.aim.subtract(s.position()).multiply(1, 0, 1);
            if (dir.lengthSqr() > 1.0E-4) {
                s.faceDir(dir.normalize());
            }
            if (k > 4 && k < SLAM_HIT && k % 3 == 0) {
                aimLine(level, FISSURE_LEN + 1.5);
            }
            if (k == SLAM_HIT) {
                level.playSound(null, s, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.7F, 1.4F);
                Vec3 d = s.forward();
                Vec3 hit = s.position().add(d.scale(1.5));
                level.sendParticles(ParticleTypes.LAVA, hit.x, hit.y + 0.2, hit.z, 8, 0.4, 0.1, 0.4, 0.0);
                s.fissureFrom = s.position();
                s.fissureDir = d;
                s.fissureStep = 0;
                s.fissureHit.clear();
            }
        }
    }
}
