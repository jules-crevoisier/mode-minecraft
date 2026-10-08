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
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import org.jetbrains.annotations.Nullable;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.CalderaCastellan.CHARGE;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.CHOP;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.HEAT;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.LEAP;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.RAMPART;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.REAP;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.REEL;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.ROAR;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.STAGGER;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.STOMP;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.SWEEP;
import static com.brasshaven.generated.MobAnims.CalderaCastellan.VENTS;

/**
 * Le Châtelain de la caldeira (The Castellan of the Caldera), lord of the Caldera Ringwall: a towering lord in basalt
 * plate split by cracks of cooling magma, a crater of obsidian spikes on his helm, a volcano for a right pauldron and
 * a great halberd. He waits in the open court on the summit of the needle in the crater lake.
 * <p>A hard Overworld fight (the ringwall is a colossal structure): 520 health, armour 15, poise 105, hits of 12 to 20.
 * Three phases:
 * <ul>
 *     <li>Phase 1: <b>sweep</b> (the halberd swept across 230 degrees), <b>chop</b> (an overhead cleave down a line),
 *     <b>charge</b> (a lowered-halberd run), <b>leap</b> (he jumps onto the spot marked under you and a lava crack
 *     runs on from the landing), <b>stomp</b> (punishes huggers).</li>
 *     <li>Phase 2 (a roar at 60%): faster, combos, <b>rampart</b> (walls of obsidian burst from the floor to box you
 *     in or cut you off, then he charges or leaps) and <b>reap</b> (a forehand and backhand double sweep). A charge
 *     that hits one of his own walls breaks it and leaves him reeling (and brittle): bait it.</li>
 *     <li>Phase 3 (at 30%): <b>heat</b>, he kneels over the halberd and draws the volcano's heat (invulnerable), then
 *     every 10 seconds or so <b>vents</b>: the floor vents erupt in telegraphed patterns (rings, spirals, a checker,
 *     a hunt). Venting the heat leaves his armour brittle for 3 seconds (+30% damage taken): the punish window.</li>
 * </ul>
 * Every obsidian block he raises is temporary: tracked here, removed when it expires (10-12 s), when a charge breaks
 * it, when the arena empties, when the fight resets, when he dies or is removed, and after a reload (saved positions).
 */
public class CalderaCastellan extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final int VENTS_EVERY = 200;
    private static final int WALL_LIFE = 200;
    private static final int WALL_LIFE_HEATED = 240;
    private static final int MAX_WALL_BLOCKS = 150;
    private static final double LEAP_RANGE = 18.0;
    private static final DustParticleOptions OBSIDIAN = new DustParticleOptions(0x3A2650, 1.4F);
    private static final DustParticleOptions MAGMA = new DustParticleOptions(0xFF7A1A, 1.2F);

    /** Obsidian blocks he raised, with the tick they crumble. Never left behind. */
    private final Map<BlockPos, Integer> walls = new LinkedHashMap<>();
    /** Saved wall positions read back after a reload: removed on the first tick. */
    private final List<BlockPos> staleWalls = new ArrayList<>();
    private final Set<UUID> rammed = new HashSet<>();
    private @Nullable Vec3 centre;
    private @Nullable Vec3 leapFrom;
    private @Nullable Vec3 leapTo;
    /** Planned wall lines of the current rampart (pairs of end points). */
    private final List<Vec3[]> plannedWalls = new ArrayList<>();
    private boolean corridor;
    private boolean heated;
    private int heatGuard;
    private int brittle;
    private int phaseTwoTick = -1;
    private int ventTimer;
    private int ventPattern;

    public CalderaCastellan(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 520.0)
                .add(Attributes.ARMOR, 15.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 18.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.CalderaCastellan.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.RED;
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
        return 0.6F;
    }

    @Override
    protected double preferredRange() {
        return 4.5;
    }

    /** Phase 3: he has drawn the volcano's heat. */
    public boolean isHeated() {
        return heated;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // sweep: the halberd hauled back over his right shoulder (0.9 s, the reach outlined in embers), then swept flat
        // across 230 degrees in front of him
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(18, 4, 14).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 7.4, 115, ParticleTypes.SMALL_FLAME);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 7.5, 115)) {
                        b.strike(level, e, 17.0F, 1.6, 0.3);
                        burn(e, 40);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    for (int a = -115; a <= 115; a += 10) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(5.5));
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.2, p.z, 2, 0.2, 0.2, 0.2, 0.02);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c && b.phase() == 2) {
                        float r = b.getRandom().nextFloat();
                        if (r < (c.heated ? 0.5F : 0.35F)) {
                            b.chain(level, c.heated && r < 0.25F ? "reap" : "chop");
                        }
                    }
                })
                .build());
        // chop: the halberd raised high in both hands (1.0 s, the line it will cleave glows), then brought straight
        // down: a cleave 7 blocks long, a burst of magma where the blade bites
        out.add(BossAttack.of("chop").anim(CHOP).timing(20, 3, 15).range(0, 8.0).cooldown(70).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (double d = 1.5; d <= 7; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(MAGMA, p.x, p.y + 0.15, p.z, 1, 0.15, 0, 0.15, 0);
                        }
                    }
                    if (tick == 8) {
                        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitLine(level, 7.0, 1.3, 20.0F, 1.0);
                    Vec3 tip = b.ahead(6.0);
                    b.addEffect(magmaBurst(tip, 8, 1.8, 10.0F));
                    level.sendParticles(ParticleTypes.EXPLOSION, tip.x, tip.y + 0.3, tip.z, 2, 0.4, 0.1, 0.4, 0);
                    level.sendParticles(ParticleTypes.LAVA, tip.x, tip.y + 0.3, tip.z, 14, 0.8, 0.2, 0.8, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) > 6.0 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "charge");
                    }
                })
                .build());
        // charge: the halberd levelled like a lance (0.8 s, a line of smoke shows the run), then a heavy run for one
        // second: 15 once per target. A charge into one of his own walls breaks it and leaves him reeling
        out.add(BossAttack.of("charge").anim(CHARGE).timing(16, 20, 14).range(6.0, 22.0).cooldown(110).weight(8)
                .start((b, level, t, tick) -> rammed.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 18; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y + 0.2, p.z, 1, 0.15, 0, 0.15, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> b.lunge(0.95, 0.0))
                .active((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.tickCharge(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // leap: a deep crouch while a ring of embers follows the target (0.6 s); the ring locks and turns to flame as he
        // jumps (max 18 blocks), and he lands halberd-first on it at 1.2 s: 20 in 3.5 blocks, then a lava crack runs on
        // 14 blocks from the landing (three cracks in phase 2), flaring 0.6 s after it passes
        out.add(BossAttack.of("leap").anim(LEAP).timing(24, 4, 18).range(7.0, 22.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    leapFrom = null;
                    leapTo = null;
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.tickLeap(level, t, tick);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.land(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // stomp: the right foot raised high (0.7 s, a ring at his feet), stamped: 12 and a shove; in phase 2 a ring of
        // heat rolls out (jump it)
        out.add(BossAttack.of("stomp").anim(STOMP).timing(14, 3, 12).range(0, 4.5).cooldown(60).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, ParticleTypes.SMOKE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.5, 12.0F, 2.2, 0.5);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 9, 0.5, 8.0F, ParticleTypes.FLAME));
                    }
                    level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 0.2, b.getZ(), 16, 1.6, 0.1, 1.6, 0);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // rampart: the left gauntlet raised, magma pouring off it (1.0 s, the lines where walls will rise smoke on the
        // floor), driven into the floor: walls of obsidian three blocks high burst up. Alternately a corridor (two walls
        // flanking the target, open toward him: then he charges down it) or a pen (a wall behind the target and two at
        // its sides: then he leaps on it). Whoever stands on a line is thrown aside (8).
        out.add(BossAttack.of("rampart").anim(RAMPART).phaseTwo().timing(20, 6, 16).range(4.0, 20.0).cooldown(220).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.planWalls(t);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c && tick % 3 == 0) {
                        c.drawPlannedWalls(level);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    level.sendParticles(ParticleTypes.DRIPPING_LAVA, b.getX(), b.getY() + 5.0, b.getZ(), 2, 0.6, 0.3, 0.6, 0);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.raisePlannedWalls(level);
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.BASALT_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (!(b instanceof CalderaCastellan c) || t == null) {
                        return;
                    }
                    double d = b.distanceTo(t);
                    if (c.corridor && d >= 6.0 && b.getRandom().nextFloat() < 0.7F) {
                        b.chain(level, "charge");
                    } else if (!c.corridor && d >= 7.0 && b.getRandom().nextFloat() < 0.6F) {
                        b.chain(level, "leap");
                    }
                })
                .build());
        // reap: the halberd drawn to his right (0.8 s, arc outlined), a forehand sweep, then 0.6 s later the haft is
        // whipped back for a backhand sweep (the second arc is outlined while it comes)
        out.add(BossAttack.of("reap").anim(REAP).phaseTwo().timing(16, 16, 14).range(0, 8.0).cooldown(120).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 7.4, 115, ParticleTypes.FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 7.5, 115)) {
                        b.strike(level, e, 15.0F, 1.2, 0.25);
                        burn(e, 40);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick > 1 && tick < 12 && tick % 3 == 0) {
                        b.telegraphArc(level, 7.4, 115, ParticleTypes.SMALL_FLAME);
                    }
                    if (tick == 12) {
                        for (LivingEntity e : arcVictims(b, level, 7.5, 115)) {
                            b.strike(level, e, 15.0F, 1.6, 0.3);
                            burn(e, 40);
                        }
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.4F);
                        for (int a = -115; a <= 115; a += 10) {
                            Vec3 p = b.position().add(rotate(b.forward(), a).scale(5.5));
                            level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.2, p.z, 2, 0.2, 0.2, 0.2, 0.02);
                        }
                    }
                })
                .build());

        // ---------------------------------------------------------------- never rolled (range 999)
        // reel: his charge broke on his own wall: thrown back, he sags over the haft for 1.7 s, brittle
        out.add(BossAttack.of("reel").anim(REEL).phaseTwo().timing(6, 2, 32).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.brittle = Math.max(c.brittle, 44);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.sendParticles(ParticleTypes.CRIT, b.getX(), b.getY() + 4.0, b.getZ(), 30, 0.6, 0.6, 0.6, 0.3);
                })
                .build());
        // heat (phase 3, once): he drives the halberd into the floor and kneels over it, drawing the volcano's heat
        // (1.5 s, invulnerable, the floor smokes round him), then rises: a ring of heat to jump (12) and bursts round him
        out.add(BossAttack.of("heat").anim(HEAT).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    heatGuard = 52;
                    level.playSound(null, b, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.4, ParticleTypes.LARGE_SMOKE);
                        level.playSound(null, b, SoundEvents.LAVA_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.02F);
                    }
                    level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 0.5, b.getZ(), 3, 3.0, 0.1, 3.0, 0);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.drawHeat(level);
                    }
                })
                .build());
        // vents (phase 3, scheduled): the halberd raised to the sky (1.0 s), then its point driven into the floor: for
        // 2.5 s the floor vents erupt in a pattern (rings, spiral, checker or hunt), each vent warned 1 s by smoke and
        // dripping lava (13 + fire). Venting leaves his armour brittle for 3 s afterwards
        out.add(BossAttack.of("vents").anim(VENTS).phaseTwo().timing(20, 50, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                    level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 5.5 + tick * 0.1, b.getZ(), 3, 0.4, 0.3, 0.4, 0.02);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.erupt(level);
                    }
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.LAVA_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof CalderaCastellan c) {
                        c.brittle = Math.max(c.brittle, 60);
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** One tick of the charge: run on, hit what is in front, break on his own walls, stop on anything else. */
    private void tickCharge(ServerLevel level, int tick) {
        Vec3 f = forward();
        BlockPos[] front = {BlockPos.containing(ahead(1.8).add(0, 0.5, 0)), BlockPos.containing(ahead(1.8).add(0, 1.5, 0))};
        for (BlockPos p : front) {
            if (walls.containsKey(p)) {
                shatterWallsNear(level, p, 3.0);
                setDeltaMovement(0, getDeltaMovement().y, 0);
                chain(level, "reel");
                return;
            }
        }
        boolean blocked = level.getBlockState(front[1]).blocksMotion();
        if (tick < 18 && !blocked) {
            setDeltaMovement(f.x * 0.95, getDeltaMovement().y, f.z * 0.95);
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
        hurtMarked = true;
        for (LivingEntity e : victims(level, ahead(1.6), 2.2)) {
            if (rammed.add(e.getUUID())) {
                strike(level, e, 15.0F, 2.0, 0.5);
                level.playSound(null, this, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 1.5F, 0.5F);
            }
        }
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.3, getZ(), 3, 0.7, 0.1, 0.7, 0.01);
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 0.3, getZ(), 1, 0.5, 0.1, 0.5, 0);
    }

    /** The leap's wind-up: crouch and mark the target (ticks 0-11), then fly on a fixed arc to the mark (12-23). */
    private void tickLeap(ServerLevel level, @Nullable LivingEntity target, int tick) {
        if (tick < 12) {
            if (target != null) {
                leapTo = clampToArena(target.position());
                Vec3 to = leapTo.subtract(position()).multiply(1, 0, 1);
                if (to.length() > LEAP_RANGE) {
                    leapTo = position().add(to.normalize().scale(LEAP_RANGE));
                }
            }
            if (leapTo != null && tick % 2 == 0) {
                telegraphRing(level, leapTo, 3.5, ParticleTypes.SMALL_FLAME);
            }
            return;
        }
        if (leapTo == null) {
            leapTo = ahead(8.0);
        }
        if (tick == 12) {
            leapFrom = position();
            Vec3 to = leapTo.subtract(position());
            snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
            setNoGravity(true);
            level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.7F);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.3, getZ(), 20, 1.0, 0.2, 1.0, 0.05);
        }
        if (tick % 2 == 0) {
            telegraphRing(level, leapTo, 3.5, ParticleTypes.FLAME);
        }
        if (leapFrom != null) {
            double k = (tick - 11) / 12.0;
            double height = 5.0 * 4 * k * (1 - k);
            Vec3 p = leapFrom.lerp(leapTo, k);
            setPos(p.x, leapFrom.y + (leapTo.y - leapFrom.y) * k + height, p.z);
            setDeltaMovement(Vec3.ZERO);
            hurtMarked = true;
        }
    }

    /** The landing: the chop on the mark, then the lava crack(s) run on from it. */
    private void land(ServerLevel level) {
        setNoGravity(false);
        if (leapTo != null) {
            setPos(leapTo.x, leapTo.y, leapTo.z);
        }
        Vec3 c = position();
        hitCircle(level, c, 3.5, 20.0F, 1.4, 0.6);
        for (LivingEntity e : victims(level, c, 3.5)) {
            burn(e, 40);
        }
        LivingEntity target = getTarget();
        Vec3 dir = target != null ? target.position().subtract(c).multiply(1, 0, 1) : forward();
        dir = dir.lengthSqr() < 0.5 ? forward() : dir.normalize();
        addEffect(crack(c, dir, 14, 12.0F));
        if (phase() == 2) {
            addEffect(crack(c, rotate(dir, 28), 12, 12.0F));
            addEffect(crack(c, rotate(dir, -28), 12, 12.0F));
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 4, 1.0, 0.1, 1.0, 0);
        level.sendParticles(ParticleTypes.LAVA, c.x, c.y + 0.3, c.z, 24, 1.6, 0.3, 1.6, 0);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** A point pulled back inside the arena floor (2 blocks inside the edge). */
    private Vec3 clampToArena(Vec3 p) {
        Vec3 c = centre();
        Vec3 to = p.subtract(c).multiply(1, 0, 1);
        double max = 13.0;
        Vec3 flat = to.length() > max ? to.normalize().scale(max) : to;
        return new Vec3(c.x + flat.x, c.y, c.z + flat.z);
    }

    /**
     * A lava crack running from {@code from} along {@code dir}: it spreads a block a tick (magma dust, dripping lava),
     * and every stretch flares 12 ticks after the crack has passed it: {@code damage} + fire, a small lift, once each.
     */
    private static Effect crack(Vec3 from, Vec3 dir, int length, float damage) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            int k = t[0]++;
            for (int d = 2; d <= length; d++) {
                Vec3 p = from.add(dir.scale(d));
                int lit = d - 2;
                if (k >= lit && k < lit + 12 && (k - lit) % 3 == 0) {
                    level.sendParticles(MAGMA, p.x, p.y + 0.1, p.z, 2, 0.25, 0, 0.25, 0);
                    level.sendParticles(ParticleTypes.SMOKE, p.x, p.y + 0.1, p.z, 1, 0.2, 0, 0.2, 0.01);
                }
                if (k == lit + 12) {
                    level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.5, p.z, 8, 0.3, 0.8, 0.3, 0.05);
                    level.sendParticles(ParticleTypes.LAVA, p.x, p.y + 0.3, p.z, 2, 0.2, 0.2, 0.2, 0);
                    if (d % 3 == 0) {
                        level.playSound(null, p.x, p.y, p.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.8F, 0.6F);
                    }
                    for (LivingEntity e : boss.victims(level, p, 1.3)) {
                        if (flatDist(e.position(), p) <= 1.3 && e.getY() - p.y < 1.5 && hit.add(e.getUUID())) {
                            boss.strike(level, e, damage, 0.3, 0.5);
                            burn(e, 60);
                        }
                    }
                }
            }
            return k > length + 12;
        };
    }

    /** A vent: smoke and dripping lava for {@code delay} ticks, then a column of fire: damage, fire, lift. */
    private static Effect magmaBurst(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y + 0.1, pos.z, 2, radius * 0.4, 0, radius * 0.4, 0.01);
                    level.sendParticles(MAGMA, pos.x, pos.y + 0.1, pos.z, 3, radius * 0.45, 0, radius * 0.45, 0);
                }
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.FALLING_LAVA, pos.x, pos.y + 2.5, pos.z, 1, radius * 0.3, 0.2, radius * 0.3, 0);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 1.2, pos.z, 18, radius * 0.35, 1.2, radius * 0.35, 0.04);
            level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 0.5, pos.z, 4, radius * 0.3, 0.3, radius * 0.3, 0);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (flatDist(e.position(), pos) <= radius && e.getY() - pos.y < 3.0) {
                    boss.strike(level, e, damage, 0.2, 0.6);
                    burn(e, 60);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ obsidian walls

    /** Chooses the wall lines of the next rampart around the target: a corridor or a pen, alternately. */
    private void planWalls(@Nullable LivingEntity target) {
        plannedWalls.clear();
        corridor = !corridor;
        Vec3 t = target != null ? clampToArena(target.position()) : ahead(8.0);
        Vec3 dir = t.subtract(position()).multiply(1, 0, 1);
        dir = dir.lengthSqr() < 0.5 ? forward() : dir.normalize();
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        if (corridor) {
            // two walls flanking the target, along his line of charge
            for (int s = -1; s <= 1; s += 2) {
                Vec3 o = t.add(side.scale(2.6 * s));
                plannedWalls.add(new Vec3[] {o.add(dir.scale(-5.5)), o.add(dir.scale(5.5))});
            }
        } else {
            // a pen: a wall behind the target and two at its sides, open toward him
            Vec3 back = t.add(dir.scale(3.0));
            plannedWalls.add(new Vec3[] {back.add(side.scale(-4.5)), back.add(side.scale(4.5))});
            for (int s = -1; s <= 1; s += 2) {
                Vec3 o = t.add(side.scale(3.6 * s));
                plannedWalls.add(new Vec3[] {o.add(dir.scale(-1.5)), o.add(dir.scale(2.5))});
            }
        }
    }

    private void drawPlannedWalls(ServerLevel level) {
        for (Vec3[] w : plannedWalls) {
            for (BlockPos col : columns(w[0], w[1])) {
                level.sendParticles(OBSIDIAN, col.getX() + 0.5, getY() + 0.15, col.getZ() + 0.5, 1, 0.2, 0, 0.2, 0);
                if (getRandom().nextInt(4) == 0) {
                    level.sendParticles(ParticleTypes.SMOKE, col.getX() + 0.5, getY() + 0.2, col.getZ() + 0.5, 1, 0.1, 0.1, 0.1, 0.01);
                }
            }
        }
    }

    /** The block columns (x, z) under a wall line, at the boss's feet level. */
    private List<BlockPos> columns(Vec3 a, Vec3 b) {
        List<BlockPos> out = new ArrayList<>();
        Set<Long> seen = new HashSet<>();
        double len = a.distanceTo(b);
        int y = Mth.floor(getY() + 0.01);
        for (double s = 0; s <= len; s += 0.4) {
            Vec3 p = a.lerp(b, len < 1.0E-3 ? 0 : s / len);
            BlockPos col = new BlockPos(Mth.floor(p.x), y, Mth.floor(p.z));
            if (seen.add(col.asLong())) {
                out.add(col);
            }
        }
        return out;
    }

    private void raisePlannedWalls(ServerLevel level) {
        int life = heated ? WALL_LIFE_HEATED : WALL_LIFE;
        Vec3 c = centre();
        for (Vec3[] w : plannedWalls) {
            for (BlockPos col : columns(w[0], w[1])) {
                if (walls.size() >= MAX_WALL_BLOCKS) {
                    break;
                }
                Vec3 mid = Vec3.atBottomCenterOf(col);
                if (flatDist(mid, c) > 15.0 || flatDist(mid, position()) < 2.5) {
                    continue;
                }
                BlockPos below = col.below();
                if (!level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)) {
                    continue;
                }
                // whoever stands on the line is thrown aside and the column is left open
                AABB cell = new AABB(col.getX(), col.getY(), col.getZ(), col.getX() + 1, col.getY() + 3, col.getZ() + 1);
                List<LivingEntity> inside = level.getEntitiesOfClass(LivingEntity.class, cell, LivingEntity::isAlive);
                if (!inside.isEmpty()) {
                    for (LivingEntity e : victims(level, mid, 1.5)) {
                        if (e.getBoundingBox().intersects(cell)) {
                            strike(level, e, 8.0F, 1.0, 0.7);
                        }
                    }
                    continue;
                }
                for (int dy = 0; dy < 3; dy++) {
                    BlockPos p = col.above(dy);
                    if (!level.getBlockState(p).isAir()) {
                        break;
                    }
                    level.setBlock(p, Blocks.OBSIDIAN.defaultBlockState(), 3);
                    walls.put(p.immutable(), tickCount + life + getRandom().nextInt(20));
                }
                level.sendParticles(ParticleTypes.LAVA, mid.x, mid.y + 0.5, mid.z, 2, 0.3, 0.3, 0.3, 0);
                level.sendParticles(ParticleTypes.LARGE_SMOKE, mid.x, mid.y + 1.5, mid.z, 2, 0.3, 0.6, 0.3, 0.02);
            }
        }
        plannedWalls.clear();
    }

    /** A charge broke on a wall: every wall block within {@code radius} shatters (shards hurt whoever is close). */
    private void shatterWallsNear(ServerLevel level, BlockPos at, double radius) {
        Iterator<Map.Entry<BlockPos, Integer>> it = walls.entrySet().iterator();
        while (it.hasNext()) {
            BlockPos p = it.next().getKey();
            if (p.distSqr(at) <= radius * radius + 9) {
                removeWallBlock(level, p, true);
                it.remove();
            }
        }
        Vec3 c = Vec3.atCenterOf(at);
        hitCircle(level, c, 3.0, 6.0F, 1.0, 0.3);
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y, c.z, 3, 0.6, 0.6, 0.6, 0);
        level.playSound(null, at, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.5F, 0.4F);
        level.playSound(null, at, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private static void removeWallBlock(ServerLevel level, BlockPos p, boolean loud) {
        BlockState s = level.getBlockState(p);
        if (s.is(Blocks.OBSIDIAN)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
            level.sendParticles(OBSIDIAN, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, loud ? 8 : 4, 0.3, 0.3, 0.3, 0.05);
            if (loud) {
                level.sendParticles(ParticleTypes.LAVA, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 1, 0.2, 0.2, 0.2, 0);
            }
        }
    }

    /** Crumbles the walls whose time is up, or all of them. */
    private void clearWalls(ServerLevel level, boolean all) {
        if (walls.isEmpty()) {
            return;
        }
        boolean any = false;
        Iterator<Map.Entry<BlockPos, Integer>> it = walls.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<BlockPos, Integer> en = it.next();
            if (all || tickCount >= en.getValue()) {
                removeWallBlock(level, en.getKey(), false);
                it.remove();
                any = true;
            }
        }
        if (any) {
            level.playSound(null, this, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ phase 3

    /** Phase 3 starts: the heat is drawn, a ring rolls out, bursts round him, and he is faster from now on. */
    private void drawHeat(ServerLevel level) {
        heated = true;
        ventTimer = 70;
        Vec3 c = position();
        addEffect(WayfarerBoss.wave(c, 14, 0.55, 12.0F, ParticleTypes.FLAME));
        for (int i = 0; i < 10; i++) {
            double a = Math.PI * 2 * i / 10;
            addEffect(magmaBurst(c.add(Math.cos(a) * 6.0, 0, Math.sin(a) * 6.0), 14, 1.5, 12.0F));
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("caldera_castellan_heat"), 0.15,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 2, c.z, 6, 1.2, 1.0, 1.2, 0);
        level.sendParticles(ParticleTypes.LAVA, c.x, c.y + 2.5, c.z, 40, 1.2, 1.2, 1.2, 0);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    /** The vents erupt: one of four patterns round the arena centre, all warned for a second. */
    private void erupt(ServerLevel level) {
        Vec3 c = centre();
        int pattern = ventPattern++ % 4;
        switch (pattern) {
            case 0 -> {        // rings: three rings, then the three between them
                double[][] waves = {{2.5, 7.5, 12.5}, {5.0, 10.0, 14.5}};
                for (int w = 0; w < 2; w++) {
                    for (double r : waves[w]) {
                        int n = Math.max(6, (int) (Math.PI * 2 * r / 2.2));
                        for (int i = 0; i < n; i++) {
                            double a = Math.PI * 2 * i / n;
                            addEffect(delayed(w * 24, magmaBurst(c.add(Math.cos(a) * r, 0, Math.sin(a) * r), 20, 1.4, 13.0F)));
                        }
                    }
                }
            }
            case 1 -> {        // spiral: three arms unwinding outward
                double base = getRandom().nextDouble() * Math.PI * 2;
                for (int arm = 0; arm < 3; arm++) {
                    int step = 0;
                    for (double r = 2.0; r <= 14.5; r += 1.6, step++) {
                        double a = base + arm * Math.PI * 2 / 3 + r * 0.32;
                        addEffect(delayed(step * 3, magmaBurst(c.add(Math.cos(a) * r, 0, Math.sin(a) * r), 20, 1.6, 13.0F)));
                    }
                }
            }
            case 2 -> {        // checker: 4-block squares, the dark ones then the light ones
                for (int gx = -4; gx < 4; gx++) {
                    for (int gz = -4; gz < 4; gz++) {
                        Vec3 p = c.add(gx * 4 + 2, 0, gz * 4 + 2);
                        if (flatDist(p, c) > 15.0) {
                            continue;
                        }
                        int w = Math.floorMod(gx + gz, 2);
                        addEffect(delayed(w * 26, magmaBurst(p, 20, 2.2, 13.0F)));
                    }
                }
            }
            default -> {       // hunt: four volleys a little apart, a vent under every player and strays
                for (int v = 0; v < 4; v++) {
                    for (LivingEntity e : victims(level, c, 24.0)) {
                        addEffect(delayed(v * 12, ventOn(e)));
                    }
                    for (int i = 0; i < scaledCount(2); i++) {
                        double a = getRandom().nextDouble() * Math.PI * 2;
                        double r = 3 + getRandom().nextDouble() * 11;
                        addEffect(delayed(v * 12, magmaBurst(c.add(Math.cos(a) * r, 0, Math.sin(a) * r), 20, 1.6, 13.0F)));
                    }
                }
            }
        }
    }

    /** A vent opening where {@code target} stands when it starts. */
    private static Effect ventOn(LivingEntity target) {
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (!target.isAlive()) {
                    return true;
                }
                inner[0] = magmaBurst(new Vec3(target.getX(), boss.getY(), target.getZ()), 20, 1.6, 13.0F);
            }
            return inner[0].tick(boss, level);
        };
    }

    // ------------------------------------------------------------------ shared helpers

    /** Living targets inside the arc that {@link #hitArc} covers (so a hit can also burn). */
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

    private static double flatDist(Vec3 a, Vec3 b) {
        return a.multiply(1, 0, 1).distanceTo(b.multiply(1, 0, 1));
    }

    private static void burn(LivingEntity e, int ticks) {
        e.setRemainingFireTicks(Math.max(e.getRemainingFireTicks(), ticks));
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
        if (heatGuard > 0) {
            level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 2.5, getZ(), 4, 0.6, 1.0, 0.6, 0);
            return false;
        }
        if (brittle > 0) {
            amount *= 1.3F;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleWalls.isEmpty()) {        // walls saved by an unload: they never outlive the fight
            for (BlockPos p : staleWalls) {
                removeWallBlock(level, p, false);
            }
            staleWalls.clear();
        }
        if (heatGuard > 0) {
            heatGuard--;
        }
        if (brittle > 0) {
            brittle--;
            if (tickCount % 4 == 0) {
                level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 3.0, getZ(), 2, 0.6, 1.0, 0.6, 0.01);
            }
        }
        BossAttack current = currentAttack();
        if (isNoGravity() && (current == null || !current.name.equals("leap"))) {
            setNoGravity(false);            // a leap cut short by a stagger or the roar
        }
        // the arena emptied (death, flight) or the fight was reset: no wall stays up
        if (!walls.isEmpty()) {
            boolean anyone = com.brasshaven.util.NearbyPlayers.any(level, new AABB(BlockPos.containing(centre())).inflate(28, 16, 28),
                    p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
            clearWalls(level, !anyone);
        }
        if (phase() == 1) {
            if (heated) {                   // the fight was reset: the heat is gone
                heated = false;
                phaseTwoTick = -1;
                brittle = 0;
                clearWalls(level, true);
            }
        } else if (phaseTwoTick >= 0 && tickCount - phaseTwoTick > 50 && current == null && !isStaggered()
                && getTarget() != null && getTarget().isAlive()) {
            if (!heated && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "heat");
            } else if (heated && --ventTimer <= 0) {
                ventTimer = (int) Math.round(VENTS_EVERY * cooldownScale());
                chain(level, "vents");
            }
        }
        // ambience: smoke from the volcano pauldron, embers off the cracks, the crater on his helm
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        if (tickCount % (heated ? 2 : 4) == 0) {
            double px = getX() + Mth.cos(yaw) * 1.2;
            double pz = getZ() + Mth.sin(yaw) * 1.2;
            level.sendParticles(heated ? ParticleTypes.LARGE_SMOKE : ParticleTypes.SMOKE, px, getY() + 4.9, pz, 1, 0.1, 0.1, 0.1, 0.02);
        }
        if (tickCount % (heated ? 4 : 10) == 0) {
            level.sendParticles(ParticleTypes.DRIPPING_LAVA, getX(), getY() + 2.5, getZ(), 1, 0.7, 1.2, 0.7, 0);
        }
        if (heated && tickCount % 6 == 0) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 5.6, getZ(), 1, 0.2, 0.1, 0.2, 0.01);
        }
        if (tickCount % 80 == 0) {
            level.playSound(null, this, SoundEvents.LAVA_AMBIENT, SoundSource.HOSTILE, 1.0F, 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        phaseTwoTick = tickCount;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("caldera_castellan_wrath"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 4.5, getZ(), 40, 1.0, 1.5, 1.0, 0);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        clearWalls(level, true);
        setNoGravity(false);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2.5, getZ(), 5, 1.0, 1.5, 1.0, 0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 2.5, getZ(), 60, 1.2, 2.0, 1.2, 0.05);
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 3, getZ(), 30, 1.0, 1.5, 1.0, 0);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.BASALT_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            clearWalls(level, true);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        List<Long> all = new ArrayList<>();
        walls.keySet().forEach(p -> all.add(p.asLong()));
        staleWalls.forEach(p -> all.add(p.asLong()));
        output.store("CastellanWalls", Codec.LONG.listOf(), all);
        output.putBoolean("CastellanHeated", heated);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        input.read("CastellanWalls", Codec.LONG.listOf()).ifPresent(l -> l.forEach(p -> staleWalls.add(BlockPos.of(p))));
        heated = input.getBooleanOr("CastellanHeated", false) && phase() == 2;
        if (phase() == 2) {
            phaseTwoTick = -100;            // reloaded mid-fight: phase 3 and the vents keep their schedule
        }
    }
}
