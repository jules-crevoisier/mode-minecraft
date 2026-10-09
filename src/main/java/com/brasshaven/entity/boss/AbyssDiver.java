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
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.AbyssDiver.CALL;
import static com.brasshaven.generated.MobAnims.AbyssDiver.GRIND;
import static com.brasshaven.generated.MobAnims.AbyssDiver.GROAN;
import static com.brasshaven.generated.MobAnims.AbyssDiver.HARPOON;
import static com.brasshaven.generated.MobAnims.AbyssDiver.OVERCHARGE;
import static com.brasshaven.generated.MobAnims.AbyssDiver.RIVETS;
import static com.brasshaven.generated.MobAnims.AbyssDiver.ROAR;
import static com.brasshaven.generated.MobAnims.AbyssDiver.SILT;
import static com.brasshaven.generated.MobAnims.AbyssDiver.SLAM;
import static com.brasshaven.generated.MobAnims.AbyssDiver.STAGGER;
import static com.brasshaven.generated.MobAnims.AbyssDiver.THRUST;

/**
 * Le Scaphandrier des abysses (The Abyssal Diver), the champion of the Abyssal Station: the station's chief diver fused
 * with his armoured suit (3.8 blocks), a brass hard-hat with a glowing teal porthole, pressure tanks on his back, a giant
 * drill for a right arm and a rivet-and-harpoon gun in his left, lead boots, barnacles and kelp. He waits in the drill
 * chamber at the bottom of the trench (34 wide, under the brass skylight dome, the drill string hanging over the
 * borehole in its middle): an air pocket sealed from the sea.
 * <ul>
 *     <li>Phase 1: the drill <b>thrust</b> down a drawn lane, the drill <b>grind</b> (a drawn arc, three hits), the
 *     <b>rivets</b> (three volleys along drawn lines), the pressure <b>slam</b> (a drawn ring, then a wave to jump) and
 *     the <b>harpoon</b> (a drawn line: it hauls you toward him).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>silt</b> cloud (a drawn ring: blinds briefly) and the <b>call</b>
 *     (drowned and drowned marines); the grind chains into the slam or the rivets, the harpoon into the grind.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the hull <b>groans</b> (a wave, jump it);
 *     pressure spikes then burst on marked circles, bioluminescent jellies drift toward the players and burst when
 *     touched, and every ~18 s he <b>overcharges</b> his suit: faster and harder-hitting for 7 s, but he takes more.</li>
 * </ul>
 * He places and breaks no blocks at all (the chamber is an air pocket under the sea): every hazard is particles and
 * damage. Pushes are capped and never thrown off the open floor (into the wall, the struts, the spoil heaps).
 */
public class AbyssDiver extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 3.8F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double THRUST_MAX = 8.0;
    private static final double THRUST_HALF = 1.0;
    private static final double THRUST_TIP = 2.5;
    private static final double GRIND_R = 4.5;
    private static final double GRIND_HALF = 40;
    private static final double RIVET_MAX = 22.0;
    private static final double SLAM_R = 5.0;
    private static final double HARPOON_MAX = 18.0;
    private static final double SILT_R = 4.5;
    private static final double SPIKE_R = 2.0;
    private static final double JELLY_R = 2.0;
    private static final double SURGE_R = 3.5;
    private static final int SPIKE_EVERY = 70;
    private static final int JELLY_EVERY = 100;
    private static final int SURGE_EVERY = 360;
    private static final int OVERCHARGE_TICKS = 140;
    private static final DustParticleOptions AQUA = new DustParticleOptions(0x50FFD6, 1.4F);
    private static final DustParticleOptions DEEP = new DustParticleOptions(0x1E8C8C, 1.8F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xE0B050, 1.2F);
    private static final DustParticleOptions SILT_DUST = new DustParticleOptions(0x2A2420, 2.4F);
    private static final DustParticleOptions SPARK = new DustParticleOptions(0xFFF07A, 1.0F);
    private static final DustParticleOptions JELLY = new DustParticleOptions(0x7CFFE8, 1.7F);
    private static final DustParticleOptions JELLY_PINK = new DustParticleOptions(0xE070FF, 1.2F);
    private static final net.minecraft.resources.Identifier OVERCHARGE_ID = com.brasshaven.Brasshaven.id("abyss_diver_overcharge");

    /** A drifting bioluminescent jelly (particles only): where it is, how long it lived, its fuse once touched. */
    private static final class Jelly {
        Vec3 pos;
        int age;
        int fuse = -1;

        Jelly(Vec3 pos) {
            this.pos = pos;
        }
    }

    private @Nullable Vec3 centre;
    private int radius = 18;
    /** The drill chamber's middle (the borehole) and how far its open floor runs; found on the first tick. */
    private @Nullable Vec3 hub;
    private double openR = 14.5;
    /** Phase 3 has started (the hull groans). */
    private boolean groaning;
    private int guard;
    private int roarUntil = -1;
    private int spikeTimer = 50;
    private int jellyTimer = 40;
    private int surgeTimer = 160;
    private int overchargeUntil = -1;
    // moves in flight
    private double thrustLen = 6.0;
    private Vec3 thrustFrom = Vec3.ZERO;
    private Vec3 thrustTo = Vec3.ZERO;
    private final List<Vec3> rivetDirs = new ArrayList<>();
    private final List<Double> rivetLens = new ArrayList<>();
    private double harpoonLen = 10.0;
    private boolean harpooned;
    private final List<Jelly> jellies = new ArrayList<>();
    private final Set<UUID> adds = new HashSet<>();

    public AbyssDiver(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 660.0)
                .add(Attributes.ARMOR, 13.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.AbyssDiver.TICKS;
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
        return 4.0;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    /** His own silt does not blind him, and the deep does not drown him. */
    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        if (effect.is(MobEffects.BLINDNESS) || effect.is(MobEffects.DARKNESS)) {
            return false;
        }
        return super.canBeAffected(effect);
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    // ------------------------------------------------------------------ arena memory (the drill chamber)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.hub = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /**
     * The borehole: the shroomlight cells glowing in the floor layer round the seal (their centroid is the chamber's
     * middle; the open floor then runs to 14.5 from it, short of the struts' feet and the spoil heaps at the wall).
     * Without at least 4 of them (a summoned fight) the seal's spot is the middle and the floor runs to radius - 3.
     */
    private Vec3 hub(ServerLevel level) {
        if (hub != null) {
            return hub;
        }
        Vec3 c = centre();
        int y = Mth.floor(c.y) - 1;
        int r = radius + 2;
        double sx = 0;
        double sz = 0;
        int n = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                p.set(Mth.floor(c.x) + dx, y, Mth.floor(c.z) + dz);
                if (level.isLoaded(p) && level.getBlockState(p).is(Blocks.SHROOMLIGHT)) {
                    sx += p.getX() + 0.5;
                    sz += p.getZ() + 0.5;
                    n++;
                }
            }
        }
        if (n >= 4) {
            hub = new Vec3(sx / n, c.y, sz / n);
            openR = 14.5;
        } else {
            hub = c;
            openR = Math.max(6.0, radius - 3.0);
        }
        return hub;
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

    /**
     * A spot of open floor at (x, z): the floor within 0.6 of the seal's level, two blocks of air over it, and within
     * the open radius of the chamber's middle; or null.
     */
    private @Nullable Vec3 floor(ServerLevel level, double x, double z) {
        Vec3 h = hub(level);
        if (Math.hypot(x - h.x, z - h.z) > openR) {
            return null;
        }
        Vec3 c = centre();
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
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(hub(level))).inflate(openR + 6, 14, openR + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** Height of {@code e}'s feet over the floor under it (0 standing, more when jumping). */
    private static double overFloor(ServerLevel level, LivingEntity e) {
        double fy = floorY(level, e.getX(), e.getY(), e.getZ());
        return Double.isNaN(fy) ? 9.0 : e.getY() - fy;
    }

    /** The push is dropped where it would carry {@code e} off the open floor (into the wall, a strut, a heap). */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 dir = push.multiply(1, 0, 1).normalize();
        for (double d : new double[] {1.5, 3.0}) {
            Vec3 probe = e.position().add(dir.scale(d));
            if (floor(level, probe.x, probe.z) == null) {
                return Vec3.ZERO;
            }
        }
        return new Vec3(push.x, 0, push.z);
    }

    private boolean overcharged() {
        return tickCount < overchargeUntil;
    }

    /** Pushes capped at 1.0, lift at 0.45 (0.2 when no open floor lies 3 blocks beyond); none off the floor. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.0, knockback));
        }
        shove(level, e, damage, push, lift);
    }

    private boolean shove(ServerLevel level, LivingEntity e, float damage, Vec3 push, double lift) {
        float dmg = overcharged() ? damage * 1.15F : damage;
        if (!e.hurtServer(level, damageSources().mobAttack(this), dmg)) {
            return false;
        }
        Vec3 safe = safePush(level, e, push);
        lift = Math.min(lift, safe.lengthSqr() < push.lengthSqr() - 1.0E-6 ? 0.2 : 0.45);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
        return true;
    }

    /** The muzzle of the rivet gun in his left hand. */
    private Vec3 muzzle() {
        Vec3 f = forward();
        Vec3 left = new Vec3(-f.z, 0, f.x);
        return position().add(left.scale(0.9)).add(f.scale(1.6)).add(0, 2.0, 0);
    }

    /** The tip of the drill on his right arm, held forward. */
    private Vec3 drillTip() {
        Vec3 f = forward();
        Vec3 right = new Vec3(f.z, 0, -f.x);
        return position().add(right.scale(0.9)).add(f.scale(2.4)).add(0, 1.8, 0);
    }

    private Vec3 porthole() {
        return position().add(forward().scale(0.6)).add(0, 3.2, 0);
    }

    private void sparks(ServerLevel level, Vec3 at, int n) {
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, n, 0.3, 0.3, 0.3, 0.2);
        level.sendParticles(SPARK, at.x, at.y, at.z, n / 2 + 1, 0.4, 0.3, 0.4, 0);
    }

    private void steam(ServerLevel level, Vec3 at, int n, double spread) {
        level.sendParticles(ParticleTypes.CLOUD, at.x, at.y, at.z, n, spread, 0.3, spread, 0.03);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // thrust: the drill drawn back and spun up, a crouch (1.1 s; the lane drawn aqua follows you slowly, then locks
        // red 0.4 s before); he lunges down it in 0.2 s, the drill at full reach: 14 to everyone in the lane and 2.5
        // blocks past its end, a push
        out.add(BossAttack.of("thrust").anim(THRUST).timing(22, 12, 16).range(4.0, 12.0).cooldown(100).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    thrustLen = lineLength(level, THRUST_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 14) {
                        turnToward(t, 4.0F);
                        thrustLen = lineLength(level, THRUST_MAX);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), thrustLen + THRUST_TIP, THRUST_HALF, tick < 14 ? AQUA : RED);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.2F, 0.5F + tick * 0.03F);
                    }
                    sparks(level, drillTip(), 1);
                })
                .impact((b, level, t, tick) -> {
                    thrustFrom = position();
                    thrustTo = position().add(forward().scale(Math.max(0.0, thrustLen - 1.0)));
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 5) {
                        Vec3 step = thrustTo.subtract(position()).multiply(1, 0, 1).scale(1.0 / (5 - tick));
                        move(MoverType.SELF, step);
                        setDeltaMovement(0, getDeltaMovement().y, 0);
                        steam(level, position().add(0, 0.3, 0), 3, 0.4);
                    }
                    if (tick == 4) {
                        thrustHit(level);
                    }
                })
                .build());
        // grind: the drill raised level and howling up to speed (0.8 s; the arc drawn aqua, following you slowly, red
        // for the last 0.3 s), then held out grinding for 1.5 s: 5 at 0.8, 1.3 and 1.8 s to whoever stays in the arc
        out.add(BossAttack.of("grind").anim(GRIND).timing(16, 30, 14).range(0, 5.5).cooldown(60).weight(11)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 3.0F);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, GRIND_R, GRIND_HALF, tick < 10 ? AQUA : RED);
                        b.telegraphArc(level, GRIND_R - 2.0, GRIND_HALF, tick < 10 ? AQUA : RED);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                    sparks(level, drillTip(), 1);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 30) {
                        sparks(level, drillTip(), 3);
                        if (tick % 3 == 0) {
                            b.telegraphArc(level, GRIND_R, GRIND_HALF, RED);
                        }
                        if (tick % 4 == 0) {
                            level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.8F);
                        }
                        if (tick % 10 == 0) {
                            grindHit(level);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "slam" : "rivets");
                    }
                })
                .build());
        // rivets: the rivet gun levelled (1.0 s; 3 lines, phase 2 five, 9° apart, drawn aqua and following you, red for
        // the last 0.4 s), then three volleys along the same lines at 1.0, 1.5 and 2.0 s: 5 and a small push per rivet
        out.add(BossAttack.of("rivets").anim(RIVETS).timing(20, 24, 14).range(5.0, 24.0).cooldown(90).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planRivets(level);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12) {
                        turnToward(t, 4.0F);
                        planRivets(level);
                    }
                    if (tick % 2 == 0) {
                        Vec3 m = muzzle();
                        for (int i = 0; i < rivetDirs.size(); i++) {
                            drawRay(level, new Vec3(m.x, getY(), m.z), rivetDirs.get(i), rivetLens.get(i), tick < 12 ? AQUA : RED);
                        }
                    }
                    if (tick == 4 || tick == 12) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 10 == 0 && tick <= 20) {
                        Vec3 m = muzzle();
                        for (int i = 0; i < rivetDirs.size(); i++) {
                            b.addEffect(rivet(m, rivetDirs.get(i), rivetLens.get(i)));
                        }
                        level.sendParticles(ParticleTypes.SMOKE, m.x, m.y, m.z, 8, 0.15, 0.15, 0.15, 0.03);
                        level.playSound(null, b, SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 1.6F, 0.6F);
                        level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.5F, 1.8F);
                    }
                })
                .build());
        // slam: both arms heaved overhead, the suit swelling (1.2 s; a ring r 5 drawn aqua round him, red for the last
        // 0.4 s); he comes down on the floor: 12 within the ring and a lift, then a pressure wave runs on to 11 (6, jump)
        out.add(BossAttack.of("slam").anim(SLAM).timing(24, 12, 16).range(0, 8.0).cooldown(120).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), SLAM_R, tick < 16 ? AQUA : RED);
                    }
                    if (tick % 6 == 0) {
                        steam(level, b.position().add(0, 2.5, 0), 4, 0.6);
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_STEP, SoundSource.HOSTILE, 1.4F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : victims(level, position(), SLAM_R + 1)) {
                        if (flatDist(e.position(), position()) <= SLAM_R + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 2.5) {
                            strike(level, e, 12.0F, 0.6, 0.4);
                        }
                    }
                    b.addEffect(floorWave(position(), SLAM_R, 11.0, 0.5, 6.0F, AQUA));
                    level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.3, getZ(), 3, 1.5, 0.2, 1.5, 0);
                    level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.3, getZ(), 60, 2.5, 0.2, 2.5, 0.3);
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.DEEPSLATE.defaultBlockState()), getX(),
                            getY() + 0.2, getZ(), 40, 2.0, 0.2, 2.0, 0.1);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.2F, 0.6F);
                })
                .build());
        // harpoon: the gun levelled at you (1.0 s; a line drawn aqua, following you until 0.6 s, then red); the harpoon
        // flies 2 blocks a tick (walls stop it): the first one it bites takes 6 and is hauled up to 7 blocks toward
        // him, never closer than 3
        out.add(BossAttack.of("harpoon").anim(HARPOON).timing(20, 14, 14).range(6.0, HARPOON_MAX).cooldown(160).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    harpooned = false;
                    if (t != null) {
                        faceToward(t.position());
                    }
                    harpoonLen = clipLen(level, muzzle(), forward(), HARPOON_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12) {
                        turnToward(t, 5.0F);
                        harpoonLen = clipLen(level, muzzle(), forward(), HARPOON_MAX);
                    }
                    if (tick % 2 == 0) {
                        Vec3 m = muzzle();
                        drawRay(level, new Vec3(m.x, getY(), m.z), forward(), harpoonLen, tick < 12 ? AQUA : RED);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_START.value(), SoundSource.HOSTILE, 1.2F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(harpoonFlight(muzzle(), forward(), harpoonLen));
                    level.playSound(null, b, SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 2.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && harpooned && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "grind");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // silt: he hunches over his valves, the tanks swelling (0.9 s; a ring r 4.5 drawn dark round him, red for the
        // last 0.3 s); silt bursts out of the suit: 4, a push and Blindness 2 s within the ring, and the cloud lingers
        // there 4 s (Blindness 1.5 s to whoever walks in)
        out.add(BossAttack.of("silt").anim(SILT).phaseTwo().timing(18, 10, 14).range(0, 14.0).cooldown(220).weight(6)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), SILT_R, tick < 12 ? SILT_DUST : RED);
                    }
                    level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY() + 2.5, getZ(), 2, 0.6, 0.4, 0.6, 0.01);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_INSIDE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 at = position();
                    for (LivingEntity e : victims(level, at, SILT_R + 1)) {
                        if (flatDist(e.position(), at) <= SILT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                            strike(level, e, 4.0F, 0.7, 0.2);
                            e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0));
                        }
                    }
                    level.sendParticles(ParticleTypes.SQUID_INK, at.x, at.y + 1.5, at.z, 80, 2.5, 1.0, 2.5, 0.05);
                    level.sendParticles(SILT_DUST, at.x, at.y + 1.0, at.z, 60, 3.0, 0.8, 3.0, 0);
                    level.playSound(null, b, SoundEvents.SQUID_SQUIRT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.5F);
                    b.addEffect(siltCloud(at));
                })
                .build());
        // call: he bangs the drill housing on his helmet three times (1.0 s), the signal to his drowned crew: drowned
        // marines and drowned climb out of the borehole's mist (2, more in co-op), never more than 3 of them at once
        out.add(BossAttack.of("call").anim(CALL).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick == 6 || tick == 12 || tick == 18) {
                        level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 1.4F);
                        sparks(level, porthole(), 4);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    spawnAdds(level, 2);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // groan: the drill raised high, howling (2.0 s, guarded; aqua rings gather round him, the dome creaks and drips);
        // he drives it into the floor: the hull groans and a pressure wave runs to 14 (10, jump it); the spikes start
        out.add(BossAttack.of("groan").anim(GROAN).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, AQUA);
                    }
                    drips(level, 4);
                    sparks(level, drillTip().add(0, 2.0, 0), 2);
                    if (tick % 10 == 0) {
                        hullCreak(level, 0.5F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> groan(level))
                .build());
        // overcharge: he stands tall, arms spread, the tanks swelling and the porthole blazing (1.5 s; a ring r 3.5 drawn
        // yellow round him, red for the last 0.5 s); the overload bursts out: 8 and a push within the ring, then for 7 s
        // he is 20% faster and hits 15% harder, but takes 15% more (sparks crackle over him)
        out.add(BossAttack.of("overcharge").anim(OVERCHARGE).phaseTwo().timing(30, 10, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), SURGE_R, tick < 20 ? SPARK : RED);
                    }
                    sparks(level, b.position().add(0, 2.0 + getRandom().nextDouble() * 1.5, 0), 2);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 1.5F, 1.2F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> surge(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** The thrust: everyone within the lane from where he sprang to 2.5 blocks past where he stands. */
    private void thrustHit(ServerLevel level) {
        Vec3 dir = forward();
        double len = flatDist(thrustFrom, position()) + THRUST_TIP;
        for (LivingEntity e : victims(level, position(), len + 2)) {
            Vec3 to = e.position().subtract(thrustFrom).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            if (along >= -0.5 && along <= len && side <= THRUST_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 14.0F, 0.6, 0.2);
            }
        }
        Vec3 tip = ahead(2.5);
        sparks(level, tip.add(0, 1.4, 0), 14);
        level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 1.4, tip.z, 14, 0.5, 0.3, 0.5, 0.2);
        level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.0F, 0.6F);
        level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /** One bite of the grinding drill: 5 to everyone in the arc. */
    private void grindHit(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(GRIND_HALF));
        for (LivingEntity e : victims(level, position(), GRIND_R + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= GRIND_R + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos) && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 5.0F, 0.0, 0.0);
                sparks(level, e.position().add(0, 1.0, 0), 4);
            }
        }
        level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.6F, 1.5F);
    }

    /** How far a line along his facing runs over open floor. */
    private double lineLength(ServerLevel level, double max) {
        double len = 2.0;
        for (double d = 1.0; d <= max; d += 1.0) {
            Vec3 p = ahead(d);
            if (floor(level, p.x, p.z) == null) {
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

    /** A thin line on the floor (a rivet's or the harpoon's flight). */
    private void drawRay(ServerLevel level, Vec3 from, Vec3 dir, double len, DustParticleOptions dust) {
        for (double d = 1.0; d <= len; d += 0.8) {
            Vec3 p = from.add(dir.scale(d));
            level.sendParticles(dust, p.x, from.y + 0.15, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** How far a flight from {@code from} along the flat {@code dir} runs before a wall, up to {@code max}. */
    private double clipLen(ServerLevel level, Vec3 from, Vec3 dir, double max) {
        BlockHitResult hit = level.clip(new ClipContext(from, from.add(dir.scale(max)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? max : Math.max(1.0, hit.getLocation().distanceTo(from) - 0.2);
    }

    /** The rivet lines: 3 (phase 2: 5), 9° apart round his facing, each to the first wall. */
    private void planRivets(ServerLevel level) {
        rivetDirs.clear();
        rivetLens.clear();
        int n = phase() == 2 ? 5 : 3;
        Vec3 m = muzzle();
        for (int i = 0; i < n; i++) {
            Vec3 dir = rotate(forward(), (i - (n - 1) / 2.0) * 9.0);
            rivetDirs.add(dir);
            rivetLens.add(clipLen(level, m, dir, RIVET_MAX));
        }
    }

    /** One rivet flying 2 blocks a tick along its line: the first creature within 0.7 of it takes 5. */
    private Effect rivet(Vec3 from, Vec3 dir, double len) {
        double[] d = {0.0};
        return (boss, level) -> {
            if (!(boss instanceof AbyssDiver a)) {
                return true;
            }
            double d0 = d[0];
            double d1 = Math.min(len, d0 + 2.0);
            d[0] = d1;
            for (double s = d0; s <= d1; s += 0.5) {
                Vec3 p = from.add(dir.scale(s));
                level.sendParticles(BRASS, p.x, p.y, p.z, 1, 0, 0, 0, 0);
                for (LivingEntity e : boss.victims(level, p, 1.5)) {
                    if (e.getBoundingBox().inflate(0.4).contains(p) || e.getBoundingBox().inflate(0.7, 0.2, 0.7).contains(p)) {
                        a.shove(level, e, 5.0F, dir.scale(0.3), 0.05);
                        level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 6, 0.2, 0.2, 0.2, 0.1);
                        return true;
                    }
                }
            }
            if (d1 >= len) {
                Vec3 p = from.add(dir.scale(len));
                level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 4, 0.1, 0.1, 0.1, 0.1);
                return true;
            }
            return false;
        };
    }

    /** The harpoon: 2 blocks a tick; on the first creature it bites, 6 and a haul toward him (up to 7, stops 3 short). */
    private Effect harpoonFlight(Vec3 from, Vec3 dir, double len) {
        double[] d = {0.0};
        return (boss, level) -> {
            if (!(boss instanceof AbyssDiver a)) {
                return true;
            }
            double d0 = d[0];
            double d1 = Math.min(len, d0 + 2.0);
            d[0] = d1;
            Vec3 m = a.muzzle();
            Vec3 head = from.add(dir.scale(d1));
            for (double s = 0.5; s <= d1; s += 0.6) {
                Vec3 p = from.add(dir.scale(s));
                level.sendParticles(BRASS, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
            level.sendParticles(ParticleTypes.CRIT, head.x, head.y, head.z, 2, 0.05, 0.05, 0.05, 0);
            for (double s = d0; s <= d1; s += 0.5) {
                Vec3 p = from.add(dir.scale(s));
                for (LivingEntity e : boss.victims(level, p, 1.5)) {
                    if (e.getBoundingBox().inflate(0.5).contains(p)) {
                        if (a.shove(level, e, 6.0F, Vec3.ZERO, 0.0)) {
                            a.haul(level, e);
                        }
                        level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 10, 0.3, 0.3, 0.3, 0.2);
                        level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 1.5F, 0.7F);
                        return true;
                    }
                }
            }
            if (d1 >= len) {
                level.playSound(null, head.x, head.y, head.z, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.0F, 0.8F);
                return true;
            }
            return false;
        };
    }

    /** Hauls {@code e} toward him: up to 7 blocks, never closer than 3, with a little lift. */
    private void haul(ServerLevel level, LivingEntity e) {
        Vec3 to = position().subtract(e.position()).multiply(1, 0, 1);
        double dist = to.length();
        double travel = Mth.clamp(dist - 3.0, 0.0, 7.0);
        if (travel < 0.5) {
            return;
        }
        Vec3 v = to.normalize().scale(Math.min(1.2, travel / 6.0));
        e.setDeltaMovement(v.x, 0.3, v.z);
        e.hurtMarked = true;
        harpooned = true;
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.2F, 0.6F);
    }

    /** A jumpable ring from {@code c} running from {@code from} to {@code max}: it hits once whoever stands at its edge. */
    private Effect floorWave(Vec3 c, double from, double max, double speed, float damage, DustParticleOptions dust) {
        double[] r = {from};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof AbyssDiver a)) {
                return true;
            }
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double ang = Math.PI * 2 * i / n;
                double x = c.x + Math.cos(ang) * rr;
                double z = c.z + Math.sin(ang) * rr;
                level.sendParticles(dust, x, c.y + 0.2, z, 1, 0, 0.05, 0, 0);
                if (i % 4 == 0) {
                    level.sendParticles(ParticleTypes.SPLASH, x, c.y + 0.3, z, 1, 0.1, 0, 0.1, 0);
                }
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && overFloor(level, e) < 0.6 && hit.add(e.getUUID())) {
                    a.strike(level, e, damage, 0.6, 0.35);
                }
            }
            return rr >= max;
        };
    }

    /** The lingering silt where he burst: 80 ticks, its edge drawn; whoever is in it is blinded 1.5 s. */
    private Effect siltCloud(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k % 2 == 0) {
                level.sendParticles(SILT_DUST, at.x, at.y + 1.0, at.z, 8, SILT_R * 0.6, 0.8, SILT_R * 0.6, 0);
                level.sendParticles(ParticleTypes.SQUID_INK, at.x, at.y + 1.2, at.z, 2, SILT_R * 0.5, 0.6, SILT_R * 0.5, 0.005);
            }
            if (k % 8 == 0) {
                boss.telegraphRing(level, at, SILT_R, SILT_DUST);
            }
            if (k % 10 == 0) {
                for (LivingEntity e : boss.victims(level, at, SILT_R + 1)) {
                    if (flatDist(e.position(), at) <= SILT_R && Math.abs(e.getY() - at.y) < 3.0) {
                        MobEffectInstance b = e.getEffect(MobEffects.BLINDNESS);
                        if (b == null || b.getDuration() < 15) {
                            e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0));
                        }
                    }
                }
            }
            return k >= 80;
        };
    }

    // ---- the drowned crew

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
            EntityType<? extends Mob> type = i % 2 == 0 ? ModEntities.DROWNED_MARINE.get() : net.minecraft.world.entity.EntityTypes.DROWNED;
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                at = floor(level, getX() + Math.cos(a) * 3.5, getZ() + Math.sin(a) * 3.5);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.5, at.z, 30, 0.4, 0.5, 0.4, 0.2);
            steam(level, at.add(0, 0.5, 0), 6, 0.4);
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

    // ------------------------------------------------------------------ phase 3: the hull groans

    private void hullCreak(ServerLevel level, float pitch) {
        Vec3 h = hub(level);
        level.playSound(null, h.x, h.y + 10, h.z, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.2F, pitch * 0.5F);
        level.playSound(null, h.x, h.y + 10, h.z, SoundEvents.IRON_DOOR_CLOSE, SoundSource.HOSTILE, 1.5F, pitch * 0.4F);
    }

    /** Water seeping from the dome (particles only: nothing is opened, nothing is placed). */
    private void drips(ServerLevel level, int n) {
        Vec3 h = hub(level);
        for (int i = 0; i < n; i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = getRandom().nextDouble() * openR;
            level.sendParticles(ParticleTypes.FALLING_WATER, h.x + Math.cos(a) * d, h.y + 10 + getRandom().nextDouble() * 5,
                    h.z + Math.sin(a) * d, 1, 0, 0, 0, 0);
        }
    }

    private void groan(ServerLevel level) {
        groaning = true;
        spikeTimer = 50;
        jellyTimer = 30;
        surgeTimer = 160;
        addEffect(floorWave(position(), 0.5, 14.0, 0.55, 10.0F, AQUA));
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.3, getZ(), 4, 1.5, 0.2, 1.5, 0);
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.3, getZ(), 80, 3.0, 0.2, 3.0, 0.3);
        sparks(level, drillTip(), 20);
        drips(level, 40);
        hullCreak(level, 0.6F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /** The overload: a burst round him and 7 s of overcharge. */
    private void surge(ServerLevel level) {
        for (LivingEntity e : victims(level, position(), SURGE_R + 1)) {
            if (flatDist(e.position(), position()) <= SURGE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 8.0F, 0.8, 0.3);
            }
        }
        overchargeUntil = tickCount + OVERCHARGE_TICKS;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(OVERCHARGE_ID);
            speed.addTransientModifier(new AttributeModifier(OVERCHARGE_ID, 0.2, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        sparks(level, position().add(0, 2.0, 0), 30);
        steam(level, position().add(0, 2.0, 0), 20, 1.0);
        level.playSound(null, this, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.0F, 1.6F);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 0.8F, 1.6F);
    }

    private void endOvercharge(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null && speed.getModifier(OVERCHARGE_ID) != null) {
            speed.removeModifier(OVERCHARGE_ID);
            steam(level, position().add(0, 2.5, 0), 16, 0.8);
            level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
        overchargeUntil = -1;
    }

    /**
     * A volley of pressure spikes: one under the target, one under each of up to 2 other players, the rest on random
     * open floor; {@code min(5, scaledCount(2) + 1)} in all.
     */
    private void castSpikes(ServerLevel level, @Nullable LivingEntity target) {
        int n = Math.min(5, scaledCount(2) + 1);
        List<Vec3> marks = new ArrayList<>();
        if (target != null) {
            addMark(level, marks, target.getX(), target.getZ());
        }
        int extra = 0;
        for (Player p : fighters(level)) {
            if (p != target && extra++ < 2) {
                addMark(level, marks, p.getX(), p.getZ());
            }
        }
        Vec3 h = hub(level);
        for (int tries = 0; tries < 30 && marks.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = getRandom().nextDouble() * (openR - 2.0);
            addMark(level, marks, h.x + Math.cos(a) * d, h.z + Math.sin(a) * d);
        }
        for (Vec3 m : marks) {
            addEffect(spike(m));
        }
        hullCreak(level, 0.7F + getRandom().nextFloat() * 0.3F);
    }

    private void addMark(ServerLevel level, List<Vec3> marks, double x, double z) {
        Vec3 s = floor(level, x, z);
        if (s == null) {
            return;
        }
        for (Vec3 o : marks) {
            if (flatDist(o, s) < 3.0) {
                return;
            }
        }
        marks.add(s);
    }

    /** A pressure spike: its ring drawn aqua 30 ticks (red the last 10), then it bursts: 8 and a lift. */
    private Effect spike(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    DustParticleOptions d = k >= 20 ? RED : AQUA;
                    boss.telegraphRing(level, at, SPIKE_R, d);
                    boss.telegraphRing(level, at, SPIKE_R * 0.45, d);
                }
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.2, at.z, 2 + k / 6, 0.6, 0, 0.6, 0.05);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.CLOUD, at.x, at.y + 0.5, at.z, 20, 0.5, 1.2, 0.5, 0.08);
            level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.5, at.z, 40, 0.8, 0.8, 0.8, 0.3);
            level.sendParticles(DEEP, at.x, at.y + 1.0, at.z, 20, 0.6, 1.5, 0.6, 0);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.8F, 1.5F);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.BUBBLE_COLUMN_UPWARDS_INSIDE, SoundSource.HOSTILE, 2.0F, 0.6F);
            if (boss instanceof AbyssDiver a) {
                for (LivingEntity e : boss.victims(level, at, SPIKE_R + 1)) {
                    if (flatDist(e.position(), at) <= SPIKE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        a.strike(level, e, 8.0F, 0.0, 0.5);
                    }
                }
            }
            return true;
        };
    }

    /** A new jelly on open floor, at least 6 from every player, drifting at chest height. */
    private void spawnJelly(ServerLevel level) {
        Vec3 h = hub(level);
        List<Player> ps = fighters(level);
        for (int tries = 0; tries < 20; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = openR * (0.5 + getRandom().nextDouble() * 0.45);
            Vec3 s = floor(level, h.x + Math.cos(a) * d, h.z + Math.sin(a) * d);
            if (s == null) {
                continue;
            }
            boolean ok = true;
            for (Player p : ps) {
                if (flatDist(p.position(), s) < 6.0) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                jellies.add(new Jelly(s.add(0, 1.3, 0)));
                level.sendParticles(JELLY, s.x, s.y + 1.3, s.z, 20, 0.4, 0.4, 0.4, 0);
                level.playSound(null, s.x, s.y, s.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 0.6F);
                return;
            }
        }
    }

    /**
     * The jellies drift 0.05 a tick toward the nearest player (a floor ring under each shows where it is); a player
     * within 1.4 (and 1.6 in height) lights its fuse: 12 ticks, its ring red, then it bursts: 7, a push and Slowness I
     * 1 s within 2. Each fades harmlessly after 20 s.
     */
    private void tickJellies(ServerLevel level) {
        if (jellies.isEmpty()) {
            return;
        }
        List<Player> ps = fighters(level);
        Vec3 c = centre();
        for (Jelly j : new ArrayList<>(jellies)) {
            j.age++;
            Vec3 floorAt = new Vec3(j.pos.x, c.y, j.pos.z);
            if (j.fuse < 0) {
                Player near = null;
                double best = Double.MAX_VALUE;
                for (Player p : ps) {
                    double d = p.position().distanceToSqr(j.pos);
                    if (d < best) {
                        best = d;
                        near = p;
                    }
                }
                if (near != null) {
                    Vec3 to = near.position().subtract(j.pos).multiply(1, 0, 1);
                    if (to.lengthSqr() > 1.0E-4) {
                        Vec3 step = to.normalize().scale(0.05);
                        if (floor(level, j.pos.x + step.x * 10, j.pos.z + step.z * 10) != null) {
                            j.pos = j.pos.add(step);
                        }
                    }
                    double bob = Math.sin(j.age * 0.12) * 0.15;
                    double wantY = Mth.clamp(near.getY() + 1.0, c.y + 0.8, c.y + 2.2) + bob;
                    j.pos = new Vec3(j.pos.x, j.pos.y + Mth.clamp(wantY - j.pos.y, -0.04, 0.04), j.pos.z);
                    if (flatDist(near.position(), j.pos) <= 1.4 && Math.abs(near.getY() + 0.9 - j.pos.y) < 1.6) {
                        j.fuse = 12;
                        level.playSound(null, j.pos.x, j.pos.y, j.pos.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 1.5F, 1.4F);
                    }
                }
            } else if (--j.fuse <= 0) {
                burstJelly(level, j);
                jellies.remove(j);
                continue;
            }
            if (j.age >= 400) {
                level.sendParticles(JELLY, j.pos.x, j.pos.y, j.pos.z, 8, 0.3, 0.3, 0.3, 0);
                jellies.remove(j);
                continue;
            }
            // the bell, its tentacles and the ring on the floor under it
            if (j.age % 2 == 0) {
                level.sendParticles(j.fuse >= 0 ? RED : JELLY, j.pos.x, j.pos.y, j.pos.z, 4, 0.25, 0.12, 0.25, 0);
                level.sendParticles(ParticleTypes.GLOW, j.pos.x, j.pos.y, j.pos.z, 1, 0.2, 0.1, 0.2, 0);
                for (int i = 0; i < 3; i++) {
                    double a = j.age * 0.1 + i * Math.PI * 2 / 3;
                    level.sendParticles(JELLY_PINK, j.pos.x + Math.cos(a) * 0.2, j.pos.y - 0.4 - i * 0.15, j.pos.z + Math.sin(a) * 0.2,
                            1, 0, 0, 0, 0);
                }
            }
            if (j.age % 4 == 0 || j.fuse >= 0) {
                telegraphRing(level, floorAt, j.fuse >= 0 ? JELLY_R : 1.0, j.fuse >= 0 ? RED : AQUA);
            }
        }
    }

    private void burstJelly(ServerLevel level, Jelly j) {
        level.sendParticles(JELLY, j.pos.x, j.pos.y, j.pos.z, 40, 0.8, 0.6, 0.8, 0);
        level.sendParticles(ParticleTypes.GLOW, j.pos.x, j.pos.y, j.pos.z, 20, 0.8, 0.6, 0.8, 0.05);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, j.pos.x, j.pos.y, j.pos.z, 12, 0.6, 0.4, 0.6, 0.2);
        level.playSound(null, j.pos.x, j.pos.y, j.pos.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 1.5F, 0.8F);
        level.playSound(null, j.pos.x, j.pos.y, j.pos.z, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.5F, 0.6F);
        for (LivingEntity e : victims(level, j.pos, JELLY_R + 1.5)) {
            if (flatDist(e.position(), j.pos) <= JELLY_R + e.getBbWidth() / 2 && Math.abs(e.getY() + e.getBbHeight() / 2 - j.pos.y) < 2.0) {
                Vec3 push = e.position().subtract(j.pos).multiply(1, 0, 1);
                push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(0.5);
                if (shove(level, e, 7.0F, push, 0.3)) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                }
            }
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(AQUA, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.5F, 1.8F);
            return false;
        }
        return super.hurtServer(level, source, overcharged() ? amount * 1.15F : amount);
    }

    private void cleanUp(ServerLevel level) {
        discardAdds(level);
        jellies.clear();
        endOvercharge(level);
    }

    /** Back to the first phase (the fight was reset): the hull quiets, base speed. */
    private void resetForm(ServerLevel level) {
        groaning = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("abyss_diver_wrath"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        if (overchargeUntil >= 0 && tickCount >= overchargeUntil) {
            endOvercharge(level);
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(hub(level))).inflate(openR + 14, 20, openR + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && !jellies.isEmpty()) {
            jellies.clear();                               // the chamber emptied (death, flight)
        }
        if (phase() == 1 && groaning) {
            resetForm(level);                              // the fight was reset
        }
        tickJellies(level);
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!groaning && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "groan");
            } else if (groaning && --surgeTimer <= 0) {
                surgeTimer = Math.max(220, (int) Math.round(SURGE_EVERY * cooldownScale()));
                chain(level, "overcharge");
            }
        }
        // phase 3: the hull groans; pressure spikes and drifting jellies (they wait while he groans)
        if (groaning && phase() == 2 && anyone) {
            if (tickCount % 3 == 0) {
                drips(level, 2);
            }
            if (tickCount % 100 == 0) {
                hullCreak(level, 0.6F + getRandom().nextFloat() * 0.3F);
            }
            cur = currentAttack();
            boolean busy = cur != null && "groan".equals(cur.name);
            if (fighting && !busy && guard == 0) {
                if (--spikeTimer <= 0) {
                    spikeTimer = Math.max(40, (int) Math.round(SPIKE_EVERY * cooldownScale()));
                    castSpikes(level, target);
                }
                if (--jellyTimer <= 0) {
                    jellyTimer = Math.max(60, (int) Math.round(JELLY_EVERY * cooldownScale()));
                    if (jellies.size() < Math.min(5, scaledCount(2) + 1)) {
                        spawnJelly(level);
                    }
                }
            }
        }
        // ambience: the porthole's glow, bubbles of air from the helmet valve, sparks while overcharged
        if (tickCount % 6 == 0) {
            Vec3 p = porthole();
            level.sendParticles(ParticleTypes.GLOW, p.x, p.y, p.z, 1, 0.15, 0.15, 0.15, 0);
        }
        if (tickCount % 14 == 0) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 3.9, getZ(), 1, 0.05, 0.05, 0.05, 0.01);
        }
        if (overcharged() && tickCount % 2 == 0) {
            sparks(level, position().add(0, 1.0 + getRandom().nextDouble() * 2.5, 0), 2);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("abyss_diver_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take it back where it would carry them off the open floor
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        steam(level, position().add(0, 2.5, 0), 30, 1.2);
        sparks(level, porthole(), 10);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        steam(level, position().add(0, 2.0, 0), 50, 1.2);
        level.sendParticles(JELLY, getX(), getY() + 3, getZ(), 40, 1.0, 1.0, 1.0, 0);
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 1, getZ(), 80, 1.5, 1.0, 1.5, 0.3);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("DiverCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("DiverRadius", radius);
        output.putBoolean("DiverGroaning", groaning);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("DiverCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("DiverRadius", 18);
        groaning = input.getBooleanOr("DiverGroaning", false) && phase() == 2;
        hub = null;
        jellies.clear();
        overchargeUntil = -1;
    }
}
