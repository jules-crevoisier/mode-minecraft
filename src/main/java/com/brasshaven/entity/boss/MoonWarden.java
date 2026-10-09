package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.MoonWarden.COMET;
import static com.brasshaven.generated.MobAnims.MoonWarden.ECLIPSE;
import static com.brasshaven.generated.MobAnims.MoonWarden.FLIP;
import static com.brasshaven.generated.MobAnims.MoonWarden.ORBIT;
import static com.brasshaven.generated.MobAnims.MoonWarden.RADIANCE;
import static com.brasshaven.generated.MobAnims.MoonWarden.ROAR;
import static com.brasshaven.generated.MobAnims.MoonWarden.SHADE;
import static com.brasshaven.generated.MobAnims.MoonWarden.STAGGER;
import static com.brasshaven.generated.MobAnims.MoonWarden.SUMMON;
import static com.brasshaven.generated.MobAnims.MoonWarden.SWEEP;
import static com.brasshaven.generated.MobAnims.MoonWarden.WELL;

/**
 * La Gardienne de la lune (The Moon Warden), the champion of the Hollow Moon: an elegant celestial automaton
 * (3.6 blocks) levitating on end-rod thrusters. A slender porcelain and gold body, a face that is a moon-phase dial, a
 * halo of orbiting brass planets, long arms ending in astrolabe blades, a cloak of purpur and starfield. She waits on
 * the core platform (r 17, a void all round it) under the glowing core of the machine.
 * <ul>
 *     <li>Phase 1: the double astrolabe <b>sweep</b>, the <b>orbit</b> (her planets fly out along marked spirals), the
 *     <b>well</b> (a marked gravity well draws everyone in gently, then bursts), the levitation <b>flip</b> (marked rings
 *     under the players: who stays in floats up, then drifts down slowly). Her dial turns through the moon's phases:
 *     at the new moon her <b>shade</b>s dash along marked lines, at the full moon the <b>radiance</b> runs out as a ring
 *     (jump it), and in the crescent phases her second sweep throws a crescent of light.</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>comet</b> (she rises and dives onto a marked ring), the <b>summon</b>
 *     (void larvae and star motes), more planets and rings.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the <b>eclipse</b>. The core dims, darkness
 *     pulses, three gravity beams from the core sweep the platform round (walk with the gap), meteors fall on marked
 *     circles.</li>
 * </ul>
 * The only blocks she changes are the core's sea lanterns (tinted glass while it is eclipsed): all of them go back when
 * the fight resets, the arena empties, she dies or is removed, and on the first tick after a reload. There is a void
 * round the platform, so no push ever carries anyone outward: pushes that would near the edge are turned into a gentle
 * pull toward the centre, and every marked spot lies well inside the rim.
 */
public class MoonWarden extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_RANGE = 5.5;
    private static final double SWEEP_HALF = 80;
    private static final double CRESCENT_HALF = 40;
    private static final double WELL_R = 2.5;
    private static final double WELL_PULL_R = 7.0;
    private static final double FLIP_R = 2.5;
    private static final double COMET_R = 3.0;
    private static final double METEOR_R = 2.2;
    private static final double CORE_UP = 16.0;
    private static final int MOON_FULL = 0;
    private static final int MOON_WANING = 1;
    private static final int MOON_NEW = 2;
    private static final int MOON_WAXING = 3;
    private static final int MOON_ECLIPSE = 4;
    private static final int MOON_EVERY = 220;
    private static final int SWEEP_EVERY = 300;
    private static final int METEOR_EVERY = 110;
    private static final int BEAMS = 3;
    private static final int BEAM_DRAW = 40;
    private static final int BEAM_TURN = 140;
    private static final double BEAM_SPEED = 0.75;          // degrees a tick: 0.2 blocks a tick at the rim
    private static final EntityDataAccessor<Integer> DATA_MOON = SynchedEntityData.defineId(MoonWarden.class,
            EntityDataSerializers.INT);
    private static final DustParticleOptions SILVER = new DustParticleOptions(0xDCE6FF, 1.4F);
    private static final DustParticleOptions MOONLIGHT = new DustParticleOptions(0xF4F8FF, 2.0F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xD6A64C, 2.0F);
    private static final DustParticleOptions VIOLET = new DustParticleOptions(0xA868E0, 1.5F);
    private static final DustParticleOptions SHADOW = new DustParticleOptions(0x2A1E44, 1.8F);
    private static final DustParticleOptions CORONA = new DustParticleOptions(0xFFB858, 1.6F);

    private record Temp(BlockState original, BlockState placed) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 15;
    /** Floors must lie within this of the seal's level (0.6 on the flat platform, 1.6 on rough ground). */
    private double floorTol = -1;
    /** Phase 3 has started (the eclipse). */
    private boolean eclipsed;
    private int guard;
    private int roarUntil = -1;
    private int moonTimer = 160;
    private int sweepTimer = 80;
    private int meteorTimer = 60;
    // the gravity beams of the eclipse: -1 idle, else the tick of the sweep
    private int beamTick = -1;
    private double beamStart;
    private int beamDir = 1;
    private final Map<UUID, Integer> beamHits = new HashMap<>();
    // moves in flight
    private final List<List<Vec3>> orbitPaths = new ArrayList<>();
    private @Nullable Vec3 wellAt;
    private final List<Vec3> flipSpots = new ArrayList<>();
    private final List<@Nullable UUID> flipOwners = new ArrayList<>();
    private final List<List<Vec3>> shadeLines = new ArrayList<>();
    private @Nullable Vec3 cometTo;
    private final Set<UUID> adds = new HashSet<>();
    // the dimmed core: temporary blocks with their original state
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public MoonWarden(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 720.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_MOON, MOON_WAXING);
    }

    /** The dial's texture: 0 full, 1 waning, 2 new, 3 waxing, 4 eclipse. */
    @Override
    public int modelVariant() {
        return entityData.get(DATA_MOON);
    }

    private int moon() {
        return entityData.get(DATA_MOON);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MoonWarden.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.PURPLE;
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
        return 4.5;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (the core platform)

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

    /** The glowing core over the platform's centre. */
    private Vec3 core() {
        Vec3 c = centre();
        return new Vec3(c.x, c.y + CORE_UP, c.z);
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

    /**
     * A spot of open platform at (x, z): floor within the tolerance of the seal's level, two blocks of air over it and,
     * with {@code inArena}, within the arena's radius; or null (the void, the rim rail, the posts).
     */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z, boolean inArena) {
        Vec3 c = centre();
        if (inArena && Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
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
            Vec3 s = pad(level, x, z, true);
            if (s != null) {
                return s;
            }
            x = c.x + (x - c.x) * 0.8;
            z = c.z + (z - c.z) * 0.8;
        }
        return null;
    }

    private void faceToward(Vec3 p) {
        snapFacing((float) (Mth.atan2(p.z - getZ(), p.x - getX()) * (180.0 / Math.PI)) - 90.0F);
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
     * There is a void round the platform: a push is kept only when open platform lies 1.5 and 3 blocks along it, well
     * inside the rim; otherwise it becomes a gentle pull toward the centre (at most 0.5).
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
            if (flatDist(probe, c) > radius - 1.5 || pad(level, probe.x, probe.z, true) == null) {
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

    /** Pushes capped at 0.8, lift at 0.4 (0.2 when the push was turned inward); never toward the void. */
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

    private Vec3 dial() {
        return position().add(0, 3.1, 0).add(forward().scale(0.2));
    }

    private void setMoon(ServerLevel level, int m) {
        entityData.set(DATA_MOON, m);
        Vec3 d = dial();
        level.sendParticles(m == MOON_NEW ? SHADOW : MOONLIGHT, d.x, d.y, d.z, 16, 0.4, 0.4, 0.4, 0.01);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, m == MOON_NEW ? 0.5F : 1.2F);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // sweep: the right astrolabe blade drawn back across her body (0.9 s, the arc drawn silver) and swept round her
        // front: 13 and a small push; she turns (up to 25°), the arc is drawn red and the left blade sweeps back 0.4 s
        // later: 11. In the crescent phases the second sweep throws a crescent of light that flies out to 13
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(18, 14, 14).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, SILVER);
                        b.telegraphArc(level, SWEEP_RANGE - 2.0, SWEEP_HALF, SILVER);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> sweepHit(level, 13.0F, 0.5))
                .active((b, level, t, tick) -> {
                    if (tick == 1) {
                        turnToward(t, 25.0F);
                    }
                    if (tick >= 1 && tick < 8 && tick % 2 == 1) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, RED);
                        b.telegraphArc(level, SWEEP_RANGE - 2.0, SWEEP_HALF, RED);
                    }
                    if (tick == 8) {
                        sweepHit(level, 11.0F, 0.4);
                        if (moon() == MOON_WAXING || moon() == MOON_WANING) {
                            addEffect(crescent(position(), forward()));
                            level.playSound(null, b, SoundEvents.TRIDENT_RIPTIDE_1.value(), SoundSource.HOSTILE, 1.5F, 1.4F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 8.0 ? "flip" : "orbit");
                    }
                })
                .build());
        // orbit: she spreads her arms and the orrery spins up (1.2 s); spirals (3, phase 2 five) are marked from the
        // start, gold, red for the last 0.4 s; then her planets fly out along them one point a tick: 9 (once a spiral)
        out.add(BossAttack.of("orbit").anim(ORBIT).timing(24, 30, 14).range(0, 20.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planOrbits(level);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 16 ? RED : GOLD;
                        for (List<Vec3> path : orbitPaths) {
                            for (Vec3 p : path) {
                                level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                            }
                        }
                    }
                    Vec3 h = dial().add(forward().scale(-0.6));
                    level.sendParticles(BRASS, h.x, h.y, h.z, 1, 0.6, 0.6, 0.6, 0);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 1.5F, 1.2F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (List<Vec3> path : orbitPaths) {
                        b.addEffect(planetRun(path));
                    }
                    level.playSound(null, b, SoundEvents.ILLUSIONER_CAST_SPELL, SoundSource.HOSTILE, 1.5F, 1.2F);
                })
                .build());
        // well: both blades pointed at a marked spot well inside the rim (1.4 s: an inner ring r 2.5, red from 0.9 s, and
        // the pull's reach r 7 dotted); for 0.8 s everyone within 7 is drawn gently toward it (slower than walking), then
        // it bursts: 10 and a small lift to whoever is in the inner ring
        out.add(BossAttack.of("well").anim(WELL).timing(28, 20, 14).range(0, 18.0).cooldown(180).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    Vec3 aim = t != null ? t.position() : ahead(6.0);
                    wellAt = inner(level, aim.x, aim.z, radius - 5.0);
                    if (wellAt == null) {
                        wellAt = centre();
                    }
                    faceToward(wellAt);
                })
                .windup((b, level, t, tick) -> {
                    Vec3 w = wellAt;
                    if (w == null) {
                        return;
                    }
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, w, WELL_R, tick >= 18 ? RED : VIOLET);
                    }
                    if (tick % 4 == 0) {
                        dotted(level, w, WELL_PULL_R, VIOLET);
                    }
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, w.x, w.y + 0.5, w.z, 3, 1.2, 0.3, 1.2, 0.02);
                    if (tick % 7 == 0) {
                        level.playSound(null, w.x, w.y, w.z, SoundEvents.PORTAL_AMBIENT, SoundSource.HOSTILE, 1.0F, 1.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    Vec3 w = wellAt;
                    if (w == null) {
                        return;
                    }
                    if (tick < 16) {
                        pull(level, w);
                        double r = WELL_PULL_R * (1.0 - tick / 18.0);
                        b.telegraphRing(level, w, r, VIOLET);
                        b.telegraphRing(level, w, WELL_R, RED);
                        level.sendParticles(ParticleTypes.PORTAL, w.x, w.y + 0.6, w.z, 10, 2.0, 0.4, 2.0, -0.6);
                    }
                    if (tick == 16) {
                        burstWell(level, w);
                    }
                })
                .build());
        // flip: she raises both blades, palms up (1.1 s); rings (r 2.5) under every player (up to 3; phase 2 one more
        // near the target) follow them until 0.6 s, then lock red; at 1.1 s gravity flips in them: 7, Levitation 1 s
        // (about 2 blocks straight up) and Slow Falling 4 s, so whoever was caught drifts back down where they stood
        out.add(BossAttack.of("flip").anim(FLIP).timing(22, 10, 16).range(0, 20.0).cooldown(160).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planFlips(level, t);
                })
                .windup((b, level, t, tick) -> {
                    for (int i = 0; i < flipSpots.size(); i++) {
                        UUID id = flipOwners.get(i);
                        if (tick < 12 && id != null && level.getEntity(id) instanceof Player p) {
                            Vec3 s = inner(level, p.getX(), p.getZ(), radius - 3.0);
                            if (s != null) {
                                flipSpots.set(i, s);
                            }
                        }
                        Vec3 s = flipSpots.get(i);
                        if (tick % 2 == 0) {
                            b.telegraphRing(level, s, FLIP_R, tick < 12 ? VIOLET : RED);
                        }
                        if (tick % 3 == 0) {
                            level.sendParticles(ParticleTypes.REVERSE_PORTAL, s.x, s.y + 0.2, s.z, 3, 1.0, 0.1, 1.0, 0.0);
                        }
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.SHULKER_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Vec3 s : flipSpots) {
                        flipAt(level, s);
                    }
                    level.playSound(null, b, SoundEvents.SHULKER_SHOOT, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- the moon's phases (scheduled from bossTick)
        // shade (new moon): she folds her cloak round her (1.2 s); lines (2, more in co-op and phase 2, up to 4) across
        // the platform, one through each player, are marked from the start in shadow, red for the last 0.5 s; at 1.2 s
        // her shadows dash along them one after the other (0.3 s apart, 0.9 blocks a tick): 9 and Slowness I 1 s
        out.add(BossAttack.of("shade").anim(SHADE).timing(24, 40, 14).range(999, 999).cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> planShades(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 14 ? RED : SHADOW;
                        for (List<Vec3> line : shadeLines) {
                            for (int k = 0; k < line.size(); k += 1) {
                                Vec3 p = line.get(k);
                                level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                            }
                            Vec3 s = line.get(0);
                            level.sendParticles(SHADOW, s.x, s.y + 1.4, s.z, 4, 0.25, 0.8, 0.25, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ENDERMAN_STARE, SoundSource.HOSTILE, 1.5F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int i = 0; i < shadeLines.size(); i++) {
                        b.addEffect(shadeRun(shadeLines.get(i), i * 6));
                    }
                })
                .build());
        // radiance (full moon): she rises, arms wide, the halo swelling, gold rings gathering round her (1.5 s); the full
        // moon flares: a radiant ring runs out to 15 (10 and a small lift; jump it: it only hits who stands on the floor);
        // phase 2: a second ring 0.7 s later
        out.add(BossAttack.of("radiance").anim(RADIANCE).timing(30, 30, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(0.6, 4.0 - tick * 0.12), GOLD);
                    }
                    Vec3 d = dial();
                    level.sendParticles(MOONLIGHT, d.x, d.y, d.z, 2, 0.5, 0.5, 0.5, 0.0);
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 1.0F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    addEffect(floorRing(position(), radius, 0.5, 10.0F, MOONLIGHT));
                    Vec3 d = dial();
                    level.sendParticles(ParticleTypes.END_ROD, d.x, d.y, d.z, 40, 1.0, 1.0, 1.0, 0.15);
                    level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 1.4F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 14 && b.phase() == 2) {
                        addEffect(floorRing(position(), radius, 0.5, 10.0F, MOONLIGHT));
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.0F, 1.6F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // comet: she rises with the blades held high (1.5 s; a ring r 3 under you follows until 1.0 s, then locks red),
        // dives onto it and drives the blades in at 1.75 s: 13 and a small lift
        out.add(BossAttack.of("comet").anim(COMET).phaseTwo().timing(30, 10, 18).range(5.0, 18.0).cooldown(160).weight(6)
                .track(false)
                .start((b, level, t, tick) -> {
                    Vec3 aim = t != null ? t.position() : ahead(6.0);
                    cometTo = inner(level, aim.x, aim.z, radius - 3.0);
                    if (cometTo == null) {
                        cometTo = position();
                    }
                    faceToward(cometTo);
                    setNoGravity(true);
                    level.playSound(null, b, SoundEvents.FIREWORK_ROCKET_LAUNCH, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 24) {
                        move(MoverType.SELF, new Vec3(0, 0.12, 0));
                    }
                    setDeltaMovement(Vec3.ZERO);
                    if (tick < 20 && t != null) {
                        Vec3 s = inner(level, t.getX(), t.getZ(), radius - 3.0);
                        if (s != null) {
                            cometTo = s;
                            faceToward(s);
                        }
                    }
                    Vec3 c = cometTo;
                    if (c != null && tick % 2 == 0) {
                        b.telegraphRing(level, c, COMET_R, tick < 20 ? VIOLET : RED);
                    }
                    level.sendParticles(ParticleTypes.END_ROD, getX(), getY() - 0.2, getZ(), 2, 0.4, 0.1, 0.4, 0.02);
                })
                .active((b, level, t, tick) -> {
                    Vec3 c = cometTo;
                    if (c == null) {
                        return;
                    }
                    if (tick < 5) {
                        Vec3 step = c.subtract(position()).scale(1.0 / (5 - tick));
                        move(MoverType.SELF, step);
                        setDeltaMovement(Vec3.ZERO);
                        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 1.5, getZ(), 6, 0.3, 0.6, 0.3, 0.02);
                        level.sendParticles(VIOLET, getX(), getY() + 1.5, getZ(), 4, 0.3, 0.6, 0.3, 0);
                    }
                    if (tick == 5) {
                        setNoGravity(false);
                        cometSlam(level, c);
                    }
                })
                .end((b, level, t, tick) -> setNoGravity(false))
                .build());
        // summon: one blade raised to the core (1.0 s): void larvae and star motes come through the void (2, more in
        // co-op), never more than 3 at once
        out.add(BossAttack.of("summon").anim(SUMMON).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600).weight(4)
                .windup((b, level, t, tick) -> {
                    Vec3 d = dial();
                    level.sendParticles(ParticleTypes.PORTAL, d.x, d.y + 1.0, d.z, 4, 0.4, 0.4, 0.4, 0.3);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.ENDERMAN_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> spawnAdds(level, 2))
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // eclipse: she rises, arms crossed over the dial, the halo closing (2.0 s, guarded; dark rings converge on her);
        // she throws her arms open: the core dims, darkness falls, a dark ring runs out to 15 (10, jump it)
        out.add(BossAttack.of("eclipse").anim(ECLIPSE).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(0.8, 12.0 - tick * 0.28), SHADOW);
                    }
                    Vec3 k = core();
                    level.sendParticles(CORONA, k.x, k.y, k.z, 4, 3.0, 3.0, 3.0, 0);
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> eclipse(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void sweepHit(ServerLevel level, float damage, double knock) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SWEEP_HALF));
        for (LivingEntity e : victims(level, position(), SWEEP_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SWEEP_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.5) {
                strike(level, e, damage, knock, 0.2);
            }
        }
        for (double a = -SWEEP_HALF; a <= SWEEP_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SWEEP_RANGE - 1.0));
            level.sendParticles(SILVER, p.x, p.y + 1.3, p.z, 2, 0.1, 0.2, 0.1, 0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.7F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.HOSTILE, 1.5F, 0.8F);
    }

    /** A crescent of light flying out from {@code from} (±40°, 0.55 blocks a tick to 13): 7 to whoever it meets. */
    private Effect crescent(Vec3 from, Vec3 dir) {
        double[] r = {2.0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            r[0] += 0.55;
            double rr = r[0];
            for (double a = -CRESCENT_HALF; a <= CRESCENT_HALF; a += 6) {
                double thick = 0.5 * Math.cos(Math.toRadians(a) * 2.0);
                Vec3 p = from.add(rotate(dir, a).scale(rr + thick));
                level.sendParticles(MOONLIGHT, p.x, from.y + 1.0, p.z, 1, 0.05, 0.25, 0.05, 0);
            }
            double cos = Math.cos(Math.toRadians(CRESCENT_HALF));
            for (LivingEntity e : boss.victims(level, from, rr + 1.5)) {
                Vec3 to = e.position().subtract(from).multiply(1, 0, 1);
                double d = to.length();
                if (Math.abs(d - rr) <= 0.9 + e.getBbWidth() / 2 && d > 0.1 && to.normalize().dot(dir) >= cos
                        && Math.abs(e.getY() - from.y) < 2.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 7.0F, 0.0, 0.0);
                }
            }
            return rr >= 13.0;
        };
    }

    private void dotted(ServerLevel level, Vec3 c, double r, DustParticleOptions dust) {
        int n = Math.max(12, (int) (r * 3));
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2 * i / n;
            level.sendParticles(dust, c.x + Math.cos(a) * r, c.y + 0.15, c.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
        }
    }

    // ---- the orbit

    /** Spirals from her: 3 (phase 2: 5), evenly spread round her facing, winding out to the arena's edge. */
    private void planOrbits(ServerLevel level) {
        orbitPaths.clear();
        int n = phase() == 2 ? 5 : 3;
        Vec3 c = centre();
        for (int i = 0; i < n; i++) {
            double a0 = i * 360.0 / n;
            List<Vec3> path = new ArrayList<>();
            for (int k = 0; k < 24; k++) {
                double r = 1.8 + 0.7 * k;
                Vec3 dir = rotate(forward(), a0 + k * 11.0);
                Vec3 p = position().add(dir.scale(r));
                if (flatDist(p, c) > radius - 0.5) {
                    break;
                }
                Vec3 s = pad(level, p.x, p.z, true);
                if (s == null) {
                    break;
                }
                path.add(s);
            }
            if (!path.isEmpty()) {
                orbitPaths.add(path);
            }
        }
    }

    /** A brass planet flying out along its spiral, one point a tick: 9 (once) to whoever it meets. */
    private Effect planetRun(List<Vec3> path) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (k >= path.size()) {
                return true;
            }
            Vec3 p = path.get(k);
            level.sendParticles(BRASS, p.x, p.y + 1.0, p.z, 6, 0.2, 0.2, 0.2, 0);
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 1.0, p.z, 1, 0.1, 0.1, 0.1, 0.01);
            if (k % 4 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.0F, 0.8F + k * 0.04F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.2 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 9.0F, 0.0, 0.1);
                }
            }
            return false;
        };
    }

    // ---- the gravity well

    /** Everyone within 7 of the well is drawn toward it, slower than walking (they can walk out). */
    private void pull(ServerLevel level, Vec3 w) {
        for (LivingEntity e : victims(level, w, WELL_PULL_R + 1)) {
            Vec3 to = w.subtract(e.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > WELL_PULL_R || d < 0.6 || Math.abs(e.getY() - w.y) > 3.0) {
                continue;
            }
            Vec3 add = to.normalize().scale(0.045);
            Vec3 v = e.getDeltaMovement().add(add);
            double h = Math.hypot(v.x, v.z);
            if (h > 0.3) {
                v = new Vec3(v.x * 0.3 / h, v.y, v.z * 0.3 / h);
            }
            e.setDeltaMovement(v);
            e.hurtMarked = true;
        }
    }

    private void burstWell(ServerLevel level, Vec3 w) {
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, w.x, w.y + 0.6, w.z, 60, 1.2, 0.5, 1.2, 0.3);
        level.sendParticles(VIOLET, w.x, w.y + 0.6, w.z, 30, 1.4, 0.4, 1.4, 0);
        level.sendParticles(ParticleTypes.EXPLOSION, w.x, w.y + 0.5, w.z, 1, 0, 0, 0, 0);
        level.playSound(null, w.x, w.y, w.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.2F, 1.4F);
        for (LivingEntity e : victims(level, w, WELL_R + 1)) {
            if (flatDist(e.position(), w) <= WELL_R + e.getBbWidth() / 2 && Math.abs(e.getY() - w.y) < 2.5) {
                strike(level, e, 10.0F, 0.0, 0.35);
            }
        }
    }

    // ---- the levitation flip

    /** Rings under the players (up to 3), plus one near the target in phase 2; at least 4 apart, inside the rim. */
    private void planFlips(ServerLevel level, @Nullable LivingEntity target) {
        flipSpots.clear();
        flipOwners.clear();
        List<LivingEntity> marks = new ArrayList<>();
        if (target != null) {
            marks.add(target);
        }
        for (Player p : fighters(level)) {
            if (p != target && marks.size() < 3) {
                marks.add(p);
            }
        }
        for (LivingEntity e : marks) {
            Vec3 s = inner(level, e.getX(), e.getZ(), radius - 3.0);
            if (s != null && apart(flipSpots, s, 4.0)) {
                flipSpots.add(s);
                flipOwners.add(e instanceof Player ? e.getUUID() : null);
            }
        }
        if (phase() == 2) {
            Vec3 base = target != null ? target.position() : ahead(6.0);
            for (int tries = 0; tries < 20; tries++) {
                double a = getRandom().nextDouble() * Math.PI * 2;
                double d = 4.0 + getRandom().nextDouble() * 3.0;
                Vec3 s = inner(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d, radius - 3.0);
                if (s != null && apart(flipSpots, s, 4.0)) {
                    flipSpots.add(s);
                    flipOwners.add(null);
                    break;
                }
            }
        }
        if (flipSpots.isEmpty()) {
            Vec3 a = ahead(5.0);
            Vec3 s = inner(level, a.x, a.z, radius - 3.0);
            flipSpots.add(s != null ? s : centre());
            flipOwners.add(null);
        }
    }

    private static boolean apart(List<Vec3> spots, Vec3 s, double min) {
        for (Vec3 o : spots) {
            if (flatDist(o, s) < min) {
                return false;
            }
        }
        return true;
    }

    /** Gravity flips in a ring: 7, then a short straight float up and a slow drift down (no sideways push at all). */
    private void flipAt(ServerLevel level, Vec3 s) {
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, s.x, s.y + 0.5, s.z, 40, FLIP_R * 0.5, 0.8, FLIP_R * 0.5, 0.1);
        level.sendParticles(ParticleTypes.END_ROD, s.x, s.y + 0.3, s.z, 12, FLIP_R * 0.5, 0.2, FLIP_R * 0.5, 0.05);
        for (LivingEntity e : victims(level, s, FLIP_R + 1)) {
            if (flatDist(e.position(), s) <= FLIP_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.0) {
                strike(level, e, 7.0F, 0.0, 0.0);
                if (e.isAlive()) {
                    e.setDeltaMovement(0, Math.max(0, e.getDeltaMovement().y), 0);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 20, 1));
                    e.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 80, 0));
                }
            }
        }
    }

    // ---- the new moon's shades

    /** Lines through the target, the other players, then random platform: 2 (+1 phase 2, more in co-op), at most 4. */
    private void planShades(ServerLevel level, @Nullable LivingEntity target) {
        shadeLines.clear();
        int n = Math.min(4, scaledCount(2) + (phase() == 2 ? 1 : 0));
        List<Vec3> marks = new ArrayList<>();
        if (target != null) {
            marks.add(target.position());
        }
        for (Player p : fighters(level)) {
            if (p != target && marks.size() < n) {
                marks.add(p.position());
            }
        }
        Vec3 c = centre();
        for (int tries = 0; tries < 20 && marks.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = getRandom().nextDouble() * (radius - 4);
            marks.add(new Vec3(c.x + Math.cos(a) * d, c.y, c.z + Math.sin(a) * d));
        }
        for (Vec3 m : marks) {
            if (shadeLines.size() >= n) {
                break;
            }
            double a = getRandom().nextDouble() * Math.PI * 2;
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            List<Vec3> back = new ArrayList<>();
            List<Vec3> fwd = new ArrayList<>();
            for (double d = 0; d <= 9.0; d += 1.0) {
                Vec3 p = inside(level, m.x - dir.x * d, m.z - dir.z * d);
                if (p == null) {
                    break;
                }
                back.add(0, p);
            }
            for (double d = 1.0; d <= 9.0; d += 1.0) {
                Vec3 p = inside(level, m.x + dir.x * d, m.z + dir.z * d);
                if (p == null) {
                    break;
                }
                fwd.add(p);
            }
            List<Vec3> line = new ArrayList<>(back);
            line.addAll(fwd);
            if (line.size() >= 4) {
                shadeLines.add(line);
            }
        }
    }

    /** Open platform at least 1.5 inside the arena's edge, or null. */
    private @Nullable Vec3 inside(ServerLevel level, double x, double z) {
        if (Math.hypot(x - centre().x, z - centre().z) > radius - 1.5) {
            return null;
        }
        return pad(level, x, z, true);
    }

    /** A shadow of her dashing along its line, 0.9 blocks a tick after {@code delay}: 9 and Slowness I 1 s (once). */
    private Effect shadeRun(List<Vec3> line, int delay) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        double len = flatDist(line.get(0), line.get(line.size() - 1));
        int steps = Math.max(2, (int) Math.ceil(len / 0.9));
        return (boss, level) -> {
            int k = t[0]++;
            Vec3 a = line.get(0);
            Vec3 b = line.get(line.size() - 1);
            if (k < delay) {
                if (k % 2 == 0) {
                    level.sendParticles(SHADOW, a.x, a.y + 1.4, a.z, 3, 0.25, 0.8, 0.25, 0);
                    level.sendParticles(RED, b.x, b.y + 0.15, b.z, 1, 0.1, 0, 0.1, 0);
                }
                return false;
            }
            int j = k - delay;
            if (j > steps) {
                level.sendParticles(ParticleTypes.SQUID_INK, b.x, b.y + 1.0, b.z, 10, 0.3, 0.6, 0.3, 0.02);
                return true;
            }
            Vec3 p = a.lerp(b, j / (double) steps);
            level.sendParticles(SHADOW, p.x, p.y + 1.2, p.z, 8, 0.25, 0.8, 0.25, 0);
            level.sendParticles(ParticleTypes.SQUID_INK, p.x, p.y + 1.0, p.z, 2, 0.2, 0.5, 0.2, 0.01);
            if (j == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.2F, 0.6F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.1 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 9.0F, 0.0, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                }
            }
            return false;
        };
    }

    /** A ring running out over the floor from {@code c}: it hits once whoever stands on the floor at its edge (jump). */
    private Effect floorRing(Vec3 c, double max, double speed, float damage, DustParticleOptions dust) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(dust, c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && overFloor(level, e) < 0.6 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.0, 0.3);
                }
            }
            return rr >= max;
        };
    }

    // ---- the comet

    private void cometSlam(ServerLevel level, Vec3 at) {
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.6, 0.2, 0.6, 0);
        level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 0.3, at.z, 30, 1.5, 0.2, 1.5, 0.15);
        level.sendParticles(VIOLET, at.x, at.y + 0.3, at.z, 30, COMET_R * 0.6, 0.2, COMET_R * 0.6, 0);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.9F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 1.4F);
        for (LivingEntity e : victims(level, at, COMET_R + 1)) {
            if (flatDist(e.position(), at) <= COMET_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                strike(level, e, 13.0F, 0.0, 0.3);
            }
        }
    }

    // ---- the adds (End creatures of the mod)

    private int liveAdds(ServerLevel level) {
        adds.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        return adds.size();
    }

    private void spawnAdds(ServerLevel level, int base) {
        int n = Math.min(3 - liveAdds(level), scaledCount(base));
        for (int i = 0; i < n; i++) {
            EntityType<? extends Mob> type = i % 2 == 0 ? ModEntities.VOID_LARVA.get() : ModEntities.STAR_MOTE.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                at = inside(level, getX() + Math.cos(a) * 3.5, getZ() + Math.sin(a) * 3.5);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.PORTAL, at.x, at.y + 0.5, at.z, 30, 0.4, 0.6, 0.4, 0.5);
        }
        level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.5F);
    }

    private void discardAdds(ServerLevel level) {
        for (UUID id : adds) {
            var e = level.getEntity(id);
            if (e != null && e.isAlive()) {
                level.sendParticles(ParticleTypes.POOF, e.getX(), e.getY() + 0.5, e.getZ(), 10, 0.3, 0.3, 0.3, 0.02);
                e.discard();
            }
        }
        adds.clear();
    }

    // ------------------------------------------------------------------ phase 3: the eclipse

    private void eclipse(ServerLevel level) {
        eclipsed = true;
        entityData.set(DATA_MOON, MOON_ECLIPSE);
        sweepTimer = 80;
        meteorTimer = 60;
        beamTick = -1;
        dimCore(level);
        addEffect(floorRing(position(), radius, 0.55, 10.0F, SHADOW));
        for (Player p : fighters(level)) {
            p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 40, 0, false, false));
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("moon_warden_eclipse"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 k = core();
        level.sendParticles(CORONA, k.x, k.y, k.z, 120, 4.0, 4.0, 4.0, 0);
        level.sendParticles(ParticleTypes.SQUID_INK, k.x, k.y, k.z, 60, 3.0, 3.0, 3.0, 0.05);
        level.playSound(null, k.x, k.y, k.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 4.0F, 0.4F);
        level.playSound(null, this, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /** The core's sea lanterns turn to tinted glass while it is eclipsed (all put back afterwards). */
    private void dimCore(ServerLevel level) {
        Vec3 k = core();
        BlockPos c = BlockPos.containing(k);
        BlockState dark = Blocks.TINTED_GLASS.defaultBlockState();
        for (BlockPos p : BlockPos.betweenClosed(c.offset(-6, -6, -6), c.offset(6, 6, 6))) {
            if (p.distToCenterSqr(k) > 36.0 || !level.isLoaded(p) || temps.containsKey(p.asLong())) {
                continue;
            }
            BlockState s = level.getBlockState(p);
            if (s.is(Blocks.SEA_LANTERN)) {
                temps.put(p.asLong(), new Temp(s, dark));
                level.setBlock(p, dark, 3);
            }
        }
    }

    private void clearTemp(ServerLevel level, long key) {
        Temp t = temps.remove(key);
        BlockPos p = BlockPos.of(key);
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        if (level.getBlockState(p).getBlock() == t.placed().getBlock()) {
            level.setBlock(p, t.original(), 3);
        }
    }

    /** Every changed block goes back (only where it is still the one set). */
    private void restoreAll(ServerLevel level) {
        for (SavedTemp s : staleTemps) {
            temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed()));
        }
        staleTemps.clear();
        for (Long key : new ArrayList<>(temps.keySet())) {
            clearTemp(level, key);
        }
    }

    /** Beam {@code i}'s bearing (degrees) at the current tick of the sweep. */
    private double beamAngle(int i) {
        int turn = Math.max(0, beamTick - BEAM_DRAW);
        return beamStart + i * (360.0 / BEAMS) + beamDir * BEAM_SPEED * turn;
    }

    /**
     * The gravity sweep: three beams from the core onto the platform, radial lines from 2.5 out to the edge, drawn for
     * 2 s (red the last 0.5 s, arrows showing the way they will turn), then they turn round the platform at 0.75° a
     * tick for 7 s: 5 and Slowness I 1 s, at most every 10 ticks, to whoever they cross. Walk with the gap.
     */
    private void tickSweep(ServerLevel level) {
        Vec3 c = centre();
        Vec3 k = core();
        boolean drawing = beamTick < BEAM_DRAW;
        if (beamTick == 0) {
            for (Player p : fighters(level)) {
                p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 30, 0, false, false));
            }
            level.playSound(null, k.x, k.y, k.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
        }
        if (beamTick == BEAM_DRAW) {
            level.playSound(null, k.x, k.y, k.z, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
        for (int i = 0; i < BEAMS; i++) {
            double a = Math.toRadians(beamAngle(i));
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            if (beamTick % 2 == 0) {
                DustParticleOptions d = drawing ? (beamTick >= BEAM_DRAW - 10 ? RED : VIOLET) : VIOLET;
                for (double r = 2.5; r <= radius; r += 1.0) {
                    Vec3 p = c.add(dir.scale(r));
                    level.sendParticles(d, p.x, c.y + 0.15, p.z, 1, 0, 0, 0, 0);
                    if (!drawing) {
                        level.sendParticles(ParticleTypes.END_ROD, p.x, c.y + 0.3 + getRandom().nextDouble() * 2.0, p.z, 1, 0.05, 0.2, 0.05, 0);
                    }
                }
                if (drawing) {                                              // arrows: the way the beam will turn
                    Vec3 side = rotate(dir, beamDir * 90.0);
                    for (double r = 5.0; r <= radius; r += 5.0) {
                        Vec3 p = c.add(dir.scale(r)).add(side.scale(0.8));
                        level.sendParticles(GOLD, p.x, c.y + 0.2, p.z, 1, 0, 0, 0, 0);
                    }
                }
                Vec3 foot = c.add(dir.scale(radius * 0.5));
                for (double f = 0.1; f < 1.0; f += 0.15) {                  // the beam's line down from the core
                    Vec3 p = k.lerp(foot, f);
                    level.sendParticles(drawing ? SHADOW : VIOLET, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
                }
            }
            if (drawing) {
                continue;
            }
            for (LivingEntity e : victims(level, c, radius + 2)) {
                Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                double along = to.dot(dir);
                double side = Math.abs(to.x * dir.z - to.z * dir.x);
                if (along >= 2.5 && along <= radius + 1.0 && side <= 0.8 + e.getBbWidth() / 2 && Math.abs(e.getY() - c.y) < 3.5
                        && beamTick - beamHits.getOrDefault(e.getUUID(), -99) >= 10) {
                    beamHits.put(e.getUUID(), beamTick);
                    strike(level, e, 5.0F, 0.0, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                }
            }
        }
        if (++beamTick >= BEAM_DRAW + BEAM_TURN) {
            beamTick = -1;
            beamHits.clear();
        }
    }

    /** Meteors: one on the target, one on each of up to 2 other players, the rest on random platform; at most 4. */
    private void castMeteors(ServerLevel level, @Nullable LivingEntity target) {
        int n = Math.min(4, scaledCount(2));
        List<Vec3> marks = new ArrayList<>();
        if (target != null) {
            Vec3 s = inner(level, target.getX(), target.getZ(), radius - 2.0);
            if (s != null) {
                marks.add(s);
            }
        }
        int extra = 0;
        for (Player p : fighters(level)) {
            if (p != target && extra++ < 2) {
                Vec3 s = inner(level, p.getX(), p.getZ(), radius - 2.0);
                if (s != null && apart(marks, s, 3.0)) {
                    marks.add(s);
                }
            }
        }
        Vec3 c = centre();
        for (int tries = 0; tries < 20 && marks.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = getRandom().nextDouble() * (radius - 3);
            Vec3 s = pad(level, c.x + Math.cos(a) * d, c.z + Math.sin(a) * d, true);
            if (s != null && apart(marks, s, 3.0)) {
                marks.add(s);
            }
        }
        for (Vec3 m : marks) {
            addEffect(meteor(m));
        }
    }

    /** A meteor: its circle (r 2.2) drawn 30 ticks (red the last 10), falling in the last 12; 8 and a small lift. */
    private Effect meteor(Vec3 at) {
        int[] t = {0};
        Vec3 from = at.add(4.0 - getRandom().nextDouble() * 8.0, 20.0, 4.0 - getRandom().nextDouble() * 8.0);
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, METEOR_R, k >= 20 ? RED : VIOLET);
                }
                if (k >= 18) {
                    Vec3 p = from.lerp(at, (k - 18) / 12.0);
                    level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 4, 0.2, 0.2, 0.2, 0.01);
                    level.sendParticles(VIOLET, p.x, p.y, p.z, 4, 0.3, 0.3, 0.3, 0);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y + 0.5, p.z, 1, 0.1, 0.1, 0.1, 0);
                }
                if (k == 18) {
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST_FAR, SoundSource.HOSTILE, 2.0F, 0.5F);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 0.3, at.z, 20, 1.0, 0.3, 1.0, 0.1);
            level.sendParticles(VIOLET, at.x, at.y + 0.3, at.z, 24, METEOR_R * 0.5, 0.2, METEOR_R * 0.5, 0);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.4F, 1.1F);
            for (LivingEntity e : boss.victims(level, at, METEOR_R + 1)) {
                if (flatDist(e.position(), at) <= METEOR_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                    boss.strike(level, e, 8.0F, 0.0, 0.3);
                }
            }
            return true;
        };
    }

    /** The eclipse over the platform: dark motes, a corona flickering round the core. */
    private void eclipseWeather(ServerLevel level) {
        Vec3 c = centre();
        Vec3 k = core();
        if (tickCount % 3 == 0) {
            double r = radius - 1.0;
            for (int i = 0; i < 3; i++) {
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                level.sendParticles(SHADOW, x, c.y + 1 + getRandom().nextDouble() * 8, z, 1, 0.2, 0.2, 0.2, 0);
            }
            level.sendParticles(CORONA, k.x, k.y, k.z, 3, 3.5, 3.5, 3.5, 0);
        }
        if (tickCount % 140 == 0) {
            level.playSound(null, k.x, k.y, k.z, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(CORONA, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.HOSTILE, 0.8F, 1.4F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardAdds(level);
        setNoGravity(false);
    }

    /** Back to the first phase (the fight was reset): the core lights up again, the dial waxes, base speed. */
    private void resetForm(ServerLevel level) {
        eclipsed = false;
        roarUntil = -1;
        guard = 0;
        beamTick = -1;
        beamHits.clear();
        moonTimer = 160;
        entityData.set(DATA_MOON, MOON_WAXING);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("moon_warden_eclipse"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("moon_warden_wrath"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleTemps.isEmpty()) {                       // saved by an unload: put back on the first tick
            restoreAll(level);
            if (eclipsed && phase() == 2) {
                dimCore(level);                            // still eclipsed: dim it again, fresh
            }
        }
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        if (isNoGravity() && (cur == null || !"comet".equals(cur.name))) {
            setNoGravity(false);                           // a dive cut short (stagger, phase change)
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && !temps.isEmpty()) {
            restoreAll(level);                             // the arena emptied (death, flight)
        }
        if (phase() == 1 && (eclipsed || moon() == MOON_ECLIPSE)) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !eclipsed && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "eclipse");
            free = false;
        }
        // the moon's phases turn on her dial: the new moon sends her shades, the full moon her radiance
        if (!eclipsed && fighting && cur == null && --moonTimer <= 0 && free) {
            moonTimer = Math.max(120, (int) Math.round(MOON_EVERY * cooldownScale()));
            int next = (moon() + 1) % 4;
            setMoon(level, next);
            if (next == MOON_NEW) {
                chain(level, "shade");
            } else if (next == MOON_FULL) {
                chain(level, "radiance");
            }
        }
        // phase 3: the gravity beams sweep round, and meteors fall between the sweeps
        if (eclipsed && phase() == 2 && anyone) {
            eclipseWeather(level);
            cur = currentAttack();
            boolean busy = cur != null && "eclipse".equals(cur.name);
            if (beamTick >= 0) {
                tickSweep(level);
            } else if (fighting && !busy && guard == 0) {
                if (--sweepTimer <= 0) {
                    sweepTimer = Math.max(200, (int) Math.round(SWEEP_EVERY * cooldownScale()));
                    beamStart = getRandom().nextDouble() * 360.0;
                    beamDir = -beamDir;
                    beamTick = 0;
                    beamHits.clear();
                } else if (--meteorTimer <= 0) {
                    meteorTimer = Math.max(60, (int) Math.round(METEOR_EVERY * cooldownScale()));
                    castMeteors(level, target);
                }
            }
        }
        // ambience: the thrusters under her hem, starlight off the cloak
        if (tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 0.1, getZ(), 1, 0.35, 0.0, 0.35, 0.01);
        }
        if (tickCount % 10 == 0) {
            level.sendParticles(eclipsed ? CORONA : SILVER, getX(), getY() + 1.5, getZ(), 1, 0.5, 0.8, 0.5, 0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("moon_warden_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: over a void, take it back (gently inward where needed)
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z).scale(0.3));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.2), h.z);
            e.hurtMarked = true;
        }
        Vec3 d = dial();
        level.sendParticles(MOONLIGHT, d.x, d.y, d.z, 40, 1.0, 1.0, 1.0, 0.05);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 30, 1.5, 1.5, 1.5, 0.1);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        Vec3 d = dial();
        level.sendParticles(ParticleTypes.END_ROD, d.x, d.y, d.z, 80, 1.5, 1.5, 1.5, 0.1);
        level.sendParticles(BRASS, getX(), getY() + 2.5, getZ(), 40, 1.0, 1.0, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.0F, 1.2F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            restoreAll(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("MoonCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("MoonRadius", radius);
        output.putBoolean("MoonEclipsed", eclipsed);
        output.putInt("MoonPhase", moon());
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("MoonBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("MoonCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("MoonRadius", 15);
        floorTol = -1;
        eclipsed = input.getBooleanOr("MoonEclipsed", false) && phase() == 2;
        int m = input.getIntOr("MoonPhase", MOON_WAXING);
        entityData.set(DATA_MOON, eclipsed ? MOON_ECLIPSE : Mth.clamp(m, 0, 3));
        staleTemps.clear();
        input.read("MoonBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
    }
}
