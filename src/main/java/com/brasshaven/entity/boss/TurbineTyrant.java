package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
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
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.TurbineTyrant.CHARGE;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.DASH;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.GRIND;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.OVERLOAD;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.PRESSURE;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.ROAR;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.ROTOR;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.STAGGER;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.STOMP;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.VENTS;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.VORTEX;
import static com.brasshaven.generated.MobAnims.TurbineTyrant.WRENCH;

/**
 * Le Tyran des turbines (The Turbine Tyrant), the engineer of the Dam of the Drowned Valley, fused into his turbine: a
 * 5.7-block walking scroll-case on hydraulic legs, a turbine rotor for a right arm and a valve-wrench as long as a man
 * in his left fist. He waits in the main turbine chamber, whose floor is set with copper grates over the steam mains.
 * <p>A hard fight: 600 health, armour 14, poise 115, hits of 3 to 22. Three phases:
 * <ul>
 *     <li>Phase 1: <b>rotor sweep</b> (wind-up whine, 240 degrees), <b>wrench slam</b> (the floor cracks in a line that
 *     runs on and sets off any grate it crosses), <b>steam vents</b> (he cranks his valve: half the floor grates blow
 *     for 1.5 s), <b>pressure</b> (2.3 s of build-up, then a radial blast over 16 blocks that only spares those he
 *     cannot see: hide behind a pillar or a generator, or get out of range), <b>ram</b> and an anti-hug <b>stomp</b>.</li>
 *     <li>Phase 2 (a roar at 65%): faster, the blast reaches 19 blocks, the vents leave only two grates quiet, combos,
 *     <b>grind</b> (rotor, wrench, rotor), <b>vortex</b> (the rotor draws everyone in, then he whirls) and the
 *     <b>cascade</b> (the grates blow one after another round the chamber).</li>
 *     <li>Phase 3 (at 30%): <b>overload</b>. He kneels (invulnerable) and cranks his own heart; then he is faster, the
 *     grates blow on their own every 9 s, and every 11 s he <b>dashes</b> across the chamber through three marks,
 *     leaving trails of sparks that burn for 4 s.</li>
 * </ul>
 * He never places a block: cracks, steam and sparks are timed effects, cleared when the fight resets.
 */
public class TurbineTyrant extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double ROTOR_RANGE = 7.0;
    private static final double ROTOR_HALF = 120;
    private static final double SLAM_AHEAD = 4.0;
    private static final double SLAM_R = 2.8;
    private static final double STOMP_R = 4.5;
    private static final double VORTEX_PULL = 14.0;
    private static final double VORTEX_R = 4.8;
    private static final int DASH_EVERY = 220;
    private static final int VENTS_EVERY = 180;
    private static final DustParticleOptions HOT_DUST = new DustParticleOptions(0xFF8A2A, 1.4F);
    private static final DustParticleOptions BRASS_DUST = new DustParticleOptions(0xF0CE78, 1.2F);
    private static final DustParticleOptions STEAM_DUST = new DustParticleOptions(0xF2F2EE, 1.6F);

    /** A group of floor grates over one steam main: its cells (the grate blocks) and its centre on the floor. */
    private record Vent(List<BlockPos> cells, Vec3 centre) {}

    private @Nullable Vec3 centre;
    private int radius = 17;
    /** The chamber's vents, found by scanning the floor for copper grates (or a ring of virtual ones). Not saved. */
    private @Nullable List<Vent> vents;
    /** Phase 3 has started. */
    private boolean overloaded;
    private int overloadGuard;
    private int roarUntil = -1;
    private int dashTimer;
    private int ventTimer;
    private final List<Vec3> marks = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable Vec3 vortexFrom;

    public TurbineTyrant(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.TurbineTyrant.TICKS;
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
        return 115.0F;
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

    /** Phase 3 counts as a third stage of the fight (the base class knows only two). */
    public boolean isOverloaded() {
        return overloaded;
    }

    // ------------------------------------------------------------------ arena memory

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.vents = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Blast reach of the pressure vent: out-range it or break his line of sight. */
    private double blastReach() {
        return phase() == 2 ? 19.0 : 16.0;
    }

    /**
     * The chamber's steam vents: every connected group of copper grates set in the floor within the arena. Without
     * grates (a boss spawned elsewhere), eight virtual 3 x 3 vents on a ring 12 blocks round the centre.
     */
    private List<Vent> vents(ServerLevel level) {
        if (vents != null) {
            return vents;
        }
        Vec3 c = centre();
        int floor = Mth.floor(c.y) - 1;
        int r = radius + 2;
        Set<Long> grate = new HashSet<>();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                p.set(Mth.floor(c.x) + dx, floor, Mth.floor(c.z) + dz);
                if (isGrate(level.getBlockState(p)) && level.getBlockState(p.above()).isAir()) {
                    grate.add(p.asLong());
                }
            }
        }
        List<Vent> out = new ArrayList<>();
        Set<Long> seen = new HashSet<>();
        for (long start : grate) {
            if (!seen.add(start)) {
                continue;
            }
            List<BlockPos> cells = new ArrayList<>();
            ArrayDeque<Long> todo = new ArrayDeque<>();
            todo.add(start);
            while (!todo.isEmpty()) {
                BlockPos at = BlockPos.of(todo.poll());
                cells.add(at);
                for (BlockPos n : new BlockPos[] {at.north(), at.south(), at.east(), at.west()}) {
                    if (grate.contains(n.asLong()) && seen.add(n.asLong())) {
                        todo.add(n.asLong());
                    }
                }
            }
            double sx = 0;
            double sz = 0;
            for (BlockPos b : cells) {
                sx += b.getX() + 0.5;
                sz += b.getZ() + 0.5;
            }
            out.add(new Vent(cells, new Vec3(sx / cells.size(), floor + 1, sz / cells.size())));
        }
        if (out.size() < 3) {
            out.clear();
            for (int k = 0; k < 8; k++) {
                double a = Math.PI * 2 * k / 8;
                BlockPos mid = BlockPos.containing(c.x + Math.cos(a) * 12, floor, c.z + Math.sin(a) * 12);
                List<BlockPos> cells = new ArrayList<>();
                for (int dx = -1; dx <= 1; dx++) {
                    for (int dz = -1; dz <= 1; dz++) {
                        cells.add(mid.offset(dx, 0, dz));
                    }
                }
                out.add(new Vent(cells, new Vec3(mid.getX() + 0.5, floor + 1, mid.getZ() + 0.5)));
            }
        }
        // round the chamber in order (for the cascade)
        out.sort((a, b) -> Double.compare(Math.atan2(a.centre.z - c.z, a.centre.x - c.x),
                Math.atan2(b.centre.z - c.z, b.centre.x - c.x)));
        vents = out;
        return out;
    }

    private static boolean isGrate(BlockState state) {
        return BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath().contains("copper_grate");
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // rotor sweep: the rotor drawn back to his right while it spins up with a rising whine (1.1 s, the arc marked
        // in brass), then swept across his front over 240 degrees
        out.add(BossAttack.of("rotor").anim(ROTOR).timing(22, 4, 16).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, ROTOR_RANGE, ROTOR_HALF, BRASS_DUST);
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.06F);
                    }
                    if (b instanceof TurbineTyrant tt) {
                        Vec3 r = tt.rotorPos();
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, r.x, r.y, r.z, 2, 0.6, 0.6, 0.6, 0.05);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, ROTOR_RANGE, ROTOR_HALF)) {
                        b.strike(level, e, 16.0F, 1.3, 0.25);
                    }
                    sweepParticles(b, level, ROTOR_RANGE - 1.5, ROTOR_HALF);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "wrench" : "charge");
                    }
                })
                .build());
        // wrench slam: the valve-wrench heaved over his shoulder (1.0 s, the crack's line marked), then slammed into
        // the floor before him; a crack runs on along the line and blows any grate it crosses. P2: three cracks.
        out.add(BossAttack.of("wrench").anim(WRENCH).timing(20, 4, 16).range(0, 12.0).cooldown(80).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof TurbineTyrant tt) {
                        for (double a : tt.crackAngles()) {
                            tt.drawLine(level, rotate(b.forward(), a), SLAM_AHEAD + 1.5, 20.0, HOT_DUST);
                        }
                        b.telegraphRing(level, b.ahead(SLAM_AHEAD), SLAM_R, HOT_DUST);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.slam(level, 18.0F, 20.0, tt.crackAngles());
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.5 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "rotor");
                    }
                })
                .build());
        // steam vents: the wrench jammed on the valve wheel of his shoulder and cranked (0.9 s); the grates hiss 1.2 s,
        // then blow for 1.5 s: half of them (alternate ones) in phase 1, all but two in phase 2
        out.add(BossAttack.of("vents").anim(VENTS).timing(18, 30, 14).range(0, 30.0).cooldown(200).weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.blowVents(level);
                    }
                    level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 7 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .build());
        // pressure: he seals himself in and builds pressure (2.3 s: the case swells, the stacks shake, the blast's
        // reach is drawn in steam), then vents it all at once: everyone within reach whom he can see takes 22 and is
        // hurled away. Break his line of sight (a pillar, a generator) or get out of range.
        out.add(BossAttack.of("pressure").anim(PRESSURE).timing(46, 10, 20).range(0, 30.0).cooldown(360).weight(5)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof TurbineTyrant tt)) {
                        return;
                    }
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), tt.blastReach(), STEAM_DUST);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.03F);
                        level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.02F);
                    }
                    if (tick == 34) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 1.4F);
                    }
                    tt.stackSmoke(level, 1 + tick / 10);
                    if (tick % 2 == 0) {                            // the gauges creep into the red
                        level.sendParticles(HOT_DUST, b.getX(), b.getY() + 3.2, b.getZ(), 2 + tick / 12, 1.0, 0.3, 1.0, 0);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.blast(level);
                    }
                })
                .build());
        // ram: shoulders down, rotor levelled (0.8 s, his path marked), then he barrels 13 blocks forward
        out.add(BossAttack.of("charge").anim(CHARGE).timing(16, 12, 14).range(6.0, 22.0).cooldown(120).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && b instanceof TurbineTyrant tt) {
                        tt.drawLine(level, b.forward(), 1.5, 14.0, BRASS_DUST);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.ramStep(level, b.forward(), 1.15, 15.0F);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // stomp: a hydraulic leg lifted (0.6 s, a ring of steam at his feet), slammed down: steam bursts out round him
        out.add(BossAttack.of("stomp").anim(STOMP).timing(12, 4, 14).range(0, 4.0).cooldown(60).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), STOMP_R, STEAM_DUST);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), STOMP_R, 13.0F, 1.4, 0.5);
                    steamRing(level, b.position(), STOMP_R);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "rotor");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // grind: rotor sweep at once (0.9 s), a turn, the wrench slam 0.6 s later (a short crack), a turn, then the
        // rotor back the other way 0.6 s after that; every blow re-telegraphed
        out.add(BossAttack.of("grind").anim(GRIND).phaseTwo().timing(18, 30, 16).range(0, 7.5).cooldown(160).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, ROTOR_RANGE, 110, BRASS_DUST);
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.07F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof TurbineTyrant tt)) {
                        return;
                    }
                    if (tick == 0 || tick == 24) {
                        for (LivingEntity e : arcVictims(b, level, ROTOR_RANGE, 110)) {
                            b.strike(level, e, 14.0F, 1.2, 0.25);
                        }
                        sweepParticles(b, level, ROTOR_RANGE - 1.5, 110);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                    if ((tick == 3 || tick == 15) && t != null) {
                        tt.turnToward(t, 40.0F);
                    }
                    if (tick > 3 && tick < 12 && tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(SLAM_AHEAD), SLAM_R, HOT_DUST);
                        tt.drawLine(level, b.forward(), SLAM_AHEAD + 1.5, 11.0, HOT_DUST);
                    }
                    if (tick == 12) {
                        tt.slam(level, 16.0F, 11.0, new double[] {0});
                    }
                    if (tick > 15 && tick < 24 && tick % 2 == 0) {
                        b.telegraphArc(level, ROTOR_RANGE, 110, BRASS_DUST);
                    }
                })
                .build());
        // vortex: the rotor raised before him like a fan (1.0 s, rings closing on him); it draws everyone within 14
        // blocks in for 1.2 s (run against it), then he whirls round once (16 within 4.8)
        out.add(BossAttack.of("vortex").anim(VORTEX).phaseTwo().timing(20, 30, 14).range(0, 16.0).cooldown(220).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        double r = VORTEX_R + (VORTEX_PULL - VORTEX_R) * (1.0 - tick / 20.0);
                        b.telegraphRing(level, b.position(), r, ParticleTypes.CLOUD);
                        b.telegraphRing(level, b.position(), VORTEX_R, HOT_DUST);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_INHALE, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.vortexFrom = b.position();
                    }
                    level.playSound(null, b, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.vortexStep(level, tick);
                    }
                })
                .build());
        // cascade: he cranks the valve hard (0.9 s); the grates blow one after another round the chamber, starting
        // with the one nearest the target (in phase 3 a second run goes the other way)
        out.add(BossAttack.of("cascade").anim(VENTS).phaseTwo().timing(18, 30, 14).range(0, 30.0).cooldown(240).weight(6)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.cascade(level, t);
                    }
                    level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.5F, 0.8F);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // overload: he kneels and cranks his own heart (1.5 s, invulnerable), the rotor raised and screaming; then he
        // rises and slams the floor: a ring of sparks rolls out and the turbine runs wild
        out.add(BossAttack.of("overload").anim(OVERLOAD).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    overloadGuard = 52;
                    level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.05F);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.4, ParticleTypes.ELECTRIC_SPARK);
                    }
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 4.5, b.getZ(), 6, 1.0, 1.0, 1.0, 0.2);
                    if (b instanceof TurbineTyrant tt) {
                        tt.stackSmoke(level, 3);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.callOverload(level);
                    }
                })
                .build());
        // dash: crouched like a sprinter, rotor blazing (1.0 s; three marks, on the players first, linked by lines of
        // sparks), then he dashes through them in 2.25 s, leaving burning sparks behind
        out.add(BossAttack.of("dash").anim(DASH).phaseTwo().timing(20, 45, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    marks.clear();
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.8F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof TurbineTyrant tt)) {
                        return;
                    }
                    if (tick < 14) {
                        tt.pickMarks(level);
                    }
                    if (tick % 2 == 0) {
                        tt.drawMarks(level, tick >= 14);
                    }
                    if (tick == 14) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.5F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> struck.clear())
                .active((b, level, t, tick) -> {
                    if (b instanceof TurbineTyrant tt) {
                        tt.dashStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** Where the rotor spins (his right, in front, at chest height). */
    private Vec3 rotorPos() {
        Vec3 f = forward();
        Vec3 right = new Vec3(-f.z, 0, f.x);
        return position().add(f.scale(1.6)).add(right.scale(1.1)).add(0, 2.6, 0);
    }

    private double[] crackAngles() {
        return phase() == 2 ? new double[] {-20, 0, 20} : new double[] {0};
    }

    /** A line of particles on the floor from {@code from} to {@code to} blocks along {@code dir}. */
    private void drawLine(ServerLevel level, Vec3 dir, double from, double to, net.minecraft.core.particles.ParticleOptions particle) {
        for (double d = from; d <= to; d += 1.0) {
            Vec3 p = position().add(dir.scale(d));
            level.sendParticles(particle, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
        }
    }

    /** The wrench lands: a blow in front, then the cracks run on along {@code angles}. */
    private void slam(ServerLevel level, float damage, double crackLen, double[] angles) {
        Vec3 at = ahead(SLAM_AHEAD);
        hitCircle(level, at, SLAM_R, damage, 1.2, 0.4);
        BlockState floor = level.getBlockState(BlockPos.containing(at.x, at.y - 0.5, at.z));
        if (!floor.isAir()) {
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, floor), at.x, at.y + 0.2, at.z, 60, 1.4, 0.3, 1.4, 0.2);
        }
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.6, 0.2, 0.6, 0);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
        for (double a : angles) {
            addEffect(crack(at, rotate(forward(), a), crackLen - SLAM_AHEAD));
        }
    }

    /**
     * A crack running along the floor at one block per tick, stopping at a wall: 12 and a jolt upward to whoever stands
     * on it (once), and every grate it crosses blows at once.
     */
    private Effect crack(Vec3 from, Vec3 dir, double length) {
        Set<UUID> hit = new HashSet<>();
        Set<Integer> blown = new HashSet<>();
        double[] d = {1.0};
        return (boss, level) -> {
            if (!(boss instanceof TurbineTyrant tt)) {
                return true;
            }
            Vec3 p = from.add(dir.scale(d[0]));
            BlockPos feet = BlockPos.containing(p.x, p.y + 0.5, p.z);
            if (!level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()) {
                return true;                                        // a wall or a pillar stops it
            }
            BlockState floor = level.getBlockState(feet.below());
            if (!floor.isAir()) {
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, floor), p.x, p.y + 0.1, p.z, 8, 0.3, 0.1, 0.3, 0.1);
            }
            level.sendParticles(ParticleTypes.LAVA, p.x, p.y + 0.1, p.z, 1, 0.2, 0, 0.2, 0);
            level.sendParticles(ParticleTypes.SMOKE, p.x, p.y + 0.2, p.z, 3, 0.3, 0.1, 0.3, 0.01);
            if (((int) d[0]) % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 1.0F, 0.5F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.3 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 1.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 12.0F, 0.3, 0.7);
                }
            }
            List<Vent> vs = tt.vents(level);
            for (int i = 0; i < vs.size(); i++) {
                if (!blown.contains(i) && tt.onVent(vs.get(i), p, 0.6)) {
                    blown.add(i);
                    boss.addEffect(tt.vent(vs.get(i), 6, 16, 10.0F));
                }
            }
            d[0] += 1.0;
            return d[0] > length;
        };
    }

    /** True when {@code p} stands over one of the vent's grates (with {@code margin} blocks of slack). */
    private boolean onVent(Vent v, Vec3 p, double margin) {
        for (BlockPos c : v.cells) {
            if (Math.abs(p.x - (c.getX() + 0.5)) <= 0.5 + margin && Math.abs(p.z - (c.getZ() + 0.5)) <= 0.5 + margin) {
                return true;
            }
        }
        return false;
    }

    /**
     * A steam vent: the grates hiss and smoke for {@code warn} ticks (a ring of hot dust for the last 8), then a column
     * of steam bursts up: {@code burst} and thrown up, then 3 every quarter second while you stay in it, for
     * {@code column} ticks.
     */
    private Effect vent(Vent v, int warn, int column, float burst) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    for (BlockPos c : v.cells) {
                        level.sendParticles(ParticleTypes.WHITE_SMOKE, c.getX() + 0.5, c.getY() + 1.05, c.getZ() + 0.5, 1, 0.25, 0.02, 0.25, 0.01);
                    }
                }
                if (warn - k <= 8 && k % 2 == 0) {
                    boss.telegraphRing(level, v.centre, 1.9, HOT_DUST);
                }
                if (k == 0) {
                    level.playSound(null, v.centre.x, v.centre.y, v.centre.z, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.6F);
                }
                return false;
            }
            int j = k - warn;
            if (j == 0) {
                level.playSound(null, v.centre.x, v.centre.y, v.centre.z, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 1.6F, 0.5F);
                level.playSound(null, v.centre.x, v.centre.y, v.centre.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.6F, 0.5F);
            }
            if (j % 2 == 0) {
                for (BlockPos c : v.cells) {
                    level.sendParticles(ParticleTypes.CLOUD, c.getX() + 0.5, c.getY() + 1.6, c.getZ() + 0.5, 2, 0.25, 1.0, 0.25, 0.08);
                }
                level.sendParticles(STEAM_DUST, v.centre.x, v.centre.y + 2.5, v.centre.z, 4, 0.8, 1.2, 0.8, 0.02);
            }
            if (j == 0 || j % 5 == 0) {
                for (LivingEntity e : boss.victims(level, v.centre, 4.0)) {
                    double dy = e.getY() - v.centre.y;
                    if (dy > -0.5 && dy < 3.5 && ((TurbineTyrant) boss).onVent(v, e.position(), e.getBbWidth() / 2)) {
                        if (j == 0) {
                            boss.strike(level, e, burst, 0.2, 0.9);
                        } else if (e.hurtServer(level, boss.damageSources().mobAttack(boss), 3.0F)) {
                            e.push(0, 0.25, 0);
                            e.hurtMarked = true;
                        }
                    }
                }
            }
            return j >= column;
        };
    }

    /** Phase 1: every other vent; phase 2: every vent but two opposite ones. */
    private void blowVents(ServerLevel level) {
        List<Vent> vs = vents(level);
        int n = vs.size();
        int column = overloaded ? 40 : 30;
        if (phase() == 1) {
            int parity = getRandom().nextInt(2);
            for (int i = 0; i < n; i++) {
                if (i % 2 == parity) {
                    addEffect(vent(vs.get(i), 24, column, 10.0F));
                }
            }
        } else {
            int safe = getRandom().nextInt(n);
            int other = (safe + n / 2) % n;
            for (int i = 0; i < n; i++) {
                if (i != safe && i != other) {
                    addEffect(vent(vs.get(i), 24, column, 10.0F));
                } else {
                    Vec3 c = vs.get(i).centre;
                    level.sendParticles(BRASS_DUST, c.x, c.y + 0.3, c.z, 12, 0.8, 0.1, 0.8, 0);
                }
            }
        }
    }

    /** The vents blow one after another round the chamber, from the one nearest the target. */
    private void cascade(ServerLevel level, @Nullable LivingEntity target) {
        List<Vent> vs = vents(level);
        int n = vs.size();
        int start = 0;
        if (target != null) {
            double best = Double.MAX_VALUE;
            for (int i = 0; i < n; i++) {
                double d = flatDist(vs.get(i).centre, target.position());
                if (d < best) {
                    best = d;
                    start = i;
                }
            }
        }
        int dir = getRandom().nextBoolean() ? 1 : -1;
        for (int k = 0; k < n; k++) {
            Vent v = vs.get(Math.floorMod(start + dir * k, n));
            addEffect(delayed(k * 5, vent(v, 16, 14, 10.0F)));
            if (overloaded) {
                Vent w = vs.get(Math.floorMod(start - dir * k, n));
                addEffect(delayed(20 + k * 5, vent(w, 16, 14, 10.0F)));
            }
        }
    }

    /** True when no block stands between his chest and the creature (head or body): the blast reaches it. */
    private boolean exposed(ServerLevel level, LivingEntity e) {
        Vec3 from = position().add(0, 2.6, 0);
        for (Vec3 to : new Vec3[] {e.getEyePosition(), e.position().add(0, e.getBbHeight() * 0.45, 0)}) {
            if (level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this)).getType()
                    == HitResult.Type.MISS) {
                return true;
            }
        }
        return false;
    }

    /** The pressure vents: 22 and hurled away for everyone within reach he can see; a visible ring of steam. */
    private void blast(ServerLevel level) {
        double reach = blastReach();
        for (LivingEntity e : victims(level, position(), reach + 1)) {
            double d = flatDist(e.position(), position());
            if (d <= reach && (d < 3.5 || exposed(level, e))) {
                strike(level, e, 22.0F, 2.0, 0.6);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                level.sendParticles(ParticleTypes.CLOUD, e.getX(), e.getY() + 1, e.getZ(), 20, 0.4, 0.6, 0.4, 0.15);
            }
        }
        Vec3 c = position();
        int[] t = {0};
        addEffect((boss, lvl) -> {                                   // the visible front of the blast
            double r = 1.5 + t[0]++ * (reach / 6.0);
            boss.telegraphRing(lvl, c, r, ParticleTypes.CLOUD);
            boss.telegraphRing(lvl, c.add(0, 1.2, 0), r, ParticleTypes.WHITE_SMOKE);
            return r >= reach;
        });
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, getX(), getY() + 2, getZ(), 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.5, getZ(), 120, 2.0, 1.5, 2.0, 0.5);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    private void stackSmoke(ServerLevel level, int amount) {
        Vec3 f = forward();
        Vec3 right = new Vec3(-f.z, 0, f.x);
        Vec3 back = position().subtract(f.scale(0.7));
        Vec3 a = back.add(right.scale(0.55)).add(0, 5.9, 0);
        Vec3 b = back.subtract(right.scale(0.75)).add(0, 5.2, 0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, a.x, a.y, a.z, amount, 0.15, 0.2, 0.15, 0.03);
        level.sendParticles(ParticleTypes.WHITE_SMOKE, b.x, b.y, b.z, amount, 0.15, 0.2, 0.15, 0.03);
    }

    private static void steamRing(ServerLevel level, Vec3 c, double r) {
        for (int i = 0; i < 24; i++) {
            double a = Math.PI * 2 * i / 24;
            level.sendParticles(ParticleTypes.CLOUD, c.x + Math.cos(a) * r * 0.7, c.y + 0.4, c.z + Math.sin(a) * r * 0.7,
                    3, 0.3, 0.2, 0.3, 0.08);
        }
    }

    /** One tick of the ram: barrel on, hit what is in the way once, stop dead on walls. */
    private void ramStep(ServerLevel level, Vec3 dir, double speed, float damage) {
        setDeltaMovement(dir.x * speed, getDeltaMovement().y, dir.z * speed);
        hurtMarked = true;
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 0.3, getZ(), 4, 0.6, 0.1, 0.6, 0.02);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.2, getZ(), 4, 0.6, 0.1, 0.6, 0.1);
        for (LivingEntity e : victims(level, position(), 3.0)) {
            if (flatDist(e.position(), position()) <= 2.4 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, damage, 1.6, 0.4);
            }
        }
        if (horizontalCollision) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 1.5, getZ(), 1, 0.3, 0.3, 0.3, 0);
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    /** One tick of the vortex: the pull toward his rotor, then the whirl. */
    private void vortexStep(ServerLevel level, int tick) {
        Vec3 from = vortexFrom != null ? vortexFrom : position();
        if (tick < 24) {
            for (LivingEntity e : victims(level, from, VORTEX_PULL)) {
                Vec3 to = from.subtract(e.position()).multiply(1, 0, 1);
                double d = to.length();
                if (d < 2.0 || d > VORTEX_PULL) {
                    continue;
                }
                Vec3 v = e.getDeltaMovement().add(to.normalize().scale(0.09));
                double h = Math.hypot(v.x, v.z);
                if (h > 0.55) {
                    v = new Vec3(v.x * 0.55 / h, v.y, v.z * 0.55 / h);
                }
                e.setDeltaMovement(v);
                e.hurtMarked = true;
                if (tick % 3 == 0) {
                    level.sendParticles(ParticleTypes.CLOUD, e.getX(), e.getY() + 0.4, e.getZ(), 2, 0.2, 0.1, 0.2, 0);
                }
            }
            if (tick % 2 == 0) {
                telegraphRing(level, from, VORTEX_R, HOT_DUST);
                telegraphRing(level, from, VORTEX_PULL * (1.0 - tick / 24.0) + VORTEX_R * tick / 24.0, ParticleTypes.CLOUD);
            }
            if (tick % 6 == 0) {
                level.playSound(null, this, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.02F);
            }
        } else if (tick == 26) {
            hitCircle(level, from, VORTEX_R, 16.0F, 1.6, 0.5);
            steamRing(level, from, VORTEX_R);
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, from.x, from.y + 1.5, from.z, 6, 2.0, 0.3, 2.0, 0);
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.5F);
            level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    private void turnToward(LivingEntity target, float maxTurn) {
        double dx = target.getX() - getX();
        double dz = target.getZ() - getZ();
        float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private Vec3 clampToArena(Vec3 p) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(3.0, radius - 2.0);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    private Vec3 randomSpot() {
        double a = getRandom().nextDouble() * Math.PI * 2;
        double r = 3 + getRandom().nextDouble() * Math.max(3, radius - 5);
        return centre().add(Math.cos(a) * r, 0, Math.sin(a) * r);
    }

    // ------------------------------------------------------------------ phase 3: overload, dash, sparks

    private void callOverload(ServerLevel level) {
        overloaded = true;
        dashTimer = 100;
        ventTimer = 140;
        addEffect(WayfarerBoss.wave(position(), 14, 0.55, 12.0F, ParticleTypes.ELECTRIC_SPARK));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("turbine_tyrant_overload"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 200, 2.5, 2.0, 2.5, 0.5);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 1, getZ(), 6, 1.5, 0.5, 1.5, 0);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** Dash marks: every player in the arena (up to three) while they still follow, then random spots. */
    private void pickMarks(ServerLevel level) {
        marks.clear();
        for (LivingEntity e : victims(level, centre(), radius + 4.0)) {
            if (e instanceof Player && marks.size() < 3) {
                marks.add(clampToArena(e.position()));
            }
        }
        while (marks.size() < 3) {
            marks.add(clampToArena(randomSpot()));
        }
    }

    private void drawMarks(ServerLevel level, boolean locked) {
        Vec3 prev = position();
        for (Vec3 m : marks) {
            telegraphRing(level, m, 2.0, locked ? HOT_DUST : BRASS_DUST);
            double len = flatDist(prev, m);
            for (double d = 0; d < len; d += 1.5) {
                Vec3 p = prev.lerp(m, d / Math.max(0.01, len));
                level.sendParticles(locked ? ParticleTypes.ELECTRIC_SPARK : BRASS_DUST, p.x, m.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
            prev = m;
        }
    }

    /** One tick of the dash: run to the current mark, hit whoever is in the way once per leg, drop sparks. */
    private void dashStep(ServerLevel level, int tick) {
        if (marks.isEmpty()) {
            return;
        }
        int leg = Math.min(marks.size() - 1, tick / 15);
        if (tick % 15 == 0) {
            struck.clear();
        }
        Vec3 goal = marks.get(leg);
        Vec3 to = goal.subtract(position()).multiply(1, 0, 1);
        int left = Math.max(1, 15 * (leg + 1) - tick - 3);
        double speed = Math.min(1.8, to.length() / left);
        if (to.lengthSqr() > 0.04) {
            Vec3 v = to.normalize().scale(speed);
            setDeltaMovement(v.x, getDeltaMovement().y, v.z);
            snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
        hurtMarked = true;
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 0.6, getZ(), 10, 0.8, 0.4, 0.8, 0.2);
        if (tick % 2 == 0 && speed > 0.3) {
            addEffect(sparks(position(), 80));
        }
        if (tick % 4 == 0) {
            level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.8F);
        }
        for (LivingEntity e : victims(level, position(), 3.0)) {
            if (flatDist(e.position(), position()) <= 2.2 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, 14.0F, 1.2, 0.4);
            }
        }
    }

    /** A patch of sparks on the floor for {@code life} ticks: 3 and set alight every half second to whoever stands in it. */
    private static Effect sparks(Vec3 pos, int life) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k % 4 == 0) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, pos.x, pos.y + 0.2, pos.z, 3, 0.5, 0.1, 0.5, 0.05);
                level.sendParticles(ParticleTypes.SMALL_FLAME, pos.x, pos.y + 0.1, pos.z, 1, 0.4, 0.0, 0.4, 0.0);
            }
            if (k % 10 == 5) {
                for (LivingEntity e : boss.victims(level, pos, 1.6)) {
                    if (flatDist(e.position(), pos) <= 1.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 1.2) {
                        if (e.hurtServer(level, boss.damageSources().mobAttack(boss), 3.0F)) {
                            e.igniteForSeconds(2.0F);
                        }
                    }
                }
            }
            return k >= life;
        };
    }

    // ------------------------------------------------------------------ static helpers

    private static List<LivingEntity> arcVictims(WayfarerBoss b, ServerLevel level, double range, double halfAngle) {
        Vec3 fwd = b.forward();
        double cos = Math.cos(Math.toRadians(halfAngle));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : b.victims(level, b.position(), range + 1)) {
            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                out.add(e);
            }
        }
        return out;
    }

    private static void sweepParticles(WayfarerBoss b, ServerLevel level, double r, double halfAngle) {
        for (double a = -halfAngle; a <= halfAngle; a += 12) {
            Vec3 p = b.position().add(rotate(b.forward(), a).scale(r));
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 1.6, p.z, 4, 0.2, 0.3, 0.2, 0.1);
            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 1.4, p.z, 1, 0.2, 0.2, 0.2, 0.02);
        }
        Vec3 c = b.ahead(r * 0.6);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.6, c.z, 1, 0, 0, 0, 0);
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    /** Runs {@code inner} after {@code delay} ticks. */
    private static Effect delayed(int delay, Effect inner) {
        int[] t = {0};
        return (boss, level) -> t[0]++ >= delay && inner.tick(boss, level);
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (overloadGuard > 0) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.1);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (overloadGuard > 0) {
            overloadGuard--;
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (phase() == 1 && overloaded) {                   // the fight was reset: the turbine runs down
            overloaded = false;
            roarUntil = -1;
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("turbine_tyrant_overload"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("turbine_tyrant_wrath"));
            }
        }
        boolean free = fighting && currentAttack() == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!overloaded && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "overload");
                free = false;
            } else if (overloaded && --dashTimer <= 0) {
                dashTimer = (int) Math.round(DASH_EVERY * cooldownScale());
                chain(level, "dash");
                free = false;
            }
        }
        // phase 3: the grates blow on their own, whatever he is doing (a third of them, warned 1.5 s)
        if (overloaded && fighting && --ventTimer <= 0) {
            ventTimer = (int) Math.round(VENTS_EVERY * cooldownScale());
            List<Vent> vs = new ArrayList<>(vents(level));
            Collections.shuffle(vs, new java.util.Random(getRandom().nextLong()));
            int n = Math.max(1, (vs.size() + 2) / 3);
            for (int i = 0; i < n; i++) {
                addEffect(vent(vs.get(i), 30, 30, 10.0F));
            }
            level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.5F, 1.6F);
        }
        // ambience: smoke from the stacks, sparks off the rotor, the intake's hum
        if (tickCount % 5 == 0) {
            stackSmoke(level, overloaded ? 3 : 1);
        }
        if (tickCount % 6 == 0 || overloaded && tickCount % 2 == 0) {
            Vec3 r = rotorPos();
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, r.x, r.y, r.z, 1, 0.5, 0.5, 0.5, 0.05);
        }
        if (tickCount % 60 == 0) {
            level.playSound(null, this, SoundEvents.MINECART_RIDING, SoundSource.HOSTILE, 0.6F, overloaded ? 1.2F : 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("turbine_tyrant_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, ParticleTypes.CLOUD));
        stackSmoke(level, 30);
        level.playSound(null, this, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 0.4F);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.5, getZ(), 80, 1.5, 2.0, 1.5, 0.2);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.5, getZ(), 150, 1.5, 2.0, 1.5, 0.3);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 120, 1.5, 2.0, 1.5, 0.4);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2, getZ(), 4, 1.0, 1.0, 1.0, 0);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DEATH, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("TyrantCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("TyrantRadius", radius);
        output.putBoolean("TyrantOverload", overloaded);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("TyrantCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("TyrantRadius", 17);
        overloaded = input.getBooleanOr("TyrantOverload", false) && phase() == 2;
        vents = null;
    }
}
