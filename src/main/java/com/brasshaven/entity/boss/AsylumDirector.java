package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
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
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.AsylumDirector.DISSECT;
import static com.brasshaven.generated.MobAnims.AsylumDirector.FORCEPS;
import static com.brasshaven.generated.MobAnims.AsylumDirector.HANDS;
import static com.brasshaven.generated.MobAnims.AsylumDirector.MIDNIGHT;
import static com.brasshaven.generated.MobAnims.AsylumDirector.PENDULUM;
import static com.brasshaven.generated.MobAnims.AsylumDirector.REWIND;
import static com.brasshaven.generated.MobAnims.AsylumDirector.ROAR;
import static com.brasshaven.generated.MobAnims.AsylumDirector.SAW;
import static com.brasshaven.generated.MobAnims.AsylumDirector.SCALPEL;
import static com.brasshaven.generated.MobAnims.AsylumDirector.SPIDERS;
import static com.brasshaven.generated.MobAnims.AsylumDirector.STAGGER;
import static com.brasshaven.generated.MobAnims.AsylumDirector.SYRINGE;
import static com.brasshaven.generated.MobAnims.AsylumDirector.TIMESLIP;

/**
 * La Directrice de l'asile (The Asylum Director), the champion of the Clockwork Asylum: a tall, thin surgeon (about 3.6
 * blocks) in a long stained white coat and a brass plague-doctor mask, a clockwork heart ticking behind a glass plate in
 * her chest, four spindly brass surgical arms (scalpel, bone saw, syringe, forceps) spread from her back like a spider's
 * legs, and a pocket watch on a chain. She waits in the clock stage at the top of the tower (a 35-block square behind
 * the four dials, the floor laid out as a clock face).
 * <ul>
 *     <li>Phase 1: the <b>scalpel</b> lunge down a drawn line, the <b>saw</b> sweep, the <b>syringe</b> dart (it slows),
 *     the <b>rewind</b> (a clock ghost marks where you stand; three seconds later you are snapped back to it, and its
 *     ring bursts 0.7 s after that), the <b>pendulum</b> (the great pendulum swings across the room along drawn lanes,
 *     each turned 45 degrees from the last) and the <b>spiders</b> (clockwork spiders, never more than four).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>forceps</b> grab and saw cut, the <b>dissection</b> (four quarters
 *     round her struck in turn, each drawn red before it falls), the <b>time-slip</b> behind you; the saw sweeps back,
 *     the syringe fires a fan, the rewind marks every player, the pendulum swings three times.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>midnight</b> once, then the great clock's
 *     <b>hands</b>: from the dial's centre an hour hand and a minute hand sweep three quarters of the way round, a
 *     quarter apart; stay in the gap between them and follow it. Chimes warn before they move.</li>
 * </ul>
 * She places no blocks. Every push is capped and never thrown outward near the walls or over the stairwell, and the
 * only loss of control is the rewind's snap (a teleport, nothing held).
 */
public class AsylumDirector extends WayfarerBoss {
    public static final float WIDTH = 1.2F;
    public static final float HEIGHT = 3.7F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SAW_RANGE = 5.5;
    private static final double SAW_HALF = 100;
    private static final double LANE_HALF = 1.5;
    private static final double BEAM_HALF = 0.9;
    private static final double GAP = 90.0;
    private static final int HANDS_LEAD = 10;
    private static final int HANDS_TURN = 170;
    private static final double HANDS_SPIN = 270.0;
    private static final int HANDS_EVERY = 360;
    private static final int REWIND_SNAP = 60;
    private static final int REWIND_BURST = 14;
    private static final DustParticleOptions RED = new DustParticleOptions(0xD0303C, 1.4F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xE0B050, 1.4F);
    private static final DustParticleOptions BRASS_BIG = new DustParticleOptions(0xD8A848, 2.4F);
    private static final DustParticleOptions WHITE = new DustParticleOptions(0xEEEAE0, 1.2F);
    private static final DustParticleOptions SERUM = new DustParticleOptions(0x78EC96, 1.3F);
    private static final DustParticleOptions GHOST = new DustParticleOptions(0xB8F0FF, 1.1F);

    private @Nullable Vec3 centre;
    private int radius = 17;
    private boolean wasPhaseTwo;
    /** Phase 3 has started (midnight struck). */
    private boolean struck;
    private int guard;
    private int roarUntil = -1;
    private int handsTimer = 50;
    /** Bumped on every reset: delayed rewinds from an earlier fight give up. */
    private int epoch;
    private final List<UUID> adds = new ArrayList<>();
    // scalpel lunge
    private @Nullable Vec3 lungeFrom;
    private @Nullable Vec3 lungeTo;
    private final Set<UUID> lungeHit = new HashSet<>();
    // pendulum lanes (degrees round the centre)
    private final List<Double> swings = new ArrayList<>();
    // forceps
    private @Nullable UUID held;
    // dissection: quarter order (0 front, 1 left, 2 back, 3 right of her facing at the start)
    private final List<Integer> quarters = new ArrayList<>();
    private float dissectYaw;
    // time-slip
    private @Nullable Vec3 slipTo;
    // the great hands: the minute hand's angle at the start (degrees, atan2(z, x)); the hour hand trails by GAP
    private double handsStart;
    private final Set<UUID> minuteHit = new HashSet<>();
    private final Set<UUID> hourHit = new HashSet<>();

    public AsylumDirector(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 13.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.25);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.AsylumDirector.TICKS;
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
        return 110.0F;
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

    // ------------------------------------------------------------------ arena memory (a square room)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Half width of the usable floor round the seal (the clock stage is 35 across inside). */
    private double reach() {
        return Math.max(6.0, Math.min(16.0, radius - 1.0));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Distance from the centre in the room's square metric. */
    private double cheb(Vec3 p) {
        return Math.max(Math.abs(p.x - centre().x), Math.abs(p.z - centre().z));
    }

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

    /** A standing spot at (x, z), level with the seal, with room for her above (4 blocks); or null. */
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

    private static Vec3 dirOf(double degrees) {
        double r = Math.toRadians(degrees);
        return new Vec3(Math.cos(r), 0, Math.sin(r));
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

    /** Removes the outward part of {@code push} near the walls (square room), all of it toward a drop. */
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
        for (double d = 1.0; d <= 2.0; d += 1.0) {
            Vec3 probe = e.position().add(push.normalize().scale(d));
            double fy = floorY(level, probe.x, e.getY(), probe.z);
            if (Double.isNaN(fy) || fy < e.getY() - 2.5) {
                return Vec3.ZERO;
            }
        }
        return new Vec3(px, 0, pz);
    }

    /** Pushes capped at 1.2 and lift at 0.45; near the walls or the stairwell the outward part is removed. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        strikeAlong(level, e, damage, e.position().subtract(position()), knockback, lift);
    }

    /** {@link #strike} with the push along {@code dir} instead of away from her. */
    private void strikeAlong(ServerLevel level, LivingEntity e, float damage, Vec3 dir, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        Vec3 flat = dir.multiply(1, 0, 1);
        if (knockback > 0 && flat.lengthSqr() > 1.0E-4) {
            push = safePush(level, e, flat.normalize().scale(Math.min(1.2, knockback)));
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
        // scalpel: the scalpel arm drawn back over her shoulder (0.7 s; she turns toward you for 0.5 s, then a red line
        // locks, at most 7 blocks and only over floor), then she lunges down it in 4 ticks: 13 to whoever is in the way
        out.add(BossAttack.of("scalpel").anim(SCALPEL).timing(14, 8, 14).range(2.5, 11.0).cooldown(70).weight(10)
                .track(false)
                .start((b, level, t, tick) -> {
                    lungeFrom = null;
                    lungeTo = null;
                    lungeHit.clear();
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 14.0F);
                    } else if (tick == 10) {
                        planLunge(level);
                        level.playSound(null, b, SoundEvents.TRIDENT_RETURN, SoundSource.HOSTILE, 1.5F, 1.4F);
                    }
                    if (tick % 2 == 0) {
                        if (lungeTo != null) {
                            drawSegment(level, position(), lungeTo, RED);
                        } else {
                            drawSegment(level, position(), ahead(7.0), WHITE);
                        }
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 1.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (lungeFrom == null || lungeTo == null || tick > 4) {
                        return;
                    }
                    Vec3 p = lungeFrom.lerp(lungeTo, Math.min(1.0, (tick + 1) / 5.0));
                    teleportTo(p.x, p.y, p.z);
                    setDeltaMovement(Vec3.ZERO);
                    getNavigation().stop();
                    for (LivingEntity e : victims(level, p, 2.5)) {
                        if (flatDist(e.position(), p) <= 1.4 + e.getBbWidth() / 2 && lungeHit.add(e.getUUID())) {
                            strikeAlong(level, e, 13.0F, lungeTo.subtract(lungeFrom), 0.6, 0.2);
                            level.sendParticles(ParticleTypes.CRIT, e.getX(), e.getY() + 1.2, e.getZ(), 10, 0.3, 0.4, 0.3, 0.1);
                        }
                    }
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 1, 0, 0, 0, 0);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 1.3F);
                    }
                })
                .build());
        // saw: the bone-saw arm raised high to her left (0.8 s; the wide arc drawn), swept across her front: 14.
        // Phase 2: she turns and sweeps back across at 1.5 s (11), the arc drawn again first
        out.add(BossAttack.of("saw").anim(SAW).timing(16, 24, 14).range(0, 6.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SAW_RANGE, SAW_HALF, BRASS);
                        b.telegraphArc(level, SAW_RANGE * 0.6, SAW_HALF, BRASS);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> sawCut(level, 14.0F))
                .active((b, level, t, tick) -> {
                    if (b.phase() != 2) {
                        return;
                    }
                    if (tick == 5) {
                        turnToward(t, 30.0F);
                    }
                    if (tick > 5 && tick < 14 && tick % 2 == 0) {
                        b.telegraphArc(level, SAW_RANGE, SAW_HALF, RED);
                    }
                    if (tick == 14) {
                        sawCut(level, 11.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 5.0 ? "dissect" : "forceps");
                    }
                })
                .build());
        // syringe: the syringe arm swings round to aim past her shoulder (0.9 s; a green line follows you for 0.6 s,
        // then locks red), then the dart: 1.5 blocks a tick, walls stop it; 8 and Slowness II 3 s. Phase 2: a fan of 3
        out.add(BossAttack.of("syringe").anim(SYRINGE).timing(18, 12, 12).range(5.0, 24.0).cooldown(80).weight(9)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick < 12) {
                        turnToward(t, 10.0F);
                    }
                    if (tick % 2 == 0) {
                        for (double a : dartAngles()) {
                            drawSegment(level, position(), position().add(rotate(forward(), a).scale(14.0)), tick < 12 ? SERUM : RED);
                        }
                    }
                    if (tick == 12) {
                        level.playSound(null, b, SoundEvents.BREWING_STAND_BREW, SoundSource.HOSTILE, 1.5F, 1.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 from = position().add(0, 2.4, 0);
                    for (double a : dartAngles()) {
                        b.addEffect(dart(from, rotate(forward(), a)));
                    }
                    level.playSound(null, b, SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 1.5F, 1.8F);
                })
                .build());
        // rewind: she raises the pocket watch and winds it back (1.0 s); a clock ghost forms at your feet (every player's
        // in phase 2) and runs backward for 3 s, chiming, then snaps you back to it; its ring (r 2) has been drawn the
        // whole time, red from the last 0.5 s, and bursts 0.7 s after the snap: 12. Step out of it
        out.add(BossAttack.of("rewind").anim(REWIND).timing(20, 8, 14).range(0, 28.0).cooldown(300).weight(7)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(GHOST, b.getX(), b.getY() + 3.0, b.getZ(), 2, 0.4, 0.4, 0.4, 0.0);
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 1.5F, 1.8F - tick * 0.04F);
                    }
                })
                .impact((b, level, t, tick) -> markRewinds(level, t))
                .build());
        // pendulum: the watch lifted high (1.2 s) while the great pendulum's lane is drawn through the room's centre
        // (red for the last 0.6 s before it swings); it swings across in 0.5 s: 14 and a shove out of the lane. The next
        // lane is turned 45 degrees and drawn as soon as the first swings. Two swings, three in phase 2
        out.add(BossAttack.of("pendulum").anim(PENDULUM).timing(24, 36, 14).range(0, 30.0).cooldown(320).weight(7)
                .track(false)
                .start((b, level, t, tick) -> planSwings(t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawSwings(level, tick - 24);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> b.addEffect(pendulumSwings()))
                .build());
        // spiders: she bends low and raps the floor with all four arms (0.9 s; sparks where they will crawl out): two
        // clockwork spiders (three in phase 2, +1 per 2 extra players), never more than four alive
        out.add(BossAttack.of("spiders").anim(SPIDERS).timing(18, 4, 14).range(0, 30.0).cooldown(480).weight(5)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 0.3, b.getZ(), 4, 2.0, 0.1, 2.0, 0.05);
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 1.5F, 1.2F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    spawnSpiders(level, b.phase() == 2 ? 3 : 2);
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 1.5F, 0.8F);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.0F, 1.8F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // forceps: the forceps arm shoots out down a red line (0.8 s, 7 long); the first one within it is seized (8),
        // hauled to her over 6 ticks and let go; the saw's arc is drawn and it cuts at 1.5 s (10, within 3.8)
        out.add(BossAttack.of("forceps").anim(FORCEPS).phaseTwo().timing(16, 22, 14).range(0, 8.0).cooldown(140).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawSegment(level, position(), ahead(7.0), RED);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 1.5F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> seize(level))
                .active((b, level, t, tick) -> {
                    if (tick >= 1 && tick <= 6) {
                        reel(level, tick == 6);
                    }
                    if (tick >= 6 && tick < 14 && tick % 2 == 0) {
                        b.telegraphArc(level, 3.8, 60, RED);
                    }
                    if (tick == 14) {
                        b.hitArc(level, 3.8, 60, 10.0F, 0.9);
                        Vec3 c = ahead(2.0);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 2, 0.5, 0.1, 0.5, 0);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 1.1F);
                    }
                })
                .build());
        // dissection: all four arms raised (0.8 s); the four quarters round her (r 4.5) are struck one after another at
        // 0.8, 1.2, 1.6 and 2.0 s (9 each); the next quarter is drawn red for 0.4 s before it falls, the one after it white
        out.add(BossAttack.of("dissect").anim(DISSECT).phaseTwo().timing(16, 30, 14).range(0, 5.0).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    quarters.clear();
                    for (int q = 0; q < 4; q++) {
                        quarters.add(q);
                    }
                    Collections.shuffle(quarters, new java.util.Random(getRandom().nextLong()));
                    dissectYaw = getYRot();
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawQuarters(level, tick - 16);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 1.2F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawQuarters(level, tick);
                    }
                    if (tick % 8 == 0 && tick / 8 < quarters.size()) {
                        strikeQuarter(level, quarters.get(tick / 8));
                    }
                })
                .build());
        // time-slip: she winds the watch and thins to a sliver (0.6 s; a clock ghost forms 2.5 blocks behind you),
        // vanishes and reappears there, then sweeps the saw
        out.add(BossAttack.of("timeslip").anim(TIMESLIP).phaseTwo().timing(12, 2, 8).range(7.0, 28.0).cooldown(180).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick <= 6 && t != null) {
                        Vec3 back = t.getLookAngle().multiply(1, 0, 1);
                        back = back.lengthSqr() < 1.0E-4 ? Vec3.ZERO : back.normalize().scale(-2.5);
                        slipTo = landingSpot(level, t.position().add(back));
                    }
                    if (slipTo != null && tick % 2 == 0) {
                        drawClock(level, slipTo, 1.4, -tick * 0.4, tick > 6 ? RED : GHOST);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (slipTo == null) {
                        return;
                    }
                    level.sendParticles(GHOST, getX(), getY() + 1.8, getZ(), 30, 0.4, 1.2, 0.4, 0.0);
                    teleportTo(slipTo.x, slipTo.y, slipTo.z);
                    setDeltaMovement(Vec3.ZERO);
                    getNavigation().stop();
                    faceToward(t != null ? t.position() : centre());
                    level.sendParticles(GHOST, slipTo.x, slipTo.y + 1.8, slipTo.z, 30, 0.4, 1.2, 0.4, 0.0);
                    level.playSound(null, b, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.6F);
                    level.playSound(null, b, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .end((b, level, t, tick) -> b.chain(level, "saw"))
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // midnight: she rises, arms spread like clock hands, her heart racing (2.0 s, invulnerable; twelve strokes of
        // the bell count down), then the great clock strikes: a ring to jump (11), she quickens, the hands' timer starts
        out.add(BossAttack.of("midnight").anim(MIDNIGHT).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> guard = 64)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        drawClock(level, b.position(), 2.0 + tick * 0.2, tick * 0.3, BRASS);
                    }
                    if (tick % 4 == 0 && tick > 0) {
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 0.5F + tick * 0.01F);
                    }
                    level.sendParticles(BRASS, b.getX(), b.getY() + 2.4, b.getZ(), 2, 0.4, 0.6, 0.4, 0.0);
                })
                .impact((b, level, t, tick) -> strikeMidnight(level))
                .build());
        // hands: she strides to the dial's centre and points (1.5 s; the two hands drawn red from her to the walls, the
        // gap between them in gold, a chime every half second); 0.5 s later they sweep 270 degrees round in 8.5 s, a
        // quarter apart; she turns with them. Each hand that crosses you deals 12 once. Stay in the gap and follow it
        out.add(BossAttack.of("hands").anim(HANDS).phaseTwo().timing(30, HANDS_LEAD + HANDS_TURN, 16).range(999, 999)
                .cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> startHands(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawHands(level, handsStart, true);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, centre().x, centre().y + 3, centre().z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE,
                                3.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> tickHands(level, tick))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void drawSegment(ServerLevel level, Vec3 a, Vec3 b, DustParticleOptions dust) {
        double len = flatDist(a, b);
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = a.lerp(b, d / len);
            level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
        }
    }

    /** The lunge's end: up to 7 blocks ahead, stopping before any spot that is not floor level with the seal. */
    private void planLunge(ServerLevel level) {
        lungeFrom = position();
        Vec3 end = position();
        for (double d = 0.5; d <= 7.0; d += 0.5) {
            Vec3 p = position().add(forward().scale(d));
            if (cheb(p) > reach() - 1.0 || safeSpot(level, p.x, p.z) == null) {
                break;
            }
            end = new Vec3(p.x, centre().y, p.z);
        }
        lungeTo = end;
    }

    private void sawCut(ServerLevel level, float damage) {
        hitArc(level, SAW_RANGE, SAW_HALF, damage, 0.9);
        for (double a = -SAW_HALF; a <= SAW_HALF; a += 15) {
            Vec3 p = position().add(rotate(forward(), a).scale(SAW_RANGE - 1.0));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.4, p.z, 2, 0.1, 0.2, 0.1, 0.05);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 2, 0.6, 0.1, 0.6, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.8F);
    }

    private double[] dartAngles() {
        return phase() == 2 ? new double[] {-12, 0, 12} : new double[] {0};
    }

    /** A syringe dart flying 1.5 blocks a tick (24 at most); walls stop it; the first one it meets: 8 and Slowness II 3 s. */
    private Effect dart(Vec3 from, Vec3 dir) {
        Vec3[] pos = {from};
        double[] flown = {0};
        return (boss, level) -> {
            for (int s = 0; s < 3; s++) {
                Vec3 p = pos[0].add(dir.scale(0.5));
                pos[0] = p;
                flown[0] += 0.5;
                BlockPos bp = BlockPos.containing(p);
                if (!level.getBlockState(bp).getCollisionShape(level, bp).isEmpty() || flown[0] > 24.0) {
                    level.sendParticles(SERUM, p.x, p.y, p.z, 8, 0.2, 0.2, 0.2, 0.0);
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 0.8F, 1.6F);
                    return true;
                }
                for (LivingEntity e : boss.victims(level, p, 2.5)) {
                    if (e.getBoundingBox().inflate(0.4).contains(p)) {
                        boss.strike(level, e, 8.0F, 0.2, 0.0);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), boss);
                        level.sendParticles(SERUM, p.x, p.y, p.z, 14, 0.3, 0.3, 0.3, 0.0);
                        level.playSound(null, p.x, p.y, p.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.0F, 1.8F);
                        return true;
                    }
                }
            }
            level.sendParticles(SERUM, pos[0].x, pos[0].y, pos[0].z, 2, 0.02, 0.02, 0.02, 0.0);
            level.sendParticles(ParticleTypes.END_ROD, pos[0].x, pos[0].y, pos[0].z, 1, 0, 0, 0, 0);
            return false;
        };
    }

    /** A clock face on the floor at {@code c}: a ring, twelve marks and two hands at {@code turn} radians. */
    private void drawClock(ServerLevel level, Vec3 c, double r, double turn, DustParticleOptions dust) {
        telegraphRing(level, c, r, dust);
        for (int h = 0; h < 12; h++) {
            double a = h * Math.PI / 6;
            level.sendParticles(WHITE, c.x + Math.cos(a) * r * 0.8, c.y + 0.2, c.z + Math.sin(a) * r * 0.8, 1, 0, 0, 0, 0);
        }
        for (int k = 0; k < 2; k++) {
            double a = k == 0 ? turn : turn / 12.0;
            double len = k == 0 ? r * 0.75 : r * 0.5;
            for (double d = 0.25; d <= len; d += 0.25) {
                level.sendParticles(ParticleTypes.END_ROD, c.x + Math.cos(a) * d, c.y + 0.2, c.z + Math.sin(a) * d, 1, 0, 0, 0, 0);
            }
        }
    }

    private void markRewinds(ServerLevel level, @Nullable LivingEntity target) {
        List<Player> marked = new ArrayList<>();
        if (phase() == 2) {
            for (Player p : fighters(level)) {
                if (marked.size() < 4) {
                    marked.add(p);
                }
            }
        } else if (target instanceof Player p) {
            marked.add(p);
        }
        for (Player p : marked) {
            double y = p.onGround() ? p.getY() : floorY(level, p.getX(), p.getY(), p.getZ());
            if (Double.isNaN(y) || p.getY() - y > 4.0) {
                continue;
            }
            addEffect(rewind(p.getUUID(), new Vec3(p.getX(), y, p.getZ())));
        }
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, this, SoundEvents.ENDER_EYE_DEATH, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /**
     * One player's clock ghost: it runs backward for {@link #REWIND_SNAP} ticks (a tick every 10, chimes at the end),
     * then snaps the player back to it (a teleport only, if they moved more than a block and are still in the room); its
     * ring (r 2) bursts {@link #REWIND_BURST} ticks later: 12 to everyone inside.
     */
    private Effect rewind(UUID who, Vec3 ghost) {
        int[] t = {0};
        int born = epoch;
        return (boss, level) -> {
            if (!(boss instanceof AsylumDirector d) || d.epoch != born) {
                return true;
            }
            int k = t[0]++;
            if (k % 2 == 0) {
                d.drawClock(level, ghost, 1.2, -k * 0.35, GHOST);
                boss.telegraphRing(level, ghost, 2.0, k >= REWIND_SNAP - 10 ? RED : BRASS);
                for (double y = 0.3; y <= 1.8; y += 0.3) {
                    level.sendParticles(GHOST, ghost.x, ghost.y + y, ghost.z, 1, 0.15, 0.05, 0.15, 0.0);
                }
            }
            if (k < REWIND_SNAP && k % 10 == 0) {
                level.playSound(null, ghost.x, ghost.y, ghost.z, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 2.0F, 1.6F);
            }
            if (k == REWIND_SNAP - 10 || k == REWIND_SNAP - 5) {
                level.playSound(null, ghost.x, ghost.y, ghost.z, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 2.5F, 1.2F);
            }
            if (k == REWIND_SNAP) {
                Player p = level.getPlayerByUUID(who);
                if (p instanceof ServerPlayer sp && sp.isAlive() && !sp.isSpectator() && sp.level() == level
                        && flatDist(sp.position(), ghost) > 1.0 && flatDist(sp.position(), d.centre()) <= d.radius + 6) {
                    Vec3 from = sp.position();
                    for (double f = 0; f <= 1.0; f += 0.1) {
                        Vec3 q = from.lerp(ghost, f);
                        level.sendParticles(GHOST, q.x, q.y + 1.0, q.z, 1, 0.05, 0.05, 0.05, 0.0);
                    }
                    sp.teleportTo(level, ghost.x, ghost.y, ghost.z, Set.of(), sp.getYRot(), sp.getXRot(), false);
                    sp.setDeltaMovement(Vec3.ZERO);
                    sp.hurtMarked = true;
                    sp.fallDistance = 0;
                    level.playSound(null, ghost.x, ghost.y, ghost.z, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.5F);
                }
                level.playSound(null, ghost.x, ghost.y, ghost.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 1.4F);
            }
            if (k == REWIND_SNAP + REWIND_BURST) {
                for (LivingEntity e : boss.victims(level, ghost, 3.0)) {
                    if (flatDist(e.position(), ghost) <= 2.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - ghost.y) < 2.5) {
                        d.strikeAlong(level, e, 12.0F, e.position().subtract(ghost), 0.5, 0.4);
                    }
                }
                level.sendParticles(BRASS_BIG, ghost.x, ghost.y + 0.6, ghost.z, 30, 1.0, 0.4, 1.0, 0.0);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, ghost.x, ghost.y + 0.5, ghost.z, 20, 1.0, 0.5, 1.0, 0.1);
                level.playSound(null, ghost.x, ghost.y, ghost.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 1.6F);
                return true;
            }
            return false;
        };
    }

    // ---- the pendulum

    private int swingCount() {
        return phase() == 2 ? 3 : 2;
    }

    private void planSwings(@Nullable LivingEntity t) {
        swings.clear();
        double a = getRandom().nextDouble() * 180.0;
        if (t != null && flatDist(t.position(), centre()) > 2.0) {
            a = Math.toDegrees(Math.atan2(t.getZ() - centre().z, t.getX() - centre().x));
        }
        double step = getRandom().nextBoolean() ? 45.0 : -45.0;
        for (int k = 0; k < swingCount(); k++) {
            swings.add(a + k * step);
        }
    }

    /** Half the chord through the centre at angle {@code a} (to the walls of the square room). */
    private double chord(double a) {
        Vec3 d = dirOf(a);
        return (reach() - 0.5) / Math.max(Math.abs(d.x), Math.abs(d.z));
    }

    private Vec3 swingEnd(double a, int end) {
        return centre().add(dirOf(a).scale(end * chord(a)));
    }

    /** Swing k starts at time 12 k (time 0 = the impact); its lane is drawn from 24 ticks before, red the last 12. */
    private void drawSwings(ServerLevel level, int now) {
        for (int k = 0; k < swings.size(); k++) {
            int start = 12 * k;
            if (now < start - 24 || now >= start + 10) {
                continue;
            }
            boolean hot = now >= start - 12;
            double a = swings.get(k);
            Vec3 e0 = swingEnd(a, -1);
            Vec3 e1 = swingEnd(a, 1);
            Vec3 side = dirOf(a + 90);
            double len = flatDist(e0, e1);
            for (double d = 0; d <= len; d += 1.0) {
                Vec3 p = e0.lerp(e1, d / len);
                for (int s = -1; s <= 1; s += 2) {
                    Vec3 q = p.add(side.scale(s * LANE_HALF));
                    level.sendParticles(hot ? RED : BRASS, q.x, q.y + 0.15, q.z, 1, 0.05, 0, 0.05, 0);
                }
            }
        }
    }

    private Effect pendulumSwings() {
        int[] t = {0};
        List<Double> lanes = List.copyOf(swings);
        List<Set<UUID>> hit = new ArrayList<>();
        for (int i = 0; i < lanes.size(); i++) {
            hit.add(new HashSet<>());
        }
        return (boss, level) -> {
            if (!(boss instanceof AsylumDirector d)) {
                return true;
            }
            int k = t[0]++;
            if (k % 2 == 0) {
                d.drawSwings(level, k);
            }
            Vec3 c = d.centre();
            Vec3 pivot = c.add(0, 16.0, 0);
            for (int i = 0; i < lanes.size(); i++) {
                int s = k - 12 * i;
                if (s < 0 || s > 10) {
                    continue;
                }
                int dir = i % 2 == 0 ? 1 : -1;
                double a = lanes.get(i);
                Vec3 e0 = d.swingEnd(a, -dir);
                Vec3 e1 = d.swingEnd(a, dir);
                double f0 = Math.max(0, s - 1) / 10.0;
                double f1 = s / 10.0;
                Vec3 bob = e0.lerp(e1, f1);
                Vec3 prev = e0.lerp(e1, f0);
                double lift = Math.abs(f1 - 0.5) * 2.0 * 3.0;                 // the bob rises at the ends of its arc
                level.sendParticles(BRASS_BIG, bob.x, bob.y + 1.0 + lift, bob.z, 6, 0.5, 0.5, 0.5, 0.0);
                level.sendParticles(ParticleTypes.CRIT, bob.x, bob.y + 1.0 + lift, bob.z, 4, 0.6, 0.6, 0.6, 0.1);
                for (double f = 0.2; f < 1.0; f += 0.2) {
                    Vec3 q = pivot.lerp(bob.add(0, 1.0 + lift, 0), f);
                    level.sendParticles(BRASS, q.x, q.y, q.z, 1, 0.05, 0.05, 0.05, 0.0);
                }
                if (s == 0) {
                    level.playSound(null, bob.x, bob.y, bob.z, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                }
                if (s == 5) {
                    level.playSound(null, c.x, c.y + 2, c.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, c.x, c.y + 2, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0F, 0.5F);
                }
                Vec3 u = dirOf(a);
                Vec3 side = dirOf(a + 90);
                double h0 = prev.subtract(c).dot(u);
                double h1 = bob.subtract(c).dot(u);
                for (LivingEntity e : boss.victims(level, bob, d.reach() * 2.2)) {
                    Vec3 to = e.position().subtract(c);
                    double along = to.dot(u);
                    double across = to.dot(side);
                    if (Math.abs(across) <= LANE_HALF + e.getBbWidth() / 2 && along >= Math.min(h0, h1) - 1.5
                            && along <= Math.max(h0, h1) + 1.5 && Math.abs(e.getY() - c.y) < 3.5 && hit.get(i).add(e.getUUID())) {
                        d.strikeAlong(level, e, 14.0F, side.scale(across >= 0 ? 1 : -1), 1.0, 0.3);
                    }
                }
            }
            return k > 12 * (lanes.size() - 1) + 11;
        };
    }

    // ---- spiders

    private int liveAdds(ServerLevel level) {
        adds.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        return adds.size();
    }

    private void spawnSpiders(ServerLevel level, int base) {
        int n = Math.min(4 - liveAdds(level), scaledCount(base));
        for (int i = 0; i < n; i++) {
            Mob mob = ModEntities.CLOCKWORK_SPIDER.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                at = safeSpot(level, getX() + Math.cos(a) * 3.0, getZ() + Math.sin(a) * 3.0);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + 0.5, at.z, 15, 0.4, 0.3, 0.4, 0.05);
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

    // ---- forceps

    private void seize(ServerLevel level) {
        held = null;
        Vec3 fwd = forward();
        LivingEntity best = null;
        double bestAlong = 99;
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= 7.0 && side <= 0.9 + e.getBbWidth() / 2 && along < bestAlong) {
                best = e;
                bestAlong = along;
            }
        }
        for (double d = 1.0; d <= 7.0; d += 0.5) {
            Vec3 p = ahead(d);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.4, p.z, 1, 0.02, 0.02, 0.02, 0.0);
        }
        level.playSound(null, this, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 1.5F, 1.6F);
        if (best != null) {
            strikeAlong(level, best, 8.0F, Vec3.ZERO, 0.0, 0.0);
            held = best.getUUID();
            level.playSound(null, best, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 1.2F);
        }
    }

    /** The seized one is hauled to 1.6 blocks in front of her over 6 ticks, then let go. */
    private void reel(ServerLevel level, boolean last) {
        if (held == null) {
            return;
        }
        var ent = level.getEntity(held);
        if (!(ent instanceof LivingEntity e) || !e.isAlive()) {
            held = null;
            return;
        }
        Vec3 to = ahead(1.6).subtract(e.position()).multiply(1, 0, 1);
        double dist = to.length();
        Vec3 v = dist < 0.3 ? Vec3.ZERO : to.normalize().scale(Math.min(1.0, dist * 0.45));
        e.setDeltaMovement(v.x, Math.min(e.getDeltaMovement().y, 0.1), v.z);
        e.hurtMarked = true;
        level.sendParticles(ParticleTypes.CRIT, e.getX(), e.getY() + 1.2, e.getZ(), 2, 0.2, 0.2, 0.2, 0.0);
        if (last) {
            held = null;
        }
    }

    // ---- dissection

    private Vec3 quarterDir(int q) {
        float yaw = (dissectYaw + q * 90.0F) * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** The next quarter (struck at 8 i) red for the 8 ticks before; the one after it white. */
    private void drawQuarters(ServerLevel level, int now) {
        for (int i = 0; i < quarters.size(); i++) {
            int at = 8 * i;
            DustParticleOptions dust = now >= at - 8 && now < at ? RED : now >= at - 16 && now < at - 8 ? WHITE : null;
            if (dust == null) {
                continue;
            }
            Vec3 mid = quarterDir(quarters.get(i));
            for (double a = -45; a <= 45; a += 9) {
                Vec3 d = rotate(mid, a);
                for (double r = 1.5; r <= 4.5; r += 1.5) {
                    if (r == 4.5 || Math.abs(a) == 45) {
                        Vec3 p = position().add(d.scale(r));
                        level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                    }
                }
            }
        }
    }

    private void strikeQuarter(ServerLevel level, int q) {
        Vec3 mid = quarterDir(q);
        double cos = Math.cos(Math.toRadians(45));
        for (LivingEntity e : victims(level, position(), 5.5)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= 4.5 + e.getBbWidth() / 2 && (d < 0.8 || to.normalize().dot(mid) >= cos)) {
                strike(level, e, 9.0F, 0.6, 0.2);
            }
        }
        Vec3 p = position().add(mid.scale(2.5));
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 2, 0.6, 0.2, 0.6, 0);
        level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.0, p.z, 12, 1.0, 0.4, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 1.5F, 1.0F + q * 0.1F);
    }

    // ------------------------------------------------------------------ phase 3: the great clock

    private void strikeMidnight(ServerLevel level) {
        struck = true;
        handsTimer = 50;
        addEffect(WayfarerBoss.wave(position(), 14, 0.55, 11.0F, BRASS));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("asylum_director_midnight"),
                    0.12, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(BRASS_BIG, getX(), getY() + 3, getZ(), 80, 2.0, 2.0, 2.0, 0.0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 40, 1.5, 1.5, 1.5, 0.1);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    /** She goes to the dial's centre; the minute hand starts 45 degrees ahead of the target, so it starts in the gap. */
    private void startHands(ServerLevel level, @Nullable LivingEntity t) {
        minuteHit.clear();
        hourHit.clear();
        Vec3 spot = landingSpot(level, centre());
        level.sendParticles(GHOST, getX(), getY() + 1.8, getZ(), 30, 0.4, 1.2, 0.4, 0.0);
        teleportTo(spot.x, spot.y, spot.z);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
        double a = getRandom().nextDouble() * 360.0;
        if (t != null && flatDist(t.position(), centre()) > 1.5) {
            a = Math.toDegrees(Math.atan2(t.getZ() - centre().z, t.getX() - centre().x));
        }
        handsStart = a + GAP / 2;
        faceToward(centre().add(dirOf(handsStart)));
        level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /** Length of a hand at angle {@code a}: from the centre to the wall. */
    private double handLength(double a) {
        return chord(a);
    }

    /** Both hands (the minute hand at {@code minute}, the hour hand GAP behind it); the gap between them in gold. */
    private void drawHands(ServerLevel level, double minute, boolean warn) {
        Vec3 c = centre();
        for (int k = 0; k < 2; k++) {
            double a = k == 0 ? minute : minute - GAP;
            Vec3 u = dirOf(a);
            double len = handLength(a);
            for (double d = 1.0; d <= len; d += warn ? 1.0 : 0.7) {
                Vec3 p = c.add(u.scale(d));
                level.sendParticles(RED, p.x, p.y + 0.2, p.z, 1, 0.05, 0, 0.05, 0);
                if (!warn && ((int) (d * 10)) % 3 == 0) {
                    level.sendParticles(k == 0 ? ParticleTypes.END_ROD : ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 0.6 + (d % 2.0),
                            p.z, 1, 0.05, 0.4, 0.05, 0.0);
                }
            }
        }
        if (warn || tickCount % 4 == 0) {
            for (double r = 4.0; r <= 12.0; r += 4.0) {
                for (double a = minute - GAP + 10; a <= minute - 10; a += 80.0 / r) {
                    Vec3 p = c.add(dirOf(a).scale(r));
                    level.sendParticles(BRASS, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                }
            }
        }
    }

    private void tickHands(ServerLevel level, int tick) {
        double turn = tick <= HANDS_LEAD ? 0 : Math.min(HANDS_SPIN, (tick - HANDS_LEAD) * HANDS_SPIN / HANDS_TURN);
        double minute = handsStart + turn;
        drawHands(level, minute, tick <= HANDS_LEAD);
        if (tick < HANDS_LEAD && tick % 5 == 0) {
            level.playSound(null, centre().x, centre().y + 3, centre().z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.8F);
        }
        if (tick <= HANDS_LEAD) {
            return;
        }
        faceToward(centre().add(dirOf(minute)));
        if ((tick - HANDS_LEAD) % 19 == 0) {
            level.playSound(null, centre().x, centre().y + 3, centre().z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 0.5F);
        }
        if (tick % 10 == 0) {
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 2.0F, 0.8F);
        }
        Vec3 c = centre();
        for (int k = 0; k < 2; k++) {
            double a = k == 0 ? minute : minute - GAP;
            Set<UUID> hit = k == 0 ? minuteHit : hourHit;
            Vec3 u = dirOf(a);
            Vec3 side = dirOf(a + 90);
            double len = handLength(a);
            for (LivingEntity e : victims(level, c, reach() + 3)) {
                Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                double along = to.dot(u);
                double across = to.dot(side);
                if (along >= 0.6 && along <= len + 0.5 && Math.abs(across) <= BEAM_HALF + e.getBbWidth() / 2
                        && Math.abs(e.getY() - c.y) < 3.0 && hit.add(e.getUUID())) {
                    strikeAlong(level, e, 12.0F, side.scale(across >= 0 ? 1 : -1), 0.5, 0.2);
                    level.sendParticles(ParticleTypes.CRIT, e.getX(), e.getY() + 1.0, e.getZ(), 10, 0.3, 0.4, 0.3, 0.1);
                }
            }
        }
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

    private void cleanUp(ServerLevel level) {
        epoch++;
        discardAdds(level);
        held = null;
    }

    /** Back to the first phase (the fight was reset): base speed, no spiders, no pending rewinds. */
    private void resetForm(ServerLevel level) {
        wasPhaseTwo = false;
        struck = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("asylum_director_midnight"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("asylum_director_wrath"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        if (phase() == 1 && (wasPhaseTwo || struck)) {
            resetForm(level);
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && !adds.isEmpty()) {
            cleanUp(level);
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!struck && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "midnight");
            } else if (struck && --handsTimer <= 0) {
                handsTimer = Math.max(200, (int) Math.round(HANDS_EVERY * cooldownScale()));
                chain(level, "hands");
            }
        }
        // ambience: the heart ticking, a glint off the lenses, the great clock's tick in phase 3
        if (tickCount % 20 == 0) {
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 0.6F, 1.9F);
        }
        if (tickCount % 6 == 0) {
            level.sendParticles(SERUM, getX(), getY() + 3.2, getZ(), 1, 0.2, 0.1, 0.2, 0.0);
        }
        if (struck && phase() == 2 && tickCount % 40 == 0) {
            level.playSound(null, centre().x, centre().y + 6, centre().z, SoundEvents.NOTE_BLOCK_BASEDRUM.value(), SoundSource.HOSTILE,
                    2.0F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        wasPhaseTwo = true;
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        held = null;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("asylum_director_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take the outward part back near the walls and the stairwell
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 60, 2.0, 1.5, 2.0, 0.1);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 1.2F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(BRASS_BIG, getX(), getY() + 2, getZ(), 100, 1.5, 2.0, 1.5, 0.0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 60, 1.0, 1.5, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            cleanUp(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("DirectorCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("DirectorRadius", radius);
        output.putBoolean("DirectorStruck", struck);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("DirectorCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("DirectorRadius", 17);
        struck = input.getBooleanOr("DirectorStruck", false) && phase() == 2;
        wasPhaseTwo = phase() == 2;
        adds.clear();
    }
}
