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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Golem de scories (Slag Golem): the waste of the Forge of the Basalt Titan walking on its own (model
 * tools/wf/mobs/slag_golem.py). Slow, heavy, fire-proof; every blow leaves a <b>puddle of cooling slag</b> on the
 * floor: glowing and bubbling at first, then smoking as it cools, it burns whatever stands in it for 5 s (particles and
 * damage only: no block is placed).
 * <ul>
 *     <li><b>Molten haymaker</b> (within 3 blocks, every 1.6 s): drags its right fist back past its hip while it
 *     flares, lands at 12 ticks: hurts, sets on fire and knocks back; a small puddle where it lands.</li>
 *     <li><b>Double slam</b> (within 3.5 blocks, every 6 s): heaves both fists over its head, slag dripping from them,
 *     brings them down at 18 ticks: hurts and throws up everything in a wide arc in front, and leaves a wide puddle.</li>
 *     <li><b>Slag lob</b> (4 to 14 blocks, in sight, every 5 s): claws a gobbet off its shoulder and swings it back
 *     overhead; the spot it aims at (the prey's feet) smokes, the aim <b>locks at 12 ticks</b>, the gobbet flies at 16
 *     on an arc and splashes there in a puddle. Step off the smoking spot.</li>
 * </ul>
 */
public class SlagGolem extends ActionMonster {
    public static final float WIDTH = 1.3F;
    public static final float HEIGHT = 2.4F;
    private static final int PUNCH_HIT = 12;   // 0.6 s, matches slag_golem.py
    private static final int SLAM_HIT = 18;    // 0.9 s
    private static final int LOB_LOCK = 12;
    private static final int LOB_THROW = 16;   // 0.8 s
    private static final int PUDDLE_LIFE = 100;
    private static final double GRAVITY = 0.06;

    private record Puddle(Vec3 at, double radius, int[] age) {}

    private static final class Glob {
        Vec3 p;
        Vec3 v;
        int life = 60;

        Glob(Vec3 p, Vec3 v) {
            this.p = p;
            this.v = v;
        }
    }

    private final List<Puddle> puddles = new ArrayList<>();
    private final List<Glob> globs = new ArrayList<>();
    private int punchCooldown = 10;
    private int slamCooldown = 60;
    private int lobCooldown = 60;
    private Vec3 aim = Vec3.ZERO;

    public SlagGolem(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 14;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 9.0)
                .add(Attributes.MOVEMENT_SPEED, 0.18)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new SlagGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SlagGolem.TICKS;
    }

    @Override
    public boolean fireImmune() {
        return true;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ slag puddles and gobbets

    /** A puddle of slag on the floor under ``p`` (snapped down to the first solid block within 3 blocks). */
    private void puddle(ServerLevel level, Vec3 p, double radius) {
        BlockPos b = BlockPos.containing(p.x, p.y + 0.5, p.z);
        for (int i = 0; i < 4 && level.getBlockState(b.below()).getCollisionShape(level, b.below()).isEmpty(); i++) {
            b = b.below();
        }
        Vec3 at = new Vec3(p.x, b.getY() + 0.05, p.z);
        puddles.add(new Puddle(at, radius, new int[] {0}));
        level.playSound(null, at.x, at.y, at.z, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 0.8F, 0.6F);
        level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.2, at.z, 6, radius * 0.4, 0.1, radius * 0.4, 0.0);
    }

    private void tickPuddles(ServerLevel level) {
        for (int i = puddles.size() - 1; i >= 0; i--) {
            Puddle pd = puddles.get(i);
            int age = pd.age()[0]++;
            if (age >= PUDDLE_LIFE) {
                puddles.remove(i);
                continue;
            }
            boolean hot = age < PUDDLE_LIFE / 2;
            Vec3 c = pd.at();
            if (age % 3 == 0) {
                int n = (int) Math.ceil(pd.radius() * 3);
                for (int k = 0; k < n; k++) {
                    double a = random.nextDouble() * Math.PI * 2;
                    double r = Math.sqrt(random.nextDouble()) * pd.radius();
                    double x = c.x + Math.cos(a) * r;
                    double z = c.z + Math.sin(a) * r;
                    if (hot) {
                        level.sendParticles(random.nextInt(3) == 0 ? ParticleTypes.LAVA : ParticleTypes.FLAME, x, c.y + 0.05, z, 1,
                                0.0, 0.02, 0.0, 0.005);
                    } else {
                        level.sendParticles(random.nextBoolean() ? ParticleTypes.SMOKE : ParticleTypes.WHITE_ASH, x, c.y + 0.1, z, 1,
                                0.0, 0.02, 0.0, 0.01);
                    }
                }
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MAGMA_BLOCK.defaultBlockState()),
                        c.x, c.y + 0.05, c.z, hot ? 2 : 1, pd.radius() * 0.5, 0.0, pd.radius() * 0.5, 0.0);
            }
            if (age % 10 == 0) {
                if (age % 30 == 0) {
                    level.playSound(null, c.x, c.y, c.z, hot ? SoundEvents.LAVA_POP : SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE,
                            0.5F, hot ? 0.8F : 1.4F);
                }
                AABB box = new AABB(c.x - pd.radius(), c.y - 0.2, c.z - pd.radius(), c.x + pd.radius(), c.y + 0.8, c.z + pd.radius());
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e.isAlive() && !e.fireImmune())) {
                    double dx = e.getX() - c.x;
                    double dz = e.getZ() - c.z;
                    if (dx * dx + dz * dz > pd.radius() * pd.radius()) {
                        continue;
                    }
                    if (e.hurtServer(level, damageSources().hotFloor(), hot ? 3.0F : 1.5F) && hot) {
                        e.igniteForSeconds(2.0F);
                    }
                }
            }
        }
    }

    private void tickGlobs(ServerLevel level) {
        for (int i = globs.size() - 1; i >= 0; i--) {
            Glob g = globs.get(i);
            Vec3 next = g.p.add(g.v);
            g.v = g.v.add(0, -GRAVITY, 0);
            boolean land = --g.life <= 0;
            HitResult hit = level.clip(new ClipContext(g.p, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.ANY, this));
            if (hit.getType() != HitResult.Type.MISS) {
                next = hit.getLocation();
                land = true;
            }
            AABB sweep = new AABB(g.p, next).inflate(0.4);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, sweep, e -> e != this && e.isAlive() && !(e instanceof SlagGolem))) {
                if (e.getBoundingBox().inflate(0.3).clip(g.p, next).isPresent()) {
                    land = true;
                    break;
                }
            }
            g.p = next;
            level.sendParticles(ParticleTypes.FLAME, g.p.x, g.p.y, g.p.z, 2, 0.08, 0.08, 0.08, 0.0);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, g.p.x, g.p.y, g.p.z, 1, 0.05, 0.05, 0.05, 0.0);
            if (random.nextInt(3) == 0) {
                level.sendParticles(ParticleTypes.FALLING_LAVA, g.p.x, g.p.y, g.p.z, 1, 0.05, 0.05, 0.05, 0.0);
            }
            if (land) {
                splash(level, g.p);
                globs.remove(i);
            }
        }
    }

    private void splash(ServerLevel level, Vec3 p) {
        level.playSound(null, p.x, p.y, p.z, SoundEvents.GENERIC_BURN, SoundSource.HOSTILE, 1.0F, 0.6F);
        level.sendParticles(ParticleTypes.LAVA, p.x, p.y, p.z, 10, 0.6, 0.2, 0.6, 0.0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y, p.z, 8, 0.6, 0.3, 0.6, 0.02);
        float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.7F;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(1.6),
                e -> e != this && e.isAlive() && !(e instanceof SlagGolem))) {
            if (e.position().distanceTo(p) > 1.8) {
                continue;
            }
            if (e.hurtServer(level, damageSources().mobProjectile(this, this), dmg)) {
                e.igniteForSeconds(3.0F);
            }
        }
        puddle(level, p, 1.8);
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (punchCooldown > 0) {
            punchCooldown--;
        }
        if (slamCooldown > 0) {
            slamCooldown--;
        }
        if (lobCooldown > 0) {
            lobCooldown--;
        }
        tickPuddles(level);
        tickGlobs(level);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(4) == 0) {
            // slag dripping off the molten fists
            Vec3 fwd = forward();
            Vec3 side = new Vec3(-fwd.z, 0, fwd.x).scale(random.nextBoolean() ? 0.9 : -0.9);
            Vec3 p = position().add(side).add(fwd.scale(0.3));
            level().addParticle(ParticleTypes.DRIPPING_LAVA, p.x, getY() + 0.5, p.z, 0, 0, 0);
        }
    }

    // ------------------------------------------------------------------ sounds: grinding stone and hissing slag

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.LAVA_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.BASALT_BREAK;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.IRON_GOLEM_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 1.0F, 0.5F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.6F;
    }

    /** Punch and slam up close, lob slag at range. */
    static final class SlagGoal extends Goal {
        private final SlagGolem g;
        private int repath;

        SlagGoal(SlagGolem g) {
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
                if (a == MobAnims.SlagGolem.PUNCH) {
                    if (k > 0 && k < PUNCH_HIT && k % 3 == 0) {
                        Vec3 fwd = g.forward();
                        Vec3 p = g.position().add(fwd.scale(-0.5)).add(new Vec3(fwd.z, 0, -fwd.x).scale(0.9)).add(0, 0.8, 0);
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 3, 0.15, 0.15, 0.15, 0.01);
                    }
                    if (t != null && k < PUNCH_HIT) {
                        g.getLookControl().setLookAt(t, 20.0F, 30.0F);
                    }
                    if (k == PUNCH_HIT) {
                        punch(level, t);
                    }
                } else if (a == MobAnims.SlagGolem.SLAM) {
                    if (k > 2 && k < SLAM_HIT && k % 2 == 0) {
                        // the telegraph: slag dripping from both fists raised over its head
                        Vec3 fwd = g.forward();
                        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
                        for (int s = -1; s <= 1; s += 2) {
                            Vec3 p = g.position().add(side.scale(0.6 * s)).add(fwd.scale(-0.3)).add(0, 3.0, 0);
                            level.sendParticles(ParticleTypes.FALLING_LAVA, p.x, p.y, p.z, 1, 0.1, 0.05, 0.1, 0.0);
                        }
                        if (k % 6 == 0) {
                            level.playSound(null, g, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 0.8F, 0.6F);
                        }
                    }
                    if (k == SLAM_HIT) {
                        slam(level);
                    }
                } else if (a == MobAnims.SlagGolem.LOB) {
                    if (k >= 0 && k <= LOB_LOCK && t != null && t.isAlive()) {
                        g.aim = t.position();
                        g.getLookControl().setLookAt(t, 20.0F, 30.0F);
                    }
                    if (k >= 0 && k < LOB_THROW && k % 2 == 0) {
                        // the telegraph: the spot it aims at smokes and spits embers (sparks once locked)
                        for (int i = 0; i < 6; i++) {
                            double ang = i * Math.PI / 3 + k * 0.2;
                            level.sendParticles(k > LOB_LOCK ? ParticleTypes.FLAME : ParticleTypes.SMOKE, g.aim.x + Math.cos(ang) * 1.2,
                                    g.aim.y + 0.1, g.aim.z + Math.sin(ang) * 1.2, 1, 0.0, 0.02, 0.0, 0.0);
                        }
                    }
                    if (k == LOB_LOCK) {
                        level.playSound(null, g, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 1.0F, 0.6F);
                    }
                    if (k == LOB_THROW) {
                        lob(level);
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            g.getLookControl().setLookAt(t, 20.0F, 30.0F);
            double dist = Math.sqrt(g.distanceToSqr(t));
            boolean sees = g.getSensing().hasLineOfSight(t);
            if (dist <= 3.5 && g.slamCooldown == 0 && g.random.nextInt(3) == 0) {
                g.slamCooldown = 120;
                g.punchCooldown = Math.max(g.punchCooldown, 20);
                g.begin(MobAnims.SlagGolem.SLAM);
                level.playSound(null, g, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 0.7F, 0.5F);
                return;
            }
            if (dist <= 3.0 && g.punchCooldown == 0) {
                g.punchCooldown = 32;
                g.begin(MobAnims.SlagGolem.PUNCH);
                return;
            }
            if (dist >= 4.0 && dist <= 14.0 && sees && g.lobCooldown == 0) {
                g.lobCooldown = 100;
                g.aim = t.position();
                g.begin(MobAnims.SlagGolem.LOB);
                level.playSound(null, g, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 1.0F, 0.8F);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                if (dist > 2.4) {
                    g.getNavigation().moveTo(t, 1.0);
                } else {
                    g.getNavigation().stop();
                }
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(g.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.8 || to.normalize().dot(g.forward()) >= minDot;
        }

        private void punch(ServerLevel level, @Nullable LivingEntity t) {
            level.playSound(null, g, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 1.2F, 0.6F);
            Vec3 at = g.position().add(g.forward().scale(2.2));
            if (t != null && t.isAlive() && g.distanceToSqr(t) <= 3.4 * 3.4 && inFront(t, 0.3)) {
                if (t.hurtServer(level, g.damageSources().mobAttack(g), (float) g.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                    t.igniteForSeconds(3.0F);
                    Vec3 push = g.toward(t).scale(0.9);
                    t.push(push.x, 0.3, push.z);
                    t.hurtMarked = true;
                }
                at = t.position();
            }
            level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.6, at.z, 6, 0.3, 0.3, 0.3, 0.0);
            g.puddle(level, at, 1.2);
        }

        private void slam(ServerLevel level) {
            level.playSound(null, g, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 0.4F);
            level.playSound(null, g, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.6F, 1.4F);
            Vec3 fwd = g.forward();
            Vec3 at = g.position().add(fwd.scale(1.8));
            BlockState under = g.getBlockStateOn();
            for (int i = 0; i < 16; i++) {
                double ang = i * Math.PI * 2 / 16;
                Vec3 p = at.add(Math.cos(ang) * 1.6, 0.1, Math.sin(ang) * 1.6);
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, under), p.x, p.y, p.z, 3, 0.1, 0.05, 0.1, 0.1);
            }
            level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.2, at.z, 14, 1.0, 0.2, 1.0, 0.0);
            float dmg = (float) g.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.3F;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, g.getBoundingBox().inflate(3.8, 1.0, 3.8),
                    e -> e != g && e.isAlive() && !(e instanceof SlagGolem))) {
                if (g.distanceToSqr(e) > 3.9 * 3.9 || !inFront(e, -0.2)) {
                    continue;
                }
                if (e.hurtServer(level, g.damageSources().mobAttack(g), dmg)) {
                    Vec3 push = g.toward(e).scale(0.5);
                    e.push(push.x, 0.6, push.z);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), g);
                }
            }
            g.puddle(level, at, 2.2);
        }

        private void lob(ServerLevel level) {
            Vec3 fwd = g.forward();
            Vec3 from = g.position().add(fwd.scale(0.6)).add(0, 3.0, 0);
            Vec3 to = g.aim.add(0, 0.2, 0);
            Vec3 d = to.subtract(from);
            double flat = Math.sqrt(d.x * d.x + d.z * d.z);
            int ticks = Mth.clamp((int) (flat / 0.6), 10, 30);
            Vec3 v = new Vec3(d.x / ticks, (d.y + 0.5 * GRAVITY * ticks * ticks) / ticks, d.z / ticks);
            g.globs.add(new Glob(from, v));
            level.playSound(null, g, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.0F, 0.5F);
            level.sendParticles(ParticleTypes.LAVA, from.x, from.y, from.z, 4, 0.2, 0.2, 0.2, 0.0);
        }
    }
}
