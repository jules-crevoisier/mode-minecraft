package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
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
import net.minecraft.world.entity.LivingEntity;
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
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.ChimeAbbot.AWAKEN;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.BELLCRASH;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.BREATH;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.CHIMERING;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.FLURRY;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.PALM;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.PETALS;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.ROAR;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.STAFF;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.STAGGER;
import static com.brasshaven.generated.MobAnims.ChimeAbbot.STEP;

/**
 * L'Abbé des carillons (The Chime Abbot), the champion of the Cloud Pagoda: an ancient monk fused with clockwork, about
 * 3 blocks tall, floating a hand's breadth over the deck in layered cherry-red and white robes, a brass halo of
 * wind-chime rods behind his head and a bronze dragon-head staff. He waits on the open top deck under the ninth roof (a
 * 33-block square, railing round it, four roof posts at the corners).
 * <ul>
 *     <li>Phase 1: the <b>staff</b> combo, the <b>palm</b> strike (a cone of wind), the <b>chime ring</b> (rods fly out of
 *     his halo, hang in a circle and ring one after another, each marking its strike zone before it hits), the
 *     <b>petal storm</b> (a ring of petals with three gaps rolls over the deck and blinds whoever it catches) and the
 *     <b>step</b> (he scatters into petals and reappears at the deck corner nearest you).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>flurry</b> (three thrusts and a spin), the <b>bell-crash</b> (he soars
 *     and drops on a ring that followed you), chime rings that ring both ways round plus a rod over every player, a
 *     second petal ring.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): he <b>awakens</b> the brass dragon of the
 *     pagoda; its ghost (particles, not an entity) circles over the deck and every 12 s he conducts its <b>breath</b>
 *     down three or four lanes across the deck, drawn on the floor long before each pass.</li>
 * </ul>
 * He places no blocks. Pushes are capped and never thrown outward near the railing or over a drop, so nobody leaves the
 * deck by his hand.
 */
public class ChimeAbbot extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.1F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double STAFF_RANGE = 5.0;
    private static final double STAFF_HALF = 70;
    private static final double PALM_RANGE = 9.0;
    private static final double PALM_HALF = 28;
    private static final double RING_R = 6.5;
    private static final double ZONE_R = 2.4;
    private static final int ROD_WARN = 12;
    private static final double GAP_HALF = 24;
    private static final double LANE_HALF = 1.6;
    private static final int BREATH_EVERY = 240;
    private static final DustParticleOptions CHERRY = new DustParticleOptions(0xF0A0B8, 1.3F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xD0303C, 1.4F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xE0B050, 1.4F);
    private static final DustParticleOptions BRASS_BIG = new DustParticleOptions(0xD8A848, 2.4F);
    private static final DustParticleOptions WIND = new DustParticleOptions(0xE8F4F4, 1.2F);
    private static final DustParticleOptions SPIRIT = new DustParticleOptions(0x7CF0D8, 1.6F);

    private @Nullable Vec3 centre;
    private int radius = 16;
    /** Phase 3 has started (the brass dragon awakened). */
    private boolean awakened;
    private int guard;
    private int roarUntil = -1;
    private int breathTimer = 60;
    private int breathCount;
    private @Nullable List<Vec3> corners;
    private @Nullable Vec3 stepTo;
    private @Nullable Vec3 crashAt;
    private final List<Vec3> rods = new ArrayList<>();
    private final List<Double> gaps = new ArrayList<>();
    private final List<Double> gaps2 = new ArrayList<>();
    /** Breath lanes: offset across the deck; the axis is {@link #laneAlongX} (true = the lane runs along x). */
    private final List<Double> lanes = new ArrayList<>();
    private boolean laneAlongX;

    public ChimeAbbot(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 560.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 13.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ChimeAbbot.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.PINK;
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

    // ------------------------------------------------------------------ arena memory (a square deck)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        corners = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Half width of the usable deck round the seal (the deck is 33 across, the railing on its rim). */
    private double reach() {
        return Math.max(6.0, Math.min(15.0, radius - 1.0));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Distance from the centre in the deck's square metric (the larger of the two axis offsets). */
    private double cheb(Vec3 p) {
        return Math.max(Math.abs(p.x - centre().x), Math.abs(p.z - centre().z));
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

    private static int headroom(ServerLevel level, Vec3 p, int max) {
        BlockPos b = BlockPos.containing(p);
        for (int y = 0; y < max; y++) {
            BlockPos q = b.above(y);
            if (!level.getBlockState(q).getCollisionShape(level, q).isEmpty()) {
                return y;
            }
        }
        return max;
    }

    /** A standing spot on the deck at (x, z), level with the seal, with room for him above; or null. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 0.6) {
            return null;
        }
        return headroom(level, new Vec3(x, y, z), 4) >= 4 ? new Vec3(x, y, z) : null;
    }

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        double max = Math.max(2.0, reach() - margin);
        return new Vec3(c.x + Mth.clamp(p.x - c.x, -max, max), c.y, c.z + Mth.clamp(p.z - c.z, -max, max));
    }

    /** The nearest standing spot to {@code want} on the way to the centre (the centre itself at worst). */
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

    /** Removes the outward part of {@code push} for someone near the railing (square deck), all of it over a drop. */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 c = centre();
        double dx = e.getX() - c.x;
        double dz = e.getZ() - c.z;
        double edge = reach() - 3.0;
        double px = push.x;
        double pz = push.z;
        if (Math.abs(dx) > edge && px * dx > 0) {
            px = 0;
        }
        if (Math.abs(dz) > edge && pz * dz > 0) {
            pz = 0;
        }
        Vec3 probe = e.position().add(push.normalize().scale(2.0));
        double fy = floorY(level, probe.x, e.getY(), probe.z);
        if (Double.isNaN(fy) || fy < e.getY() - 2.5) {
            return Vec3.ZERO;
        }
        return new Vec3(px, 0, pz);
    }

    /** Pushes capped at 1.2 and lift at 0.45; near the railing or a drop the outward part is removed. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.2, knockback));
            push = safePush(level, e, push);
        }
        lift = Math.min(lift, cheb(e.position()) > reach() - 3.0 ? 0.2 : 0.45);
        if (push.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // staff: the dragon staff swung back over his right shoulder (0.7 s, the arc drawn in petals), a forehand sweep,
        // a turn and a backhand 0.6 s later; phase 2 adds an overhead slam on a marked circle 0.5 s after that
        out.add(BossAttack.of("staff").anim(STAFF).timing(14, 26, 14).range(0, 6.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, STAFF_RANGE, STAFF_HALF, CHERRY);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 12) {
                        staffCut(level, 12.0F);
                    }
                    if (tick == 4) {
                        turnToward(t, 35.0F);
                    }
                    if (tick > 4 && tick < 12 && tick % 2 == 0) {
                        b.telegraphArc(level, STAFF_RANGE, STAFF_HALF, CHERRY);
                    }
                    if (b.phase() == 2) {
                        if (tick == 14) {
                            turnToward(t, 25.0F);
                        }
                        if (tick > 14 && tick < 22 && tick % 2 == 0) {
                            b.telegraphRing(level, b.ahead(3.0), 2.5, RED);
                        }
                        if (tick == 22) {
                            Vec3 at = b.ahead(3.0);
                            b.hitCircle(level, at, 2.5, 16.0F, 0.8, 0.3);
                            b.addEffect(WayfarerBoss.wave(at, 6.0, 0.5, 7.0F, CHERRY));
                            level.sendParticles(ParticleTypes.GUST, at.x, at.y + 0.3, at.z, 2, 0.4, 0.1, 0.4, 0.0);
                            level.playSound(null, at.x, at.y, at.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 0.6F);
                            level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.0F, 0.8F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "flurry" : "palm");
                    }
                })
                .build());
        // palm: the open left palm drawn back to his hip, wind gathering (0.9 s; the cone drawn in white), then driven
        // out: a cone of wind 9 deep. Phase 2: a ring of wind rolls out round him as well (jump it)
        out.add(BossAttack.of("palm").anim(PALM).timing(18, 6, 16).range(0, 9.0).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (double r = 3.0; r <= PALM_RANGE; r += 3.0) {
                            b.telegraphArc(level, r, PALM_HALF, WIND);
                        }
                        for (int s = -1; s <= 1; s += 2) {
                            Vec3 dir = rotate(b.forward(), s * PALM_HALF);
                            for (double d = 1.5; d <= PALM_RANGE; d += 1.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(WIND, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    level.sendParticles(ParticleTypes.SMALL_GUST, b.getX(), b.getY() + 1.4, b.getZ(), 1, 0.6, 0.4, 0.6, 0.0);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BREEZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, PALM_RANGE, PALM_HALF, 14.0F, 1.1);
                    for (double d = 1.5; d <= PALM_RANGE; d += 1.5) {
                        Vec3 p = b.ahead(d);
                        level.sendParticles(ParticleTypes.GUST, p.x, p.y + 1.0, p.z, 1, d * 0.15, 0.3, d * 0.15, 0.0);
                    }
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 7.0, 0.5, 7.0F, WIND));
                    }
                    level.playSound(null, b, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.5F, 0.6F);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.5F, 1.4F);
                })
                .build());
        // chime ring: arms spread, the halo blazing (1.0 s; the circle of rods drawn round him), then the rods fly out
        // and hang in a circle; they ring one after another round it, each marking its strike zone 0.6 s before it hits
        out.add(BossAttack.of("chimering").anim(CHIMERING).timing(20, 44, 16).range(0, 24.0).cooldown(240).weight(7)
                .track(false)
                .start((b, level, t, tick) -> planRods())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 r : rods) {
                            level.sendParticles(ParticleTypes.END_ROD, r.x, r.y + 2.5 - tick * 0.05, r.z, 1, 0.05, 0.2, 0.05, 0.0);
                        }
                        b.telegraphRing(level, b.position(), RING_R, BRASS);
                    }
                    level.sendParticles(BRASS, b.getX(), b.getY() + 3.0, b.getZ(), 3, 0.6, 0.6, 0.3, 0.0);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.04F);
                    }
                })
                .impact((b, level, t, tick) -> ringRods(level))
                .build());
        // petal storm: the staff whirled overhead (1.1 s; three gaps drawn as white wind lines from him outward), then
        // a ring of cherry petals rolls over the whole deck: whoever it catches outside a gap is blinded briefly and
        // cut. Phase 2: a second ring 0.8 s later, its gaps turned 60 degrees (drawn as soon as the first ring goes)
        out.add(BossAttack.of("petals").anim(PETALS).timing(22, 30, 14).range(0, 24.0).cooldown(320).weight(6)
                .track(false)
                .start((b, level, t, tick) -> planGaps())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawGaps(level, gaps, WIND);
                    }
                    level.sendParticles(ParticleTypes.CHERRY_LEAVES, b.getX(), b.getY() + 3.0, b.getZ(), 6, 1.5, 0.6, 1.5, 0.0);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 1.5F, 0.8F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(petalRing(position(), List.copyOf(gaps)));
                    level.playSound(null, b, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 0.8F);
                    level.playSound(null, b, SoundEvents.CHERRY_LEAVES_BREAK, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() != 2) {
                        return;
                    }
                    if (tick < 16 && tick % 2 == 0) {
                        drawGaps(level, gaps2, CHERRY);
                    }
                    if (tick == 16) {
                        b.addEffect(petalRing(position(), List.copyOf(gaps2)));
                        level.playSound(null, b, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 1.0F);
                    }
                })
                .build());
        // step: he draws into himself (0.6 s; a column of petals swirls at the deck corner nearest you), scatters into a
        // gust and reappears there; then the staff (close) or the palm
        out.add(BossAttack.of("step").anim(STEP).timing(12, 4, 10).range(7.0, 32.0).cooldown(160).weight(8).track(false)
                .start((b, level, t, tick) -> stepTo = pickCorner(level, t))
                .windup((b, level, t, tick) -> {
                    if (stepTo != null && tick % 2 == 0) {
                        b.telegraphRing(level, stepTo, 1.4, CHERRY);
                        level.sendParticles(ParticleTypes.CHERRY_LEAVES, stepTo.x, stepTo.y + 1 + (tick % 6) * 0.5, stepTo.z,
                                4, 0.4, 0.4, 0.4, 0.0);
                    }
                    level.sendParticles(ParticleTypes.CHERRY_LEAVES, b.getX(), b.getY() + 1.5, b.getZ(), 4, 0.5, 0.8, 0.5, 0.0);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 2.0F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> stepToCorner(level, t))
                .end((b, level, t, tick) -> {
                    if (t != null) {
                        b.chain(level, b.distanceTo(t) < 6.5 ? "staff" : "palm");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // flurry: three thrusts of the dragon staff down a line (0.7, 1.1 and 1.5 s; the line drawn before each,
        // turning toward you between them), then a full spin (2.0 s; the ring drawn from 1.6 s)
        out.add(BossAttack.of("flurry").anim(FLURRY).phaseTwo().timing(14, 34, 14).range(0, 7.0).cooldown(90).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLine(level, 6.5, RED);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BREEZE_SHOOT, SoundSource.HOSTILE, 1.5F, 1.2F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 8 || tick == 16) {
                        b.hitLine(level, 6.5, 1.0, 10.0F, 0.5);
                        for (double d = 1.0; d <= 6.5; d += 0.5) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.SMALL_GUST, p.x, p.y + 1.4, p.z, 1, 0.05, 0.05, 0.05, 0.0);
                        }
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 0.8F + tick * 0.02F);
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 1.0F + tick * 0.03F);
                    }
                    if (tick == 3 || tick == 11) {
                        turnToward(t, 25.0F);
                    }
                    if ((tick > 3 && tick < 8 || tick > 11 && tick < 16) && tick % 2 == 0) {
                        drawLine(level, 6.5, RED);
                    }
                    if (tick > 18 && tick < 26 && tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, RED);
                    }
                    if (tick == 26) {
                        b.hitCircle(level, b.position(), 4.5, 13.0F, 1.0, 0.3);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX(), b.getY() + 1.4, b.getZ(), 6, 2.0, 0.2, 2.0, 0.0);
                        level.sendParticles(ParticleTypes.CHERRY_LEAVES, b.getX(), b.getY() + 1.4, b.getZ(), 30, 2.5, 0.3, 2.5, 0.0);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .build());
        // bell-crash: he gathers himself and soars up (1.0 s; a ring follows you), hangs over the deck while the ring
        // locks and turns red (0.5 s), then drops onto it: 17 within 3 and a ring of wind to 8 (jump it)
        out.add(BossAttack.of("bellcrash").anim(BELLCRASH).phaseTwo().timing(20, 20, 18).range(5.0, 24.0).cooldown(200)
                .weight(8).track(false)
                .start((b, level, t, tick) -> crashAt = t != null ? clampToArena(t.position(), 2.0) : position())
                .windup((b, level, t, tick) -> {
                    if (t != null && t.isAlive()) {
                        crashAt = clampToArena(t.position(), 2.0);
                    }
                    if (crashAt != null && tick % 2 == 0) {
                        b.telegraphRing(level, crashAt, 3.0, BRASS);
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (crashAt != null) {
                        crashAt = landingSpot(level, crashAt);
                    }
                    level.sendParticles(ParticleTypes.GUST, b.getX(), b.getY() + 0.5, b.getZ(), 3, 0.5, 0.2, 0.5, 0.0);
                    level.playSound(null, b, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (crashAt == null) {
                        return;
                    }
                    if (tick < 10) {
                        if (tick % 2 == 0) {
                            b.telegraphRing(level, crashAt, 3.0, RED);
                        }
                        level.sendParticles(ParticleTypes.CHERRY_LEAVES, crashAt.x, crashAt.y + 6 - tick * 0.5, crashAt.z,
                                3, 0.4, 0.2, 0.4, 0.0);
                    } else if (tick == 10) {
                        level.sendParticles(ParticleTypes.CHERRY_LEAVES, b.getX(), b.getY() + 1.5, b.getZ(), 20, 0.5, 1.0, 0.5, 0.0);
                        teleportTo(crashAt.x, crashAt.y, crashAt.z);
                        setDeltaMovement(Vec3.ZERO);
                        getNavigation().stop();
                        if (t != null) {
                            faceToward(t.position());
                        }
                        b.hitCircle(level, crashAt, 3.0, 17.0F, 1.0, 0.4);
                        b.addEffect(WayfarerBoss.wave(crashAt, 8.0, 0.5, 8.0F, CHERRY));
                        level.sendParticles(ParticleTypes.EXPLOSION, crashAt.x, crashAt.y + 0.5, crashAt.z, 2, 0.6, 0.2, 0.6, 0.0);
                        level.sendParticles(ParticleTypes.GUST, crashAt.x, crashAt.y + 0.3, crashAt.z, 4, 1.2, 0.1, 1.2, 0.0);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.7F);
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // awaken: he rises, the halo spinning ever faster, the dragon staff held high (2.0 s, invulnerable; the spirit
        // gathers in brass dust round him), then the brass dragon's ghost tears free: a ring of wind (11, jump it)
        out.add(BossAttack.of("awaken").anim(AWAKEN).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.ENDER_DRAGON_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.8F);
                })
                .windup((b, level, t, tick) -> {
                    double a = tick * 0.35;
                    double r = 4.0 - tick * 0.07;
                    for (int k = 0; k < 3; k++) {
                        double ang = a + k * Math.PI * 2 / 3;
                        level.sendParticles(BRASS, b.getX() + Math.cos(ang) * r, b.getY() + 1 + tick * 0.07,
                                b.getZ() + Math.sin(ang) * r, 2, 0.1, 0.1, 0.1, 0.0);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, SPIRIT);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.5F, 0.5F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> awaken(level))
                .build());
        // breath: he points the dragon staff (1.0 s; the lanes are drawn on the deck from the start, the next one in red
        // with the dragon's head waiting at its end), then conducts the spirit dragon down each lane in turn
        out.add(BossAttack.of("breath").anim(BREATH).phaseTwo().timing(20, 40, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> planLanes(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLanes(level, -20 + tick);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.0F, 1.3F);
                    }
                })
                .impact((b, level, t, tick) -> b.addEffect(breathPasses()))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void staffCut(ServerLevel level, float damage) {
        hitArc(level, STAFF_RANGE, STAFF_HALF, damage, 1.0);
        for (double a = -STAFF_HALF; a <= STAFF_HALF; a += 12) {
            Vec3 p = position().add(rotate(forward(), a).scale(STAFF_RANGE - 1.0));
            level.sendParticles(ParticleTypes.CHERRY_LEAVES, p.x, p.y + 1.4, p.z, 2, 0.1, 0.2, 0.1, 0.0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 1.2F);
    }

    private void drawLine(ServerLevel level, double len, DustParticleOptions dust) {
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = ahead(d);
            level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
        }
    }

    /** Eight rods in a circle round him (radius 6.5), from a random start angle. */
    private void planRods() {
        rods.clear();
        double start = getRandom().nextDouble() * Math.PI * 2;
        for (int k = 0; k < 8; k++) {
            double a = start + k * Math.PI * 2 / 8;
            rods.add(position().add(Math.cos(a) * RING_R, 0, Math.sin(a) * RING_R));
        }
    }

    /**
     * The rods ring in sequence. Phase 1: round the circle one way, every 4 ticks. Phase 2: both ways from the first rod,
     * every 5 ticks, then a rod over every player (up to 4) last. Each rod's zone is marked 12 ticks before it hits.
     */
    private void ringRods(ServerLevel level) {
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.5F, 1.2F);
        for (Vec3 r : rods) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3.0, getZ(), 2, 0.2, 0.2, 0.2, 0.05);
            level.sendParticles(BRASS, r.x, r.y + 2.5, r.z, 6, 0.1, 0.4, 0.1, 0.0);
        }
        if (phase() == 2) {
            int n = rods.size();
            for (int k = 0; k <= n / 2; k++) {
                addEffect(chimeRod(rods.get(k % n), 2 + k * 5, k));
                if (k != 0 && k != n - k) {
                    addEffect(chimeRod(rods.get((n - k) % n), 2 + k * 5, k));
                }
            }
            int step = n / 2 + 1;
            int i = 0;
            for (Player p : fighters(level)) {
                if (i++ >= 4) {
                    break;
                }
                addEffect(chimeRod(clampToArena(p.position(), 0.5), 2 + step * 5, step));
            }
        } else {
            for (int k = 0; k < rods.size(); k++) {
                addEffect(chimeRod(rods.get(k), 2 + k * 4, k));
            }
        }
    }

    /** One hanging rod: it waits {@code start} ticks, its zone is marked for 12, then it strikes: 11 within 2.4. */
    private Effect chimeRod(Vec3 at, int start, int note) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < start) {
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 2.6, at.z, 1, 0.03, 0.3, 0.03, 0.0);
                    level.sendParticles(BRASS, at.x, at.y + 2.6, at.z, 1, 0.03, 0.3, 0.03, 0.0);
                }
                return false;
            }
            if (k < start + ROD_WARN) {
                if (k == start) {
                    level.playSound(null, at.x, at.y + 2, at.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F,
                            0.7F + note * 0.1F);
                    level.sendParticles(ParticleTypes.NOTE, at.x, at.y + 3.2, at.z, 1, 0, 0, 0, 0);
                }
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, ZONE_R, k - start < 8 ? BRASS : RED);
                }
                level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 2.6, at.z, 1, 0.05, 0.3, 0.05, 0.02);
                return false;
            }
            level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 1.2, at.z, 14, 0.2, 1.0, 0.2, 0.05);
            level.sendParticles(ParticleTypes.GUST, at.x, at.y + 0.3, at.z, 1, 0, 0, 0, 0);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0F, 0.9F + note * 0.08F);
            for (LivingEntity e : boss.victims(level, at, ZONE_R + 1)) {
                if (flatDist(e.position(), at) <= ZONE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                    boss.strike(level, e, 11.0F, 0.2, 0.3);
                }
            }
            return true;
        };
    }

    /** Three gaps 120 degrees apart (phase 2: a second set turned by 60), degrees round him. */
    private void planGaps() {
        gaps.clear();
        gaps2.clear();
        double start = getRandom().nextDouble() * 360.0;
        for (int k = 0; k < 3; k++) {
            gaps.add(start + k * 120.0);
            gaps2.add(start + 60.0 + k * 120.0);
        }
    }

    private void drawGaps(ServerLevel level, List<Double> set, DustParticleOptions dust) {
        for (double g : set) {
            double a = Math.toRadians(g);
            for (double d = 2.0; d <= 14.0; d += 1.0) {
                level.sendParticles(dust, getX() + Math.cos(a) * d, getY() + 0.2, getZ() + Math.sin(a) * d, 1, 0.05, 0, 0.05, 0);
            }
        }
    }

    private static boolean inGap(Vec3 c, Vec3 p, List<Double> set) {
        double ang = Math.toDegrees(Math.atan2(p.z - c.z, p.x - c.x));
        for (double g : set) {
            double diff = Math.abs(Mth.wrapDegrees(ang - g));
            if (diff <= GAP_HALF) {
                return true;
            }
        }
        return false;
    }

    /**
     * A ring of petals rolling out from {@code c} over the whole deck (0.55 blocks a tick): too tall to jump. Whoever it
     * catches outside the gaps is blinded briefly (1.5 s, phase 2: 2 s), cut (5) and nudged.
     */
    private Effect petalRing(Vec3 c, List<Double> set) {
        double[] r = {1.0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof ChimeAbbot abbot)) {
                return true;
            }
            r[0] += 0.55;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 5));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                Vec3 p = c.add(Math.cos(a) * rr, 0, Math.sin(a) * rr);
                if (inGap(c, p, set) || abbot.cheb(p) > abbot.reach() + 1) {
                    continue;
                }
                level.sendParticles(i % 3 == 0 ? CHERRY : ParticleTypes.CHERRY_LEAVES, p.x, p.y + 0.6 + (i % 4) * 0.5, p.z,
                        1, 0.1, 0.3, 0.1, 0.0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 0.9 && Math.abs(e.getY() - c.y) < 3.5 && !inGap(c, e.position(), set)
                        && hit.add(e.getUUID())) {
                    boss.strike(level, e, 5.0F, 0.4, 0.1);
                    e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, boss.phase() == 2 ? 40 : 30, 0), boss);
                    level.sendParticles(ParticleTypes.CHERRY_LEAVES, e.getX(), e.getY() + 1.4, e.getZ(), 12, 0.3, 0.4, 0.3, 0.0);
                }
            }
            return rr >= abbot.reach() * 1.45;
        };
    }

    /** The deck corners he steps between: four spots on the diagonals inside the roof posts (found once). */
    private List<Vec3> corners(ServerLevel level) {
        if (corners != null) {
            return corners;
        }
        List<Vec3> out = new ArrayList<>();
        double d = Math.min(9.0, reach() * 0.6);
        for (int sx = -1; sx <= 1; sx += 2) {
            for (int sz = -1; sz <= 1; sz += 2) {
                out.add(landingSpot(level, centre().add(sx * d, 0, sz * d)));
            }
        }
        corners = out;
        return out;
    }

    /** The corner nearest the target that he is not already standing at. */
    private @Nullable Vec3 pickCorner(ServerLevel level, @Nullable LivingEntity target) {
        Vec3 best = null;
        double bestD = Double.MAX_VALUE;
        for (Vec3 c : corners(level)) {
            if (flatDist(c, position()) < 3.0) {
                continue;
            }
            double d = target != null ? flatDist(c, target.position()) : getRandom().nextDouble();
            if (d < bestD) {
                bestD = d;
                best = c;
            }
        }
        return best;
    }

    private void stepToCorner(ServerLevel level, @Nullable LivingEntity target) {
        if (stepTo == null) {
            return;
        }
        level.sendParticles(ParticleTypes.CHERRY_LEAVES, getX(), getY() + 1.5, getZ(), 30, 0.6, 1.0, 0.6, 0.0);
        level.sendParticles(ParticleTypes.GUST, getX(), getY() + 1.0, getZ(), 1, 0, 0, 0, 0);
        teleportTo(stepTo.x, stepTo.y, stepTo.z);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
        faceToward(target != null ? target.position() : centre());
        level.sendParticles(ParticleTypes.CHERRY_LEAVES, stepTo.x, stepTo.y + 1.5, stepTo.z, 30, 0.6, 1.0, 0.6, 0.0);
        level.playSound(null, this, SoundEvents.BREEZE_LAND, SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.0F, 1.5F);
    }

    // ------------------------------------------------------------------ phase 3: the brass dragon

    private void awaken(ServerLevel level) {
        awakened = true;
        breathTimer = 50;
        addEffect(WayfarerBoss.wave(position(), 12, 0.55, 11.0F, SPIRIT));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("chime_abbot_dragon"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(BRASS_BIG, getX(), getY() + 4, getZ(), 80, 2.0, 2.0, 2.0, 0.0);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 4, getZ(), 40, 1.5, 1.5, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 3.0F, 0.9F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    /** The spirit dragon's head (particles) at {@code p}, looking along {@code dir}. */
    private void drawDragon(ServerLevel level, Vec3 p, Vec3 dir, boolean breathing) {
        Vec3 f = dir.multiply(1, 0, 1).lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : dir.multiply(1, 0, 1).normalize();
        Vec3 side = new Vec3(-f.z, 0, f.x);
        for (double a = -1.0; a <= 1.4; a += 0.6) {                        // skull and snout
            double w = a > 0.6 ? 0.35 : 0.6;
            Vec3 q = p.add(f.scale(a));
            level.sendParticles(BRASS_BIG, q.x, q.y, q.z, 2, w * 0.5, 0.25, w * 0.5, 0.0);
        }
        for (int s = -1; s <= 1; s += 2) {
            Vec3 eye = p.add(f.scale(0.4)).add(side.scale(s * 0.45)).add(0, 0.3, 0);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, eye.x, eye.y, eye.z, 1, 0, 0, 0, 0);
            Vec3 horn = p.add(f.scale(-0.9)).add(side.scale(s * 0.4)).add(0, 0.9, 0);
            level.sendParticles(BRASS, horn.x, horn.y, horn.z, 2, 0.05, 0.25, 0.05, 0.0);
            Vec3 whisker = p.add(f.scale(1.2)).add(side.scale(s * 0.8)).add(0, -0.3, 0);
            level.sendParticles(SPIRIT, whisker.x, whisker.y, whisker.z, 1, 0.1, 0.1, 0.1, 0.0);
        }
        for (double a = 1.5; a <= 6.0; a += 1.5) {                         // the ghostly neck trailing behind
            Vec3 q = p.subtract(f.scale(a)).add(0, Math.sin(a + tickCount * 0.3) * 0.4, 0);
            level.sendParticles(SPIRIT, q.x, q.y, q.z, 1, 0.2, 0.2, 0.2, 0.0);
        }
        if (breathing) {
            Vec3 m = p.add(f.scale(1.8)).add(0, -0.5, 0);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, m.x, m.y, m.z, 6, 0.3, 0.3, 0.3, 0.05);
            level.sendParticles(ParticleTypes.GUST, m.x, m.y - 0.6, m.z, 1, 0, 0, 0, 0);
        }
    }

    /**
     * Lanes across the deck (3, or 4 with three players or more), half width 1.6, at least 5.8 blocks of safe floor
     * between them; one of them runs through the target. The axis alternates between passes.
     */
    private void planLanes(ServerLevel level, @Nullable LivingEntity target) {
        lanes.clear();
        laneAlongX = breathCount++ % 2 == 0;
        int n = Math.min(4, 2 + scaledCount(1));
        double[][] patterns = n >= 4
                ? new double[][] {{-11.0, -3.5, 3.5, 11.0}, {-13.0, -5.5, 2.0, 9.5}, {-9.5, -2.0, 5.5, 13.0}}
                : new double[][] {{-9.0, 0.0, 9.0}, {-12.0, -3.0, 6.0}, {-6.0, 3.0, 12.0}};
        double scale = reach() / 15.0;
        double want = 0;
        if (target != null) {
            want = laneAlongX ? target.getZ() - centre().z : target.getX() - centre().x;
        }
        double[] best = patterns[0];
        double bestD = Double.MAX_VALUE;
        for (double[] pat : patterns) {
            for (double o : pat) {
                double d = Math.abs(o * scale - want);
                if (d < bestD) {
                    bestD = d;
                    best = pat;
                }
            }
        }
        List<Double> order = new ArrayList<>();
        for (double o : best) {
            order.add(o * scale);
        }
        java.util.Collections.shuffle(order, new java.util.Random(getRandom().nextLong()));
        lanes.addAll(order);
    }

    private Vec3 laneEnd(double offset, int end) {
        double half = reach() + 1.0;
        Vec3 c = centre();
        return laneAlongX ? new Vec3(c.x + end * half, c.y, c.z + offset) : new Vec3(c.x + offset, c.y, c.z + end * half);
    }

    /** Every lane outlined on the floor; the next one to fire (at time {@code now} of the passes) in red. */
    private void drawLanes(ServerLevel level, int now) {
        for (int i = 0; i < lanes.size(); i++) {
            int fireAt = 6 + i * 10;
            if (now >= fireAt + 8) {
                continue;
            }
            boolean next = now >= fireAt - 14;
            Vec3 a = laneEnd(lanes.get(i), -1);
            Vec3 b = laneEnd(lanes.get(i), 1);
            double len = flatDist(a, b);
            Vec3 side = laneAlongX ? new Vec3(0, 0, 1) : new Vec3(1, 0, 0);
            for (double d = 0; d <= len; d += 1.0) {
                Vec3 p = a.lerp(b, d / len);
                for (int s = -1; s <= 1; s += 2) {
                    Vec3 q = p.add(side.scale(s * LANE_HALF));
                    level.sendParticles(next ? RED : SPIRIT, q.x, q.y + 0.15, q.z, 1, 0.05, 0, 0.05, 0);
                }
                if (next && ((int) d) % 3 == 0) {
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.2, p.z, 1, 0.3, 0, 0.3, 0.0);
                }
            }
            if (next) {
                drawDragon(level, a.add(0, 2.2, 0), b.subtract(a), false);
            }
        }
    }

    /**
     * The passes: lane i fires at tick 6 + 10 i; the head crosses the deck in 8 ticks, breathing; whoever stands in the
     * lane when the head passes takes 13 and Slowness 2 s (once per lane). The lanes stay drawn until they fire.
     */
    private Effect breathPasses() {
        int[] t = {0};
        List<Set<UUID>> hit = new ArrayList<>();
        for (int i = 0; i < lanes.size(); i++) {
            hit.add(new HashSet<>());
        }
        List<Double> offs = List.copyOf(lanes);
        return (boss, level) -> {
            if (!(boss instanceof ChimeAbbot abbot) || boss.phase() == 1) {
                return true;
            }
            int k = t[0]++;
            if (k % 2 == 0) {
                abbot.drawLanes(level, k);
            }
            for (int i = 0; i < offs.size(); i++) {
                int s = k - (6 + i * 10);
                if (s < 0 || s > 8) {
                    continue;
                }
                Vec3 a = abbot.laneEnd(offs.get(i), -1);
                Vec3 b = abbot.laneEnd(offs.get(i), 1);
                Vec3 head = a.lerp(b, s / 8.0);
                Vec3 prev = a.lerp(b, Math.max(0, s - 1) / 8.0);
                abbot.drawDragon(level, head.add(0, 1.6, 0), b.subtract(a), true);
                for (double d = 0; d <= 1.0; d += 0.25) {
                    Vec3 p = prev.lerp(head, d);
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.5, p.z, 3, LANE_HALF * 0.5, 0.4, LANE_HALF * 0.5, 0.02);
                    level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 0.8, p.z, 1, LANE_HALF * 0.4, 0.3, LANE_HALF * 0.4, 0.02);
                }
                if (s == 0) {
                    level.playSound(null, a.x, a.y, a.z, SoundEvents.ENDER_DRAGON_SHOOT, SoundSource.HOSTILE, 3.0F, 0.8F);
                    level.playSound(null, a.x, a.y, a.z, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                }
                if (s == 4) {
                    level.playSound(null, head.x, head.y, head.z, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 2.5F, 1.2F);
                }
                for (Player p : abbot.fighters(level)) {
                    double across = abbot.laneAlongX ? p.getZ() - (abbot.centre().z + offs.get(i)) : p.getX() - (abbot.centre().x + offs.get(i));
                    double along = abbot.laneAlongX ? p.getX() : p.getZ();
                    double h0 = abbot.laneAlongX ? prev.x : prev.z;
                    double h1 = abbot.laneAlongX ? head.x : head.z;
                    boolean passed = along >= Math.min(h0, h1) - 2.0 && along <= Math.max(h0, h1) + 2.0;
                    if (Math.abs(across) <= LANE_HALF + p.getBbWidth() / 2 && passed && Math.abs(p.getY() - head.y) < 4.0
                            && hit.get(i).add(p.getUUID())) {
                        abbot.strike(level, p, 13.0F, 0.0, 0.2);
                        p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), boss);
                    }
                }
            }
            return k > 6 + offs.size() * 10 + 2;
        };
    }

    /** The spirit circling over the deck in phase 3 (when it is not breathing). */
    private void ambientDragon(ServerLevel level) {
        double a = tickCount * 0.05;
        double r = Math.min(10.0, reach() - 3.0);
        Vec3 c = centre();
        Vec3 p = c.add(Math.cos(a) * r, 7.5 + Math.sin(tickCount * 0.1) * 0.6, Math.sin(a) * r);
        Vec3 dir = new Vec3(-Math.sin(a), 0, Math.cos(a));
        drawDragon(level, p, dir, false);
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(BRASS, getX(), getY() + 2, getZ(), 6, 0.5, 0.8, 0.5, 0.0);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (phase() == 1 && awakened) {                                   // the fight was reset
            awakened = false;
            roarUntil = -1;
            breathCount = 0;
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("chime_abbot_dragon"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("chime_abbot_wrath"));
            }
        }
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!awakened && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "awaken");
            } else if (awakened && --breathTimer <= 0) {
                breathTimer = Math.max(140, (int) Math.round(BREATH_EVERY * cooldownScale()));
                chain(level, "breath");
            }
        }
        // ambience: petals drifting off him, the halo's glints, the chimes; the spirit dragon circling in phase 3
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.CHERRY_LEAVES, getX(), getY() + 2.5, getZ(), 1, 0.8, 0.6, 0.8, 0.0);
        }
        if (tickCount % 10 == 0) {
            level.sendParticles(BRASS, getX(), getY() + 2.9, getZ(), 1, 0.5, 0.5, 0.2, 0.0);
        }
        if (awakened && phase() == 2 && tickCount % 2 == 0 && (cur == null || !"breath".equals(cur.name))) {
            ambientDragon(level);
        }
        if (tickCount % 120 == 0) {
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 0.8F + getRandom().nextFloat() * 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("chime_abbot_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take the outward part back near the railing
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.CHERRY_LEAVES, getX(), getY() + 2, getZ(), 80, 3.0, 1.5, 3.0, 0.0);
        level.sendParticles(BRASS, getX(), getY() + 3, getZ(), 40, 1.5, 1.0, 1.5, 0.0);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.8F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.CHERRY_LEAVES, getX(), getY() + 2, getZ(), 150, 2.0, 2.0, 2.0, 0.0);
        level.sendParticles(BRASS_BIG, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.0);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("AbbotCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("AbbotRadius", radius);
        output.putBoolean("AbbotAwakened", awakened);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("AbbotCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("AbbotRadius", 16);
        awakened = input.getBooleanOr("AbbotAwakened", false) && phase() == 2;
        corners = null;
    }
}
