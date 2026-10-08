package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
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
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LightBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.MineBaron.BLACKOUT;
import static com.brasshaven.generated.MobAnims.MineBaron.CAVEIN;
import static com.brasshaven.generated.MobAnims.MineBaron.CHARGE;
import static com.brasshaven.generated.MobAnims.MineBaron.COMBO;
import static com.brasshaven.generated.MobAnims.MineBaron.DRILL;
import static com.brasshaven.generated.MobAnims.MineBaron.DYNAMITE;
import static com.brasshaven.generated.MobAnims.MineBaron.EXHAUST;
import static com.brasshaven.generated.MobAnims.MineBaron.FUSELINE;
import static com.brasshaven.generated.MobAnims.MineBaron.GLARE;
import static com.brasshaven.generated.MobAnims.MineBaron.GREED;
import static com.brasshaven.generated.MobAnims.MineBaron.OREBREAK;
import static com.brasshaven.generated.MobAnims.MineBaron.SLAM;
import static com.brasshaven.generated.MobAnims.MineBaron.STAGGER;
import static com.brasshaven.generated.MobAnims.MineBaron.VEINBURST;

/**
 * Le Baron de la mine (The Mine Baron): the greedy foreman of the Rust Mesa Mine-City, a huge man strapped into a
 * riveted steam exo-rig, his right arm a pneumatic drill, a colossal pickaxe-hammer in his left hand and a lantern on
 * his brass hard hat. He waits in the excavated cavern round the half-quarried gold and copper vein.
 * <p>A deliberately hard fight: 600 health, armour 12, poise 130, hits of 6 to 22. Three phases:
 * <ul>
 *     <li>Phase 1 (the foreman): the <b>drill</b> thrust (two grinding hits down a line), the pickaxe <b>slam</b> (a
 *     blow and a line of ore spikes), the drilling <b>charge</b> (a rush that jams into walls and brings rocks down),
 *     <b>dynamite</b> (lit bundles thrown on marked spots, their fuses burning before they blow), the <b>cave-in</b>
 *     (he strikes the floor and bellows: rocks fall on marks round every player) and, if anyone loiters at his back,
 *     the boiler's <b>exhaust</b>.</li>
 *     <li>Phase 2 (the gold-greed, at 65%): ore crawls over him and armours him (every hit from the front does a fifth);
 *     four glowing geodes on the boiler at his back are the weak spots: each hit from behind knocks off a chunk (3 solo,
 *     +1 per extra player, at most 6), and when the last falls he drops to one knee, dazed (4 s, +30% damage). He
 *     re-gilds himself after a while (break it by dealing enough damage during the wind-up). New moves: the
 *     <b>combo</b> (drill, backhand, slam), the <b>vein-burst</b> (ore spikes run along the floor at every player) and
 *     the <b>fuse-line</b> (a keg lobbed at you, a fuse burning back along the floor to it). Two bandit marksmen join
 *     from the scaffolds (more in co-op).</li>
 *     <li>Phase 3 (at 30%): the <b>blackout</b>: he blows the support props; every light in the cavern goes out but
 *     the lantern on his helmet, the burning fuses and the vein, which now sparks and arcs to anyone near it; the
 *     cave-in comes on a timer and the lantern <b>glare</b> blinds whoever it catches in the open (hide behind the vein
 *     or the scaffolds) before he charges them.</li>
 * </ul>
 * Every block he changes is temporary: the lights he puts out (lanterns, torches and any other light block in the
 * cavern) and the invisible light blocks of his lantern, fuses and sparks are put back when the fight ends, resets or
 * the arena empties, when he dies or is removed, and on the first tick after a reload. Thrown bundles and falling rock
 * are falling blocks that never land as blocks; explosions break nothing.
 */
public class MineBaron extends WayfarerBoss {
    public static final float WIDTH = 2.6F;
    public static final float HEIGHT = 5.6F;
    private static final EntityDataAccessor<Integer> DATA_FORM = SynchedEntityData.defineId(MineBaron.class,
            EntityDataSerializers.INT);
    private static final int BARE = 0;
    private static final int GILDED = 1;
    private static final int CRACKED = 2;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final int REGILD_EVERY = 520;
    private static final int CAVEIN_EVERY = 260;
    private static final Set<String> SCHEDULED = Set.of("exhaust", "orebreak", "regild", "blackout");
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF5C842, 1.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xD83A2A, 1.4F);
    private static final DustParticleOptions LAMP = new DustParticleOptions(0xFFF0B0, 1.2F);
    private static final DustParticleOptions STEAM = new DustParticleOptions(0xE8E8E8, 1.6F);
    private static final DustParticleOptions COPPER = new DustParticleOptions(0xD87848, 1.2F);

    private record Temp(BlockState original, BlockState placed) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 20;
    private @Nullable List<BossAttack> moves;
    private final Map<String, Integer> lastStart = new HashMap<>();
    // phase 2: the ore armour
    private int chunks;
    private int chunksMax;
    private int lastChunk = -100;
    private int gildAt = -1;
    private int regildTimer = REGILD_EVERY;
    private boolean regilding;
    private float regildDamage;
    private boolean bandits;
    private boolean wasPhaseTwo;
    private int roarUntil = -1;
    // phase 3: the blackout
    private boolean blackout;
    private int guard;
    private int caveTimer = CAVEIN_EVERY;
    private int sparkTimer = 60;
    private final List<BlockPos> vein = new ArrayList<>();
    private @Nullable BlockPos lampAt;
    private @Nullable BlockPos beamAt;
    // the exhaust: how long someone has loitered at his back
    private int behindTicks;
    // moves in flight
    private final List<Vec3> spots = new ArrayList<>();
    private final List<LivingEntity> marked = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private final List<List<Vec3>> burstLines = new ArrayList<>();
    private boolean jammed;
    private @Nullable Vec3 keg;
    private @Nullable Vec3 fuseFrom;
    private @Nullable LivingEntity blinded;
    private final List<UUID> adds = new ArrayList<>();
    private final List<FallingBlockEntity> flying = new ArrayList<>();
    // every block changed (lights out, light blocks placed): its original state and what was put there
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public MineBaron(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_FORM, BARE);
    }

    /** 0 bare, 1 gilded (ore crust, four geodes), 2 cracked (half the crust and two geodes left). */
    @Override
    public int modelVariant() {
        return entityData.get(DATA_FORM);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MineBaron.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.YELLOW;
    }

    @Override
    protected int roarAction() {
        return GREED;
    }

    @Override
    protected int staggerAction() {
        return STAGGER;
    }

    @Override
    protected float maxPoise() {
        return 130.0F;
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

    // ------------------------------------------------------------------ arena geometry

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

    /** Usable floor radius round the seal (the cavern floor is about 21 round its own centre, the seal off-centre). */
    private double reach() {
        return Math.max(6.0, Math.min(17.0, radius - 2.0));
    }

    private boolean armoured() {
        return chunks > 0;
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

    private static BlockParticleOption block(BlockState state) {
        return new BlockParticleOption(ParticleTypes.BLOCK, state);
    }

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(2.0, reach() - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    /** The floor under {@code p} (its own height if it stands on one), searched 3 up and 4 down. */
    private static Vec3 floorAt(ServerLevel level, Vec3 p) {
        BlockPos b = BlockPos.containing(p.x, p.y + 3, p.z);
        for (int i = 0; i < 8; i++) {
            BlockPos below = b.below();
            if (level.getBlockState(b).getCollisionShape(level, b).isEmpty()
                    && !level.getBlockState(below).getCollisionShape(level, below).isEmpty()) {
                return new Vec3(p.x, b.getY(), p.z);
            }
            b = below;
        }
        return p;
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 14, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** True when {@code from} lies behind him (more than ~105 degrees off his facing). */
    private boolean behind(Vec3 from) {
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        if (to.lengthSqr() < 0.25) {
            return false;
        }
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 fwd = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
        return to.normalize().dot(fwd) < -0.25;
    }

    /** The helmet lantern in the world: 5.2 above his feet, half a block ahead of his face. */
    private Vec3 lampPos() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return position().add(-Mth.sin(yaw) * 0.9, 5.2, Mth.cos(yaw) * 0.9);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        moves = out;
        // drill: the drill arm drawn back at the hip (0.8 s, its line drawn in red), thrust ahead and held grinding:
        // 9 at once and 9 again 0.55 s later down a 6.5 line (half-width 1.2). P3 (dark): a third grind
        out.add(BossAttack.of("drill").anim(DRILL).timing(16, 14, 16).range(0, 7.5).cooldown(50).weight(12)
                .start((b, level, t, tick) -> gate(level, t, "drill"))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 6.5; d += 0.8) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(RED, p.x, p.y + 0.15, p.z, 1, 0.25, 0, 0.25, 0);
                        }
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.0F, 0.6F + tick * 0.03F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && (tick == 0 || tick == 11)) {
                        m.grind(level, 6.5, 9.0F);
                    }
                })
                .build());
        // slam: the pickaxe-hammer heaved over the left shoulder (1.0 s, a ring 3.5 ahead and the spike line in gold),
        // brought down: 18 in r 2.6, then ore spikes burst along the line at 5.5 / 7.5 / 9.5 (11 each). P2+: three lines
        out.add(BossAttack.of("slam").anim(SLAM).timing(20, 4, 16).range(0, 9).cooldown(70).weight(11)
                .start((b, level, t, tick) -> gate(level, t, "slam"))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 2.6, GOLD);
                    }
                    if (tick % 4 == 0) {
                        for (double fan : b.phase() == 2 ? new double[] {-25, 0, 25} : new double[] {0}) {
                            Vec3 dir = rotate(b.forward(), fan);
                            for (double d = 5.5; d <= 9.5; d += 2.0) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(GOLD, p.x, p.y + 0.15, p.z, 3, 0.3, 0, 0.3, 0);
                            }
                        }
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 at = b.ahead(3.5);
                    b.hitCircle(level, at, 2.6, 18.0F, 0.9, 0.4);
                    level.sendParticles(block(Blocks.COBBLED_DEEPSLATE.defaultBlockState()), at.x, at.y + 0.3, at.z, 50, 1.2, 0.3, 1.2, 0.2);
                    level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 1, 0.3, 0.1, 0.3, 0);
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    for (double fan : b.phase() == 2 ? new double[] {-25, 0, 25} : new double[] {0}) {
                        Vec3 dir = rotate(b.forward(), fan);
                        int k = 0;
                        for (double d = 5.5; d <= 9.5; d += 2.0) {
                            Vec3 p = b.position().add(dir.scale(d));
                            if (solid(level, p.add(0, 0.5, 0))) {
                                break;
                            }
                            b.addEffect(WayfarerBoss.eruption(p, 4 + 4 * k++, 1.6, 11.0F, GOLD,
                                    block(Blocks.GOLD_ORE.defaultBlockState())));
                        }
                    }
                })
                .build());
        // charge: crouched behind the drill (0.9 s, its path drawn 14 ahead), a rush at 1 block a tick for 0.7 s: 13
        // once to each creature hit and a heavy shove; if the drill jams into rock, the cavern sheds stones round him
        out.add(BossAttack.of("charge").anim(CHARGE).timing(18, 16, 18).range(6, 24).cooldown(110).weight(9)
                .start((b, level, t, tick) -> {
                    if (gate(level, t, "charge")) {
                        struck.clear();
                        jammed = false;
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 14; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(RED, p.x, p.y + 0.15, p.z, 1, 0.3, 0, 0.3, 0);
                        }
                    }
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 5.5, b.getZ(), 3, 0.4, 0.2, 0.4, 0.02);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.chargeTick(level, tick);
                    }
                })
                .build());
        // dynamite: a bundle lit on the helmet lamp (0.9 s): red rings follow their marks for 0.6 s and lock; the
        // bundles fly (0.6 s), land and fizz (1.1 s, 0.9 in P2, 0.8 in P3), then blow: 14 in r 3, hurled away
        out.add(BossAttack.of("dynamite").anim(DYNAMITE).timing(18, 24, 14).range(4, 28).cooldown(100).weight(10)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.noteStart("dynamite");
                        m.pickBundles(level, t);
                    }
                    level.playSound(null, b, SoundEvents.FLINTANDSTEEL_USE, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof MineBaron m)) {
                        return;
                    }
                    if (tick < 12) {
                        for (int i = 0; i < m.marked.size() && i < m.spots.size(); i++) {
                            LivingEntity e = m.marked.get(i);
                            if (e != null && e.isAlive()) {
                                m.spots.set(i, m.clampToArena(e.position(), 1.0));
                            }
                        }
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 s : m.spots) {
                            b.telegraphRing(level, s, 3.0, tick < 12 ? GOLD : RED);
                        }
                    }
                    Vec3 lamp = m.lampPos();
                    level.sendParticles(ParticleTypes.SMALL_FLAME, lamp.x, lamp.y + 0.3, lamp.z, 1, 0.1, 0.1, 0.1, 0.01);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && tick % 4 == 0 && tick / 4 < m.spots.size()) {
                        m.throwBundle(level, m.spots.get(tick / 4));
                    }
                })
                .build());
        // exhaust (scheduled: someone loiters at his back): a whistle (0.7 s, the cone behind him drawn in steam), the
        // boiler blasts: 13 in a cone 6 deep behind him (+-65 degrees), shoved away; 6 within 2.6 all round
        out.add(BossAttack.of("exhaust").anim(EXHAUST).timing(14, 4, 12).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.HOSTILE, 3.0F, 2.0F))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && b instanceof MineBaron m) {
                        m.drawBackCone(level, 6.0, 65, STEAM);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 5.0, b.getZ(), 2, 0.3, 0.3, 0.3, 0.05);
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.HOSTILE, 3.0F, 1.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.exhaust(level);
                    }
                })
                .build());
        // cave-in: the pickaxe struck on the floor (1.1 s, a ring round him), then he bellows at the roof: marks round
        // every player (one on them, one near) and strays, each warned 0.7 s, then a rock falls: 13 in r 1.8, slowed
        out.add(BossAttack.of("cavein").anim(CAVEIN).timing(22, 30, 14).range(0, 30).cooldown(220).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.noteStart("cavein");
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(2.5), 2.2, GOLD);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.caveIn(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && tick % 3 == 0 && tick / 3 < m.spots.size()) {
                        b.addEffect(m.debris(level, m.spots.get(tick / 3), 13.0F));
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2 (and 3)
        // combo: drill jab (0.7 s: 10 down a 5 line), pickaxe backhand 0.55 s later (12 over +-90 degrees, 5.5 out),
        // overhead slam 0.55 s after (16 in r 2.4 at 3 ahead, and a ring to jump: 8 out to 7)
        out.add(BossAttack.of("combo").anim(COMBO).phaseTwo().timing(14, 30, 14).range(0, 6.5).cooldown(90).weight(11)
                .start((b, level, t, tick) -> gate(level, t, "combo"))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphArc(level, 5.5, 90, RED);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0) {
                        b.hitLine(level, 5.0, 1.1, 10.0F, 0.2);
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.8F);
                    } else if (tick == 11) {
                        b.hitArc(level, 5.5, 90, 12.0F, 1.0);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                    } else if (tick > 11 && tick < 22 && tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(3.0), 2.4, RED);
                    } else if (tick == 22) {
                        Vec3 at = b.ahead(3.0);
                        b.hitCircle(level, at, 2.4, 16.0F, 0.8, 0.4);
                        b.addEffect(WayfarerBoss.wave(at, 7.0, 0.5, 8.0F, ParticleTypes.CRIT));
                        level.sendParticles(block(Blocks.COBBLED_DEEPSLATE.defaultBlockState()), at.x, at.y + 0.3, at.z, 40, 1.0, 0.3, 1.0, 0.2);
                        level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.7F);
                    }
                })
                .build());
        // veinburst: the drill raised and driven into the floor (1.0 s, gold lines drawn toward up to 3 players): ore
        // spikes run along each line, one every 1.2 blocks, 2 ticks apart, out to 18 (12 each, thrown up)
        out.add(BossAttack.of("veinburst").anim(VEINBURST).phaseTwo().timing(20, 20, 16).range(4, 24).cooldown(130).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.gate(level, t, "veinburst")) {
                        m.marked.clear();
                        for (Player p : m.fighters(level)) {
                            if (m.marked.size() < 3) {
                                m.marked.add(p);
                            }
                        }
                        if (m.marked.isEmpty() && t != null) {
                            m.marked.add(t);
                        }
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof MineBaron m) || tick % 3 != 0) {
                        return;
                    }
                    for (LivingEntity e : m.marked) {
                        Vec3 dir = e.position().subtract(b.position()).multiply(1, 0, 1);
                        if (dir.lengthSqr() < 0.01) {
                            continue;
                        }
                        dir = dir.normalize();
                        for (double d = 2; d <= 18; d += 1.2) {
                            Vec3 p = b.position().add(dir.scale(d));
                            level.sendParticles(GOLD, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.veinBurst(level);
                    }
                })
                .build());
        // fuseline: a keg swung underarm and lobbed at the target (0.8 s, a red ring r 5 where it will land); a fuse
        // burns back from his drill along the floor to it (6 to whoever the spark passes), then the keg blows: 20 in
        // r 5 (thrown), four ore spikes round it. He stands holding the fuse the whole time: hit him or run
        out.add(BossAttack.of("fuseline").anim(FUSELINE).phaseTwo().timing(16, 40, 14).range(6, 26).cooldown(200).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.gate(level, t, "fuseline")) {
                        m.struck.clear();
                        Vec3 aim = t != null ? t.position() : b.ahead(10);
                        m.keg = m.clampToArena(aim, 1.5);
                        m.fuseFrom = null;
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.keg != null && tick % 2 == 0) {
                        b.telegraphRing(level, m.keg, 5.0, RED);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.keg != null) {
                        m.lobKeg(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.fuseTick(level, tick);
                    }
                })
                .build());
        // glare (phase 3 only, in the dark): head lowered, the lamp turned up (0.9 s, the cone drawn in pale light):
        // whoever stands in the cone (+-35 degrees, 18 deep) with nothing between them and the lamp is blinded 3 s,
        // slowed and takes 4; then he charges the first one blinded. Hide behind the vein or a scaffold
        out.add(BossAttack.of("glare").anim(GLARE).phaseTwo().timing(18, 10, 12).range(0, 20).cooldown(150).weight(9)
                .start((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.gate(level, t, "glare")) {
                        m.blinded = null;
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 2.0F, 1.6F);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof MineBaron m) {
                        m.drawCone(level, 18, 35, LAMP);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.glare(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.blinded != null && m.blinded.isAlive()) {
                        b.setTarget(m.blinded);
                        b.chain(level, "charge");
                    }
                })
                .build());

        // ---------------------------------------------------------------- scheduled (range 999, weight 0)
        // orebreak: the last geode knocked off: he drops to one knee, dazed (+30% damage taken)
        out.add(BossAttack.of("orebreak").anim(OREBREAK).phaseTwo().timing(10, 60, 10).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .impact((b, level, t, tick) -> {
                    level.sendParticles(block(Blocks.RAW_GOLD_BLOCK.defaultBlockState()), b.getX(), b.getY() + 3, b.getZ(), 80, 1.5, 1.5, 1.5, 0.3);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 6 == 0) {
                        level.sendParticles(ParticleTypes.SMOKE, b.getX(), b.getY() + 4.5, b.getZ(), 6, 0.5, 0.3, 0.5, 0.02);
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 2.5, b.getZ(), 4, 1.0, 0.8, 1.0, 0.1);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.regildTimer = (int) Math.round(REGILD_EVERY * m.cooldownScale());
                    }
                })
                .build());
        // regild: arms out, gold dust streams to him from the walls (1.5 s): unless the players deal enough damage in
        // the wind-up (60, +25% per extra player), the crust locks on again
        out.add(BossAttack.of("regild").anim(GREED).phaseTwo().timing(30, 10, 10).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.regilding = true;
                        m.regildDamage = 0;
                    }
                    level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.streamGold(level, tick);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && m.regilding) {
                        m.regilding = false;
                        m.gild(level);
                    }
                })
                .build());
        // blackout (phase 3, once): bundles flung at the props round the walls (1.5 s, invulnerable): they blow, every
        // light in the cavern dies, rocks fall all over, a shock ring to jump (12, out to 14); the crust is blasted off
        out.add(BossAttack.of("blackout").anim(BLACKOUT).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 74;
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof MineBaron m && (tick == 8 || tick == 16 || tick == 24)) {
                        for (int k = 0; k < 2; k++) {
                            m.throwAtWall(level, tick * 13 + k * 180);
                        }
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, RED);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof MineBaron m) {
                        m.goDark(level);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ gating (phase 3 moves need the dark)

    private void noteStart(String name) {
        lastStart.put(name, tickCount);
    }

    private boolean gate(ServerLevel level, @Nullable LivingEntity t, String name) {
        if (!"glare".equals(name) || blackout) {
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
        List<BossAttack> ok = new ArrayList<>();
        int total = 0;
        for (BossAttack a : moves) {
            if (a.weight <= 0 || SCHEDULED.contains(a.name) || "glare".equals(a.name) || !a.allowedIn(phase())
                    || dist < a.minRange || dist > a.maxRange) {
                continue;
            }
            Integer last = lastStart.get(a.name);
            if (last != null && tickCount - last < a.cooldown * cooldownScale()) {
                continue;
            }
            ok.add(a);
            total += a.weight;
        }
        String pick = dist > 6 ? "dynamite" : "drill";
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

    /** One grind of the drill: everything down the line in front takes {@code damage}, barely pushed (it holds you). */
    private void grind(ServerLevel level, double length, float damage) {
        hitLine(level, length, 1.2, damage, 0.15);
        Vec3 tip = ahead(4.0);
        level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 2.0, tip.z, 12, 0.6, 0.4, 0.6, 0.2);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, tip.x, tip.y + 2.0, tip.z, 8, 0.4, 0.3, 0.4, 0.1);
        level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    private void chargeTick(ServerLevel level, int tick) {
        if (tick < 14 && !jammed) {
            Vec3 f = forward();
            Vec3 next = position().add(f.scale(1.8));
            boolean wall = solid(level, next.add(0, 1.2, 0)) || solid(level, next.add(0, 2.5, 0));
            boolean edge = flatDist(next, centre()) > reach() + 1.5;
            if (wall || edge) {
                jammed = true;
                setDeltaMovement(0, getDeltaMovement().y, 0);
                hurtMarked = true;
                if (wall) {
                    jam(level);
                }
            } else {
                setDeltaMovement(f.x, getDeltaMovement().y, f.z);
                hurtMarked = true;
            }
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
        Vec3 tip = ahead(2.6);
        level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 1.8, tip.z, 4, 0.3, 0.3, 0.3, 0.1);
        if (tick % 2 == 0) {
            level.sendParticles(block(Blocks.COARSE_DIRT.defaultBlockState()), getX(), getY() + 0.2, getZ(), 6, 0.8, 0.1, 0.8, 0.1);
        }
        if (tick % 4 == 0) {
            level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
        for (LivingEntity e : victims(level, tip, 3.0)) {
            if (flatDist(e.position(), tip) <= 2.6 && struck.add(e.getUUID())) {
                strike(level, e, 13.0F, 1.5, 0.35);
            }
        }
    }

    /** The drill jammed into rock: sparks, and three stones shaken loose from the roof round him. */
    private void jam(ServerLevel level) {
        Vec3 tip = ahead(2.2);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, tip.x, tip.y + 2, tip.z, 30, 0.6, 0.6, 0.6, 0.3);
        level.sendParticles(block(Blocks.DEEPSLATE.defaultBlockState()), tip.x, tip.y + 2, tip.z, 40, 0.8, 0.8, 0.8, 0.2);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        for (int i = 0; i < 3; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 2.5 + random.nextDouble() * 3.0;
            addEffect(debris(level, clampToArena(position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 0.8), 10.0F));
        }
    }

    // ---- dynamite

    private void pickBundles(ServerLevel level, @Nullable LivingEntity t) {
        marked.clear();
        spots.clear();
        if (phase() == 1) {
            if (t != null) {
                marked.add(t);
                spots.add(clampToArena(t.position(), 1.0));
            }
        } else {
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
        }
        Vec3 anchor = t != null ? t.position() : ahead(8);
        int extra = blackout ? 3 : 2;
        for (int i = 0; i < extra && spots.size() < 6; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 2.5 + random.nextDouble() * 3.0;
            marked.add(null);
            spots.add(clampToArena(anchor.add(Math.cos(a) * r, 0, Math.sin(a) * r), 1.0));
        }
    }

    private void throwBundle(ServerLevel level, Vec3 spot) {
        Vec3 to = floorAt(level, spot);
        Vec3 from = lampPos().add(0, 0.5, 0);
        int fuse = blackout ? 16 : phase() == 2 ? 18 : 22;
        addEffect(bundle(level, from, to, 12, fuse, 3.0, 14.0F));
        level.playSound(null, this, SoundEvents.SNOWBALL_THROW, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /**
     * A lit bundle of dynamite: a falling block flown on an arc from {@code from} to {@code to}, removed before it
     * lands; then its fuse fizzes for {@code fuse} ticks on the floor (a red ring, sparks, a temporary light), then it
     * blows: {@code damage} within {@code r}, everything hurled away from the blast. Nothing is broken.
     */
    private Effect bundle(ServerLevel level, Vec3 from, Vec3 to, int flight, int fuse, double r, float damage) {
        FallingBlockEntity stick = spawnBlock(level, from, Blocks.TNT.defaultBlockState(), false);
        if (stick != null) {
            double drag = (1 - Math.pow(0.98, flight)) / 0.02;
            stick.setDeltaMovement((to.x - stick.getX()) / drag, solveLift(stick.getY(), to.y + 0.5, flight), (to.z - stick.getZ()) / drag);
            stick.hurtMarked = true;
        }
        int[] t = {0};
        int[] landed = {-1};
        BlockPos[] light = {null};
        return (boss, lvl) -> {
            int k = t[0]++;
            MineBaron m = boss instanceof MineBaron mb ? mb : null;
            if (landed[0] < 0) {
                if (k % 2 == 0) {
                    boss.telegraphRing(lvl, to, r, RED);
                }
                boolean down = k >= flight + 6;
                if (stick != null && stick.isAlive()) {
                    Vec3 v = stick.getDeltaMovement();
                    lvl.sendParticles(ParticleTypes.SMOKE, stick.getX(), stick.getY() + 0.8, stick.getZ(), 1, 0, 0, 0, 0);
                    if (v.y < 0 && (stick.getY() + v.y <= to.y + 0.6 || stick.onGround())) {
                        stick.discard();
                        down = true;
                    }
                } else if (stick != null) {
                    down = true;
                }
                if (down) {
                    landed[0] = k;
                    lvl.playSound(null, to.x, to.y, to.z, SoundEvents.TNT_PRIMED, SoundSource.HOSTILE, 1.5F, 1.0F);
                    if (m != null) {
                        light[0] = m.placeLight(lvl, BlockPos.containing(to.x, to.y + 0.5, to.z), 11);
                    }
                }
                return false;
            }
            int burn = k - landed[0];
            if (burn < fuse) {
                lvl.sendParticles(ParticleTypes.SMALL_FLAME, to.x, to.y + 0.7, to.z, 1, 0.05, 0.05, 0.05, 0.01);
                lvl.sendParticles(ParticleTypes.SMOKE, to.x, to.y + 0.8, to.z, 1, 0.05, 0.05, 0.05, 0.01);
                lvl.sendParticles(block(Blocks.TNT.defaultBlockState()), to.x, to.y + 0.3, to.z, 1, 0.15, 0.1, 0.15, 0);
                if (burn % 2 == 0) {
                    boss.telegraphRing(lvl, to, r, burn > fuse - 6 ? RED : GOLD);
                }
                return false;
            }
            if (m != null) {
                m.blast(lvl, to, r, damage);
                if (light[0] != null) {
                    m.clearTemp(lvl, light[0]);
                }
            }
            return true;
        };
    }

    /** An explosion that breaks nothing: {@code damage} within {@code r} (full in the middle, 60% at the edge), hurled. */
    private void blast(ServerLevel level, Vec3 at, double r, float damage) {
        for (LivingEntity e : victims(level, at, r + 1)) {
            double d = flatDist(e.position(), at);
            if (d > r + e.getBbWidth() / 2 || Math.abs(e.getY() - at.y) > 3.0) {
                continue;
            }
            float k = (float) (1.0 - 0.4 * Math.min(1.0, d / r));
            if (e.hurtServer(level, damageSources().mobAttack(this), damage * k)) {
                Vec3 away = e.position().subtract(at).multiply(1, 0, 1);
                away = away.lengthSqr() < 1.0E-4 ? forward() : away.normalize();
                e.push(away.x * 1.1 * k, 0.5, away.z * 1.1 * k);
                e.hurtMarked = true;
            }
        }
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y + 0.5, at.z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.FLAME, at.x, at.y + 0.5, at.z, 20, r * 0.3, 0.3, r * 0.3, 0.05);
        level.sendParticles(block(Blocks.COARSE_DIRT.defaultBlockState()), at.x, at.y + 0.3, at.z, 30, r * 0.3, 0.3, r * 0.3, 0.2);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F, 0.9F);
    }

    /** A falling block for show (a bundle, a stone): put into an air cell for an instant and lifted out at once. */
    private @Nullable FallingBlockEntity spawnBlock(ServerLevel level, Vec3 at, BlockState state, boolean weightless) {
        BlockPos cell = BlockPos.containing(at);
        if (!level.isLoaded(cell) || !level.getBlockState(cell).isAir()) {
            return null;
        }
        if (state.is(Blocks.TNT) && level.hasNeighborSignal(cell)) {
            state = Blocks.BRICKS.defaultBlockState();               // never a real TNT next to redstone power
        }
        level.setBlock(cell, state, 2);
        FallingBlockEntity fb = FallingBlockEntity.fall(level, cell, state);
        fb.dropItem = false;
        fb.disableDrop();
        fb.setNoGravity(weightless);
        flying.add(fb);
        return fb;
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

    // ---- the exhaust and the cones

    private void drawBackCone(ServerLevel level, double depth, double half, ParticleOptions p) {
        Vec3 back = forward().scale(-1);
        for (double a = -half; a <= half; a += 13) {
            Vec3 dir = rotate(back, a);
            for (double d = 1.5; d <= depth; d += 1.5) {
                Vec3 q = position().add(dir.scale(d));
                level.sendParticles(p, q.x, q.y + 0.2, q.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private void drawCone(ServerLevel level, double depth, double half, ParticleOptions p) {
        for (double a = -half; a <= half; a += 10) {
            Vec3 dir = rotate(forward(), a);
            for (double d = 2; d <= depth; d += 2) {
                Vec3 q = position().add(dir.scale(d));
                level.sendParticles(p, q.x, q.y + 0.25, q.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private void exhaust(ServerLevel level) {
        Vec3 back = forward().scale(-1);
        double cos = Math.cos(Math.toRadians(65));
        for (LivingEntity e : victims(level, position(), 7.0)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= 6.0 + e.getBbWidth() / 2 && d > 0.5 && to.normalize().dot(back) >= cos) {
                if (e.hurtServer(level, damageSources().mobAttack(this), 13.0F)) {
                    Vec3 away = to.normalize();
                    e.push(away.x * 1.4, 0.4, away.z * 1.4);
                    e.hurtMarked = true;
                }
            } else if (d <= 2.6 + e.getBbWidth() / 2) {
                strike(level, e, 6.0F, 0.9, 0.2);
            }
        }
        for (double a = -60; a <= 60; a += 15) {
            Vec3 dir = rotate(back, a);
            Vec3 q = position().add(dir.scale(1.5)).add(0, 2.5, 0);
            level.sendParticles(ParticleTypes.CLOUD, q.x, q.y, q.z, 0, dir.x, -0.1, dir.z, 0.8);
            level.sendParticles(ParticleTypes.CLOUD, q.x, q.y - 1, q.z, 0, dir.x, -0.15, dir.z, 0.6);
        }
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    // ---- the cave-in

    private void caveIn(ServerLevel level) {
        Vec3 at = ahead(2.5);
        hitCircle(level, at, 2.2, 12.0F, 0.8, 0.3);
        level.sendParticles(block(Blocks.COBBLED_DEEPSLATE.defaultBlockState()), at.x, at.y + 0.3, at.z, 40, 1.0, 0.3, 1.0, 0.2);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.6F);
        spots.clear();
        int players = 0;
        for (Player p : fighters(level)) {
            if (players++ >= 4) {
                break;
            }
            spots.add(clampToArena(p.position(), 0.8));
            int near = blackout ? 2 : 1;
            for (int i = 0; i < near; i++) {
                double a = random.nextDouble() * Math.PI * 2;
                double r = 2.0 + random.nextDouble() * 2.5;
                spots.add(clampToArena(p.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 0.8));
            }
        }
        for (int i = 0; i < scaledCount(1); i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = random.nextDouble() * reach();
            spots.add(clampToArena(centre().add(Math.cos(a) * r, 0, Math.sin(a) * r), 0.8));
        }
        Vec3 c = centre();
        level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.DEEPSLATE.defaultBlockState()),
                c.x, c.y + 14, c.z, 80, reach() * 0.5, 2.0, reach() * 0.5, 0.05);
    }

    /**
     * A rock falling from the roof over {@code at}: a ring and falling dust warn for 14 ticks (gold, red from 8), then
     * a falling block drops (removed before it lands): {@code damage} within 1.8 and slowed 2 s.
     */
    private Effect debris(ServerLevel level, Vec3 at, float damage) {
        int[] t = {0};
        FallingBlockEntity[] rock = {null};
        double[] top = {Double.NaN};
        BlockState state = random.nextInt(3) == 0 ? Blocks.COBBLED_DEEPSLATE.defaultBlockState() : Blocks.TUFF.defaultBlockState();
        Vec3 floor = floorAt(level, at);
        return (boss, lvl) -> {
            int k = t[0]++;
            if (Double.isNaN(top[0])) {
                top[0] = ceiling(lvl, floor);
            }
            if (k % 2 == 0) {
                boss.telegraphRing(lvl, floor, 1.8, k < 8 ? GOLD : RED);
                lvl.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, state), floor.x, top[0] - 0.5, floor.z, 2, 0.6, 0, 0.6, 0);
            }
            if (k == 14 && boss instanceof MineBaron m) {
                rock[0] = m.spawnBlock(lvl, new Vec3(floor.x, top[0] - 1.0, floor.z), state, false);
                lvl.playSound(null, floor.x, top[0], floor.z, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            if (k < 14) {
                return false;
            }
            boolean landed;
            if (rock[0] != null && rock[0].isAlive()) {
                landed = rock[0].getY() + rock[0].getDeltaMovement().y <= floor.y + 0.6 || rock[0].onGround();
                if (landed) {
                    rock[0].discard();
                }
            } else {
                landed = k >= 14 + 24 || rock[0] != null;
            }
            if (!landed && k < 70) {
                return false;
            }
            for (LivingEntity e : boss.victims(lvl, floor, 2.5)) {
                if (flatDist(e.position(), floor) <= 1.8 + e.getBbWidth() / 2 && Math.abs(e.getY() - floor.y) < 2.5) {
                    boss.strike(lvl, e, damage, 0.4, 0.3);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0), boss);
                }
            }
            lvl.sendParticles(block(state), floor.x, floor.y + 0.5, floor.z, 40, 0.8, 0.4, 0.8, 0.15);
            lvl.playSound(null, floor.x, floor.y, floor.z, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
            return true;
        };
    }

    /** The y of the roof over {@code at} (the bottom of the first solid block above), or 14 up. */
    private static double ceiling(ServerLevel level, Vec3 at) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(at.x), Mth.floor(at.y) + 3, Mth.floor(at.z));
        for (int i = 0; i < 24; i++) {
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return p.getY();
            }
            p.move(0, 1, 0);
        }
        return at.y + 14;
    }

    // ---- vein-burst

    private void veinBurst(ServerLevel level) {
        Vec3 at = ahead(2.5);
        hitCircle(level, at, 3.0, 12.0F, 0.8, 0.5);
        level.sendParticles(block(Blocks.GOLD_ORE.defaultBlockState()), at.x, at.y + 0.3, at.z, 50, 1.2, 0.3, 1.2, 0.2);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.8F);
        level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 3.0F, 0.4F);
        for (LivingEntity e : marked) {
            Vec3 dir = e.position().subtract(position()).multiply(1, 0, 1);
            if (dir.lengthSqr() < 0.01) {
                continue;
            }
            dir = dir.normalize();
            int k = 0;
            for (double d = 3.0; d <= 18; d += 1.2) {
                Vec3 p = position().add(dir.scale(d));
                if (solid(level, p.add(0, 0.5, 0)) || flatDist(p, centre()) > reach() + 2) {
                    break;
                }
                addEffect(WayfarerBoss.eruption(floorAt(level, p), 3 + 2 * k++, 1.3, 12.0F, GOLD,
                        block((k % 2 == 0 ? Blocks.GOLD_ORE : Blocks.COPPER_ORE).defaultBlockState())));
            }
        }
    }

    // ---- fuse-line

    private void lobKeg(ServerLevel level) {
        Vec3 to = floorAt(level, keg);
        keg = to;
        FallingBlockEntity k = spawnBlock(level, lampPos(), Blocks.TNT.defaultBlockState(), false);
        if (k != null) {
            double drag = (1 - Math.pow(0.98, 12)) / 0.02;
            k.setDeltaMovement((to.x - k.getX()) / drag, solveLift(k.getY(), to.y + 0.5, 12), (to.z - k.getZ()) / drag);
            k.hurtMarked = true;
            FallingBlockEntity kk = k;
            int[] t = {0};
            addEffect((boss, lvl) -> {
                t[0]++;
                if (!kk.isAlive()) {
                    return true;
                }
                if ((kk.getDeltaMovement().y < 0 && kk.getY() + kk.getDeltaMovement().y <= to.y + 0.6) || kk.onGround() || t[0] > 30) {
                    kk.discard();
                    return true;
                }
                return false;
            });
        }
        fuseFrom = floorAt(level, ahead(2.0));
        level.playSound(null, this, SoundEvents.SNOWBALL_THROW, SoundSource.HOSTILE, 2.0F, 0.3F);
    }

    private void fuseTick(ServerLevel level, int tick) {
        if (keg == null || fuseFrom == null) {
            return;
        }
        if (tick % 2 == 0) {
            telegraphRing(level, keg, 5.0, tick > 32 ? RED : GOLD);
            level.sendParticles(block(Blocks.TNT.defaultBlockState()), keg.x, keg.y + 0.4, keg.z, 3, 0.3, 0.3, 0.3, 0);
            double len = flatDist(fuseFrom, keg);
            for (double d = 0; d <= len; d += 1.0) {
                Vec3 p = fuseFrom.lerp(keg, len < 0.01 ? 0 : d / len);
                level.sendParticles(COPPER, p.x, p.y + 0.1, p.z, 1, 0, 0, 0, 0);
            }
        }
        if (tick >= 10 && tick < 38) {
            double u = (tick - 10) / 28.0;
            Vec3 spark = fuseFrom.lerp(keg, u);
            level.sendParticles(ParticleTypes.FLAME, spark.x, spark.y + 0.2, spark.z, 3, 0.1, 0.1, 0.1, 0.02);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, spark.x, spark.y + 0.3, spark.z, 3, 0.1, 0.1, 0.1, 0.1);
            if (tick % 4 == 0) {
                level.playSound(null, spark.x, spark.y, spark.z, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 1.5F, 1.5F);
            }
            if (tick % 3 == 0) {
                moveBeam(level, BlockPos.containing(spark.x, spark.y + 0.5, spark.z), 10);
            }
            for (LivingEntity e : victims(level, spark, 1.5)) {
                if (flatDist(e.position(), spark) <= 1.0 && struck.add(e.getUUID())) {
                    strike(level, e, 6.0F, 0.3, 0.3);
                    e.igniteForSeconds(2.0F);
                }
            }
        }
        if (tick == 38) {
            moveBeam(level, null, 0);
            blast(level, keg, 5.0, 20.0F);
            for (int k = 0; k < 4; k++) {
                double a = k * Math.PI / 2 + random.nextDouble();
                Vec3 p = clampToArena(keg.add(Math.cos(a) * 4.5, 0, Math.sin(a) * 4.5), 0.8);
                addEffect(WayfarerBoss.eruption(floorAt(level, p), 6 + k * 2, 1.4, 10.0F, GOLD, block(Blocks.GOLD_ORE.defaultBlockState())));
            }
        }
    }

    // ---- glare

    private void glare(ServerLevel level) {
        Vec3 eye = lampPos();
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(35));
        for (Player p : fighters(level)) {
            Vec3 to = p.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > 18 || (d > 1 && to.normalize().dot(fwd) < cos)) {
                continue;
            }
            if (level.clip(new ClipContext(eye, p.getEyePosition(), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this))
                    .getType() != HitResult.Type.MISS) {
                continue;                                  // behind the vein, a scaffold: safe
            }
            p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), this);
            p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
            strike(level, p, 4.0F, 0.0, 0.0);
            if (blinded == null) {
                blinded = p;
            }
        }
        for (double a = -35; a <= 35; a += 7) {
            Vec3 dir = rotate(fwd, a);
            for (double d = 2; d <= 18; d += 1.5) {
                Vec3 q = eye.add(dir.scale(d)).add(0, -d * 0.2, 0);
                level.sendParticles(ParticleTypes.END_ROD, q.x, q.y, q.z, 1, 0.1, 0.1, 0.1, 0);
            }
        }
        level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 1.8F);
    }

    // ------------------------------------------------------------------ the ore armour (phase 2)

    private void gild(ServerLevel level) {
        chunksMax = Math.min(6, 3 + scaledPlayers() - 1);
        chunks = chunksMax;
        entityData.set(DATA_FORM, GILDED);
        level.sendParticles(block(Blocks.RAW_GOLD_BLOCK.defaultBlockState()), getX(), getY() + 3, getZ(), 80, 1.2, 1.6, 1.2, 0.1);
        level.sendParticles(block(Blocks.RAW_COPPER_BLOCK.defaultBlockState()), getX(), getY() + 3, getZ(), 40, 1.2, 1.6, 1.2, 0.1);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.DEEPSLATE_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
        if (!bandits) {
            bandits = true;
            spawnBandits(level);
        }
    }

    private void knockChunk(ServerLevel level) {
        chunks--;
        lastChunk = tickCount;
        Vec3 back = position().add(forward().scale(-1.3)).add(0, 3.0 + random.nextDouble() * 1.2, 0);
        level.sendParticles(block(Blocks.RAW_GOLD_BLOCK.defaultBlockState()), back.x, back.y, back.z, 40, 0.4, 0.4, 0.4, 0.2);
        level.sendParticles(ParticleTypes.WAX_ON, back.x, back.y, back.z, 12, 0.4, 0.4, 0.4, 0.3);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 1.6F);
        if (chunks <= 0) {
            chunks = 0;
            entityData.set(DATA_FORM, BARE);
            level.playSound(null, this, SoundEvents.RAVAGER_HURT, SoundSource.HOSTILE, 3.0F, 0.5F);
            chain(level, "orebreak");
        } else if (chunks * 2 <= chunksMax) {
            entityData.set(DATA_FORM, CRACKED);
        }
    }

    private void streamGold(ServerLevel level, int tick) {
        Vec3 c = position().add(0, 3, 0);
        for (int i = 0; i < 4; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 6 + random.nextDouble() * 8;
            Vec3 from = new Vec3(c.x + Math.cos(a) * r, c.y + random.nextDouble() * 4 - 1, c.z + Math.sin(a) * r);
            Vec3 v = c.subtract(from);
            level.sendParticles(GOLD, from.x, from.y, from.z, 0, v.x, v.y, v.z, 0.12);
        }
        if (tick % 3 == 0) {
            telegraphRing(level, position(), 3.5, GOLD);
        }
        if (tick % 8 == 0) {
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.6F + tick * 0.02F);
        }
    }

    private void spawnBandits(ServerLevel level) {
        int n = scaledCount(1) + 1;
        for (int i = 0; i < n; i++) {
            Mob mob = ModEntities.BANDIT_MARKSMAN.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 12 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                double r = reach() * (0.6 + random.nextDouble() * 0.35);
                Vec3 p = floorAt(level, centre().add(Math.cos(a) * r, 0, Math.sin(a) * r));
                if (!solid(level, p.add(0, 0.5, 0)) && !solid(level, p.add(0, 1.5, 0)) && flatDist(p, position()) > 6) {
                    at = p;
                }
            }
            if (at == null) {
                at = centre();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.POOF, at.x, at.y + 1, at.z, 15, 0.3, 0.5, 0.3, 0.05);
        }
    }

    private void discardAdds(ServerLevel level) {
        for (UUID id : adds) {
            var e = level.getEntity(id);
            if (e != null && e.isAlive()) {
                level.sendParticles(ParticleTypes.POOF, e.getX(), e.getY() + 1, e.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
                e.discard();
            }
        }
        adds.clear();
    }

    // ------------------------------------------------------------------ the blackout (phase 3)

    private void throwAtWall(ServerLevel level, double degrees) {
        Vec3 c = centre();
        Vec3 dir = rotate(new Vec3(1, 0, 0), degrees + random.nextInt(40));
        Vec3 last = c.add(dir.scale(6)).add(0, 2, 0);
        for (double d = 6; d <= 26; d += 0.5) {
            Vec3 p = c.add(dir.scale(d)).add(0, 2, 0);
            if (solid(level, p)) {
                break;
            }
            last = p;
        }
        Vec3 to = last;
        addEffect(bundle(level, lampPos().add(0, 0.5, 0), to, 10, 8, 2.5, 12.0F));
        level.playSound(null, this, SoundEvents.SNOWBALL_THROW, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /** The props blow: every light in the cavern goes out (temporarily), the crust is blasted off, stones fall. */
    private void goDark(ServerLevel level) {
        blackout = true;
        caveTimer = (int) Math.round(CAVEIN_EVERY * 0.5 * cooldownScale());
        sparkTimer = 40;
        if (chunks > 0) {
            chunks = 0;
            level.sendParticles(block(Blocks.RAW_GOLD_BLOCK.defaultBlockState()), getX(), getY() + 3, getZ(), 100, 1.5, 1.5, 1.5, 0.3);
        }
        entityData.set(DATA_FORM, BARE);
        Vec3 c = centre();
        BlockPos base = BlockPos.containing(c);
        int r = radius + 4;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        int lights = 0;
        vein.clear();
        List<BlockPos> ores = new ArrayList<>();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                if (dx * dx + dz * dz > r * r) {
                    continue;
                }
                for (int dy = -2; dy <= 26; dy++) {
                    p.set(base.getX() + dx, base.getY() + dy, base.getZ() + dz);
                    if (!level.isLoaded(p)) {
                        continue;
                    }
                    BlockState s = level.getBlockState(p);
                    if (s.isAir()) {
                        continue;
                    }
                    if (isLamp(s)) {
                        setTemp(level, p.immutable(), Blocks.AIR.defaultBlockState());
                        level.sendParticles(ParticleTypes.SMOKE, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 6, 0.2, 0.2, 0.2, 0.01);
                        lights++;
                    } else if (isOre(s) && exposed(level, p)) {
                        ores.add(p.immutable());
                    }
                }
            }
        }
        for (int i = 0; i < 160 && !ores.isEmpty(); i++) {
            vein.add(ores.remove(random.nextInt(ores.size())));
        }
        hitCircle(level, position(), 4.0, 12.0F, 1.4, 0.5);
        addEffect(WayfarerBoss.wave(position(), 14.0, 0.55, 12.0F, ParticleTypes.FLAME));
        for (int i = 0; i < 6; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double rr = random.nextDouble() * reach();
            addEffect(debris(level, clampToArena(c.add(Math.cos(a) * rr, 0, Math.sin(a) * rr), 0.8), 12.0F));
        }
        for (Player pl : fighters(level)) {
            addEffect(debris(level, clampToArena(pl.position(), 0.8), 12.0F));
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("mine_baron_dark"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.DEEPSLATE.defaultBlockState()),
                c.x, c.y + 14, c.z, 200, reach() * 0.6, 3.0, reach() * 0.6, 0.05);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2, getZ(), 6, 2.0, 1.0, 2.0, 0);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        if (lights > 0) {
            level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
    }

    /** Any vanilla block that gives light and holds nothing (lanterns, torches, candles, glowstone...), never fluids. */
    private static boolean isLamp(BlockState s) {
        if (s.getLightEmission() <= 0 || s.hasBlockEntity() || s.is(Blocks.LIGHT) || s.is(Blocks.FIRE) || s.is(Blocks.SOUL_FIRE)
                || !s.getFluidState().isEmpty()) {
            return false;
        }
        return net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(s.getBlock()).getNamespace().equals("minecraft");
    }

    private static boolean isOre(BlockState s) {
        return s.is(Blocks.GOLD_ORE) || s.is(Blocks.DEEPSLATE_GOLD_ORE) || s.is(Blocks.RAW_GOLD_BLOCK) || s.is(Blocks.GOLD_BLOCK)
                || s.is(Blocks.COPPER_ORE) || s.is(Blocks.DEEPSLATE_COPPER_ORE) || s.is(Blocks.RAW_COPPER_BLOCK);
    }

    private static boolean exposed(ServerLevel level, BlockPos p) {
        for (Direction d : Direction.values()) {
            if (level.getBlockState(p.relative(d)).isAir()) {
                return true;
            }
        }
        return false;
    }

    /** The vein sparks: a crackle on an exposed ore face (0.6 s, a flicker of light), then it arcs: 7 within 3.5. */
    private void spark(ServerLevel level) {
        Vec3 at;
        BlockPos ore = vein.isEmpty() ? null : vein.get(random.nextInt(vein.size()));
        BlockPos lit = null;
        if (ore != null) {
            BlockPos open = null;
            for (Direction d : Direction.values()) {
                if (level.getBlockState(ore.relative(d)).isAir()) {
                    open = ore.relative(d);
                    break;
                }
            }
            if (open == null) {
                return;
            }
            at = Vec3.atCenterOf(open);
            lit = open;
        } else {
            double a = random.nextDouble() * Math.PI * 2;
            at = centre().add(Math.cos(a) * 3, 3, Math.sin(a) * 3);
        }
        BlockPos light = lit;
        int[] t = {0};
        addEffect((boss, lvl) -> {
            int k = t[0]++;
            MineBaron m = boss instanceof MineBaron mb ? mb : null;
            if (k == 0 && m != null && light != null) {
                m.placeLight(lvl, light, 9);
            }
            if (k < 12) {
                lvl.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 3, 0.3, 0.3, 0.3, 0.15);
                if (k % 2 == 0) {
                    lvl.sendParticles(GOLD, at.x, at.y, at.z, 2, 0.4, 0.4, 0.4, 0);
                }
                if (k % 4 == 0) {
                    lvl.playSound(null, at.x, at.y, at.z, SoundEvents.COPPER_BULB_TURN_ON, SoundSource.HOSTILE, 1.5F, 1.4F);
                }
                return false;
            }
            if (k == 12) {
                for (LivingEntity e : boss.victims(lvl, at, 3.5)) {
                    Vec3 to = e.position().add(0, 1, 0);
                    if (to.distanceTo(at) > 4.0) {
                        continue;
                    }
                    for (double s = 0; s <= 1.0; s += 0.1) {
                        Vec3 q = at.lerp(to, s);
                        lvl.sendParticles(ParticleTypes.ELECTRIC_SPARK, q.x, q.y, q.z, 1, 0.05, 0.05, 0.05, 0);
                    }
                    boss.strike(lvl, e, 7.0F, 0.4, 0.2);
                }
                lvl.sendParticles(ParticleTypes.WAX_OFF, at.x, at.y, at.z, 16, 0.5, 0.5, 0.5, 0.3);
                lvl.playSound(null, at.x, at.y, at.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 1.2F, 1.6F);
                if (m != null && light != null) {
                    m.placeLight(lvl, light, 14);
                }
                return false;
            }
            if (k >= 18) {
                if (m != null && light != null) {
                    m.clearTemp(lvl, light);
                }
                return true;
            }
            return false;
        });
    }

    // ------------------------------------------------------------------ temporary blocks and lights

    private void setTemp(ServerLevel level, BlockPos p, BlockState state) {
        Temp old = temps.get(p.asLong());
        temps.put(p.asLong(), new Temp(old != null ? old.original() : level.getBlockState(p), state));
        level.setBlock(p, state, 3);
    }

    /** An invisible light block of {@code lvl} in the air cell {@code p} (or the one above); null when none is free. */
    private @Nullable BlockPos placeLight(ServerLevel level, BlockPos p, int lvl) {
        for (BlockPos q : new BlockPos[] {p, p.above()}) {
            if (!level.isLoaded(q)) {
                continue;
            }
            BlockState now = level.getBlockState(q);
            Temp mine = temps.get(q.asLong());
            if (now.isAir() || (mine != null && now.is(Blocks.LIGHT))) {
                setTemp(level, q, Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, lvl));
                return q;
            }
        }
        return null;
    }

    /** Puts one changed block back (only if it is still what was put there). */
    private void clearTemp(ServerLevel level, BlockPos p) {
        Temp t = temps.remove(p.asLong());
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        if (level.getBlockState(p).getBlock() == t.placed().getBlock()) {
            level.setBlock(p, t.original(), 3);
        }
    }

    /** The helmet lantern's light follows him in the dark (a light block moved every other tick). */
    private void moveLamp(ServerLevel level) {
        BlockPos want = BlockPos.containing(lampPos());
        if (want.equals(lampAt)) {
            return;
        }
        if (lampAt != null) {
            clearTemp(level, lampAt);
        }
        lampAt = placeLight(level, want, 14);
        if (lampAt == null) {
            lampAt = placeLight(level, want.below(), 14);
        }
    }

    /** A second moving light (the burning fuse, the lamp's beam); null puts it out. */
    private void moveBeam(ServerLevel level, @Nullable BlockPos to, int lvl) {
        if (beamAt != null && !beamAt.equals(to)) {
            clearTemp(level, beamAt);
            beamAt = null;
        }
        if (to != null && beamAt == null) {
            beamAt = placeLight(level, to, lvl);
        }
    }

    /** Every changed block goes back (only where it is still the one set), top first. */
    private void restoreAll(ServerLevel level) {
        lampAt = null;
        beamAt = null;
        if (!staleTemps.isEmpty()) {
            for (SavedTemp s : staleTemps) {
                temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed()));
            }
            staleTemps.clear();
        }
        if (temps.isEmpty()) {
            return;
        }
        List<Map.Entry<Long, Temp>> all = new ArrayList<>(temps.entrySet());
        all.sort((a, b) -> Integer.compare(BlockPos.getY(b.getKey()), BlockPos.getY(a.getKey())));
        temps.clear();
        for (Map.Entry<Long, Temp> e : all) {
            BlockPos p = BlockPos.of(e.getKey());
            if (!level.isLoaded(p)) {
                continue;
            }
            if (level.getBlockState(p).getBlock() == e.getValue().placed().getBlock()) {
                level.setBlock(p, e.getValue().original(), 3);
            }
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 3.0, getZ(), 8, 0.8, 1.0, 0.8, 0.02);
            level.playSound(null, this, SoundEvents.ANVIL_HIT, SoundSource.HOSTILE, 1.0F, 1.4F);
            return false;
        }
        BossAttack cur = currentAttack();
        if (cur != null && "orebreak".equals(cur.name)) {
            amount *= 1.3F;                                 // dazed: wide open
        }
        if (armoured() && source.getEntity() instanceof Player) {
            Vec3 from = source.getSourcePosition() != null ? source.getSourcePosition() : source.getEntity().position();
            if (behind(from) && amount >= 3.0F && tickCount - lastChunk >= 8) {
                knockChunk(level);                          // a geode off his back: the hit goes through in full
            } else {
                amount *= 0.2F;                             // the ore crust takes it
                Vec3 at = from.subtract(position()).multiply(1, 0, 1);
                at = at.lengthSqr() < 1.0E-4 ? forward() : at.normalize();
                level.sendParticles(block(Blocks.GOLD_ORE.defaultBlockState()), getX() + at.x * 1.3, getY() + 2.8,
                        getZ() + at.z * 1.3, 8, 0.3, 0.4, 0.3, 0.1);
                level.playSound(null, this, SoundEvents.STONE_HIT, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && regilding && cur != null && "regild".equals(cur.name) && source.getEntity() instanceof Player) {
            regildDamage += amount;
            if (regildDamage >= 60.0F * (1.0F + 0.25F * (scaledPlayers() - 1))) {
                regilding = false;                          // the stream of gold broken: he reels
                level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                chain(level, "orebreak");
            }
        }
        return hurt;
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardAdds(level);
        for (FallingBlockEntity fb : flying) {
            if (fb.isAlive()) {
                fb.discard();
            }
        }
        flying.clear();
        keg = null;
        fuseFrom = null;
    }

    /** Back to the first phase (the fight was reset): no crust, lights back, base speed. */
    private void resetForm(ServerLevel level) {
        chunks = 0;
        chunksMax = 0;
        gildAt = -1;
        regilding = false;
        bandits = false;
        blackout = false;
        wasPhaseTwo = false;
        roarUntil = -1;
        guard = 0;
        behindTicks = 0;
        vein.clear();
        entityData.set(DATA_FORM, BARE);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("mine_baron_dark"));
        }
        cleanUp(level);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleTemps.isEmpty()) {                       // saved by an unload: put back on the first tick
            restoreAll(level);
        }
        if (guard > 0) {
            guard--;
        }
        flying.removeIf(fb -> !fb.isAlive());
        BossAttack cur = currentAttack();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!temps.isEmpty() || !adds.isEmpty() || !flying.isEmpty())) {
            cleanUp(level);                                // the arena emptied (death, flight)
        }
        if (phase() == 1 && (wasPhaseTwo || blackout || chunks > 0 || entityData.get(DATA_FORM) != BARE)) {
            resetForm(level);                              // the fight was reset
        }
        if (gildAt > 0 && tickCount >= gildAt) {           // the phase-2 roar: the crust locks on
            gildAt = -1;
            if (!blackout) {
                gild(level);
            }
        }
        if (regilding && (cur == null || !"regild".equals(cur.name))) {
            regilding = false;                             // the re-gilding was cut short (stagger)
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil && gildAt < 0;
        if (phase() == 2 && !blackout && !armoured() && regildTimer > 0 && fighting) {
            regildTimer--;
        }
        // the exhaust: someone loitering at his back
        boolean someoneBehind = false;
        if (fighting && anyone) {
            for (Player p : fighters(level)) {
                if (p.distanceTo(this) < 6.0 && behind(p.position())) {
                    someoneBehind = true;
                    break;
                }
            }
        }
        behindTicks = someoneBehind ? behindTicks + 1 : Math.max(0, behindTicks - 2);
        Integer lastExhaust = lastStart.get("exhaust");
        if (free) {
            if (phase() == 2 && !blackout && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "blackout");
            } else if (behindTicks >= (armoured() ? 40 : 26) && (lastExhaust == null || tickCount - lastExhaust > 100 * cooldownScale())) {
                behindTicks = 0;
                noteStart("exhaust");
                chain(level, "exhaust");
            } else if (phase() == 2 && !blackout && !armoured() && regildTimer <= 0) {
                regildTimer = (int) Math.round(REGILD_EVERY * cooldownScale());
                chain(level, "regild");
            } else if (blackout && --caveTimer <= 0) {
                caveTimer = (int) Math.round(CAVEIN_EVERY * cooldownScale());
                noteStart("cavein");
                chain(level, "cavein");
            }
        }
        if (blackout && anyone) {
            if (tickCount % 2 == 0) {
                moveLamp(level);
            }
            if (--sparkTimer <= 0) {
                sparkTimer = Math.max(24, (int) Math.round(50 * cooldownScale()));
                int n = 1 + (scaledPlayers() - 1) / 2;
                for (int i = 0; i < n; i++) {
                    spark(level);
                }
            }
            BossAttack now = currentAttack();
            boolean beaming = now != null && "glare".equals(now.name);
            if (beaming && beamAt == null) {
                moveBeam(level, BlockPos.containing(lampPos().add(forward().scale(5)).add(0, -2, 0)), 13);
            } else if (!beaming && (now == null || !"fuseline".equals(now.name)) && beamAt != null) {
                moveBeam(level, null, 0);
            }
        }
        // the weak spots: glowing geodes on his back while the crust is on
        if (armoured() && tickCount % 4 == 0) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            Vec3 back = new Vec3(Mth.sin(yaw), 0, -Mth.cos(yaw));
            Vec3 side = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
            for (int k = 0; k < chunks; k++) {
                double sx = (k % 2 == 0 ? -0.5 : 0.5);
                double y = 3.6 - (k / 2) * 0.8;
                Vec3 q = position().add(back.scale(1.4)).add(side.scale(sx)).add(0, y, 0);
                level.sendParticles(GOLD, q.x, q.y, q.z, 1, 0.08, 0.08, 0.08, 0);
                level.sendParticles(ParticleTypes.WAX_ON, q.x, q.y, q.z, 1, 0.1, 0.1, 0.1, 0.02);
            }
        }
        // ambience: the boiler chuffs, the lamp's glow, embers in the dark
        if (tickCount % 10 == 0) {
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 6.0, getZ(), 1, 0.2, 0.1, 0.2, 0.01);
        }
        if (tickCount % 6 == 0) {
            Vec3 lamp = lampPos();
            level.sendParticles(LAMP, lamp.x, lamp.y, lamp.z, 1, 0.05, 0.05, 0.05, 0);
        }
        if (tickCount % 120 == 0) {
            level.playSound(null, this, SoundEvents.IRON_GOLEM_STEP, SoundSource.HOSTILE, 1.5F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        wasPhaseTwo = true;
        int roar = GREED >= 0 && GREED < actionTicks().length ? actionTicks()[GREED] : 40;
        roarUntil = tickCount + roar + 6;
        gildAt = tickCount + 30;
        regildTimer = (int) Math.round(REGILD_EVERY * cooldownScale());
        if (keg != null) {
            keg = null;
            fuseFrom = null;
        }
        level.sendParticles(GOLD, getX(), getY() + 3, getZ(), 80, 1.5, 1.5, 1.5, 0.1);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(block(Blocks.RAW_GOLD_BLOCK.defaultBlockState()), getX(), getY() + 3, getZ(), 120, 1.5, 2.0, 1.5, 0.3);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 4, getZ(), 60, 1.0, 1.5, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.4F);
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
            output.putLong("BaronCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("BaronRadius", radius);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("BaronBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("BaronCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("BaronRadius", 20);
        staleTemps.clear();
        input.read("BaronBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
        // a reload mid-fight: lights come back (first tick), the crust and the dark are lost with them
        chunks = 0;
        blackout = false;
        entityData.set(DATA_FORM, BARE);
    }
}
