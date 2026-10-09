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
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
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

import static com.brasshaven.generated.MobAnims.FrostCommodore.ANCHOR;
import static com.brasshaven.generated.MobAnims.FrostCommodore.BLIZZARD;
import static com.brasshaven.generated.MobAnims.FrostCommodore.BREATH;
import static com.brasshaven.generated.MobAnims.FrostCommodore.FLARE;
import static com.brasshaven.generated.MobAnims.FrostCommodore.HURL;
import static com.brasshaven.generated.MobAnims.FrostCommodore.RAMSHOCK;
import static com.brasshaven.generated.MobAnims.FrostCommodore.ROAR;
import static com.brasshaven.generated.MobAnims.FrostCommodore.SPIKES;
import static com.brasshaven.generated.MobAnims.FrostCommodore.STAGGER;
import static com.brasshaven.generated.MobAnims.FrostCommodore.STRAYS;
import static com.brasshaven.generated.MobAnims.FrostCommodore.THROW;

/**
 * Le Commodore gelé (The Frozen Commodore), the champion of the Icebound Fleet: the expedition's commander, dead in the
 * ice but kept moving by a frost-rimed brass life-support rig. A huge figure (3.8 blocks) in a fur-lined greatcoat
 * crusted with ice, an iron diving-bell hood with a cracked visor glowing pale blue, a frozen beard, a boiler on his
 * back venting cold steam; an ice-encrusted anchor on its chain in his right hand, a signal-flare pistol in his left.
 * He waits on the icebreaker's forecastle deck (about 34 across, the bridge front aft, the bow ahead, a two-high
 * bulwark round it, the deck listing a little to starboard).
 * <ul>
 *     <li>Phase 1: the <b>anchor</b> swings (forehand, then a backhand drawn red first), the anchor <b>throw</b> down a
 *     drawn line (it bites at the end, then the chain drags it back along the same line: it hits on the way back too
 *     and hauls you in), ice <b>spikes</b> erupting along marked lines from the deck, the freezing <b>breath</b> (a
 *     drawn cone that slows) and the <b>hurl</b> of ice blocks onto marked rings that shatter into short-lived slippery
 *     patches of packed ice.</li>
 *     <li>Phase 2 (a roar at 65%): faster, the signal <b>flare</b> shot down a drawn line, the <b>strays</b> (the frozen
 *     crew answers his flare), more spikes and more ice blocks, the swings chain into the breath or the hurl.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>blizzard</b>. The rig's valves blow once
 *     (a wave, jump it), the deck ices over (snow, frost on the screen and a mild slow, no sliding), icicles fall from
 *     the rigging onto marked circles every few seconds, and every ~14 s the <b>ram shock</b>: the ship rams a floe (a
 *     bell rings three times) and the whole deck lurches: two waves roll across the deck from the bow to the stern,
 *     jump them. The icicles pause while the ship lurches.</li>
 * </ul>
 * The only blocks he places are the slippery patches (packed ice over plain full deck blocks): each goes back after
 * 5 s, and all of them when the fight resets, the arena empties, he dies or is removed, and on the first tick after a
 * reload. Pushes are capped and never thrown toward the bulwark or a drop.
 */
public class FrostCommodore extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 3.8F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWING_RANGE = 5.5;
    private static final double SWING_HALF = 80;
    private static final double THROW_MAX = 16.0;
    private static final double THROW_HALF = 1.2;
    private static final double SPIKE_MAX = 16.0;
    private static final double BREATH_RANGE = 10.0;
    private static final double BREATH_HALF = 30;
    private static final double BLOCK_R = 2.0;
    private static final double ICICLE_R = 1.6;
    private static final int PATCH_TICKS = 100;
    private static final int RAM_EVERY = 280;
    private static final int ICICLE_EVERY = 60;
    private static final DustParticleOptions FROST = new DustParticleOptions(0xAEE4FF, 1.4F);
    private static final DustParticleOptions FROST_BIG = new DustParticleOptions(0xD8F4FF, 2.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions FLARE_DUST = new DustParticleOptions(0xFF7A30, 1.3F);
    private static final DustParticleOptions SNOW = new DustParticleOptions(0xF4FAFF, 1.0F);
    private static final DustParticleOptions CHAIN_DUST = new DustParticleOptions(0x8C96A6, 0.9F);

    private record Temp(BlockState original, BlockState placed, int until) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 18;
    /** Unit vector from the deck's centre toward the bow (found from the deck's shape, the structure may be rotated). */
    private @Nullable Vec3 bow;
    /** Phase 3 has started (the blizzard closed in). */
    private boolean blizzard;
    private int guard;
    private int roarUntil = -1;
    private int ramTimer = 120;
    private int icicleTimer = 40;
    /** Ticks the ram waves still roll (the icicles wait for them). */
    private int lurching;
    // moves in flight
    private double throwLen = 8.0;
    private final List<List<Vec3>> spikeLines = new ArrayList<>();
    private final List<Vec3> blockSpots = new ArrayList<>();
    private double flareLen = 20.0;
    // slippery patches: temporary packed ice with the original state and the tick it goes back
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public FrostCommodore(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 640.0)
                .add(Attributes.ARMOR, 13.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.FrostCommodore.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.WHITE;
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

    @Override
    public boolean canFreeze() {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (the forecastle deck)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.bow = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    private double reach() {
        return Math.max(6.0, Math.min(17.0, radius - 1.0));
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
     * A spot of open deck at (x, z): floor within 1.6 of the seal's level (the deck lists a little), two blocks of air
     * over it and, with {@code inArena}, within the arena's radius; or null.
     */
    private @Nullable Vec3 deck(ServerLevel level, double x, double z, boolean inArena) {
        Vec3 c = centre();
        if (inArena && Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > 1.6 || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** The direction of the bow: of the four axis directions, the one with the longest run of open deck. */
    private Vec3 bow(ServerLevel level) {
        if (bow != null) {
            return bow;
        }
        Vec3 c = centre();
        Vec3[] dirs = {new Vec3(1, 0, 0), new Vec3(-1, 0, 0), new Vec3(0, 0, 1), new Vec3(0, 0, -1)};
        Vec3 best = dirs[0];
        int bestRun = -1;
        for (Vec3 d : dirs) {
            Vec3 side = new Vec3(-d.z, 0, d.x);
            int run = 0;
            for (int off = -6; off <= 6; off += 6) {
                int k = 0;
                for (int s = 1; s <= 32; s++) {
                    Vec3 p = c.add(d.scale(s)).add(side.scale(off));
                    if (deck(level, p.x, p.z, false) == null) {
                        break;
                    }
                    k = s;
                }
                run = Math.max(run, k);
            }
            if (run > bestRun) {
                bestRun = run;
                best = d;
            }
        }
        bow = best;
        return best;
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

    /** The push is dropped where it would carry {@code e} off the open deck (into the bulwark, over a drop). */
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

    /** Pushes capped at 1.2, lift at 0.45 (0.2 when no open deck lies 3 blocks beyond); none off the deck. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.2, knockback));
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

    private static void chill(LivingEntity e, int slowTicks, int amp, int frost) {
        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, slowTicks, amp));
        if (e.canFreeze()) {
            e.setTicksFrozen(Math.min(130, Math.max(e.getTicksFrozen(), 0) + frost));
        }
    }

    private void iceBurst(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()), at.x, at.y + 0.5,
                at.z, count, spread, 0.4, spread, 0.1);
        level.sendParticles(ParticleTypes.SNOWFLAKE, at.x, at.y + 0.6, at.z, count / 2, spread, 0.4, spread, 0.04);
    }

    /** The anchor in his right hand (at his side). */
    private Vec3 anchorHand() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(left.scale(1.1)).add(f.scale(0.4)).add(0, 1.6, 0);
    }

    /** The muzzle of the flare pistol in his left hand. */
    private Vec3 pistol() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(left.scale(-1.0)).add(f.scale(1.0)).add(0, 2.2, 0);
    }

    private Vec3 visor() {
        return position().add(forward().scale(0.7)).add(0, 3.2, 0);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // anchor: the anchor hauled back over his shoulder (0.9 s, the arc drawn in frost), swung round: 14 and a push;
        // he turns (up to 30°) and the backhand's arc is drawn red at once, then he hauls it back the other way 0.6 s
        // later: 11
        out.add(BossAttack.of("anchor").anim(ANCHOR).timing(18, 22, 14).range(0, 6.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SWING_RANGE, SWING_HALF, FROST);
                        b.telegraphArc(level, SWING_RANGE - 2.0, SWING_HALF, FROST);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> swing(level, 14.0F, 1.0))
                .active((b, level, t, tick) -> {
                    if (tick == 2 && t != null) {
                        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F;
                        snapFacing(Mth.approachDegrees(getYRot(), yaw, 30.0F));
                    }
                    if (tick >= 2 && tick < 12 && tick % 2 == 0) {
                        b.telegraphArc(level, SWING_RANGE, SWING_HALF, RED);
                        b.telegraphArc(level, SWING_RANGE - 2.0, SWING_HALF, RED);
                    }
                    if (tick == 12) {
                        swing(level, 11.0F, 0.8);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 7.0 ? "breath" : "hurl");
                    }
                })
                .build());
        // throw: the anchor whirled round his head on its chain (1.2 s; the line drawn in frost follows you slowly,
        // then locks and turns red 0.5 s before), let fly: it crosses the line in 0.5 s (12 to whoever it meets), bites
        // at the end (8 in r 2, the ring drawn while it flies), lies there 0.3 s with the way back drawn red, then the
        // chain drags it back to him along the line in 0.7 s: 10, slowed and hauled toward him
        out.add(BossAttack.of("throw").anim(THROW).timing(24, 36, 14).range(4.0, 18.0).cooldown(110).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    throwLen = lineLength(level, THROW_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 14) {
                        turnToward(t, 4.0F);
                        throwLen = lineLength(level, THROW_MAX);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), throwLen, THROW_HALF, tick < 14 ? FROST : RED);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.4F, 0.6F + tick * 0.03F);
                    }
                    double a = tick * 0.6;
                    level.sendParticles(CHAIN_DUST, getX() + Math.cos(a) * 1.6, getY() + 4.4, getZ() + Math.sin(a) * 1.6, 1, 0, 0, 0, 0);
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    b.addEffect(anchorThrow(position(), forward(), throwLen));
                })
                .build());
        // spikes: the anchor raised high and driven into the deck (1.0 s); lines of ice (3, phase 2 five) are marked
        // from the start, fanning out from him (one at you), red for the last 0.4 s; the spikes burst along each line
        // one block a tick: 12 and a lift (once)
        out.add(BossAttack.of("spikes").anim(SPIKES).timing(20, 30, 14).range(0, 24.0).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planSpikes(level);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 12 ? RED : FROST;
                        for (List<Vec3> line : spikeLines) {
                            for (Vec3 p : line) {
                                level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (List<Vec3> line : spikeLines) {
                        b.addEffect(spikeRun(line));
                    }
                    iceBurst(level, ahead(1.5), 20, 0.6);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // breath: head thrown back, the rig filling him with cold (1.5 s; the cone drawn from 0.4 s, it follows you
        // slowly, red from 1.0 s), then a freezing cone through the cracked visor for 1 s: 4, Slowness II 3 s and
        // frost, four times (every 0.25 s) to whoever stays in it
        out.add(BossAttack.of("breath").anim(BREATH).timing(30, 24, 16).range(0, BREATH_RANGE).cooldown(170).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 20) {
                        turnToward(t, 3.0F);
                    }
                    if (tick >= 8 && tick % 3 == 0) {
                        drawCone(level, tick < 20 ? FROST : RED);
                    }
                    Vec3 v = visor();
                    level.sendParticles(ParticleTypes.SNOWFLAKE, v.x, v.y, v.z, 2, 1.2, 0.8, 1.2, -0.05);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 1.5F, 0.5F + tick * 0.02F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick < 20) {
                        breathe(level);
                        if (tick % 5 == 0) {
                            hitCone(level);
                        }
                    }
                    if (tick % 6 == 0 && tick < 20) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .build());
        // hurl: the anchor dragged low through the deck's ice (1.0 s) and heaved up: blocks of ice (2, phase 2 three)
        // fly onto rings (r 2) marked from the start, the first following you until 0.6 s, all red from then; they
        // land 0.9 s after the heave: 11, and each leaves a slippery patch of packed ice for 5 s
        out.add(BossAttack.of("hurl").anim(HURL).timing(20, 12, 14).range(5.0, 24.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planBlocks(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12 && t != null && !blockSpots.isEmpty()) {
                        Vec3 s = deck(level, t.getX(), t.getZ(), true);
                        if (s != null && flatDist(s, position()) > 2.5) {
                            blockSpots.set(0, s);
                        }
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 s : blockSpots) {
                            b.telegraphRing(level, s, BLOCK_R, tick < 12 ? FROST : RED);
                        }
                    }
                    if (tick % 4 == 0) {
                        iceBurst(level, ahead(1.2).add(0, -0.3, 0), 4, 0.5);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Vec3 s : blockSpots) {
                        b.addEffect(iceBlock(anchorHand().add(0, 1.5, 0), s, 18));
                    }
                    level.playSound(null, b, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // strays: the flare pistol raised straight up (1.0 s), the signal fired: two strays (more in co-op) climb out
        // of the ice onto the deck, unless three of his crew already stand there
        out.add(BossAttack.of("strays").anim(STRAYS).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(700).weight(4)
                .windup((b, level, t, tick) -> {
                    Vec3 m = pistol();
                    level.sendParticles(ParticleTypes.SMALL_FLAME, m.x, m.y + 1.5, m.z, 1, 0.1, 0.1, 0.1, 0.01);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.STRAY_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int k = 0; k < 12; k++) {
                        level.sendParticles(FLARE_DUST, getX(), getY() + 5 + k, getZ(), 2, 0.1, 0.2, 0.1, 0);
                    }
                    level.sendParticles(ParticleTypes.FIREWORK, getX(), getY() + 17, getZ(), 40, 1.0, 1.0, 1.0, 0.1);
                    level.playSound(null, b, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 3.0F, 0.7F);
                    if (crewCount(level) < 3) {
                        b.summon(level, EntityTypes.STRAY, 2, 4.0);
                    }
                })
                .build());
        // flare: the pistol levelled at you (0.8 s; the line drawn in orange follows you, red from 0.5 s), the shot:
        // the flare flies 1.6 blocks a tick down the line and bursts on the first one it meets or at the end: 9 and
        // fire 2 s in r 2
        out.add(BossAttack.of("flare").anim(FLARE).phaseTwo().timing(16, 10, 12).range(6.0, 26.0).cooldown(120).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    flareLen = lineLength(level, 24.0);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 5.0F);
                        flareLen = lineLength(level, 24.0);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), flareLen, 0.6, tick < 10 ? FLARE_DUST : RED);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 2.0F, 1.2F);
                    b.addEffect(flareShot(pistol(), forward(), flareLen));
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // blizzard: the rig's valves thrown wide (2.0 s, guarded; rings of frost grow round him, the steam roars), the
        // anchor slammed down: a wave to 14 (10, jump it); the deck ices over, the icicles start
        out.add(BossAttack.of("blizzard").anim(BLIZZARD).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.5F, 0.4F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, FROST);
                        double a = getRandom().nextDouble() * Math.PI * 2;
                        level.sendParticles(ParticleTypes.CLOUD, b.getX() + Math.cos(a) * 1.0, b.getY() + 4.0, b.getZ() + Math.sin(a) * 1.0,
                                0, Math.cos(a) * 0.3, 0.4, Math.sin(a) * 0.3, 0.3);
                    }
                    level.sendParticles(ParticleTypes.SNOWFLAKE, b.getX(), b.getY() + 3, b.getZ(), 4, 3.0, 2.0, 3.0, 0.02);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 2.0F, 0.4F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> startBlizzard(level))
                .build());
        // ram shock: he plants the anchor and braces, the ship's bell rings three times (1.5 s; the bow end of the deck
        // drawn red, a frost line across it), the ship rams the floe: a wave rolls the length of the deck from the bow
        // to the stern (0.7 blocks a tick, 9, a shove sternward, jump it), and a second one 1 s later
        out.add(BossAttack.of("ramshock").anim(RAMSHOCK).phaseTwo().timing(30, 40, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 10 == 0) {
                        Vec3 c = centre();
                        level.playSound(null, c.x, c.y, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                    if (tick % 3 == 0) {
                        drawFront(level, reach(), tick < 18 ? FROST : RED);
                    }
                    if (tick == 20) {
                        level.playSound(null, b, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> ram(level))
                .active((b, level, t, tick) -> {
                    if (tick == 20) {
                        ram(level);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void swing(ServerLevel level, float damage, double knock) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SWING_HALF));
        for (LivingEntity e : victims(level, position(), SWING_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SWING_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.5) {
                strike(level, e, damage, knock, 0.3);
            }
        }
        for (double a = -SWING_HALF; a <= SWING_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SWING_RANGE - 1.0));
            level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.2, p.z, 2, 0.1, 0.2, 0.1, 0.01);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /** How far a line along his facing runs over open deck (stopping at props, the bulwark, the arena's edge). */
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
            double fy = floorY(level, p.x, from.y + 0.5, p.z);
            double y = Double.isNaN(fy) ? from.y : fy;
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = p.add(side.scale(s * half));
                level.sendParticles(dust, q.x, y + 0.15, q.z, 1, 0, 0, 0, 0);
            }
            if (((int) d) % 2 == 0) {
                level.sendParticles(dust, p.x, y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /**
     * The thrown anchor: out along the line in 10 ticks (12 to whoever it meets, once), bites at the end (8 in r 2), lies
     * 6 ticks with the way back drawn red, then is dragged back to him in 14 ticks: 10, slowed and hauled in (once).
     */
    private Effect anchorThrow(Vec3 from, Vec3 dir, double len) {
        int[] t = {0};
        Set<UUID> outHit = new HashSet<>();
        Set<UUID> backHit = new HashSet<>();
        Vec3 end = from.add(dir.scale(len));
        Vec3[] pos = {from};
        return (boss, level) -> {
            if (!(boss instanceof FrostCommodore c)) {
                return true;
            }
            int k = t[0]++;
            double fy = floorY(level, end.x, from.y + 0.5, end.z);
            Vec3 endF = new Vec3(end.x, Double.isNaN(fy) ? from.y : fy, end.z);
            Vec3 hand = c.anchorHand();
            Vec3 at;
            if (k < 10) {
                at = from.lerp(endF, (k + 1) / 10.0);
                if (k % 2 == 0) {
                    boss.telegraphRing(level, endF, 2.0, FROST);
                }
            } else if (k < 16) {
                at = endF;
                if (k == 10) {
                    c.iceBurst(level, endF, 30, 1.0);
                    level.playSound(null, endF.x, endF.y, endF.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, endF.x, endF.y, endF.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                    for (LivingEntity e : boss.victims(level, endF, 3.0)) {
                        if (flatDist(e.position(), endF) <= 2.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - endF.y) < 2.5) {
                            c.strike(level, e, 8.0F, 0.4, 0.3);
                        }
                    }
                }
                if (k % 2 == 0) {
                    Vec3 back = hand.subtract(endF).multiply(1, 0, 1);
                    double bl = back.length();
                    if (bl > 1.0) {
                        c.drawLine(level, endF, back.normalize(), bl, THROW_HALF, RED);
                    }
                }
            } else {
                double f = Math.min(1.0, (k - 15) / 14.0);
                at = endF.lerp(new Vec3(hand.x, boss.getY(), hand.z), f);
                if (k % 4 == 0) {
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.2F, 0.7F);
                }
            }
            Vec3 prev = pos[0];
            pos[0] = at;
            // the anchor (ice and iron) and its chain back to his hand
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()), at.x, at.y + 0.6,
                    at.z, 4, 0.25, 0.25, 0.25, 0.0);
            level.sendParticles(FROST_BIG, at.x, at.y + 0.6, at.z, 2, 0.2, 0.2, 0.2, 0.0);
            Vec3 link = hand.subtract(at.add(0, 0.6, 0));
            double ll = link.length();
            for (double d = 0.5; d < ll; d += 0.8) {
                Vec3 q = at.add(0, 0.6, 0).add(link.scale(d / ll));
                level.sendParticles(CHAIN_DUST, q.x, q.y, q.z, 1, 0, 0, 0, 0);
            }
            if (k < 10 || k >= 16) {
                boolean back = k >= 16;
                for (LivingEntity e : boss.victims(level, at, 3.0)) {
                    double dist = distToSegment(e.position(), prev, at);
                    if (dist <= THROW_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        if (!back && outHit.add(e.getUUID())) {
                            c.strike(level, e, 12.0F, 0.5, 0.2);
                        } else if (back && backHit.add(e.getUUID())) {
                            Vec3 pull = boss.position().subtract(e.position()).multiply(1, 0, 1);
                            pull = pull.length() < 2.5 ? Vec3.ZERO : pull.normalize().scale(0.7);
                            c.shove(level, e, 10.0F, pull, 0.15);
                            chill(e, 40, 1, 30);
                        }
                    }
                }
            }
            if (k >= 29) {
                level.playSound(null, boss, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 1.2F);
                return true;
            }
            return false;
        };
    }

    private static double distToSegment(Vec3 p, Vec3 a, Vec3 b) {
        double dx = b.x - a.x;
        double dz = b.z - a.z;
        double l2 = dx * dx + dz * dz;
        double f = l2 < 1.0E-6 ? 0 : Mth.clamp(((p.x - a.x) * dx + (p.z - a.z) * dz) / l2, 0, 1);
        return Math.hypot(p.x - (a.x + dx * f), p.z - (a.z + dz * f));
    }

    /** Spike lines from him: 3 (phase 2: 5), the middle one at his facing, 25° apart, over open deck only. */
    private void planSpikes(ServerLevel level) {
        spikeLines.clear();
        int n = phase() == 2 ? 5 : 3;
        for (int i = 0; i < n; i++) {
            double a = (i - (n - 1) / 2.0) * 25.0;
            Vec3 dir = rotate(forward(), a);
            List<Vec3> line = new ArrayList<>();
            for (double d = 1.5; d <= SPIKE_MAX; d += 1.0) {
                Vec3 p = position().add(dir.scale(d));
                Vec3 s = deck(level, p.x, p.z, true);
                if (s == null) {
                    break;
                }
                line.add(s);
            }
            if (!line.isEmpty()) {
                spikeLines.add(line);
            }
        }
    }

    /** Spikes bursting along a line, one point a tick from him outward: 12 and a lift to whoever stands on it (once). */
    private Effect spikeRun(List<Vec3> line) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof FrostCommodore c)) {
                return true;
            }
            int k = t[0]++;
            if (k >= line.size()) {
                return true;
            }
            Vec3 p = line.get(k);
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()), p.x, p.y + 0.8,
                    p.z, 12, 0.25, 0.7, 0.25, 0.05);
            level.sendParticles(FROST_BIG, p.x, p.y + 1.2, p.z, 3, 0.15, 0.6, 0.15, 0.0);
            level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.6, p.z, 2, 0.2, 0.3, 0.2, 0.02);
            if (k % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.0F, 0.7F + k * 0.03F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.0 && hit.add(e.getUUID())) {
                    c.strike(level, e, 12.0F, 0.0, 0.5);
                }
            }
            return false;
        };
    }

    private void drawCone(ServerLevel level, DustParticleOptions dust) {
        for (double r = 3.5; r <= BREATH_RANGE; r += 3.25) {
            telegraphArc(level, r, BREATH_HALF, dust);
        }
        telegraphArc(level, BREATH_RANGE, BREATH_HALF, dust);
        for (int s = -1; s <= 1; s += 2) {
            Vec3 dir = rotate(forward(), s * BREATH_HALF);
            for (double d = 1.5; d <= BREATH_RANGE; d += 1.5) {
                Vec3 p = position().add(dir.scale(d));
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private void breathe(ServerLevel level) {
        Vec3 v = visor();
        for (int i = 0; i < 6; i++) {
            Vec3 dir = rotate(forward(), (getRandom().nextDouble() * 2 - 1) * BREATH_HALF);
            double sp = 0.45 + getRandom().nextDouble() * 0.35;
            level.sendParticles(ParticleTypes.SNOWFLAKE, v.x, v.y, v.z, 0, dir.x, -0.25, dir.z, sp);
        }
        for (double d = 2.0; d <= BREATH_RANGE; d += 2.0) {
            Vec3 p = ahead(d);
            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 1.0, p.z, 1, d * 0.2, 0.4, d * 0.2, 0.01);
        }
    }

    private void hitCone(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(BREATH_HALF));
        for (LivingEntity e : victims(level, position(), BREATH_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= BREATH_RANGE + e.getBbWidth() / 2 && (d < 1.5 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 4.0 && e.hurtServer(level, damageSources().mobAttack(this), 4.0F)) {
                chill(e, 60, 1, 35);
            }
        }
    }

    /** Ice block spots: the target, then the other players, then open deck near the target; at least 4 apart. */
    private void planBlocks(ServerLevel level, @Nullable LivingEntity target) {
        blockSpots.clear();
        int n = phase() == 2 ? 3 : 2;
        if (target != null) {
            tryBlock(level, target.getX(), target.getZ());
        }
        for (Player p : fighters(level)) {
            if (blockSpots.size() >= n) {
                break;
            }
            if (p != target) {
                tryBlock(level, p.getX(), p.getZ());
            }
        }
        Vec3 base = target != null ? target.position() : ahead(8.0);
        for (int tries = 0; tries < 40 && blockSpots.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 4.0 + getRandom().nextDouble() * 3.0;
            tryBlock(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d);
        }
        if (blockSpots.isEmpty()) {
            Vec3 a = ahead(6.0);
            blockSpots.add(new Vec3(a.x, getY(), a.z));
        }
    }

    private void tryBlock(ServerLevel level, double x, double z) {
        Vec3 s = deck(level, x, z, true);
        if (s == null || flatDist(s, position()) < 3.0) {
            return;
        }
        for (Vec3 o : blockSpots) {
            if (flatDist(o, s) < 4.0) {
                return;
            }
        }
        blockSpots.add(s);
    }

    /** A block of ice arcing onto its ring (red while it flies), shattering: 11 in r 2 and a slippery patch. */
    private Effect iceBlock(Vec3 from, Vec3 at, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                double f = (k + 1) / (double) delay;
                Vec3 p = from.lerp(at, f).add(0, Math.sin(f * Math.PI) * 5.0, 0);
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()), p.x, p.y, p.z,
                        6, 0.3, 0.3, 0.3, 0.0);
                level.sendParticles(FROST_BIG, p.x, p.y, p.z, 2, 0.25, 0.25, 0.25, 0.0);
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, BLOCK_R, RED);
                }
                return false;
            }
            if (boss instanceof FrostCommodore c) {
                c.iceBurst(level, at, 40, 1.0);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                for (LivingEntity e : boss.victims(level, at, BLOCK_R + 1)) {
                    if (flatDist(e.position(), at) <= BLOCK_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        Vec3 out = e.position().subtract(at).multiply(1, 0, 1);
                        out = out.lengthSqr() < 1.0E-4 ? Vec3.ZERO : out.normalize().scale(0.4);
                        c.shove(level, e, 11.0F, out, 0.25);
                    }
                }
                c.slipPatch(level, at);
            }
            return true;
        };
    }

    /** Packed ice over the plain full deck blocks of the 3 x 3 under {@code at}, each back in 5 s. */
    private void slipPatch(ServerLevel level, Vec3 at) {
        BlockPos c = BlockPos.containing(at.x, at.y - 0.5, at.z);
        int until = tickCount + PATCH_TICKS;
        List<BlockPos> placed = new ArrayList<>();
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                BlockPos p = c.offset(dx, 0, dz);
                if (!level.isLoaded(p) || temps.containsKey(p.asLong())) {
                    continue;
                }
                BlockState s = level.getBlockState(p);
                if (s.isAir() || s.hasBlockEntity() || level.getBlockEntity(p) != null || !s.isCollisionShapeFullBlock(level, p)
                        || !level.getBlockState(p.above()).isAir() || s.is(Blocks.PACKED_ICE) || s.is(Blocks.BLUE_ICE)
                        || s.is(Blocks.ICE)) {
                    continue;
                }
                temps.put(p.asLong(), new Temp(s, Blocks.PACKED_ICE.defaultBlockState(), until));
                level.setBlock(p, Blocks.PACKED_ICE.defaultBlockState(), 3);
                placed.add(p);
            }
        }
        if (placed.isEmpty()) {
            return;
        }
        int[] t = {0};
        addEffect((boss, lvl) -> {
            int k = t[0]++;
            if (k >= PATCH_TICKS) {
                return true;
            }
            if (k % 6 == 0) {
                for (BlockPos p : placed) {
                    lvl.sendParticles(ParticleTypes.SNOWFLAKE, p.getX() + 0.5, p.getY() + 1.1, p.getZ() + 0.5, 1, 0.3, 0.05, 0.3, 0.0);
                }
            }
            return false;
        });
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
            temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed(), 0));
        }
        staleTemps.clear();
        for (Long key : new ArrayList<>(temps.keySet())) {
            clearTemp(level, key);
        }
    }

    private int crewCount(ServerLevel level) {
        return level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 10, radius + 4),
                m -> m.isAlive() && m.entityTags().contains(MINION_TAG)).size();
    }

    private void discardCrew(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 8, 12, radius + 8),
                m -> m.isAlive() && m.entityTags().contains(MINION_TAG) && m.getType() == EntityTypes.STRAY)) {
            m.discard();
        }
    }

    /** The signal flare: 1.6 blocks a tick along the line; it bursts on the first one within 1 of it, or at the end. */
    private Effect flareShot(Vec3 from, Vec3 dir, double len) {
        double[] d = {0.5};
        return (boss, level) -> {
            if (!(boss instanceof FrostCommodore c)) {
                return true;
            }
            d[0] = Math.min(len, d[0] + 1.6);
            Vec3 p = from.add(dir.scale(d[0])).add(0, -d[0] * 0.05, 0);
            level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 3, 0.05, 0.05, 0.05, 0.01);
            level.sendParticles(FLARE_DUST, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0.0);
            boolean struck = false;
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (e.getBoundingBox().inflate(0.6).contains(p)) {
                    struck = true;
                    break;
                }
            }
            if (!struck && d[0] < len) {
                return false;
            }
            level.sendParticles(ParticleTypes.FIREWORK, p.x, p.y, p.z, 20, 0.6, 0.6, 0.6, 0.08);
            level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 20, 0.8, 0.5, 0.8, 0.04);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 1.5F, 1.0F);
            for (LivingEntity e : boss.victims(level, p, 3.0)) {
                if (e.position().add(0, e.getBbHeight() / 2, 0).distanceTo(p) <= 2.0 + e.getBbWidth() / 2) {
                    c.strike(level, e, 9.0F, 0.4, 0.2);
                    e.igniteForSeconds(2.0F);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ phase 3: blizzard

    private void startBlizzard(ServerLevel level) {
        blizzard = true;
        ramTimer = 140;
        icicleTimer = 40;
        addEffect(deckRing(position(), 14.0, 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("frost_commodore_blizzard"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(FROST_BIG, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.0);
        level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 3, getZ(), 80, 3.0, 2.0, 3.0, 0.1);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2, getZ(), 30, 2.0, 1.0, 2.0, 0.1);
        level.playSound(null, this, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    /** A jumpable ring of frost from {@code c}: it hits once whoever stands on the floor at its edge. */
    private Effect deckRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof FrostCommodore fc)) {
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
                level.sendParticles(FROST, x, (Double.isNaN(fy) ? c.y : fy) + 0.2, z, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && overFloor(level, e) < 0.6 && hit.add(e.getUUID())) {
                    fc.strike(level, e, damage, 0.6, 0.35);
                }
            }
            return rr >= max;
        };
    }

    /** The bow-side line across the deck, {@code along} blocks from the centre toward the bow. */
    private void drawFront(ServerLevel level, double along, DustParticleOptions dust) {
        Vec3 b = bow(level);
        Vec3 side = new Vec3(-b.z, 0, b.x);
        Vec3 base = centre().add(b.scale(along));
        for (double s = -radius; s <= radius; s += 1.0) {
            Vec3 p = base.add(side.scale(s));
            Vec3 f = deck(level, p.x, p.z, true);
            if (f != null) {
                level.sendParticles(dust, f.x, f.y + 0.15, f.z, 1, 0.1, 0, 0.1, 0);
            }
        }
    }

    private void ram(ServerLevel level) {
        Vec3 c = centre();
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        Vec3 b = bow(level);
        Vec3 tip = c.add(b.scale(reach()));
        iceBurst(level, tip, 60, 3.0);
        addEffect(deckWave(level));
        lurching = Math.max(lurching, (int) Math.ceil(2 * (reach() + 1) / 0.7) + 4);
    }

    /**
     * The lurch: a wave front across the whole deck rolling from the bow to the stern at 0.7 blocks a tick; whoever
     * stands on the floor where it passes takes 9 and a shove sternward (once).
     */
    private Effect deckWave(ServerLevel lvl0) {
        Vec3 b = bow(lvl0);
        Vec3 side = new Vec3(-b.z, 0, b.x);
        double[] front = {reach() + 1.0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof FrostCommodore fc)) {
                return true;
            }
            double f0 = front[0];
            double f1 = f0 - 0.7;
            front[0] = f1;
            Vec3 c = fc.centre();
            Vec3 base = c.add(b.scale(f1));
            for (double s = -fc.radius; s <= fc.radius; s += 1.0) {
                Vec3 p = base.add(side.scale(s));
                Vec3 f = fc.deck(level, p.x, p.z, true);
                if (f == null) {
                    continue;
                }
                level.sendParticles(ParticleTypes.CLOUD, f.x, f.y + 0.3, f.z, 1, 0.1, 0.15, 0.1, 0.01);
                if (((int) (s + 100)) % 2 == 0) {
                    level.sendParticles(FROST, f.x, f.y + 0.6, f.z, 1, 0.05, 0.1, 0.05, 0);
                    level.sendParticles(ParticleTypes.SNOWFLAKE, f.x, f.y + 0.4, f.z, 1, 0.1, 0.2, 0.1, 0.02);
                }
            }
            if (((int) (f1 / 0.7)) % 4 == 0) {
                level.playSound(null, base.x, base.y, base.z, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 1.2F, 0.5F);
            }
            for (Player p : fc.fighters(level)) {
                Vec3 to = p.position().subtract(c);
                double along = to.x * b.x + to.z * b.z;
                if (along <= f0 + 0.4 && along >= f1 - 0.6 && Math.abs(p.getY() - c.y) < 3.0 && overFloor(level, p) < 0.6
                        && hit.add(p.getUUID())) {
                    fc.shove(level, p, 9.0F, b.scale(-0.5), 0.3);
                }
            }
            return f1 <= -(fc.reach() + 1.0);
        };
    }

    /** One icicle: its ring (frost, red for the last 10 ticks) for 30 ticks, falling from the rigging, then the hit. */
    private Effect icicle(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, ICICLE_R, k >= 20 ? RED : FROST);
                }
                if (k >= 20) {
                    double y = at.y + 12 - (k - 20) * 1.2;
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.ICE.defaultBlockState()), at.x, y, at.z, 3,
                            0.1, 0.3, 0.1, 0.0);
                    level.sendParticles(FROST_BIG, at.x, y, at.z, 1, 0.05, 0.2, 0.05, 0.0);
                } else if (k % 5 == 0) {
                    level.sendParticles(ParticleTypes.SNOWFLAKE, at.x, at.y + 10, at.z, 2, 0.3, 0.3, 0.3, 0.0);
                }
                return false;
            }
            if (boss instanceof FrostCommodore c) {
                c.iceBurst(level, at, 24, 0.7);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.6F, 0.9F);
                for (LivingEntity e : boss.victims(level, at, ICICLE_R + 1)) {
                    if (flatDist(e.position(), at) <= ICICLE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        c.strike(level, e, 10.0F, 0.0, 0.0);
                        chill(e, 40, 0, 20);
                    }
                }
            }
            return true;
        };
    }

    /** A volley of icicles: one over the target, one over each other player (up to 3), the rest on open deck. */
    private void dropIcicles(ServerLevel level, @Nullable LivingEntity target) {
        int n = scaledCount(3);
        List<Vec3> spots = new ArrayList<>();
        List<LivingEntity> marks = new ArrayList<>();
        if (target != null) {
            marks.add(target);
        }
        int extra = 0;
        for (Player p : fighters(level)) {
            if (p != target && extra++ < 3) {
                marks.add(p);
            }
        }
        for (LivingEntity m : marks) {
            Vec3 s = deck(level, m.getX(), m.getZ(), true);
            if (s != null) {
                spots.add(s);
            }
        }
        Vec3 c = centre();
        double r = reach() - 1.0;
        for (int tries = 0; tries < 40 && spots.size() < n + Math.max(0, marks.size() - 1); tries++) {
            Vec3 s = deck(level, c.x + (getRandom().nextDouble() * 2 - 1) * r, c.z + (getRandom().nextDouble() * 2 - 1) * r, true);
            if (s == null) {
                continue;
            }
            boolean ok = true;
            for (Vec3 o : spots) {
                if (flatDist(o, s) < 3.5) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                spots.add(s);
            }
        }
        for (Vec3 s : spots) {
            addEffect(icicle(s));
        }
        level.playSound(null, c.x, c.y + 8, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 0.8F, 1.6F);
    }

    /** The blizzard's weather over the deck: snow, frost on the deck, and a mild chill on the players on it. */
    private void blizzardWeather(ServerLevel level) {
        Vec3 c = centre();
        double r = reach();
        if (tickCount % 2 == 0) {
            for (int i = 0; i < 8; i++) {
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                level.sendParticles(ParticleTypes.SNOWFLAKE, x, c.y + 1 + getRandom().nextDouble() * 6, z, 0, 0.3, -0.15, 0.1, 1.0);
            }
        }
        if (tickCount % 10 == 0) {
            for (int i = 0; i < 12; i++) {
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                Vec3 f = deck(level, x, z, true);
                if (f != null) {
                    level.sendParticles(SNOW, f.x, f.y + 0.1, f.z, 2, 0.4, 0, 0.4, 0);
                }
            }
        }
        if (tickCount % 5 == 0) {
            for (Player p : fighters(level)) {
                if (flatDist(p.position(), c) <= radius + 1 && Math.abs(p.getY() - c.y) < 4.0) {
                    if (p.canFreeze()) {
                        p.setTicksFrozen(Math.max(p.getTicksFrozen(), Math.min(120, p.getTicksFrozen() + 14)));
                    }
                    if (tickCount % 20 == 0) {
                        p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0, true, false));
                    }
                }
            }
        }
        if (tickCount % 120 == 0) {
            level.playSound(null, c.x, c.y + 4, c.z, SoundEvents.ELYTRA_FLYING, SoundSource.HOSTILE, 0.6F, 0.5F);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0.02);
            level.playSound(null, this, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 0.8F, 1.6F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardCrew(level);
        lurching = 0;
    }

    /** Back to the first phase (the fight was reset): the blizzard lifts, the ice goes, base speed. */
    private void resetForm(ServerLevel level) {
        blizzard = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("frost_commodore_blizzard"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("frost_commodore_wrath"));
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
        if (lurching > 0) {
            lurching--;
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
        if (phase() == 1 && blizzard) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!blizzard && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "blizzard");
            } else if (blizzard && --ramTimer <= 0) {
                ramTimer = Math.max(160, (int) Math.round(RAM_EVERY * cooldownScale()));
                chain(level, "ramshock");
            }
        }
        // phase 3: the blizzard's weather and the icicles (they wait while the ship lurches)
        if (blizzard && phase() == 2 && anyone) {
            blizzardWeather(level);
            cur = currentAttack();
            boolean busy = cur != null && ("ramshock".equals(cur.name) || "blizzard".equals(cur.name));
            if (fighting && !busy && lurching == 0 && guard == 0 && --icicleTimer <= 0) {
                icicleTimer = Math.max(34, (int) Math.round(ICICLE_EVERY * cooldownScale()));
                dropIcicles(level, target);
            }
        }
        // ambience: cold steam from the rig's vent pipes, the visor's glow, frost falling off him
        if (tickCount % 3 == 0) {
            Vec3 f = forward();
            Vec3 back = position().subtract(f.scale(0.7));
            Vec3 side = new Vec3(-f.z, 0, f.x);
            for (int s = -1; s <= 1; s += 2) {
                Vec3 p = back.add(side.scale(s * 0.3));
                level.sendParticles(ParticleTypes.CLOUD, p.x, getY() + 4.1, p.z, 1, 0.05, 0.1, 0.05, 0.01);
            }
        }
        if (tickCount % 10 == 0) {
            level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 2.0, getZ(), 1, 0.6, 1.0, 0.6, 0.0);
        }
        if (tickCount % 90 == 0) {
            level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 0.8F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("frost_commodore_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take it back where it would carry them off the deck
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 4, getZ(), 40, 1.0, 1.0, 1.0, 0.1);
        level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 3, getZ(), 60, 2.0, 1.5, 2.0, 0.1);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 2, getZ(), 100, 1.5, 2.0, 1.5, 0.05);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 3, getZ(), 50, 1.0, 1.5, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0F, 0.4F);
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
            output.putLong("CommodoreCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("CommodoreRadius", radius);
        output.putBoolean("CommodoreBlizzard", blizzard);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("CommodoreBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("CommodoreCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("CommodoreRadius", 18);
        blizzard = input.getBooleanOr("CommodoreBlizzard", false) && phase() == 2;
        bow = null;
        staleTemps.clear();
        input.read("CommodoreBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
    }
}
