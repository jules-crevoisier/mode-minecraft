package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
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
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.StranglerQueen.CAGES;
import static com.brasshaven.generated.MobAnims.StranglerQueen.CANOPY;
import static com.brasshaven.generated.MobAnims.StranglerQueen.COMBO;
import static com.brasshaven.generated.MobAnims.StranglerQueen.HARVEST;
import static com.brasshaven.generated.MobAnims.StranglerQueen.LASH;
import static com.brasshaven.generated.MobAnims.StranglerQueen.OVERGROWTH;
import static com.brasshaven.generated.MobAnims.StranglerQueen.PLUNGE;
import static com.brasshaven.generated.MobAnims.StranglerQueen.POLLEN;
import static com.brasshaven.generated.MobAnims.StranglerQueen.ROAR;
import static com.brasshaven.generated.MobAnims.StranglerQueen.ROOTLINE;
import static com.brasshaven.generated.MobAnims.StranglerQueen.ROOTRING;
import static com.brasshaven.generated.MobAnims.StranglerQueen.SNARE;
import static com.brasshaven.generated.MobAnims.StranglerQueen.STAGGER;
import static com.brasshaven.generated.MobAnims.StranglerQueen.SWING;
import static com.brasshaven.generated.MobAnims.StranglerQueen.THORNS;
import static com.brasshaven.generated.MobAnims.StranglerQueen.WHIPSTORM;

/**
 * La Reine-figuier étrangleur (The Strangler Fig Queen), the lost queen of the Canopy Temple-City: a 6-block woman of
 * woven roots and carved jade rising from a skirt of strangler-fig roots, a crown of orchids, a thorned root-whip for a
 * left arm and a jade macuahuitl in her right hand. She waits on the temple's summit under the broken brass sun-disc,
 * 66 blocks over the jungle.
 * <p>A deliberately hard fight: 620 health, armour 12, poise 115, hits of 6 to 18. Three phases:
 * <ul>
 *     <li>Phase 1: the <b>lash</b> (a whip crack 11 blocks down a line), the <b>macuahuitl combo</b> (forehand,
 *     backhand), <b>root lines</b> (roots burst along three marked lines from her outward), <b>root rings</b> (bands
 *     round her erupt from the inside out: stand between them), the <b>pollen cloud</b> (drowsiness builds while you
 *     stand in it: leave it), the <b>whip-swing</b> (she casts the whip and hauls herself through you) and the
 *     <b>thorns</b> (anti-hug).</li>
 *     <li>Phase 2 (a roar at 65%): faster, combos, a third overhead blow, the <b>whip-storm</b> (two sweeps round her:
 *     hug her or stand clear), the <b>snare</b> (the whip catches and hauls you in for a macuahuitl blow) and, at once
 *     and then every 40 s, the <b>canopy</b>: she springs up into the sun-disc (untouchable), drops jaguar spirits
 *     (few, more in co-op) and seed-bombs on marked players, then plunges onto the one she marks. Kill the spirits and
 *     she falls early, exposed.</li>
 *     <li>Phase 3 (at 30%): she sinks into her roots (invulnerable) and the <b>overgrowth</b> erupts; every 12 s
 *     <b>root cages</b> close on marked spots round every player (real, temporary mangrove roots): step out before
 *     they snap shut, or break out, because 2.5 s later she <b>harvests</b> a full cage with her macuahuitl.</li>
 * </ul>
 * The arena is a summit: near the parapet no hit throws a player outward and lift is capped (see {@link #strike}); her
 * leaps and swings never land outside the floor. Every block she places (the cages) is temporary: removed when it
 * expires, when the fight resets or the arena empties, when she dies or is removed, and on the first tick after a
 * reload.
 */
public class StranglerQueen extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.8F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double LASH_LEN = 11.0;
    private static final double MACA_RANGE = 5.5;
    private static final double MACA_HALF = 75;
    private static final double CLOUD_R = 4.5;
    private static final int CLOUD_LIFE = 160;
    private static final int CANOPY_EVERY = 800;
    private static final int CAGE_EVERY = 240;
    private static final int CAGE_LIFE = 140;
    private static final int MAX_CAGE_BLOCKS = 320;
    /** Inside this radius from the centre a push is left alone (only capped); beyond it, the summit's edge rules. */
    private static final double EDGE_SAFE = 9.0;
    private static final DustParticleOptions THORN = new DustParticleOptions(0xD6C8A0, 1.3F);
    private static final DustParticleOptions JADE = new DustParticleOptions(0x5CE0A0, 1.3F);
    private static final DustParticleOptions ROOTDUST = new DustParticleOptions(0x6A4E36, 1.6F);
    private static final DustParticleOptions POLLEN_DUST = new DustParticleOptions(0xF4DC5A, 1.4F);
    private static final DustParticleOptions ORCHID = new DustParticleOptions(0xE25CB0, 1.2F);

    private @Nullable Vec3 centre;
    private int radius = 18;
    /** Phase 3 has started (the overgrowth erupted). */
    private boolean overgrown;
    private int guard;
    private int roarUntil = -1;
    private int canopyTimer = 10;
    private int cageTimer = 60;
    private int harvestAt = -1;
    private int exposedUntil = -1;
    /** Up in the sun-disc: hidden from blows, no gravity. */
    private boolean perched;
    private boolean exposedDrop;
    private @Nullable Vec3 perch;
    private @Nullable Vec3 lockedSpot;
    private @Nullable LivingEntity snared;
    private final List<UUID> spirits = new ArrayList<>();
    private final List<Vec3> spots = new ArrayList<>();
    private final List<Vec3> lines = new ArrayList<>();
    private final List<LivingEntity> marked = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable Vec3 swingFrom;
    private @Nullable Vec3 swingTo;
    /** Root cages: every block placed (into air) and the tick it goes; and the cages' centres with their end tick. */
    private final Map<BlockPos, Integer> cageBlocks = new HashMap<>();
    private final Map<Vec3, Integer> cages = new LinkedHashMap<>();
    private boolean staleCages;

    public StranglerQueen(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 620.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.StranglerQueen.TICKS;
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
        return 115.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 5.0;
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
        perch = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Usable floor radius round the seal: the summit is 15 blocks to its nearest parapet. */
    private double reach() {
        return Math.max(6.0, Math.min(14.0, radius - 3.0));
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

    /** A standing spot on the summit floor at (x, z) with room for her above, or null. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 2.5) {
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

    /** {@code p} pulled inside the summit (at most {@code reach() - margin} from the centre), at floor height. */
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
    private Vec3 landingSpot(ServerLevel level, Vec3 want) {
        Vec3 p = clampToArena(want, 1.5);
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

    private void face(@Nullable LivingEntity t) {
        if (t != null) {
            snapFacing((float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F);
        }
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

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 12, radius + 4),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    // ------------------------------------------------------------------ fairness on the summit

    /**
     * Every hit of hers (moves, waves, the NG+ shockwave) comes through here. Pushes are capped at 1.4; beyond 9 blocks
     * from the centre (and wherever the floor ends 2 blocks along the push) the outward part is dropped and the rest
     * halved, and lift is capped: she never throws a player off the summit.
     */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.4, knockback));
            push = tame(level, e, push);
        }
        if (flatDist(e.position(), centre()) > EDGE_SAFE) {
            lift = Math.min(lift, 0.35);
        }
        if (push.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    /** A horizontal push made safe for the summit (see {@link #strike}). */
    private Vec3 tame(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 radial = e.position().subtract(centre()).multiply(1, 0, 1);
        double r = radial.length();
        Vec3 dir = push.normalize();
        Vec3 probe = e.position().add(dir.scale(2.0));
        boolean drop = Double.isNaN(floorY(level, probe.x, e.getY(), probe.z))
                || floorY(level, probe.x, e.getY(), probe.z) < e.getY() - 2.5;
        if ((r > EDGE_SAFE || drop) && r > 0.1) {
            Vec3 n = radial.scale(1.0 / r);
            double out = push.dot(n);
            if (out > 0) {
                push = push.subtract(n.scale(out));
            }
            push = push.scale(0.5);
            if (drop) {
                push = Vec3.ZERO;
            }
        }
        return push;
    }

    /** Draws {@code e} toward {@code to} (inward pulls only ever bring players onto the floor). */
    private static void pull(LivingEntity e, Vec3 to, double max) {
        Vec3 d = to.subtract(e.position()).multiply(1, 0, 1);
        double len = d.length();
        if (len < 0.3) {
            return;
        }
        Vec3 v = d.normalize().scale(Math.min(max, 0.25 + len * 0.18));
        e.setDeltaMovement(v.x, 0.25, v.z);
        e.hurtMarked = true;
    }

    private static BlockParticleOption rootBlock() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.ROOTED_DIRT.defaultBlockState());
    }

    private static BlockParticleOption mangroveBlock() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MANGROVE_ROOTS.defaultBlockState());
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // lash: the whip drawn back over her left shoulder and coiled (0.8 s, the line drawn in thorn dust), then
        // cracked 11 blocks straight ahead: 14, and it drags you a little toward her
        out.add(BossAttack.of("lash").anim(LASH).timing(16, 4, 14).range(0, 12.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= LASH_LEN; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(THORN, p.x, p.y + 0.15, p.z, 1, 0.15, 0, 0.15, 0);
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.VINE_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.lashBlow(level, LASH_LEN, 1.1, 14.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "combo" : "snare");
                    }
                })
                .build());
        // macuahuitl combo: raised over her right shoulder (0.7 s, the arc drawn in jade), a forehand cut, a backhand
        // 0.5 s later after a turn toward you; phase 2 adds an overhead blow down a line 0.5 s after that
        out.add(BossAttack.of("combo").anim(COMBO).timing(14, 24, 14).range(0, 6.5).cooldown(70).weight(11)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, MACA_RANGE, MACA_HALF, JADE);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.CREAKING_ACTIVATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    if (tick == 0 || tick == 10) {
                        q.macaCut(level, 13.0F);
                    }
                    if (tick == 3) {
                        q.turnToward(t, 30.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, MACA_RANGE, MACA_HALF, JADE);
                    }
                    if (b.phase() == 2) {
                        if (tick == 12) {
                            q.turnToward(t, 25.0F);
                        }
                        if (tick > 12 && tick < 20 && tick % 2 == 0) {
                            for (double d = 1.0; d <= 6.5; d += 1.0) {
                                Vec3 p = b.ahead(d);
                                level.sendParticles(JADE, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                        if (tick == 20) {
                            b.hitLine(level, 6.5, 1.3, 16.0F, 0.6);
                            Vec3 p = b.ahead(4.5);
                            level.sendParticles(rootBlock(), p.x, p.y + 0.3, p.z, 40, 1.0, 0.3, 1.0, 0.1);
                            level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.7F);
                        }
                    }
                })
                .build());
        // root lines: the whip plunged into the floor (1.0 s; the lines drawn in root dust, three or five fanned toward
        // you); roots burst along them from her outward, 1.2 blocks a tick: 12 and a toss
        out.add(BossAttack.of("rootline").anim(ROOTLINE).timing(20, 20, 14).range(0, 20.0).cooldown(130).weight(9)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    q.planLines();
                    if (tick % 2 == 0) {
                        for (Vec3 dir : q.lines) {
                            for (double d = 2.0; d <= q.lineLength(); d += 1.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(ROOTDUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.planLines();
                        for (Vec3 dir : q.lines) {
                            b.addEffect(q.rootRun(b.position(), dir, q.lineLength(), 1.2, 12.0F));
                        }
                        level.playSound(null, b, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .build());
        // root rings: the macuahuitl lifted in both hands (1.1 s; bands at 4, 8 and 12 drawn round her), driven into
        // the floor: the bands erupt one after another from the inside out (stand between them). Phase 2: back in again
        out.add(BossAttack.of("rootring").anim(ROOTRING).timing(22, 30, 14).range(0, 14.0).cooldown(200).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof StranglerQueen q) {
                        for (double r : q.bands()) {
                            b.telegraphRing(level, b.position(), r - 0.9, ROOTDUST);
                            b.telegraphRing(level, b.position(), r + 0.9, ROOTDUST);
                        }
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.CREAKING_HEART_HURT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 3.0F, 0.5F);
                    double[] bands = q.bands();
                    for (int i = 0; i < bands.length; i++) {
                        b.addEffect(q.rootBand(b.position(), bands[i], i * 12, 11.0F));
                        if (b.phase() == 2) {
                            b.addEffect(q.rootBand(b.position(), bands[i], 34 + (bands.length - 1 - i) * 12, 11.0F));
                        }
                    }
                })
                .build());
        // pollen: she bows and shakes her orchid crown (0.9 s, pollen pouring off it), then flings a cloud onto the
        // target (phase 2: onto every player, plus strays). Staying in a cloud makes you drowsy: slower and slower,
        // then you nod off (Blindness, 4). Leave it
        out.add(BossAttack.of("pollen").anim(POLLEN).timing(18, 10, 14).range(0, 22.0).cooldown(220).weight(7)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(POLLEN_DUST, b.getX(), b.getY() + 5.6, b.getZ(), 4, 0.8, 0.4, 0.8, 0.02);
                    level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, b.getX(), b.getY() + 5.8, b.getZ(), 2, 0.8, 0.3, 0.8, 0);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BEE_POLLINATE, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                    if (b instanceof StranglerQueen q && tick < 14) {
                        q.pickCloudSpots(level, t);
                    }
                    if (tick % 3 == 0 && b instanceof StranglerQueen q) {
                        for (Vec3 p : q.spots) {
                            b.telegraphRing(level, p, CLOUD_R, POLLEN_DUST);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.SPORE_BLOSSOM_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    for (Vec3 p : q.spots) {
                        b.addEffect(q.pollenCloud(p, CLOUD_R, CLOUD_LIFE));
                    }
                    q.spots.clear();
                })
                .build());
        // whip-swing: the whip flung up and ahead to catch a hold near you (0.8 s, the line to it drawn), then she hauls
        // herself along it in 9 ticks: 15 to whoever stands in her path
        out.add(BossAttack.of("swing").anim(SWING).timing(16, 12, 14).range(7.0, 22.0).cooldown(120).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && t != null && b instanceof StranglerQueen q) {
                        Vec3 to = q.clampToArena(t.position(), 1.5);
                        double len = flatDist(b.position(), to);
                        for (double d = 1.5; d < len; d += 1.0) {
                            Vec3 p = b.position().lerp(to, d / len);
                            level.sendParticles(THORN, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                        b.telegraphRing(level, to, 1.5, JADE);
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.VINE_PLACE, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        Vec3 want = t != null ? t.position() : b.ahead(10);
                        q.swingFrom = b.position();
                        q.swingTo = q.landingSpot(level, want);
                        q.faceToward(q.swingTo);
                        level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.swingStep(level, tick, 15.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.0 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "combo");
                    }
                })
                .build());
        // thorns: she draws into her roots (0.6 s, a thorn ring at her feet), then thorns burst all round her: anti-hug.
        // Phase 2: a ring of thorns runs on to 8 (jump it)
        out.add(BossAttack.of("thorns").anim(THORNS).timing(12, 3, 12).range(0, 4.5).cooldown(70).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, THORN);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.5, 11.0F, 1.0, 0.3);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 8, 0.5, 7.0F, THORN));
                    }
                    level.sendParticles(mangroveBlock(), b.getX(), b.getY() + 0.6, b.getZ(), 60, 2.2, 0.4, 2.2, 0.1);
                    level.playSound(null, b, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // whip-storm: the whip whirled overhead (0.9 s; the outer ring at 9 in thorn dust, a safe disc at 2.5 in jade),
        // then swept round her twice: 14 between 2.5 and 9 each turn
        out.add(BossAttack.of("whipstorm").anim(WHIPSTORM).phaseTwo().timing(18, 16, 14).range(0, 9.0).cooldown(160)
                .weight(8).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 9.0, THORN);
                        b.telegraphRing(level, b.position(), 2.5, JADE);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 8) {
                        for (LivingEntity e : b.victims(level, b.position(), 10)) {
                            double d = flatDist(e.position(), b.position());
                            if (d >= 2.5 - e.getBbWidth() / 2 && d <= 9.0 + e.getBbWidth() / 2 && e.getY() - b.getY() < 2.5) {
                                b.strike(level, e, 14.0F, 0.8, 0.2);
                            }
                        }
                        for (int a = 0; a < 360; a += 10) {
                            Vec3 p = b.position().add(rotate(new Vec3(0, 0, 1), a).scale(6.5));
                            level.sendParticles(THORN, p.x, p.y + 0.8, p.z, 2, 0.6, 0.2, 0.6, 0.02);
                        }
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                    } else if (tick < 8 && tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 9.0, THORN);
                    }
                })
                .build());
        // snare: the whip cast low ahead (0.9 s, a narrow line 12 long); the first player it catches takes 8, is hauled
        // in and held, and at 1.5 s the macuahuitl comes down in front of her (16): break away to the side
        out.add(BossAttack.of("snare").anim(SNARE).phaseTwo().timing(18, 16, 14).range(3.0, 12.0).cooldown(180).weight(7)
                .start((b, level, t, tick) -> snared = null)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 12.0; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(THORN, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.castSnare(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    if (tick < 6 && q.snared != null && q.snared.isAlive()) {
                        pull(q.snared, b.ahead(2.5), 0.9);
                    }
                    if (tick > 3 && tick < 12 && tick % 2 == 0) {
                        b.telegraphArc(level, 4.5, 50, JADE);
                    }
                    if (tick == 12) {
                        b.hitArc(level, 4.5, 50, 16.0F, 0.6);
                        Vec3 p = b.ahead(3.0);
                        level.sendParticles(rootBlock(), p.x, p.y + 0.3, p.z, 30, 0.8, 0.3, 0.8, 0.1);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.7F);
                        q.snared = null;
                    }
                })
                .build());
        // canopy: never rolled; at the start of phase 2 and every 40 s she crouches into her roots (1.0 s, roots coil
        // round her), springs up into the sun-disc and clings there, untouchable, for 9 s: jaguar spirits drop onto the
        // summit (few, more in co-op) and three volleys of seed-bombs fall on marked players. Kill the spirits and she
        // falls early, exposed. Then she plunges
        out.add(BossAttack.of("canopy").anim(CANOPY).phaseTwo().timing(20, 180, 4).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    exposedDrop = false;
                    level.playSound(null, b, SoundEvents.CREAKING_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(mangroveBlock(), b.getX(), b.getY() + 0.5, b.getZ(), 6, 1.6, 0.3, 1.6, 0.05);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.5, ROOTDUST);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.climb(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.canopyStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> b.chain(level, "plunge"))
                .build());
        // plunge: crouched on the disc (1.2 s) while a ring follows her prey, then locks for the last half second; she
        // dives onto it: 17 in 3.5 and a ring of roots (8, jump it). After an early fall she is exposed for 4 s
        out.add(BossAttack.of("plunge").anim(PLUNGE).phaseTwo().timing(24, 4, 22).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> lockedSpot = null)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    if (tick <= 14 || q.lockedSpot == null) {
                        LivingEntity aim = t != null && t.isAlive() ? t : null;
                        q.lockedSpot = q.landingSpot(level, aim != null ? aim.position() : q.centre());
                    }
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, q.lockedSpot, 3.5, tick > 14 ? JADE : THORN);
                        if (q.perched) {
                            level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, b.getX(), b.getY(), b.getZ(), 3, 0.5, 0.2, 0.5, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.plungeDown(level);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // overgrowth: she sinks into her roots, arms raised, the crown blooming (1.5 s, invulnerable; roots heave over
        // the whole summit), then the summit erupts: a ring of roots (12, jump it), +12% speed
        out.add(BossAttack.of("overgrowth").anim(OVERGROWTH).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 52;
                    level.playSound(null, b, SoundEvents.CREAKING_HEART_SPAWN, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    Vec3 c = q.centre();
                    double r = q.reach();
                    level.sendParticles(rootBlock(), c.x, c.y + 0.2, c.z, 10, r * 0.5, 0.1, r * 0.5, 0.05);
                    level.sendParticles(ORCHID, b.getX(), b.getY() + 5.6, b.getZ(), 3, 0.8, 0.4, 0.8, 0.02);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.4, ROOTDUST);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.overgrow(level);
                    }
                })
                .build());
        // cages: both hands raised (1.2 s): a ring of thorns follows every player for 0.6 s, then locks for 0.6 s; the
        // cages snap shut on the locked spots (real mangrove roots, 7 s). Whoever is caught takes 6 and is strangled
        out.add(BossAttack.of("cages").anim(CAGES).phaseTwo().timing(24, 16, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.pickCageTargets(level);
                    }
                    level.playSound(null, b, SoundEvents.CREAKING_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StranglerQueen q)) {
                        return;
                    }
                    if (tick < 12) {
                        for (int i = 0; i < q.marked.size() && i < q.spots.size(); i++) {
                            LivingEntity e = q.marked.get(i);
                            if (e.isAlive()) {
                                q.spots.set(i, new Vec3(Mth.floor(e.getX()) + 0.5, q.centre().y, Mth.floor(e.getZ()) + 0.5));
                            }
                        }
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 p : q.spots) {
                            b.telegraphRing(level, p, 1.6, tick < 12 ? THORN : JADE);
                            if (tick >= 12) {
                                level.sendParticles(mangroveBlock(), p.x, p.y + 0.2, p.z, 3, 0.8, 0.1, 0.8, 0.02);
                            }
                        }
                    }
                    if (tick == 12) {
                        level.playSound(null, b, SoundEvents.MANGROVE_ROOTS_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.closeCages(level);
                    }
                })
                .build());
        // harvest: never rolled; 2.5 s after a cage closed on someone she crouches toward it (1.0 s, a ring round it),
        // leaps onto it and crushes it: 18 within 2.5 of the cage
        out.add(BossAttack.of("harvest").anim(HARVEST).phaseTwo().timing(20, 4, 22).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q && q.lockedSpot != null) {
                        q.faceToward(q.lockedSpot);
                        if (tick % 2 == 0) {
                            b.telegraphRing(level, q.lockedSpot, 2.5, JADE);
                            b.telegraphRing(level, q.lockedSpot, 1.2, THORN);
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StranglerQueen q) {
                        q.harvest(level);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void lashBlow(ServerLevel level, double len, double half, float damage) {
        Vec3 fwd = forward();
        for (LivingEntity e : victims(level, position(), len + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= len && side <= half + e.getBbWidth() / 2 && e.getY() - getY() < 3) {
                strike(level, e, damage, 0.0, 0.1);
                pull(e, position().add(fwd.scale(Math.max(3.0, along - 3.0))), 0.6);
            }
        }
        for (double d = 1.5; d <= len; d += 0.7) {
            Vec3 p = ahead(d);
            level.sendParticles(THORN, p.x, p.y + 1.0, p.z, 2, 0.1, 0.1, 0.1, 0.02);
        }
        Vec3 tip = ahead(len);
        level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 1.0, tip.z, 14, 0.3, 0.3, 0.3, 0.3);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 1.4F);
        level.playSound(null, tip.x, tip.y, tip.z, SoundEvents.PLAYER_ATTACK_CRIT, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    private void macaCut(ServerLevel level, float damage) {
        for (LivingEntity e : arcVictims(level, MACA_RANGE, MACA_HALF)) {
            strike(level, e, damage, 1.0, 0.2);
        }
        for (double a = -MACA_HALF; a <= MACA_HALF; a += 12) {
            Vec3 p = position().add(rotate(forward(), a).scale(MACA_RANGE - 1.2));
            level.sendParticles(JADE, p.x, p.y + 1.6, p.z, 2, 0.2, 0.3, 0.2, 0.02);
        }
        Vec3 c = ahead(3.0);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.6, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.CREAKING_ATTACK, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    private List<LivingEntity> arcVictims(ServerLevel level, double range, double halfAngle) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(halfAngle));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : victims(level, position(), range + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                out.add(e);
            }
        }
        return out;
    }

    private double lineLength() {
        return Math.min(18.0, reach() * 2);
    }

    /** The root lines: three (phase 2: five) fanned round her facing. */
    private void planLines() {
        lines.clear();
        double[] fan = phase() == 2 ? new double[] {-36, -18, 0, 18, 36} : new double[] {-25, 0, 25};
        for (double a : fan) {
            lines.add(rotate(forward(), a));
        }
    }

    /** Roots bursting along a line from {@code from}, {@code speed} blocks a tick; 12 and a toss once per victim. */
    private Effect rootRun(Vec3 from, Vec3 dir, double len, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] d = {1.5};
        return (boss, level) -> {
            Vec3 p = from.add(dir.scale(d[0]));
            if (boss instanceof StranglerQueen q && flatDist(p, q.centre()) > q.reach() + 1.5) {
                return true;                                     // the summit ends here
            }
            level.sendParticles(rootBlock(), p.x, p.y + 0.4, p.z, 8, 0.3, 0.6, 0.3, 0.1);
            level.sendParticles(mangroveBlock(), p.x, p.y + 1.2, p.z, 4, 0.2, 0.8, 0.2, 0.05);
            if (((int) (d[0] * 10)) % 30 < 12) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.ROOTS_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.1 + e.getBbWidth() / 2 && e.getY() - p.y < 2.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.0, 0.55);
                }
            }
            d[0] += speed;
            return d[0] > len;
        };
    }

    private double[] bands() {
        double r = reach();
        return r >= 12.5 ? new double[] {4.0, 8.0, 12.0} : new double[] {3.5, 6.5, Math.max(8.0, r - 1.0)};
    }

    /** A band of roots round {@code c} at radius {@code r} (±0.9): it flashes for 8 ticks, then erupts after {@code delay}. */
    private Effect rootBand(Vec3 c, double r, int delay, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k >= delay - 8 && k % 2 == 0) {
                    boss.telegraphRing(level, c, r - 0.9, THORN);
                    boss.telegraphRing(level, c, r + 0.9, THORN);
                }
                return false;
            }
            int n = Math.max(12, (int) (r * 5));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(rootBlock(), c.x + Math.cos(a) * r, c.y + 0.5, c.z + Math.sin(a) * r, 2, 0.3, 0.6, 0.3, 0.1);
            }
            level.playSound(null, c.x, c.y, c.z, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F + (float) r * 0.03F);
            for (LivingEntity e : boss.victims(level, c, r + 2)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - r) <= 0.9 + e.getBbWidth() / 2 && e.getY() - c.y < 2.5) {
                    boss.strike(level, e, damage, 0.0, 0.6);
                }
            }
            return true;
        };
    }

    /** Cloud spots: on the target (phase 1), on every player (phase 2, up to 4), plus 1 (phase 3: 2) strays. */
    private void pickCloudSpots(ServerLevel level, @Nullable LivingEntity target) {
        spots.clear();
        if (target != null) {
            spots.add(clampToArena(target.position(), 1.0));
        }
        if (phase() == 2) {
            for (Player p : fighters(level)) {
                if (p != target && spots.size() < 4) {
                    spots.add(clampToArena(p.position(), 1.0));
                }
            }
            int strays = overgrown ? 2 : 1;
            java.util.Random r = new java.util.Random(getUUID().getLeastSignificantBits() + tickCount / 60);
            for (int i = 0, tries = 0; i < strays && tries < 20; tries++) {
                double a = r.nextDouble() * Math.PI * 2;
                double d = 3 + r.nextDouble() * Math.max(2, reach() - 4);
                Vec3 p = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
                boolean ok = true;
                for (Vec3 s : spots) {
                    ok &= flatDist(s, p) >= CLOUD_R * 1.5;
                }
                if (ok) {
                    spots.add(p);
                    i++;
                }
            }
        }
    }

    /**
     * A pollen cloud: it lingers {@code life} ticks. A player inside grows drowsy: Slowness I at once, II after 1.5 s,
     * III and Mining Fatigue after 2.5 s; after 4 s they nod off (Blindness 2 s, Nausea, 4) and it starts again from
     * 2 s. Out of it the drowsiness fades within a second.
     */
    private Effect pollenCloud(Vec3 pos, double r, int life) {
        int[] t = {0};
        Map<UUID, Integer> inside = new HashMap<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (k % 2 == 0) {
                level.sendParticles(POLLEN_DUST, pos.x, pos.y + 1.0, pos.z, 6, r * 0.45, 0.8, r * 0.45, 0.01);
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, pos.x, pos.y + 1.2, pos.z, 3, r * 0.45, 0.8, r * 0.45, 0.0);
            }
            if (k % 10 == 0) {
                boss.telegraphRing(level, pos, r, POLLEN_DUST);
            }
            if (k % 5 == 0) {
                Set<UUID> now = new HashSet<>();
                for (LivingEntity e : boss.victims(level, pos, r + 1)) {
                    if (!(e instanceof Player) || flatDist(e.position(), pos) > r || Math.abs(e.getY() - pos.y) > 3.0) {
                        continue;
                    }
                    now.add(e.getUUID());
                    int in = inside.merge(e.getUUID(), 5, Integer::sum);
                    int amp = in >= 50 ? 2 : in >= 30 ? 1 : 0;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 15, amp), boss);
                    if (in >= 50) {
                        e.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 15, 1), boss);
                    }
                    if (in >= 80) {
                        e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0), boss);
                        e.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 60, 0), boss);
                        e.hurtServer(level, boss.damageSources().mobAttack(boss), 4.0F);
                        level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.BEE_POLLINATE, SoundSource.HOSTILE, 1.5F, 0.4F);
                        inside.put(e.getUUID(), 40);
                    }
                }
                inside.keySet().retainAll(now);
            }
            return k >= life;
        };
    }

    private void swingStep(ServerLevel level, int tick, float damage) {
        if (swingFrom == null || swingTo == null) {
            return;
        }
        if (tick <= 9) {
            Vec3 p = swingFrom.lerp(swingTo, tick / 9.0);
            teleportTo(p.x, swingTo.y + Math.sin(Math.PI * tick / 9.0) * 1.2, p.z);
            setDeltaMovement(Vec3.ZERO);
            level.sendParticles(THORN, getX(), getY() + 3.0, getZ(), 4, 0.4, 0.4, 0.4, 0.02);
            level.sendParticles(mangroveBlock(), getX(), getY() + 0.5, getZ(), 3, 0.5, 0.2, 0.5, 0.02);
            for (LivingEntity e : victims(level, position(), 3.0)) {
                if (flatDist(e.position(), position()) <= 2.2 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                    strike(level, e, damage, 1.0, 0.3);
                }
            }
        }
        if (tick == 9) {
            teleportTo(swingTo.x, swingTo.y, swingTo.z);
            level.sendParticles(rootBlock(), getX(), getY() + 0.3, getZ(), 30, 1.2, 0.2, 1.2, 0.1);
            level.playSound(null, this, SoundEvents.BREEZE_LAND, SoundSource.HOSTILE, 2.5F, 0.6F);
        }
    }

    private void castSnare(ServerLevel level) {
        Vec3 fwd = forward();
        LivingEntity best = null;
        double bestAlong = 99;
        for (LivingEntity e : victims(level, position(), 13)) {
            if (!(e instanceof Player)) {
                continue;
            }
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            if (along > 0 && along <= 12.0 && to.subtract(fwd.scale(along)).length() <= 0.9 + e.getBbWidth() / 2
                    && e.getY() - getY() < 3 && along < bestAlong) {
                best = e;
                bestAlong = along;
            }
        }
        for (double d = 1.5; d <= (best != null ? bestAlong : 12.0); d += 0.6) {
            Vec3 p = ahead(d);
            level.sendParticles(THORN, p.x, p.y + 0.6, p.z, 1, 0.05, 0.05, 0.05, 0);
        }
        level.playSound(null, this, SoundEvents.VINE_BREAK, SoundSource.HOSTILE, 2.5F, 0.6F);
        if (best != null) {
            strike(level, best, 8.0F, 0.0, 0.0);
            best.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 14, 6), this);
            snared = best;
            level.playSound(null, best.getX(), best.getY(), best.getZ(), SoundEvents.MANGROVE_ROOTS_HIT, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ the canopy

    /** Where she clings: in front of the sun-disc's jade face (found by its froglight eyes), else high over the centre. */
    private Vec3 findPerch(ServerLevel level) {
        if (perch != null) {
            return perch;
        }
        Vec3 c = centre();
        BlockPos base = BlockPos.containing(c);
        double sx = 0, sy = 0, sz = 0;
        int n = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -24; dx <= 24; dx++) {
            for (int dz = -24; dz <= 24; dz++) {
                for (int dy = 12; dy <= 26; dy++) {
                    p.set(base.getX() + dx, base.getY() + dy, base.getZ() + dz);
                    if (level.getBlockState(p).is(Blocks.VERDANT_FROGLIGHT)) {
                        sx += p.getX() + 0.5;
                        sy += p.getY();
                        sz += p.getZ() + 0.5;
                        n++;
                    }
                }
            }
        }
        if (n > 0) {
            Vec3 eye = new Vec3(sx / n, sy / n, sz / n);
            Vec3 dir = c.subtract(eye).multiply(1, 0, 1);
            dir = dir.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, 1) : dir.normalize();
            for (int out = 0; out <= 4; out++) {
                for (int dy = 0; dy <= 5; dy++) {
                    Vec3 q = eye.add(dir.scale(1.6 + out)).add(0, -7 + dy, 0);
                    if (clear(level, q, 6)) {
                        perch = new Vec3(Mth.floor(q.x) + 0.5, Mth.floor(q.y), Mth.floor(q.z) + 0.5);
                        return perch;
                    }
                }
            }
        }
        for (int up = 11; up >= 6; up--) {
            Vec3 q = c.add(0, up, 0);
            if (clear(level, q, 6)) {
                perch = q;
                return perch;
            }
        }
        perch = c.add(0, 6, 0);
        return perch;
    }

    private static boolean clear(ServerLevel level, Vec3 p, int height) {
        BlockPos b = BlockPos.containing(p);
        for (int y = 0; y < height; y++) {
            if (!level.getBlockState(b.above(y)).getCollisionShape(level, b.above(y)).isEmpty()) {
                return false;
            }
        }
        return true;
    }

    private void climb(ServerLevel level) {
        Vec3 to = findPerch(level);
        level.sendParticles(mangroveBlock(), getX(), getY() + 1, getZ(), 40, 1.0, 1.0, 1.0, 0.1);
        level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, getX(), getY() + 3, getZ(), 20, 1.0, 2.0, 1.0, 0);
        perched = true;
        setNoGravity(true);
        teleportTo(to.x, to.y, to.z);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
        faceToward(centre());
        level.sendParticles(mangroveBlock(), to.x, to.y + 2, to.z, 40, 1.0, 1.5, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.VINE_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** One tick up in the disc: spirits at tick 10, seed-bombs at 30, 80 and 130; an early fall once the spirits die. */
    private void canopyStep(ServerLevel level, int tick) {
        if (perch != null) {
            teleportTo(perch.x, perch.y, perch.z);
            setDeltaMovement(Vec3.ZERO);
        }
        if (tick % 4 == 0) {
            level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, getX(), getY() + 1, getZ(), 2, 1.0, 0.5, 1.0, 0);
            level.sendParticles(JADE, getX(), getY() + 4.5, getZ(), 1, 0.3, 0.3, 0.3, 0);
        }
        if (tick == 10) {
            dropSpirits(level);
        }
        if (tick == 30 || tick == 80 || tick == 130) {
            seedVolley(level);
        }
        if (tick >= 50 && tick % 5 == 0 && livingSpirits(level) == 0) {
            exposedDrop = true;
            level.playSound(null, this, SoundEvents.CREAKING_HEART_HURT, SoundSource.HOSTILE, 3.0F, 0.7F);
            chain(level, "plunge");
        }
    }

    private int spiritCap() {
        return scaledCount(3);
    }

    private int livingSpirits(ServerLevel level) {
        int n = 0;
        for (UUID id : spirits) {
            if (level.getEntity(id) instanceof JaguarSpirit s && s.isAlive()) {
                n++;
            }
        }
        return n;
    }

    /** Jaguar spirits drop from the canopy onto the summit: 2 (+1 per 2 extra players), never more than the cap alive. */
    private void dropSpirits(ServerLevel level) {
        spirits.removeIf(id -> !(level.getEntity(id) instanceof JaguarSpirit s) || !s.isAlive());
        int n = Math.min(scaledCount(2), spiritCap() - spirits.size());
        List<Player> players = fighters(level);
        for (int i = 0; i < n; i++) {
            Vec3 near = players.isEmpty() ? centre() : players.get(i % players.size()).position();
            Vec3 spot = null;
            for (int tries = 0; tries < 10 && spot == null; tries++) {
                double a = getRandom().nextDouble() * Math.PI * 2;
                double d = 3.0 + getRandom().nextDouble() * 3.0;
                Vec3 want = clampToArena(near.add(Math.cos(a) * d, 0, Math.sin(a) * d), 1.5);
                spot = safeSpot(level, want.x, want.z);
            }
            if (spot == null) {
                spot = centre();
            }
            JaguarSpirit s = ModEntities.JAGUAR_SPIRIT.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (s == null) {
                continue;
            }
            s.snapTo(spot.x, spot.y, spot.z, getRandom().nextFloat() * 360, 0);
            s.setOwner(this);
            s.addTag(MINION_TAG);
            level.addFreshEntity(s);
            spirits.add(s.getUUID());
            level.sendParticles(JADE, spot.x, spot.y + 1, spot.z, 30, 0.4, 0.6, 0.4, 0.05);
            level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, spot.x, spot.y + 4, spot.z, 10, 0.4, 2.0, 0.4, 0);
        }
        if (n > 0) {
            level.playSound(null, this, SoundEvents.OCELOT_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
        }
    }

    /** A seed-bomb on every player (up to 4) plus strays: a ring follows each for 16 ticks, locks 12, then the seed hits. */
    private void seedVolley(ServerLevel level) {
        List<Player> players = fighters(level);
        int k = 0;
        for (Player p : players) {
            if (k++ >= 4) {
                break;
            }
            addEffect(seedBomb(p, null, 16, 12, 2.5, 13.0F));
        }
        for (int i = 0; i < scaledCount(1); i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * Math.max(2, reach() - 3);
            addEffect(seedBomb(null, centre().add(Math.cos(a) * d, 0, Math.sin(a) * d), 16, 12, 2.5, 13.0F));
        }
        level.playSound(null, this, SoundEvents.SNIFFER_DROP_SEED, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private Effect seedBomb(@Nullable LivingEntity follow, @Nullable Vec3 fixed, int track, int lock, double r, float damage) {
        int[] t = {0};
        Vec3[] at = {fixed};
        return (boss, level) -> {
            int k = t[0]++;
            if (follow != null && k < track && follow.isAlive() && boss instanceof StranglerQueen q) {
                at[0] = q.clampToArena(follow.position(), 0.5);
            }
            if (at[0] == null) {
                return true;
            }
            Vec3 p = at[0];
            if (k < track + lock) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, p, r, k < track ? ORCHID : JADE);
                }
                if (k >= track) {               // the seed falling from the disc
                    double h = 14.0 * (1.0 - (k - track) / (double) lock);
                    level.sendParticles(JADE, p.x, p.y + h, p.z, 2, 0.1, 0.1, 0.1, 0);
                    level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, p.x, p.y + h + 0.5, p.z, 1, 0.1, 0.1, 0.1, 0);
                }
                return false;
            }
            level.sendParticles(rootBlock(), p.x, p.y + 0.4, p.z, 30, r * 0.4, 0.5, r * 0.4, 0.1);
            level.sendParticles(ORCHID, p.x, p.y + 0.8, p.z, 16, r * 0.4, 0.5, r * 0.4, 0.05);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 2.0F, 0.7F);
            for (LivingEntity e : boss.victims(level, p, r + 1)) {
                if (flatDist(e.position(), p) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.5) {
                    boss.strike(level, e, damage, 0.0, 0.4);
                }
            }
            return true;
        };
    }

    private void plungeDown(ServerLevel level) {
        Vec3 spot = lockedSpot != null ? lockedSpot : landingSpot(level, centre());
        perched = false;
        setNoGravity(false);
        teleportTo(spot.x, spot.y, spot.z);
        setDeltaMovement(Vec3.ZERO);
        hitCircle(level, spot, 3.5, 17.0F, 1.0, 0.4);
        addEffect(WayfarerBoss.wave(spot, 10, 0.5, 8.0F, ROOTDUST));
        level.sendParticles(rootBlock(), spot.x, spot.y + 0.3, spot.z, 80, 2.0, 0.3, 2.0, 0.15);
        level.sendParticles(ParticleTypes.EXPLOSION, spot.x, spot.y + 0.5, spot.z, 2, 0.6, 0.2, 0.6, 0);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
        if (exposedDrop) {
            exposedUntil = tickCount + 80;
            addEffect((boss, lvl) -> {                           // dazed: roots tangled round her, a slow
                if (boss.tickCount >= exposedUntil) {
                    return true;
                }
                if (boss.tickCount % 4 == 0) {
                    lvl.sendParticles(ParticleTypes.CRIT, boss.getX(), boss.getY() + 5.0, boss.getZ(), 3, 0.5, 0.2, 0.5, 0.1);
                }
                return false;
            });
            addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 3));
        }
        exposedDrop = false;
    }

    /** Back on the floor at once (a cut-short canopy: stagger, reset, reload). */
    private void land(ServerLevel level) {
        perched = false;
        setNoGravity(false);
        Vec3 spot = landingSpot(level, position());
        teleportTo(spot.x, spot.y, spot.z);
        setDeltaMovement(Vec3.ZERO);
        level.sendParticles(mangroveBlock(), spot.x, spot.y + 1, spot.z, 30, 0.8, 0.8, 0.8, 0.1);
    }

    // ------------------------------------------------------------------ phase 3: the overgrowth and the cages

    private void overgrow(ServerLevel level) {
        overgrown = true;
        cageTimer = 60;
        addEffect(WayfarerBoss.wave(position(), 13, 0.55, 12.0F, ROOTDUST));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("strangler_queen_overgrown"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 c = centre();
        level.sendParticles(rootBlock(), c.x, c.y + 0.5, c.z, 200, reach() * 0.5, 0.3, reach() * 0.5, 0.1);
        level.sendParticles(ORCHID, getX(), getY() + 5.5, getZ(), 60, 1.5, 1.0, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    private void pickCageTargets(ServerLevel level) {
        marked.clear();
        spots.clear();
        for (Player p : fighters(level)) {
            if (marked.size() < 4) {
                marked.add(p);
                spots.add(new Vec3(Mth.floor(p.getX()) + 0.5, centre().y, Mth.floor(p.getZ()) + 0.5));
            }
        }
        if (marked.isEmpty() && getTarget() != null) {
            marked.add(getTarget());
            spots.add(new Vec3(Mth.floor(getTarget().getX()) + 0.5, centre().y, Mth.floor(getTarget().getZ()) + 0.5));
        }
    }

    /** Snaps every marked cage shut: who is still in the middle takes 6 and is caught (and strangled while inside). */
    private void closeCages(ServerLevel level) {
        level.playSound(null, this, SoundEvents.MANGROVE_ROOTS_PLACE, SoundSource.HOSTILE, 3.0F, 0.4F);
        boolean caught = false;
        Vec3 first = null;
        for (Vec3 s : spots) {
            Vec3 at = landingSpotFloor(level, s);
            if (at == null) {
                continue;
            }
            placeCage(level, at);
            cages.put(at, tickCount + CAGE_LIFE);
            for (LivingEntity e : victims(level, at, 2.0)) {
                if (flatDist(e.position(), at) <= 0.9 && Math.abs(e.getY() - at.y) < 1.5) {
                    strike(level, e, 6.0F, 0.0, 0.0);
                    caught = true;
                    if (first == null) {
                        first = at;
                    }
                }
            }
            addEffect(strangle(at, CAGE_LIFE));
        }
        spots.clear();
        marked.clear();
        if (caught) {
            harvestAt = tickCount + 50;
            lockedSpot = first;
        }
    }

    /** The floor cell under {@code s} (its centre at feet height), or null where the summit has no floor. */
    private @Nullable Vec3 landingSpotFloor(ServerLevel level, Vec3 s) {
        double y = floorY(level, s.x, centre().y + 1, s.z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 2.5 || flatDist(s, centre()) > reach() + 1.5) {
            return null;
        }
        return new Vec3(Mth.floor(s.x) + 0.5, y, Mth.floor(s.z) + 0.5);
    }

    /** A cage of mangrove roots round the cell at {@code at}: the 8 cells round it, 3 high, and a roof. Air only. */
    private void placeCage(ServerLevel level, Vec3 at) {
        BlockPos c = BlockPos.containing(at);
        int until = tickCount + CAGE_LIFE;
        for (int dy = 0; dy <= 3; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    boolean ring = dx != 0 || dz != 0;
                    if (dy < 3 && !ring) {
                        continue;                                // the hollow inside
                    }
                    if (cageBlocks.size() >= MAX_CAGE_BLOCKS) {
                        return;
                    }
                    BlockPos p = c.offset(dx, dy, dz);
                    if (!level.getBlockState(p).isAir() || cageBlocks.containsKey(p)) {
                        continue;
                    }
                    AABB cell = new AABB(p);
                    if (getBoundingBox().intersects(cell) || !level.getEntitiesOfClass(LivingEntity.class, cell, LivingEntity::isAlive).isEmpty()) {
                        continue;                                // never inside a creature
                    }
                    level.setBlock(p, Blocks.MANGROVE_ROOTS.defaultBlockState(), 3);
                    cageBlocks.put(p.immutable(), until);
                }
            }
        }
        level.sendParticles(mangroveBlock(), at.x, at.y + 1.5, at.z, 40, 0.9, 1.0, 0.9, 0.1);
    }

    /** While the cage stands, whoever is inside is strangled: 2 a second (after the first second) and slowed. */
    private Effect strangle(Vec3 at, int life) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (boss instanceof StranglerQueen q && !q.cages.containsKey(at)) {
                return true;                                     // harvested or gone
            }
            if (k > 20 && k % 20 == 0) {
                for (LivingEntity e : boss.victims(level, at, 1.5)) {
                    if (flatDist(e.position(), at) <= 1.0 && Math.abs(e.getY() - at.y) < 2.0) {
                        e.hurtServer(level, boss.damageSources().mobAttack(boss), 2.0F);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 25, 1), boss);
                        level.sendParticles(THORN, e.getX(), e.getY() + 1, e.getZ(), 8, 0.3, 0.5, 0.3, 0.02);
                    }
                }
            }
            return k >= life;
        };
    }

    /** A cage that still holds a player, or null. */
    private @Nullable Vec3 fullCage(ServerLevel level) {
        for (Vec3 at : cages.keySet()) {
            for (LivingEntity e : victims(level, at, 1.5)) {
                if (e instanceof Player && flatDist(e.position(), at) <= 1.0 && Math.abs(e.getY() - at.y) < 2.0) {
                    return at;
                }
            }
        }
        return null;
    }

    private void harvest(ServerLevel level) {
        Vec3 at = lockedSpot;
        if (at == null) {
            return;
        }
        Vec3 dir = position().subtract(at).multiply(1, 0, 1);
        dir = dir.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, 1) : dir.normalize();
        Vec3 stand = landingSpot(level, at.add(dir.scale(2.6)));
        teleportTo(stand.x, stand.y, stand.z);
        faceToward(at);
        breakCage(level, at);
        for (LivingEntity e : victims(level, at, 3.5)) {
            if (flatDist(e.position(), at) <= 2.5 + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                strike(level, e, 18.0F, 0.6, 0.3);
            }
        }
        level.sendParticles(mangroveBlock(), at.x, at.y + 1.2, at.z, 60, 1.0, 1.0, 1.0, 0.15);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, at.x, at.y + 1.5, at.z, 2, 0.5, 0.3, 0.5, 0);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        lockedSpot = null;
    }

    private void breakCage(ServerLevel level, Vec3 at) {
        BlockPos c = BlockPos.containing(at);
        List<BlockPos> gone = new ArrayList<>();
        for (BlockPos p : cageBlocks.keySet()) {
            if (Math.abs(p.getX() - c.getX()) <= 1 && Math.abs(p.getZ() - c.getZ()) <= 1 && p.getY() - c.getY() >= 0
                    && p.getY() - c.getY() <= 3) {
                gone.add(p);
            }
        }
        for (BlockPos p : gone) {
            removeRoot(level, p);
            cageBlocks.remove(p);
        }
        cages.remove(at);
    }

    private static void removeRoot(ServerLevel level, BlockPos p) {
        if (level.isLoaded(p) && level.getBlockState(p).is(Blocks.MANGROVE_ROOTS)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    /** Removes cage blocks whose time is up (or all of them); only blocks that are still mangrove roots. */
    private void restoreCages(ServerLevel level, boolean all) {
        if (!cageBlocks.isEmpty()) {
            List<BlockPos> done = new ArrayList<>();
            for (Map.Entry<BlockPos, Integer> en : cageBlocks.entrySet()) {
                if (all || en.getValue() <= tickCount) {
                    removeRoot(level, en.getKey());
                    done.add(en.getKey());
                }
            }
            done.forEach(cageBlocks::remove);
        }
        cages.values().removeIf(until -> all || until <= tickCount);
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0 || perched) {
            level.sendParticles(mangroveBlock(), getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        if (tickCount < exposedUntil) {
            amount *= 1.3F;
        }
        return super.hurtServer(level, source, amount);
    }

    private void discardSpirits(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 24, 24, radius + 24),
                m -> m instanceof JaguarSpirit || m.entityTags().contains(MINION_TAG) && spirits.contains(m.getUUID()))) {
            level.sendParticles(JADE, m.getX(), m.getY() + 0.5, m.getZ(), 12, 0.3, 0.3, 0.3, 0.05);
            m.discard();
        }
        spirits.clear();
    }

    /** Puts everything back: the cages, the spirits, her footing. */
    private void cleanUp(ServerLevel level) {
        restoreCages(level, true);
        discardSpirits(level);
        harvestAt = -1;
        if (perched) {
            land(level);
        }
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleCages) {                         // saved by an unload: removed on the first tick
            staleCages = false;
            restoreCages(level, true);
        }
        if (guard > 0) {
            guard--;
        }
        restoreCages(level, false);
        BossAttack cur = currentAttack();
        if (perched && (cur == null || !("canopy".equals(cur.name) || "plunge".equals(cur.name)))) {
            land(level);                          // the canopy was cut short
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!cageBlocks.isEmpty() || !spirits.isEmpty())) {
            cleanUp(level);                       // the arena emptied (death, flight)
        }
        if (phase() == 1 && (overgrown || canopyTimer != 10 || !cageBlocks.isEmpty())) {      // the fight was reset
            overgrown = false;
            roarUntil = -1;
            exposedUntil = -1;
            canopyTimer = 10;
            cleanUp(level);
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("strangler_queen_overgrown"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("strangler_queen_wrath"));
            }
        }
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!overgrown && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "overgrowth");
            } else if (overgrown) {
                if (harvestAt > 0 && tickCount >= harvestAt) {
                    harvestAt = -1;
                    Vec3 full = fullCage(level);
                    if (full != null) {
                        lockedSpot = full;
                        chain(level, "harvest");
                    }
                } else if (--cageTimer <= 0) {
                    cageTimer = (int) Math.round(CAGE_EVERY * cooldownScale());
                    chain(level, "cages");
                }
            } else if (--canopyTimer <= 0) {
                canopyTimer = Math.max(11, (int) Math.round(CANOPY_EVERY * cooldownScale()));
                chain(level, "canopy");
            }
        }
        // ambience: pollen off the crown, the jade eyes, roots stirring at her feet
        if (!perched) {
            if (tickCount % 6 == 0) {
                level.sendParticles(POLLEN_DUST, getX(), getY() + 5.8, getZ(), 1, 0.6, 0.2, 0.6, 0.005);
            }
            if (overgrown && tickCount % 5 == 0) {
                level.sendParticles(rootBlock(), getX(), getY() + 0.2, getZ(), 2, 1.4, 0.1, 1.4, 0.02);
            }
            if (tickCount % 120 == 0) {
                level.playSound(null, this, SoundEvents.CREAKING_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        canopyTimer = 9;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("strangler_queen_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ORCHID, getX(), getY() + 5.5, getZ(), 80, 1.5, 1.0, 1.5, 0.08);
        level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, getX(), getY() + 6, getZ(), 60, 3.0, 1.0, 3.0, 0);
        level.playSound(null, this, SoundEvents.CREAKING_HEART_SPAWN, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(ORCHID, getX(), getY() + 4, getZ(), 120, 1.5, 2.0, 1.5, 0.05);
        level.sendParticles(mangroveBlock(), getX(), getY() + 2, getZ(), 100, 1.5, 2.0, 1.5, 0.1);
        level.playSound(null, this, SoundEvents.CREAKING_DEATH, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            restoreCages(level, true);
            discardSpirits(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("QueenCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("QueenRadius", radius);
        output.putBoolean("QueenOvergrown", overgrown);
        List<Long> roots = new ArrayList<>();
        cageBlocks.keySet().forEach(p -> roots.add(p.asLong()));
        output.store("QueenCageBlocks", Codec.LONG.listOf(), roots);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("QueenCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("QueenRadius", 18);
        overgrown = input.getBooleanOr("QueenOvergrown", false) && phase() == 2;
        cageBlocks.clear();
        cages.clear();
        input.read("QueenCageBlocks", Codec.LONG.listOf()).ifPresent(l -> l.forEach(p -> cageBlocks.put(BlockPos.of(p), 0)));
        staleCages = !cageBlocks.isEmpty();
        perched = false;
        perch = null;
        setNoGravity(false);
    }
}
