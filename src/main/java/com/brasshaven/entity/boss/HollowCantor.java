package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
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
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.HollowCantor.BATON;
import static com.brasshaven.generated.MobAnims.HollowCantor.CADENCE;
import static com.brasshaven.generated.MobAnims.HollowCantor.CHOIR;
import static com.brasshaven.generated.MobAnims.HollowCantor.FUGUE;
import static com.brasshaven.generated.MobAnims.HollowCantor.ORGAN;
import static com.brasshaven.generated.MobAnims.HollowCantor.REQUIEM;
import static com.brasshaven.generated.MobAnims.HollowCantor.RESONANCE;
import static com.brasshaven.generated.MobAnims.HollowCantor.ROAR;
import static com.brasshaven.generated.MobAnims.HollowCantor.SHRIEK;
import static com.brasshaven.generated.MobAnims.HollowCantor.SILENCE;
import static com.brasshaven.generated.MobAnims.HollowCantor.STAGGER;
import static com.brasshaven.generated.MobAnims.HollowCantor.TOLL;

/**
 * Le Chantre creux (The Hollow Cantor), the champion of the Echo Cathedral: a gaunt 3.5-block choirmaster of tarnished
 * brass and deepslate, his ribcage an organ chest, a fan of organ pipes behind an empty hood, a long baton that ends in
 * a tuning fork. He waits at the organ console in the apse (radius 15). Theme: sound against silence.
 * <ul>
 *     <li>Phase 1: the <b>baton</b> (downbeat and backswing), the <b>shriek</b> (a sonic cone, its ripples drawn on the
 *     floor while he draws breath), the <b>toll</b> (the fork driven into the floor, a ring to jump), the
 *     <b>cadence</b> (he glides along a drawn line through you) and the <b>resonance</b> (amethyst buds grow on the
 *     floor; when the fork's note peaks the whole floor rings, and only the tiles round a bud are safe).</li>
 *     <li>Phase 2 (a roar at 65%): the <b>silence</b> (for 7 s a zone of hush: players inside are slowed, their sound
 *     cut and their sight darkened, while he fades to a shimmer; a hit reveals him), the <b>choir</b> (echo choristers:
 *     bell monks and banshees) and the <b>fugue</b> (three voices burst under marked circles, one after another).</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the <b>organ</b> awakes. Pipe blasts rise from
 *     the floor under every player on a timer (warned 1.2 s by a ring of rising dust), and every 12 s the <b>requiem</b>
 *     marches rows of blasts across the floor, each row with a gap to step into.</li>
 * </ul>
 * The only blocks he places are the resonance's amethyst buds (into air, drop nothing without silk touch); they are
 * removed when the move ends or is cut short, when the fight resets or the arena empties, when he dies or is removed,
 * and on the first tick after a reload (saved as {@code CantorBlocks}).
 */
public class HollowCantor extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double BATON_RANGE = 5.0;
    private static final double BATON_HALF = 65;
    private static final double TOLL_R = 3.5;
    private static final double SAFE_R = 2.2;
    private static final double SILENCE_R = 8.0;
    private static final int SILENCE_LIFE = 140;
    private static final int REQUIEM_EVERY = 240;
    private static final int BLAST_EVERY = 130;
    private static final DustParticleOptions ECHO = new DustParticleOptions(0x96ECE6, 1.3F);
    private static final DustParticleOptions HUSH = new DustParticleOptions(0x6A6A78, 1.5F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF0C860, 1.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xD83A2A, 1.4F);
    private static final DustParticleOptions VIOLET = new DustParticleOptions(0xB278EC, 1.3F);

    private record Temp(BlockState original, BlockState placed) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 15;
    private boolean wasPhaseTwo;
    private int roarUntil = -1;
    // phase 2: the silence
    private @Nullable Vec3 silenceAt;
    private int silenceUntil = -1;
    private int revealUntil = -1;
    // phase 3: the organ
    private boolean organ;
    private int guard;
    private int blastTimer = 60;
    private int requiemTimer = 100;
    // moves in flight
    private final List<Vec3> buds = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable Vec3 glideFrom;
    private @Nullable Vec3 glideTo;
    private final List<Vec3> chorusAt = new ArrayList<>();
    private final List<List<Vec3>> rows = new ArrayList<>();
    private final List<UUID> adds = new ArrayList<>();
    // every block changed (the amethyst buds): its original state and what was put there
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public HollowCantor(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 640.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 13.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.25);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.HollowCantor.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.WHITE;
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
        return 4.0;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
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

    /** Usable floor radius round the seal. */
    private double reach() {
        return Math.max(6.0, Math.min(15.0, radius - 1.0));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Top of the first solid block at or below {@code y + 2} (scanning 8 blocks), or NaN. */
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

    private static boolean open(ServerLevel level, BlockPos p) {
        return level.getBlockState(p).getCollisionShape(level, p).isEmpty();
    }

    /** A spot on the arena floor at (x, z) (within 2.5 of the seal's height, two free blocks above), or null. */
    private @Nullable Vec3 floorSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 2.5) {
            return null;
        }
        BlockPos b = BlockPos.containing(x, y, z);
        return open(level, b) && open(level, b.above()) ? new Vec3(x, y, z) : null;
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

    private void faceToward(Vec3 p) {
        snapFacing((float) (Mth.atan2(p.z - getZ(), p.x - getX()) * (180.0 / Math.PI)) - 90.0F);
    }

    private void turnToward(@Nullable LivingEntity t, float maxTurn) {
        if (t == null) {
            return;
        }
        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 14, radius + 4),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** Pushes are capped at 1.2 and lifts at 0.5; near the arena's edge the outward part is removed. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.2, knockback));
            Vec3 radial = e.position().subtract(centre()).multiply(1, 0, 1);
            double r = radial.length();
            if (r > reach() - 3.0 && r > 0.1) {
                Vec3 n = radial.scale(1.0 / r);
                double out = push.dot(n);
                if (out > 0) {
                    push = push.subtract(n.scale(out));
                }
            }
        }
        lift = Math.min(lift, 0.5);
        if (push.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    /** Everything in a cone ahead: within {@code length} and {@code half} degrees of the facing. */
    private void hitCone(ServerLevel level, double length, double half, float damage, double knockback) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(half));
        for (LivingEntity e : victims(level, position(), length + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= length + e.getBbWidth() / 2 && (d < 1.2 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 4.0) {
                strike(level, e, damage, knockback, 0.3);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0), this);
            }
        }
    }

    private void drawCone(ServerLevel level, double length, double half, double at, DustParticleOptions dust) {
        for (double a = -half; a <= half; a += 8) {
            Vec3 p = position().add(rotate(forward(), a).scale(at));
            level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
        }
        for (int side = -1; side <= 1; side += 2) {
            Vec3 dir = rotate(forward(), half * side);
            for (double d = 1.5; d <= length; d += 1.5) {
                Vec3 p = position().add(dir.scale(d));
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
            }
        }
    }

    private double shriekLength() {
        return phase() == 2 ? 17.0 : 14.0;
    }

    private double shriekHalf() {
        return phase() == 2 ? 40.0 : 30.0;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // baton: the upbeat over his right shoulder (0.7 s, the arc drawn in echo-light), the downbeat sweep, then a
        // backswing half a second later after a turn toward you
        out.add(BossAttack.of("baton").anim(BATON).timing(14, 18, 14).range(0, 6.0).cooldown(55).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, BATON_RANGE, BATON_HALF, ECHO);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0) {
                        batonCut(level, 13.0F);
                    }
                    if (tick == 3) {
                        turnToward(t, 35.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, BATON_RANGE, BATON_HALF, ECHO);
                    }
                    if (tick == 10) {
                        batonCut(level, 11.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 4.5 ? "toll" : "shriek");
                    }
                })
                .build());
        // shriek: the hood thrown back and the pipes swelling (1.1 s): ripples run down the cone on the floor, closer
        // and closer together, while he turns slowly toward you for the first 0.7 s; then the cone locks and he screams
        out.add(BossAttack.of("shriek").anim(SHRIEK).timing(22, 12, 14).range(3.0, 16.0).cooldown(120).weight(10)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick < 14) {
                        turnToward(t, 6.0F);
                    }
                    if (tick % 2 == 0) {
                        double len = shriekLength();
                        double at = 1.5 + (tick * (tick < 14 ? 0.5 : 0.9)) % (len - 1.5);
                        drawCone(level, len, shriekHalf(), at, tick < 14 ? ECHO : RED);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.5F, 1.1F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double len = shriekLength();
                    hitCone(level, len, shriekHalf(), b.phase() == 2 ? 16.0F : 14.0F, 1.1);
                    for (double d = 2.0; d <= len; d += 3.0) {
                        Vec3 p = b.ahead(d);
                        level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y + 1.6, p.z, 1, 0, 0, 0, 0);
                    }
                    level.playSound(null, b, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3.0F, 1.2F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawCone(level, shriekLength(), shriekHalf(), 2.0 + tick * 1.2, ECHO);
                    }
                })
                .build());
        // toll: the fork raised overhead in both hands (0.9 s, a ring drawn round him), driven into the floor: 15 inside
        // the ring and a ring of sound rolls out (jump it). Phase 2: a second ring half a second later
        out.add(BossAttack.of("toll").anim(TOLL).timing(18, 20, 14).range(0, 9.0).cooldown(90).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), TOLL_R, ECHO);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), TOLL_R, 15.0F, 1.0, 0.4);
                    b.addEffect(WayfarerBoss.wave(b.position(), 10, 0.5, 8.0F, ECHO));
                    level.sendParticles(ParticleTypes.SONIC_BOOM, b.getX(), b.getY() + 0.5, b.getZ(), 1, 0, 0, 0, 0);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 10 && b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 12, 0.55, 8.0F, VIOLET));
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.7F);
                    }
                })
                .build());
        // cadence: he leans in with the baton levelled (0.8 s, the line drawn in echo-light), then glides along it in
        // 6 ticks: 12 to whoever stands in his path
        out.add(BossAttack.of("cadence").anim(CADENCE).timing(16, 12, 14).range(6.0, 20.0).cooldown(110).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        Vec3 to = glideEnd(t);
                        double len = flatDist(b.position(), to);
                        for (double d = 1.0; d < len; d += 1.0) {
                            Vec3 p = b.position().lerp(to, d / len);
                            level.sendParticles(ECHO, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    glideFrom = b.position();
                    glideTo = landing(level, glideEnd(t));
                    faceToward(glideTo);
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .active((b, level, t, tick) -> glideStep(level, tick))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.0 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "baton");
                    }
                })
                .build());
        // resonance: amethyst buds grow on the floor (golden rings round them) while he strikes the fork on his palm
        // and raises it (1.2 s); the note swells for 0.8 s more, the floor shivering outside the rings, then the whole
        // floor rings: 14 and Slowness to everyone on it outside a ring. The buds shatter after
        out.add(BossAttack.of("resonance").anim(RESONANCE).timing(24, 34, 16).range(0, 30.0).cooldown(300).weight(7)
                .track(false)
                .start((b, level, t, tick) -> growBuds(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawBuds(level, false);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 1.0F))
                .active((b, level, t, tick) -> resonanceStep(level, tick))
                .end((b, level, t, tick) -> clearBuds(level, false))
                .build());

        // ---------------------------------------------------------------- phase 2
        // silence: a long finger to the empty hood, "hush" (1.0 s, the zone's edge drawn round him, ash drifting in):
        // for 7 s a zone of hush: players inside are slowed, their sound cut and their sight darkened; inside it he
        // fades to a shimmer of ash (a hit reveals him for a second)
        out.add(BossAttack.of("silence").anim(SILENCE).phaseTwo().timing(20, 6, 12).range(0, 14.0).cooldown(520)
                .weight(6).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), SILENCE_R, HUSH);
                    }
                    for (int k = 0; k < 3; k++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        level.sendParticles(ParticleTypes.WHITE_ASH, b.getX() + Math.cos(a) * SILENCE_R, b.getY() + 1.0,
                                b.getZ() + Math.sin(a) * SILENCE_R, 2, 0.2, 0.5, 0.2, 0.0);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.SCULK_CLICKING, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> openSilence(level))
                .build());
        // choir: both arms raised to the unseen choir (1.1 s; soul light rises where they will stand), the downbeat
        // calls the echo choristers: bell monks and banshees
        out.add(BossAttack.of("choir").anim(CHOIR).phaseTwo().timing(22, 8, 14).range(0, 30.0).cooldown(640).weight(5)
                .track(false)
                .start((b, level, t, tick) -> planChorus(level))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Vec3 p : chorusAt) {
                            b.telegraphRing(level, p, 1.0, ECHO);
                            level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y + 0.3 + (tick % 6) * 0.3, p.z, 1, 0.2, 0.2, 0.2, 0.01);
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> callChorus(level, t))
                .build());
        // fugue: the baton traces the opening phrase (1.0 s), then three downbeats 0.6 s apart: each one marks a ring
        // under every player that follows for half a second, locks, and bursts half a second later (12)
        out.add(BossAttack.of("fugue").anim(FUGUE).phaseTwo().timing(20, 40, 14).range(0, 30.0).cooldown(240).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.NOTE, b.getX(), b.getY() + 4.2, b.getZ(), 2, 0.6, 0.3, 0.6, 1.0);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_PLING.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> voices(level, t, 0))
                .active((b, level, t, tick) -> {
                    if (tick == 12 || tick == 24) {
                        voices(level, t, tick / 12);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // organ: he rises, arms spread, the pipes swelling (2.0 s, guarded; the floor hums), then the great chord: a
        // ring of sound (12, jump it), a pulse of darkness, +12% speed, and the organ starts to play
        out.add(BossAttack.of("organ").anim(ORGAN).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.WARDEN_NEARBY_CLOSEST, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    Vec3 c = centre();
                    double r = reach();
                    level.sendParticles(ECHO, c.x, c.y + 0.2, c.z, 10, r * 0.5, 0.05, r * 0.5, 0.0);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.3, ECHO);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> wakeOrgan(level))
                .build());
        // requiem: he plays the air like a keyboard (1.0 s; the rows are drawn on the floor in grey, their gaps in
        // gold), then six rows of pipe blasts march away from him, one every 6 ticks, each warned in red for 0.7 s:
        // 13 to whoever is on a row outside its gap
        out.add(BossAttack.of("requiem").anim(REQUIEM).phaseTwo().timing(20, 50, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planRows(level);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        drawRows(level, -1);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> requiemStep(level, tick))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void batonCut(ServerLevel level, float damage) {
        hitArc(level, BATON_RANGE, BATON_HALF, damage, 1.0);
        for (double a = -BATON_HALF; a <= BATON_HALF; a += 12) {
            Vec3 p = position().add(rotate(forward(), a).scale(BATON_RANGE - 1.0));
            level.sendParticles(ParticleTypes.NOTE, p.x, p.y + 1.6, p.z, 1, 0.1, 0.2, 0.1, 0.5);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.5, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.7F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.0F, 1.2F);
    }

    private Vec3 glideEnd(@Nullable LivingEntity t) {
        double len = t != null ? Math.min(12.0, flatDist(position(), t.position()) + 3.0) : 8.0;
        return clampToArena(position().add(forward().scale(len)), 1.5);
    }

    /** The furthest spot along the line to {@code want} that has floor, or where he stands. */
    private Vec3 landing(ServerLevel level, Vec3 want) {
        Vec3 from = position();
        for (int i = 0; i <= 10; i++) {
            Vec3 q = want.lerp(from, i / 10.0);
            Vec3 s = floorSpot(level, q.x, q.z);
            if (s != null) {
                return s;
            }
        }
        return from;
    }

    private void glideStep(ServerLevel level, int tick) {
        if (glideFrom == null || glideTo == null) {
            return;
        }
        if (tick <= 6) {
            Vec3 p = glideFrom.lerp(glideTo, tick / 6.0);
            teleportTo(p.x, glideTo.y, p.z);
            setDeltaMovement(Vec3.ZERO);
            level.sendParticles(ECHO, getX(), getY() + 1.2, getZ(), 4, 0.3, 0.6, 0.3, 0.0);
            level.sendParticles(ParticleTypes.NOTE, getX(), getY() + 2.0, getZ(), 1, 0.3, 0.3, 0.3, 0.8);
            for (LivingEntity e : victims(level, position(), 3.0)) {
                if (flatDist(e.position(), position()) <= 1.6 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                    strike(level, e, 12.0F, 0.8, 0.3);
                }
            }
        }
        if (tick == 6) {
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ the resonance (temporary amethyst buds)

    /** Buds: one 3-5 blocks from each player (up to 4), more scattered, all at least 4.5 apart (3 to 6 of them). */
    private void growBuds(ServerLevel level, @Nullable LivingEntity target) {
        clearBuds(level, false);
        int want = Math.min(6, 3 + scaledPlayers() - 1);
        List<Vec3> pool = new ArrayList<>();
        int k = 0;
        for (Player p : fighters(level)) {
            if (k++ >= 4) {
                break;
            }
            for (int tries = 0; tries < 8; tries++) {
                double a = getRandom().nextDouble() * Math.PI * 2;
                double d = 3 + getRandom().nextDouble() * 2;
                Vec3 q = clampToArena(p.position().add(Math.cos(a) * d, 0, Math.sin(a) * d), 1.0);
                if (budOk(level, q, pool)) {
                    pool.add(floorSpot(level, q.x, q.z));
                    break;
                }
            }
        }
        for (int tries = 0; pool.size() < want && tries < 60; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * (reach() - 3);
            Vec3 q = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
            if (budOk(level, q, pool) && flatDist(q, position()) > 2.5) {
                pool.add(floorSpot(level, q.x, q.z));
            }
        }
        for (Vec3 p : pool) {
            BlockPos at = BlockPos.containing(p);
            if (level.getBlockState(at).isAir() && !open(level, at.below())) {
                setTemp(level, at, Blocks.LARGE_AMETHYST_BUD.defaultBlockState());
            }
            buds.add(Vec3.atBottomCenterOf(at));
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState()),
                    p.x, p.y + 0.3, p.z, 12, 0.3, 0.2, 0.3, 0.05);
        }
        level.playSound(null, this, SoundEvents.LARGE_AMETHYST_BUD_PLACE, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    private boolean budOk(ServerLevel level, Vec3 q, List<Vec3> pool) {
        if (floorSpot(level, q.x, q.z) == null) {
            return false;
        }
        for (Vec3 s : pool) {
            if (flatDist(s, q) < 4.5) {
                return false;
            }
        }
        return true;
    }

    private void drawBuds(ServerLevel level, boolean late) {
        for (Vec3 b : buds) {
            telegraphRing(level, b, SAFE_R, GOLD);
            level.sendParticles(late ? ParticleTypes.END_ROD : ParticleTypes.ENCHANT, b.x, b.y + 0.8, b.z, 1, 0.1, 0.2, 0.1, 0.05);
        }
    }

    private boolean nearBud(Vec3 p, double extra) {
        for (Vec3 b : buds) {
            if (flatDist(p, b) <= SAFE_R + extra) {
                return true;
            }
        }
        return false;
    }

    private void resonanceStep(ServerLevel level, int tick) {
        if (tick < 16) {
            if (tick % 2 == 0) {
                drawBuds(level, true);
                Vec3 c = centre();
                double r = reach();
                for (int i = 0; i < 14; i++) {                    // the floor shivers outside the rings
                    double a = getRandom().nextDouble() * Math.PI * 2;
                    double d = Math.sqrt(getRandom().nextDouble()) * r;
                    Vec3 p = c.add(Math.cos(a) * d, 0, Math.sin(a) * d);
                    if (!nearBud(p, 0)) {
                        level.sendParticles(tick < 10 ? ECHO : RED, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                    }
                }
            }
            if (tick == 8) {
                level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 1.4F);
            }
        } else if (tick == 16) {
            Vec3 c = centre();
            for (LivingEntity e : victims(level, c, reach() + 3)) {
                if (nearBud(e.position(), e.getBbWidth() / 2)) {
                    level.sendParticles(GOLD, e.getX(), e.getY() + 0.3, e.getZ(), 8, 0.4, 0.1, 0.4, 0.0);
                    continue;
                }
                double fy = floorY(level, e.getX(), e.getY(), e.getZ());
                if (Double.isNaN(fy) || e.getY() - fy > 1.5) {
                    continue;                                     // in the air: the floor's note misses
                }
                strike(level, e, 14.0F, 0.0, 0.3);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                level.sendParticles(ParticleTypes.NOTE, e.getX(), e.getY() + 1.8, e.getZ(), 3, 0.3, 0.3, 0.3, 1.0);
            }
            for (int i = 0; i < 6; i++) {
                double a = Math.PI * 2 * i / 6;
                level.sendParticles(ParticleTypes.SONIC_BOOM, c.x + Math.cos(a) * reach() * 0.5, c.y + 0.6,
                        c.z + Math.sin(a) * reach() * 0.5, 1, 0, 0, 0, 0);
            }
            level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 1.0F);
            level.playSound(null, this, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 2.0F, 1.6F);
        } else if (tick == 18) {
            clearBuds(level, true);
        }
    }

    /** The buds go (only where the bud is still the one he set); {@code shatter} adds the breaking glass. */
    private void clearBuds(ServerLevel level, boolean shatter) {
        for (Vec3 b : buds) {
            BlockPos at = BlockPos.containing(b);
            if (shatter) {
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState()),
                        b.x, b.y + 0.4, b.z, 16, 0.3, 0.3, 0.3, 0.1);
            }
            clearTemp(level, at);
        }
        if (shatter && !buds.isEmpty()) {
            level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 2.5F, 0.8F);
        }
        buds.clear();
    }

    private void setTemp(ServerLevel level, BlockPos p, BlockState state) {
        Temp old = temps.get(p.asLong());
        temps.put(p.asLong(), new Temp(old != null ? old.original() : level.getBlockState(p), state));
        level.setBlock(p, state, 3);
    }

    private void clearTemp(ServerLevel level, BlockPos p) {
        Temp t = temps.remove(p.asLong());
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        if (level.getBlockState(p).getBlock() == t.placed().getBlock()) {
            level.setBlock(p, t.original(), 3);
        }
    }

    /** Every changed block goes back (only where it is still the one set). */
    private void restoreAll(ServerLevel level) {
        if (!staleTemps.isEmpty()) {
            for (SavedTemp s : staleTemps) {
                temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed()));
            }
            staleTemps.clear();
        }
        buds.clear();
        for (Map.Entry<Long, Temp> e : new ArrayList<>(temps.entrySet())) {
            BlockPos p = BlockPos.of(e.getKey());
            if (level.isLoaded(p) && level.getBlockState(p).getBlock() == e.getValue().placed().getBlock()) {
                level.setBlock(p, e.getValue().original(), 3);
            }
        }
        temps.clear();
    }

    // ------------------------------------------------------------------ the silence (phase 2)

    private boolean silenceOn() {
        return silenceAt != null && tickCount < silenceUntil;
    }

    private void openSilence(ServerLevel level) {
        if (silenceOn()) {
            return;
        }
        silenceAt = position();
        silenceUntil = tickCount + SILENCE_LIFE + (organ ? 20 : 0);
        level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1.5, getZ(), 120, SILENCE_R * 0.5, 1.0, SILENCE_R * 0.5, 0.0);
        level.sendParticles(ParticleTypes.SONIC_BOOM, getX(), getY() + 1.5, getZ(), 1, 0, 0, 0, 0);
        for (Player p : fighters(level)) {
            if (flatDist(p.position(), silenceAt) <= SILENCE_R && p instanceof ServerPlayer sp) {
                sp.connection.send(new ClientboundStopSoundPacket(null, null));
                p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0), this);
            }
        }
    }

    private void tickSilence(ServerLevel level) {
        if (silenceAt == null) {
            return;
        }
        if (!silenceOn()) {
            silenceAt = null;
            removeEffect(MobEffects.INVISIBILITY);
            level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1.8, getZ(), 30, 0.6, 1.0, 0.6, 0.0);
            return;
        }
        Vec3 c = silenceAt;
        if (tickCount % 4 == 0) {
            telegraphRing(level, c, SILENCE_R, HUSH);
            level.sendParticles(ParticleTypes.WHITE_ASH, c.x, c.y + 1.5, c.z, 6, SILENCE_R * 0.5, 1.0, SILENCE_R * 0.5, 0.0);
        }
        if (tickCount % 10 == 0) {
            for (Player p : fighters(level)) {
                if (flatDist(p.position(), c) > SILENCE_R) {
                    continue;
                }
                p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 25, 0), this);
                if (!p.hasEffect(MobEffects.DARKNESS)) {
                    p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0), this);
                }
                if (tickCount % 20 == 0 && p instanceof ServerPlayer sp) {
                    sp.connection.send(new ClientboundStopSoundPacket(null, null));     // muffled
                }
            }
        }
        boolean inside = flatDist(position(), c) <= SILENCE_R;
        if (inside && tickCount > revealUntil) {
            if (tickCount % 10 == 0) {
                addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 15, 0, false, false));
            }
            if (tickCount % 2 == 0) {                              // a shimmer of ash where he stands: never truly gone
                level.sendParticles(HUSH, getX(), getY() + 0.4 + getRandom().nextDouble() * 3.0, getZ(), 2, 0.3, 0.3, 0.3, 0.0);
            }
        } else if (hasEffect(MobEffects.INVISIBILITY)) {
            removeEffect(MobEffects.INVISIBILITY);
        }
    }

    // ------------------------------------------------------------------ the choir (echo choristers)

    private int aliveAdds(ServerLevel level) {
        adds.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        return adds.size();
    }

    private void planChorus(ServerLevel level) {
        chorusAt.clear();
        int room = 2 + scaledPlayers() - aliveAdds(level);
        int n = Math.min(room, scaledCount(2));
        for (int tries = 0; chorusAt.size() < n && tries < 30; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = reach() * (0.5 + getRandom().nextDouble() * 0.4);
            Vec3 s = floorSpot(level, centre().x + Math.cos(a) * d, centre().z + Math.sin(a) * d);
            if (s != null && flatDist(s, position()) > 4.0) {
                chorusAt.add(s);
            }
        }
    }

    private void callChorus(ServerLevel level, @Nullable LivingEntity target) {
        int i = 0;
        for (Vec3 at : chorusAt) {
            EntityType<? extends Mob> type = i++ % 2 == 0 ? ModEntities.BELL_MONK.get() : ModEntities.BANSHEE.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            mob.snapTo(at.x, at.y, at.z, getRandom().nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(target);
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.SCULK_SOUL, at.x, at.y + 1, at.z, 15, 0.3, 0.6, 0.3, 0.02);
        }
        chorusAt.clear();
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.5F, 1.4F);
    }

    private void discardAdds(ServerLevel level) {
        for (UUID id : adds) {
            var e = level.getEntity(id);
            if (e != null && e.isAlive()) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, e.getX(), e.getY() + 1, e.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
                e.discard();
            }
        }
        adds.clear();
    }

    // ------------------------------------------------------------------ the fugue

    /** One voice: a ring under every player (up to 4) and {@code scaledCount(1)} strays. */
    private void voices(ServerLevel level, @Nullable LivingEntity target, int n) {
        int k = 0;
        for (Player p : fighters(level)) {
            if (k++ >= 4) {
                break;
            }
            addEffect(voice(p, null, 10, 10, 2.2, 12.0F));
        }
        if (k == 0 && target != null) {
            addEffect(voice(target, null, 10, 10, 2.2, 12.0F));
        }
        for (int i = 0; i < scaledCount(1); i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * Math.max(2, reach() - 3);
            addEffect(voice(null, centre().add(Math.cos(a) * d, 0, Math.sin(a) * d), 10, 10, 2.2, 12.0F));
        }
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.HOSTILE, 3.0F, 0.5F + n * 0.25F);
    }

    /** A ring follows {@code follow} for {@code track} ticks, locks (red) for {@code lock}, then a burst of sound. */
    private Effect voice(@Nullable LivingEntity follow, @Nullable Vec3 fixed, int track, int lock, double r, float damage) {
        int[] t = {0};
        Vec3[] at = {fixed};
        return (boss, level) -> {
            int k = t[0]++;
            if (follow != null && k < track && follow.isAlive() && boss instanceof HollowCantor c) {
                at[0] = c.clampToArena(follow.position(), 0.5).add(0, follow.getY() - c.centre().y, 0);
            }
            if (at[0] == null) {
                return true;
            }
            Vec3 p = at[0];
            if (k < track + lock) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, p, r, k < track ? ECHO : RED);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.NOTE, p.x, p.y + 0.5, p.z, 8, r * 0.4, 0.6, r * 0.4, 1.0);
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y + 0.8, p.z, 1, 0, 0, 0, 0);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.HOSTILE, 2.5F, 0.8F);
            for (LivingEntity e : boss.victims(level, p, r + 1)) {
                if (flatDist(e.position(), p) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 3.0) {
                    boss.strike(level, e, damage, 0.3, 0.3);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ phase 3: the organ

    private void wakeOrgan(ServerLevel level) {
        organ = true;
        blastTimer = 60;
        requiemTimer = 120;
        addEffect(WayfarerBoss.wave(position(), 14, 0.55, 12.0F, ECHO));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("hollow_cantor_organ"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        for (Player p : fighters(level)) {
            p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 50, 0), this);
        }
        Vec3 c = centre();
        level.sendParticles(ParticleTypes.SONIC_BOOM, getX(), getY() + 2, getZ(), 3, 1.0, 1.0, 1.0, 0);
        level.sendParticles(ParticleTypes.NOTE, c.x, c.y + 3, c.z, 60, reach() * 0.5, 2.0, reach() * 0.5, 1.0);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** A pipe blast at {@code p}: 24 ticks of warning (a ring, dust rising), then a column of sound (12, a toss). */
    private Effect pipeBlast(Vec3 p, int warn, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, p, 1.6, k < warn - 8 ? ECHO : RED);
                    level.sendParticles(ParticleTypes.DUST_PLUME, p.x, p.y + 0.1, p.z, 2, 0.4, 0.0, 0.4, 0.02);
                }
                if (k == 0) {
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.HOSTILE, 1.5F, 0.5F);
                }
                return false;
            }
            for (double y = 0.2; y <= 7.0; y += 0.7) {
                level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + y, p.z, 2, 0.25, 0.1, 0.25, 0.02);
            }
            level.sendParticles(ParticleTypes.NOTE, p.x, p.y + 3.5, p.z, 4, 0.4, 2.0, 0.4, 1.0);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 1.2F, 1.8F);
            for (LivingEntity e : boss.victims(level, p, 2.6)) {
                if (flatDist(e.position(), p) <= 1.6 + e.getBbWidth() / 2 && e.getY() - p.y < 6.0 && e.getY() - p.y > -2.0) {
                    boss.strike(level, e, damage, 0.0, 0.6);
                }
            }
            return true;
        };
    }

    private void organBlasts(ServerLevel level) {
        int k = 0;
        for (Player p : fighters(level)) {
            if (k++ >= 4) {
                break;
            }
            Vec3 s = floorSpot(level, p.getX(), p.getZ());
            if (s != null) {
                addEffect(pipeBlast(s, 24, 12.0F));
            }
        }
        for (int i = 0; i < scaledCount(1); i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * Math.max(2, reach() - 3);
            Vec3 s = floorSpot(level, centre().x + Math.cos(a) * d, centre().z + Math.sin(a) * d);
            if (s != null) {
                addEffect(pipeBlast(s, 24, 12.0F));
            }
        }
    }

    /** Six rows across his facing, 2.5 blocks apart from 2 blocks out, each with a three-point gap (a safe key). */
    private void planRows(ServerLevel level) {
        rows.clear();
        Vec3 fwd = forward();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        int gap = getRandom().nextInt(9) - 4;
        for (int k = 0; k < 6; k++) {
            List<Vec3> row = new ArrayList<>();
            gap = Mth.clamp(gap + getRandom().nextInt(5) - 2, -5, 5);
            for (int j = -7; j <= 7; j++) {
                if (Math.abs(j - gap) <= 1) {
                    continue;
                }
                Vec3 q = position().add(fwd.scale(2.0 + 2.5 * k)).add(side.scale(j * 1.4));
                if (flatDist(q, centre()) > reach() + 0.5) {
                    continue;
                }
                Vec3 s = floorSpot(level, q.x, q.z);
                if (s != null) {
                    row.add(s);
                }
            }
            rows.add(row);
        }
    }

    private void drawRows(ServerLevel level, int hot) {
        for (int k = 0; k < rows.size(); k++) {
            DustParticleOptions dust = k == hot ? RED : HUSH;
            for (Vec3 p : rows.get(k)) {
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
            }
        }
    }

    private void requiemStep(ServerLevel level, int tick) {
        for (int k = 0; k < rows.size(); k++) {
            int at = 8 + 6 * k;
            if (tick < at && tick >= at - 14 && tick % 2 == 0) {
                for (Vec3 p : rows.get(k)) {
                    level.sendParticles(RED, p.x, p.y + 0.15, p.z, 1, 0.15, 0, 0.15, 0);
                    level.sendParticles(ParticleTypes.DUST_PLUME, p.x, p.y + 0.1, p.z, 1, 0.2, 0, 0.2, 0.01);
                }
            }
            if (tick == at) {
                Set<UUID> hit = new HashSet<>();
                for (Vec3 p : rows.get(k)) {
                    for (double y = 0.2; y <= 6.0; y += 1.0) {
                        level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + y, p.z, 1, 0.2, 0.1, 0.2, 0.02);
                    }
                    for (LivingEntity e : victims(level, p, 2.0)) {
                        if (flatDist(e.position(), p) <= 1.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 4.0
                                && hit.add(e.getUUID())) {
                            strike(level, e, 13.0F, 0.0, 0.5);
                        }
                    }
                }
                if (!rows.get(k).isEmpty()) {
                    Vec3 m = rows.get(k).get(rows.get(k).size() / 2);
                    level.sendParticles(ParticleTypes.NOTE, m.x, m.y + 3, m.z, 6, 3.0, 1.0, 3.0, 1.0);
                    level.playSound(null, m.x, m.y, m.z, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.HOSTILE, 3.0F, 0.5F + k * 0.1F);
                    level.playSound(null, m.x, m.y, m.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 1.0F, 1.7F);
                }
            }
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.NOTE, getX(), getY() + 2.5, getZ(), 4, 0.5, 0.6, 0.5, 1.0);
            level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.0F, 1.6F);
            return false;
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && silenceOn() && source.getEntity() instanceof Player) {
            revealUntil = tickCount + 20;                          // a hit breaks the hush around him for a second
            removeEffect(MobEffects.INVISIBILITY);
        }
        return hurt;
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardAdds(level);
        silenceAt = null;
        silenceUntil = -1;
        removeEffect(MobEffects.INVISIBILITY);
        rows.clear();
    }

    /** Back to the first phase (the fight was reset): no silence, no organ, base speed, buds and choristers gone. */
    private void resetForm(ServerLevel level) {
        wasPhaseTwo = false;
        organ = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("hollow_cantor_organ"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("hollow_cantor_wrath"));
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
        BossAttack cur = currentAttack();
        if (!buds.isEmpty() && (cur == null || !"resonance".equals(cur.name))) {
            clearBuds(level, true);                        // the resonance was cut short (stagger)
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!temps.isEmpty() || !adds.isEmpty() || silenceAt != null)) {
            cleanUp(level);                                // the arena emptied (death, flight)
        }
        if (phase() == 1 && (wasPhaseTwo || organ || silenceAt != null)) {
            resetForm(level);                              // the fight was reset
        }
        tickSilence(level);
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!organ && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "organ");
            } else if (organ && --requiemTimer <= 0) {
                requiemTimer = Math.max(120, (int) Math.round(REQUIEM_EVERY * cooldownScale()));
                chain(level, "requiem");
            }
        }
        if (organ && phase() == 2 && fighting && anyone && !isStaggered() && guard <= 0 && --blastTimer <= 0) {
            blastTimer = Math.max(70, (int) Math.round(BLAST_EVERY * cooldownScale()));
            organBlasts(level);
        }
        // ambience: echo-light breathing in the organ chest, notes drifting off the pipes, the organ's hum in phase 3
        if (tickCount % 6 == 0 && !silenceOn()) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            Vec3 back = new Vec3(Mth.sin(yaw), 0, -Mth.cos(yaw));
            Vec3 p = position().add(back.scale(0.4)).add(0, 3.6, 0);
            level.sendParticles(ECHO, p.x, p.y, p.z, 1, 0.4, 0.3, 0.2, 0.0);
        }
        if (tickCount % 40 == 0 && !silenceOn()) {
            level.sendParticles(ParticleTypes.NOTE, getX(), getY() + 3.8, getZ(), 1, 0.4, 0.2, 0.4, 1.0);
        }
        if (organ && tickCount % 80 == 0) {
            level.playSound(null, centre().x, centre().y + 6, centre().z, SoundEvents.NOTE_BLOCK_BASS.value(),
                    SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        wasPhaseTwo = true;
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 8;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("hollow_cantor_wrath"), 0.08,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.NOTE, getX(), getY() + 3.5, getZ(), 40, 1.5, 1.0, 1.5, 1.0);
        level.sendParticles(ParticleTypes.SONIC_BOOM, getX(), getY() + 2, getZ(), 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 3.0F, 1.2F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(ParticleTypes.NOTE, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 1.0);
        level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 2, getZ(), 150, 1.2, 1.5, 1.2, 0.0);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
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
            output.putLong("CantorCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("CantorRadius", radius);
        output.putBoolean("CantorOrgan", organ);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("CantorBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("CantorCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("CantorRadius", 15);
        organ = input.getBooleanOr("CantorOrgan", false) && phase() == 2;
        wasPhaseTwo = phase() == 2;
        staleTemps.clear();
        input.read("CantorBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
    }
}
