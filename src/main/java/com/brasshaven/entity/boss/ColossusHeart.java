package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.ColossusHeart.BURST;
import static com.brasshaven.generated.MobAnims.ColossusHeart.CLEAVE;
import static com.brasshaven.generated.MobAnims.ColossusHeart.LUNGE;
import static com.brasshaven.generated.MobAnims.ColossusHeart.MAGNET;
import static com.brasshaven.generated.MobAnims.ColossusHeart.PLATESTORM;
import static com.brasshaven.generated.MobAnims.ColossusHeart.QUAKE;
import static com.brasshaven.generated.MobAnims.ColossusHeart.REFORGE;
import static com.brasshaven.generated.MobAnims.ColossusHeart.RINGS;
import static com.brasshaven.generated.MobAnims.ColossusHeart.RUBBLE;
import static com.brasshaven.generated.MobAnims.ColossusHeart.SHIELDTHROW;
import static com.brasshaven.generated.MobAnims.ColossusHeart.STAGGER;
import static com.brasshaven.generated.MobAnims.ColossusHeart.SWEEP;
import static com.brasshaven.generated.MobAnims.ColossusHeart.VENT;

/**
 * Le Cœur du Colosse (The Colossus's Heart): the still-beating brass engine-heart of the Fallen Colossus. It hangs in
 * an iron cage of ribs inside the statue's helm and has pulled loose bronze plates and rubble round itself into a
 * 6-block knight, every plate held off the next by glowing magnetic tethers, a fragment of the statue's broken
 * greatsword in its right hand and a curved shield-plate torn from the breastplate on its left arm.
 * <p>A deliberately hard fight: 640 health, armour 14, poise 120, hits of 6 to 20. Three phases:
 * <ul>
 *     <li>Phase 1 (the knight): the <b>sweep</b> (a 7.5-block greatsword sweep over 210°), the <b>cleave</b> (the blade
 *     driven into the floor and a crack runs on 16 blocks), the <b>lunge</b> (a long thrusting charge), the
 *     <b>shield-throw</b> (the plate flies out on a loop like a boomerang and comes back: it hits going and coming),
 *     the <b>rubble</b> (chunks torn from the helm's walls hurled at marked spots) and the <b>magnet</b> (the heart drags
 *     players and dropped metal toward it, harder the more metal armour they wear, then slams everything shut).</li>
 *     <li>Phase 2 (a burst at 65%): the armour blows apart into two rings of orbiting plates; the heart is exposed in its
 *     cage (+35% damage taken, armour -8) but four plates circle it (anti-hug) and it fights with the plates: the
 *     <b>rings</b> (it rises to the centre of the helm and the plates sweep two bands round it, then the two other
 *     bands: the safe bands match the chiseled tuff rings of the floor), the <b>plate-storm</b> (plates shot one by one
 *     down marked lines), the <b>vent</b> (steam out of every seam, a ring to jump, rust mites spill out), plus rubble
 *     and magnet.</li>
 *     <li>Phase 3 (at 30%): the <b>reforge</b> (invulnerable 2.6 s): the plates slam back on, 15% bigger, seamed with
 *     amber; the knight's moves return, harder (combos, three cracks, a double loop), and every 10 s the
 *     <b>quake</b>: the sword is driven into the floor and the helm sheds debris on marks round every player
 *     (temporary rubble that stays 8 s).</li>
 * </ul>
 * Every block it places (the quake's rubble) is temporary: removed when it expires, when the fight resets or the arena
 * empties, when it dies or is removed, and on the first tick after a reload. Flying rubble and the shield are falling
 * blocks that never land as blocks.
 */
public class ColossusHeart extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 6.0F;
    private static final EntityDataAccessor<Integer> DATA_FORM = SynchedEntityData.defineId(ColossusHeart.class,
            EntityDataSerializers.INT);
    private static final int WHOLE = 0;
    private static final int OPEN = 1;
    private static final int REFORGED = 2;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_R = 7.5;
    private static final double SWEEP_HALF = 105;
    private static final int QUAKE_EVERY = 200;
    private static final int RUBBLE_LIFE = 160;
    private static final int MAX_RUBBLE_BLOCKS = 80;
    private static final double ORBIT_R = 3.0;
    private static final Set<String> KNIGHT = Set.of("sweep", "cleave", "lunge", "shieldthrow");
    private static final Set<String> PLATES = Set.of("rings", "platestorm", "vent");
    private static final Set<String> SCHEDULED = Set.of("reforge", "quake");
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF0C050, 1.3F);
    private static final DustParticleOptions AMBER = new DustParticleOptions(0xFF9A30, 1.5F);
    private static final DustParticleOptions IRON = new DustParticleOptions(0x8A8A90, 1.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xD04030, 1.4F);
    private static final DustParticleOptions VERD = new DustParticleOptions(0x56A892, 1.3F);

    private @Nullable Vec3 centre;
    private int radius = 13;
    /** Phase 3 has started (the knight re-formed). */
    private boolean reforged;
    private int guard;
    private int roarUntil = -1;
    private int openAt = -1;
    private int quakeTimer = 60;
    private @Nullable List<BossAttack> moves;
    private final Map<String, Integer> lastStart = new HashMap<>();
    private final Map<UUID, Integer> orbitHit = new HashMap<>();
    private final Map<UUID, Integer> ringHit = new HashMap<>();
    private final List<UUID> mites = new ArrayList<>();
    private final List<FallingBlockEntity> flying = new ArrayList<>();
    private final List<Vec3> spots = new ArrayList<>();
    private final List<Vec3> sources = new ArrayList<>();
    private final List<LivingEntity> marked = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable Vec3 glideFrom;
    /** The shield-plate in flight: where it left from, its loop, and the falling block drawn there. */
    private @Nullable Vec3 loopOrigin;
    private Vec3 loopFwd = new Vec3(0, 0, 1);
    private double loopDepth = 10;
    private int loops = 1;
    private @Nullable FallingBlockEntity shield;
    private final Map<UUID, Integer> shieldHit = new HashMap<>();
    /** Quake rubble: every block placed (into air) and the tick it goes. */
    private final Map<BlockPos, Integer> rubbleBlocks = new HashMap<>();
    private boolean staleRubble;

    public ColossusHeart(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 640.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_FORM, WHOLE);
    }

    /** 0 the armoured knight, 1 the burst (plates orbiting, the heart bare), 2 the re-formed knight. */
    @Override
    public int modelVariant() {
        return entityData.get(DATA_FORM);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ColossusHeart.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.YELLOW;
    }

    @Override
    protected int roarAction() {
        return BURST;
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
        return 4.5;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory, geometry

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

    /** Usable floor radius round the seal (the helm's floor is about 14.5 to its wall). */
    private double reach() {
        return Math.max(6.0, Math.min(13.5, radius + 0.5));
    }

    /** True while the armour is off (phase 2, before the reforge). */
    private boolean open() {
        return phase() == 2 && !reforged;
    }

    /** Size factor of the re-formed knight (its reach grows with it). */
    private double big() {
        return reforged ? 1.15 : 1.0;
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

    private static boolean solid(ServerLevel level, Vec3 p) {
        BlockPos b = BlockPos.containing(p);
        return !level.getBlockState(b).getCollisionShape(level, b).isEmpty();
    }

    /** {@code p} pulled inside the helm's floor (at most {@code reach() - margin} from the centre), at floor height. */
    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(2.0, reach() - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 12, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    private void faceToward(Vec3 p) {
        snapFacing((float) (Mth.atan2(p.z - getZ(), p.x - getX()) * (180.0 / Math.PI)) - 90.0F);
    }

    private static BlockParticleOption block(BlockState state) {
        return new BlockParticleOption(ParticleTypes.BLOCK, state);
    }

    private static BlockState plateState() {
        return Blocks.COPPER_BLOCK.weathering().weathered().defaultBlockState();
    }

    private static BlockState verdState() {
        return Blocks.COPPER_BLOCK.weathering().oxidized().defaultBlockState();
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        moves = out;
        // sweep: the greatsword drawn back over the right shoulder (0.9 s, the arc drawn in gold), swept round over
        // 210 degrees out to 7.5: 16. Phase 3: 45% chains into the cleave
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(18, 3, 14).range(0, 8.5).cooldown(60).weight(12)
                .start((b, level, t, tick) -> gate(level, t, "sweep"))
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof ColossusHeart h) {
                        b.telegraphArc(level, SWEEP_R * h.big(), SWEEP_HALF, GOLD);
                        b.telegraphArc(level, SWEEP_R * h.big() * 0.55, SWEEP_HALF, GOLD);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double r = SWEEP_R * (b instanceof ColossusHeart h ? h.big() : 1.0);
                    b.hitArc(level, r, SWEEP_HALF, 16.0F, 1.0);
                    for (double a = -SWEEP_HALF; a <= SWEEP_HALF; a += 15) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(r * 0.7));
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 1, 0, 0, 0, 0);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h && h.reforged && t != null && b.distanceTo(t) < 9 && b.getRandom().nextFloat() < 0.45F) {
                        b.chain(level, "cleave");
                    }
                })
                .build());
        // cleave: the sword raised high in both hands (1.1 s, a ring 4 ahead and the crack's line in gold dots), driven
        // into the floor: 20 in r 2.8, then a crack runs on to 16 blocks (13 and thrown up). Phase 3: three cracks
        out.add(BossAttack.of("cleave").anim(CLEAVE).timing(22, 4, 18).range(0, 12).cooldown(80).weight(10)
                .start((b, level, t, tick) -> gate(level, t, "cleave"))
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof ColossusHeart h)) {
                        return;
                    }
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(4.0 * h.big()), 2.8, GOLD);
                    }
                    if (tick % 4 == 0) {
                        for (double fan : h.reforged ? new double[] {-22, 0, 22} : new double[] {0}) {
                            Vec3 dir = rotate(b.forward(), fan);
                            for (double d = 6; d <= 16; d += 1.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(GOLD, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                            }
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof ColossusHeart h)) {
                        return;
                    }
                    Vec3 at = b.ahead(4.0 * h.big());
                    b.hitCircle(level, at, 2.8, 20.0F, 0.8, 0.4);
                    level.sendParticles(block(Blocks.TUFF.defaultBlockState()), at.x, at.y + 0.3, at.z, 50, 1.2, 0.3, 1.2, 0.2);
                    level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 2, 0.5, 0.2, 0.5, 0);
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    for (double fan : h.reforged ? new double[] {-22, 0, 22} : new double[] {0}) {
                        b.addEffect(crack(at, rotate(b.forward(), fan), 12.0, 13.0F));
                    }
                })
                .build());
        // lunge: the sword drawn back at the hip (0.8 s, its line drawn 12 ahead), then a lunging thrust that carries
        // it 9 blocks: 15 once and a heavy push. Phase 3: 40% chains into the sweep
        out.add(BossAttack.of("lunge").anim(LUNGE).timing(16, 10, 16).range(5, 15).cooldown(90).weight(9)
                .start((b, level, t, tick) -> {
                    if (gate(level, t, "lunge")) {
                        struck.clear();
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 12; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(GOLD, p.x, p.y + 0.15, p.z, 1, 0.2, 0, 0.2, 0);
                        }
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick < 8) {
                        Vec3 f = b.forward().scale(1.15);
                        b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                        b.hurtMarked = true;
                    } else {
                        b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    }
                    Vec3 tip = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 1.4, tip.z, 4, 0.3, 0.3, 0.3, 0.1);
                    for (LivingEntity e : b.victims(level, tip, 2.6)) {
                        if (flatDist(e.position(), tip) <= 2.4 && struck.add(e.getUUID())) {
                            b.strike(level, e, 15.0F, 1.4, 0.3);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h && h.reforged && t != null && b.distanceTo(t) < 8 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // shieldthrow: the shield-plate drawn across the body (0.9 s, its loop drawn in verdigris), flung out like a
        // discus: it flies a loop out to the target and back (1.8 s), 12 each time it passes through someone. Phase 3:
        // two loops, the second mirrored, faster
        out.add(BossAttack.of("shieldthrow").anim(SHIELDTHROW).timing(18, 40, 12).range(4, 20).cooldown(140).weight(8)
                .start((b, level, t, tick) -> gate(level, t, "shieldthrow"))
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof ColossusHeart h)) {
                        return;
                    }
                    h.planLoop(level, t);
                    if (tick % 3 == 0) {
                        for (int i = 1; i < 24; i++) {
                            Vec3 p = h.loopPoint(level, i / 24.0);
                            level.sendParticles(VERD, p.x, b.getY() + 0.2, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_DAMAGE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.throwShield(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.flyShield(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.catchShield(level);
                    }
                })
                .build());
        // rubble: arms raised, the heart flaring (1.0 s): chunks tear out of the helm's wall (dust where they come
        // from) over rings that follow their players for 0.6 s and lock; then the chunks are hurled one after another
        // and smash down on the rings: 13 in r 2.5, thrown up
        out.add(BossAttack.of("rubble").anim(RUBBLE).timing(20, 24, 14).range(0, 30).cooldown(110).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.noteStart("rubble");
                        h.pickRubble(level, t);
                    }
                    level.playSound(null, b, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 3.0F, 0.7F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof ColossusHeart h)) {
                        return;
                    }
                    if (tick < 12) {
                        for (int i = 0; i < h.marked.size() && i < h.spots.size(); i++) {
                            LivingEntity e = h.marked.get(i);
                            if (e.isAlive()) {
                                h.spots.set(i, h.clampToArena(e.position(), 1.0));
                            }
                        }
                    }
                    if (tick % 2 == 0) {
                        for (int i = 0; i < h.spots.size(); i++) {
                            b.telegraphRing(level, h.spots.get(i), 2.5, tick < 12 ? GOLD : RED);
                            Vec3 s = h.sources.get(i);
                            level.sendParticles(block(Blocks.TUFF.defaultBlockState()), s.x, s.y, s.z, 4, 0.5, 0.5, 0.5, 0.05);
                        }
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h && tick % 3 == 0 && tick / 3 < h.spots.size()) {
                        int i = tick / 3;
                        b.addEffect(h.boulder(level, h.sources.get(i), h.spots.get(i), 14, 13.0F));
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .build());
        // magnet: arms thrown wide, the heart swelling (0.7 s, iron dust drawn in from all round): for 1.4 s every
        // player within 16 (18 in phase 3) and every dropped item is dragged toward it, harder for each piece of metal
        // armour worn; at 2.2 s everything is slammed shut (red ring for the last half second): 14 within 4.5 (16
        // within 5 when the plates do it)
        out.add(BossAttack.of("magnet").anim(MAGNET).timing(14, 34, 14).range(0, 16).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.noteStart("magnet");
                    }
                    level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        double r = 16 - tick;
                        b.telegraphRing(level, b.position(), Math.max(2, r), IRON);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.magnetTick(level, tick);
                    }
                })
                .build());

        // ---------------------------------------------------------------- the burst (phase 2, armour off)
        // rings: the heart rises and glides to the centre of the helm (1.0 s, the first two bands drawn in red); the
        // plates sweep bands 2-5.5 and 8.5-11.5 for 1.75 s (a 70-degree gap turns in each), then (0.25 s of amber
        // warning) bands 0-2, 5.5-8.5 and 11.5+ for 1.5 s: 10 per pass. The safe bands of the first sweep are the
        // chiseled tuff rings of the floor
        out.add(BossAttack.of("rings").anim(RINGS).phaseTwo().timing(20, 70, 14).range(0, 30).cooldown(240).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h && h.gate(level, t, "rings")) {
                        h.glideFrom = b.position();
                        h.ringHit.clear();
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof ColossusHeart h)) {
                        return;
                    }
                    if (h.glideFrom != null) {
                        Vec3 to = h.centre();
                        Vec3 p = h.glideFrom.lerp(to, Math.min(1.0, (tick + 1) / 16.0));
                        b.teleportTo(p.x, to.y, p.z);
                    }
                    if (tick % 3 == 0) {
                        h.drawBands(level, false, RED);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.ringsTick(level, tick);
                    }
                })
                .build());
        // platestorm: the plates gather in a crown over the heart (0.8 s); six plates (eight in phase 3 of the burst's
        // co-op scaling) fly out a quarter second apart, each down a line drawn 0.4 s before toward a player: 9 to the
        // first creature on the line
        out.add(BossAttack.of("platestorm").anim(PLATESTORM).phaseTwo().timing(16, 30, 14).range(0, 26).cooldown(120)
                .weight(10).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.gate(level, t, "platestorm");
                    }
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(block(plateState()), b.getX(), b.getY() + 5.0, b.getZ(), 3, 1.2, 0.3, 1.2, 0.02);
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.ANVIL_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h && tick % 5 == 0) {
                        h.firePlate(level, tick / 5);
                    }
                })
                .build());
        // vent: the heart contracts (0.7 s, steam hissing from the seams): it bursts: 14 within 4 and thrown back, a
        // ring of steam to jump (8, out to 9), and rust mites spill out of the cracks (2, more in co-op, at most 4)
        out.add(BossAttack.of("vent").anim(VENT).phaseTwo().timing(14, 4, 14).range(0, 6).cooldown(110).weight(10)
                .start((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.gate(level, t, "vent");
                    }
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 4.0, b.getZ(), 3, 0.8, 0.6, 0.8, 0.02);
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, AMBER);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.0, 14.0F, 1.4, 0.5);
                    b.addEffect(WayfarerBoss.wave(b.position(), 9.0, 0.5, 8.0F, ParticleTypes.CLOUD));
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 3.5, b.getZ(), 40, 1.5, 1.0, 1.5, 0.08);
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 3.5, b.getZ(), 40, 1.5, 1.0, 1.5, 0.2);
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
                    if (b instanceof ColossusHeart h) {
                        h.spillMites(level);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // reforge: the rings close in on the heart (1.5 s, invulnerable, a spiral of plates): the plates slam back on,
        // bigger: a shock round it (12 within 5) and a ring to jump (12, out to 14)
        out.add(BossAttack.of("reforge").anim(REFORGE).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 54;
                    level.playSound(null, b, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    double r = 10.0 - tick * 0.3;
                    for (int k = 0; k < 6; k++) {
                        double a = tick * 0.35 + k * Math.PI / 3;
                        level.sendParticles(block(plateState()), b.getX() + Math.cos(a) * r, b.getY() + 2.5 + k * 0.4,
                                b.getZ() + Math.sin(a) * r, 2, 0.2, 0.2, 0.2, 0);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.0, AMBER);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.reforge(level);
                    }
                })
                .build());
        // quake: the sword lifted point-down (0.9 s, a ring at its feet), driven into the floor of the helm: 14 within
        // 2.5 ahead; the helm sheds debris: three marks round every player (one on them, two near) and strays, the
        // chunks fall a beat later: 14 in r 1.8 and slowed, each leaves a heap of rubble for 8 s
        out.add(BossAttack.of("quake").anim(QUAKE).phaseTwo().timing(18, 30, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 2.5, GOLD);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h) {
                        h.quake(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof ColossusHeart h && tick % 2 == 0 && tick / 2 < h.spots.size()) {
                        int i = tick / 2;
                        b.addEffect(h.debris(level, h.spots.get(i), 14.0F));
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ form gating

    private static boolean allowedIn(boolean open, String name) {
        if (SCHEDULED.contains(name)) {
            return false;
        }
        return open ? !KNIGHT.contains(name) : !PLATES.contains(name);
    }

    private void noteStart(String name) {
        lastStart.put(name, tickCount);
    }

    /**
     * The picker knows two phases, the heart three forms: a knight move rolled while the armour is off (or a plate move
     * rolled in armour) hands over to a move of the right form. Returns true when the move goes ahead.
     */
    private boolean gate(ServerLevel level, @Nullable LivingEntity t, String name) {
        if (allowedIn(open(), name)) {
            noteStart(name);
            return true;
        }
        redirect(level, t);
        return false;
    }

    private void redirect(ServerLevel level, @Nullable LivingEntity t) {
        if (moves == null) {
            return;
        }
        double dist = t != null ? distanceTo(t) : 6.0;
        boolean open = open();
        List<BossAttack> ok = new ArrayList<>();
        int total = 0;
        for (BossAttack a : moves) {
            if (a.weight <= 0 || !a.allowedIn(phase()) || !allowedIn(open, a.name) || dist < a.minRange || dist > a.maxRange) {
                continue;
            }
            Integer last = lastStart.get(a.name);
            if (last != null && tickCount - last < a.cooldown * cooldownScale()) {
                continue;
            }
            ok.add(a);
            total += a.weight;
        }
        String pick = open ? "platestorm" : "rubble";
        if (total > 0) {
            int roll = random.nextInt(total);
            for (BossAttack a : ok) {
                roll -= a.weight;
                if (roll < 0) {
                    pick = a.name;
                    break;
                }
            }
        }
        chain(level, pick);
    }

    // ------------------------------------------------------------------ move helpers

    /** A crack running along the floor from {@code from} in {@code dir}, 1 block a tick; it stops at a wall. */
    private Effect crack(Vec3 from, Vec3 dir, double length, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] d = {1.0};
        return (boss, level) -> {
            d[0] += 1.0;
            Vec3 p = from.add(dir.scale(d[0]));
            if (solid(level, p.add(0, 0.5, 0))) {
                return true;
            }
            level.sendParticles(block(Blocks.TUFF.defaultBlockState()), p.x, p.y + 0.2, p.z, 6, 0.3, 0.1, 0.3, 0.1);
            level.sendParticles(GOLD, p.x, p.y + 0.3, p.z, 2, 0.2, 0.2, 0.2, 0);
            for (LivingEntity e : boss.victims(level, p, 1.6)) {
                if (flatDist(e.position(), p) <= 1.2 && Math.abs(e.getY() - p.y) < 1.5 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.3, 0.6);
                }
            }
            if ((int) d[0] % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.TUFF_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
            return d[0] >= length;
        };
    }

    // ---- the shield-plate boomerang

    private void planLoop(ServerLevel level, @Nullable LivingEntity t) {
        loopOrigin = position();
        loopFwd = forward();
        double want = t != null ? flatDist(t.position(), position()) + 3.0 : 10.0;
        loopDepth = Mth.clamp(want, 8.0, reforged ? 17.0 : 15.0);
        loops = reforged ? 2 : 1;
    }

    /** Point of the loop at {@code u} in [0, 1] (each loop: out on the right, back on the left; the second mirrored). */
    private Vec3 loopPoint(ServerLevel level, double u) {
        Vec3 o = loopOrigin != null ? loopOrigin : position();
        double per = 1.0 / loops;
        int k = Math.min(loops - 1, (int) (u / per));
        double v = (u - k * per) / per;
        double side = (k % 2 == 0 ? 1 : -1) * 4.0;
        Vec3 right = new Vec3(-loopFwd.z, 0, loopFwd.x);
        Vec3 p = o.add(loopFwd.scale(loopDepth * Math.sin(Math.PI * v))).add(right.scale(side * Math.sin(2 * Math.PI * v)));
        return clampToArena(p, 1.0).add(0, o.y - centre().y, 0);
    }

    private void throwShield(ServerLevel level) {
        shieldHit.clear();
        Vec3 o = loopOrigin != null ? loopOrigin : position();
        Vec3 start = o.add(loopFwd.scale(1.5)).add(0, 1.2, 0);
        shield = spawnBlock(level, start, Blocks.COPPER_TRAPDOOR.waxed().weathered().defaultBlockState(), true);
        level.playSound(null, this, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    private void flyShield(ServerLevel level, int tick) {
        int span = 36;
        if (tick >= span) {
            return;
        }
        double u = (tick + 1) / (double) span;
        Vec3 p = loopPoint(level, u).add(0, 1.2, 0);
        if (shield != null && shield.isAlive()) {
            Vec3 step = p.subtract(shield.position());
            if (step.length() > 2.5) {
                shield.setPos(p.x, p.y, p.z);
                step = Vec3.ZERO;
            }
            shield.setDeltaMovement(step);
            shield.hurtMarked = true;
        }
        level.sendParticles(block(verdState()), p.x, p.y + 0.4, p.z, 3, 0.4, 0.2, 0.4, 0.05);
        level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.4, p.z, 2, 0.3, 0.2, 0.3, 0.05);
        if (tick % 4 == 0) {
            level.playSound(null, p.x, p.y, p.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.0F, 1.4F);
        }
        for (LivingEntity e : victims(level, p, 2.2)) {
            Integer last = shieldHit.get(e.getUUID());
            if (flatDist(e.position(), p) <= 1.7 && Math.abs(e.getY() + 0.9 - p.y) < 1.9
                    && (last == null || tickCount - last > 10)) {
                shieldHit.put(e.getUUID(), tickCount);
                if (e.hurtServer(level, damageSources().mobAttack(this), 12.0F)) {
                    Vec3 push = e.position().subtract(p).multiply(1, 0, 1);
                    push = push.lengthSqr() < 1.0E-4 ? loopFwd : push.normalize();
                    e.push(push.x * 0.9, 0.3, push.z * 0.9);
                    e.hurtMarked = true;
                    level.playSound(null, e, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 1.2F);
                }
            }
        }
    }

    private void catchShield(ServerLevel level) {
        if (shield != null) {
            shield.discard();
            shield = null;
        }
        level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 1.5F, 0.7F);
    }

    /**
     * A falling block for show (the shield, a rubble chunk): put into an air cell for an instant and lifted out at once,
     * so the world is never changed; it never drops nor lands as a block.
     */
    private @Nullable FallingBlockEntity spawnBlock(ServerLevel level, Vec3 at, BlockState state, boolean weightless) {
        BlockPos cell = BlockPos.containing(at);
        if (!level.getBlockState(cell).isAir() || !level.isLoaded(cell)) {
            return null;
        }
        level.setBlock(cell, state, 2);
        FallingBlockEntity fb = FallingBlockEntity.fall(level, cell, state);
        fb.dropItem = false;
        fb.disableDrop();
        fb.setNoGravity(weightless);
        flying.add(fb);
        return fb;
    }

    // ---- rubble torn from the walls

    private void pickRubble(ServerLevel level, @Nullable LivingEntity t) {
        marked.clear();
        spots.clear();
        sources.clear();
        for (Player p : fighters(level)) {
            if (marked.size() < 4) {
                marked.add(p);
                spots.add(clampToArena(p.position(), 1.0));
            }
        }
        if (marked.isEmpty() && t != null) {
            marked.add(t);
            spots.add(clampToArena(t.position(), 1.0));
        }
        Vec3 anchor = t != null ? t.position() : position();
        int extra = phase() == 2 ? 3 : 2;
        for (int i = 0; i < extra; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 3.0 + random.nextDouble() * 4.0;
            spots.add(clampToArena(anchor.add(Math.cos(a) * r, 0, Math.sin(a) * r), 1.5));
        }
        for (Vec3 s : spots) {
            sources.add(wallPoint(level, s));
        }
    }

    /** A point on the inside of the helm's wall, behind {@code spot} as seen from the centre, 4 blocks up. */
    private Vec3 wallPoint(ServerLevel level, Vec3 spot) {
        Vec3 c = centre();
        Vec3 dir = spot.subtract(c).multiply(1, 0, 1);
        dir = dir.lengthSqr() < 0.01 ? rotate(new Vec3(1, 0, 0), random.nextInt(360)) : dir.normalize();
        Vec3 last = c.add(dir.scale(6)).add(0, 4.5, 0);
        for (double d = 6; d <= 19; d += 0.5) {
            Vec3 p = c.add(dir.scale(d)).add(0, 4.5, 0);
            if (solid(level, p)) {
                return last;
            }
            last = p;
        }
        return c.add(dir.scale(12)).add(0, 6, 0);
    }

    /**
     * A chunk of the wall: a real falling block launched on a ballistic arc from {@code from} to {@code to} in about
     * {@code flight} ticks, removed just before touching the ground; the impact hurts everything within 2.5.
     */
    private Effect boulder(ServerLevel level, Vec3 from, Vec3 to, int flight, float damage) {
        BlockState state = random.nextBoolean() ? Blocks.TUFF.defaultBlockState() : Blocks.COBBLESTONE.defaultBlockState();
        FallingBlockEntity rock = spawnBlock(level, from, state, false);
        if (rock != null) {
            double drag = (1 - Math.pow(0.98, flight)) / 0.02;
            rock.setDeltaMovement((to.x - rock.getX()) / drag, solveLift(rock.getY(), to.y, flight), (to.z - rock.getZ()) / drag);
            rock.hurtMarked = true;
        }
        level.sendParticles(block(state), from.x, from.y, from.z, 20, 0.6, 0.6, 0.6, 0.1);
        Set<UUID> none = new HashSet<>();
        int[] t = {0};
        return (boss, lvl) -> {
            t[0]++;
            if (t[0] % 2 == 0) {
                boss.telegraphRing(lvl, to, 2.5, RED);
            }
            boolean done = t[0] >= flight + 4;
            Vec3 at = to;
            if (rock != null && rock.isAlive()) {
                Vec3 v = rock.getDeltaMovement();
                if (v.y < 0 && (rock.getY() + v.y - 0.04 <= to.y + 0.4 || rock.onGround())) {
                    at = rock.position();
                    rock.discard();
                    done = true;
                }
            } else if (rock != null) {
                done = true;
            }
            if (!done) {
                return false;
            }
            Vec3 c = new Vec3(at.x, to.y, at.z);
            for (LivingEntity e : boss.victims(lvl, c, 3.0)) {
                if (flatDist(e.position(), c) <= 2.5 && none.add(e.getUUID())) {
                    boss.strike(lvl, e, damage, 0.8, 0.6);
                }
            }
            lvl.sendParticles(block(state), c.x, c.y + 0.4, c.z, 40, 1.0, 0.3, 1.0, 0.2);
            lvl.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 1, 0.3, 0.1, 0.3, 0);
            lvl.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.6F, 0.7F);
            return true;
        };
    }

    private static double solveLift(double y0, double y1, int n) {
        double lo = -1.0;
        double hi = 3.0;
        for (int it = 0; it < 40; it++) {
            double mid = (lo + hi) / 2;
            double y = y0;
            double v = mid;
            for (int k = 0; k < n; k++) {
                v -= 0.04;
                y += v;
                v *= 0.98;
            }
            if (y < y1) {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        return (lo + hi) / 2;
    }

    // ---- the magnet

    /** Pieces of metal armour (iron, chain, gold, copper, netherite, brass...) a creature wears: each makes the pull worse. */
    private static int metal(LivingEntity e) {
        int n = 0;
        for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
            ItemStack s = e.getItemBySlot(slot);
            if (s.isEmpty()) {
                continue;
            }
            String id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
            if (id.contains("iron") || id.contains("chain") || id.contains("gold") || id.contains("copper")
                    || id.contains("netherite") || id.contains("brass") || id.contains("steel") || id.contains("mithril")) {
                n++;
            }
        }
        return n;
    }

    private void magnetTick(ServerLevel level, int tick) {
        double range = reforged ? 18.0 : 16.0;
        double strength = reforged ? 1.2 : 1.0;
        Vec3 me = position();
        if (tick < 28) {
            for (Player p : fighters(level)) {
                Vec3 d = me.subtract(p.position()).multiply(1, 0, 1);
                double len = d.length();
                if (len > range || len < 2.5) {
                    continue;
                }
                int m = metal(p);
                double pull = (0.07 + 0.022 * m) * strength;
                double cap = (0.42 + 0.07 * m) * strength;
                Vec3 v = p.getDeltaMovement().add(d.normalize().scale(pull));
                Vec3 flat = new Vec3(v.x, 0, v.z);
                double toward = flat.dot(d.normalize());
                if (toward > cap) {
                    flat = flat.subtract(d.normalize().scale(toward - cap));
                }
                p.setDeltaMovement(flat.x, v.y, flat.z);
                p.hurtMarked = true;
                if (tick % 3 == 0) {
                    Vec3 mid = p.position().add(0, 1.0, 0).lerp(me.add(0, 3.5, 0), 0.5);
                    level.sendParticles(m > 0 ? RED : IRON, mid.x, mid.y, mid.z, 2, 0.3, 0.3, 0.3, 0.0);
                }
            }
            for (ItemEntity it : level.getEntitiesOfClass(ItemEntity.class, getBoundingBox().inflate(range, 4, range))) {
                Vec3 d = me.add(0, 1, 0).subtract(it.position());
                if (d.length() > 1.5) {
                    it.setDeltaMovement(d.normalize().scale(0.35));
                    it.hurtMarked = true;
                }
            }
            if (tick % 2 == 0) {
                for (int k = 0; k < 10; k++) {
                    double a = random.nextDouble() * Math.PI * 2;
                    double r = 3 + random.nextDouble() * (range - 3);
                    level.sendParticles(IRON, me.x + Math.cos(a) * r, me.y + 0.5 + random.nextDouble() * 3, me.z + Math.sin(a) * r,
                            0, -Math.cos(a), 0, -Math.sin(a), 0.6);
                }
            }
            if (tick >= 18 && tick % 2 == 0) {
                telegraphRing(level, me, open() ? 5.0 : 4.5, RED);
            }
            if (tick % 8 == 0) {
                level.playSound(null, this, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 3.0F, 0.9F);
            }
        } else if (tick == 30) {
            boolean plates = open();
            double r = plates ? 5.0 : 4.5;
            hitCircle(level, me, r, plates ? 16.0F : 14.0F, 1.4, 0.4);
            level.sendParticles(block(plateState()), me.x, me.y + 2.0, me.z, 60, r * 0.4, 1.0, r * 0.4, 0.3);
            level.sendParticles(ParticleTypes.EXPLOSION, me.x, me.y + 2.0, me.z, 3, 1.0, 0.6, 1.0, 0);
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.5F);
            level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.7F);
        }
    }

    // ---- the rings (phase 2)

    /** Dangerous radial bands of the sweep: first half, or second half. */
    private static double[][] bands(boolean second) {
        return second ? new double[][] {{0.0, 2.0}, {5.5, 8.5}, {11.5, 15.5}} : new double[][] {{2.0, 5.5}, {8.5, 11.5}};
    }

    private void drawBands(ServerLevel level, boolean second, ParticleOptions p) {
        Vec3 c = position();
        for (double[] b : bands(second)) {
            for (double r : b) {
                if (r > 0.5) {
                    telegraphRing(level, c, Math.min(r, reach() + 0.5), p);
                }
            }
        }
    }

    private void ringsTick(ServerLevel level, int tick) {
        boolean second = tick >= 40;
        boolean live = tick < 35 || tick >= 40;
        if (tick >= 25 && tick < 40 && tick % 3 == 0) {
            drawBands(level, true, AMBER);                       // the next bands, warned
        }
        if (tick == 35) {
            level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
        if (!live) {
            return;
        }
        Vec3 c = position();
        double gapCentre = Math.toRadians(tick * 6.0);
        double gapHalf = Math.toRadians(35);
        // the plates: particles over every band but the turning gap
        if (tick % 2 == 0) {
            for (double[] b : bands(second)) {
                double r = Math.min((b[0] + b[1]) / 2, reach());
                int n = Math.max(8, (int) (r * 5));
                for (int i = 0; i < n; i++) {
                    double a = Math.PI * 2 * i / n + (second ? -1 : 1) * tick * 0.12;
                    double off = Math.abs(Mth.wrapDegrees(Math.toDegrees(a - gapCentre)));
                    if (Math.toRadians(off) < gapHalf) {
                        continue;
                    }
                    level.sendParticles(block(plateState()), c.x + Math.cos(a) * r, c.y + 0.9, c.z + Math.sin(a) * r, 1, 0.2, 0.3, 0.2, 0);
                }
                for (int s = -1; s <= 1; s += 2) {                // gold at the edges of the gap
                    double a = gapCentre + s * gapHalf;
                    level.sendParticles(GOLD, c.x + Math.cos(a) * r, c.y + 1.2, c.z + Math.sin(a) * r, 2, 0.1, 0.4, 0.1, 0);
                }
            }
        }
        if (tick % 10 == 0) {
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
        for (LivingEntity e : victims(level, c, 16.0)) {
            double d = flatDist(e.position(), c);
            boolean in = false;
            for (double[] b : bands(second)) {
                if (d >= b[0] && d < b[1]) {
                    in = true;
                }
            }
            if (!in || Math.abs(e.getY() - c.y) > 3.0) {
                continue;
            }
            double ang = Math.atan2(e.getZ() - c.z, e.getX() - c.x);
            double off = Math.abs(Mth.wrapDegrees(Math.toDegrees(ang - gapCentre)));
            if (Math.toRadians(off) < gapHalf) {
                continue;                                          // standing in the gap
            }
            Integer last = ringHit.get(e.getUUID());
            if (last == null || tickCount - last >= 12) {
                ringHit.put(e.getUUID(), tickCount);
                strike(level, e, 10.0F, 0.5, 0.3);
            }
        }
    }

    // ---- the plate-storm (phase 2)

    private void firePlate(ServerLevel level, int shot) {
        List<Player> ps = fighters(level);
        LivingEntity aim = !ps.isEmpty() ? ps.get(shot % ps.size()) : getTarget();
        if (aim == null || !aim.isAlive()) {
            return;
        }
        Vec3 from = position().add(0, 4.5, 0);
        Vec3 lock = aim.position().add(0, 1.0, 0);
        Vec3 dir = lock.subtract(from);
        if (dir.lengthSqr() < 1.0E-3) {
            return;
        }
        Vec3 d = dir.normalize();
        addEffect(plateShot(from, d, 22.0, 8, 9.0F));
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DAMAGE, SoundSource.HOSTILE, 1.5F, 1.2F);
    }

    /** A plate: its line drawn for {@code warn} ticks, then it flies 1.6 blocks a tick and hits the first creature. */
    private static Effect plateShot(Vec3 from, Vec3 dir, double max, int warn, float damage) {
        int[] t = {0};
        double[] d = {0.0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 2 == 0) {
                    for (double s = 1; s <= max; s += 1.5) {
                        Vec3 p = from.add(dir.scale(s));
                        if (solid(level, p)) {
                            break;
                        }
                        level.sendParticles(VERD, p.x, p.y, p.z, 1, 0, 0, 0, 0);
                    }
                }
                return false;
            }
            for (int sub = 0; sub < 2; sub++) {
                d[0] += 0.8;
                Vec3 p = from.add(dir.scale(d[0]));
                if (d[0] > max || solid(level, p)) {
                    level.sendParticles(block(plateState()), p.x, p.y, p.z, 12, 0.3, 0.3, 0.3, 0.1);
                    return true;
                }
                level.sendParticles(block(plateState()), p.x, p.y, p.z, 2, 0.15, 0.15, 0.15, 0);
                level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0);
                for (LivingEntity e : boss.victims(level, p, 1.5)) {
                    if (e.getBoundingBox().inflate(0.5).contains(p)) {
                        boss.strike(level, e, damage, 0.6, 0.2);
                        level.playSound(null, e, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 1.5F);
                        return true;
                    }
                }
            }
            return false;
        };
    }

    // ---- rust mites (phase 2, from the vent)

    private void spillMites(ServerLevel level) {
        mites.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        int cap = scaledCount(4);
        int n = Math.min(scaledCount(2), cap - mites.size());
        for (int i = 0; i < n; i++) {
            Mob mite = ModEntities.RUST_MITE.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mite == null) {
                continue;
            }
            double a = random.nextDouble() * Math.PI * 2;
            mite.snapTo(getX() + Math.cos(a) * 1.5, getY() + 2.5, getZ() + Math.sin(a) * 1.5, (float) Math.toDegrees(a), 0);
            mite.addTag(MINION_TAG);
            mite.setTarget(getTarget());
            mite.setDeltaMovement(Math.cos(a) * 0.4, 0.3, Math.sin(a) * 0.4);
            level.addFreshEntity(mite);
            mites.add(mite.getUUID());
            level.sendParticles(new DustParticleOptions(0xA4502A, 1.2F), mite.getX(), mite.getY(), mite.getZ(), 10, 0.2, 0.2, 0.2, 0.02);
        }
    }

    private void discardMites(ServerLevel level) {
        for (UUID id : mites) {
            var e = level.getEntity(id);
            if (e != null && e.isAlive()) {
                level.sendParticles(new DustParticleOptions(0xA4502A, 1.0F), e.getX(), e.getY() + 0.15, e.getZ(), 8, 0.15, 0.1, 0.15, 0);
                e.discard();
            }
        }
        mites.clear();
    }

    // ---- the orbit (phase 2, passive)

    /** Four plates circle the bare heart at 3 blocks: whoever hugs it is clipped as they pass (6, at most every 0.75 s). */
    private void orbitTick(ServerLevel level) {
        Vec3 c = position();
        double base = Math.toRadians(tickCount * 6.0);
        for (int k = 0; k < 4; k++) {
            double a = base + k * Math.PI / 2;
            double x = c.x + Math.cos(a) * ORBIT_R;
            double z = c.z + Math.sin(a) * ORBIT_R;
            if (tickCount % 2 == 0) {
                level.sendParticles(block(plateState()), x, c.y + 3.6, z, 1, 0.15, 0.4, 0.15, 0);
            }
        }
        for (LivingEntity e : victims(level, c, 4.5)) {
            double d = flatDist(e.position(), c);
            if (d < 1.8 || d > 4.2 || Math.abs(e.getY() - c.y) > 5.0) {
                continue;
            }
            double ang = Math.atan2(e.getZ() - c.z, e.getX() - c.x);
            for (int k = 0; k < 4; k++) {
                double off = Math.abs(Mth.wrapDegrees(Math.toDegrees(ang - base - k * Math.PI / 2)));
                Integer last = orbitHit.get(e.getUUID());
                if (off < 22 && (last == null || tickCount - last >= 15)) {
                    orbitHit.put(e.getUUID(), tickCount);
                    strike(level, e, 6.0F, 0.7, 0.2);
                    level.playSound(null, e, SoundEvents.ANVIL_HIT, SoundSource.HOSTILE, 0.8F, 1.3F);
                    break;
                }
            }
        }
    }

    // ---- phase 3

    private void reforge(ServerLevel level) {
        reforged = true;
        entityData.set(DATA_FORM, REFORGED);
        quakeTimer = 60;
        var armor = getAttribute(Attributes.ARMOR);
        if (armor != null) {
            armor.removeModifier(com.brasshaven.Brasshaven.id("colossus_heart_open"));
        }
        var scale = getAttribute(Attributes.SCALE);
        if (scale != null) {
            scale.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("colossus_heart_reforged"), 0.15,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("colossus_heart_reforged"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        hitCircle(level, position(), 5.0, 12.0F, 1.6, 0.5);
        addEffect(WayfarerBoss.wave(position(), 14.0, 0.55, 12.0F, AMBER));
        level.sendParticles(block(plateState()), getX(), getY() + 3, getZ(), 120, 2.0, 2.0, 2.0, 0.4);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 3, getZ(), 6, 1.5, 1.5, 1.5, 0);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 0.5F);
        discardMites(level);
    }

    /** The sword driven into the floor: a hit ahead, then marks round every player for the debris (taken by active). */
    private void quake(ServerLevel level) {
        Vec3 at = ahead(3.5);
        hitCircle(level, at, 2.5, 14.0F, 0.9, 0.5);
        level.sendParticles(block(Blocks.TUFF.defaultBlockState()), at.x, at.y + 0.3, at.z, 50, 1.2, 0.3, 1.2, 0.2);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        spots.clear();
        int players = 0;
        for (Player p : fighters(level)) {
            if (players++ >= 4) {
                break;
            }
            spots.add(clampToArena(p.position(), 0.8));
            for (int i = 0; i < 2; i++) {
                double a = random.nextDouble() * Math.PI * 2;
                double r = 2.0 + random.nextDouble() * 3.0;
                spots.add(clampToArena(p.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 0.8));
            }
        }
        for (int i = 0; i < scaledCount(2); i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = random.nextDouble() * reach();
            spots.add(clampToArena(centre().add(Math.cos(a) * r, 0, Math.sin(a) * r), 0.8));
        }
        // shake the helm: dust everywhere
        Vec3 c = centre();
        level.sendParticles(block(Blocks.TUFF.defaultBlockState()), c.x, c.y + 9, c.z, 80, reach() * 0.5, 2.0, reach() * 0.5, 0.05);
    }

    /**
     * A chunk falling from the helm's ceiling over {@code at}: a ring and falling dust warn for 10 ticks, then a real
     * falling block drops (removed before it lands); 14 within 1.8, slowed, and a heap of rubble left for 8 s.
     */
    private Effect debris(ServerLevel level, Vec3 at, float damage) {
        int[] t = {0};
        FallingBlockEntity[] rock = {null};
        double[] top = {Double.NaN};
        BlockState state = random.nextInt(3) == 0 ? Blocks.COBBLED_DEEPSLATE.defaultBlockState() : Blocks.TUFF.defaultBlockState();
        return (boss, lvl) -> {
            int k = t[0]++;
            if (Double.isNaN(top[0])) {
                top[0] = ceiling(lvl, at);
            }
            if (k % 2 == 0) {
                boss.telegraphRing(lvl, at, 1.8, k < 10 ? GOLD : RED);
                lvl.sendParticles(ParticleTypes.FALLING_DUST == null ? GOLD : new BlockParticleOption(ParticleTypes.FALLING_DUST, state),
                        at.x, top[0] - 0.5, at.z, 2, 0.6, 0, 0.6, 0);
            }
            if (k == 10 && boss instanceof ColossusHeart h) {
                rock[0] = h.spawnBlock(lvl, new Vec3(at.x, top[0] - 1.0, at.z), state, false);
                lvl.playSound(null, at.x, top[0], at.z, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            if (k < 10) {
                return false;
            }
            boolean landed;
            if (rock[0] != null && rock[0].isAlive()) {
                landed = rock[0].getY() + rock[0].getDeltaMovement().y <= at.y + 0.6 || rock[0].onGround();
                if (landed) {
                    rock[0].discard();
                }
            } else {
                landed = k >= 10 + 24 || rock[0] != null;
            }
            if (!landed && k < 60) {
                return false;
            }
            for (LivingEntity e : boss.victims(lvl, at, 2.5)) {
                if (flatDist(e.position(), at) <= 1.8 + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                    boss.strike(lvl, e, damage, 0.4, 0.3);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0), boss);
                }
            }
            lvl.sendParticles(block(state), at.x, at.y + 0.5, at.z, 40, 0.8, 0.4, 0.8, 0.15);
            lvl.playSound(null, at.x, at.y, at.z, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
            if (boss instanceof ColossusHeart h) {
                h.placeRubble(lvl, at, state);
            }
            return true;
        };
    }

    /** The y of the helm's ceiling over {@code at} (the bottom of the first solid block above), or 10 up. */
    private static double ceiling(ServerLevel level, Vec3 at) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(at.x), Mth.floor(at.y) + 2, Mth.floor(at.z));
        for (int i = 0; i < 16; i++) {
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return p.getY();
            }
            p.move(0, 1, 0);
        }
        return at.y + 10;
    }

    /** A heap of rubble on the floor cell at {@code at} (and sometimes one on top): air only, never in a creature. */
    private void placeRubble(ServerLevel level, Vec3 at, BlockState state) {
        BlockPos base = BlockPos.containing(at.x, at.y + 0.1, at.z);
        int until = tickCount + RUBBLE_LIFE;
        int high = random.nextInt(3) == 0 ? 2 : 1;
        for (int dy = 0; dy < high; dy++) {
            BlockPos p = base.above(dy);
            if (rubbleBlocks.size() >= MAX_RUBBLE_BLOCKS || !level.getBlockState(p).isAir() || rubbleBlocks.containsKey(p)
                    || level.getBlockState(p.below()).getCollisionShape(level, p.below()).isEmpty()) {
                return;
            }
            AABB cell = new AABB(p);
            if (getBoundingBox().intersects(cell) || !level.getEntitiesOfClass(LivingEntity.class, cell, LivingEntity::isAlive).isEmpty()) {
                return;
            }
            level.setBlock(p, state, 3);
            rubbleBlocks.put(p.immutable(), until);
        }
    }

    private static void removeRubble(ServerLevel level, BlockPos p) {
        if (level.isLoaded(p)) {
            BlockState s = level.getBlockState(p);
            if (s.is(Blocks.TUFF) || s.is(Blocks.COBBLED_DEEPSLATE)) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                level.sendParticles(block(s), p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 8, 0.3, 0.3, 0.3, 0.05);
            }
        }
    }

    /** Removes rubble whose time is up (or all of it); only blocks that are still the rubble it placed. */
    private void restoreRubble(ServerLevel level, boolean all) {
        if (rubbleBlocks.isEmpty()) {
            return;
        }
        List<BlockPos> done = new ArrayList<>();
        for (Map.Entry<BlockPos, Integer> en : rubbleBlocks.entrySet()) {
            if (all || en.getValue() <= tickCount) {
                removeRubble(level, en.getKey());
                done.add(en.getKey());
            }
        }
        done.forEach(rubbleBlocks::remove);
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(block(plateState()), getX(), getY() + 3.0, getZ(), 8, 0.8, 1.0, 0.8, 0.02);
            level.playSound(null, this, SoundEvents.ANVIL_HIT, SoundSource.HOSTILE, 1.0F, 1.6F);
            return false;
        }
        if (open()) {
            amount *= 1.35F;                                     // the heart is bare
        }
        return super.hurtServer(level, source, amount);
    }

    /** Puts everything back: the rubble, the mites, anything still flying. */
    private void cleanUp(ServerLevel level) {
        restoreRubble(level, true);
        discardMites(level);
        for (FallingBlockEntity fb : flying) {
            if (fb.isAlive()) {
                fb.discard();
            }
        }
        flying.clear();
        shield = null;
    }

    /** Back to the first form (the fight was reset): plates on, normal size, no modifiers. */
    private void resetForm(ServerLevel level) {
        reforged = false;
        openAt = -1;
        roarUntil = -1;
        guard = 0;
        quakeTimer = 60;
        entityData.set(DATA_FORM, WHOLE);
        var armor = getAttribute(Attributes.ARMOR);
        if (armor != null) {
            armor.removeModifier(com.brasshaven.Brasshaven.id("colossus_heart_open"));
        }
        var scale = getAttribute(Attributes.SCALE);
        if (scale != null) {
            scale.removeModifier(com.brasshaven.Brasshaven.id("colossus_heart_reforged"));
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("colossus_heart_reforged"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleRubble) {                        // saved by an unload: removed on the first tick
            staleRubble = false;
            restoreRubble(level, true);
        }
        if (guard > 0) {
            guard--;
        }
        restoreRubble(level, false);
        flying.removeIf(fb -> !fb.isAlive());
        BossAttack cur = currentAttack();
        if (shield != null && (cur == null || !"shieldthrow".equals(cur.name))) {
            catchShield(level);                   // the throw was cut short (stagger, reset)
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!rubbleBlocks.isEmpty() || !mites.isEmpty() || !flying.isEmpty())) {
            cleanUp(level);                       // the arena emptied (death, flight)
        }
        if (phase() == 1 && (reforged || entityData.get(DATA_FORM) != WHOLE || openAt > 0 || !rubbleBlocks.isEmpty())) {
            resetForm(level);                     // the fight was reset
        }
        if (openAt > 0 && tickCount >= openAt) {  // the burst's plates are gone: show the bare heart
            openAt = -1;
            if (!reforged) {
                entityData.set(DATA_FORM, OPEN);
            }
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!reforged && openAt < 0 && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "reforge");
            } else if (reforged && --quakeTimer <= 0) {
                quakeTimer = Math.max(40, (int) Math.round(QUAKE_EVERY * cooldownScale()));
                chain(level, "quake");
            }
        }
        boolean open = open() && entityData.get(DATA_FORM) == OPEN;
        if (open && (cur == null || !"rings".equals(cur.name))) {
            orbitTick(level);
        }
        // ambience: the heart's beat, amber light in the seams, dust from the ceiling in phase 3
        if (tickCount % (open ? 16 : 24) == 0) {
            level.playSound(null, this, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, open ? 2.0F : 1.2F, 0.6F);
            level.sendParticles(AMBER, getX(), getY() + 4.1 * big(), getZ(), open ? 8 : 3, 0.4, 0.4, 0.4, 0.01);
        }
        if (reforged && tickCount % 20 == 0) {
            Vec3 c = centre();
            double a = random.nextDouble() * Math.PI * 2;
            double r = random.nextDouble() * reach();
            level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.TUFF.defaultBlockState()),
                    c.x + Math.cos(a) * r, c.y + 9, c.z + Math.sin(a) * r, 4, 0.5, 0, 0.5, 0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = BURST >= 0 && BURST < actionTicks().length ? actionTicks()[BURST] : 40;
        roarUntil = tickCount + roar + 10;
        openAt = tickCount + 30;
        var armor = getAttribute(Attributes.ARMOR);
        if (armor != null) {
            armor.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("colossus_heart_open"), -8.0,
                    AttributeModifier.Operation.ADD_VALUE));
        }
        if (shield != null) {
            catchShield(level);
        }
        level.sendParticles(block(plateState()), getX(), getY() + 3.5, getZ(), 120, 2.0, 2.0, 2.0, 0.5);
        level.sendParticles(AMBER, getX(), getY() + 4.0, getZ(), 60, 1.0, 1.0, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(block(plateState()), getX(), getY() + 3, getZ(), 150, 2.0, 2.5, 2.0, 0.3);
        level.sendParticles(AMBER, getX(), getY() + 4, getZ(), 80, 1.0, 1.0, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            cleanUp(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("HeartCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("HeartRadius", radius);
        output.putBoolean("HeartReforged", reforged);
        output.putInt("HeartForm", entityData.get(DATA_FORM));
        List<Long> heaps = new ArrayList<>();
        rubbleBlocks.keySet().forEach(p -> heaps.add(p.asLong()));
        output.store("HeartRubble", Codec.LONG.listOf(), heaps);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("HeartCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("HeartRadius", 13);
        reforged = input.getBooleanOr("HeartReforged", false) && phase() == 2;
        int form = input.getIntOr("HeartForm", WHOLE);
        entityData.set(DATA_FORM, phase() == 1 ? WHOLE : reforged ? REFORGED : form == WHOLE ? OPEN : form);
        rubbleBlocks.clear();
        input.read("HeartRubble", Codec.LONG.listOf()).ifPresent(l -> l.forEach(p -> rubbleBlocks.put(BlockPos.of(p), 0)));
        staleRubble = !rubbleBlocks.isEmpty();
    }
}
