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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
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
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.AbyssalArchitect.CHAINSWING;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.COMPASS;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.DESCEND;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.ECLIPSE;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.FLAIL;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.KEYSTONE;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.MASONRY;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.PLUMMET;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.ROAR;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.SCRIBE;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.STAGGER;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.SWINGDROP;
import static com.brasshaven.generated.MobAnims.AbyssalArchitect.UNMOOR;

/**
 * L'Architecte de l'abîme (The Abyssal Architect), the builder-priest of the Inverted Spire: a gaunt, four-armed
 * priest of 5.7 blocks in a slate cassock, a limestone mask with three soul-blue slits under a pinnacle mitre, three
 * chains rising from his back. He hangs under the point of the spire over the lake and drops onto the island when
 * the fight begins. Upper right hand: a plumb-bob flail; upper left: a compass-blade; lower hands: a set-square and a
 * soul lantern.
 * <p>A hard fight: 600 health, armour 12, poise 110, hits of 7 to 17. Three phases:
 * <ul>
 *     <li>Phase 1: <b>compass slash</b> (fast, 13), <b>flail</b> (a huge circle of the plumb-bob out to 8.5: hug him,
 *     the inner 2.2 blocks are safe), <b>plummet</b> (the bob hurled 11 blocks down a marked line, then reeled back
 *     along it), <b>masonry</b> (stones fall from the vault on marks that follow every player, leaving rubble for 8 s)
 *     and <b>swing drop</b> (he swings across the arena on a chain and lands on a marked ring).</li>
 *     <li>Phase 2 (a roar at 65%): faster, combos, <b>scribe</b> (one turn round his planted compass: an outer ring,
 *     then the inner disc), <b>eclipse</b> (the lantern is snuffed: everyone is blinded for 3 s and he vanishes; his
 *     echoing footsteps and soul-blue footprints show where he walks before the slash) and <b>keystone</b> (a
 *     checkerboard of the vault falls in two halves).</li>
 *     <li>Phase 3 (at 30%): he <b>unmoors</b> the island (invulnerable): from then on the floor tiles crack in a
 *     marked pattern (rings, spokes, checkers, spiral, halves), crumble into the lake for 5 s and rise again; and
 *     every 15 s he leaps onto the ceiling chains for the <b>chain swing</b>: he circles the arena hanging from them and
 *     dives three times on marks that follow the players.</li>
 * </ul>
 * Every block he removes or places is temporary: rubble and crumbled tiles are recorded with their original state
 * and restored when they expire, when the arena empties, when the fight resets, when he dies or is removed, and after
 * a reload.
 */
public class AbyssalArchitect extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double COMPASS_RANGE = 4.8;
    private static final double COMPASS_HALF = 65;
    private static final double FLAIL_INNER = 2.2;
    private static final double FLAIL_OUTER = 8.5;
    private static final double PLUMB_REACH = 11.0;
    private static final double SCRIBE_SPLIT = 4.5;
    private static final double SCRIBE_OUTER = 9.0;
    private static final int CHAINSWING_EVERY = 300;
    private static final int FLOOR_MAX_R = 16;
    private static final int FLOOR_DEPTH = 4;
    private static final int CRACK_WARN = 40;
    private static final int HOLE_LIFE = 100;
    private static final int FLOOR_PAUSE = 140;
    private static final int RUBBLE_LIFE = 160;
    private static final int KEY_CELL = 4;
    private static final DustParticleOptions SOUL_DUST = new DustParticleOptions(0x60E2F6, 1.3F);
    private static final DustParticleOptions CHALK = new DustParticleOptions(0xD6D2C4, 1.2F);
    private static final DustParticleOptions CHAIN = new DustParticleOptions(0x5A5A66, 1.0F);
    private static final DustParticleOptions INK = new DustParticleOptions(0x1A1A26, 2.0F);
    private static final BlockParticleOption CRUMBS = new BlockParticleOption(ParticleTypes.BLOCK,
            Blocks.DEEPSLATE_BRICKS.defaultBlockState());
    private static final BlockParticleOption DUST_FALL = new BlockParticleOption(ParticleTypes.FALLING_DUST,
            Blocks.TUFF.defaultBlockState());

    /** A block he changed: its original state and the ticks left before it comes back. */
    private static final class Temp {
        final BlockState original;
        int life;

        Temp(BlockState original, int life) {
            this.original = original;
            this.life = life;
        }
    }

    private record SavedTemp(long pos, BlockState state, int life) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("state").forGetter(SavedTemp::state),
                Codec.INT.fieldOf("life").forGetter(SavedTemp::life)).apply(i, SavedTemp::new));
    }

    /** Arena centre (feet level) and radius, from the seal. */
    private @Nullable Vec3 centre;
    private int radius = 15;
    /** He has not made his entrance yet (hanging from the chains, dropping when the fight starts). */
    private boolean introPending = true;
    /** Phase 3 has begun (the island is unmoored). */
    private boolean unmoored;
    private int unmoorGuard;
    private int roarUntil = -1;
    private int chainTimer;
    private int emptyTicks;
    /** Changed blocks, by packed position, in the order they were changed. */
    private final Map<Long, Temp> temps = new LinkedHashMap<>();
    /** Blocks saved by an unload: restored on the first tick. */
    private final List<SavedTemp> staleTemps = new ArrayList<>();
    /** The floor cycle of phase 3: 0 waiting, 1 tiles cracking (marked), 2 crumbled. */
    private int floorState;
    private int floorTimer;
    private final List<BlockPos> cracked = new ArrayList<>();
    // move state
    private final List<Vec3> marks = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable Vec3 moveFrom;
    private @Nullable Vec3 moveTo;
    private @Nullable Vec3 plumbAt;
    private double orbitAngle;
    private boolean landed;
    private int keyPhase;
    private int keyOffX;
    private int keyOffZ;

    public AbyssalArchitect(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
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
        return MobAnims.AbyssalArchitect.TICKS;
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

    /** Phase 3 counts as a third stage of the fight (the base class knows only two). */
    public boolean isUnmoored() {
        return unmoored;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = Vec3.atBottomCenterOf(blockPosition());
        }
        return centre;
    }

    /** Free air above the arena centre (blocks), at most 14: the spire's point hangs 12 above the island. */
    private int headroom(ServerLevel level) {
        BlockPos c = BlockPos.containing(centre());
        for (int h = 1; h <= 14; h++) {
            if (!level.getBlockState(c.above(h)).isAir()) {
                return h;
            }
        }
        return 14;
    }

    /** Where the chains hang from: the spire's point over the centre (or the ceiling, 8 to 14 up). */
    private Vec3 anchor(ServerLevel level) {
        return centre().add(0, Math.max(8, headroom(level)), 0);
    }

    /** Height of the circle he swings on, under the anchor. */
    private double orbitHeight(ServerLevel level) {
        return Mth.clamp(headroom(level) - HEIGHT - 0.5, 3.0, 6.5);
    }

    private double floorR() {
        return Math.min(FLOOR_MAX_R, Math.max(6, radius));
    }

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(3.0, Math.min(radius, FLOOR_MAX_R) - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    private Vec3 randomSpot() {
        double a = getRandom().nextDouble() * Math.PI * 2;
        double r = 2 + getRandom().nextDouble() * Math.max(3, Math.min(radius, FLOOR_MAX_R) - 3);
        return centre().add(Math.cos(a) * r, 0, Math.sin(a) * r);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // compass slash: the compass-blade drawn up over his left shoulder (0.6 s, the arc chalked on the floor), then
        // slashed down across his front
        out.add(BossAttack.of("compass").anim(COMPASS).timing(12, 4, 12).range(0, 5.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, COMPASS_RANGE, COMPASS_HALF, CHALK);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 1.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, COMPASS_RANGE, COMPASS_HALF)) {
                        b.strike(level, e, 13.0F, 0.9, 0.2);
                    }
                    sweepParticles(b, level, COMPASS_RANGE - 1.0, COMPASS_HALF, ParticleTypes.CRIT);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.7F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, b.distanceTo(t) < 7.0 ? "flail" : "plummet");
                    }
                })
                .build());
        // flail: the plumb-bob whirled overhead (0.9 s; the outer ring in soul light, the safe inner ring in chalk),
        // then swept round him in a huge circle out to 8.5 blocks. Hug him: the inner 2.2 blocks are safe
        out.add(BossAttack.of("flail").anim(FLAIL).timing(18, 6, 14).range(0, 9.0).cooldown(70).weight(10).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), FLAIL_OUTER, SOUL_DUST);
                        b.telegraphRing(level, b.position(), FLAIL_INNER, CHALK);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 2.5F, 0.5F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), FLAIL_OUTER + 1)) {
                        double d = flatDist(e.position(), b.position());
                        if (d >= FLAIL_INNER && d <= FLAIL_OUTER + e.getBbWidth() / 2 && Math.abs(e.getY() - b.getY()) < 3.0) {
                            b.strike(level, e, 15.0F, 1.4, 0.3);
                        }
                    }
                    for (int i = 0; i < 36; i++) {
                        double a = Math.PI * 2 * i / 36;
                        level.sendParticles(ParticleTypes.CRIT, b.getX() + Math.cos(a) * 6.5, b.getY() + 1.3,
                                b.getZ() + Math.sin(a) * 6.5, 2, 0.3, 0.2, 0.3, 0.05);
                    }
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 4.5 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "compass");
                    }
                })
                .build());
        // plummet: the plumb-bob raised high behind him (1.0 s; a chalk line 11 blocks long and a soul ring where it
        // will land, following the target), then hurled down the line: 17 and pinned in the ring; 0.4 s later the
        // chain is reeled back along the line: 9 and dragged toward him
        out.add(BossAttack.of("plummet").anim(PLUMMET).timing(20, 14, 14).range(4.0, 16.0).cooldown(110).weight(9)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= PLUMB_REACH; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(CHALK, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                        b.telegraphRing(level, b.ahead(PLUMB_REACH), 2.6, SOUL_DUST);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.plumbAt = b.ahead(PLUMB_REACH);
                        a.crash(level, a.plumbAt, 2.6, 17.0F, true);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 8 && b instanceof AbyssalArchitect a) {
                        a.reel(level);
                    }
                })
                .build());
        // masonry: plumb and compass lifted to the vault (1.1 s, dust trickling over the players), then snapped
        // down: stones fall on marks that follow every player for half a second then lock (plus strays): 15 and a
        // pile of rubble for 8 s. Phase 2: a second volley a second later
        out.add(BossAttack.of("masonry").anim(MASONRY).timing(22, 34, 14).range(0, 30.0).cooldown(200).weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.AMBIENT_CAVE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    if (tick % 4 == 0 && b instanceof AbyssalArchitect a) {
                        for (LivingEntity e : b.victims(level, a.centre(), a.radius + 6.0)) {
                            if (e instanceof Player) {
                                level.sendParticles(DUST_FALL, e.getX(), e.getY() + 7, e.getZ(), 4, 0.8, 0.5, 0.8, 0);
                            }
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof AbyssalArchitect a)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.DEEPSLATE_BRICKS_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    int volleys = b.phase() == 2 ? 2 : 1;
                    List<LivingEntity> targets = b.victims(level, a.centre(), a.radius + 6.0);
                    for (int v = 0; v < volleys; v++) {
                        for (LivingEntity e : targets) {
                            if (e instanceof Player) {
                                b.addEffect(delayed(v * 20, a.stoneOn(e, 26)));
                            }
                        }
                        for (int i = 0; i < b.scaledCount(b.phase() == 2 ? 4 : 3); i++) {
                            b.addEffect(delayed(v * 20 + i * 2, a.fallingStone(a.randomSpot(), 26, true)));
                        }
                    }
                })
                .build());
        // swing drop: crouched, his hands up on a chain (0.9 s; a ring follows the target for 0.6 s, then locks), then
        // flung across the arena on it: he lands on the ring compass first: 16 within 3, and a ring of shock (jump it)
        out.add(BossAttack.of("swingdrop").anim(SWINGDROP).timing(18, 12, 16).range(7.0, 26.0).cooldown(140).weight(8)
                .start((b, level, t, tick) -> marks.clear())
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof AbyssalArchitect a)) {
                        return;
                    }
                    if (tick < 12 && t != null) {
                        a.moveTo = a.clampToArena(t.position(), 2.0);
                    }
                    if (a.moveTo != null && tick % 2 == 0) {
                        b.telegraphRing(level, a.moveTo, 3.0, tick >= 12 ? CHALK : SOUL_DUST);
                    }
                    if (tick % 3 == 0) {
                        a.chainLine(level, b.position().add(0, 5, 0), a.anchor(level));
                    }
                    if (tick == 12) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.moveFrom = b.position();
                        if (a.moveTo == null) {
                            a.moveTo = a.clampToArena(b.ahead(8.0), 2.0);
                        }
                        b.setNoGravity(true);
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_FALL, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.swingStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    b.setNoGravity(false);
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 5.0 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "compass");
                    }
                })
                .build());
        // the entrance: never rolled; bossTick chains it once the fight starts. He hangs limp from the chains under
        // the spire's point (1.5 s), then lets go and drops onto the island: 14 within 3.5 where he lands and a ring of
        // shock (jump it)
        out.add(BossAttack.of("descend").anim(DESCEND).timing(30, 30, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.hangUp(level);
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 3.0F, 0.4F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof AbyssalArchitect a) || a.moveFrom == null) {
                        return;
                    }
                    b.setPos(a.moveFrom);
                    b.setDeltaMovement(Vec3.ZERO);
                    if (tick % 2 == 0) {
                        a.chainLine(level, b.position().add(0, HEIGHT - 0.6, 0), a.anchor(level));
                        b.telegraphRing(level, a.centre(), 3.5, SOUL_DUST);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.setNoGravity(false);
                    b.setDeltaMovement(0, -0.6, 0);
                    b.hurtMarked = true;
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    if (b instanceof AbyssalArchitect a) {
                        a.landed = false;
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a && !a.landed && (tick > 1 && b.onGround() || tick == 29)) {
                        a.landed = true;
                        a.slam(level, b.position(), 3.5, 14.0F, 9.0, 8.0F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // scribe: the compass's needle planted at his feet (0.8 s; the outer ring in soul light, the split in chalk),
        // then one turn round it: the blade leg sweeps the outer ring (4.5 to 9 blocks: 14) and is drawn in 0.7 s later
        // across the inner disc (14). Stand outside, or step in after the first cut
        out.add(BossAttack.of("scribe").anim(SCRIBE).phaseTwo().timing(16, 20, 14).range(0, 9.0).cooldown(160).weight(9)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), SCRIBE_OUTER, SOUL_DUST);
                        b.telegraphRing(level, b.position(), SCRIBE_SPLIT, CHALK);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.5F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), SCRIBE_OUTER + 1)) {
                        double d = flatDist(e.position(), b.position());
                        if (d >= SCRIBE_SPLIT && d <= SCRIBE_OUTER + e.getBbWidth() / 2 && Math.abs(e.getY() - b.getY()) < 3.0) {
                            b.strike(level, e, 14.0F, 1.0, 0.25);
                        }
                    }
                    for (int i = 0; i < 40; i++) {
                        double a = Math.PI * 2 * i / 40;
                        level.sendParticles(ParticleTypes.CRIT, b.getX() + Math.cos(a) * 7, b.getY() + 0.8,
                                b.getZ() + Math.sin(a) * 7, 1, 0.4, 0.1, 0.4, 0.05);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 14 && tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), SCRIBE_SPLIT, SOUL_DUST);
                        b.telegraphRing(level, b.position(), SCRIBE_SPLIT * 0.5, SOUL_DUST);
                    }
                    if (tick == 14) {
                        b.hitCircle(level, b.position(), SCRIBE_SPLIT, 14.0F, 1.4, 0.4);
                        sweepParticles(b, level, 2.5, 180, ParticleTypes.CRIT);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.9F);
                    }
                })
                .build());
        // eclipse: the soul lantern raised high (1.0 s; darkness gathers in a closing ring), then snuffed: everyone in
        // the arena is blinded for 3 s and he vanishes. He stalks behind his target: every step echoes and leaves a
        // soul-blue footprint; at 1.5 s the compass-blade snicks open (its arc shown), and 0.5 s later he slashes
        out.add(BossAttack.of("eclipse").anim(ECLIPSE).phaseTwo().timing(20, 48, 14).range(0, 20.0).cooldown(320).weight(6)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof AbyssalArchitect a)) {
                        return;
                    }
                    if (tick % 2 == 0) {
                        double r = 1.0 + (a.radius + 4.0) * (1.0 - tick / 20.0);
                        b.telegraphRing(level, a.centre(), r, INK);
                    }
                    if (tick == 0 || tick == 10) {
                        level.playSound(null, b, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 3.0F, 0.7F);
                    }
                    level.sendParticles(SOUL_DUST, b.getX(), b.getY() + 6.0, b.getZ(), 2, 0.3, 0.3, 0.3, 0.01);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.snuff(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.stalkStep(level, t, tick);
                    }
                })
                .end((b, level, t, tick) -> b.setInvisible(false))
                .build());
        // keystone: all four hands raised to the vault (1.0 s): half of a checkerboard of 4-block squares is marked
        // with falling dust; 1.2 s after the impact those squares fall (14) and the other half is marked; 1.2 s later
        // the other half falls
        out.add(BossAttack.of("keystone").anim(KEYSTONE).phaseTwo().timing(20, 60, 14).range(0, 30.0).cooldown(260).weight(6)
                .track(false)
                .start((b, level, t, tick) -> {
                    keyOffX = getRandom().nextInt(KEY_CELL);
                    keyOffZ = getRandom().nextInt(KEY_CELL);
                    keyPhase = getRandom().nextInt(2);
                    level.playSound(null, b, SoundEvents.AMBIENT_CAVE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof AbyssalArchitect a) {
                        a.drawKeystone(level, a.keyPhase);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof AbyssalArchitect a)) {
                        return;
                    }
                    if (tick < 24 && tick % 3 == 0) {
                        a.drawKeystone(level, a.keyPhase);
                    } else if (tick == 24) {
                        a.dropKeystone(level, a.keyPhase);
                    } else if (tick > 24 && tick < 48 && tick % 3 == 0) {
                        a.drawKeystone(level, 1 - a.keyPhase);
                    } else if (tick == 48) {
                        a.dropKeystone(level, 1 - a.keyPhase);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // unmoor: the plumb-bob raised in both upper hands (1.5 s, invulnerable, the chains rattling), then driven
        // into the floor: a ring of shock (12, jump it) and the island begins to break up
        out.add(BossAttack.of("unmoor").anim(UNMOOR).phaseTwo().timing(30, 10, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    unmoorGuard = 52;
                    level.playSound(null, b, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 12.0 - tick * 0.3, CHALK);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F + tick * 0.02F);
                    }
                    level.sendParticles(DUST_FALL, b.getX(), b.getY() + 9, b.getZ(), 4, 4.0, 0.5, 4.0, 0);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.callUnmoor(level);
                    }
                })
                .build());
        // chain swing: he crouches (1.2 s) and leaps up onto the ceiling chains; hanging from them he circles the
        // arena for 4.5 s and dives three times on soul rings that follow a player for 0.7 s, then lock: 16 within 3.2
        // and a ring of shock each. After the third dive he stays crouched (the punish window)
        out.add(BossAttack.of("chainswing").anim(CHAINSWING).phaseTwo().timing(24, 100, 18).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    moveFrom = b.position();
                    Vec3 off = b.position().subtract(centre());
                    orbitAngle = Math.atan2(off.z, off.x);
                    level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.climbStep(level, tick);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 3.0F, 0.4F))
                .active((b, level, t, tick) -> {
                    if (b instanceof AbyssalArchitect a) {
                        a.orbitStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> b.setNoGravity(false))
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

    private static void sweepParticles(WayfarerBoss b, ServerLevel level, double r, double halfAngle, ParticleOptions p) {
        for (double a = -halfAngle; a <= halfAngle; a += 10) {
            Vec3 q = b.position().add(rotate(b.forward(), a).scale(r));
            level.sendParticles(p, q.x, q.y + 1.2, q.z, 3, 0.2, 0.3, 0.2, 0.05);
        }
        Vec3 c = b.ahead(r * 0.6);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
    }

    /** A chain drawn in particles between two points. */
    private void chainLine(ServerLevel level, Vec3 from, Vec3 to) {
        double len = from.distanceTo(to);
        for (double d = 0; d < len; d += 0.6) {
            Vec3 p = from.lerp(to, d / Math.max(0.01, len));
            level.sendParticles(CHAIN, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** The plumb-bob (or a stone) crashes down at {@code at}: damage in a circle, crumbs, a pin of slowness. */
    private void crash(ServerLevel level, Vec3 at, double r, float damage, boolean pin) {
        for (LivingEntity e : victims(level, at, r + 1)) {
            if (flatDist(e.position(), at) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                strike(level, e, damage, 0.3, 0.3);
                if (pin) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 2), this);
                }
            }
        }
        level.sendParticles(CRUMBS, at.x, at.y + 0.3, at.z, 40, r * 0.4, 0.3, r * 0.4, 0.15);
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 1, 0, 0, 0, 0);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    /** The plummet's chain reeled back along its line: 9 once and a drag toward him. */
    private void reel(ServerLevel level) {
        if (plumbAt == null) {
            return;
        }
        Vec3 from = position();
        Vec3 dir = plumbAt.subtract(from).multiply(1, 0, 1);
        double len = dir.length();
        if (len < 0.1) {
            return;
        }
        dir = dir.normalize();
        for (LivingEntity e : victims(level, from, len + 1)) {
            Vec3 rel = e.position().subtract(from).multiply(1, 0, 1);
            double along = rel.dot(dir);
            double side = rel.subtract(dir.scale(along)).length();
            if (along >= 1.0 && along <= len + 1 && side <= 1.3 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                if (e.hurtServer(level, damageSources().mobAttack(this), 9.0F)) {
                    e.push(-dir.x * 0.9, 0.2, -dir.z * 0.9);
                    e.hurtMarked = true;
                }
            }
        }
        for (double d = 1; d <= len; d += 0.7) {
            Vec3 p = from.add(dir.scale(d));
            level.sendParticles(CRUMBS, p.x, p.y + 0.2, p.z, 2, 0.2, 0.05, 0.2, 0.05);
        }
        level.playSound(null, this, SoundEvents.CHAIN_FALL, SoundSource.HOSTILE, 2.5F, 0.7F);
    }

    /** A landing: damage in a circle and a ring of shock to jump. */
    private void slam(ServerLevel level, Vec3 at, double r, float damage, double waveR, float waveDamage) {
        hitCircle(level, at, r, damage, 1.1, 0.4);
        addEffect(WayfarerBoss.wave(at, waveR, 0.5, waveDamage, CRUMBS));
        level.sendParticles(CRUMBS, at.x, at.y + 0.3, at.z, 60, r * 0.5, 0.3, r * 0.5, 0.2);
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.6, 0.1, 0.6, 0);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /**
     * A stone falling from the vault on {@code pos}: a chalk ring and dust trickling down a shrinking column for
     * {@code warn} ticks, then 15 within 2.2 and (with {@code rubble}) a pile of rubble.
     */
    private Effect fallingStone(Vec3 pos, int warn, boolean rubble) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, 2.2, warn - k <= 8 ? SOUL_DUST : CHALK);
                    double h = 1.0 + 9.0 * (1.0 - (double) k / warn);
                    level.sendParticles(DUST_FALL, pos.x, pos.y + h, pos.z, 3, 0.4, 0.2, 0.4, 0);
                    level.sendParticles(CRUMBS, pos.x, pos.y + h, pos.z, 1, 0.3, 0.2, 0.3, 0);
                }
                return false;
            }
            if (boss instanceof AbyssalArchitect a) {
                a.crash(level, pos, 2.2, 15.0F, false);
                if (rubble) {
                    a.placeRubble(level, pos);
                }
            }
            return true;
        };
    }

    /** A falling stone whose mark follows {@code target} for 10 ticks, then locks where it stands. */
    private Effect stoneOn(LivingEntity target, int warn) {
        int lock = 10;
        int[] t = {0};
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (!target.isAlive()) {
                    return true;
                }
                if (t[0]++ < lock) {
                    if (t[0] % 2 == 0) {
                        boss.telegraphRing(level, target.position(), 2.2, CHALK);
                    }
                    return false;
                }
                inner[0] = fallingStone(new Vec3(target.getX(), floorY(target), target.getZ()), warn - lock, true);
            }
            return inner[0].tick(boss, level);
        };
    }

    private double floorY(LivingEntity e) {
        return Math.abs(e.getY() - centre().y) < 4.0 ? centre().y : e.getY();
    }

    /** One tick of the swing drop: an arc from where he leapt to the ring, then the landing. */
    private void swingStep(ServerLevel level, int tick) {
        if (moveFrom == null || moveTo == null) {
            return;
        }
        if (tick < 10) {
            double s = (tick + 1) / 10.0;
            Vec3 p = moveFrom.lerp(moveTo, s).add(0, 4.0 * Math.sin(Math.PI * s), 0);
            setPos(p);
            setDeltaMovement(Vec3.ZERO);
            Vec3 to = moveTo.subtract(moveFrom);
            snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
            chainLine(level, p.add(0, 5, 0), anchor(level));
            level.sendParticles(SOUL_DUST, p.x, p.y + 2, p.z, 3, 0.5, 1.0, 0.5, 0);
        }
        if (tick == 9) {
            setNoGravity(false);
            slam(level, moveTo, 3.0, 16.0F, 7.0, 7.0F);
        }
    }

    /** The entrance: up under the spire's point, hanging from the chains. */
    private void hangUp(ServerLevel level) {
        double hang = Mth.clamp(headroom(level) - HEIGHT - 1.0, 0.0, 7.0);
        Vec3 c = centre();
        moveFrom = new Vec3(c.x, c.y + (hang >= 2.0 ? hang : 0.0), c.z);
        setNoGravity(hang >= 2.0);
        setPos(moveFrom);
        setDeltaMovement(Vec3.ZERO);
        landed = false;
    }

    /** The eclipse: the lantern snuffed, every player in the arena blinded, the Architect gone from sight. */
    private void snuff(ServerLevel level) {
        for (LivingEntity e : victims(level, centre(), radius + 6.0)) {
            if (e instanceof Player) {
                e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), this);
                e.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 70, 0), this);
            }
        }
        setInvisible(true);
        level.sendParticles(INK, getX(), getY() + 3, getZ(), 120, radius * 0.4, 1.5, radius * 0.4, 0.02);
        level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY() + 3, getZ(), 40, 1.0, 1.5, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** One tick of the stalk in the dark: footsteps behind the target, the snick, the slash. */
    private void stalkStep(ServerLevel level, @Nullable LivingEntity target, int tick) {
        if (tick < 30 && target != null && target.isAlive()) {
            Vec3 look = target.getLookAngle().multiply(1, 0, 1);
            look = look.lengthSqr() < 1.0E-4 ? Vec3.ZERO : look.normalize();
            Vec3 goal = clampToArena(target.position().subtract(look.scale(2.5)), 1.5);
            Vec3 to = goal.subtract(position()).multiply(1, 0, 1);
            if (to.length() > 0.5) {
                Vec3 v = to.normalize().scale(Math.min(0.34, to.length()));
                setDeltaMovement(v.x, getDeltaMovement().y, v.z);
            } else {
                setDeltaMovement(0, getDeltaMovement().y, 0);
            }
            Vec3 face = target.position().subtract(position());
            snapFacing((float) (Mth.atan2(face.z, face.x) * (180.0 / Math.PI)) - 90.0F);
            if (tick % 6 == 0) {                            // the echoing footsteps and their soul-blue prints
                level.playSound(null, this, SoundEvents.DEEPSLATE_STEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                level.playSound(null, this, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                telegraphRing(level, position(), 0.7, SOUL_DUST);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, getX(), getY() + 0.1, getZ(), 6, 0.3, 0.05, 0.3, 0.01);
            }
            return;
        }
        if (tick == 30) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            level.playSound(null, this, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 3.0F, 1.8F);
            level.playSound(null, this, SoundEvents.WARDEN_TENDRIL_CLICKS, SoundSource.HOSTILE, 3.0F, 0.8F);
        }
        if (tick >= 30 && tick < 40) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            if (tick % 2 == 0) {
                telegraphArc(level, 5.0, 80, SOUL_DUST);
            }
        }
        if (tick == 40) {
            setInvisible(false);
            for (LivingEntity e : arcVictims(this, level, 5.2, 80)) {
                strike(level, e, 16.0F, 1.1, 0.25);
            }
            sweepParticles(this, level, 3.8, 80, SOUL_DUST);
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.6F);
            level.playSound(null, this, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.HOSTILE, 2.5F, 0.8F);
        }
    }

    /** Is the keystone square containing (dx, dz) (from the centre) in half {@code half} of the checkerboard? */
    private boolean keyHalf(double dx, double dz, int half) {
        int cx = Math.floorDiv((int) Math.floor(dx) + keyOffX, KEY_CELL);
        int cz = Math.floorDiv((int) Math.floor(dz) + keyOffZ, KEY_CELL);
        return Math.floorMod(cx + cz, 2) == half;
    }

    private void drawKeystone(ServerLevel level, int half) {
        Vec3 c = centre();
        int r = (int) floorR();
        for (int dx = -r; dx <= r; dx += 2) {
            for (int dz = -r; dz <= r; dz += 2) {
                if (dx * dx + dz * dz > r * r || !keyHalf(dx + 0.5, dz + 0.5, half)) {
                    continue;
                }
                level.sendParticles(CHALK, c.x + dx + 0.5, c.y + 0.15, c.z + dz + 0.5, 1, 0.4, 0, 0.4, 0);
                if (getRandom().nextInt(4) == 0) {
                    level.sendParticles(DUST_FALL, c.x + dx + 0.5, c.y + 6.0, c.z + dz + 0.5, 1, 0.8, 0.5, 0.8, 0);
                }
            }
        }
    }

    private void dropKeystone(ServerLevel level, int half) {
        Vec3 c = centre();
        double r = floorR();
        for (LivingEntity e : victims(level, c, r + 2)) {
            double dx = e.getX() - c.x + 0.5;
            double dz = e.getZ() - c.z + 0.5;
            if (dx * dx + dz * dz <= (r + 1) * (r + 1) && keyHalf(dx, dz, half)
                    && Math.abs(e.getY() - c.y) < 3.0) {
                strike(level, e, 14.0F, 0.2, 0.2);
            }
        }
        int ir = (int) r;
        for (int dx = -ir; dx <= ir; dx += 2) {
            for (int dz = -ir; dz <= ir; dz += 2) {
                if (dx * dx + dz * dz <= ir * ir && keyHalf(dx + 0.5, dz + 0.5, half) && getRandom().nextInt(3) == 0) {
                    level.sendParticles(CRUMBS, c.x + dx + 0.5, c.y + 0.4, c.z + dz + 0.5, 6, 0.6, 0.3, 0.6, 0.1);
                }
            }
        }
        level.playSound(null, c.x, c.y, c.z, SoundEvents.DEEPSLATE_BRICKS_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
    }

    /** Wind-up of the chain swing: crouch, then climb from the floor onto the circle under the chains. */
    private void climbStep(ServerLevel level, int tick) {
        if (moveFrom == null || tick < 12) {
            return;
        }
        if (tick == 12) {
            setNoGravity(true);
            level.playSound(null, this, SoundEvents.CHAIN_FALL, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
        double s = (tick - 11) / 12.0;
        Vec3 p = moveFrom.lerp(orbitPoint(level), s);
        setPos(p);
        setDeltaMovement(Vec3.ZERO);
        chainLine(level, p.add(0, HEIGHT - 0.6, 0), anchor(level));
    }

    private Vec3 orbitPoint(ServerLevel level) {
        double r = Math.max(5.0, Math.min(11.0, radius - 3.0));
        Vec3 c = centre();
        return new Vec3(c.x + Math.cos(orbitAngle) * r, c.y + orbitHeight(level), c.z + Math.sin(orbitAngle) * r);
    }

    /**
     * One tick of the chain swing: three cycles of 30 ticks. Each: rise back to the circle (0-5), swing round it while
     * a soul ring follows the target (to 13) and locks (14), dive on it (20-24), slam (24), pause (25-29). He stays on
     * the floor after the third slam.
     */
    private void orbitStep(ServerLevel level, int tick) {
        int n = tick / 30;
        int c = tick % 30;
        if (n >= 3 || n == 2 && c > 24) {
            setNoGravity(false);
            return;
        }
        LivingEntity target = getTarget();
        if (c <= 19) {
            orbitAngle += 0.07;
            Vec3 orbit = orbitPoint(level);
            Vec3 p = orbit;
            if (n > 0 && c <= 5 && moveTo != null) {
                p = moveTo.lerp(orbit, c / 5.0);
            }
            setNoGravity(true);
            setPos(p);
            setDeltaMovement(Vec3.ZERO);
            Vec3 tangent = new Vec3(-Math.sin(orbitAngle), 0, Math.cos(orbitAngle));
            snapFacing((float) (Mth.atan2(tangent.z, tangent.x) * (180.0 / Math.PI)) - 90.0F);
            if (c < 14) {
                if (target != null && target.isAlive()) {
                    moveTo = clampToArena(target.position(), 2.0);
                } else if (moveTo == null || c == 0) {
                    moveTo = clampToArena(randomSpot(), 2.0);
                }
            }
            if (c == 14) {
                level.playSound(null, this, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 3.0F, 0.6F);
            }
            if (c % 2 == 0 && moveTo != null) {
                telegraphRing(level, moveTo, 3.2, c >= 14 ? CHALK : SOUL_DUST);
            }
            if (c == 19) {
                moveFrom = p;
            }
            if (c % 5 == 0) {
                level.playSound(null, this, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 2.0F, 0.6F);
            }
        } else if (c <= 24 && moveFrom != null && moveTo != null) {
            Vec3 p = moveFrom.lerp(moveTo, (c - 19) / 5.0);
            setPos(p);
            setDeltaMovement(Vec3.ZERO);
            Vec3 to = moveTo.subtract(moveFrom);
            snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
            level.sendParticles(SOUL_DUST, p.x, p.y + 2, p.z, 4, 0.5, 1.0, 0.5, 0);
            if (c == 24) {
                slam(level, moveTo, 3.2, 16.0F, 6.0, 7.0F);
                if (n == 2) {
                    setNoGravity(false);
                }
            }
        }
        if (isNoGravity() && tick % 2 == 0) {
            chainLine(level, position().add(0, HEIGHT - 0.6, 0), anchor(level));
        }
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    private static Effect delayed(int delay, Effect inner) {
        int[] t = {0};
        return (boss, level) -> t[0]++ >= delay && inner.tick(boss, level);
    }

    // ------------------------------------------------------------------ temporary blocks

    /** Change a block for {@code life} ticks, remembering what was there first (only the first change counts). */
    private void setTemp(ServerLevel level, BlockPos pos, BlockState state, int life) {
        long key = pos.asLong();
        Temp old = temps.get(key);
        if (old == null) {
            temps.put(key, new Temp(level.getBlockState(pos), life));
        } else {
            old.life = Math.max(old.life, life);
        }
        level.setBlock(pos, state, 3);
    }

    /** A pile of rubble where a stone fell: a block of masonry on the floor (and one beside it), never on anyone. */
    private void placeRubble(ServerLevel level, Vec3 at) {
        BlockPos base = BlockPos.containing(at.x, centre().y + 0.5, at.z);
        if (Math.abs(at.y - centre().y) > 1.0) {
            return;
        }
        BlockState[] kinds = {Blocks.COBBLED_DEEPSLATE.defaultBlockState(), Blocks.CRACKED_DEEPSLATE_BRICKS.defaultBlockState(),
                Blocks.CHISELED_DEEPSLATE.defaultBlockState()};
        List<BlockPos> cells = new ArrayList<>(List.of(base));
        Direction d = Direction.Plane.HORIZONTAL.getRandomDirection(getRandom());
        cells.add(base.relative(d));
        for (BlockPos p : cells) {
            BlockPos below = p.below();
            boolean occupied = !level.getEntitiesOfClass(LivingEntity.class, new AABB(p)).isEmpty();
            if (!occupied && level.getBlockState(p).isAir() && level.getBlockEntity(below) == null
                    && level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)
                    && flatDist(Vec3.atBottomCenterOf(p), centre()) > 2.0) {
                setTemp(level, p, kinds[getRandom().nextInt(kinds.length)], RUBBLE_LIFE + getRandom().nextInt(30));
            }
        }
    }

    /** Puts one changed block back, lifting whoever stands inside it onto it. */
    private void restore(ServerLevel level, long key, Temp temp) {
        BlockPos p = BlockPos.of(key);
        level.setBlock(p, temp.original, 3);
        if (!temp.original.isAir()) {
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(p))) {
                e.teleportTo(e.getX(), p.getY() + 1.0, e.getZ());
            }
        }
        if (getRandom().nextInt(6) == 0) {
            level.sendParticles(CRUMBS, p.getX() + 0.5, p.getY() + 1.0, p.getZ() + 0.5, 3, 0.3, 0.1, 0.3, 0.05);
        }
    }

    /** Every changed block goes back, deepest first (so lifted creatures end on the floor). */
    private void restoreAll(ServerLevel level) {
        if (temps.isEmpty()) {
            return;
        }
        List<Map.Entry<Long, Temp>> all = new ArrayList<>(temps.entrySet());
        all.sort((a, b) -> Integer.compare(BlockPos.getY(a.getKey()), BlockPos.getY(b.getKey())));
        temps.clear();
        for (Map.Entry<Long, Temp> e : all) {
            restore(level, e.getKey(), e.getValue());
        }
        cracked.clear();
        floorState = 0;
    }

    private void tickTemps(ServerLevel level) {
        if (temps.isEmpty()) {
            return;
        }
        List<Map.Entry<Long, Temp>> due = new ArrayList<>();
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            if (--e.getValue().life <= 0) {
                due.add(e);
            }
        }
        if (due.isEmpty()) {
            return;
        }
        due.sort((a, b) -> Integer.compare(BlockPos.getY(a.getKey()), BlockPos.getY(b.getKey())));
        for (Map.Entry<Long, Temp> e : due) {
            temps.remove(e.getKey());
            restore(level, e.getKey(), e.getValue());
        }
        level.playSound(null, BlockPos.of(due.get(0).getKey()), SoundEvents.DEEPSLATE_BRICKS_BREAK, SoundSource.HOSTILE, 1.5F, 1.2F);
    }

    // ------------------------------------------------------------------ phase 3: the island breaks up

    private void callUnmoor(ServerLevel level) {
        unmoored = true;
        chainTimer = 140;
        floorState = 0;
        floorTimer = 30;
        addEffect(WayfarerBoss.wave(position(), 12, 0.55, 12.0F, CRUMBS));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("abyssal_architect_unmoor"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 c = centre();
        level.sendParticles(CRUMBS, c.x, c.y + 0.5, c.z, 300, radius * 0.5, 0.2, radius * 0.5, 0.2);
        level.sendParticles(DUST_FALL, c.x, c.y + 9, c.z, 120, radius * 0.5, 1.0, radius * 0.5, 0);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BRICKS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    /**
     * Does the floor column at (dx, dz) from the centre crumble in pattern {@code kind} (turned by {@code turn}
     * radians)? 0 rings, 1 spokes, 2 checkers, 3 spiral, 4 halves (outer half on one side, inner disc on the other).
     */
    private static boolean inPattern(int kind, double dx, double dz, double turn, int flip) {
        double r = Math.hypot(dx, dz);
        double ang = Math.atan2(dz, dx) + turn;
        double rx = dx * Math.cos(turn) - dz * Math.sin(turn);
        return switch (kind) {
            case 0 -> Math.floorMod((int) Math.floor(r / 3.0) + flip, 2) == 0;
            case 1 -> Math.floorMod((int) Math.floor(ang / (Math.PI / 4)) + flip, 2) == 0;
            case 2 -> Math.floorMod(Math.floorDiv((int) Math.floor(rx), 3)
                    + Math.floorDiv((int) Math.floor(dx * Math.sin(turn) + dz * Math.cos(turn)), 3) + flip, 2) == 0;
            case 3 -> Math.floorMod((int) Math.floor(ang / (Math.PI * 2) * 4 + r / 4.0) + flip, 2) == 0;
            default -> (rx > 0) == (flip == 0) ? r > 7.0 : r <= 7.0 && r > 3.0;
        };
    }

    /** Marks the next pattern: the columns that will crumble (never the seal's, nor under or beside him). */
    private void markPattern(ServerLevel level) {
        cracked.clear();
        int kind = getRandom().nextInt(5);
        double turn = getRandom().nextDouble() * Math.PI * 2;
        int flip = getRandom().nextInt(2);
        BlockPos c = BlockPos.containing(centre());
        int y = c.getY() - 1;
        int r = (int) floorR();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.hypot(dx, dz);
                if (d > r || d < 2.5 || !inPattern(kind, dx, dz, turn, flip)) {
                    continue;
                }
                BlockPos p = new BlockPos(c.getX() + dx, y, c.getZ() + dz);
                if (flatDist(Vec3.atBottomCenterOf(p), position()) < 3.0 || temps.containsKey(p.asLong())) {
                    continue;
                }
                BlockState top = level.getBlockState(p);
                if (top.isAir() || !level.getFluidState(p).isEmpty() || level.getBlockEntity(p) != null
                        || !level.getBlockState(p.above()).isAir() || !top.isFaceSturdy(level, p, Direction.UP)) {
                    continue;
                }
                cracked.add(p);
            }
        }
        level.playSound(null, c, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void drawCracks(ServerLevel level, boolean hard) {
        for (int i = 0; i < cracked.size(); i++) {
            if (!hard && (i + tickCount) % 3 != 0) {
                continue;
            }
            BlockPos p = cracked.get(i);
            level.sendParticles(hard ? SOUL_DUST : CHALK, p.getX() + 0.5, p.getY() + 1.1, p.getZ() + 0.5, 1, 0.3, 0, 0.3, 0);
            if (hard && getRandom().nextInt(5) == 0) {
                level.sendParticles(CRUMBS, p.getX() + 0.5, p.getY() + 1.05, p.getZ() + 0.5, 2, 0.3, 0, 0.3, 0.02);
            }
        }
    }

    /** The marked tiles crumble into the lake: each column (4 deep) becomes water for 5 s, then rises again. */
    private void crumble(ServerLevel level) {
        BlockState water = Blocks.WATER.defaultBlockState();
        for (BlockPos top : cracked) {
            boolean ok = true;
            for (int d = 0; d < FLOOR_DEPTH && ok; d++) {
                BlockPos q = top.below(d);
                if (level.getBlockEntity(q) != null || level.getBlockState(q).isAir()) {
                    ok = false;
                }
                for (Direction side : Direction.Plane.HORIZONTAL) {     // the water must stay in its column
                    if (level.getBlockState(q.relative(side)).isAir()) {
                        ok = false;
                    }
                }
            }
            if (!ok || level.getBlockState(top.below(FLOOR_DEPTH)).isAir()) {
                continue;
            }
            for (int d = 0; d < FLOOR_DEPTH; d++) {
                BlockPos q = top.below(d);
                setTemp(level, q, water, HOLE_LIFE + d);
            }
            if (getRandom().nextInt(4) == 0) {
                level.sendParticles(ParticleTypes.SPLASH, top.getX() + 0.5, top.getY() + 1.0, top.getZ() + 0.5, 6, 0.4, 0.2, 0.4, 0.1);
                level.sendParticles(CRUMBS, top.getX() + 0.5, top.getY() + 0.8, top.getZ() + 0.5, 4, 0.3, 0.1, 0.3, 0.05);
            }
        }
        BlockPos c = BlockPos.containing(centre());
        level.playSound(null, c, SoundEvents.DEEPSLATE_BRICKS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, c, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.5F);
        cracked.clear();
    }

    /** The floor cycle: wait, mark (2 s of cracking), crumble (5 s), wait again. */
    private void tickFloor(ServerLevel level) {
        if (--floorTimer > 0) {
            if (floorState == 1) {
                drawCracks(level, floorTimer <= 12);
                if (floorTimer % 10 == 0) {
                    level.playSound(null, BlockPos.containing(centre()), SoundEvents.GRAVEL_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                }
            }
            return;
        }
        switch (floorState) {
            case 0 -> {
                markPattern(level);
                floorState = 1;
                floorTimer = CRACK_WARN;
            }
            case 1 -> {
                crumble(level);
                floorState = 2;
                floorTimer = HOLE_LIFE + 4;
            }
            default -> {
                floorState = 0;
                floorTimer = (int) Math.round(FLOOR_PAUSE * cooldownScale());
            }
        }
    }

    /** Whoever falls through the floor into the lake is dragged at by the abyss: 3 and slowed every half second. */
    private void abyssDrag(ServerLevel level) {
        for (LivingEntity e : victims(level, centre(), floorR() + 2.0)) {
            if (!e.isInWater()) {
                continue;
            }
            BlockPos at = e.blockPosition();
            if (temps.containsKey(at.asLong()) || temps.containsKey(at.below().asLong())) {
                if (e.hurtServer(level, damageSources().mobAttack(this), 3.0F)) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 1), this);
                }
                e.setDeltaMovement(e.getDeltaMovement().add(0, -0.08, 0));
                e.hurtMarked = true;
                level.sendParticles(SOUL_DUST, e.getX(), e.getY() + 0.5, e.getZ(), 4, 0.3, 0.3, 0.3, 0);
            }
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (unmoorGuard > 0) {
            level.sendParticles(CRUMBS, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.1);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void endPhaseThree(ServerLevel level) {
        unmoored = false;
        roarUntil = -1;
        restoreAll(level);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("abyssal_architect_unmoor"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("abyssal_architect_wrath"));
        }
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleTemps.isEmpty()) {          // blocks saved by an unload never outlive it
            for (SavedTemp s : staleTemps) {
                temps.putIfAbsent(s.pos(), new Temp(s.state(), 0));
            }
            staleTemps.clear();
            restoreAll(level);
        }
        if (unmoorGuard > 0) {
            unmoorGuard--;
        }
        BossAttack current = currentAttack();
        String move = current == null ? "" : current.name;
        // gravity and sight come back whenever the move that took them is over (stagger, reset, chain)
        if (isNoGravity() && !move.equals("chainswing") && !move.equals("swingdrop") && !move.equals("descend")) {
            setNoGravity(false);
        }
        if (isInvisible() && !move.equals("eclipse")) {
            setInvisible(false);
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level, new AABB(BlockPos.containing(centre())).inflate(radius + 14, 16, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone) {                        // the arena emptied (death, flight): every block goes back at once
            restoreAll(level);
            if (++emptyTicks > 410) {
                introPending = true;          // the fight has reset: he will hang from his chains again
            }
        } else {
            emptyTicks = 0;
        }
        if (phase() == 1 && unmoored) {       // the fight was reset: the island is whole again
            endPhaseThree(level);
        }
        tickTemps(level);
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (introPending && fighting && current == null && phase() == 1) {
            introPending = false;
            chain(level, "descend");
            return;
        }
        boolean free = fighting && current == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!unmoored && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "unmoor");
            } else if (unmoored && --chainTimer <= 0) {
                chainTimer = (int) Math.round(CHAINSWING_EVERY * cooldownScale());
                chain(level, "chainswing");
            }
        }
        if (unmoored && anyone) {
            tickFloor(level);
            if (tickCount % 10 == 0) {
                abyssDrag(level);
            }
        }
        // ambience: the soul lantern, the creak of the chains, dust from the vault
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        if (tickCount % 4 == 0 && !isInvisible()) {
            double lx = getX() + Mth.cos(yaw) * 1.0 - Mth.sin(yaw) * 0.9;
            double lz = getZ() + Mth.sin(yaw) * 1.0 + Mth.cos(yaw) * 0.9;
            level.sendParticles(ParticleTypes.SOUL, lx, getY() + 2.0, lz, 1, 0.1, 0.1, 0.1, 0.005);
        }
        if (tickCount % 80 == 0) {
            level.playSound(null, this, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.2F, 0.5F);
        }
        if (unmoored && tickCount % 6 == 0) {
            Vec3 c = centre();
            level.sendParticles(DUST_FALL, c.x, c.y + 10, c.z, 2, radius * 0.4, 0.5, radius * 0.4, 0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("abyssal_architect_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, CRUMBS));
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.sendParticles(SOUL_DUST, getX(), getY() + 3, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        restoreAll(level);
        setNoGravity(false);
        setInvisible(false);
        level.sendParticles(CRUMBS, getX(), getY() + 2.5, getZ(), 150, 1.2, 2.0, 1.2, 0.3);
        level.sendParticles(SOUL_DUST, getX(), getY() + 3, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.WARDEN_DEATH, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            restoreAll(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("ArchitectCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("ArchitectRadius", radius);
        output.putBoolean("ArchitectIntro", introPending);
        output.putBoolean("ArchitectUnmoored", unmoored);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original, e.getValue().life));
        }
        output.store("ArchitectBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("ArchitectCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("ArchitectRadius", 15);
        introPending = input.getBooleanOr("ArchitectIntro", true);
        unmoored = input.getBooleanOr("ArchitectUnmoored", false) && phase() == 2;
        staleTemps.clear();
        input.read("ArchitectBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
    }
}
