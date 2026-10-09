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
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.MyceliumAbbot.BURROW;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.CENSER;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.COMMUNION;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.CROOK;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.CROZIER;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.MONKS;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.PODS;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.ROAR;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.STAGGER;
import static com.brasshaven.generated.MobAnims.MyceliumAbbot.TENDRILS;

/**
 * L'Abbé du Mycélium (The Mycelium Abbot), the champion of the Mycelium Monastery: a steam monk (3.4 blocks) grown into
 * the fungal network, in an umber habit eaten into mycelium, a broad brown mushroom cap for a hood, brass censer chains
 * and a brass reliquary-boiler on his back; a crozier crowned with a glowing mushroom in his right hand, a censer
 * swinging from his left. He holds the arena under the cap's dome (44 wide, a glass oculus at its crown).
 * <ul>
 *     <li>Phase 1: the <b>crozier</b> (a sweep round his front, then an overhead slam down a red line), the
 *     <b>censer</b> (swung across his front, it leaves a trail of spore clouds: Nausea and Poison, briefly), the
 *     <b>tendrils</b> (marked circles under the players: tendrils erupt and root whoever stays), the <b>crook</b> (a
 *     marked line: the crook snaps along it and hauls whoever it catches toward him).</li>
 *     <li>Phase 2 (a roar at 65%): faster, he plants <b>pods</b> on marked spots (mushroom blocks that burst after 5 s
 *     unless broken) and calls his <b>monks</b> (bell monks, never more than 3).</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>Communion</b>. He <b>burrows</b> into the
 *     floor and bursts up under a player inside a ring that hunts them, and rings of mushrooms <b>bloom</b> outward over
 *     the floor (jump them).</li>
 * </ul>
 * The only blocks he places are the pods (red mushroom blocks in air cells over the floor): each goes away when it
 * bursts, when the fight resets, the arena empties, he dies or is removed, and on the first tick after a reload.
 */
public class MyceliumAbbot extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.4F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_RANGE = 5.5;
    private static final double SWEEP_HALF = 70;
    private static final double SLAM_LEN = 7.5;
    private static final double SLAM_HALF = 1.2;
    private static final double CENSER_HALF = 60;
    private static final double CENSER_RANGE = 7.5;
    private static final double PUFF_R = 1.7;
    private static final double TENDRIL_R = 2.0;
    private static final double CROOK_LEN = 9.0;
    private static final double CROOK_HALF = 1.0;
    private static final double POD_BLAST = 3.5;
    private static final int POD_FUSE = 100;
    private static final double BURROW_R = 2.5;
    private static final double BURROW_SPEED = 0.18;     // the hunting ring: slower than walking
    private static final int BURROW_EVERY = 240;
    private static final int BLOOM_EVERY = 220;
    private static final int BLOOM_WARN = 30;
    private static final DustParticleOptions SPORE = new DustParticleOptions(0x9C7FB0, 1.5F);
    private static final DustParticleOptions CYAN = new DustParticleOptions(0x64E8D8, 1.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xD8342A, 1.5F);
    private static final DustParticleOptions CAPDUST = new DustParticleOptions(0x92603C, 1.6F);
    private static final DustParticleOptions WHITE = new DustParticleOptions(0xE6DEEA, 1.4F);
    private static final DustParticleOptions GREEN = new DustParticleOptions(0x7EA050, 1.8F);

    /** A planted pod: the air cell it fills, its age in ticks. */
    private static final class Pod {
        final BlockPos pos;
        int age;

        Pod(BlockPos pos, int age) {
            this.pos = pos;
            this.age = age;
        }
    }

    private record SavedPod(long pos) {
        static final Codec<SavedPod> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedPod::pos)).apply(i, SavedPod::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 16;
    private double floorTol = -1;
    /** Phase 3 has started (the Communion). */
    private boolean communion;
    private int guard;
    private int roarUntil = -1;
    private int burrowTimer = 100;
    private int bloomTimer = 60;
    private int bloomTick = -1;
    private boolean hidden;
    // moves in flight
    private Vec3 swingDir = new Vec3(0, 0, 1);
    private final List<Vec3> marks = new ArrayList<>();
    private Vec3 ringAt = Vec3.ZERO;
    private @Nullable UUID ringOwner;
    private final List<Vec3> podSpots = new ArrayList<>();
    private final List<Pod> pods = new ArrayList<>();
    private final List<SavedPod> stalePods = new ArrayList<>();
    private final Set<UUID> adds = new HashSet<>();

    public MyceliumAbbot(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 650.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 13.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.25);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MyceliumAbbot.TICKS;
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
        return 110.0F;
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

    // ------------------------------------------------------------------ arena memory (the floor under the cap's dome)

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

    /** The usable floor: seal radius + 3, between 12 and 19 (the braziers stand at 20.8 in the monastery). */
    private double floorR() {
        return Math.min(Math.max(radius, 9) + 3.0, 19.0);
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

    /** Whether the floor round the seal is flat (the arena) or rough (a command spawn somewhere else). */
    private double floorTol(ServerLevel level) {
        if (floorTol > 0) {
            return floorTol;
        }
        Vec3 c = centre();
        int flat = 0;
        int samples = 0;
        for (int i = 0; i < 48; i++) {
            double a = i * 2.39996;
            double d = Math.sqrt((i + 0.5) / 48.0) * Math.max(3, floorR() - 1);
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

    /** A spot of open floor at (x, z) within the usable radius, two blocks of air over it; or null. */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z) {
        Vec3 c = centre();
        if (Math.hypot(x - c.x, z - c.z) > floorR() + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > floorTol(level) || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Open floor at (x, z), moved toward the centre until it lies within {@code maxR} of it; or null. */
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
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 8, 14, radius + 8),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    private static boolean apart(List<Vec3> spots, Vec3 s, double min) {
        for (Vec3 o : spots) {
            if (flatDist(o, s) < min) {
                return false;
            }
        }
        return true;
    }

    /** Pushes are kept only when open floor lies 1.5 blocks along them; otherwise they are dropped. */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        Vec3 flat = new Vec3(push.x, 0, push.z);
        if (flat.lengthSqr() < 1.0E-6) {
            return Vec3.ZERO;
        }
        Vec3 probe = e.position().add(flat.normalize().scale(1.5));
        return pad(level, probe.x, probe.z) == null ? Vec3.ZERO : flat;
    }

    /** Pushes capped at 1.0 and lift at 0.5 (0.2 when the push was dropped at the floor's edge). */
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
        lift = Math.min(lift, dropped ? 0.2 : 0.5);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
    }

    /** The glowing mushroom on the crozier's crook, over his right shoulder. */
    private Vec3 crook() {
        return position().add(0, 3.6, 0).add(rotate(forward(), -90).scale(0.9));
    }

    private void sporeBurst(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(SPORE, at.x, at.y, at.z, count, spread, spread * 0.6, spread, 0.0);
        level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, at.x, at.y, at.z, Math.max(1, count / 2), spread, spread * 0.6, spread, 0.0);
    }

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double len, double half, DustParticleOptions d) {
        Vec3 side = rotate(dir, 90).scale(half);
        for (double s = 1.0; s <= len; s += 1.0) {
            Vec3 p = from.add(dir.scale(s));
            level.sendParticles(d, p.x + side.x, p.y + 0.15, p.z + side.z, 1, 0, 0, 0, 0);
            level.sendParticles(d, p.x - side.x, p.y + 0.15, p.z - side.z, 1, 0, 0, 0, 0);
        }
    }

    /** Whoever stands within {@code half} of the line from his feet along {@code dir}, {@code len} long. */
    private List<LivingEntity> onLine(ServerLevel level, Vec3 dir, double len, double half) {
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : victims(level, position().add(dir.scale(len / 2)), len / 2 + half + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(dir);
            double off = to.subtract(dir.scale(along)).length();
            if (along >= -0.5 && along <= len + 0.5 && off <= half + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                out.add(e);
            }
        }
        return out;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // crozier: he draws the crozier back over his right shoulder (0.7 s, an arc drawn in spores, red from 0.45 s) and
        // sweeps it round his front: 12 and a push; he turns (up to 20°), a red line is drawn ahead and 0.5 s later he
        // brings the crozier down overhead along it: 13 and a lift
        out.add(BossAttack.of("crozier").anim(CROZIER).timing(14, 14, 16).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        DustParticleOptions d = tick >= 9 ? RED : SPORE;
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, d);
                        b.telegraphArc(level, SWEEP_RANGE - 2.0, SWEEP_HALF, d);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> sweep(level))
                .active((b, level, t, tick) -> {
                    if (tick == 0) {
                        turnToward(t, 20.0F);
                    }
                    if (tick < 10 && tick % 2 == 0) {
                        drawLine(level, position(), forward(), SLAM_LEN, SLAM_HALF, RED);
                    }
                    if (tick == 10) {
                        slam(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) > 5.0 ? "crook" : "censer");
                    }
                })
                .build());
        // censer: the censer swung back on its chain (0.9 s) while an arc (±60°, 7.5) is drawn in spores, red from 0.6 s;
        // from 0.9 s he swings it across his front in 0.8 s and it leaves a trail of spore clouds (r 1.7) that hang 2 s
        // (3 s in phase 2): 2 every half second inside, with Nausea 3 s and Poison I 2.5 s
        out.add(BossAttack.of("censer").anim(CENSER).timing(18, 16, 14).range(0, 9.0).cooldown(90).weight(10)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    swingDir = forward();
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        DustParticleOptions d = tick >= 12 ? RED : SPORE;
                        for (double a = -CENSER_HALF; a <= CENSER_HALF; a += 8) {
                            Vec3 p = position().add(rotate(swingDir, a).scale(CENSER_RANGE));
                            level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                        for (double s = 1.5; s <= CENSER_RANGE; s += 1.0) {
                            for (int side = -1; side <= 1; side += 2) {
                                Vec3 p = position().add(rotate(swingDir, side * CENSER_HALF).scale(s));
                                level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.0F, 0.8F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        double a = CENSER_HALF - 2 * CENSER_HALF * tick / 14.0;
                        Vec3 dir = rotate(swingDir, a);
                        int life = b.phase() == 2 ? 60 : 40;
                        for (double s = 2.5; s <= CENSER_RANGE - 0.5; s += 2.5) {
                            Vec3 p = pad(level, getX() + dir.x * s, getZ() + dir.z * s);
                            if (p != null) {
                                addEffect(puff(p, life));
                            }
                        }
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 0.6F, 0.6F + tick * 0.03F);
                    }
                })
                .build());
        // tendrils: he raises the crozier, chanting (1.3 s); a circle (r 2) is marked under each player where they stand
        // (and two more on open floor in phase 2), drawn in spores, red from 0.8 s; at 1.3 s he drives the crozier into the
        // floor and tendrils erupt in them: 10, a small lift, and Slowness IV 1.5 s (rooted)
        out.add(BossAttack.of("tendrils").anim(TENDRILS).timing(26, 10, 14).range(0, 24.0).cooldown(120).weight(9)
                .track(false)
                .start((b, level, t, tick) -> planTendrils(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Vec3 s : marks) {
                            b.telegraphRing(level, s, TENDRIL_R, tick >= 16 ? RED : SPORE);
                            level.sendParticles(ParticleTypes.MYCELIUM, s.x, s.y + 0.1, s.z, 4, 0.8, 0.05, 0.8, 0);
                        }
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 1.2F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Vec3 s : marks) {
                        level.sendParticles(WHITE, s.x, s.y + 0.6, s.z, 24, 0.8, 0.8, 0.8, 0);
                        level.sendParticles(ParticleTypes.MYCELIUM, s.x, s.y + 0.4, s.z, 16, 1.0, 0.6, 1.0, 0.05);
                        for (LivingEntity e : victims(level, s, TENDRIL_R + 1)) {
                            if (flatDist(e.position(), s) <= TENDRIL_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.5) {
                                strike(level, e, 10.0F, 0.0, 0.3);
                                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 3));
                            }
                        }
                        level.playSound(null, s.x, s.y, s.z, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .build());
        // crook: the crozier levelled at you, the crook hooked out (0.8 s); a line (9, half width 1) toward you is drawn
        // in spores while he turns after you (until 0.5 s), then red; at 0.8 s the crook snaps along it: 7, and whoever
        // it catches is hauled toward him (never off the floor)
        out.add(BossAttack.of("crook").anim(CROOK).timing(16, 8, 16).range(3.5, 10.0).cooldown(80).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 4.0F);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), CROOK_LEN, CROOK_HALF, tick >= 10 ? RED : SPORE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 fwd = forward();
                    for (double s = 1.0; s <= CROOK_LEN; s += 0.7) {
                        Vec3 p = position().add(fwd.scale(s));
                        level.sendParticles(CYAN, p.x, p.y + 1.2, p.z, 2, 0.1, 0.1, 0.1, 0);
                    }
                    for (LivingEntity e : onLine(level, fwd, CROOK_LEN, CROOK_HALF)) {
                        strike(level, e, 7.0F, 0.0, 0.1);
                        Vec3 to = position().subtract(e.position()).multiply(1, 0, 1);
                        double d = to.length();
                        if (d > 2.5) {
                            Vec3 pull = safePush(level, e, to.normalize().scale(Math.min(1.0, (d - 2.0) * 0.18)));
                            e.push(pull.x, 0.15, pull.z);
                            e.hurtMarked = true;
                        }
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 0.7F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // pods: he kneels and sows spores from the censer (1.0 s); spots on open floor are marked (a circle r 1 and the
        // burst's reach r 3.5 dotted); at 1.0 s a pod (a red mushroom block) sprouts on each: it swells for 5 s (red the
        // last 1.5 s) and bursts (8 and Poison I 3 s within 3.5) unless a player breaks it first
        out.add(BossAttack.of("pods").anim(PODS).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(360).weight(6)
                .track(false)
                .start((b, level, t, tick) -> planPods(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Vec3 s : podSpots) {
                            b.telegraphRing(level, s, 1.0, CYAN);
                        }
                    }
                    if (tick % 6 == 0) {
                        for (Vec3 s : podSpots) {
                            b.telegraphRing(level, s, POD_BLAST, SPORE);
                        }
                        level.playSound(null, b, SoundEvents.BONE_MEAL_USE, SoundSource.HOSTILE, 1.2F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> plantPods(level))
                .build());
        // monks: he rings the censer high over his head (1.0 s): bell monks answer from the dark (2, more in co-op), never
        // more than 3 at once
        out.add(BossAttack.of("monks").anim(MONKS).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        sporeBurst(level, position().add(0, 4.2, 0), 4, 0.3);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> spawnAdds(level, 2))
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // communion: he sinks to his knees, arms wide (2.0 s, guarded; rings of spores close in on him); then the network
        // answers: a ring of mushrooms blooms out over the floor (10, jump it)
        out.add(BossAttack.of("communion").anim(COMMUNION).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(0.8, 12.0 - tick * 0.28), tick % 6 == 0 ? SPORE : CYAN);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.2F, 0.5F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> startCommunion(level))
                .build());
        // burrow: he sinks into the floor (1.0 s); hidden and untouchable, a ring (r 2.5) hunts a player at 0.18 blocks a
        // tick for 1 s, then holds red 0.5 s; he bursts up in it (14 and a lift) and two rings of mushrooms bloom out from
        // there 0.4 s apart (7 each, jump them)
        out.add(BossAttack.of("burrow").anim(BURROW).phaseTwo().timing(20, 40, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 80;
                    ringOwner = t != null ? t.getUUID() : null;
                    Vec3 base = t != null ? t.position() : centre();
                    Vec3 s = inner(level, base.x, base.z, floorR() - 1.0);
                    ringAt = s != null ? s : centre();
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.MYCELIUM, getX(), getY() + 0.2, getZ(), 10, 1.0, 0.1, 1.0, 0.05);
                    level.sendParticles(CAPDUST, getX(), getY() + 0.3, getZ(), 4, 0.8, 0.2, 0.8, 0);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                    if (tick == 19) {
                        hide(true);
                    }
                })
                .active((b, level, t, tick) -> burrowTick(level, tick))
                .end((b, level, t, tick) -> {
                    hide(false);
                    guard = 0;
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void sweep(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SWEEP_HALF));
        for (LivingEntity e : victims(level, position(), SWEEP_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SWEEP_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 12.0F, 0.6, 0.2);
            }
        }
        for (double a = -SWEEP_HALF; a <= SWEEP_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SWEEP_RANGE - 0.8));
            level.sendParticles(CYAN, p.x, p.y + 1.3, p.z, 2, 0.1, 0.2, 0.1, 0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    private void slam(ServerLevel level) {
        Vec3 fwd = forward();
        for (LivingEntity e : onLine(level, fwd, SLAM_LEN, SLAM_HALF)) {
            strike(level, e, 13.0F, 0.0, 0.35);
        }
        for (double s = 1.0; s <= SLAM_LEN; s += 1.0) {
            Vec3 p = position().add(fwd.scale(s));
            sporeBurst(level, p.add(0, 0.3, 0), 3, 0.3);
            level.sendParticles(CYAN, p.x, p.y + 0.4, p.z, 2, 0.3, 0.2, 0.3, 0);
        }
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.3F);
        level.playSound(null, this, SoundEvents.FUNGUS_BREAK, SoundSource.HOSTILE, 1.5F, 0.5F);
    }

    /** A spore cloud left by the censer: hangs {@code life} ticks; 2, Nausea 3 s and Poison I 2.5 s every 10 ticks inside. */
    private Effect puff(Vec3 at, int life) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k >= life || !boss.isAlive()) {
                return true;
            }
            if (k % 2 == 0) {
                level.sendParticles(SPORE, at.x, at.y + 0.8, at.z, 3, PUFF_R * 0.5, 0.5, PUFF_R * 0.5, 0);
                level.sendParticles(GREEN, at.x, at.y + 1.0, at.z, 1, PUFF_R * 0.4, 0.4, PUFF_R * 0.4, 0);
            }
            if (k % 6 == 0) {
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, at.x, at.y + 1.0, at.z, 2, PUFF_R * 0.5, 0.5, PUFF_R * 0.5, 0);
            }
            if (k % 10 == 4) {
                for (LivingEntity e : boss.victims(level, at, PUFF_R + 1)) {
                    if (flatDist(e.position(), at) <= PUFF_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        boss.strike(level, e, 2.0F, 0.0, 0.0);
                        e.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 60, 0));
                        e.addEffect(new MobEffectInstance(MobEffects.POISON, 50, 0));
                    }
                }
            }
            return false;
        };
    }

    /** One circle under each player (snapshot), plus two on open floor near them in phase 2; at most 6. */
    private void planTendrils(ServerLevel level, @Nullable LivingEntity target) {
        marks.clear();
        List<LivingEntity> who = new ArrayList<>(fighters(level));
        if (target != null && !who.contains(target)) {
            who.add(0, target);
        }
        for (LivingEntity e : who) {
            Vec3 s = inner(level, e.getX(), e.getZ(), floorR());
            if (s != null && marks.size() < 4) {
                marks.add(s);
            }
        }
        int extra = phase() == 2 ? 2 : 0;
        for (int tries = 0; tries < 20 && extra > 0 && !who.isEmpty(); tries++) {
            LivingEntity e = who.get(getRandom().nextInt(who.size()));
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 3.0 + getRandom().nextDouble() * 3.0;
            Vec3 s = pad(level, e.getX() + Math.cos(a) * d, e.getZ() + Math.sin(a) * d);
            if (s != null && apart(marks, s, 3.0)) {
                marks.add(s);
                extra--;
            }
        }
        if (marks.isEmpty()) {
            marks.add(target != null ? target.position() : ahead(4));
        }
    }

    // ---- the pods

    /** {@code min(4, scaledCount(2) + 1)} spots on open floor, 4-9 from a player, never within 2.5 of one, 3 apart. */
    private void planPods(ServerLevel level, @Nullable LivingEntity target) {
        podSpots.clear();
        int n = Math.min(4, scaledCount(2) + 1);
        List<Player> who = fighters(level);
        for (int tries = 0; tries < 40 && podSpots.size() < n; tries++) {
            Vec3 base = who.isEmpty() ? (target != null ? target.position() : centre()) : who.get(getRandom().nextInt(who.size())).position();
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 4.0 + getRandom().nextDouble() * 5.0;
            Vec3 s = pad(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d);
            if (s == null || !apart(podSpots, s, 3.0) || flatDist(s, position()) < 2.0) {
                continue;
            }
            boolean near = false;
            for (Player p : who) {
                if (flatDist(p.position(), s) < 2.5) {
                    near = true;
                }
            }
            if (!near) {
                podSpots.add(s);
            }
        }
    }

    /** A pod in each planned air cell (still air, nobody standing in it). */
    private void plantPods(ServerLevel level) {
        BlockState pod = Blocks.RED_MUSHROOM_BLOCK.defaultBlockState();
        for (Vec3 s : podSpots) {
            BlockPos b = BlockPos.containing(s.x, s.y + 0.05, s.z);
            if (!level.isLoaded(b) || !level.getBlockState(b).isAir()
                    || !level.getEntitiesOfClass(LivingEntity.class, new AABB(b)).isEmpty()) {
                continue;
            }
            level.setBlock(b, pod, 3);
            pods.add(new Pod(b, 0));
            sporeBurst(level, Vec3.atCenterOf(b), 10, 0.5);
            level.playSound(null, b, SoundEvents.FUNGUS_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
        podSpots.clear();
    }

    /** Pods swell for 5 s and burst; a broken pod (no longer a mushroom block) fizzles. */
    private void tickPods(ServerLevel level) {
        for (Pod p : new ArrayList<>(pods)) {
            p.age++;
            Vec3 c = Vec3.atBottomCenterOf(p.pos);
            if (!level.isLoaded(p.pos)) {
                continue;
            }
            if (!level.getBlockState(p.pos).is(Blocks.RED_MUSHROOM_BLOCK)) {
                pods.remove(p);                                   // broken in time
                level.sendParticles(ParticleTypes.POOF, c.x, c.y + 0.5, c.z, 8, 0.3, 0.3, 0.3, 0.02);
                level.playSound(null, p.pos, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.0F, 0.8F);
                continue;
            }
            boolean late = p.age >= POD_FUSE - 30;
            if (p.age % (late ? 4 : 10) == 0) {
                telegraphRing(level, c, POD_BLAST, late ? RED : SPORE);
                level.playSound(null, p.pos, SoundEvents.PUFFER_FISH_BLOW_UP, SoundSource.HOSTILE, 0.8F, 0.6F + p.age * 0.01F);
            }
            if (p.age % 3 == 0) {
                level.sendParticles(SPORE, c.x, c.y + 1.1, c.z, 2, 0.3, 0.1, 0.3, 0);
            }
            if (p.age >= POD_FUSE) {
                pods.remove(p);
                level.setBlock(p.pos, Blocks.AIR.defaultBlockState(), 3);
                sporeBurst(level, c.add(0, 0.6, 0), 40, 1.6);
                level.sendParticles(GREEN, c.x, c.y + 0.6, c.z, 20, 1.5, 0.6, 1.5, 0);
                level.playSound(null, p.pos, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.5F);
                for (LivingEntity e : victims(level, c, POD_BLAST + 1)) {
                    if (flatDist(e.position(), c) <= POD_BLAST + e.getBbWidth() / 2 && Math.abs(e.getY() - c.y) < 2.5) {
                        strike(level, e, 8.0F, 0.4, 0.3);
                        e.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0));
                    }
                }
            }
        }
    }

    /** Every pod goes away (only where it is still a mushroom block). */
    private void clearPods(ServerLevel level) {
        for (SavedPod s : stalePods) {
            pods.add(new Pod(BlockPos.of(s.pos()), 0));
        }
        stalePods.clear();
        for (Pod p : pods) {
            if (level.isLoaded(p.pos) && level.getBlockState(p.pos).is(Blocks.RED_MUSHROOM_BLOCK)) {
                level.setBlock(p.pos, Blocks.AIR.defaultBlockState(), 3);
            }
        }
        pods.clear();
        podSpots.clear();
    }

    // ---- the monks (bell monks of the order)

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
            EntityType<? extends Mob> type = ModEntities.BELL_MONK.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                double d = 5.0 + random.nextDouble() * 4.0;
                at = pad(level, getX() + Math.cos(a) * d, getZ() + Math.sin(a) * d);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            sporeBurst(level, at.add(0, 1.0, 0), 10, 0.5);
            level.sendParticles(ParticleTypes.MYCELIUM, at.x, at.y + 0.2, at.z, 16, 0.6, 0.1, 0.6, 0.05);
        }
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.5F, 0.6F);
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

    // ------------------------------------------------------------------ phase 3: Communion

    private void startCommunion(ServerLevel level) {
        communion = true;
        burrowTimer = 100;
        bloomTimer = 60;
        bloomTick = -1;
        addEffect(bloom(position(), floorR(), 0.5, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("mycelium_abbot_communion"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        sporeBurst(level, position().add(0, 2.5, 0), 50, 2.5);
        level.playSound(null, this, SoundEvents.SCULK_CATALYST_BLOOM, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    /** A ring of mushrooms blooming out over the floor from {@code c}: hits once whoever stands on the floor (jump). */
    private Effect bloom(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                double x = c.x + Math.cos(a) * rr;
                double z = c.z + Math.sin(a) * rr;
                level.sendParticles(i % 3 == 0 ? CYAN : CAPDUST, x, c.y + 0.25, z, 1, 0, 0.08, 0, 0);
                if (i % 4 == 0) {
                    level.sendParticles(WHITE, x, c.y + 0.05, z, 1, 0, 0, 0, 0);
                }
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                double fy = floorY(level, e.getX(), e.getY(), e.getZ());
                double over = Double.isNaN(fy) ? 9.0 : e.getY() - fy;
                if (Math.abs(d - rr) <= 1.0 && over < 0.6 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.0, 0.3);
                }
            }
            return rr >= max;
        };
    }

    private void hide(boolean on) {
        hidden = on;
        setInvisible(on);
    }

    /** 0-19 the ring hunts its player, 20-29 it holds red, 30 he bursts up in it, 30 and 38 the blooms. */
    private void burrowTick(ServerLevel level, int tick) {
        Vec3 s = ringAt;
        if (tick < 20 && ringOwner != null) {
            var owner = level.getEntity(ringOwner);
            if (owner instanceof LivingEntity le && le.isAlive()) {
                Vec3 to = le.position().subtract(s).multiply(1, 0, 1);
                double d = to.length();
                if (d > 0.05) {
                    Vec3 next = s.add(to.normalize().scale(Math.min(d, BURROW_SPEED)));
                    Vec3 p = inner(level, next.x, next.z, floorR() - 1.0);
                    if (p != null) {
                        ringAt = s = p;
                    }
                }
            }
        }
        if (tick < 30 && tick % 2 == 0) {
            telegraphRing(level, s, BURROW_R, tick >= 20 ? RED : SPORE);
            telegraphRing(level, s, BURROW_R * 0.5, CYAN);
            level.sendParticles(ParticleTypes.MYCELIUM, s.x, s.y + 0.1, s.z, 6, 1.0, 0.05, 1.0, 0.02);
        }
        if (tick < 30 && tick % 6 == 0) {
            level.playSound(null, s.x, s.y, s.z, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 1.2F, 0.5F + tick * 0.02F);
        }
        if (tick == 30) {
            teleportTo(s.x, s.y, s.z);
            hide(false);
            guard = 0;
            sporeBurst(level, s.add(0, 1.0, 0), 30, 1.2);
            level.sendParticles(ParticleTypes.EXPLOSION, s.x, s.y + 0.5, s.z, 1, 0, 0, 0, 0);
            level.playSound(null, s.x, s.y, s.z, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
            level.playSound(null, s.x, s.y, s.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.2F);
            for (LivingEntity e : victims(level, s, BURROW_R + 1)) {
                if (flatDist(e.position(), s) <= BURROW_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.5) {
                    strike(level, e, 14.0F, 0.8, 0.5);
                }
            }
            addEffect(bloom(s, 9.0, 0.45, 7.0F));
        }
        if (tick == 38) {
            addEffect(bloom(ringAt, 9.0, 0.45, 7.0F));
        }
    }

    /** The fairy rings: 30 ticks of a ring gathering at the centre, then three rings bloom out 12 ticks apart. */
    private void tickBloom(ServerLevel level) {
        int k = bloomTick;
        Vec3 c = centre();
        if (k < BLOOM_WARN) {
            if (k % 3 == 0) {
                telegraphRing(level, c, Math.max(0.8, 4.0 - k * 0.1), k >= BLOOM_WARN - 10 ? RED : CYAN);
                level.sendParticles(ParticleTypes.MYCELIUM, c.x, c.y + 0.1, c.z, 8, 1.5, 0.05, 1.5, 0.02);
            }
            if (k == 0) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.8F);
            }
        } else {
            int w = k - BLOOM_WARN;
            if (w % 12 == 0) {
                addEffect(bloom(c, floorR(), 0.4, 7.0F));
                level.playSound(null, c.x, c.y, c.z, SoundEvents.SCULK_CATALYST_BLOOM, SoundSource.HOSTILE, 2.0F, 0.8F + w * 0.02F);
            }
            if (w >= 24) {
                bloomTick = -1;
                bloomTimer = Math.max(120, (int) Math.round(BLOOM_EVERY * cooldownScale()));
                return;
            }
        }
        bloomTick++;
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0 || hidden) {
            if (!hidden) {
                level.sendParticles(SPORE, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
                level.playSound(null, this, SoundEvents.FUNGUS_BREAK, SoundSource.HOSTILE, 0.6F, 1.6F);
            }
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        bloomTick = -1;
        clearPods(level);
        discardAdds(level);
        if (hidden) {
            hide(false);
        }
    }

    /** Back to the first phase (the fight was reset): base speed, no communion. */
    private void resetForm(ServerLevel level) {
        communion = false;
        roarUntil = -1;
        guard = 0;
        burrowTimer = 100;
        bloomTimer = 60;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("mycelium_abbot_communion"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("mycelium_abbot_wrath"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!stalePods.isEmpty()) {                        // saved by an unload: cleared on the first tick
            clearPods(level);
        }
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        if (hidden && (cur == null || !"burrow".equals(cur.name))) {
            hide(false);                                   // never stay underground outside the burrow (stagger, reset)
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!pods.isEmpty() || bloomTick >= 0)) {
            bloomTick = -1;                                // the arena emptied (death, flight)
            clearPods(level);
        }
        if (!pods.isEmpty()) {
            tickPods(level);
        }
        if (phase() == 1 && communion) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !communion && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "communion");
            free = false;
        }
        // phase 3: he burrows under the players, fairy rings bloom out from the centre
        if (communion && phase() == 2 && anyone) {
            cur = currentAttack();
            boolean busy = cur != null && ("communion".equals(cur.name) || "burrow".equals(cur.name));
            if (bloomTick >= 0) {
                tickBloom(level);
            } else if (fighting && !busy && guard == 0 && --bloomTimer <= 0) {
                bloomTick = 0;
            }
            if (burrowTimer > 0) {
                burrowTimer--;
            }
            if (free && guard == 0 && bloomTick < 0 && burrowTimer <= 0 && currentAttack() == null) {
                burrowTimer = Math.max(150, (int) Math.round(BURROW_EVERY * cooldownScale()));
                chain(level, "burrow");
            }
            if (tickCount % 4 == 0) {                       // spores drifting down from the gills of the dome
                Vec3 c = centre();
                double r = floorR() - 1.0;
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, x, c.y + 6 + getRandom().nextDouble() * 8, z, 1, 0.3, 0.3, 0.3, 0);
            }
        }
        // ambience: steam from the reliquary's chimney, spore-light from the censer
        if (!hidden && tickCount % 8 == 0) {
            Vec3 back = position().add(forward().scale(-0.5));
            level.sendParticles(ParticleTypes.WHITE_SMOKE, back.x, getY() + 3.4, back.z, 1, 0.05, 0.05, 0.05, 0.01);
            Vec3 cr = crook();
            level.sendParticles(CYAN, cr.x, cr.y, cr.z, 1, 0.15, 0.15, 0.15, 0);
        }
        if (!hidden && tickCount % 60 == 0) {
            level.playSound(null, this, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 0.6F, 0.7F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("mycelium_abbot_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        sporeBurst(level, position().add(0, 3.0, 0), 30, 1.5);
        level.sendParticles(ParticleTypes.MYCELIUM, getX(), getY() + 0.2, getZ(), 40, 2.0, 0.2, 2.0, 0.05);
        level.playSound(null, this, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        sporeBurst(level, position().add(0, 2.5, 0), 50, 1.5);
        level.sendParticles(ParticleTypes.MYCELIUM, getX(), getY() + 0.5, getZ(), 50, 1.5, 0.5, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.4F);
        level.playSound(null, this, SoundEvents.FUNGUS_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            clearPods(level);
            discardAdds(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("AbbotCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("AbbotRadius", radius);
        output.putBoolean("AbbotCommunion", communion);
        List<SavedPod> saved = new ArrayList<>(stalePods);
        for (Pod p : pods) {
            saved.add(new SavedPod(p.pos.asLong()));
        }
        output.store("MyceliumAbbotPods", SavedPod.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("AbbotCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("AbbotRadius", 16);
        floorTol = -1;
        communion = input.getBooleanOr("AbbotCommunion", false) && phase() == 2;
        stalePods.clear();
        input.read("MyceliumAbbotPods", SavedPod.CODEC.listOf()).ifPresent(stalePods::addAll);
        pods.clear();
        bloomTick = -1;
        hidden = false;
        setInvisible(false);
    }
}
