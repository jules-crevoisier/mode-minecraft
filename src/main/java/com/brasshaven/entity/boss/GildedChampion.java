package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
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
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.hoglin.Hoglin;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.GildedChampion.BASH;
import static com.brasshaven.generated.MobAnims.GildedChampion.BLOCK;
import static com.brasshaven.generated.MobAnims.GildedChampion.CHARGE;
import static com.brasshaven.generated.MobAnims.GildedChampion.COMBO;
import static com.brasshaven.generated.MobAnims.GildedChampion.CROWD;
import static com.brasshaven.generated.MobAnims.GildedChampion.FAVOUR;
import static com.brasshaven.generated.MobAnims.GildedChampion.GATES;
import static com.brasshaven.generated.MobAnims.GildedChampion.NET;
import static com.brasshaven.generated.MobAnims.GildedChampion.RIPOSTE;
import static com.brasshaven.generated.MobAnims.GildedChampion.ROAR;
import static com.brasshaven.generated.MobAnims.GildedChampion.STAGGER;

/**
 * Le Champion doré (The Gilded Champion), the champion of the Crimson Colosseum: the undefeated piglin gladiator, a
 * massive brute (4 blocks) in ornate gilded plate, a crested gladiator's helmet, gold-capped tusks, a crimson cape, a
 * huge gold-and-netherite gladius and a round gilded shield with a hoglin skull for its boss. He fights on the sand
 * floor of the colosseum (an oval 44 x 34 ringed by the podium wall), over the four iron grates of the beast lifts.
 * <ul>
 *     <li>Phase 1: the gladius <b>combo</b> (two drawn cuts), the shield <b>bash</b>, the shield <b>block</b> (raised
 *     before him for 2 s: frontal blows glance off, flank and back blows hurt more; a blocked blow earns a drawn
 *     <b>riposte</b>), the <b>charge</b> down a drawn lane, the gold <b>net</b> on a marked ring (it slows), and
 *     <b>the crowd roars</b>: he taunts the stands and they hurl gold debris onto marked circles.</li>
 *     <li>Phase 2 (a roar at 65%): faster, the combo ends in a thrust, two nets, burning debris, he calls piglin brutes
 *     and hoglins through the beast <b>gates</b>.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>the emperor's favour</b> (a wave, jump it):
 *     gilded rage (his gold glows), the shield is cast aside for a second gladius (the bash and the block become combos,
 *     the combo ends in a crossed double cut), and lava jets erupt from the grates along marked lines (particles and
 *     fire, no lava is placed).</li>
 * </ul>
 * He places and breaks no block. Pushes are capped and dropped where they would carry a fighter off the open sand.
 */
public class GildedChampion extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 4.0F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double COMBO_R = 5.0;
    private static final double COMBO_HALF = 75;
    private static final double BASH_R = 4.0;
    private static final double BASH_HALF = 50;
    private static final double THRUST_LEN = 6.0;
    private static final double BLOCK_HALF = 70;
    private static final double CHARGE_MAX = 20.0;
    private static final double CHARGE_HALF = 1.2;
    private static final double NET_R = 2.6;
    private static final double DEBRIS_R = 2.0;
    private static final double JET_MAX = 16.0;
    private static final double JET_HALF = 1.0;
    private static final int JET_EVERY = 120;
    private static final EntityDataAccessor<Boolean> DATA_GILDED = SynchedEntityData.defineId(GildedChampion.class,
            EntityDataSerializers.BOOLEAN);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xFFD24A, 1.5F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions CRIMSON = new DustParticleOptions(0xB81C2C, 1.5F);
    private static final DustParticleOptions ORANGE = new DustParticleOptions(0xFF8A22, 1.5F);
    private static final DustParticleOptions SAND = new DustParticleOptions(0xE8D29A, 1.4F);

    /** A marked circle: where debris (or a burning fire charge) from the stands lands, and when. */
    private record Mark(Vec3 at, int delay, boolean fire) {}

    private @Nullable Vec3 centre;
    private int radius = 20;
    /** The four grates of the beast lifts in the sand (found at runtime; points round the centre otherwise). */
    private @Nullable List<Vec3> grates;
    private boolean staleCheck = true;
    private int guard;
    private int roarUntil = -1;
    private int jetTimer = 60;
    /** Ticks of the shield block left (only while the block move is active) and blows it turned aside. */
    private int blockTicks;
    private int blocked;
    // moves in flight
    private double laneLen = 6.0;
    private final List<Vec3> netAims = new ArrayList<>();
    private final List<Mark> marks = new ArrayList<>();
    private final Set<UUID> chargeHit = new HashSet<>();
    private final Set<UUID> adds = new HashSet<>();

    public GildedChampion(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 700.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_GILDED, false);
    }

    /** 0 plain, 1 gilded (phase 3: the glowing gold, the second gladius, no shield). */
    @Override
    public int modelVariant() {
        return gilded() ? 1 : 0;
    }

    private boolean gilded() {
        return entityData.get(DATA_GILDED);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.GildedChampion.TICKS;
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
        return 130.0F;
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

    // ------------------------------------------------------------------ arena memory (the sand floor)

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        this.grates = null;
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
     * A spot of open sand at (x, z): floor within 0.6 of the seal's level, two blocks of air over it and inside the
     * arena radius; or null. The podium wall, the stands and the gate passages are never open sand.
     */
    private @Nullable Vec3 sand(ServerLevel level, double x, double z) {
        Vec3 c = centre();
        if (Math.hypot(x - c.x, z - c.z) > radius + 0.5) {
            return null;
        }
        double y = floorY(level, x, c.y + 0.5, z);
        if (Double.isNaN(y) || Math.abs(y - c.y) > 0.6 || !clear(level, x, y, z, 2)) {
            return null;
        }
        return new Vec3(x, y, z);
    }

    /** Finds the iron grates of the beast lifts in the sand (clusters of iron trapdoors in the floor layer). */
    private List<Vec3> grates(ServerLevel level) {
        if (grates != null) {
            return grates;
        }
        Vec3 c = centre();
        int y = Mth.floor(c.y) - 1;
        List<double[]> clusters = new ArrayList<>();      // sx, sz, n
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                for (int dy = 0; dy <= 1; dy++) {
                    p.set(Mth.floor(c.x) + dx, y + dy, Mth.floor(c.z) + dz);
                    if (!level.isLoaded(p)) {
                        continue;
                    }
                    Identifier id = BuiltInRegistries.BLOCK.getKey(level.getBlockState(p).getBlock());
                    if (!"iron_trapdoor".equals(id.getPath())) {
                        continue;
                    }
                    double px = p.getX() + 0.5;
                    double pz = p.getZ() + 0.5;
                    double[] into = null;
                    for (double[] k : clusters) {
                        if (Math.hypot(k[0] / k[2] - px, k[1] / k[2] - pz) < 3.0) {
                            into = k;
                            break;
                        }
                    }
                    if (into == null) {
                        clusters.add(new double[] {px, pz, 1});
                    } else {
                        into[0] += px;
                        into[1] += pz;
                        into[2]++;
                    }
                }
            }
        }
        List<Vec3> out = new ArrayList<>();
        for (double[] k : clusters) {
            if (k[2] >= 4 && out.size() < 6) {
                out.add(new Vec3(k[0] / k[2], c.y, k[1] / k[2]));
            }
        }
        if (out.size() < 2) {                               // a command spawn: four points round the centre
            out.clear();
            for (double[] o : new double[][] {{9, 0}, {-9, 0}, {0, 7}, {0, -7}}) {
                Vec3 s = sand(level, c.x + o[0], c.z + o[1]);
                out.add(s != null ? s : new Vec3(c.x + o[0], c.y, c.z + o[1]));
            }
        }
        grates = out;
        return out;
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

    private List<Player> fighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, new AABB(BlockPos.containing(centre())).inflate(radius + 6, 14, radius + 6),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    /** Height of {@code e}'s feet over the floor under it (0 standing, more when jumping). */
    private static double overFloor(ServerLevel level, LivingEntity e) {
        double fy = floorY(level, e.getX(), e.getY(), e.getZ());
        return Double.isNaN(fy) ? 9.0 : e.getY() - fy;
    }

    /** The push is dropped where it would carry {@code e} off the open sand (into the podium wall, a gate). */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 dir = push.multiply(1, 0, 1).normalize();
        for (double d : new double[] {1.5, 3.0}) {
            Vec3 probe = e.position().add(dir.scale(d));
            if (sand(level, probe.x, probe.z) == null) {
                return Vec3.ZERO;
            }
        }
        return new Vec3(push.x, 0, push.z);
    }

    /** Pushes capped at 1.0, lift at 0.45 (0.2 when the push was dropped); none off the sand. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.0, knockback));
        }
        shove(level, e, damage, push, lift);
    }

    private boolean shove(ServerLevel level, LivingEntity e, float damage, Vec3 push, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return false;
        }
        Vec3 safe = safePush(level, e, push);
        lift = Math.min(lift, safe.lengthSqr() < push.lengthSqr() - 1.0E-6 ? 0.2 : 0.45);
        if (safe.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(safe.x, lift, safe.z);
            e.hurtMarked = true;
        }
        return true;
    }

    private static BlockParticleOption block(net.minecraft.world.level.block.state.BlockState s) {
        return new BlockParticleOption(ParticleTypes.BLOCK, s);
    }

    private void sandBurst(ServerLevel level, Vec3 at, int count, double spread) {
        level.sendParticles(block(Blocks.SAND.defaultBlockState()), at.x, at.y + 0.3, at.z, count, spread, 0.3, spread, 0.12);
        level.sendParticles(SAND, at.x, at.y + 0.4, at.z, count / 2, spread, 0.3, spread, 0.0);
    }

    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    /** Everyone in the arc in front of him (reach r, ±half degrees), within 3.5 vertically. */
    private List<LivingEntity> inArc(ServerLevel level, double r, double half) {
        List<LivingEntity> out = new ArrayList<>();
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(half));
        for (LivingEntity e : victims(level, position(), r + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= r + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos) && Math.abs(e.getY() - getY()) < 3.5) {
                out.add(e);
            }
        }
        return out;
    }

    private void slashFx(ServerLevel level, double r, double half, boolean rightToLeft) {
        Vec3 fwd = forward();
        for (double a = -half; a <= half; a += 15) {
            Vec3 p = position().add(rotate(fwd, rightToLeft ? a : -a).scale(r - 1.2));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.6, p.z, 2, 0.15, 0.15, 0.15, 0.15);
            level.sendParticles(GOLD, p.x, p.y + 1.6, p.z, 1, 0.1, 0.1, 0.1, 0);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.6, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** How far a lane along his facing runs over open sand (stopping at the podium wall or a gate). */
    private double laneLength(ServerLevel level, double max) {
        double len = 2.0;
        for (double d = 1.0; d <= max; d += 1.0) {
            Vec3 p = ahead(d);
            if (sand(level, p.x, p.z) == null) {
                break;
            }
            len = d;
        }
        return Math.max(2.0, len);
    }

    private void drawLine(ServerLevel level, Vec3 from, Vec3 dir, double start, double len, double half, DustParticleOptions dust) {
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        for (double d = start; d <= len; d += 1.0) {
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

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // combo: the gladius drawn back over his right shoulder (0.8 s, the arc drawn gold), a forehand cut (12), he
        // turns a little and the arc goes red, the backhand return 0.4 s later (11); phase 2: a thrust down a line drawn
        // red (13) 0.4 s after that; gilded: a crossed cut of both blades instead (13)
        out.add(BossAttack.of("combo").anim(COMBO).timing(16, 18, 14).range(0, 6.5).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, COMBO_R, COMBO_HALF, GOLD);
                        b.telegraphArc(level, COMBO_R - 2.5, COMBO_HALF, GOLD);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : inArc(level, COMBO_R, COMBO_HALF)) {
                        strike(level, e, 12.0F, 0.4, 0.1);
                    }
                    slashFx(level, COMBO_R, COMBO_HALF, true);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 1) {
                        turnToward(t, 20.0F);
                    }
                    if (tick >= 1 && tick < 8 && tick % 2 == 1) {
                        b.telegraphArc(level, COMBO_R, COMBO_HALF, RED);
                    }
                    if (tick == 8) {
                        for (LivingEntity e : inArc(level, COMBO_R, COMBO_HALF)) {
                            e.invulnerableTime = 0;
                            strike(level, e, 11.0F, 0.4, 0.1);
                        }
                        slashFx(level, COMBO_R, COMBO_HALF, false);
                    }
                    if (phase() != 2) {
                        return;
                    }
                    if (gilded()) {
                        if (tick >= 9 && tick < 16 && tick % 2 == 1) {
                            b.telegraphArc(level, COMBO_R + 0.5, 80, RED);
                        }
                        if (tick == 16) {
                            for (LivingEntity e : inArc(level, COMBO_R + 0.5, 80)) {
                                e.invulnerableTime = 0;
                                strike(level, e, 13.0F, 0.6, 0.15);
                            }
                            slashFx(level, COMBO_R + 0.5, 80, true);
                            slashFx(level, COMBO_R + 0.5, 80, false);
                        }
                    } else {
                        if (tick >= 9 && tick < 16 && tick % 2 == 1) {
                            drawLine(level, position(), forward(), 1.0, THRUST_LEN, 1.0, RED);
                        }
                        if (tick == 16) {
                            thrust(level, THRUST_LEN, 1.0, 13.0F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (phase() == 2 && t != null && !gilded() && b.getRandom().nextFloat() < 0.25F && b.distanceTo(t) < 5.0) {
                        b.chain(level, "bash");
                    }
                })
                .build());
        // bash: the shield drawn back to his left (0.7 s; a short arc drawn gold, red the last 0.3 s), slammed forward:
        // 9, a push and Slowness II 1 s
        out.add(BossAttack.of("bash").anim(BASH).timing(14, 8, 16).range(0, 4.5).cooldown(70).weight(9)
                .start((b, level, t, tick) -> {
                    if (gilded()) {
                        b.chain(level, "combo");
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphArc(level, BASH_R, BASH_HALF, tick >= 8 ? RED : GOLD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : inArc(level, BASH_R, BASH_HALF)) {
                        strike(level, e, 9.0F, 0.9, 0.2);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 20, 1));
                    }
                    Vec3 p = ahead(2.0);
                    level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.5, p.z, 16, 0.5, 0.5, 0.5, 0.3);
                    level.playSound(null, b, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.8F, 0.8F);
                })
                .build());
        // block: the shield raised before his face (0.6 s; a wall of gold motes in front of him), held 2 s while he turns
        // slowly toward you: blows from the front glance off, blows from the flank or back hurt 30% more. A blocked
        // blow earns a riposte when he lowers it
        out.add(BossAttack.of("block").anim(BLOCK).timing(12, 40, 12).range(0, 10.0).cooldown(220).weight(6)
                .start((b, level, t, tick) -> {
                    if (gilded()) {
                        b.chain(level, "combo");
                        return;
                    }
                    blocked = 0;
                    level.playSound(null, b, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 2.0F, 0.8F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        shieldWall(level, tick >= 6 ? GOLD : SAND);
                    }
                })
                .impact((b, level, t, tick) -> {
                    blockTicks = 40;
                    level.playSound(null, b, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 1.5F, 1.2F);
                })
                .active((b, level, t, tick) -> {
                    blockTicks = Math.max(0, 39 - tick);
                    turnToward(t, 2.5F);
                    if (tick % 3 == 0) {
                        shieldWall(level, GOLD);
                    }
                })
                .end((b, level, t, tick) -> {
                    blockTicks = 0;
                    if (blocked > 0) {
                        blocked = 0;
                        b.chain(level, "riposte");
                    }
                })
                .build());
        // riposte (after a blocked blow only): out from behind the shield, a line drawn red for 0.5 s, the gladius
        // driven straight down it: 13
        out.add(BossAttack.of("riposte").anim(RIPOSTE).timing(10, 6, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), 1.0, THRUST_LEN, 1.1, RED);
                    }
                })
                .impact((b, level, t, tick) -> {
                    move(MoverType.SELF, forward().scale(1.2));
                    thrust(level, THRUST_LEN, 1.1, 13.0F);
                })
                .build());
        // charge: he lowers his helmet behind the shield and paws the sand (1.2 s; a lane 2.4 wide drawn across the sand
        // follows you slowly, red from 0.8 s), then tackles down it: 14, a lift and a shove out of the lane (once)
        out.add(BossAttack.of("charge").anim(CHARGE).timing(24, 16, 14).range(6.0, 24.0).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                    laneLen = laneLength(level, CHARGE_MAX);
                    chargeHit.clear();
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 16) {
                        turnToward(t, 3.0F);
                        laneLen = laneLength(level, CHARGE_MAX);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, position(), forward(), 1.0, laneLen, CHARGE_HALF, tick < 16 ? GOLD : RED);
                    }
                    if (tick % 6 == 0) {
                        sandBurst(level, position(), 8, 0.6);
                        level.playSound(null, b, SoundEvents.HOGLIN_ANGRY, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    double speed = Mth.clamp(laneLen / 12.0, 0.6, 1.6);
                    double done = speed * tick;
                    if (done < laneLen - 1.0) {
                        Vec3 before = position();
                        move(MoverType.SELF, forward().scale(speed));
                        setDeltaMovement(0, getDeltaMovement().y, 0);
                        sandBurst(level, position(), 6, 0.5);
                        chargeHits(level, before);
                    }
                })
                .build());
        // net: a weighted gold net whirled overhead (1.0 s; a ring r 2.6 under you follows until 0.6 s, then locks red),
        // flung: where it lands (0.3 s later) 4 and Slowness III 3 s, and the net lies there 3 s (Slowness II inside).
        // Phase 2: two nets
        out.add(BossAttack.of("net").anim(NET).timing(20, 10, 16).range(4.0, 20.0).cooldown(180).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    planNets(level, t);
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 12 && t != null && !netAims.isEmpty()) {
                        Vec3 s = sand(level, t.getX(), t.getZ());
                        if (s != null) {
                            netAims.set(0, s);
                            faceToward(s);
                        }
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 a : netAims) {
                            b.telegraphRing(level, a, NET_R, tick < 12 ? GOLD : RED);
                        }
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.5F, 0.6F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Vec3 a : netAims) {
                        b.addEffect(goldNet(position().add(0, 3.0, 0), a));
                    }
                    level.playSound(null, b, SoundEvents.FISHING_BOBBER_THROW, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // the crowd roars: he taunts the stands (1.1 s; circles r 2 marked yellow under every player and round the
        // target); the crowd hurls gold debris from the stands onto them one after another: 8 and a lift. Phase 2: some
        // are burning fire charges (7, fire 3 s)
        out.add(BossAttack.of("crowd").anim(CROWD).timing(22, 30, 16).range(0, 30.0).cooldown(260).weight(6)
                .track(false)
                .start((b, level, t, tick) -> {
                    planMarks(level, t);
                    crowdCheer(level, 1.0F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (Mark m : marks) {
                            b.telegraphRing(level, m.at(), DEBRIS_R, m.fire() ? ORANGE : GOLD);
                        }
                    }
                    if (tick == 12) {
                        crowdCheer(level, 1.3F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Mark m : marks) {
                        b.addEffect(debris(m));
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // gates: the gladius beaten on the shield three times (1.0 s; the grates of the beast lifts marked gold), then
        // pointed at them: piglin brutes and hoglins come up through the grates (2, more in co-op), at most 3 at once
        out.add(BossAttack.of("gates").anim(GATES).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(700).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick == 4 || tick == 10 || tick == 16) {
                        level.playSound(null, b, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                    if (tick % 3 == 0) {
                        for (Vec3 g : grates(level)) {
                            b.telegraphRing(level, g, 1.5, GOLD);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.IRON_DOOR_OPEN, SoundSource.HOSTILE, 2.0F, 0.5F);
                    crowdCheer(level, 0.9F);
                    spawnAdds(level, 2, t);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // the emperor's favour: he kneels to the royal box, gladius raised (2.0 s, guarded; gold rings gather round him,
        // the crowd roars), rises and slams it into the sand: a wave to 14 (10, jump it); gilded rage
        out.add(BossAttack.of("favour").anim(FAVOUR).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    crowdCheer(level, 0.8F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 14.0 - tick * 0.3, GOLD);
                    }
                    level.sendParticles(ParticleTypes.WAX_ON, getX(), getY() + 2.5, getZ(), 3, 0.8, 1.2, 0.8, 0.05);
                    if (tick % 10 == 0) {
                        crowdCheer(level, 1.0F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> favour(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** A thrust down the line ahead (half width {@code half}, length {@code len}): damage and a push along it. */
    private void thrust(ServerLevel level, double len, double half, float damage) {
        Vec3 fwd = forward();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        for (LivingEntity e : victims(level, position(), len + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            if (along >= -0.5 && along <= len + e.getBbWidth() / 2 && Math.abs(to.dot(side)) <= half + e.getBbWidth() / 2
                    && Math.abs(e.getY() - getY()) < 3.0) {
                e.invulnerableTime = 0;
                shove(level, e, damage, fwd.scale(0.6), 0.1);
            }
        }
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = ahead(d);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.6, p.z, 2, 0.1, 0.1, 0.1, 0.1);
        }
        level.playSound(null, this, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    /** The shield raised: a short wall of motes in front of him (±70°), showing which side it covers. */
    private void shieldWall(ServerLevel level, DustParticleOptions d) {
        Vec3 fwd = forward();
        for (double a = -BLOCK_HALF; a <= BLOCK_HALF; a += 14) {
            Vec3 p = position().add(rotate(fwd, a).scale(1.6));
            level.sendParticles(d, p.x, p.y + 1.0, p.z, 1, 0, 0.6, 0, 0);
            level.sendParticles(d, p.x, p.y + 2.4, p.z, 1, 0, 0.4, 0, 0);
        }
    }

    /** The tackle: everyone he runs through (once each): 14, a lift and a shove out of the lane. */
    private void chargeHits(ServerLevel level, Vec3 before) {
        Vec3 fwd = forward();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        for (LivingEntity e : victims(level, position(), CHARGE_HALF + 3)) {
            Vec3 to = e.position().subtract(before).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double off = to.dot(side);
            double moved = flatDist(before, position());
            if (along >= -0.5 && along <= moved + 1.6 && Math.abs(off) <= CHARGE_HALF + e.getBbWidth() / 2
                    && Math.abs(e.getY() - getY()) < 3.0 && chargeHit.add(e.getUUID())) {
                if (shove(level, e, 14.0F, side.scale(off >= 0 ? 0.8 : -0.8), 0.35)) {
                    level.playSound(null, this, SoundEvents.PLAYER_ATTACK_KNOCKBACK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.sendParticles(ParticleTypes.CRIT, e.getX(), e.getY() + 1, e.getZ(), 12, 0.4, 0.4, 0.4, 0.2);
                }
            }
        }
    }

    // ---- the gold net

    private void planNets(ServerLevel level, @Nullable LivingEntity t) {
        netAims.clear();
        Vec3 first = t != null ? sand(level, t.getX(), t.getZ()) : null;
        netAims.add(first != null ? first : ahead(6.0));
        if (phase() != 2) {
            return;
        }
        for (Player p : fighters(level)) {
            if (p != t) {
                Vec3 s = sand(level, p.getX(), p.getZ());
                if (s != null && flatDist(s, netAims.get(0)) > NET_R * 2) {
                    netAims.add(s);
                    return;
                }
            }
        }
        Vec3 base = netAims.get(0);
        for (int tries = 0; tries < 20; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            Vec3 s = sand(level, base.x + Math.cos(a) * 6.0, base.z + Math.sin(a) * 6.0);
            if (s != null) {
                netAims.add(s);
                return;
            }
        }
    }

    /** The net flies 6 ticks in an arc of gold, lands: 4 and Slowness III 3 s; then lies there 60 ticks. */
    private Effect goldNet(Vec3 from, Vec3 at) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < 6) {
                double s = (k + 1) / 6.0;
                Vec3 p = from.lerp(at, s).add(0, Math.sin(Math.PI * s) * 3.0, 0);
                level.sendParticles(GOLD, p.x, p.y, p.z, 6, 0.6, 0.3, 0.6, 0);
                boss.telegraphRing(level, at, NET_R, RED);
                return false;
            }
            if (k == 6) {
                level.playSound(null, at.x, at.y, at.z, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                if (boss instanceof GildedChampion g) {
                    for (LivingEntity e : boss.victims(level, at, NET_R + 1)) {
                        if (flatDist(e.position(), at) <= NET_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                            g.strike(level, e, 4.0F, 0.0, 0.0);
                            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
                        }
                    }
                }
            }
            // the net lying on the sand: a gold grid, Slowness II to whoever stands in it
            if (k % 3 == 0) {
                for (double dx = -NET_R; dx <= NET_R; dx += 0.9) {
                    for (double dz = -NET_R; dz <= NET_R; dz += 0.9) {
                        if (dx * dx + dz * dz <= NET_R * NET_R && (Math.round(dx / 0.9) + Math.round(dz / 0.9)) % 2 == 0) {
                            level.sendParticles(GOLD, at.x + dx, at.y + 0.1, at.z + dz, 1, 0, 0, 0, 0);
                        }
                    }
                }
            }
            if (k % 10 == 0) {
                for (LivingEntity e : boss.victims(level, at, NET_R + 1)) {
                    if (flatDist(e.position(), at) <= NET_R && Math.abs(e.getY() - at.y) < 2.0) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 12, 1));
                    }
                }
            }
            return k >= 66;
        };
    }

    // ---- the crowd

    private void crowdCheer(ServerLevel level, float pitch) {
        Vec3 c = centre();
        for (int i = 0; i < 4; i++) {
            double a = Math.PI / 2 * i + tickCount * 0.1;
            level.playSound(null, c.x + Math.cos(a) * (radius + 6), c.y + 9, c.z + Math.sin(a) * (radius + 6),
                    SoundEvents.PIGLIN_CELEBRATE, SoundSource.HOSTILE, 3.0F, pitch);
        }
    }

    /** Debris circles: one under each player (up to 4), plus 2 (phase 2: 3, more in co-op) round the target. */
    private void planMarks(ServerLevel level, @Nullable LivingEntity target) {
        marks.clear();
        int players = 0;
        List<Vec3> spots = new ArrayList<>();
        for (Player p : fighters(level)) {
            if (players >= 4) {
                break;
            }
            Vec3 s = sand(level, p.getX(), p.getZ());
            if (s != null && spaced(spots, s, 3.5)) {
                spots.add(s);
                players++;
            }
        }
        int extra = scaledCount(phase() == 2 ? 3 : 2) + (gilded() ? 1 : 0);
        Vec3 base = target != null ? target.position() : ahead(6.0);
        int added = 0;
        for (int tries = 0; tries < 40 && added < extra; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 3.5 + getRandom().nextDouble() * 6.0;
            Vec3 s = sand(level, base.x + Math.cos(a) * d, base.z + Math.sin(a) * d);
            if (s != null && spaced(spots, s, 3.5) && flatDist(s, position()) > 2.5) {
                spots.add(s);
                added++;
            }
        }
        for (int i = 0; i < spots.size(); i++) {
            marks.add(new Mark(spots.get(i), 8 + i * 4, phase() == 2 && i % 2 == 1));
        }
    }

    private static boolean spaced(List<Vec3> spots, Vec3 s, double min) {
        for (Vec3 o : spots) {
            if (flatDist(o, s) < min) {
                return false;
            }
        }
        return true;
    }

    /**
     * Debris from the stands: the circle stays red while it flies in a high arc from the stands behind it; on landing
     * 8 and a lift (fire charges: 7 and fire 3 s).
     */
    private Effect debris(Mark m) {
        int[] t = {0};
        Vec3 c = centre();
        Vec3 out = m.at().subtract(c).multiply(1, 0, 1);
        Vec3 dir = out.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, 1) : out.normalize();
        Vec3 from = c.add(dir.scale(radius + 4)).add(0, 10, 0);
        return (boss, level) -> {
            int k = t[0]++;
            if (k < m.delay()) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, m.at(), DEBRIS_R, RED);
                }
                double s = (k + 1) / (double) m.delay();
                Vec3 p = from.lerp(m.at(), s).add(0, Math.sin(Math.PI * s) * 5.0, 0);
                if (m.fire()) {
                    level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 4, 0.2, 0.2, 0.2, 0.01);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0.01);
                } else {
                    level.sendParticles(block(Blocks.GOLD_BLOCK.defaultBlockState()), p.x, p.y, p.z, 4, 0.2, 0.2, 0.2, 0.05);
                    level.sendParticles(GOLD, p.x, p.y, p.z, 2, 0.2, 0.2, 0.2, 0);
                }
                if (k == 0) {
                    level.playSound(null, from.x, from.y, from.z, m.fire() ? SoundEvents.BLAZE_SHOOT : SoundEvents.PIGLIN_ADMIRING_ITEM,
                            SoundSource.HOSTILE, 2.0F, 0.7F);
                }
                return false;
            }
            Vec3 a = m.at();
            if (m.fire()) {
                level.sendParticles(ParticleTypes.FLAME, a.x, a.y + 0.3, a.z, 30, 1.0, 0.3, 1.0, 0.05);
                level.sendParticles(ParticleTypes.LAVA, a.x, a.y + 0.3, a.z, 6, 0.8, 0.2, 0.8, 0);
                level.playSound(null, a.x, a.y, a.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.0F, 0.8F);
            } else {
                level.sendParticles(block(Blocks.GOLD_BLOCK.defaultBlockState()), a.x, a.y + 0.3, a.z, 30, 0.8, 0.3, 0.8, 0.15);
                level.playSound(null, a.x, a.y, a.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 1.2F);
            }
            if (boss instanceof GildedChampion g) {
                for (LivingEntity e : boss.victims(level, a, DEBRIS_R + 1)) {
                    if (flatDist(e.position(), a) <= DEBRIS_R + e.getBbWidth() / 2 && Math.abs(e.getY() - a.y) < 2.5) {
                        if (m.fire()) {
                            if (g.shove(level, e, 7.0F, Vec3.ZERO, 0.2)) {
                                e.igniteForSeconds(3.0F);
                            }
                        } else {
                            g.shove(level, e, 8.0F, Vec3.ZERO, 0.3);
                        }
                    }
                }
            }
            return true;
        };
    }

    // ---- the beasts through the gates

    private int liveAdds(ServerLevel level) {
        adds.removeIf(id -> {
            var e = level.getEntity(id);
            return e == null || !e.isAlive();
        });
        return adds.size();
    }

    private void spawnAdds(ServerLevel level, int base, @Nullable LivingEntity target) {
        int n = Math.min(3 - liveAdds(level), scaledCount(base));
        List<Vec3> gs = new ArrayList<>(grates(level));
        if (target != null) {                            // the gates farthest from the target first
            gs.sort((a, b) -> Double.compare(flatDist(b, target.position()), flatDist(a, target.position())));
        }
        for (int i = 0; i < n; i++) {
            EntityType<? extends Mob> type = i % 2 == 0 ? EntityTypes.PIGLIN_BRUTE : EntityTypes.HOGLIN;
            Mob mob = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mob == null) {
                continue;
            }
            Vec3 g = gs.isEmpty() ? position() : gs.get(i % gs.size());
            Vec3 at = sand(level, g.x, g.z);
            if (at == null) {
                at = g;
            }
            if (mob instanceof AbstractPiglin pig) {
                pig.setImmuneToZombification(true);
            }
            if (mob instanceof Hoglin hog) {
                hog.setImmuneToZombification(true);
            }
            mob.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
            mob.addTag(MINION_TAG);
            mob.setTarget(getTarget());
            level.addFreshEntity(mob);
            adds.add(mob.getUUID());
            level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 0.5, at.z, 16, 0.5, 0.3, 0.5, 0.03);
            level.sendParticles(block(Blocks.SAND.defaultBlockState()), at.x, at.y + 0.3, at.z, 20, 0.8, 0.2, 0.8, 0.1);
            level.playSound(null, at.x, at.y, at.z, i % 2 == 0 ? SoundEvents.PIGLIN_BRUTE_ANGRY : SoundEvents.HOGLIN_ANGRY,
                    SoundSource.HOSTILE, 2.0F, 0.9F);
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

    // ------------------------------------------------------------------ phase 3: the emperor's favour

    private void favour(ServerLevel level) {
        entityData.set(DATA_GILDED, true);
        jetTimer = 60;
        addEffect(sandRing(position(), 14.0, 0.55, 10.0F));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("gilded_champion_favour"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.WAX_ON, getX(), getY() + 2, getZ(), 60, 1.0, 1.5, 1.0, 0.3);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.5, getZ(), 1, 0, 0, 0, 0);
        sandBurst(level, position(), 50, 2.0);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.playSound(null, this, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
        crowdCheer(level, 1.4F);
    }

    /** A jumpable ring from {@code c}: it hits once whoever stands on the floor at its edge. */
    private Effect sandRing(Vec3 c, double max, double speed, float damage) {
        double[] r = {0.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof GildedChampion g)) {
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

    /**
     * A lava jet line from a grate toward {@code toward}: a ring on the grate and the line drawn orange for 30 ticks
     * (red the last 10); then fire erupts along it from the grate out, 2 blocks a tick: 7, a lift and fire 3 s (once).
     * Only particles: no lava is placed.
     */
    private Effect lavaJet(ServerLevel level0, Vec3 grate, Vec3 toward) {
        Vec3 d0 = toward.subtract(grate).multiply(1, 0, 1);
        Vec3 dir = d0.lengthSqr() < 1.0E-3 ? rotate(new Vec3(1, 0, 0), getRandom().nextDouble() * 360) : d0.normalize();
        double len = 1.0;
        for (double d = 1.0; d <= JET_MAX; d += 1.0) {
            Vec3 p = grate.add(dir.scale(d));
            if (sand(level0, p.x, p.z) == null) {
                break;
            }
            len = d;
        }
        double length = len;
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof GildedChampion g)) {
                return true;
            }
            int k = t[0]++;
            if (k < 30) {
                if (k % 2 == 0) {
                    DustParticleOptions d = k >= 20 ? RED : ORANGE;
                    boss.telegraphRing(level, grate, 1.8, d);
                    g.drawLine(level, grate, dir, 1.0, length, JET_HALF, d);
                }
                if (k % 4 == 0) {
                    level.sendParticles(ParticleTypes.LAVA, grate.x, grate.y + 0.2, grate.z, 2, 0.6, 0.05, 0.6, 0);
                    level.sendParticles(ParticleTypes.SMOKE, grate.x, grate.y + 0.2, grate.z, 4, 0.6, 0.05, 0.6, 0.02);
                }
                if (k == 10) {
                    level.playSound(null, grate.x, grate.y, grate.z, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 2.0F, 0.6F);
                }
                return false;
            }
            int s = k - 30;
            double reach = Math.min(length, s * 2.0 + 2.0);
            for (double d = Math.max(0.0, reach - 2.0); d <= reach; d += 0.7) {
                Vec3 p = grate.add(dir.scale(d));
                level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.5, p.z, 4, 0.25, 0.8, 0.25, 0.04);
                level.sendParticles(ParticleTypes.LAVA, p.x, p.y + 0.4, p.z, 1, 0.2, 0.3, 0.2, 0);
            }
            if (s == 0) {
                level.playSound(null, grate.x, grate.y, grate.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.5F, 0.5F);
                level.sendParticles(ParticleTypes.FLAME, grate.x, grate.y + 1.0, grate.z, 30, 0.5, 1.5, 0.5, 0.08);
            }
            Vec3 side = new Vec3(-dir.z, 0, dir.x);
            for (LivingEntity e : boss.victims(level, grate, length + 2)) {
                Vec3 to = e.position().subtract(grate).multiply(1, 0, 1);
                double along = to.dot(dir);
                boolean onGrate = flatDist(e.position(), grate) <= 1.8 + e.getBbWidth() / 2;
                boolean onLine = along >= 0 && along <= reach && Math.abs(to.dot(side)) <= JET_HALF + e.getBbWidth() / 2;
                if ((onGrate || onLine) && Math.abs(e.getY() - grate.y) < 3.0 && hit.add(e.getUUID())) {
                    if (g.shove(level, e, 7.0F, Vec3.ZERO, 0.3)) {
                        e.igniteForSeconds(3.0F);
                    }
                }
            }
            return reach >= length && s >= 8;
        };
    }

    private void castJets(ServerLevel level, LivingEntity target) {
        List<Vec3> gs = new ArrayList<>(grates(level));
        if (gs.isEmpty()) {
            return;
        }
        gs.sort((a, b) -> Double.compare(flatDist(a, target.position()), flatDist(b, target.position())));
        int n = Math.min(gs.size(), Math.min(4, scaledCount(1) + 1));
        List<Vec3> chosen = new ArrayList<>(gs.subList(0, 1));
        List<Vec3> rest = new ArrayList<>(gs.subList(1, gs.size()));
        while (chosen.size() < n && !rest.isEmpty()) {
            chosen.add(rest.remove(getRandom().nextInt(rest.size())));
        }
        for (Vec3 g : chosen) {
            addEffect(lavaJet(level, g, target.position()));
        }
    }

    /** Gilded rage: gold motes and embers stream off him. */
    private void gildedWeather(ServerLevel level) {
        if (tickCount % 3 == 0) {
            level.sendParticles(GOLD, getX(), getY() + 2.0, getZ(), 2, 0.6, 1.2, 0.6, 0);
            level.sendParticles(ParticleTypes.SMALL_FLAME, getX(), getY() + 1.5, getZ(), 1, 0.6, 1.0, 0.6, 0.01);
        }
        if (tickCount % 20 == 0) {
            for (Vec3 g : grates(level)) {
                level.sendParticles(ParticleTypes.SMOKE, g.x, g.y + 0.2, g.z, 3, 0.6, 0.05, 0.6, 0.01);
            }
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(GOLD, getX(), getY() + 2, getZ(), 6, 0.6, 0.8, 0.6, 0);
            level.playSound(null, this, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.6F, 1.6F);
            return false;
        }
        BossAttack cur = currentAttack();
        if (blockTicks > 0 && cur != null && "block".equals(cur.name) && !isStaggered()) {
            Vec3 src = source.getSourcePosition();
            if (src != null) {
                Vec3 to = src.subtract(position()).multiply(1, 0, 1);
                boolean front = to.lengthSqr() < 1.0E-4 || to.normalize().dot(forward()) >= Math.cos(Math.toRadians(BLOCK_HALF));
                if (front) {
                    blocked++;
                    Vec3 s = position().add(forward().scale(1.4));
                    level.sendParticles(ParticleTypes.CRIT, s.x, s.y + 2.0, s.z, 10, 0.3, 0.4, 0.3, 0.2);
                    level.sendParticles(GOLD, s.x, s.y + 2.0, s.z, 6, 0.3, 0.4, 0.3, 0);
                    level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.8F);
                    if (source.getEntity() instanceof LivingEntity a && a.distanceTo(this) < 5.0) {
                        Vec3 back = a.position().subtract(position()).multiply(1, 0, 1);
                        if (back.lengthSqr() > 1.0E-4) {
                            Vec3 v = safePush(level, a, back.normalize().scale(0.4));
                            a.push(v.x, 0.05, v.z);
                            a.hurtMarked = true;
                        }
                    }
                    return false;
                }
                amount *= 1.3F;                               // caught from the flank or behind his shield
                level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 2, getZ(), 8, 0.4, 0.5, 0.4, 0.2);
            }
        }
        return super.hurtServer(level, source, amount);
    }

    /** Back to the first phase (the fight was reset): the gold dims, the shield is back, base speed. */
    private void resetForm(ServerLevel level) {
        entityData.set(DATA_GILDED, false);
        roarUntil = -1;
        guard = 0;
        blockTicks = 0;
        blocked = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(com.brasshaven.Brasshaven.id("gilded_champion_favour"));
            speed.removeModifier(com.brasshaven.Brasshaven.id("gilded_champion_wrath"));
        }
        discardAdds(level);
    }

    /** Beasts left over by an unload (tagged minions round the arena that this champion no longer tracks). */
    private void discardStaleAdds(ServerLevel level) {
        AABB box = new AABB(BlockPos.containing(centre())).inflate(radius + 6, 12, radius + 6);
        for (Mob m : level.getEntitiesOfClass(Mob.class, box, e -> e.entityTags().contains(MINION_TAG)
                && (e instanceof AbstractPiglin || e instanceof Hoglin) && !adds.contains(e.getUUID()))) {
            m.discard();
        }
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleCheck) {                                  // the first tick (after a reload too)
            staleCheck = false;
            discardStaleAdds(level);
        }
        if (guard > 0) {
            guard--;
        }
        BossAttack cur = currentAttack();
        if (cur == null || !"block".equals(cur.name)) {
            blockTicks = 0;
        }
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 20, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (phase() == 1 && gilded()) {
            resetForm(level);                              // the fight was reset
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free && !gilded() && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
            chain(level, "favour");
        }
        // phase 3: the lava jets from the grates (they wait while he takes the favour or is guarded)
        if (gilded() && phase() == 2 && anyone) {
            gildedWeather(level);
            cur = currentAttack();
            boolean busy = cur != null && "favour".equals(cur.name);
            if (fighting && !busy && guard == 0 && --jetTimer <= 0) {
                jetTimer = Math.max(70, (int) Math.round(JET_EVERY * cooldownScale()));
                castJets(level, target);
            }
        }
        if (tickCount % 200 == 0 && fighting) {
            crowdCheer(level, 1.0F + getRandom().nextFloat() * 0.3F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        blockTicks = 0;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("gilded_champion_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the roar shoves everyone within 7 away: take it back where it would carry them into the podium wall
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        crowdCheer(level, 1.2F);
        sandBurst(level, position(), 40, 2.0);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        discardAdds(level);
        blockTicks = 0;
        level.sendParticles(block(Blocks.GOLD_BLOCK.defaultBlockState()), getX(), getY() + 2, getZ(), 80, 1.0, 1.5, 1.0, 0.2);
        level.sendParticles(ParticleTypes.WAX_ON, getX(), getY() + 2, getZ(), 40, 1.0, 1.5, 1.0, 0.2);
        level.playSound(null, this, SoundEvents.PIGLIN_BRUTE_DEATH, SoundSource.HOSTILE, 3.0F, 0.5F);
        crowdCheer(level, 0.7F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("ChampionCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("ChampionRadius", radius);
        output.putBoolean("ChampionGilded", gilded());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("ChampionCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("ChampionRadius", 20);
        entityData.set(DATA_GILDED, input.getBooleanOr("ChampionGilded", false) && phase() == 2);
        grates = null;
        staleCheck = true;
    }
}
