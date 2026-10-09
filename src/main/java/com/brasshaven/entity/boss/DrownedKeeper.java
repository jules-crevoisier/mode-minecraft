package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
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
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.DrownedKeeper.CALL;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.OVERLOAD;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.ROAR;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.SLAM;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.STAGGER;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.SURGE;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.SWEEP;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.THROW;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.THRUST;
import static com.brasshaven.generated.MobAnims.DrownedKeeper.WHIRL;

/**
 * Le Gardien noyé du phare (The Drowned Lightkeeper), the champion of the Leviathan Lighthouse: the old keeper of the
 * light (3.4 blocks), drowned in a storm and brought back fused with the great clockwork lens, which turns on his back
 * like a halo. A faded oilskin coat over a barnacled ribcage with a storm lantern burning in it for a heart, a
 * sou'wester, a white beard dripping kelp; a whaling harpoon on a chain in his right hand, a whale's jawbone in his left.
 * He fights in the lantern room at the top of the tower (33 wide under the cupola and the great lamp).
 * <ul>
 *     <li>Phase 1: the <b>thrust</b> (a harpoon lunge down a marked line), the <b>throw</b> (the harpoon flies down a
 *     marked line; whoever it bites is hauled in on its chain), the <b>whirl</b> (the harpoon swung round him on its
 *     chain over a marked ring; close in is safe), the <b>sweep</b> (the great lamp's beam turns through a marked half
 *     of the room, blinding whoever it crosses).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>surge</b> (storm waves roll across the floor one after another: jump
 *     them), the <b>call</b> (drowned marines and tide wraiths climb in, at most 3).</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the <b>overload</b>. The room goes dark and
 *     the lamp shines in three turning sectors; it flashes on a timer, hurting and blinding whoever stands in the
 *     light, so keep to the moving shadow. He adds the whale-bone <b>slam</b>.</li>
 * </ul>
 * He places and breaks no blocks.
 */
public class DrownedKeeper extends WayfarerBoss {
    public static final float WIDTH = 1.3F;
    public static final float HEIGHT = 3.4F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double THRUST_LEN = 6.0;
    private static final double THRUST_HALF = 1.0;
    private static final double THROW_MAX = 16.0;
    private static final double THROW_HALF = 1.0;
    private static final double WHIRL_IN = 2.0;
    private static final double WHIRL_OUT = 6.5;
    private static final double SWEEP_TURN = 4.5;          // degrees a tick: half the room in 40 ticks
    private static final double LAMP_UP = 17.0;            // the great lamp under the cupola, over the room's centre
    private static final double WAVE_SPEED = 0.7;
    private static final double SECTOR_TURN = 0.8;         // degrees a tick: 0.2 blocks a tick at 14 from the centre
    private static final int FLASH_EVERY = 150;
    private static final int FLASH_WARN = 30;
    private static final int SLAM_EVERY = 160;
    private static final double SLAM_R = 3.5;
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.5F);
    private static final DustParticleOptions WHITE = new DustParticleOptions(0xF6F2E8, 1.5F);
    private static final DustParticleOptions SEA = new DustParticleOptions(0x3A8CC8, 1.6F);
    private static final DustParticleOptions FOAM = new DustParticleOptions(0xDDF2F6, 1.3F);
    private static final DustParticleOptions BEAM = new DustParticleOptions(0xFFF2B8, 1.3F);
    private static final DustParticleOptions STEEL = new DustParticleOptions(0x9AA0A8, 1.1F);
    private static final DustParticleOptions LAMP = new DustParticleOptions(0xFFC45C, 1.4F);

    private @Nullable Vec3 centre;
    private int radius = 16;
    private double floorTol = -1;
    /** Phase 3 has started (the Lamp Overload). */
    private boolean overload;
    private int guard;
    private int roarUntil = -1;
    private int slamTimer = 80;
    private int darkTimer;
    // the lamp's sectors in phase 3: their angle turns all the time; a flash is warned for FLASH_WARN ticks
    private double sectorAngle;
    private int sectorDir = 1;
    private int flashTimer = 60;
    private int flashTick = -1;
    // moves in flight
    private final List<Vec3> line = new ArrayList<>();
    private double sweepStart;
    private int sweepDir = 1;
    private final Map<UUID, Integer> sweepHit = new HashMap<>();
    private final Set<UUID> whirlHit = new HashSet<>();
    private @Nullable Vec3 surgeDir;
    private @Nullable Vec3 slamAt;
    private final Set<UUID> adds = new HashSet<>();

    public DrownedKeeper(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 680.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.DrownedKeeper.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.YELLOW;
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
        return 4.0;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (the lantern room)

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

    /** The room's usable radius: the deck inside the glazing (16 in the lantern), never more than the seal's. */
    private double roomR() {
        return Math.min(radius, 16.0);
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

    /** Whether the floor round the seal is flat (the lantern deck) or rough (a command spawn somewhere else). */
    private double floorTol(ServerLevel level) {
        if (floorTol > 0) {
            return floorTol;
        }
        Vec3 c = centre();
        int flat = 0;
        int samples = 0;
        for (int i = 0; i < 48; i++) {
            double a = i * 2.39996;
            double d = Math.sqrt((i + 0.5) / 48.0) * Math.max(3, roomR() - 1);
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
     * Open deck at (x, z): floor within the tolerance of the seal's level, two blocks of air over it, inside the
     * glazing; or null (the hatch house, the glass, the gallery outside it).
     */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z) {
        Vec3 c = centre();
        if (Math.hypot(x - c.x, z - c.z) > roomR() + 0.3) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > floorTol(level) || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Open deck at (x, z), moved toward the centre until it lies within {@code maxR} of it; or null. */
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

    /** Angle in degrees of {@code p} round the room's centre (0 = +x, turning toward +z). */
    private double angleOf(Vec3 p) {
        Vec3 c = centre();
        return Math.toDegrees(Math.atan2(p.z - c.z, p.x - c.x));
    }

    private Vec3 onRing(double degrees, double r) {
        Vec3 c = centre();
        double a = Math.toRadians(degrees);
        return new Vec3(c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r);
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
     * Pushes stay on the deck: a push is kept only when open deck lies 1.5 blocks along it (never into the glazing, the
     * hatch house or out over the gallery's rail); otherwise it is dropped.
     */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        Vec3 flat = new Vec3(push.x, 0, push.z);
        if (flat.lengthSqr() < 1.0E-6) {
            return Vec3.ZERO;
        }
        Vec3 probe = e.position().add(flat.normalize().scale(1.5));
        return pad(level, probe.x, probe.z) == null ? Vec3.ZERO : flat;
    }

    /** A hit pushing along {@code dir}: pushes capped at 1.0 and lift at 0.45 (0.2 when the push was dropped). */
    private void strikeAlong(ServerLevel level, LivingEntity e, float damage, Vec3 dir, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        Vec3 flat = dir.multiply(1, 0, 1);
        if (knockback > 0 && flat.lengthSqr() > 1.0E-6) {
            push = flat.normalize().scale(Math.min(1.0, knockback));
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

    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        strikeAlong(level, e, damage, e.position().subtract(position()), knockback, lift);
    }

    private Vec3 hand() {
        return position().add(0, 2.0, 0).add(rotate(forward(), -90).scale(0.6));
    }

    private Vec3 lamp() {
        return centre().add(0, LAMP_UP, 0);
    }

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double len, double half, DustParticleOptions d) {
        Vec3 side = rotate(dir, 90).scale(half);
        for (double s = 1.0; s <= len; s += 1.0) {
            Vec3 p = from.add(dir.scale(s));
            level.sendParticles(d, p.x + side.x, p.y + 0.15, p.z + side.z, 1, 0, 0, 0, 0);
            level.sendParticles(d, p.x - side.x, p.y + 0.15, p.z - side.z, 1, 0, 0, 0, 0);
        }
    }

    /** A radial line from the room's centre at {@code degrees}, from r 1.5 to the glazing. */
    private void drawSpoke(ServerLevel level, double degrees, DustParticleOptions d, double step) {
        for (double r = 1.5; r <= roomR(); r += step) {
            Vec3 p = onRing(degrees, r);
            level.sendParticles(d, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** Signed progress of {@code a} from {@code from} in direction {@code dir}, in [0, 360). */
    private static double progress(double from, double a, int dir) {
        return Mth.positiveModulo((a - from) * dir, 360.0);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // thrust: he draws the harpoon back level at his hip (0.7 s) while a line ahead is drawn gold (red from 0.45 s,
        // when he stops turning); at 0.7 s he drives it down the line: 12 and a push
        out.add(BossAttack.of("thrust").anim(THRUST).timing(14, 6, 14).range(0, 6.5).cooldown(40).weight(12)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick < 9) {
                        turnToward(t, 8.0F);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), THRUST_LEN, THRUST_HALF, tick >= 9 ? RED : GOLD);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> thrustHit(level))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) > 6.0 ? "throw" : "whirl");
                    }
                })
                .build());
        // throw: he lifts the harpoon over his shoulder (0.9 s); a line toward you (to the glazing, at most 16) is drawn
        // white while he follows you (until 0.6 s), then red; at 0.9 s the harpoon flies down it at 1.2 blocks a tick:
        // the first player it meets takes 9 and is hauled in on the chain to 2.5 blocks from him (Slowness I 1 s)
        out.add(BossAttack.of("throw").anim(THROW).timing(18, 20, 14).range(5.0, 16.0).cooldown(100).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planLine(level, THROW_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12) {
                        turnToward(t, 5.0F);
                        planLine(level, THROW_MAX);
                    }
                    if (tick % 2 == 0 && !line.isEmpty()) {
                        drawLine(level, position(), forward(), flatDist(position(), line.get(line.size() - 1)), THROW_HALF,
                                tick >= 12 ? RED : WHITE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(harpoon(new ArrayList<>(line)));
                    level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .build());
        // whirl: he swings the harpoon low on its chain (0.9 s): a ring of 6.5 round him is drawn gold, red from 0.6 s,
        // the inner circle of 2 drawn white (safe); from 0.9 s the harpoon whirls once round him in 0.8 s: 10 and a push
        // to whoever stands between the circles when it passes
        out.add(BossAttack.of("whirl").anim(WHIRL).timing(18, 16, 14).range(0, 7.0).cooldown(90).weight(8)
                .track(false)
                .start((b, level, t, tick) -> whirlHit.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, position(), WHIRL_OUT, tick >= 12 ? RED : GOLD);
                        b.telegraphRing(level, position(), WHIRL_IN, WHITE);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.2F, 0.8F + tick * 0.03F);
                    }
                })
                .active((b, level, t, tick) -> whirlTick(level, tick))
                .build());
        // sweep: he raises his arm to the great lamp; the lens on his back spins up (1.2 s). The half of the room the
        // beam will turn through is drawn: its edge (a line through the centre) and arcs across it, gold, red from
        // 0.8 s, with arrows the way it will turn. From 1.2 s the beam turns through that half in 2 s: 8 and Blindness
        // 1.5 s to whoever it crosses. The other half, and the circle of 1.5 under the lamp, are safe
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(24, 40, 16).range(0, 30.0).cooldown(200).weight(6)
                .track(false)
                .start((b, level, t, tick) -> {
                    sweepDir = getRandom().nextBoolean() ? 1 : -1;
                    double aim = t != null ? angleOf(t.position()) : getRandom().nextDouble() * 360.0;
                    sweepStart = aim - sweepDir * 90.0;
                    sweepHit.clear();
                    level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    Vec3 l = lamp();
                    level.sendParticles(ParticleTypes.END_ROD, l.x, l.y - 1.0, l.z, 2, 0.6, 0.4, 0.6, 0.02);
                    if (tick % 3 != 0) {
                        return;
                    }
                    DustParticleOptions d = tick >= 16 ? RED : GOLD;
                    drawSpoke(level, sweepStart, d, 0.8);
                    drawSpoke(level, sweepStart + sweepDir * 180.0, d, 0.8);
                    for (double r : new double[] {5.0, 10.0, roomR() - 0.5}) {
                        for (double a = 10; a < 180; a += 120.0 / r) {
                            Vec3 p = onRing(sweepStart + sweepDir * a, r);
                            level.sendParticles(d, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    for (double r = 4.0; r <= roomR() - 2; r += 4.0) {      // arrows the way the beam turns
                        Vec3 p = onRing(sweepStart, r);
                        Vec3 tangent = rotate(p.subtract(centre()).multiply(1, 0, 1), sweepDir * 90.0);
                        for (double s = 0.5; s <= 2.0; s += 0.5) {
                            Vec3 q = p.add(tangent.scale(s));
                            level.sendParticles(WHITE, q.x, q.y + 0.3, q.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .active((b, level, t, tick) -> sweepTick(level, tick))
                .build());

        // ---------------------------------------------------------------- phase 2
        // surge: he raises the jawbone and the harpoon and calls the storm (1.1 s): the edge of the room behind him
        // is drawn sea blue with arrows toward you (red from 0.7 s); at 1.1 s he smashes them down and three waves
        // roll across the deck from that edge, 0.7 s apart, at 0.7 blocks a tick: 8, a shove along and a little lift
        // to whoever stands on the floor as one passes. Jump them
        out.add(BossAttack.of("surge").anim(SURGE).phaseTwo().timing(22, 40, 16).range(0, 30.0).cooldown(320).weight(5)
                .track(false)
                .start((b, level, t, tick) -> {
                    Vec3 to = t != null ? t.position().subtract(centre()).multiply(1, 0, 1) : forward();
                    if (to.lengthSqr() < 1.0) {
                        to = t != null ? t.position().subtract(position()).multiply(1, 0, 1) : forward();
                    }
                    surgeDir = to.lengthSqr() < 1.0E-4 ? forward() : to.normalize();
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (surgeDir == null || tick % 2 != 0) {
                        return;
                    }
                    DustParticleOptions d = tick >= 14 ? RED : SEA;
                    waveFront(level, -roomR() + 0.5, d, 0.8);
                    Vec3 side = rotate(surgeDir, 90);
                    for (int k = -2; k <= 2; k++) {
                        Vec3 base = centre().add(side.scale(k * 4.0));
                        for (double s = -2.0; s <= 1.0; s += 0.5) {
                            Vec3 q = base.add(surgeDir.scale(s));
                            level.sendParticles(FOAM, q.x, q.y + 0.3, q.z, 1, 0, 0, 0, 0);
                        }
                    }
                    level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 3.5, getZ(), 6, 0.6, 0.3, 0.6, 0.1);
                })
                .impact((b, level, t, tick) -> {
                    if (surgeDir != null) {
                        for (int i = 0; i < 3; i++) {
                            b.addEffect(wave(surgeDir, i * 14));
                        }
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.7F);
                    level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());
        // call: he swings his lantern heart's light over the floor like a signal lamp (1.0 s): the drowned crew climbs
        // in (drowned marines and tide wraiths, 2, more in co-op), never more than 3 at once
        out.add(BossAttack.of("call").anim(CALL).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(LAMP, getX(), getY() + 2.0, getZ(), 3, 0.5, 0.3, 0.5, 0);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> spawnAdds(level, 2))
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // overload: the lens tears up off his back and blazes over his head (2.0 s, guarded; rings of light gather on
        // him); at 2.0 s a ring of light runs out over the deck (10, jump it) and the Lamp Overload begins
        out.add(BossAttack.of("overload").anim(OVERLOAD).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(0.8, 12.0 - tick * 0.28), tick % 6 == 0 ? BEAM : GOLD);
                    }
                    level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 4.2, getZ(), 2, 0.4, 0.3, 0.4, 0.02);
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> startOverload(level))
                .build());
        // slam: he heaves the whale's jawbone over his head (1.1 s): a circle (3.5) 3.5 ahead of him is drawn gold while
        // he turns after you (until 0.6 s), red from 0.7 s; at 1.1 s it comes down: 15, a push and a lift inside, then
        // a ring runs out from it to 9 (6, jump it)
        out.add(BossAttack.of("slam").anim(SLAM).phaseTwo().timing(22, 10, 18).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planSlam(level);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12) {
                        turnToward(t, 4.0F);
                        planSlam(level);
                    }
                    if (tick % 2 == 0 && slamAt != null) {
                        b.telegraphRing(level, slamAt, SLAM_R, tick >= 14 ? RED : GOLD);
                        if (tick % 6 == 0) {
                            b.telegraphRing(level, slamAt, 9.0, WHITE);
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> slamHit(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void thrustHit(ServerLevel level) {
        Vec3 fwd = forward();
        for (LivingEntity e : victims(level, position(), THRUST_LEN + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= -0.5 && along <= THRUST_LEN && side <= THRUST_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                strikeAlong(level, e, 12.0F, fwd, 0.5, 0.15);
            }
        }
        for (double s = 1.0; s <= THRUST_LEN; s += 0.5) {
            Vec3 p = position().add(fwd.scale(s));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.4, p.z, 2, 0.1, 0.1, 0.1, 0.05);
        }
        Vec3 tip = ahead(THRUST_LEN);
        level.sendParticles(ParticleTypes.SPLASH, tip.x, tip.y + 1.2, tip.z, 10, 0.3, 0.3, 0.3, 0.1);
        level.playSound(null, this, SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 1.5F, 0.7F);
    }

    /** Open deck along his facing (every 0.6) out to {@code max}, stopping at the glazing or anything solid. */
    private void planLine(ServerLevel level, double max) {
        line.clear();
        Vec3 fwd = forward();
        for (double d = 1.0; d <= max; d += 0.6) {
            Vec3 p = position().add(fwd.scale(d));
            Vec3 s = pad(level, p.x, p.z);
            if (s == null) {
                break;
            }
            line.add(s);
        }
        if (line.isEmpty()) {
            line.add(ahead(1.0));
        }
    }

    /**
     * The thrown harpoon: two points of its line a tick (1.2 blocks), its chain drawn back to his hand. The first player
     * within reach of its head takes 9 and is hauled in on the chain (0.6 blocks a tick, up to 14 ticks) until 2.5 blocks
     * from him; Slowness I 1 s. If it meets no one it is drawn back.
     */
    private Effect harpoon(List<Vec3> path) {
        int[] t = {0};
        int[] head = {0};
        UUID[] caught = {null};
        int[] haul = {0};
        return (boss, level) -> {
            DrownedKeeper k = (DrownedKeeper) boss;
            t[0]++;
            if (caught[0] == null) {
                if (head[0] >= path.size()) {
                    return true;                                         // spent: the chain is wound back
                }
                head[0] = Math.min(path.size(), head[0] + 2);
                Vec3 p = path.get(head[0] - 1);
                level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.3, p.z, 3, 0.1, 0.1, 0.1, 0.02);
                k.chainTo(level, p.add(0, 1.3, 0));
                for (LivingEntity e : boss.victims(level, p, 2.5)) {
                    if (e instanceof Player && flatDist(e.position(), p) <= THROW_HALF + e.getBbWidth() / 2
                            && Math.abs(e.getY() - p.y) < 2.5) {
                        boss.strike(level, e, 9.0F, 0.0, 0.0);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                        caught[0] = e.getUUID();
                        level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 1.5F, 0.8F);
                        level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 0.7F);
                        break;
                    }
                }
                return false;
            }
            var ent = level.getEntity(caught[0]);
            if (!(ent instanceof LivingEntity e) || !e.isAlive() || haul[0]++ >= 14) {
                return true;
            }
            Vec3 to = boss.position().subtract(e.position()).multiply(1, 0, 1);
            if (to.length() <= 2.5) {
                e.setDeltaMovement(e.getDeltaMovement().multiply(0.2, 1, 0.2));
                e.hurtMarked = true;
                return true;
            }
            Vec3 pull = to.normalize().scale(0.6);
            e.setDeltaMovement(pull.x, Math.max(e.getDeltaMovement().y, 0.05), pull.z);
            e.hurtMarked = true;
            k.chainTo(level, e.position().add(0, 1.0, 0));
            if (haul[0] % 4 == 0) {
                level.playSound(null, boss, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.2F, 0.6F);
            }
            return false;
        };
    }

    private void chainTo(ServerLevel level, Vec3 to) {
        Vec3 from = hand();
        double len = from.distanceTo(to);
        for (double s = 0; s <= len; s += 0.6) {
            Vec3 p = from.lerp(to, s / Math.max(len, 0.01));
            level.sendParticles(STEEL, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
    }

    private void whirlTick(ServerLevel level, int tick) {
        double a = getYRot() + 90.0 - tick * 22.5;                      // a full turn in 16 ticks, from his facing
        Vec3 dir = rotate(new Vec3(1, 0, 0), a);
        for (double r = WHIRL_IN; r <= WHIRL_OUT; r += 0.5) {
            Vec3 p = position().add(dir.scale(r));
            level.sendParticles(r > WHIRL_OUT - 1 ? ParticleTypes.CRIT : STEEL, p.x, p.y + 0.6, p.z, 1, 0, 0, 0, 0);
        }
        double cos = Math.cos(Math.toRadians(15.0));
        for (LivingEntity e : victims(level, position(), WHIRL_OUT + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d >= WHIRL_IN && d <= WHIRL_OUT + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 2.5
                    && to.normalize().dot(dir) >= cos && whirlHit.add(e.getUUID())) {
                strike(level, e, 10.0F, 0.6, 0.15);
            }
        }
        if (tick % 4 == 0) {
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.2F, 0.7F);
        }
    }

    /** The lamp's beam at {@code tick}: it crosses players between its last place and this one (hit once each). */
    private void sweepTick(ServerLevel level, int tick) {
        double done = Math.min(180.0, tick * SWEEP_TURN + SWEEP_TURN);
        double a = sweepStart + sweepDir * done;
        Vec3 l = lamp();
        for (double r = 1.5; r <= roomR(); r += 1.0) {
            Vec3 p = onRing(a, r);
            level.sendParticles(BEAM, p.x, p.y + 0.3, p.z, 2, 0.15, 0.25, 0.15, 0);
            if (((int) r) % 4 == 0) {
                for (double f = 0.1; f < 1.0; f += 0.15) {
                    Vec3 q = l.lerp(p, f);
                    level.sendParticles(BEAM, q.x, q.y, q.z, 1, 0.05, 0.05, 0.05, 0);
                }
            }
        }
        Vec3 end = onRing(a, roomR() - 0.5);
        level.sendParticles(ParticleTypes.END_ROD, end.x, end.y + 0.5, end.z, 2, 0.3, 0.3, 0.3, 0.01);
        for (Player p : fighters(level)) {
            double d = flatDist(p.position(), centre());
            if (d < 1.5 || d > roomR() + 0.5 || Math.abs(p.getY() - centre().y) > 3.0 || sweepHit.containsKey(p.getUUID())) {
                continue;
            }
            double prog = progress(sweepStart, angleOf(p.position()), sweepDir);
            double slack = Math.toDegrees(0.6 / Math.max(1.5, d));
            if (prog <= 180.0 && prog <= done + slack) {
                sweepHit.put(p.getUUID(), tick);
                strike(level, p, 8.0F, 0.0, 0.0);
                p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0));
            }
        }
        if (tick % 10 == 0) {
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 1.4F);
        }
    }

    /** Points of a wave front {@code along} blocks from the centre along the surge (only inside the room). */
    private void waveFront(ServerLevel level, double along, DustParticleOptions d, double step) {
        if (surgeDir == null) {
            return;
        }
        Vec3 side = rotate(surgeDir, 90);
        double r = roomR();
        double half = Math.sqrt(Math.max(0, r * r - along * along));
        Vec3 mid = centre().add(surgeDir.scale(along));
        for (double s = -half; s <= half; s += step) {
            Vec3 p = mid.add(side.scale(s));
            level.sendParticles(d, p.x, p.y + 0.3, p.z, 1, 0, 0.05, 0, 0);
        }
    }

    /** A storm wave after {@code delay}: it rolls from the back edge across the room; it hits once who stands on the floor. */
    private Effect wave(Vec3 dir, int delay) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            DrownedKeeper k = (DrownedKeeper) boss;
            int j = t[0]++ - delay;
            if (j < 0) {
                return false;
            }
            double r = k.roomR();
            double along = -r + j * WAVE_SPEED;
            if (along > r) {
                return true;
            }
            Vec3 saved = k.surgeDir;
            k.surgeDir = dir;
            k.waveFront(level, along, SEA, 0.7);
            k.waveFront(level, along - 0.4, FOAM, 1.4);
            k.surgeDir = saved;
            Vec3 mid = k.centre().add(dir.scale(along));
            level.sendParticles(ParticleTypes.SPLASH, mid.x, mid.y + 0.6, mid.z, 12, r * 0.4, 0.2, r * 0.4, 0.1);
            for (Player p : k.fighters(level)) {
                double a = p.position().subtract(k.centre()).multiply(1, 0, 1).dot(dir);
                if (Math.abs(a - along) <= 0.8 && flatDist(p.position(), k.centre()) <= r + 0.5
                        && Math.abs(p.getY() - k.centre().y) < 2.5 && overFloor(level, p) < 0.6 && hit.add(p.getUUID())) {
                    k.strikeAlong(level, p, 8.0F, dir, 0.4, 0.3);
                }
            }
            if (j % 8 == 0) {
                level.playSound(null, mid.x, mid.y, mid.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 1.5F, 0.7F);
            }
            return false;
        };
    }

    // ---- the whale-bone slam (phase 3)

    private void planSlam(ServerLevel level) {
        Vec3 p = ahead(3.5);
        Vec3 s = inner(level, p.x, p.z, roomR() - 1.0);
        slamAt = s != null ? s : position();
    }

    private void slamHit(ServerLevel level) {
        Vec3 at = slamAt != null ? slamAt : ahead(3.5);
        for (LivingEntity e : victims(level, at, SLAM_R + 1)) {
            if (flatDist(e.position(), at) <= SLAM_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                strikeAlong(level, e, 15.0F, e.position().subtract(at), 0.6, 0.4);
            }
        }
        addEffect(floorRing(at, 9.0, 0.5, 6.0F, FOAM));
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.5, 0.2, 0.5, 0);
        level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.5, at.z, 30, 1.5, 0.3, 1.5, 0.2);
        level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 0.3, at.z, 12, 1.2, 0.1, 1.2, 0.05);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** A ring running out over the floor from {@code c}: it hits once whoever stands on the floor (jump). */
    private Effect floorRing(Vec3 c, double max, double speed, float damage, DustParticleOptions colour) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(colour, c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr, 1, 0, 0.05, 0, 0);
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

    // ---- the drowned crew (existing mobs of the mod)

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
            EntityType<? extends Mob> type = i % 2 == 0 ? ModEntities.DROWNED_MARINE.get() : ModEntities.TIDE_WRAITH.get();
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
            level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.5, at.z, 20, 0.4, 0.4, 0.4, 0.1);
            level.sendParticles(ParticleTypes.BUBBLE_POP, at.x, at.y + 0.8, at.z, 10, 0.3, 0.5, 0.3, 0.02);
        }
        level.playSound(null, this, SoundEvents.DROWNED_AMBIENT_WATER, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    private void discardAdds(ServerLevel level) {
        for (UUID id : adds) {
            var e = level.getEntity(id);
            if (e != null && e.isAlive()) {
                level.sendParticles(ParticleTypes.SPLASH, e.getX(), e.getY() + 0.5, e.getZ(), 10, 0.3, 0.3, 0.3, 0.05);
                e.discard();
            }
        }
        adds.clear();
    }

    // ------------------------------------------------------------------ phase 3: the Lamp Overload

    private void startOverload(ServerLevel level) {
        overload = true;
        flashTimer = 60;
        flashTick = -1;
        slamTimer = 80;
        darkTimer = 0;
        sectorAngle = getRandom().nextDouble() * 360.0;
        addEffect(floorRing(position(), roomR(), 0.55, 10.0F, BEAM));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("drowned_keeper_overload"), 0.08,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 l = lamp();
        level.sendParticles(ParticleTypes.END_ROD, l.x, l.y, l.z, 60, 2.0, 1.0, 2.0, 0.2);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3, getZ(), 30, 0.8, 0.8, 0.8, 0.15);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 2.0F, 0.8F);
    }

    /** Whether {@code p} stands in one of the three lit sectors (60° each, 60° of shadow between; under the lamp lit). */
    private boolean lit(Vec3 p) {
        if (flatDist(p, centre()) < 2.0) {
            return true;
        }
        double rel = Mth.positiveModulo(angleOf(p) - sectorAngle, 120.0);
        return rel < 60.0;
    }

    /** The turning sectors: their edges drawn sparsely all the time, densely during a flash's warning. */
    private void drawSectors(ServerLevel level, boolean warn, boolean red) {
        DustParticleOptions d = red ? RED : warn ? GOLD : BEAM;
        for (int k = 0; k < 3; k++) {
            double a0 = sectorAngle + k * 120.0;
            drawSpoke(level, a0, d, warn ? 0.8 : 2.0);
            drawSpoke(level, a0 + 60.0, d, warn ? 0.8 : 2.0);
            if (warn) {
                for (double r : new double[] {6.0, 12.0}) {
                    for (double a = 6; a < 60; a += 60.0 / r * 1.5) {
                        Vec3 p = onRing(a0 + a, r);
                        level.sendParticles(BEAM, p.x, p.y + 0.4, p.z, 1, 0.1, 0.1, 0.1, 0);
                    }
                }
            }
        }
    }

    private void flash(ServerLevel level) {
        Vec3 l = lamp();
        level.sendParticles(ParticleTypes.END_ROD, l.x, l.y - 2, l.z, 40, 1.5, 0.8, 1.5, 0.2);
        for (int k = 0; k < 3; k++) {
            for (double a = 5; a < 60; a += 10) {
                for (double r = 3; r <= roomR(); r += 3) {
                    Vec3 p = onRing(sectorAngle + k * 120.0 + a, r);
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.6, p.z, 1, 0.3, 0.3, 0.3, 0.02);
                }
            }
        }
        for (Player p : fighters(level)) {
            if (flatDist(p.position(), centre()) <= roomR() + 0.5 && Math.abs(p.getY() - centre().y) < 3.0 && lit(p.position())) {
                strike(level, p, 9.0F, 0.0, 0.0);
                p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0));
            }
        }
        level.playSound(null, l.x, l.y, l.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 1.6F);
        level.playSound(null, l.x, l.y, l.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 1.5F, 1.4F);
    }

    private void tickOverload(ServerLevel level, boolean busy, boolean fighting) {
        sectorAngle += sectorDir * SECTOR_TURN;
        if (--darkTimer <= 0) {                                    // the room goes dark
            darkTimer = 40;
            for (Player p : fighters(level)) {
                if (flatDist(p.position(), centre()) <= radius + 4) {
                    p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 70, 0, false, false));
                }
            }
        }
        if (flashTick >= 0) {
            boolean red = flashTick >= FLASH_WARN - 10;
            if (flashTick % 2 == 0) {
                drawSectors(level, true, red);
            }
            if (flashTick == FLASH_WARN - 10) {
                Vec3 l = lamp();
                level.playSound(null, l.x, l.y, l.z, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 3.0F, 1.8F);
            }
            if (++flashTick >= FLASH_WARN) {
                flash(level);
                flashTick = -1;
                flashTimer = Math.max(100, (int) Math.round(FLASH_EVERY * cooldownScale()));
                sectorDir = -sectorDir;
            }
            return;
        }
        if (tickCount % 6 == 0) {
            drawSectors(level, false, false);
        }
        if (fighting && !busy && guard == 0 && --flashTimer <= 0) {
            flashTick = 0;
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(BEAM, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.8F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    /** Back to the first phase (the fight was reset): base speed, no overload. */
    private void resetForm(ServerLevel level) {
        overload = false;
        roarUntil = -1;
        guard = 0;
        flashTick = -1;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("drowned_keeper_overload"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("drowned_keeper_wrath"));
        }
        discardAdds(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (phase() == 1 && overload) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !overload && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "overload");
            free = false;
        }
        if (overload && phase() == 2 && anyone) {
            cur = currentAttack();
            boolean busy = cur != null && "overload".equals(cur.name);
            tickOverload(level, busy, fighting);
            if (free && guard == 0 && flashTick < 0 && --slamTimer <= 0) {
                slamTimer = Math.max(100, (int) Math.round(SLAM_EVERY * cooldownScale()));
                chain(level, "slam");
            }
        } else if (overload && !anyone) {
            flashTick = -1;
        }
        // ambience: the lantern heart glows, water drips from his coat
        if (tickCount % 5 == 0) {
            Vec3 f = forward();
            level.sendParticles(LAMP, getX() + f.x * 0.45, getY() + 2.2, getZ() + f.z * 0.45, 1, 0.08, 0.08, 0.08, 0);
            level.sendParticles(ParticleTypes.DRIPPING_WATER, getX(), getY() + 1.5, getZ(), 1, 0.5, 0.6, 0.5, 0);
        }
        if (tickCount % 60 == 0) {
            level.playSound(null, this, SoundEvents.DROWNED_AMBIENT_WATER, SoundSource.HOSTILE, 0.8F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("drowned_keeper_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: cut it, and drop it where it would carry out of the room
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z).scale(0.3));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.2), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.5, getZ(), 40, 1.0, 1.0, 1.0, 0.2);
        level.sendParticles(LAMP, getX(), getY() + 2.2, getZ(), 20, 0.6, 0.6, 0.6, 0);
        level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        discardAdds(level);
        flashTick = -1;
        level.sendParticles(LAMP, getX(), getY() + 2.2, getZ(), 30, 0.8, 0.8, 0.8, 0.02);
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.0, getZ(), 60, 1.0, 1.5, 1.0, 0.2);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            discardAdds(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("LampCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("LampRadius", radius);
        output.putBoolean("LampOverload", overload);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("LampCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("LampRadius", 16);
        floorTol = -1;
        overload = input.getBooleanOr("LampOverload", false) && phase() == 2;
        flashTick = -1;
    }
}
