package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
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
import net.minecraft.world.level.pathfinder.PathType;
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

import static com.brasshaven.generated.MobAnims.TideAbbess.ACOLYTES;
import static com.brasshaven.generated.MobAnims.TideAbbess.BAPTISM;
import static com.brasshaven.generated.MobAnims.TideAbbess.CENSER;
import static com.brasshaven.generated.MobAnims.TideAbbess.FLOOD;
import static com.brasshaven.generated.MobAnims.TideAbbess.RIPTIDE;
import static com.brasshaven.generated.MobAnims.TideAbbess.ROAR;
import static com.brasshaven.generated.MobAnims.TideAbbess.STAGGER;
import static com.brasshaven.generated.MobAnims.TideAbbess.SURGE;
import static com.brasshaven.generated.MobAnims.TideAbbess.SWEEP;
import static com.brasshaven.generated.MobAnims.TideAbbess.THURIBLE;
import static com.brasshaven.generated.MobAnims.TideAbbess.TIDEWAVE;
import static com.brasshaven.generated.MobAnims.TideAbbess.TOLL;

/**
 * L'Abbesse des Marées (The Abbess of the Tides), the drowned saint of the Tidal Abbey: a 5.4-block abbess in a
 * barnacled chasuble over a robe of sea-dark linen, a crown of coral grown through her veil, a nautilus crozier in her
 * right hand and a bronze bell-censer swinging from her left. She waits in the rotunda under the church.
 * <p>A hard fight: 560 health, armour 12, poise 105, hits of 3 to 16. Three phases:
 * <ul>
 *     <li>Phase 1: <b>crozier sweep</b> (200 degrees, 15), <b>censer swing</b> (12, it leaves lingering brine clouds),
 *     <b>tide wave</b> (a wall of water sweeps the whole rotunda behind her toward you: too tall to jump, stand in one
 *     of the marked gaps), <b>bell toll</b> (the tide draws everyone in for a second, then the brine bursts round her:
 *     run against the pull), <b>surge</b> (she glides down a line of bubbles, crozier first) and, every half minute,
 *     her <b>drowned acolytes</b> (vanilla drowned, two at most, more in co-op).</li>
 *     <li>Phase 2 (a roar at 65%): faster, combos, a second tide wave across the first, <b>baptism</b> (geysers of
 *     brine burst under every player, two volleys) and <b>thurible</b> (two censer swings, forehand then backhand).</li>
 *     <li>Phase 3 (at 30%): the <b>flood</b>. She kneels (invulnerable) and the rotunda floods with a hand of real
 *     water: you wade, she swims (much faster). Every 12 s she dives into the <b>riptide</b> and swims through
 *     three marks (on the players) in two seconds. The water is temporary: it drains when she dies, when the fight
 *     resets, when the arena empties, and after a reload.</li>
 * </ul>
 */
public class TideAbbess extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.3F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_RANGE = 6.5;
    private static final double SWEEP_HALF = 100;
    private static final double CENSER_RANGE = 6.0;
    private static final double CENSER_HALF = 70;
    private static final double TOLL_PULL = 20.0;
    private static final double TOLL_BURST = 5.0;
    private static final double GAP_HALF = 1.8;
    private static final int ACOLYTES_EVERY = 600;
    private static final int RIPTIDE_EVERY = 240;
    private static final int FLOOD_MAX_R = 15;
    private static final DustParticleOptions BRINE = new DustParticleOptions(0x3FA58E, 1.4F);
    private static final DustParticleOptions SEA_GLASS = new DustParticleOptions(0x7CF2DA, 1.2F);
    private static final DustParticleOptions FOAM = new DustParticleOptions(0xE6F6F2, 1.6F);

    /** Arena centre and radius (from the seal), saved with the boss. */
    private @Nullable Vec3 centre;
    private int radius = 14;
    /** Phase 3 has started (the abbess called the flood). */
    private boolean deluge;
    /** Water she placed is standing in the arena. */
    private boolean flooded;
    private int floodY;
    private int floodR;
    /** Water cells that were already there before the flood: never touched by the drain. */
    private final Set<Long> preWater = new HashSet<>();
    /** The flood was saved by an unload: drained on the first tick. */
    private boolean staleFlood;
    private int floodGuard;
    private int roarUntil = -1;
    private int acolyteTimer = 240;
    private int riptideTimer;
    /** The planned tide wave: its direction and the lateral centres of its gaps. */
    private @Nullable Vec3 waveDir;
    private final List<Double> waveGaps = new ArrayList<>();
    private final List<Vec3> spots = new ArrayList<>();
    private final List<Vec3> marks = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable Vec3 tollFrom;

    public TideAbbess(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        setPathfindingMalus(PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 560.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5)
                .add(Attributes.WATER_MOVEMENT_EFFICIENCY, 1.0);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.TideAbbess.TICKS;
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
        return 4.5;
    }

    /** Phase 3 counts as a third stage of the fight (the base class knows only two). */
    public boolean isDeluge() {
        return deluge;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    /** A drowned saint: she never needs air. */
    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    /** She wades through her flood instead of bobbing up and down in it (the float goal jumps above this depth). */
    @Override
    public double getFluidJumpThreshold() {
        return 2.5;
    }

    // ------------------------------------------------------------------ arena memory

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

    /** Half-length of a tide wave: the arena radius, never more than the rotunda's 16 blocks. */
    private double waveReach() {
        return Math.min(16.0, radius + 2.0);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // crozier sweep: the crozier drawn back over her right shoulder (0.8 s, the arc outlined in foam), then swept
        // across her front over 200 degrees
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(16, 4, 14).range(0, 7.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, ParticleTypes.SPLASH);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, SWEEP_RANGE, SWEEP_HALF)) {
                        b.strike(level, e, 15.0F, 1.3, 0.25);
                    }
                    sweepParticles(b, level, SWEEP_RANGE - 1.5, SWEEP_HALF);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.TRIDENT_RIPTIDE_1.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "thurible" : "surge");
                    }
                })
                .build());
        // censer swing: the bell-censer swung back low behind her (0.9 s), then flung round in a wide arc in front;
        // brine smoke pours out of it and lingers where it passed
        out.add(BossAttack.of("censer").anim(CENSER).timing(18, 6, 14).range(0, 6.5).cooldown(70).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, CENSER_RANGE, CENSER_HALF, BRINE);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.censerBlow(level, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) > 6.0 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "surge");
                    }
                })
                .build());
        // tide wave: the crozier raised high (1.1 s; the start line behind her and the gaps in the wave are marked on
        // the floor), then struck down: a wall of water sweeps the rotunda from behind her toward the target. Too tall
        // to jump: stand in a gap. Phase 2: a second wave across the first.
        out.add(BossAttack.of("tidewave").anim(TIDEWAVE).timing(22, 40, 14).range(0, 30.0).cooldown(220).weight(7)
                .start((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.planWave(t);
                    }
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof TideAbbess a && a.waveDir != null) {
                        a.drawWavePlan(level, a.waveDir, a.waveGaps, -a.waveReach());
                    }
                    if (tick == 12) {
                        level.playSound(null, b, SoundEvents.AMBIENT_UNDERWATER_ENTER, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof TideAbbess a) || a.waveDir == null) {
                        return;
                    }
                    double speed = a.flooded ? 0.8 : 0.6;
                    b.addEffect(a.tideWave(a.waveDir, List.copyOf(a.waveGaps), 0, speed, 13.0F));
                    if (b.phase() == 2) {                           // and a second one across the first
                        Vec3 across = rotate(a.waveDir, b.getRandom().nextBoolean() ? 90 : -90);
                        b.addEffect(a.tideWave(across, a.pickGaps(a.deluge ? 1 : 2, null), 34, speed, 13.0F));
                    }
                    Vec3 c = b.ahead(1.5);
                    level.sendParticles(ParticleTypes.SPLASH, c.x, c.y + 0.3, c.z, 60, 1.2, 0.2, 1.2, 0.3);
                    level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.AMBIENT_UNDERWATER_LOOP_ADDITIONS, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .build());
        // bell toll: the censer raised high over her crown (1.0 s, rings of sea glass close in on her), then rung:
        // the tide draws everyone within 20 blocks toward her for 0.7 s, and the brine bursts round her (r 5) 0.8 s
        // after the toll. Run against the pull.
        out.add(BossAttack.of("toll").anim(TOLL).timing(20, 20, 14).range(0, 18.0).cooldown(200).weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        double r = TOLL_BURST + (TOLL_PULL - TOLL_BURST) * (1.0 - tick / 20.0);
                        b.telegraphRing(level, b.position(), r, SEA_GLASS);
                        b.telegraphRing(level, b.position(), TOLL_BURST, BRINE);
                    }
                    if (tick == 0 || tick == 10) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.5F, 1.4F);
                    if (b instanceof TideAbbess a) {
                        a.tollFrom = b.position();
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.tollStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.5 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // surge: she leans into the tide, crozier levelled (0.7 s, a line of bubbles on the floor), then glides down
        // it ferrule first: 14 once per target. In her flood she swims it half as far again.
        out.add(BossAttack.of("surge").anim(SURGE).timing(14, 10, 14).range(5.0, 20.0).cooldown(120).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && b instanceof TideAbbess a) {
                        double len = a.flooded ? 15 : 10;
                        for (double d = 1.5; d <= len; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(SEA_GLASS, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.TRIDENT_RIPTIDE_2.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.surgeStep(level, a.flooded ? 1.5 : 1.0, 14.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.5 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // drowned acolytes: never rolled; bossTick chains it every half minute while there is room. The censer swung
        // in a slow circle (0.9 s, bubbling rings where they will rise), then the crozier struck down: they rise
        out.add(BossAttack.of("acolytes").anim(ACOLYTES).timing(18, 4, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.pickAcolyteSpots(level);
                    }
                    level.playSound(null, b, SoundEvents.CONDUIT_ACTIVATE, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 p : spots) {
                            b.telegraphRing(level, p, 1.0, ParticleTypes.SPLASH);
                            level.sendParticles(BRINE, p.x, p.y + 0.2, p.z, 3, 0.3, 0.1, 0.3, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.raiseAcolytes(level);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // baptism: the crozier lifted overhead (0.9 s, rings close on every player), then lowered over the floor:
        // geysers of brine burst where the rings locked (14, thrown up), two volleys (three once flooded)
        out.add(BossAttack.of("baptism").anim(BAPTISM).phaseTwo().timing(18, 30, 12).range(0, 26.0).cooldown(200).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CONDUIT_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    if (tick % 3 == 0) {
                        level.sendParticles(SEA_GLASS, b.getX(), b.getY() + 6.5, b.getZ(), 6, 0.6, 0.6, 0.6, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof TideAbbess a)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 0.8F);
                    List<LivingEntity> targets = b.victims(level, a.centre(), a.radius + 6.0);
                    int volleys = a.deluge ? 3 : 2;
                    for (int v = 0; v < volleys; v++) {
                        for (LivingEntity e : targets) {
                            if (e instanceof Player) {
                                b.addEffect(delayed(v * 20, a.geyserOn(e, 20, 1.8, 14.0F)));
                            }
                        }
                        for (int i = 0; i < b.scaledCount(2); i++) {
                            b.addEffect(delayed(v * 20 + i * 3, geyser(a.randomSpot(), 20, 1.8, 14.0F)));
                        }
                    }
                })
                .build());
        // thurible: two censer swings, each warned: forehand at once (0.8 s), backhand 0.6 s later after a turn
        // toward the target; both leave brine
        out.add(BossAttack.of("thurible").anim(THURIBLE).phaseTwo().timing(16, 16, 14).range(0, 6.5).cooldown(150).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, CENSER_RANGE, CENSER_HALF, BRINE);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof TideAbbess a)) {
                        return;
                    }
                    if (tick == 0 || tick == 12) {
                        a.censerBlow(level, tick == 0 ? 0 : 1);
                    }
                    if (tick == 3 && t != null) {
                        a.turnToward(t, 35.0F);
                    }
                    if (tick > 3 && tick < 12 && tick % 2 == 0) {
                        b.telegraphArc(level, CENSER_RANGE, CENSER_HALF, BRINE);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // flood: she sinks to her knees and rings the censer three times as the water rises round her (1.5 s,
        // invulnerable), then drives the crozier into the floor: the rotunda floods and a ring of water rolls out
        out.add(BossAttack.of("flood").anim(FLOOD).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    floodGuard = 52;
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.5F, 0.5F + tick * 0.01F);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.4, ParticleTypes.SPLASH);
                    }
                    level.sendParticles(ParticleTypes.FALLING_WATER, b.getX(), b.getY() + 4.0, b.getZ(), 6, 1.2, 1.5, 1.2, 0);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.callFlood(level);
                    }
                })
                .build());
        // riptide: she bows low into the flood (1.0 s; three marks, one on each player, the rest at random, linked by
        // lines of sea glass), then swims through them in turn in 2 s: 14 to whoever is in her way
        out.add(BossAttack.of("riptide").anim(RIPTIDE).phaseTwo().timing(20, 40, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    marks.clear();
                    level.playSound(null, b, SoundEvents.DOLPHIN_SPLASH, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof TideAbbess a)) {
                        return;
                    }
                    if (tick < 14) {
                        a.pickMarks(level);
                    }
                    if (tick % 2 == 0) {
                        a.drawMarks(level, tick >= 14);
                    }
                    if (tick == 14) {
                        level.playSound(null, b, SoundEvents.TRIDENT_RIPTIDE_3.value(), SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> struck.clear())
                .active((b, level, t, tick) -> {
                    if (b instanceof TideAbbess a) {
                        a.riptideStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

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
        for (double a = -halfAngle; a <= halfAngle; a += 10) {
            Vec3 p = b.position().add(rotate(b.forward(), a).scale(r));
            level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 1.2, p.z, 6, 0.2, 0.3, 0.2, 0.1);
        }
        Vec3 c = b.ahead(r * 0.6);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
    }

    /** One swing of the censer: 12 and slowness in the arc, three brine clouds along it. */
    private void censerBlow(ServerLevel level, int which) {
        for (LivingEntity e : arcVictims(this, level, CENSER_RANGE, CENSER_HALF)) {
            strike(level, e, 12.0F, 1.0, 0.2);
            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
        }
        int life = deluge ? 140 : 100;
        for (double a : which == 0 ? new double[] {-45, 0, 45} : new double[] {-25, 25}) {
            addEffect(brineCloud(position().add(rotate(forward(), a).scale(4.0)), 2.2, life));
        }
        Vec3 c = ahead(3.0);
        level.sendParticles(BRINE, c.x, c.y + 1.2, c.z, 30, 2.0, 0.6, 2.0, 0.02);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.5F, 1.2F);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /**
     * A brine cloud: a low green haze for {@code life} ticks; whoever stands in it takes 3 and is slowed every half
     * second.
     */
    private static Effect brineCloud(Vec3 pos, double r, int life) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k % 3 == 0) {
                level.sendParticles(BRINE, pos.x, pos.y + 0.6, pos.z, 5, r * 0.5, 0.4, r * 0.5, 0.005);
                level.sendParticles(ParticleTypes.FALLING_WATER, pos.x, pos.y + 1.6, pos.z, 1, r * 0.4, 0.2, r * 0.4, 0);
            }
            if (k % 10 == 5) {
                for (LivingEntity e : boss.victims(level, pos, r + 1)) {
                    if (flatDist(e.position(), pos) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 2.0) {
                        if (e.hurtServer(level, boss.damageSources().mobAttack(boss), 3.0F)) {
                            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0), boss);
                        }
                    }
                }
            }
            return k >= life;
        };
    }

    /** Plans the next tide wave: from behind her toward the target, with its gaps. */
    private void planWave(@Nullable LivingEntity target) {
        Vec3 dir = forward();
        if (target != null) {
            Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
            if (to.lengthSqr() > 1.0E-3) {
                dir = to.normalize();
            }
        }
        waveDir = dir;
        waveGaps.clear();
        waveGaps.addAll(pickGaps(deluge ? 1 : 2, target));
    }

    /**
     * Lateral centres of {@code n} gaps across a wave, at least 5 blocks apart. With a target, the first gap is
     * never more than 9 blocks from where it stands across the wave (reachable in time).
     */
    private List<Double> pickGaps(int n, @Nullable LivingEntity target) {
        List<Double> out = new ArrayList<>();
        double half = waveReach() - 3.0;
        for (int tries = 0; out.size() < n && tries < 40; tries++) {
            double g = (getRandom().nextDouble() * 2 - 1) * half;
            if (out.isEmpty() && target != null && waveDir != null) {
                Vec3 side = new Vec3(-waveDir.z, 0, waveDir.x);
                double lat = target.position().subtract(centre()).dot(side);
                if (Math.abs(g - lat) > 9.0) {
                    continue;
                }
            }
            boolean ok = true;
            for (double o : out) {
                ok &= Math.abs(o - g) >= 5.0;
            }
            if (ok) {
                out.add(g);
            }
        }
        if (out.isEmpty()) {
            out.add(0.0);
        }
        return out;
    }

    private static boolean inGap(double lat, List<Double> gaps) {
        for (double g : gaps) {
            if (Math.abs(lat - g) <= GAP_HALF) {
                return true;
            }
        }
        return false;
    }

    /** The plan of a wave: its start line (foam) and the edges of every gap (sea glass) across the arena. */
    private void drawWavePlan(ServerLevel level, Vec3 dir, List<Double> gaps, double startAt) {
        Vec3 c = centre();
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        double reach = waveReach();
        for (double lat = -reach; lat <= reach; lat += 1.0) {
            double span = Math.sqrt(Math.max(0, reach * reach - lat * lat));
            if (span <= 0 || inGap(lat, gaps)) {
                continue;
            }
            Vec3 p = c.add(side.scale(lat)).add(dir.scale(Math.max(startAt, -span)));
            level.sendParticles(FOAM, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
        }
        for (double g : gaps) {
            for (double edge : new double[] {g - GAP_HALF, g + GAP_HALF}) {
                double span = Math.sqrt(Math.max(0, reach * reach - edge * edge));
                for (double s = -span; s <= span; s += 1.5) {
                    Vec3 p = c.add(side.scale(edge)).add(dir.scale(s));
                    level.sendParticles(SEA_GLASS, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                }
            }
        }
    }

    /**
     * A tide wave: after {@code warn} ticks (its plan drawn on the floor), a wall of water 2.6 high rolls across the
     * arena along {@code dir} at {@code speed}; whoever it meets outside the gaps takes {@code damage} once and is
     * swept along.
     */
    private Effect tideWave(Vec3 dir, List<Double> gaps, int warn, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        int[] t = {0};
        double reach = waveReach();
        Vec3 c = centre();
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    drawWavePlan(level, dir, gaps, -reach);
                }
                if (k == 0) {
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.AMBIENT_UNDERWATER_ENTER, SoundSource.HOSTILE, 3.0F, 0.6F);
                }
                return false;
            }
            double s = -reach + (k - warn) * speed;
            double span = Math.sqrt(Math.max(0, reach * reach - s * s));
            for (double lat = -span; lat <= span; lat += 0.9) {
                if (inGap(lat, gaps)) {
                    continue;
                }
                Vec3 p = c.add(side.scale(lat)).add(dir.scale(s));
                level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 0.4, p.z, 3, 0.2, 0.3, 0.2, 0.1);
                level.sendParticles(FOAM, p.x, p.y + 1.4 + (lat % 2 == 0 ? 0.6 : 0), p.z, 1, 0.15, 0.5, 0.15, 0);
                if (((int) Math.floor(lat)) % 3 == 0) {
                    level.sendParticles(ParticleTypes.FALLING_WATER, p.x, p.y + 2.6, p.z, 1, 0.2, 0.1, 0.2, 0);
                }
            }
            if (k % 6 == 0) {
                Vec3 m = c.add(dir.scale(s));
                level.playSound(null, m.x, m.y, m.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            for (LivingEntity e : boss.victims(level, c, reach + 2)) {
                Vec3 rel = e.position().subtract(c).multiply(1, 0, 1);
                double along = rel.dot(dir);
                double lat = rel.dot(side);
                if (Math.abs(along - s) <= 1.0 && !inGap(lat, gaps) && e.getY() - c.y < 2.6 && hit.add(e.getUUID())) {
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage)) {
                        e.push(dir.x * 1.3, 0.35, dir.z * 1.3);
                        e.hurtMarked = true;
                    }
                }
            }
            return s >= reach;
        };
    }

    /** One tick of the toll: the pull toward her, then the burst. */
    private void tollStep(ServerLevel level, int tick) {
        Vec3 from = tollFrom != null ? tollFrom : position();
        if (tick < 14) {
            for (LivingEntity e : victims(level, from, TOLL_PULL)) {
                Vec3 to = from.subtract(e.position()).multiply(1, 0, 1);
                double d = to.length();
                if (d < 2.5 || d > TOLL_PULL) {
                    continue;
                }
                Vec3 v = e.getDeltaMovement().add(to.normalize().scale(0.11));
                double h = Math.hypot(v.x, v.z);
                if (h > 0.6) {
                    v = new Vec3(v.x * 0.6 / h, v.y, v.z * 0.6 / h);
                }
                e.setDeltaMovement(v);
                e.hurtMarked = true;
                if (tick % 3 == 0) {
                    level.sendParticles(SEA_GLASS, e.getX(), e.getY() + 0.3, e.getZ(), 2, 0.2, 0.1, 0.2, 0);
                }
            }
            if (tick % 2 == 0) {
                telegraphRing(level, from, TOLL_BURST, BRINE);
                telegraphRing(level, from, TOLL_PULL * (1.0 - tick / 14.0) + TOLL_BURST * tick / 14.0, ParticleTypes.SPLASH);
            }
        } else if (tick == 16) {
            hitCircle(level, from, TOLL_BURST, 14.0F, 1.4, 0.4);
            for (int i = 0; i < 24; i++) {
                double a = Math.PI * 2 * i / 24;
                level.sendParticles(ParticleTypes.SPLASH, from.x + Math.cos(a) * 3, from.y + 0.5, from.z + Math.sin(a) * 3,
                        8, 0.5, 0.6, 0.5, 0.2);
            }
            level.sendParticles(BRINE, from.x, from.y + 1, from.z, 60, 2.5, 0.8, 2.5, 0.05);
            level.playSound(null, this, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.6F);
            level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 0.7F);
        }
    }

    /** One tick of the surge: glide on, hit what is in the way once, stop on walls. */
    private void surgeStep(ServerLevel level, double speed, float damage) {
        Vec3 f = forward().scale(speed);
        setDeltaMovement(f.x, getDeltaMovement().y, f.z);
        hurtMarked = true;
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.3, getZ(), 8, 0.6, 0.2, 0.6, 0.1);
        level.sendParticles(FOAM, getX(), getY() + 0.8, getZ(), 2, 0.5, 0.3, 0.5, 0);
        for (LivingEntity e : victims(level, position(), 2.6)) {
            if (flatDist(e.position(), position()) <= 2.2 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, damage, 1.1, 0.35);
            }
        }
        if (horizontalCollision) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
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
        double max = Math.max(3.0, Math.min(radius, FLOOD_MAX_R) - 2.0);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    private Vec3 randomSpot() {
        double a = getRandom().nextDouble() * Math.PI * 2;
        double r = 2 + getRandom().nextDouble() * Math.max(3, Math.min(radius, FLOOD_MAX_R) - 3);
        return centre().add(Math.cos(a) * r, 0, Math.sin(a) * r);
    }

    /**
     * A geyser on {@code pos}: a ring of splashes for {@code warn} ticks (foam for its last 6), then the brine bursts
     * up: {@code damage}, thrown up.
     */
    private static Effect geyser(Vec3 pos, int warn, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, warn - k <= 6 ? FOAM : ParticleTypes.SPLASH);
                }
                return false;
            }
            if (k == warn) {
                level.sendParticles(ParticleTypes.SPLASH, pos.x, pos.y + 1.0, pos.z, 40, radius * 0.3, 1.4, radius * 0.3, 0.3);
                level.sendParticles(FOAM, pos.x, pos.y + 1.5, pos.z, 16, radius * 0.25, 1.2, radius * 0.25, 0.02);
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 1.4F, 0.6F);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (flatDist(e.position(), pos) <= radius + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 2.0) {
                        boss.strike(level, e, damage, 0.2, 0.9);
                    }
                }
                return false;
            }
            if (k % 2 == 0) {                                   // the column lingers a moment
                level.sendParticles(ParticleTypes.FALLING_WATER, pos.x, pos.y + 3.0, pos.z, 3, 0.3, 0.6, 0.3, 0);
            }
            return k >= warn + 8;
        };
    }

    /** A geyser that follows {@code target} for the first third of its warning, then locks where it stands. */
    private Effect geyserOn(LivingEntity target, int warn, double radius, float damage) {
        int lock = Math.max(4, warn / 3);
        int[] t = {0};
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (!target.isAlive()) {
                    return true;
                }
                if (t[0]++ < lock) {
                    if (t[0] % 2 == 0) {
                        boss.telegraphRing(level, target.position(), radius, ParticleTypes.SPLASH);
                    }
                    return false;
                }
                inner[0] = geyser(new Vec3(target.getX(), floorY(target), target.getZ()), warn - lock, radius, damage);
            }
            return inner[0].tick(boss, level);
        };
    }

    /** The arena floor under a creature (a jumping player does not lift the geyser into the air). */
    private double floorY(LivingEntity e) {
        return Math.abs(e.getY() - centre().y) < 4.0 ? centre().y : e.getY();
    }

    private int minions(ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(centre())).inflate(radius + 12, 12, radius + 12),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    /** Acolytes alive at most: two (three in the flood), +1 per two extra players. */
    private int acolyteCap() {
        return scaledCount(deluge ? 3 : 2);
    }

    private void pickAcolyteSpots(ServerLevel level) {
        spots.clear();
        int room = Math.max(0, acolyteCap() - minions(level));
        int n = Math.min(room, scaledCount(2));
        double base = getRandom().nextDouble() * Math.PI * 2;
        for (int i = 0; i < n; i++) {
            double a = base + Math.PI * 2 * i / Math.max(1, n);
            spots.add(clampToArena(position().add(Math.cos(a) * 5.0, 0, Math.sin(a) * 5.0)));
        }
    }

    private void raiseAcolytes(ServerLevel level) {
        level.playSound(null, this, SoundEvents.DROWNED_AMBIENT_WATER, SoundSource.HOSTILE, 2.5F, 0.5F);
        for (Vec3 p : spots) {
            Mob m = net.minecraft.world.entity.EntityTypes.DROWNED.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (m == null) {
                continue;
            }
            m.snapTo(p.x, p.y, p.z, getYRot(), 0);
            m.addTag(MINION_TAG);
            m.setTarget(getTarget());
            level.addFreshEntity(m);
            level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 0.5, p.z, 40, 0.4, 0.8, 0.4, 0.2);
            level.sendParticles(BRINE, p.x, p.y + 1, p.z, 15, 0.4, 0.8, 0.4, 0.02);
        }
        spots.clear();
    }

    /** Riptide marks: every player in the arena (up to three) while they still follow, then random spots. */
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
            telegraphRing(level, m, 2.0, locked ? FOAM : SEA_GLASS);
            double len = flatDist(prev, m);
            for (double d = 0; d < len; d += 1.5) {
                Vec3 p = prev.lerp(m, d / Math.max(0.01, len));
                level.sendParticles(SEA_GLASS, p.x, m.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
            prev = m;
        }
    }

    /** One tick of the riptide: swim to the current mark, hit whoever is in the way once per leg. */
    private void riptideStep(ServerLevel level, int tick) {
        if (marks.isEmpty()) {
            return;
        }
        int leg = Math.min(marks.size() - 1, tick / 13);
        if (tick % 13 == 0) {
            struck.clear();
        }
        Vec3 goal = marks.get(leg);
        Vec3 to = goal.subtract(position()).multiply(1, 0, 1);
        int left = Math.max(1, 13 * (leg + 1) - tick - 2);
        double speed = Math.min(1.6, to.length() / left);
        if (to.lengthSqr() > 0.04) {
            Vec3 v = to.normalize().scale(speed);
            setDeltaMovement(v.x, getDeltaMovement().y, v.z);
            snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
        hurtMarked = true;
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.4, getZ(), 12, 0.8, 0.2, 0.8, 0.2);
        level.sendParticles(FOAM, getX(), getY() + 0.6, getZ(), 3, 0.7, 0.2, 0.7, 0);
        if (tick % 4 == 0) {
            level.playSound(null, this, SoundEvents.DOLPHIN_SWIM, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
        for (LivingEntity e : victims(level, position(), 3.0)) {
            if (flatDist(e.position(), position()) <= 2.2 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, 14.0F, 1.2, 0.4);
            }
        }
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

    // ------------------------------------------------------------------ the flood (real, temporary water)

    /** Phase 3 starts (or the flood comes back): water fills the floor, a ring rolls out, she swims fast. */
    private void callFlood(ServerLevel level) {
        boolean first = !deluge;
        deluge = true;
        if (first) {
            riptideTimer = 120;
        }
        floodArena(level);
        Vec3 c = position();
        addEffect(WayfarerBoss.wave(c, 14, 0.55, 12.0F, ParticleTypes.SPLASH));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("tide_abbess_flood"), 0.35,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 h = centre();
        level.sendParticles(ParticleTypes.SPLASH, h.x, h.y + 0.5, h.z, 300, radius * 0.6, 0.2, radius * 0.6, 0.2);
        level.playSound(null, this, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.CONDUIT_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /**
     * Fills every open floor cell within {@link #FLOOD_MAX_R} of the centre with a water source (one block deep).
     * Water that already stood nearby is remembered so the drain never touches it.
     */
    private void floodArena(ServerLevel level) {
        if (flooded) {
            return;
        }
        BlockPos c = BlockPos.containing(centre());
        floodY = c.getY();
        floodR = Math.min(FLOOD_MAX_R, Math.max(6, radius + 1));
        preWater.clear();
        int box = floodR + 6;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -box; dx <= box; dx++) {
            for (int dz = -box; dz <= box; dz++) {
                for (int y = floodY - 2; y <= floodY + 1; y++) {
                    p.set(c.getX() + dx, y, c.getZ() + dz);
                    if (level.getFluidState(p).is(FluidTags.WATER)) {
                        preWater.add(p.asLong());
                    }
                }
            }
        }
        for (int dx = -floodR; dx <= floodR; dx++) {
            for (int dz = -floodR; dz <= floodR; dz++) {
                if (dx * dx + dz * dz > floodR * floodR) {
                    continue;
                }
                p.set(c.getX() + dx, floodY, c.getZ() + dz);
                BlockPos below = p.below();
                if (level.getBlockState(p).isAir() && level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)) {
                    level.setBlock(p, Blocks.WATER.defaultBlockState(), 3);
                }
            }
        }
        flooded = true;
    }

    /**
     * Drains the flood: every water block (source or flowing, including sources the water made by itself at the
     * edges) in the flood's box that was not there before is removed. Flowing water further out dries on its own once
     * nothing feeds it.
     */
    private void drain(ServerLevel level) {
        if (!flooded) {
            return;
        }
        flooded = false;
        BlockPos c = BlockPos.containing(centre());
        int box = floodR + 6;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -box; dx <= box; dx++) {
            for (int dz = -box; dz <= box; dz++) {
                for (int y = floodY - 2; y <= floodY + 1; y++) {
                    p.set(c.getX() + dx, y, c.getZ() + dz);
                    if (!preWater.contains(p.asLong()) && level.getBlockState(p).is(Blocks.WATER)) {
                        level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                        if (getRandom().nextInt(12) == 0) {
                            level.sendParticles(ParticleTypes.SPLASH, p.getX() + 0.5, p.getY() + 0.2, p.getZ() + 0.5, 3, 0.3, 0.1, 0.3, 0.05);
                        }
                    }
                }
            }
        }
        preWater.clear();
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("tide_abbess_flood"));
        }
        level.playSound(null, c, SoundEvents.AMBIENT_UNDERWATER_EXIT, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (floodGuard > 0) {
            level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.1);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleFlood) {                   // a flood saved by an unload never outlives it
            staleFlood = false;
            flooded = true;
            drain(level);
        }
        if (floodGuard > 0) {
            floodGuard--;
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (flooded) {                      // the arena emptied (death, flight): the water drains at once
            boolean anyone = com.brasshaven.util.NearbyPlayers.any(level, new AABB(BlockPos.containing(centre())).inflate(radius + 14, 16, radius + 14),
                    p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
            if (!anyone) {
                drain(level);
            }
        }
        if (phase() == 1 && (deluge || flooded)) {      // the fight was reset: the tide goes out
            deluge = false;
            roarUntil = -1;
            drain(level);
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("tide_abbess_wrath"));
            }
        }
        boolean free = fighting && currentAttack() == null && !isStaggered() && tickCount > roarUntil;
        if (fighting && --acolyteTimer <= 0 && free && acolyteCap() - minions(level) > 0) {
            acolyteTimer = (int) Math.round(ACOLYTES_EVERY * cooldownScale());
            chain(level, "acolytes");
            free = false;
        }
        if (phase() == 2 && free) {
            if (!deluge && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "flood");
            } else if (deluge && !flooded) {            // players came back after the water drained
                chain(level, "flood");
            } else if (deluge && --riptideTimer <= 0) {
                riptideTimer = (int) Math.round(RIPTIDE_EVERY * cooldownScale());
                chain(level, "riptide");
            }
        }
        if (flooded && fighting && tickCount % 20 == 0) {    // the brine drags at whoever wades in it
            for (LivingEntity e : victims(level, centre(), floodR + 2.0)) {
                if (e instanceof Player && e.isInWater()) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0), this);
                }
            }
        }
        // ambience: brine smoke from the censer, drips off her robe, the sea-glass lamp
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        if (tickCount % 4 == 0) {
            double cx = getX() + Mth.cos(yaw) * 1.4 - Mth.sin(yaw) * 0.6;
            double cz = getZ() + Mth.sin(yaw) * 1.4 + Mth.cos(yaw) * 0.6;
            level.sendParticles(BRINE, cx, getY() + 1.8, cz, 1, 0.1, 0.2, 0.1, 0.01);
        }
        if (tickCount % 8 == 0) {
            level.sendParticles(ParticleTypes.FALLING_WATER, getX(), getY() + 3.0, getZ(), 2, 0.8, 1.2, 0.8, 0);
        }
        if (flooded && tickCount % 3 == 0 && getDeltaMovement().horizontalDistanceSqr() > 0.01) {
            level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.9, getZ(), 6, 0.8, 0.1, 0.8, 0.1);
        }
        if (tickCount % 90 == 0) {
            level.playSound(null, this, SoundEvents.DROWNED_AMBIENT_WATER, SoundSource.HOSTILE, 1.2F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("tide_abbess_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, ParticleTypes.SPLASH));
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.5, getZ(), 80, 1.5, 2.0, 1.5, 0.2);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        drain(level);
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(blockPosition()).inflate(40),
                m -> m.entityTags().contains(MINION_TAG))) {
            level.sendParticles(ParticleTypes.SPLASH, m.getX(), m.getY() + 1, m.getZ(), 15, 0.3, 0.6, 0.3, 0.1);
            m.discard();
        }
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.5, getZ(), 150, 1.2, 2.0, 1.2, 0.3);
        level.sendParticles(BRINE, getX(), getY() + 3, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_DEATH, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            drain(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("AbbessCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("AbbessRadius", radius);
        output.putBoolean("AbbessDeluge", deluge);
        output.putBoolean("AbbessFlood", flooded || staleFlood);
        output.putInt("AbbessFloodY", floodY);
        output.putInt("AbbessFloodR", floodR);
        output.store("AbbessPreWater", Codec.LONG.listOf(), List.copyOf(preWater));
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("AbbessCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("AbbessRadius", 14);
        deluge = input.getBooleanOr("AbbessDeluge", false) && phase() == 2;
        staleFlood = input.getBooleanOr("AbbessFlood", false);
        floodY = input.getIntOr("AbbessFloodY", 0);
        floodR = input.getIntOr("AbbessFloodR", FLOOD_MAX_R);
        preWater.clear();
        input.read("AbbessPreWater", Codec.LONG.listOf()).ifPresent(preWater::addAll);
        flooded = false;
    }
}
