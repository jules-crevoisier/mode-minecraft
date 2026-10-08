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
import net.minecraft.world.entity.Entity;
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
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Acolyte du vide (Void Acolyte): the masked cultist of the Shattered Halo (model tools/wf/mobs/void_acolyte.py).
 * <ul>
 *     <li><b>Void orb</b> (3 to 16 blocks, line of sight, every 2.5 s): the orb drawn to the chest and fed while it
 *     swells, thrown at 14 ticks: a slow glowing orb (0.4 block per tick) that bends after its prey for 4 s; it bursts
 *     on blocks; on a hit, 5 magic damage and the prey floats up for 1.5 s. Dodge sideways or put a block in its way.</li>
 *     <li><b>Blink</b> (a short teleport, 4 to 6 blocks): to flank its prey every 6 s, or to escape when cornered. The
 *     spot it will land on flickers with portal sparks for 9 ticks first, then it folds away and unfolds there.</li>
 *     <li><b>Dagger stab</b> (within 2.3 blocks, every 1.5 s): lands at 6 ticks.</li>
 *     <li>Keeps 5 to 9 blocks from its prey.</li>
 * </ul>
 */
public class VoidAcolyte extends ActionMonster {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.9F;
    private static final int CAST_THROW = 14;    // 0.7 s, matches void_acolyte.py
    private static final int BLINK_AT = 9;       // 0.45 s
    private static final int STAB_HIT = 6;       // 0.3 s
    private static final double ORB_SPEED = 0.4;

    /** A flying orb: position, velocity, ticks left, the prey it bends after. */
    private static final class Orb {
        Vec3 p;
        Vec3 v;
        int life = 80;
        final int target;

        Orb(Vec3 p, Vec3 v, int target) {
            this.p = p;
            this.v = v;
            this.target = target;
        }
    }

    private final List<Orb> orbs = new ArrayList<>();
    private int castCooldown = 30;
    private int blinkCooldown = 60;
    private int stabCooldown;
    private @Nullable Vec3 blinkTo;

    public VoidAcolyte(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 9;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new AcolyteGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.VoidAcolyte.TICKS;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    // ------------------------------------------------------------------ orbs

    private Vec3 palm() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 fwd = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
        Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
        return position().add(fwd.scale(0.6)).add(left.scale(0.35)).add(0, 1.3, 0);
    }

    private void tickOrbs(ServerLevel level) {
        for (int i = orbs.size() - 1; i >= 0; i--) {
            Orb o = orbs.get(i);
            if (--o.life <= 0) {
                burst(level, o.p);
                orbs.remove(i);
                continue;
            }
            Entity t = level.getEntity(o.target);
            if (t instanceof LivingEntity le && le.isAlive()) {
                // bends gently after its prey
                Vec3 want = le.position().add(0, le.getBbHeight() * 0.5, 0).subtract(o.p).normalize().scale(ORB_SPEED);
                o.v = o.v.scale(0.9).add(want.scale(0.1)).normalize().scale(ORB_SPEED);
            }
            Vec3 next = o.p.add(o.v);
            if (!level.getBlockState(BlockPos.containing(next)).getCollisionShape(level, BlockPos.containing(next)).isEmpty()) {
                burst(level, o.p);
                orbs.remove(i);
                continue;
            }
            o.p = next;
            level.sendParticles(ParticleTypes.END_ROD, o.p.x, o.p.y, o.p.z, 1, 0.05, 0.05, 0.05, 0.0);
            level.sendParticles(ParticleTypes.WITCH, o.p.x, o.p.y, o.p.z, 2, 0.12, 0.12, 0.12, 0.0);
            if (o.life % 6 == 0) {
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, o.p.x, o.p.y, o.p.z, 3, 0.1, 0.1, 0.1, 0.02);
            }
            AABB box = new AABB(o.p.x - 0.35, o.p.y - 0.35, o.p.z - 0.35, o.p.x + 0.35, o.p.y + 0.35, o.p.z + 0.35);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box.inflate(0.3),
                    e -> e != this && e.isAlive() && !(e instanceof VoidAcolyte))) {
                if (e.getBoundingBox().intersects(box)) {
                    if (e.hurtServer(level, damageSources().indirectMagic(this, this), 5.0F)) {
                        e.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 30, 0), this);
                    }
                    burst(level, o.p);
                    orbs.remove(i);
                    break;
                }
            }
        }
    }

    private void burst(ServerLevel level, Vec3 p) {
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y, p.z, 16, 0.2, 0.2, 0.2, 0.08);
        level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 4, 0.1, 0.1, 0.1, 0.05);
        level.playSound(null, p.x, p.y, p.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 0.8F, 1.3F);
    }

    // ------------------------------------------------------------------ blink

    /** A free, standable spot about ``dist`` blocks from ``around`` at angle ``ang`` (radians), or null. */
    private @Nullable Vec3 standable(ServerLevel level, Vec3 around, double ang, double dist) {
        double x = around.x + Math.cos(ang) * dist;
        double z = around.z + Math.sin(ang) * dist;
        for (int dy = 2; dy >= -3; dy--) {
            Vec3 p = new Vec3(x, Math.floor(around.y) + dy, z);
            BlockPos below = BlockPos.containing(p).below();
            if (level.getBlockState(below).isFaceSturdy(level, below, net.minecraft.core.Direction.UP)
                    && level.noCollision(this, getDimensions(getPose()).makeBoundingBox(p))) {
                return p;
            }
        }
        return null;
    }

    private boolean planBlink(ServerLevel level, LivingEntity t, boolean escape) {
        Vec3 rel = position().subtract(t.position());
        double base = Math.atan2(rel.z, rel.x);
        double[] offsets = escape ? new double[] {0.0, 0.6, -0.6, 1.2, -1.2}
                : (random.nextBoolean() ? new double[] {1.5, -1.5, 1.0, -1.0} : new double[] {-1.5, 1.5, -1.0, 1.0});
        for (double off : offsets) {
            Vec3 p = standable(level, escape ? position() : t.position(), base + off, escape ? 5.5 : 5.0);
            if (p != null) {
                blinkTo = p;
                return true;
            }
        }
        return false;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (castCooldown > 0) {
            castCooldown--;
        }
        if (blinkCooldown > 0) {
            blinkCooldown--;
        }
        if (stabCooldown > 0) {
            stabCooldown--;
        }
        tickOrbs(level);
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        orbs.clear();
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(3) == 0) {
            level().addParticle(ParticleTypes.PORTAL, getRandomX(0.6), getY() + random.nextDouble() * 1.9, getRandomZ(0.6),
                    (random.nextDouble() - 0.5) * 0.4, -0.1, (random.nextDouble() - 0.5) * 0.4);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.ILLUSIONER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.ILLUSIONER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.ILLUSIONER_DEATH;
    }

    /** Keep the distance, throw orbs, blink to the flank (or away), stab the ones who corner it. */
    static final class AcolyteGoal extends Goal {
        private final VoidAcolyte c;
        private int repath;

        AcolyteGoal(VoidAcolyte c) {
            this.c = c;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = c.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return c.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            c.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(c.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = c.getTarget();
            if (c.action >= 0) {
                int a = c.action;
                int k = c.step();
                c.getNavigation().stop();
                if (t != null && a != MobAnims.VoidAcolyte.BLINK) {
                    c.getLookControl().setLookAt(t, 40.0F, 40.0F);
                }
                if (a == MobAnims.VoidAcolyte.CAST) {
                    Vec3 palm = c.palm();
                    if (k < CAST_THROW && k % 2 == 0) {
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, palm.x, palm.y, palm.z, 3, 0.4, 0.4, 0.4, 0.0);
                    }
                    if (k == CAST_THROW && t != null) {
                        Vec3 v = t.position().add(0, t.getBbHeight() * 0.5, 0).subtract(palm).normalize().scale(ORB_SPEED);
                        c.orbs.add(new Orb(palm, v, t.getId()));
                        level.playSound(null, c, SoundEvents.EVOKER_CAST_SPELL, SoundSource.HOSTILE, 1.0F, 1.4F);
                    }
                } else if (a == MobAnims.VoidAcolyte.BLINK && c.blinkTo != null) {
                    Vec3 p = c.blinkTo;
                    // the telegraph: the arrival spot flickers
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 0.9, p.z, 6, 0.2, 0.7, 0.2, 0.01);
                    level.sendParticles(ParticleTypes.WITCH, p.x, p.y + 0.1, p.z, 2, 0.3, 0.02, 0.3, 0.0);
                    if (k == BLINK_AT) {
                        Vec3 from = c.position();
                        c.teleportTo(p.x, p.y, p.z);
                        c.blinkTo = null;
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, from.x, from.y + 1.0, from.z, 24, 0.3, 0.7, 0.3, 0.05);
                        level.playSound(null, from.x, from.y, from.z, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 0.8F, 1.4F);
                        c.begin(MobAnims.VoidAcolyte.REFORM);
                    }
                } else if (a == MobAnims.VoidAcolyte.STAB && k == STAB_HIT && t != null && t.isAlive()
                        && c.distanceToSqr(t) <= 2.7 * 2.7) {
                    if (c.doHurtTarget(level, t)) {
                        Vec3 push = c.toward(t).scale(0.4);
                        t.push(push.x, 0.1, push.z);
                        t.hurtMarked = true;
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            c.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(c.distanceToSqr(t));
            boolean sees = c.getSensing().hasLineOfSight(t);
            if (dist < 3.0) {
                if (c.blinkCooldown == 0 && c.random.nextInt(2) == 0 && c.planBlink(level, t, true)) {
                    c.blinkCooldown = 120;
                    c.begin(MobAnims.VoidAcolyte.BLINK);
                    level.playSound(null, c, SoundEvents.ENDERMAN_AMBIENT, SoundSource.HOSTILE, 0.6F, 1.6F);
                    return;
                }
                if (dist <= 2.3 && c.stabCooldown == 0) {
                    c.stabCooldown = 30;
                    c.begin(MobAnims.VoidAcolyte.STAB);
                    return;
                }
            }
            if (sees && dist >= 3.0 && dist <= 16.0 && c.castCooldown == 0) {
                c.castCooldown = 50;
                c.begin(MobAnims.VoidAcolyte.CAST);
                level.playSound(null, c, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 0.8F, 1.6F);
                return;
            }
            if (dist >= 4.0 && dist <= 10.0 && c.blinkCooldown == 0 && c.random.nextInt(20) == 0 && c.planBlink(level, t, false)) {
                c.blinkCooldown = 120;
                c.begin(MobAnims.VoidAcolyte.BLINK);
                level.playSound(null, c, SoundEvents.ENDERMAN_AMBIENT, SoundSource.HOSTILE, 0.6F, 1.6F);
                return;
            }
            if (--repath <= 0) {
                repath = 12;
                if (dist > 9.0 || !sees) {
                    c.getNavigation().moveTo(t, 1.0);
                } else if (dist < 5.0) {
                    Vec3 away = c.position().subtract(t.position()).multiply(1, 0, 1).normalize().scale(4.0);
                    c.getNavigation().moveTo(c.getX() + away.x, c.getY(), c.getZ() + away.z, 1.1);
                } else {
                    c.getNavigation().stop();
                }
            }
        }
    }
}
