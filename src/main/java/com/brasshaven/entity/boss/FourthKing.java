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
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DecoratedPotBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.FourthKing.BEAM_HIGH;
import static com.brasshaven.generated.MobAnims.FourthKing.BEAM_LOW;
import static com.brasshaven.generated.MobAnims.FourthKing.DRAIN;
import static com.brasshaven.generated.MobAnims.FourthKing.FLAIL;
import static com.brasshaven.generated.MobAnims.FourthKing.PROCESSION;
import static com.brasshaven.generated.MobAnims.FourthKing.ROAR;
import static com.brasshaven.generated.MobAnims.FourthKing.SANDBURST;
import static com.brasshaven.generated.MobAnims.FourthKing.SANDFALL;
import static com.brasshaven.generated.MobAnims.FourthKing.SEAL;
import static com.brasshaven.generated.MobAnims.FourthKing.SMITE;
import static com.brasshaven.generated.MobAnims.FourthKing.STAGGER;
import static com.brasshaven.generated.MobAnims.FourthKing.SWARM;
import static com.brasshaven.generated.MobAnims.FourthKing.VERDICT;

/**
 * Le Quatrième Roi (The Fourth King), champion of the Necropolis of Kings: the seated colossus whose face was
 * chiselled away, risen as a gaunt 6-block mummified monarch in a cracked sandstone-and-lapis mask, a royal flail in
 * his right hand and a scarab sceptre in his left. He waits in the king's arena at the bottom of the tombs (radius 16,
 * 18 high, a star ceiling with an oculus up to the hypostyle hall, a dais with two seated colossi, jackal statues).
 * <p>A deliberately hard fight: 640 health, armour 12, poise 120, hits of 6 to 20. Three phases:
 * <ul>
 *     <li>Phase 1: the <b>flail combo</b> (forehand, backhand, overhead line), the <b>smite</b> (an overhead slam),
 *     the <b>low beam</b> (the sceptre's ray sweeps the floor from his right to his left: jump it), the <b>high
 *     beam</b> (a ray at head height scythes across ahead of him and back: no jumping it and nothing to duck under,
 *     step out of its arc or under his arm), the <b>sandfall</b> (sand pours from the ceiling onto marked spots), the
 *     <b>scarab swarm</b> (a swarm that hunts one player a little faster than walking: sprint, or lead it under a
 *     sandfall to bury it), the <b>procession</b> (a gliding gap-closer ending in an overhead lash), the
 *     <b>sandburst</b> (anti-hug). Four canopic jars (more in co-op) stand round the room: every 20 s or so he
 *     <b>drains</b> the jars still standing to heal; break them first (one hit, or an arrow).</li>
 *     <li>Phase 2 (a roar at 65%): the broken jars are raised again, he is faster, his beams sweep wider, he chains
 *     beams and lashes, two swarms hunt two players, more sand falls.</li>
 *     <li>Phase 3 (at 30%): the <b>seal</b>: invulnerable 3 s, the tomb seals into darkness (the oculus is stopped up,
 *     the lanterns and the star lights die, Darkness on everyone), and the spirits of the three other kings appear
 *     round the walls: one after another their <b>gaze</b> sweeps across the floor (a cone of lapis light: stay out of
 *     it); every 15 s the <b>verdict</b>: he kneels and all three gaze at once, wheeling round the room.</li>
 * </ul>
 * Every block he places (the jars, the plug in the oculus) or removes (the lanterns, the star lights) is temporary:
 * put back when the arena empties, when the fight resets, when he dies or is removed, and on the first tick after a
 * reload.
 */
public class FourthKing extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 5.9F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double FLAIL_RANGE = 5.5;
    private static final double FLAIL_HALF = 70;
    private static final double SAND_R = 2.2;
    private static final double JAR_R = 9.5;
    private static final int DRAIN_EVERY = 420;
    private static final int VERDICT_EVERY = 300;
    private static final double GAZE_HALF = 11.0;
    private static final DustParticleOptions GOLD_DUST = new DustParticleOptions(0xF2C14E, 1.3F);
    private static final DustParticleOptions LAPIS = new DustParticleOptions(0x3A5BD0, 1.4F);
    private static final DustParticleOptions LAPIS_L = new DustParticleOptions(0x9CC0FF, 1.2F);
    private static final DustParticleOptions SAND_DUST = new DustParticleOptions(0xE0C890, 1.5F);
    private static final DustParticleOptions SCARAB = new DustParticleOptions(0x1E2A4A, 1.0F);
    private static final DustParticleOptions SCARAB_G = new DustParticleOptions(0x6FA27A, 0.8F);
    private static final BlockParticleOption SAND_BLOCK = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.SAND.defaultBlockState());
    private static final BlockParticleOption SAND_FALLING = new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.SAND.defaultBlockState());
    private static final BlockParticleOption STONE_BITS = new BlockParticleOption(ParticleTypes.BLOCK,
            Blocks.SMOOTH_SANDSTONE.defaultBlockState());

    /** A block he changed: the state it replaced and the state he set (only put back while it is still his). */
    private record Temp(BlockState original, BlockState placed) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    /** A scarab swarm hunting one player. */
    private static final class Swarm {
        Vec3 pos;
        final UUID prey;
        int life;
        boolean dead;

        Swarm(Vec3 pos, UUID prey, int life) {
            this.pos = pos;
            this.prey = prey;
            this.life = life;
        }
    }

    private @Nullable Vec3 centre;
    private int radius = 16;
    private final Map<Long, Temp> temps = new LinkedHashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();
    private final List<BlockPos> jars = new ArrayList<>();
    private boolean jarsRaised;
    private int drainTimer = 200;
    private final List<Swarm> swarms = new ArrayList<>();
    private final List<Vec3> spots = new ArrayList<>();
    private final Map<UUID, Integer> lastBeamHit = new HashMap<>();
    private @Nullable Vec3 glideFrom;
    private @Nullable Vec3 glideTo;
    private final List<UUID> glideHit = new ArrayList<>();
    private boolean wasPhaseTwo;
    private int roarUntil = -1;
    // phase 3: the sealed tomb
    private boolean sealed;
    private int guard;
    private int verdictTimer;
    private final Vec3[] spirits = new Vec3[3];
    private int gazeIndex;
    private int gazeTick = -40;
    private double gazeOffset;
    private double verdictPhase;

    public FourthKing(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 640.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.FourthKing.TICKS;
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

    /** Usable floor radius round the seal (the king's arena: 13 to the jackals, 15.6 to the columns). */
    private double reach() {
        return Math.max(6.0, Math.min(14.0, radius - 2.0));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Horizontal vector rotated by {@code degrees} (positive: toward the boss's right). */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    private static double floorY(ServerLevel level, double x, double y, double z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(y + 2), Mth.floor(z));
        for (int i = 0; i < 8; i++) {
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return p.getY() + 1.0;
            }
            p.move(0, -1, 0);
        }
        return Double.NaN;
    }

    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 2.5) {
            return null;
        }
        for (int dy = 0; dy < 6; dy++) {
            BlockPos p = BlockPos.containing(x, y + dy, z);
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return null;
            }
        }
        return new Vec3(x, y, z);
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

    private Vec3 landingSpot(ServerLevel level, Vec3 want) {
        Vec3 p = clampToArena(want, 1.5);
        Vec3 c = centre();
        for (int i = 0; i < 12; i++) {
            Vec3 q = p.lerp(c, i / 12.0);
            Vec3 s = safeSpot(level, q.x, q.z);
            if (s != null) {
                return s;
            }
        }
        return c;
    }

    /** The ceiling over the arena (first solid block above the floor, off the oculus), or 18 up. */
    private double ceilingY(ServerLevel level) {
        Vec3 c = centre();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dy = 3; dy <= 26; dy++) {
            p.set(Mth.floor(c.x) + 4, Mth.floor(c.y) + dy, Mth.floor(c.z));
            if (!level.getBlockState(p).isAir()) {
                return p.getY();
            }
        }
        return c.y + 18;
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 14, radius + 4),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    private boolean clearLine(ServerLevel level, Vec3 from, Vec3 to) {
        return level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this)).getType()
                == HitResult.Type.MISS;
    }

    private void turnToward(@Nullable LivingEntity t, float maxTurn) {
        if (t == null) {
            return;
        }
        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private void faceToward(Vec3 p) {
        snapFacing((float) (Mth.atan2(p.z - getZ(), p.x - getX()) * (180.0 / Math.PI)) - 90.0F);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // flail combo: raised behind his right shoulder (0.7 s, the arc drawn in gold), a forehand lash, a backhand
        // 0.5 s later after a turn toward you, then the flail brought over his head and down a line at 1.7 s
        out.add(BossAttack.of("flail").anim(FLAIL).timing(14, 26, 14).range(0, 6.5).cooldown(60).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, FLAIL_RANGE, FLAIL_HALF, GOLD_DUST);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof FourthKing k)) {
                        return;
                    }
                    if (tick == 0 || tick == 10) {
                        k.lash(level, 12.0F);
                    }
                    if (tick == 3 || tick == 13) {
                        k.turnToward(t, 30.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, FLAIL_RANGE, FLAIL_HALF, GOLD_DUST);
                    }
                    if (tick > 13 && tick < 20 && tick % 2 == 0) {
                        for (double d = 1.0; d <= 7.0; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(GOLD_DUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 20) {
                        b.hitLine(level, 7.0, 1.3, 15.0F, 0.7);
                        Vec3 p = b.ahead(5.0);
                        level.sendParticles(SAND_BLOCK, p.x, p.y + 0.3, p.z, 40, 1.0, 0.3, 1.0, 0.1);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "smite" : "beam_high");
                    }
                })
                .build());
        // smite: the flail swung up over his head in both hands (1.0 s, the circle drawn 3.5 ahead), crashed into the
        // floor: 20 in r 3. Phase 2: a ring of sand rolls out to 10 (jump it)
        out.add(BossAttack.of("smite").anim(SMITE).timing(20, 4, 18).range(0, 7.0).cooldown(90).weight(9).track(true)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 3.0, tick > 12 ? LAPIS : GOLD_DUST);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.HUSK_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 p = b.ahead(3.5);
                    b.hitCircle(level, p, 3.0, 20.0F, 1.0, 0.4);
                    level.sendParticles(SAND_BLOCK, p.x, p.y + 0.3, p.z, 70, 1.5, 0.3, 1.5, 0.15);
                    level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.5, p.z, 1, 0, 0, 0, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(p, 10, 0.5, 9.0F, SAND_DUST));
                    }
                })
                .build());
        // low beam: the sceptre lowered to the floor at his right (1.1 s, a gold line on the floor where it starts and
        // the arc it will cover); the ray sweeps the floor from his right to his left in 2 s: 15 + Slowness to anyone
        // with their feet on the floor. Jump it as it passes
        out.add(BossAttack.of("beam_low").anim(BEAM_LOW).timing(22, 40, 16).range(0, 16.0).cooldown(160).weight(9)
                .start((b, level, t, tick) -> lastBeamHit.clear())
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof FourthKing k)) {
                        return;
                    }
                    if (tick % 2 == 0) {
                        Vec3 dir = rotate(b.forward(), k.lowSweep());
                        for (double d = 1.5; d <= k.beamLength(); d += 0.8) {
                            Vec3 p = b.position().add(dir.scale(d));
                            level.sendParticles(GOLD_DUST, p.x, p.y + 0.2, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, k.beamLength(), k.lowSweep(), GOLD_DUST);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        double span = k.lowSweep();
                        double a = span - 2 * span * tick / 39.0;
                        k.beam(level, a, 0.35, 15.0F, true, 0.0);
                        if (tick % 10 == 0) {
                            level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.5F, 1.6F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "beam_high");
                    }
                })
                .build());
        // high beam: the sceptre raised level with his eyes (1.0 s, the arc it covers drawn in lapis, a gold safe ring
        // at his feet); the ray scythes across ahead of him at head height and back in 1.5 s: 16. Nothing to jump and
        // nothing to duck under: step out of the arc, behind him, or right under his arm (2.5 blocks)
        out.add(BossAttack.of("beam_high").anim(BEAM_HIGH).timing(20, 30, 16).range(0, 16.0).cooldown(150).weight(8)
                .start((b, level, t, tick) -> lastBeamHit.clear())
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof FourthKing k)) {
                        return;
                    }
                    if (tick % 3 == 0) {
                        double span = k.highSweep();
                        for (double a = -span; a <= span + 0.1; a += span / 6) {
                            Vec3 dir = rotate(b.forward(), a);
                            for (double d = 2.5; d <= k.beamLength(); d += 2.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(LAPIS, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                            }
                        }
                        b.telegraphRing(level, b.position(), 2.5, GOLD_DUST);
                        Vec3 tip = b.position().add(0, 4.6, 0);
                        level.sendParticles(LAPIS_L, tip.x, tip.y, tip.z, 3, 0.3, 0.3, 0.3, 0.01);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.5F, 1.2F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        double a = k.highSweep() * Math.cos(2 * Math.PI * tick / 30.0);
                        k.beam(level, a, 1.6, 16.0F, false, 2.5);
                        if (tick % 8 == 0) {
                            level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.5F, 1.9F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.0 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "flail");
                    }
                })
                .build());
        // sandfall: the sceptre thrust up at the ceiling (0.9 s); sand starts trickling over marked spots (on the
        // target and strays; phase 2 on every player too) and 1.5 s later pours down: 14 in r 2.2, Slowness II,
        // blinded a moment. A sandfall buries any scarab swarm under it
        out.add(BossAttack.of("sandfall").anim(SANDFALL).timing(18, 6, 14).range(0, 24.0).cooldown(170).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (b instanceof FourthKing k && tick == 0) {
                        k.pickSandSpots(level, t);
                    }
                    Vec3 tip = b.position().add(0, 6.0, 0);
                    level.sendParticles(SAND_FALLING, tip.x, tip.y, tip.z, 3, 0.4, 0.2, 0.4, 0);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.SAND_FALL, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        double ceiling = k.ceilingY(level);
                        int delay = b.phase() == 2 ? 26 : 30;
                        for (Vec3 p : k.spots) {
                            b.addEffect(k.sandColumn(p, ceiling, delay, 14.0F));
                        }
                        k.spots.clear();
                        level.playSound(null, b, SoundEvents.GRAVEL_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .build());
        // swarm: the sceptre levelled at one of you, the scarab's wings opening (0.8 s, a ring under the prey); a swarm
        // pours out and hunts that player for 12 s, a little faster than walking: 3 + Poison + Hunger every half second
        // in it. Sprint, or lead it under a sandfall. Phase 2: a second swarm after another player
        out.add(BossAttack.of("swarm").anim(SWARM).timing(16, 4, 14).range(0, 22.0).cooldown(260).weight(7)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 1.4, SCARAB_G);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.SILVERFISH_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        k.releaseSwarms(level, t);
                    }
                })
                .build());
        // procession: he leans into a long gliding stride (0.7 s, a gold line to where he will stop), sweeps across the
        // floor in 8 ticks (12 to anyone in his path) and at 1.3 s brings the flail down a line ahead: 16
        out.add(BossAttack.of("procession").anim(PROCESSION).timing(14, 16, 14).range(8.0, 24.0).cooldown(140).weight(8)
                .start((b, level, t, tick) -> glideHit.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && t != null && b instanceof FourthKing k) {
                        Vec3 to = k.clampToArena(t.position(), 1.5);
                        double len = flatDist(b.position(), to);
                        for (double d = 1.5; d < len; d += 1.0) {
                            Vec3 p = b.position().lerp(to, d / len);
                            level.sendParticles(GOLD_DUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.HUSK_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        Vec3 target = t != null ? t.position() : b.ahead(10);
                        Vec3 dir = target.subtract(b.position()).multiply(1, 0, 1);
                        double len = dir.length();
                        dir = len < 1.0E-3 ? b.forward() : dir.scale(1.0 / len);
                        k.glideFrom = b.position();
                        k.glideTo = k.landingSpot(level, b.position().add(dir.scale(Math.max(0, len - 2.5))));
                        k.faceToward(target);
                        level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        k.glideStep(level, tick);
                        if (tick > 8 && tick < 12 && tick % 2 == 0) {
                            for (double d = 1.0; d <= 6.0; d += 1.0) {
                                Vec3 p = b.ahead(d);
                                level.sendParticles(GOLD_DUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                        if (tick == 12) {
                            b.hitLine(level, 6.0, 1.3, 16.0F, 0.8);
                            Vec3 p = b.ahead(4.0);
                            level.sendParticles(SAND_BLOCK, p.x, p.y + 0.3, p.z, 40, 1.0, 0.3, 1.0, 0.1);
                            level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.7F);
                        }
                    }
                })
                .build());
        // sandburst: he draws in, hunched (0.6 s, a ring of sand at his feet), then flings his arms out: sand bursts all
        // round him: 11 in r 4.5. Phase 2: a ring of sand rolls on to 8 (jump it)
        out.add(BossAttack.of("sandburst").anim(SANDBURST).timing(12, 3, 12).range(0, 4.5).cooldown(70).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, SAND_DUST);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.5, 11.0F, 1.2, 0.3);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 8, 0.5, 7.0F, SAND_DUST));
                    }
                    level.sendParticles(SAND_BLOCK, b.getX(), b.getY() + 0.6, b.getZ(), 80, 2.2, 0.5, 2.2, 0.15);
                    level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- scheduled (range 999, weight 0: never rolled)
        // drain: every ~20 s while canopic jars stand and he is hurt: sceptre lifted, a hand clawed toward the jars
        // (1.0 s, a ring round every jar, a stream from each to him); held 2.5 s, then each jar still standing heals
        // him 3.5% of his health (phase 2: 4.5%). Break the jars before it ends
        out.add(BossAttack.of("drain").anim(DRAIN).timing(20, 50, 16).range(999, 999).cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 3.0F, 0.5F))
                .windup((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        k.drainStreams(level, tick, true);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        k.drainStreams(level, tick, false);
                        if (tick == 49) {
                            k.drainHeal(level);
                        }
                    }
                })
                .build());
        // seal (phase 3, once): arms raised to the ceiling (1.5 s, invulnerable, sand pouring from the vault), his fists
        // come down: a ring of sand (12, jump it), the tomb seals into darkness and the three kings' spirits appear
        out.add(BossAttack.of("seal").anim(SEAL).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 62;
                    level.playSound(null, b, SoundEvents.AMBIENT_CAVE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof FourthKing k)) {
                        return;
                    }
                    Vec3 c = k.centre();
                    double r = k.reach();
                    double top = c.y + 14;
                    level.sendParticles(SAND_FALLING, c.x, top, c.z, 12, r * 0.5, 0.5, r * 0.5, 0);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.35, SAND_DUST);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 3.0F, 0.3F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        k.sealTomb(level);
                    }
                })
                .build());
        // verdict (phase 3, every 15 s): he kneels, arms spread, face lifted to his brothers (1.2 s, their eyes flare);
        // for 4 s all three spirits gaze at once, their three cones wheeling round the room in and out: 8 + Wither
        out.add(BossAttack.of("verdict").anim(VERDICT).phaseTwo().timing(24, 80, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    lastBeamHit.clear();
                    verdictPhase = b.getRandom().nextDouble() * 360;
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof FourthKing k && tick % 2 == 0) {
                        for (int i = 0; i < 3; i++) {
                            Vec3 aim = k.verdictAim(i, 0);
                            b.telegraphRing(level, aim, 2.0, LAPIS);
                            Vec3 s = k.spirits[i];
                            if (s != null) {
                                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, s.x, s.y + 0.4, s.z, 3, 0.3, 0.3, 0.3, 0.02);
                            }
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FourthKing k) {
                        for (int i = 0; i < 3; i++) {
                            k.gaze(level, i, k.verdictAim(i, tick), 8.0F);
                        }
                        if (tick % 20 == 0) {
                            level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
                        }
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void lash(ServerLevel level, float damage) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(FLAIL_HALF));
        for (LivingEntity e : victims(level, position(), FLAIL_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= FLAIL_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos) && e.getY() - getY() < 4) {
                strike(level, e, damage, 1.0, 0.2);
            }
        }
        for (double a = -FLAIL_HALF; a <= FLAIL_HALF; a += 12) {
            Vec3 p = position().add(rotate(fwd, a).scale(FLAIL_RANGE - 1.2));
            level.sendParticles(GOLD_DUST, p.x, p.y + 1.4, p.z, 2, 0.2, 0.3, 0.2, 0.02);
        }
        Vec3 c = ahead(3.0);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    private double beamLength() {
        return reach() + 3.0;
    }

    /** Half-span of the low sweep in degrees (100, phase 2: 120). */
    private double lowSweep() {
        return phase() == 2 ? 120 : 100;
    }

    /** Half-span of the high scythe in degrees (40, phase 2: 50). */
    private double highSweep() {
        return phase() == 2 ? 50 : 40;
    }

    /**
     * One tick of a sceptre beam at {@code angle} degrees from his facing (positive: his right), {@code height} over
     * the floor. Blocks stop it. Low beams only hurt whoever has their feet on the floor; high ones hurt everyone up
     * to 3.5 blocks over it, from {@code minDist} out. Once per 10 ticks per creature.
     */
    private void beam(ServerLevel level, double angle, double height, float damage, boolean low, double minDist) {
        Vec3 dir = rotate(forward(), angle);
        Vec3 from = position().add(dir.scale(0.8)).add(0, height, 0);
        Vec3 far = from.add(dir.scale(beamLength()));
        var hit = level.clip(new ClipContext(from, far, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        double len = hit.getType() == HitResult.Type.MISS ? beamLength() : hit.getLocation().distanceTo(from);
        for (double d = Math.max(0.5, minDist); d <= len; d += 0.7) {
            Vec3 p = from.add(dir.scale(d));
            level.sendParticles(low ? GOLD_DUST : LAPIS_L, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0);
        }
        Vec3 end = from.add(dir.scale(len));
        level.sendParticles(ParticleTypes.END_ROD, end.x, end.y, end.z, 1, 0.05, 0.05, 0.05, 0.01);
        for (LivingEntity e : victims(level, position(), len + 2)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            double dy = e.getY() - getY();
            boolean inHeight = low ? dy < 0.9 : dy < 3.5 && dy > -1.5;
            if (along < Math.max(0.8, minDist) || along > len || side > 0.75 + e.getBbWidth() / 2 || !inHeight) {
                continue;
            }
            Integer last = lastBeamHit.get(e.getUUID());
            if (last != null && tickCount - last < 10) {
                continue;
            }
            lastBeamHit.put(e.getUUID(), tickCount);
            strike(level, e, damage, 0.4, 0.1);
            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, low ? 1 : 0), this);
            level.sendParticles(ParticleTypes.CRIT, e.getX(), e.getY() + 1, e.getZ(), 10, 0.3, 0.4, 0.3, 0.2);
        }
    }

    /** Sand spots: on the target, strays round the room (2, phase 2: on every player too and 4 strays). */
    private void pickSandSpots(ServerLevel level, @Nullable LivingEntity target) {
        spots.clear();
        if (target != null) {
            spots.add(clampToArena(target.position(), 0.5));
        }
        if (phase() == 2) {
            for (Player p : fighters(level)) {
                if (p != target && spots.size() < 4) {
                    spots.add(clampToArena(p.position(), 0.5));
                }
            }
        }
        int strays = scaledCount(phase() == 2 ? 4 : 2) + (sealed ? 1 : 0);
        for (int i = 0, tries = 0; i < strays && tries < 30; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * Math.max(2, reach() - 3);
            Vec3 p = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
            boolean ok = true;
            for (Vec3 s : spots) {
                ok &= flatDist(s, p) >= SAND_R * 2;
            }
            if (ok) {
                spots.add(p);
                i++;
            }
        }
    }

    /** Sand trickling from the ceiling over {@code p} for {@code delay} ticks (a ring on the floor), then the pour. */
    private Effect sandColumn(Vec3 p, double ceiling, int delay, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, p, SAND_R, k < delay - 10 ? SAND_DUST : GOLD_DUST);
                    level.sendParticles(SAND_FALLING, p.x, ceiling - 0.2, p.z, 3 + k / 6, SAND_R * 0.4, 0.1, SAND_R * 0.4, 0);
                }
                return false;
            }
            for (double y = p.y; y < ceiling; y += 1.0) {
                level.sendParticles(SAND_BLOCK, p.x, y, p.z, 6, SAND_R * 0.35, 0.4, SAND_R * 0.35, 0.05);
            }
            level.sendParticles(SAND_BLOCK, p.x, p.y + 0.3, p.z, 50, SAND_R * 0.5, 0.2, SAND_R * 0.5, 0.15);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.GRAVEL_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
            for (LivingEntity e : boss.victims(level, p, SAND_R + 1)) {
                if (flatDist(e.position(), p) <= SAND_R + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 3.0) {
                    boss.strike(level, e, damage, 0.0, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), boss);
                    e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 25, 0), boss);
                }
            }
            if (boss instanceof FourthKing king) {
                for (Swarm s : king.swarms) {
                    if (!s.dead && flatDist(s.pos, p) <= SAND_R + 0.6) {
                        s.dead = true;                          // buried
                        level.sendParticles(SCARAB, s.pos.x, s.pos.y, s.pos.z, 30, 0.5, 0.4, 0.5, 0.05);
                        level.playSound(null, s.pos.x, s.pos.y, s.pos.z, SoundEvents.SILVERFISH_DEATH, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                }
            }
            return true;
        };
    }

    /** Swarms: one on the target (phase 2: and one on another player), never more than the cap alive. */
    private void releaseSwarms(ServerLevel level, @Nullable LivingEntity target) {
        swarms.removeIf(s -> s.dead);
        int cap = scaledCount(phase() == 2 ? 2 : 1);
        List<LivingEntity> prey = new ArrayList<>();
        if (target != null) {
            prey.add(target);
        }
        if (phase() == 2) {
            for (Player p : fighters(level)) {
                if (p != target) {
                    prey.add(p);
                }
            }
        }
        Vec3 from = position().add(rotate(forward(), -40).scale(1.2)).add(0, 4.0, 0);
        int n = 0;
        for (LivingEntity e : prey) {
            if (swarms.size() >= cap || n >= (phase() == 2 ? 2 : 1)) {
                break;
            }
            boolean hunted = false;
            for (Swarm s : swarms) {
                hunted |= s.prey.equals(e.getUUID());
            }
            if (hunted) {
                continue;
            }
            swarms.add(new Swarm(from, e.getUUID(), 240));
            n++;
        }
        level.sendParticles(SCARAB, from.x, from.y, from.z, 40, 0.6, 0.6, 0.6, 0.1);
        level.playSound(null, this, SoundEvents.SILVERFISH_HURT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void tickSwarms(ServerLevel level) {
        if (swarms.isEmpty()) {
            return;
        }
        double speed = phase() == 2 ? 0.23 : 0.19;
        for (Swarm s : swarms) {
            if (s.dead) {
                continue;
            }
            if (--s.life <= 0) {
                s.dead = true;
                level.sendParticles(SCARAB, s.pos.x, s.pos.y, s.pos.z, 20, 0.5, 0.4, 0.5, 0.05);
                continue;
            }
            Player prey = level.getPlayerByUUID(s.prey);
            if (prey == null || !prey.isAlive() || prey.isSpectator() || prey.isCreative()
                    || flatDist(prey.position(), centre()) > radius + 6) {
                s.dead = true;
                continue;
            }
            Vec3 want = prey.position().add(0, 0.6, 0);
            Vec3 d = want.subtract(s.pos);
            double len = d.length();
            if (len > 1.0E-3) {
                s.pos = s.pos.add(d.scale(Math.min(len, speed) / len));
            }
            level.sendParticles(SCARAB, s.pos.x, s.pos.y + 0.3, s.pos.z, 8, 0.6, 0.4, 0.6, 0.02);
            level.sendParticles(SCARAB_G, s.pos.x, s.pos.y + 0.3, s.pos.z, 2, 0.5, 0.3, 0.5, 0.02);
            if (tickCount % 20 == 0) {
                level.playSound(null, s.pos.x, s.pos.y, s.pos.z, SoundEvents.SILVERFISH_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.7F);
            }
            if (tickCount % 10 == 0) {
                for (LivingEntity e : victims(level, s.pos, 2.0)) {
                    if (flatDist(e.position(), s.pos) <= 1.4 + e.getBbWidth() / 2 && Math.abs(e.getY() + 0.6 - s.pos.y) < 2.0) {
                        e.hurtServer(level, damageSources().mobAttack(this), 3.0F);
                        e.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), this);
                        e.addEffect(new MobEffectInstance(MobEffects.HUNGER, 100, 1), this);
                    }
                }
            }
        }
        swarms.removeIf(s -> s.dead);
    }

    private void glideStep(ServerLevel level, int tick) {
        if (glideFrom == null || glideTo == null) {
            return;
        }
        if (tick <= 8) {
            Vec3 p = glideFrom.lerp(glideTo, tick / 8.0);
            teleportTo(p.x, glideTo.y, p.z);
            setDeltaMovement(Vec3.ZERO);
            level.sendParticles(SAND_BLOCK, getX(), getY() + 0.2, getZ(), 6, 0.5, 0.1, 0.5, 0.05);
            level.sendParticles(SAND_DUST, getX(), getY() + 2.5, getZ(), 3, 0.4, 1.0, 0.4, 0.02);
            for (LivingEntity e : victims(level, position(), 3.0)) {
                if (flatDist(e.position(), position()) <= 1.8 + e.getBbWidth() / 2 && !glideHit.contains(e.getUUID())) {
                    glideHit.add(e.getUUID());
                    strike(level, e, 12.0F, 1.0, 0.3);
                }
            }
        }
        if (tick == 8) {
            teleportTo(glideTo.x, glideTo.y, glideTo.z);
            level.playSound(null, this, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.5F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ the canopic jars (temporary blocks)

    /** Raises the jars (4, +1 per extra player, at most 6) round the room where they are missing. */
    private void raiseJars(ServerLevel level) {
        jarsRaised = true;
        jars.removeIf(p -> !level.getBlockState(p).is(Blocks.DECORATED_POT));
        int n = Math.min(6, 4 + (scaledPlayers() - 1));
        Vec3 c = centre();
        int raised = 0;
        for (int k = 0; k < n; k++) {
            double base = 45 + k * 360.0 / n;
            BlockPos at = null;
            outer:
            for (double dr : new double[] {0, -1, 1, -2}) {
                for (double da : new double[] {0, 8, -8, 16, -16}) {
                    double a = Math.toRadians(base + da);
                    BlockPos p = BlockPos.containing(c.x + Math.cos(a) * (JAR_R + dr), c.y, c.z + Math.sin(a) * (JAR_R + dr));
                    if (jars.contains(p) || nearJar(p)) {
                        at = null;
                        break outer;                       // this jar still stands
                    }
                    if (canHold(level, p)) {
                        at = p;
                        break outer;
                    }
                }
            }
            if (at == null) {
                continue;
            }
            Direction facing = Direction.getApproximateNearest(c.x - (at.getX() + 0.5), 0, c.z - (at.getZ() + 0.5));
            if (facing.getAxis().isVertical()) {
                facing = Direction.NORTH;
            }
            BlockState jar = Blocks.DECORATED_POT.defaultBlockState().setValue(DecoratedPotBlock.HORIZONTAL_FACING, facing);
            setTemp(level, at, jar);
            jars.add(at);
            raised++;
            level.sendParticles(SAND_BLOCK, at.getX() + 0.5, at.getY() + 0.5, at.getZ() + 0.5, 20, 0.4, 0.4, 0.4, 0.05);
            level.sendParticles(LAPIS_L, at.getX() + 0.5, at.getY() + 1.2, at.getZ() + 0.5, 10, 0.2, 0.3, 0.2, 0.02);
        }
        if (raised > 0) {
            level.playSound(null, BlockPos.containing(c), SoundEvents.DECORATED_POT_PLACE, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
    }

    private boolean nearJar(BlockPos p) {
        for (BlockPos j : jars) {
            if (j.distManhattan(p) <= 3) {
                return true;
            }
        }
        return false;
    }

    private boolean canHold(ServerLevel level, BlockPos p) {
        BlockPos below = p.below();
        return level.getBlockState(p).isAir() && level.getBlockState(p.above()).isAir()
                && level.getBlockState(below).isFaceSturdy(level, below, Direction.UP) && level.getBlockEntity(below) == null
                && level.getEntitiesOfClass(LivingEntity.class, new AABB(p)).isEmpty() && !temps.containsKey(p.asLong());
    }

    /** Jars broken by the players: they shatter (no pot dropped, the jar was his). */
    private void checkJars(ServerLevel level) {
        if (jars.isEmpty()) {
            return;
        }
        List<BlockPos> broken = new ArrayList<>();
        for (BlockPos p : jars) {
            if (level.isLoaded(p) && !level.getBlockState(p).is(Blocks.DECORATED_POT)) {
                broken.add(p);
            }
        }
        for (BlockPos p : broken) {
            jars.remove(p);
            for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, new AABB(p).inflate(1.5),
                    i -> i.getItem().is(Items.DECORATED_POT))) {
                item.discard();
            }
            level.sendParticles(LAPIS_L, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 30, 0.3, 0.4, 0.3, 0.08);
            level.sendParticles(ParticleTypes.SOUL, p.getX() + 0.5, p.getY() + 0.8, p.getZ() + 0.5, 6, 0.2, 0.3, 0.2, 0.03);
            level.playSound(null, p, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        }
    }

    private void drainStreams(ServerLevel level, int tick, boolean windup) {
        Vec3 to = position().add(0, 4.4, 0);
        for (BlockPos j : jars) {
            Vec3 from = Vec3.atCenterOf(j);
            if (tick % 2 == 0) {
                telegraphRing(level, Vec3.atBottomCenterOf(j), 1.2, windup ? LAPIS : LAPIS_L);
            }
            double len = from.distanceTo(to);
            double phase = (tick % 10) / 10.0;
            for (double d = phase; d < len; d += 1.0) {
                Vec3 p = from.lerp(to, d / len);
                level.sendParticles(windup ? LAPIS : ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y, p.z, 1, 0.03, 0.03, 0.03, 0);
            }
        }
        if (tick % 10 == 0) {
            level.playSound(null, this, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    private void drainHeal(ServerLevel level) {
        int n = jars.size();
        if (n == 0) {
            level.playSound(null, this, SoundEvents.WITHER_AMBIENT, SoundSource.HOSTILE, 2.0F, 1.4F);
            return;
        }
        float per = phase() == 2 ? 0.045F : 0.035F;
        heal(getMaxHealth() * per * n);
        level.sendParticles(LAPIS_L, getX(), getY() + 3, getZ(), 40 * n, 0.8, 1.6, 0.8, 0.05);
        level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    // ------------------------------------------------------------------ temporary blocks

    private void setTemp(ServerLevel level, BlockPos p, BlockState state) {
        Temp old = temps.get(p.asLong());
        temps.put(p.asLong(), new Temp(old != null ? old.original() : level.getBlockState(p), state));
        level.setBlock(p, state, 3);
    }

    /** Every changed block goes back (only where it is still the one he set), top first. */
    private void restoreAll(ServerLevel level) {
        jars.clear();
        jarsRaised = false;
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
            BlockState now = level.getBlockState(p);
            if (now.getBlock() == e.getValue().placed().getBlock()) {
                level.setBlock(p, e.getValue().original(), 3);
            }
        }
    }

    // ------------------------------------------------------------------ phase 3: the sealed tomb

    /** The oculus stopped up, the lanterns and the star lights out, the spirits of the three kings round the walls. */
    private void sealTomb(ServerLevel level) {
        sealed = true;
        verdictTimer = 200;
        gazeIndex = 0;
        gazeTick = -30;
        Vec3 c = centre();
        BlockPos base = BlockPos.containing(c);
        int r = radius + 2;
        int ceiling = (int) ceilingY(level);
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        int lights = 0;
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                if (dx * dx + dz * dz > r * r) {
                    continue;
                }
                for (int dy = 1; dy <= 22; dy++) {
                    p.set(base.getX() + dx, base.getY() + dy, base.getZ() + dz);
                    BlockState s = level.getBlockState(p);
                    if (s.is(Blocks.LANTERN) || s.is(Blocks.SOUL_LANTERN)) {
                        setTemp(level, p.immutable(), Blocks.AIR.defaultBlockState());
                        level.sendParticles(ParticleTypes.SMOKE, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 6, 0.2, 0.2, 0.2, 0.01);
                        lights++;
                    } else if (s.is(Blocks.OCHRE_FROGLIGHT) || s.is(Blocks.PEARLESCENT_FROGLIGHT) || s.is(Blocks.GLOWSTONE)) {
                        setTemp(level, p.immutable(), Blocks.DYED_TERRACOTTA.blue().defaultBlockState());
                        lights++;
                    }
                }
                // the oculus: open cells in the ceiling layer near the centre are stopped up with sandstone
                if (dx * dx + dz * dz <= 9) {
                    p.set(base.getX() + dx, ceiling, base.getZ() + dz);
                    if (level.getBlockState(p).isAir() && level.getBlockEntity(p) == null) {
                        setTemp(level, p.immutable(), Blocks.CHISELED_SANDSTONE.defaultBlockState());
                    }
                }
            }
        }
        // the spirits: three anchors round the walls, 9 blocks up (lower if the vault is lower)
        double rr = Math.max(4.0, reach() - 1.0);
        for (int i = 0; i < 3; i++) {
            double a = Math.toRadians(90 + i * 120);
            Vec3 s = null;
            for (double rad = rr; rad >= 3 && s == null; rad -= 1.5) {
                for (int up = 9; up >= 5; up--) {
                    Vec3 q = c.add(Math.cos(a) * rad, up, Math.sin(a) * rad);
                    if (level.getBlockState(BlockPos.containing(q)).isAir()) {
                        s = q;
                        break;
                    }
                }
            }
            spirits[i] = s != null ? s : c.add(Math.cos(a) * 4, 6, Math.sin(a) * 4);
            Vec3 sp = spirits[i];
            level.sendParticles(ParticleTypes.SOUL, sp.x, sp.y, sp.z, 30, 0.4, 0.8, 0.4, 0.05);
        }
        darken(level);
        addEffect(WayfarerBoss.wave(position(), 13, 0.55, 12.0F, SAND_DUST));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("fourth_king_sealed"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(SAND_BLOCK, c.x, c.y + 0.5, c.z, 200, reach() * 0.5, 0.3, reach() * 0.5, 0.1);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BRICKS_PLACE, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.HOSTILE, 3.0F, 0.5F);
        if (lights > 0) {
            level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
    }

    private void darken(ServerLevel level) {
        for (Player pl : fighters(level)) {
            pl.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0, false, false), this);
        }
    }

    private void lighten(ServerLevel level) {
        for (Player pl : fighters(level)) {
            pl.removeEffect(MobEffects.DARKNESS);
        }
    }

    /** The spirits: soul light in a crowned figure, their eyes burning lapis. */
    private void drawSpirits(ServerLevel level) {
        for (Vec3 s : spirits) {
            if (s == null) {
                continue;
            }
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, s.x, s.y - 1.0, s.z, 3, 0.25, 0.8, 0.25, 0.005);
            level.sendParticles(LAPIS, s.x, s.y + 0.2, s.z, 2, 0.2, 0.2, 0.2, 0);
            level.sendParticles(GOLD_DUST, s.x, s.y + 1.0, s.z, 2, 0.25, 0.1, 0.25, 0);
            level.sendParticles(ParticleTypes.END_ROD, s.x, s.y + 0.1, s.z, 1, 0.15, 0.05, 0.15, 0);
        }
    }

    /** The point the floor footprint of a spirit's gaze is on, {@code t} ticks into a lone sweep across the room. */
    private Vec3 sweepAim(int i, double t, double length) {
        Vec3 c = centre();
        Vec3 s = spirits[i] == null ? c.add(0, 8, 8) : spirits[i];
        Vec3 d = c.subtract(s).multiply(1, 0, 1);
        d = d.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, 1) : d.normalize();
        Vec3 side = new Vec3(-d.z, 0, d.x);
        double r = reach() - 1.0;
        return c.add(d.scale(gazeOffset)).add(side.scale(-r + 2 * r * Mth.clamp(t / length, 0, 1)));
    }

    /** Verdict: the three footprints wheel round the room and swing in and out. */
    private Vec3 verdictAim(int i, int t) {
        double a = Math.toRadians(verdictPhase + i * 120 + t * 2.4);
        double r = 3.0 + (reach() - 4.0) * (0.5 - 0.5 * Math.cos(2 * Math.PI * t / 80.0));
        Vec3 c = centre();
        return c.add(Math.cos(a) * r, 0, Math.sin(a) * r);
    }

    /** One tick of spirit {@code i}'s gaze on the floor point {@code aim}: a cone of lapis light, walls shield you. */
    private void gaze(ServerLevel level, int i, Vec3 aim, float damage) {
        Vec3 eye = spirits[i];
        if (eye == null) {
            return;
        }
        Vec3 axis = aim.subtract(eye);
        double dist = axis.length();
        if (dist < 1.0E-3) {
            return;
        }
        Vec3 n = axis.scale(1.0 / dist);
        for (double d = 1.0; d < dist; d += 1.2) {
            Vec3 p = eye.add(n.scale(d));
            level.sendParticles(LAPIS_L, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
        }
        double foot = dist * Math.tan(Math.toRadians(GAZE_HALF));
        if (tickCount % 2 == 0) {
            telegraphRing(level, aim, foot, LAPIS_L);
            level.sendParticles(ParticleTypes.END_ROD, aim.x, aim.y + 0.2, aim.z, 2, foot * 0.4, 0.05, foot * 0.4, 0.01);
        }
        double cos = Math.cos(Math.toRadians(GAZE_HALF));
        for (LivingEntity e : victims(level, aim, foot + 3)) {
            Vec3 body = e.position().add(0, e.getBbHeight() * 0.5, 0);
            Vec3 to = body.subtract(eye);
            double len = to.length();
            if (len < 1.0E-3 || to.scale(1.0 / len).dot(n) < cos || len > dist + 3) {
                continue;
            }
            if (!clearLine(level, eye, body)) {
                continue;
            }
            Integer last = lastBeamHit.get(e.getUUID());
            if (last != null && tickCount - last < 10) {
                continue;
            }
            lastBeamHit.put(e.getUUID(), tickCount);
            e.hurtServer(level, damageSources().indirectMagic(this, this), damage);
            e.addEffect(new MobEffectInstance(MobEffects.WITHER, 50, 0), this);
            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0), this);
            level.sendParticles(ParticleTypes.SOUL, e.getX(), e.getY() + 1, e.getZ(), 6, 0.3, 0.5, 0.3, 0.02);
        }
    }

    /** Between verdicts: one spirit at a time, a 1 s warning (its band drawn on the floor), a 3.5 s sweep, a pause. */
    private void tickGaze(ServerLevel level) {
        int warn = 20;
        int sweep = 70;
        int k = gazeTick++;
        if (k < 0) {
            return;
        }
        if (k == 0) {
            gazeOffset = (getRandom().nextDouble() - 0.5) * 8.0;
            Vec3 s = spirits[gazeIndex];
            if (s != null) {
                level.playSound(null, s.x, s.y, s.z, SoundEvents.TRIAL_SPAWNER_OMINOUS_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
            }
        }
        if (k < warn) {
            if (k % 3 == 0) {
                Vec3 a = sweepAim(gazeIndex, 0, sweep);
                Vec3 b = sweepAim(gazeIndex, sweep, sweep);
                double len = flatDist(a, b);
                Vec3 s = spirits[gazeIndex];
                double foot = s == null ? 2.0 : s.distanceTo(centre()) * Math.tan(Math.toRadians(GAZE_HALF));
                Vec3 dir = b.subtract(a).multiply(1, 0, 1).normalize();
                Vec3 side = new Vec3(-dir.z, 0, dir.x).scale(foot);
                for (double d = 0; d <= len; d += 1.0) {
                    Vec3 p = a.add(dir.scale(d));
                    level.sendParticles(LAPIS, p.x + side.x, p.y + 0.15, p.z + side.z, 1, 0.05, 0, 0.05, 0);
                    level.sendParticles(LAPIS, p.x - side.x, p.y + 0.15, p.z - side.z, 1, 0.05, 0, 0.05, 0);
                }
                if (s != null) {
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, s.x, s.y + 0.2, s.z, 4, 0.2, 0.2, 0.2, 0.02);
                }
            }
            return;
        }
        if (k < warn + sweep) {
            gaze(level, gazeIndex, sweepAim(gazeIndex, k - warn, sweep), 6.0F);
            return;
        }
        gazeIndex = (gazeIndex + 1) % 3;
        gazeTick = -(int) Math.round(30 * cooldownScale());
    }

    private void unseal(ServerLevel level) {
        sealed = false;
        lighten(level);
        for (int i = 0; i < 3; i++) {
            spirits[i] = null;
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("fourth_king_sealed"));
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(STONE_BITS, getX(), getY() + 3, getZ(), 8, 0.5, 1.0, 0.5, 0.02);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        if (sealed) {
            unseal(level);
        }
        restoreAll(level);
        swarms.clear();
        spots.clear();
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!staleTemps.isEmpty()) {                   // saved by an unload: put back on the first tick
            restoreAll(level);
        }
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!temps.isEmpty() || sealed || !swarms.isEmpty())) {
            cleanUp(level);                            // the arena emptied (death, flight)
        }
        if (phase() == 1 && (wasPhaseTwo || sealed)) {   // the fight was reset
            wasPhaseTwo = false;
            roarUntil = -1;
            cleanUp(level);
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (fighting && anyone && !jarsRaised) {
            raiseJars(level);
            drainTimer = (int) Math.round(DRAIN_EVERY * 0.6 * cooldownScale());
        }
        checkJars(level);
        tickSwarms(level);
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (drainTimer > 0) {
            drainTimer--;
        }
        if (free) {
            if (phase() == 2 && !sealed && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "seal");
            } else if (sealed && --verdictTimer <= 0) {
                verdictTimer = (int) Math.round(VERDICT_EVERY * cooldownScale());
                chain(level, "verdict");
            } else if (drainTimer <= 0 && !jars.isEmpty() && getHealth() < getMaxHealth() * 0.92F) {
                drainTimer = (int) Math.round(DRAIN_EVERY * cooldownScale());
                chain(level, "drain");
            }
        }
        if (sealed && anyone) {
            if (tickCount % 40 == 0) {
                darken(level);
            }
            if (tickCount % 4 == 0) {
                drawSpirits(level);
            }
            boolean verdict = cur != null && "verdict".equals(cur.name);
            boolean sealing = cur != null && "seal".equals(cur.name);
            if (!verdict && !sealing) {
                tickGaze(level);
            }
        }
        // ambience: sand sifting from his wrappings, the burning lapis eye
        if (tickCount % 5 == 0) {
            level.sendParticles(SAND_FALLING, getX(), getY() + 3.5, getZ(), 1, 0.4, 0.8, 0.4, 0);
        }
        if (tickCount % 7 == 0) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            level.sendParticles(LAPIS_L, getX() - Mth.sin(yaw) * 0.5 + Mth.cos(yaw) * 0.2, getY() + 5.0,
                    getZ() + Mth.cos(yaw) * 0.5 + Mth.sin(yaw) * 0.2, 1, 0.02, 0.02, 0.02, 0);
        }
        if (tickCount % 140 == 0) {
            level.playSound(null, this, SoundEvents.HUSK_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.4F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        wasPhaseTwo = true;
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("fourth_king_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        raiseJars(level);                              // the broken jars rise again
        drainTimer = Math.max(drainTimer, 160);
        level.sendParticles(LAPIS_L, getX(), getY() + 4.5, getZ(), 80, 1.5, 1.5, 1.5, 0.08);
        level.sendParticles(SAND_BLOCK, getX(), getY() + 1, getZ(), 80, 3.0, 0.5, 3.0, 0.1);
        level.playSound(null, this, SoundEvents.HUSK_DEATH, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(SAND_BLOCK, getX(), getY() + 2, getZ(), 160, 1.0, 2.5, 1.0, 0.1);
        level.sendParticles(LAPIS_L, getX(), getY() + 4, getZ(), 80, 1.0, 1.5, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.HUSK_DEATH, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
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
            output.putLong("KingCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("KingRadius", radius);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("KingBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("KingCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("KingRadius", 16);
        staleTemps.clear();
        input.read("KingBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
        jars.clear();
        jarsRaised = false;
        sealed = false;
    }
}
