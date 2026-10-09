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
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.ThornGardener.CALL;
import static com.brasshaven.generated.MobAnims.ThornGardener.IGNITE;
import static com.brasshaven.generated.MobAnims.ThornGardener.LUNGE;
import static com.brasshaven.generated.MobAnims.ThornGardener.PHOTOSYNTH;
import static com.brasshaven.generated.MobAnims.ThornGardener.POLLEN;
import static com.brasshaven.generated.MobAnims.ThornGardener.ROAR;
import static com.brasshaven.generated.MobAnims.ThornGardener.SNARE;
import static com.brasshaven.generated.MobAnims.ThornGardener.SNIP;
import static com.brasshaven.generated.MobAnims.ThornGardener.SPRAY;
import static com.brasshaven.generated.MobAnims.ThornGardener.STAGGER;
import static com.brasshaven.generated.MobAnims.ThornGardener.THORNS;

/**
 * Le Jardinier en chef (The Head Gardener), the champion of the Sunken Arboretum: a tall brass gardening automaton
 * (3.8 blocks) left alone to tend the palm house until the garden grew into it. A riveted copper body with moss and ivy
 * spilling out of the seams, a glass bell jar for a head with a glowing flower inside, very long arms ending in pruning
 * shears, a watering can made into a cannon on his back, roots trailing from his flowerpot boots. He waits on the giant
 * lily pad (r 16, a red upturned rim) in the dome's pool, under the hanging sun-lamp.
 * <ul>
 *     <li>Phase 1: the double <b>snip</b> (two drawn arcs, the second red), the scissor <b>lunge</b> down a drawn lane,
 *     <b>thorns</b> bursting along marked lines from the pad, the vine <b>snare</b> (a marked ring under you: it roots
 *     you 1.5 s; hit anything or get hurt and it tears) and the watering-cannon <b>spray</b> (a drawn cone that pushes a
 *     little and leaves fertilized patches where thorn bushes spring up for 5 s).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>call</b> (dart frogs and clockwork spiders of the garden) and the
 *     <b>pollen</b> bursts on marked rings; the snips chain into the spray or the lunge.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the sun-lamp <b>ignites</b> (a wave, jump it);
 *     concentrated sunbeams then sweep the pad along marked paths, and every ~16 s he <b>photosynthesises</b>: he
 *     basks in a drawn ring of light and heals 1% a pulse, unless a player stands in the ring to shade him.</li>
 * </ul>
 * The only blocks he places are the thorn bushes (sweet berry bushes in the air over moss tiles of the pad): each goes
 * back after 5 s, and all of them when the fight resets, the arena empties, he dies or is removed, and on the first tick
 * after a reload. Pushes are capped and never thrown toward the rim or the water.
 */
public class ThornGardener extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 3.8F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SNIP_RANGE = 5.0;
    private static final double SNIP_HALF = 70;
    private static final double LUNGE_MAX = 9.0;
    private static final double LUNGE_HALF = 1.0;
    private static final double LUNGE_TIP = 3.0;
    private static final double THORN_MAX = 15.0;
    private static final double SNARE_R = 1.6;
    private static final int SNARE_TICKS = 30;
    private static final double SPRAY_RANGE = 11.0;
    private static final double SPRAY_HALF = 25;
    private static final double FERTILE_R = 1.5;
    private static final double POLLEN_R = 2.2;
    private static final double BEAM_R = 2.0;
    private static final double PHOTO_R = 3.0;
    private static final int BUSH_TICKS = 100;
    private static final int BEAM_EVERY = 90;
    private static final int PHOTO_EVERY = 320;
    private static final DustParticleOptions GREEN = new DustParticleOptions(0x6BD64A, 1.4F);
    private static final DustParticleOptions LEAFY = new DustParticleOptions(0x3E8A30, 1.8F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions WATER = new DustParticleOptions(0x5AB4FF, 1.4F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions SUN = new DustParticleOptions(0xFFF2B0, 2.2F);
    private static final DustParticleOptions POLLEN_DUST = new DustParticleOptions(0xF2E05A, 1.3F);
    private static final DustParticleOptions PETAL = new DustParticleOptions(0xEC56AA, 1.2F);

    private record Temp(BlockState original, BlockState placed, int until) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    /** A rooted player: when it ends, the swing count it started with and the lowest health seen since. */
    private static final class Snare {
        final int until;
        final int swing;
        float health;

        Snare(int until, int swing, float health) {
            this.until = until;
            this.swing = swing;
            this.health = health;
        }
    }

    private @Nullable Vec3 centre;
    private int radius = 17;
    /** Phase 3 has started (the sun-lamp ignited). */
    private boolean sunlit;
    private int guard;
    private int roarUntil = -1;
    private int beamTimer = 60;
    private int photoTimer = 240;
    // moves in flight
    private double lungeLen = 6.0;
    private Vec3 lungeFrom = Vec3.ZERO;
    private Vec3 lungeTo = Vec3.ZERO;
    private final List<List<Vec3>> thornLines = new ArrayList<>();
    private @Nullable Vec3 snareSpot;
    private final List<Vec3> pollenSpots = new ArrayList<>();
    private final Map<UUID, Snare> snares = new HashMap<>();
    private final Set<UUID> adds = new HashSet<>();
    // thorn bushes: temporary blocks with the original state and the tick they go back
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public ThornGardener(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 650.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ThornGardener.TICKS;
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

    // ------------------------------------------------------------------ arena memory (the lily pad)

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

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Top of the first solid shape at or below {@code y + 2} (scanning 8 blocks), or NaN. */
    private static double floorY(ServerLevel level, double x, double y, double z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(y + 2), Mth.floor(z));
        for (int i = 0; i < 8; i++) {
            VoxelShape s = level.getBlockState(p).getCollisionShape(level, p);
            if (!s.isEmpty()) {
                return p.getY() + s.max(Direction.Axis.Y);
            }
            p.move(0, -1, 0);
        }
        return Double.NaN;
    }

    private static boolean clear(ServerLevel level, double x, double y, double z, int height) {
        BlockPos b = BlockPos.containing(x, y + 0.05, z);
        for (int k = 0; k < height; k++) {
            BlockPos q = b.above(k);
            if (!level.getBlockState(q).getCollisionShape(level, q).isEmpty()) {
                return false;
            }
        }
        return true;
    }

    /**
     * A spot of open pad at (x, z): floor within 0.6 of the seal's level (the pad is flat; the rim stands 2.5 higher,
     * the water lies far below), two blocks of air over it and, with {@code inArena}, within the arena's radius; or null.
     */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z, boolean inArena) {
        Vec3 c = centre();
        if (inArena && Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > 0.6 || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
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

    /** Height of {@code e}'s feet over the floor under it (0 standing, more when jumping). */
    private static double overFloor(ServerLevel level, LivingEntity e) {
        double fy = floorY(level, e.getX(), e.getY(), e.getZ());
        return Double.isNaN(fy) ? 9.0 : e.getY() - fy;
    }

    /** The push is dropped where it would carry {@code e} off the open pad (into the rim, toward the water). */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 dir = push.multiply(1, 0, 1).normalize();
        for (double d : new double[] {1.5, 3.0}) {
            Vec3 probe = e.position().add(dir.scale(d));
            if (pad(level, probe.x, probe.z, true) == null) {
                return Vec3.ZERO;
            }
        }
        return new Vec3(push.x, 0, push.z);
    }

    /** Pushes capped at 1.0, lift at 0.4 (0.2 when no open pad lies 3 blocks beyond); none off the pad. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.0, knockback));
        }
        shove(level, e, damage, push, lift);
    }

    private void shove(ServerLevel level, LivingEntity e, float damage, Vec3 push, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 safe = safePush(level, e, push);
        lift = Math.min(lift, safe.lengthSqr() < push.lengthSqr() - 1.0E-6 ? 0.2 : 0.4);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
    }

    private void leafBurst(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AZALEA_LEAVES.defaultBlockState()), at.x, at.y + 0.5,
                at.z, count, spread, 0.4, spread, 0.1);
        level.sendParticles(LEAFY, at.x, at.y + 0.6, at.z, count / 2, spread, 0.4, spread, 0.0);
    }

    /** The sprinkler rose of the watering-can cannon, over his right shoulder. */
    private Vec3 rose() {
        Vec3 f = forward();
        Vec3 right = new Vec3(-f.z, 0, f.x).scale(-1);
        return position().add(right.scale(0.6)).add(f.scale(1.1)).add(0, 3.0, 0);
    }

    private Vec3 bloom() {
        return position().add(0, 3.3, 0);
    }

    /** The sun-lamp's lens over the arena's centre. */
    private Vec3 lamp() {
        Vec3 c = centre();
        return new Vec3(c.x, c.y + 17.0, c.z);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // snip: both shears swung wide open (0.8 s, the arc drawn green), the right shears snap shut across his front:
        // 12 and a small push; he turns (up to 25°), the left arc is drawn red at once and snaps 0.4 s later: 10
        out.add(BossAttack.of("snip").anim(SNIP).timing(16, 14, 14).range(0, 6.0).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SNIP_RANGE, SNIP_HALF, GREEN);
                        b.telegraphArc(level, SNIP_RANGE - 2.0, SNIP_HALF, GREEN);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.SHEEP_SHEAR, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> snip(level, 12.0F, 0.6))
                .active((b, level, t, tick) -> {
                    if (tick == 1) {
                        turnToward(t, 25.0F);
                    }
                    if (tick >= 1 && tick < 8 && tick % 2 == 1) {
                        b.telegraphArc(level, SNIP_RANGE, SNIP_HALF, RED);
                        b.telegraphArc(level, SNIP_RANGE - 2.0, SNIP_HALF, RED);
                    }
                    if (tick == 8) {
                        snip(level, 10.0F, 0.5);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 7.0 ? "spray" : "lunge");
                    }
                })
                .build());
        // lunge: he crouches, the right shears drawn back wide open (1.1 s; the lane drawn green follows you slowly,
        // then locks red 0.4 s before), springs down the lane in 0.25 s and the blades snap shut at full reach: 15 to
        // everyone in the lane and 3 blocks past its end, a small push
        out.add(BossAttack.of("lunge").anim(LUNGE).timing(22, 12, 16).range(4.0, 12.0).cooldown(100).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    lungeLen = lineLength(level, LUNGE_MAX);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 14) {
                        turnToward(t, 4.0F);
                        lungeLen = lineLength(level, LUNGE_MAX);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), lungeLen + LUNGE_TIP, LUNGE_HALF, tick < 14 ? GREEN : RED);
                    }
                    if (tick % 7 == 0) {
                        level.playSound(null, b, SoundEvents.SHEEP_SHEAR, SoundSource.HOSTILE, 1.0F, 0.6F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    lungeFrom = position();
                    lungeTo = position().add(forward().scale(Math.max(0.0, lungeLen - 1.0)));
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 5) {
                        Vec3 step = lungeTo.subtract(position()).multiply(1, 0, 1).scale(1.0 / (5 - tick));
                        move(MoverType.SELF, step);
                        setDeltaMovement(0, getDeltaMovement().y, 0);
                        leafBurst(level, position(), 4, 0.4);
                    }
                    if (tick == 4) {
                        lungeCut(level);
                    }
                })
                .build());
        // thorns: both shears plunged into the pad (1.0 s); lines of thorns (3, phase 2 five) are marked from the start,
        // fanning out from him (one at you), red for the last 0.4 s; the thorns burst along each line one block a tick:
        // 11, a lift and Slowness I 1 s (once)
        out.add(BossAttack.of("thorns").anim(THORNS).timing(20, 24, 14).range(0, 22.0).cooldown(150).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planThorns(level);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 12 ? RED : GREEN;
                        for (List<Vec3> line : thornLines) {
                            for (Vec3 p : line) {
                                level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (List<Vec3> line : thornLines) {
                        b.addEffect(thornRun(line));
                    }
                    leafBurst(level, ahead(1.5), 20, 0.6);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.7F);
                })
                .build());
        // snare: the left shears stabbed into the pad at his feet (1.2 s); a ring (r 1.6) under you, following you until
        // 0.7 s, then locked red, a vine creeping to it from his feet; it closes: 6 and rooted 1.5 s. Hit anything, or be
        // hurt by anything, and the vine tears at once (so nothing lands on you for free while you are held)
        out.add(BossAttack.of("snare").anim(SNARE).timing(24, 10, 14).range(3.0, 18.0).cooldown(200).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    snareSpot = t != null ? pad(level, t.getX(), t.getZ(), true) : null;
                    if (snareSpot == null) {
                        Vec3 a = ahead(5.0);
                        snareSpot = new Vec3(a.x, getY(), a.z);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 14 && t != null) {
                        Vec3 s = pad(level, t.getX(), t.getZ(), true);
                        if (s != null && flatDist(s, position()) > 2.5) {
                            snareSpot = s;
                        }
                    }
                    Vec3 s = snareSpot;
                    if (s == null) {
                        return;
                    }
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, s, SNARE_R, tick < 14 ? GREEN : RED);
                    }
                    Vec3 to = s.subtract(position());
                    double f = (tick + 1) / 24.0;
                    for (double d = 0.5; d <= to.length() * f; d += 0.7) {
                        Vec3 p = position().add(to.normalize().scale(d));
                        level.sendParticles(LEAFY, p.x, p.y + 0.1, p.z, 1, 0.05, 0, 0.05, 0);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, s.x, s.y, s.z, SoundEvents.ROOTED_DIRT_PLACE, SoundSource.HOSTILE, 1.2F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> closeSnare(level))
                .build());
        // spray: the watering-can cannon levelled over his shoulder (1.3 s; the cone drawn blue from 0.3 s, following you
        // slowly, red from 0.8 s), then a jet of water for 1 s: 3 and a small push (0.35, never off the pad) four times
        // to whoever stays in it; where it soaked the pad, 2 patches (phase 2 three) are fertilized: marked for 1.5 s,
        // then thorn bushes spring up there (7 in r 1.5) and stay 5 s
        out.add(BossAttack.of("spray").anim(SPRAY).timing(26, 20, 14).range(0, SPRAY_RANGE).cooldown(160).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 16) {
                        turnToward(t, 3.0F);
                    }
                    if (tick >= 6 && tick % 3 == 0) {
                        drawCone(level, tick < 16 ? WATER : RED);
                    }
                    Vec3 r = rose();
                    level.sendParticles(ParticleTypes.DRIPPING_WATER, r.x, r.y, r.z, 1, 0.2, 0.2, 0.2, 0);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BUCKET_FILL, SoundSource.HOSTILE, 1.4F, 0.5F + tick * 0.02F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick < 20) {
                        sprayJet(level);
                        if (tick % 5 == 0) {
                            hitSpray(level);
                        }
                        if (tick % 6 == 0) {
                            level.playSound(null, b, SoundEvents.BUCKET_EMPTY, SoundSource.HOSTILE, 1.5F, 0.6F);
                        }
                    }
                    if (tick == 19) {
                        fertilize(level);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // call: the shears clacked together over his head three times (1.0 s): dart frogs and clockwork spiders of the
        // garden climb onto the pad (2, more in co-op), never more than 3 of them at once
        out.add(BossAttack.of("call").anim(CALL).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick == 6 || tick == 12 || tick == 18) {
                        level.playSound(null, b, SoundEvents.SHEEP_SHEAR, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                    Vec3 f = bloom();
                    level.sendParticles(PETAL, f.x, f.y + 0.5, f.z, 1, 0.3, 0.2, 0.3, 0);
                })
                .impact((b, level, t, tick) -> {
                    leafBurst(level, position(), 30, 2.0);
                    spawnAdds(level, 2);
                })
                .build());
        // pollen: he bows and shakes his head (0.9 s); rings (r 2.2) are marked in yellow under you and the other players
        // (2, phase 3 three); the bloom bursts at impact, the pollen lands 0.8 s later (the rings red meanwhile): 8 and
        // Slowness I 2 s
        out.add(BossAttack.of("pollen").anim(POLLEN).phaseTwo().timing(18, 12, 14).range(0, 24.0).cooldown(130).weight(7)
                .track(false)
                .start((b, level, t, tick) -> planPollen(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Vec3 s : pollenSpots) {
                            b.telegraphRing(level, s, POLLEN_R, POLLEN_DUST);
                        }
                    }
                    Vec3 f = bloom();
                    level.sendParticles(POLLEN_DUST, f.x, f.y, f.z, 2, 0.4, 0.3, 0.4, 0);
                })
                .impact((b, level, t, tick) -> {
                    Vec3 f = bloom();
                    level.sendParticles(POLLEN_DUST, f.x, f.y + 0.5, f.z, 40, 0.8, 0.8, 0.8, 0.05);
                    level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, f.x, f.y + 0.5, f.z, 30, 1.0, 0.8, 1.0, 0.02);
                    level.playSound(null, b, SoundEvents.AZALEA_LEAVES_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    for (Vec3 s : pollenSpots) {
                        b.addEffect(pollenCloud(f, s, 16));
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // ignite: both shears thrown up to the sun-lamp (2.0 s, guarded; gold rings gather round him, light rains down
        // from the lamp), slammed down: the lamp ignites and a wave runs to 14 (10, jump it); the sunbeams start
        out.add(BossAttack.of("ignite").anim(IGNITE).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, GOLD);
                    }
                    Vec3 l = lamp();
                    for (double y = l.y; y > b.getY() + 4; y -= 2.0) {
                        level.sendParticles(SUN, l.x + (getRandom().nextDouble() - 0.5) * 3, y, l.z + (getRandom().nextDouble() - 0.5) * 3,
                                1, 0, 0, 0, 0);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.6F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> ignite(level))
                .build());
        // photosynth: he plants his shears, spreads his arms and turns his jar up to the lamp (1.5 s; a ring of light
        // r 3 drawn round him in gold, a beam coming down on him); for 2.5 s he basks, healing 1% of his health every
        // 0.5 s (5 pulses), unless a player stands in the ring to shade him (that pulse is lost). He does nothing else.
        out.add(BossAttack.of("photosynth").anim(PHOTOSYNTH).phaseTwo().timing(30, 50, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), PHOTO_R, GOLD);
                    }
                    lightColumn(level, b.position(), (tick + 1) / 30.0);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 1.2F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), PHOTO_R, GOLD);
                    }
                    lightColumn(level, b.position(), 1.0);
                    if (tick % 10 == 5) {
                        photosynthPulse(level);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void snip(ServerLevel level, float damage, double knock) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SNIP_HALF));
        for (LivingEntity e : victims(level, position(), SNIP_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SNIP_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.5) {
                strike(level, e, damage, knock, 0.2);
            }
        }
        for (double a = -SNIP_HALF; a <= SNIP_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SNIP_RANGE - 1.0));
            level.sendParticles(LEAFY, p.x, p.y + 1.2, p.z, 2, 0.1, 0.2, 0.1, 0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.SHEEP_SHEAR, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /** The lunge's closing blades: everyone within the lane from where he sprang to 3 blocks past where he stands. */
    private void lungeCut(ServerLevel level) {
        Vec3 dir = forward();
        double len = flatDist(lungeFrom, position()) + LUNGE_TIP;
        for (LivingEntity e : victims(level, position(), len + 2)) {
            Vec3 to = e.position().subtract(lungeFrom).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            if (along >= -0.5 && along <= len && side <= LUNGE_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 15.0F, 0.5, 0.2);
            }
        }
        Vec3 tip = ahead(2.0);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, tip.x, tip.y + 1.2, tip.z, 2, 0.3, 0.1, 0.3, 0);
        level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 1.2, tip.z, 12, 0.5, 0.3, 0.5, 0.2);
        level.playSound(null, this, SoundEvents.SHEEP_SHEAR, SoundSource.HOSTILE, 2.5F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.8F, 1.6F);
    }

    /** How far a line along his facing runs over open pad (stopping at the rim, the arena's edge). */
    private double lineLength(ServerLevel level, double max) {
        double len = 2.0;
        for (double d = 1.0; d <= max; d += 1.0) {
            Vec3 p = ahead(d);
            if (pad(level, p.x, p.z, true) == null) {
                break;
            }
            len = d;
        }
        return Math.max(2.0, len);
    }

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double len, double half, DustParticleOptions dust) {
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = from.add(dir.scale(d));
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = p.add(side.scale(s * half));
                level.sendParticles(dust, q.x, from.y + 0.15, q.z, 1, 0, 0, 0, 0);
            }
            if (((int) d) % 2 == 0) {
                level.sendParticles(dust, p.x, from.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /** Thorn lines from him: 3 (phase 2: 5), the middle one at his facing, 22° apart, over open pad only. */
    private void planThorns(ServerLevel level) {
        thornLines.clear();
        int n = phase() == 2 ? 5 : 3;
        for (int i = 0; i < n; i++) {
            double a = (i - (n - 1) / 2.0) * 22.0;
            Vec3 dir = rotate(forward(), a);
            List<Vec3> line = new ArrayList<>();
            for (double d = 1.5; d <= THORN_MAX; d += 1.0) {
                Vec3 p = position().add(dir.scale(d));
                Vec3 s = pad(level, p.x, p.z, true);
                if (s == null) {
                    break;
                }
                line.add(s);
            }
            if (!line.isEmpty()) {
                thornLines.add(line);
            }
        }
    }

    /** Thorns bursting along a line, one point a tick from him outward: 11, a lift and a slow (once). */
    private Effect thornRun(List<Vec3> line) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof ThornGardener g)) {
                return true;
            }
            int k = t[0]++;
            if (k >= line.size()) {
                return true;
            }
            Vec3 p = line.get(k);
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.ROOTED_DIRT.defaultBlockState()), p.x, p.y + 0.6,
                    p.z, 8, 0.25, 0.5, 0.25, 0.05);
            level.sendParticles(LEAFY, p.x, p.y + 1.0, p.z, 4, 0.15, 0.7, 0.15, 0);
            level.sendParticles(GREEN, p.x, p.y + 1.6, p.z, 2, 0.1, 0.3, 0.1, 0);
            if (k % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.SWEET_BERRY_BUSH_PLACE, SoundSource.HOSTILE, 1.0F, 0.6F + k * 0.03F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 2.0 && hit.add(e.getUUID())) {
                    g.strike(level, e, 11.0F, 0.0, 0.4);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                }
            }
            return false;
        };
    }

    // ---- the snare

    private void closeSnare(ServerLevel level) {
        Vec3 s = snareSpot;
        if (s == null) {
            return;
        }
        leafBurst(level, s, 30, 0.8);
        level.playSound(null, s.x, s.y, s.z, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
        for (LivingEntity e : victims(level, s, SNARE_R + 1)) {
            if (flatDist(e.position(), s) <= SNARE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.0) {
                strike(level, e, 6.0F, 0.0, 0.0);
                if (e instanceof Player p && p.isAlive()) {
                    snares.put(p.getUUID(), new Snare(tickCount + SNARE_TICKS, p.getLastHurtMobTimestamp(), p.getHealth()));
                    p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, SNARE_TICKS, 9, false, false));
                } else {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, SNARE_TICKS, 3));
                }
            }
        }
    }

    /** The rooted players: vines round their legs; torn by any swing they make or any hurt they take, or in 1.5 s. */
    private void tickSnares(ServerLevel level) {
        if (snares.isEmpty()) {
            return;
        }
        for (Map.Entry<UUID, Snare> en : new ArrayList<>(snares.entrySet())) {
            Snare s = en.getValue();
            if (!(level.getEntity(en.getKey()) instanceof Player p) || !p.isAlive()) {
                snares.remove(en.getKey());
                continue;
            }
            boolean torn = p.getLastHurtMobTimestamp() != s.swing || p.getHealth() < s.health - 0.01F;
            s.health = Math.min(s.health, p.getHealth());
            if (torn || tickCount >= s.until) {
                release(level, p);
                snares.remove(en.getKey());
                continue;
            }
            if (tickCount % 2 == 0) {
                for (int i = 0; i < 4; i++) {
                    double a = (tickCount * 0.3) + i * Math.PI / 2;
                    level.sendParticles(LEAFY, p.getX() + Math.cos(a) * 0.5, p.getY() + 0.2 + (i % 2) * 0.5, p.getZ() + Math.sin(a) * 0.5,
                            1, 0, 0, 0, 0);
                }
            }
        }
    }

    private void release(ServerLevel level, Player p) {
        MobEffectInstance slow = p.getEffect(MobEffects.SLOWNESS);
        if (slow != null && slow.getAmplifier() == 9) {
            p.removeEffect(MobEffects.SLOWNESS);
        }
        leafBurst(level, p.position(), 12, 0.4);
        level.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.GRASS_BREAK, SoundSource.HOSTILE, 1.2F, 0.8F);
    }

    private void releaseAll(ServerLevel level) {
        for (UUID id : snares.keySet()) {
            if (level.getEntity(id) instanceof Player p) {
                release(level, p);
            }
        }
        snares.clear();
    }

    // ---- the spray and the fertilized patches

    private void drawCone(ServerLevel level, DustParticleOptions dust) {
        for (double r = 3.5; r <= SPRAY_RANGE; r += 3.75) {
            telegraphArc(level, r, SPRAY_HALF, dust);
        }
        telegraphArc(level, SPRAY_RANGE, SPRAY_HALF, dust);
        for (int s = -1; s <= 1; s += 2) {
            Vec3 dir = rotate(forward(), s * SPRAY_HALF);
            for (double d = 1.5; d <= SPRAY_RANGE; d += 1.5) {
                Vec3 p = position().add(dir.scale(d));
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private void sprayJet(ServerLevel level) {
        Vec3 r = rose();
        for (int i = 0; i < 6; i++) {
            Vec3 dir = rotate(forward(), (getRandom().nextDouble() * 2 - 1) * SPRAY_HALF);
            double sp = 0.5 + getRandom().nextDouble() * 0.4;
            level.sendParticles(ParticleTypes.SPLASH, r.x, r.y, r.z, 0, dir.x, -0.15, dir.z, sp);
        }
        for (double d = 2.0; d <= SPRAY_RANGE; d += 2.0) {
            Vec3 p = ahead(d);
            level.sendParticles(WATER, p.x, p.y + 1.2 - d * 0.08, p.z, 2, d * 0.18, 0.3, d * 0.18, 0);
            level.sendParticles(ParticleTypes.FALLING_WATER, p.x, p.y + 1.5, p.z, 1, d * 0.2, 0.3, d * 0.2, 0);
        }
    }

    private void hitSpray(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SPRAY_HALF));
        for (LivingEntity e : victims(level, position(), SPRAY_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SPRAY_RANGE + e.getBbWidth() / 2 && (d < 1.5 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 4.0) {
                Vec3 push = d < 1.0E-3 ? fwd.scale(0.35) : to.normalize().scale(0.35);
                shove(level, e, 3.0F, push, 0.1);
                e.clearFire();
            }
        }
    }

    /** Patches in the soaked cone: 2 (phase 2: 3), 4-10 out, on open pad, at least 3 apart. */
    private void fertilize(ServerLevel level) {
        int n = phase() == 2 ? 3 : 2;
        List<Vec3> spots = new ArrayList<>();
        for (int tries = 0; tries < 30 && spots.size() < n; tries++) {
            Vec3 dir = rotate(forward(), (getRandom().nextDouble() * 2 - 1) * SPRAY_HALF * 0.8);
            Vec3 p = position().add(dir.scale(4.0 + getRandom().nextDouble() * 6.0));
            Vec3 s = pad(level, p.x, p.z, true);
            if (s == null) {
                continue;
            }
            boolean ok = true;
            for (Vec3 o : spots) {
                if (flatDist(o, s) < 3.0) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                spots.add(s);
            }
        }
        for (Vec3 s : spots) {
            addEffect(fertile(s));
        }
    }

    /** A fertilized patch: marked for 30 ticks (red for the last 10), then thorn bushes spring up: 7 in r 1.5. */
    private Effect fertile(Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, FERTILE_R, k >= 20 ? RED : GREEN);
                }
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.HAPPY_VILLAGER, at.x, at.y + 0.3, at.z, 3, 0.6, 0.1, 0.6, 0);
                }
                return false;
            }
            if (boss instanceof ThornGardener g) {
                g.leafBurst(level, at, 24, 0.8);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.SWEET_BERRY_BUSH_PLACE, SoundSource.HOSTILE, 2.0F, 0.6F);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.BONE_MEAL_USE, SoundSource.HOSTILE, 1.5F, 0.7F);
                for (LivingEntity e : boss.victims(level, at, FERTILE_R + 1)) {
                    if (flatDist(e.position(), at) <= FERTILE_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.0) {
                        g.strike(level, e, 7.0F, 0.0, 0.3);
                    }
                }
                g.growBushes(level, at);
            }
            return true;
        };
    }

    /** Sweet berry bushes in the air over the moss of the plus of 5 cells round {@code at}, each gone in 5 s. */
    private void growBushes(ServerLevel level, Vec3 at) {
        BlockPos c = BlockPos.containing(at.x, at.y + 0.05, at.z);
        int until = tickCount + BUSH_TICKS;
        BlockState bush = Blocks.SWEET_BERRY_BUSH.defaultBlockState().setValue(SweetBerryBushBlock.AGE, 2);
        int[][] cells = {{0, 0}, {1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        for (int[] o : cells) {
            BlockPos p = c.offset(o[0], 0, o[1]);
            if (!level.isLoaded(p) || temps.containsKey(p.asLong())) {
                continue;
            }
            BlockState s = level.getBlockState(p);
            if (!s.isAir() || !bush.canSurvive(level, p)) {
                level.sendParticles(LEAFY, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 6, 0.3, 0.3, 0.3, 0);
                continue;
            }
            temps.put(p.asLong(), new Temp(s, bush, until));
            level.setBlock(p, bush, 3);
        }
    }

    private void clearTemp(ServerLevel level, long key) {
        Temp t = temps.remove(key);
        BlockPos p = BlockPos.of(key);
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        if (level.getBlockState(p).getBlock() == t.placed().getBlock()) {
            level.setBlock(p, t.original(), 3);
            level.sendParticles(LEAFY, p.getX() + 0.5, p.getY() + 0.4, p.getZ() + 0.5, 3, 0.25, 0.2, 0.25, 0);
        }
    }

    /** Every changed block goes back (only where it is still the one set). */
    private void restoreAll(ServerLevel level) {
        for (SavedTemp s : staleTemps) {
            temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed(), 0));
        }
        staleTemps.clear();
        for (Long key : new ArrayList<>(temps.keySet())) {
            clearTemp(level, key);
        }
    }

    // ---- the garden's creatures

    private int liveAdds(ServerLevel level) {
        adds.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        return adds.size();
    }

    private void spawnAdds(ServerLevel level, int base) {
        int n = Math.min(3 - liveAdds(level), scaledCount(base));
        for (int i = 0; i < n; i++) {
            EntityType<? extends Mob> type = i % 2 == 0 ? ModEntities.DART_FROG_ASSASSIN.get() : ModEntities.CLOCKWORK_SPIDER.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                at = pad(level, getX() + Math.cos(a) * 3.5, getZ() + Math.sin(a) * 3.5, true);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            leafBurst(level, at, 12, 0.4);
        }
    }

    private void discardAdds(ServerLevel level) {
        for (UUID id : adds) {
            var e = level.getEntity(id);
            if (e != null && e.isAlive()) {
                level.sendParticles(ParticleTypes.POOF, e.getX(), e.getY() + 0.5, e.getZ(), 10, 0.3, 0.3, 0.3, 0.02);
                e.discard();
            }
        }
        adds.clear();
    }

    // ---- pollen

    /** Pollen rings: the target, then the other players, then open pad near the target; at least 4 apart. */
    private void planPollen(ServerLevel level, @Nullable LivingEntity target) {
        pollenSpots.clear();
        int n = sunlit ? 3 : 2;
        if (target != null) {
            tryPollen(level, target.getX(), target.getZ());
        }
        for (Player p : fighters(level)) {
            if (pollenSpots.size() >= Math.max(n, 1 + Math.min(3, fighters(level).size() - 1))) {
                break;
            }
            if (p != target) {
                tryPollen(level, p.getX(), p.getZ());
            }
        }
        Vec3 base = target != null ? target.position() : ahead(6.0);
        for (int tries = 0; tries < 40 && pollenSpots.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 4.0 + getRandom().nextDouble() * 3.0;
            tryPollen(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d);
        }
    }

    private void tryPollen(ServerLevel level, double x, double z) {
        Vec3 s = pad(level, x, z, true);
        if (s == null) {
            return;
        }
        for (Vec3 o : pollenSpots) {
            if (flatDist(o, s) < 4.0) {
                return;
            }
        }
        pollenSpots.add(s);
    }

    /** A puff of pollen arcing from the bloom onto its ring (red meanwhile), bursting: 8 and Slowness I 2 s. */
    private Effect pollenCloud(Vec3 from, Vec3 at, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                double f = (k + 1) / (double) delay;
                Vec3 p = from.lerp(at, f).add(0, Math.sin(f * Math.PI) * 3.0, 0);
                level.sendParticles(POLLEN_DUST, p.x, p.y, p.z, 4, 0.25, 0.25, 0.25, 0);
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, POLLEN_R, RED);
                }
                return false;
            }
            level.sendParticles(POLLEN_DUST, at.x, at.y + 0.8, at.z, 50, 1.2, 0.6, 1.2, 0.02);
            level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, at.x, at.y + 1.0, at.z, 20, 1.2, 0.6, 1.2, 0.01);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.AZALEA_LEAVES_BREAK, SoundSource.HOSTILE, 1.5F, 1.2F);
            if (boss instanceof ThornGardener g) {
                for (LivingEntity e : boss.victims(level, at, POLLEN_R + 1)) {
                    if (flatDist(e.position(), at) <= POLLEN_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        g.strike(level, e, 8.0F, 0.0, 0.0);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0));
                    }
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ phase 3: the sun-lamp

    private void ignite(ServerLevel level) {
        sunlit = true;
        beamTimer = 50;
        photoTimer = 200;
        addEffect(padRing(position(), 14.0, 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("thorn_gardener_sun"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 l = lamp();
        level.sendParticles(ParticleTypes.END_ROD, l.x, l.y, l.z, 60, 2.5, 1.5, 2.5, 0.15);
        level.sendParticles(SUN, l.x, l.y, l.z, 80, 3.0, 2.0, 3.0, 0);
        level.sendParticles(POLLEN_DUST, getX(), getY() + 3, getZ(), 50, 2.0, 1.5, 2.0, 0.05);
        level.playSound(null, l.x, l.y, l.z, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 4.0F, 0.5F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** A jumpable ring of light from {@code c}: it hits once whoever stands on the floor at its edge. */
    private Effect padRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof ThornGardener g)) {
                return true;
            }
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(GOLD, c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 1.0 && overFloor(level, e) < 0.6 && hit.add(e.getUUID())) {
                    g.strike(level, e, damage, 0.6, 0.35);
                }
            }
            return rr >= max;
        };
    }

    private void lightColumn(ServerLevel level, Vec3 at, double frac) {
        Vec3 l = lamp();
        double bottom = l.y - (l.y - at.y) * Math.min(1.0, frac);
        for (double y = l.y; y >= bottom; y -= 1.5) {
            level.sendParticles(SUN, at.x + (getRandom().nextDouble() - 0.5) * 1.2, y, at.z + (getRandom().nextDouble() - 0.5) * 1.2,
                    1, 0, 0, 0, 0);
        }
    }

    /** One pulse of the basking: 1% back unless a player stands in the ring of light (r 3) round him. */
    private void photosynthPulse(ServerLevel level) {
        List<Player> shading = new ArrayList<>();
        for (Player p : fighters(level)) {
            if (flatDist(p.position(), position()) <= PHOTO_R + p.getBbWidth() / 2 && Math.abs(p.getY() - getY()) < 3.0) {
                shading.add(p);
            }
        }
        if (shading.isEmpty()) {
            heal(getMaxHealth() * 0.01F);
            level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + 2.5, getZ(), 10, 0.8, 1.0, 0.8, 0);
            level.sendParticles(PETAL, getX(), getY() + 3.4, getZ(), 6, 0.4, 0.2, 0.4, 0);
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 1.2F);
        } else {
            for (Player p : shading) {
                level.sendParticles(ParticleTypes.SMOKE, p.getX(), p.getY() + 2.2, p.getZ(), 6, 0.3, 0.1, 0.3, 0.01);
            }
            level.playSound(null, this, SoundEvents.GRASS_BREAK, SoundSource.HOSTILE, 1.0F, 0.5F);
        }
    }

    /**
     * A volley of sunbeams: one sweeping across each player (up to 3) and the rest across open pad near the target;
     * each starts 3-5 blocks from its mark and runs through it to 4 beyond (clipped to the pad).
     */
    private void castBeams(ServerLevel level, @Nullable LivingEntity target) {
        int n = Math.min(4, scaledCount(2));
        List<Vec3> marks = new ArrayList<>();
        if (target != null) {
            marks.add(target.position());
        }
        int extra = 0;
        for (Player p : fighters(level)) {
            if (p != target && extra++ < 2) {
                marks.add(p.position());
            }
        }
        Vec3 c = centre();
        for (int tries = 0; tries < 20 && marks.size() < n; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = getRandom().nextDouble() * (radius - 3);
            marks.add(new Vec3(c.x + Math.cos(a) * d, c.y, c.z + Math.sin(a) * d));
        }
        for (Vec3 m : marks) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            double back = 3.0 + getRandom().nextDouble() * 2.0;
            Vec3 start = pad(level, m.x - dir.x * back, m.z - dir.z * back, true);
            if (start == null) {
                start = pad(level, m.x, m.z, true);
            }
            if (start == null) {
                continue;
            }
            Vec3 end = start;
            for (double d = 1.0; d <= back + 4.0; d += 1.0) {
                Vec3 p = pad(level, start.x + dir.x * d, start.z + dir.z * d, true);
                if (p == null) {
                    break;
                }
                end = p;
            }
            addEffect(sunbeam(start, end));
        }
        level.playSound(null, lamp().x, lamp().y, lamp().z, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.0F, 1.4F);
    }

    /**
     * One sunbeam: its ring (r 2) and its path drawn in gold for 30 ticks (red for the last 10), then the beam comes
     * down and sweeps the path at 0.22 blocks a tick: 4 and fire 2 s every 10 ticks to whoever is in it.
     */
    private Effect sunbeam(Vec3 start, Vec3 end) {
        int[] t = {0};
        Map<UUID, Integer> last = new HashMap<>();
        double len = flatDist(start, end);
        int sweep = (int) Math.ceil(len / 0.22) + 1;
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    DustParticleOptions d = k >= 20 ? RED : GOLD;
                    boss.telegraphRing(level, start, BEAM_R, d);
                    Vec3 dir = end.subtract(start);
                    for (double s = 1.0; s <= len; s += 1.0) {
                        Vec3 p = start.add(dir.scale(s / len));
                        level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                    }
                    boss.telegraphRing(level, end, 0.6, d);
                }
                return false;
            }
            int j = k - 30;
            double f = sweep <= 1 ? 1.0 : Math.min(1.0, j / (double) (sweep - 1));
            Vec3 at = start.lerp(end, f);
            if (boss instanceof ThornGardener g) {
                Vec3 l = g.lamp();
                for (double y = l.y; y > at.y; y -= 2.0) {
                    double q = (y - at.y) / (l.y - at.y);
                    Vec3 p = at.lerp(l, q);
                    level.sendParticles(SUN, p.x, y, p.z, 1, 0.15, 0, 0.15, 0);
                }
                boss.telegraphRing(level, at, BEAM_R, GOLD);
                level.sendParticles(ParticleTypes.SMALL_FLAME, at.x, at.y + 0.1, at.z, 3, BEAM_R * 0.5, 0.05, BEAM_R * 0.5, 0.01);
                level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 0.5, at.z, 1, 0.4, 0.3, 0.4, 0.01);
                if (j % 10 == 0) {
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 1.5F, 1.2F);
                }
                for (LivingEntity e : boss.victims(level, at, BEAM_R + 1)) {
                    if (flatDist(e.position(), at) <= BEAM_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0
                            && j - last.getOrDefault(e.getUUID(), -99) >= 10) {
                        last.put(e.getUUID(), j);
                        g.strike(level, e, 4.0F, 0.0, 0.0);
                        e.igniteForSeconds(2.0F);
                    }
                }
            }
            return j >= sweep + 6;
        };
    }

    /** The lamp's light over the pad: motes drifting down, a warm glow, pollen in the air. */
    private void sunWeather(ServerLevel level) {
        Vec3 c = centre();
        double r = radius - 1.0;
        if (tickCount % 3 == 0) {
            for (int i = 0; i < 5; i++) {
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                level.sendParticles(ParticleTypes.END_ROD, x, c.y + 2 + getRandom().nextDouble() * 10, z, 0, 0, -0.05, 0, 1.0);
            }
            double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
            double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
            level.sendParticles(POLLEN_DUST, x, c.y + 1 + getRandom().nextDouble() * 3, z, 1, 0.2, 0.2, 0.2, 0);
        }
        if (tickCount % 120 == 0) {
            Vec3 l = lamp();
            level.playSound(null, l.x, l.y, l.z, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.8F);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(GOLD, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.HOSTILE, 0.8F, 1.4F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardAdds(level);
        releaseAll(level);
    }

    /** Back to the first phase (the fight was reset): the lamp dims, the bushes go, base speed. */
    private void resetForm(ServerLevel level) {
        sunlit = false;
        roarUntil = -1;
        guard = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("thorn_gardener_sun"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("thorn_gardener_wrath"));
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
        tickSnares(level);
        if (!temps.isEmpty()) {
            for (Map.Entry<Long, Temp> e : new ArrayList<>(temps.entrySet())) {
                if (tickCount >= e.getValue().until()) {
                    clearTemp(level, e.getKey());
                }
            }
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!temps.isEmpty() || !snares.isEmpty())) {
            restoreAll(level);                             // the arena emptied (death, flight)
            releaseAll(level);
        }
        if (phase() == 1 && sunlit) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!sunlit && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "ignite");
            } else if (sunlit && --photoTimer <= 0) {
                photoTimer = Math.max(200, (int) Math.round(PHOTO_EVERY * cooldownScale()));
                chain(level, "photosynth");
            }
        }
        // phase 3: the lamp's light and the sweeping sunbeams (they wait while he ignites or basks)
        if (sunlit && phase() == 2 && anyone) {
            sunWeather(level);
            cur = currentAttack();
            boolean busy = cur != null && ("ignite".equals(cur.name) || "photosynth".equals(cur.name));
            if (fighting && !busy && guard == 0 && --beamTimer <= 0) {
                beamTimer = Math.max(50, (int) Math.round(BEAM_EVERY * cooldownScale()));
                castBeams(level, target);
            }
        }
        // ambience: the flower's glow, leaves falling off him, water dripping from the rose
        if (tickCount % 4 == 0) {
            Vec3 f = bloom();
            level.sendParticles(PETAL, f.x, f.y, f.z, 1, 0.2, 0.2, 0.2, 0);
        }
        if (tickCount % 12 == 0) {
            level.sendParticles(LEAFY, getX(), getY() + 2.0, getZ(), 1, 0.6, 1.0, 0.6, 0);
            Vec3 r = rose();
            level.sendParticles(ParticleTypes.DRIPPING_WATER, r.x, r.y, r.z, 1, 0.1, 0.1, 0.1, 0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("thorn_gardener_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take it back where it would carry them off the pad
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(PETAL, getX(), getY() + 3.4, getZ(), 40, 1.0, 1.0, 1.0, 0.05);
        leafBurst(level, position(), 50, 2.0);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        leafBurst(level, position(), 80, 1.5);
        level.sendParticles(PETAL, getX(), getY() + 3, getZ(), 60, 1.0, 1.5, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.AZALEA_LEAVES_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            restoreAll(level);
            releaseAll(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("GardenerCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("GardenerRadius", radius);
        output.putBoolean("GardenerSunlit", sunlit);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("GardenerBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("GardenerCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("GardenerRadius", 17);
        sunlit = input.getBooleanOr("GardenerSunlit", false) && phase() == 2;
        staleTemps.clear();
        input.read("GardenerBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
    }
}
