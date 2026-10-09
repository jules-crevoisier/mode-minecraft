package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.TeslaArchon.ARCLINE;
import static com.brasshaven.generated.MobAnims.TeslaArchon.ARCPUNCH;
import static com.brasshaven.generated.MobAnims.TeslaArchon.ARCSWEEP;
import static com.brasshaven.generated.MobAnims.TeslaArchon.COILSLAM;
import static com.brasshaven.generated.MobAnims.TeslaArchon.CORONA;
import static com.brasshaven.generated.MobAnims.TeslaArchon.MAGNET;
import static com.brasshaven.generated.MobAnims.TeslaArchon.ORB;
import static com.brasshaven.generated.MobAnims.TeslaArchon.OVERLOAD;
import static com.brasshaven.generated.MobAnims.TeslaArchon.ROAR;
import static com.brasshaven.generated.MobAnims.TeslaArchon.STAGGER;

/**
 * L'Archonte Tesla (The Tesla Archon), the champion of the Storm Spire: a mad electrical engineer fused with his own
 * copper coil suit, about 3.4 blocks tall, a towering tesla coil on his back, a coil-wound gauntlet on his right arm and
 * a coil-staff in his left hand. He waits on the open crown platform at the top of the spire (a railed disc about 33
 * across, lightning rods round its rim, the corona ring of rods hanging overhead).
 * <ul>
 *     <li>Phase 1: the <b>arc punch</b> (the arc then jumps on to the nearest other fighter unless they step away), the
 *     <b>ball lightning</b> (slow drifting orbs that prime and burst on a marked circle), the <b>coil slam</b> (a marked
 *     circle, then a ring of sparks to jump) and the <b>arc line</b> (a discharge down a line that locks before it
 *     fires).</li>
 *     <li>Phase 2 (a roar at 65%): he <b>charges the corona</b> (lightning falls one bolt after another on circles
 *     marked across the platform: visual-only bolts, the damage is his own, nothing burns) and turns his core into a
 *     <b>magnet</b> (a pull toward him slower than walking, then a discharge round him); two orbs, side lines on the
 *     arc line, a wider slam ring, two jumps on the arc punch.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>overload</b> (once), then every 13 s the
 *     <b>arc sweep</b>: he floats up over the middle of the platform and arc beams at ankle height turn round it under
 *     him; jump them.</li>
 * </ul>
 * He places and breaks no blocks (his only lightning is visual). Pushes are capped and never thrown toward the rim or
 * the stair door, so nobody leaves the crown by his hand.
 */
public class TeslaArchon extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.4F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double PUNCH_RANGE = 4.5;
    private static final double PUNCH_HALF = 50;
    private static final double CHAIN_RANGE = 6.0;
    private static final double ORB_R = 2.2;
    private static final double SLAM_R = 3.5;
    private static final double LINE_LEN = 18.0;
    private static final double LINE_HALF = 1.2;
    private static final double STRIKE_R = 2.0;
    private static final double PULL_R = 12.0;
    private static final double MAG_R = 3.5;
    private static final double CORONA_UP = 17.0;
    private static final double HOVER = 2.5;
    private static final double BEAM_SPEED = 3.0;              // degrees a tick: 0.26 blocks a tick at r 5, 0.8 at the rim
    private static final double BEAM_HALF = 0.6;
    private static final int SWEEP_EVERY = 260;
    private static final DustParticleOptions ARC = new DustParticleOptions(0x82DCFF, 1.3F);
    private static final DustParticleOptions ARC_BIG = new DustParticleOptions(0xB8F0FF, 2.2F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.4F);
    private static final DustParticleOptions COPPER = new DustParticleOptions(0xD8864A, 1.4F);

    private @Nullable Vec3 centre;
    private int radius = 15;
    private double floorTol = -1;
    /** Phase 3 has started (the overload). */
    private boolean overloaded;
    private int guard;
    private int roarUntil = -1;
    private int sweepTimer = 60;
    private int sweepCount;
    /** The arc punch's chain: the first fighter struck, then each one the arc will jump on to. */
    private final List<LivingEntity> arcChain = new ArrayList<>();
    private final List<Vec3> spots = new ArrayList<>();
    private @Nullable Vec3 hoverFrom;
    private double beamStart;
    private int beamDir = 1;
    private int beams = 3;
    private final Map<UUID, Integer> beamHits = new HashMap<>();

    public TeslaArchon(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 700.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.TeslaArchon.TICKS;
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
        return 120.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (the crown platform)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.floorTol = -1;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Top of the first solid shape at or below {@code y + 2} (scanning 8 blocks), or NaN. */
    private static double floorY(ServerLevel level, double x, double y, double z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(y + 2), Mth.floor(z));
        for (int i = 0; i < 8; i++) {
            VoxelShape s = level.getBlockState(p).getCollisionShape(level, p);
            if (!s.isEmpty()) {
                return p.getY() + s.max(Direction.Axis.Y);
            }
            p.move(0, -1, 0);
        }
        return Double.NaN;
    }

    private static boolean clear(ServerLevel level, double x, double y, double z, int height) {
        BlockPos b = BlockPos.containing(x, y + 0.05, z);
        for (int k = 0; k < height; k++) {
            BlockPos q = b.above(k);
            if (!level.getBlockState(q).getCollisionShape(level, q).isEmpty()) {
                return false;
            }
        }
        return true;
    }

    /** Whether the floor round the seal is flat (the platform) or rough (a command spawn somewhere else). */
    private double floorTol(ServerLevel level) {
        if (floorTol > 0) {
            return floorTol;
        }
        Vec3 c = centre();
        int flat = 0;
        int samples = 0;
        for (int i = 0; i < 48; i++) {
            double a = i * 2.39996;
            double d = Math.sqrt((i + 0.5) / 48.0) * Math.max(3, radius - 1);
            double y = floorY(level, c.x + Math.cos(a) * d, c.y + 0.5, c.z + Math.sin(a) * d);
            if (!Double.isNaN(y)) {
                samples++;
                if (Math.abs(y - c.y) <= 0.6) {
                    flat++;
                }
            }
        }
        floorTol = samples > 0 && flat >= samples * 0.7 ? 0.6 : 1.6;
        return floorTol;
    }

    /** Open platform at (x, z): floor level with the seal, two blocks of air over it, inside the arena; or null. */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z) {
        Vec3 c = centre();
        if (Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > floorTol(level) || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Open platform at (x, z), moved toward the centre until it lies within {@code maxR} of it; or null. */
    private @Nullable Vec3 inner(ServerLevel level, double x, double z, double maxR) {
        Vec3 c = centre();
        double d = Math.hypot(x - c.x, z - c.z);
        if (d > maxR && d > 1.0E-3) {
            x = c.x + (x - c.x) * maxR / d;
            z = c.z + (z - c.z) * maxR / d;
        }
        for (int i = 0; i < 6; i++) {
            Vec3 s = pad(level, x, z);
            if (s != null) {
                return s;
            }
            x = c.x + (x - c.x) * 0.8;
            z = c.z + (z - c.z) * 0.8;
        }
        return null;
    }

    private void turnToward(@Nullable LivingEntity t, float maxTurn) {
        if (t == null) {
            return;
        }
        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 14, radius + 4),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** Height of {@code e}'s feet over the floor under it (0 standing, more when jumping). */
    private static double overFloor(ServerLevel level, LivingEntity e) {
        double fy = floorY(level, e.getX(), e.getY(), e.getZ());
        return Double.isNaN(fy) ? 9.0 : e.getY() - fy;
    }

    /**
     * The crown is railed but high: a push is kept only when open platform lies 1.5 and 3 blocks along it well inside
     * the rim; otherwise it becomes a gentle push toward the centre (at most 0.5).
     */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        Vec3 flat = new Vec3(push.x, 0, push.z);
        if (flat.lengthSqr() < 1.0E-6) {
            return Vec3.ZERO;
        }
        Vec3 dir = flat.normalize();
        Vec3 c = centre();
        boolean ok = true;
        for (double d : new double[] {1.5, 3.0}) {
            Vec3 probe = e.position().add(dir.scale(d));
            if (flatDist(probe, c) > radius - 1.5 || pad(level, probe.x, probe.z) == null) {
                ok = false;
                break;
            }
        }
        if (ok) {
            return flat;
        }
        Vec3 in = c.subtract(e.position()).multiply(1, 0, 1);
        return in.lengthSqr() < 1.0 ? Vec3.ZERO : in.normalize().scale(Math.min(0.5, flat.length()));
    }

    /** Pushes capped at 0.8, lift at 0.4 (0.2 when the push was turned inward); never toward the rim. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(0.8, knockback));
        }
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 safe = safePush(level, e, push);
        boolean turned = push.lengthSqr() > 1.0E-6 && safe.subtract(push).lengthSqr() > 1.0E-6;
        lift = Math.min(lift, turned ? 0.2 : 0.4);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
    }

    /** A spark line between two points (an arc). */
    private static void arcLine(ServerLevel level, Vec3 a, Vec3 b, DustParticleOptions dust, boolean sparks) {
        double len = a.distanceTo(b);
        int n = Math.max(2, (int) (len * 2));
        for (int i = 0; i <= n; i++) {
            Vec3 p = a.lerp(b, i / (double) n);
            double j = (i == 0 || i == n) ? 0 : 0.15;
            level.sendParticles(dust, p.x, p.y, p.z, 1, j, j, j, 0);
            if (sparks && i % 2 == 0) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0.05);
            }
        }
    }

    /** A bolt of visual-only lightning (no fire, no vanilla damage, no block touched) at {@code p}. */
    private static void visualBolt(ServerLevel level, Vec3 p) {
        LightningBolt b = net.minecraft.world.entity.EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
        if (b != null) {
            b.snapTo(p.x, p.y, p.z);
            b.setVisualOnly(true);
            level.addFreshEntity(b);
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // arc punch: the gauntlet cocked back, sparks climbing the coil (0.7 s, the arc drawn), a driving punch: 12; the
        // arc then crackles from whoever was struck to the nearest other fighter within 6 (the line drawn for 0.4 s, a
        // ring under them) and jumps: 7 (phase 2: 9, and a second jump) unless they stepped out of reach
        out.add(BossAttack.of("arcpunch").anim(ARCPUNCH).timing(14, 10, 14).range(0, 5.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, PUNCH_RANGE, PUNCH_HALF, ARC);
                        b.telegraphArc(level, PUNCH_RANGE - 1.5, PUNCH_HALF, ARC);
                    }
                    Vec3 fist = position().add(rotate(forward(), 60).scale(1.2)).add(0, 1.6, 0);
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, fist.x, fist.y, fist.z, 2, 0.3, 0.3, 0.3, 0.05);
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 1.2F, 1.8F);
                    }
                })
                .impact((b, level, t, tick) -> punch(level))
                .active((b, level, t, tick) -> tickChain(level, tick))
                .end((b, level, t, tick) -> {
                    arcChain.clear();
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.25F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "magnet" : "arcline");
                    }
                })
                .build());
        // ball lightning: hands cupped before the core, a ball swelling between them (1.0 s), pushed out: an orb (phase
        // 2: two) drifts after you slower than you walk, its circle drawn under it; near a fighter (or after 7 s) it
        // stops, the circle turns red for 0.6 s and it bursts: 9
        out.add(BossAttack.of("orb").anim(ORB).timing(20, 6, 14).range(4.0, 24.0).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    Vec3 h = ahead(1.0).add(0, 1.6, 0);
                    double s = 0.1 + tick * 0.02;
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, h.x, h.y, h.z, 3, s, s, s, 0.02);
                    level.sendParticles(ARC, h.x, h.y, h.z, 1, s * 0.5, s * 0.5, s * 0.5, 0);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 1.5F, 1.4F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    int n = b.phase() == 2 ? 2 : 1;
                    for (int i = 0; i < n; i++) {
                        Vec3 dir = n == 1 ? forward() : rotate(forward(), i == 0 ? -25 : 25);
                        addEffect(ballLightning(position().add(dir.scale(1.4)).add(0, 1.3, 0), dir,
                                t != null ? t.getUUID() : null));
                    }
                    level.playSound(null, b, SoundEvents.TRIDENT_THUNDER.value(), SoundSource.HOSTILE, 1.0F, 1.6F);
                })
                .build());
        // coil slam: both arms raised, the coil blazing (1.1 s; a circle drawn round him, red the last 0.4 s), both fists
        // on the floor: 14 within 3.5, then a ring of sparks runs out to 8 (phase 2: 11): 7, jump it
        out.add(BossAttack.of("coilslam").anim(COILSLAM).timing(22, 8, 16).range(0, 7.0).cooldown(90).weight(9)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), SLAM_R, tick >= 14 ? RED : ARC);
                    }
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 3.6, b.getZ(), 3, 0.4, 0.4, 0.4, 0.05);
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 1.5F, 1.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), SLAM_R, 14.0F, 0.8, 0.3);
                    b.addEffect(WayfarerBoss.wave(b.position(), b.phase() == 2 ? 11.0 : 8.0, 0.5, 7.0F, ARC));
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 0.3, b.getZ(), 60, 2.0, 0.2, 2.0, 0.3);
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 0.5, b.getZ(), 16, 0.4, 0.4, 0.4, 0.2);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.8F);
                    level.playSound(null, b, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 1.5F, 1.4F);
                })
                .build());
        // arc line: the coil-staff levelled at you (a line 18 long drawn, he turns toward you until 0.7 s, then it locks
        // red for 0.5 s), the discharge down the line: 13. Phase 2: two side lines at 30 degrees, drawn red from the lock,
        // discharge 0.3 s later: 10
        out.add(BossAttack.of("arcline").anim(ARCLINE).timing(24, 12, 14).range(3.0, 20.0).cooldown(110).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick < 14) {
                        turnToward(t, 6.0F);
                    }
                    if (tick % 2 == 0) {
                        boolean locked = tick >= 14;
                        drawLine(level, forward(), locked ? RED : ARC);
                        if (locked && b.phase() == 2) {
                            drawLine(level, rotate(forward(), -30), RED);
                            drawLine(level, rotate(forward(), 30), RED);
                        }
                    }
                    Vec3 orb = ahead(1.0).add(0, 2.6, 0);
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, orb.x, orb.y, orb.z, 2, 0.2, 0.2, 0.2, 0.05);
                    if (tick == 14) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> discharge(level, forward(), 13.0F))
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick < 6 && tick % 2 == 0) {
                        drawLine(level, rotate(forward(), -30), RED);
                        drawLine(level, rotate(forward(), 30), RED);
                    }
                    if (b.phase() == 2 && tick == 6) {
                        discharge(level, rotate(forward(), -30), 10.0F);
                        discharge(level, rotate(forward(), 30), 10.0F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // corona: staff and gauntlet thrown up to the sky (1.5 s), the corona ring overhead charging; circles are marked
        // across the platform (one where each fighter stood, the rest at random), gold, red in their last 0.5 s; then
        // lightning falls on them one after another, 0.3 s apart: 10 within 2 (visual-only bolts: nothing burns)
        out.add(BossAttack.of("corona").anim(CORONA).phaseTwo().timing(30, 40, 16).range(0, 30.0).cooldown(260).weight(7)
                .track(false)
                .start((b, level, t, tick) -> planSpots(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Vec3 s : spots) {
                            b.telegraphRing(level, s, STRIKE_R, GOLD);
                        }
                    }
                    if (tick % 3 == 0) {
                        drawCorona(level, tick);
                    }
                    Vec3 c = centre();
                    double y = b.getY() + 3.8 + (tick % 10) * (c.y + CORONA_UP - b.getY() - 3.8) / 10.0;
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), y, b.getZ(), 2, 0.2, 0.2, 0.2, 0.02);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.8F + tick * 0.04F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    List<Vec3> marks = List.copyOf(spots);
                    for (int k = 0; k < marks.size(); k++) {
                        addEffect(coronaStrike(marks.get(k), 4 + k * 6));
                    }
                    level.playSound(null, b, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 2.0F, 1.2F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        drawCorona(level, 30 + tick);
                    }
                })
                .build());
        // magnet: arms spread wide, the core blazing (1.0 s; rings of field lines closing on him); for 1.4 s everyone
        // within 12 is drawn toward him, slower than walking away; a circle of 3.5 round him is drawn, red from 0.8 s;
        // he claps the arms shut: 12 within it
        out.add(BossAttack.of("magnet").anim(MAGNET).phaseTwo().timing(20, 36, 16).range(0, 14.0).cooldown(220).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(MAG_R, PULL_R - tick * 0.45), COPPER);
                    }
                    Vec3 core = b.position().add(0, 2.3, 0).add(forward().scale(0.5));
                    level.sendParticles(ARC, core.x, core.y, core.z, 2, 0.2, 0.2, 0.2, 0);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick < 28) {
                        pull(level);
                        if (tick % 2 == 0) {
                            b.telegraphRing(level, b.position(), MAG_R, tick >= 16 ? RED : ARC);
                            b.telegraphRing(level, b.position(), PULL_R - (tick % 8) * 1.0, COPPER);
                        }
                        if (tick % 8 == 0) {
                            level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.03F);
                        }
                    }
                    if (tick == 28) {
                        for (LivingEntity e : victims(level, b.position(), MAG_R + 1)) {
                            if (flatDist(e.position(), b.position()) <= MAG_R + e.getBbWidth() / 2 && Math.abs(e.getY() - b.getY()) < 3.0) {
                                strike(level, e, 12.0F, 0.0, 0.3);
                            }
                        }
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 1.0, b.getZ(), 60, MAG_R * 0.5, 0.6, MAG_R * 0.5, 0.3);
                        level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 1.5, b.getZ(), 16, 0.4, 0.4, 0.4, 0.2);
                        level.playSound(null, b, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // overload: he rises off the deck, every coil blazing (2.0 s, invulnerable; arcs spiralling in), and the
        // overload bursts out of him: a ring of sparks to 12 (10, jump it)
        out.add(BossAttack.of("overload").anim(OVERLOAD).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    double a = tick * 0.4;
                    double r = 4.0 - tick * 0.08;
                    for (int k = 0; k < 3; k++) {
                        double ang = a + k * Math.PI * 2 / 3;
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX() + Math.cos(ang) * r, b.getY() + 1 + tick * 0.06,
                                b.getZ() + Math.sin(ang) * r, 2, 0.1, 0.1, 0.1, 0.02);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, ARC);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.5F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> overload(level))
                .build());
        // arc sweep: he lifts off and floats over the middle of the platform (1.5 s; the beams drawn on the floor from
        // there, red the last 0.5 s, gold marks beside them showing which way they will turn); he hangs there 6 s while
        // the beams turn round under him at 3 degrees a tick: 7 to whoever stands on one as it passes (jump it)
        out.add(BossAttack.of("arcsweep").anim(ARCSWEEP).phaseTwo().timing(30, 120, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    hoverFrom = position();
                    beamStart = getRandom().nextDouble() * 360.0;
                    beamDir = sweepCount++ % 2 == 0 ? 1 : -1;
                    beams = Math.min(4, 2 + scaledCount(1));
                    beamHits.clear();
                    setNoGravity(true);
                    level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.5F, 0.7F);
                })
                .windup((b, level, t, tick) -> {
                    hoverAt(Math.min(1.0, (tick + 1) / 30.0));
                    if (tick % 2 == 0) {
                        drawBeams(level, 0, tick >= 20 ? RED : ARC, true);
                    }
                })
                .active((b, level, t, tick) -> {
                    hoverAt(1.0);
                    tickBeams(level, tick);
                    if (tick == 119) {
                        setNoGravity(false);
                        hoverFrom = null;
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** The punch: 12 in the arc; the arc then picks its chain (one jump, two in phase 2). */
    private void punch(ServerLevel level) {
        arcChain.clear();
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(PUNCH_HALF));
        LivingEntity first = null;
        double best = Double.MAX_VALUE;
        for (LivingEntity e : victims(level, position(), PUNCH_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= PUNCH_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                strike(level, e, 12.0F, 0.6, 0.2);
                if (d < best) {
                    best = d;
                    first = e;
                }
            }
        }
        Vec3 fist = ahead(2.0).add(0, 1.4, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, fist.x, fist.y, fist.z, 30, 0.6, 0.4, 0.6, 0.3);
        level.sendParticles(ParticleTypes.CRIT, fist.x, fist.y, fist.z, 8, 0.4, 0.3, 0.4, 0.2);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, this, SoundEvents.TRIDENT_THUNDER.value(), SoundSource.HOSTILE, 0.8F, 1.8F);
        if (first == null) {
            return;
        }
        arcChain.add(first);
        int jumps = phase() == 2 ? 2 : 1;
        for (int j = 0; j < jumps; j++) {
            LivingEntity from = arcChain.get(arcChain.size() - 1);
            LivingEntity next = null;
            double nd = CHAIN_RANGE;
            for (LivingEntity e : victims(level, from.position(), CHAIN_RANGE + 1)) {
                double d = e.distanceTo(from);
                if (!arcChain.contains(e) && d <= nd) {
                    nd = d;
                    next = e;
                }
            }
            if (next == null) {
                break;
            }
            arcChain.add(next);
        }
    }

    /** The chain's warning (a crackling line and a ring under each next fighter), then the jumps at active 8 and 9. */
    private void tickChain(ServerLevel level, int tick) {
        for (int i = 1; i < arcChain.size(); i++) {
            LivingEntity from = arcChain.get(i - 1);
            LivingEntity to = arcChain.get(i);
            int fireAt = 7 + i;
            if (!from.isAlive() || !to.isAlive() || tick > fireAt) {
                continue;
            }
            boolean inReach = to.distanceTo(from) <= CHAIN_RANGE;
            if (tick < fireAt && tick % 2 == 0) {
                arcLine(level, from.position().add(0, 1.0, 0), to.position().add(0, 1.0, 0), inReach ? ARC : COPPER, false);
                telegraphRing(level, to.position(), 1.0, tick >= 4 ? RED : ARC);
            }
            if (tick == fireAt && inReach) {
                arcLine(level, from.position().add(0, 1.0, 0), to.position().add(0, 1.0, 0), ARC_BIG, true);
                strike(level, to, phase() == 2 ? 9.0F : 7.0F, 0.0, 0.1);
                level.playSound(null, to.getX(), to.getY(), to.getZ(), SoundEvents.TRIDENT_THUNDER.value(), SoundSource.HOSTILE, 0.8F, 2.0F);
            }
        }
    }

    /**
     * A ball of lightning drifting at 0.13 blocks a tick toward {@code target} (turning up to 4 degrees a tick), kept
     * inside the rim, its circle drawn under it. Within 1.8 of a fighter (or after 7 s) it stops, the circle turns red
     * for 12 ticks, then it bursts: 9 within 2.2.
     */
    private Effect ballLightning(Vec3 start, Vec3 dir0, @Nullable UUID target) {
        Vec3[] pos = {start};
        Vec3[] dir = {dir0.multiply(1, 0, 1).normalize()};
        int[] age = {0};
        int[] fuse = {-1};
        return (boss, level) -> {
            if (!(boss instanceof TeslaArchon archon)) {
                return true;
            }
            int k = age[0]++;
            Vec3 p = pos[0];
            Vec3 floor = new Vec3(p.x, p.y - 1.3, p.z);
            if (fuse[0] < 0) {
                LivingEntity t = target != null && level.getEntity(target) instanceof LivingEntity le && le.isAlive() ? le : null;
                if (t != null) {
                    Vec3 want = t.position().subtract(p).multiply(1, 0, 1);
                    if (want.lengthSqr() > 1.0E-4) {
                        double cur = Math.toDegrees(Math.atan2(dir[0].z, dir[0].x));
                        double goal = Math.toDegrees(Math.atan2(want.z, want.x));
                        double nd = Math.toRadians(cur + Mth.clamp(Mth.wrapDegrees(goal - cur), -4.0, 4.0));
                        dir[0] = new Vec3(Math.cos(nd), 0, Math.sin(nd));
                    }
                }
                Vec3 next = p.add(dir[0].scale(0.13));
                Vec3 c = archon.centre();
                if (flatDist(next, c) > archon.radius - 1.0) {
                    Vec3 in = c.subtract(next).multiply(1, 0, 1).normalize();
                    dir[0] = in;
                    next = p.add(in.scale(0.13));
                }
                pos[0] = next;
                p = next;
                floor = new Vec3(p.x, p.y - 1.3, p.z);
                boolean near = false;
                for (LivingEntity e : boss.victims(level, floor, 3.0)) {
                    if (flatDist(e.position(), floor) <= 1.8 && Math.abs(e.getY() - floor.y) < 2.5) {
                        near = true;
                    }
                }
                if (near || k >= 140) {
                    fuse[0] = 12;
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 1.2F, 1.8F);
                }
                if (k % 2 == 0) {
                    boss.telegraphRing(level, floor, ORB_R, ARC);
                }
            } else {
                if (fuse[0] % 2 == 0) {
                    boss.telegraphRing(level, floor, ORB_R, RED);
                }
                if (--fuse[0] < 0) {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 50, 1.0, 0.8, 1.0, 0.4);
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 16, 0.4, 0.4, 0.4, 0.2);
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 1.5F, 1.6F);
                    for (LivingEntity e : boss.victims(level, floor, ORB_R + 1)) {
                        if (flatDist(e.position(), floor) <= ORB_R + e.getBbWidth() / 2 && Math.abs(e.getY() - floor.y) < 2.5) {
                            boss.strike(level, e, 9.0F, 0.0, 0.2);
                        }
                    }
                    return true;
                }
            }
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 3, 0.25, 0.25, 0.25, 0.05);
            level.sendParticles(fuse[0] >= 0 ? RED : ARC_BIG, p.x, p.y, p.z, 1, 0.12, 0.12, 0.12, 0);
            if (k % 3 == 0) {
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
            }
            if (k % 20 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 0.8F, 2.0F);
            }
            return false;
        };
    }

    private void drawLine(ServerLevel level, Vec3 dir, DustParticleOptions dust) {
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        for (double d = 1.0; d <= LINE_LEN; d += 1.0) {
            Vec3 p = position().add(dir.scale(d));
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = p.add(side.scale(s * LINE_HALF));
                level.sendParticles(dust, q.x, q.y + 0.15, q.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /** The discharge down a line from him: {@code damage} to whoever is in it (18 long, half width 1.2), a small push. */
    private void discharge(ServerLevel level, Vec3 dir, float damage) {
        for (LivingEntity e : victims(level, position(), LINE_LEN + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            if (along >= 0 && along <= LINE_LEN && side <= LINE_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, damage, 0.3, 0.2);
            }
        }
        Vec3 from = position().add(dir.scale(1.0)).add(0, 1.6, 0);
        Vec3 to = position().add(dir.scale(LINE_LEN)).add(0, 1.0, 0);
        arcLine(level, from, to, ARC_BIG, true);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 2.0F, 1.5F);
    }

    /** Circles for the corona: one where each fighter stands (up to 3), the rest on random open platform, 3.5 apart. */
    private void planSpots(ServerLevel level, @Nullable LivingEntity target) {
        spots.clear();
        int n = Math.min(7, 3 + scaledCount(1));
        List<LivingEntity> marks = new ArrayList<>();
        if (target != null) {
            marks.add(target);
        }
        for (Player p : fighters(level)) {
            if (marks.size() >= 3) {
                break;
            }
            if (!marks.contains(p)) {
                marks.add(p);
            }
        }
        for (LivingEntity e : marks) {
            Vec3 s = inner(level, e.getX(), e.getZ(), radius - 2.0);
            if (s != null && apart(s, 3.5)) {
                spots.add(s);
            }
        }
        Vec3 c = centre();
        for (int tries = 0; tries < 40 && spots.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 3.0 + getRandom().nextDouble() * Math.max(1.0, radius - 5.0);
            Vec3 s = pad(level, c.x + Math.cos(a) * d, c.z + Math.sin(a) * d);
            if (s != null && apart(s, 3.5) && flatDist(s, position()) > 2.5) {
                spots.add(s);
            }
        }
    }

    private boolean apart(Vec3 s, double min) {
        for (Vec3 o : spots) {
            if (flatDist(o, s) < min) {
                return false;
            }
        }
        return true;
    }

    /** The corona ring over the platform, charging (sparks running round it faster as {@code t} grows). */
    private void drawCorona(ServerLevel level, int t) {
        Vec3 c = centre();
        double r = Math.min(18.5, radius + 3.5);
        int n = 24;
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2 * i / n + t * 0.05;
            double x = c.x + Math.cos(a) * r;
            double z = c.z + Math.sin(a) * r;
            level.sendParticles(i % 3 == 0 ? ParticleTypes.ELECTRIC_SPARK : ARC, x, c.y + CORONA_UP, z, 1, 0.1, 0.1, 0.1, 0.01);
        }
    }

    /** One corona strike: the circle stays drawn (red for the last 10 ticks), then a visual bolt and 10 within 2. */
    private Effect coronaStrike(Vec3 at, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, STRIKE_R, delay - k <= 10 ? RED : GOLD);
                }
                if (delay - k <= 10) {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + 0.2, at.z, 2, STRIKE_R * 0.4, 0.05, STRIKE_R * 0.4, 0.05);
                }
                return false;
            }
            visualBolt(level, at);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + 0.4, at.z, 30, STRIKE_R * 0.4, 0.6, STRIKE_R * 0.4, 0.3);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 2.0F, 1.0F);
            for (LivingEntity e : boss.victims(level, at, STRIKE_R + 1)) {
                if (flatDist(e.position(), at) <= STRIKE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                    boss.strike(level, e, 10.0F, 0.0, 0.25);
                }
            }
            return true;
        };
    }

    /** Everyone within 12 is drawn toward him, slower than walking (they can walk out of it). */
    private void pull(ServerLevel level) {
        for (LivingEntity e : victims(level, position(), PULL_R + 1)) {
            Vec3 to = position().subtract(e.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > PULL_R || d < 1.5 || Math.abs(e.getY() - getY()) > 3.0) {
                continue;
            }
            Vec3 v = e.getDeltaMovement().add(to.normalize().scale(0.04));
            double h = Math.hypot(v.x, v.z);
            if (h > 0.28) {
                v = new Vec3(v.x * 0.28 / h, v.y, v.z * 0.28 / h);
            }
            e.setDeltaMovement(v);
            e.hurtMarked = true;
            if (getRandom().nextInt(4) == 0) {
                level.sendParticles(COPPER, e.getX(), e.getY() + 1.0, e.getZ(), 1, 0.2, 0.3, 0.2, 0);
            }
        }
    }

    // ------------------------------------------------------------------ phase 3: overload

    private void overload(ServerLevel level) {
        overloaded = true;
        sweepTimer = 60;
        addEffect(WayfarerBoss.wave(position(), 12, 0.55, 10.0F, ARC));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("tesla_archon_overload"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 120, 2.0, 2.0, 2.0, 0.5);
        level.sendParticles(ARC_BIG, getX(), getY() + 3, getZ(), 50, 1.5, 1.5, 1.5, 0);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 16, 0.4, 0.4, 0.4, 0.2);
        visualBolt(level, position());
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 3.0F, 0.8F);
    }

    /** Floats him from where the sweep began toward the hover point over the centre ({@code f} 0..1). */
    private void hoverAt(double f) {
        Vec3 to = centre().add(0, HOVER, 0);
        Vec3 from = hoverFrom != null ? hoverFrom : to;
        double s = f * f * (3 - 2 * f);
        Vec3 p = from.lerp(to, s);
        setPos(p.x, p.y, p.z);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
    }

    private double beamAngle(int i, int turned) {
        return beamStart + i * (360.0 / beams) + beamDir * BEAM_SPEED * turned;
    }

    /** The beams on the floor at {@code turned} ticks of turning; with {@code arrows} the way they will turn. */
    private void drawBeams(ServerLevel level, int turned, DustParticleOptions dust, boolean arrows) {
        Vec3 c = centre();
        for (int i = 0; i < beams; i++) {
            double a = Math.toRadians(beamAngle(i, turned));
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            for (double r = 1.0; r <= radius + 0.5; r += 1.0) {
                Vec3 p = c.add(dir.scale(r));
                level.sendParticles(dust, p.x, c.y + 0.3, p.z, 1, 0, 0.05, 0, 0);
            }
            if (arrows) {
                Vec3 side = rotate(dir, beamDir * 90.0);
                for (double r = 4.0; r <= radius; r += 4.0) {
                    Vec3 p = c.add(dir.scale(r)).add(side.scale(0.9));
                    level.sendParticles(GOLD, p.x, c.y + 0.2, p.z, 1, 0, 0, 0, 0);
                }
            }
        }
    }

    /**
     * The beams turn at 3 degrees a tick from 1 block out to the rim, at ankle height: 7 and a small lift to whoever
     * stands on one (feet within 0.6 of the floor) as it passes, at most every 10 ticks. Jump them.
     */
    private void tickBeams(ServerLevel level, int tick) {
        Vec3 c = centre();
        Vec3 hub = position().add(0, 1.0, 0);
        for (int i = 0; i < beams; i++) {
            double a = Math.toRadians(beamAngle(i, tick));
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            for (double r = 1.0; r <= radius + 0.5; r += 1.0) {
                Vec3 p = c.add(dir.scale(r));
                level.sendParticles(ARC, p.x, c.y + 0.35, p.z, 1, 0.05, 0.08, 0.05, 0);
                if ((tick + (int) r) % 3 == 0) {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, c.y + 0.4, p.z, 1, 0.1, 0.1, 0.1, 0.05);
                }
            }
            if (tick % 2 == 0) {
                arcLine(level, hub, c.add(dir.scale(1.0)).add(0, 0.35, 0), ARC, false);
            }
            for (LivingEntity e : victims(level, c, radius + 2)) {
                Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                double along = to.dot(dir);
                double side = Math.abs(to.x * dir.z - to.z * dir.x);
                if (along >= 0.6 && along <= radius + 1.0 && side <= BEAM_HALF + e.getBbWidth() / 2
                        && Math.abs(e.getY() - c.y) < 3.0 && overFloor(level, e) < 0.6
                        && tick - beamHits.getOrDefault(e.getUUID(), -99) >= 10) {
                    beamHits.put(e.getUUID(), tick);
                    strike(level, e, 7.0F, 0.0, 0.25);
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, e.getX(), e.getY() + 0.5, e.getZ(), 12, 0.3, 0.3, 0.3, 0.2);
                }
            }
        }
        if (tick % 10 == 0) {
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 1.6F);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 6, 0.5, 0.8, 0.5, 0.1);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    /** Back to the first phase (the fight was reset): base speed, on his feet, no beams. */
    private void resetForm() {
        overloaded = false;
        roarUntil = -1;
        guard = 0;
        sweepCount = 0;
        beamHits.clear();
        arcChain.clear();
        hoverFrom = null;
        setNoGravity(false);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("tesla_archon_overload"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("tesla_archon_wrath"));
        }
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        if (isNoGravity() && (cur == null || !"arcsweep".equals(cur.name))) {
            setNoGravity(false);                           // a sweep cut short (stagger, reset, reload)
            hoverFrom = null;
        }
        if (phase() == 1 && overloaded) {
            resetForm();                                   // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!overloaded && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "overload");
            } else if (overloaded && guard == 0 && --sweepTimer <= 0) {
                sweepTimer = Math.max(160, (int) Math.round(SWEEP_EVERY * cooldownScale()));
                chain(level, "arcsweep");
            }
        }
        // ambience: sparks off the coil's toroid and the core; more of them once he overloads
        if (tickCount % (overloaded ? 2 : 5) == 0) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 3.7, getZ(), 1, 0.6, 0.3, 0.6, 0.05);
        }
        if (tickCount % 12 == 0) {
            level.sendParticles(ARC, getX(), getY() + 2.2, getZ(), 1, 0.3, 0.3, 0.3, 0);
        }
        if (overloaded && tickCount % 40 == 0) {
            Vec3 a = position().add(0, 3.7, 0);
            Vec3 b = position().add(getRandom().nextDouble() * 4 - 2, 0.2, getRandom().nextDouble() * 4 - 2);
            arcLine(level, a, b, ARC, true);
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 1.0F, 1.8F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("tesla_archon_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: high up on the crown, cut it and take it back near the rim
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z).scale(0.3));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.2), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 80, 2.0, 1.5, 2.0, 0.4);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 2.5F, 1.1F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        setNoGravity(false);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 150, 1.5, 2.0, 1.5, 0.5);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 3, getZ(), 40, 0.8, 1.0, 0.8, 0.02);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("ArchonCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("ArchonRadius", radius);
        output.putBoolean("ArchonOverloaded", overloaded);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("ArchonCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("ArchonRadius", 15);
        floorTol = -1;
        overloaded = input.getBooleanOr("ArchonOverloaded", false) && phase() == 2;
        setNoGravity(false);
    }
}
