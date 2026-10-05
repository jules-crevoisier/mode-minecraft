package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.RuneColossus.BEAM;
import static com.brasshaven.generated.MobAnims.RuneColossus.DETACH;
import static com.brasshaven.generated.MobAnims.RuneColossus.OVERLOAD;
import static com.brasshaven.generated.MobAnims.RuneColossus.ROAR;
import static com.brasshaven.generated.MobAnims.RuneColossus.SLAM;
import static com.brasshaven.generated.MobAnims.RuneColossus.STAGGER;
import static com.brasshaven.generated.MobAnims.RuneColossus.STOMP;
import static com.brasshaven.generated.MobAnims.RuneColossus.SWEEP;
import static com.brasshaven.generated.MobAnims.RuneColossus.THROW;

/**
 * Le Colosse runique (The Rune Colossus): boss of the Rune Circle, waking in the rune vault under the crypt.
 *
 * <p>Phase 1, slow but devastating: the double-fist slam (a rune shockwave ring to jump), the stomp against
 * those under it, the backhand sweep of the menhir arm, the rock throw (a real boulder arcing onto a warned
 * zone), the rune beam (a long line from the head) and the crash, a leap that lands as a slam (gap closer).</p>
 *
 * <p>Phase 2 (after the roar): rune overload (fists driven into the ground, eruptions racing out along
 * telegraphed lines, then a second, offset set), the detached forearm thrown 4 blocks ahead on a tether of
 * runes (long punish window), slams that ring twice and chain into a second slam, three boulders per throw,
 * the beam sweeping sideways, sweep chaining into stomp.</p>
 *
 * <p>Private helpers: {@link #boulder} (a falling-block projectile that is removed before it can land as a
 * block) and {@link #runeLine}.</p>
 */
public class RuneColossus extends WayfarerBoss {
    public static final float WIDTH = 3.2F;
    public static final float HEIGHT = 5.6F;
    private static final DustParticleOptions RUNE = new DustParticleOptions(0x5CE8FF, 1.8F);
    private static final DustParticleOptions RUNE_SMALL = new DustParticleOptions(0x9AF4FF, 1.0F);

    private final List<Vec3> throwSpots = new ArrayList<>();
    private int slamsInRow;

    public RuneColossus(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 480.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.RuneColossus.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.BLUE;
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
        return 110.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.5;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // both fists raised high, hammered down 3 blocks ahead (1.1 s): a rune ring rolls out (jump it)
        out.add(BossAttack.of("slam").anim(SLAM).timing(22, 3, 19).range(0, 7.0).cooldown(70).weight(12)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_AGITATED, SoundSource.HOSTILE, 2.0F, 0.5F))
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.0), 3.5, RUNE);
                    }
                })
                .impact((b, level, t, tick) -> slamImpact(level, b.ahead(3.0)))
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 2) {      // a second, slower ring right behind the first
                        b.addEffect(WayfarerBoss.wave(b.ahead(3.0), 12, 0.32, 8.0F, RUNE_SMALL));
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && slamsInRow++ == 0 && t != null && b.distanceToSqr(t) < 64
                            && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "slam");             // phase 2: the second slam comes at once
                    } else {
                        slamsInRow = 0;
                    }
                })
                .build());
        // stomp on whoever stands under it (0.8 s)
        out.add(BossAttack.of("stomp").anim(STOMP).timing(16, 2, 14).range(0, 4.5).cooldown(60).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, RUNE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.5, 14.0F, 1.3, 0.7);
                    b.addEffect(WayfarerBoss.wave(b.position(), 7, 0.5, 7.0F, RUNE_SMALL));
                    dust(level, b.position(), 2.5);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());
        // backhand of the long menhir arm across the front (0.85 s)
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(17, 3, 16).range(0, 6.5).cooldown(50).weight(11)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.0, 80, RUNE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.5, 85, 15.0F, 1.8);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.4F);
                    level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    Vec3 p = b.ahead(3.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.5, p.z, 4, 2.0, 0.3, 2.0, 0);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceToSqr(t) < 20 && b.getRandom().nextFloat() < 0.45F) {
                        b.chain(level, "stomp");
                    }
                })
                .build());
        // rock throw: tears up a boulder, hurls it onto a warned zone (release 1.0 s)
        out.add(BossAttack.of("throw").anim(THROW).timing(20, 2, 18).range(5.0, 30).cooldown(100).weight(10)
                .start((b, level, t, tick) -> {
                    throwSpots.clear();
                    if (t != null) {
                        Vec3 aim = t.position().add(t.getDeltaMovement().multiply(10, 0, 10));
                        throwSpots.add(aim);
                        if (b.phase() == 2) {
                            for (int k = 0; k < 2; k++) {
                                double a = b.getRandom().nextDouble() * Math.PI * 2;
                                throwSpots.add(aim.add(Math.cos(a) * 4.5, 0, Math.sin(a) * 4.5));
                            }
                        }
                    }
                    dust(level, b.ahead(1.5), 1.5);
                    level.playSound(null, b, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 s : throwSpots) {
                            b.telegraphRing(level, s, 3.0, RUNE);
                            level.sendParticles(RUNE_SMALL, s.x, s.y + 0.2, s.z, 4, 1.2, 0.05, 1.2, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 hand = b.position().add(0, 6.0, 0).add(b.forward().scale(1.0));
                    int i = 0;
                    for (Vec3 s : throwSpots) {
                        b.addEffect(boulder(level, hand, s, 16 + 3 * i++, 16.0F));
                    }
                    level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.5F, 0.4F);
                })
                .build());
        // rune beam from the head, a long line (charges 1.1 s, burns 0.8 s); in phase 2 it sweeps sideways
        out.add(BossAttack.of("beam").anim(BEAM).timing(22, 16, 14).range(4.0, 24).cooldown(140).weight(8)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.5F, 0.6F))
                .windup((b, level, t, tick) -> {
                    Vec3 eye = b.position().add(0, 4.4, 0).add(b.forward().scale(0.8));
                    level.sendParticles(ParticleTypes.ENCHANT, eye.x, eye.y, eye.z, 12, 1.2, 1.2, 1.2, 0.6);
                    if (tick % 3 == 0) {
                        runeLine(level, b.position(), b.forward(), 22, RUNE_SMALL, 2);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3.0F, 0.6F))
                .active((b, level, t, tick) -> {
                    double sweep = b.phase() == 2 ? Math.toRadians(-35 + 70 * tick / 15.0) : 0;
                    Vec3 f = b.forward();
                    Vec3 dir = new Vec3(f.x * Math.cos(sweep) - f.z * Math.sin(sweep), 0, f.x * Math.sin(sweep) + f.z * Math.cos(sweep));
                    Vec3 eye = b.position().add(0, 4.4, 0).add(dir.scale(0.8));
                    for (int i = 0; i <= 44; i++) {
                        double d = i * 0.5;
                        double y = eye.y + (b.getY() + 1.0 - eye.y) * Math.min(1.0, d / 10.0);
                        Vec3 p = new Vec3(eye.x + dir.x * d, y, eye.z + dir.z * d);
                        level.sendParticles(i % 2 == 0 ? RUNE : ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
                    }
                    if (tick % 5 == 0) {
                        for (LivingEntity e : b.victims(level, b.position(), 23)) {
                            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
                            double along = to.dot(dir);
                            double side = to.subtract(dir.scale(along)).length();
                            if (along >= 1.0 && along <= 22 && side <= 1.3 + e.getBbWidth() / 2) {
                                b.strike(level, e, 7.0F, 0.4, 0.1);
                            }
                        }
                    }
                })
                .build());
        // gap closer: the crash - it leaps at the target and lands in a double-fist slam (fists down at 1.1 s)
        out.add(BossAttack.of("crash").anim(SLAM).timing(22, 3, 19).range(8.0, 22).cooldown(120).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 4.0, RUNE);
                    }
                    if (tick == 9) {
                        double dist = t == null ? 10 : Math.sqrt(b.distanceToSqr(t));
                        b.lunge(Math.min(1.6, Math.max(0.0, dist - 3.0) * 0.085), 0.75);
                        level.playSound(null, b, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 1.5F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> slamImpact(level, b.ahead(2.5)))
                .build());

        // ---------------------------------------------------------------- phase 2
        // rune overload: fists into the ground (1.0 s), eruptions race out along the telegraphed lines, then
        // a second set along the lines in between
        out.add(BossAttack.of("overload").anim(OVERLOAD).phaseTwo().timing(20, 28, 12).range(0, 20).cooldown(320).weight(10)
                .track(false)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_EMERGE, SoundSource.HOSTILE, 2.5F, 0.6F))
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int k = 0; k < 6; k++) {
                            runeLine(level, b.position(), dirAt(b, k * 60.0), 17, RUNE, 2);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int k = 0; k < 6; k++) {
                        eruptLine(b, b.position(), dirAt(b, k * 60.0), 4);
                    }
                    dust(level, b.ahead(1.5), 3.0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.4F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 12 && tick % 3 == 0) {
                        for (int k = 0; k < 6; k++) {
                            runeLine(level, b.position(), dirAt(b, k * 60.0 + 30.0), 17, RUNE_SMALL, 3);
                        }
                    }
                    if (tick == 12) {
                        for (int k = 0; k < 6; k++) {
                            eruptLine(b, b.position(), dirAt(b, k * 60.0 + 30.0), 3);
                        }
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .build());
        // detach: the right forearm tears free on a tether of runes and crashes 4 blocks ahead (1.2 s); the
        // arm takes a long time to come back (punish), sometimes followed at once by a slam
        out.add(BossAttack.of("detach").anim(DETACH).phaseTwo().timing(24, 3, 25).range(2.0, 9.0).cooldown(110).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(4.2), 3.2, RUNE);
                    }
                    if (tick == 14) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                    if (tick >= 16) {
                        runeLine(level, b.position(), b.forward(), 4.2, RUNE_SMALL, 1);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(4.2);
                    b.hitCircle(level, c, 3.2, 19.0F, 1.0, 0.7);
                    b.addEffect(WayfarerBoss.wave(c, 9, 0.5, 8.0F, RUNE_SMALL));
                    dust(level, c, 2.0);
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 2, 0.6, 0.2, 0.6, 0);
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> runeLine(level, b.position(), b.forward(), 4.2, RUNE, 1))
                .end((b, level, t, tick) -> {
                    if (t != null && b.distanceToSqr(t) < 49 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "slam");
                    }
                })
                .build());
    }

    private void slamImpact(ServerLevel level, Vec3 c) {
        hitCircle(level, c, 3.6, 20.0F, 1.1, 0.6);
        addEffect(WayfarerBoss.wave(c, phase() == 2 ? 14 : 11, phase() == 2 ? 0.55 : 0.45, 9.0F, RUNE));
        dust(level, c, 2.5);
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 3, 1.0, 0.2, 1.0, 0);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, c.x, c.y + 0.3, c.z, 30, 2.0, 0.2, 2.0, 0.05);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** Horizontal direction at {@code deg} degrees from the facing. */
    private static Vec3 dirAt(WayfarerBoss b, double deg) {
        Vec3 f = b.forward();
        double a = Math.toRadians(deg);
        return new Vec3(f.x * Math.cos(a) - f.z * Math.sin(a), 0, f.x * Math.sin(a) + f.z * Math.cos(a));
    }

    /** Eruptions racing outward along a line: one every 2.5 blocks, {@code step} ticks apart. */
    private static void eruptLine(WayfarerBoss b, Vec3 from, Vec3 dir, int step) {
        for (int i = 1; i <= 7; i++) {
            Vec3 p = from.add(dir.scale(1.0 + i * 2.4));
            b.addEffect(WayfarerBoss.eruption(p, 3 + i * step, 1.6, 12.0F, RUNE_SMALL, ParticleTypes.SOUL_FIRE_FLAME));
        }
    }

    /** Rune particles along the ground in a straight line (telegraphs, tethers). */
    private static void runeLine(ServerLevel level, Vec3 from, Vec3 dir, double length, DustParticleOptions dust, int every) {
        for (double d = 1.0; d <= length; d += 0.7 * every) {
            Vec3 p = from.add(dir.scale(d));
            level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
        }
    }

    private static void dust(ServerLevel level, Vec3 c, double spread) {
        BlockParticleOption stone = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MOSSY_COBBLESTONE.defaultBlockState());
        level.sendParticles(stone, c.x, c.y + 0.3, c.z, 40, spread, 0.3, spread, 0.2);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, c.x, c.y + 0.3, c.z, 6, spread * 0.6, 0.1, spread * 0.6, 0.01);
    }

    /**
     * A boulder: a real falling block launched on a ballistic arc from {@code from} to {@code to} in about
     * {@code flight} ticks. It is removed just before touching the ground (it never becomes a block), then
     * the impact hurts everything within 3 blocks.
     */
    private static Effect boulder(ServerLevel level, Vec3 from, Vec3 to, int flight, float damage) {
        BlockPos at = BlockPos.containing(from);
        FallingBlockEntity rock = null;
        BlockState state = Blocks.MOSSY_COBBLESTONE.defaultBlockState();
        if (level.getBlockState(at).isAir()) {
            level.setBlock(at, state, 2);
            rock = FallingBlockEntity.fall(level, at, state);
            rock.dropItem = false;
            rock.disableDrop();
            // horizontal speed corrected for the falling block's 0.98 drag, vertical by simulation
            double drag = (1 - Math.pow(0.98, flight)) / 0.02;
            double vx = (to.x - rock.getX()) / drag;
            double vz = (to.z - rock.getZ()) / drag;
            double vy = solveLift(rock.getY(), to.y, flight);
            rock.setDeltaMovement(vx, vy, vz);
            rock.hurtMarked = true;
        }
        FallingBlockEntity r = rock;
        Set<UUID> none = new HashSet<>();
        int[] t = {0};
        return (boss, lvl) -> {
            t[0]++;
            if (t[0] % 3 == 0) {
                boss.telegraphRing(lvl, to, 3.0, RUNE);
            }
            boolean done = t[0] >= flight + 4;
            Vec3 at2 = to;
            if (r != null && r.isAlive()) {
                lvl.sendParticles(RUNE_SMALL, r.getX(), r.getY() + 0.5, r.getZ(), 2, 0.2, 0.2, 0.2, 0);
                Vec3 v = r.getDeltaMovement();
                if (v.y < 0 && (r.getY() + v.y - 0.04 <= to.y + 0.4 || r.onGround())) {
                    at2 = r.position();
                    r.discard();
                    done = true;
                }
            } else if (r != null) {
                done = true;
            }
            if (!done) {
                return false;
            }
            Vec3 c = new Vec3(at2.x, to.y, at2.z);
            for (LivingEntity e : boss.victims(lvl, c, 3.2)) {
                if (e.position().multiply(1, 0, 1).distanceTo(c.multiply(1, 0, 1)) <= 3.0 && none.add(e.getUUID())) {
                    boss.strike(lvl, e, damage, 0.9, 0.5);
                }
            }
            dust(lvl, c, 1.8);
            lvl.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 2, 0.6, 0.2, 0.6, 0);
            lvl.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 1.8F, 0.7F);
            if (boss.phase() == 2) {
                boss.addEffect(WayfarerBoss.wave(c, 5, 0.35, 7.0F, RUNE_SMALL));
            }
            return true;
        };
    }

    /** Initial vertical speed so that a falling block (gravity 0.04 then drag 0.98) is at {@code y1} after n ticks. */
    private static double solveLift(double y0, double y1, int n) {
        double lo = -1.0;
        double hi = 3.0;
        for (int it = 0; it < 40; it++) {
            double mid = (lo + hi) / 2;
            double y = y0;
            double v = mid;
            for (int k = 0; k < n; k++) {
                v -= 0.04;
                y += v;
                v *= 0.98;
            }
            if (y < y1) {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        return (lo + hi) / 2;
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 5 == 0) {
            double a = tickCount * 0.3;
            level.sendParticles(RUNE_SMALL, getX() + Math.cos(a) * 1.4, getY() + 3.4, getZ() + Math.sin(a) * 1.4, 1, 0.1, 0.3, 0.1, 0);
        }
        if (phase() == 2 && tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 3.0, getZ(), 2, 1.0, 1.5, 1.0, 0.01);
        }
        if (walkAnimation.isMoving() && tickCount % 20 == 0) {
            level.playSound(null, this, SoundEvents.WARDEN_STEP, SoundSource.HOSTILE, 2.0F, 0.5F);
            dust(level, position(), 1.0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("colossus_phase_two"), 0.25,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 3.0F, 0.6F);
        addEffect(WayfarerBoss.wave(position(), 12, 0.6, 6.0F, RUNE));
        float yaw = getYRot() * Mth.DEG_TO_RAD;
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX() - Mth.sin(yaw), getY() + 4, getZ() + Mth.cos(yaw), 60, 1.5, 1.5, 1.5, 0.08);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        dust(level, position(), 3.0);
        level.sendParticles(RUNE, getX(), getY() + 3, getZ(), 120, 2.0, 2.5, 2.0, 0);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BRICKS_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
    }
}
