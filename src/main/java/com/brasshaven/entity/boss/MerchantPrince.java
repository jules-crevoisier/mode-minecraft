package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
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

import static com.brasshaven.generated.MobAnims.MerchantPrince.AUCTION;
import static com.brasshaven.generated.MobAnims.MerchantPrince.BID;
import static com.brasshaven.generated.MobAnims.MerchantPrince.CHARGE;
import static com.brasshaven.generated.MobAnims.MerchantPrince.COINS;
import static com.brasshaven.generated.MobAnims.MerchantPrince.DASH;
import static com.brasshaven.generated.MobAnims.MerchantPrince.HIRE;
import static com.brasshaven.generated.MobAnims.MerchantPrince.ROAR;
import static com.brasshaven.generated.MobAnims.MerchantPrince.SANDSTORM;
import static com.brasshaven.generated.MobAnims.MerchantPrince.SLASH;
import static com.brasshaven.generated.MobAnims.MerchantPrince.STAGGER;

/**
 * Le Prince marchand de laiton (The Brass Merchant Prince), the champion of the Brass Caravanserai: a decadent prince
 * (3.6 blocks) in brass-plated silks and a jewelled turban, riding a clockwork palanquin that scuttles on four brass
 * legs. A scimitar in his right hand; a great brass mechanical arm on the palanquin's back throws his gold for him. He
 * holds court in the sunken auction pit under the great dome (35 wide, two tiers of bidders' steps round it).
 * <ul>
 *     <li>Phase 1: the <b>slash</b> (a scimitar sweep round his front, then a crescent of gold flies down a red line),
 *     the <b>coins</b> (the arm flings fans of gold coins down marked lanes: stand between them), the <b>bid</b> (a
 *     price is set on a player: a circle follows them, the price climbs, then a gold bar slams down on it), the
 *     <b>charge</b> (the palanquin scuttles down a marked lane).</li>
 *     <li>Phase 2 (a roar at 65%): faster, he <b>hires</b> bandit marksmen (never more than 3) and conjures a
 *     <b>sandstorm</b> vortex that drifts after the players and drags them slowly round and in; more coins.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the <b>Final Auction</b>. Sectors of the pit's
 *     floor are gold-plated, glitter and detonate, and he <b>dashes</b> between the dome's piers down marked lanes.</li>
 * </ul>
 * The only blocks he changes are the floor blocks of the plated sectors (gold blocks, for 1.5 s): each goes back after
 * the sector detonates, when the fight resets, the arena empties, he dies or is removed, and on the first tick after a
 * reload.
 */
public class MerchantPrince extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 3.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SLASH_RANGE = 5.5;
    private static final double SLASH_HALF = 70;
    private static final double CRESCENT_LEN = 13.0;
    private static final double CRESCENT_HALF = 1.2;
    private static final double LANE_LEN = 14.0;
    private static final double FAN_HALF = 40.0;
    private static final int FAN_LANES = 7;
    private static final double COIN_R = 0.7;
    private static final double BID_R = 2.5;
    private static final double BID_SPEED = 0.16;          // blocks a tick: slower than walking
    private static final double CHARGE_HALF = 1.3;
    private static final double VORTEX_R = 7.0;
    private static final double VORTEX_EYE = 2.0;
    private static final double VORTEX_SPEED = 0.06;
    private static final int VORTEX_LIFE = 140;
    private static final double PIER_R = 15.0;             // the foot of the bidders' steps under the dome's eight piers
    private static final int SECTOR_EVERY = 180;
    private static final int SECTOR_WARN = 20;             // edges drawn before the plating
    private static final int SECTOR_FUSE = 30;             // plated before it blows (red the last 10)
    private static final int DASH_EVERY = 260;
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.5F);
    private static final DustParticleOptions WHITE = new DustParticleOptions(0xF6F2E8, 1.5F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xD6A64C, 1.6F);
    private static final DustParticleOptions SAND = new DustParticleOptions(0xD8BE84, 1.8F);
    private static final DustParticleOptions SAND_D = new DustParticleOptions(0xB08A52, 1.6F);
    private static final DustParticleOptions AZURE = new DustParticleOptions(0x3A68C8, 1.4F);

    private record Temp(BlockState original, BlockState placed) {}

    private record SavedTemp(long pos, BlockState original, BlockState placed) {
        static final Codec<SavedTemp> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.LONG.fieldOf("pos").forGetter(SavedTemp::pos),
                BlockState.CODEC.fieldOf("original").forGetter(SavedTemp::original),
                BlockState.CODEC.fieldOf("placed").forGetter(SavedTemp::placed)).apply(i, SavedTemp::new));
    }

    private @Nullable Vec3 centre;
    private int radius = 15;
    private double floorTol = -1;
    /** Phase 3 has started (the Final Auction). */
    private boolean auction;
    private int guard;
    private int roarUntil = -1;
    private int sectorTimer = 60;
    private int dashTimer = 120;
    // the plated sectors of the auction: -1 idle, else their tick
    private int sectorTick = -1;
    private final List<Integer> sectors = new ArrayList<>();
    private double sectorStart;
    // moves in flight
    private final List<Vec3> lane = new ArrayList<>();
    private final Set<UUID> laneHit = new HashSet<>();
    private Vec3 fanDir = new Vec3(0, 0, 1);
    private final List<UUID> bidOwners = new ArrayList<>();
    private final List<Vec3> bidSpots = new ArrayList<>();
    private Vec3 vortexAt = Vec3.ZERO;
    private int dashLeg;
    private int lastPier = -1;
    private final Set<UUID> adds = new HashSet<>();
    // the plated floor with its original blocks
    private final Map<Long, Temp> temps = new HashMap<>();
    private final List<SavedTemp> staleTemps = new ArrayList<>();

    public MerchantPrince(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 660.0)
                .add(Attributes.ARMOR, 11.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.MerchantPrince.TICKS;
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
        return 4.0;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (the auction pit)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.floorTol = -1;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** The pit's usable radius: the flat floor inside the bidders' steps (17.5 in the caravanserai), kept to 17. */
    private double pitR() {
        return Math.min(Math.max(radius, 12) + 2.0, 17.0);
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

    /** Whether the floor round the seal is flat (the pit) or rough (a command spawn somewhere else). */
    private double floorTol(ServerLevel level) {
        if (floorTol > 0) {
            return floorTol;
        }
        Vec3 c = centre();
        int flat = 0;
        int samples = 0;
        for (int i = 0; i < 48; i++) {
            double a = i * 2.39996;
            double d = Math.sqrt((i + 0.5) / 48.0) * Math.max(3, pitR() - 1);
            double y = floorY(level, c.x + Math.cos(a) * d, c.y + 0.5, c.z + Math.sin(a) * d);
            if (!Double.isNaN(y)) {
                samples++;
                if (Math.abs(y - c.y) <= 0.6) {
                    flat++;
                }
            }
        }
        floorTol = samples > 0 && flat >= samples * 0.7 ? 0.6 : 1.6;
        return floorTol;
    }

    /**
     * A spot of open pit floor at (x, z): floor within the tolerance of the seal's level, two blocks of air over it,
     * within the pit's radius; or null (the bidders' steps, the aisles, the lectern and the podium).
     */
    private @Nullable Vec3 pad(ServerLevel level, double x, double z) {
        Vec3 c = centre();
        if (Math.hypot(x - c.x, z - c.z) > pitR() + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > floorTol(level) || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Open floor at (x, z), moved toward the centre until it lies within {@code maxR} of it; or null. */
    private @Nullable Vec3 inner(ServerLevel level, double x, double z, double maxR) {
        Vec3 c = centre();
        double d = Math.hypot(x - c.x, z - c.z);
        if (d > maxR && d > 1.0E-3) {
            x = c.x + (x - c.x) * maxR / d;
            z = c.z + (z - c.z) * maxR / d;
        }
        for (int i = 0; i < 6; i++) {
            Vec3 s = pad(level, x, z);
            if (s != null) {
                return s;
            }
            x = c.x + (x - c.x) * 0.8;
            z = c.z + (z - c.z) * 0.8;
        }
        return null;
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
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 14, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    private static boolean apart(List<Vec3> spots, Vec3 s, double min) {
        for (Vec3 o : spots) {
            if (flatDist(o, s) < min) {
                return false;
            }
        }
        return true;
    }

    /**
     * Pushes stay on the pit floor: a push is kept only when open floor lies 1.5 blocks along it (not into the steps,
     * the aisles or the podium); otherwise it is dropped.
     */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        Vec3 flat = new Vec3(push.x, 0, push.z);
        if (flat.lengthSqr() < 1.0E-6) {
            return Vec3.ZERO;
        }
        Vec3 probe = e.position().add(flat.normalize().scale(1.5));
        return pad(level, probe.x, probe.z) == null ? Vec3.ZERO : flat;
    }

    /** Pushes capped at 1.0 and lift at 0.45 (0.2 when the push was dropped at the pit's edge). */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.0, knockback));
        }
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 safe = safePush(level, e, push);
        boolean dropped = push.lengthSqr() > 1.0E-6 && safe.lengthSqr() < 1.0E-6;
        lift = Math.min(lift, dropped ? 0.2 : 0.45);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
    }

    /** The claw of the brass arm over his left shoulder. */
    private Vec3 claw() {
        return position().add(0, 3.4, 0).add(rotate(forward(), 90).scale(0.9));
    }

    private void coinBurst(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(GOLD, at.x, at.y, at.z, count, spread, spread * 0.6, spread, 0.0);
        level.sendParticles(ParticleTypes.WAX_ON, at.x, at.y, at.z, Math.max(1, count / 2), spread, spread * 0.6, spread, 0.05);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // slash: he draws the scimitar back across his body (0.7 s, an arc drawn gold, red from 0.45 s) and sweeps it
        // round his front: 12 and a push; he turns (up to 20°), a red line is drawn ahead and a crescent of gold flies
        // down it 0.3 s later at 0.9 blocks a tick: 8 and a small lift
        out.add(BossAttack.of("slash").anim(SLASH).timing(14, 12, 16).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        DustParticleOptions d = tick >= 9 ? RED : GOLD;
                        b.telegraphArc(level, SLASH_RANGE, SLASH_HALF, d);
                        b.telegraphArc(level, SLASH_RANGE - 2.0, SLASH_HALF, d);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> slashSweep(level))
                .active((b, level, t, tick) -> {
                    if (tick == 0) {
                        turnToward(t, 20.0F);
                    }
                    if (tick < 6 && tick % 2 == 0) {
                        drawLine(level, position(), forward(), CRESCENT_LEN, CRESCENT_HALF, RED);
                    }
                    if (tick == 6) {
                        addEffect(crescent(position(), forward()));
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) > 6.0 ? "charge" : "coins");
                    }
                })
                .build());
        // coins: the brass arm scoops gold from the palanquin's coffer and swings back (0.9 s) while seven lanes fan out
        // ahead of him (±40°, 14 long) drawn gold, red from 0.6 s; at 0.9 s the arm flings three fans of coins down them,
        // one every 0.25 s (in phase 2 a fourth, down the lanes between, drawn white): 5 to whoever a coin meets
        out.add(BossAttack.of("coins").anim(COINS).timing(18, 16, 14).range(3.0, 18.0).cooldown(90).weight(10)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    fanDir = forward();
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        DustParticleOptions d = tick >= 12 ? RED : GOLD;
                        for (Vec3 dir : fan(0)) {
                            drawRay(level, position(), dir, LANE_LEN, d);
                        }
                        if (b.phase() == 2) {
                            for (Vec3 dir : fan(1)) {
                                drawRay(level, position(), dir, LANE_LEN, tick >= 12 ? RED : WHITE);
                            }
                        }
                    }
                    Vec3 h = claw();
                    level.sendParticles(GOLD, h.x, h.y, h.z, 2, 0.2, 0.2, 0.2, 0);
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.0F, 1.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    int fans = b.phase() == 2 ? 4 : 3;
                    if (tick % 5 == 0 && tick / 5 < fans) {
                        int k = tick / 5;
                        int half = k == 3 ? 1 : 0;
                        for (Vec3 dir : fan(half)) {
                            addEffect(coinFlight(claw(), position(), dir));
                        }
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 1.5F, 1.4F + k * 0.1F);
                    }
                })
                .build());
        // bid: he raises a jewelled finger and the arm lifts a gold bar high (0.8 s); a price is set on a player (more
        // in co-op, at most 3): a gold circle (r 2.5) follows each at 0.16 blocks a tick (slower than walking) while a
        // column of coins climbs over it and the bell rings higher; after 1.4 s it stops and turns red, and 0.55 s later
        // the gold bar slams down on it: 14 and a lift
        out.add(BossAttack.of("bid").anim(BID).timing(16, 40, 14).range(3.0, 24.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    planBids(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (int i = 0; i < bidSpots.size(); i++) {
                            b.telegraphRing(level, bidSpots.get(i), BID_R, WHITE);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 1.5F, 0.8F);
                    }
                })
                .active((b, level, t, tick) -> bidTick(level, tick))
                .build());
        // charge: the palanquin crouches on its four legs, the scimitar levelled (0.8 s); a lane (half width 1.3) toward
        // you over open floor is drawn gold while he turns after you (until 0.5 s), then red; at 0.8 s the palanquin
        // scuttles down it in 0.3 s: 13 and a push to whoever he meets
        out.add(BossAttack.of("charge").anim(CHARGE).timing(16, 8, 16).range(6.0, 16.0).cooldown(80).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    laneHit.clear();
                    planLane(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 4.0F);
                        planLane(level, t);
                    }
                    if (tick % 2 == 0 && !lane.isEmpty()) {
                        drawLine(level, position(), forward(), flatDist(position(), lane.get(lane.size() - 1)), CHARGE_HALF,
                                tick >= 10 ? RED : GOLD);
                    }
                })
                .active((b, level, t, tick) -> runLane(level, tick, 13.0F))
                .end((b, level, t, tick) -> setDeltaMovement(Vec3.ZERO))
                .build());

        // ---------------------------------------------------------------- phase 2
        // hire: he tosses a fat purse of coins into the air (1.0 s): bandit marksmen leap down into the pit to earn it
        // (2, more in co-op), never more than 3 at once
        out.add(BossAttack.of("hire").anim(HIRE).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(600).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        coinBurst(level, claw().add(0, 0.6, 0), 3, 0.3);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.VILLAGER_TRADE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> spawnAdds(level, 2))
                .build());
        // sandstorm: he sweeps the scimitar round over his head and the sand of the caravan roads rises (1.2 s); a ring
        // (r 2) on the target's spot is drawn sand-gold, red from 0.8 s, with the vortex's reach (r 7) dotted round it;
        // then the vortex lives 7 s, drifting after the nearest player at 0.06 blocks a tick, dragging everyone within 7
        // slowly round and in (walk out of it); in its eye (r 2): 3 and Slowness I every second
        out.add(BossAttack.of("sandstorm").anim(SANDSTORM).phaseTwo().timing(24, 6, 16).range(0, 30.0).cooldown(460).weight(5)
                .track(false)
                .start((b, level, t, tick) -> {
                    Vec3 base = t != null ? t.position() : centre();
                    Vec3 s = inner(level, base.x, base.z, pitR() - 3.0);
                    vortexAt = s != null ? s : centre();
                    level.playSound(null, b, SoundEvents.ELYTRA_FLYING, SoundSource.HOSTILE, 1.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, vortexAt, VORTEX_EYE, tick >= 16 ? RED : SAND);
                    }
                    if (tick % 6 == 0) {
                        b.telegraphRing(level, vortexAt, VORTEX_R, SAND_D);
                    }
                    level.sendParticles(SAND, vortexAt.x, vortexAt.y + 0.3 + tick * 0.08, vortexAt.z, 3, 0.6, 0.2, 0.6, 0);
                })
                .impact((b, level, t, tick) -> {
                    addEffect(vortex(vortexAt));
                    level.playSound(null, vortexAt.x, vortexAt.y, vortexAt.z, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(),
                            SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // auction: he rises on the palanquin, arms wide, the arm ringing a gavel on the coffer (2.0 s, guarded; rings of
        // gold gather on him); then the gavel falls: a ring of gold runs out over the pit (10, jump it)
        out.add(BossAttack.of("auction").anim(AUCTION).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), Math.max(0.8, 12.0 - tick * 0.28), tick % 6 == 0 ? GOLD : AZURE);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 1.2F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> startAuction(level))
                .build());
        // dash: he picks a pier of the dome and a lane to its foot over open floor is drawn gold, red the last 0.3 s
        // (0.8 s); he dashes down it in 0.3 s (11 and a push), then the next lane is drawn (0.7 s) and he dashes again,
        // three dashes in all
        out.add(BossAttack.of("dash").anim(DASH).phaseTwo().timing(16, 46, 14).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    dashLeg = 0;
                    laneHit.clear();
                    planPierLane(level, t);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLane(level, tick >= 10 ? RED : GOLD);
                    }
                })
                .active((b, level, t, tick) -> {
                    int k = tick % 20;
                    if (tick >= 40 && k >= 6) {
                        return;
                    }
                    if (k < 6) {
                        runLane(level, k, 11.0F);
                    } else {
                        if (k == 6) {
                            setDeltaMovement(Vec3.ZERO);
                            laneHit.clear();
                            planPierLane(level, t);
                        }
                        if (k % 2 == 0) {
                            drawLane(level, k >= 14 ? RED : GOLD);
                        }
                    }
                })
                .end((b, level, t, tick) -> setDeltaMovement(Vec3.ZERO))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double len, double half, DustParticleOptions d) {
        Vec3 side = rotate(dir, 90).scale(half);
        for (double s = 1.0; s <= len; s += 1.0) {
            Vec3 p = from.add(dir.scale(s));
            level.sendParticles(d, p.x + side.x, p.y + 0.15, p.z + side.z, 1, 0, 0, 0, 0);
            level.sendParticles(d, p.x - side.x, p.y + 0.15, p.z - side.z, 1, 0, 0, 0, 0);
        }
    }

    private void drawRay(ServerLevel level, Vec3 from, Vec3 dir, double len, DustParticleOptions d) {
        for (double s = 1.5; s <= len; s += 1.0) {
            Vec3 p = from.add(dir.scale(s));
            level.sendParticles(d, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
        }
    }

    private void drawLane(ServerLevel level, DustParticleOptions d) {
        if (!lane.isEmpty()) {
            Vec3 end = lane.get(lane.size() - 1);
            Vec3 dir = end.subtract(position()).multiply(1, 0, 1);
            if (dir.lengthSqr() > 1.0E-4) {
                drawLine(level, position(), dir.normalize(), flatDist(position(), end), CHARGE_HALF, d);
                telegraphRing(level, end, 1.0, d);
            }
        }
    }

    private void slashSweep(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SLASH_HALF));
        for (LivingEntity e : victims(level, position(), SLASH_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SLASH_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)
                    && Math.abs(e.getY() - getY()) < 3.0) {
                strike(level, e, 12.0F, 0.6, 0.2);
            }
        }
        for (double a = -SLASH_HALF; a <= SLASH_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SLASH_RANGE - 0.8));
            level.sendParticles(GOLD, p.x, p.y + 1.3, p.z, 2, 0.1, 0.2, 0.1, 0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.8F);
    }

    /** A gilded crescent flying down a line from {@code from}: 0.9 blocks a tick, 8 and a small lift, once each. */
    private Effect crescent(Vec3 from, Vec3 dir) {
        double[] s = {1.0};
        Set<UUID> hit = new HashSet<>();
        Vec3 side = rotate(dir, 90);
        return (boss, level) -> {
            s[0] += 0.9;
            Vec3 p = from.add(dir.scale(s[0]));
            for (int k = -3; k <= 3; k++) {
                double f = k / 3.0;
                Vec3 q = p.add(side.scale(f * CRESCENT_HALF * 1.2)).subtract(dir.scale(f * f * 0.7));
                level.sendParticles(GOLD, q.x, q.y + 1.0, q.z, 1, 0.02, 0.05, 0.02, 0);
            }
            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 1.0, p.z, 1, 0.3, 0.2, 0.3, 0.0);
            for (LivingEntity e : boss.victims(level, p, CRESCENT_HALF + 1.5)) {
                Vec3 to = e.position().subtract(from).multiply(1, 0, 1);
                double along = to.dot(dir);
                double off = to.subtract(dir.scale(along)).length();
                if (Math.abs(along - s[0]) <= 0.9 && off <= CRESCENT_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - from.y) < 2.5
                        && hit.add(e.getUUID())) {
                    boss.strike(level, e, 8.0F, 0.0, 0.25);
                }
            }
            return s[0] >= CRESCENT_LEN;
        };
    }

    // ---- the coin fans

    /** The lanes of a fan round the facing at the move's start: {@code half} 1 is the set between them. */
    private List<Vec3> fan(int half) {
        List<Vec3> out = new ArrayList<>();
        Vec3 fwd = fanDir;
        double step = 2 * FAN_HALF / (FAN_LANES - 1);
        int n = half == 1 ? FAN_LANES - 1 : FAN_LANES;
        for (int i = 0; i < n; i++) {
            out.add(rotate(fwd, -FAN_HALF + step * (i + half * 0.5)));
        }
        return out;
    }

    /** A coin thrown from the claw down its lane at 0.8 blocks a tick (14 long): 5 to the first it meets. */
    private Effect coinFlight(Vec3 from, Vec3 base, Vec3 dir) {
        double[] s = {1.0};
        return (boss, level) -> {
            s[0] += 0.8;
            Vec3 p = base.add(dir.scale(s[0]));
            double drop = Math.max(0, 1.0 - s[0] / 4.0);
            Vec3 at = new Vec3(p.x, base.y + 1.0 + drop * (from.y - base.y - 1.0), p.z);
            level.sendParticles(GOLD, at.x, at.y, at.z, 2, 0.05, 0.05, 0.05, 0);
            for (LivingEntity e : boss.victims(level, at, 2.0)) {
                if (flatDist(e.position(), at) <= COIN_R + e.getBbWidth() / 2 && at.y >= e.getY() - 0.3
                        && at.y <= e.getY() + e.getBbHeight() + 0.3) {
                    boss.strike(level, e, 5.0F, 0.0, 0.0);
                    level.sendParticles(ParticleTypes.WAX_ON, at.x, at.y, at.z, 4, 0.2, 0.2, 0.2, 0.05);
                    return true;
                }
            }
            BlockPos bp = BlockPos.containing(at);
            if (!level.getBlockState(bp).getCollisionShape(level, bp).isEmpty()) {
                return true;
            }
            return s[0] >= LANE_LEN;
        };
    }

    // ---- the bid

    /** The target first, then the other players (at most 3 in all, {@code scaledCount(1)}). */
    private void planBids(ServerLevel level, @Nullable LivingEntity target) {
        bidOwners.clear();
        bidSpots.clear();
        int n = Math.min(3, scaledCount(1));
        List<LivingEntity> who = new ArrayList<>();
        if (target != null) {
            who.add(target);
        }
        for (Player p : fighters(level)) {
            if (p != target && who.size() < n) {
                who.add(p);
            }
        }
        for (LivingEntity e : who) {
            Vec3 s = inner(level, e.getX(), e.getZ(), pitR() - 1.0);
            bidOwners.add(e.getUUID());
            bidSpots.add(s != null ? s : centre());
        }
        if (bidSpots.isEmpty()) {
            bidOwners.add(getUUID());
            bidSpots.add(centre());
        }
    }

    /** 0-27 the circles follow their players, 28-38 they hold red, 39 the gold bars fall. */
    private void bidTick(ServerLevel level, int tick) {
        for (int i = 0; i < bidSpots.size(); i++) {
            Vec3 s = bidSpots.get(i);
            if (tick < 28) {
                var owner = level.getEntity(bidOwners.get(i));
                if (owner instanceof LivingEntity le && le.isAlive() && owner != this) {
                    Vec3 to = le.position().subtract(s).multiply(1, 0, 1);
                    double d = to.length();
                    if (d > 0.05) {
                        Vec3 next = s.add(to.normalize().scale(Math.min(d, BID_SPEED)));
                        Vec3 p = inner(level, next.x, next.z, pitR() - 1.0);
                        if (p != null) {
                            s = p;
                            bidSpots.set(i, p);
                        }
                    }
                }
            }
            if (tick % 2 == 0) {
                telegraphRing(level, s, BID_R, tick >= 28 ? RED : GOLD);
                double h = 0.6 + Math.min(28, tick) * 0.12;           // the price climbing
                for (double y = 0.4; y <= h; y += 0.35) {
                    level.sendParticles(GOLD, s.x, s.y + y, s.z, 1, 0.12, 0.02, 0.12, 0);
                }
            }
            if (tick >= 32 && tick < 39) {                           // the bar falling
                double y = 7.0 - (tick - 32) * 1.0;
                level.sendParticles(BRASS, s.x, s.y + y, s.z, 6, 0.5, 0.15, 0.25, 0);
            }
            if (tick == 39) {
                level.sendParticles(ParticleTypes.EXPLOSION, s.x, s.y + 0.4, s.z, 1, 0, 0, 0, 0);
                coinBurst(level, s.add(0, 0.6, 0), 16, 1.0);
                level.playSound(null, s.x, s.y, s.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.6F, 0.7F);
                for (LivingEntity e : victims(level, s, BID_R + 1)) {
                    if (flatDist(e.position(), s) <= BID_R + e.getBbWidth() / 2 && Math.abs(e.getY() - s.y) < 2.5) {
                        strike(level, e, 14.0F, 0.0, 0.35);
                    }
                }
            }
        }
        if (tick < 28 && tick % 4 == 0) {
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_PLING.value(), SoundSource.HOSTILE, 1.2F, 0.6F + tick * 0.04F);
        }
    }

    // ---- lanes (the charge and the dashes)

    /** Open floor along his facing (every 0.5) to the target + 2, at most 12, with headroom for him. */
    private void planLane(ServerLevel level, @Nullable LivingEntity target) {
        lane.clear();
        double len = target != null ? Math.min(12.0, distanceTo(target) + 2.0) : 8.0;
        Vec3 fwd = forward();
        for (double d = 0.5; d <= len; d += 0.5) {
            Vec3 p = position().add(fwd.scale(d));
            Vec3 s = pad(level, p.x, p.z);
            if (s == null || !clear(level, s.x, s.y, s.z, 4)) {
                break;
            }
            lane.add(s);
        }
    }

    /**
     * A lane to the foot of one of the dome's eight piers (r 15 round the pit's centre, at 22.5° + 45° k): not the one
     * he stands at, the one whose lane passes nearest the target; open floor with headroom, cut short where blocked.
     */
    private void planPierLane(ServerLevel level, @Nullable LivingEntity target) {
        lane.clear();
        Vec3 c = centre();
        double r = Math.min(PIER_R, pitR() - 1.5);
        int best = -1;
        double bestScore = Double.MAX_VALUE;
        for (int k = 0; k < 8; k++) {
            if (k == lastPier) {
                continue;
            }
            double a = Math.toRadians(22.5 + 45.0 * k);
            Vec3 p = new Vec3(c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r);
            double len = flatDist(position(), p);
            if (len < 6.0) {
                continue;
            }
            double score = len * 0.2;
            if (target != null) {
                Vec3 dir = p.subtract(position()).multiply(1, 0, 1).normalize();
                Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
                double along = Mth.clamp(to.dot(dir), 0, len);
                score += to.subtract(dir.scale(along)).length();
            }
            score += getRandom().nextDouble() * 2.0;
            if (score < bestScore) {
                bestScore = score;
                best = k;
            }
        }
        if (best < 0) {
            return;
        }
        lastPier = best;
        double a = Math.toRadians(22.5 + 45.0 * best);
        Vec3 end = new Vec3(c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r);
        faceToward(end);
        Vec3 dir = end.subtract(position()).multiply(1, 0, 1);
        double len = dir.length();
        dir = dir.normalize();
        for (double d = 0.5; d <= len; d += 0.5) {
            Vec3 p = position().add(dir.scale(d));
            Vec3 s = pad(level, p.x, p.z);
            if (s == null || !clear(level, s.x, s.y, s.z, 4)) {
                break;
            }
            lane.add(s);
        }
    }

    /** Ticks 0-5: he runs down the lane (`move`, collisions kept), hitting whoever is within 1.6 of him once. */
    private void runLane(ServerLevel level, int tick, float damage) {
        if (lane.isEmpty() || tick > 5) {
            return;
        }
        Vec3 end = lane.get(lane.size() - 1);
        Vec3 step = end.subtract(position()).multiply(1, 0, 1).scale(1.0 / (6 - tick));
        move(MoverType.SELF, step);
        setDeltaMovement(Vec3.ZERO);
        level.sendParticles(SAND, getX(), getY() + 0.3, getZ(), 6, 0.6, 0.2, 0.6, 0);
        level.sendParticles(GOLD, getX(), getY() + 1.5, getZ(), 3, 0.4, 0.6, 0.4, 0);
        for (LivingEntity e : victims(level, position(), 3.0)) {
            if (flatDist(e.position(), position()) <= 1.6 + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 2.5
                    && laneHit.add(e.getUUID())) {
                strike(level, e, damage, 0.7, 0.2);
            }
        }
        if (tick == 0) {
            level.playSound(null, this, SoundEvents.IRON_GOLEM_STEP, SoundSource.HOSTILE, 1.5F, 1.4F);
            level.playSound(null, this, SoundEvents.TRIDENT_RIPTIDE_1.value(), SoundSource.HOSTILE, 1.2F, 1.4F);
        }
    }

    // ---- the sandstorm

    /**
     * The vortex: lives 7 s, drifts after the nearest player at 0.06 blocks a tick over open floor; every 4 ticks it
     * drags whoever stands within 7 a little round and in (0.08 a push, walking beats it, never off the floor); every
     * second, 3 and Slowness I 1 s in its eye (r 2). It ends early if the fight resets.
     */
    private Effect vortex(Vec3 start) {
        int[] t = {0};
        Vec3[] at = {start};
        return (boss, level) -> {
            MerchantPrince mp = (MerchantPrince) boss;
            int k = t[0]++;
            if (k >= VORTEX_LIFE || boss.phase() != 2 || !boss.isAlive()) {
                return true;
            }
            Vec3 c = at[0];
            Player near = null;
            double best = 99;
            for (Player p : mp.fighters(level)) {
                double d = flatDist(p.position(), c);
                if (d < best) {
                    best = d;
                    near = p;
                }
            }
            if (near != null && best > 0.3) {
                Vec3 next = c.add(near.position().subtract(c).multiply(1, 0, 1).normalize().scale(VORTEX_SPEED));
                Vec3 s = mp.inner(level, next.x, next.z, mp.pitR() - 2.0);
                if (s != null) {
                    at[0] = s;
                    c = s;
                }
            }
            for (int i = 0; i < 3; i++) {                            // the funnel
                double a = (k * 0.35 + i * 2.094);
                double y = (k % 20) * 0.25 + i;
                double r = 0.8 + y * 0.45;
                level.sendParticles(SAND, c.x + Math.cos(a) * r, c.y + y, c.z + Math.sin(a) * r, 2, 0.15, 0.15, 0.15, 0);
                level.sendParticles(SAND_D, c.x + Math.cos(a + 1) * r * 0.8, c.y + y * 0.7, c.z + Math.sin(a + 1) * r * 0.8,
                        1, 0.1, 0.1, 0.1, 0);
            }
            if (k % 3 == 0) {
                double a = boss.getRandom().nextDouble() * Math.PI * 2;
                double r = 2.0 + boss.getRandom().nextDouble() * (VORTEX_R - 2.0);
                level.sendParticles(SAND, c.x + Math.cos(a) * r, c.y + 0.3, c.z + Math.sin(a) * r, 1, 0.1, 0.05, 0.1, 0);
            }
            if (k % 10 == 0) {
                boss.telegraphRing(level, c, VORTEX_EYE, SAND_D);
            }
            if (k % 4 == 0) {
                for (LivingEntity e : boss.victims(level, c, VORTEX_R + 1)) {
                    Vec3 to = c.subtract(e.position()).multiply(1, 0, 1);
                    double d = to.length();
                    if (d > VORTEX_R || d < 0.5 || Math.abs(e.getY() - c.y) > 3.0) {
                        continue;
                    }
                    Vec3 in = to.normalize();
                    Vec3 round = rotate(in, 90);
                    Vec3 push = mp.safePush(level, e, in.scale(0.04).add(round.scale(0.06)));
                    if (push.lengthSqr() > 1.0E-6) {
                        e.push(push.x, 0, push.z);
                        e.hurtMarked = true;
                    }
                }
            }
            if (k % 20 == 10) {
                for (LivingEntity e : boss.victims(level, c, VORTEX_EYE + 1)) {
                    if (flatDist(e.position(), c) <= VORTEX_EYE + e.getBbWidth() / 2 && Math.abs(e.getY() - c.y) < 3.0) {
                        boss.strike(level, e, 3.0F, 0.0, 0.0);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 0));
                    }
                }
            }
            if (k % 20 == 0) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.ELYTRA_FLYING, SoundSource.HOSTILE, 0.6F, 0.5F);
            }
            return false;
        };
    }

    // ---- the mercenaries (bandit marksmen hired for the fight)

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
            EntityType<? extends Mob> type = ModEntities.BANDIT_MARKSMAN.get();
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 at = null;
            for (int tries = 0; tries < 10 && at == null; tries++) {
                double a = random.nextDouble() * Math.PI * 2;
                double d = 5.0 + random.nextDouble() * 4.0;
                at = pad(level, getX() + Math.cos(a) * d, getZ() + Math.sin(a) * d);
            }
            if (at == null) {
                at = position();
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            coinBurst(level, at.add(0, 1.0, 0), 8, 0.4);
            level.sendParticles(ParticleTypes.POOF, at.x, at.y + 0.5, at.z, 10, 0.3, 0.3, 0.3, 0.02);
        }
        level.playSound(null, this, SoundEvents.VILLAGER_YES, SoundSource.HOSTILE, 1.5F, 0.7F);
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

    // ------------------------------------------------------------------ phase 3: the Final Auction

    private void startAuction(ServerLevel level) {
        auction = true;
        sectorTimer = 40;
        dashTimer = 120;
        sectorTick = -1;
        addEffect(floorRing(position(), pitR(), 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("merchant_prince_auction"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        coinBurst(level, position().add(0, 3.0, 0), 40, 2.5);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 3.0F, 1.0F);
    }

    /** A ring of gold running out over the floor from {@code c}: it hits once whoever stands on the floor (jump). */
    private Effect floorRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            r[0] += speed;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(i % 2 == 0 ? GOLD : AZURE, c.x + Math.cos(a) * rr, c.y + 0.2, c.z + Math.sin(a) * rr,
                        1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                double fy = floorY(level, e.getX(), e.getY(), e.getZ());
                double over = Double.isNaN(fy) ? 9.0 : e.getY() - fy;
                if (Math.abs(d - rr) <= 1.0 && over < 0.6 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.0, 0.3);
                }
            }
            return rr >= max;
        };
    }

    /** The sector (0-7, 45° each from {@link #sectorStart}) of a point, or -1 inside r 1 of the centre. */
    private int sectorOf(Vec3 p) {
        Vec3 c = centre();
        if (flatDist(p, c) < 1.0) {
            return -1;
        }
        double a = Math.toDegrees(Math.atan2(p.z - c.z, p.x - c.x)) - sectorStart;
        return Math.floorMod((int) Math.floor(a / 45.0), 8);
    }

    /** {@code min(4, scaledCount(2) + 1)} of the eight sectors, the target's first, never two side by side when it can help. */
    private void planSectors(@Nullable LivingEntity target) {
        sectors.clear();
        sectorStart = getRandom().nextInt(2) * 22.5;
        int n = Math.min(4, scaledCount(2) + 1);
        if (target != null) {
            int s = sectorOf(target.position());
            if (s >= 0) {
                sectors.add(s);
            }
        }
        List<Integer> order = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            order.add(i);
        }
        java.util.Collections.shuffle(order, new java.util.Random(getRandom().nextLong()));
        for (int pass = 0; pass < 2 && sectors.size() < n; pass++) {
            for (int s : order) {
                if (sectors.size() >= n || sectors.contains(s)) {
                    continue;
                }
                boolean side = sectors.contains((s + 1) % 8) || sectors.contains((s + 7) % 8);
                if (pass == 1 || !side) {
                    sectors.add(s);
                }
            }
        }
    }

    private void drawSectors(ServerLevel level, DustParticleOptions d) {
        Vec3 c = centre();
        double r = pitR();
        for (int s : sectors) {
            for (int edge = 0; edge < 2; edge++) {
                double a = Math.toRadians(sectorStart + (s + edge) * 45.0);
                for (double q = 1.0; q <= r; q += 1.0) {
                    level.sendParticles(d, c.x + Math.cos(a) * q, c.y + 0.15, c.z + Math.sin(a) * q, 1, 0, 0, 0, 0);
                }
            }
            for (double a = 0; a <= 45.0; a += 45.0 / Math.max(6, r * 0.8)) {
                double rad = Math.toRadians(sectorStart + s * 45.0 + a);
                level.sendParticles(d, c.x + Math.cos(rad) * r, c.y + 0.15, c.z + Math.sin(rad) * r, 1, 0, 0, 0, 0);
            }
        }
    }

    /** Gold blocks over the open floor of the chosen sectors (only plain full blocks with air over them). */
    private void plate(ServerLevel level) {
        Vec3 c = centre();
        int y = Mth.floor(c.y + 0.01) - 1;
        int r = (int) Math.ceil(pitR());
        BlockState gold = Blocks.GOLD_BLOCK.defaultBlockState();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                Vec3 p = new Vec3(Mth.floor(c.x) + dx + 0.5, c.y, Mth.floor(c.z) + dz + 0.5);
                double d = flatDist(p, c);
                if (d < 1.5 || d > pitR() || !sectors.contains(sectorOf(p))) {
                    continue;
                }
                BlockPos b = BlockPos.containing(p.x, y + 0.5, p.z);
                if (!level.isLoaded(b) || temps.containsKey(b.asLong())) {
                    continue;
                }
                BlockState st = level.getBlockState(b);
                if (st.isAir() || st.hasBlockEntity() || !st.isCollisionShapeFullBlock(level, b)
                        || !level.getBlockState(b.above()).getCollisionShape(level, b.above()).isEmpty()) {
                    continue;
                }
                temps.put(b.asLong(), new Temp(st, gold));
                level.setBlock(b, gold, 3);
            }
        }
    }

    /**
     * The plated sectors: edges drawn gold 20 ticks, then the floor is gold-plated and glitters 30 ticks (edges red the
     * last 10), then it detonates (9 and a lift to whoever stands in a plated sector) and the floor goes back.
     */
    private void tickSectors(ServerLevel level) {
        int k = sectorTick;
        Vec3 c = centre();
        if (k < SECTOR_WARN) {
            if (k % 2 == 0) {
                drawSectors(level, GOLD);
            }
            if (k == 0) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.HOSTILE, 2.0F, 1.2F);
            }
        } else if (k < SECTOR_WARN + SECTOR_FUSE) {
            if (k == SECTOR_WARN) {
                plate(level);
                level.playSound(null, c.x, c.y, c.z, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
            }
            if (k % 2 == 0) {
                drawSectors(level, k >= SECTOR_WARN + SECTOR_FUSE - 10 ? RED : GOLD);
            }
            for (int i = 0; i < 6; i++) {                             // the glitter
                double a = Math.toRadians(sectorStart + (sectors.get(getRandom().nextInt(sectors.size())) + getRandom().nextDouble()) * 45.0);
                double r = 1.5 + getRandom().nextDouble() * (pitR() - 1.5);
                level.sendParticles(ParticleTypes.WAX_ON, c.x + Math.cos(a) * r, c.y + 0.2, c.z + Math.sin(a) * r, 1, 0.1, 0.1, 0.1, 0.02);
            }
            if (k == SECTOR_WARN + SECTOR_FUSE - 10) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.TNT_PRIMED, SoundSource.HOSTILE, 2.0F, 1.2F);
            }
        } else {
            for (int s : sectors) {
                for (int i = 0; i < 4; i++) {
                    double a = Math.toRadians(sectorStart + (s + 0.2 + i * 0.2) * 45.0);
                    double r = 3.0 + i * 3.2;
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x + Math.cos(a) * r, c.y + 0.5, c.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
                }
            }
            for (Player p : fighters(level)) {
                if (sectors.contains(sectorOf(p.position())) && flatDist(p.position(), c) <= pitR() + 0.5
                        && Math.abs(p.getY() - c.y) < 2.5) {
                    strike(level, p, 9.0F, 0.0, 0.4);
                    coinBurst(level, p.position().add(0, 0.5, 0), 6, 0.5);
                }
            }
            for (LivingEntity e : victims(level, c, pitR() + 1)) {
                if (!(e instanceof Player) && sectors.contains(sectorOf(e.position())) && Math.abs(e.getY() - c.y) < 2.5) {
                    strike(level, e, 9.0F, 0.0, 0.4);
                }
            }
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 1.1F);
            endSectors(level);
            return;
        }
        sectorTick++;
    }

    private void endSectors(ServerLevel level) {
        sectorTick = -1;
        sectors.clear();
        sectorTimer = Math.max(110, (int) Math.round(SECTOR_EVERY * cooldownScale()));
        restoreAll(level);
    }

    private void clearTemp(ServerLevel level, long key) {
        Temp t = temps.remove(key);
        BlockPos p = BlockPos.of(key);
        if (t == null || !level.isLoaded(p)) {
            return;
        }
        BlockState now = level.getBlockState(p);
        if (now.getBlock() == t.placed().getBlock() || now.isAir()) {      // still gold, or mined out during the fight
            level.setBlock(p, t.original(), 3);
        }
    }

    /** Every changed block goes back (only where it is still the one set, or was mined out). */
    private void restoreAll(ServerLevel level) {
        for (SavedTemp s : staleTemps) {
            temps.putIfAbsent(s.pos(), new Temp(s.original(), s.placed()));
        }
        staleTemps.clear();
        for (Long key : new ArrayList<>(temps.keySet())) {
            clearTemp(level, key);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(GOLD, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.8F);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    private void cleanUp(ServerLevel level) {
        sectorTick = -1;
        sectors.clear();
        restoreAll(level);
        discardAdds(level);
    }

    /** Back to the first phase (the fight was reset): base speed, no auction. */
    private void resetForm(ServerLevel level) {
        auction = false;
        roarUntil = -1;
        guard = 0;
        sectorTimer = 60;
        dashTimer = 120;
        lastPier = -1;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("merchant_prince_auction"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("merchant_prince_wrath"));
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
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!temps.isEmpty() || sectorTick >= 0)) {
            sectorTick = -1;                               // the arena emptied (death, flight)
            sectors.clear();
            restoreAll(level);
        }
        if (phase() == 1 && auction) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !auction && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "auction");
            free = false;
        }
        // phase 3: the plated sectors detonate, he dashes between the piers
        if (auction && phase() == 2 && anyone) {
            cur = currentAttack();
            boolean busy = cur != null && "auction".equals(cur.name);
            if (sectorTick >= 0) {
                tickSectors(level);
            } else if (fighting && !busy && guard == 0 && --sectorTimer <= 0) {
                planSectors(target);
                sectorTick = sectors.isEmpty() ? -1 : 0;
                if (sectors.isEmpty()) {
                    sectorTimer = 40;
                }
            }
            if (dashTimer > 0) {
                dashTimer--;
            }
            if (free && guard == 0 && dashTimer <= 0 && currentAttack() == null) {
                dashTimer = Math.max(160, (int) Math.round(DASH_EVERY * cooldownScale()));
                chain(level, "dash");
            }
            if (tickCount % 5 == 0) {                       // gold dust drifting down under the dome
                Vec3 c = centre();
                double r = pitR() - 1.0;
                double x = c.x + (getRandom().nextDouble() * 2 - 1) * r;
                double z = c.z + (getRandom().nextDouble() * 2 - 1) * r;
                level.sendParticles(GOLD, x, c.y + 6 + getRandom().nextDouble() * 8, z, 1, 0.3, 0.3, 0.3, 0);
            }
        }
        // ambience: the palanquin's clockwork ticking, a glint off the turban's jewel
        if (tickCount % 10 == 0) {
            level.sendParticles(ParticleTypes.WAX_ON, getX(), getY() + 3.7, getZ(), 1, 0.2, 0.1, 0.2, 0.01);
        }
        if (tickCount % 40 == 0) {
            level.playSound(null, this, SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.HOSTILE, 0.6F, 1.8F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("merchant_prince_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        coinBurst(level, position().add(0, 3.0, 0), 20, 1.5);
        level.sendParticles(SAND, getX(), getY() + 1.0, getZ(), 30, 1.5, 0.5, 1.5, 0.0);
        level.playSound(null, this, SoundEvents.VILLAGER_NO, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        cleanUp(level);
        coinBurst(level, position().add(0, 2.5, 0), 40, 1.5);
        level.sendParticles(BRASS, getX(), getY() + 2.5, getZ(), 40, 1.0, 1.0, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.HOSTILE, 2.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (level() instanceof ServerLevel level && reason.shouldDestroy()) {
            restoreAll(level);
            discardAdds(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("PitCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("PitRadius", radius);
        output.putBoolean("PitAuction", auction);
        List<SavedTemp> saved = new ArrayList<>(staleTemps);
        for (Map.Entry<Long, Temp> e : temps.entrySet()) {
            saved.add(new SavedTemp(e.getKey(), e.getValue().original(), e.getValue().placed()));
        }
        output.store("MerchantPrinceGold", SavedTemp.CODEC.listOf(), saved);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("PitCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("PitRadius", 15);
        floorTol = -1;
        auction = input.getBooleanOr("PitAuction", false) && phase() == 2;
        staleTemps.clear();
        input.read("MerchantPrinceGold", SavedTemp.CODEC.listOf()).ifPresent(staleTemps::addAll);
        temps.clear();
        sectorTick = -1;
        sectors.clear();
    }
}
