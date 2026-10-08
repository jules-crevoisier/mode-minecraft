package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.LockMaster.BASH;
import static com.brasshaven.generated.MobAnims.LockMaster.BURST;
import static com.brasshaven.generated.MobAnims.LockMaster.FLUSH;
import static com.brasshaven.generated.MobAnims.LockMaster.JETS;
import static com.brasshaven.generated.MobAnims.LockMaster.REEL;
import static com.brasshaven.generated.MobAnims.LockMaster.ROAR;
import static com.brasshaven.generated.MobAnims.LockMaster.SKEWER;
import static com.brasshaven.generated.MobAnims.LockMaster.SLUICE;
import static com.brasshaven.generated.MobAnims.LockMaster.SPIN;
import static com.brasshaven.generated.MobAnims.LockMaster.STAGGER;
import static com.brasshaven.generated.MobAnims.LockMaster.SURGE;
import static com.brasshaven.generated.MobAnims.LockMaster.THRUST;

/**
 * Le Maître des écluses (The Lock-Master), warden of the Great Aqueduct: a 5.2-block hydraulic warden in riveted
 * brass, a whole sluice gate on his left arm for a shield and a pressure-lance longer than he is tall in his right.
 * He waits in the great cistern under the castellum (radius 17, a ring of eight columns, a dome 9 to 17 high).
 * <p>A hard fight: 600 health, armour 14, poise 120, hits of 7 to 18. Three phases:
 * <ul>
 *     <li>Phase 1: <b>lance thrust</b> (9.5 blocks of reach, 16), <b>spin</b> (all round him, 13; he answers anyone
 *     who lingers behind him), <b>shield bash</b> (he walks behind the gate, which blocks every frontal hit: a heavy
 *     blow of 11+ or any hit in the back breaks his guard and he reels open; else he rushes, 14), <b>pressure jets</b>
 *     (a jet of water sweeps 100 degrees in front of him, 10 and pushed back; the columns and the gates stop it) and
 *     <b>sluice gates</b> (marked tiles on and around every player; gates of iron bars slam down from the dome on them,
 *     18, and stand 9 s as walls).</li>
 *     <li>Phase 2 (a roar at 65%): faster, combos, the jets sweep there and back, <b>skewer</b> (three thrusts),
 *     <b>surge</b> (a jet-propelled ram down a 16-block line; it breaks on a gate and leaves him reeling) and
 *     <b>burst</b> (the gate slammed into the floor, a ring of steam, 14, then a wave to jump, 7).</li>
 *     <li>Phase 3 (at 30%): the <b>flush</b>. He wrenches his valve wheel (invulnerable 1.5 s) and the cistern's
 *     sluices open: for 6.8 s a current sweeps the floor in one direction (the lee of a column or a gate shelters you)
 *     while he charges four times down it. Again every 22 s.</li>
 * </ul>
 * Every gate block he drops is temporary: removed when it expires, when a charge breaks it, when the arena empties,
 * when he dies or is removed, and after a reload.
 */
public class LockMaster extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 5.2F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double LANCE = 9.5;
    private static final double SPIN_R = 6.5;
    private static final double JET_SWEEP = 50.0;
    private static final float HEAVY_HIT = 11.0F;
    private static final int GATE_LIFE = 180;
    private static final int MAX_GATE_BLOCKS = 150;
    private static final int FLUSH_EVERY = 440;
    private static final int LEG = 34;
    private static final DustParticleOptions WATER = new DustParticleOptions(0x46C4EC, 1.3F);
    private static final DustParticleOptions FOAM = new DustParticleOptions(0xD8F6FF, 1.5F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xE8B850, 1.3F);
    private static final BlockParticleOption BARS = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.IRON_BARS.defaultBlockState());

    /** A gate about to drop: its floor cells (feet level) and where its drips fall from. */
    private record GatePlan(List<BlockPos> cells, Vec3 mid, double ceil) {}

    private @Nullable Vec3 centre;
    private int radius = 16;
    /** The shield is up (bash wind-up): frontal hits are blocked. */
    private boolean guarding;
    /** Until this tick the guard is broken: he takes 30% more damage. */
    private int reelUntil = -1;
    /** Gate blocks he dropped, with the tick they lift. Never left behind. */
    private final Map<BlockPos, Integer> gates = new HashMap<>();
    /** Gates saved by an unload: removed on the first tick. */
    private final List<BlockPos> staleGates = new ArrayList<>();
    private final List<GatePlan> plans = new ArrayList<>();
    /** Phase 3 has started (the sluices were opened once). */
    private boolean opened;
    private int flushTimer;
    private int flushGuard;
    private Vec3 flushDir = new Vec3(1, 0, 0);
    private @Nullable LivingEntity legTarget;
    private boolean legStopped;
    private float jetBase;
    private final Set<UUID> struck = new HashSet<>();
    private int roarUntil = -1;
    private int backTicks;
    private int nextBackSpin;

    public LockMaster(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.LockMaster.TICKS;
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
        return 120.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 6.0;
    }

    /** Phase 3 counts as a third stage of the fight (the base class knows only two). */
    public boolean isFlushing() {
        return opened;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

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

    private double jetReach() {
        return opened ? 22.0 : 18.0;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // thrust: the lance drawn back along his right side (0.8 s, a line of water-light marks its reach), then driven
        // straight ahead: 9.5 blocks of reach
        out.add(BossAttack.of("thrust").anim(THRUST).timing(16, 4, 14).range(0, 10.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLine(level, LANCE, tick >= 10 ? FOAM : WATER);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitLine(level, LANCE, 1.0, 16.0F, 1.0);
                    sprayLine(level, LANCE);
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_KNOCKBACK, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 5.0 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "spin");
                    }
                })
                .build());
        // spin: shield tucked, lance swung back across his left side (0.9 s, a ring of brass round him), then he pivots
        // on his heel and the lance sweeps all round at knee height. bossTick also starts it on whoever lingers behind
        out.add(BossAttack.of("spin").anim(SPIN).timing(18, 4, 16).range(0, 6.0).cooldown(120).weight(6).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), SPIN_R, BRASS);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), SPIN_R, 13.0F, 1.4, 0.3);
                    for (int i = 0; i < 24; i++) {
                        double a = Math.PI * 2 * i / 24;
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX() + Math.cos(a) * 4.5, b.getY() + 0.8,
                                b.getZ() + Math.sin(a) * 4.5, 1, 0, 0, 0, 0);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());
        // shield bash: the sluice gate raised square in front (1.2 s) while he walks behind it: frontal hits are blocked
        // unless heavy (11+); a hit in the back breaks the guard too (he reels). Then the gate rushes forward
        out.add(BossAttack.of("bash").anim(BASH).timing(24, 8, 16).range(0, 12.0).cooldown(160).weight(8)
                .start((b, level, t, tick) -> {
                    guarding = true;
                    struck.clear();
                    level.playSound(null, b, SoundEvents.IRON_DOOR_CLOSE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    Vec3 f = b.forward().scale(0.07);
                    b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                    if (tick % 3 == 0) {
                        drawLine(level, 7.0, BRASS);
                        Vec3 p = b.ahead(1.6);
                        level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 2.2, p.z, 3, 0.8, 1.0, 0.8, 0.05);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 1.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    guarding = false;
                    level.playSound(null, b, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 6) {
                        rush(level, opened ? 1.2 : 1.0, 14.0F, 1.7);
                    } else {
                        b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    guarding = false;
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < LANCE && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "thrust");
                    }
                })
                .build());
        // pressure jets: feet planted, the lance levelled at the hip (1.0 s; the two edges of the sweep are drawn), then
        // the nozzle opens and a jet of water sweeps 100 degrees in front of him, turning his whole body with it. Phase
        // 2: it sweeps there and back. Columns and gates stop it: hide behind one, or get behind him
        out.add(BossAttack.of("jets").anim(JETS).timing(20, 40, 16).range(0, 26.0).cooldown(200).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        drawJetPlan(level);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    jetBase = b.getYRot() - (float) JET_SWEEP;
                    struck.clear();
                    level.playSound(null, b, SoundEvents.BUCKET_EMPTY, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    double sweep = 2 * JET_SWEEP;
                    double a;
                    if (b.phase() == 1) {
                        a = sweep * tick / 39.0;
                    } else if (tick < 20) {
                        a = sweep * tick / 19.0;
                    } else {
                        if (tick == 20) {
                            struck.clear();
                        }
                        a = sweep * (1.0 - (tick - 20) / 19.0);
                    }
                    b.snapFacing(jetBase + (float) a);
                    fireJet(level, opened ? 11.0F : 10.0F);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .build());
        // sluice gates: the lance raised to the dome (1.0 s; the marked tiles on and around every player are outlined in
        // brass, water drips from the vault above them), then the butt slammed into the floor: the gates drop one after
        // another, the first half a second later
        out.add(BossAttack.of("sluice").anim(SLUICE).timing(20, 10, 18).range(0, 26.0).cooldown(260).weight(7).track(false)
                .start((b, level, t, tick) -> {
                    planGates(level);
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (GatePlan p : plans) {
                            drawPlan(level, p, false);
                        }
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.IRON_DOOR_OPEN, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int i = 0; i < plans.size(); i++) {
                        b.addEffect(gateDrop(plans.get(i), 10 + 3 * i));
                    }
                    plans.clear();
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .build());
        // guard broken: never rolled; hurtServer starts it when a heavy blow or a hit in the back breaks the shield
        out.add(BossAttack.of("reel").anim(REEL).timing(6, 4, 30).range(999, 999).cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guarding = false;
                    reelUntil = b.tickCount + 40;
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    level.playSound(null, b, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.6F);
                    level.sendParticles(ParticleTypes.CRIT, b.getX(), b.getY() + 3.0, b.getZ(), 30, 0.8, 0.8, 0.8, 0.3);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // skewer: three thrusts (0.7 s, then 0.5 s apart), turning up to 30 degrees toward the target between them
        out.add(BossAttack.of("skewer").anim(SKEWER).phaseTwo().timing(14, 24, 14).range(0, 10.0).cooldown(120).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLine(level, LANCE, WATER);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 10 || tick == 20) {
                        b.hitLine(level, LANCE, 1.0, 13.0F, 0.9);
                        sprayLine(level, LANCE);
                        level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.01F);
                    }
                    if ((tick == 4 || tick == 14) && t != null) {
                        turnToward(t, 30.0F);
                    }
                    if ((tick > 4 && tick < 10) || (tick > 14 && tick < 20)) {
                        drawLine(level, LANCE, FOAM);
                    }
                })
                .build());
        // surge: crouched, lance levelled, the tanks hissing (0.8 s, a line of water-light 16 blocks long), then the jet
        // drives him down it like a ram; it breaks on a gate (he reels)
        out.add(BossAttack.of("surge").anim(SURGE).phaseTwo().timing(16, 14, 16).range(6.0, 22.0).cooldown(140).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLine(level, 16.0, tick >= 10 ? FOAM : WATER);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    struck.clear();
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> rush(level, 1.15, 15.0F, 1.5))
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (t != null && b.distanceTo(t) < LANCE && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "thrust");
                    }
                })
                .build());
        // burst: the gate lifted high (0.9 s, a ring of steam round him), slammed edge-down into the floor: scalding
        // steam bursts round him (r 6) and a wave rolls out to 12 (jump it)
        out.add(BossAttack.of("burst").anim(BURST).phaseTwo().timing(18, 4, 16).range(0, 7.0).cooldown(180).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 6.0, ParticleTypes.CLOUD);
                        level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 4.0, b.getZ() + 0.0, 3, 0.6, 0.3, 0.6, 0.02);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 6.0, 14.0F, 1.6, 0.6);
                    b.addEffect(WayfarerBoss.wave(b.position(), 12.0, 0.6, 7.0F, ParticleTypes.CLOUD));
                    for (int i = 0; i < 20; i++) {
                        double a = Math.PI * 2 * i / 20;
                        level.sendParticles(ParticleTypes.CLOUD, b.getX() + Math.cos(a) * 3.5, b.getY() + 0.5,
                                b.getZ() + Math.sin(a) * 3.5, 3, 0.6, 0.4, 0.6, 0.08);
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.6F);
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // flush: he plants the lance and wrenches the valve wheel on his shoulder round (1.5 s, invulnerable; chevrons
        // of foam show where the water will run), then the sluices open: a current sweeps the floor for 6.8 s while he
        // charges four times down the arena, each charge aimed at a player for 0.6 s
        out.add(BossAttack.of("flush").anim(FLUSH).phaseTwo().timing(30, 4 * LEG, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    flushGuard = 32;
                    double a = b.getRandom().nextInt(8) * Math.PI / 4;
                    flushDir = new Vec3(Math.cos(a), 0, Math.sin(a));
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.4F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        drawChevrons(level);
                    }
                    if (tick == 10 || tick == 20) {
                        level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                    if (tick == 24) {
                        level.playSound(null, b, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    boolean first = !opened;
                    opened = true;
                    if (first) {
                        var speed = b.getAttribute(Attributes.MOVEMENT_SPEED);
                        if (speed != null) {
                            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("lock_master_flush"),
                                    0.12, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
                        }
                        b.addEffect(WayfarerBoss.wave(b.position(), 14.0, 0.55, 12.0F, ParticleTypes.SPLASH));
                    }
                    b.addEffect(current(flushDir, 4 * LEG));
                    flushTimer = (int) Math.round(FLUSH_EVERY * cooldownScale()) + 4 * LEG;
                    level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.3F);
                    level.playSound(null, b, SoundEvents.AMBIENT_UNDERWATER_ENTER, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .active((b, level, t, tick) -> flushLeg(level, tick))
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    flushTimer = (int) Math.round(FLUSH_EVERY * cooldownScale());
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void drawLine(ServerLevel level, double length, DustParticleOptions p) {
        for (double d = 1.5; d <= length; d += 1.0) {
            Vec3 at = ahead(d);
            level.sendParticles(p, at.x, at.y + 0.15, at.z, 1, 0.1, 0, 0.1, 0);
        }
    }

    private void sprayLine(ServerLevel level, double length) {
        for (double d = 2.0; d <= length; d += 1.0) {
            Vec3 at = ahead(d);
            level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 1.6, at.z, 3, 0.2, 0.2, 0.2, 0.1);
        }
        Vec3 tip = ahead(length);
        level.sendParticles(ParticleTypes.CLOUD, tip.x, tip.y + 1.6, tip.z, 4, 0.3, 0.3, 0.3, 0.05);
    }

    /** One tick of a rush (bash, surge): move on, hit what is in the way once, break on gates (and reel) or walls. */
    private void rush(ServerLevel level, double speed, float damage, double knock) {
        Vec3 f = forward().scale(speed);
        Vec3 next = position().add(f);
        if (flatDist(next, centre()) > radius - 1.5 && flatDist(next, centre()) > flatDist(position(), centre())) {
            setDeltaMovement(0, getDeltaMovement().y, 0);       // never out through a doorway
            return;
        }
        setDeltaMovement(f.x, getDeltaMovement().y, f.z);
        hurtMarked = true;
        for (LivingEntity e : victims(level, position(), 3.0)) {
            if (flatDist(e.position(), position()) <= 2.4 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, damage, knock, 0.4);
                if (opened) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                }
            }
        }
        if (tickCount % 2 == 0) {
            level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.3, getZ(), 8, 1.0, 0.2, 1.0, 0.2);
        }
        if (horizontalCollision) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            if (shatterGatesNear(level, BlockPos.containing(ahead(1.8)), 2.5) && currentAttack() != null
                    && "surge".equals(currentAttack().name)) {
                chain(level, "reel");                           // he rammed his own gate
            }
        }
    }

    private void turnToward(LivingEntity target, float maxTurn) {
        double dx = target.getX() - getX();
        double dz = target.getZ() - getZ();
        float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private static Vec3 dirOfYaw(double yaw) {
        double r = Math.toRadians(yaw);
        return new Vec3(-Math.sin(r), 0, Math.cos(r));
    }

    /** How far a jet from the nozzle reaches along {@code dir} before a column, a gate or a wall stops it. */
    private double jetLength(ServerLevel level, Vec3 dir) {
        Vec3 from = position().add(0, 1.6, 0).add(dir.scale(1.5));
        Vec3 to = from.add(dir.scale(jetReach()));
        BlockHitResult hit = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return 1.5 + (hit.getType() == HitResult.Type.MISS ? jetReach() : hit.getLocation().distanceTo(from));
    }

    /** The jet's plan: its two edges (foam), stopped where the jet will be stopped, and the arc between them. */
    private void drawJetPlan(ServerLevel level) {
        float yaw = getYRot();
        for (double a : new double[] {-JET_SWEEP, JET_SWEEP}) {
            Vec3 dir = dirOfYaw(yaw + a);
            double len = jetLength(level, dir);
            for (double d = 2.0; d <= len; d += 1.2) {
                Vec3 p = position().add(dir.scale(d));
                level.sendParticles(FOAM, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
            }
        }
        for (double a = -JET_SWEEP; a <= JET_SWEEP; a += 10) {
            Vec3 p = position().add(dirOfYaw(yaw + a).scale(5.0));
            level.sendParticles(WATER, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** One tick of the jet along the current facing: whoever it reaches is hit once per pass and driven back. */
    private void fireJet(ServerLevel level, float damage) {
        Vec3 fwd = forward();
        double len = jetLength(level, fwd);
        for (double d = 2.0; d <= len; d += 0.8) {
            Vec3 p = position().add(fwd.scale(d));
            level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 1.6, p.z, 2, 0.15, 0.15, 0.15, 0.05);
            if (((int) (d * 10)) % 16 == 0) {
                level.sendParticles(WATER, p.x, p.y + 1.6, p.z, 1, 0.1, 0.1, 0.1, 0);
            }
        }
        Vec3 end = position().add(fwd.scale(len));
        level.sendParticles(ParticleTypes.CLOUD, end.x, end.y + 1.5, end.z, 2, 0.3, 0.4, 0.3, 0.05);
        level.sendParticles(ParticleTypes.SPLASH, end.x, end.y + 1.5, end.z, 8, 0.5, 0.5, 0.5, 0.2);
        for (LivingEntity e : victims(level, position(), len + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            double dy = e.getY() - getY();
            if (along >= 1.0 && along <= len && side <= 0.9 + e.getBbWidth() / 2 && dy > -1.5 && dy < 2.6
                    && struck.add(e.getUUID())) {
                if (e.hurtServer(level, damageSources().mobAttack(this), damage)) {
                    e.push(fwd.x * 1.2, 0.25, fwd.z * 1.2);
                    e.hurtMarked = true;
                }
            }
        }
    }

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(3.0, Math.min(radius, 16) - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    // ------------------------------------------------------------------ sluice gates (real, temporary blocks)

    /** Marks the gates of the next sluice: one on every player (up to four) plus a few strays, across their way. */
    private void planGates(ServerLevel level) {
        plans.clear();
        List<Vec3> marks = new ArrayList<>();
        for (LivingEntity e : victims(level, centre(), radius + 4.0)) {
            if (e instanceof Player && marks.size() < 4) {
                marks.add(clampToArena(e.position(), 2.0));
            }
        }
        int strays = scaledCount(opened ? 3 : phase() == 2 ? 2 : 1);
        for (int i = 0; i < strays && marks.size() < 7; i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double r = 4 + getRandom().nextDouble() * Math.max(2, Math.min(radius, 16) - 7);
            marks.add(centre().add(Math.cos(a) * r, 0, Math.sin(a) * r));
        }
        int y = Mth.floor(centre().y + 0.01);
        for (Vec3 m : marks) {
            Vec3 to = m.subtract(position());
            boolean alongZ = Math.abs(to.x) > Math.abs(to.z);   // the gate stands across the line from him
            List<BlockPos> cells = new ArrayList<>();
            BlockPos mid = new BlockPos(Mth.floor(m.x), y, Mth.floor(m.z));
            for (int k = -1; k <= 1; k++) {
                cells.add(alongZ ? mid.offset(0, 0, k) : mid.offset(k, 0, 0));
            }
            double ceil = y + 8;
            for (int dy = 3; dy <= 18; dy++) {
                if (!level.getBlockState(mid.above(dy)).isAir()) {
                    ceil = y + dy - 0.1;
                    break;
                }
            }
            plans.add(new GatePlan(cells, Vec3.atBottomCenterOf(mid), ceil));
        }
    }

    /** A marked gate: brass squares on its tiles and water dripping from the vault above (foam when it is close). */
    private void drawPlan(ServerLevel level, GatePlan p, boolean close) {
        for (BlockPos c : p.cells()) {
            double x = c.getX(), z = c.getZ(), y = c.getY() + 0.1;
            DustParticleOptions d = close ? FOAM : BRASS;
            level.sendParticles(d, x + 0.15, y, z + 0.15, 1, 0, 0, 0, 0);
            level.sendParticles(d, x + 0.85, y, z + 0.15, 1, 0, 0, 0, 0);
            level.sendParticles(d, x + 0.15, y, z + 0.85, 1, 0, 0, 0, 0);
            level.sendParticles(d, x + 0.85, y, z + 0.85, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.DRIPPING_WATER, x + 0.5, p.ceil(), z + 0.5, close ? 3 : 1, 0.3, 0, 0.3, 0);
        }
    }

    /** The gate drops {@code delay} ticks after the slam: still drawn until then, then the bars come down. */
    private Effect gateDrop(GatePlan plan, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 3 == 0 || delay - k <= 6) {
                    drawPlan(level, plan, delay - k <= 8);
                }
                return false;
            }
            slamGate(level, plan);
            return true;
        };
    }

    private void slamGate(ServerLevel level, GatePlan plan) {
        int life = (opened ? GATE_LIFE + 40 : GATE_LIFE);
        Vec3 c = centre();
        for (BlockPos col : plan.cells()) {
            Vec3 mid = Vec3.atBottomCenterOf(col);
            if (flatDist(mid, c) > Math.min(radius, 16) - 1.0 || flatDist(mid, position()) < 2.0) {
                continue;
            }
            BlockPos below = col.below();
            if (!level.getBlockState(col).isAir() || !level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)) {
                continue;
            }
            AABB cell = new AABB(col.getX(), col.getY(), col.getZ(), col.getX() + 1, col.getY() + 3, col.getZ() + 1);
            boolean occupied = false;
            for (LivingEntity e : victims(level, mid, 2.0)) {
                if (e.getBoundingBox().intersects(cell)) {
                    occupied = true;
                    if (struck.add(e.getUUID())) {
                        strike(level, e, 18.0F, 0.6, 0.0);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                    }
                }
            }
            if (!level.getEntitiesOfClass(LivingEntity.class, cell, LivingEntity::isAlive).isEmpty()) {
                occupied = true;
            }
            level.sendParticles(ParticleTypes.SPLASH, mid.x, mid.y + 0.3, mid.z, 10, 0.4, 0.2, 0.4, 0.2);
            level.sendParticles(BARS, mid.x, mid.y + 1.5, mid.z, 6, 0.3, 0.8, 0.3, 0.1);
            if (occupied) {
                continue;                                       // whoever stood there keeps the column open
            }
            for (int dy = 0; dy < 3 && gates.size() < MAX_GATE_BLOCKS; dy++) {
                BlockPos p = col.above(dy);
                if (!level.getBlockState(p).isAir()) {
                    break;
                }
                level.setBlock(p, Blocks.IRON_BARS.defaultBlockState(), 3);
                gates.put(p.immutable(), tickCount + life + getRandom().nextInt(20));
            }
        }
        struck.clear();
        level.playSound(null, plan.mid().x, plan.mid().y, plan.mid().z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, plan.mid().x, plan.mid().y, plan.mid().z, SoundEvents.IRON_DOOR_CLOSE, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** A charge broke on a gate: every gate block within {@code r} bursts. True when there was one. */
    private boolean shatterGatesNear(ServerLevel level, BlockPos at, double r) {
        boolean any = false;
        Iterator<Map.Entry<BlockPos, Integer>> it = gates.entrySet().iterator();
        while (it.hasNext()) {
            BlockPos p = it.next().getKey();
            if (p.distSqr(at) <= r * r + 4) {
                removeGateBlock(level, p, true);
                it.remove();
                any = true;
            }
        }
        if (any) {
            level.playSound(null, at, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
            level.playSound(null, at, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.7F);
        }
        return any;
    }

    private static void removeGateBlock(ServerLevel level, BlockPos p, boolean loud) {
        if (level.getBlockState(p).is(Blocks.IRON_BARS)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
            level.sendParticles(BARS, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, loud ? 10 : 4, 0.3, 0.3, 0.3, 0.05);
        }
    }

    /** Lifts the gates whose time is up, or all of them. */
    private void clearGates(ServerLevel level, boolean all) {
        if (gates.isEmpty()) {
            return;
        }
        boolean any = false;
        Iterator<Map.Entry<BlockPos, Integer>> it = gates.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<BlockPos, Integer> en = it.next();
            if (all || tickCount >= en.getValue()) {
                removeGateBlock(level, en.getKey(), false);
                it.remove();
                any = true;
            }
        }
        if (any) {
            level.playSound(null, this, SoundEvents.IRON_DOOR_OPEN, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ the flush (phase 3)

    /** Where the water will run: rows of foam chevrons across the arena, pointing downstream. */
    private void drawChevrons(ServerLevel level) {
        Vec3 c = centre();
        Vec3 side = new Vec3(-flushDir.z, 0, flushDir.x);
        double r = Math.min(radius, 16) - 1.0;
        for (double a = -r + 2; a <= r - 2; a += 4.0) {
            for (double l = -r + 2; l <= r - 2; l += 4.0) {
                if (a * a + l * l > r * r) {
                    continue;
                }
                Vec3 tip = c.add(flushDir.scale(a + 0.8)).add(side.scale(l));
                for (int s = -1; s <= 1; s += 2) {
                    for (double k = 0.0; k <= 1.0; k += 0.5) {
                        Vec3 p = tip.subtract(flushDir.scale(k)).add(side.scale(s * k));
                        level.sendParticles(FOAM, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                    }
                }
            }
        }
    }

    /** Behind a column or a gate (seen from upstream, within 3 blocks): the current does not reach there. */
    private boolean sheltered(ServerLevel level, LivingEntity e, Vec3 dir) {
        for (double d = 1.0; d <= 3.0; d += 1.0) {
            BlockPos p = BlockPos.containing(e.position().subtract(dir.scale(d)).add(0, 0.2, 0));
            if (level.getBlockState(p).blocksMotion() || level.getBlockState(p.above()).blocksMotion()) {
                return true;
            }
        }
        return false;
    }

    /** The current: for {@code life} ticks every player on the floor is pushed downstream (capped 0.42 b/t). */
    private Effect current(Vec3 dir, int life) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            Vec3 c = centre();
            double r = Math.min(radius, 16) + 2.0;
            for (LivingEntity e : boss.victims(level, c, r)) {
                if (!(e instanceof Player) || Math.abs(e.getY() - c.y) > 3.0 || sheltered(level, e, dir)) {
                    continue;
                }
                Vec3 v = e.getDeltaMovement().add(dir.scale(0.07));
                double along = v.x * dir.x + v.z * dir.z;
                if (along > 0.42) {
                    v = v.subtract(dir.scale(along - 0.42));
                }
                e.setDeltaMovement(v);
                e.hurtMarked = true;
            }
            if (k % 2 == 0) {
                for (int i = 0; i < 26; i++) {
                    double a = boss.getRandom().nextDouble() * Math.PI * 2;
                    double rr = Math.sqrt(boss.getRandom().nextDouble()) * (r - 2.5);
                    double x = c.x + Math.cos(a) * rr;
                    double z = c.z + Math.sin(a) * rr;
                    level.sendParticles(ParticleTypes.CLOUD, x, c.y + 0.15, z, 0, dir.x, 0.0, dir.z, 0.35);
                    if (i % 3 == 0) {
                        level.sendParticles(ParticleTypes.SPLASH, x, c.y + 0.2, z, 2, 0.3, 0.05, 0.3, 0.1);
                    }
                }
            }
            if (k % 20 == 0) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.7F);
            }
            return k >= life;
        };
    }

    /** One tick of the flush charges: aim at a player for 0.6 s (a line drawn), charge 0.9 s, rest 0.2 s; four legs. */
    private void flushLeg(ServerLevel level, int tick) {
        int k = tick % LEG;
        int leg = tick / LEG;
        if (k == 0) {
            List<LivingEntity> players = new ArrayList<>();
            for (LivingEntity e : victims(level, centre(), radius + 4.0)) {
                if (e instanceof Player) {
                    players.add(e);
                }
            }
            legTarget = players.isEmpty() ? getTarget() : players.get(leg % players.size());
            legStopped = false;
            struck.clear();
        }
        if (k < 12) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            if (legTarget != null && legTarget.isAlive()) {
                turnToward(legTarget, 40.0F);
            }
            if (k % 2 == 0) {
                drawLine(level, 16.0, k >= 6 ? FOAM : WATER);
            }
            return;
        }
        if (k == 12) {
            level.playSound(null, this, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.5F, 0.5F);
            level.playSound(null, this, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
        if (k < 30 && !legStopped) {
            rush(level, 1.1, 16.0F, 1.5);
            if (horizontalCollision || getDeltaMovement().horizontalDistanceSqr() < 1.0E-4) {
                legStopped = true;
            }
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
    }

    // ------------------------------------------------------------------ damage: the guard

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (flushGuard > 0) {
            return false;
        }
        if (tickCount < reelUntil) {
            amount *= 1.3F;
        }
        if (guarding && !source.is(DamageTypeTags.BYPASSES_SHIELD) && source.getSourcePosition() != null) {
            Vec3 to = source.getSourcePosition().subtract(position()).multiply(1, 0, 1);
            double dot = to.lengthSqr() > 1.0E-4 ? to.normalize().dot(forward()) : 0.0;
            if (dot >= 0.2) {
                if (amount < HEAVY_HIT) {
                    level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F,
                            0.5F + getRandom().nextFloat() * 0.2F);
                    Vec3 p = ahead(1.5);
                    level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 2.2, p.z, 12, 0.5, 0.7, 0.5, 0.3);
                    return false;
                }
                breakGuard(level);
            } else if (dot <= -0.3) {
                breakGuard(level);
                amount *= 1.25F;
            }
        }
        return super.hurtServer(level, source, amount);
    }

    private void breakGuard(ServerLevel level) {
        guarding = false;
        chain(level, "reel");
    }

    // ------------------------------------------------------------------ ticking, cleanup

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleGates.isEmpty()) {                        // gates saved by an unload never outlive it
            for (BlockPos p : staleGates) {
                removeGateBlock(level, p, false);
            }
            staleGates.clear();
        }
        if (flushGuard > 0) {
            flushGuard--;
        }
        BossAttack cur = currentAttack();
        if (guarding && (cur == null || !"bash".equals(cur.name))) {
            guarding = false;                               // interrupted (stagger, phase change)
        }
        clearGates(level, false);
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 16, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone) {
            clearGates(level, true);                        // the arena emptied: the gates lift at once
        }
        if (phase() == 1 && opened) {                       // the fight was reset: the sluices close
            opened = false;
            roarUntil = -1;
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("lock_master_flush"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("lock_master_wrath"));
            }
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (free && phase() == 2) {
            if (!opened && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "flush");
                free = false;
            } else if (opened && --flushTimer <= 0) {
                chain(level, "flush");
                free = false;
            }
        }
        // whoever lingers behind him is answered with the spin
        if (free && distanceTo(target) < SPIN_R) {
            Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
            if (to.lengthSqr() > 1.0E-3 && to.normalize().dot(forward()) < -0.4) {
                if (++backTicks >= 24 && tickCount >= nextBackSpin) {
                    backTicks = 0;
                    nextBackSpin = tickCount + (int) Math.round(160 * cooldownScale());
                    chain(level, "spin");
                }
            } else {
                backTicks = 0;
            }
        }
        // ambience: drips off his plates, steam from the tanks, the nozzle hissing
        if (tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.DRIPPING_WATER, getX(), getY() + 3.0, getZ(), 2, 1.0, 1.0, 1.0, 0);
        }
        if (tickCount % 12 == 0) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            double bx = getX() + Mth.sin(yaw) * 1.0;
            double bz = getZ() - Mth.cos(yaw) * 1.0;
            level.sendParticles(ParticleTypes.CLOUD, bx, getY() + 4.4, bz, 1, 0.3, 0.1, 0.3, 0.01);
        }
        if (tickCount % 100 == 0) {
            level.playSound(null, this, SoundEvents.IRON_GOLEM_HURT, SoundSource.HOSTILE, 1.0F, 0.4F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        guarding = false;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("lock_master_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, ParticleTypes.CLOUD));
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        clearGates(level, true);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DEATH, SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            clearGates(level, true);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("LockCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("LockRadius", radius);
        output.putBoolean("LockOpened", opened);
        List<Long> all = new ArrayList<>();
        gates.keySet().forEach(p -> all.add(p.asLong()));
        staleGates.forEach(p -> all.add(p.asLong()));
        output.store("LockGates", Codec.LONG.listOf(), all);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("LockCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("LockRadius", 16);
        opened = input.getBooleanOr("LockOpened", false) && phase() == 2;
        gates.clear();
        staleGates.clear();
        input.read("LockGates", Codec.LONG.listOf()).ifPresent(l -> l.forEach(p -> staleGates.add(BlockPos.of(p))));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }
}
