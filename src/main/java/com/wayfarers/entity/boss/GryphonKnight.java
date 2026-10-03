package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.projectile.hurtingprojectile.windcharge.WindCharge;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.GryphonKnight.DIVE;
import static com.wayfarers.generated.MobAnims.GryphonKnight.FLY;
import static com.wayfarers.generated.MobAnims.GryphonKnight.GUST;
import static com.wayfarers.generated.MobAnims.GryphonKnight.LAND;
import static com.wayfarers.generated.MobAnims.GryphonKnight.PECK;
import static com.wayfarers.generated.MobAnims.GryphonKnight.POUNCE;
import static com.wayfarers.generated.MobAnims.GryphonKnight.RAKE;
import static com.wayfarers.generated.MobAnims.GryphonKnight.ROAR;
import static com.wayfarers.generated.MobAnims.GryphonKnight.STAGGER;
import static com.wayfarers.generated.MobAnims.GryphonKnight.STORM;
import static com.wayfarers.generated.MobAnims.GryphonKnight.SWEEP;
import static com.wayfarers.generated.MobAnims.GryphonKnight.TAKEOFF;
import static com.wayfarers.generated.MobAnims.GryphonKnight.VOLLEY;

/**
 * Le Chevalier-griffon (The Gryphon Knight): boss of the Sky Island, guardian of the sky temple.
 *
 * <p>Ground moveset (phase 1): a three-beat beak peck combo, a rearing claw rake, a pouncing leap (gap closer),
 * a wind blast (a travelling cone of wind), a tail spin against flankers, and the take-off.</p>
 *
 * <p>Air phase: the gryphon flies on its own controller (no gravity, always inside the arena): it soars around
 * the target, then mixes telegraphed dives along a line (talons first, low swoop = punish window) and feather
 * volleys (warned impact spots), and finally lands with a gust shockwave ring (jump it) and a long recovery.</p>
 *
 * <p>Phase 2 (after the roar): the storm (lightning on telegraphed spots), longer air phases, double dives,
 * stray bolts while it flies, wind charges in the wind blast, the peck combo chaining into the rake.</p>
 *
 * <p>Private helpers (the engine has no flight): the flight controller ({@link #flightTick}), the facing
 * override ({@link #tick}), and the {@link #quill}, {@link #bolt} and {@link #gustWall} effects.</p>
 */
public class GryphonKnight extends WayfarerBoss {
    public static final float WIDTH = 2.6F;
    public static final float HEIGHT = 3.6F;

    private static final int CLIMB = 0;
    private static final int CIRCLE = 1;
    private static final int HOVER = 2;
    private static final int DIVING = 3;
    private static final int DESCEND = 4;
    private static final double CRUISE = 8.5;
    private static final Set<String> AIR_MOVES = Set.of("takeoff", "takeoff2", "soar", "dive", "volley", "land");

    private boolean airborne;
    private int flightMode = CLIMB;
    private int animUntil;
    private int airActions;
    private int divesInRow;
    private double circleAngle;
    private int circleDir = 1;
    private @Nullable Vec3 flyGoal;
    private @Nullable Vec3 diveEnd;
    private @Nullable Vec3 landSpot;
    private final Set<UUID> diveHits = new HashSet<>();
    private final List<Vec3> marks = new ArrayList<>();
    private @Nullable Float faceYaw;
    private @Nullable BlockPos arenaCenter;
    private int arenaRadius = 16;

    public GryphonKnight(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.GryphonKnight.TICKS;
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
        return 75.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.8;
    }

    // ------------------------------------------------------------------ arena bookkeeping (flight bounds)

    @Override
    public void setArena(BlockPos center, int radius, @Nullable BlockPos sealPos) {
        super.setArena(center, radius, sealPos);
        arenaCenter = center.immutable();
        arenaRadius = radius;
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long h = input.getLongOr("BossHome", Long.MIN_VALUE);
        arenaCenter = h == Long.MIN_VALUE ? null : BlockPos.of(h);
        arenaRadius = input.getIntOr("BossArena", 16);
    }

    private BlockPos center() {
        if (arenaCenter == null) {
            arenaCenter = blockPosition();
        }
        return arenaCenter;
    }

    private double groundY() {
        return center().getY();
    }

    /** Keep a point inside the arena (horizontal circle of radius - margin around the centre). */
    private Vec3 clamp(Vec3 p, double margin) {
        BlockPos c = center();
        double cx = c.getX() + 0.5;
        double cz = c.getZ() + 0.5;
        double dx = p.x - cx;
        double dz = p.z - cz;
        double r = Math.sqrt(dx * dx + dz * dz);
        double max = Math.max(2.0, arenaRadius - margin);
        if (r > max) {
            dx *= max / r;
            dz *= max / r;
        }
        return new Vec3(cx + dx, p.y, cz + dz);
    }

    private Vec3 ground(Vec3 p) {
        return new Vec3(p.x, groundY(), p.z);
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // three pecks: 0.55 s, 0.95 s and a heavy one at 1.5 s
        out.add(BossAttack.of("peck").anim(PECK).timing(11, 20, 13).range(0, 5.0).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.0, 35, ParticleTypes.CRIT);
                    }
                })
                .impact((b, level, t, tick) -> peck(level, 4.5, 9.0F, 0.5))
                .active((b, level, t, tick) -> {
                    if (tick == 8) {
                        peck(level, 4.5, 9.0F, 0.5);
                    } else if (tick == 3 || tick == 14) {
                        b.telegraphArc(level, 5.0, 40, ParticleTypes.CRIT);
                    } else if (tick == 19) {
                        peck(level, 5.5, 15.0F, 1.3);
                        Vec3 p = b.ahead(3.5);
                        level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.4, p.z, 1, 0, 0, 0, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceToSqr(t) < 30 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "rake");
                    }
                })
                .build());
        // rears on the lion legs, both talons rake down (0.85 s)
        out.add(BossAttack.of("rake").anim(RAKE).timing(17, 3, 18).range(0, 5.5).cooldown(60).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.0, 70, ParticleTypes.CRIT);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.PHANTOM_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 5.0, 75, 16.0F, 1.3);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.RAVAGER_ATTACK, SoundSource.HOSTILE, 1.5F, 1.2F);
                    Vec3 p = b.ahead(2.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.0, p.z, 4, 1.5, 0.3, 1.5, 0);
                })
                .build());
        // gap closer: crouch, leap on the target, land talons first (leap 0.6 s, landing 1.15 s)
        out.add(BossAttack.of("pounce").anim(POUNCE).timing(12, 11, 13).range(6.0, 18.0).cooldown(90).weight(10)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 3.0, ParticleTypes.CRIT);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(2.0, dist * 0.16), 0.55);
                    level.playSound(null, b, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 2.0F, 0.9F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 10) {
                        b.hitCircle(level, b.position(), 3.2, 14.0F, 1.0, 0.4);
                        level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.2, b.getZ(), 40, 1.8, 0.1, 1.8, 0.15);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .build());
        // wind blast: rears and beats the wings forward, a cone of wind sweeps the floor (0.9 s)
        out.add(BossAttack.of("gust").anim(GUST).timing(18, 6, 12).range(0, 13.0).cooldown(110).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 7.0, 30, ParticleTypes.CLOUD);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BREEZE_INHALE, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 dir = b.forward();
                    b.addEffect(gustWall(b.ahead(1.5), dir, 14, 0.9, 9.0F));
                    level.playSound(null, b.getX(), b.getY(), b.getZ(), SoundEvents.WIND_CHARGE_BURST, SoundSource.HOSTILE, 3.0F, 0.6F);
                    if (b.phase() == 2) {
                        for (int k = -1; k <= 1; k++) {
                            float yaw = b.getYRot() + k * 22.0F;
                            Vec3 d = new Vec3(-Mth.sin(yaw * Mth.DEG_TO_RAD), -0.05, Mth.cos(yaw * Mth.DEG_TO_RAD));
                            WindCharge charge = new WindCharge(level, b.getX() + d.x * 2, b.getY() + 2.0, b.getZ() + d.z * 2, d);
                            charge.setOwner(b);
                            level.addFreshEntity(charge);
                        }
                    }
                })
                .build());
        // tail spin against whoever hugs its flanks (0.65 s), does not turn first
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(13, 3, 14).range(0, 4.2).cooldown(70).weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.6, ParticleTypes.CLOUD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.8, 11.0F, 1.5, 0.35);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.4F);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX(), b.getY() + 1.0, b.getZ(), 6, 2.5, 0.2, 2.5, 0);
                })
                .build());
        // phase 2 spectacle: the storm - lightning falls on warned spots around every player (call 1.0 s)
        out.add(BossAttack.of("storm").anim(STORM).phaseTwo().timing(20, 16, 16).range(0, 40).cooldown(420).weight(9)
                .start((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.PHANTOM_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b.getX(), b.getY(), b.getZ(), SoundEvents.TRIDENT_THUNDER, SoundSource.HOSTILE, 2.0F, 0.6F);
                    int i = 0;
                    for (LivingEntity v : b.victims(level, ground(b.position()), arenaRadius + 4)) {
                        b.addEffect(bolt(ground(v.position()), 22 + 3 * i++, 13.0F));
                    }
                    for (int k = 0; k < 5; k++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 3 + b.getRandom().nextDouble() * (arenaRadius - 5);
                        BlockPos c = center();
                        Vec3 p = new Vec3(c.getX() + 0.5 + Math.cos(a) * r, groundY(), c.getZ() + 0.5 + Math.sin(a) * r);
                        b.addEffect(bolt(p, 24 + 4 * k, 13.0F));
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 4.5, b.getZ(), 10, 1.5, 0.8, 1.5, 0.2);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 1.3F))
                .build());

        // ---------------------------------------------------------------- the air phase
        out.add(takeoff("takeoff").cooldown(340).phaseOne().build());
        out.add(takeoff("takeoff2").cooldown(230).phaseTwo().build());
        // circling between air actions (never chosen from the ground: out-of-reach range)
        out.add(BossAttack.of("soar").timing(0, 26, 0).range(999, 999).cooldown(0)
                .start((b, level, t, tick) -> {
                    flightMode = CIRCLE;
                    circleDir = b.getRandom().nextBoolean() ? 1 : -1;
                })
                .end((b, level, t, tick) -> nextAirAction(level, t))
                .build());
        // the dive: rears in the air and screams (telegraphed line), stoops talons first (0.9 s), pulls up low
        out.add(BossAttack.of("dive").timing(18, 9, 13).range(999, 999).cooldown(0)
                .start((b, level, t, tick) -> {
                    play(DIVE);
                    flightMode = HOVER;
                    flyGoal = position().add(0, 1.0, 0);
                    diveHits.clear();
                    level.playSound(null, b, SoundEvents.PHANTOM_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    Vec3 end = diveTarget(t);
                    if (tick % 3 == 0) {
                        Vec3 s = ground(position());
                        for (int i = 0; i <= 16; i++) {
                            Vec3 p = s.lerp(end, i / 16.0);
                            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                        b.telegraphRing(level, end, 2.0, ParticleTypes.END_ROD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    diveEnd = diveTarget(t).add(0, 0.6, 0);
                    flightMode = DIVING;
                    level.playSound(null, b, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, position(), 2.6)) {
                        if (e.position().distanceTo(position()) < 3.0 && diveHits.add(e.getUUID())) {
                            b.strike(level, e, 17.0F, 1.5, 0.5);
                        }
                    }
                    level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 1.2, getZ(), 4, 0.6, 0.4, 0.6, 0.02);
                    if (tick == 8) {
                        flightMode = CLIMB;
                        level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, getX(), groundY() + 0.3, getZ(), 1, 0, 0, 0, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    airActions++;
                    divesInRow++;
                    if (b.phase() == 2 && divesInRow == 1 && t != null) {
                        b.chain(level, "dive");     // the double dive
                    } else {
                        b.chain(level, "soar");
                    }
                })
                .build());
        // feather volley: flares the wings and flings quills at warned spots around the target (0.85 s)
        out.add(BossAttack.of("volley").timing(17, 2, 17).range(999, 999).cooldown(0)
                .start((b, level, t, tick) -> {
                    play(VOLLEY);
                    flightMode = HOVER;
                    flyGoal = position();
                    marks.clear();
                    Vec3 c = t != null ? ground(t.position()) : ground(Vec3.atBottomCenterOf(center()));
                    marks.add(clamp(c, 1.5));
                    int n = b.phase() == 2 ? 10 : 6;
                    for (int i = 0; i < n; i++) {
                        double a = Math.PI * 2 * i / n + b.getRandom().nextDouble() * 0.4;
                        double r = 2.2 + b.getRandom().nextDouble() * 3.5;
                        marks.add(clamp(c.add(Math.cos(a) * r, 0, Math.sin(a) * r), 1.5));
                    }
                    level.playSound(null, b, SoundEvents.PARROT_FLY, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 m : marks) {
                            b.telegraphRing(level, m, 1.3, ParticleTypes.END_ROD);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 from = position().add(0, 2.2, 0);
                    int i = 0;
                    for (Vec3 m : marks) {
                        b.addEffect(quill(from, m, 7 + (i++ % 4), 8.0F));
                    }
                    level.playSound(null, b, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 3.0F, 1.2F);
                    level.playSound(null, b, SoundEvents.ARROW_SHOOT, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    airActions++;
                    divesInRow = 0;
                    b.chain(level, "soar");
                })
                .build());
        // landing: drops beside the target (telegraphed ring), beats the wings on touch-down (0.75 s): a gust
        // ring rolls out (jump it), then a long recovery on the ground
        out.add(BossAttack.of("land").timing(15, 2, 19).range(999, 999).cooldown(0)
                .start((b, level, t, tick) -> {
                    play(LAND);
                    flightMode = DESCEND;
                    Vec3 aim = t != null ? t.position() : Vec3.atBottomCenterOf(center());
                    Vec3 from = ground(position());
                    Vec3 off = from.subtract(ground(aim));
                    off = off.lengthSqr() < 1e-3 ? new Vec3(1, 0, 0) : off.normalize();
                    landSpot = clamp(ground(aim).add(off.scale(3.5)), 2.5);
                })
                .windup((b, level, t, tick) -> {
                    if (landSpot != null && tick % 3 == 0) {
                        b.telegraphRing(level, landSpot, 4.5, ParticleTypes.CLOUD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    endFlight();
                    Vec3 c = landSpot != null ? landSpot : ground(position());
                    b.hitCircle(level, c, 4.5, 13.0F, 1.4, 0.5);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 13 : 10, 0.5, 9.0F, ParticleTypes.CLOUD));
                    level.sendParticles(ParticleTypes.GUST_EMITTER_LARGE, c.x, c.y + 0.5, c.z, 1, 0, 0, 0, 0);
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.WIND_CHARGE_BURST, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.7F);
                })
                .build());
    }

    /** Take-off: crouches (dust), springs up on a wing beat that shoves away whoever stands close (0.7 s). */
    private BossAttack.Builder takeoff(String name) {
        return BossAttack.of(name).anim(TAKEOFF).timing(14, 1, 13).range(0, 40).weight(9)
                .start((b, level, t, tick) -> {
                    animUntil = tickCount + MobAnims.GryphonKnight.TICKS[TAKEOFF];
                    airActions = 0;
                    divesInRow = 0;
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.2, b.getZ(), 8, 2.0, 0.1, 2.0, 0.05);
                        b.telegraphRing(level, b.position(), 3.5, ParticleTypes.CLOUD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    airborne = true;
                    flightMode = CLIMB;
                    setNoGravity(true);
                    setDeltaMovement(getDeltaMovement().x, 0.9, getDeltaMovement().z);
                    hurtMarked = true;
                    b.hitCircle(level, b.position(), 3.5, 6.0F, 1.6, 0.4);
                    level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, b.getX(), b.getY() + 0.5, b.getZ(), 1, 0, 0, 0, 0);
                    level.playSound(null, b, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 3.0F, 0.8F);
                })
                .end((b, level, t, tick) -> b.chain(level, "soar"));
    }

    private void peck(ServerLevel level, double range, float damage, double knockback) {
        lunge(0.35, 0.0);
        hitArc(level, range, 40, damage, knockback);
        level.playSound(null, this, SoundEvents.PHANTOM_BITE, SoundSource.HOSTILE, 2.0F, 0.6F);
        Vec3 p = ahead(range - 1.0);
        level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.0, p.z, 10, 0.4, 0.4, 0.4, 0.2);
    }

    /** Where a dive ends: on the ground through the target, overshooting a little, inside the arena. */
    private Vec3 diveTarget(@Nullable LivingEntity t) {
        Vec3 aim = t != null ? ground(t.position()) : ground(Vec3.atBottomCenterOf(center()));
        Vec3 from = ground(position());
        Vec3 dir = aim.subtract(from);
        dir = dir.lengthSqr() < 1e-3 ? new Vec3(0, 0, 1) : dir.normalize();
        return clamp(aim.add(dir.scale(3.0)), 2.0);
    }

    private void nextAirAction(ServerLevel level, @Nullable LivingEntity t) {
        int max = phase() == 2 ? 5 : 3;
        if (t == null || !t.isAlive() || airActions >= max) {
            chain(level, "land");
            return;
        }
        divesInRow = 0;
        chain(level, getRandom().nextFloat() < 0.58F ? "dive" : "volley");
    }

    private void play(int anim) {
        AnimatedMob.playAction(this, anim);
        animUntil = tickCount + MobAnims.GryphonKnight.TICKS[anim];
    }

    private void endFlight() {
        airborne = false;
        flightMode = CLIMB;
        setNoGravity(false);
        faceYaw = null;
        Vec3 v = getDeltaMovement();
        setDeltaMovement(v.x * 0.3, Math.min(v.y, -0.6), v.z * 0.3);
    }

    // ------------------------------------------------------------------ flight controller

    @Override
    protected void bossTick(ServerLevel level) {
        fallDistance = 0;
        if (airborne) {
            flightTick(level);
        }
        if (tickCount % 8 == 0 && phase() == 2) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 3, 1.2, 1.0, 1.2, 0.05);
        }
    }

    private void flightTick(ServerLevel level) {
        BossAttack c = currentAttack();
        if (c == null || !AIR_MOVES.contains(c.name)) {
            endFlight();     // staggered, phase change or reset: it drops out of the sky
            return;
        }
        setNoGravity(true);
        if (tickCount >= animUntil) {
            play(FLY);
            level.playSound(null, this, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 1.6F, 1.1F);
        }
        LivingEntity t = getTarget();
        double gy = groundY();
        Vec3 pos = position();
        Vec3 want;
        double speed;
        double blend;
        switch (flightMode) {
            case CIRCLE -> {
                circleAngle += 0.07 * circleDir;
                Vec3 c0 = t != null ? clamp(t.position(), 6.0) : Vec3.atBottomCenterOf(center());
                want = new Vec3(c0.x + Math.cos(circleAngle) * 7.5, gy + CRUISE + Math.sin(tickCount * 0.1) * 0.8,
                        c0.z + Math.sin(circleAngle) * 7.5);
                speed = 0.55;
                blend = 0.25;
            }
            case HOVER -> {
                want = flyGoal != null ? flyGoal : pos;
                want = new Vec3(want.x, Math.max(want.y, gy + 5.0) + Math.sin(tickCount * 0.25) * 0.15, want.z);
                speed = 0.2;
                blend = 0.3;
            }
            case DIVING -> {
                want = diveEnd != null ? diveEnd : ground(pos);
                speed = 1.45;
                blend = 1.0;
            }
            case DESCEND -> {
                want = landSpot != null ? landSpot : ground(pos);
                speed = 0.75;
                blend = 0.6;
            }
            default -> {    // CLIMB
                want = new Vec3(pos.x, gy + CRUISE, pos.z);
                speed = 0.5;
                blend = 0.35;
            }
        }
        want = clamp(want, 2.0);
        Vec3 delta = want.subtract(pos);
        double dist = delta.length();
        Vec3 vel = dist > speed ? delta.scale(speed / dist) : delta;
        Vec3 cur = getDeltaMovement();
        setDeltaMovement(cur.scale(1 - blend).add(vel.scale(blend)));
        // face the way it flies (or the target while hovering)
        Vec3 look = flightMode == HOVER || flightMode == DESCEND
                ? (t != null ? t.position().subtract(pos) : Vec3.ZERO) : vel;
        if (look.horizontalDistanceSqr() > 1e-4) {
            faceYaw = (float) (Mth.atan2(look.z, look.x) * (180.0 / Math.PI)) - 90.0F;
        }
        if (tickCount % 6 == 0) {
            level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1.5, getZ(), 6, 2.5, 0.4, 2.5, 0.02);
        }
        if (phase() == 2 && t != null && tickCount % 70 == 0) {
            addEffect(bolt(clamp(ground(t.position()), 1.0), 26, 12.0F));   // stray bolts while it flies
        }
    }

    /** The engine re-locks the yaw during moves; while flying, the gryphon faces its flight direction. */
    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide() && airborne && faceYaw != null) {
            float yaw = Mth.approachDegrees(getYRot(), faceYaw, 14.0F);
            setYRot(yaw);
            yBodyRot = yaw;
            yHeadRot = yaw;
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("gryphon_phase_two"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, getX(), getY(), getZ(), SoundEvents.TRIDENT_THUNDER, SoundSource.HOSTILE, 3.0F, 0.7F);
        LightningBolt b = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
        if (b != null) {
            b.snapTo(position());
            b.setVisualOnly(true);
            level.addFreshEntity(b);
        }
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        endFlight();
        level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 2, getZ(), 120, 3.0, 2.0, 3.0, 0.05);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 40, 2.0, 2.0, 2.0, 0.05);
    }

    // ------------------------------------------------------------------ private effects

    /** A quill flung from {@code from}: it streaks to {@code to} in {@code flight} ticks, then bursts. */
    private static Effect quill(Vec3 from, Vec3 to, int flight, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            t[0]++;
            double a = Math.min(1.0, t[0] / (double) flight);
            Vec3 p = from.lerp(to, a);
            Vec3 q = from.lerp(to, Math.max(0, a - 0.08));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.WHITE_ASH, q.x, q.y + 0.2, q.z, 2, 0.05, 0.05, 0.05, 0);
            if (t[0] < flight) {
                return false;
            }
            level.sendParticles(ParticleTypes.CRIT, to.x, to.y + 0.3, to.z, 14, 0.5, 0.2, 0.5, 0.25);
            level.sendParticles(ParticleTypes.CLOUD, to.x, to.y + 0.2, to.z, 5, 0.4, 0.1, 0.4, 0.02);
            level.playSound(null, to.x, to.y, to.z, SoundEvents.ARROW_HIT, SoundSource.HOSTILE, 1.0F, 0.7F);
            for (LivingEntity e : boss.victims(level, to, 1.6)) {
                if (e.position().multiply(1, 0, 1).distanceTo(to.multiply(1, 0, 1)) <= 1.5) {
                    boss.strike(level, e, damage, 0.3, 0.2);
                }
            }
            return true;
        };
    }

    /** A telegraphed lightning strike: a crackling ring for {@code delay} ticks, then the bolt. */
    private static Effect bolt(Vec3 pos, int delay, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    boss.telegraphRing(level, pos, 2.2, ParticleTypes.ELECTRIC_SPARK);
                    level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.3, pos.z, 2, 0.1, 1.5, 0.1, 0.0);
                }
                t[0]++;
                return false;
            }
            LightningBolt b = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
            if (b != null) {
                b.snapTo(pos);
                b.setVisualOnly(true);
                level.addFreshEntity(b);
            }
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 2.0F, 1.0F);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, pos.x, pos.y + 0.5, pos.z, 30, 1.0, 0.6, 1.0, 0.3);
            for (LivingEntity e : boss.victims(level, pos, 2.6)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= 2.4) {
                    boss.strike(level, e, damage, 0.4, 0.6);
                }
            }
            return true;
        };
    }

    /** A wall of wind rolling forward along {@code dir} and widening: hits (and shoves) each victim once. */
    private static Effect gustWall(Vec3 start, Vec3 dir, int ticks, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        int[] t = {0};
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, level) -> {
            t[0]++;
            double along = t[0] * speed;
            double half = 1.2 + along * 0.3;
            Vec3 c = start.add(dir.scale(along));
            for (double s = -half; s <= half; s += 0.8) {
                Vec3 p = c.add(side.scale(s));
                level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 0.4, p.z, 1, 0.1, 0.3, 0.1, 0.01);
            }
            if (t[0] % 4 == 0) {
                level.sendParticles(ParticleTypes.GUST, c.x, c.y + 0.8, c.z, 1, 0, 0, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, half + 1.0)) {
                Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                double a = to.dot(dir);
                double s = to.subtract(dir.scale(a)).length();
                if (Math.abs(a) <= 0.9 && s <= half + 0.3 && hit.add(e.getUUID())) {
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage)) {
                        e.push(dir.x * 1.5, 0.35, dir.z * 1.5);
                        e.hurtMarked = true;
                    }
                }
            }
            return t[0] >= ticks;
        };
    }
}
