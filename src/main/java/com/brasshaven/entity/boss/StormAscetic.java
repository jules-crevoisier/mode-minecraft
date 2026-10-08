package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
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
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.StormAscetic.BEADS;
import static com.brasshaven.generated.MobAnims.StormAscetic.CYCLONE;
import static com.brasshaven.generated.MobAnims.StormAscetic.GUST;
import static com.brasshaven.generated.MobAnims.StormAscetic.LIGHTNING;
import static com.brasshaven.generated.MobAnims.StormAscetic.MIRROR;
import static com.brasshaven.generated.MobAnims.StormAscetic.ROAR;
import static com.brasshaven.generated.MobAnims.StormAscetic.SPIN;
import static com.brasshaven.generated.MobAnims.StormAscetic.STAFF;
import static com.brasshaven.generated.MobAnims.StormAscetic.STAGGER;
import static com.brasshaven.generated.MobAnims.StormAscetic.TEMPEST;
import static com.brasshaven.generated.MobAnims.StormAscetic.THUNDER;
import static com.brasshaven.generated.MobAnims.StormAscetic.TOLL;
import static com.brasshaven.generated.MobAnims.StormAscetic.VAULT;

/**
 * L'Ascète des tempêtes (The Storm Ascetic), the hermit of the summit of Pilgrim's Ascent: a gaunt old monk with a
 * staff taller than himself, nine prayer beads orbiting him, wreathed in wind and lightning. He wakes in the bell
 * temple at the top of the stairway (a round hall of radius 14, two doors, the great bell overhead).
 * <p>580 health, armour 12, poise 100, hits of 7 to 18. Three phases:
 * <ul>
 *     <li>Phase 1: <b>staff combo</b> (a wide sweep then a long thrust), <b>pole vault</b> onto the ring that follows
 *     you, <b>gust</b> (a cone of wind that pushes you toward the walls), <b>call lightning</b> on marked spots,
 *     <b>prayer beads</b> flung out in a fan that come back to him, and a <b>whirl</b> when you hug him.</li>
 *     <li>Phase 2 (roar at 65%): the <b>mirror</b> (he vanishes and reappears with two illusions that die in one
 *     hit), the <b>tempest</b> (three staff blows, the last one calling lightning down a line), the <b>cyclone</b>
 *     (the wind draws you in, then a ring you jump), a second lightning volley, combos.</li>
 *     <li>Phase 3 (at 30%, an invulnerable <b>toll</b>): he strikes the floor and the great bell answers. From then on
 *     the bell tolls on its own every ~8 s (a thunder ring rolls out from the centre of the hall: jump it), and he
 *     adds the <b>thunder</b>: three rings in a row from his staff.</li>
 * </ul>
 * The arena is a summit: no hit of his throws a player outward near the edge (see {@link #strike}), the gust's wind
 * stops at a ring drawn before it blows, and his vault never lands outside the hall.
 */
public class StormAscetic extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 4.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double STAFF_REACH = 7.0;
    private static final double GUST_RANGE = 12.0;
    private static final double GUST_HALF = 40.0;
    private static final int MIRROR_EVERY = 520;
    private static final int BELL_EVERY = 160;
    private static final int BELL_WARN = 24;
    private static final int THUNDER_EVERY = 300;
    private static final DustParticleOptions STORM = new DustParticleOptions(0xB8E4FF, 1.3F);
    private static final DustParticleOptions SAFFRON = new DustParticleOptions(0xE0A040, 1.1F);

    /** Arena centre and radius (from the seal), saved with the boss. */
    private @Nullable Vec3 centre;
    private int radius = 13;
    /** Phase 3: the bell has answered. */
    private boolean belled;
    private int tollGuard;
    private int bellTimer;
    private int thunderTimer;
    private int mirrorTimer = 80;
    private int roarUntil = -1;

    private final Set<UUID> struck = new HashSet<>();
    private final List<Vec3> spots = new ArrayList<>();
    private final List<LivingEntity> following = new ArrayList<>();
    private @Nullable Vec3 dest;
    private @Nullable Vec3 vaultFrom;

    public StormAscetic(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 580.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.2);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.StormAscetic.TICKS;
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
        return 100.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 5.5;
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

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("AsceticCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("AsceticRadius", radius);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("AsceticCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("AsceticRadius", 13);
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Where the gust's wind stops: the warning ring drawn before it blows. */
    private double windWall() {
        return Math.max(5.0, radius - 3.0);
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

    /** A standing spot on the hall's floor at (x, z) with room above, or null. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 3) {
            return null;
        }
        for (int dy = 0; dy < 5; dy++) {
            BlockPos p = BlockPos.containing(x, y + dy, z);
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return null;
            }
        }
        return new Vec3(x, y, z);
    }

    private Vec3 floorUnder(ServerLevel level, Vec3 v) {
        double y = floorY(level, v.x, v.y, v.z);
        return Double.isNaN(y) ? new Vec3(v.x, centre().y, v.z) : new Vec3(v.x, y, v.z);
    }

    /** {@code p} pulled inside the hall (at most {@code radius - margin} from the centre). */
    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(2.0, radius - margin);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    private void teleport(ServerLevel level, Vec3 to) {
        level.sendParticles(ParticleTypes.GUST, getX(), getY() + 2, getZ(), 2, 0.4, 1.0, 0.4, 0.0);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2, getZ(), 30, 0.5, 1.4, 0.5, 0.05);
        teleportTo(to.x, to.y, to.z);
        getNavigation().stop();
        setDeltaMovement(Vec3.ZERO);
        level.sendParticles(ParticleTypes.CLOUD, to.x, to.y + 2, to.z, 30, 0.5, 1.4, 0.5, 0.05);
        level.playSound(null, to.x, to.y, to.z, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.0F, 0.7F);
    }

    private void face(@Nullable LivingEntity t) {
        if (t != null) {
            snapFacing((float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F);
        }
    }

    /** Turn toward {@code target} by at most {@code maxTurn} degrees, then keep that facing. */
    private void turnToward(@Nullable LivingEntity target, float maxTurn) {
        if (target == null) {
            return;
        }
        float yaw = (float) (Mth.atan2(target.getZ() - getZ(), target.getX() - getX()) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    // ------------------------------------------------------------------ fairness on the summit

    /**
     * Every hit of his (moves, waves, the NG+ shockwave) comes through here. Within 5 blocks of the edge of the hall
     * the outward part of the knockback is removed and the lift capped: he never throws a player out of a door.
     */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage) || knockback <= 0) {
            return;
        }
        Vec3 push = e.position().subtract(position()).multiply(1, 0, 1);
        push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(knockback);
        push = tame(e, push);
        if (flatDist(e.position(), centre()) > radius - 5.0) {
            lift = Math.min(lift, 0.35);
        }
        e.push(push.x, lift, push.z);
        e.hurtMarked = true;
    }

    /** A horizontal push made safe: near the edge its outward part is dropped and the rest halved. */
    private Vec3 tame(LivingEntity e, Vec3 push) {
        Vec3 radial = e.position().subtract(centre()).multiply(1, 0, 1);
        double r = radial.length();
        if (r > radius - 5.0 && r > 0.1) {
            Vec3 n = radial.scale(1.0 / r);
            double out = push.dot(n);
            if (out > 0) {
                push = push.subtract(n.scale(out));
            }
            push = push.scale(0.5);
        }
        return push;
    }

    /** Pure damage, no push. */
    private void hurt(ServerLevel level, LivingEntity e, float damage) {
        e.hurtServer(level, damageSources().mobAttack(this), damage);
    }

    /**
     * A bolt of lightning on {@code pos} (visual only: no fire, no vanilla damage), then {@code damage} to whoever
     * stands within {@code r}: a small lift, no push. Shared with the illusions.
     */
    static void bolt(ServerLevel level, LivingEntity caster, Vec3 pos, double r, float damage) {
        LightningBolt b = net.minecraft.world.entity.EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
        if (b != null) {
            b.snapTo(pos.x, pos.y, pos.z);
            b.setVisualOnly(true);
            level.addFreshEntity(b);
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, pos.x, pos.y + 0.4, pos.z, 30, r * 0.4, 0.6, r * 0.4, 0.3);
        level.sendParticles(ParticleTypes.CLOUD, pos.x, pos.y + 0.2, pos.z, 8, r * 0.4, 0.1, r * 0.4, 0.02);
        level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.HOSTILE, 2.0F, 1.0F);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos, pos).inflate(r + 1, 3, r + 1), e -> {
            if (!e.isAlive() || e instanceof WayfarerBoss || e instanceof StormIllusion || e.entityTags().contains(MINION_TAG)) {
                return false;
            }
            if (e instanceof Player p) {
                return !p.isCreative() && !p.isSpectator();
            }
            return !(e instanceof Enemy);
        })) {
            if (damage > 0 && flatDist(e.position(), pos) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 2.5) {
                if (e.hurtServer(level, caster.damageSources().mobAttack(caster), damage)) {
                    e.push(0, 0.4, 0);
                    e.hurtMarked = true;
                }
            }
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // staff combo: the staff swung back over his right shoulder (0.7 s, the arc drawn in wind), a wide sweep to his
        // left (15), then he turns up to 40 degrees toward you and drives a long thrust down a marked line (14)
        out.add(BossAttack.of("staff").anim(STAFF).timing(14, 14, 14).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, STAFF_REACH, 65, ParticleTypes.CLOUD);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BREEZE_INHALE, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, STAFF_REACH, 65, 15.0F, 0.6);
                    sweepParticles(b, level, STAFF_REACH, 65);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick == 2) {
                        s.turnToward(t, 40.0F);
                    } else if (tick > 2 && tick < 10 && tick % 2 == 1) {
                        lineDust(b, level, 9.0, ParticleTypes.SMALL_GUST);
                    } else if (tick == 10) {
                        b.hitLine(level, 9.0, 1.0, 14.0F, 0.7);
                        lineDust(b, level, 9.0, ParticleTypes.CLOUD);
                        level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, b.distanceTo(t) > 7 ? "vault" : "spin");
                    }
                })
                .build());
        // pole vault: he plants the staff and crouches (1.0 s): a ring follows you for 0.6 s, then locks; he vaults over
        // in an arc and lands on it at the 10th tick: 16 within 3.2 blocks and a ring of wind (8, jump it)
        out.add(BossAttack.of("vault").anim(VAULT).timing(20, 10, 16).range(7.0, 22.0).cooldown(110).weight(9).track(true)
                .start((b, level, t, tick) -> dest = null)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick < 12 && t != null) {
                        s.dest = s.floorUnder(level, s.clampToArena(t.position(), 2.5));
                    }
                    if (s.dest != null && tick % 2 == 0) {
                        b.telegraphRing(level, s.dest, 3.2, tick < 12 ? ParticleTypes.CLOUD : ParticleTypes.ELECTRIC_SPARK);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_CHARGE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.vaultFrom = s.position();
                        if (s.dest != null) {
                            s.snapFacing((float) (Mth.atan2(s.dest.z - s.getZ(), s.dest.x - s.getX()) * (180.0 / Math.PI)) - 90.0F);
                        }
                        level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.vaultStep(level, tick);
                    }
                })
                .build());
        // gust: the left palm thrust out (0.9 s: the cone is drawn in wind, and a ring of cloud near the walls marks
        // where the wind stops), then 1.2 s of wind pushing everyone in the cone away from him: 5 once. The push never
        // carries anyone past the ring
        out.add(BossAttack.of("gust").anim(GUST).timing(18, 24, 12).range(0, 11.0).cooldown(150).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick % 3 == 0) {
                        s.coneDust(level, ParticleTypes.SMALL_GUST);
                    }
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, s.centre(), s.windWall(), ParticleTypes.CLOUD);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_INHALE, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.BREEZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F))
                .active((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.blow(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "lightning");
                    }
                })
                .build());
        // call lightning: the staff raised to the sky (1.1 s): rings follow every player for 0.6 s, then lock (sparks),
        // with a few strays; the bolts fall on them all: 14, no push. Phase 2: a second volley falls 0.7 s later on
        // where the players have moved to
        out.add(BossAttack.of("lightning").anim(LIGHTNING).timing(22, 20, 14).range(0, 26.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.pickSpots(level, b.phase() == 2 ? 5 : 3);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick < 12) {
                        s.followSpots(level);
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 p : s.spots) {
                            b.telegraphRing(level, p, 1.8, tick < 12 ? STORM : ParticleTypes.ELECTRIC_SPARK);
                        }
                    }
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 6.5, b.getZ(), 2, 0.4, 0.4, 0.4, 0.1);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.strikeSpots(level);
                        if (b.phase() == 2) {
                            s.pickSpots(level, 0);
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s) || s.spots.isEmpty()) {
                        return;
                    }
                    if (tick < 14 && tick % 2 == 0) {
                        for (Vec3 p : s.spots) {
                            b.telegraphRing(level, p, 1.8, ParticleTypes.ELECTRIC_SPARK);
                        }
                    } else if (tick == 14) {
                        s.strikeSpots(level);
                    }
                })
                .build());
        // prayer beads: the palm raised, the beads spin up and lift (0.8 s, a ring on the target), then flung out one by
        // one in a fan toward you; each flies 14 blocks, turns and comes back to him: 7 going, 7 coming back
        out.add(BossAttack.of("beads").anim(BEADS).timing(16, 32, 10).range(4.0, 22.0).cooldown(110).weight(8)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 1.3, SAFFRON);
                    }
                    double a = tick * 0.7;
                    level.sendParticles(SAFFRON, b.getX() + Math.cos(a) * 1.4, b.getY() + 2.8, b.getZ() + Math.sin(a) * 1.4,
                            1, 0, 0, 0, 0);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 2.0F, 1.0F);
                    }
                })
                .active((b, level, t, tick) -> {
                    int n = b.phase() == 2 ? 9 : 8;
                    if (tick % 2 == 0 && tick / 2 < n && t != null) {
                        int i = tick / 2;
                        Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                        Vec3 dir = to.lengthSqr() < 1.0E-4 ? b.forward() : to.normalize();
                        double spread = b.phase() == 2 ? 10.0 : 8.0;
                        dir = rotate(dir, (i - (n - 1) / 2.0) * spread);
                        b.addEffect(bead(b.position().add(0, 2.6, 0), dir, 14.0, 7.0F));
                        level.playSound(null, b, SoundEvents.WIND_CHARGE_THROW, SoundSource.HOSTILE, 1.5F, 1.2F);
                    }
                })
                .build());
        // whirl (anti-hug): the staff swung low round him (0.6 s, a ring at 4.5 blocks), one full turn: 13
        out.add(BossAttack.of("spin").anim(SPIN).timing(12, 4, 14).range(0, 3.5).cooldown(70).weight(10).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, ParticleTypes.CLOUD);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_IDLE_GROUND, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.5, 13.0F, 0.9, 0.3);
                    for (int a = 0; a < 360; a += 20) {
                        double r = Math.toRadians(a);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX() + Math.cos(r) * 3, b.getY() + 1.2,
                                b.getZ() + Math.sin(r) * 3, 1, 0, 0, 0, 0);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // tempest: three blows. The sweep (14) at once, a backhand (13) after he turns up to 40 degrees, then the staff
        // raised high and slammed down a marked line (18 close, then three bolts along the line: 12 each)
        out.add(BossAttack.of("tempest").anim(TEMPEST).phaseTwo().timing(16, 30, 16).range(0, 7.5).cooldown(160).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, STAFF_REACH, 65, ParticleTypes.CLOUD);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_INHALE, SoundSource.HOSTILE, 2.0F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, STAFF_REACH, 65, 14.0F, 0.5);
                    sweepParticles(b, level, STAFF_REACH, 65);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick == 4 || tick == 13) {
                        s.turnToward(t, 40.0F);
                    }
                    if (tick > 4 && tick < 10 && tick % 2 == 1) {
                        b.telegraphArc(level, 6.5, 70, ParticleTypes.CLOUD);
                    } else if (tick == 10) {
                        b.hitArc(level, 6.5, 70, 13.0F, 0.6);
                        sweepParticles(b, level, 6.5, 70);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.8F);
                    } else if (tick > 13 && tick < 22 && tick % 2 == 0) {
                        lineDust(b, level, 10.0, ParticleTypes.ELECTRIC_SPARK);
                        for (double d = 3; d <= 9; d += 3) {
                            b.telegraphRing(level, b.ahead(d), 1.5, STORM);
                        }
                    } else if (tick == 22) {
                        b.hitLine(level, 4.0, 1.2, 18.0F, 0.4);
                        for (double d = 3; d <= 9; d += 3) {
                            bolt(level, b, s.floorUnder(level, b.ahead(d)), 1.5, 12.0F);
                        }
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .build());
        // cyclone: the staff whirled overhead (1.0 s: a ring of wind at 12 blocks); for 1.0 s the wind draws everyone
        // within 12 blocks toward him (inward only), then he hurls it out: a ring rolls out (12, jump it)
        out.add(BossAttack.of("cyclone").anim(CYCLONE).phaseTwo().timing(20, 30, 14).range(0, 10.0).cooldown(220).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 12.0, ParticleTypes.SMALL_GUST);
                    }
                    double a = tick * 0.6;
                    level.sendParticles(ParticleTypes.CLOUD, b.getX() + Math.cos(a) * 2, b.getY() + 5.5, b.getZ() + Math.sin(a) * 2,
                            2, 0.1, 0.1, 0.1, 0.0);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick < 20) {
                        s.pull(level, tick);
                    } else if (tick == 20) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 12.0, 0.6, 12.0F, ParticleTypes.CLOUD));
                        level.sendParticles(ParticleTypes.GUST_EMITTER_LARGE, b.getX(), b.getY() + 1, b.getZ(), 1, 0, 0, 0, 0);
                        level.playSound(null, b, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .build());
        // mirror (scheduled by bossTick, never rolled): he whirls in a column of wind (1.0 s) while three rings of cloud
        // are drawn round you; he vanishes and reappears on one of them, his illusions on the others. An illusion
        // dies to any blow
        out.add(BossAttack.of("mirror").anim(MIRROR).timing(20, 4, 10).range(9999, 9999).weight(1).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.pickMirrorSpots(level, t);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof StormAscetic s)) {
                        return;
                    }
                    if (tick % 2 == 0) {
                        for (Vec3 p : s.spots) {
                            b.telegraphRing(level, p, 1.4, ParticleTypes.CLOUD);
                            level.sendParticles(ParticleTypes.SMALL_GUST, p.x, p.y + 1.5, p.z, 1, 0.3, 1.0, 0.3, 0.0);
                        }
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 2, b.getZ(), 4, 0.5, 1.6, 0.5, 0.04);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_MIRROR, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.splitIntoIllusions(level, t);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (scheduled by bossTick)
        // toll: the transition. He kneels and lifts the staff to the great bell, invulnerable (2.0 s); he strikes the
        // floor, the bell answers and a ring of thunder rolls out from the centre of the hall (8, jump it)
        out.add(BossAttack.of("toll").anim(TOLL).timing(40, 6, 18).range(9999, 9999).weight(1).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.tollGuard = 66;
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 6 + tick * 0.1, b.getZ(), 4, 0.6, 0.4, 0.6, 0.15);
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 1.0F + tick * 0.02F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof StormAscetic s) {
                        s.answerBell(level);
                    }
                })
                .build());
        // thunder: the staff raised (1.0 s, rings flash at his feet); the bell tolls three times, 0.65 s apart, and each
        // time a ring of thunder rolls out from him (11, jump it)
        out.add(BossAttack.of("thunder").anim(THUNDER).timing(20, 40, 16).range(9999, 9999).weight(1).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0, ParticleTypes.ELECTRIC_SPARK);
                        b.telegraphRing(level, b.position(), 14.0, STORM);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.8F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 13 || tick == 26) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 14.0, 0.55, 11.0F, ParticleTypes.ELECTRIC_SPARK));
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.5F);
                        level.playSound(null, b, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 1.5F, 1.6F);
                    } else if (tick == 10 || tick == 23) {
                        b.telegraphRing(level, b.position(), 2.0, ParticleTypes.ELECTRIC_SPARK);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private static void sweepParticles(WayfarerBoss b, ServerLevel level, double range, double halfAngle) {
        for (double a = -halfAngle; a <= halfAngle; a += 15) {
            Vec3 p = b.position().add(rotate(b.forward(), a).scale(range * 0.7));
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.4, p.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 1.4, p.z, 1, 0.1, 0.1, 0.1, 0.02);
        }
    }

    private static void lineDust(WayfarerBoss b, ServerLevel level, double length, ParticleOptions p) {
        for (double d = 1.5; d <= length; d += 1.0) {
            Vec3 at = b.ahead(d);
            level.sendParticles(p, at.x, b.getY() + 0.15, at.z, 1, 0, 0, 0, 0);
        }
    }

    /** The outline of the gust's cone (its two edges and its far arc). */
    private void coneDust(ServerLevel level, ParticleOptions p) {
        for (int side = -1; side <= 1; side += 2) {
            Vec3 dir = rotate(forward(), GUST_HALF * side);
            for (double d = 1.5; d <= GUST_RANGE; d += 1.0) {
                Vec3 at = position().add(dir.scale(d));
                level.sendParticles(p, at.x, getY() + 0.2, at.z, 1, 0, 0, 0, 0);
            }
        }
        for (double a = -GUST_HALF; a <= GUST_HALF; a += 8) {
            Vec3 at = position().add(rotate(forward(), a).scale(GUST_RANGE));
            level.sendParticles(p, at.x, getY() + 0.2, at.z, 1, 0, 0, 0, 0);
        }
    }

    /**
     * One tick of the gust: everyone in the cone is pushed away from him (5 damage the first time). Past the wind wall
     * (the ring drawn during the wind-up) the outward part of the push is dropped and any outward speed cancelled, so
     * the wind pins players against the ring but never carries them out of the hall.
     */
    private void blow(ServerLevel level, int tick) {
        if (tick % 2 == 0) {
            for (double a = -GUST_HALF; a <= GUST_HALF; a += 16) {
                Vec3 dir = rotate(forward(), a);
                Vec3 at = position().add(dir.scale(2.0 + (tick % 6) * 1.6));
                level.sendParticles(ParticleTypes.GUST, at.x, getY() + 1.2, at.z, 1, 0.2, 0.4, 0.2, 0.0);
            }
            telegraphRing(level, centre(), windWall(), ParticleTypes.CLOUD);
        }
        if (tick % 6 == 0) {
            level.playSound(null, this, SoundEvents.BREEZE_IDLE_AIR, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
        Vec3 c = centre();
        double cos = Math.cos(Math.toRadians(GUST_HALF));
        for (LivingEntity e : victims(level, position(), GUST_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > GUST_RANGE + e.getBbWidth() / 2 || d < 0.1 || to.normalize().dot(forward()) < cos) {
                continue;
            }
            if (struck.add(e.getUUID())) {
                hurt(level, e, 5.0F);
            }
            Vec3 push = to.normalize().scale(0.13);
            Vec3 radial = e.position().subtract(c).multiply(1, 0, 1);
            double r = radial.length();
            Vec3 v = e.getDeltaMovement();
            if (r > windWall() - 1.5 && r > 0.1) {
                Vec3 n = radial.scale(1.0 / r);
                double out = push.dot(n);
                if (out > 0) {
                    push = push.subtract(n.scale(out));
                }
                double vOut = v.x * n.x + v.z * n.z;
                if (vOut > 0) {
                    v = v.subtract(n.x * vOut, 0, n.z * vOut);      // the wind wall: no drift outward past the ring
                }
                if (tick % 3 == 0) {
                    level.sendParticles(ParticleTypes.CLOUD, e.getX(), e.getY() + 1, e.getZ(), 2, 0.3, 0.5, 0.3, 0.01);
                }
            }
            Vec3 nv = v.add(push.x, 0, push.z);
            double h = Math.hypot(nv.x, nv.z);
            if (h > 0.6) {
                nv = new Vec3(nv.x * 0.6 / h, nv.y, nv.z * 0.6 / h);
            }
            e.setDeltaMovement(nv);
            e.hurtMarked = true;
        }
    }

    /** One tick of the cyclone's draw: everyone within 12 blocks drifts toward him (inward: always safe). */
    private void pull(ServerLevel level, int tick) {
        for (int i = 0; i < 4; i++) {
            double a = tick * 0.5 + i * Math.PI / 2;
            double r = 12.0 - tick * 0.5;
            level.sendParticles(ParticleTypes.SMALL_GUST, getX() + Math.cos(a) * r, getY() + 0.6, getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0);
        }
        for (LivingEntity e : victims(level, position(), 12.0)) {
            Vec3 to = position().subtract(e.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d < 2.0 || d > 12.0) {
                continue;
            }
            Vec3 in = to.normalize().scale(0.07);
            e.push(in.x, 0, in.z);
            e.hurtMarked = true;
        }
    }

    /** One tick of the vault: an arc from where he sprang to the locked ring, landing on the last tick. */
    private void vaultStep(ServerLevel level, int tick) {
        if (vaultFrom == null || dest == null) {
            return;
        }
        resetFallDistance();
        double f = Math.min(1.0, (tick + 1) / 10.0);
        Vec3 want = vaultFrom.add(dest.subtract(vaultFrom).scale(f)).add(0, 5.5 * Math.sin(Math.PI * f), 0);
        setDeltaMovement(want.subtract(position()));
        hurtMarked = true;
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 1, getZ(), 3, 0.4, 0.6, 0.4, 0.02);
        if (tick % 2 == 0) {
            telegraphRing(level, dest, 3.2, ParticleTypes.ELECTRIC_SPARK);
        }
        if (tick == 9) {
            Vec3 c = dest;
            move(MoverType.SELF, c.subtract(position()));
            hitCircle(level, c, 3.2, 16.0F, 0.7, 0.4);
            addEffect(WayfarerBoss.wave(c, 8.0, 0.5, 8.0F, ParticleTypes.CLOUD));
            level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, c.x, c.y + 0.3, c.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y + 0.3, c.z, 40, 1.4, 0.3, 1.4, 0.2);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.7F);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
    }

    /** Ring spots for the lightning: every player in the hall, plus {@code strays} random spots on the floor. */
    private void pickSpots(ServerLevel level, int strays) {
        spots.clear();
        following.clear();
        for (LivingEntity e : victims(level, centre(), radius + 4.0)) {
            spots.add(floorUnder(level, e.position()));
            following.add(e);
        }
        for (int i = 0, tries = 0; i < strays && tries < 20; tries++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 2.0 + random.nextDouble() * Math.max(1.0, radius - 4.0);
            Vec3 p = safeSpot(level, centre().x + Math.cos(a) * r, centre().z + Math.sin(a) * r);
            if (p != null) {
                spots.add(p);
                i++;
            }
        }
    }

    /** The rings on players follow them until they lock. */
    private void followSpots(ServerLevel level) {
        for (int i = 0; i < following.size() && i < spots.size(); i++) {
            LivingEntity e = following.get(i);
            if (e.isAlive()) {
                spots.set(i, floorUnder(level, e.position()));
            }
        }
    }

    private void strikeSpots(ServerLevel level) {
        for (Vec3 p : spots) {
            bolt(level, this, p, 1.8, 14.0F);
        }
        spots.clear();
        following.clear();
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 2.0F, 1.2F);
    }

    /** A thrown prayer bead: out {@code maxDist} blocks (or to a wall), then back to him; 7 each way, once per pass. */
    private static Effect bead(Vec3 from, Vec3 dir, double maxDist, float damage) {
        Set<UUID> out = new HashSet<>();
        Set<UUID> back = new HashSet<>();
        double[] d = {0};
        boolean[] returning = {false};
        Vec3[] pos = {from};
        int[] life = {0};
        return (boss, level) -> {
            life[0]++;
            Vec3 p;
            if (!returning[0]) {
                d[0] += 0.8;
                p = from.add(dir.scale(d[0]));
                BlockPos bp = BlockPos.containing(p);
                if (d[0] >= maxDist || !level.getBlockState(bp).getCollisionShape(level, bp).isEmpty()) {
                    returning[0] = true;
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.BAMBOO_HIT, SoundSource.HOSTILE, 1.0F, 0.8F);
                }
            } else {
                Vec3 home = boss.position().add(0, 2.6, 0);
                Vec3 to = home.subtract(pos[0]);
                if (to.length() < 1.2 || life[0] > 120) {
                    return true;
                }
                p = pos[0].add(to.normalize().scale(0.9));
            }
            pos[0] = p;
            level.sendParticles(SAFFRON, p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0.0);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
            Set<UUID> hit = returning[0] ? back : out;
            for (LivingEntity e : boss.victims(level, p, 1.5)) {
                if (e.getBoundingBox().inflate(0.4).contains(p) && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.25, 0.1);
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.WOOD_HIT, SoundSource.HOSTILE, 1.0F, 1.2F);
                }
            }
            return false;
        };
    }

    // ------------------------------------------------------------------ phase 2: the mirror

    private List<StormIllusion> illusions(ServerLevel level) {
        return level.getEntitiesOfClass(StormIllusion.class, new AABB(BlockPos.containing(centre())).inflate(radius + 16, 16, radius + 16),
                StormIllusion::isAlive);
    }

    /** Three (co-op: up to four) spots on a circle of 6 blocks round the target, inside the hall. */
    private void pickMirrorSpots(ServerLevel level, @Nullable LivingEntity t) {
        spots.clear();
        Vec3 c = t != null ? t.position() : centre();
        int n = 1 + Math.min(3, scaledCount(2));
        double base = random.nextDouble() * Math.PI * 2;
        for (int i = 0; i < n * 3 && spots.size() < n; i++) {
            double a = base + Math.PI * 2 * i / n + (i >= n ? 0.4 * (i / n) : 0);
            Vec3 p = clampToArena(c.add(Math.cos(a) * 6.0, 0, Math.sin(a) * 6.0), 2.0);
            Vec3 s = safeSpot(level, p.x, p.z);
            if (s != null) {
                spots.add(s);
            }
        }
    }

    private void splitIntoIllusions(ServerLevel level, @Nullable LivingEntity t) {
        if (spots.isEmpty()) {
            return;
        }
        int me = random.nextInt(spots.size());
        Vec3 self = spots.get(me);
        teleport(level, self);
        face(t);
        for (int i = 0; i < spots.size(); i++) {
            if (i == me) {
                continue;
            }
            Vec3 p = spots.get(i);
            StormIllusion ill = ModEntities.STORM_ILLUSION.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (ill == null) {
                continue;
            }
            float yaw = t == null ? getYRot() : (float) (Mth.atan2(t.getZ() - p.z, t.getX() - p.x) * (180.0 / Math.PI)) - 90.0F;
            ill.snapTo(p.x, p.y, p.z, yaw, 0);
            ill.setOwner(this);
            ill.addTag(MINION_TAG);
            ill.setTarget(t);
            level.addFreshEntity(ill);
            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 2, p.z, 30, 0.5, 1.4, 0.5, 0.05);
        }
        spots.clear();
        level.playSound(null, this, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 3.0F, 0.7F);
    }

    private void dispelIllusions(ServerLevel level) {
        for (StormIllusion ill : illusions(level)) {
            ill.pop(level);
        }
    }

    // ------------------------------------------------------------------ phase 3: the bell

    private void answerBell(ServerLevel level) {
        belled = true;
        tollGuard = 0;
        bellTimer = 100;
        thunderTimer = 160;
        Vec3 c = centre();
        addEffect(WayfarerBoss.wave(c, radius + 1.0, 0.6, 8.0F, ParticleTypes.ELECTRIC_SPARK));
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 1, getZ(), 80, 1.5, 0.5, 1.5, 0.3);
        level.playSound(null, c.x, c.y + 12, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 6.0F, 0.4F);
        level.playSound(null, c.x, c.y + 12, c.z, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 4.0F, 0.5F);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 3.0F, 0.8F);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("storm_ascetic_bell"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
    }

    /**
     * The great bell tolls on its own: for {@link #BELL_WARN} ticks sparks gather at the centre of the hall and the
     * bell hums, then a ring of thunder rolls out to the walls (9, jump it).
     */
    private Effect bellRing() {
        int[] t = {0};
        return (boss, level) -> {
            Vec3 c = centre();
            if (t[0] < BELL_WARN) {
                if (t[0] % 3 == 0) {
                    boss.telegraphRing(level, c, 1.0 + t[0] * 0.06, ParticleTypes.ELECTRIC_SPARK);
                    level.sendParticles(STORM, c.x, c.y + 10 - t[0] * 0.4, c.z, 3, 0.3, 0.3, 0.3, 0);
                }
                if (t[0] == 0) {
                    level.playSound(null, c.x, c.y + 12, c.z, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 4.0F, 0.6F);
                }
                t[0]++;
                return false;
            }
            boss.addEffect(WayfarerBoss.wave(c, radius + 1.0, 0.55, 9.0F, ParticleTypes.ELECTRIC_SPARK));
            level.playSound(null, c.x, c.y + 12, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 5.0F, 0.45F);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 1.5F, 1.5F);
            return true;
        };
    }

    // ------------------------------------------------------------------ helpers

    /** Horizontal vector rotated by {@code degrees} around the vertical axis (positive turns toward his right). */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    // ------------------------------------------------------------------ brain: phases, the bell, ambience

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (tollGuard > 0) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 6, 0.6, 1.0, 0.6, 0.1);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (tollGuard > 0) {
            tollGuard--;
        }
        if (phase() == 1 && (belled || roarUntil >= 0)) {     // the fight was reset
            belled = false;
            roarUntil = -1;
            mirrorTimer = 80;
            tollGuard = 0;
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("storm_ascetic_bell"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("storm_ascetic_wrath"));
            }
            dispelIllusions(level);
        }
        // never lost off the summit: back to the centre if he ever leaves the hall
        Vec3 c = centre();
        if (getY() < c.y - 4 || flatDist(position(), c) > radius + 3) {
            Vec3 home = safeSpot(level, c.x, c.z);
            teleport(level, home != null ? home : c);
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean free = fighting && currentAttack() == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2) {
            if (free && !belled && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "toll");
                free = false;
            }
            if (free && --mirrorTimer <= 0 && illusions(level).isEmpty()) {
                mirrorTimer = (int) Math.round(MIRROR_EVERY * cooldownScale());
                chain(level, "mirror");
                free = false;
            }
            if (belled && fighting) {
                if (--bellTimer <= 0) {
                    bellTimer = (int) Math.round(BELL_EVERY * cooldownScale());
                    addEffect(bellRing());
                }
                if (free && --thunderTimer <= 0) {
                    thunderTimer = (int) Math.round(THUNDER_EVERY * cooldownScale());
                    chain(level, "thunder");
                }
            }
        }
        // ambience: wind round his feet, sparks on the staff's ring, the beads' glint
        if (tickCount % 6 == 0) {
            level.sendParticles(ParticleTypes.SMALL_GUST, getX(), getY() + 0.3, getZ(), 1, 0.8, 0.1, 0.8, 0.0);
        }
        if (tickCount % (belled ? 3 : 8) == 0) {
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            double sx = getX() - Mth.cos(yaw) * 1.3;
            double sz = getZ() - Mth.sin(yaw) * 1.3;
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, sx, getY() + 5.4, sz, 1, 0.3, 0.3, 0.3, 0.05);
        }
        if (tickCount % 10 == 0) {
            double a = tickCount * 0.105;
            level.sendParticles(SAFFRON, getX() + Math.cos(a) * 1.1, getY() + 2.8, getZ() + Math.sin(a) * 1.1, 1, 0, 0, 0, 0);
        }
        if (phase() == 2 && tickCount % 50 == 0) {
            level.playSound(null, this, SoundEvents.BREEZE_IDLE_AIR, SoundSource.HOSTILE, 1.0F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        roarUntil = tickCount + MobAnims.StormAscetic.TICKS[ROAR] + 5;
        mirrorTimer = 90;
        // the engine's roar shoves everyone nearby; on a summit that shove is replaced by a gentle one that never
        // points outward near the edge
        for (LivingEntity e : victims(level, position(), 7.5)) {
            Vec3 away = e.position().subtract(position()).multiply(1, 0, 1);
            Vec3 v = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize().scale(0.5);
            v = tame(e, v);
            e.setDeltaMovement(v.x, 0.3, v.z);
            e.hurtMarked = true;
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("storm_ascetic_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        bolt(level, this, position(), 0.1, 0.0F);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.0, getZ(), 80, 1.5, 2.0, 1.5, 0.1);
        level.playSound(null, this, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.HOSTILE, 3.0F, 0.7F);
        level.playSound(null, this, SoundEvents.BREEZE_WHIRL, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        dispelIllusions(level);
        Vec3 c = centre();
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.5, getZ(), 150, 1.2, 2.5, 1.2, 0.15);
        level.sendParticles(SAFFRON, getX(), getY() + 2.5, getZ(), 60, 1.0, 1.5, 1.0, 0.0);
        level.playSound(null, c.x, c.y + 12, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 5.0F, 0.6F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 4.0F, 0.8F);
        belled = false;
    }
}
