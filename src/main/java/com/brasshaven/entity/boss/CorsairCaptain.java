package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
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
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.CorsairCaptain.BOARDING;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.CUTLASS;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.CYCLONE;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.DIVEBOMB;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.FLAREBOMB;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.FLARESHOT;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.GUST;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.HARPOON;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.LISTING;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.MUSTER;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.ROAR;
import static com.brasshaven.generated.MobAnims.CorsairCaptain.STAGGER;

/**
 * La Capitaine corsaire (The Corsair Captain): the sky-pirate who seized the moored airship of the Airship Graveyard,
 * a tall woman in a long teal greatcoat under a rotor engine, a cutlass in her right hand and a harpoon gun in her
 * left. She waits on the open top deck of the moored ship (42 x 35, a two-high bulwark all round).
 * <p>Three phases:
 * <ul>
 *     <li>Phase 1: the <b>cutlass</b> (two cuts), the <b>harpoon</b> (a line drawn at you: whoever it catches is reeled
 *     in and cut), the rotor <b>gust</b> (a cone that blows you toward the rail: sprint against it), the
 *     <b>dive-bomb</b> (she lifts off on the rotor and drops on a ring that follows you, then locks) and the
 *     <b>flare shot</b>.</li>
 *     <li>Phase 2 (65%): a roar, a signal flare and 2-3 sky raiders board (more in co-op). The cutlass gains a lunging
 *     thrust, the flare shot a second flare; new moves: the <b>boarding</b> rush along a drawn path and the
 *     <b>cyclone</b> spin when you hug her.</li>
 *     <li>Phase 3 (30%, driven by the class like the Chained Jailer): the ship <b>lists</b> (once, guarded, a ring to
 *     jump): from then on sweeping <b>wind lanes</b> cross the deck every ~10 s (drawn 1.5 s ahead, the gaps between
 *     them are safe) and she adds <b>flare-bombs</b>: flares fired up that fall on rings and leave short-lived fire on
 *     the deck.</li>
 * </ul>
 * Fairness: every push is capped (knockback 1.2, lift 0.35: never over the bulwark) and cancelled where no floor lies
 * ahead. The fire patches are temporary magma blocks (no fire block: the deck is wood): each goes back after 5 s, and
 * all of them when the fight resets, the arena empties, she dies or is removed, and on the first tick after a reload.
 */
public class CorsairCaptain extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 4.8F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final int PATCH_TICKS = 100;
    private static final Set<String> SCHEDULED = Set.of("muster", "listing");
    private static final DustParticleOptions RED = new DustParticleOptions(0xD83A2A, 1.4F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF0C050, 1.3F);
    private static final DustParticleOptions WIND = new DustParticleOptions(0xE6F4FF, 1.5F);
    private static final DustParticleOptions FLARE = new DustParticleOptions(0xFF6A20, 1.4F);

    private record Temp(BlockState original, BlockState placed, int until) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 18;
    private @Nullable Vec3 across;           // unit vector across the deck (the wind lanes blow along it)
    private @Nullable List<BossAttack> moves;
    private final Map<String, Integer> lastStart = new HashMap<>();
    private boolean wasPhaseTwo;
    private int musterAt = -1;
    private boolean listed;
    private int listSign = 1;
    private int guard;
    private int laneTimer;
    // moves in flight
    private final List<Vec3> spots = new ArrayList<>();
    private final List<LivingEntity> marked = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private @Nullable LivingEntity reeled;
    private @Nullable Vec3 diveSpot;
    private @Nullable LivingEntity diveMark;
    private final List<UUID> adds = new ArrayList<>();
    // fire patches: temporary magma blocks with their original state and the tick they go back
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public CorsairCaptain(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 580.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 13.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.25);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.CorsairCaptain.TICKS;
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

    // ------------------------------------------------------------------ arena geometry

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.across = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Usable deck radius round the seal (the top deck runs 16 to the side rails, 21 to the ends). */
    private double reach() {
        return Math.max(6.0, Math.min(15.0, radius - 3.0));
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

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(2.0, reach() - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    /** The floor under {@code p} (its own height if it stands on one), searched 3 up and 5 down. */
    private static Vec3 floorAt(ServerLevel level, Vec3 p) {
        BlockPos b = BlockPos.containing(p.x, p.y + 3, p.z);
        for (int i = 0; i < 9; i++) {
            BlockPos below = b.below();
            if (level.getBlockState(b).getCollisionShape(level, b).isEmpty()
                    && !level.getBlockState(below).getCollisionShape(level, below).isEmpty()) {
                return new Vec3(p.x, b.getY(), p.z);
            }
            b = below;
        }
        return p;
    }

    /** The deck goes on (or a wall stops you) 1 and 2 blocks along {@code dir}: false over a drop. */
    private static boolean floorAhead(ServerLevel level, Vec3 from, Vec3 dir) {
        for (double d = 1.0; d <= 2.01; d += 1.0) {
            Vec3 p = from.add(dir.scale(d));
            boolean ok = solid(level, p.add(0, 0.5, 0)) || solid(level, p.add(0, 1.5, 0));
            for (int dy = 1; dy <= 3 && !ok; dy++) {
                ok = solid(level, p.add(0, 0.5 - dy, 0));
            }
            if (!ok) {
                return false;
            }
        }
        return true;
    }

    /** The deck's cross axis, measured once: the shorter of the two spans between the walls round the centre. */
    private Vec3 across(ServerLevel level) {
        if (across == null) {
            double[] span = new double[4];
            Vec3[] dirs = {new Vec3(1, 0, 0), new Vec3(-1, 0, 0), new Vec3(0, 0, 1), new Vec3(0, 0, -1)};
            for (int k = 0; k < 4; k++) {
                span[k] = 32;
                for (int d = 1; d <= 32; d++) {
                    Vec3 p = centre().add(dirs[k].scale(d));
                    if (solid(level, p.add(0, 0.5, 0)) || solid(level, p.add(0, 1.5, 0))) {
                        span[k] = d;
                        break;
                    }
                }
            }
            across = span[0] + span[1] < span[2] + span[3] ? new Vec3(1, 0, 0) : new Vec3(0, 0, 1);
        }
        return across;
    }

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 14, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** Where the harpoon gun's muzzle is: at her left shoulder, a little ahead. */
    private Vec3 gunPos() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 fwd = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
        Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
        return position().add(fwd.scale(1.2)).add(left.scale(0.6)).add(0, 2.7, 0);
    }

    // ------------------------------------------------------------------ fair pushes

    /** Pushes are capped (never over the two-high bulwark) and dropped where no deck lies ahead. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 away = e.position().subtract(position()).multiply(1, 0, 1);
        double k = Math.min(1.2, knockback);
        double l = Math.min(0.35, lift);
        if (away.lengthSqr() > 1.0E-4 && !floorAhead(level, e.position(), away.normalize())) {
            k = 0;
            l = Math.min(l, 0.15);
        }
        super.strike(level, e, damage, k, l);
    }

    /** A steady wind shove along {@code dir}, adding {@code amount} a tick up to {@code cap} blocks a tick. */
    private void shove(ServerLevel level, LivingEntity e, Vec3 dir, double amount, double cap) {
        Vec3 flat = dir.multiply(1, 0, 1);
        if (flat.lengthSqr() < 1.0E-4) {
            return;
        }
        flat = flat.normalize();
        if (!floorAhead(level, e.position(), flat)) {
            return;
        }
        Vec3 v = e.getDeltaMovement().add(flat.x * amount, 0, flat.z * amount);
        double h = Math.hypot(v.x, v.z);
        if (h > cap) {
            v = new Vec3(v.x / h * cap, v.y, v.z / h * cap);
        }
        e.setDeltaMovement(v.x, Math.min(v.y, 0.2), v.z);
        e.hurtMarked = true;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        moves = out;
        // cutlass: the blade drawn back over her shoulder (0.7 s, the arc drawn in red), a forehand cut and a backhand
        // 0.5 s later (10 each, +-70 degrees, 4.8 out). P2+: a lunging thrust 0.5 s after (13 down a 6.5 line)
        out.add(BossAttack.of("cutlass").anim(CUTLASS).timing(14, 26, 14).range(0, 5.5).cooldown(40).weight(12)
                .start((b, level, t, tick) -> gate(level, t, "cutlass"))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphArc(level, 4.8, 70, RED);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_CHAIN.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 10) {
                        b.hitArc(level, 4.8, 70, 10.0F, 0.6);
                        Vec3 p = b.ahead(2.5);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 2.0, p.z, 2, 0.6, 0.3, 0.6, 0);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, tick == 0 ? 0.8F : 0.95F);
                    } else if (b.phase() == 2 && tick > 10 && tick < 20 && tick % 2 == 0) {
                        for (double d = 1.5; d <= 6.5; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(RED, p.x, p.y + 0.15, p.z, 1, 0.15, 0, 0.15, 0);
                        }
                    } else if (b.phase() == 2 && tick == 20) {
                        b.lunge(0.6, 0.0);
                        b.hitLine(level, 6.5, 1.0, 13.0F, 0.8);
                        level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .build());
        // harpoon: the gun levelled at you (0.9 s, the line drawn in red, turning with you): the harpoon flies down it
        // (up to 20, walls stop it); the first one it meets takes 8 and is reeled in over 0.45 s, then a cutlass cut
        // at 1.5 s (9, +-60 degrees, a ring drawn first). Sidestep the line
        out.add(BossAttack.of("harpoon").anim(HARPOON).timing(18, 16, 14).range(6, 20).cooldown(120).weight(9)
                .start((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.gate(level, t, "harpoon")) {
                        c.reeled = null;
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_START.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0 && b instanceof CorsairCaptain c) {
                        double len = t != null ? Math.min(20, b.distanceTo(t) + 2) : 14;
                        for (double d = 1.5; d <= len; d += 0.9) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(RED, p.x, p.y + 1.2, p.z, 1, 0.02, 0.02, 0.02, 0);
                        }
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c) {
                        c.fireHarpoon(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c) {
                        c.reelTick(level, tick);
                    }
                })
                .build());
        // gust: feet planted, the rotor tilted and spun up (1.0 s, the cone drawn in white wind, +-40 degrees, 12 deep):
        // 3 at once, then for 1 s everyone in the cone is blown away from her (sprinting against it holds)
        out.add(BossAttack.of("gust").anim(GUST).timing(20, 20, 14).range(0, 12).cooldown(140).weight(8)
                .start((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.gate(level, t, "gust")) {
                        level.playSound(null, b, SoundEvents.BREEZE_INHALE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof CorsairCaptain c) {
                        c.drawCone(level, 12, 40, WIND);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 5.0, b.getZ(), 2, 0.6, 0.1, 0.6, 0.05);
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.BREEZE_CHARGE, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    if (b instanceof CorsairCaptain c) {
                        for (LivingEntity e : c.inCone(level, 12, 40)) {
                            if (e.hurtServer(level, b.damageSources().mobAttack(b), 3.0F)) {
                                e.hurtMarked = true;
                            }
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c) {
                        c.gustTick(level, tick);
                    }
                })
                .build());
        // divebomb: a crouch under the screaming rotor (0.8 s, a red ring on you), take-off: she rises (0.5 s), hovers
        // over the ring while it follows you (to 0.7 s after take-off, then it locks), and plunges onto it 1.5 s after
        // take-off: 16 within 3, then a ring to jump (6, out to 7)
        out.add(BossAttack.of("divebomb").anim(DIVEBOMB).timing(16, 34, 18).range(5, 22).cooldown(160).weight(8)
                .start((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.gate(level, t, "divebomb")) {
                        c.diveMark = t;
                        c.diveSpot = c.clampToArena(t != null ? t.position() : b.ahead(8), 2.0);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof CorsairCaptain c)) {
                        return;
                    }
                    c.followDiveMark(level);
                    if (tick % 2 == 0 && c.diveSpot != null) {
                        b.telegraphRing(level, c.diveSpot, 3.0, GOLD);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.2, b.getZ(), 3, 1.0, 0.05, 1.0, 0.05);
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 1.5F, 0.6F + tick * 0.04F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.setNoGravity(true);
                    level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, b.getX(), b.getY() + 0.5, b.getZ(), 1, 0, 0, 0, 0);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c) {
                        c.diveTick(level, tick);
                    }
                })
                .end((b, level, t, tick) -> b.setNoGravity(false))
                .build());
        // flareshot: the gun swung up and aimed (0.7 s, a thin orange line): a flare flies at you (1.4 a tick): 9 and
        // set alight 3 s; it bursts on walls (6 within 1.5). P2+: a second flare 0.3 s later at another player
        out.add(BossAttack.of("flareshot").anim(FLARESHOT).timing(14, 10, 12).range(6, 26).cooldown(70).weight(9)
                .start((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.gate(level, t, "flareshot")) {
                        c.marked.clear();
                        if (t != null) {
                            c.marked.add(t);
                        }
                        for (Player p : c.fighters(level)) {
                            if (p != t && c.marked.size() < 2) {
                                c.marked.add(p);
                            }
                        }
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && t != null) {
                        Vec3 from = b.position().add(0, 2.7, 0);
                        Vec3 to = t.position().add(0, 1.0, 0);
                        Vec3 dir = to.subtract(from);
                        double len = Math.min(26, dir.length());
                        dir = dir.normalize();
                        for (double d = 1.5; d <= len; d += 1.2) {
                            Vec3 p = from.add(dir.scale(d));
                            level.sendParticles(FLARE, p.x, p.y, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof CorsairCaptain c)) {
                        return;
                    }
                    if (tick == 0) {
                        c.shootFlare(level, c.marked.isEmpty() ? t : c.marked.get(0));
                    } else if (tick == 6 && b.phase() == 2) {
                        c.shootFlare(level, c.marked.size() > 1 ? c.marked.get(1) : (c.marked.isEmpty() ? t : c.marked.get(0)));
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2 (and 3)
        // boarding: a crouch, the cutlass levelled (0.9 s, the path drawn 14 ahead): a rush on the rotor at 1 block a
        // tick for 0.6 s: 12 once to each creature in the way and shoved aside; she stops short of the rail
        out.add(BossAttack.of("boarding").anim(BOARDING).phaseTwo().timing(18, 14, 14).range(7, 24).cooldown(130).weight(8)
                .start((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.gate(level, t, "boarding")) {
                        c.struck.clear();
                        level.playSound(null, b, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 14; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(RED, p.x, p.y + 0.15, p.z, 1, 0.3, 0, 0.3, 0);
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c) {
                        c.boardTick(level, tick);
                    }
                })
                .build());
        // cyclone: twisted back, the cutlass out wide (0.8 s, a red ring r 4.2): two full spins 0.4 s apart, 11 each
        out.add(BossAttack.of("cyclone").anim(CYCLONE).phaseTwo().timing(16, 16, 14).range(0, 5).cooldown(90).weight(9)
                .start((b, level, t, tick) -> gate(level, t, "cyclone"))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 4.2, RED);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 2.0F, 0.8F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 8) {
                        b.hitCircle(level, b.position(), 4.2, 11.0F, 0.8, 0.2);
                        for (int a = 0; a < 360; a += 45) {
                            double r = Math.toRadians(a + tick * 10);
                            level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX() + Math.cos(r) * 2.8, b.getY() + 1.8,
                                    b.getZ() + Math.sin(r) * 2.8, 1, 0, 0, 0, 0);
                        }
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .build());
        // flarebomb (phase 3 only, once the ship lists): the gun raised to the sky (1.0 s; rings follow the marked
        // players for 0.6 s, then lock red); three flares fired up 0.3 s apart (more rings in co-op); each falls 0.9 s
        // later: 10 within 2.5, set alight, and leaves a fire patch on the deck for 5 s (2 every 0.5 s, burning)
        out.add(BossAttack.of("flarebomb").anim(FLAREBOMB).phaseTwo().timing(20, 24, 14).range(0, 30).cooldown(160).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.gate(level, t, "flarebomb")) {
                        c.pickFlareSpots(level, t);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof CorsairCaptain c)) {
                        return;
                    }
                    if (tick < 12) {
                        for (int i = 0; i < c.marked.size() && i < c.spots.size(); i++) {
                            LivingEntity e = c.marked.get(i);
                            if (e != null && e.isAlive()) {
                                c.spots.set(i, c.clampToArena(e.position(), 1.5));
                            }
                        }
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 s : c.spots) {
                            b.telegraphRing(level, s, 2.5, tick < 12 ? GOLD : RED);
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && tick % 4 == 0 && tick / 4 < c.spots.size()) {
                        c.launchBomb(level, c.spots.get(tick / 4));
                    }
                })
                .build());

        // ---------------------------------------------------------------- scheduled (range 999, weight 0)
        // muster: a signal flare fired straight up (1.0 s): 2-3 sky raiders swoop aboard (+1 per 2 extra players)
        out.add(BossAttack.of("muster").anim(MUSTER).phaseTwo().timing(20, 10, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 3.0F, 0.5F))
                .windup((b, level, t, tick) -> {
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 3.0F, 0.8F);
                    for (int k = 0; k < 12; k++) {
                        level.sendParticles(FLARE, b.getX(), b.getY() + 4 + k * 1.2, b.getZ(), 2, 0.1, 0.1, 0.1, 0);
                    }
                    level.sendParticles(ParticleTypes.FIREWORK, b.getX(), b.getY() + 18, b.getZ(), 40, 1.5, 1.5, 1.5, 0.1);
                    if (b instanceof CorsairCaptain c) {
                        c.spawnRaiders(level);
                    }
                })
                .build());
        // listing (phase 3, once): the ship heels over (1.5 s, guarded, the deck creaking, a red ring round her); the
        // cutlass driven into the deck: a ring to jump (12, out to 13), +10% speed, the wind lanes start
        out.add(BossAttack.of("listing").anim(LISTING).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 74;
                    level.playSound(null, b, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.9F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, RED);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.WOOD_HIT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c) {
                        c.list(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof CorsairCaptain c && c.liveAdds(level) < 2) {
                        b.chain(level, "muster");
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ gating (flare-bombs need the list)

    private void noteStart(String name) {
        lastStart.put(name, tickCount);
    }

    private boolean gate(ServerLevel level, @Nullable LivingEntity t, String name) {
        if (!"flarebomb".equals(name) || listed) {
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
            if (a.weight <= 0 || SCHEDULED.contains(a.name) || "flarebomb".equals(a.name) || !a.allowedIn(phase())
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
        String pick = dist > 6 ? "flareshot" : "cutlass";
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

    // ---- harpoon

    private void fireHarpoon(ServerLevel level) {
        Vec3 from = position().add(0, 1.2, 0);
        Vec3 dir = forward();
        BlockHitResult wall = level.clip(new ClipContext(from.add(dir.scale(1.0)), from.add(dir.scale(20)),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        double reach = wall.getType() == HitResult.Type.MISS ? 20 : wall.getLocation().distanceTo(from);
        LivingEntity caught = null;
        double best = reach + 1;
        for (LivingEntity e : victims(level, from, reach + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            if (along > 0.5 && along <= reach && side <= 1.0 + e.getBbWidth() / 2 && along < best
                    && Math.abs(e.getY() - getY()) < 3.0) {
                caught = e;
                best = along;
            }
        }
        double shown = caught != null ? best : reach;
        for (double d = 1; d <= shown; d += 0.5) {
            Vec3 p = from.add(dir.scale(d));
            level.sendParticles(d % 1.0 == 0 ? ParticleTypes.CRIT : GOLD, p.x, p.y + 0.4, p.z, 1, 0.02, 0.02, 0.02, 0);
        }
        level.playSound(null, this, SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
        reeled = null;
        if (caught != null && caught.hurtServer(level, damageSources().mobAttack(this), 8.0F)) {
            reeled = caught;
            level.playSound(null, caught, SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 2.0F, 0.7F);
        }
    }

    private void reelTick(ServerLevel level, int tick) {
        LivingEntity e = reeled;
        if (e != null && e.isAlive() && tick >= 1 && tick <= 9) {
            Vec3 to = ahead(2.2).subtract(e.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > 0.6) {
                Vec3 v = to.normalize().scale(Math.min(0.9, 0.25 + d * 0.15));
                e.setDeltaMovement(v.x, 0.08, v.z);
                e.hurtMarked = true;
            }
            Vec3 a = position().add(0, 2.6, 0);
            Vec3 b = e.position().add(0, 1.0, 0);
            for (double k = 0; k <= 1.0; k += 0.1) {
                Vec3 p = a.lerp(b, k);
                level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
            if (tick % 3 == 1) {
                level.playSound(null, this, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
            }
        }
        if (tick >= 8 && tick < 12 && tick % 2 == 0) {
            telegraphArc(level, 3.8, 60, RED);
        }
        if (tick == 12) {
            hitArc(level, 3.8, 60, 9.0F, 0.6);
            Vec3 p = ahead(2.0);
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.8, p.z, 1, 0, 0, 0, 0);
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.9F);
            reeled = null;
        }
    }

    // ---- gust

    private List<LivingEntity> inCone(ServerLevel level, double depth, double half) {
        List<LivingEntity> out = new ArrayList<>();
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(half));
        for (LivingEntity e : victims(level, position(), depth + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= depth && d > 0.3 && to.normalize().dot(fwd) >= cos && Math.abs(e.getY() - getY()) < 4.0) {
                out.add(e);
            }
        }
        return out;
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

    private void gustTick(ServerLevel level, int tick) {
        for (LivingEntity e : inCone(level, 12, 40)) {
            shove(level, e, e.position().subtract(position()), 0.11, 0.7);
        }
        if (tick % 2 == 0) {
            for (double a = -35; a <= 35; a += 17.5) {
                Vec3 dir = rotate(forward(), a);
                Vec3 q = position().add(dir.scale(2.0)).add(0, 1.2, 0);
                level.sendParticles(ParticleTypes.CLOUD, q.x, q.y, q.z, 0, dir.x, 0.0, dir.z, 0.7);
            }
            Vec3 g = ahead(5);
            level.sendParticles(ParticleTypes.GUST, g.x, g.y + 1, g.z, 1, 2.0, 0.5, 2.0, 0);
        }
        if (tick % 6 == 0) {
            level.playSound(null, this, SoundEvents.BREEZE_IDLE_AIR, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
    }

    // ---- divebomb

    private void followDiveMark(ServerLevel level) {
        if (diveMark != null && diveMark.isAlive()) {
            diveSpot = clampToArena(diveMark.position(), 2.0);
        }
    }

    private void diveTick(ServerLevel level, int tick) {
        if (diveSpot == null) {
            diveSpot = clampToArena(ahead(6), 2.0);
        }
        if (tick < 14) {
            followDiveMark(level);
        }
        Vec3 floor = floorAt(level, diveSpot);
        if (tick % 2 == 0) {
            telegraphRing(level, floor, 3.0, tick < 14 ? GOLD : RED);
        }
        double top = floor.y + 8.0;
        if (tick < 10) {
            setDeltaMovement(getDeltaMovement().x * 0.5, Math.max(0.0, Math.min(0.9, (top - getY()) * 0.3)), getDeltaMovement().z * 0.5);
        } else if (tick < 24) {
            Vec3 want = new Vec3(floor.x, top, floor.z);
            Vec3 v = want.subtract(position()).scale(0.25);
            double h = Math.hypot(v.x, v.z);
            if (h > 1.0) {
                v = new Vec3(v.x / h, v.y, v.z / h);
            }
            setDeltaMovement(v.x, Mth.clamp(v.y, -0.4, 0.4), v.z);
        } else if (tick < 30) {
            Vec3 v = floor.subtract(position());
            setDeltaMovement(v.x * 0.4, Math.min(-0.6, v.y * 0.35), v.z * 0.4);
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2, getZ(), 3, 0.4, 0.6, 0.4, 0.05);
        } else if (tick == 30) {
            setNoGravity(false);
            if (flatDist(position(), floor) < 4.0 && Math.abs(getY() - floor.y) < 6.0
                    && !solid(level, floor.add(0, 0.5, 0)) && !solid(level, floor.add(0, 2.5, 0))) {
                teleportTo(floor.x, floor.y, floor.z);
            }
            setDeltaMovement(0, -0.2, 0);
            hitCircle(level, floor, 3.0, 16.0F, 0.9, 0.3);
            addEffect(WayfarerBoss.wave(floor, 7.0, 0.5, 6.0F, ParticleTypes.CLOUD));
            level.sendParticles(ParticleTypes.EXPLOSION, floor.x, floor.y + 0.5, floor.z, 2, 0.6, 0.1, 0.6, 0);
            level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, floor.x, floor.y + 0.5, floor.z, 1, 0, 0, 0, 0);
            level.playSound(null, floor.x, floor.y, floor.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.8F);
            level.playSound(null, floor.x, floor.y, floor.z, SoundEvents.BREEZE_LAND, SoundSource.HOSTILE, 3.0F, 0.6F);
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
        hurtMarked = true;
        if (tick < 30 && tick % 4 == 0) {
            level.playSound(null, this, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 1.5F, 1.0F);
        }
    }

    // ---- flares

    /** A flare shot from the gun at {@code at} (its position at the shot): 9 and alight on the first hit, a burst on walls. */
    private void shootFlare(ServerLevel level, @Nullable LivingEntity at) {
        Vec3 from = gunPos();
        Vec3 aim = at != null ? at.position().add(0, 1.0, 0) : from.add(forward().scale(16));
        Vec3 dir = aim.subtract(from);
        if (dir.lengthSqr() < 1.0E-4) {
            return;
        }
        Vec3 step = dir.normalize().scale(1.4);
        level.playSound(null, this, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 2.5F, 1.4F);
        Vec3[] pos = {from};
        int[] t = {0};
        addEffect((boss, lvl) -> {
            Vec3 p = pos[0];
            Vec3 next = p.add(step);
            BlockHitResult hit = lvl.clip(new ClipContext(p, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, boss));
            for (LivingEntity e : boss.victims(lvl, next, 2.0)) {
                if (e.getBoundingBox().inflate(0.6).intersects(new AABB(p, next))) {
                    if (e.hurtServer(lvl, boss.damageSources().mobAttack(boss), 9.0F)) {
                        e.igniteForSeconds(3.0F);
                        e.hurtMarked = true;
                    }
                    lvl.sendParticles(ParticleTypes.FLAME, e.getX(), e.getY() + 1, e.getZ(), 12, 0.3, 0.4, 0.3, 0.05);
                    lvl.playSound(null, e, SoundEvents.FIREWORK_ROCKET_TWINKLE, SoundSource.HOSTILE, 1.5F, 1.0F);
                    return true;
                }
            }
            if (hit.getType() != HitResult.Type.MISS || ++t[0] > 20) {
                Vec3 at2 = hit.getType() != HitResult.Type.MISS ? hit.getLocation() : next;
                for (LivingEntity e : boss.victims(lvl, at2, 2.0)) {
                    if (e.position().add(0, 1, 0).distanceTo(at2) <= 1.5 + e.getBbWidth() / 2) {
                        e.hurtServer(lvl, boss.damageSources().mobAttack(boss), 6.0F);
                    }
                }
                lvl.sendParticles(ParticleTypes.FLAME, at2.x, at2.y, at2.z, 16, 0.4, 0.4, 0.4, 0.05);
                lvl.sendParticles(FLARE, at2.x, at2.y, at2.z, 8, 0.5, 0.5, 0.5, 0);
                lvl.playSound(null, at2.x, at2.y, at2.z, SoundEvents.FIREWORK_ROCKET_TWINKLE, SoundSource.HOSTILE, 1.5F, 0.8F);
                return true;
            }
            lvl.sendParticles(FLARE, next.x, next.y, next.z, 2, 0.05, 0.05, 0.05, 0);
            lvl.sendParticles(ParticleTypes.FLAME, next.x, next.y, next.z, 1, 0.02, 0.02, 0.02, 0.01);
            pos[0] = next;
            return false;
        });
    }

    // ---- flare-bombs and fire patches (phase 3)

    private void pickFlareSpots(ServerLevel level, @Nullable LivingEntity t) {
        marked.clear();
        spots.clear();
        for (Player p : fighters(level)) {
            if (marked.size() < 4) {
                marked.add(p);
                spots.add(clampToArena(p.position(), 1.5));
            }
        }
        if (marked.isEmpty() && t != null) {
            marked.add(t);
            spots.add(clampToArena(t.position(), 1.5));
        }
        Vec3 anchor = t != null ? t.position() : ahead(8);
        int extra = Math.max(0, 3 - spots.size()) + scaledCount(1) - 1;
        for (int i = 0; i < extra && spots.size() < 6; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 3.5 + random.nextDouble() * 3.0;
            marked.add(null);
            spots.add(clampToArena(anchor.add(Math.cos(a) * r, 0, Math.sin(a) * r), 1.5));
        }
    }

    private void launchBomb(ServerLevel level, Vec3 spot) {
        Vec3 from = gunPos().add(0, 1.0, 0);
        for (int k = 0; k < 10; k++) {
            level.sendParticles(FLARE, from.x, from.y + k * 1.4, from.z, 1, 0.05, 0.05, 0.05, 0);
        }
        level.playSound(null, this, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 2.5F, 1.1F);
        Vec3 floor = floorAt(level, spot);
        int[] t = {0};
        addEffect((boss, lvl) -> {
            int k = t[0]++;
            if (k < 18) {
                if (k % 2 == 0) {
                    boss.telegraphRing(lvl, floor, 2.5, RED);
                }
                double y = floor.y + 14 - k * 0.75;
                lvl.sendParticles(FLARE, floor.x, y, floor.z, 2, 0.1, 0.1, 0.1, 0);
                lvl.sendParticles(ParticleTypes.FLAME, floor.x, y, floor.z, 1, 0.05, 0.05, 0.05, 0.01);
                return false;
            }
            for (LivingEntity e : boss.victims(lvl, floor, 3.0)) {
                if (flatDist(e.position(), floor) <= 2.5 + e.getBbWidth() / 2 && Math.abs(e.getY() - floor.y) < 2.5) {
                    boss.strike(lvl, e, 10.0F, 0.6, 0.25);
                    e.igniteForSeconds(2.0F);
                }
            }
            lvl.sendParticles(ParticleTypes.EXPLOSION, floor.x, floor.y + 0.5, floor.z, 1, 0, 0, 0, 0);
            lvl.sendParticles(ParticleTypes.FLAME, floor.x, floor.y + 0.4, floor.z, 30, 1.2, 0.3, 1.2, 0.05);
            lvl.playSound(null, floor.x, floor.y, floor.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 1.2F);
            if (boss instanceof CorsairCaptain c) {
                c.firePatch(lvl, floor);
            }
            return true;
        });
    }

    /** Five magma blocks in a plus round {@code at} (only full, plain floor blocks under air), each back in 5 s. */
    private void firePatch(ServerLevel level, Vec3 at) {
        BlockPos c = BlockPos.containing(at.x, at.y - 0.5, at.z);
        int until = tickCount + PATCH_TICKS;
        List<BlockPos> placed = new ArrayList<>();
        for (BlockPos p : new BlockPos[] {c, c.north(), c.south(), c.east(), c.west()}) {
            if (!level.isLoaded(p) || temps.containsKey(p.asLong())) {
                continue;
            }
            BlockState s = level.getBlockState(p);
            if (s.isAir() || s.hasBlockEntity() || level.getBlockEntity(p) != null || !s.isCollisionShapeFullBlock(level, p)
                    || !level.getBlockState(p.above()).isAir() || s.is(Blocks.MAGMA_BLOCK)) {
                continue;
            }
            temps.put(p.asLong(), new Temp(s, Blocks.MAGMA_BLOCK.defaultBlockState(), until));
            level.setBlock(p, Blocks.MAGMA_BLOCK.defaultBlockState(), 3);
            placed.add(p);
        }
        if (placed.isEmpty()) {
            return;
        }
        int[] t = {0};
        addEffect((boss, lvl) -> {
            int k = t[0]++;
            if (k >= PATCH_TICKS) {
                return true;
            }
            if (k % 4 == 0) {
                for (BlockPos p : placed) {
                    lvl.sendParticles(ParticleTypes.FLAME, p.getX() + 0.5, p.getY() + 1.1, p.getZ() + 0.5, 2, 0.3, 0.1, 0.3, 0.01);
                }
                lvl.sendParticles(ParticleTypes.SMOKE, at.x, at.y + 0.8, at.z, 2, 0.6, 0.2, 0.6, 0.01);
            }
            if (k % 10 == 0) {
                for (LivingEntity e : boss.victims(lvl, at, 2.5)) {
                    if (flatDist(e.position(), at) <= 1.6 + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 1.3) {
                        e.hurtServer(lvl, boss.damageSources().mobAttack(boss), 2.0F);
                        e.igniteForSeconds(2.0F);
                    }
                }
            }
            return false;
        });
    }

    private void clearTemp(ServerLevel level, long key) {
        Temp t = temps.remove(key);
        BlockPos p = BlockPos.of(key);
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        if (level.getBlockState(p).getBlock() == t.placed().getBlock()) {
            level.setBlock(p, t.original(), 3);
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

    // ---- boarding

    private void boardTick(ServerLevel level, int tick) {
        if (tick < 12) {
            Vec3 f = forward();
            Vec3 next = position().add(f.scale(1.6));
            boolean wall = solid(level, next.add(0, 0.6, 0)) || solid(level, next.add(0, 1.8, 0));
            boolean edge = flatDist(next, centre()) > reach() + 1.0 || !floorAhead(level, position(), f);
            if (wall || edge) {
                setDeltaMovement(0, getDeltaMovement().y, 0);
            } else {
                setDeltaMovement(f.x, getDeltaMovement().y, f.z);
            }
            hurtMarked = true;
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 0.5, getZ(), 2, 0.4, 0.1, 0.4, 0.02);
            Vec3 tip = ahead(1.8);
            for (LivingEntity e : victims(level, tip, 2.5)) {
                if (flatDist(e.position(), tip) <= 2.0 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                    strike(level, e, 12.0F, 1.0, 0.3);
                }
            }
            if (tick % 4 == 0) {
                level.playSound(null, this, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 1.5F, 1.2F);
            }
        } else {
            setDeltaMovement(0, getDeltaMovement().y, 0);
            hurtMarked = true;
        }
    }

    // ---- the sky raiders

    private int liveAdds(ServerLevel level) {
        adds.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        return adds.size();
    }

    private void spawnRaiders(ServerLevel level) {
        int n = Math.min(4 - liveAdds(level), scaledCount(2));
        for (int i = 0; i < n; i++) {
            Mob mob = ModEntities.SKY_RAIDER.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 12 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                double r = reach() * (0.55 + random.nextDouble() * 0.35);
                Vec3 p = floorAt(level, centre().add(Math.cos(a) * r, 0, Math.sin(a) * r)).add(0, 3, 0);
                if (!solid(level, p) && !solid(level, p.add(0, 1, 0)) && flatDist(p, position()) > 5) {
                    at = p;
                }
            }
            if (at == null) {
                at = centre().add(0, 3, 0);
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

    // ------------------------------------------------------------------ the list (phase 3)

    private void list(ServerLevel level) {
        listed = true;
        listSign = random.nextBoolean() ? 1 : -1;
        laneTimer = 60;
        addEffect(WayfarerBoss.wave(position(), 13.0, 0.55, 12.0F, ParticleTypes.CLOUD));
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.5, getZ(), 3, 1.0, 0.2, 1.0, 0);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            var id = com.brasshaven.Brasshaven.id("corsair_captain_listing");
            speed.removeModifier(id);
            speed.addPermanentModifier(new AttributeModifier(id, 0.10, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
    }

    /**
     * The wind lanes: four strips 3 wide running across the deck (along {@link #across}), 7 apart (safe gaps 4 wide).
     * Each is drawn for 1.5 s (wind streaming along it, toward the rail the ship lists to), then blows for 0.7 s:
     * 4 once, and a shove toward the rail (0.16 a tick, at most 0.8). They go off one after another, 0.5 s apart,
     * sweeping the deck from one end to the other.
     */
    private void windLanes(ServerLevel level) {
        Vec3 a = across(level);
        Vec3 along = new Vec3(-a.z, 0, a.x);
        Vec3 blow = a.scale(listSign);
        double shift = (random.nextDouble() - 0.5) * 3.0;
        boolean reverse = random.nextBoolean();
        double half = reach() + 2.0;
        level.playSound(null, this, SoundEvents.WOOD_HIT, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ELYTRA_FLYING, SoundSource.HOSTILE, 1.5F, 0.6F);
        for (int k = 0; k < 4; k++) {
            double off = -10.5 + 7.0 * (reverse ? 3 - k : k) + shift;
            Vec3 mid = centre().add(along.scale(off));
            int delay = k * 10;
            int[] t = {0};
            Set<UUID> hit = new HashSet<>();
            addEffect((boss, lvl) -> {
                int i = t[0]++;
                int warn = 30 + delay;
                if (i < warn) {
                    if (i % 2 == 0) {
                        for (double s = -half; s <= half; s += 1.5) {
                            for (int e = -1; e <= 1; e += 2) {
                                Vec3 p = mid.add(a.scale(s)).add(along.scale(1.5 * e));
                                lvl.sendParticles(i > warn - 10 ? RED : WIND, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                        Vec3 q = mid.add(a.scale((random.nextDouble() * 2 - 1) * half));
                        lvl.sendParticles(ParticleTypes.CLOUD, q.x, q.y + 0.6, q.z, 0, blow.x, 0, blow.z, 0.5);
                    }
                    return false;
                }
                if (i >= warn + 14) {
                    return true;
                }
                if (i == warn) {
                    lvl.playSound(null, mid.x, mid.y, mid.z, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                }
                for (double s = -half; s <= half; s += 2.0) {
                    Vec3 p = mid.add(a.scale(s));
                    lvl.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 0.8, p.z, 0, blow.x, 0.0, blow.z, 0.6);
                }
                if (boss instanceof CorsairCaptain c) {
                    for (LivingEntity e : boss.victims(lvl, mid, half + 2)) {
                        Vec3 rel = e.position().subtract(mid).multiply(1, 0, 1);
                        if (Math.abs(rel.dot(along)) > 1.5 + e.getBbWidth() / 2 || Math.abs(rel.dot(a)) > half
                                || Math.abs(e.getY() - mid.y) > 3.0) {
                            continue;
                        }
                        if (hit.add(e.getUUID())) {
                            e.hurtServer(lvl, boss.damageSources().mobAttack(boss), 4.0F);
                        }
                        c.shove(lvl, e, blow, 0.16, 0.8);
                    }
                }
                return false;
            });
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.02);
            level.playSound(null, this, SoundEvents.ANVIL_HIT, SoundSource.HOSTILE, 1.0F, 1.4F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        restoreAll(level);
        discardAdds(level);
        reeled = null;
        diveSpot = null;
        diveMark = null;
        setNoGravity(false);
    }

    /** Back to the first phase (the fight was reset): deck level, fires out, base speed. */
    private void resetForm(ServerLevel level) {
        wasPhaseTwo = false;
        listed = false;
        musterAt = -1;
        guard = 0;
        across = null;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("corsair_captain_listing"));
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
        if (isNoGravity() && (cur == null || !"divebomb".equals(cur.name))) {
            setNoGravity(false);                           // the dive was cut short (stagger, reset)
        }
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
        if (!anyone && (!temps.isEmpty() || !adds.isEmpty())) {
            cleanUp(level);                                // the arena emptied (death, flight)
        }
        if (phase() == 1 && (wasPhaseTwo || listed)) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && (musterAt < 0 || tickCount >= musterAt);
        if (free) {
            if (musterAt > 0) {
                musterAt = -1;
                chain(level, "muster");
            } else if (phase() == 2 && !listed && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "listing");
            }
        }
        if (listed && anyone && fighting && guard == 0 && --laneTimer <= 0) {
            laneTimer = 74 + Math.max(110, (int) Math.round(200 * cooldownScale()));
            windLanes(level);
        }
        // ambience: the rotor's downdraught, the coat in the wind
        if (tickCount % 8 == 0) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 4.9, getZ(), 1, 0.6, 0.05, 0.6, 0.01);
        }
        if (listed && tickCount % 5 == 0) {
            Vec3 a = across(level).scale(listSign);
            double r = reach();
            Vec3 q = centre().add((random.nextDouble() * 2 - 1) * r, 0.5 + random.nextDouble() * 2, (random.nextDouble() * 2 - 1) * r);
            level.sendParticles(WIND, q.x, q.y, q.z, 0, a.x, 0, a.z, 0.3);
        }
        if (tickCount % 140 == 0) {
            level.playSound(null, this, SoundEvents.BREEZE_IDLE_AIR, SoundSource.HOSTILE, 1.0F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        wasPhaseTwo = true;
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        musterAt = tickCount + roar + 4;
        reeled = null;
        setNoGravity(false);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.1);
        level.playSound(null, this, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 3, getZ(), 80, 1.0, 2.0, 1.0, 0.1);
        level.sendParticles(ParticleTypes.FIREWORK, getX(), getY() + 6, getZ(), 40, 1.0, 1.0, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BREEZE_DEATH, SoundSource.HOSTILE, 3.0F, 0.6F);
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
            output.putLong("CorsairCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("CorsairRadius", radius);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("CorsairBlocks", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("CorsairCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("CorsairRadius", 18);
        staleTemps.clear();
        input.read("CorsairBlocks", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
        // a reload mid-fight: the fires go out (first tick); the list is lost with them
        listed = false;
        setNoGravity(false);
    }
}
