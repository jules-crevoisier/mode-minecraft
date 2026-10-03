package com.wayfarers.entity.boss;

import com.wayfarers.Wayfarers;
import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.AshLord.COMBO1;
import static com.wayfarers.generated.MobAnims.AshLord.COMBO2;
import static com.wayfarers.generated.MobAnims.AshLord.COMBO3;
import static com.wayfarers.generated.MobAnims.AshLord.LEAP;
import static com.wayfarers.generated.MobAnims.AshLord.METEOR;
import static com.wayfarers.generated.MobAnims.AshLord.PLANT;
import static com.wayfarers.generated.MobAnims.AshLord.ROAR;
import static com.wayfarers.generated.MobAnims.AshLord.SPIN;
import static com.wayfarers.generated.MobAnims.AshLord.STAGGER;
import static com.wayfarers.generated.MobAnims.AshLord.THRUST;
import static com.wayfarers.generated.MobAnims.AshLord.TRAIL;

/**
 * Le Seigneur des Cendres (The Ash Lord): boss of the Basalt Fortress, a 4.7-block knight in ember-cracked
 * plate with a flaming greatsword.
 * <ul>
 *     <li>Phase 1: a three-hit combo (each swing telegraphed on its own, the second and third may not come),
 *     a lunging thrust, a jumping slam that sends a ring of fire, a dragged blade that rips a line of
 *     eruptions, and the sword plant that raises two rings of fire pillars around him.</li>
 *     <li>Phase 2 (the blade ignites fully): faster, the combo always runs to its end and leaves fire in its
 *     wake, a third ring of pillars, three trails at once, an ash meteor rain and a spinning flame sweep.</li>
 * </ul>
 * Moves that never start on their own (combo hits 2 and 3) use an impossible range and are only chained.
 */
public class AshLord extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 4.6F;
    /** Range for moves that only ever start as the follow-up of another one. */
    private static final double CHAINED = -1.0;

    public AshLord(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 620.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.AshLord.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.RED;
    }

    @Override
    protected int roarAction() {
        return ROAR;
    }

    @Override
    protected int staggerAction() {
        return STAGGER;
    }

    @Override
    protected float maxPoise() {
        return 90.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // combo, hit 1: the blade cocked far out to his right, a flat sweep across (0.70 s)
        out.add(BossAttack.of("combo1").anim(COMBO1).timing(14, 3, 11).range(0, 5.5).cooldown(40).weight(14)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.0, 100, ParticleTypes.SMALL_FLAME);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> slash(b, level, 5.5, 100, 15.0F))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 || b.getRandom().nextFloat() < 0.6F) {
                        b.chain(level, "combo2");
                    }
                })
                .build());
        // combo, hit 2: wound across to his left, a backhand sweep (0.55 s)
        out.add(BossAttack.of("combo2").anim(COMBO2).timing(11, 3, 12).range(CHAINED, CHAINED).cooldown(0).weight(1)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 5.0, 100, ParticleTypes.SMALL_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> slash(b, level, 5.5, 100, 13.0F))
                .end((b, level, t, tick) -> {
                    if (b.getRandom().nextFloat() < (b.phase() == 2 ? 0.8F : 0.5F)) {
                        b.chain(level, "combo3");
                    }
                })
                .build());
        // combo, hit 3: the overhead cleave that splits the ground (0.90 s); in phase 2 it leaves a fire line
        out.add(BossAttack.of("combo3").anim(COMBO3).timing(18, 3, 17).range(CHAINED, CHAINED).cooldown(0).weight(1)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        line(b, level, 1, 6, ParticleTypes.SMALL_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitLine(level, 6.5, 1.3, 20.0F, 0.8);
                    burnLine(b, level, 6.5, 1.3);
                    b.addEffect(flameBurst(b.ahead(4.2), 0, 2.4, 10.0F));
                    if (b.phase() == 2) {
                        fireTrail(b, b.forward(), 6, 14, 2.0, 12.0F);
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // thrust: drawn back level at the hip, then a lunging stab that closes the gap (0.75 s)
        out.add(BossAttack.of("thrust").anim(THRUST).timing(15, 4, 13).range(3.5, 11.0).cooldown(70).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        line(b, level, 1, 9, ParticleTypes.SMALL_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(1.7, 0.05);
                    level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.7F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 1 || tick == 3) {
                        b.hitLine(level, 6.0, 1.2, 17.0F, 1.0);
                        burnLine(b, level, 6.0, 1.2);
                    }
                    Vec3 p = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.8, p.z, 8, 1.2, 0.2, 1.2, 0.02);
                })
                .build());
        // leap: crouch, jump onto the target with the sword raised, crash down in a ring of fire (1.05 s)
        out.add(BossAttack.of("leap").anim(LEAP).timing(21, 3, 16).range(6.0, 18.0).cooldown(130).weight(8)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 3.5, ParticleTypes.FLAME);
                    }
                    if (tick == 9) {
                        double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                        b.lunge(Math.min(1.7, dist / 12.0 * 1.15), 0.55);
                        level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    if (tick > 9) {
                        level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 1.5, b.getZ(), 6, 0.5, 1.0, 0.5, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.position();
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    b.hitCircle(level, c, 3.5, 18.0F, 1.3, 0.5);
                    b.addEffect(fireWave(c, b.phase() == 2 ? 13 : 10, 0.5, 10.0F));
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 4, 1.2, 0.2, 1.2, 0);
                    level.sendParticles(ParticleTypes.LAVA, c.x, c.y + 0.3, c.z, 30, 2.0, 0.2, 2.0, 0);
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 0.7F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .build());
        // trail: the blade dragged through the ground, then ripped up: eruptions race along the furrow (0.85 s)
        out.add(BossAttack.of("trail").anim(TRAIL).timing(17, 4, 15).range(0, 13.0).cooldown(110).weight(9)
                .windup((b, level, t, tick) -> {
                    Vec3 tip = b.position().add(sideways(b, -1.3)).add(b.forward().scale(0.8 - tick * 0.04));
                    level.sendParticles(ParticleTypes.FLAME, tip.x, tip.y + 0.1, tip.z, 3, 0.2, 0.05, 0.2, 0.01);
                    if (tick % 4 == 0) {
                        line(b, level, 2, 14, ParticleTypes.SMOKE);
                        level.playSound(null, b, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 4.0, 50, 14.0F, 1.0);
                    fireTrail(b, b.forward(), 2, 15, 1.4, 13.0F);
                    if (b.phase() == 2) {
                        fireTrail(b, rotate(b.forward(), 22), 3, 13, 1.4, 11.0F);
                        fireTrail(b, rotate(b.forward(), -22), 3, 13, 1.4, 11.0F);
                    }
                    level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());
        // plant: the sword plunged into the ground, rings of fire pillars rise around him in turn (0.90 s)
        out.add(BossAttack.of("plant").anim(PLANT).timing(18, 14, 16).range(0, 9.0).cooldown(170).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 3.0, ParticleTypes.FLAME);
                        b.telegraphRing(level, b.position(), 5.5, ParticleTypes.SMALL_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 2.5, 14.0F, 1.6, 0.6);
                    level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 0.2, b.getZ(), 25, 1.0, 0.1, 1.0, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    // three rings, offset so the gaps of one are covered by the next: wait, then step in
                    if (tick == 0) {
                        pillarRing(b, 3.2, 6, 0.0, 8);
                    } else if (tick == 5) {
                        pillarRing(b, 5.8, 9, 20.0, 8);
                    } else if (tick == 10 && b.phase() == 2) {
                        pillarRing(b, 8.5, 12, 0.0, 8);
                    }
                })
                .build());
        // meteor (phase 2): the blade raised to the sky; burning ash falls on the arena (0.80 s)
        out.add(BossAttack.of("meteor").anim(METEOR).phaseTwo().timing(16, 4, 20).range(0, 30).cooldown(240).weight(8)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 5.0 + tick * 0.15, b.getZ(), 4, 0.3, 0.6, 0.3, 0.05);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BLAZE_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 1.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.WITHER_SHOOT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 7, b.getZ(), 2, 0.5, 0.5, 0.5, 0);
                    int n = 0;
                    for (LivingEntity v : b.victims(level, b.position(), 28)) {
                        if (v instanceof Player) {
                            b.addEffect(meteor(v.position(), 26 + n * 6));
                            b.addEffect(meteor(v.position().add(v.getDeltaMovement().scale(20)), 34 + n * 6));
                            n++;
                        }
                    }
                    for (int i = 0; i < 10; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 3 + b.getRandom().nextDouble() * 11;
                        b.addEffect(meteor(b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 22 + i * 5));
                    }
                })
                .build());
        // spin (phase 2): the blade held out at arm's length, two full burning turns (0.60 s, then 16 ticks)
        out.add(BossAttack.of("spin").anim(SPIN).phaseTwo().timing(12, 16, 12).range(0, 6.5).cooldown(140).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.5, ParticleTypes.FLAME);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.4F))
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.hitCircle(level, b.position(), 5.5, 10.0F, 1.0, 0.3);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                    for (LivingEntity v : b.victims(level, b.position(), 5.5)) {
                        v.igniteForSeconds(3.0F);
                    }
                    double a0 = tick * 0.8;
                    for (int k = 0; k < 4; k++) {
                        double a = a0 + k * Math.PI / 2;
                        for (double r = 1.5; r <= 5.0; r += 0.9) {
                            level.sendParticles(ParticleTypes.FLAME, b.getX() + Math.cos(a) * r, b.getY() + 2.0,
                                    b.getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private helpers

    /** A burning sweep: arc hit, everyone struck is set alight. */
    private static void slash(WayfarerBoss b, ServerLevel level, double range, double halfAngle, float damage) {
        b.hitArc(level, range, halfAngle, damage, 1.2);
        for (LivingEntity v : b.victims(level, b.position(), range)) {
            Vec3 to = v.position().subtract(b.position()).multiply(1, 0, 1);
            if (to.length() <= range && (to.length() < 1 || to.normalize().dot(b.forward()) >= Math.cos(Math.toRadians(halfAngle)))) {
                v.igniteForSeconds(4.0F);
            }
        }
        Vec3 p = b.ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 3, 1.5, 0.2, 1.5, 0);
        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.6, p.z, 30, 2.0, 0.3, 2.0, 0.03);
        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.2F, 0.7F);
    }

    /** Sets alight everyone on the line {@link WayfarerBoss#hitLine} covers. */
    private static void burnLine(WayfarerBoss b, ServerLevel level, double length, double halfWidth) {
        Vec3 fwd = b.forward();
        for (LivingEntity v : b.victims(level, b.position(), length + 1)) {
            Vec3 to = v.position().subtract(b.position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            if (along >= 0 && along <= length && to.subtract(fwd.scale(along)).length() <= halfWidth + v.getBbWidth() / 2) {
                v.igniteForSeconds(4.0F);
            }
        }
    }

    /** Ground telegraph: particles on a straight line in front of the boss. */
    private static void line(WayfarerBoss b, ServerLevel level, int from, int to, ParticleOptions particle) {
        for (int i = from; i <= to; i++) {
            Vec3 p = b.ahead(i);
            level.sendParticles(particle, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
        }
    }

    private static Vec3 sideways(WayfarerBoss b, double dist) {
        Vec3 f = b.forward();
        return new Vec3(-f.z, 0, f.x).scale(dist);
    }

    private static Vec3 rotate(Vec3 v, double degrees) {
        double a = Math.toRadians(degrees);
        double c = Math.cos(a);
        double s = Math.sin(a);
        return new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
    }

    /** Eruptions racing away from the boss along {@code dir}, one every 1.5 blocks, each warned first. */
    private static void fireTrail(WayfarerBoss b, Vec3 dir, int from, int to, double step, float damage) {
        int k = 0;
        for (double d = from; d <= to; d += step) {
            Vec3 p = b.position().add(dir.scale(d));
            b.addEffect(flameBurst(p, 6 + k * 2, 1.4, damage));
            k++;
        }
    }

    /** A ring of fire pillars around the boss, each warned for {@code warn} ticks. */
    private static void pillarRing(WayfarerBoss b, double radius, int count, double offsetDeg, int warn) {
        for (int i = 0; i < count; i++) {
            double a = Math.toRadians(offsetDeg + 360.0 * i / count);
            Vec3 p = b.position().add(Math.cos(a) * radius, 0, Math.sin(a) * radius);
            b.addEffect(pillar(p, warn, 1.3, 13.0F));
        }
    }

    /** A fire burst: smoke and small flames on the ground for {@code delay} ticks, then flames that burn. */
    private static Effect flameBurst(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 2 == 0) {
                    level.sendParticles(ParticleTypes.SMALL_FLAME, pos.x, pos.y + 0.1, pos.z, 4, radius * 0.4, 0.02, radius * 0.4, 0.01);
                    level.sendParticles(ParticleTypes.SMOKE, pos.x, pos.y + 0.2, pos.z, 2, radius * 0.3, 0.05, radius * 0.3, 0.01);
                }
                t[0]++;
                return false;
            }
            level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.6, pos.z, 26, radius * 0.4, 0.8, radius * 0.4, 0.06);
            level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 0.3, pos.z, 4, radius * 0.3, 0.1, radius * 0.3, 0);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.0F, 0.7F);
            burnCircle(boss, level, pos, radius, damage, 0.8);
            return true;
        };
    }

    /** A tall pillar of fire: a warned circle, then a column that throws its victims up. */
    private static Effect pillar(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 2 == 0) {
                    level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.1, pos.z, 5, radius * 0.4, 0.02, radius * 0.4, 0.01);
                }
                t[0]++;
                return false;
            }
            int age = t[0] - delay;
            for (double y = 0; y < 5.0; y += 0.5) {
                level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + y, pos.z, 2, radius * 0.25, 0.1, radius * 0.25, 0.02);
            }
            if (age == 0) {
                level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 0.5, pos.z, 6, 0.3, 0.3, 0.3, 0);
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.2F, 0.6F);
                burnCircle(boss, level, pos, radius, damage, 1.1);
            }
            t[0]++;
            return age >= 6;
        };
    }

    /** An ash meteor: a warned circle, a burning streak falling from the sky, then an explosion. */
    private static Effect meteor(Vec3 target, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            Vec3 pos = new Vec3(target.x, boss.getY(), target.z);
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    boss.telegraphRing(level, pos, 2.2, ParticleTypes.SMALL_FLAME);
                }
                int left = delay - t[0];
                if (left <= 12) {
                    double h = left * 1.1;
                    level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + h, pos.z, 6, 0.3, 0.3, 0.3, 0.02);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y + h + 0.8, pos.z, 3, 0.3, 0.3, 0.3, 0.01);
                }
                t[0]++;
                return false;
            }
            level.sendParticles(ParticleTypes.EXPLOSION, pos.x, pos.y + 0.5, pos.z, 2, 0.6, 0.2, 0.6, 0);
            level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.5, pos.z, 30, 1.0, 0.6, 1.0, 0.08);
            level.sendParticles(ParticleTypes.ASH, pos.x, pos.y + 1, pos.z, 30, 1.5, 1.0, 1.5, 0.02);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 1.4F, 0.8F);
            burnCircle(boss, level, pos, 2.2, 14.0F, 0.9);
            return true;
        };
    }

    /** An expanding ring of fire (jump over it): {@link WayfarerBoss#wave} that also sets alight. */
    private static Effect fireWave(Vec3 center, double maxRadius, double speed, float damage) {
        Effect wave = WayfarerBoss.wave(center, maxRadius, speed, damage, ParticleTypes.FLAME);
        double[] r = {0.5};
        Set<UUID> burnt = new HashSet<>();
        return (boss, level) -> {
            r[0] += speed;
            for (LivingEntity e : boss.victims(level, center, r[0] + 1.5)) {
                double d = e.position().multiply(1, 0, 1).distanceTo(center.multiply(1, 0, 1));
                if (Math.abs(d - r[0]) <= 1.0 && e.getY() - center.y < 0.9 && burnt.add(e.getUUID())) {
                    e.igniteForSeconds(3.0F);
                }
            }
            return wave.tick(boss, level);
        };
    }

    private static void burnCircle(WayfarerBoss boss, ServerLevel level, Vec3 pos, double radius, float damage, double lift) {
        for (LivingEntity e : boss.victims(level, pos, radius)) {
            if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                boss.strike(level, e, damage, 0.3, lift);
                e.igniteForSeconds(4.0F);
            }
        }
    }

    // ------------------------------------------------------------------ ambience, phases

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.SMALL_FLAME, getX(), getY() + 2.6, getZ(), 2, 0.6, 1.0, 0.6, 0.01);
            level.sendParticles(ParticleTypes.ASH, getX(), getY() + 3.0, getZ(), 3, 1.0, 1.2, 1.0, 0.01);
        }
        if (phase() == 2 && tickCount % 2 == 0) {
            // the fully ignited blade: flames along the sword held low at his right side
            Vec3 f = forward();
            Vec3 side = new Vec3(-f.z, 0, f.x).scale(-1.0);
            for (double d = 0.6; d <= 3.0; d += 0.6) {
                Vec3 p = position().add(side).add(f.scale(d));
                level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.5 - d * 0.45, p.z, 1, 0.08, 0.08, 0.08, 0.01);
            }
            if (tickCount % 20 == 0) {
                level.playSound(null, this, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 1.0F, 0.7F);
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(Wayfarers.id("ash_lord_phase_two"), 0.22,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(fireWave(position(), 9, 0.45, 6.0F));
        level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2, getZ(), 120, 1.0, 2.0, 1.0, 0.25);
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 1, getZ(), 30, 1.5, 0.5, 1.5, 0);
        level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.0F, 1.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
        level.sendParticles(ParticleTypes.ASH, getX(), getY() + 2, getZ(), 200, 2.0, 2.0, 2.0, 0.05);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 2, getZ(), 60, 1.0, 2.0, 1.0, 0.05);
    }
}
