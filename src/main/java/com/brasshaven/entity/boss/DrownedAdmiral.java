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
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.DrownedAdmiral.BOARDING;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.BROADSIDE;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.CANNON;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.CHARGE;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.HOOK;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.ROAR;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.SCUTTLE;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.SLASH;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.STAGGER;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.STAMP;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.THRUST;
import static com.brasshaven.generated.MobAnims.DrownedAdmiral.VALVES;

/**
 * L'Amiral noyé (The Drowned Admiral), the last commander of the Leviathan Dreadnought: a 5.9-block naval officer in a
 * waterlogged greatcoat, a brass diving helmet under a bicorne, a boarding cutlass in his right hand and a deck cannon
 * for a left forearm. He holds the boiler hall in the stern of his broken ship (four giant boilers, the funnel uptakes
 * open to the sky).
 * <p>A deliberately hard fight: 620 health, armour 12, poise 115, hits of 4 to 20. Three phases:
 * <ul>
 *     <li>Phase 1: <b>cutlass slash</b> (forehand and backhand), <b>lunging thrust</b>, the <b>deck cannon</b> (a red aim
 *     laser that follows you a little slower than you can strafe, locks, then a shell that bursts where it meets you or
 *     the wall: splash damage), the <b>boiler valves</b> (lanes of scalding steam vent from the boilers' fireboxes toward
 *     the players and linger), the <b>boarding hook</b> (a grapnel on a chain drags whoever it catches to his feet) and
 *     a <b>lead-boot stamp</b> (anti-hug).</li>
 *     <li>Phase 2 (a roar at 65%): faster, combos, the <b>broadside</b> (three aimed shots), the <b>boarding combo</b>
 *     (two cuts and a leaping chop) and the <b>ramming charge</b> (he reels for 2 s if he rams a boiler or a wall).</li>
 *     <li>Phase 3 (at 30%): he <b>scuttles</b> the ship (invulnerable): seawater floods the hall knee-deep for 18 s,
 *     slowing you while he wades at full speed, and 2-4 <b>drowned marines</b> (more with more players) board.
 *     Every 12 s after the water drains he scuttles again; the steam lanes scald harder over the flood.</li>
 * </ul>
 * The water is the only block he places, and it is temporary: drained when the flood ends, when the fight resets or
 * the arena empties, when he dies or is removed, and on the first tick after a reload.
 */
public class DrownedAdmiral extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SLASH_RANGE = 5.5;
    private static final double SLASH_HALF = 65;
    private static final double LANE_HALF = 1.5;
    private static final double LANE_HEIGHT = 3.5;
    private static final double SPLASH_R = 3.5;
    private static final int FLOOD_MAX_R = 20;
    private static final int FLOOD_LIFE = 360;
    private static final int SCUTTLE_EVERY = 240;
    private static final DustParticleOptions LASER = new DustParticleOptions(0xFF3020, 0.7F);
    private static final DustParticleOptions LASER_LOCK = new DustParticleOptions(0xFFE060, 1.0F);
    private static final DustParticleOptions STEAM = new DustParticleOptions(0xEDEFF0, 1.6F);
    private static final DustParticleOptions RUST = new DustParticleOptions(0x8C5A3A, 1.2F);
    private static final DustParticleOptions BRINE = new DustParticleOptions(0x3FA58E, 1.4F);
    private static final DustParticleOptions CHAIN = new DustParticleOptions(0x6E6E72, 0.9F);

    private @Nullable Vec3 centre;
    private int radius = 18;
    /** Phase 3 has started (he scuttled the ship once). */
    private boolean scuttled;
    private int guard;
    private int roarUntil = -1;
    private int scuttleTimer;
    private int reelUntil = -1;
    /** Water he let in is standing in the hall. */
    private boolean flooded;
    private int floodUntil;
    private int floodY;
    private int floodR;
    private final Set<Long> preWater = new HashSet<>();
    private boolean staleFlood;
    /** Boiler fireboxes found round the arena (the steam valves), else fixed spots round the centre. */
    private final List<Vec3> valves = new ArrayList<>();
    private final List<Vec3> laneFrom = new ArrayList<>();
    private final List<Vec3> laneDir = new ArrayList<>();
    private final List<LivingEntity> laneAim = new ArrayList<>();
    /** The cannon's aim: the point the laser rests on, and whether it is locked. */
    private @Nullable Vec3 aim;
    private boolean aimLocked;
    private @Nullable Vec3 leapTo;
    private @Nullable Vec3 hookAt;
    private boolean hooked;
    private final Set<UUID> struck = new HashSet<>();

    public DrownedAdmiral(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        setPathfindingMalus(PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 620.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5)
                .add(Attributes.WATER_MOVEMENT_EFFICIENCY, 1.0);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.DrownedAdmiral.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.BLUE;
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

    public boolean isScuttled() {
        return scuttled;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    /** A drowned man in a diving helmet: he never needs air. */
    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    /** He wades through his flood instead of bobbing up in it. */
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
        valves.clear();
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Usable floor radius: the boiler hall is 40 x 31, never more than the seal says. */
    private double reach() {
        return Math.min(20.0, radius + 2.0);
    }

    /**
     * The steam valves: the lit fireboxes of the boilers round the hall (the lower blast furnace of each, on the floor),
     * one spot each just in front of it; with no boiler in reach (a spawn egg, a command), four spots round the centre.
     */
    private List<Vec3> valves(ServerLevel level) {
        if (valves.isEmpty()) {
            BlockPos c = BlockPos.containing(centre());
            int r = (int) Math.ceil(reach()) + 2;
            BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    p.set(c.getX() + dx, c.getY(), c.getZ() + dz);
                    if (level.getBlockState(p).is(Blocks.BLAST_FURNACE) && valves.size() < 6) {
                        Vec3 at = Vec3.atBottomCenterOf(p);
                        Vec3 in = centre().subtract(at).multiply(1, 0, 1);
                        valves.add(in.lengthSqr() > 1.0E-3 ? at.add(in.normalize().scale(1.2)) : at);
                    }
                }
            }
            if (valves.isEmpty()) {
                Vec3 cc = centre();
                double ax = Math.min(14, reach() - 3);
                for (int sx = -1; sx <= 1; sx += 2) {
                    for (int sz = -1; sz <= 1; sz += 2) {
                        valves.add(cc.add(sx * ax, 0, sz * 8));
                    }
                }
            }
        }
        return valves;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // cutlass slash: drawn back over his right shoulder (0.7 s, the arc chalked in rust), a forehand cut, then the
        // blade carried round toward the target and a backhand cut half a second later
        out.add(BossAttack.of("slash").anim(SLASH).timing(14, 18, 14).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SLASH_RANGE, SLASH_HALF, RUST);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.cut(level, 14.0F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof DrownedAdmiral a)) {
                        return;
                    }
                    if (tick == 3 && t != null) {
                        a.turnToward(t, 30.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, SLASH_RANGE, SLASH_HALF, RUST);
                    }
                    if (tick == 10) {
                        a.cut(level, 14.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 5.0 ? "stamp" : "hook");
                    }
                })
                .build());
        // lunging thrust: feet set, the blade drawn back at the hip point first (0.8 s, a line of rust 9 long), then a
        // lunge through you
        out.add(BossAttack.of("thrust").anim(THRUST).timing(16, 8, 14).range(3.5, 12.0).cooldown(80).weight(9)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 9.0; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(RUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.rush(level, a.flooded ? 1.15 : 0.9, 16.0F, false);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // deck cannon: the arm raised level (1.4 s); a red aim laser follows the target a little slower than a strafe
        // for 1 s, then locks (yellow, a click) for 0.4 s; the shell bursts where it meets the target or a wall
        out.add(BossAttack.of("cannon").anim(CANNON).timing(28, 6, 16).range(6.0, 32.0).cooldown(120).weight(9)
                .start((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.startAim(t);
                    }
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.aimStep(level, t, tick >= 20);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.fire(level, 18.0F);
                    }
                })
                .build());
        // boiler valves: the cutlass raised as a signal (1.2 s); lanes of steam are marked from the boilers' fireboxes
        // toward the players (they follow for 0.7 s, then lock); at the chop the valves burst: 13 and a shove down the
        // lane, then the steam lingers 2.5 s (4 every half second, slowed)
        out.add(BossAttack.of("valves").anim(VALVES).timing(24, 50, 14).range(0, 32.0).cooldown(240).weight(8).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.planLanes(level, t);
                    }
                    level.playSound(null, b, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0F, 1.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.laneStep(level, tick);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof DrownedAdmiral a)) {
                        return;
                    }
                    for (int i = 0; i < a.laneFrom.size(); i++) {
                        b.addEffect(a.steamLane(level, a.laneFrom.get(i), a.laneDir.get(i), 50, a.flooded ? 16.0F : 13.0F));
                    }
                    level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .build());
        // boarding hook: the grapnel whirled under the cannon arm (0.9 s; a grey chain line to the target, a ring on it,
        // locked for the last 6 ticks), flung along the line; whoever it catches is hurt and hauled to his feet
        out.add(BossAttack.of("hook").anim(HOOK).timing(18, 14, 14).range(6.0, 22.0).cooldown(160).weight(8)
                .start((b, level, t, tick) -> {
                    hookAt = null;
                    hooked = false;
                    level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.hookAim(level, t, tick);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        b.addEffect(a.grapnel(a.hookAt != null ? a.hookAt : b.ahead(14), 22.0));
                        level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a && a.hooked && t != null && b.distanceTo(t) < 6.0
                            && b.getRandom().nextFloat() < (b.phase() == 2 ? 0.7F : 0.4F)) {
                        b.chain(level, "slash");
                    }
                })
                .build());
        // lead-boot stamp: a diving boot lifted (0.6 s, a ring at his feet), stamped down. Phase 2: a ring rolls out
        out.add(BossAttack.of("stamp").anim(STAMP).timing(12, 3, 12).range(0, 4.5).cooldown(70).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, RUST);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.0, 12.0F, 1.4, 0.35);
                    for (LivingEntity e : b.victims(level, b.position(), 4.5)) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), b);
                    }
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 9, 0.5, 8.0F, ParticleTypes.SPLASH));
                    }
                    level.sendParticles(ParticleTypes.SPLASH, b.getX(), b.getY() + 0.3, b.getZ(), 40, 2.0, 0.2, 2.0, 0.2);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.4F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // broadside: three aimed shots (1.2 s for the first aim, then 0.6 s of tracking and 0.4 s locked before each)
        out.add(BossAttack.of("broadside").anim(BROADSIDE).phaseTwo().timing(24, 44, 16).range(8.0, 32.0).cooldown(260)
                .weight(7)
                .start((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.startAim(t);
                    }
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.aimStep(level, t, tick >= 16);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.fire(level, 15.0F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof DrownedAdmiral a) || tick == 0) {
                        return;
                    }
                    int k = tick % 20;
                    if (k == 0 && tick <= 40) {
                        a.fire(level, 15.0F);
                    } else if (tick < 40) {
                        if (k == 1) {
                            a.aimLocked = false;
                        }
                        if (t != null && k < 12) {
                            a.turnToward(t, 12.0F);
                        }
                        a.aimStep(level, t, k >= 12);
                    }
                })
                .build());
        // boarding combo: forehand cut at the impact, backhand at active 10, then he leaps at the locked spot and chops
        // down at active 24 (18 in r 3 and a ring to jump)
        out.add(BossAttack.of("boarding").anim(BOARDING).phaseTwo().timing(16, 30, 16).range(0, 9.0).cooldown(160).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SLASH_RANGE, SLASH_HALF, RUST);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.cut(level, 15.0F);
                        a.leapTo = null;
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof DrownedAdmiral a)) {
                        return;
                    }
                    if (tick == 3 && t != null) {
                        a.turnToward(t, 30.0F);
                    }
                    if (tick == 10) {
                        a.cut(level, 15.0F);
                    }
                    if (tick == 12) {
                        a.leapTo = a.clampToArena(t != null ? t.position() : b.ahead(4));
                        level.playSound(null, b, SoundEvents.DROWNED_SHOOT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    if (tick >= 12 && tick < 24 && a.leapTo != null && tick % 2 == 0) {
                        b.telegraphRing(level, a.leapTo, 3.0, LASER_LOCK);
                    }
                    if (tick == 16 && a.leapTo != null) {
                        Vec3 to = a.leapTo.subtract(b.position()).multiply(1, 0, 1);
                        double d = Math.min(8.0, to.length());
                        Vec3 v = to.lengthSqr() > 1.0E-3 ? to.normalize().scale(d / 8.0) : Vec3.ZERO;
                        b.setDeltaMovement(v.x, 0.55, v.z);
                        b.hurtMarked = true;
                    }
                    if (tick == 24) {
                        b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                        Vec3 at = a.leapTo != null && a.leapTo.distanceTo(b.position()) < 3.0 ? a.leapTo : b.ahead(1.5);
                        b.hitCircle(level, at, 3.0, 18.0F, 1.0, 0.4);
                        b.addEffect(WayfarerBoss.wave(at, 7, 0.45, 8.0F, ParticleTypes.SPLASH));
                        level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 0.3, at.z, 50, 1.4, 0.2, 1.4, 0.2);
                        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .build());
        // ramming charge: helmet lowered, the cannon braced like a ram (0.8 s, a line 14 long); he charges 12 ticks
        // (faster in the flood). If he rams a boiler or a wall he reels for 2 s (+30% damage taken)
        out.add(BossAttack.of("charge").anim(CHARGE).phaseTwo().timing(16, 12, 14).range(7.0, 22.0).cooldown(180).weight(7)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 14.0; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(BRINE, p.x, p.y + 0.15, p.z, 1, 0.3, 0, 0.3, 0);
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0F, 0.8F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.rush(level, a.flooded ? 1.35 : 1.0, 15.0F, tick >= 2);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // reeling after ramming a wall: never rolled, chained by the charge
        out.add(BossAttack.of("reel").anim(STAGGER).phaseTwo().timing(10, 20, 10).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.reelUntil = a.tickCount + 44;
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.sendParticles(ParticleTypes.CRIT, b.getX(), b.getY() + 5.2, b.getZ(), 6, 0.6, 0.2, 0.6, 0.1);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // scuttle: he kneels and drives the cutlass into the deck (1.5 s, invulnerable; the floor bubbles, the hull
        // groans); the sea cocks open: the hall floods knee-deep, a ring of water rolls out, the marines board
        out.add(BossAttack.of("scuttle").anim(SCUTTLE).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 52;
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof DrownedAdmiral a)) {
                        return;
                    }
                    Vec3 c = a.centre();
                    double r = a.reach();
                    level.sendParticles(ParticleTypes.BUBBLE_POP, c.x, c.y + 0.1, c.z, 14, r * 0.5, 0, r * 0.4, 0);
                    level.sendParticles(ParticleTypes.FALLING_WATER, c.x, c.y + 8, c.z, 10, r * 0.5, 2, r * 0.4, 0);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.4, BRINE);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DrownedAdmiral a) {
                        a.scuttle(level);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void cut(ServerLevel level, float damage) {
        hitArc(level, SLASH_RANGE, SLASH_HALF, damage, 1.2);
        for (double a = -SLASH_HALF; a <= SLASH_HALF; a += 10) {
            Vec3 p = position().add(rotate(forward(), a).scale(SLASH_RANGE - 1.2));
            level.sendParticles(RUST, p.x, p.y + 1.6, p.z, 2, 0.2, 0.3, 0.2, 0.02);
            level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 1.4, p.z, 2, 0.2, 0.2, 0.2, 0.05);
        }
        Vec3 c = ahead(3.0);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.6, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    /** One tick of a rush (thrust or charge): forward at {@code speed}, hits once per target; a charge reels on walls. */
    private void rush(ServerLevel level, double speed, float damage, boolean reelOnWall) {
        Vec3 f = forward().scale(speed);
        setDeltaMovement(f.x, getDeltaMovement().y, f.z);
        hurtMarked = true;
        level.sendParticles(flooded ? ParticleTypes.SPLASH : ParticleTypes.POOF, getX(), getY() + 0.3, getZ(), 6, 0.6, 0.1, 0.6, 0.05);
        if (tickCount % 3 == 0) {
            level.playSound(null, this, flooded ? SoundEvents.PLAYER_SPLASH_HIGH_SPEED : SoundEvents.ANVIL_LAND,
                    SoundSource.HOSTILE, 1.2F, 0.6F);
        }
        for (LivingEntity e : victims(level, position(), 3.0)) {
            if (flatDist(e.position(), position().add(forward())) <= 2.0 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, damage, 1.4, 0.35);
            }
        }
        if (horizontalCollision) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            if (reelOnWall) {
                Vec3 p = ahead(1.2);
                level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 2, p.z, 2, 0.4, 0.6, 0.4, 0);
                level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 2, p.z, 20, 0.6, 1.0, 0.6, 0.05);
                level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
                level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
                chain(level, "reel");
            }
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
        double max = Math.max(3.0, reach() - 2.0);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    // ---- the cannon

    /** The muzzle of the cannon arm, raised level at his left side. */
    private Vec3 muzzle() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(f.scale(2.2)).add(left.scale(-1.1)).add(0, 3.3, 0);
    }

    private void startAim(@Nullable LivingEntity t) {
        aimLocked = false;
        aim = t != null ? t.position().add(0, 1.0, 0) : ahead(10).add(0, 1.0, 0);
    }

    /**
     * One tick of the aim laser: while free, the aim point slides toward the target's chest at 0.33 b/t (a sprint or a
     * strafe outruns it); once locked it stays. The beam is drawn from the muzzle through the aim point to the wall.
     */
    private void aimStep(ServerLevel level, @Nullable LivingEntity t, boolean locked) {
        if (aim == null) {
            startAim(t);
        }
        if (locked && !aimLocked) {
            aimLocked = true;
            level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.0F, 1.8F);
        }
        if (!aimLocked && t != null && t.isAlive()) {
            Vec3 goal = t.position().add(0, 1.0, 0);
            Vec3 to = goal.subtract(aim);
            double step = 0.33;
            aim = to.length() <= step ? goal : aim.add(to.normalize().scale(step));
        }
        Vec3 from = muzzle();
        Vec3 end = shotEnd(level, from, aim);
        double len = from.distanceTo(end);
        DustParticleOptions dust = aimLocked ? LASER_LOCK : LASER;
        for (double d = 0.8; d < len; d += aimLocked ? 0.5 : 0.8) {
            Vec3 p = from.lerp(end, d / Math.max(0.01, len));
            level.sendParticles(dust, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        if (aimLocked) {
            telegraphRing(level, new Vec3(end.x, floorAt(end), end.z), SPLASH_R, LASER_LOCK);
        }
    }

    /** Where a shot from {@code from} toward {@code at} stops: the first wall, up to 34 blocks. */
    private Vec3 shotEnd(ServerLevel level, Vec3 from, Vec3 at) {
        Vec3 dir = at.subtract(from);
        if (dir.lengthSqr() < 1.0E-4) {
            dir = forward();
        }
        Vec3 far = from.add(dir.normalize().scale(34));
        BlockHitResult hit = level.clip(new ClipContext(from, far, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? far : hit.getLocation();
    }

    private double floorAt(Vec3 p) {
        return Math.abs(p.y - centre().y) < 3.0 ? centre().y : p.y - 1.0;
    }

    /** The shot: the shell flies along the aim and bursts on the first creature it meets or on the wall. */
    private void fire(ServerLevel level, float damage) {
        Vec3 from = muzzle();
        Vec3 end = shotEnd(level, from, aim != null ? aim : ahead(10).add(0, 1, 0));
        Vec3 dir = end.subtract(from);
        double len = dir.length();
        Vec3 burst = end;
        LivingEntity direct = null;
        if (len > 1.0E-3) {
            Vec3 n = dir.normalize();
            for (double d = 0.5; d < len; d += 0.5) {
                Vec3 p = from.add(n.scale(d));
                for (LivingEntity e : victims(level, p, 1.5)) {
                    if (e.getBoundingBox().inflate(0.3).contains(p)) {
                        direct = e;
                        break;
                    }
                }
                if (direct != null) {
                    burst = p;
                    break;
                }
                if (((int) (d * 2)) % 3 == 0) {
                    level.sendParticles(ParticleTypes.SMOKE, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.01);
                }
            }
        }
        if (direct != null) {
            strike(level, direct, 4.0F, 0.0, 0.0);
        }
        Vec3 c = burst;
        for (LivingEntity e : victims(level, c, SPLASH_R + 1)) {
            double d = e.position().add(0, e.getBbHeight() * 0.5, 0).distanceTo(c);
            if (d <= SPLASH_R + e.getBbWidth() / 2) {
                float k = (float) (1.0 - 0.5 * Math.min(1.0, d / SPLASH_R));
                if (e.hurtServer(level, damageSources().mobAttack(this), damage * k)) {
                    Vec3 away = e.position().subtract(c).multiply(1, 0, 1);
                    away = away.lengthSqr() < 1.0E-4 ? forward() : away.normalize();
                    e.push(away.x * 1.1 * k, 0.45, away.z * 1.1 * k);
                    e.hurtMarked = true;
                }
            }
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y, c.z, 3, 0.8, 0.5, 0.8, 0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, c.x, c.y, c.z, 20, 1.0, 0.6, 1.0, 0.03);
        level.sendParticles(flooded ? ParticleTypes.SPLASH : ParticleTypes.FLAME, c.x, c.y, c.z, 30, 1.2, 0.4, 1.2, 0.1);
        Vec3 m = from;
        level.sendParticles(ParticleTypes.CLOUD, m.x, m.y, m.z, 10, 0.3, 0.3, 0.3, 0.08);
        level.sendParticles(ParticleTypes.FLAME, m.x, m.y, m.z, 6, 0.2, 0.2, 0.2, 0.05);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F, 0.9F);
        aimLocked = false;
    }

    // ---- the boiler valves

    /** Picks the venting valves (2, 3 in phase 2, 4 once scuttled), each assigned a player to aim at. */
    private void planLanes(ServerLevel level, @Nullable LivingEntity target) {
        laneFrom.clear();
        laneDir.clear();
        laneAim.clear();
        int want = scuttled ? 4 : phase() == 2 ? 3 : 2;
        List<LivingEntity> players = new ArrayList<>();
        if (target != null) {
            players.add(target);
        }
        for (LivingEntity e : victims(level, centre(), reach() + 4)) {
            if (e instanceof Player && e != target) {
                players.add(e);
            }
        }
        List<Vec3> pool = new ArrayList<>(valves(level));
        java.util.Collections.shuffle(pool, new java.util.Random(getRandom().nextLong()));
        for (int i = 0; i < Math.min(want, pool.size()); i++) {
            laneFrom.add(pool.get(i));
            LivingEntity who = players.isEmpty() ? null : players.get(i % players.size());
            laneAim.add(who);
            laneDir.add(dirTo(pool.get(i), who != null ? who.position() : centre()));
        }
    }

    private static Vec3 dirTo(Vec3 from, Vec3 to) {
        Vec3 d = to.subtract(from).multiply(1, 0, 1);
        return d.lengthSqr() < 1.0E-3 ? new Vec3(0, 0, 1) : d.normalize();
    }

    /** Wind-up tick of the valves: the lanes follow their players until tick 14, then lock; hissing at each valve. */
    private void laneStep(ServerLevel level, int tick) {
        for (int i = 0; i < laneFrom.size(); i++) {
            Vec3 from = laneFrom.get(i);
            LivingEntity who = laneAim.get(i);
            if (tick <= 14 && who != null && who.isAlive()) {
                laneDir.set(i, dirTo(from, who.position()));
            }
            if (tick % 2 == 0) {
                drawLane(level, from, laneDir.get(i), tick > 14);
            }
            level.sendParticles(ParticleTypes.CLOUD, from.x, from.y + 1.5, from.z, 2, 0.2, 0.3, 0.2, 0.03);
        }
        if (tick % 6 == 0) {
            for (Vec3 v : laneFrom) {
                level.playSound(null, v.x, v.y, v.z, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 1.2F + tick * 0.02F);
            }
        }
    }

    /** Length of a lane from {@code from} along {@code dir}: until a wall at chest height, up to 30 blocks. */
    private double laneLength(ServerLevel level, Vec3 from, Vec3 dir) {
        Vec3 a = from.add(0, 1.2, 0);
        BlockHitResult hit = level.clip(new ClipContext(a, a.add(dir.scale(30)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? 30 : Math.max(2.0, hit.getLocation().distanceTo(a));
    }

    private void drawLane(ServerLevel level, Vec3 from, Vec3 dir, boolean locked) {
        double len = laneLength(level, from, dir);
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        for (double d = 0.5; d <= len; d += 1.2) {
            for (int s = -1; s <= 1; s += 2) {
                Vec3 p = from.add(dir.scale(d)).add(side.scale(LANE_HALF * s));
                level.sendParticles(locked ? STEAM : RUST, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /**
     * A lane of scalding steam: bursts at once (damage and a shove down the lane, too tall to jump), then lingers for
     * {@code life} ticks (4 every half second and Slowness II to whoever stays in it).
     */
    private Effect steamLane(ServerLevel level0, Vec3 from, Vec3 dir, int life, float damage) {
        int[] t = {0};
        double len = laneLength(level0, from, dir);
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, level) -> {
            int k = t[0]++;
            boolean burst = k == 0;
            if (k % 2 == 0 || burst) {
                for (double d = 0.5; d <= len; d += burst ? 0.7 : 1.4) {
                    Vec3 p = from.add(dir.scale(d));
                    level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 1.0, p.z, burst ? 3 : 1, 0.6, 0.8, 0.6, burst ? 0.12 : 0.02);
                    if (burst || d % 3 < 1.4) {
                        level.sendParticles(STEAM, p.x, p.y + 2.2, p.z, 1, 0.5, 0.6, 0.5, 0);
                    }
                }
            }
            if (k % 10 == 0) {
                Vec3 m = from.add(dir.scale(len * 0.5));
                level.playSound(null, m.x, m.y, m.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, burst ? 2.5F : 1.2F, 0.6F);
            }
            if (burst || k % 10 == 0) {
                for (LivingEntity e : boss.victims(level, from.add(dir.scale(len * 0.5)), len * 0.5 + 2)) {
                    Vec3 rel = e.position().subtract(from).multiply(1, 0, 1);
                    double along = rel.dot(dir);
                    if (along < -0.5 || along > len + 0.5 || Math.abs(rel.dot(side)) > LANE_HALF + e.getBbWidth() / 2
                            || e.getY() - from.y > LANE_HEIGHT || e.getY() - from.y < -2) {
                        continue;
                    }
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), burst ? damage : 4.0F)) {
                        if (burst) {
                            e.push(dir.x * 1.0, 0.3, dir.z * 1.0);
                            e.hurtMarked = true;
                        }
                    }
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 1), boss);
                }
            }
            return k >= life;
        };
    }

    // ---- the boarding hook

    private Vec3 hand() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(f.scale(1.2)).add(left.scale(-1.4)).add(0, 2.4, 0);
    }

    private void hookAim(ServerLevel level, @Nullable LivingEntity t, int tick) {
        if (tick < 12 && t != null) {
            hookAt = t.position();
        }
        if (hookAt == null) {
            hookAt = ahead(14);
        }
        if (tick % 2 == 0) {
            Vec3 from = hand();
            Vec3 to = hookAt.add(0, 1.0, 0);
            double len = from.distanceTo(to);
            for (double d = 1.0; d < len; d += 1.0) {
                Vec3 p = from.lerp(to, d / Math.max(0.01, len));
                level.sendParticles(CHAIN, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
            telegraphRing(level, hookAt, 1.4, tick >= 12 ? LASER_LOCK : CHAIN);
        }
        if (tick % 5 == 0) {
            level.playSound(null, this, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 0.8F + tick * 0.02F);
        }
    }

    /**
     * The grapnel: flies from his hand toward {@code at} (and on past it) at 2 blocks a tick up to {@code range}; the
     * first creature it touches takes 8, is slowed, and is hauled to 2.5 blocks in front of him over 8 ticks.
     */
    private Effect grapnel(Vec3 at, double range) {
        Vec3 from = hand();
        Vec3 dir = at.add(0, 1.0, 0).subtract(from);
        Vec3 n = dir.lengthSqr() < 1.0E-4 ? forward() : dir.normalize();
        int[] t = {0};
        double[] dist = {0};
        LivingEntity[] caught = {null};
        int[] pull = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (caught[0] == null) {
                if (k > 14) {
                    return true;
                }
                double d0 = dist[0];
                dist[0] = Math.min(range, d0 + 2.0);
                for (double d = d0; d <= dist[0]; d += 0.5) {
                    Vec3 p = from.add(n.scale(d));
                    if (!level.getBlockState(BlockPos.containing(p)).getCollisionShape(level, BlockPos.containing(p)).isEmpty()) {
                        level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 8, 0.2, 0.2, 0.2, 0.1);
                        level.playSound(null, p.x, p.y, p.z, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 0.6F);
                        return true;
                    }
                    for (LivingEntity e : boss.victims(level, p, 1.6)) {
                        if (e.getBoundingBox().inflate(0.5).contains(p)) {
                            caught[0] = e;
                            break;
                        }
                    }
                    if (caught[0] != null) {
                        LivingEntity e = caught[0];
                        e.hurtServer(level, boss.damageSources().mobAttack(boss), 8.0F);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 2), boss);
                        level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                        if (boss instanceof DrownedAdmiral a) {
                            a.hooked = true;
                        }
                        break;
                    }
                }
                Vec3 head = from.add(n.scale(dist[0]));
                drawChain(level, boss instanceof DrownedAdmiral a ? a.hand() : from, head);
                level.sendParticles(ParticleTypes.CRIT, head.x, head.y, head.z, 2, 0.1, 0.1, 0.1, 0);
                return caught[0] == null && dist[0] >= range;
            }
            LivingEntity e = caught[0];
            if (!e.isAlive() || pull[0]++ >= 8) {
                return true;
            }
            Vec3 goal = boss.position().add(boss.forward().scale(2.5));
            Vec3 to = goal.subtract(e.position()).multiply(1, 0, 1);
            double left = to.length();
            Vec3 v = left > 0.4 ? to.normalize().scale(Math.min(1.6, left / Math.max(1, 8 - pull[0] + 1) + 0.4)) : Vec3.ZERO;
            e.setDeltaMovement(v.x, 0.12, v.z);
            e.hurtMarked = true;
            drawChain(level, boss instanceof DrownedAdmiral a ? a.hand() : from, e.position().add(0, 1.0, 0));
            if (pull[0] % 3 == 0) {
                level.playSound(null, boss, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
            return false;
        };
    }

    private static void drawChain(ServerLevel level, Vec3 a, Vec3 b) {
        double len = a.distanceTo(b);
        for (double d = 0; d < len; d += 0.6) {
            Vec3 p = a.lerp(b, d / Math.max(0.01, len));
            level.sendParticles(CHAIN, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
    }

    // ---- phase 3: scuttling

    private void scuttle(ServerLevel level) {
        boolean first = !scuttled;
        scuttled = true;
        if (first) {
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("drowned_admiral_scuttled"), 0.12,
                        AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
            }
        }
        floodHall(level);
        floodUntil = tickCount + FLOOD_LIFE;
        addEffect(WayfarerBoss.wave(position(), 12, 0.55, 12.0F, ParticleTypes.SPLASH));
        boardMarines(level);
        Vec3 h = centre();
        level.sendParticles(ParticleTypes.SPLASH, h.x, h.y + 0.5, h.z, 300, reach() * 0.6, 0.2, reach() * 0.5, 0.2);
        level.playSound(null, this, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.AMBIENT_UNDERWATER_ENTER, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.CONDUIT_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private int minions(ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(centre())).inflate(radius + 12, 12, radius + 12),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    /** Marines alive at most: two solo, three with two players, four with three or more. */
    private int marineCap() {
        return Math.min(4, 1 + Math.max(1, scaledPlayers()));
    }

    /** Drowned marines climb aboard round the hall: vanilla drowned in marine helmets with cutlasses or tridents. */
    private void boardMarines(ServerLevel level) {
        int n = Math.max(0, marineCap() - minions(level));
        double base = getRandom().nextDouble() * Math.PI * 2;
        for (int i = 0; i < n; i++) {
            double a = base + Math.PI * 2 * i / Math.max(1, n);
            Vec3 p = clampToArena(centre().add(Math.cos(a) * 9, 0, Math.sin(a) * 9));
            Mob m = net.minecraft.world.entity.EntityTypes.DROWNED.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (m == null) {
                continue;
            }
            m.snapTo(p.x, p.y, p.z, getYRot(), 0);
            m.setItemSlot(EquipmentSlot.HEAD, new ItemStack(Items.CHAINMAIL_HELMET));
            m.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(i % 2 == 0 ? Items.IRON_SWORD : Items.TRIDENT));
            for (EquipmentSlot s : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.MAINHAND}) {
                m.setDropChance(s, 0.0F);
            }
            m.addTag(MINION_TAG);
            m.setTarget(getTarget());
            level.addFreshEntity(m);
            level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 0.5, p.z, 40, 0.4, 0.8, 0.4, 0.2);
            level.sendParticles(BRINE, p.x, p.y + 1, p.z, 15, 0.4, 0.8, 0.4, 0.02);
        }
        if (n > 0) {
            level.playSound(null, this, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
        }
    }

    /**
     * Fills every open floor cell of the hall within {@link #FLOOD_MAX_R} of the centre with a water source, one block
     * deep. Water that already stood nearby (the sea outside the hull) is remembered so the drain never touches it.
     */
    private void floodHall(ServerLevel level) {
        if (flooded) {
            return;
        }
        BlockPos c = BlockPos.containing(centre());
        floodY = c.getY();
        floodR = Math.min(FLOOD_MAX_R, Math.max(6, radius + 2));
        preWater.clear();
        int box = floodR + 8;
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
        int rr = (floodR + 4) * (floodR + 4);
        for (int dx = -floodR; dx <= floodR; dx++) {
            for (int dz = -floodR; dz <= floodR; dz++) {
                if (dx * dx + dz * dz > rr) {
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

    /** Drains the flood: every water block in the flood's box that was not there before is removed. */
    private void drain(ServerLevel level) {
        if (!flooded) {
            return;
        }
        flooded = false;
        BlockPos c = BlockPos.containing(centre());
        int box = floodR + 8;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -box; dx <= box; dx++) {
            for (int dz = -box; dz <= box; dz++) {
                for (int y = floodY - 2; y <= floodY + 1; y++) {
                    p.set(c.getX() + dx, y, c.getZ() + dz);
                    if (!preWater.contains(p.asLong()) && level.isLoaded(p) && level.getBlockState(p).is(Blocks.WATER)) {
                        level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                        if (getRandom().nextInt(14) == 0) {
                            level.sendParticles(ParticleTypes.BUBBLE_POP, p.getX() + 0.5, p.getY() + 0.2, p.getZ() + 0.5, 3, 0.3, 0.1, 0.3, 0.02);
                        }
                    }
                }
            }
        }
        preWater.clear();
        level.playSound(null, c, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
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

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.1);
            return false;
        }
        if (tickCount < reelUntil) {
            amount *= 1.3F;
        }
        return super.hurtServer(level, source, amount);
    }

    private void discardMarines(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 20, 16, radius + 20),
                m -> m.entityTags().contains(MINION_TAG))) {
            level.sendParticles(ParticleTypes.SPLASH, m.getX(), m.getY() + 1, m.getZ(), 15, 0.3, 0.6, 0.3, 0.1);
            m.discard();
        }
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleFlood) {                       // a flood saved by an unload never outlives it
            staleFlood = false;
            flooded = true;
            drain(level);
        }
        if (guard > 0) {
            guard--;
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 16, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (flooded && (!anyone || tickCount >= floodUntil)) {
            drain(level);                       // the flood ends, or the arena emptied (death, flight)
            scuttleTimer = (int) Math.round(SCUTTLE_EVERY * cooldownScale());
        }
        if (phase() == 1 && (scuttled || flooded)) {     // the fight was reset: the sea goes out, the marines leave
            scuttled = false;
            roarUntil = -1;
            reelUntil = -1;
            drain(level);
            discardMarines(level);
        }
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!scuttled && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "scuttle");
            } else if (scuttled && !flooded && --scuttleTimer <= 0) {
                chain(level, "scuttle");
            }
        }
        if (flooded && fighting && tickCount % 20 == 0) {    // the sea drags at whoever wades in it
            for (LivingEntity e : victims(level, centre(), floodR + 4.0)) {
                if (e instanceof Player && e.isInWater()) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 1), this);
                }
            }
        }
        if (flooded) {
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null && tickCount % 20 == 0) {
                speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("drowned_admiral_wading"), 0.25,
                        AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
            }
            if (tickCount % 3 == 0 && getDeltaMovement().horizontalDistanceSqr() > 0.01) {
                level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.9, getZ(), 6, 0.8, 0.1, 0.8, 0.1);
            }
            if (floodUntil - tickCount == 60) {   // 3 s warning: the water starts to fall
                level.playSound(null, BlockPos.containing(centre()), SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT,
                        SoundSource.HOSTILE, 3.0F, 0.7F);
            }
        } else if (tickCount % 20 == 0) {
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("drowned_admiral_wading"));
            }
        }
        // ambience: drips off his coat, a wisp of smoke from the muzzle, bubbles in the helmet
        if (tickCount % 8 == 0) {
            level.sendParticles(ParticleTypes.FALLING_WATER, getX(), getY() + 3.0, getZ(), 2, 0.9, 1.2, 0.9, 0);
        }
        if (tickCount % 6 == 0) {
            Vec3 m = muzzle();
            level.sendParticles(ParticleTypes.SMOKE, m.x, m.y - 1.6, m.z, 1, 0.05, 0.05, 0.05, 0.01);
        }
        if (tickCount % 10 == 0) {
            level.sendParticles(ParticleTypes.BUBBLE_POP, getX(), getY() + 5.0, getZ(), 2, 0.3, 0.3, 0.3, 0);
        }
        if (tickCount % 120 == 0) {
            level.playSound(null, this, SoundEvents.DROWNED_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.4F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("drowned_admiral_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, ParticleTypes.SPLASH));
        level.playSound(null, this, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.1);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        drain(level);
        discardMarines(level);
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 2.5, getZ(), 150, 1.2, 2.0, 1.2, 0.3);
        level.sendParticles(ParticleTypes.BUBBLE_POP, getX(), getY() + 3, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.5F, 0.4F);
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
            output.putLong("AdmiralCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("AdmiralRadius", radius);
        output.putBoolean("AdmiralScuttled", scuttled);
        output.putBoolean("AdmiralFlood", flooded || staleFlood);
        output.putInt("AdmiralFloodY", floodY);
        output.putInt("AdmiralFloodR", floodR);
        output.store("AdmiralPreWater", Codec.LONG.listOf(), List.copyOf(preWater));
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("AdmiralCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("AdmiralRadius", 18);
        scuttled = input.getBooleanOr("AdmiralScuttled", false) && phase() == 2;
        staleFlood = input.getBooleanOr("AdmiralFlood", false);
        floodY = input.getIntOr("AdmiralFloodY", 0);
        floodR = input.getIntOr("AdmiralFloodR", FLOOD_MAX_R);
        preWater.clear();
        input.read("AdmiralPreWater", Codec.LONG.listOf()).ifPresent(preWater::addAll);
        flooded = false;
        valves.clear();
    }
}
