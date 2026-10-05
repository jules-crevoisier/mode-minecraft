package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.projectile.hurtingprojectile.SmallFireball;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.ForgeKing.ANVIL;
import static com.brasshaven.generated.MobAnims.ForgeKing.BASH;
import static com.brasshaven.generated.MobAnims.ForgeKing.LEAP;
import static com.brasshaven.generated.MobAnims.ForgeKing.ROAR;
import static com.brasshaven.generated.MobAnims.ForgeKing.SLAM;
import static com.brasshaven.generated.MobAnims.ForgeKing.SPARKS;
import static com.brasshaven.generated.MobAnims.ForgeKing.SPIN;
import static com.brasshaven.generated.MobAnims.ForgeKing.STAGGER;
import static com.brasshaven.generated.MobAnims.ForgeKing.SWEEP;
import static com.brasshaven.generated.MobAnims.ForgeKing.TRIPLE;

/**
 * Le Roi-Forgeron (The Forge King), boss of the Dwarven Forge: a colossal dwarf king with a red-hot war hammer
 * and an anvil strapped to his arm as a shield.
 * <ul>
 *     <li>Phase 1: overhead slam that sends a molten ring (jump it), wide hammer sweep, anvil-shield charge
 *     (gap closer), an uppercut that flings a fan of embers (small fireballs), and the anvil drop: he drives the
 *     anvil into the floor and molten anvils fall on every player after a warning.</li>
 *     <li>Phase 2 (after a roar), molten armour: a fire aura and magma eruptions trailing him, faster moves,
 *     combos (sweep into slam, charge into sweep), a three-turn hammer spin, a triple slam whose third blow is
 *     delayed, and a leaping crash from afar.</li>
 * </ul>
 */
public class ForgeKing extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 3.7F;

    /** Players already hit by the current shield charge (one hit per charge). */
    private final Set<UUID> charged = new HashSet<>();
    private boolean landed;
    private int trailTicks;

    public ForgeKing(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 480.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ForgeKing.TICKS;
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
        return 85.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // overhead slam: the hammer climbs over the shoulder for a full second, then a molten ring rolls out
        out.add(BossAttack.of("slam").anim(SLAM).timing(20, 3, 17).range(0, 6.5).cooldown(70).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.2), 3.0, ParticleTypes.FLAME);
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.2);
                    b.hitCircle(level, c, 3.0, 18.0F, 1.0, 0.5);
                    b.addEffect(moltenWave(c, b.phase() == 2 ? 13 : 10, 0.5, 9.0F));
                    burst(level, c, 1.0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // wide sweep: wound back to the right, scythes left through 200 degrees in front of him
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(16, 4, 10).range(0, 6.0).cooldown(45).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.8, 100, ParticleTypes.SMALL_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.0, 100, 13.0F, 1.6);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.5F, 0.7F);
                    for (int a = -100; a <= 100; a += 20) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(4.5));
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.0, p.z, 3, 0.3, 0.3, 0.3, 0.02);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "slam");
                    }
                })
                .build());
        // anvil-shield charge: crouches behind the anvil (telegraph line), then barrels forward
        out.add(BossAttack.of("bash").anim(BASH).timing(14, 10, 12).range(5.0, 15.0).cooldown(100).weight(8)
                .start((b, level, t, tick) -> charged.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 12; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.SMOKE, p.x, p.y + 0.2, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(1.1, 0.0);
                    level.playSound(null, b, SoundEvents.RAVAGER_ATTACK, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    Vec3 f = b.forward().scale(1.0);
                    b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                    b.hurtMarked = true;
                    Vec3 front = b.ahead(1.6);
                    for (LivingEntity e : b.victims(level, front, 2.0)) {
                        if (charged.add(e.getUUID())) {
                            b.strike(level, e, 14.0F, 2.0, 0.5);
                            level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.8F, 0.7F);
                        }
                    }
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 0.3, b.getZ(), 3, 0.6, 0.1, 0.6, 0.01);
                    level.sendParticles(ParticleTypes.LAVA, front.x, front.y + 1.0, front.z, 1, 0.4, 0.4, 0.4, 0);
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // ember uppercut: the hammer scrapes the floor, then flings a fan of small fireballs at the target
        out.add(BossAttack.of("sparks").anim(SPARKS).timing(15, 6, 12).range(4.0, 22.0).cooldown(80).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick >= 8) {
                        Vec3 p = b.position().add(right(b).scale(2.0)).add(b.forward().scale(-0.5));
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 0.2, p.z, 4, 0.3, 0.1, 0.3, 0.1);
                        level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y + 0.2, p.z, 2, 0.3, 0.05, 0.3, 0.01);
                    }
                    if (tick == 8) {
                        level.playSound(null, b, SoundEvents.SMITHING_TABLE_USE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> emberFan(level, t, b.phase() == 2 ? 7 : 5))
                .active((b, level, t, tick) -> {
                    if (tick == 4 && b.phase() == 2) {
                        emberFan(level, t, 4);
                    }
                })
                .build());
        // anvil drop: the anvil is driven into the floor, and molten anvils fall on every player after a warning
        out.add(BossAttack.of("anvil").anim(ANVIL).timing(18, 2, 18).range(0, 26.0).cooldown(150).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 4.2, b.getZ(), 2, 0.6, 0.2, 0.6, 0);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(1.6);
                    b.hitCircle(level, c, 2.6, 12.0F, 1.0, 0.6);
                    burst(level, c, 0.7);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
                    for (LivingEntity e : b.victims(level, b.position(), 26.0)) {
                        b.addEffect(fallingAnvil(e.position(), 24, 2.2, 15.0F));
                    }
                    if (b.phase() == 2) { // three more fall at random around him
                        for (int i = 0; i < 3; i++) {
                            double a = b.getRandom().nextDouble() * Math.PI * 2;
                            double r = 4 + b.getRandom().nextDouble() * 6;
                            b.addEffect(fallingAnvil(b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 30, 2.2, 15.0F));
                        }
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // hammer spin: three turns at arm's length, drifting toward the target
        out.add(BossAttack.of("spin").anim(SPIN).phaseTwo().timing(12, 30, 12).range(0, 8.0).cooldown(160).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 3.6, ParticleTypes.FLAME);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (t != null) {
                        Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                        if (to.length() > 1.5) {
                            Vec3 d = to.normalize().scale(0.14);
                            b.setDeltaMovement(d.x, b.getDeltaMovement().y, d.z);
                            b.hurtMarked = true;
                        }
                    }
                    if (tick % 5 == 0) {
                        b.hitCircle(level, b.position(), 3.6, 8.0F, 1.2, 0.3);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.0F, 0.5F);
                    }
                    double a = tick * 0.62;
                    for (int k = 0; k < 2; k++) {
                        double aa = a + k * Math.PI;
                        level.sendParticles(ParticleTypes.FLAME, b.getX() + Math.cos(aa) * 3.2, b.getY() + 1.6,
                                b.getZ() + Math.sin(aa) * 3.2, 4, 0.2, 0.2, 0.2, 0.01);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // triple slam: 0.9 s, 1.5 s, then a held, delayed third blow at 2.3 s with a double molten ring
        out.add(BossAttack.of("triple").anim(TRIPLE).phaseTwo().timing(18, 31, 16).range(0, 7.0).cooldown(150).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.2), 2.8, ParticleTypes.FLAME);
                    }
                })
                .impact((b, level, t, tick) -> smallSlam(level))
                .active((b, level, t, tick) -> {
                    if (tick == 12) {
                        smallSlam(level);
                    } else if (tick > 14 && tick < 28 && tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(3.2), 3.6, ParticleTypes.LAVA);
                    } else if (tick == 28) {
                        Vec3 c = b.ahead(3.2);
                        b.hitCircle(level, c, 3.6, 20.0F, 1.3, 0.6);
                        b.addEffect(moltenWave(c, 14, 0.5, 9.0F));
                        b.addEffect(delayed(10, moltenWave(c, 14, 0.35, 8.0F)));
                        burst(level, c, 1.4);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                        level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .build());
        // leaping crash: crouches (ring on the target), launches, lands hammer-first with a ring of eruptions
        out.add(BossAttack.of("leap").anim(LEAP).phaseTwo().timing(16, 14, 18).range(7.0, 22.0).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 3.5, ParticleTypes.FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    landed = false;
                    double dist = t == null ? 10 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(2.4, dist * 0.15), 0.75);
                    level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 0.2, b.getZ(), 30, 1.2, 0.1, 1.2, 0.05);
                })
                .active((b, level, t, tick) -> {
                    if (landed || !(tick == 13 || (tick >= 6 && b.onGround()))) {
                        return;
                    }
                    landed = true;
                    Vec3 c = b.position();
                    b.hitCircle(level, c, 3.5, 18.0F, 1.4, 0.6);
                    b.addEffect(moltenWave(c, 12, 0.55, 9.0F));
                    for (int i = 0; i < 6; i++) {
                        double a = Math.PI * 2 * i / 6;
                        b.addEffect(WayfarerBoss.eruption(c.add(Math.cos(a) * 5.5, 0, Math.sin(a) * 5.5), 16, 1.8, 10.0F,
                                ParticleTypes.SMALL_FLAME, ParticleTypes.LAVA));
                    }
                    burst(level, c, 1.5);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** A small slam in front (the first two blows of the triple slam). */
    private void smallSlam(ServerLevel level) {
        Vec3 c = ahead(3.2);
        hitCircle(level, c, 2.8, 14.0F, 0.9, 0.4);
        addEffect(moltenWave(c, 8, 0.5, 7.0F));
        burst(level, c, 0.8);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** A fan of small fireballs from the hammer head toward the target. */
    private void emberFan(ServerLevel level, LivingEntity target, int count) {
        Vec3 from = position().add(forward().scale(1.5)).add(0, 3.0, 0);
        Vec3 aim = target != null
                ? target.position().add(0, target.getBbHeight() * 0.5, 0).subtract(from).normalize()
                : forward();
        double spread = 9.0;
        for (int i = 0; i < count; i++) {
            double a = (i - (count - 1) / 2.0) * spread;
            Vec3 dir = rotate(aim, a).add(0, (getRandom().nextDouble() - 0.5) * 0.08, 0).normalize();
            SmallFireball ball = new SmallFireball(level, from.x, from.y, from.z, dir.scale(0.6));
            ball.setOwner(this);
            level.addFreshEntity(ball);
        }
        level.sendParticles(ParticleTypes.LAVA, from.x, from.y, from.z, 12, 0.5, 0.5, 0.5, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, from.x, from.y, from.z, 30, 0.6, 0.6, 0.6, 0.3);
        level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.playSound(null, this, SoundEvents.ANVIL_USE, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    private static void burst(ServerLevel level, Vec3 c, double size) {
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.4, c.z, (int) (3 * size), size, 0.2, size, 0);
        level.sendParticles(ParticleTypes.LAVA, c.x, c.y + 0.3, c.z, (int) (20 * size), size, 0.3, size, 0);
        level.sendParticles(ParticleTypes.FLAME, c.x, c.y + 0.3, c.z, (int) (40 * size), size * 1.5, 0.3, size * 1.5, 0.08);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, c.x, c.y + 0.5, c.z, (int) (15 * size), size, 0.5, size, 0.03);
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        return new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c).normalize();
    }

    /** The boss's right-hand side (the hammer side), from its body rotation. */
    private static Vec3 right(WayfarerBoss b) {
        float yaw = b.yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw));
    }

    /** Like {@link WayfarerBoss#wave}, but molten: fire particles, and whoever it catches is set alight. */
    private static Effect moltenWave(Vec3 center, double maxRadius, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] radius = {0.5};
        return (boss, level) -> {
            radius[0] += speed;
            double r = radius[0];
            int n = Math.max(16, (int) (r * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                double x = center.x + Math.cos(a) * r;
                double z = center.z + Math.sin(a) * r;
                level.sendParticles(ParticleTypes.FLAME, x, center.y + 0.15, z, 1, 0, 0.05, 0, 0.01);
                if (i % 4 == 0) {
                    level.sendParticles(ParticleTypes.LAVA, x, center.y + 0.2, z, 1, 0, 0, 0, 0);
                }
            }
            for (LivingEntity e : boss.victims(level, center, r + 1.5)) {
                double d = e.position().multiply(1, 0, 1).distanceTo(center.multiply(1, 0, 1));
                boolean grounded = e.getY() - center.y < 0.9;
                if (Math.abs(d - r) <= 1.0 && grounded && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.8, 0.45);
                    e.igniteForSeconds(3.0F);
                }
            }
            return r >= maxRadius;
        };
    }

    /** Runs {@code inner} after {@code delay} ticks. */
    private static Effect delayed(int delay, Effect inner) {
        int[] t = {0};
        return (boss, level) -> t[0]++ >= delay && inner.tick(boss, level);
    }

    /**
     * A molten anvil falling on {@code pos}: a ring and a column of embers mark the spot for {@code delay} ticks,
     * then it lands (hurts, ignites and throws up) with a clang.
     */
    private static Effect fallingAnvil(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, ParticleTypes.FLAME);
                }
                double h = 8.0 * (1.0 - (double) k / delay);
                level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + h + 0.5, pos.z, 1, 0.3, 0.1, 0.3, 0);
                level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y + h + 0.8, pos.z, 2, 0.4, 0.2, 0.4, 0);
                return false;
            }
            level.sendParticles(ParticleTypes.EXPLOSION, pos.x, pos.y + 0.5, pos.z, 2, 0.5, 0.2, 0.5, 0);
            level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 0.3, pos.z, 16, radius * 0.4, 0.3, radius * 0.4, 0);
            level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.3, pos.z, 30, radius * 0.5, 0.4, radius * 0.5, 0.06);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                    boss.strike(level, e, damage, 0.3, 0.8);
                    e.igniteForSeconds(3.0F);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ ambience, phase 2 molten armour

    @Override
    protected void bossTick(ServerLevel level) {
        Vec3 head = position().add(right(this).scale(1.6)).add(0, 3.3, 0);
        if (tickCount % 5 == 0) { // the red-hot hammer head smokes and drips
            level.sendParticles(ParticleTypes.SMOKE, head.x, head.y + 0.5, head.z, 2, 0.25, 0.2, 0.25, 0.01);
        }
        if (tickCount % 17 == 0) {
            level.sendParticles(ParticleTypes.LAVA, head.x, head.y, head.z, 1, 0.2, 0.2, 0.2, 0);
        }
        if (phase() < 2) {
            return;
        }
        // molten armour: flames lick the plates, nearby players catch fire
        if (tickCount % 2 == 0) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 1.8, getZ(), 3, 0.9, 1.0, 0.9, 0.01);
        }
        if (tickCount % 20 == 0) {
            for (LivingEntity e : victims(level, position(), 2.8)) {
                e.igniteForSeconds(2.0F);
            }
            level.playSound(null, this, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 1.5F, 0.7F);
        }
        // magma eruptions trailing him while he walks
        boolean moving = getDeltaMovement().horizontalDistanceSqr() > 0.002 && currentAttack() == null;
        if (moving && ++trailTicks >= 22) {
            trailTicks = 0;
            addEffect(WayfarerBoss.eruption(position(), 26, 1.6, 8.0F, ParticleTypes.SMALL_FLAME, ParticleTypes.LAVA));
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("forge_king_molten"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        burst(level, position(), 2.0);
        level.playSound(null, this, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.5F, 0.5F);
    }
}
