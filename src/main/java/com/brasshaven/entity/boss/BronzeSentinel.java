package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.BronzeSentinel.BASH;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.BEAMS;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.CLEAVE;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.DANCE;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.OVERHEAD;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.ROAR;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.SHIELDWALL;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.STAGGER;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.STOMP;
import static com.brasshaven.generated.MobAnims.BronzeSentinel.TOPPLE;

/**
 * La Sentinelle d'airain (The Bronze Sentinel), living guardian of the Fallen Colossus: a 5.6-block knight automaton
 * of stone under verdigris bronze plate, moss in the joints, a broken cross-visor helm glowing gold from inside, a
 * tower shield on the left arm and a long greatsword in the right hand. It waits inside the toppled statue's helm.
 * <p>A hard overworld fight: 460 health, armour 14, poise 100, hits of 10 to 22.
 * <ul>
 *     <li>Phase 1: <b>shield bash</b> (a lunging gap-closer, 12), <b>overhead</b> (22 in front, then a crack runs
 *     12 blocks along the ground, 14), <b>cleave</b> (a 220 degree sweep, 18), <b>shield wall</b> (2 s behind the
 *     shield: frontal hits are blocked, punish from behind; if it blocked anything it answers with a bash) and
 *     <b>stomp</b> (12 around, then a ring to jump, 10).</li>
 *     <li>Phase 2 (after a roar at half health): its plates fall away (armour -6, +20% speed), combos (cleave into
 *     overhead, bash into cleave), the <b>blade dance</b> (three whirling turns while it advances, 11 each),
 *     the <b>topple</b> (a leap that lands sword-first on a circle marked at your feet, 22 + a ring) and
 *     <b>rune beams</b>: lines of rune light warned across the floor, then fired (14), three volleys.</li>
 * </ul>
 */
public class BronzeSentinel extends WayfarerBoss {
    public static final float WIDTH = 2.2F;
    public static final float HEIGHT = 5.6F;
    private static final double TOPPLE_RADIUS = 4.0;

    /** True while the shield wall is up: frontal hits are blocked. */
    private boolean guarding;
    /** The shield wall blocked at least one hit (it then answers with a bash). */
    private boolean blockedAny;
    /** Victims already hit by the current bash. */
    private final Set<UUID> bashed = new HashSet<>();
    /** The topple leap: where it took off and where it lands. */
    private Vec3 leapFrom = Vec3.ZERO;
    private Vec3 leapTo = Vec3.ZERO;

    public BronzeSentinel(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 460.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BronzeSentinel.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.GREEN;
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
        return 100.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // shield bash: the shield drawn in, the shoulder set (0.7 s, a line of sparks marks the rush), then it lunges
        out.add(BossAttack.of("bash").anim(BASH).timing(14, 8, 12).range(3.5, 14.0).cooldown(90).weight(10)
                .start((b, level, t, tick) -> bashed.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 9; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(1.3, 0.1);
                    level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.ahead(1.8), 2.3)) {
                        if (bashed.add(e.getUUID())) {
                            b.strike(level, e, 12.0F, 2.2, 0.5);
                            level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.7F);
                        }
                    }
                    level.sendParticles(ParticleTypes.SCRAPE, b.getX(), b.getY() + 2.0, b.getZ(), 3, 0.8, 0.8, 0.8, 0.05);
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "cleave");
                    }
                })
                .build());
        // overhead: the greatsword heaved over the helm (1.1 s), brought down 3.5 blocks ahead; a crack runs on along
        // the ground for 12 blocks (in phase 2, three cracks in a fan)
        out.add(BossAttack.of("overhead").anim(OVERHEAD).timing(22, 4, 16).range(0, 10.0).cooldown(80).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 2.6, ParticleTypes.CRIT);
                        for (int k = -1; k <= 1; k++) {
                            if (k != 0 && b.phase() == 1) {
                                continue;
                            }
                            Vec3 dir = rotate(b.forward(), k * 25);
                            for (double d = 5; d <= 17; d += 1.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.5);
                    b.hitCircle(level, c, 2.6, 22.0F, 1.2, 0.5);
                    for (int k = -1; k <= 1; k++) {
                        if (k != 0 && b.phase() == 1) {
                            continue;
                        }
                        Vec3 dir = rotate(b.forward(), k * 25);
                        b.addEffect(crack(b.position().add(dir.scale(5)), dir, 12.0, 14.0F));
                    }
                    level.sendParticles(stoneDust(), c.x, c.y + 0.3, c.z, 40, 1.2, 0.3, 1.2, 0.1);
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 2, 0.6, 0.1, 0.6, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .build());
        // cleave: the blade drawn far back to the right (0.8 s, the arc is outlined), then swept across 220 degrees
        out.add(BossAttack.of("cleave").anim(CLEAVE).timing(16, 3, 14).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 7.2, 110, ParticleTypes.CRIT);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 7.5, 110, 18.0F, 1.6);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    for (int a = -110; a <= 110; a += 20) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(5.0));
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.4, p.z, 1, 0, 0, 0, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "overhead");
                    }
                })
                .build());
        // shield wall: the tower shield planted in front (0.5 s, the guarded front is outlined in gold) for two
        // seconds; frontal hits clang off it. Walk round it and strike its back. If it blocked anything, it bashes.
        out.add(BossAttack.of("shieldwall").anim(SHIELDWALL).timing(10, 40, 10).range(0, 12.0).cooldown(220).weight(7)
                .start((b, level, t, tick) -> blockedAny = false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphArc(level, 2.4, 70, ParticleTypes.WAX_ON);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_NETHERITE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    guarding = true;
                    level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 2.4, 70, ParticleTypes.WAX_ON);
                    }
                    if (tick == 39) {
                        guarding = false;
                    }
                })
                .end((b, level, t, tick) -> {
                    guarding = false;
                    if (blockedAny) {
                        b.chain(level, "bash");
                    }
                })
                .build());
        // stomp: the right foot raised high (0.9 s, a ring marks its reach), driven down: 12 around, then a ring to jump
        out.add(BossAttack.of("stomp").anim(STOMP).timing(18, 3, 12).range(0, 6.0).cooldown(110).weight(8).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 3.5, ParticleTypes.CRIT);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 3.5, 12.0F, 1.4, 0.6);
                    b.addEffect(WayfarerBoss.wave(b.position(), b.phase() == 2 ? 12 : 9, 0.5, 10.0F, ParticleTypes.CRIT));
                    level.sendParticles(stoneDust(), b.getX(), b.getY() + 0.2, b.getZ(), 50, 2.0, 0.2, 2.0, 0.1);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.IRON_GOLEM_DAMAGE, SoundSource.HOSTILE, 1.5F, 0.4F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // blade dance: the blade held out to the side (0.6 s, a ring marks its reach), then three whirling turns
        // while it walks the target down: 11 at each turn
        out.add(BossAttack.of("dance").anim(DANCE).phaseTwo().timing(12, 36, 14).range(0, 9.0).cooldown(160).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.8, ParticleTypes.CRIT);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (t != null) {
                        Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                        if (to.length() > 1.5) {
                            Vec3 d = to.normalize().scale(0.18);
                            b.setDeltaMovement(d.x, b.getDeltaMovement().y, d.z);
                            b.hurtMarked = true;
                        }
                    }
                    if (tick % 12 == 6) {
                        b.hitCircle(level, b.position(), 4.8, 11.0F, 1.2, 0.3);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
                        for (int a = 0; a < 360; a += 30) {
                            Vec3 p = b.position().add(rotate(new Vec3(0, 0, 1), a).scale(3.8));
                            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    double a = tick * 0.52;
                    level.sendParticles(ParticleTypes.WAX_ON, b.getX() + Math.cos(a) * 4.0, b.getY() + 1.6,
                            b.getZ() + Math.sin(a) * 4.0, 2, 0.1, 0.1, 0.1, 0);
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // topple: it crouches and raises the blade while a circle follows the target (1.0 s), then leaps; the circle
        // locks where the target stood and it lands there sword-first a second later: 22 inside, then a ring
        out.add(BossAttack.of("topple").anim(TOPPLE).phaseTwo().timing(20, 20, 18).range(5.0, 22.0).cooldown(170).weight(8)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 2 == 0) {
                        b.telegraphRing(level, t.position(), TOPPLE_RADIUS, ParticleTypes.WAX_ON);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof BronzeSentinel s) {
                        s.startLeap(t);
                    }
                    level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.5F, 0.4F);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof BronzeSentinel s) {
                        s.tickLeap(level, tick);
                    }
                })
                .build());
        // rune beams: the blade lifted to the sky (1.0 s, gold light rises) and driven into the floor; three volleys of
        // rune-light lines are drawn across the floor (warned 0.9 s), one through every player, then they fire
        out.add(BossAttack.of("beams").anim(BEAMS).phaseTwo().timing(20, 50, 14).range(0, 30.0).cooldown(260).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 6.5, b.getZ(), 2, 0.2, 0.6, 0.2, 0.02);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0, ParticleTypes.WAX_ON);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.7F);
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 0.3, b.getZ(), 40, 1.5, 0.1, 1.5, 0.1);
                    for (int v = 0; v < 3; v++) {
                        for (LivingEntity e : b.victims(level, b.position(), 30.0)) {
                            double ang = b.getRandom().nextDouble() * 360;
                            b.addEffect(delayed(v * 16, runeBeamOn(e, rotate(new Vec3(0, 0, 1), ang), 16.0, 18, 14.0F)));
                        }
                        double ang = b.getRandom().nextDouble() * 360;
                        b.addEffect(delayed(v * 16 + 6, runeBeam(b.position(), rotate(new Vec3(0, 0, 1), ang), 16.0, 18, 14.0F)));
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ the shield wall

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guarding && isFrontal(source) && !source.is(DamageTypeTags.BYPASSES_SHIELD)) {
            blockedAny = true;
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.6F + random.nextFloat() * 0.2F);
            Vec3 p = position().add(forward().scale(1.4));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 2.2, p.z, 12, 0.4, 0.6, 0.4, 0.3);
            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 2.2, p.z, 4, 0.4, 0.6, 0.4, 0.1);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private boolean isFrontal(DamageSource source) {
        Vec3 from = source.getSourcePosition();
        if (from == null) {
            return false;
        }
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        return to.lengthSqr() > 1.0E-4 && to.normalize().dot(forward()) >= 0.2;
    }

    // ------------------------------------------------------------------ the topple leap

    private void startLeap(LivingEntity target) {
        leapFrom = position();
        Vec3 dest = target != null ? target.position() : ahead(8.0);
        Vec3 flat = dest.subtract(leapFrom).multiply(1, 0, 1);
        if (flat.length() > 18.0) {
            dest = leapFrom.add(flat.normalize().scale(18.0)).add(0, dest.y - leapFrom.y, 0);
        }
        leapTo = dest;
        if (flat.lengthSqr() > 1.0E-4) {
            snapFacing((float) (Mth.atan2(flat.z, flat.x) * Mth.RAD_TO_DEG) - 90.0F);
        }
    }

    private void tickLeap(ServerLevel level, int tick) {
        double s = Math.min(1.0, (tick + 1) / 20.0);
        Vec3 p = leapFrom.lerp(leapTo, s);
        setPos(p.x, p.y + Math.sin(Math.PI * s) * 5.0, p.z);
        setDeltaMovement(Vec3.ZERO);
        if (tick % 2 == 0) {
            telegraphRing(level, leapTo, TOPPLE_RADIUS, ParticleTypes.WAX_ON);
            telegraphRing(level, leapTo, TOPPLE_RADIUS * 0.5, ParticleTypes.CRIT);
        }
        level.sendParticles(ParticleTypes.SCRAPE, getX(), getY() + 2.5, getZ(), 2, 0.6, 1.0, 0.6, 0.02);
        if (tick == 19) {
            hitCircle(level, leapTo, TOPPLE_RADIUS, 22.0F, 1.5, 0.7);
            addEffect(WayfarerBoss.wave(leapTo, 9, 0.5, 9.0F, ParticleTypes.CRIT));
            level.sendParticles(ParticleTypes.EXPLOSION, leapTo.x, leapTo.y + 0.4, leapTo.z, 4, 1.2, 0.2, 1.2, 0);
            level.sendParticles(stoneDust(), leapTo.x, leapTo.y + 0.3, leapTo.z, 60, 2.2, 0.3, 2.2, 0.15);
            level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.4F);
            level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ move helpers

    private static BlockParticleOption stoneDust() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE_BRICKS.defaultBlockState());
    }

    /** A crack running along the ground from {@code start}: 0.8 blocks a tick, it hurts once whoever it reaches. */
    private static Effect crack(Vec3 start, Vec3 dir, double length, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] d = {0};
        return (boss, level) -> {
            d[0] += 0.8;
            Vec3 p = start.add(dir.scale(d[0]));
            level.sendParticles(stoneDust(), p.x, p.y + 0.2, p.z, 8, 0.3, 0.2, 0.3, 0.1);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.3, p.z, 3, 0.2, 0.3, 0.2, 0.1);
            if (((int) (d[0] / 0.8)) % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 1.2F, 0.5F);
            }
            for (LivingEntity e : boss.victims(level, p, 1.6)) {
                if (flatDist(e.position(), p) <= 1.3 && e.getY() - p.y < 1.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.4, 0.7);
                }
            }
            return d[0] >= length;
        };
    }

    /** A rune beam across the floor through wherever {@code target} stands when it is drawn. */
    private static Effect runeBeamOn(LivingEntity target, Vec3 dir, double halfLength, int warn, float damage) {
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (!target.isAlive()) {
                    return true;
                }
                inner[0] = runeBeam(target.position(), dir, halfLength, warn, damage);
            }
            return inner[0].tick(boss, level);
        };
    }

    /**
     * A line of rune light through {@code center} along {@code dir}: dotted gold for {@code warn} ticks, then it flares
     * and hurts whoever stands on it (a step aside is enough; it is too tall to jump).
     */
    private static Effect runeBeam(Vec3 center, Vec3 dir, double halfLength, int warn, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    for (double d = -halfLength; d <= halfLength; d += 1.0) {
                        Vec3 p = center.add(dir.scale(d));
                        level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 0.12, p.z, 1, 0, 0, 0, 0);
                    }
                }
                if (k == warn - 8) {
                    level.playSound(null, center.x, center.y, center.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                }
                return false;
            }
            for (double d = -halfLength; d <= halfLength; d += 0.5) {
                Vec3 p = center.add(dir.scale(d));
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.3, p.z, 1, 0.05, 0.4, 0.05, 0.02);
            }
            level.playSound(null, center.x, center.y, center.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.0F, 1.4F);
            for (LivingEntity e : boss.victims(level, center, halfLength + 1)) {
                Vec3 to = e.position().subtract(center).multiply(1, 0, 1);
                double along = to.dot(dir);
                double side = to.subtract(dir.scale(along)).length();
                if (Math.abs(along) <= halfLength && side <= 0.8 + e.getBbWidth() / 2 && Math.abs(e.getY() - center.y) < 3.0) {
                    boss.strike(level, e, damage, 0.6, 0.4);
                }
            }
            return true;
        };
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return a.multiply(1, 0, 1).distanceTo(b.multiply(1, 0, 1));
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis (positive turns toward the boss's right). */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    /** Runs {@code inner} after {@code delay} ticks. */
    private static Effect delayed(int delay, Effect inner) {
        int[] t = {0};
        return (boss, level) -> t[0]++ >= delay && inner.tick(boss, level);
    }

    // ------------------------------------------------------------------ ambience, phase 2

    @Override
    protected void bossTick(ServerLevel level) {
        BossAttack a = currentAttack();
        if (guarding && (a == null || !a.name.equals("shieldwall"))) {
            guarding = false;   // interrupted (stagger, phase change)
        }
        if (tickCount % 12 == 0) {   // gold light leaking from the broken visor
            Vec3 face = position().add(forward().scale(0.5));
            level.sendParticles(ParticleTypes.WAX_ON, face.x, getY() + 5.0, face.z, 1, 0.15, 0.1, 0.15, 0.01);
        }
        if (phase() == 2 && tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.SCRAPE, getX(), getY() + 3.0, getZ(), 1, 0.7, 1.2, 0.7, 0.02);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("bronze_sentinel_unplated"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        var armor = getAttribute(Attributes.ARMOR);
        if (armor != null) {
            armor.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("bronze_sentinel_plates_fallen"), -6.0,
                    AttributeModifier.Operation.ADD_VALUE));
        }
        // the oxidised plates crack and fall away
        BlockParticleOption plates = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.COPPER_BLOCK.weathering().weathered().defaultBlockState());
        level.sendParticles(plates, getX(), getY() + 3.0, getZ(), 120, 1.0, 1.8, 1.0, 0.2);
        level.sendParticles(ParticleTypes.SCRAPE, getX(), getY() + 3.0, getZ(), 30, 1.0, 1.8, 1.0, 0.2);
        level.playSound(null, this, SoundEvents.COPPER_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DAMAGE, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockParticleOption plates = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.COPPER_BLOCK.weathering().oxidized().defaultBlockState());
        level.sendParticles(plates, getX(), getY() + 3.0, getZ(), 120, 1.0, 2.0, 1.0, 0.2);
        level.sendParticles(stoneDust(), getX(), getY() + 2.0, getZ(), 80, 1.2, 1.5, 1.2, 0.15);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 5.0, getZ(), 30, 0.4, 0.4, 0.4, 0.1);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DEATH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.COPPER_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.0F, 0.5F);
    }
}
