package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
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
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ShulkerBullet;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.StarCurator.BLINK;
import static com.brasshaven.generated.MobAnims.StarCurator.CONSTELLATION;
import static com.brasshaven.generated.MobAnims.StarCurator.INVERT;
import static com.brasshaven.generated.MobAnims.StarCurator.LANCE;
import static com.brasshaven.generated.MobAnims.StarCurator.ORBIT;
import static com.brasshaven.generated.MobAnims.StarCurator.PAGESTORM;
import static com.brasshaven.generated.MobAnims.StarCurator.ROAR;
import static com.brasshaven.generated.MobAnims.StarCurator.STAFF;
import static com.brasshaven.generated.MobAnims.StarCurator.STAGGER;
import static com.brasshaven.generated.MobAnims.StarCurator.STARFALL;
import static com.brasshaven.generated.MobAnims.StarCurator.STARLANCE;
import static com.brasshaven.generated.MobAnims.StarCurator.VOLLEY;
import static com.brasshaven.generated.MobAnims.StarCurator.WELL;

/**
 * Le Conservateur dévoreur d'étoiles (The Star-Eater Curator), the keeper of the Starfall Library: a 5.6-block robed
 * scholar whose head is the cracked meteorite that wrecked his archive, a starfield showing through the cracks; five
 * books orbit him and he fights with an astrolabe staff. He waits in the crater chamber under the floating library
 * (radius 17, a dome 13 to 19 high, four starlight braziers crowned with amethyst: the meteorite's crystal nodes).
 * <p>End tier, deliberately hard: 780 health, armour 14, poise 125, hits of 6 to 17. Three phases:
 * <ul>
 *     <li>Phase 1: the <b>staff</b> combo, the <b>book volley</b> (weakly homing tomes that any hit or arrow shoots
 *     down), the <b>gravity well</b> (everyone is drawn toward him, then it implodes: run outward), the
 *     <b>starfall</b> (shards fall on marked spots), the <b>orbit</b> (anti-hug) and the <b>lance</b> (he streaks
 *     along a line through you).</li>
 *     <li>Phase 2 (a roar at 65%): faster, chained combos, the <b>page storm</b> (for 7 s, whoever is outside the
 *     moving safe circles is blinded and cut by pages, while he keeps fighting) and the <b>constellation</b> (lines
 *     between stars on the floor burst one after another).</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): the crater's gravity <b>inverts</b>. Every
 *     8 s a pulse lifts every player who is not standing by a crystal node he does not occupy (Levitation for about
 *     1.3 s, then Slow Falling so everyone lands on the floor); every 10 s he <b>blinks</b> to another node and fires a
 *     <b>star-lance</b> across the crater that also hits floating players.</li>
 * </ul>
 * He places no blocks. Every lift ends on the floor: players are only lifted over floor with headroom, are pulled
 * toward the centre while afloat, and get Slow Falling when the pulse ends (also when he dies or the fight resets).
 */
public class StarCurator extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double STAFF_RANGE = 5.5;
    private static final double STAFF_HALF = 70;
    private static final double WELL_CORE = 4.0;
    private static final double ANCHOR_R = 3.5;
    private static final double SAFE_R = 3.0;
    private static final int PULSE_EVERY = 160;
    private static final int BLINK_EVERY = 200;
    private static final int STORM_LIFE = 170;
    private static final int STORM_GRACE = 30;
    private static final DustParticleOptions STARDUST = new DustParticleOptions(0xBFD8FF, 1.3F);
    private static final DustParticleOptions VIOLET = new DustParticleOptions(0xA060E0, 1.4F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF0C860, 1.4F);
    private static final DustParticleOptions PAGE = new DustParticleOptions(0xEADBB8, 1.2F);
    private static final DustParticleOptions EMBER = new DustParticleOptions(0xE2783C, 1.3F);

    private @Nullable Vec3 centre;
    private int radius = 16;
    /** Phase 3 has started (the crater's gravity inverted). */
    private boolean inverted;
    private int guard;
    private int roarUntil = -1;
    private int pulseTimer = 60;
    private int blinkTimer = 80;
    private int stormUntil = -1;
    private @Nullable List<Vec3> nodes;
    private int nodeAt = -1;
    private int nodeNext = -1;
    private @Nullable Vec3 lanceFrom;
    private @Nullable Vec3 lanceTo;
    private final List<Vec3> stars = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();

    public StarCurator(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 780.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.StarCurator.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.PURPLE;
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
        return 125.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 5.0;
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
        nodes = null;
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Usable floor radius round the seal (the crater floor is 17 across from the seal). */
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

    /** Free blocks above {@code p} (up to {@code max}). */
    private static int headroom(ServerLevel level, Vec3 p, int max) {
        BlockPos b = BlockPos.containing(p);
        for (int y = 0; y < max; y++) {
            BlockPos q = b.above(y);
            if (!level.getBlockState(q).getCollisionShape(level, q).isEmpty()) {
                return y;
            }
        }
        return max;
    }

    /** A standing spot on the crater floor at (x, z) with room for him above, or null. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 2.5) {
            return null;
        }
        return headroom(level, new Vec3(x, y, z), 6) >= 6 ? new Vec3(x, y, z) : null;
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

    /** Pushes are capped at 1.3; near the wall (or a drop) the outward part is removed, so nobody is thrown away. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.3, knockback));
            Vec3 radial = e.position().subtract(centre()).multiply(1, 0, 1);
            double r = radial.length();
            Vec3 probe = e.position().add(push.lengthSqr() > 1.0E-6 ? push.normalize().scale(2.0) : Vec3.ZERO);
            double fy = floorY(level, probe.x, e.getY(), probe.z);
            boolean drop = Double.isNaN(fy) || fy < e.getY() - 2.5;
            if ((r > reach() - 3.0 || drop) && r > 0.1) {
                Vec3 n = radial.scale(1.0 / r);
                double out = push.dot(n);
                if (out > 0) {
                    push = push.subtract(n.scale(out));
                }
                if (drop) {
                    push = Vec3.ZERO;
                }
            }
        }
        lift = Math.min(lift, 0.5);
        if (push.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // staff: the astrolabe swung back over his right shoulder (0.7 s, the arc drawn in stardust), a forehand sweep,
        // a backhand 0.5 s later after a turn toward you; phase 2 adds a thrust down a line 0.5 s after that
        out.add(BossAttack.of("staff").anim(STAFF).timing(14, 24, 14).range(0, 6.5).cooldown(60).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, STAFF_RANGE, STAFF_HALF, STARDUST);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 10) {
                        staffCut(level, 13.0F);
                    }
                    if (tick == 3) {
                        turnToward(t, 30.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, STAFF_RANGE, STAFF_HALF, STARDUST);
                    }
                    if (b.phase() == 2) {
                        if (tick == 12) {
                            turnToward(t, 25.0F);
                        }
                        if (tick > 12 && tick < 20 && tick % 2 == 0) {
                            for (double d = 1.0; d <= 7.0; d += 1.0) {
                                Vec3 p = b.ahead(d);
                                level.sendParticles(STARDUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                            }
                        }
                        if (tick == 20) {
                            b.hitLine(level, 7.0, 1.2, 16.0F, 0.6);
                            for (double d = 1.0; d <= 7.0; d += 0.5) {
                                Vec3 p = b.ahead(d);
                                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 1.6, p.z, 1, 0.05, 0.05, 0.05, 0.01);
                            }
                            level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.5F, 0.6F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 4.5 ? "orbit" : "lance");
                    }
                })
                .build());
        // volley: the left hand raised, the books drawn in and spinning (0.9 s), then flung: tomes that drift after
        // you (weakly homing). Any hit or arrow shoots one down
        out.add(BossAttack.of("volley").anim(VOLLEY).timing(18, 10, 14).range(5.0, 28.0).cooldown(120).weight(9)
                .windup((b, level, t, tick) -> {
                    double a = tick * 0.6;
                    for (int k = 0; k < 3; k++) {
                        double ang = a + k * Math.PI * 2 / 3;
                        level.sendParticles(ParticleTypes.ENCHANT, b.getX() + Math.cos(ang) * 1.6, b.getY() + 3.3,
                                b.getZ() + Math.sin(ang) * 1.6, 2, 0.1, 0.1, 0.1, 0.2);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> launchTomes(level, t))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) > 7.0 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "lance");
                    }
                })
                .build());
        // gravity well: the staff planted before him (1.0 s; the core ring drawn, dust streaming in): for 1.5 s
        // everyone within 15 is drawn toward him (sprint outward to hold), then the well implodes: 15 within 4.
        // Phase 2: a ring of force rolls out after it (jump it)
        out.add(BossAttack.of("well").anim(WELL).timing(20, 40, 16).range(0, 14.0).cooldown(220).weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), WELL_CORE, VIOLET);
                    }
                    for (int k = 0; k < 4; k++) {
                        double ang = b.getRandom().nextDouble() * Math.PI * 2;
                        double d = 4 + b.getRandom().nextDouble() * 10;
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX() + Math.cos(ang) * d, b.getY() + 0.6,
                                b.getZ() + Math.sin(ang) * d, 1, 0.1, 0.2, 0.1, 0.02);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.sendParticles(ParticleTypes.SONIC_BOOM, b.getX(), b.getY() + 0.5, b.getZ(), 1, 0, 0, 0, 0);
                })
                .active((b, level, t, tick) -> wellStep(level, tick))
                .build());
        // starfall: the astrolabe raised to the dome (0.8 s); a ring follows every player for 0.7 s, then locks, and
        // 0.8 s later a star-shard falls on it (14 within 2.5); strays fall round the crater. Phase 2: a second volley
        out.add(BossAttack.of("starfall").anim(STARFALL).timing(16, 50, 14).range(0, 30.0).cooldown(200).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 6.5, b.getZ(), 2, 0.3, 0.3, 0.3, 0.05);
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> starVolley(level, t))
                .active((b, level, t, tick) -> {
                    if (tick == 25 && b.phase() == 2) {
                        starVolley(level, t);
                    }
                })
                .build());
        // orbit: anti-hug. He draws in (0.6 s, the books' ring at 5 drawn round him), then the books spin out: 11
        // within 5. Phase 2: they fly on outward as a ring to 9 (jump it)
        out.add(BossAttack.of("orbit").anim(ORBIT).timing(12, 16, 12).range(0, 4.5).cooldown(70).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.0, PAGE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 5.0, 11.0F, 1.0, 0.3);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 9, 0.5, 7.0F, PAGE));
                    }
                    for (int a = 0; a < 360; a += 15) {
                        Vec3 p = b.position().add(rotate(new Vec3(0, 0, 1), a).scale(3.8));
                        level.sendParticles(ParticleTypes.ENCHANT, p.x, p.y + 1.6, p.z, 3, 0.3, 0.3, 0.3, 0.4);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.BOOK_PUT, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .build());
        // lance: the staff levelled (0.8 s, the line drawn in stardust), then he streaks along it in 6 ticks: 15 to
        // whoever stands in his path
        out.add(BossAttack.of("lance").anim(LANCE).timing(16, 10, 16).range(6.0, 20.0).cooldown(110).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        Vec3 to = lanceEnd(t);
                        double len = flatDist(b.position(), to);
                        for (double d = 1.0; d < len; d += 1.0) {
                            Vec3 p = b.position().lerp(to, d / len);
                            level.sendParticles(STARDUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 3) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    lanceFrom = b.position();
                    lanceTo = landingSpot(level, lanceEnd(t));
                    faceToward(lanceTo);
                    level.playSound(null, b, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> lanceStep(level, tick))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.0 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "staff");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // page storm: both arms flung up, the books torn open (1.2 s); for 8.5 s the crater fills with whirling pages
        // (1.5 s of warning first): outside the moving golden circles you are blinded and cut (2 a second). He keeps
        // fighting meanwhile
        out.add(BossAttack.of("pagestorm").anim(PAGESTORM).phaseTwo().timing(24, 6, 14).range(0, 30.0).cooldown(460)
                .weight(6).track(false)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(PAGE, b.getX(), b.getY() + 4.0, b.getZ(), 6, 1.2, 1.0, 1.2, 0.05);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (tickCount >= stormUntil) {
                        stormUntil = tickCount + STORM_LIFE;
                        b.addEffect(pageStorm(level));
                    }
                    level.playSound(null, b, SoundEvents.ELYTRA_FLYING, SoundSource.HOSTILE, 2.0F, 1.4F);
                })
                .build());
        // constellation: he traces stars on the floor with the staff (1.0 s; six stars, at least one by every player,
        // joined by faint lines), then strikes: the lines burst one after another, 3 ticks apart (13 and a toss)
        out.add(BossAttack.of("constellation").anim(CONSTELLATION).phaseTwo().timing(20, 30, 14).range(0, 30.0)
                .cooldown(240).weight(7).track(false)
                .start((b, level, t, tick) -> planStars(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawStars(level, tick > 12);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.8F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        burstSegment(level, tick / 3);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // invert: he rises off the floor, robe hanging upward (2.0 s, invulnerable; dust streams up off the floor),
        // then the crater's gravity flips: a ring of force (12, jump it), +12% speed, the pulses and the blinks start
        out.add(BossAttack.of("invert").anim(INVERT).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.END_PORTAL_SPAWN, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    Vec3 c = centre();
                    double r = reach();
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, c.x, c.y + 0.3, c.z, 12, r * 0.5, 0.1, r * 0.5, 0.02);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.3, VIOLET);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.HOSTILE, 3.0F, 0.4F + tick * 0.01F);
                    }
                })
                .impact((b, level, t, tick) -> invert(level))
                .build());
        // blink: he folds into starlight (0.7 s; a pillar of light rises over the crystal node he is going to), and
        // appears there; the star-lance always follows
        out.add(BossAttack.of("blink").anim(BLINK).phaseTwo().timing(14, 4, 6).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> pickNextNode(level, t))
                .windup((b, level, t, tick) -> {
                    Vec3 to = nodeNext >= 0 ? nodes().get(nodeNext) : null;
                    if (to != null && tick % 2 == 0) {
                        b.telegraphRing(level, to, 1.5, STARDUST);
                        level.sendParticles(ParticleTypes.END_ROD, to.x, to.y + 1 + (tick % 7) * 0.8, to.z, 3, 0.2, 0.4, 0.2, 0.01);
                    }
                    level.sendParticles(ParticleTypes.PORTAL, b.getX(), b.getY() + 2.5, b.getZ(), 6, 0.5, 1.5, 0.5, 0.3);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CHORUS_FRUIT_TELEPORT, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> blinkToNode(level, t))
                .end((b, level, t, tick) -> b.chain(level, "starlance"))
                .build());
        // star-lance: from the node, the astrolabe aimed across the crater (0.9 s; the line drawn to the far wall,
        // turning with you for the first 0.5 s, then locked): a beam of starlight, 16 to everyone on it, even afloat
        out.add(BossAttack.of("starlance").anim(STARLANCE).phaseTwo().timing(18, 6, 18).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick < 10) {
                        turnToward(t, 14.0F);
                    }
                    if (tick % 2 == 0) {
                        double len = beamLength();
                        for (double d = 1.5; d <= len; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(tick < 10 ? STARDUST : VIOLET, p.x, p.y + 0.15, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> fireBeam(level))
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void staffCut(ServerLevel level, float damage) {
        hitArc(level, STAFF_RANGE, STAFF_HALF, damage, 1.0);
        for (double a = -STAFF_HALF; a <= STAFF_HALF; a += 12) {
            Vec3 p = position().add(rotate(forward(), a).scale(STAFF_RANGE - 1.0));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 1.6, p.z, 1, 0.1, 0.2, 0.1, 0.01);
        }
        Vec3 c = ahead(3.0);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.6, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.0F, 0.8F);
    }

    /** Tomes: 3 at the target (phase 2: 2 at every player, up to 4 players, plus strays at the target). */
    private void launchTomes(ServerLevel level, @Nullable LivingEntity target) {
        List<LivingEntity> aims = new ArrayList<>();
        if (phase() == 2) {
            for (Player p : fighters(level)) {
                if (aims.size() < 8) {
                    aims.add(p);
                    aims.add(p);
                }
            }
            for (int i = 0; i < scaledCount(1) && target != null; i++) {
                aims.add(target);
            }
        } else if (target != null) {
            for (int i = 0; i < 3; i++) {
                aims.add(target);
            }
        }
        float damage = phase() == 2 ? 6.0F : 7.0F;
        for (int i = 0; i < aims.size(); i++) {
            double ang = Math.toRadians(getYRot() + 90 + (i - (aims.size() - 1) / 2.0) * 30);
            Tome tome = new Tome(level, this, aims.get(i), damage);
            tome.snapTo(getX() + Math.cos(ang) * 1.6, getY() + 3.3 + (i % 2) * 0.6, getZ() + Math.sin(ang) * 1.6, 0, 0);
            level.addFreshEntity(tome);
            level.sendParticles(ParticleTypes.ENCHANT, tome.getX(), tome.getY(), tome.getZ(), 8, 0.2, 0.2, 0.2, 0.3);
        }
        level.playSound(null, this, SoundEvents.SHULKER_SHOOT, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 2.5F, 1.2F);
    }

    /** The gravity well: a pull every other tick for 30 ticks (the core ring flashing faster), then the implosion. */
    private void wellStep(ServerLevel level, int tick) {
        Vec3 c = position();
        if (tick < 30) {
            if (tick % 2 == 0) {
                for (Player p : fighters(level)) {
                    Vec3 in = c.subtract(p.position()).multiply(1, 0, 1);
                    double d = in.length();
                    if (d > 1.8 && d < 15.0 && Math.abs(p.getY() - c.y) < 4.0) {
                        Vec3 v = in.normalize().scale(0.11 + 0.05 * (1.0 - d / 15.0));
                        p.setDeltaMovement(v.x, Math.min(0.0, p.getDeltaMovement().y), v.z);
                        p.hurtMarked = true;
                    }
                }
                for (int k = 0; k < 8; k++) {
                    double ang = getRandom().nextDouble() * Math.PI * 2;
                    double d = 3 + getRandom().nextDouble() * 12;
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, c.x + Math.cos(ang) * d, c.y + 0.5, c.z + Math.sin(ang) * d,
                            1, 0.0, 0.1, 0.0, 0.02);
                }
            }
            if (tick % (tick < 20 ? 4 : 2) == 0) {
                telegraphRing(level, c, WELL_CORE, tick < 20 ? VIOLET : EMBER);
            }
            if (tick % 10 == 0) {
                level.playSound(null, this, SoundEvents.PORTAL_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.02F);
            }
        } else if (tick == 30) {
            hitCircle(level, c, WELL_CORE, 15.0F, 1.2, 0.4);
            if (phase() == 2) {
                addEffect(WayfarerBoss.wave(c, 10, 0.5, 8.0F, VIOLET));
            }
            level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 1, c.z, 3, 1.0, 0.4, 1.0, 0);
            level.sendParticles(ParticleTypes.END_ROD, c.x, c.y + 1, c.z, 40, 1.2, 0.6, 1.2, 0.2);
            level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
            level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
        }
    }

    private void starVolley(ServerLevel level, @Nullable LivingEntity target) {
        int k = 0;
        for (Player p : fighters(level)) {
            if (k++ >= 4) {
                break;
            }
            addEffect(starShard(p, null, 14, 16, 2.5, 14.0F));
        }
        if (k == 0 && target != null) {
            addEffect(starShard(target, null, 14, 16, 2.5, 14.0F));
        }
        for (int i = 0; i < scaledCount(2); i++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * Math.max(2, reach() - 3);
            addEffect(starShard(null, centre().add(Math.cos(a) * d, 0, Math.sin(a) * d), 14, 16, 2.5, 14.0F));
        }
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** A star-shard: a ring follows {@code follow} for {@code track} ticks, locks, the shard falls for {@code lock}. */
    private Effect starShard(@Nullable LivingEntity follow, @Nullable Vec3 fixed, int track, int lock, double r, float damage) {
        int[] t = {0};
        Vec3[] at = {fixed};
        return (boss, level) -> {
            int k = t[0]++;
            if (follow != null && k < track && follow.isAlive() && boss instanceof StarCurator c) {
                at[0] = c.clampToArena(follow.position(), 0.5);
            }
            if (at[0] == null) {
                return true;
            }
            Vec3 p = at[0];
            if (k < track + lock) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, p, r, k < track ? STARDUST : EMBER);
                }
                if (k >= track) {
                    double h = 13.0 * (1.0 - (k - track) / (double) lock);
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + h, p.z, 2, 0.1, 0.1, 0.1, 0);
                    level.sendParticles(EMBER, p.x, p.y + h + 0.6, p.z, 2, 0.15, 0.3, 0.15, 0);
                }
                return false;
            }
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState()),
                    p.x, p.y + 0.4, p.z, 30, r * 0.4, 0.4, r * 0.4, 0.1);
            level.sendParticles(ParticleTypes.FIREWORK, p.x, p.y + 0.6, p.z, 16, r * 0.3, 0.3, r * 0.3, 0.08);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 2.5F, 0.6F);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.2F);
            for (LivingEntity e : boss.victims(level, p, r + 1)) {
                if (flatDist(e.position(), p) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - p.y) < 3.0) {
                    boss.strike(level, e, damage, 0.3, 0.3);
                }
            }
            return true;
        };
    }

    private Vec3 lanceEnd(@Nullable LivingEntity t) {
        Vec3 fwd = forward();
        double len = t != null ? Math.min(14.0, flatDist(position(), t.position()) + 3.0) : 10.0;
        return clampToArena(position().add(fwd.scale(len)), 1.5);
    }

    private void lanceStep(ServerLevel level, int tick) {
        if (lanceFrom == null || lanceTo == null) {
            return;
        }
        if (tick <= 6) {
            Vec3 p = lanceFrom.lerp(lanceTo, tick / 6.0);
            teleportTo(p.x, lanceTo.y, p.z);
            setDeltaMovement(Vec3.ZERO);
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2.5, getZ(), 6, 0.4, 1.0, 0.4, 0.02);
            level.sendParticles(STARDUST, getX(), getY() + 1.0, getZ(), 4, 0.4, 0.5, 0.4, 0.0);
            for (LivingEntity e : victims(level, position(), 3.0)) {
                if (flatDist(e.position(), position()) <= 1.6 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                    strike(level, e, 15.0F, 0.8, 0.3);
                }
            }
        }
        if (tick == 6) {
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.5F);
        }
    }

    /**
     * The page storm: 1.5 s of warning (the safe circles shown), then 7 s of storm. Safe circles: one per player (2 to
     * 4), radius 3, wheeling slowly round the centre. Outside them a player is blinded (refreshed) and takes 2 a second.
     */
    private Effect pageStorm(ServerLevel level0) {
        int[] t = {0};
        int n = Math.max(2, Math.min(4, fighters(level0).size()));
        double start = getRandom().nextDouble() * Math.PI * 2;
        return (boss, level) -> {
            if (!(boss instanceof StarCurator c)) {
                return true;
            }
            int k = t[0]++;
            double path = Math.max(3.0, Math.min(9.0, c.reach() - 4.0));
            List<Vec3> safe = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                double a = start + i * Math.PI * 2 / n + k * 0.016;
                safe.add(c.centre().add(Math.cos(a) * path, 0, Math.sin(a) * path));
            }
            if (k % 2 == 0) {
                for (Vec3 s : safe) {
                    boss.telegraphRing(level, s, SAFE_R, GOLD);
                    level.sendParticles(ParticleTypes.END_ROD, s.x, s.y + 0.3, s.z, 1, 0.3, 0.1, 0.3, 0.0);
                }
            }
            if (k >= STORM_GRACE) {
                double r = c.reach();
                for (int i = 0; i < 10; i++) {
                    double a = boss.getRandom().nextDouble() * Math.PI * 2;
                    double d = Math.sqrt(boss.getRandom().nextDouble()) * r;
                    Vec3 p = c.centre().add(Math.cos(a) * d, 1 + boss.getRandom().nextDouble() * 3, Math.sin(a) * d);
                    boolean inSafe = false;
                    for (Vec3 s : safe) {
                        inSafe |= flatDist(p, s) < SAFE_R;
                    }
                    if (!inSafe) {
                        level.sendParticles(PAGE, p.x, p.y, p.z, 1, 0.3, 0.3, 0.3, 0.05);
                        level.sendParticles(ParticleTypes.ENCHANT, p.x, p.y, p.z, 1, 0.3, 0.3, 0.3, 0.3);
                    }
                }
                if (k % 10 == 0) {
                    for (Player p : c.fighters(level)) {
                        boolean inside = false;
                        for (Vec3 s : safe) {
                            inside |= flatDist(p.position(), s) <= SAFE_R + p.getBbWidth() / 2;
                        }
                        if (!inside) {
                            p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0), boss);
                            if (k % 20 == 0) {
                                p.hurtServer(level, boss.damageSources().mobAttack(boss), 2.0F);
                                level.sendParticles(PAGE, p.getX(), p.getY() + 1.2, p.getZ(), 6, 0.3, 0.5, 0.3, 0.05);
                            }
                        }
                    }
                }
                if (k % 30 == 0) {
                    level.playSound(null, c.centre().x, c.centre().y, c.centre().z, SoundEvents.BOOK_PAGE_TURN,
                            SoundSource.HOSTILE, 3.0F, 0.5F);
                }
            } else if (k == 0) {
                level.playSound(null, boss, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 3.0F, 1.2F);
            }
            return k >= STORM_LIFE || boss.phase() == 1;
        };
    }

    /** Six stars: one near each player (up to 4), the rest scattered; joined nearest-first from the first one. */
    private void planStars(ServerLevel level, @Nullable LivingEntity target) {
        stars.clear();
        List<Vec3> pool = new ArrayList<>();
        for (Player p : fighters(level)) {
            if (pool.size() < 4) {
                double a = getRandom().nextDouble() * Math.PI * 2;
                pool.add(clampToArena(p.position().add(Math.cos(a) * 1.5, 0, Math.sin(a) * 1.5), 1.0));
            }
        }
        if (pool.isEmpty() && target != null) {
            pool.add(clampToArena(target.position(), 1.0));
        }
        for (int tries = 0; pool.size() < 6 && tries < 40; tries++) {
            double a = getRandom().nextDouble() * Math.PI * 2;
            double d = 2 + getRandom().nextDouble() * (reach() - 3);
            Vec3 p = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
            boolean ok = true;
            for (Vec3 s : pool) {
                ok &= flatDist(s, p) > 4.0;
            }
            if (ok) {
                pool.add(p);
            }
        }
        Vec3 cur = pool.remove(0);
        stars.add(cur);
        while (!pool.isEmpty()) {
            Vec3 best = pool.get(0);
            for (Vec3 s : pool) {
                if (flatDist(s, cur) < flatDist(best, cur)) {
                    best = s;
                }
            }
            pool.remove(best);
            stars.add(best);
            cur = best;
        }
    }

    private void drawStars(ServerLevel level, boolean late) {
        for (int i = 0; i < stars.size(); i++) {
            Vec3 s = stars.get(i);
            level.sendParticles(ParticleTypes.END_ROD, s.x, s.y + 0.3, s.z, 1, 0.1, 0.1, 0.1, 0.0);
            if (i + 1 < stars.size()) {
                Vec3 e = stars.get(i + 1);
                double len = flatDist(s, e);
                for (double d = 0.5; d < len; d += 0.8) {
                    Vec3 p = s.lerp(e, d / len);
                    level.sendParticles(late ? VIOLET : STARDUST, p.x, p.y + 0.15, p.z, 1, 0.03, 0, 0.03, 0);
                }
            }
        }
    }

    private void burstSegment(ServerLevel level, int i) {
        if (i + 1 >= stars.size()) {
            return;
        }
        Vec3 s = stars.get(i);
        Vec3 e = stars.get(i + 1);
        double len = Math.max(0.1, flatDist(s, e));
        Vec3 dir = e.subtract(s).multiply(1, 0, 1).scale(1.0 / len);
        for (double d = 0; d <= len; d += 0.6) {
            Vec3 p = s.add(dir.scale(d));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.4, p.z, 2, 0.1, 0.5, 0.1, 0.05);
            level.sendParticles(VIOLET, p.x, p.y + 0.8, p.z, 1, 0.1, 0.4, 0.1, 0.0);
        }
        level.sendParticles(ParticleTypes.FIREWORK, e.x, e.y + 0.6, e.z, 12, 0.3, 0.3, 0.3, 0.1);
        level.playSound(null, e.x, e.y, e.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.5F, 0.7F + i * 0.1F);
        for (LivingEntity v : victims(level, s.lerp(e, 0.5), len / 2 + 2)) {
            Vec3 to = v.position().subtract(s).multiply(1, 0, 1);
            double along = Mth.clamp(to.dot(dir), 0, len);
            double side = to.subtract(dir.scale(along)).length();
            if (side <= 1.0 + v.getBbWidth() / 2 && Math.abs(v.getY() - s.y) < 2.5) {
                strike(level, v, 13.0F, 0.0, 0.5);
            }
        }
    }

    // ------------------------------------------------------------------ phase 3: the inverted crater, the nodes

    /**
     * The meteorite's crystal nodes: the amethyst crowns of the starlight braziers round the crater (found at runtime,
     * so a rotated piece still works), each turned into a standing spot 2.5 blocks toward the centre; or four points on
     * the diagonals when there are none (the demo spawn).
     */
    private List<Vec3> nodes() {
        if (nodes != null) {
            return nodes;
        }
        List<Vec3> found = new ArrayList<>();
        if (level() instanceof ServerLevel level) {
            BlockPos base = BlockPos.containing(centre());
            int r = radius + 3;
            BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    if (dx * dx + dz * dz > r * r) {
                        continue;
                    }
                    for (int dy = 1; dy <= 3; dy++) {
                        p.set(base.getX() + dx, base.getY() + dy, base.getZ() + dz);
                        if (!level.getBlockState(p).is(Blocks.AMETHYST_CLUSTER)
                                || level.getBlockState(p.below()).getCollisionShape(level, p.below()).isEmpty()) {
                            continue;
                        }
                        Vec3 crystal = Vec3.atBottomCenterOf(p);
                        Vec3 in = centre().subtract(crystal).multiply(1, 0, 1);
                        if (in.lengthSqr() < 4.0) {
                            continue;
                        }
                        Vec3 stand = null;
                        for (double step = 2.5; step <= 5.0 && stand == null; step += 1.0) {
                            Vec3 q = crystal.add(in.normalize().scale(step));
                            stand = safeSpot(level, q.x, q.z);
                        }
                        boolean dup = false;
                        for (Vec3 f : found) {
                            dup |= stand != null && flatDist(f, stand) < 3.0;
                        }
                        if (stand != null && !dup) {
                            found.add(stand);
                        }
                    }
                }
            }
            if (found.size() < 3) {
                found.clear();
                for (int k = 0; k < 4; k++) {
                    double a = Math.toRadians(45 + 90 * k);
                    double d = reach() * 0.75;
                    Vec3 want = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
                    Vec3 s = safeSpot(level, want.x, want.z);
                    found.add(s != null ? s : landingSpot(level, want));
                }
            }
        }
        if (found.isEmpty()) {
            found.add(centre());
        }
        nodes = found;
        return nodes;
    }

    private void invert(ServerLevel level) {
        inverted = true;
        pulseTimer = 50;
        blinkTimer = 70;
        addEffect(WayfarerBoss.wave(position(), 13, 0.55, 12.0F, VIOLET));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("star_curator_inverted"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 c = centre();
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, c.x, c.y + 0.5, c.z, 200, reach() * 0.5, 0.3, reach() * 0.5, 0.05);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 4, getZ(), 60, 1.5, 1.5, 1.5, 0.1);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.4F);
        nodes();
    }

    /** The node he stands at (within 3 blocks), or -1. */
    private int currentNode() {
        List<Vec3> ns = nodes();
        for (int i = 0; i < ns.size(); i++) {
            if (flatDist(ns.get(i), position()) < 3.0) {
                return i;
            }
        }
        return -1;
    }

    /** Another node: one with a player within 12 blocks of it when possible (he hunts), never the one he is at. */
    private void pickNextNode(ServerLevel level, @Nullable LivingEntity target) {
        List<Vec3> ns = nodes();
        int at = currentNode();
        List<Integer> near = new ArrayList<>();
        List<Integer> any = new ArrayList<>();
        for (int i = 0; i < ns.size(); i++) {
            if (i == at) {
                continue;
            }
            any.add(i);
            if (target != null && flatDist(ns.get(i), target.position()) < 12.0) {
                near.add(i);
            }
        }
        List<Integer> from = near.isEmpty() ? any : near;
        nodeNext = from.isEmpty() ? -1 : from.get(getRandom().nextInt(from.size()));
    }

    private void blinkToNode(ServerLevel level, @Nullable LivingEntity target) {
        if (nodeNext < 0) {
            return;
        }
        Vec3 to = nodes().get(nodeNext);
        level.sendParticles(ParticleTypes.PORTAL, getX(), getY() + 2.5, getZ(), 40, 0.5, 1.5, 0.5, 0.5);
        teleportTo(to.x, to.y, to.z);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
        nodeAt = nodeNext;
        if (target != null) {
            faceToward(target.position());
        } else {
            faceToward(centre());
        }
        level.sendParticles(ParticleTypes.END_ROD, to.x, to.y + 2.5, to.z, 40, 0.5, 1.5, 0.5, 0.1);
        level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private double beamLength() {
        return Math.max(8.0, Math.min(30.0, reach() * 2 + 1));
    }

    private void fireBeam(ServerLevel level) {
        double len = beamLength();
        hitLine(level, len, 1.3, 16.0F, 0.6);
        for (double d = 1.0; d <= len; d += 0.5) {
            Vec3 p = ahead(d);
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 1.2, p.z, 2, 0.15, 0.6, 0.15, 0.01);
            if (((int) (d * 2)) % 6 == 0) {
                level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y + 1.5, p.z, 1, 0, 0, 0, 0);
            }
        }
        level.playSound(null, this, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3.0F, 1.3F);
    }

    /**
     * A gravity pulse: 1.5 s of warning (dust rises off the floor; golden anchor rings round every node he is not at),
     * then every player outside the anchors who stands on floor with headroom is lifted (Levitation II for 26 ticks,
     * 4), held over the floor (drawn toward the centre while near the wall) and gets Slow Falling when it ends.
     */
    private Effect gravityPulse() {
        int[] t = {0};
        Set<UUID> afloat = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof StarCurator c)) {
                return true;
            }
            int k = t[0]++;
            List<Vec3> ns = c.nodes();
            int at = c.currentNode();
            if (k < 30) {
                if (k % 2 == 0) {
                    Vec3 ce = c.centre();
                    double r = c.reach();
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, ce.x, ce.y + 0.2, ce.z, 14, r * 0.55, 0.05, r * 0.55, 0.03);
                    for (int i = 0; i < ns.size(); i++) {
                        if (i != at) {
                            boss.telegraphRing(level, ns.get(i), ANCHOR_R, GOLD);
                        }
                    }
                }
                if (k == 0) {
                    level.playSound(null, boss, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.HOSTILE, 3.0F, 0.5F);
                }
                if (k == 20) {
                    level.playSound(null, boss, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 1.5F);
                }
                return false;
            }
            if (k == 30) {
                level.playSound(null, boss, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
                for (Player p : c.fighters(level)) {
                    boolean anchored = false;
                    for (int i = 0; i < ns.size(); i++) {
                        anchored |= i != at && flatDist(p.position(), ns.get(i)) <= ANCHOR_R + p.getBbWidth() / 2;
                    }
                    if (anchored) {
                        level.sendParticles(GOLD, p.getX(), p.getY() + 0.3, p.getZ(), 10, 0.4, 0.1, 0.4, 0.0);
                        continue;
                    }
                    double fy = floorY(level, p.getX(), p.getY(), p.getZ());
                    if (Double.isNaN(fy) || p.getY() - fy > 1.5 || headroom(level, p.position(), 6) < 6) {
                        continue;                       // never lift anyone who is not on floor with room above
                    }
                    p.hurtServer(level, boss.damageSources().mobAttack(boss), 4.0F);
                    p.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 26, 1), boss);
                    afloat.add(p.getUUID());
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.getX(), p.getY() + 0.5, p.getZ(), 20, 0.3, 0.6, 0.3, 0.05);
                }
                return afloat.isEmpty();
            }
            if (k % 2 == 0) {
                for (Player p : c.fighters(level)) {
                    if (!afloat.contains(p.getUUID())) {
                        continue;
                    }
                    level.sendParticles(STARDUST, p.getX(), p.getY(), p.getZ(), 2, 0.3, 0.1, 0.3, 0.0);
                    Vec3 off = p.position().subtract(c.centre()).multiply(1, 0, 1);
                    if (off.length() > c.reach() - 3.0) {
                        Vec3 v = off.normalize().scale(-0.15);
                        p.setDeltaMovement(v.x, p.getDeltaMovement().y, v.z);
                        p.hurtMarked = true;
                    }
                }
            }
            if (k >= 56) {
                releaseFloaters(level, afloat);
                return true;
            }
            return false;
        };
    }

    /** Ends a lift: no Levitation left, Slow Falling to land softly. */
    private void releaseFloaters(ServerLevel level, @Nullable Set<UUID> only) {
        for (Player p : fighters(level)) {
            if (only != null && !only.contains(p.getUUID())) {
                continue;
            }
            if (only == null && !p.hasEffect(MobEffects.LEVITATION)) {
                continue;
            }
            p.removeEffect(MobEffects.LEVITATION);
            p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0), this);
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3, getZ(), 6, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (guard > 0) {
            guard--;
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (phase() == 1 && (inverted || stormUntil > 0)) {      // the fight was reset
            inverted = false;
            roarUntil = -1;
            stormUntil = -1;
            nodeAt = -1;
            releaseFloaters(level, null);
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("star_curator_inverted"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("star_curator_wrath"));
            }
        }
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!inverted && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "invert");
            } else if (inverted && --blinkTimer <= 0) {
                blinkTimer = Math.max(60, (int) Math.round(BLINK_EVERY * cooldownScale()));
                chain(level, "blink");
            }
        }
        if (inverted && phase() == 2 && fighting && !isStaggered() && --pulseTimer <= 0) {
            pulseTimer = Math.max(90, (int) Math.round(PULSE_EVERY * cooldownScale())) + 30;
            addEffect(gravityPulse());
        }
        // ambience: the starfield breathing through the cracks, the orbiting pages, motes over the nodes in phase 3
        if (tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.ENCHANT, getX(), getY() + 3.4, getZ(), 2, 1.2, 0.3, 1.2, 0.3);
        }
        if (tickCount % 8 == 0) {
            level.sendParticles(STARDUST, getX(), getY() + 5.0, getZ(), 1, 0.3, 0.3, 0.3, 0.0);
        }
        if (inverted && tickCount % 10 == 0) {
            for (Vec3 n : nodes()) {
                level.sendParticles(ParticleTypes.END_ROD, n.x, n.y + 0.5 + getRandom().nextDouble() * 3, n.z, 1, 0.2, 0.2, 0.2, 0.0);
            }
        }
        if (tickCount % 140 == 0) {
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("star_curator_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 5, getZ(), 80, 1.5, 1.0, 1.5, 0.1);
        level.sendParticles(PAGE, getX(), getY() + 3.5, getZ(), 60, 2.5, 1.0, 2.5, 0.05);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        releaseFloaters(level, null);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 4, getZ(), 150, 1.5, 2.0, 1.5, 0.1);
        level.sendParticles(PAGE, getX(), getY() + 3, getZ(), 120, 2.0, 2.0, 2.0, 0.05);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            releaseFloaters(level, null);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("CuratorCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("CuratorRadius", radius);
        output.putBoolean("CuratorInverted", inverted);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("CuratorCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("CuratorRadius", 16);
        inverted = input.getBooleanOr("CuratorInverted", false) && phase() == 2;
        nodes = null;
    }

    // ------------------------------------------------------------------ the tomes

    /**
     * A flying tome: a shulker bullet underneath (it drifts after its target, and any hit or arrow shoots it down),
     * dressed in enchanting glyphs. It deals the Curator's damage instead of the bullet's levitation, never hits him
     * or another tome, crumbles after 8 s and is never saved.
     */
    static final class Tome extends ShulkerBullet {
        private final float damage;

        Tome(Level level, StarCurator owner, Entity target, float damage) {
            super(level, owner, target, Direction.Axis.Y);
            this.damage = damage;
        }

        @Override
        public void tick() {
            super.tick();
            if (level() instanceof ServerLevel level) {
                if (tickCount % 2 == 0) {
                    level.sendParticles(ParticleTypes.ENCHANT, getX(), getY(), getZ(), 2, 0.15, 0.15, 0.15, 0.2);
                    level.sendParticles(PAGE, getX(), getY(), getZ(), 1, 0.1, 0.1, 0.1, 0.0);
                }
                if (tickCount > 160) {
                    level.sendParticles(PAGE, getX(), getY(), getZ(), 8, 0.2, 0.2, 0.2, 0.05);
                    discard();
                }
            }
        }

        @Override
        protected boolean canHitEntity(Entity entity) {
            return super.canHitEntity(entity) && !(entity instanceof WayfarerBoss)
                    && !entity.entityTags().contains(MINION_TAG);
        }

        @Override
        protected void onHitEntity(EntityHitResult hit) {
            if (!(level() instanceof ServerLevel level) || !(hit.getEntity() instanceof LivingEntity e)) {
                return;
            }
            if (getOwner() instanceof StarCurator c && c.isAlive()) {
                c.strike(level, e, damage, 0.3, 0.05);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 0), c);
            } else {
                e.hurtServer(level, damageSources().magic(), damage * 0.5F);
            }
            level.sendParticles(PAGE, e.getX(), e.getY() + 1.2, e.getZ(), 10, 0.3, 0.4, 0.3, 0.05);
            level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.BOOK_PUT, SoundSource.HOSTILE, 1.5F, 0.6F);
        }

        @Override
        public boolean shouldBeSaved() {
            return false;
        }
    }
}
