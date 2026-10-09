package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
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
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
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

import static com.brasshaven.generated.MobAnims.SporeAlchemist.BLOOM;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.BOGGED;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.EXHALE;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.FLASK;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.ROAR;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.SHROUD;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.SPRAY;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.SPROUT;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.STAFF;
import static com.brasshaven.generated.MobAnims.SporeAlchemist.STAGGER;

/**
 * L'Alchimiste des spores (The Spore Alchemist), the champion of the Spore Refinery: a hunched alchemist (3.5 blocks)
 * half-consumed by the fungus he refined. A leather apron over a plum work coat, a brass respirator mask with glowing
 * green lenses, a hump that is a sprouting fly agaric, mycelium trailing from his sleeves, shelf fungi on his
 * shoulders, a brass spore-tank on his back feeding the nozzle-gun in his left hand, a long flask-tipped stirring staff
 * in his right. He waits on the open top of the giant fly agaric's cap (about 42 across, fenced, two railed stairwell
 * openings in it, a gilded ring inlaid round its middle).
 * <ul>
 *     <li>Phase 1: the <b>staff</b> (a sweep, then the flask brought down on a red ring), the <b>spray</b> (a drawn
 *     cone of spores that poisons and leaves a lingering cloud), thrown <b>flasks</b> onto rings coloured by their brew
 *     (poison green, slowness grey, blindness black) and the <b>sprout</b>: rings under his foes where mushrooms burst
 *     out 1.5 s later and stand a few seconds as obstacles.</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>shroud</b> (he vanishes into a spore cloud and bursts out on a marked
 *     ring), the <b>bogged</b> (mushroom-grown skeletons climb out of the cap), more flasks and sprouts.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>bloom</b>. The cap breathes: a wave (jump
 *     it), vents round the edge burst on marked rings every few seconds, every ~16 s the <b>exhale</b>: the gilded ring
 *     flares and one side of it (the inside, then the outside, in turn) fills with spores (drawn for 2.5 s, step across
 *     the ring), and a mycelium tether field round him slows whoever stays close.</li>
 * </ul>
 * The only blocks he places are the sprouted mushrooms (a stem and a red cap over the open cap floor, never where
 * anyone stands): each goes after 6 s, and all of them when the fight resets, the arena empties, he dies or is removed,
 * and on the first tick after a reload. Pushes are capped and never thrown toward a stairwell or the cap's edge.
 */
public class SporeAlchemist extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 3.5F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_RANGE = 5.0;
    private static final double SWEEP_HALF = 75;
    private static final double SLAM_R = 2.0;
    private static final double SPRAY_RANGE = 9.0;
    private static final double SPRAY_HALF = 28;
    private static final double FLASK_R = 2.2;
    private static final double SPROUT_R = 1.5;
    private static final double SHROUD_R = 3.0;
    private static final double VENT_R = 2.0;
    private static final double TETHER_R = 6.0;
    private static final int MUSHROOM_TICKS = 120;
    private static final int EXHALE_EVERY = 320;
    private static final int VENT_EVERY = 80;
    private static final int MAX_MUSHROOMS = 14;
    private static final DustParticleOptions SPORE = new DustParticleOptions(0x78EC60, 1.4F);
    private static final DustParticleOptions SPORE_BIG = new DustParticleOptions(0xB4FF9A, 2.2F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions BROWN = new DustParticleOptions(0x9A6A3C, 1.4F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF2C450, 1.5F);
    private static final DustParticleOptions THREAD = new DustParticleOptions(0xECEADE, 0.8F);
    private static final DustParticleOptions[] BREW = {
            new DustParticleOptions(0x5AC83C, 1.5F),    // poison
            new DustParticleOptions(0x9AAAC4, 1.5F),    // slowness
            new DustParticleOptions(0x2A2448, 1.6F)};   // blindness

    private record Temp(BlockState original, BlockState placed, int until) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 19;
    /** The gilded ring's centre and radius (found from the inlaid trim; the arena centre and 0.7 x radius without). */
    private @Nullable Vec3 ringCentre;
    private double ringR = 13;
    private boolean ringFound;
    /** The floor is flat (the cap): floors must lie within 0.6 of the seal's level (1.6 on rough ground). */
    private double floorTol = -1;
    /** Phase 3 has started (the cap breathes). */
    private boolean bloomed;
    private int guard;
    private int roarUntil = -1;
    private int exhaleTimer = 140;
    private int ventTimer = 60;
    private boolean exhaleInside;
    /** Hidden in the spore shroud (invisible, guarded). */
    private boolean hidden;
    // moves in flight
    private @Nullable Vec3 slamAt;
    private final List<Vec3> flaskSpots = new ArrayList<>();
    private final List<Integer> flaskKinds = new ArrayList<>();
    private @Nullable Vec3 shroudDest;
    // sprouted mushrooms: temporary blocks with the original state and the tick they go
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public SporeAlchemist(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 620.0)
                .add(Attributes.ARMOR, 11.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 13.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SporeAlchemist.TICKS;
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
        return 105.0F;
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

    /** His own brews and spores do not take on him. */
    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        if (effect.is(MobEffects.POISON) || effect.is(MobEffects.SLOWNESS) || effect.is(MobEffects.BLINDNESS)) {
            return false;
        }
        return super.canBeAffected(effect);
    }

    // ------------------------------------------------------------------ arena memory (the cap)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.ringCentre = null;
        this.floorTol = -1;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    private double reach() {
        return Math.max(6.0, Math.min(18.0, radius - 1.0));
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

    /** Finds the gilded ring inlaid in the cap (the floor layer round the seal) and whether the floor is flat. */
    private void survey(ServerLevel level) {
        if (ringCentre != null && floorTol > 0) {
            return;
        }
        Vec3 c = centre();
        int y = Mth.floor(c.y) - 1;
        int r = radius + 3;
        double sx = 0;
        double sz = 0;
        List<long[]> found = new ArrayList<>();
        int flat = 0;
        int samples = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                if (dx * dx + dz * dz > r * r) {
                    continue;
                }
                p.set(Mth.floor(c.x) + dx, y, Mth.floor(c.z) + dz);
                if (!level.isLoaded(p)) {
                    continue;
                }
                Identifier id = BuiltInRegistries.BLOCK.getKey(level.getBlockState(p).getBlock());
                if ("brasshaven".equals(id.getNamespace()) && "gilded_trim".equals(id.getPath())) {
                    found.add(new long[] {p.getX(), p.getZ()});
                    sx += p.getX() + 0.5;
                    sz += p.getZ() + 0.5;
                }
                if ((dx & 3) == 0 && (dz & 3) == 0 && dx * dx + dz * dz <= radius * radius) {
                    samples++;
                    double fy = floorY(level, p.getX() + 0.5, c.y + 0.5, p.getZ() + 0.5);
                    if (!Double.isNaN(fy) && Math.abs(fy - c.y) <= 0.6) {
                        flat++;
                    }
                }
            }
        }
        floorTol = samples > 0 && flat >= samples * 0.7 ? 0.6 : 1.6;
        if (found.size() >= 24) {
            Vec3 rc = new Vec3(sx / found.size(), c.y, sz / found.size());
            double sum = 0;
            for (long[] f : found) {
                sum += Math.hypot(f[0] + 0.5 - rc.x, f[1] + 0.5 - rc.z);
            }
            ringCentre = rc;
            ringR = sum / found.size();
            ringFound = true;
        } else {
            ringCentre = c;
            ringR = Mth.clamp(radius * 0.7, 6.0, 14.0);
            ringFound = false;
        }
    }

    private Vec3 ringCentre() {
        return ringCentre != null ? ringCentre : centre();
    }

    /**
     * A spot of open cap at (x, z): floor at the seal's level, two blocks of air over it and, with {@code inArena},
     * within the arena (and, where the gilded ring was found, no further than 6 blocks out from it, short of the fence
     * and the cap's edge); or null.
     */
    private @Nullable Vec3 deck(ServerLevel level, double x, double z, boolean inArena) {
        survey(level);
        Vec3 c = centre();
        if (inArena) {
            if (Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
                return null;
            }
            if (ringFound && Math.hypot(x - ringCentre().x, z - ringCentre().z) > ringR + 6.0) {
                return null;
            }
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > floorTol || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Open cap at {@code p} and all round it within {@code r} (no stairwell, railing or edge in the circle). */
    private @Nullable Vec3 openAround(ServerLevel level, double x, double z, double r) {
        Vec3 s = deck(level, x, z, true);
        if (s == null) {
            return null;
        }
        for (int i = 0; i < 8; i++) {
            double a = Math.PI * 2 * i / 8;
            if (deck(level, x + Math.cos(a) * r, z + Math.sin(a) * r, true) == null) {
                return null;
            }
        }
        return s;
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

    /** The push is dropped where it would carry {@code e} off the open cap (into a stairwell, the fence, the edge). */
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

    /** Pushes capped at 1.1, lift at 0.45 (0.2 when no open cap lies 3 blocks beyond); none off the cap. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.1, knockback));
        }
        shove(level, e, damage, push, lift);
    }

    private boolean shove(ServerLevel level, LivingEntity e, float damage, Vec3 push, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
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

    private static void sicken(LivingEntity e, int ticks, int amp) {
        e.addEffect(new MobEffectInstance(MobEffects.POISON, ticks, amp));
    }

    private void sporeBurst(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(SPORE_BIG, at.x, at.y + 0.6, at.z, count / 2, spread, 0.5, spread, 0.0);
        level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, at.x, at.y + 0.8, at.z, count, spread, 0.6, spread, 0.02);
        level.sendParticles(ParticleTypes.MYCELIUM, at.x, at.y + 0.3, at.z, count / 2, spread, 0.2, spread, 0.0);
    }

    /** The flask at the tip of his staff (right hand). */
    private Vec3 staffTip() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(left.scale(1.0)).add(f.scale(0.8)).add(0, 3.4, 0);
    }

    /** The mouth of the nozzle-gun in his left hand. */
    private Vec3 nozzle() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(left.scale(-0.9)).add(f.scale(1.5)).add(0, 1.7, 0);
    }

    private Vec3 mask() {
        return position().add(forward().scale(0.9)).add(0, 2.9, 0);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // staff: the staff drawn back over his shoulder (0.8 s, the arc drawn in green), swept across: 13 and a push;
        // he turns (up to 30°) and a ring 3.5 ahead is drawn red at once, then the flask comes down on it 0.6 s later:
        // 11 and Poison I 2 s
        out.add(BossAttack.of("staff").anim(STAFF).timing(16, 20, 14).range(0, 6.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, SPORE);
                        b.telegraphArc(level, SWEEP_RANGE - 2.0, SWEEP_HALF, SPORE);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.BOTTLE_FILL, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> sweep(level, 13.0F, 0.9))
                .active((b, level, t, tick) -> {
                    if (tick == 1) {
                        if (t != null) {
                            turnToward(t, 30.0F);
                        }
                        Vec3 a = ahead(3.5);
                        Vec3 s = deck(level, a.x, a.z, false);
                        slamAt = s != null ? s : new Vec3(a.x, getY(), a.z);
                    }
                    if (slamAt != null && tick >= 1 && tick < 12 && tick % 2 == 1) {
                        b.telegraphRing(level, slamAt, SLAM_R, RED);
                    }
                    if (tick == 12 && slamAt != null) {
                        slam(level, slamAt);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 8.0 ? "spray" : "flask");
                    }
                })
                .build());
        // spray: the nozzle-gun levelled, the tank building pressure (1.2 s; the cone drawn green from 0.3 s, it
        // follows you slowly, red from 0.8 s), then spores sprayed for 1 s: 3 and Poison I 3 s, four times (every
        // 0.25 s) to whoever stays in it; a lingering spore cloud (r 2.5, 5 s) is left 5 blocks ahead
        out.add(BossAttack.of("spray").anim(SPRAY).timing(24, 20, 16).range(0, SPRAY_RANGE + 0.5).cooldown(150).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 16) {
                        turnToward(t, 3.0F);
                    }
                    if (tick >= 6 && tick % 3 == 0) {
                        drawCone(level, tick < 16 ? SPORE : RED);
                    }
                    Vec3 n = nozzle();
                    level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, n.x, n.y, n.z, 1, 0.1, 0.1, 0.1, 0.0);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 0.8F, 1.2F + tick * 0.02F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick < 20) {
                        spray(level);
                        if (tick % 5 == 0) {
                            hitCone(level);
                        }
                    }
                    if (tick % 5 == 0 && tick < 20) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.4F, 0.6F);
                    }
                    if (tick == 19) {
                        Vec3 a = ahead(5.0);
                        Vec3 s = deck(level, a.x, a.z, true);
                        if (s != null) {
                            sporeCloud(level, s, 2.5F, 100);
                        }
                    }
                })
                .build());
        // flask: flasks plucked from his belt (1.0 s): 2 (phase 2 three) rings (r 2.2) drawn in the colour of their brew
        // (green poison, grey slowness, black blindness), the first following you until 0.6 s, a red ring inside each
        // from then; lobbed at 1.0 s, they land 0.8 s later: 8, a little push, and Poison II 3 s / Slowness II 3 s /
        // Blindness 2 s
        out.add(BossAttack.of("flask").anim(FLASK).timing(20, 10, 14).range(4.0, 24.0).cooldown(120).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planFlasks(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12 && t != null && !flaskSpots.isEmpty()) {
                        Vec3 s = deck(level, t.getX(), t.getZ(), true);
                        if (s != null && flatDist(s, position()) > 2.5) {
                            flaskSpots.set(0, s);
                        }
                    }
                    if (tick % 2 == 0) {
                        for (int i = 0; i < flaskSpots.size(); i++) {
                            b.telegraphRing(level, flaskSpots.get(i), FLASK_R, BREW[flaskKinds.get(i)]);
                            if (tick >= 12) {
                                b.telegraphRing(level, flaskSpots.get(i), FLASK_R - 0.6, RED);
                            }
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BOTTLE_FILL, SoundSource.HOSTILE, 1.2F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int i = 0; i < flaskSpots.size(); i++) {
                        b.addEffect(flaskFlight(staffTip(), flaskSpots.get(i), flaskKinds.get(i), 16));
                    }
                    level.playSound(null, b, SoundEvents.SPLASH_POTION_THROW, SoundSource.HOSTILE, 1.6F, 0.6F);
                })
                .build());
        // sprout: the staff driven into the cap (0.9 s; mycelium creeps out round his feet); a ring (r 1.5) under each
        // foe (up to 4) and on 2 more open spots (phase 2 four), drawn for 1.5 s (red for the last 0.5 s), then a
        // mushroom bursts out of each: 10, a lift and Poison I 2 s; it stands there 6 s (only where nobody stands)
        out.add(BossAttack.of("sprout").anim(SPROUT).timing(18, 8, 16).range(0, 26.0).cooldown(170).weight(7)
                .windup((b, level, t, tick) -> {
                    double a = tick * 0.7;
                    for (int s = 0; s < 3; s++) {
                        double r = 1.0 + tick * 0.1;
                        double aa = a + s * Math.PI * 2 / 3;
                        level.sendParticles(ParticleTypes.MYCELIUM, b.getX() + Math.cos(aa) * r, b.getY() + 0.2, b.getZ() + Math.sin(aa) * r,
                                2, 0.1, 0.05, 0.1, 0.0);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.FUNGUS_PLACE, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Vec3 s : planSprouts(level, t)) {
                        b.addEffect(sprout(s));
                    }
                    sporeBurst(level, ahead(1.0), 16, 0.6);
                    level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // shroud: the tank's valve thrown open, a cloud billowing round him (1.0 s); he vanishes into it (guarded) and
        // a ring (r 3) is drawn where he will come out, near you but never on anyone (green, red for the last 0.5 s);
        // 1.5 s after vanishing he bursts out of it: 11, a push out of the ring and Poison I 3 s
        out.add(BossAttack.of("shroud").anim(SHROUD).phaseTwo().timing(20, 40, 14).range(0, 30.0).cooldown(260).weight(6)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 1.0 + tick * 0.12, SPORE);
                    }
                    level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, b.getX(), b.getY() + 1.5, b.getZ(), 1, 0.6, 0.6, 0.6, 0.0);
                    level.sendParticles(SPORE_BIG, b.getX(), b.getY() + 1.5, b.getZ(), 3, 0.3 + tick * 0.06, 0.8, 0.3 + tick * 0.06, 0.0);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.2F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    hide(true);
                    guard = Math.max(guard, 34);
                    sporeBurst(level, position(), 50, 1.4);
                    level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), getY() + 1.5, getZ(), 20, 1.2, 1.0, 1.2, 0.01);
                    level.playSound(null, b, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 1.6F, 0.6F);
                    shroudDest = pickShroud(level, t);
                })
                .active((b, level, t, tick) -> {
                    Vec3 d = shroudDest;
                    if (d == null) {
                        return;
                    }
                    if (tick < 30 && tick % 2 == 0) {
                        b.telegraphRing(level, d, SHROUD_R, tick < 20 ? SPORE : RED);
                        level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, d.x, d.y + 0.5, d.z, 4, 1.0, 0.4, 1.0, 0.01);
                    }
                    if (tick == 20) {
                        teleportTo(d.x, d.y, d.z);
                        if (t != null) {
                            faceToward(t.position());
                        }
                    }
                    if (tick == 30) {
                        reappear(level, d);
                    }
                })
                .build());
        // bogged: the staff stirred over the cap (1.0 s) and struck down: two bogged (more in co-op) claw out of the
        // mycelium, unless three of his helpers already stand there
        out.add(BossAttack.of("bogged").anim(BOGGED).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(700).weight(4)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.MYCELIUM, b.getX(), b.getY() + 0.3, b.getZ(), 6, 3.0, 0.1, 3.0, 0.0);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BOGGED_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    sporeBurst(level, position(), 30, 3.0);
                    if (minionCount(level) < 3) {
                        b.summon(level, EntityTypes.BOGGED, 2, 4.0);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // bloom: the hump swells, the tank shudders (2.0 s, guarded; rings of spores grow round him), the staff slammed
        // down: a wave to 14 (10, jump it); the cap starts to breathe
        out.add(BossAttack.of("bloom").anim(BLOOM).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, SPORE);
                    }
                    level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, b.getX(), b.getY() + 3, b.getZ(), 4, 2.0, 1.5, 2.0, 0.02);
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> startBloom(level))
                .build());
        // exhale: the cap breathes in (2.5 s): the gilded ring flares gold, and one side of it (the outside first,
        // then the inside, in turn) fills with drifting spores, red from 1.8 s; the cap breathes out: everyone on that
        // side takes 9 and Poison II 3 s (the ring itself is always safe; jumping does not help)
        out.add(BossAttack.of("exhale").anim(EXHALE).phaseTwo().timing(50, 10, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    survey(level);
                    exhaleInside = !exhaleInside;
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawExhale(level, tick < 36 ? SPORE : RED);
                    }
                    if (tick % 10 == 0) {
                        Vec3 c = ringCentre();
                        level.playSound(null, c.x, c.y, c.z, SoundEvents.PLAYER_BREATH, SoundSource.HOSTILE, 3.0F, 0.4F);
                        level.playSound(null, c.x, c.y, c.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> exhale(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void sweep(ServerLevel level, float damage, double knock) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SWEEP_HALF));
        for (LivingEntity e : victims(level, position(), SWEEP_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SWEEP_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.5) {
                strike(level, e, damage, knock, 0.3);
            }
        }
        for (double a = -SWEEP_HALF; a <= SWEEP_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SWEEP_RANGE - 1.0));
            level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, p.x, p.y + 1.2, p.z, 2, 0.1, 0.2, 0.1, 0.01);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    /** The flask brought down: 11 and Poison I 2 s in r 2 (a lift, no push). */
    private void slam(ServerLevel level, Vec3 at) {
        sporeBurst(level, at, 30, 1.0);
        level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.3, at.z, 30, 1.0, 0.2, 1.0, 0.1);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.SPLASH_POTION_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
        for (LivingEntity e : victims(level, at, SLAM_R + 1)) {
            if (flatDist(e.position(), at) <= SLAM_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5
                    && shove(level, e, 11.0F, Vec3.ZERO, 0.3)) {
                sicken(e, 40, 0);
            }
        }
    }

    private void drawCone(ServerLevel level, DustParticleOptions dust) {
        for (double r = 3.0; r <= SPRAY_RANGE; r += 3.0) {
            telegraphArc(level, r, SPRAY_HALF, dust);
        }
        telegraphArc(level, SPRAY_RANGE, SPRAY_HALF, dust);
        for (int s = -1; s <= 1; s += 2) {
            Vec3 dir = rotate(forward(), s * SPRAY_HALF);
            for (double d = 1.5; d <= SPRAY_RANGE; d += 1.5) {
                Vec3 p = position().add(dir.scale(d));
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private void spray(ServerLevel level) {
        Vec3 n = nozzle();
        for (int i = 0; i < 6; i++) {
            Vec3 dir = rotate(forward(), (getRandom().nextDouble() * 2 - 1) * SPRAY_HALF);
            double sp = 0.4 + getRandom().nextDouble() * 0.35;
            level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, n.x, n.y, n.z, 0, dir.x, -0.1, dir.z, sp);
        }
        for (double d = 2.0; d <= SPRAY_RANGE; d += 2.0) {
            Vec3 p = ahead(d);
            level.sendParticles(SPORE, p.x, p.y + 1.0, p.z, 1, d * 0.18, 0.4, d * 0.18, 0.0);
        }
    }

    private void hitCone(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SPRAY_HALF));
        for (LivingEntity e : victims(level, position(), SPRAY_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SPRAY_RANGE + e.getBbWidth() / 2 && (d < 1.5 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 4.0 && e.hurtServer(level, damageSources().mobAttack(this), 3.0F)) {
                sicken(e, 60, 0);
            }
        }
    }

    /** A lingering spore cloud (an area effect cloud of Poison I) with its edge marked in green while it lasts. */
    private void sporeCloud(ServerLevel level, Vec3 at, float r, int duration) {
        AreaEffectCloud cloud = new AreaEffectCloud(level, at.x, at.y, at.z);
        cloud.setOwner(this);
        cloud.setRadius(r);
        cloud.setDuration(duration);
        cloud.setWaitTime(10);
        cloud.setRadiusPerTick(-r / (duration + 60.0F));
        cloud.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0));
        level.addFreshEntity(cloud);
        int[] t = {0};
        addEffect((boss, lvl) -> {
            int k = t[0]++;
            if (k % 8 == 0) {
                boss.telegraphRing(lvl, at, Math.max(0.5, r - r * k / (duration + 60.0)), SPORE);
            }
            return k >= duration;
        });
    }

    /** Flask spots: the target, then the other players, then open cap near the target; at least 4 apart. */
    private void planFlasks(ServerLevel level, @Nullable LivingEntity target) {
        flaskSpots.clear();
        flaskKinds.clear();
        int n = phase() == 2 ? 3 : 2;
        if (target != null) {
            tryFlask(level, target.getX(), target.getZ());
        }
        for (Player p : fighters(level)) {
            if (flaskSpots.size() >= n) {
                break;
            }
            if (p != target) {
                tryFlask(level, p.getX(), p.getZ());
            }
        }
        Vec3 base = target != null ? target.position() : ahead(8.0);
        for (int tries = 0; tries < 40 && flaskSpots.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 4.0 + getRandom().nextDouble() * 3.0;
            tryFlask(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d);
        }
        if (flaskSpots.isEmpty()) {
            Vec3 a = ahead(6.0);
            flaskSpots.add(new Vec3(a.x, getY(), a.z));
        }
        for (int i = 0; i < flaskSpots.size(); i++) {
            flaskKinds.add(i == 0 ? 0 : getRandom().nextInt(3));
        }
    }

    private void tryFlask(ServerLevel level, double x, double z) {
        Vec3 s = deck(level, x, z, true);
        if (s == null || flatDist(s, position()) < 3.0) {
            return;
        }
        for (Vec3 o : flaskSpots) {
            if (flatDist(o, s) < 4.0) {
                return;
            }
        }
        flaskSpots.add(s);
    }

    /** A flask arcing onto its ring (the ring red while it flies), shattering: 8 in r 2.2 and its brew. */
    private Effect flaskFlight(Vec3 from, Vec3 at, int kind, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                double f = (k + 1) / (double) delay;
                Vec3 p = from.lerp(at, f).add(0, Math.sin(f * Math.PI) * 4.5, 0);
                level.sendParticles(BREW[kind], p.x, p.y, p.z, 3, 0.1, 0.1, 0.1, 0.0);
                level.sendParticles(ParticleTypes.WITCH, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, FLASK_R, BREW[kind]);
                    boss.telegraphRing(level, at, FLASK_R - 0.6, RED);
                }
                return false;
            }
            if (boss instanceof SporeAlchemist sa) {
                level.sendParticles(BREW[kind], at.x, at.y + 0.5, at.z, 40, FLASK_R * 0.6, 0.4, FLASK_R * 0.6, 0.0);
                level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.3, at.z, 30, 1.0, 0.2, 1.0, 0.1);
                level.sendParticles(ParticleTypes.WITCH, at.x, at.y + 0.5, at.z, 12, 1.0, 0.4, 1.0, 0.02);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.SPLASH_POTION_BREAK, SoundSource.HOSTILE, 2.0F, 0.8F);
                for (LivingEntity e : boss.victims(level, at, FLASK_R + 1)) {
                    if (flatDist(e.position(), at) <= FLASK_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        Vec3 out = e.position().subtract(at).multiply(1, 0, 1);
                        out = out.lengthSqr() < 1.0E-4 ? Vec3.ZERO : out.normalize().scale(0.3);
                        if (sa.shove(level, e, 8.0F, out, 0.2)) {
                            switch (kind) {
                                case 0 -> sicken(e, 60, 1);
                                case 1 -> e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
                                default -> e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0));
                            }
                        }
                    }
                }
            }
            return true;
        };
    }

    /** Sprout spots: under each player (up to 4), then 2 (phase 2: 4, more in co-op) open spots; at least 3 apart. */
    private List<Vec3> planSprouts(ServerLevel level, @Nullable LivingEntity target) {
        List<Vec3> spots = new ArrayList<>();
        List<LivingEntity> marks = new ArrayList<>();
        if (target != null) {
            marks.add(target);
        }
        for (Player p : fighters(level)) {
            if (p != target && marks.size() < 4) {
                marks.add(p);
            }
        }
        for (LivingEntity m : marks) {
            Vec3 s = deck(level, m.getX(), m.getZ(), true);
            if (s != null) {
                spots.add(s);
            }
        }
        int extra = scaledCount(phase() == 2 ? 4 : 2);
        Vec3 c = ringCentre();
        double r = Math.min(reach(), ringR + 4.0);
        int want = spots.size() + extra;
        for (int tries = 0; tries < 50 && spots.size() < want; tries++) {
            Vec3 s = deck(level, c.x + (getRandom().nextDouble() * 2 - 1) * r, c.z + (getRandom().nextDouble() * 2 - 1) * r, true);
            if (s == null || flatDist(s, position()) < 2.5) {
                continue;
            }
            boolean ok = true;
            for (Vec3 o : spots) {
                if (flatDist(o, s) < 3.0) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                spots.add(s);
            }
        }
        return spots;
    }

    /** A sprouting ring (brown, red for the last 10 ticks) for 30 ticks, then the mushroom bursts out and stands. */
    private Effect sprout(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, SPROUT_R, k >= 20 ? RED : BROWN);
                }
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.MYCELIUM, at.x, at.y + 0.15, at.z, 3, 0.6, 0.02, 0.6, 0.0);
                }
                return false;
            }
            if (boss instanceof SporeAlchemist sa) {
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.RED_MUSHROOM_BLOCK.defaultBlockState()), at.x,
                        at.y + 1.0, at.z, 30, 0.5, 0.8, 0.5, 0.1);
                sa.sporeBurst(level, at, 20, 0.6);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.FUNGUS_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 1.5F, 0.8F);
                for (LivingEntity e : boss.victims(level, at, SPROUT_R + 1)) {
                    if (flatDist(e.position(), at) <= SPROUT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.0
                            && sa.shove(level, e, 10.0F, Vec3.ZERO, 0.5)) {
                        sicken(e, 40, 0);
                    }
                }
                sa.growMushroom(level, at);
            }
            return true;
        };
    }

    /** A stem and a red cap over the open cap floor at {@code at} for 6 s, only where nobody stands. */
    private void growMushroom(ServerLevel level, Vec3 at) {
        if (temps.size() >= MAX_MUSHROOMS * 2) {
            return;
        }
        BlockPos stem = BlockPos.containing(at.x, at.y + 0.05, at.z);
        BlockPos top = stem.above();
        if (!level.isLoaded(stem) || temps.containsKey(stem.asLong()) || temps.containsKey(top.asLong())
                || !level.getBlockState(stem).isAir() || !level.getBlockState(top).isAir()) {
            return;
        }
        if (!level.getEntitiesOfClass(LivingEntity.class, new AABB(stem).expandTowards(0, 1, 0).inflate(0.1)).isEmpty()) {
            return;
        }
        int until = tickCount + MUSHROOM_TICKS;
        place(level, stem, Blocks.MUSHROOM_STEM.defaultBlockState(), until);
        place(level, top, Blocks.RED_MUSHROOM_BLOCK.defaultBlockState(), until);
    }

    /** Sets a temporary block without updating its neighbours' shapes (the cap's mushroom blocks keep their faces). */
    private void place(ServerLevel level, BlockPos p, BlockState s, int until) {
        temps.put(p.asLong(), new Temp(level.getBlockState(p), s, until));
        level.setBlock(p, s, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
    }

    private void clearTemp(ServerLevel level, long key) {
        Temp t = temps.remove(key);
        BlockPos p = BlockPos.of(key);
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        if (level.getBlockState(p).getBlock() == t.placed().getBlock()) {
            level.setBlock(p, t.original(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
            level.sendParticles(ParticleTypes.MYCELIUM, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.0);
        }
    }

    /** Every changed block goes back (only where it is still the one set). */
    private void restoreAll(ServerLevel level) {
        for (SavedTemp s : staleTemps) {
            temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed(), 0));
        }
        staleTemps.clear();
        for (Long key : new ArrayList<>(temps.keySet())) {
            clearTemp(level, key);
        }
    }

    private int minionCount(ServerLevel level) {
        return level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 10, radius + 4),
                m -> m.isAlive() && m.entityTags().contains(MINION_TAG)).size();
    }

    private void discardBogged(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 8, 12, radius + 8),
                m -> m.isAlive() && m.entityTags().contains(MINION_TAG) && m.getType() == EntityTypes.BOGGED)) {
            m.discard();
        }
    }

    private void hide(boolean on) {
        hidden = on;
        setInvisible(on);
    }

    /**
     * Where he comes out of the shroud: open cap 5-8 blocks from the target, at least 4.5 from every player, the
     * whole ring over open cap (no stairwell, fence or edge in it); the arena centre, or where he stood, without one.
     */
    private Vec3 pickShroud(ServerLevel level, @Nullable LivingEntity target) {
        List<Player> ps = fighters(level);
        Vec3 base = target != null ? target.position() : centre();
        for (int tries = 0; tries < 40; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 5.0 + getRandom().nextDouble() * 3.0;
            Vec3 s = openAround(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d, SHROUD_R);
            if (s == null || !clear(level, s.x, s.y, s.z, 4)) {
                continue;
            }
            boolean ok = true;
            for (Player p : ps) {
                if (flatDist(p.position(), s) < 4.5) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                return s;
            }
        }
        return position();
    }

    /** Out of the shroud: 11, a push out of the ring and Poison I 3 s in r 3. */
    private void reappear(ServerLevel level, Vec3 at) {
        hide(false);
        guard = 0;
        sporeBurst(level, at, 60, 1.6);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, at.x, at.y + 1.0, at.z, 16, 1.4, 0.6, 1.4, 0.01);
        level.playSound(null, this, SoundEvents.PUFFER_FISH_BLOW_UP, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.5F);
        for (LivingEntity e : victims(level, at, SHROUD_R + 1)) {
            if (flatDist(e.position(), at) <= SHROUD_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                Vec3 out = e.position().subtract(at).multiply(1, 0, 1);
                out = out.lengthSqr() < 1.0E-4 ? forward().scale(0.6) : out.normalize().scale(0.6);
                if (shove(level, e, 11.0F, out, 0.3)) {
                    sicken(e, 60, 0);
                }
            }
        }
    }

    // ------------------------------------------------------------------ phase 3: the cap breathes

    private void startBloom(ServerLevel level) {
        bloomed = true;
        exhaleTimer = 140;
        ventTimer = 60;
        exhaleInside = true;            // toggled before each exhale: the outside goes first
        addEffect(capRing(position(), 14.0, 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("spore_alchemist_bloom"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        sporeBurst(level, position().add(0, 2, 0), 80, 2.5);
        level.playSound(null, this, SoundEvents.PUFFER_FISH_BLOW_UP, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    /** A jumpable ring of spores from {@code c}: it hits once whoever stands on the floor at its edge. */
    private Effect capRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof SporeAlchemist sa)) {
                return true;
            }
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                double x = c.x + Math.cos(a) * rr;
                double z = c.z + Math.sin(a) * rr;
                double fy = floorY(level, x, c.y + 0.5, z);
                level.sendParticles(SPORE, x, (Double.isNaN(fy) ? c.y : fy) + 0.2, z, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && overFloor(level, e) < 0.6 && hit.add(e.getUUID())) {
                    sa.strike(level, e, damage, 0.6, 0.35);
                }
            }
            return rr >= max;
        };
    }

    /** Is {@code p} on the side of the gilded ring that breathes out this time (the ring's own band is safe)? */
    private boolean unsafe(Vec3 p) {
        double d = flatDist(p, ringCentre());
        return exhaleInside ? d < ringR - 1.0 : d > ringR + 1.0;
    }

    /** The ring flaring gold, spores drifting over the side that will breathe out. */
    private void drawExhale(ServerLevel level, DustParticleOptions dust) {
        Vec3 c = ringCentre();
        int n = Math.max(24, (int) (ringR * 5));
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2 * i / n;
            level.sendParticles(GOLD, c.x + Math.cos(a) * ringR, c.y + 0.25, c.z + Math.sin(a) * ringR, 1, 0, 0.1, 0, 0);
        }
        double outer = ringFound ? ringR + 6.0 : reach();
        for (int i = 0; i < 40; i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = exhaleInside ? Math.sqrt(getRandom().nextDouble()) * (ringR - 1.0)
                    : ringR + 1.0 + getRandom().nextDouble() * (outer - ringR - 1.0);
            Vec3 f = deck(level, c.x + Math.cos(a) * d, c.z + Math.sin(a) * d, true);
            if (f != null) {
                level.sendParticles(dust, f.x, f.y + 0.2 + getRandom().nextDouble() * 1.2, f.z, 1, 0.1, 0.1, 0.1, 0);
                if (i % 4 == 0) {
                    level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, f.x, f.y + 0.5, f.z, 1, 0.3, 0.3, 0.3, 0.0);
                }
            }
        }
    }

    private void exhale(ServerLevel level) {
        Vec3 c = ringCentre();
        level.playSound(null, c.x, c.y, c.z, SoundEvents.PUFFER_FISH_BLOW_UP, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        double outer = ringFound ? ringR + 6.0 : reach();
        for (int i = 0; i < 90; i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = exhaleInside ? Math.sqrt(getRandom().nextDouble()) * (ringR - 1.0)
                    : ringR + 1.0 + getRandom().nextDouble() * (outer - ringR - 1.0);
            Vec3 f = deck(level, c.x + Math.cos(a) * d, c.z + Math.sin(a) * d, true);
            if (f != null) {
                level.sendParticles(SPORE_BIG, f.x, f.y + 0.6, f.z, 2, 0.4, 0.6, 0.4, 0.0);
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, f.x, f.y + 0.8, f.z, 2, 0.5, 0.6, 0.5, 0.02);
            }
        }
        for (Player p : fighters(level)) {
            if (unsafe(p.position()) && Math.abs(p.getY() - c.y) < 3.5
                    && p.hurtServer(level, damageSources().mobAttack(this), 9.0F)) {
                sicken(p, 60, 1);
            }
        }
    }

    /** A vent near the edge: its ring (green, red for the last 10 ticks) for 30 ticks, then a geyser of spores. */
    private Effect vent(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, VENT_R, k >= 20 ? RED : SPORE);
                }
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, at.x, at.y + 0.3, at.z, 3, 0.4, 0.1, 0.4, 0.01);
                }
                return false;
            }
            if (boss instanceof SporeAlchemist sa) {
                for (int y = 0; y < 6; y++) {
                    level.sendParticles(SPORE_BIG, at.x, at.y + 0.5 + y, at.z, 4, 0.5, 0.3, 0.5, 0.0);
                }
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, at.x, at.y + 2, at.z, 30, 0.8, 1.5, 0.8, 0.05);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.8F, 0.6F);
                for (LivingEntity e : boss.victims(level, at, VENT_R + 1)) {
                    if (flatDist(e.position(), at) <= VENT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0
                            && sa.shove(level, e, 8.0F, Vec3.ZERO, 0.4)) {
                        sicken(e, 40, 0);
                    }
                }
            }
            return true;
        };
    }

    /** {@code n} vents spread round the cap near its edge, each ring wholly over open cap. */
    private void fireVents(ServerLevel level, int n) {
        survey(level);
        Vec3 c = ringCentre();
        double base = getRandom().nextDouble() * Math.PI * 2;
        for (int i = 0; i < n; i++) {
            double a = base + Math.PI * 2 * i / n + (getRandom().nextDouble() - 0.5) * 0.5;
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            double edge = 0;
            for (double d = 2.0; d <= 26.0; d += 1.0) {
                Vec3 p = c.add(dir.scale(d));
                if (deck(level, p.x, p.z, true) != null) {
                    edge = d;
                }
            }
            double want = Math.min(ringR + 4.0, edge - 2.5);
            for (int k = 0; k < 4 && want > 3.0; k++, want -= 1.0) {
                Vec3 p = c.add(dir.scale(want));
                Vec3 s = openAround(level, p.x, p.z, VENT_R);
                if (s != null) {
                    addEffect(vent(s));
                    break;
                }
            }
        }
        level.playSound(null, c.x, c.y, c.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.4F);
    }

    /** The mycelium tether field: threads to everyone within 6 of him, who stay slowed while they stay close. */
    private void tetherField(ServerLevel level) {
        if (hidden || tickCount % 5 != 0) {
            return;
        }
        if (tickCount % 10 == 0) {
            telegraphRing(level, position(), TETHER_R, THREAD);
        }
        Vec3 from = position().add(0, 1.2, 0);
        for (Player p : fighters(level)) {
            Vec3 to = p.position().add(0, 0.9, 0);
            double d = flatDist(p.position(), position());
            if (d > TETHER_R || Math.abs(p.getY() - getY()) > 3.0) {
                continue;
            }
            Vec3 link = to.subtract(from);
            double ll = link.length();
            for (double s = 0.6; s < ll; s += 0.6) {
                Vec3 q = from.add(link.scale(s / ll)).add(0, Math.sin(s / ll * Math.PI) * -0.4, 0);
                level.sendParticles(THREAD, q.x, q.y, q.z, 1, 0, 0, 0, 0);
            }
            if (tickCount % 20 == 0) {
                p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0, true, true));
            }
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0 || hidden) {
            level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0.02);
            level.playSound(null, this, SoundEvents.FUNGUS_BREAK, SoundSource.HOSTILE, 0.8F, 1.4F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardBogged(level);
        if (hidden || isInvisible()) {
            hide(false);
        }
    }

    /** Back to the first phase (the fight was reset): the cap stops breathing, the mushrooms go, base speed. */
    private void resetForm(ServerLevel level) {
        bloomed = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("spore_alchemist_bloom"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("spore_alchemist_wrath"));
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
        if (hidden && (cur == null || !"shroud".equals(cur.name))) {
            hide(false);                                   // the shroud was cut short
        }
        if (!temps.isEmpty()) {
            for (Map.Entry<Long, Temp> e : new ArrayList<>(temps.entrySet())) {
                if (tickCount >= e.getValue().until()) {
                    clearTemp(level, e.getKey());
                }
            }
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && !temps.isEmpty()) {
            restoreAll(level);                             // the arena emptied (death, flight)
        }
        if (phase() == 1 && bloomed) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!bloomed && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "bloom");
            } else if (bloomed && --exhaleTimer <= 0) {
                exhaleTimer = Math.max(180, (int) Math.round(EXHALE_EVERY * cooldownScale()));
                chain(level, "exhale");
            }
        }
        // phase 3: the vents and the tether field (the vents wait while he blooms or the cap breathes out)
        if (bloomed && phase() == 2 && anyone) {
            tetherField(level);
            cur = currentAttack();
            boolean busy = cur != null && ("exhale".equals(cur.name) || "bloom".equals(cur.name));
            if (fighting && !busy && guard == 0 && --ventTimer <= 0) {
                ventTimer = Math.max(40, (int) Math.round(VENT_EVERY * cooldownScale()));
                fireVents(level, scaledCount(2) + 1);
            }
            if (tickCount % 6 == 0) {
                Vec3 c = ringCentre();
                double a = getRandom().nextDouble() * Math.PI * 2;
                double d = getRandom().nextDouble() * reach();
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, c.x + Math.cos(a) * d, c.y + 1.0, c.z + Math.sin(a) * d,
                        2, 0.5, 0.5, 0.5, 0.0);
            }
        }
        // ambience: spores puffing off the hump, the lenses' glow, mycelium dripping from the sleeves
        if (!hidden) {
            if (tickCount % 4 == 0) {
                Vec3 back = position().subtract(forward().scale(0.6));
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, back.x, getY() + 3.3, back.z, 1, 0.4, 0.1, 0.4, 0.0);
            }
            if (tickCount % 12 == 0) {
                Vec3 m = mask();
                level.sendParticles(SPORE, m.x, m.y, m.z, 1, 0.15, 0.05, 0.15, 0.0);
                level.sendParticles(ParticleTypes.MYCELIUM, getX(), getY() + 1.2, getZ(), 2, 0.6, 0.4, 0.6, 0.0);
            }
            if (tickCount % 100 == 0) {
                level.playSound(null, this, SoundEvents.BREWING_STAND_BREW, SoundSource.HOSTILE, 0.8F, 0.6F);
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        if (hidden) {
            hide(false);
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("spore_alchemist_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the roar shoves everyone within 7 away: take it back where it would carry them off the cap
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        sporeBurst(level, position().add(0, 2, 0), 60, 2.0);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        sporeBurst(level, position().add(0, 1, 0), 100, 1.6);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.RED_MUSHROOM_BLOCK.defaultBlockState()), getX(),
                getY() + 3, getZ(), 40, 1.0, 0.6, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.FUNGUS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.4F);
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
            output.putLong("AlchemistCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("AlchemistRadius", radius);
        output.putBoolean("AlchemistBloom", bloomed);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("AlchemistBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("AlchemistCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("AlchemistRadius", 19);
        bloomed = input.getBooleanOr("AlchemistBloom", false) && phase() == 2;
        ringCentre = null;
        floorTol = -1;
        hidden = false;
        setInvisible(false);
        staleTemps.clear();
        input.read("AlchemistBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
    }
}
