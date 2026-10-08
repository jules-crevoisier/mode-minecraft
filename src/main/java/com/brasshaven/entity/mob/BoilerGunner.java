package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
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

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Canonnier-chaudière (Boiler Gunner): the walking gun of the Walking Fortress Wreck (model tools/wf/mobs/boiler_gunner.py).
 * Slow and heavy; it keeps its distance and shells its prey.
 * <ul>
 *     <li><b>Flak shot</b> (6 to 20 blocks, in sight, every 4 s): plants its feet and raises the cannon while the gauge
 *     on its head climbs into the red and a trail of smoke runs from the muzzle to the spot it aims at (the prey's
 *     feet). The aim <b>locks at 15 ticks</b>, the shot goes off at 20: the shell flies to the locked spot (or the
 *     first block or creature in the way) and bursts in a cloud of flak: damage within 2.5 blocks, falling off with
 *     distance, no harm to blocks. Keep moving.</li>
 *     <li><b>Firebox belch</b> (within 3.5 blocks, every 6 s): leans in and swings its firebox door open (12 ticks),
 *     then a gout of fire in a cone in front of it for 8 ticks: sets everything in it on fire.</li>
 *     <li><b>Stomp</b> (within 2.5 blocks, every 5 s): lifts a foot high, stamps at 14 ticks: a shockwave that hurts and
 *     throws back everything within 3 blocks.</li>
 * </ul>
 */
public class BoilerGunner extends ActionMonster {
    public static final float WIDTH = 1.0F;
    public static final float HEIGHT = 2.3F;
    private static final int FLAK_LOCK = 15;
    private static final int FLAK_FIRE = 20;     // 1.0 s, matches boiler_gunner.py
    private static final int BELCH_START = 12;   // 0.6 s
    private static final int BELCH_END = 20;     // 1.0 s
    private static final int STOMP_HIT = 14;     // 0.7 s
    private static final double SHELL_SPEED = 1.1;

    private static final class Shell {
        Vec3 p;
        final Vec3 to;
        int life;

        Shell(Vec3 p, Vec3 to) {
            this.p = p;
            this.to = to;
            this.life = 40;
        }
    }

    private final List<Shell> shells = new ArrayList<>();
    private int flakCooldown = 40;
    private int belchCooldown = 40;
    private int stompCooldown = 40;
    private Vec3 aim = Vec3.ZERO;

    public BoilerGunner(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 12;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 44.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.17)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new GunnerGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 16.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BoilerGunner.TICKS;
    }

    @Override
    public boolean fireImmune() {
        return true;
    }

    @Override
    protected int decreaseAirSupply(int currentSupply) {
        return currentSupply;                                               // a boiler, not lungs
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** The cannon's muzzle (right shoulder, forward). */
    private Vec3 muzzle() {
        Vec3 fwd = forward();
        Vec3 right = new Vec3(-fwd.z, 0, fwd.x);
        return position().add(fwd.scale(1.0)).add(right.scale(0.55)).add(0, 1.5, 0);
    }

    // ------------------------------------------------------------------ shells

    private void tickShells(ServerLevel level) {
        for (int i = shells.size() - 1; i >= 0; i--) {
            Shell s = shells.get(i);
            Vec3 d = s.to.subtract(s.p);
            boolean arrive = d.length() <= SHELL_SPEED || --s.life <= 0;
            Vec3 next = arrive ? s.to : s.p.add(d.normalize().scale(SHELL_SPEED));
            HitResult hit = level.clip(new ClipContext(s.p, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
            if (hit.getType() != HitResult.Type.MISS) {
                next = hit.getLocation();
                arrive = true;
            }
            AABB sweep = new AABB(s.p, next).inflate(0.4);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, sweep,
                    e -> e != this && e.isAlive() && !(e instanceof BoilerGunner))) {
                if (e.getBoundingBox().inflate(0.3).clip(s.p, next).isPresent()) {
                    arrive = true;
                    break;
                }
            }
            s.p = next;
            level.sendParticles(ParticleTypes.LARGE_SMOKE, s.p.x, s.p.y, s.p.z, 1, 0.02, 0.02, 0.02, 0.0);
            level.sendParticles(ParticleTypes.SMALL_FLAME, s.p.x, s.p.y, s.p.z, 1, 0.02, 0.02, 0.02, 0.0);
            if (arrive) {
                burst(level, s.p);
                shells.remove(i);
            }
        }
    }

    private void burst(ServerLevel level, Vec3 p) {
        level.playSound(null, p.x, p.y, p.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.6F);
        level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y, p.z, 14, 0.8, 0.5, 0.8, 0.03);
        level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 24, 1.0, 0.6, 1.0, 0.4);
        level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y, p.z, 10, 0.6, 0.4, 0.6, 0.05);
        float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.2F;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(2.5),
                e -> e != this && e.isAlive() && !(e instanceof BoilerGunner))) {
            double d = e.position().add(0, e.getBbHeight() * 0.5, 0).distanceTo(p);
            if (d > 2.6) {
                continue;
            }
            if (e.hurtServer(level, damageSources().mobProjectile(this, this), (float) (dmg * (1.0 - d / 4.0)))) {
                Vec3 push = e.position().subtract(p).multiply(1, 0, 1);
                push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(0.5);
                e.push(push.x, 0.25, push.z);
                e.hurtMarked = true;
            }
        }
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (flakCooldown > 0) {
            flakCooldown--;
        }
        if (belchCooldown > 0) {
            belchCooldown--;
        }
        if (stompCooldown > 0) {
            stompCooldown--;
        }
        tickShells(level);
        if (tickCount % 20 == 0) {
            Vec3 b = position().add(forward().scale(-0.35));
            level.sendParticles(ParticleTypes.SMOKE, b.x, b.y + 2.4, b.z, 2, 0.05, 0.05, 0.05, 0.01);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.FURNACE_FIRE_CRACKLE;
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
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.9F, 0.6F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.7F;
    }

    /** Keep the prey at gun range; belch and stomp when it closes in. */
    static final class GunnerGoal extends Goal {
        private final BoilerGunner g;
        private int repath;

        GunnerGoal(BoilerGunner g) {
            this.g = g;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = g.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return g.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            g.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(g.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = g.getTarget();
            if (g.action >= 0) {
                int a = g.action;
                int k = g.step();
                g.getNavigation().stop();
                if (a == MobAnims.BoilerGunner.FLAK) {
                    flak(level, t, k);
                } else if (a == MobAnims.BoilerGunner.BELCH) {
                    if (k > 0 && k < BELCH_START && k % 3 == 0) {
                        Vec3 p = g.position().add(g.forward().scale(0.6)).add(0, 0.6, 0);
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 2, 0.15, 0.1, 0.15, 0.01);
                    }
                    if (k == BELCH_START) {
                        level.playSound(null, g, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.2F, 0.5F);
                    }
                    if (k >= BELCH_START && k < BELCH_END) {
                        belch(level, k == BELCH_START);
                    }
                } else if (a == MobAnims.BoilerGunner.STOMP && k == STOMP_HIT) {
                    stomp(level);
                }
                return;
            }
            if (t == null) {
                return;
            }
            g.getLookControl().setLookAt(t, 15.0F, 30.0F);
            double dist = Math.sqrt(g.distanceToSqr(t));
            boolean sees = g.getSensing().hasLineOfSight(t);
            if (dist <= 2.5 && g.stompCooldown == 0) {
                g.stompCooldown = 100;
                g.belchCooldown = Math.max(g.belchCooldown, 30);
                g.begin(MobAnims.BoilerGunner.STOMP);
                return;
            }
            if (dist <= 3.5 && g.belchCooldown == 0) {
                g.belchCooldown = 120;
                g.begin(MobAnims.BoilerGunner.BELCH);
                level.playSound(null, g, SoundEvents.IRON_DOOR_OPEN, SoundSource.HOSTILE, 1.0F, 0.6F);
                return;
            }
            if (dist >= 6.0 && dist <= 20.0 && sees && g.flakCooldown == 0) {
                g.flakCooldown = 80;
                g.aim = t.position();
                g.begin(MobAnims.BoilerGunner.FLAK);
                level.playSound(null, g, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 1.0F, 0.5F);
                return;
            }
            if (--repath <= 0) {
                repath = 15;
                if (dist > 14.0 || !sees) {
                    g.getNavigation().moveTo(t, 1.0);
                } else {
                    g.getNavigation().stop();                               // in range: hold position and shoot
                }
            }
        }

        private void flak(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                return;
            }
            if (k <= FLAK_LOCK && t != null && t.isAlive()) {
                g.aim = t.position();
                g.getLookControl().setLookAt(t, 30.0F, 30.0F);
            }
            if (k < FLAK_FIRE) {
                // the telegraph: steam hisses and a smoke trail runs from the muzzle to the aimed spot; once locked
                // the trail turns to flame-lit sparks
                if (k % 2 == 0) {
                    Vec3 from = g.muzzle();
                    Vec3 to = g.aim.add(0, 0.2, 0);
                    Vec3 step = to.subtract(from);
                    int n = Math.max(3, (int) (step.length() * 1.5));
                    for (int i = 1; i <= n; i++) {
                        Vec3 p = from.add(step.scale(i / (double) n));
                        level.sendParticles(k > FLAK_LOCK ? ParticleTypes.SMALL_FLAME : ParticleTypes.SMOKE, p.x, p.y, p.z, 1,
                                0.0, 0.0, 0.0, 0.0);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, g.getX(), g.getY() + 2.2, g.getZ(), 1, 0.2, 0.1, 0.2, 0.02);
                }
                if (k % 5 == 0) {
                    level.playSound(null, g, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 0.4F, 1.2F + k * 0.04F);
                }
                if (k == FLAK_LOCK) {
                    level.playSound(null, g, SoundEvents.IRON_TRAPDOOR_CLOSE, SoundSource.HOSTILE, 1.0F, 1.4F);
                }
                return;
            }
            if (k == FLAK_FIRE) {
                Vec3 from = g.muzzle();
                g.shells.add(new Shell(from, g.aim.add(0, 0.4, 0)));
                level.playSound(null, g, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.2F, 0.7F);
                level.playSound(null, g, SoundEvents.DISPENSER_LAUNCH, SoundSource.HOSTILE, 1.2F, 0.5F);
                level.sendParticles(ParticleTypes.LARGE_SMOKE, from.x, from.y, from.z, 8, 0.2, 0.2, 0.2, 0.05);
                level.sendParticles(ParticleTypes.FLAME, from.x, from.y, from.z, 6, 0.1, 0.1, 0.1, 0.05);
            }
        }

        private void belch(ServerLevel level, boolean first) {
            Vec3 fwd = g.forward();
            Vec3 base = g.position().add(fwd.scale(0.6)).add(0, 0.6, 0);
            for (int i = 0; i < 6; i++) {
                double spread = (g.random.nextDouble() - 0.5) * 0.6;
                Vec3 dir = new Vec3(fwd.x - fwd.z * spread, 0.05, fwd.z + fwd.x * spread).normalize();
                level.sendParticles(ParticleTypes.FLAME, base.x, base.y, base.z, 0, dir.x, dir.y, dir.z, 0.35);
            }
            if (first) {
                level.sendParticles(ParticleTypes.LARGE_SMOKE, base.x, base.y + 0.3, base.z, 6, 0.3, 0.2, 0.3, 0.03);
            }
            float dmg = (float) g.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.35F;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, g.getBoundingBox().inflate(3.8, 1.0, 3.8),
                    e -> e != g && e.isAlive() && !(e instanceof BoilerGunner))) {
                Vec3 to = e.position().subtract(g.position()).multiply(1, 0, 1);
                double d = to.length();
                if (d > 4.0 || (d > 0.5 && to.normalize().dot(fwd) < 0.6)) {
                    continue;
                }
                if (e.hurtServer(level, g.damageSources().onFire(), dmg)) {
                    e.igniteForSeconds(4.0F);
                }
            }
        }

        private void stomp(ServerLevel level) {
            level.playSound(null, g, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 0.5F);
            level.playSound(null, g, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.5F, 1.8F);
            BlockState under = g.getBlockStateOn();
            for (int i = 0; i < 20; i++) {
                double ang = i * Math.PI * 2 / 20;
                Vec3 p = g.position().add(Math.cos(ang) * 1.8, 0.1, Math.sin(ang) * 1.8);
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, under), p.x, p.y, p.z, 3, 0.1, 0.05, 0.1, 0.1);
            }
            level.sendParticles(ParticleTypes.POOF, g.getX(), g.getY() + 0.2, g.getZ(), 10, 1.0, 0.1, 1.0, 0.05);
            float dmg = (float) g.getAttributeValue(Attributes.ATTACK_DAMAGE);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, g.getBoundingBox().inflate(3.0, 0.5, 3.0),
                    e -> e != g && e.isAlive() && !(e instanceof BoilerGunner) && e.onGround())) {
                if (g.distanceToSqr(e) > 3.2 * 3.2) {
                    continue;
                }
                if (e.hurtServer(level, g.damageSources().mobAttack(g), dmg)) {
                    Vec3 push = g.toward(e).scale(1.1);
                    e.push(push.x, 0.45, push.z);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 1), g);
                }
            }
        }
    }
}
