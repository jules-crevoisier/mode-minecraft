package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
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
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.RotatedPillarBlock;
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

import static com.brasshaven.generated.MobAnims.LumberJarl.BLADE;
import static com.brasshaven.generated.MobAnims.LumberJarl.CALL;
import static com.brasshaven.generated.MobAnims.LumberJarl.CHOP;
import static com.brasshaven.generated.MobAnims.LumberJarl.OVERDRIVE;
import static com.brasshaven.generated.MobAnims.LumberJarl.ROAR;
import static com.brasshaven.generated.MobAnims.LumberJarl.ROLL;
import static com.brasshaven.generated.MobAnims.LumberJarl.STAGGER;
import static com.brasshaven.generated.MobAnims.LumberJarl.SWEEP;
import static com.brasshaven.generated.MobAnims.LumberJarl.TIMBER;

/**
 * Le Jarl du bois (The Lumber Jarl), the champion of the Timber Fortress: a giant lumberjack warlord (4 blocks) in a
 * horned fur-and-iron helm, a braided red beard, plaid under chainmail over a barrel chest, a log-carrier harness with
 * spare saw blades on his back and a steam chainsaw-axe in both hands. He waits on the keep's crown, the railed timber
 * platform (49 wide) round the brass beam engine.
 * <ul>
 *     <li>Phase 1: the chainsaw <b>sweep</b> (a drawn arc that bites four times while he holds it), the overhead
 *     <b>chop</b> (a drawn line: the deck splits along it), the thrown saw <b>blade</b> that boomerangs back along a
 *     drawn loop, <b>timber</b> (logs crash down on marked lanes under every player) and the log <b>roll</b> down a
 *     marked lane.</li>
 *     <li>Phase 2 (a roar at 65%): faster, he <b>calls</b> his crew (vindicators and bandit marksmen), two blades at
 *     once, more logs; the chop chains into the roll or the sweep.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the beam engine <b>overdrives</b> (a wave,
 *     jump it): the flywheel throws sparks in sweeping arcs over marked wedges, steam bursts from marked vents in the
 *     deck, and his chainsaw reaches further.</li>
 * </ul>
 * He places no blocks: the falling and rolling logs are falling-block visuals that never land (dropped, removed on
 * contact, at the end of their run, on reset, death, removal and after a reload). Pushes are capped and never thrown
 * toward the railing, a stairwell or the edge.
 */
public class LumberJarl extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 4.0F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final String LOG_TAG = "brasshaven_jarl_log";
    private static final double SWEEP_HALF = 80;
    private static final double CHOP_MAX = 14.0;
    private static final double CHOP_HALF = 1.0;
    private static final double BLADE_MAX = 14.0;
    private static final double BLADE_SIDE = 3.5;
    private static final double LOG_HALF_LEN = 3.0;
    private static final double LOG_HALF_W = 1.0;
    private static final double ROLL_MAX = 22.0;
    private static final double ROLL_HALF = 1.5;
    private static final double SPARK_LEN = 22.0;
    private static final double SPARK_WEDGE = 35;
    private static final double VENT_R = 1.8;
    private static final int SPARK_EVERY = 140;
    private static final int VENT_EVERY = 100;
    private static final DustParticleOptions ORANGE = new DustParticleOptions(0xFF9A30, 1.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions BARK = new DustParticleOptions(0x8A5E34, 1.5F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions STEAM = new DustParticleOptions(0xE8EEF2, 1.6F);
    private static final DustParticleOptions SPARK = new DustParticleOptions(0xFFC850, 1.1F);

    /** A falling-log lane: its centre, its axis (unit, flat) and the falling blocks over it. */
    private record Lane(Vec3 at, Vec3 dir) {}

    private @Nullable Vec3 centre;
    private int radius = 20;
    /** The gilded ring inlaid round the beam engine (its centre is the keep's axis); null until surveyed. */
    private @Nullable Vec3 axis;
    private boolean axisFound;
    /** Phase 3 has started (the beam engine overdrove). */
    private boolean overdriven;
    private boolean staleLogs = true;
    private int guard;
    private int roarUntil = -1;
    private int sparkTimer = 60;
    private int ventTimer = 40;
    private boolean sparkClockwise;
    // moves in flight
    private double lineLen = 6.0;
    private final List<Lane> lanes = new ArrayList<>();
    private final List<List<Vec3>> bladePaths = new ArrayList<>();
    private final List<FallingBlockEntity> flying = new ArrayList<>();
    private final Set<UUID> adds = new HashSet<>();

    public LumberJarl(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 660.0)
                .add(Attributes.ARMOR, 13.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.LumberJarl.TICKS;
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

    // ------------------------------------------------------------------ arena memory (the keep's crown)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.axis = null;
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

    /** Finds the gilded ring inlaid in the deck round the beam engine: its centroid is the keep's axis. */
    private void survey(ServerLevel level) {
        if (axis != null) {
            return;
        }
        Vec3 c = centre();
        int y = Mth.floor(c.y) - 1;
        int r = radius + 6;
        double sx = 0;
        double sz = 0;
        int n = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                p.set(Mth.floor(c.x) + dx, y, Mth.floor(c.z) + dz);
                if (!level.isLoaded(p)) {
                    continue;
                }
                Identifier id = BuiltInRegistries.BLOCK.getKey(level.getBlockState(p).getBlock());
                if ("brasshaven".equals(id.getNamespace()) && "gilded_trim".equals(id.getPath())) {
                    sx += p.getX() + 0.5;
                    sz += p.getZ() + 0.5;
                    n++;
                }
            }
        }
        if (n >= 24) {
            axis = new Vec3(sx / n, c.y, sz / n);
            axisFound = true;
        } else {
            axis = c;
            axisFound = false;
        }
    }

    private Vec3 axis() {
        return axis != null ? axis : centre();
    }

    /** The ground under the flywheel (8 blocks north of the keep's axis on the crown; the arena centre elsewhere). */
    private Vec3 flywheelFoot() {
        Vec3 a = axis();
        return axisFound ? new Vec3(a.x, a.y, a.z - 8.0) : a;
    }

    private Vec3 flywheelHub() {
        return flywheelFoot().add(0, 9.0, 0);
    }

    /**
     * A spot of open deck at (x, z): floor within 0.6 of the seal's level, two blocks of air over it and, with
     * {@code inArena}, within the arena (and inside the platform's railing square round the keep's axis); or null.
     * The engine's bed, the stair houses and their wells, the railing and the drop beyond are never open deck.
     */
    private @Nullable Vec3 deck(ServerLevel level, double x, double z, boolean inArena) {
        survey(level);
        Vec3 c = centre();
        if (inArena) {
            if (Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
                return null;
            }
            if (axisFound && Math.max(Math.abs(x - axis().x), Math.abs(z - axis().z)) > 23.0) {
                return null;
            }
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > 0.6 || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
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
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 14, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** Height of {@code e}'s feet over the floor under it (0 standing, more when jumping). */
    private static double overFloor(ServerLevel level, LivingEntity e) {
        double fy = floorY(level, e.getX(), e.getY(), e.getZ());
        return Double.isNaN(fy) ? 9.0 : e.getY() - fy;
    }

    /** The push is dropped where it would carry {@code e} off the open deck (the railing, a stairwell, the edge). */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 dir = push.multiply(1, 0, 1).normalize();
        for (double d : new double[] {1.5, 3.0}) {
            Vec3 probe = e.position().add(dir.scale(d));
            if (deck(level, probe.x, probe.z, true) == null) {
                return Vec3.ZERO;
            }
        }
        return new Vec3(push.x, 0, push.z);
    }

    /** Pushes capped at 1.0, lift at 0.45 (0.2 when no open deck lies 3 blocks beyond); none off the deck. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.0, knockback));
        }
        shove(level, e, damage, push, lift);
    }

    private void shove(ServerLevel level, LivingEntity e, float damage, Vec3 push, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 safe = safePush(level, e, push);
        lift = Math.min(lift, safe.lengthSqr() < push.lengthSqr() - 1.0E-6 ? 0.2 : 0.45);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
    }

    private static BlockParticleOption block(BlockState s) {
        return new BlockParticleOption(ParticleTypes.BLOCK, s);
    }

    private void chips(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(block(Blocks.SPRUCE_LOG.defaultBlockState()), at.x, at.y + 0.4, at.z, count, spread, 0.3, spread, 0.12);
        level.sendParticles(BARK, at.x, at.y + 0.5, at.z, count / 2, spread, 0.3, spread, 0.0);
    }

    /** The chainsaw's engine, at his right shoulder (where the axe rests). */
    private Vec3 sawEngine() {
        Vec3 f = forward();
        Vec3 right = new Vec3(f.z, 0, -f.x);
        return position().add(right.scale(0.9)).add(f.scale(0.6)).add(0, 3.6, 0);
    }

    /** How far the chainsaw reaches: 5.5, 7 once the engine overdrives. */
    private double reach() {
        return overdriven ? 7.0 : 5.5;
    }

    private void engineSmoke(ServerLevel level, int amount) {
        Vec3 e = sawEngine();
        level.sendParticles(ParticleTypes.LARGE_SMOKE, e.x, e.y + 0.4, e.z, amount, 0.1, 0.1, 0.1, 0.02);
        if (overdriven) {
            level.sendParticles(ParticleTypes.FLAME, e.x, e.y, e.z, 1, 0.1, 0.1, 0.1, 0.01);
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // sweep: the chainsaw-axe cocked over his right shoulder, the engine revving (0.9 s; the arc drawn orange, then
        // the chain drags across his front for 0.8 s: four bites of 4 to whoever stays in the arc (small push)
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(18, 16, 14).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        DustParticleOptions d = tick >= 12 ? RED : ORANGE;
                        b.telegraphArc(level, reach(), SWEEP_HALF, d);
                        b.telegraphArc(level, reach() - 2.5, SWEEP_HALF, d);
                    }
                    engineSmoke(level, 1);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.MINECART_RIDING, SoundSource.HOSTILE, 1.4F, 0.6F + tick * 0.04F);
                    }
                })
                .impact((b, level, t, tick) -> sawBite(level, 0))
                .active((b, level, t, tick) -> {
                    if (tick > 0 && tick < 16 && tick % 5 == 0) {
                        sawBite(level, tick / 5);
                    }
                    if (tick < 16) {
                        engineSmoke(level, 1);
                    }
                })
                .build());
        // chop: the axe raised high in both hands (1.2 s; a line drawn green from his feet follows you slowly, locks red
        // 0.4 s before), brought straight down: 16 to whoever stands right in front, then the deck splits along the line
        // one block a tick (10, a lift), ending in a small burst (6)
        out.add(BossAttack.of("chop").anim(CHOP).timing(24, 16, 16).range(0, 16.0).cooldown(110).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    lineLen = lineLength(level, CHOP_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 16) {
                        turnToward(t, 4.0F);
                        lineLen = lineLength(level, CHOP_MAX);
                    }
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick < 16 ? ORANGE : RED;
                        drawLine(level, position(), forward(), lineLen, CHOP_HALF, d);
                        b.telegraphRing(level, ahead(2.0), 2.0, d);
                    }
                    engineSmoke(level, 1);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.MINECART_RIDING, SoundSource.HOSTILE, 1.2F, 0.5F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 at = ahead(2.0);
                    for (LivingEntity e : victims(level, at, 3.0)) {
                        if (flatDist(e.position(), at) <= 2.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                            strike(level, e, 16.0F, 0.6, 0.3);
                        }
                    }
                    chips(level, at, 30, 0.8);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, at.x, at.y + 1.0, at.z, 1, 0, 0, 0, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    b.addEffect(split(position(), forward(), lineLen));
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) > 6.0 ? "roll" : "sweep");
                    }
                })
                .build());
        // blade: a spare saw blade pulled off the harness and wound back (1.0 s; its loop drawn gold out to you and back,
        // red for the last 0.3 s), flung: it flies the loop and comes back to his hand: 9 to whoever it passes (it can
        // catch you going out and coming back). Phase 2: two blades on mirrored loops
        out.add(BossAttack.of("blade").anim(BLADE).timing(20, 12, 16).range(5.0, 20.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planBlades(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 14 ? RED : GOLD;
                        for (List<Vec3> path : bladePaths) {
                            for (int i = 0; i < path.size(); i += 2) {
                                Vec3 p = path.get(i);
                                level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (List<Vec3> path : bladePaths) {
                        b.addEffect(sawBlade(path));
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .build());
        // timber: he lifts the axe and bellows "TIMBER!" (1.0 s); a lane (6 x 2) is marked under every player and on the
        // open deck round the target, red 0.5 s later, and logs come crashing down on them: 11 and Slowness I 1.5 s
        out.add(BossAttack.of("timber").anim(TIMBER).timing(20, 10, 16).range(0, 30.0).cooldown(220).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    planLanes(level, t);
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 1.2F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Lane l : lanes) {
                            drawLane(level, l, BARK);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Lane l : lanes) {
                        b.addEffect(fallingLog(l));
                    }
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.8F);
                })
                .build());
        // roll: he tears a log off his harness (1.3 s; a lane 3 wide drawn brown across the deck, following you slowly,
        // then red) and kicks it down the lane: it rolls 0.7 blocks a tick: 10, a lift and a push out of the lane
        out.add(BossAttack.of("roll").anim(ROLL).timing(26, 10, 14).range(4.0, 24.0).cooldown(160).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    lineLen = lineLength(level, ROLL_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 16) {
                        turnToward(t, 3.0F);
                        lineLen = lineLength(level, ROLL_MAX);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), lineLen, ROLL_HALF, tick < 16 ? BARK : RED);
                    }
                    if (tick == 14) {
                        level.playSound(null, b, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(rollingLog(level, position(), forward(), lineLen));
                    level.playSound(null, b, SoundEvents.ZOMBIE_ATTACK_WOODEN_DOOR, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // call: the haft hammered on the deck three times, a bellow (1.0 s): his crew climbs onto the crown
        // (vindicators and bandit marksmen, 2, more in co-op), never more than 3 at once
        out.add(BossAttack.of("call").anim(CALL).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(700).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick == 4 || tick == 10 || tick == 16) {
                        level.playSound(null, b, SoundEvents.WOOD_HIT, SoundSource.HOSTILE, 2.0F, 0.5F);
                        chips(level, ahead(1.0), 6, 0.3);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0F, 1.0F);
                    spawnAdds(level, 2);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // overdrive: the chainsaw-axe raised to the beam engine (2.0 s, guarded; orange rings gather round him, the
        // flywheel smokes), slammed into the deck: a wave to 14 (10, jump it); the engine overdrives
        out.add(BossAttack.of("overdrive").anim(OVERDRIVE).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, ORANGE);
                    }
                    Vec3 h = flywheelHub();
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, h.x, h.y, h.z, 3, 1.5, 3.0, 1.5, 0.02);
                    level.sendParticles(SPARK, h.x, h.y, h.z, 4, 0.5, 4.0, 4.0, 0);
                    engineSmoke(level, 2);
                    if (tick % 10 == 0) {
                        level.playSound(null, h.x, h.y, h.z, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> overdrive(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** One bite of the chainsaw: 4 to everyone in the arc (reach, ±80°), a small push; it bites through i-frames. */
    private void sawBite(ServerLevel level, int k) {
        Vec3 fwd = forward();
        double r = reach();
        double cos = Math.cos(Math.toRadians(SWEEP_HALF));
        for (LivingEntity e : victims(level, position(), r + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= r + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos) && Math.abs(e.getY() - getY()) < 3.5) {
                e.invulnerableTime = 0;
                strike(level, e, 4.0F, 0.25, 0.1);
            }
        }
        // the chain's sparks sweep right to left with the bites
        double a = SWEEP_HALF - k * (2 * SWEEP_HALF / 3.0);
        for (double s = -20; s <= 20; s += 10) {
            Vec3 p = position().add(rotate(fwd, -(a + s)).scale(r - 1.0));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.4, p.z, 3, 0.2, 0.2, 0.2, 0.2);
            level.sendParticles(block(Blocks.SPRUCE_PLANKS.defaultBlockState()), p.x, p.y + 1.2, p.z, 2, 0.2, 0.2, 0.2, 0.1);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.2F, 0.6F);
    }

    /** How far a line along his facing runs over open deck (stopping at the engine, a wall, the railing). */
    private double lineLength(ServerLevel level, double max) {
        double len = 2.0;
        for (double d = 1.0; d <= max; d += 1.0) {
            Vec3 p = ahead(d);
            if (deck(level, p.x, p.z, true) == null) {
                break;
            }
            len = d;
        }
        return Math.max(2.0, len);
    }

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double len, double half, DustParticleOptions dust) {
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = from.add(dir.scale(d));
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = p.add(side.scale(s * half));
                level.sendParticles(dust, q.x, from.y + 0.15, q.z, 1, 0, 0, 0, 0);
            }
            if (((int) d) % 2 == 0) {
                level.sendParticles(dust, p.x, from.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /** The split in the deck: it runs from 2 to {@code len} along {@code dir} a block a tick, then bursts. */
    private Effect split(Vec3 from, Vec3 dir, double len) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof LumberJarl j)) {
                return true;
            }
            double d = 2.0 + t[0]++;
            Vec3 p = from.add(dir.scale(Math.min(d, len)));
            level.sendParticles(block(Blocks.SPRUCE_PLANKS.defaultBlockState()), p.x, p.y + 0.3, p.z, 10, 0.4, 0.3, 0.4, 0.15);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.4, p.z, 3, 0.3, 0.2, 0.3, 0.1);
            if (t[0] % 2 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 1.2F, 0.6F + t[0] * 0.03F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= CHOP_HALF + 0.3 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.0
                        && hit.add(e.getUUID())) {
                    j.strike(level, e, 10.0F, 0.0, 0.45);
                }
            }
            if (d < len) {
                return false;
            }
            j.chips(level, p, 30, 1.2);
            level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.5, p.z, 1, 0, 0, 0, 0);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 1.5F, 0.7F);
            for (LivingEntity e : boss.victims(level, p, 3.5)) {
                if (flatDist(e.position(), p) <= 2.5 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.0 && hit.add(e.getUUID())) {
                    j.strike(level, e, 6.0F, 0.5, 0.3);
                }
            }
            return true;
        };
    }

    // ---- the boomerang blades

    /**
     * The blades' loops: out toward the target (up to 14, over open deck) on one side and back on the other, as a
     * closed loop from his hand; phase 2 adds a mirrored one.
     */
    private void planBlades(ServerLevel level, @Nullable LivingEntity t) {
        bladePaths.clear();
        Vec3 dir = forward();
        double len = Math.min(BLADE_MAX, t != null ? Math.max(6.0, flatDist(position(), t.position()) + 2.0) : 10.0);
        double ok = 3.0;
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = ahead(d);
            if (deck(level, p.x, p.z, true) == null) {
                break;
            }
            ok = d;
        }
        len = Math.max(4.0, ok);
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        int n = phase() == 2 ? 2 : 1;
        boolean right = getRandom().nextBoolean();
        for (int k = 0; k < n; k++) {
            double w = (right ^ (k == 1) ? 1 : -1) * BLADE_SIDE;
            List<Vec3> path = new ArrayList<>();
            int steps = (int) Math.ceil(len * 2.4);
            for (int i = 1; i <= steps; i++) {
                double s = i / (double) steps;
                double along = Math.sin(Math.PI * s) * len;
                double lat = Math.sin(2 * Math.PI * s) * w;
                Vec3 p = position().add(dir.scale(along)).add(side.scale(lat));
                path.add(new Vec3(p.x, getY(), p.z));
            }
            bladePaths.add(path);
        }
    }

    /** A spinning saw blade flying its loop a point a tick: 9 to whoever it passes (again after 12 ticks). */
    private Effect sawBlade(List<Vec3> path) {
        int[] t = {0};
        Map<UUID, Integer> last = new HashMap<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (k >= path.size()) {
                level.playSound(null, boss, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
                return true;
            }
            Vec3 p = path.get(k);
            double y = p.y + 1.2;
            for (int i = 0; i < 4; i++) {
                double a = k * 1.3 + i * Math.PI / 2;
                level.sendParticles(ParticleTypes.CRIT, p.x + Math.cos(a) * 0.6, y, p.z + Math.sin(a) * 0.6, 1, 0, 0, 0, 0);
            }
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, y, p.z, 1, 0, 0, 0, 0);
            level.sendParticles(block(Blocks.IRON_BLOCK.defaultBlockState()), p.x, y, p.z, 2, 0.2, 0.1, 0.2, 0.05);
            if (k % 3 == 0) {
                level.playSound(null, p.x, y, p.z, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.0F, 1.4F);
            }
            if (boss instanceof LumberJarl j) {
                for (LivingEntity e : boss.victims(level, p, 2.0)) {
                    if (flatDist(e.position(), p) <= 1.3 + e.getBbWidth() / 2 && Math.abs(e.getY() + 0.9 - y) < 1.8
                            && k - last.getOrDefault(e.getUUID(), -99) >= 12) {
                        last.put(e.getUUID(), k);
                        j.strike(level, e, 9.0F, 0.3, 0.2);
                    }
                }
            }
            return false;
        };
    }

    // ---- timber!

    /** Log lanes: one under each player (up to 4), plus 2 (phase 2: 3, more in co-op) on open deck round the target. */
    private void planLanes(ServerLevel level, @Nullable LivingEntity target) {
        lanes.clear();
        int players = 0;
        for (Player p : fighters(level)) {
            if (players >= 4) {
                break;
            }
            if (tryLane(level, p.getX(), p.getZ(), 3.0)) {
                players++;
            }
        }
        int extra = scaledCount(phase() == 2 ? 3 : 2);
        Vec3 base = target != null ? target.position() : ahead(6.0);
        int added = 0;
        for (int tries = 0; tries < 40 && added < extra; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 4.0 + getRandom().nextDouble() * 5.0;
            if (tryLane(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d, 3.5)) {
                added++;
            }
        }
    }

    private boolean tryLane(ServerLevel level, double x, double z, double spacing) {
        Vec3 s = deck(level, x, z, true);
        if (s == null || flatDist(s, position()) < 2.0) {
            return false;
        }
        for (Lane l : lanes) {
            if (flatDist(l.at(), s) < spacing) {
                return false;
            }
        }
        Vec3 dir = getRandom().nextBoolean() ? new Vec3(1, 0, 0) : new Vec3(0, 0, 1);
        lanes.add(new Lane(s, dir));
        return true;
    }

    private boolean inLane(Lane l, LivingEntity e) {
        Vec3 to = e.position().subtract(l.at()).multiply(1, 0, 1);
        double along = Math.abs(to.dot(l.dir()));
        double side = to.subtract(l.dir().scale(to.dot(l.dir()))).length();
        return along <= LOG_HALF_LEN + e.getBbWidth() / 2 && side <= LOG_HALF_W + e.getBbWidth() / 2
                && Math.abs(e.getY() - l.at().y) < 2.5;
    }

    private void drawLane(ServerLevel level, Lane l, DustParticleOptions d) {
        Vec3 side = new Vec3(-l.dir().z, 0, l.dir().x);
        double y = l.at().y + 0.15;
        for (double a = -LOG_HALF_LEN; a <= LOG_HALF_LEN; a += 0.75) {
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = l.at().add(l.dir().scale(a)).add(side.scale(s * LOG_HALF_W));
                level.sendParticles(d, q.x, y, q.z, 1, 0, 0, 0, 0);
            }
        }
        for (int e = -1; e <= 1; e += 2) {
            for (double w = -LOG_HALF_W; w <= LOG_HALF_W; w += 0.5) {
                Vec3 q = l.at().add(l.dir().scale(e * LOG_HALF_LEN)).add(side.scale(w));
                level.sendParticles(d, q.x, y, q.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /**
     * A log falling on a lane: red 10 more ticks, then three log blocks drop from 12 above (falling-block visuals,
     * removed when they reach the deck, never placed); the crash: 11 and Slowness I 1.5 s in the lane.
     */
    private Effect fallingLog(Lane l) {
        int[] t = {0};
        List<FallingBlockEntity> logs = new ArrayList<>();
        BlockState state = Blocks.SPRUCE_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS,
                Math.abs(l.dir().x) > 0.5 ? Direction.Axis.X : Direction.Axis.Z);
        return (boss, level) -> {
            if (!(boss instanceof LumberJarl j)) {
                return true;
            }
            int k = t[0]++;
            if (k % 2 == 0 && k < 24) {
                j.drawLane(level, l, RED);
                level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, state), l.at().x, l.at().y + 6, l.at().z,
                        2, 1.0, 2.0, 1.0, 0);
            }
            if (k < 10) {
                return false;
            }
            if (k == 10) {
                for (int s = -1; s <= 1; s++) {
                    Vec3 at = l.at().add(l.dir().scale(s * 2.0)).add(0, 12.0, 0);
                    FallingBlockEntity fb = j.spawnLog(level, at, state, false);
                    if (fb != null) {
                        logs.add(fb);
                    }
                }
                level.playSound(null, l.at().x, l.at().y + 8, l.at().z, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            boolean falling = false;
            for (FallingBlockEntity fb : logs) {
                if (fb.isAlive() && (fb.getY() + fb.getDeltaMovement().y <= l.at().y + 0.6 || fb.onGround())) {
                    fb.discard();
                }
                falling |= fb.isAlive();
            }
            // the crash: when the logs reach the deck (or, with no room for a visual, after the usual fall time)
            if (logs.isEmpty() ? k < 24 : (falling && k < 34)) {
                return false;
            }
            for (FallingBlockEntity fb : logs) {
                if (fb.isAlive()) {
                    fb.discard();
                }
            }
            for (double a = -LOG_HALF_LEN; a <= LOG_HALF_LEN; a += 1.0) {
                j.chips(level, l.at().add(l.dir().scale(a)), 6, 0.4);
            }
            level.playSound(null, l.at().x, l.at().y, l.at().z, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 2.5F, 0.4F);
            level.playSound(null, l.at().x, l.at().y, l.at().z, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 1.5F, 0.6F);
            for (LivingEntity e : boss.victims(level, l.at(), LOG_HALF_LEN + 2)) {
                if (j.inLane(l, e)) {
                    j.strike(level, e, 11.0F, 0.0, 0.2);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0));
                }
            }
            return true;
        };
    }

    /** A log block for show: put into an air cell for an instant and lifted out at once; it never lands as a block. */
    private @Nullable FallingBlockEntity spawnLog(ServerLevel level, Vec3 at, BlockState state, boolean weightless) {
        BlockPos cell = BlockPos.containing(at);
        if (!level.isLoaded(cell) || !level.getBlockState(cell).isAir()) {
            return null;
        }
        level.setBlock(cell, state, 2);
        FallingBlockEntity fb = FallingBlockEntity.fall(level, cell, state);
        fb.dropItem = false;
        fb.disableDrop();
        fb.setNoGravity(weightless);
        fb.addTag(LOG_TAG);
        flying.add(fb);
        return fb;
    }

    /** The kicked log rolling down the lane at 0.7 a tick: 10, a lift and a push out of the lane (once each). */
    private Effect rollingLog(ServerLevel level, Vec3 from, Vec3 dir, double len) {
        double[] d = {1.5};
        Set<UUID> hit = new HashSet<>();
        BlockState state = Blocks.SPRUCE_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS,
                Math.abs(dir.x) > Math.abs(dir.z) ? Direction.Axis.Z : Direction.Axis.X);
        FallingBlockEntity log = spawnLog(level, from.add(dir.scale(1.5)), state, true);
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, lvl) -> {
            if (!(boss instanceof LumberJarl j)) {
                return true;
            }
            double prev = d[0];
            d[0] += 0.7;
            Vec3 p = from.add(dir.scale(Math.min(d[0], len)));
            if (log != null && log.isAlive()) {
                log.setPos(p.x, from.y, p.z);
                log.setDeltaMovement(dir.scale(0.7));
            }
            lvl.sendParticles(block(state), p.x, p.y + 0.3, p.z, 4, 0.6, 0.2, 0.6, 0.05);
            if (((int) (d[0] / 0.7)) % 4 == 0) {
                lvl.playSound(null, p.x, p.y, p.z, SoundEvents.WOOD_STEP, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            for (LivingEntity e : boss.victims(lvl, p, ROLL_HALF + 2)) {
                Vec3 to = e.position().subtract(from).multiply(1, 0, 1);
                double along = to.dot(dir);
                double off = to.dot(side);
                if (along >= prev - 1.0 && along <= d[0] + 1.0 && Math.abs(off) <= ROLL_HALF + e.getBbWidth() / 2
                        && Math.abs(e.getY() - from.y) < 2.0 && hit.add(e.getUUID())) {
                    Vec3 push = side.scale(off >= 0 ? 0.7 : -0.7);
                    j.shove(lvl, e, 10.0F, push, 0.3);
                }
            }
            if (d[0] < len) {
                return false;
            }
            if (log != null && log.isAlive()) {
                log.discard();
            }
            j.chips(lvl, p, 30, 0.8);
            lvl.playSound(null, p.x, p.y, p.z, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
            return true;
        };
    }

    // ---- his crew

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
            EntityType<? extends Mob> type = i % 2 == 0 ? EntityTypes.VINDICATOR : ModEntities.BANDIT_MARKSMAN.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 12 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                at = deck(level, getX() + Math.cos(a) * 3.5, getZ() + Math.sin(a) * 3.5, true);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.POOF, at.x, at.y + 1, at.z, 12, 0.3, 0.5, 0.3, 0.05);
        }
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

    // ------------------------------------------------------------------ phase 3: the beam engine overdrives

    private void overdrive(ServerLevel level) {
        overdriven = true;
        sparkTimer = 60;
        ventTimer = 40;
        addEffect(deckRing(position(), 14.0, 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("lumber_jarl_overdrive"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 h = flywheelHub();
        level.sendParticles(ParticleTypes.LAVA, h.x, h.y, h.z, 30, 1.0, 4.0, 4.0, 0.1);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, h.x, h.y + 6, h.z, 30, 1.0, 1.0, 1.0, 0.05);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.5, getZ(), 1, 0, 0, 0, 0);
        level.playSound(null, h.x, h.y, h.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** A jumpable ring from {@code c}: it hits once whoever stands on the floor at its edge. */
    private Effect deckRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof LumberJarl j)) {
                return true;
            }
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(ORANGE, c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && overFloor(level, e) < 0.6 && hit.add(e.getUUID())) {
                    j.strike(level, e, damage, 0.6, 0.35);
                }
            }
            return rr >= max;
        };
    }

    /**
     * The flywheel throws sparks: a wedge (70°, 22 long) from the flywheel's foot toward the target, drawn orange for
     * 30 ticks (red for the last 10); then a jet of sparks sweeps across it in 24 ticks (alternately clockwise and
     * back): 6 and fire 2 s, once per sweep, to whoever the jet crosses.
     */
    private Effect sparkSweep(Vec3 foot, Vec3 toward, boolean clockwise) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        Vec3 dir0 = toward.subtract(foot).multiply(1, 0, 1);
        Vec3 mid = dir0.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, -1) : dir0.normalize();
        double from = clockwise ? -SPARK_WEDGE : SPARK_WEDGE;
        return (boss, level) -> {
            if (!(boss instanceof LumberJarl j)) {
                return true;
            }
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    DustParticleOptions d = k >= 20 ? RED : ORANGE;
                    for (double a = -SPARK_WEDGE; a <= SPARK_WEDGE; a += 7) {
                        Vec3 p = foot.add(rotate(mid, a).scale(SPARK_LEN));
                        level.sendParticles(d, p.x, foot.y + 0.15, p.z, 1, 0, 0, 0, 0);
                    }
                    for (int s = -1; s <= 1; s += 2) {
                        Vec3 edge = rotate(mid, s * SPARK_WEDGE);
                        for (double r = 3.0; r <= SPARK_LEN; r += 1.5) {
                            Vec3 p = foot.add(edge.scale(r));
                            level.sendParticles(d, p.x, foot.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                }
                Vec3 h = j.flywheelHub();
                level.sendParticles(SPARK, h.x, h.y, h.z, 2, 0.4, 3.0, 3.0, 0);
                return false;
            }
            int s = k - 30;
            double a = from + (clockwise ? 1 : -1) * (2 * SPARK_WEDGE) * Math.min(1.0, s / 23.0);
            Vec3 jet = rotate(mid, a);
            Vec3 h = j.flywheelHub();
            for (double r = 1.0; r <= SPARK_LEN; r += 1.5) {
                Vec3 p = foot.add(jet.scale(r));
                double y = foot.y + 0.4 + (1.0 - r / SPARK_LEN) * (h.y - foot.y - 0.4) * 0.6;
                level.sendParticles(ParticleTypes.LAVA, p.x, y, p.z, 1, 0.1, 0.1, 0.1, 0);
                level.sendParticles(SPARK, p.x, y, p.z, 2, 0.3, 0.2, 0.3, 0);
            }
            if (s % 4 == 0) {
                level.playSound(null, h.x, h.y, h.z, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 1.6F);
            }
            for (LivingEntity e : boss.victims(level, foot, SPARK_LEN + 1)) {
                Vec3 to = e.position().subtract(foot).multiply(1, 0, 1);
                double d = to.length();
                if (d < 1.0 || d > SPARK_LEN + e.getBbWidth() / 2 || Math.abs(e.getY() - foot.y) > 3.0) {
                    continue;
                }
                double off = Math.abs(to.normalize().dot(new Vec3(-jet.z, 0, jet.x))) * d;
                if (to.dot(jet) > 0 && off <= 1.0 + e.getBbWidth() / 2 && hit.add(e.getUUID())) {
                    j.strike(level, e, 6.0F, 0.0, 0.1);
                    e.igniteForSeconds(2.0F);
                }
            }
            return s >= 24;
        };
    }

    /** A steam vent: a ring (r 1.8) drawn white for 30 ticks (red for the last 10), then a burst: 7, a lift. */
    private Effect steamVent(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, VENT_R, k >= 20 ? RED : STEAM);
                }
                if (k % 5 == 0) {
                    level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 0.2, at.z, 2, 0.4, 0.05, 0.4, 0.01);
                }
                if (k == 15) {
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.0F, 0.6F);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 1.5, at.z, 40, 0.6, 1.5, 0.6, 0.08);
            level.sendParticles(STEAM, at.x, at.y + 2.0, at.z, 20, 0.6, 1.8, 0.6, 0);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.4F);
            if (boss instanceof LumberJarl j) {
                for (LivingEntity e : boss.victims(level, at, VENT_R + 1)) {
                    if (flatDist(e.position(), at) <= VENT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        j.strike(level, e, 7.0F, 0.0, 0.4);
                    }
                }
            }
            return true;
        };
    }

    private void castVents(ServerLevel level, @Nullable LivingEntity target) {
        int n = scaledCount(2) + 1;
        List<Vec3> spots = new ArrayList<>();
        Vec3 base = target != null ? target.position() : centre();
        for (int tries = 0; tries < 40 && spots.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = spots.isEmpty() ? getRandom().nextDouble() * 2.0 : 3.0 + getRandom().nextDouble() * 7.0;
            Vec3 s = deck(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d, true);
            if (s == null) {
                continue;
            }
            boolean ok = true;
            for (Vec3 o : spots) {
                if (flatDist(o, s) < 4.0) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                spots.add(s);
            }
        }
        for (Vec3 s : spots) {
            addEffect(steamVent(s));
        }
    }

    /** The engine in overdrive: smoke pouring off the flywheel, sparks round its rim, the beat of the piston. */
    private void engineWeather(ServerLevel level) {
        Vec3 h = flywheelHub();
        if (tickCount % 3 == 0) {
            double a = tickCount * 0.35;
            level.sendParticles(SPARK, h.x, h.y + Math.sin(a) * 7.0, h.z + Math.cos(a) * 7.0, 3, 0.2, 0.2, 0.2, 0);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, h.x, h.y + 4, h.z, 1, 1.0, 1.0, 1.0, 0.02);
        }
        if (tickCount % 30 == 0) {
            level.playSound(null, h.x, h.y, h.z, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ORANGE, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.6F, 1.6F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void discardLogs(ServerLevel level) {
        for (FallingBlockEntity fb : flying) {
            if (fb.isAlive()) {
                fb.discard();
            }
        }
        flying.clear();
    }

    /** Log visuals left over by an unload: found by their tag round the arena and removed. */
    private void discardStaleLogs(ServerLevel level) {
        AABB box = new AABB(BlockPos.containing(centre())).inflate(radius + 8, 24, radius + 8);
        for (FallingBlockEntity fb : level.getEntitiesOfClass(FallingBlockEntity.class, box, e -> e.entityTags().contains(LOG_TAG))) {
            if (!flying.contains(fb)) {
                fb.discard();
            }
        }
    }

    private void cleanUp(ServerLevel level) {
        discardLogs(level);
        discardAdds(level);
    }

    /** Back to the first phase (the fight was reset): the engine calms, base speed. */
    private void resetForm(ServerLevel level) {
        overdriven = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("lumber_jarl_overdrive"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("lumber_jarl_wrath"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleLogs) {                                   // the first tick (after a reload too)
            staleLogs = false;
            discardStaleLogs(level);
        }
        if (guard > 0) {
            guard--;
        }
        if (!flying.isEmpty()) {
            flying.removeIf(fb -> !fb.isAlive());
            for (FallingBlockEntity fb : flying) {
                if (fb.tickCount > 60) {
                    fb.discard();                          // a visual that outlived its move
                }
            }
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && !flying.isEmpty()) {
            discardLogs(level);                            // the arena emptied (death, flight)
        }
        if (phase() == 1 && overdriven) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !overdriven && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "overdrive");
        }
        // phase 3: the engine's sparks and steam (they wait while he overdrives or is guarded)
        if (overdriven && phase() == 2 && anyone) {
            engineWeather(level);
            cur = currentAttack();
            boolean busy = cur != null && "overdrive".equals(cur.name);
            if (fighting && !busy && guard == 0) {
                if (--sparkTimer <= 0) {
                    sparkTimer = Math.max(80, (int) Math.round(SPARK_EVERY * cooldownScale()));
                    sparkClockwise = !sparkClockwise;
                    addEffect(sparkSweep(flywheelFoot(), target.position(), sparkClockwise));
                    level.playSound(null, flywheelHub().x, flywheelHub().y, flywheelHub().z, SoundEvents.PISTON_CONTRACT,
                            SoundSource.HOSTILE, 2.5F, 0.6F);
                }
                if (--ventTimer <= 0) {
                    ventTimer = Math.max(60, (int) Math.round(VENT_EVERY * cooldownScale()));
                    castVents(level, target);
                }
            }
        }
        // ambience: the chainsaw's engine idling, smoke from the stack
        if (tickCount % 6 == 0) {
            engineSmoke(level, 1);
        }
        if (tickCount % 40 == 0 && fighting) {
            level.playSound(null, this, SoundEvents.MINECART_INSIDE, SoundSource.HOSTILE, 0.5F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("lumber_jarl_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take it back where it would carry them off the deck
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        engineSmoke(level, 20);
        chips(level, position(), 40, 2.0);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        chips(level, position(), 80, 1.5);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 3, getZ(), 40, 1.0, 1.5, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            discardLogs(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("JarlCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("JarlRadius", radius);
        output.putBoolean("JarlOverdriven", overdriven);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("JarlCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("JarlRadius", 20);
        overdriven = input.getBooleanOr("JarlOverdriven", false) && phase() == 2;
        axis = null;
        staleLogs = true;
    }
}
