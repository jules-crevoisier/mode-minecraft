package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
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
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Moine des cloches (Bell Monk): the silent warden of Pilgrim's Ascent (model tools/wf/mobs/bell_monk.py). He fights
 * from a distance with sound.
 * <ul>
 *     <li><b>Ring of sound</b> (3 to 14 blocks, every 4.5 s): the handbell raised and held trembling, rung at 18 ticks:
 *     a ring of sound runs out along the ground from his feet (0.45 block per tick, up to 12 blocks). Whoever is
 *     standing on the ground when it passes takes 5 damage, is pushed out and slowed: <b>jump over it</b>.</li>
 *     <li><b>Bell bash</b> (within 2.4 blocks, every 1.5 s): a backhand swing of the handbell at 6 ticks: damage, a
 *     shove and a short nausea.</li>
 *     <li><b>Knell</b> (within 6 blocks, every 15 s): both hands lift the bell over the cowl and shake it harder and
 *     harder, tolled at 24 ticks: everyone within 7 blocks is blinded by darkness for 5 s, slowed and pushed back.</li>
 *     <li>Keeps 5 to 9 blocks from his prey and backs away from it.</li>
 * </ul>
 */
public class BellMonk extends ActionMonster {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.95F;
    private static final int WAVE_RING = 18;     // 0.9 s, matches bell_monk.py
    private static final int BASH_HIT = 6;       // 0.3 s
    private static final int KNELL_TOLL = 24;    // 1.2 s
    private static final double RING_SPEED = 0.45;
    private static final double RING_MAX = 12.0;

    /** A running ring of sound: centre, radius, who it already hit. */
    private static final class Ring {
        final Vec3 c;
        double r = 0.6;
        final Set<Integer> hit = new HashSet<>();

        Ring(Vec3 c) {
            this.c = c;
        }
    }

    private final List<Ring> rings = new ArrayList<>();
    private int waveCooldown = 40;
    private int bashCooldown;
    private int knellCooldown = 160;

    public BellMonk(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 9;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MonkGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BellMonk.TICKS;
    }

    // ------------------------------------------------------------------ the rings of sound

    private void tickRings(ServerLevel level) {
        for (int i = rings.size() - 1; i >= 0; i--) {
            Ring ring = rings.get(i);
            ring.r += RING_SPEED;
            if (ring.r > RING_MAX) {
                rings.remove(i);
                continue;
            }
            int n = Math.max(12, (int) (ring.r * 5));
            for (int j = 0; j < n; j++) {
                double a = (j + (tickCount % 2) * 0.5) * Mth.TWO_PI / n;
                double x = ring.c.x + Math.cos(a) * ring.r;
                double z = ring.c.z + Math.sin(a) * ring.r;
                level.sendParticles(j % 3 == 0 ? ParticleTypes.ELECTRIC_SPARK : ParticleTypes.CRIT, x, ring.c.y + 0.15, z,
                        1, 0.0, 0.02, 0.0, 0.0);
            }
            double reach = ring.r + 0.6;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(ring.c.x - reach, ring.c.y - 1.0,
                    ring.c.z - reach, ring.c.x + reach, ring.c.y + 1.2, ring.c.z + reach),
                    e -> e != this && e.isAlive() && !(e instanceof BellMonk))) {
                double dx = e.getX() - ring.c.x;
                double dz = e.getZ() - ring.c.z;
                double d = Math.sqrt(dx * dx + dz * dz);
                // the ring runs along the ground: a creature in the air (jumping) lets it pass under its feet
                if (Math.abs(d - ring.r) > 0.55 + e.getBbWidth() / 2 || e.getY() > ring.c.y + 0.6 || ring.hit.contains(e.getId())) {
                    continue;
                }
                ring.hit.add(e.getId());
                if (e.hurtServer(level, damageSources().indirectMagic(this, this), 5.0F)) {
                    if (d > 0.1) {
                        e.push(dx / d * 0.7, 0.25, dz / d * 0.7);
                        e.hurtMarked = true;
                    }
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                }
            }
        }
    }

    private void knell(ServerLevel level) {
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.sendParticles(ParticleTypes.SONIC_BOOM, getX(), getY() + 2.4, getZ(), 1, 0, 0, 0, 0);
        for (int j = 0; j < 36; j++) {
            double a = j * Mth.TWO_PI / 36;
            level.sendParticles(ParticleTypes.NOTE, getX() + Math.cos(a) * 3.5, getY() + 1.5, getZ() + Math.sin(a) * 3.5,
                    1, 0, 0, 0, 1.0);
        }
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(7.0, 3.0, 7.0),
                e -> e != this && e.isAlive() && !(e instanceof BellMonk))) {
            if (distanceToSqr(e) > 7.0 * 7.0) {
                continue;
            }
            e.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0), this);
            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 0), this);
            e.hurtServer(level, damageSources().indirectMagic(this, this), 2.0F);
            Vec3 push = toward(e).scale(1.2);
            e.push(push.x, 0.3, push.z);
            e.hurtMarked = true;
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (waveCooldown > 0) {
            waveCooldown--;
        }
        if (bashCooldown > 0) {
            bashCooldown--;
        }
        if (knellCooldown > 0) {
            knellCooldown--;
        }
        tickRings(level);
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        rings.clear();
        if (level() instanceof ServerLevel level) {
            level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.0F, 0.4F);
        }
    }

    // ------------------------------------------------------------------ sounds: silent, but his bells

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.BELL_RESONATE;
    }

    @Override
    protected float getSoundVolume() {
        return 0.3F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.BELL_BLOCK;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.ZOMBIE_VILLAGER_DEATH;
    }

    /** Keep the distance, ring rings along the ground, bash the close ones, toll the knell. */
    static final class MonkGoal extends Goal {
        private final BellMonk m;
        private int repath;

        MonkGoal(BellMonk m) {
            this.m = m;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = m.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return m.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            m.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(m.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = m.getTarget();
            if (m.action >= 0) {
                int a = m.action;
                int k = m.step();
                m.getNavigation().stop();
                if (t != null) {
                    m.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (a == MobAnims.BellMonk.WAVE) {
                    if (k > 6 && k < WAVE_RING && k % 4 == 0) {
                        level.playSound(null, m, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 0.7F, 0.5F + k * 0.04F);
                        level.sendParticles(ParticleTypes.NOTE, m.getX(), m.getY() + 2.6, m.getZ(), 1, 0.2, 0.1, 0.2, 0.5);
                    }
                    if (k == WAVE_RING) {
                        level.playSound(null, m, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0F, 1.2F);
                        m.rings.add(new Ring(m.position()));
                    }
                } else if (a == MobAnims.BellMonk.BASH && k == BASH_HIT) {
                    level.playSound(null, m, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.0F, 1.6F);
                    if (t != null && t.isAlive() && m.distanceToSqr(t) <= 2.8 * 2.8 && m.doHurtTarget(level, t)) {
                        Vec3 push = m.toward(t).scale(0.9);
                        t.push(push.x, 0.2, push.z);
                        t.hurtMarked = true;
                        t.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 80, 0), m);
                    }
                } else if (a == MobAnims.BellMonk.KNELL) {
                    if (k > 8 && k < KNELL_TOLL && k % 3 == 0) {
                        // the telegraph: the bell shaken ever harder, notes flying off it
                        level.playSound(null, m, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 1.0F, 0.5F + k * 0.03F);
                        level.sendParticles(ParticleTypes.NOTE, m.getX(), m.getY() + 2.8, m.getZ(), 2, 0.3, 0.2, 0.3, 1.0);
                    }
                    if (k == KNELL_TOLL) {
                        m.knell(level);
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            m.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(m.distanceToSqr(t));
            boolean sees = m.getSensing().hasLineOfSight(t);
            if (dist <= 2.4 && m.bashCooldown == 0) {
                m.bashCooldown = 30;
                m.begin(MobAnims.BellMonk.BASH);
                return;
            }
            if (dist <= 6.0 && m.knellCooldown == 0 && sees) {
                m.knellCooldown = 300;
                m.begin(MobAnims.BellMonk.KNELL);
                return;
            }
            if (dist >= 3.0 && dist <= 14.0 && sees && m.waveCooldown == 0 && Math.abs(t.getY() - m.getY()) < 2.5) {
                m.waveCooldown = 90;
                m.begin(MobAnims.BellMonk.WAVE);
                return;
            }
            if (--repath <= 0) {
                repath = 12;
                if (dist > 9.0 || !sees) {
                    m.getNavigation().moveTo(t, 1.0);
                } else if (dist < 5.0) {
                    Vec3 away = m.position().subtract(t.position()).multiply(1, 0, 1).normalize().scale(4.0);
                    m.getNavigation().moveTo(m.getX() + away.x, m.getY(), m.getZ() + away.z, 1.1);
                } else {
                    m.getNavigation().stop();
                }
            }
        }
    }
}
