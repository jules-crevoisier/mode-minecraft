package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.AnvilWarden.BILLET;
import static com.brasshaven.generated.MobAnims.AnvilWarden.CHARGE;
import static com.brasshaven.generated.MobAnims.AnvilWarden.COMBO;
import static com.brasshaven.generated.MobAnims.AnvilWarden.GRAB;
import static com.brasshaven.generated.MobAnims.AnvilWarden.OVERHEAT;
import static com.brasshaven.generated.MobAnims.AnvilWarden.QUAKE;
import static com.brasshaven.generated.MobAnims.AnvilWarden.QUENCH;
import static com.brasshaven.generated.MobAnims.AnvilWarden.ROAR;
import static com.brasshaven.generated.MobAnims.AnvilWarden.SLAM;
import static com.brasshaven.generated.MobAnims.AnvilWarden.SPLASH;
import static com.brasshaven.generated.MobAnims.AnvilWarden.STAGGER;
import static com.brasshaven.generated.MobAnims.AnvilWarden.TITAN;
import static com.brasshaven.generated.MobAnims.AnvilWarden.VENT;

/**
 * Le Gardien de l'enclume (The Anvil Warden), the smith of the Forge of the Basalt Titan: a 5.6-block golem of
 * columnar basalt with molten seams, a graphite crucible for a helm, a forge hammer in its right hand and long tongs
 * in its left. It waits on the anvil's face (feet 36, a 49 x 39 slab rimmed by a low parapet, 34 blocks over the lava
 * lake), under the face of the great hammer the kneeling titan holds 30 blocks overhead.
 * <p>A deliberately hard Nether fight: 640 health, armour 14, poise 130, hits of 8 to 26. Three phases:
 * <ul>
 *     <li>Phase 1: the <b>slam</b> (a shockwave runs along the anvil from the strike), the <b>hammer combo</b>, the
 *     <b>tong grab</b> (caught, lifted and flung toward the middle of the anvil), the <b>molten splash</b> (globs from
 *     the crucible onto marked tiles, leaving burning patches), the <b>quench</b> (anti-hug steam burst) and the
 *     <b>charge</b>. A few times per phase it signals the titan and <b>the titan's hammer comes down</b> on the big
 *     marked zone under its face (or, away from the forge, on a zone round the target).</li>
 *     <li>Phase 2 (a roar at 65%): a third combo blow, triple shockwaves, the <b>quake</b> (two rings to jump), the
 *     <b>hurled billet</b> (a far-range burst), quench geysers under distant players, the titan's hammer more often.</li>
 *     <li>Phase 3 (at 30%): the <b>overheat</b> (invulnerable while it drinks the crucible): the anvil glows red, it is
 *     faster, leaves a trail of burning patches and every 15 s <b>vents</b> a radial blast of slag-steam that hugs the
 *     anvil: hide behind the anvil horn's root, the titan's fingers or a brazier, or get out of range (14).</li>
 * </ul>
 * The arena is a slab over lava: pushes are capped at 1.3; beyond 12 blocks from the centre the outward part of a push
 * is dropped and lift is capped, and where the floor ends 2.5 blocks along a push the push is cancelled (see
 * {@link #strike}). The tong throw always lands on the floor toward the centre. It places no blocks at all: its burning
 * patches, fire trail and steam are particles and hit checks, cleared on reset, death and removal.
 */
public class AnvilWarden extends WayfarerBoss {
    public static final float WIDTH = 2.6F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double EDGE_SAFE = 12.0;
    private static final double ARC_RANGE = 5.5;
    private static final double ARC_HALF = 75;
    private static final double VENT_R = 14.0;
    private static final int TITAN_P1 = 600;
    private static final int TITAN_P2 = 460;
    private static final int TITAN_P3 = 420;
    private static final int VENT_EVERY = 300;
    private static final int MAX_PATCHES = 24;
    private static final DustParticleOptions EMBER = new DustParticleOptions(0xFF7A1C, 1.4F);
    private static final DustParticleOptions HOT = new DustParticleOptions(0xFFE080, 1.3F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xC8260E, 1.6F);
    private static final DustParticleOptions STEAM = new DustParticleOptions(0xE8ECEC, 1.5F);
    private static final DustParticleOptions SLAG = new DustParticleOptions(0x3A3036, 1.6F);

    /** A burning patch on the anvil (molten splash, billet, fire trail): particles and hit checks only. */
    private record Patch(Vec3 pos, double r, int until, float damage) {}

    private @Nullable Vec3 centre;
    private int radius = 16;
    private boolean overheated;
    private boolean wasPhaseTwo;
    private int guard;
    private int roarUntil = -1;
    private int titanTimer = 300;
    private int ventTimer = 120;
    private boolean hammerSearched;
    private @Nullable Vec3 hammer;
    private double hammerR = 7.5;
    private @Nullable Vec3 zone;
    private double zoneR = 7.5;
    private @Nullable Vec3 lockedSpot;
    private @Nullable Vec3 chargeFrom;
    private @Nullable Vec3 chargeTo;
    private @Nullable LivingEntity held;
    private @Nullable Vec3 lastTrail;
    private final List<Vec3> spots = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private final List<Patch> patches = new ArrayList<>();

    public AnvilWarden(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 640.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.AnvilWarden.TICKS;
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
        return 130.0F;
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

    // ------------------------------------------------------------------ arena memory

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        hammerSearched = false;
        hammer = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Usable floor radius round the seal: the anvil's face is 18 blocks to its nearest parapet. */
    private double reach() {
        return Math.max(7.0, Math.min(15.0, radius - 1.0));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Top of the first solid block at or below {@code y + 2} (scanning 8 blocks), or NaN. */
    private static double floorY(ServerLevel level, double x, double y, double z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(y + 2), Mth.floor(z));
        for (int i = 0; i < 8; i++) {
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return p.getY() + 1.0;
            }
            p.move(0, -1, 0);
        }
        return Double.NaN;
    }

    /** A standing spot on the face at (x, z) with room for it above, or null. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 1.5) {
            return null;
        }
        for (int dy = 0; dy < 6; dy++) {
            BlockPos p = BlockPos.containing(x, y + dy, z);
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return null;
            }
        }
        return new Vec3(x, y, z);
    }

    /** {@code p} pulled inside the face (at most {@code reach() - margin} from the centre), at floor height. */
    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(2.0, reach() - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    /** A safe standing spot near {@code want}: tried there, then stepping toward the centre. */
    private Vec3 landingSpot(ServerLevel level, Vec3 want, double margin) {
        Vec3 p = clampToArena(want, margin);
        Vec3 c = centre();
        for (int i = 0; i < 12; i++) {
            Vec3 q = p.lerp(c, i / 12.0);
            Vec3 s = safeSpot(level, q.x, q.z);
            if (s != null) {
                return s;
            }
        }
        return c;
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
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 12, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    private static BlockParticleOption basaltBits() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.BASALT.defaultBlockState());
    }

    private static BlockParticleOption magmaBits() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MAGMA_BLOCK.defaultBlockState());
    }

    // ------------------------------------------------------------------ fairness over the lava

    /**
     * Every hit of its (moves, waves, the NG+ shockwave) comes through here. Pushes are capped at 1.3; beyond 12 blocks
     * from the centre (and wherever the floor ends 2.5 blocks along the push) the outward part is dropped and the rest
     * halved (cancelled at a drop), and lift is capped at 0.3: it never throws a player off the anvil.
     */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.3, knockback));
            push = tame(level, e, push);
        }
        if (flatDist(e.position(), centre()) > EDGE_SAFE) {
            lift = Math.min(lift, 0.3);
        }
        if (push.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    /** A horizontal push made safe for the anvil's edge (see {@link #strike}). */
    private Vec3 tame(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 radial = e.position().subtract(centre()).multiply(1, 0, 1);
        double r = radial.length();
        Vec3 probe = e.position().add(push.normalize().scale(2.5));
        double fy = floorY(level, probe.x, e.getY(), probe.z);
        boolean drop = Double.isNaN(fy) || fy < e.getY() - 2.5;
        if (drop) {
            return Vec3.ZERO;
        }
        if (r > EDGE_SAFE && r > 0.1) {
            Vec3 n = radial.scale(1.0 / r);
            double out = push.dot(n);
            if (out > 0) {
                push = push.subtract(n.scale(out));
            }
            push = push.scale(0.5);
        }
        return push;
    }

    /** Fire on a player, a little longer in phase 3. */
    private void burn(LivingEntity e, float seconds) {
        e.igniteForSeconds(overheated ? seconds + 1.0F : seconds);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // slam: the hammer heaved over its right shoulder (0.9 s; the strike circle and the crack line drawn in embers),
        // brought down 3.5 ahead: 16 in 2.8, and a shockwave runs on along the anvil (10, a toss). Phase 2: three lines
        out.add(BossAttack.of("slam").anim(SLAM).timing(18, 6, 16).range(0, 8.0).cooldown(60).weight(12)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 2.8, EMBER);
                        for (double a : w.slamFan()) {
                            Vec3 dir = rotate(b.forward(), a);
                            for (double d = 1.0; d <= 14.0; d += 1.5) {
                                Vec3 p = b.ahead(3.5).add(dir.scale(d));
                                level.sendParticles(EMBER, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    Vec3 at = b.ahead(3.5);
                    b.hitCircle(level, at, 2.8, 16.0F, 0.8, 0.3);
                    for (double a : w.slamFan()) {
                        b.addEffect(w.shockLine(at, rotate(b.forward(), a), 14.0, w.overheated ? 1.15 : 0.9, 10.0F));
                    }
                    level.sendParticles(basaltBits(), at.x, at.y + 0.3, at.z, 50, 1.2, 0.3, 1.2, 0.15);
                    level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.3, at.z, 8, 1.0, 0.2, 1.0, 0);
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 5.0 ? "quench" : "charge");
                    }
                })
                .build());
        // combo: the hammer cocked behind it (0.7 s, the arc drawn), a forehand, a backhand 0.5 s later after a turn
        // toward you; phase 2 adds an overhead blow down a line at 1.7 s that cracks the anvil ahead
        out.add(BossAttack.of("combo").anim(COMBO).timing(14, 24, 14).range(0, 6.5).cooldown(70).weight(11)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, ARC_RANGE, ARC_HALF, EMBER);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    if (tick == 0 || tick == 10) {
                        w.hammerArc(level, 13.0F);
                    }
                    if (tick == 3) {
                        w.turnToward(t, 30.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, ARC_RANGE, ARC_HALF, EMBER);
                    }
                    if (b.phase() == 2) {
                        if (tick == 12) {
                            w.turnToward(t, 25.0F);
                        }
                        if (tick > 12 && tick < 20 && tick % 2 == 0) {
                            for (double d = 1.0; d <= 6.5; d += 1.0) {
                                Vec3 p = b.ahead(d);
                                level.sendParticles(HOT, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                        if (tick == 20) {
                            b.hitLine(level, 6.5, 1.3, 16.0F, 0.6);
                            b.addEffect(w.shockLine(b.ahead(6.0), b.forward(), 6.0, 1.0, 9.0F));
                            Vec3 p = b.ahead(4.5);
                            level.sendParticles(basaltBits(), p.x, p.y + 0.3, p.z, 40, 1.0, 0.3, 1.0, 0.1);
                            level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.5F, 0.6F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w && w.overheated && t != null && b.distanceTo(t) > 7.0
                            && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "charge");
                    }
                })
                .build());
        // grab: the tongs opened and thrust out (0.8 s, a narrow line 5.5 long); the first player caught takes 8, is
        // lifted and held 0.6 s, then flung (6) toward the middle of the anvil: it never throws you toward the edge
        out.add(BossAttack.of("grab").anim(GRAB).timing(16, 20, 14).range(0, 6.0).cooldown(110).weight(9)
                .start((b, level, t, tick) -> held = null)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.0; d <= 5.5; d += 0.75) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(HOT, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.seize(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.holdStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> held = null)
                .build());
        // splash: the crucible tipped forward (1.0 s; the marked tiles ringed in embers, following until 0.7 s), then
        // jerked up: molten globs fly onto the tiles (12 in 2.2, set ablaze) and leave burning patches (3 s)
        out.add(BossAttack.of("splash").anim(SPLASH).timing(20, 10, 14).range(3.0, 24.0).cooldown(150).weight(9)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    if (tick < 14) {
                        w.pickSplashSpots(level, t);
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 p : w.spots) {
                            b.telegraphRing(level, p, 2.2, tick < 14 ? EMBER : HOT);
                        }
                        level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 5.6, b.getZ(), 1, 0.4, 0.1, 0.4, 0);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    Vec3 from = b.position().add(0, 5.6, 0).add(b.forward().scale(0.8));
                    for (Vec3 p : w.spots) {
                        b.addEffect(w.glob(from, p, 10, 2.2, 12.0F, 2.0, w.overheated ? 100 : 60));
                    }
                    w.spots.clear();
                    level.playSound(null, b, SoundEvents.BUCKET_EMPTY_LAVA, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .build());
        // quench: the billet plunged into the bucket at its hip (0.6 s, steam hissing round its feet), steam bursts out:
        // 11 in 5 and a scald that lingers 2 s (2 a half-second). Phase 2: geysers under up to three distant players
        out.add(BossAttack.of("quench").anim(QUENCH).timing(12, 4, 12).range(0, 5.0).cooldown(80).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.0, STEAM);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.3, b.getZ(), 4, 1.2, 0.1, 1.2, 0.02);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                    if (tick == 4 && b.phase() == 2 && b instanceof AnvilWarden w) {
                        w.pickGeysers(level);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    b.hitCircle(level, b.position(), 5.0, 11.0F, 1.0, 0.25);
                    b.addEffect(w.steamCloud(b.position(), 5.0, 40));
                    for (Vec3 p : w.spots) {
                        b.addEffect(w.geyser(p, 16, 1.8, 9.0F));
                    }
                    w.spots.clear();
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 1, b.getZ(), 80, 2.5, 0.8, 2.5, 0.08);
                    level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.GENERIC_EXTINGUISH_FIRE, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .build());
        // charge: head down, the hammer dragged behind it striking sparks (0.8 s; the path and its end drawn), it
        // barrels to you in 12 ticks (14 to whoever is in its way), then swings the hammer up through you (12, a toss)
        out.add(BossAttack.of("charge").anim(CHARGE).timing(16, 16, 16).range(7.0, 24.0).cooldown(120).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && t != null && b instanceof AnvilWarden w) {
                        Vec3 to = w.chargeEnd(level, t);
                        double len = flatDist(b.position(), to);
                        for (double d = 1.5; d < len; d += 1.0) {
                            Vec3 p = b.position().lerp(to, d / len);
                            level.sendParticles(EMBER, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                        b.telegraphRing(level, to, 2.0, HOT);
                    }
                    if (tick % 4 == 0) {
                        Vec3 back = b.position().subtract(b.forward().scale(1.5));
                        level.sendParticles(ParticleTypes.LAVA, back.x, back.y + 0.2, back.z, 2, 0.3, 0, 0.3, 0);
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.chargeFrom = b.position();
                        w.chargeTo = t != null ? w.chargeEnd(level, t) : w.landingSpot(level, b.ahead(10), 2.0);
                        w.faceToward(w.chargeTo);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.chargeStep(level, tick);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // quake: hammer and tongs raised (1.0 s; rings at 12 drawn); the hammer slams (14 in 3) and a shockwave rolls
        // out to 12 (10, jump it), then the tongs-fist slams 0.6 s later: a second ring (jump again)
        out.add(BossAttack.of("quake").anim(QUAKE).phaseTwo().timing(20, 16, 16).range(0, 12.0).cooldown(170).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 12.0, EMBER);
                        b.telegraphRing(level, b.position(), 6.0, SLAG);
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_DAMAGE, SoundSource.HOSTILE, 3.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        b.hitCircle(level, b.ahead(3.0), 3.0, 14.0F, 0.6, 0.3);
                        b.addEffect(w.ringWave(b.position(), 1.5, 12.0, 0.6, 10.0F, EMBER));
                        w.quakeBurst(level, b.ahead(3.0));
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 12 && b instanceof AnvilWarden w) {
                        b.addEffect(w.ringWave(b.position(), 1.5, 12.0, w.overheated ? 0.8 : 0.65, 10.0F, HOT));
                        w.quakeBurst(level, b.ahead(2.5));
                    }
                })
                .build());
        // billet: the glowing billet swung back over its shoulder (0.9 s; a ring follows the target, then locks for the
        // last 0.2 s) and hurled: it bursts on the spot (13 in 2.5, set ablaze, a burning patch). Phase 3: it bounces on
        out.add(BossAttack.of("billet").anim(BILLET).phaseTwo().timing(18, 6, 14).range(8.0, 26.0).cooldown(130).weight(8)
                .start((b, level, t, tick) -> lockedSpot = null)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof AnvilWarden w)) {
                        return;
                    }
                    if ((tick <= 14 || w.lockedSpot == null) && t != null) {
                        w.lockedSpot = w.clampToArena(t.position(), 0.5);
                    }
                    if (tick % 2 == 0 && w.lockedSpot != null) {
                        b.telegraphRing(level, w.lockedSpot, 2.5, tick > 14 ? HOT : EMBER);
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.BLAZE_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w && w.lockedSpot != null) {
                        Vec3 from = b.position().add(0, 4.0, 0);
                        b.addEffect(w.billet(level, from, w.lockedSpot));
                        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- scheduled (bossTick), never rolled
        // titan: it raises the hammer to the titan and beats it on the tongs three times (2.0 s); the zone under the
        // titan's hammer is ringed in red with slag sifting down from the hammer's face; the great hammer comes down:
        // 26 in the zone (set ablaze), and a shockwave rolls out from its rim to 17 (8, jump it)
        out.add(BossAttack.of("titan").anim(TITAN).timing(40, 10, 16).range(999, 999).cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.planZone(level, t);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.zoneTelegraph(level, tick);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.titanBlow(level);
                    }
                })
                .build());
        // overheat: at 30%, once: it kneels and drinks its crucible (1.5 s, invulnerable, the anvil starts to glow),
        // rises white-hot: a fire wave (12, jump it), +18% speed, a trail of burning patches from now on
        out.add(BossAttack.of("overheat").anim(OVERHEAT).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 52;
                    level.playSound(null, b, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 5.0, b.getZ(), 2, 0.6, 0.3, 0.6, 0);
                    level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 2.5, b.getZ(), 6, 1.0, 1.4, 1.0, 0.02);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.35, RED);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 3.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.overheat(level);
                    }
                })
                .build());
        // vent: it locks its arms over its chest while the crucible boils over (2.0 s; the reach of the blast, 14, ringed
        // in red); then it throws itself open: a sheet of slag-steam rolls over the anvil (20, set ablaze, a push).
        // Anything solid between you and it shields you: the root of the anvil's horn, the titan's fingers, a brazier
        out.add(BossAttack.of("vent").anim(VENT).phaseTwo().timing(40, 6, 24).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), VENT_R, RED);
                        b.telegraphRing(level, b.position(), 2.0 + (tick % 12) * 1.0, STEAM);
                    }
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 5.8, b.getZ(), 2, 0.4, 0.2, 0.4, 0.02);
                    level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 5.6, b.getZ(), 1, 0.5, 0.1, 0.5, 0);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.01F);
                    }
                    if (tick == 30) {
                        level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.3F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AnvilWarden w) {
                        w.ventBlast(level);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private double[] slamFan() {
        return phase() == 2 ? new double[] {-28, 0, 28} : new double[] {0};
    }

    private void hammerArc(ServerLevel level, float damage) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(ARC_HALF));
        for (LivingEntity e : victims(level, position(), ARC_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= ARC_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos) && e.getY() - getY() < 4) {
                strike(level, e, damage, 1.0, 0.2);
                burn(e, 2.0F);
            }
        }
        for (double a = -ARC_HALF; a <= ARC_HALF; a += 12) {
            Vec3 p = position().add(rotate(fwd, a).scale(ARC_RANGE - 1.2));
            level.sendParticles(EMBER, p.x, p.y + 1.4, p.z, 2, 0.2, 0.3, 0.2, 0.02);
        }
        Vec3 c = ahead(3.0);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.5, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    /**
     * A shockwave running along the anvil from {@code from}: basalt bursts {@code speed} blocks a tick, a toss and
     * {@code damage} once per victim within 1.2 of it; it dies where the face ends (no floor at its height).
     */
    private Effect shockLine(Vec3 from, Vec3 dir, double len, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] d = {0.5};
        return (boss, level) -> {
            Vec3 p = from.add(dir.scale(d[0]));
            double fy = floorY(level, p.x, from.y, p.z);
            if (Double.isNaN(fy) || Math.abs(fy - from.y) > 1.6) {
                return true;
            }
            level.sendParticles(basaltBits(), p.x, fy + 0.3, p.z, 8, 0.3, 0.5, 0.3, 0.1);
            level.sendParticles(EMBER, p.x, fy + 0.6, p.z, 3, 0.25, 0.4, 0.25, 0.02);
            if (((int) (d[0] * 10)) % 30 < 10) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.2 + e.getBbWidth() / 2 && e.getY() - fy < 2.0 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.0, 0.5);
                }
            }
            d[0] += speed;
            return d[0] > len;
        };
    }

    /** A ring of shock rolling out from radius {@code r0} to {@code rMax}: it hits grounded players on its rim once. */
    private Effect ringWave(Vec3 c, double r0, double rMax, double speed, float damage, ParticleOptions particle) {
        Set<UUID> hit = new HashSet<>();
        double[] r = {r0};
        return (boss, level) -> {
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(particle, c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && e.getY() - c.y < 0.9 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.6, 0.4);
                }
            }
            return rr >= rMax;
        };
    }

    private void quakeBurst(ServerLevel level, Vec3 at) {
        level.sendParticles(basaltBits(), at.x, at.y + 0.3, at.z, 60, 1.6, 0.3, 1.6, 0.15);
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.8, 0.2, 0.8, 0);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    // ---- the grab
    private void seize(ServerLevel level) {
        Vec3 fwd = forward();
        LivingEntity best = null;
        double bestAlong = 99;
        for (LivingEntity e : victims(level, position(), 7)) {
            if (!(e instanceof Player)) {
                continue;
            }
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            if (along > 0 && along <= 5.5 && to.subtract(fwd.scale(along)).length() <= 1.0 + e.getBbWidth() / 2
                    && e.getY() - getY() < 3.5 && along < bestAlong) {
                best = e;
                bestAlong = along;
            }
        }
        level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 2.0F, 1.4F);
        if (best != null) {
            strike(level, best, 8.0F, 0.0, 0.0);
            burn(best, 2.0F);
            held = best;
            level.playSound(null, best.getX(), best.getY(), best.getZ(), SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.6F);
        } else {
            Vec3 tip = ahead(5.0);
            level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 1.5, tip.z, 10, 0.3, 0.3, 0.3, 0.2);
        }
    }

    private void holdStep(ServerLevel level, int tick) {
        LivingEntity e = held;
        if (e == null || !e.isAlive() || e.distanceTo(this) > 9.0) {
            held = null;
            return;
        }
        if (tick < 12) {
            Vec3 p = ahead(2.4);
            e.teleportTo(p.x, getY() + 1.6 + tick * 0.08, p.z);
            e.setDeltaMovement(Vec3.ZERO);
            e.hurtMarked = true;
            e.fallDistance = 0;
            if (tick % 3 == 0) {
                level.sendParticles(ParticleTypes.SMALL_FLAME, e.getX(), e.getY() + 1, e.getZ(), 4, 0.3, 0.4, 0.3, 0.01);
            }
        } else if (tick == 12) {
            Vec3 dir = centre().subtract(position()).multiply(1, 0, 1);
            if (dir.length() < 3.0) {
                dir = forward().scale(-1);                       // near the middle: flung behind it
            }
            Vec3 land = landingSpot(level, position().add(dir.normalize().scale(8.0)), 3.0);
            Vec3 d = land.subtract(e.position()).multiply(1, 0, 1);
            double dist = d.length();
            e.hurtServer(level, damageSources().mobAttack(this), 6.0F);
            Vec3 v = dist < 0.3 ? Vec3.ZERO : d.normalize().scale(Math.min(1.0, dist / 9.4));
            e.setDeltaMovement(v.x, 0.55, v.z);
            e.hurtMarked = true;
            e.fallDistance = 0;
            telegraphRing(level, land, 1.5, HOT);
            level.sendParticles(ParticleTypes.FLAME, e.getX(), e.getY() + 1, e.getZ(), 16, 0.4, 0.5, 0.4, 0.05);
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
            held = null;
        }
    }

    // ---- the molten splash
    /** Marked tiles: on the target and two near it (phase 2: on every player, up to 4, plus two strays; phase 3: +1). */
    private void pickSplashSpots(ServerLevel level, @Nullable LivingEntity target) {
        spots.clear();
        if (target != null) {
            Vec3 c = clampToArena(target.position(), 1.0);
            spots.add(c);
            if (phase() == 1) {
                Vec3 side = rotate(target.position().subtract(position()).multiply(1, 0, 1), 90);
                spots.add(clampToArena(c.add(side.scale(4.2)), 1.0));
                spots.add(clampToArena(c.subtract(side.scale(4.2)), 1.0));
            }
        }
        if (phase() == 2) {
            for (Player p : fighters(level)) {
                if (p != target && spots.size() < 4) {
                    spots.add(clampToArena(p.position(), 1.0));
                }
            }
            int strays = overheated ? 3 : 2;
            java.util.Random r = new java.util.Random(getUUID().getLeastSignificantBits() + tickCount / 40);
            for (int i = 0, tries = 0; i < strays && tries < 24; tries++) {
                double a = r.nextDouble() * Math.PI * 2;
                double d = 2 + r.nextDouble() * Math.max(2, reach() - 3);
                Vec3 p = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
                boolean ok = true;
                for (Vec3 s : spots) {
                    ok &= flatDist(s, p) >= 4.0;
                }
                if (ok) {
                    spots.add(p);
                    i++;
                }
            }
        }
    }

    /** A molten glob arcing from {@code from} onto {@code to} in {@code flight} ticks: a burst, then a burning patch. */
    private Effect glob(Vec3 from, Vec3 to, int flight, double r, float damage, double patchR, int patchLife) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < flight) {
                double f = k / (double) flight;
                Vec3 p = from.lerp(to, f).add(0, Math.sin(Math.PI * f) * 4.0, 0);
                level.sendParticles(HOT, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0);
                level.sendParticles(ParticleTypes.FALLING_LAVA, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
                if (k % 2 == 0) {
                    boss.telegraphRing(level, to, r, HOT);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.LAVA, to.x, to.y + 0.3, to.z, 12, r * 0.4, 0.2, r * 0.4, 0);
            level.sendParticles(magmaBits(), to.x, to.y + 0.3, to.z, 20, r * 0.4, 0.3, r * 0.4, 0.1);
            level.playSound(null, to.x, to.y, to.z, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 2.0F, 0.7F);
            for (LivingEntity e : boss.victims(level, to, r + 1)) {
                if (flatDist(e.position(), to) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - to.y) < 2.5) {
                    boss.strike(level, e, damage, 0.0, 0.25);
                    if (boss instanceof AnvilWarden w) {
                        w.burn(e, 3.0F);
                    }
                }
            }
            if (boss instanceof AnvilWarden w) {
                w.addPatch(to, patchR, patchLife, 3.0F);
            }
            return true;
        };
    }

    private void addPatch(Vec3 at, double r, int life, float damage) {
        if (patches.size() >= MAX_PATCHES) {
            patches.remove(0);
        }
        patches.add(new Patch(at, r, tickCount + life, damage));
    }

    /** Burning patches: flames and embers; whoever stands in one takes {@code damage} every half-second and burns. */
    private void tickPatches(ServerLevel level) {
        if (patches.isEmpty()) {
            return;
        }
        patches.removeIf(p -> p.until() <= tickCount);
        for (Patch p : patches) {
            if (tickCount % 3 == 0) {
                level.sendParticles(ParticleTypes.FLAME, p.pos().x, p.pos().y + 0.1, p.pos().z, 3, p.r() * 0.45, 0.05, p.r() * 0.45, 0.01);
                level.sendParticles(EMBER, p.pos().x, p.pos().y + 0.15, p.pos().z, 2, p.r() * 0.45, 0.02, p.r() * 0.45, 0);
            }
            if (tickCount % 10 == 0) {
                for (LivingEntity e : victims(level, p.pos(), p.r() + 1)) {
                    if (flatDist(e.position(), p.pos()) <= p.r() + e.getBbWidth() / 2 && Math.abs(e.getY() - p.pos().y) < 1.3) {
                        e.hurtServer(level, damageSources().mobAttack(this), p.damage());
                        burn(e, 2.0F);
                    }
                }
            }
        }
    }

    // ---- the quench
    private void pickGeysers(ServerLevel level) {
        spots.clear();
        for (Player p : fighters(level)) {
            if (spots.size() < 3 && flatDist(p.position(), position()) > 6.0) {
                spots.add(clampToArena(p.position(), 0.5));
            }
        }
    }

    private Effect steamCloud(Vec3 at, double r, int life) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k % 2 == 0) {
                level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 0.8, at.z, 6, r * 0.45, 0.6, r * 0.45, 0.01);
            }
            if (k > 0 && k % 10 == 0) {
                for (LivingEntity e : boss.victims(level, at, r + 1)) {
                    if (e instanceof Player && flatDist(e.position(), at) <= r && Math.abs(e.getY() - at.y) < 2.5) {
                        e.hurtServer(level, boss.damageSources().mobAttack(boss), 2.0F);
                    }
                }
            }
            return k >= life;
        };
    }

    /** A steam geyser: white steam hisses on the spot for {@code warn} ticks, then it bursts: damage and a small toss. */
    private Effect geyser(Vec3 at, int warn, double r, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, r, STEAM);
                    level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 0.1, at.z, 2, r * 0.3, 0.02, r * 0.3, 0.01);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 1.5, at.z, 40, r * 0.3, 1.5, r * 0.3, 0.1);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.6F);
            for (LivingEntity e : boss.victims(level, at, r + 1)) {
                if (flatDist(e.position(), at) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                    boss.strike(level, e, damage, 0.0, 0.5);
                }
            }
            return true;
        };
    }

    // ---- the charge
    private Vec3 chargeEnd(ServerLevel level, LivingEntity t) {
        Vec3 to = t.position().subtract(position()).multiply(1, 0, 1);
        double len = to.length();
        Vec3 want = len < 1.0 ? t.position() : position().add(to.scale(Math.max(0.0, len - 1.5) / len));
        return landingSpot(level, want, 1.5);
    }

    private void chargeStep(ServerLevel level, int tick) {
        if (chargeFrom == null || chargeTo == null) {
            return;
        }
        if (tick <= 11) {
            Vec3 p = chargeFrom.lerp(chargeTo, tick / 11.0);
            teleportTo(p.x, chargeTo.y, p.z);
            setDeltaMovement(Vec3.ZERO);
            level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 0.2, getZ(), 1, 0.4, 0, 0.4, 0);
            level.sendParticles(basaltBits(), getX(), getY() + 0.2, getZ(), 4, 0.6, 0.1, 0.6, 0.05);
            for (LivingEntity e : victims(level, position(), 3.0)) {
                if (flatDist(e.position(), position()) <= 2.0 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                    strike(level, e, 14.0F, 1.0, 0.3);
                }
            }
            if (tick % 3 == 0) {
                level.playSound(null, this, SoundEvents.IRON_GOLEM_STEP, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
        }
        if (tick == 12) {
            Vec3 fwd = forward();
            double cos = Math.cos(Math.toRadians(70));
            for (LivingEntity e : victims(level, position(), 5.5)) {
                Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
                double d = to.length();
                if (d <= 4.5 + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                    strike(level, e, 12.0F, 0.6, 0.6);
                    burn(e, 2.0F);
                }
            }
            Vec3 c = ahead(2.5);
            level.sendParticles(ParticleTypes.FLAME, c.x, c.y + 1, c.z, 30, 1.0, 1.0, 1.0, 0.05);
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
        }
    }

    // ---- the billet
    private Effect billet(ServerLevel level, Vec3 from, Vec3 to) {
        int[] t = {0};
        Vec3 dir0 = to.subtract(from).multiply(1, 0, 1);
        Vec3 dir = dir0.lengthSqr() < 1.0E-4 ? forward() : dir0.normalize();
        boolean bounce = overheated;
        return (boss, lvl) -> {
            int k = t[0]++;
            int flight = 12;
            if (k < flight) {
                double f = k / (double) flight;
                Vec3 p = from.lerp(to, f).add(0, Math.sin(Math.PI * f) * 3.0, 0);
                lvl.sendParticles(HOT, p.x, p.y, p.z, 3, 0.1, 0.1, 0.1, 0);
                lvl.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
                return false;
            }
            if (k == flight && boss instanceof AnvilWarden w) {
                w.billetBurst(lvl, to, 2.5, 13.0F);
                if (!bounce) {
                    return true;
                }
            }
            if (bounce && k == flight + 8 && boss instanceof AnvilWarden w) {
                Vec3 next = w.clampToArena(to.add(dir.scale(5.0)), 0.5);
                double fy = floorY(lvl, next.x, w.centre().y + 1, next.z);
                if (!Double.isNaN(fy) && Math.abs(fy - w.centre().y) < 1.6) {
                    w.billetBurst(lvl, new Vec3(next.x, fy, next.z), 2.0, 10.0F);
                }
                return true;
            }
            if (bounce && k > flight && boss instanceof AnvilWarden w) {
                double f = (k - flight) / 8.0;
                Vec3 next = w.clampToArena(to.add(dir.scale(5.0)), 0.5);
                Vec3 p = to.lerp(next, f).add(0, Math.sin(Math.PI * f) * 2.0, 0);
                lvl.sendParticles(HOT, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0);
                if (k % 2 == 0) {
                    boss.telegraphRing(lvl, next, 2.0, HOT);
                }
            }
            return false;
        };
    }

    private void billetBurst(ServerLevel level, Vec3 at, double r, float damage) {
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.3, at.z, 10, r * 0.4, 0.2, r * 0.4, 0);
        level.sendParticles(ParticleTypes.FLAME, at.x, at.y + 0.5, at.z, 24, r * 0.4, 0.4, r * 0.4, 0.05);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.5F, 0.8F);
        for (LivingEntity e : victims(level, at, r + 1)) {
            if (flatDist(e.position(), at) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                strike(level, e, damage, 0.4, 0.3);
                burn(e, 4.0F);
            }
        }
        addPatch(at, 2.0, overheated ? 100 : 70, 3.0F);
    }

    // ---- the titan's hammer
    /**
     * The great hammer the titan holds over the anvil: the columns 26-34 blocks above the face (within 14 of the centre)
     * that hold solid blocks, averaged; its zone's radius from their count. Found once per arena; null away from the
     * forge (then the hammer falls round the target).
     */
    private void findHammer(ServerLevel level) {
        if (hammerSearched) {
            return;
        }
        hammerSearched = true;
        BlockPos base = BlockPos.containing(centre());
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        double sx = 0;
        double sz = 0;
        int n = 0;
        for (int dx = -14; dx <= 14; dx++) {
            for (int dz = -14; dz <= 14; dz++) {
                for (int dy = 26; dy <= 34; dy++) {
                    p.set(base.getX() + dx, base.getY() + dy, base.getZ() + dz);
                    if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                        sx += dx;
                        sz += dz;
                        n++;
                        break;
                    }
                }
            }
        }
        if (n >= 30) {
            hammer = new Vec3(base.getX() + 0.5 + sx / n, centre().y, base.getZ() + 0.5 + sz / n);
            hammerR = Mth.clamp(Math.sqrt(n / Math.PI) + 0.3, 5.0, 9.0);
        } else {
            hammer = null;
        }
    }

    private void planZone(ServerLevel level, @Nullable LivingEntity t) {
        findHammer(level);
        if (hammer != null) {
            zone = hammer;
            zoneR = hammerR;
        } else {
            zone = clampToArena(t != null ? t.position() : centre(), 3.0);
            zoneR = 6.0;
        }
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void zoneTelegraph(ServerLevel level, int tick) {
        if (zone == null) {
            return;
        }
        Vec3 z = zone;
        if (tick % 2 == 0) {
            telegraphRing(level, z, zoneR, RED);
            telegraphRing(level, z, Math.max(1.0, zoneR * (1.0 - tick / 40.0)), EMBER);
        }
        double drop = hammer != null ? 29.0 : 14.0;
        for (int i = 0; i < 4; i++) {                            // slag sifting down from the hammer's face
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = getRandom().nextDouble() * zoneR;
            double h = drop * getRandom().nextDouble();
            level.sendParticles(ParticleTypes.ASH, z.x + Math.cos(a) * d, z.y + h, z.z + Math.sin(a) * d, 2, 0.2, 0.2, 0.2, 0);
        }
        if (tick % 4 == 0) {
            level.sendParticles(ParticleTypes.FALLING_LAVA, z.x, z.y + drop, z.z, 6, zoneR * 0.5, 0.2, zoneR * 0.5, 0);
        }
        if (tick == 8 || tick == 16 || tick == 24) {              // the three blows on the tongs: the signal
            level.playSound(null, this, SoundEvents.ANVIL_USE, SoundSource.HOSTILE, 3.0F, 0.6F);
            level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0F, 0.5F);
            telegraphRing(level, z, zoneR + 0.5, HOT);
        }
        if (tick == 28) {
            level.playSound(null, z.x, z.y + 20, z.z, SoundEvents.IRON_GOLEM_DEATH, SoundSource.HOSTILE, 4.0F, 0.3F);
        }
    }

    private void titanBlow(ServerLevel level) {
        if (zone == null) {
            return;
        }
        Vec3 z = zone;
        for (LivingEntity e : victims(level, z, zoneR + 1)) {
            if (flatDist(e.position(), z) <= zoneR + e.getBbWidth() / 2 && Math.abs(e.getY() - z.y) < 4.0) {
                strike(level, e, 26.0F, 0.0, 0.4);
                burn(e, 3.0F);
            }
        }
        addEffect(ringWave(z, zoneR, 17.0, 0.7, 8.0F, EMBER));
        double drop = hammer != null ? 29.0 : 14.0;
        for (double h = 0; h < drop; h += 1.5) {
            level.sendParticles(ParticleTypes.LARGE_SMOKE, z.x, z.y + h, z.z, 3, zoneR * 0.4, 0.4, zoneR * 0.4, 0.01);
        }
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, z.x, z.y + 1, z.z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.EXPLOSION, z.x, z.y + 0.5, z.z, 10, zoneR * 0.5, 0.3, zoneR * 0.5, 0);
        level.sendParticles(basaltBits(), z.x, z.y + 0.5, z.z, 160, zoneR * 0.5, 0.4, zoneR * 0.5, 0.2);
        level.sendParticles(ParticleTypes.LAVA, z.x, z.y + 0.5, z.z, 30, zoneR * 0.5, 0.3, zoneR * 0.5, 0);
        level.playSound(null, z.x, z.y, z.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 5.0F, 0.3F);
        level.playSound(null, z.x, z.y, z.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 4.0F, 0.5F);
        level.playSound(null, z.x, z.y, z.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 4.0F, 0.4F);
        zone = null;
    }

    // ---- phase 3
    private void overheat(ServerLevel level) {
        overheated = true;
        ventTimer = 120;
        addEffect(ringWave(position(), 1.5, 13.0, 0.55, 12.0F, RED));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("anvil_warden_overheat"), 0.18,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 c = centre();
        level.sendParticles(RED, c.x, c.y + 0.2, c.z, 300, reach() * 0.6, 0.05, reach() * 0.6, 0);
        level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 3, getZ(), 80, 1.4, 2.0, 1.4, 0.06);
        level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** True when something solid stands between it and {@code e} at the height the slag-steam rolls (0.8 off the floor). */
    private boolean covered(ServerLevel level, LivingEntity e) {
        Vec3 from = new Vec3(getX(), getY() + 0.8, getZ());
        Vec3 to = new Vec3(e.getX(), e.getY() + 0.8, e.getZ());
        BlockHitResult r = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return r.getType() != HitResult.Type.MISS && r.getLocation().distanceToSqr(from) < from.distanceToSqr(to) - 0.25;
    }

    private void ventBlast(ServerLevel level) {
        Vec3 from = new Vec3(getX(), getY() + 0.8, getZ());
        for (int i = 0; i < 40; i++) {                          // the sheet of slag-steam, stopped by anything solid
            double a = Math.PI * 2 * i / 40;
            Vec3 to = from.add(Math.cos(a) * VENT_R, 0, Math.sin(a) * VENT_R);
            BlockHitResult r = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
            double len = r.getType() == HitResult.Type.MISS ? VENT_R : r.getLocation().distanceTo(from);
            for (double d = 1.5; d <= len; d += 1.0) {
                Vec3 p = from.add(Math.cos(a) * d, 0, Math.sin(a) * d);
                level.sendParticles(d > len - 1.0 ? ParticleTypes.LARGE_SMOKE : ParticleTypes.FLAME, p.x, p.y, p.z, 1, 0.15, 0.2, 0.15, 0.02);
            }
        }
        for (LivingEntity e : victims(level, position(), VENT_R + 1)) {
            if (flatDist(e.position(), position()) > VENT_R + e.getBbWidth() / 2 || Math.abs(e.getY() - getY()) > 4.0) {
                continue;
            }
            if (covered(level, e)) {
                level.sendParticles(ParticleTypes.WHITE_SMOKE, e.getX(), e.getY() + 1, e.getZ(), 6, 0.3, 0.4, 0.3, 0.02);
                continue;
            }
            strike(level, e, 20.0F, 0.8, 0.2);
            burn(e, 5.0F);
        }
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 1.5, getZ(), 4, 1.0, 0.5, 1.0, 0);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp() {
        patches.clear();
        spots.clear();
        held = null;
        zone = null;
        lastTrail = null;
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        tickPatches(level);
        if (phase() == 2) {
            wasPhaseTwo = true;
        }
        if (phase() == 1 && wasPhaseTwo) {                          // the fight was reset
            wasPhaseTwo = false;
            overheated = false;
            roarUntil = -1;
            titanTimer = 300;
            cleanUp();
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("anvil_warden_overheat"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("anvil_warden_wrath"));
            }
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && !patches.isEmpty()) {
            cleanUp();
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        // the scheduled moves count real fighting time and wait for a free moment to start
        if (fighting && tickCount > roarUntil) {
            titanTimer--;
            if (overheated) {
                ventTimer--;
            }
        }
        if (free) {
            if (phase() == 2 && !overheated && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "overheat");
            } else if (overheated && ventTimer <= 0) {
                ventTimer = (int) Math.round(VENT_EVERY * cooldownScale());
                titanTimer = Math.max(titanTimer, 100);
                chain(level, "vent");
            } else if (titanTimer <= 0) {
                int every = phase() == 1 ? TITAN_P1 : overheated ? TITAN_P3 : TITAN_P2;
                titanTimer = (int) Math.round(every * cooldownScale());
                ventTimer = Math.max(ventTimer, 100);
                chain(level, "titan");
            }
        }
        // the overheated anvil: a fire trail behind it, the face glowing red, embers off its seams
        if (overheated) {
            if (tickCount % 6 == 0 && fighting) {
                if (lastTrail == null || flatDist(lastTrail, position()) > 1.2) {
                    if (lastTrail != null && onGround()) {
                        addPatch(lastTrail, 1.3, 80, 3.0F);
                    }
                    lastTrail = position();
                }
            }
            if (tickCount % 4 == 0) {
                Vec3 c = centre();
                double a = getRandom().nextDouble() * Math.PI * 2;
                double d = getRandom().nextDouble() * reach();
                level.sendParticles(RED, c.x + Math.cos(a) * d, c.y + 0.1, c.z + Math.sin(a) * d, 6, 1.5, 0.02, 1.5, 0);
                level.sendParticles(ParticleTypes.LAVA, c.x + Math.cos(a) * d, c.y + 0.1, c.z + Math.sin(a) * d, 1, 1.0, 0, 1.0, 0);
            }
            if (tickCount % 3 == 0) {
                level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 2, 1.0, 1.4, 1.0, 0.01);
            }
        }
        if (tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 5.9, getZ(), 1, 0.3, 0.1, 0.3, 0.01);
        }
        if (tickCount % 140 == 0) {
            level.playSound(null, this, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        titanTimer = 40;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("anvil_warden_wrath"), 0.08,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 5.6, getZ(), 40, 1.0, 0.5, 1.0, 0);
        level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 3, getZ(), 60, 1.5, 2.0, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp();
        level.sendParticles(basaltBits(), getX(), getY() + 2, getZ(), 120, 1.5, 2.0, 1.5, 0.1);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 4, getZ(), 80, 1.2, 1.5, 1.2, 0.03);
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 5, getZ(), 30, 1.0, 0.5, 1.0, 0);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DEATH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        cleanUp();
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("WardenCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("WardenRadius", radius);
        output.putBoolean("WardenOverheated", overheated);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("WardenCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("WardenRadius", 16);
        overheated = input.getBooleanOr("WardenOverheated", false) && phase() == 2;
        wasPhaseTwo = phase() == 2;
        hammerSearched = false;
        hammer = null;
        cleanUp();
    }
}
