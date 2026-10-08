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
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ProjectileDeflection;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
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
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.SolarHierarch.BASH;
import static com.brasshaven.generated.MobAnims.SolarHierarch.COMBO;
import static com.brasshaven.generated.MobAnims.SolarHierarch.DESCENT;
import static com.brasshaven.generated.MobAnims.SolarHierarch.ECLIPSE;
import static com.brasshaven.generated.MobAnims.SolarHierarch.FLARE;
import static com.brasshaven.generated.MobAnims.SolarHierarch.FLASH;
import static com.brasshaven.generated.MobAnims.SolarHierarch.ORRERY;
import static com.brasshaven.generated.MobAnims.SolarHierarch.REEL;
import static com.brasshaven.generated.MobAnims.SolarHierarch.ROAR;
import static com.brasshaven.generated.MobAnims.SolarHierarch.SIGILS;
import static com.brasshaven.generated.MobAnims.SolarHierarch.STAGGER;
import static com.brasshaven.generated.MobAnims.SolarHierarch.SUNLANCE;
import static com.brasshaven.generated.MobAnims.SolarHierarch.SWEEP;
import static com.brasshaven.generated.MobAnims.SolarHierarch.THRUST;

/**
 * Le Hiérarque solaire (The Solar Hierarch), the priest-automaton of the Sun-Engine Ziggurat's sun chamber: a tall
 * gilded priest of 6 blocks with a turning brass sun-disc halo, a sun-staff and a mirror-shield.
 * <p>A hard fight: 620 health, armour 12, poise 115, hits of 8 to 18. Three phases:
 * <ul>
 *     <li>Phase 1: staff <b>sweep</b>, <b>thrust</b> (burns), a three-blow <b>combo</b>, the <b>mirror flash</b>
 *     (blinds whoever looks at him), the <b>sun-lance</b> (he stands on the sun disc and reflects the light of the lens
 *     shaft onto the floor: the beam hunts a player slowly across the chamber) and the <b>orrery</b> (brass planets on
 *     arms of light sweep the whole chamber round the sun disc: jump the low ones, hide behind a gnomon from the
 *     high ones).</li>
 *     <li>Phase 2 (65%): faster, combos, <b>flare</b> (three rings of fire to jump), <b>descent</b> (a leap onto a
 *     marked ring), a second ray in the sun-lance, three arms in the orrery that reverse half-way.</li>
 *     <li>Phase 3 (30%): the <b>eclipse</b>: the chamber goes dark (Darkness), only the halo and a beam that wanders
 *     after the players are lit; every 11 s he blinks between six marked sun-sigils (<b>sigils</b>), bursting a corona
 *     on each.</li>
 * </ul>
 * The mirror-shield guards every frontal blow while he walks and during his staff blows (glinting) and reflects
 * frontal projectiles back at their shooter. Three blocked blows in a row earn a shield bash; a full guard meter breaks
 * the guard (he reels open, +30% damage). His spectacle moves (sun-lance, orrery, sigils, eclipse) lower the mirror.
 * <p>Six sandstone gnomons rise round the sun disc when the fight starts: they cast the shadows that shelter from his
 * light. Every block is temporary: recorded with its original state and restored when the arena empties, when the
 * fight resets, when he dies or is removed, and after a reload.
 */
public class SolarHierarch extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.8F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_R = 5.6;
    private static final double SWEEP_HALF = 75;
    private static final double THRUST_LEN = 8.5;
    private static final double BEAM_R = 1.5;
    private static final double GNOMON_R = 9.5;
    private static final int GNOMON_H = 4;
    private static final double SIGIL_R = 13.0;
    private static final int SIGILS_EVERY = 220;
    private static final double LOW_ARM = 0.45;
    private static final double HIGH_ARM = 1.6;
    private static final Set<String> GUARDED = Set.of("sweep", "thrust", "combo", "bash", "flare", "descent");
    private static final DustParticleOptions GOLD_DUST = new DustParticleOptions(0xF2C14E, 1.3F);
    private static final DustParticleOptions SUN = new DustParticleOptions(0xFFE7A0, 1.8F);
    private static final DustParticleOptions EMBER = new DustParticleOptions(0xFF8A2A, 1.3F);
    private static final DustParticleOptions LAPIS = new DustParticleOptions(0x3A5BD0, 1.2F);
    private static final DustParticleOptions INK = new DustParticleOptions(0x14121C, 2.0F);
    private static final BlockParticleOption CRUMBS = new BlockParticleOption(ParticleTypes.BLOCK,
            Blocks.CUT_SANDSTONE.defaultBlockState());

    private record SavedBlock(long pos, BlockState state) {
        static final Codec<SavedBlock> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedBlock::pos),
                BlockState.CODEC.fieldOf("state").forGetter(SavedBlock::state)).apply(i, SavedBlock::new));
    }

    /** Arena centre (feet level) and radius, from the seal. */
    private @Nullable Vec3 centre;
    private int radius = 16;
    /** Blocks he placed (the gnomons): original states by packed position. */
    private final Map<Long, BlockState> temps = new LinkedHashMap<>();
    private final List<SavedBlock> staleTemps = new ArrayList<>();
    private boolean gnomonsRaised;
    private int emptyTicks;
    // phase 3
    private boolean eclipse;
    private int eclipseGuard;
    private int roarUntil = -1;
    private int sigilTimer;
    private @Nullable Vec3 eclipseSpot;
    private int eclipseTop = 12;
    // the mirror's guard
    private float guardMeter;
    private int lastBlockTick = -100;
    private int blockStreak;
    private int reelUntil = -1;
    // move state
    private final Map<UUID, Integer> burnedAt = new HashMap<>();
    private final Set<String> armHits = new HashSet<>();
    private final List<Vec3> trail = new ArrayList<>();
    private final List<Vec3> sigilOrder = new ArrayList<>();
    private @Nullable Vec3 spot;
    private @Nullable Vec3 spot2;
    private @Nullable Vec3 moveFrom;
    private @Nullable Vec3 moveTo;
    private double armAngle;
    private int armDir = 1;
    private boolean landed;

    public SolarHierarch(EntityType<? extends Monster> type, Level level) {
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
        return MobAnims.SolarHierarch.TICKS;
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

    /** Phase 3 (the eclipse) counts as a third stage of the fight (the base class knows only two). */
    public boolean isEclipsed() {
        return eclipse;
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

    private double floorR() {
        return Math.min(16.0, Math.max(7.0, radius));
    }

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(3.0, floorR() - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    /** Free air above {@code p} (blocks), at most {@code max}. */
    private int headroom(ServerLevel level, Vec3 p, int max) {
        BlockPos b = BlockPos.containing(p);
        for (int h = 1; h <= max; h++) {
            if (!level.getBlockState(b.above(h)).isAir()) {
                return h;
            }
        }
        return max;
    }

    /** Players fighting in the arena. */
    private List<Player> fighters(ServerLevel level) {
        List<Player> out = new ArrayList<>();
        for (LivingEntity e : victims(level, centre(), floorR() + 4.0)) {
            if (e instanceof Player p) {
                out.add(p);
            }
        }
        return out;
    }

    private @Nullable LivingEntity quarry(ServerLevel level) {
        LivingEntity t = getTarget();
        if (t != null && t.isAlive()) {
            return t;
        }
        List<Player> all = fighters(level);
        return all.isEmpty() ? null : all.get(0);
    }

    /** Is the straight line between two points blocked (a gnomon, a wall)? */
    private boolean shaded(ServerLevel level, Vec3 from, Vec3 to) {
        return level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this))
                .getType() != HitResult.Type.MISS;
    }

    private Vec3 mirrorPos() {
        return position().add(forward().scale(0.9)).add(0, 4.2, 0);
    }

    private void blink(ServerLevel level, Vec3 to) {
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3, getZ(), 40, 0.6, 1.6, 0.6, 0.08);
        level.sendParticles(SUN, getX(), getY() + 3, getZ(), 30, 0.6, 1.6, 0.6, 0);
        teleportTo(to.x, to.y, to.z);
        setDeltaMovement(Vec3.ZERO);
        level.sendParticles(ParticleTypes.END_ROD, to.x, to.y + 3, to.z, 40, 0.6, 1.6, 0.6, 0.08);
        level.playSound(null, this, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 2.5F, 0.7F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    /** He steps onto the sun disc in a flash of light (spectacle moves are cast from the centre). */
    private void toCentre(ServerLevel level) {
        if (flatDist(position(), centre()) > 1.5) {
            blink(level, centre());
        }
    }

    private void face(Vec3 at) {
        Vec3 to = at.subtract(position());
        if (to.horizontalDistanceSqr() > 1.0E-4) {
            snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
        }
    }

    /** Sun damage (beams, burns): at most once per 10 ticks per creature. */
    private void burn(ServerLevel level, LivingEntity e, float damage, float fireSeconds) {
        Integer last = burnedAt.get(e.getUUID());
        if (last != null && tickCount - last < 10) {
            return;
        }
        burnedAt.put(e.getUUID(), tickCount);
        if (e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            e.igniteForSeconds(fireSeconds);
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // sweep: the staff drawn back over his right shoulder (0.7 s, the arc traced in embers), then swept across
        // his front over 150 degrees
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(14, 4, 14).range(0, 6.0).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        telegraphArc(level, SWEEP_R, SWEEP_HALF, EMBER);
                    }
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(level, SWEEP_R, SWEEP_HALF)) {
                        strike(level, e, 14.0F, 0.9, 0.25);
                    }
                    sweepParticles(level, SWEEP_R - 1.0, SWEEP_HALF, ParticleTypes.FLAME);
                    level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (phase() == 2 && t != null && getRandom().nextFloat() < 0.35F) {
                        chain(level, distanceTo(t) > 4.5 ? "thrust" : "combo");
                    }
                })
                .build());
        // thrust: the staff levelled at the hip, its sun forward (0.8 s, the line marked), then driven straight ahead
        // as he lunges: 16 and burning
        out.add(BossAttack.of("thrust").anim(THRUST).timing(16, 4, 14).range(3.0, 9.0).cooldown(60).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.0; d <= THRUST_LEN; d += 0.8) {
                            Vec3 p = ahead(d);
                            level.sendParticles(EMBER, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, this, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : lineVictims(level, THRUST_LEN, 1.2)) {
                        strike(level, e, 16.0F, 1.0, 0.2);
                        e.igniteForSeconds(3.0F);
                    }
                    for (double d = 1.0; d <= THRUST_LEN; d += 0.6) {
                        Vec3 p = ahead(d);
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.8, p.z, 2, 0.1, 0.1, 0.1, 0.02);
                    }
                    lunge(0.9, 0.05);
                    level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (phase() == 2 && t != null && distanceTo(t) < 5.0 && getRandom().nextFloat() < 0.4F) {
                        chain(level, "sweep");
                    }
                })
                .build());
        // combo: three blows: a sweep (0.7 s), a backhand half a second later (he turns toward you between them), then
        // the staff raised and slammed down a line (17; phase 2: a ring of fire rolls on from it)
        out.add(BossAttack.of("combo").anim(COMBO).timing(14, 28, 16).range(0, 6.0).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        telegraphArc(level, 5.2, 70, EMBER);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(level, 5.2, 70)) {
                        strike(level, e, 12.0F, 0.7, 0.2);
                    }
                    sweepParticles(level, 4.2, 70, ParticleTypes.FLAME);
                    level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.7F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 5 && t != null) {
                        turnToward(t, 35.0F);
                    }
                    if (tick > 4 && tick < 10 && tick % 2 == 0) {
                        telegraphArc(level, 5.2, 70, EMBER);
                    }
                    if (tick == 10) {
                        for (LivingEntity e : arcVictims(level, 5.2, 70)) {
                            strike(level, e, 12.0F, 0.7, 0.2);
                        }
                        sweepParticles(level, 4.2, 70, ParticleTypes.FLAME);
                        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.9F);
                    }
                    if (tick == 14 && t != null) {
                        turnToward(t, 35.0F);
                    }
                    if (tick > 14 && tick < 22 && tick % 2 == 0) {
                        for (double d = 1.0; d <= 6.0; d += 0.8) {
                            Vec3 p = ahead(d);
                            level.sendParticles(SUN, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                    if (tick == 22) {
                        for (LivingEntity e : lineVictims(level, 6.0, 1.4)) {
                            strike(level, e, 17.0F, 0.6, 0.5);
                        }
                        Vec3 p = ahead(4.0);
                        level.sendParticles(CRUMBS, p.x, p.y + 0.3, p.z, 40, 1.0, 0.2, 1.0, 0.15);
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.3, p.z, 20, 0.8, 0.2, 0.8, 0.05);
                        level.playSound(null, p.x, p.y, p.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.8F);
                        if (phase() == 2) {
                            addEffect(WayfarerBoss.wave(p, 6.0, 0.5, 7.0F, ParticleTypes.FLAME));
                        }
                    }
                })
                .build());
        // shield bash: never rolled; three blows blocked in a row earn it. The mirror drawn in (0.5 s, a short arc),
        // then slammed forward: 9, thrown back hard
        out.add(BossAttack.of("bash").anim(BASH).timing(10, 4, 12).range(999, 999).cooldown(0).weight(0)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        telegraphArc(level, 3.8, 60, SUN);
                    }
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(level, 3.8, 60)) {
                        strike(level, e, 9.0F, 1.8, 0.45);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 1), this);
                    }
                    Vec3 p = ahead(1.6);
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 2.4, p.z, 20, 0.5, 0.6, 0.5, 0.1);
                    level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 1.4F);
                })
                .build());
        // guard broken: never rolled; hurtServer starts it when the mirror's guard meter fills
        out.add(BossAttack.of("reel").anim(REEL).timing(6, 4, 30).range(999, 999).cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> {
                    reelUntil = tickCount + 50;
                    guardMeter = 0;
                    blockStreak = 0;
                    setDeltaMovement(0, getDeltaMovement().y, 0);
                    level.playSound(null, this, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 2.5F, 0.6F);
                    level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.5F);
                    Vec3 p = mirrorPos();
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y - 1.5, p.z, 30, 0.6, 0.6, 0.6, 0.2);
                })
                .build());
        // mirror flash: the mirror raised and tilted to catch the light (0.9 s, the cone traced in sunlight), then
        // flashed: 8 and burning to all in the cone he can see; whoever is looking at him is blinded 2.5 s.
        // Turn your back, or put a gnomon between you
        out.add(BossAttack.of("flash").anim(FLASH).timing(18, 6, 14).range(0, 14.0).cooldown(160).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        telegraphArc(level, 12.0, 35, SUN);
                        telegraphArc(level, 6.0, 35, SUN);
                    }
                    Vec3 m = mirrorPos();
                    level.sendParticles(ParticleTypes.END_ROD, m.x, m.y, m.z, 1, 0.3, 0.3, 0.3, 0.01);
                    if (tick == 0 || tick == 10) {
                        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 1.2F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> flash(level))
                .build());
        // sun-lance: he steps onto the sun disc and lifts the mirror to the lens shaft (1.5 s: the light runs down the
        // shaft, a ring of embers marks where it will land); then for 6 s the light is reflected onto the floor and
        // the spot hunts its target at a walk. 5 and burning every half second; the gnomons stop the ray.
        // Phase 2: a second ray (the echo of the first, 1.5 s behind it; in co-op it hunts another player)
        out.add(BossAttack.of("sunlance").anim(SUNLANCE).timing(30, 120, 20).range(0, 40.0).cooldown(380).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (eclipse) {
                        chain(level, "flare");
                        return;
                    }
                    trail.clear();
                    spot = null;
                    spot2 = null;
                    toCentre(level);
                })
                .windup((b, level, t, tick) -> lanceWindup(level, tick))
                .impact((b, level, t, tick) -> {
                    level.playSound(null, this, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.8F);
                    level.playSound(null, this, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> lanceStep(level, tick))
                .end((b, level, t, tick) -> level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.5F, 0.8F))
                .build());
        // orrery: on the sun disc, the staff raised like the orrery's spindle (1.2 s: the arms drawn where they start,
        // chevrons showing the way they will turn); brass planets on arms of light sweep the whole chamber round the
        // disc for 4.5 s. Low arms (gold): jump them. High arms (sunlight): only a gnomon's shadow shelters you.
        // Phase 1: one low and one high arm, opposite, one turn. Phase 2: three arms, faster, reversing half-way
        out.add(BossAttack.of("orrery").anim(ORRERY).timing(24, 90, 20).range(0, 40.0).cooldown(420).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    toCentre(level);
                    armAngle = getRandom().nextDouble() * Math.PI * 2;
                    armDir = getRandom().nextBoolean() ? 1 : -1;
                    armHits.clear();
                    level.playSound(null, this, SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawArms(level, false);
                    }
                    if (tick == 0 || tick == 12) {
                        level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.6F))
                .active((b, level, t, tick) -> orreryStep(level, tick))
                .build());

        // ---------------------------------------------------------------- phase 2
        // flare: the staff held high, the halo blazing (1.0 s, three rings traced in embers), then planted: three
        // rings of fire roll out from him 0.6 s apart (10 each, jump them)
        out.add(BossAttack.of("flare").anim(FLARE).phaseTwo().timing(20, 30, 14).range(0, 12.0).cooldown(200).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (double r = 3.5; r <= 10.5; r += 3.5) {
                            telegraphRing(level, position(), r, EMBER);
                        }
                    }
                    level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 4.5, getZ(), 3, 1.0, 1.0, 1.0, 0.02);
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.BLAZE_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> flareRing(level))
                .active((b, level, t, tick) -> {
                    if (tick == 12 || tick == 24) {
                        flareRing(level);
                    }
                })
                .build());
        // descent: crouched, the staff raised (0.9 s; a ring follows the target for 0.6 s, then locks in sunlight); he
        // leaps and comes down on it staff first: 18 within 3 and a ring of fire (8, jump it)
        out.add(BossAttack.of("descent").anim(DESCENT).phaseTwo().timing(18, 12, 16).range(6.0, 24.0).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> moveTo = null)
                .windup((b, level, t, tick) -> {
                    if (tick < 12 && t != null) {
                        moveTo = clampToArena(t.position(), 2.0);
                    }
                    if (moveTo != null && tick % 2 == 0) {
                        telegraphRing(level, moveTo, 3.0, tick >= 12 ? SUN : EMBER);
                    }
                    if (tick == 12) {
                        level.playSound(null, this, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    moveFrom = position();
                    if (moveTo == null) {
                        moveTo = clampToArena(ahead(8.0), 2.0);
                    }
                    landed = false;
                    setNoGravity(true);
                    level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> descentStep(level, tick))
                .end((b, level, t, tick) -> {
                    setNoGravity(false);
                    if (t != null && distanceTo(t) < 5.0 && getRandom().nextFloat() < 0.4F) {
                        chain(level, "sweep");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // eclipse: he kneels, staff and mirror crossed over his head (1.5 s, invulnerable, darkness closing in a ring);
        // the mirror covers the sun like a moon: a ring of fire (12, jump it) and the chamber goes dark
        out.add(BossAttack.of("eclipse").anim(ECLIPSE).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    eclipseGuard = 52;
                    level.playSound(null, this, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.5F, 1.4F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        telegraphRing(level, centre(), 1.0 + (floorR() + 2.0) * (1.0 - tick / 30.0), INK);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> callEclipse(level))
                .build());
        // sigils: the staff raised (0.8 s; the first sun-sigil flares, a pillar of light over it); he blinks to it and
        // strikes the floor 0.4 s later: a corona (13 and burning within 4.5). Twice more, each next sigil flaring
        // 0.8 s before he appears there. After the third he stays bowed (the punish window)
        out.add(BossAttack.of("sigils").anim(SIGILS).phaseTwo().timing(16, 66, 24).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> pickSigils(level))
                .windup((b, level, t, tick) -> {
                    if (!sigilOrder.isEmpty()) {
                        flareSigil(level, sigilOrder.get(0), tick);
                    }
                })
                .active((b, level, t, tick) -> sigilStep(level, tick))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private List<LivingEntity> arcVictims(ServerLevel level, double range, double halfAngle) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(halfAngle));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : victims(level, position(), range + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.5) {
                out.add(e);
            }
        }
        return out;
    }

    private List<LivingEntity> lineVictims(ServerLevel level, double length, double halfWidth) {
        Vec3 fwd = forward();
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : victims(level, position(), length + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= length && side <= halfWidth + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.5) {
                out.add(e);
            }
        }
        return out;
    }

    private void sweepParticles(ServerLevel level, double r, double halfAngle, ParticleOptions p) {
        for (double a = -halfAngle; a <= halfAngle; a += 10) {
            Vec3 q = position().add(rotate(forward(), a).scale(r));
            level.sendParticles(p, q.x, q.y + 1.4, q.z, 2, 0.2, 0.3, 0.2, 0.02);
        }
        Vec3 c = ahead(r * 0.6);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.6, c.z, 1, 0, 0, 0, 0);
    }

    private void turnToward(LivingEntity t, float max) {
        Vec3 to = t.position().subtract(position());
        float want = (float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), want, max));
    }

    /** The mirror flash: burns all in the cone he can see; blinds whoever is looking at him. */
    private void flash(ServerLevel level) {
        Vec3 m = mirrorPos();
        for (LivingEntity e : arcVictims(level, 12.5, 35)) {
            if (shaded(level, m, e.getEyePosition())) {
                continue;                                   // behind a gnomon
            }
            strike(level, e, 8.0F, 0.3, 0.1);
            e.igniteForSeconds(2.0F);
            Vec3 toMe = m.subtract(e.getEyePosition()).normalize();
            if (e.getLookAngle().dot(toMe) > 0.5) {
                e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 50, 0), this);
            }
        }
        for (double a = -35; a <= 35; a += 7) {
            Vec3 dir = rotate(forward(), a);
            for (double d = 2; d <= 12; d += 2.5) {
                Vec3 p = m.add(dir.scale(d)).add(0, -d * 0.25, 0);
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0.02);
            }
        }
        level.sendParticles(SUN, m.x, m.y, m.z, 30, 0.4, 0.4, 0.4, 0);
        level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 1.6F);
        level.playSound(null, this, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.0F, 1.2F);
    }

    private void flareRing(ServerLevel level) {
        addEffect(WayfarerBoss.wave(position(), 11.0, 0.5, 10.0F, ParticleTypes.FLAME));
        level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 0.5, getZ(), 30, 1.0, 0.2, 1.0, 0.08);
        level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 1.5F, 1.0F);
    }

    private void descentStep(ServerLevel level, int tick) {
        if (moveFrom == null || moveTo == null || landed) {
            return;
        }
        if (tick < 9) {
            double s = (tick + 1) / 9.0;
            Vec3 p = moveFrom.lerp(moveTo, s).add(0, 5.0 * Math.sin(Math.PI * s), 0);
            setPos(p);
            setDeltaMovement(Vec3.ZERO);
            face(moveTo.add(moveTo.subtract(moveFrom)));
            level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 2, p.z, 3, 0.5, 1.0, 0.5, 0.01);
            return;
        }
        landed = true;
        setNoGravity(false);
        setPos(moveTo);
        hitCircle(level, moveTo, 3.0, 18.0F, 1.1, 0.4);
        addEffect(WayfarerBoss.wave(moveTo, 7.0, 0.5, 8.0F, ParticleTypes.FLAME));
        level.sendParticles(CRUMBS, moveTo.x, moveTo.y + 0.3, moveTo.z, 60, 1.5, 0.3, 1.5, 0.2);
        level.sendParticles(ParticleTypes.EXPLOSION, moveTo.x, moveTo.y + 0.5, moveTo.z, 2, 0.6, 0.1, 0.6, 0);
        level.playSound(null, moveTo.x, moveTo.y, moveTo.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    // ---- the sun-lance

    private Vec3 shaftTop(ServerLevel level) {
        Vec3 c = centre();
        return c.add(0, Math.max(8, headroom(level, c, 20)), 0);
    }

    private void column(ServerLevel level, Vec3 top, Vec3 bottom, double step, ParticleOptions p) {
        double len = top.distanceTo(bottom);
        for (double d = 0; d < len; d += step) {
            Vec3 q = top.lerp(bottom, d / Math.max(0.01, len));
            level.sendParticles(p, q.x, q.y, q.z, 1, 0.08, 0.08, 0.08, 0);
        }
    }

    private void lanceWindup(ServerLevel level, int tick) {
        LivingEntity t = quarry(level);
        if (spot == null) {
            Vec3 dir = t != null ? t.position().subtract(centre()).multiply(1, 0, 1) : forward();
            dir = dir.lengthSqr() < 1.0E-4 ? forward() : dir.normalize();
            spot = clampToArena(centre().add(dir.scale(3.5)), 1.0);
        }
        face(spot);
        Vec3 top = shaftTop(level);
        Vec3 m = mirrorPos();
        if (tick % 2 == 0) {
            Vec3 reach = top.lerp(m, Math.min(1.0, (tick + 2) / 30.0));
            column(level, top, reach, 0.7, ParticleTypes.END_ROD);
            telegraphRing(level, spot, BEAM_R, EMBER);
        }
        if (tick % 4 == 0) {
            column(level, m, spot, 1.0, GOLD_DUST);
        }
        if (tick == 0 || tick == 15) {
            level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.6F + tick * 0.02F);
        }
    }

    /** Where a ray from the mirror toward {@code target} lands (on the floor, or on the gnomon that stops it). */
    private Vec3 landing(ServerLevel level, Vec3 m, Vec3 target, boolean[] blocked) {
        Vec3 aim = target.add(0, 0.05, 0);
        BlockHitResult hit = level.clip(new ClipContext(m, aim, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        blocked[0] = hit.getType() != HitResult.Type.MISS && hit.getLocation().distanceTo(aim) > 0.6;
        return hit.getType() == HitResult.Type.MISS ? aim : hit.getLocation();
    }

    private Vec3 chase(Vec3 from, Vec3 to, double speed) {
        Vec3 d = to.subtract(from).multiply(1, 0, 1);
        double len = d.length();
        return len <= speed ? new Vec3(to.x, from.y, to.z) : from.add(d.scale(speed / len));
    }

    private void lanceStep(ServerLevel level, int tick) {
        LivingEntity t = quarry(level);
        if (spot == null) {
            spot = clampToArena(ahead(3.5), 1.0);
        }
        double speed = phase() == 2 ? 0.13 : 0.105;
        if (t != null) {
            spot = clampToArena(chase(spot, t.position(), speed), 1.0);
        }
        face(spot);
        Vec3 top = shaftTop(level);
        Vec3 m = mirrorPos();
        if (tick % 2 == 0) {
            column(level, top, m, 0.8, ParticleTypes.END_ROD);
        }
        ray(level, m, spot, tick);
        trail.add(spot);
        if (phase() == 2) {
            List<Player> all = fighters(level);
            Player other = null;
            for (Player p : all) {
                if (p != t && (other == null || p.distanceToSqr(t == null ? p : t) > other.distanceToSqr(t == null ? other : t))) {
                    other = p;
                }
            }
            if (other != null) {                            // co-op: the second ray hunts another player
                spot2 = clampToArena(chase(spot2 == null ? spot : spot2, other.position(), speed), 1.0);
                ray(level, m, spot2, tick + 1);
            } else if (trail.size() > 30) {                 // alone: the echo follows 1.5 s behind the first ray
                ray(level, m, trail.get(trail.size() - 31), tick + 1);
            }
        }
        if (tick % 20 == 0) {
            level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.5F, 1.2F);
        }
    }

    /** One reflected ray from the mirror to the floor: drawn, and burning whoever stands in it or on its spot. */
    private void ray(ServerLevel level, Vec3 m, Vec3 target, int tick) {
        boolean[] blocked = {false};
        Vec3 land = landing(level, m, target, blocked);
        double len = m.distanceTo(land);
        for (double d = 0.5; d < len; d += 0.6) {
            Vec3 q = m.lerp(land, d / len);
            level.sendParticles(d % 1.8 < 0.6 ? ParticleTypes.END_ROD : SUN, q.x, q.y, q.z, 1, 0.03, 0.03, 0.03, 0);
        }
        if (tick % 2 == 0) {
            if (!blocked[0]) {
                telegraphRing(level, land, BEAM_R, SUN);
            }
            level.sendParticles(ParticleTypes.FLAME, land.x, land.y + 0.1, land.z, 4, 0.4, 0.05, 0.4, 0.02);
            level.sendParticles(ParticleTypes.SMOKE, land.x, land.y + 0.2, land.z, 2, 0.3, 0.1, 0.3, 0.01);
        }
        for (LivingEntity e : victims(level, land, len + 2)) {
            Vec3 body = e.position().add(0, e.getBbHeight() * 0.5, 0);
            boolean onSpot = !blocked[0] && flatDist(e.position(), land) <= BEAM_R + e.getBbWidth() / 2
                    && Math.abs(e.getY() - land.y) < 2.5;
            if (onSpot || segDist(body, m, land) < 0.6 + e.getBbWidth() / 2) {
                burn(level, e, 5.0F, 3.0F);
            }
        }
    }

    // ---- the orrery

    private double[] armOffsets() {
        return phase() == 2 ? new double[] {0, Math.PI * 2 / 3, Math.PI * 4 / 3} : new double[] {0, Math.PI};
    }

    private boolean armLow(int i) {
        return i % 2 == 0;
    }

    /** The arms of light from the sun disc to their planets: drawn up to the gnomon that stops them. */
    private void drawArms(ServerLevel level, boolean moving) {
        Vec3 c = centre();
        double[] off = armOffsets();
        double len = floorR() + 0.5;
        for (int i = 0; i < off.length; i++) {
            double a = armAngle + off[i];
            double h = armLow(i) ? LOW_ARM : HIGH_ARM;
            Vec3 from = c.add(0, h, 0);
            Vec3 tip = c.add(Math.cos(a) * len, h, Math.sin(a) * len);
            BlockHitResult hit = level.clip(new ClipContext(from, tip, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
            double reach = hit.getType() == HitResult.Type.MISS ? len : hit.getLocation().distanceTo(from);
            for (double d = 1.0; d < reach; d += moving ? 0.7 : 1.0) {
                Vec3 q = from.add(Math.cos(a) * d, 0, Math.sin(a) * d);
                level.sendParticles(armLow(i) ? GOLD_DUST : SUN, q.x, q.y, q.z, 1, 0, 0.02, 0, 0);
                if (!armLow(i) && ((int) (d * 10)) % 25 == 0) {
                    level.sendParticles(ParticleTypes.END_ROD, q.x, q.y, q.z, 1, 0, 0, 0, 0);
                }
            }
            Vec3 planet = from.add(Math.cos(a) * reach, 0, Math.sin(a) * reach);
            level.sendParticles(ParticleTypes.WAX_ON, planet.x, planet.y, planet.z, 4, 0.25, 0.25, 0.25, 0);
            if (!moving) {                                  // chevrons: which way the arm will turn
                for (double d = 4; d < reach; d += 4) {
                    double ahead = a + armDir * 0.18;
                    Vec3 q = from.add(Math.cos(ahead) * d, 0, Math.sin(ahead) * d);
                    level.sendParticles(LAPIS, q.x, q.y, q.z, 1, 0, 0, 0, 0);
                }
            }
        }
    }

    private void orreryStep(ServerLevel level, int tick) {
        boolean two = phase() == 2;
        double speed = Math.toRadians(two ? 5.0 : 4.0);
        if (two && tick >= 35 && tick < 45) {             // the reversal is announced: chevrons flip, a chime
            if (tick == 35) {
                level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 1.2F);
            }
            if (tick % 2 == 0) {
                armDir = -armDir;
                drawArms(level, false);
                armDir = -armDir;
            }
        }
        if (two && tick == 45) {
            armDir = -armDir;
            armHits.clear();
        }
        double prev = armAngle;
        armAngle += armDir * speed;
        drawArms(level, true);
        Vec3 c = centre();
        double[] off = armOffsets();
        double len = floorR() + 0.5;
        for (LivingEntity e : victims(level, c, len + 1)) {
            double r = flatDist(e.position(), c);
            if (r > len + e.getBbWidth() / 2 || Math.abs(e.getY() - c.y) > 4.0) {
                continue;
            }
            double phi = Math.atan2(e.getZ() - c.z, e.getX() - c.x);
            double hw = Math.atan2(0.5 + e.getBbWidth() / 2, Math.max(0.5, r));
            for (int i = 0; i < off.length; i++) {
                double a0 = prev + off[i];
                double sweep = armAngle - prev;
                double d0 = Mth.wrapDegrees(Math.toDegrees(phi - a0));
                double s = Math.toDegrees(sweep);
                double hwd = Math.toDegrees(hw);
                boolean crossed = s >= 0 ? d0 >= -hwd && d0 <= s + hwd : d0 <= hwd && d0 >= s - hwd;
                if (!crossed) {
                    continue;
                }
                boolean low = armLow(i);
                double h = low ? LOW_ARM : HIGH_ARM;
                if (low && e.getY() - c.y >= 0.9) {
                    continue;                               // jumped over the low arm
                }
                if (shaded(level, c.add(0, h, 0), new Vec3(e.getX(), c.y + h, e.getZ()))) {
                    continue;                               // in a gnomon's shadow
                }
                if (!armHits.add(e.getUUID() + "/" + i)) {
                    continue;
                }
                if (e.hurtServer(level, damageSources().mobAttack(this), low ? 11.0F : 14.0F)) {
                    Vec3 tan = new Vec3(-Math.sin(phi), 0, Math.cos(phi)).scale(armDir * (low ? 0.6 : 1.0));
                    e.push(tan.x, low ? 0.45 : 0.3, tan.z);
                    e.hurtMarked = true;
                }
                level.sendParticles(ParticleTypes.CRIT, e.getX(), e.getY() + h, e.getZ(), 10, 0.3, 0.3, 0.3, 0.2);
            }
        }
        if (tick % 22 == 0) {
            level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.5F, 0.6F);
        }
    }

    // ---- phase 3: the eclipse and the sun-sigils

    private List<Vec3> sigils() {
        List<Vec3> out = new ArrayList<>();
        Vec3 c = centre();
        double r = Math.min(SIGIL_R, floorR() - 2.5);
        for (int k = 0; k < 6; k++) {
            double a = Math.toRadians(60 * k);
            out.add(new Vec3(c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r));
        }
        return out;
    }

    private Vec3 nearestSigil(Vec3 to, @Nullable Vec3 except) {
        Vec3 best = null;
        for (Vec3 s : sigils()) {
            if (except != null && s.distanceToSqr(except) < 1.0) {
                continue;
            }
            if (best == null || s.distanceToSqr(to) < best.distanceToSqr(to)) {
                best = s;
            }
        }
        return best == null ? centre() : best;
    }

    /** Three sigils: the one nearest the target, then another, then the nearest the target again. */
    private void pickSigils(ServerLevel level) {
        sigilOrder.clear();
        LivingEntity t = quarry(level);
        Vec3 aim = t != null ? t.position() : position();
        Vec3 first = nearestSigil(aim, position());
        sigilOrder.add(first);
        List<Vec3> all = sigils();
        Vec3 second = all.get(getRandom().nextInt(all.size()));
        if (second.distanceToSqr(first) < 1.0) {
            second = all.get((all.indexOf(second) + 3) % all.size());
        }
        sigilOrder.add(second);
        sigilOrder.add(null);                               // chosen when it flares (where the target is then)
        level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void flareSigil(ServerLevel level, Vec3 s, int k) {
        if (k % 2 == 0) {
            telegraphRing(level, s, 1.6, SUN);
            telegraphRing(level, s, 4.5, EMBER);
            column(level, s.add(0, 7, 0), s, 0.7, ParticleTypes.END_ROD);
        }
        if (k == 0) {
            level.playSound(null, s.x, s.y, s.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 3.0F, 1.4F);
        }
    }

    private void sigilStep(ServerLevel level, int tick) {
        int n = Math.min(2, tick / 22);
        int c = tick - n * 22;
        if (n == 2 && sigilOrder.size() > 2 && sigilOrder.get(2) == null) {
            LivingEntity t = quarry(level);
            sigilOrder.set(2, nearestSigil(t != null ? t.position() : position(), sigilOrder.get(1)));
        }
        Vec3 s = sigilOrder.size() > n ? sigilOrder.get(n) : null;
        if (s == null) {
            return;
        }
        if (c == 0) {
            blink(level, s);
            LivingEntity t = quarry(level);
            if (t != null) {
                face(t.position());
            }
        }
        if (c < 8 && c % 2 == 0) {
            telegraphRing(level, s, 4.5, EMBER);
        }
        if (c == 8) {
            for (LivingEntity e : victims(level, s, 5.5)) {
                if (flatDist(e.position(), s) <= 4.5 + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 3.0) {
                    strike(level, e, 13.0F, 1.0, 0.4);
                    e.igniteForSeconds(3.0F);
                }
            }
            for (int i = 0; i < 32; i++) {
                double a = Math.PI * 2 * i / 32;
                level.sendParticles(ParticleTypes.FLAME, s.x + Math.cos(a) * 3.5, s.y + 0.3, s.z + Math.sin(a) * 3.5, 2, 0.3, 0.1, 0.3, 0.05);
            }
            level.sendParticles(ParticleTypes.END_ROD, s.x, s.y + 1, s.z, 40, 1.5, 1.0, 1.5, 0.1);
            level.playSound(null, s.x, s.y, s.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.9F);
            level.playSound(null, s.x, s.y, s.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.5F, 0.5F);
        }
        // the next sigil flares 16 ticks before he appears there
        if (n < 2 && c >= 6) {
            Vec3 next = sigilOrder.size() > n + 1 ? sigilOrder.get(n + 1) : null;
            if (next == null && n + 1 == 2) {
                LivingEntity t = quarry(level);
                next = nearestSigil(t != null ? t.position() : position(), s);
                sigilOrder.set(2, next);
            }
            if (next != null) {
                flareSigil(level, next, c - 6);
            }
        }
    }

    private void callEclipse(ServerLevel level) {
        eclipse = true;
        sigilTimer = 80;
        eclipseSpot = null;
        addEffect(WayfarerBoss.wave(position(), 12, 0.55, 12.0F, ParticleTypes.FLAME));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("solar_hierarch_eclipse"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        darken(level);
        Vec3 c = centre();
        level.sendParticles(INK, c.x, c.y + 4, c.z, 300, floorR() * 0.5, 3.0, floorR() * 0.5, 0.02);
        level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY() + 4, getZ(), 60, 1.0, 1.5, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 1.3F);
    }

    /** The chamber goes dark: Darkness on every player in the arena (refreshed while the eclipse lasts). */
    private void darken(ServerLevel level) {
        for (Player p : fighters(level)) {
            p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 90, 0, false, false), this);
        }
    }

    /** The light that leaks past the moon: a beam straight down the lens that wanders after the target. */
    private void eclipseBeam(ServerLevel level) {
        LivingEntity t = quarry(level);
        if (eclipseSpot == null) {
            eclipseSpot = centre();
        }
        if (t != null) {
            eclipseSpot = clampToArena(chase(eclipseSpot, t.position(), 0.075), 1.0);
        }
        Vec3 s = eclipseSpot;
        if (tickCount % 10 == 0) {
            eclipseTop = Math.max(4, headroom(level, s, 18));
        }
        if (tickCount % 2 == 0) {
            column(level, s.add(0, eclipseTop - 0.5, 0), s, 0.8, ParticleTypes.END_ROD);
            telegraphRing(level, s, 1.4, SUN);
            level.sendParticles(ParticleTypes.FLAME, s.x, s.y + 0.1, s.z, 2, 0.4, 0.05, 0.4, 0.01);
        }
        for (LivingEntity e : victims(level, s, 3.0)) {
            if (flatDist(e.position(), s) <= 1.4 + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 3.0) {
                burn(level, e, 4.0F, 2.0F);
            }
        }
        if (tickCount % 30 == 0) {
            level.playSound(null, s.x, s.y, s.z, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
    }

    private void drawSigils(ServerLevel level) {
        for (Vec3 s : sigils()) {
            telegraphRing(level, s, 1.2, GOLD_DUST);
        }
    }

    // ------------------------------------------------------------------ the gnomons (temporary blocks)

    private static BlockState gnomonLayer(int y) {
        return y == 0 || y == GNOMON_H - 1 ? Blocks.CHISELED_SANDSTONE.defaultBlockState() : Blocks.CUT_SANDSTONE.defaultBlockState();
    }

    /** Six 2x2 sandstone gnomons grind up out of the floor round the sun disc, a layer every 4 ticks. */
    private void raiseGnomons(ServerLevel level) {
        gnomonsRaised = true;
        List<BlockPos> bases = new ArrayList<>();
        Vec3 c = centre();
        double r = Mth.clamp(floorR() * 0.6, 6.0, GNOMON_R);
        for (int k = 0; k < 6; k++) {
            double a = Math.toRadians(30 + 60 * k);
            int bx = Mth.floor(c.x + Math.cos(a) * r - 0.5);
            int bz = Mth.floor(c.z + Math.sin(a) * r - 0.5);
            for (int dx = 0; dx < 2; dx++) {
                for (int dz = 0; dz < 2; dz++) {
                    bases.add(new BlockPos(bx + dx, Mth.floor(c.y), bz + dz));
                }
            }
        }
        level.playSound(null, BlockPos.containing(c), SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 3.0F, 0.4F);
        int[] t = {0};
        addEffect((boss, lvl) -> {
            int k = t[0]++;
            if (k % 4 != 0) {
                return false;
            }
            int layer = k / 4;
            if (layer >= GNOMON_H || !gnomonsRaised) {
                return true;
            }
            for (BlockPos base : bases) {
                BlockPos p = base.above(layer);
                BlockPos below = p.below();
                boolean footing = layer == 0 ? lvl.getBlockState(below).isFaceSturdy(lvl, below, Direction.UP)
                        && lvl.getBlockEntity(below) == null : temps.containsKey(below.asLong());
                if (!footing || !lvl.getBlockState(p).isAir() || lvl.getBlockEntity(p) != null
                        || !lvl.getEntitiesOfClass(LivingEntity.class, new AABB(p)).isEmpty()) {
                    continue;
                }
                temps.putIfAbsent(p.asLong(), lvl.getBlockState(p));
                lvl.setBlock(p, gnomonLayer(layer), 3);
                if (getRandom().nextInt(3) == 0) {
                    lvl.sendParticles(CRUMBS, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 6, 0.4, 0.3, 0.4, 0.05);
                }
            }
            lvl.playSound(null, BlockPos.containing(centre()), SoundEvents.DEEPSLATE_BRICKS_PLACE, SoundSource.HOSTILE, 2.5F, 0.6F);
            return false;
        });
    }

    /** Every placed block goes back, top first. */
    private void restoreAll(ServerLevel level) {
        gnomonsRaised = false;
        if (temps.isEmpty()) {
            return;
        }
        List<Map.Entry<Long, BlockState>> all = new ArrayList<>(temps.entrySet());
        all.sort((a, b) -> Integer.compare(BlockPos.getY(b.getKey()), BlockPos.getY(a.getKey())));
        temps.clear();
        for (Map.Entry<Long, BlockState> e : all) {
            BlockPos p = BlockPos.of(e.getKey());
            level.setBlock(p, e.getValue(), 3);
            if (getRandom().nextInt(4) == 0) {
                level.sendParticles(CRUMBS, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.3, 0.2, 0.3, 0.05);
            }
        }
    }

    // ------------------------------------------------------------------ the mirror: guard and reflection

    private boolean guardUp() {
        if (isStaggered() || tickCount < reelUntil || eclipseGuard > 0) {
            return false;
        }
        BossAttack cur = currentAttack();
        return cur == null || GUARDED.contains(cur.name);
    }

    private boolean frontal(Vec3 from) {
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        return to.lengthSqr() > 1.0E-4 && to.normalize().dot(forward()) >= 0.5;
    }

    private float guardMax() {
        return 50.0F * (1.0F + 0.25F * (scaledPlayers() - 1));
    }

    /** Frontal projectiles are reflected back at whoever shot them while the mirror is up. */
    @Override
    public ProjectileDeflection deflection(Projectile projectile) {
        if (level().isClientSide() || !guardUp() || !frontal(projectile.position())) {
            return super.deflection(projectile);
        }
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.END_ROD, projectile.getX(), projectile.getY(), projectile.getZ(), 6, 0.2, 0.2, 0.2, 0.05);
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 1.5F, 1.4F);
        }
        return (proj, by, random) -> {
            Entity owner = proj.getOwner();
            Vec3 v = proj.getDeltaMovement();
            double sp = Math.max(0.8, v.length());
            Vec3 dir = owner != null ? owner.getEyePosition().subtract(proj.position()) : v.scale(-1);
            dir = dir.lengthSqr() < 1.0E-4 ? v.scale(-1) : dir;
            proj.setDeltaMovement(dir.normalize().scale(sp));
            proj.needsSync = true;
        };
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (eclipseGuard > 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3, getZ(), 6, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        if (tickCount < reelUntil) {
            amount *= 1.3F;
        }
        Vec3 from = source.getSourcePosition();
        if (from != null && source.getEntity() != null && !source.is(DamageTypeTags.BYPASSES_SHIELD) && guardUp()
                && frontal(from)) {
            guardMeter += amount >= 12.0F ? amount * 1.5F : amount;
            if (guardMeter >= guardMax()) {
                chain(level, "reel");                        // the guard breaks: this blow goes through
                return super.hurtServer(level, source, amount);
            }
            blockStreak = tickCount - lastBlockTick > 40 ? 1 : blockStreak + 1;
            lastBlockTick = tickCount;
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.7F + getRandom().nextFloat() * 0.2F);
            Vec3 p = mirrorPos().add(0, -1.8, 0);
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 8, 0.4, 0.5, 0.4, 0.1);
            level.sendParticles(SUN, p.x, p.y, p.z, 6, 0.4, 0.5, 0.4, 0);
            if (blockStreak >= 3 && currentAttack() == null) {
                blockStreak = 0;
                chain(level, "bash");
            }
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    // ------------------------------------------------------------------ ticking, cleanup

    private void endEclipse(ServerLevel level) {
        eclipse = false;
        roarUntil = -1;
        eclipseSpot = null;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("solar_hierarch_eclipse"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("solar_hierarch_wrath"));
        }
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleTemps.isEmpty()) {                       // blocks saved by an unload never outlive it
            for (SavedBlock s : staleTemps) {
                temps.putIfAbsent(s.pos(), s.state());
            }
            staleTemps.clear();
            restoreAll(level);
        }
        if (eclipseGuard > 0) {
            eclipseGuard--;
        }
        if (tickCount - lastBlockTick > 60 && guardMeter > 0) {
            guardMeter = Math.max(0, guardMeter - 0.5F);
        }
        if (tickCount % 200 == 0) {
            burnedAt.values().removeIf(v -> tickCount - v > 200);
        }
        BossAttack current = currentAttack();
        String move = current == null ? "" : current.name;
        if (isNoGravity() && !move.equals("descent")) {
            setNoGravity(false);
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level, new AABB(BlockPos.containing(centre())).inflate(radius + 14, 16, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone) {                                     // the arena emptied (death, flight): the gnomons sink
            restoreAll(level);
            emptyTicks++;
        } else {
            emptyTicks = 0;
        }
        if (phase() == 1 && eclipse) {                     // the fight was reset: the sun is back
            endEclipse(level);
            restoreAll(level);
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (fighting && anyone && !gnomonsRaised) {
            raiseGnomons(level);
        }
        boolean free = fighting && current == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!eclipse && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "eclipse");
            } else if (eclipse && --sigilTimer <= 0) {
                sigilTimer = (int) Math.round(SIGILS_EVERY * cooldownScale());
                chain(level, "sigils");
            }
        }
        if (eclipse && anyone) {
            if (tickCount % 40 == 0) {
                darken(level);
            }
            if (!move.equals("eclipse")) {
                eclipseBeam(level);
            }
            if (tickCount % 10 == 0) {
                drawSigils(level);
            }
        }
        // ambience: the halo's glow, the hum of the sun-engine
        if (tickCount % 3 == 0) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            double hx = getX() + Mth.sin(yaw) * 0.6;
            double hz = getZ() - Mth.cos(yaw) * 0.6;
            level.sendParticles(eclipse ? ParticleTypes.END_ROD : SUN, hx, getY() + 4.6, hz, 1, 0.8, 0.8, 0.8, 0.005);
        }
        if (tickCount % 90 == 0) {
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.7F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("solar_hierarch_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, ParticleTypes.FLAME));
        level.playSound(null, this, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.sendParticles(SUN, getX(), getY() + 4, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        restoreAll(level);
        endEclipse(level);
        setNoGravity(false);
        for (Player p : fighters(level)) {
            p.removeEffect(MobEffects.DARKNESS);
        }
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3, getZ(), 150, 1.2, 2.0, 1.2, 0.2);
        level.sendParticles(SUN, getX(), getY() + 3, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
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
            output.putLong("HierarchCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("HierarchRadius", radius);
        output.putBoolean("HierarchEclipse", eclipse);
        List<SavedBlock> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, BlockState> e : temps.entrySet()) {
            saved.add(new SavedBlock(e.getKey(), e.getValue()));
        }
        output.store("HierarchBlocks", SavedBlock.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("HierarchCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("HierarchRadius", 16);
        eclipse = input.getBooleanOr("HierarchEclipse", false) && phase() == 2;
        staleTemps.clear();
        input.read("HierarchBlocks", SavedBlock.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
        gnomonsRaised = false;
    }

    // ------------------------------------------------------------------ geometry

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Distance from point {@code p} to the segment a-b. */
    private static double segDist(Vec3 p, Vec3 a, Vec3 b) {
        Vec3 ab = b.subtract(a);
        double l2 = ab.lengthSqr();
        double s = l2 < 1.0E-6 ? 0 : Mth.clamp(p.subtract(a).dot(ab) / l2, 0.0, 1.0);
        return p.distanceTo(a.add(ab.scale(s)));
    }

    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }
}
