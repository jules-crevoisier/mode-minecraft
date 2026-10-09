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
import net.minecraft.world.level.block.LightBlock;
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

import static com.brasshaven.generated.MobAnims.Ringmaster.CANE;
import static com.brasshaven.generated.MobAnims.Ringmaster.CAROUSEL;
import static com.brasshaven.generated.MobAnims.Ringmaster.FINALE;
import static com.brasshaven.generated.MobAnims.Ringmaster.FLOURISH;
import static com.brasshaven.generated.MobAnims.Ringmaster.HAT;
import static com.brasshaven.generated.MobAnims.Ringmaster.JUGGLE;
import static com.brasshaven.generated.MobAnims.Ringmaster.PERFORMERS;
import static com.brasshaven.generated.MobAnims.Ringmaster.ROAR;
import static com.brasshaven.generated.MobAnims.Ringmaster.STAGGER;

/**
 * Le Monsieur Loyal mécanique (The Clockwork Ringmaster), the champion of the Clockwork Carnival: a tall brass showman
 * (3.6 blocks) in a scarlet tailcoat and a towering top hat, a wind-up key turning in his back, a telescoping cane in
 * his right hand and a juggling bomb in his left. He still runs the show in the big top's sawdust ring (36 wide,
 * benches rising all round it) for an audience that left long ago.
 * <ul>
 *     <li>Phase 1: the <b>cane</b> (a whip sweep round his front, then a crack straight down a red line), the
 *     <b>juggle</b> (brass bombs lobbed one after another onto marked circles), the <b>hat</b> (his top hat sails out
 *     along a marked line and back), the <b>flourish</b> (a lunge across the ring down a marked lane).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>performers</b> (clockwork spiders and rust mites tumble in), the
 *     <b>carousel</b> (fire posts on a circle round the ring's centre turn slowly: stay inside or outside it), more
 *     bombs.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the <b>finale</b>. A confetti ring runs out
 *     over the ring, then a spotlight from the great chandelier hunts one player after another (slower than walking)
 *     and blasts where it stops, and confetti charges burst on marked circles.</li>
 * </ul>
 * The only blocks he changes are the spotlight's invisible light blocks (one at a time, where the beam falls): each
 * goes back when the beam moves on or ends, when the fight resets, the arena empties, he dies or is removed, and on the
 * first tick after a reload.
 */
public class Ringmaster extends WayfarerBoss {
    public static final float WIDTH = 1.2F;
    public static final float HEIGHT = 3.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double CANE_RANGE = 5.5;
    private static final double CANE_HALF = 75;
    private static final double CRACK_LEN = 7.0;
    private static final double CRACK_HALF = 0.9;
    private static final double BOMB_R = 2.2;
    private static final double HAT_HALF = 1.2;
    private static final double LANE_HALF = 1.2;
    private static final double POST_RING = 12.0;
    private static final double POST_R = 1.5;
    private static final double CAROUSEL_SPEED = 1.2;      // degrees a tick: 0.25 blocks a tick on the post circle
    private static final double SPOT_R = 2.0;
    private static final double SPOT_SPEED = 0.17;         // blocks a tick: slower than walking
    private static final double SPOT_UP = 23.0;            // the great chandelier over the ring's centre
    private static final int SPOT_HUNT = 100;
    private static final int SPOT_HOLD = 20;
    private static final int SPOT_EVERY = 240;
    private static final int CONFETTI_EVERY = 100;
    private static final double CONFETTI_R = 2.0;
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.5F);
    private static final DustParticleOptions WHITE = new DustParticleOptions(0xF6F2E8, 1.5F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xD6A64C, 1.6F);
    private static final DustParticleOptions SILK = new DustParticleOptions(0x2A2430, 1.6F);
    private static final DustParticleOptions BEAM = new DustParticleOptions(0xFFF6D0, 1.2F);
    private static final DustParticleOptions[] CONFETTI = {
            new DustParticleOptions(0xE8323C, 1.2F), new DustParticleOptions(0xF2C641, 1.2F),
            new DustParticleOptions(0x4FA8E8, 1.2F), new DustParticleOptions(0x6CD06C, 1.2F),
            new DustParticleOptions(0xE070D0, 1.2F)};

    private record Temp(BlockState original, BlockState placed) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 22;
    private double floorTol = -1;
    /** Phase 3 has started (the Grand Finale). */
    private boolean finale;
    private int guard;
    private int roarUntil = -1;
    private int spotTimer = 40;
    private int confettiTimer = 60;
    // the spotlight of the finale: -1 idle, else its tick
    private int spotTick = -1;
    private @Nullable Vec3 spotAt;
    private @Nullable UUID spotOwner;
    private int spotTurn;
    private @Nullable BlockPos spotLight;
    // moves in flight
    private final List<Vec3> bombSpots = new ArrayList<>();
    private final List<Vec3> hatPath = new ArrayList<>();
    private final List<Vec3> lane = new ArrayList<>();
    private final Set<UUID> laneHit = new HashSet<>();
    private double carouselStart;
    private int carouselDir = 1;
    private final Map<UUID, Integer> postHits = new HashMap<>();
    private final Set<UUID> adds = new HashSet<>();
    // the spotlight's light blocks with their original state
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public Ringmaster(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 640.0)
                .add(Attributes.ARMOR, 11.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Ringmaster.TICKS;
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
        return 115.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (the sawdust ring)

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

    /** The ring's usable radius: the sawdust inside the curb (17.5 in the big top), never more than the seal's. */
    private double ringR() {
        return Math.min(radius, 17.5);
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

    /** Whether the floor round the seal is flat (the ring) or rough (a command spawn somewhere else). */
    private double floorTol(ServerLevel level) {
        if (floorTol > 0) {
            return floorTol;
        }
        Vec3 c = centre();
        int flat = 0;
        int samples = 0;
        for (int i = 0; i < 48; i++) {
            double a = i * 2.39996;
            double d = Math.sqrt((i + 0.5) / 48.0) * Math.max(3, ringR() - 1);
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
     * A spot of open ring at (x, z): floor within the tolerance of the seal's level, two blocks of air over it, within
     * the ring's radius; or null (the curb's king poles, the benches, the tunnels).
     */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z) {
        Vec3 c = centre();
        if (Math.hypot(x - c.x, z - c.z) > ringR() + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > floorTol(level) || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Open ring at (x, z), moved toward the centre until it lies within {@code maxR} of it; or null. */
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

    private static boolean apart(List<Vec3> spots, Vec3 s, double min) {
        for (Vec3 o : spots) {
            if (flatDist(o, s) < min) {
                return false;
            }
        }
        return true;
    }

    /**
     * Pushes stay on the sawdust: a push is kept only when open ring lies 1.5 blocks along it (not into the curb's king
     * poles, the benches or a tunnel mouth); otherwise it is dropped.
     */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        Vec3 flat = new Vec3(push.x, 0, push.z);
        if (flat.lengthSqr() < 1.0E-6) {
            return Vec3.ZERO;
        }
        Vec3 probe = e.position().add(flat.normalize().scale(1.5));
        return pad(level, probe.x, probe.z) == null ? Vec3.ZERO : flat;
    }

    /** Pushes capped at 1.0 and lift at 0.45 (0.2 when the push was dropped at the ring's edge). */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.0, knockback));
        }
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 safe = safePush(level, e, push);
        boolean dropped = push.lengthSqr() > 1.0E-6 && safe.lengthSqr() < 1.0E-6;
        lift = Math.min(lift, dropped ? 0.2 : 0.45);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
    }

    private Vec3 hand() {
        return position().add(0, 2.2, 0).add(rotate(forward(), -90).scale(0.5));
    }

    private void confetti(ServerLevel level, Vec3 at, int count, double spread) {
        for (DustParticleOptions d : CONFETTI) {
            level.sendParticles(d, at.x, at.y, at.z, count, spread, spread * 0.6, spread, 0.0);
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // cane: he cocks the cane over his shoulder while it telescopes out (0.7 s, an arc drawn gold, red from 0.45 s)
        // and whips it round his front: 12 and a push; he turns (up to 20°), a red line is drawn ahead and the cane
        // cracks straight down it 0.4 s later: 10 and a small lift
        out.add(BossAttack.of("cane").anim(CANE).timing(14, 16, 14).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        DustParticleOptions d = tick >= 9 ? RED : GOLD;
                        b.telegraphArc(level, CANE_RANGE, CANE_HALF, d);
                        b.telegraphArc(level, CANE_RANGE - 2.0, CANE_HALF, d);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> caneSweep(level))
                .active((b, level, t, tick) -> {
                    if (tick == 1) {
                        turnToward(t, 20.0F);
                    }
                    if (tick >= 1 && tick < 8 && tick % 2 == 1) {
                        drawLine(level, position(), forward(), CRACK_LEN, CRACK_HALF, RED);
                    }
                    if (tick == 8) {
                        caneCrack(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) > 6.0 ? "flourish" : "juggle");
                    }
                })
                .build());
        // juggle: he juggles faster and faster (1.0 s) while gold circles mark where the bombs will land (3, more in co-op,
        // +2 in phase 2, at most 6); he flings them up at 1.0 s: one leaves every 0.25 s, flies 0.8 s, its circle turns red
        // for the last 0.5 s; each bursts in confetti: 9 and a small lift
        out.add(BossAttack.of("juggle").anim(JUGGLE).timing(20, 20, 14).range(4.0, 22.0).cooldown(120).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planBombs(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Vec3 s : bombSpots) {
                            b.telegraphRing(level, s, BOMB_R, GOLD);
                        }
                    }
                    Vec3 h = hand();
                    level.sendParticles(ParticleTypes.SMALL_FLAME, h.x, h.y + 0.4 + (tick % 5) * 0.15, h.z, 1, 0.05, 0.05, 0.05, 0);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.0F, 1.4F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int i = 0; i < bombSpots.size(); i++) {
                        b.addEffect(bombLob(hand(), bombSpots.get(i), i * 5));
                    }
                    level.playSound(null, b, SoundEvents.FIREWORK_ROCKET_LAUNCH, SoundSource.HOSTILE, 1.5F, 0.8F);
                })
                .build());
        // hat: he lifts his top hat (0.45 s) and spins it out at 0.9 s along a marked line (to you + 2, at most 12, drawn
        // white, red from 0.6 s); it sails out at 0.8 blocks a tick and back again: 8 and Slowness I 1 s on each pass
        out.add(BossAttack.of("hat").anim(HAT).timing(18, 30, 14).range(3.0, 18.0).cooldown(100).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planHat(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 12 ? RED : WHITE;
                        for (int k = 0; k < hatPath.size(); k += 1) {
                            Vec3 p = hatPath.get(k);
                            Vec3 side = rotate(forward(), 90).scale(HAT_HALF);
                            level.sendParticles(d, p.x + side.x, p.y + 0.15, p.z + side.z, 1, 0, 0, 0, 0);
                            level.sendParticles(d, p.x - side.x, p.y + 0.15, p.z - side.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(hatFlight(new ArrayList<>(hatPath)));
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 1.2F);
                })
                .build());
        // flourish: he crouches and levels the cane like a rapier (0.8 s); a lane (half width 1.2) toward you over open
        // ring is drawn gold while he turns after you (until 0.5 s), then red; at 0.8 s he lunges down it in 0.3 s: 13 and
        // a push to whoever he meets
        out.add(BossAttack.of("flourish").anim(FLOURISH).timing(16, 8, 16).range(6.0, 16.0).cooldown(80).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    laneHit.clear();
                    planLane(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 4.0F);
                        planLane(level, t);
                    }
                    if (tick % 2 == 0 && !lane.isEmpty()) {
                        drawLine(level, position(), forward(), flatDist(position(), lane.get(lane.size() - 1)), LANE_HALF,
                                tick >= 10 ? RED : GOLD);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (lane.isEmpty() || tick > 5) {
                        return;
                    }
                    Vec3 end = lane.get(lane.size() - 1);
                    Vec3 step = end.subtract(position()).multiply(1, 0, 1).scale(1.0 / (6 - tick));
                    move(MoverType.SELF, step);
                    setDeltaMovement(Vec3.ZERO);
                    level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 1.5, getZ(), 6, 0.4, 0.6, 0.4, 0.1);
                    level.sendParticles(GOLD, getX(), getY() + 1.0, getZ(), 3, 0.3, 0.5, 0.3, 0);
                    for (LivingEntity e : victims(level, position(), 3.0)) {
                        if (flatDist(e.position(), position()) <= 1.6 + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 2.5
                                && laneHit.add(e.getUUID())) {
                            strike(level, e, 13.0F, 0.7, 0.2);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.TRIDENT_RIPTIDE_1.value(), SoundSource.HOSTILE, 1.5F, 1.3F);
                    }
                })
                .end((b, level, t, tick) -> setDeltaMovement(Vec3.ZERO))
                .build());

        // ---------------------------------------------------------------- phase 2
        // performers: he doffs his hat in a sweeping bow (1.0 s): clockwork spiders and rust mites tumble in (2, more in
        // co-op), never more than 3 at once
        out.add(BossAttack.of("performers").anim(PERFORMERS).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600)
                .weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        confetti(level, position().add(0, 2.5, 0), 1, 0.6);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 1.5F, 1.0F);
                    }
                })
                .impact((b, level, t, tick) -> spawnAdds(level, 2))
                .build());
        // carousel: he plants the cane and throws his arms wide (1.2 s); six fire posts (eight in phase 3) on a circle of
        // 12 round the ring's centre are drawn gold, with arrows showing the way they will turn (red for the last 0.4
        // s); then they turn for 4 s at 1.2° a tick (0.25 blocks a tick): 6 and fire 2 s within 1.5 of a post, at most
        // every 0.75 s. Stand inside or outside their circle
        out.add(BossAttack.of("carousel").anim(CAROUSEL).phaseTwo().timing(24, 80, 16).range(0, 30.0).cooldown(420).weight(5)
                .track(false)
                .start((b, level, t, tick) -> {
                    carouselStart = getRandom().nextDouble() * 360.0;
                    carouselDir = -carouselDir;
                    postHits.clear();
                    level.playSound(null, b, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 2.0F, 0.8F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 != 0) {
                        return;
                    }
                    DustParticleOptions d = tick >= 16 ? RED : GOLD;
                    for (Vec3 p : posts(level, 0)) {
                        b.telegraphRing(level, p, POST_R, d);
                        Vec3 tangent = rotate(p.subtract(centre()).multiply(1, 0, 1), carouselDir * 90.0);
                        for (double s = 1.0; s <= 2.5; s += 0.5) {
                            Vec3 q = p.add(tangent.scale(s));
                            level.sendParticles(GOLD, q.x, q.y + 0.2, q.z, 1, 0, 0, 0, 0);
                        }
                        level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y + 0.3, p.z, 1, 0.2, 0.1, 0.2, 0.01);
                    }
                })
                .active((b, level, t, tick) -> carouselTick(level, tick))
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // finale: arms rising, the key whirring, the hat lifting on a jet of steam (2.0 s, guarded; rings of confetti
        // gather on him); he flings his arms high: a ring of confetti runs out over the ring (10, jump it)
        out.add(BossAttack.of("finale").anim(FINALE).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(0.8, 12.0 - tick * 0.28), CONFETTI[(tick / 3) % CONFETTI.length]);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 3.9, getZ(), 2, 0.1, 0.2, 0.1, 0.02);
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> startFinale(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double len, double half, DustParticleOptions d) {
        Vec3 side = rotate(dir, 90).scale(half);
        for (double s = 1.0; s <= len; s += 1.0) {
            Vec3 p = from.add(dir.scale(s));
            level.sendParticles(d, p.x + side.x, p.y + 0.15, p.z + side.z, 1, 0, 0, 0, 0);
            level.sendParticles(d, p.x - side.x, p.y + 0.15, p.z - side.z, 1, 0, 0, 0, 0);
        }
    }

    private void caneSweep(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(CANE_HALF));
        for (LivingEntity e : victims(level, position(), CANE_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= CANE_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 12.0F, 0.6, 0.2);
            }
        }
        for (double a = -CANE_HALF; a <= CANE_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(CANE_RANGE - 0.8));
            level.sendParticles(BRASS, p.x, p.y + 1.3, p.z, 2, 0.1, 0.2, 0.1, 0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.8F);
    }

    private void caneCrack(ServerLevel level) {
        Vec3 fwd = forward();
        for (LivingEntity e : victims(level, position(), CRACK_LEN + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= CRACK_LEN && side <= CRACK_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 10.0F, 0.0, 0.25);
            }
        }
        for (double s = 1.0; s <= CRACK_LEN; s += 0.5) {
            Vec3 p = position().add(fwd.scale(s));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.3, p.z, 2, 0.1, 0.1, 0.1, 0.05);
        }
        Vec3 tip = ahead(CRACK_LEN);
        level.sendParticles(ParticleTypes.FIREWORK, tip.x, tip.y + 0.4, tip.z, 6, 0.2, 0.2, 0.2, 0.05);
        level.playSound(null, tip.x, tip.y, tip.z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 1.5F, 1.6F);
    }

    // ---- the juggling bombs

    /** The target's spot, then more round it (3-7 from it, 3.5 apart), all on open ring. */
    private void planBombs(ServerLevel level, @Nullable LivingEntity target) {
        bombSpots.clear();
        int n = Math.min(6, scaledCount(3) + (phase() == 2 ? 2 : 0));
        Vec3 base = target != null ? target.position() : ahead(6.0);
        Vec3 first = inner(level, base.x, base.z, ringR() - 1.5);
        if (first != null) {
            bombSpots.add(first);
        }
        for (Player p : fighters(level)) {
            if (p != target && bombSpots.size() < n) {
                Vec3 s = inner(level, p.getX(), p.getZ(), ringR() - 1.5);
                if (s != null && apart(bombSpots, s, 3.5)) {
                    bombSpots.add(s);
                }
            }
        }
        for (int tries = 0; tries < 30 && bombSpots.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 3.0 + getRandom().nextDouble() * 4.0;
            Vec3 s = inner(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d, ringR() - 1.5);
            if (s != null && apart(bombSpots, s, 3.5)) {
                bombSpots.add(s);
            }
        }
        if (bombSpots.isEmpty()) {
            bombSpots.add(centre());
        }
    }

    /** A bomb lobbed after {@code delay}: 16 ticks in the air (its circle red for the last 10), then 9 and a lift. */
    private Effect bombLob(Vec3 from, Vec3 at, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, BOMB_R, GOLD);
                }
                return false;
            }
            int j = k - delay;
            if (j < 16) {
                double f = (j + 1) / 16.0;
                Vec3 p = from.lerp(at, f).add(0, Math.sin(f * Math.PI) * 5.0, 0);
                level.sendParticles(BRASS, p.x, p.y, p.z, 3, 0.08, 0.08, 0.08, 0);
                level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y + 0.3, p.z, 1, 0.02, 0.02, 0.02, 0);
                if (j % 2 == 0) {
                    boss.telegraphRing(level, at, BOMB_R, j >= 6 ? RED : GOLD);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.FIREWORK, at.x, at.y + 0.6, at.z, 14, 0.6, 0.4, 0.6, 0.08);
            ((Ringmaster) boss).confetti(level, at.add(0, 1.0, 0), 5, 1.0);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 1.5F, 1.0F);
            for (LivingEntity e : boss.victims(level, at, BOMB_R + 1)) {
                if (flatDist(e.position(), at) <= BOMB_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                    boss.strike(level, e, 9.0F, 0.3, 0.3);
                }
            }
            return true;
        };
    }

    // ---- the top hat

    /** Points every 0.8 along his facing over open ring, to the target + 2, at most 12. */
    private void planHat(ServerLevel level, @Nullable LivingEntity target) {
        hatPath.clear();
        double len = target != null ? Math.min(12.0, distanceTo(target) + 2.0) : 10.0;
        Vec3 fwd = forward();
        for (double d = 1.2; d <= len; d += 0.8) {
            Vec3 p = position().add(fwd.scale(d));
            Vec3 s = pad(level, p.x, p.z);
            if (s == null) {
                break;
            }
            hatPath.add(s);
        }
        if (hatPath.isEmpty()) {
            hatPath.add(ahead(1.2));
        }
    }

    /** The hat sails out along its path one point a tick and back again: 8 and Slowness I 1 s, once per pass. */
    private Effect hatFlight(List<Vec3> path) {
        int[] t = {0};
        Set<UUID> out = new HashSet<>();
        Set<UUID> back = new HashSet<>();
        int n = path.size();
        return (boss, level) -> {
            int k = t[0]++;
            if (k >= 2 * n) {
                return true;
            }
            boolean returning = k >= n;
            Vec3 p = path.get(returning ? 2 * n - 1 - k : k);
            level.sendParticles(SILK, p.x, p.y + 1.3, p.z, 6, 0.3, 0.12, 0.3, 0);
            level.sendParticles(RED, p.x, p.y + 1.2, p.z, 2, 0.3, 0.05, 0.3, 0);
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 1, 0, 0, 0, 0);
            if (k % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.8F, 1.6F);
            }
            Set<UUID> hit = returning ? back : out;
            for (LivingEntity e : boss.victims(level, p, 2.5)) {
                if (flatDist(e.position(), p) <= HAT_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 8.0F, 0.0, 0.1);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                }
            }
            return false;
        };
    }

    // ---- the flourish

    /** Open ring along his facing (every 0.5) to the target + 2, at most 12, with headroom for him. */
    private void planLane(ServerLevel level, @Nullable LivingEntity target) {
        lane.clear();
        double len = target != null ? Math.min(12.0, distanceTo(target) + 2.0) : 8.0;
        Vec3 fwd = forward();
        for (double d = 0.5; d <= len; d += 0.5) {
            Vec3 p = position().add(fwd.scale(d));
            Vec3 s = pad(level, p.x, p.z);
            if (s == null || !clear(level, s.x, s.y, s.z, 4)) {
                break;
            }
            lane.add(s);
        }
    }

    // ---- the carousel of fire

    /** The fire posts on the circle round the ring's centre at {@code tick} of the turn (only those on open ring). */
    private List<Vec3> posts(ServerLevel level, int tick) {
        List<Vec3> out = new ArrayList<>();
        int n = finale ? 8 : 6;
        double r = Math.min(POST_RING, ringR() - 3.0);
        Vec3 c = centre();
        for (int i = 0; i < n; i++) {
            double a = Math.toRadians(carouselStart + i * 360.0 / n + carouselDir * CAROUSEL_SPEED * tick);
            Vec3 s = pad(level, c.x + Math.cos(a) * r, c.z + Math.sin(a) * r);
            if (s != null) {
                out.add(s);
            }
        }
        return out;
    }

    private void carouselTick(ServerLevel level, int tick) {
        for (Vec3 p : posts(level, tick)) {
            level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.2, p.z, 5, 0.25, 1.0, 0.25, 0.01);
            if (tick % 2 == 0) {
                level.sendParticles(BRASS, p.x, p.y + 0.2, p.z, 3, 0.4, 0.05, 0.4, 0);
                level.sendParticles(ParticleTypes.LAVA, p.x, p.y + 2.5, p.z, 1, 0.1, 0.1, 0.1, 0);
            }
            for (LivingEntity e : victims(level, p, POST_R + 1.5)) {
                if (flatDist(e.position(), p) <= POST_R + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 3.0
                        && tick - postHits.getOrDefault(e.getUUID(), -99) >= 15) {
                    postHits.put(e.getUUID(), tick);
                    strike(level, e, 6.0F, 0.0, 0.1);
                    e.igniteForSeconds(2.0F);
                }
            }
        }
        if (tick % 20 == 0) {
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 1.5F, 0.6F + (tick / 20) * 0.1F);
            Vec3 c = centre();
            level.playSound(null, c.x, c.y, c.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.0F, 0.8F);
        }
    }

    // ---- the performers (clockwork creatures of the mod)

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
            EntityType<? extends Mob> type = i % 2 == 0 ? ModEntities.CLOCKWORK_SPIDER.get() : ModEntities.RUST_MITE.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                at = pad(level, getX() + Math.cos(a) * 3.5, getZ() + Math.sin(a) * 3.5);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            confetti(level, at.add(0, 0.8, 0), 3, 0.4);
            level.sendParticles(ParticleTypes.POOF, at.x, at.y + 0.5, at.z, 10, 0.3, 0.3, 0.3, 0.02);
        }
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_DIDGERIDOO.value(), SoundSource.HOSTILE, 1.5F, 1.2F);
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

    // ------------------------------------------------------------------ phase 3: the Grand Finale

    private void startFinale(ServerLevel level) {
        finale = true;
        spotTimer = 40;
        confettiTimer = 60;
        spotTick = -1;
        addEffect(floorRing(position(), ringR(), 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("ringmaster_finale"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        confetti(level, position().add(0, 3.0, 0), 30, 2.5);
        level.sendParticles(ParticleTypes.FIREWORK, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.2);
        level.playSound(null, this, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.HOSTILE, 3.0F, 0.8F);
        level.playSound(null, this, SoundEvents.FIREWORK_ROCKET_TWINKLE, SoundSource.HOSTILE, 3.0F, 1.0F);
    }

    /** A ring of confetti running out over the floor from {@code c}: it hits once whoever stands on the floor (jump). */
    private Effect floorRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(CONFETTI[i % CONFETTI.length], c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr,
                        1, 0, 0.05, 0, 0);
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

    /** The spotlight picks the next player (the target first) and starts 7 blocks from them, toward the centre. */
    private void startSpot(ServerLevel level, @Nullable LivingEntity target) {
        List<Player> all = fighters(level);
        LivingEntity who = null;
        if (!all.isEmpty()) {
            who = all.get(Math.floorMod(spotTurn++, all.size()));
        } else if (target != null) {
            who = target;
        }
        if (who == null) {
            return;
        }
        Vec3 c = centre();
        Vec3 in = c.subtract(who.position()).multiply(1, 0, 1);
        Vec3 from = in.length() > 7.0 ? who.position().add(in.normalize().scale(7.0)) : c;
        Vec3 s = inner(level, from.x, from.z, ringR() - 1.0);
        spotAt = s != null ? s : c;
        spotOwner = who.getUUID();
        spotTick = 0;
        level.playSound(null, spotAt.x, spotAt.y, spotAt.z, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.0F, 1.6F);
    }

    /**
     * The spotlight: a circle (r 2) under a beam from the great chandelier follows its player at 0.17 blocks a tick
     * (slower than walking) for 5 s: every second, 4 and Glowing 2 s to whoever stands in it. Then it stops, turns red
     * for 1 s and blasts: 9 and a lift. Its light block moves with it and is put back when it ends.
     */
    private void tickSpot(ServerLevel level) {
        Vec3 s = spotAt;
        if (s == null) {
            endSpot(level);
            return;
        }
        int k = spotTick;
        if (k < SPOT_HUNT) {
            var owner = spotOwner != null ? level.getEntity(spotOwner) : null;
            if (!(owner instanceof LivingEntity le) || !le.isAlive() || flatDist(le.position(), centre()) > radius + 4) {
                spotTick = SPOT_HUNT;                                   // its player left: hold and blast here
            } else {
                Vec3 to = le.position().subtract(s).multiply(1, 0, 1);
                double d = to.length();
                if (d > 0.05) {
                    Vec3 next = s.add(to.normalize().scale(Math.min(d, SPOT_SPEED)));
                    Vec3 p = inner(level, next.x, next.z, ringR() - 1.0);
                    if (p != null) {
                        s = p;
                        spotAt = p;
                    }
                }
            }
        }
        boolean hold = spotTick >= SPOT_HUNT;
        if (k % 2 == 0) {
            telegraphRing(level, s, SPOT_R, hold ? RED : WHITE);
            Vec3 top = centre().add(0, SPOT_UP, 0);
            for (double f = 0.05; f < 1.0; f += 0.06) {
                Vec3 p = top.lerp(s.add(0, 0.5, 0), f);
                level.sendParticles(BEAM, p.x, p.y, p.z, 1, 0.08, 0.08, 0.08, 0);
            }
            level.sendParticles(ParticleTypes.END_ROD, s.x, s.y + 0.3, s.z, 2, SPOT_R * 0.4, 0.1, SPOT_R * 0.4, 0.01);
        }
        moveLight(level, s);
        if (!hold && k >= 20 && k % 20 == 10) {
            for (LivingEntity e : victims(level, s, SPOT_R + 1)) {
                if (flatDist(e.position(), s) <= SPOT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.5) {
                    strike(level, e, 4.0F, 0.0, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 40, 0));
                }
            }
            level.playSound(null, s.x, s.y, s.z, SoundEvents.NOTE_BLOCK_PLING.value(), SoundSource.HOSTILE, 1.2F, 1.6F);
        }
        if (spotTick >= SPOT_HUNT + SPOT_HOLD - 1) {
            level.sendParticles(ParticleTypes.EXPLOSION, s.x, s.y + 0.5, s.z, 2, 0.6, 0.2, 0.6, 0);
            level.sendParticles(ParticleTypes.FIREWORK, s.x, s.y + 0.6, s.z, 30, 1.0, 0.5, 1.0, 0.15);
            confetti(level, s.add(0, 1.0, 0), 6, 1.2);
            level.playSound(null, s.x, s.y, s.z, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.HOSTILE, 2.0F, 0.9F);
            for (LivingEntity e : victims(level, s, SPOT_R + 1)) {
                if (flatDist(e.position(), s) <= SPOT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.5) {
                    strike(level, e, 9.0F, 0.0, 0.3);
                }
            }
            endSpot(level);
            return;
        }
        spotTick++;
    }

    private void endSpot(ServerLevel level) {
        spotTick = -1;
        spotAt = null;
        spotOwner = null;
        spotTimer = Math.max(140, (int) Math.round(SPOT_EVERY * cooldownScale()));
        restoreAll(level);
    }

    /** The beam's light: one light block in the air over the spot, moved with it (the last one put back). */
    private void moveLight(ServerLevel level, Vec3 s) {
        BlockPos p = BlockPos.containing(s.x, s.y + 1.0, s.z);
        if (p.equals(spotLight)) {
            return;
        }
        if (spotLight != null) {
            clearTemp(level, spotLight.asLong());
        }
        spotLight = null;
        if (level.isLoaded(p) && level.getBlockState(p).isAir() && !temps.containsKey(p.asLong())) {
            BlockState light = Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, 15);
            temps.put(p.asLong(), new Temp(level.getBlockState(p), light));
            level.setBlock(p, light, 3);
            spotLight = p;
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
        spotLight = null;
    }

    /** Confetti charges: one under the target, the rest 3-9 from it, 3.5 apart; at most 5. */
    private void castConfetti(ServerLevel level, @Nullable LivingEntity target) {
        int n = Math.min(5, scaledCount(2) + 1);
        List<Vec3> marks = new ArrayList<>();
        Vec3 base = target != null ? target.position() : centre();
        Vec3 first = inner(level, base.x, base.z, ringR() - 1.5);
        if (first != null) {
            marks.add(first);
        }
        for (int tries = 0; tries < 30 && marks.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 3.0 + getRandom().nextDouble() * 6.0;
            Vec3 s = inner(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d, ringR() - 1.5);
            if (s != null && apart(marks, s, 3.5)) {
                marks.add(s);
            }
        }
        for (Vec3 m : marks) {
            addEffect(confettiCharge(m));
        }
    }

    /** A confetti charge: its circle (r 2) drawn 30 ticks (red the last 10, sparks rising), then 7 and a lift. */
    private Effect confettiCharge(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, CONFETTI_R, k >= 20 ? RED : GOLD);
                }
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.FIREWORK, at.x, at.y + 0.2, at.z, 1, 0.5, 0.0, 0.5, 0.05);
                }
                if (k == 20) {
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.TNT_PRIMED, SoundSource.HOSTILE, 1.0F, 1.4F);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 1, 0, 0, 0, 0);
            ((Ringmaster) boss).confetti(level, at.add(0, 1.0, 0), 6, 1.2);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 1.4F, 1.2F);
            for (LivingEntity e : boss.victims(level, at, CONFETTI_R + 1)) {
                if (flatDist(e.position(), at) <= CONFETTI_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                    boss.strike(level, e, 7.0F, 0.0, 0.3);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(GOLD, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.8F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        spotTick = -1;
        spotAt = null;
        spotOwner = null;
        restoreAll(level);
        discardAdds(level);
    }

    /** Back to the first phase (the fight was reset): base speed, no finale. */
    private void resetForm(ServerLevel level) {
        finale = false;
        roarUntil = -1;
        guard = 0;
        spotTimer = 40;
        confettiTimer = 60;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("ringmaster_finale"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("ringmaster_wrath"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleTemps.isEmpty()) {                       // saved by an unload: put back on the first tick
            restoreAll(level);
        }
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!temps.isEmpty() || spotTick >= 0)) {
            spotTick = -1;                                 // the arena emptied (death, flight)
            spotAt = null;
            restoreAll(level);
        }
        if (phase() == 1 && finale) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !finale && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "finale");
        }
        // phase 3: the spotlight hunts, confetti charges burst
        if (finale && phase() == 2 && anyone) {
            cur = currentAttack();
            boolean busy = cur != null && "finale".equals(cur.name);
            if (spotTick >= 0) {
                tickSpot(level);
            } else if (fighting && !busy && guard == 0 && --spotTimer <= 0) {
                startSpot(level, target);
            }
            if (fighting && !busy && guard == 0 && --confettiTimer <= 0) {
                confettiTimer = Math.max(60, (int) Math.round(CONFETTI_EVERY * cooldownScale()));
                castConfetti(level, target);
            }
            if (tickCount % 4 == 0) {
                Vec3 c = centre();
                double r = ringR() - 1.0;
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                level.sendParticles(CONFETTI[getRandom().nextInt(CONFETTI.length)], x, c.y + 6 + getRandom().nextDouble() * 8, z,
                        1, 0.3, 0.3, 0.3, 0);
            }
        }
        // ambience: steam from the hat's whistle, the key turning in his back
        if (tickCount % 8 == 0) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 4.0, getZ(), 1, 0.05, 0.1, 0.05, 0.01);
        }
        if (tickCount % 40 == 0) {
            level.playSound(null, this, SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.HOSTILE, 0.6F, 1.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("ringmaster_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 4.0, getZ(), 30, 0.4, 0.8, 0.4, 0.05);
        confetti(level, position().add(0, 3.0, 0), 10, 1.5);
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        confetti(level, position().add(0, 2.5, 0), 30, 1.5);
        level.sendParticles(BRASS, getX(), getY() + 2.5, getZ(), 40, 1.0, 1.0, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.HOSTILE, 2.0F, 0.4F);
        level.playSound(null, this, SoundEvents.FIREWORK_ROCKET_TWINKLE_FAR, SoundSource.HOSTILE, 2.0F, 0.8F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            restoreAll(level);
            discardAdds(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("RingCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("RingRadius", radius);
        output.putBoolean("RingFinale", finale);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("RingmasterLights", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("RingCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("RingRadius", 22);
        floorTol = -1;
        finale = input.getBooleanOr("RingFinale", false) && phase() == 2;
        staleTemps.clear();
        input.read("RingmasterLights", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
        spotTick = -1;
        spotLight = null;
    }
}
