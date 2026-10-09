package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
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

import static com.brasshaven.generated.MobAnims.SoulStoker.CHARGE;
import static com.brasshaven.generated.MobAnims.SoulStoker.OVERPRESSURE;
import static com.brasshaven.generated.MobAnims.SoulStoker.PISTON;
import static com.brasshaven.generated.MobAnims.SoulStoker.RINGBLAST;
import static com.brasshaven.generated.MobAnims.SoulStoker.ROAR;
import static com.brasshaven.generated.MobAnims.SoulStoker.SHOVEL;
import static com.brasshaven.generated.MobAnims.SoulStoker.STAGGER;
import static com.brasshaven.generated.MobAnims.SoulStoker.STOKE;
import static com.brasshaven.generated.MobAnims.SoulStoker.THRALLS;
import static com.brasshaven.generated.MobAnims.SoulStoker.VENTS;

/**
 * Le Chauffeur des âmes (The Soul Stoker), the champion of the Soul Engine: a hulking furnace-man about 4 blocks tall,
 * a blackstone and brass boiler for a torso with a grated firebox burning blue soul fire, a furnace-door helmet with a
 * skull face, chimneys venting blue flame on his back, bone chains of soul lanterns at his belt; his right arm ends in
 * a giant coal shovel, his left in a piston-driven fist. He waits on the crankshaft deck of the engine (39 x 39 under
 * the crankcase roof; the railing over the crank trench on the north side).
 * <ul>
 *     <li>Phase 1: the <b>shovel</b> sweep (an arc, then the embers it flings land on marked rings ahead), the
 *     <b>piston</b> punch (a long wind-up, then the fist and a shockwave down a drawn line), the <b>stoke</b> (three
 *     shovelfuls of souls into his firebox, a pressure gauge climbing over his head, then a cone of blue flame) and the
 *     <b>vents</b> (soul-fire vents marked on the deck erupt one after another, one under you).</li>
 *     <li>Phase 2 (a roar at 65%): faster, the <b>charge</b> down a drawn lane, the <b>thralls</b> (wither skeletons
 *     out of his firebox), more embers and vents, the punch chains into the sweep.</li>
 *     <li>Phase 3 (at 30%, driven by this class like the Chained Jailer): <b>overpressure</b>. The safety valves blow
 *     once (a wave, jump it), then the deck takes up the engine's crank rhythm: strips across the deck (along the
 *     crankshaft) burn in alternation every 3 s, each pulse drawn 2 s ahead; and every 11 s a <b>ring blast</b>: three
 *     rings of blue flame roll out of him, each with a gap, the gaps turning a little each ring (drawn first). The crank
 *     rhythm pauses during the ring blasts.</li>
 * </ul>
 * He places no blocks. Pushes are capped and never thrown outward near the deck's rim or over a drop (the trench).
 */
public class SoulStoker extends WayfarerBoss {
    public static final float WIDTH = 2.2F;
    public static final float HEIGHT = 4.0F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_RANGE = 5.5;
    private static final double SWEEP_HALF = 75;
    private static final double LINE_LEN = 14.0;
    private static final double LINE_HALF = 1.3;
    private static final double CONE_HALF = 32;
    private static final double VENT_R = 2.0;
    private static final double EMBER_R = 1.7;
    private static final double LANE_HALF = 1.4;
    private static final double STRIP = 4.0;
    private static final int CRANK_PERIOD = 60;
    private static final int CRANK_WARN = 40;
    private static final int CRANK_BURN = 6;
    private static final double GAP_HALF = 26;
    private static final int RING_EVERY = 220;
    private static final DustParticleOptions SOUL = new DustParticleOptions(0x46D2F0, 1.4F);
    private static final DustParticleOptions SOUL_BIG = new DustParticleOptions(0x3CC8F0, 2.4F);
    private static final DustParticleOptions RED = new DustParticleOptions(0xE03A2A, 1.4F);
    private static final DustParticleOptions BRASS = new DustParticleOptions(0xE0B050, 1.3F);
    private static final DustParticleOptions BONE = new DustParticleOptions(0xE6DCC0, 1.2F);

    private @Nullable Vec3 centre;
    private int radius = 18;
    /** Phase 3 has started (the safety valves blew). */
    private boolean overpressured;
    private int guard;
    private int roarUntil = -1;
    private int ringTimer = 100;
    private int crankTick;
    private int crankCount;
    private final Set<UUID> crankHit = new HashSet<>();
    private final List<Vec3> embers = new ArrayList<>();
    private final List<Vec3> vents = new ArrayList<>();
    private final List<Double> gaps = new ArrayList<>();
    private @Nullable Vec3 laneDir;
    private double laneLen;
    private double charged;
    private final Set<UUID> chargeHit = new HashSet<>();

    public SoulStoker(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 620.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SoulStoker.TICKS;
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
    public boolean fireImmune() {
        return true;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory (a square deck)

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

    /** Half width of the usable deck round the seal (the deck is 39 across, walls and the trench railing round it). */
    private double reach() {
        return Math.max(6.0, Math.min(17.0, radius - 1.0));
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Distance from the centre in the deck's square metric. */
    private double cheb(Vec3 p) {
        return Math.max(Math.abs(p.x - centre().x), Math.abs(p.z - centre().z));
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

    /** A standing spot on the deck at (x, z), level with the seal, with room for him above; or null. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 0.6) {
            return null;
        }
        return headroom(level, new Vec3(x, y, z), 5) >= 5 ? new Vec3(x, y, z) : null;
    }

    private Vec3 clampToArena(Vec3 p, double margin) {
        Vec3 c = centre();
        double max = Math.max(2.0, reach() - margin);
        return new Vec3(c.x + Mth.clamp(p.x - c.x, -max, max), c.y, c.z + Mth.clamp(p.z - c.z, -max, max));
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

    /** Removes the outward part of {@code push} for someone near the deck's rim (square), all of it over a drop. */
    private Vec3 safePush(ServerLevel level, LivingEntity e, Vec3 push) {
        if (push.lengthSqr() < 1.0E-6) {
            return push;
        }
        Vec3 c = centre();
        double dx = e.getX() - c.x;
        double dz = e.getZ() - c.z;
        double edge = reach() - 3.0;
        double px = push.x;
        double pz = push.z;
        if (Math.abs(dx) > edge && px * dx > 0) {
            px = 0;
        }
        if (Math.abs(dz) > edge && pz * dz > 0) {
            pz = 0;
        }
        Vec3 probe = e.position().add(push.normalize().scale(2.0));
        double fy = floorY(level, probe.x, e.getY(), probe.z);
        if (Double.isNaN(fy) || fy < e.getY() - 2.5) {
            return Vec3.ZERO;
        }
        return new Vec3(px, 0, pz);
    }

    /** Pushes capped at 1.2 and lift at 0.6; near the rim or a drop the outward part is removed. */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage)) {
            return;
        }
        Vec3 push = Vec3.ZERO;
        if (knockback > 0) {
            push = e.position().subtract(position()).multiply(1, 0, 1);
            push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(Math.min(1.2, knockback));
            push = safePush(level, e, push);
        }
        lift = Math.min(lift, cheb(e.position()) > reach() - 3.0 ? 0.25 : 0.6);
        if (push.lengthSqr() > 1.0E-6 || lift > 0) {
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    /** A strike that also sets the victim ablaze with soul fire for {@code fireSeconds}. */
    private void burn(ServerLevel level, LivingEntity e, float damage, double knockback, double lift, float fireSeconds) {
        strike(level, e, damage, knockback, lift);
        if (fireSeconds > 0) {
            e.igniteForSeconds(fireSeconds);
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // shovel: the coal shovel drawn back across his body (0.8 s, the arc drawn in soul dust), swept round: 13 in the
        // arc; its embers fly out ahead and land on rings marked as they leave the scoop (0.9 s later: 8 in r 1.7, fire)
        out.add(BossAttack.of("shovel").anim(SHOVEL).timing(16, 20, 16).range(0, 7.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, SOUL);
                        b.telegraphArc(level, SWEEP_RANGE - 2.0, SWEEP_HALF, SOUL);
                    }
                    if (tick == 1) {
                        level.playSound(null, b, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    hitSweep(level);
                    flingEmbers(level);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, b.distanceTo(t) < 6.0 ? "piston" : "stoke");
                    }
                })
                .build());
        // piston: feet planted, the fist cocked far back, steam hissing out of the arm (1.4 s; the line drawn in soul
        // dust, it follows you slowly, then locks and turns red 0.5 s before), then the punch: 18 to whoever is within
        // 4 of the fist, and a shockwave runs on down the line to 14 (10 and a lift)
        out.add(BossAttack.of("piston").anim(PISTON).timing(28, 12, 18).range(0, 14.0).cooldown(90).weight(9)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 18) {
                        turnToward(t, 5.0F);
                    }
                    if (tick % 2 == 0) {
                        drawLine(level, LINE_LEN, LINE_HALF, tick < 18 ? SOUL : RED);
                    }
                    Vec3 fist = fistPos();
                    level.sendParticles(ParticleTypes.CLOUD, fist.x, fist.y, fist.z, 1, 0.2, 0.2, 0.2, 0.02);
                    if (tick % 7 == 0) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.6F + tick * 0.02F);
                    }
                    if (tick == 22) {
                        level.playSound(null, b, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, position(), 5.5)) {
                        Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
                        double along = to.dot(forward());
                        if (along >= 0 && along <= 4.0 && to.subtract(forward().scale(along)).length() <= 1.5 + e.getBbWidth() / 2) {
                            strike(level, e, 18.0F, 1.2, 0.3);
                        }
                    }
                    Vec3 f = ahead(2.5);
                    level.sendParticles(ParticleTypes.EXPLOSION, f.x, f.y + 1.5, f.z, 1, 0, 0, 0, 0);
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.7F);
                    b.addEffect(shockLine(position(), forward()));
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 6.5 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "shovel");
                    }
                })
                .build());
        // stoke: three shovelfuls of souls heaved into the firebox (0.3, 0.8, 1.3 s), a pressure gauge of dust climbing
        // over his head from blue to red; the cone (±32°, 11 deep, 13 in phase 2) is drawn from 0.6 s, follows you
        // slowly and locks red 0.6 s before he vents it at 2.0 s: 15 and soul fire 4 s
        out.add(BossAttack.of("stoke").anim(STOKE).timing(40, 16, 20).range(0, 12.0).cooldown(200).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (t != null) {
                        faceToward(t.position());
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick < 28) {
                        turnToward(t, 3.0F);
                    }
                    if (tick == 6 || tick == 16 || tick == 26) {
                        scoop(level);
                    }
                    drawGauge(level, tick / 40.0);
                    if (tick >= 12 && tick % 3 == 0) {
                        drawCone(level, coneRange(), tick < 28 ? SOUL : RED);
                    }
                    if (tick % 8 == 0) {
                        level.playSound(null, b, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    hitCone(level, coneRange(), 15.0F);
                    level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 12) {
                        ventCone(level, coneRange());
                    }
                })
                .build());
        // vents: the shovel raised high (1.0 s) and rammed into the deck. The vents are marked from the start (5, 7 in
        // phase 2, one under the target, phase 2 one under every player): rings of soul dust over rising smoke; they
        // crack open one after another from 0.3 s after the ram, every 0.25 s, each ring red for its last 0.5 s:
        // 12 in r 2 and soul fire 3 s
        out.add(BossAttack.of("vents").anim(VENTS).timing(20, 34, 14).range(0, 30.0).cooldown(220).weight(7)
                .track(false)
                .start((b, level, t, tick) -> planVents(level, t))
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 v : vents) {
                            b.telegraphRing(level, v, VENT_R, SOUL);
                            level.sendParticles(ParticleTypes.SMOKE, v.x, v.y + 0.2, v.z, 2, 0.5, 0.05, 0.5, 0.01);
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int k = 0; k < vents.size(); k++) {
                        b.addEffect(vent(vents.get(k), 6 + 5 * k));
                    }
                    Vec3 at = ahead(2.5);
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, at.x, at.y + 0.3, at.z, 20, 0.8, 0.2, 0.8, 0.05);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // charge: he hunches, chimneys roaring (1.2 s; a lane drawn from him through the target, up to 16 long, red
        // from 0.8 s), then runs down it like a runaway engine (1.1 blocks a tick, stopping at anything in his way):
        // 15 and a shove to whoever he meets (once each), and a slam (r 3, 8) where he stops
        out.add(BossAttack.of("charge").anim(CHARGE).phaseTwo().timing(24, 16, 16).range(6.0, 22.0).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> planCharge(t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawLane(level, tick < 16 ? SOUL : RED);
                    }
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, b.getX(), b.getY() + 4.2, b.getZ(), 2, 0.6, 0.2, 0.6, 0.02);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.5F, 0.4F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    charged = 0;
                    chargeHit.clear();
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> chargeStep(level))
                .build());
        // thralls: he throws his firebox open (1.0 s) and two wither skeletons (more in co-op) step out of the soul fire,
        // unless three of his thralls already stand on the deck
        out.add(BossAttack.of("thralls").anim(THRALLS).phaseTwo().timing(20, 10, 16).range(0, 30.0).cooldown(700).weight(4)
                .windup((b, level, t, tick) -> {
                    Vec3 m = firebox();
                    level.sendParticles(ParticleTypes.SOUL, m.x, m.y, m.z, 2, 0.4, 0.3, 0.4, 0.02);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.WITHER_SKELETON_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 m = firebox();
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, m.x, m.y, m.z, 40, 0.6, 0.6, 0.6, 0.08);
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    if (thrallCount(level) < 3) {
                        b.summon(level, EntityTypes.WITHER_SKELETON, 2, 3.0);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // overpressure: every gauge pegged, he clutches his boiler and shudders (2.0 s, guarded; the gauge climbs over
        // his head, steam jets from his seams), then the safety valves blow: a wave to 12 (10, jump it)
        out.add(BossAttack.of("overpressure").anim(OVERPRESSURE).phaseTwo().timing(40, 20, 20).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    guard = 64;
                    level.playSound(null, b, SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    drawGauge(level, tick / 40.0);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, SOUL);
                        double a = getRandom().nextDouble() * Math.PI * 2;
                        level.sendParticles(ParticleTypes.CLOUD, b.getX() + Math.cos(a) * 1.2, b.getY() + 2.0 + getRandom().nextDouble(),
                                b.getZ() + Math.sin(a) * 1.2, 0, Math.cos(a), 0.1, Math.sin(a), 0.3);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> overpressure(level))
                .build());
        // ring blast: he beats the shovel and the fist against his boiler (1.0 s; the three gaps drawn as lines from him
        // outward: the first in soul blue, then gold, then red), then the valves lift in turn at active 0, 12 and 24:
        // three rings of blue flame roll out over the deck, too tall to jump, each with one gap (±26°), the gaps turning
        // 25° the same way each ring: 10 and soul fire 3 s to whoever a ring catches outside its gap
        out.add(BossAttack.of("ringblast").anim(RINGBLAST).phaseTwo().timing(20, 40, 16).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> planGaps(t))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawGaps(level, 0);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 0.5F + tick * 0.02F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        drawGaps(level, tick / 12 + (tick % 12 == 0 ? 0 : 1));
                    }
                    if (tick % 12 == 0 && tick / 12 < gaps.size()) {
                        b.addEffect(flameRing(position(), gaps.get(tick / 12)));
                        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F + tick * 0.01F);
                        level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private double coneRange() {
        return phase() == 2 ? 13.0 : 11.0;
    }

    /** Roughly where the piston fist is (his left hand, at his side). */
    private Vec3 fistPos() {
        Vec3 f = forward();
        Vec3 left = new Vec3(f.z, 0, -f.x);
        return position().add(left.scale(-1.1)).add(f.scale(0.4)).add(0, 1.8, 0);
    }

    /** The firebox mouth in his belly. */
    private Vec3 firebox() {
        return position().add(forward().scale(0.9)).add(0, 2.2, 0);
    }

    private void hitSweep(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(SWEEP_HALF));
        for (LivingEntity e : victims(level, position(), SWEEP_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= SWEEP_RANGE + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                strike(level, e, 13.0F, 0.9, 0.3);
            }
        }
        for (double a = -SWEEP_HALF; a <= SWEEP_HALF; a += 10) {
            Vec3 p = position().add(rotate(fwd, a).scale(SWEEP_RANGE - 1.0));
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 1.2, p.z, 2, 0.1, 0.2, 0.1, 0.01);
        }
        Vec3 c = ahead(2.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, this, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.5F, 0.8F);
    }

    /** 3 embers (phase 2: 5) in a fan ±36° ahead, landing 7 to 10 blocks out on the deck. */
    private void flingEmbers(ServerLevel level) {
        embers.clear();
        int n = phase() == 2 ? 5 : 3;
        for (int k = 0; k < n; k++) {
            double a = n == 1 ? 0 : -36 + 72.0 * k / (n - 1);
            double d = 7.0 + getRandom().nextDouble() * 3.0;
            Vec3 at = clampToArena(position().add(rotate(forward(), a).scale(d)), 1.0);
            embers.add(at);
            addEffect(ember(position().add(0, 2.5, 0), at, 18));
        }
    }

    /** One ember: arcs through the air for {@code delay} ticks over its ring (soul dust, red for the last 8), then bursts. */
    private Effect ember(Vec3 from, Vec3 at, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                double f = (k + 1) / (double) delay;
                Vec3 p = from.lerp(at, f).add(0, Math.sin(f * Math.PI) * 3.0 - f * 2.5, 0);
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0.0);
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, EMBER_R, delay - k <= 8 ? RED : SOUL);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, at.x, at.y + 0.4, at.z, 18, 0.6, 0.3, 0.6, 0.05);
            level.sendParticles(ParticleTypes.SOUL, at.x, at.y + 0.4, at.z, 4, 0.4, 0.2, 0.4, 0.02);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.5F, 1.2F);
            if (boss instanceof SoulStoker s) {
                for (LivingEntity e : boss.victims(level, at, EMBER_R + 1)) {
                    if (flatDist(e.position(), at) <= EMBER_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 2.5) {
                        s.burn(level, e, 8.0F, 0.2, 0.3, 2.0F);
                    }
                }
            }
            return true;
        };
    }

    private void drawLine(ServerLevel level, double len, double half, DustParticleOptions dust) {
        Vec3 f = forward();
        Vec3 side = new Vec3(-f.z, 0, f.x);
        for (double d = 1.0; d <= len; d += 1.0) {
            Vec3 p = position().add(f.scale(d));
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = p.add(side.scale(s * half));
                level.sendParticles(dust, q.x, q.y + 0.15, q.z, 1, 0, 0, 0, 0);
            }
            if (((int) d) % 2 == 0) {
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /**
     * The punch's shockwave: a front running down the line from 4 to 14 at 1.25 blocks a tick; whoever it passes takes
     * 10 and a lift (once). It stops where the deck ends (a wall or the trench).
     */
    private Effect shockLine(Vec3 from, Vec3 dir) {
        double[] front = {4.0};
        Set<UUID> hit = new HashSet<>();
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, level) -> {
            if (!(boss instanceof SoulStoker s)) {
                return true;
            }
            double d0 = front[0];
            double d1 = d0 + 1.25;
            front[0] = d1;
            Vec3 p = from.add(dir.scale(d1));
            double fy = floorY(level, p.x, from.y + 1, p.z);
            if (Double.isNaN(fy) || Math.abs(fy - from.y) > 1.5 || headroom(level, new Vec3(p.x, fy, p.z), 2) < 2) {
                return true;
            }
            for (int k = -1; k <= 1; k++) {
                Vec3 q = p.add(side.scale(k * LINE_HALF * 0.8));
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, q.x, fy + 0.3, q.z, 3, 0.2, 0.3, 0.2, 0.03);
            }
            level.sendParticles(ParticleTypes.CLOUD, p.x, fy + 0.4, p.z, 2, 0.4, 0.1, 0.4, 0.02);
            if (((int) (d1 / 1.25)) % 3 == 0) {
                level.playSound(null, p.x, fy, p.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.4F);
            }
            for (LivingEntity e : boss.victims(level, p, 3.0)) {
                Vec3 to = e.position().subtract(from).multiply(1, 0, 1);
                double along = to.dot(dir);
                if (along >= d0 - 0.5 && along <= d1 + 0.5 && Math.abs(to.dot(side)) <= LINE_HALF + e.getBbWidth() / 2
                        && Math.abs(e.getY() - fy) < 2.5 && hit.add(e.getUUID())) {
                    s.strike(level, e, 10.0F, 0.3, 0.55);
                }
            }
            return d1 >= LINE_LEN;
        };
    }

    /** A shovelful of souls heaved from the deck into his firebox. */
    private void scoop(ServerLevel level) {
        Vec3 from = position().add(forward().scale(2.2)).add(rotate(forward(), -90).scale(1.0));
        Vec3 to = firebox();
        for (double f = 0; f <= 1.0; f += 0.2) {
            Vec3 p = from.lerp(to, f).add(0, Math.sin(f * Math.PI) * 1.2, 0);
            level.sendParticles(ParticleTypes.SOUL, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0.0);
        }
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, to.x, to.y, to.z, 6, 0.3, 0.2, 0.3, 0.02);
        level.playSound(null, this, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, this, SoundEvents.SOUL_SAND_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /** The pressure gauge over his head: a column of dust filling up ({@code fill} 0..1), blue turning red near the top. */
    private void drawGauge(ServerLevel level, double fill) {
        int n = (int) Math.round(Mth.clamp(fill, 0, 1) * 8);
        for (int i = 0; i < 8; i++) {
            double y = getY() + HEIGHT + 0.6 + i * 0.25;
            DustParticleOptions d = i >= n ? BONE : (i >= 6 ? RED : SOUL);
            level.sendParticles(d, getX(), y, getZ(), 1, 0, 0, 0, 0);
        }
        if (n >= 6) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + HEIGHT, getZ(), 1, 0.4, 0.1, 0.4, 0.02);
        }
    }

    private void drawCone(ServerLevel level, double range, DustParticleOptions dust) {
        for (double r = 4.0; r <= range; r += 3.5) {
            telegraphArc(level, r, CONE_HALF, dust);
        }
        telegraphArc(level, range, CONE_HALF, dust);
        for (int s = -1; s <= 1; s += 2) {
            Vec3 dir = rotate(forward(), s * CONE_HALF);
            for (double d = 1.5; d <= range; d += 1.5) {
                Vec3 p = position().add(dir.scale(d));
                level.sendParticles(dust, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private void hitCone(ServerLevel level, double range, float damage) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(CONE_HALF));
        for (LivingEntity e : victims(level, position(), range + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.5 || to.normalize().dot(fwd) >= cos) && Math.abs(e.getY() - getY()) < 4.0) {
                burn(level, e, damage, 0.8, 0.2, 4.0F);
            }
        }
    }

    private void ventCone(ServerLevel level, double range) {
        Vec3 m = firebox();
        for (int i = 0; i < 6; i++) {
            Vec3 dir = rotate(forward(), (getRandom().nextDouble() * 2 - 1) * CONE_HALF);
            double sp = 0.5 + getRandom().nextDouble() * 0.4;
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, m.x, m.y, m.z, 0, dir.x, -0.08, dir.z, sp);
        }
        for (double d = 2.0; d <= range; d += 2.0) {
            Vec3 p = ahead(d);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.8, p.z, 2, d * 0.2, 0.4, d * 0.2, 0.02);
        }
    }

    /**
     * Vent spots: one under the target, the rest spread over the deck (at least 3.5 apart); phase 2 two more and one
     * under every other player (up to 4 players).
     */
    private void planVents(ServerLevel level, @Nullable LivingEntity target) {
        vents.clear();
        int n = phase() == 2 ? 7 : 5;
        if (target != null) {
            tryVent(level, clampToArena(target.position(), 1.5));
        }
        if (phase() == 2) {
            int i = 0;
            for (Player p : fighters(level)) {
                if (p != target && i++ < 3 && tryVent(level, clampToArena(p.position(), 1.5))) {
                    n++;
                }
            }
        }
        Vec3 c = centre();
        double r = reach() - 2.0;
        for (int tries = 0; tries < 60 && vents.size() < n; tries++) {
            tryVent(level, new Vec3(c.x + (getRandom().nextDouble() * 2 - 1) * r, c.y, c.z + (getRandom().nextDouble() * 2 - 1) * r));
        }
    }

    /** Adds a vent at {@code w} if there is deck there, away from him and at least 3.5 from the other vents. */
    private boolean tryVent(ServerLevel level, Vec3 w) {
        Vec3 s = safeSpotLow(level, w.x, w.z);
        if (s == null || flatDist(s, position()) < 2.5) {
            return false;
        }
        for (Vec3 v : vents) {
            if (flatDist(v, s) < 3.5) {
                return false;
            }
        }
        vents.add(s);
        return true;
    }

    /** A floor spot level with the seal (no headroom needed: vents only need floor). */
    private @Nullable Vec3 safeSpotLow(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        return Double.isNaN(y) || Math.abs(y - centre().y) > 0.6 ? null : new Vec3(x, y, z);
    }

    /** A soul-fire vent: smoke and its ring for {@code delay} ticks (red for the last 10), then a jet of blue flame. */
    private Effect vent(Vec3 at, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, at, VENT_R, delay - k <= 10 ? RED : SOUL);
                }
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 0.2, at.z, 1, 0.4, 0.05, 0.4, 0.01);
                    level.sendParticles(ParticleTypes.SOUL, at.x, at.y + 0.2, at.z, 1, 0.5, 0.05, 0.5, 0.01);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, at.x, at.y + 1.2, at.z, 30, 0.5, 1.2, 0.5, 0.06);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 2.5, at.z, 6, 0.4, 0.6, 0.4, 0.02);
            level.playSound(null, at.x, at.y, at.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.8F, 0.6F);
            if (boss instanceof SoulStoker s) {
                for (LivingEntity e : boss.victims(level, at, VENT_R + 1)) {
                    if (flatDist(e.position(), at) <= VENT_R + e.getBbWidth() / 2 && Math.abs(e.getY() - at.y) < 3.0) {
                        s.burn(level, e, 12.0F, 0.0, 0.6, 3.0F);
                    }
                }
            }
            return true;
        };
    }

    private void planCharge(@Nullable LivingEntity target) {
        Vec3 to = target != null ? target.position() : ahead(8.0);
        Vec3 d = to.subtract(position()).multiply(1, 0, 1);
        laneDir = d.lengthSqr() < 1.0E-4 ? forward() : d.normalize();
        laneLen = Mth.clamp(d.length() + 3.0, 6.0, 16.0);
        faceToward(position().add(laneDir));
    }

    private void drawLane(ServerLevel level, DustParticleOptions dust) {
        if (laneDir == null) {
            return;
        }
        Vec3 side = new Vec3(-laneDir.z, 0, laneDir.x);
        for (double d = 1.0; d <= laneLen; d += 1.0) {
            Vec3 p = position().add(laneDir.scale(d));
            for (int s = -1; s <= 1; s += 2) {
                Vec3 q = p.add(side.scale(s * LANE_HALF));
                level.sendParticles(dust, q.x, q.y + 0.15, q.z, 1, 0, 0, 0, 0);
            }
        }
        Vec3 end = position().add(laneDir.scale(laneLen));
        level.sendParticles(dust, end.x, end.y + 0.15, end.z, 3, 0.4, 0, 0.4, 0);
    }

    /** One tick of the charge: he steps 1.1 along the lane if there is deck and room ahead, else he stops and slams. */
    private void chargeStep(ServerLevel level) {
        if (laneDir == null || charged >= laneLen) {
            return;
        }
        double step = Math.min(1.1, laneLen - charged);
        Vec3 next = position().add(laneDir.scale(step));
        Vec3 spot = safeSpot(level, next.x, next.z);
        Vec3 wide = safeSpot(level, next.x + laneDir.x * 1.0, next.z + laneDir.z * 1.0);
        if (spot == null || wide == null || cheb(next) > reach()) {
            charged = laneLen;
            slam(level);
            return;
        }
        teleportTo(spot.x, spot.y, spot.z);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
        charged += step;
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 4.2, getZ(), 3, 0.6, 0.2, 0.6, 0.02);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.3, getZ(), 2, 0.6, 0.1, 0.6, 0.01);
        if (((int) (charged / 1.1)) % 3 == 0) {
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.8F, 0.4F);
        }
        for (LivingEntity e : victims(level, position(), 2.6)) {
            if (flatDist(e.position(), position()) <= 1.8 + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 3.5
                    && chargeHit.add(e.getUUID())) {
                strike(level, e, 15.0F, 1.1, 0.4);
            }
        }
        if (charged >= laneLen) {
            slam(level);
        }
    }

    private void slam(ServerLevel level) {
        hitCircle(level, position(), 3.0, 8.0F, 0.6, 0.3);
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.5, getZ(), 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 0.3, getZ(), 24, 1.5, 0.1, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    private int thrallCount(ServerLevel level) {
        return level.getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(centre())).inflate(radius + 4, 10, radius + 4),
                m -> m.isAlive() && m.entityTags().contains(MINION_TAG)).size();
    }

    // ------------------------------------------------------------------ phase 3: overpressure

    private void overpressure(ServerLevel level) {
        overpressured = true;
        ringTimer = 100;
        crankTick = 0;
        crankHit.clear();
        addEffect(WayfarerBoss.wave(position(), 12, 0.55, 10.0F, SOUL));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("soul_stoker_overpressure"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(SOUL_BIG, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.0);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 3, getZ(), 60, 1.5, 1.5, 1.5, 0.1);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2, getZ(), 30, 2.0, 1.0, 2.0, 0.1);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    /** Three gap angles (degrees round him): the first toward a random side, then 25° further the same way each ring. */
    private void planGaps(@Nullable LivingEntity target) {
        gaps.clear();
        double start = target != null
                ? Math.toDegrees(Math.atan2(target.getZ() - getZ(), target.getX() - getX())) + (getRandom().nextBoolean() ? 50 : -50)
                : getRandom().nextDouble() * 360.0;
        double turn = getRandom().nextBoolean() ? 25.0 : -25.0;
        for (int k = 0; k < 3; k++) {
            gaps.add(start + k * turn);
        }
    }

    /** The gap lines of the rings still to come (from ring {@code from}), each in its colour. */
    private void drawGaps(ServerLevel level, int from) {
        DustParticleOptions[] cols = {SOUL, BRASS, RED};
        for (int k = Math.max(0, from); k < gaps.size(); k++) {
            double a = Math.toRadians(gaps.get(k));
            for (double d = 2.0; d <= 16.0; d += 1.0) {
                level.sendParticles(cols[k % 3], getX() + Math.cos(a) * d, getY() + 0.2 + k * 0.15, getZ() + Math.sin(a) * d,
                        1, 0.05, 0, 0.05, 0);
            }
        }
    }

    private static boolean inGap(Vec3 c, Vec3 p, double gap) {
        double ang = Math.toDegrees(Math.atan2(p.z - c.z, p.x - c.x));
        return Math.abs(Mth.wrapDegrees(ang - gap)) <= GAP_HALF;
    }

    /** A ring of blue flame rolling out from {@code c} at 0.5 blocks a tick, too tall to jump, with one gap. */
    private Effect flameRing(Vec3 c, double gap) {
        double[] r = {1.5};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (!(boss instanceof SoulStoker s)) {
                return true;
            }
            r[0] += 0.5;
            double rr = r[0];
            int n = Math.max(16, (int) (rr * 4));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                Vec3 p = c.add(Math.cos(a) * rr, 0, Math.sin(a) * rr);
                if (inGap(c, p, gap) || s.cheb(p) > s.reach() + 1) {
                    continue;
                }
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.4 + (i % 3) * 0.6, p.z, 1, 0.05, 0.2, 0.05, 0.0);
            }
            for (LivingEntity e : boss.victims(level, c, rr + 1.5)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - rr) <= 0.8 && Math.abs(e.getY() - c.y) < 3.5 && !inGap(c, e.position(), gap)
                        && hit.add(e.getUUID())) {
                    s.burn(level, e, 10.0F, 0.4, 0.1, 3.0F);
                }
            }
            return rr >= s.reach() * 1.45;
        };
    }

    /** Index of the crank strip (strips 4 wide, running along x like the crankshaft) under {@code p}. */
    private int strip(Vec3 p) {
        return Mth.floor((p.z - centre().z + reach() + 1) / STRIP);
    }

    /**
     * The crank rhythm: every 60 ticks the strips of one parity burn (the parity alternates). For 40 ticks their edges
     * are drawn (soul dust, red for the last 12) with flames licking up more and more, then for 6 ticks they jet blue
     * flame: 5 and soul fire 2 s (once a pulse) to whoever stands on one.
     */
    private void crankRhythm(ServerLevel level) {
        int k = crankTick++;
        int parity = crankCount % 2;
        double r = reach() + 1;
        Vec3 c = centre();
        int strips = (int) Math.ceil(2 * r / STRIP);
        if (k < CRANK_WARN) {
            if (k % 4 == 0) {
                DustParticleOptions dust = CRANK_WARN - k <= 12 ? RED : SOUL;
                for (int i = parity; i < strips; i += 2) {
                    double z0 = c.z - r + i * STRIP;
                    double z1 = Math.min(c.z + r, z0 + STRIP);
                    for (double x = c.x - r; x <= c.x + r; x += 1.5) {
                        level.sendParticles(dust, x, c.y + 0.15, z0 + 0.2, 1, 0, 0, 0, 0);
                        level.sendParticles(dust, x, c.y + 0.15, z1 - 0.2, 1, 0, 0, 0, 0);
                        if (k >= CRANK_WARN / 2 && getRandom().nextInt(4) == 0) {
                            level.sendParticles(ParticleTypes.SMALL_FLAME, x, c.y + 0.1, (z0 + z1) / 2, 1, 0.3, 0, (z1 - z0) * 0.3, 0.0);
                        }
                    }
                }
            }
            if (k == CRANK_WARN - 12) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.PISTON_CONTRACT, SoundSource.HOSTILE, 2.5F, 0.5F);
            }
            return;
        }
        if (k < CRANK_WARN + CRANK_BURN) {
            if (k == CRANK_WARN) {
                crankHit.clear();
                level.playSound(null, c.x, c.y, c.z, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 3.0F, 0.5F);
                level.playSound(null, c.x, c.y, c.z, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.5F, 0.4F);
            }
            if (k % 2 == 0) {
                for (int i = parity; i < strips; i += 2) {
                    double z0 = c.z - r + i * STRIP;
                    double z1 = Math.min(c.z + r, z0 + STRIP);
                    for (double x = c.x - r; x <= c.x + r; x += 2.0) {
                        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, x, c.y + 0.6, (z0 + z1) / 2, 2, 0.5, 0.5, (z1 - z0) * 0.3, 0.02);
                    }
                }
            }
            for (Player p : fighters(level)) {
                if (Math.floorMod(strip(p.position()), 2) == parity && cheb(p.position()) <= r && Math.abs(p.getY() - c.y) < 2.5
                        && crankHit.add(p.getUUID())) {
                    burn(level, p, 5.0F, 0.0, 0.2, 2.0F);
                }
            }
            return;
        }
        if (k >= CRANK_PERIOD - 1) {
            crankTick = 0;
            crankCount++;
        }
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2, getZ(), 4, 0.6, 0.8, 0.6, 0.02);
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
        if (phase() == 1 && overpressured) {                              // the fight was reset
            overpressured = false;
            roarUntil = -1;
            crankTick = 0;
            crankCount = 0;
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("soul_stoker_overpressure"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("soul_stoker_wrath"));
            }
        }
        BossAttack cur = currentAttack();
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (phase() == 2 && free) {
            if (!overpressured && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "overpressure");
            } else if (overpressured && --ringTimer <= 0) {
                ringTimer = Math.max(120, (int) Math.round(RING_EVERY * cooldownScale()));
                chain(level, "ringblast");
            }
        }
        // phase 3: the deck's crank rhythm, paused (and restarted from a full warning) during the ring blasts
        if (overpressured && phase() == 2 && fighting) {
            cur = currentAttack();
            if (cur != null && ("ringblast".equals(cur.name) || "overpressure".equals(cur.name))) {
                crankTick = 0;
            } else {
                crankRhythm(level);
            }
        }
        // ambience: blue flame from the chimneys, souls from the firebox, steam when the pressure is up
        if (tickCount % 3 == 0) {
            Vec3 f = forward();
            Vec3 back = position().subtract(f.scale(0.6));
            Vec3 side = new Vec3(-f.z, 0, f.x);
            for (int s = -1; s <= 1; s += 2) {
                Vec3 p = back.add(side.scale(s * 0.4));
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, getY() + 4.3, p.z, 1, 0.05, 0.1, 0.05, 0.01);
            }
        }
        if (tickCount % 12 == 0) {
            Vec3 m = firebox();
            level.sendParticles(ParticleTypes.SOUL, m.x, m.y, m.z, 1, 0.3, 0.2, 0.3, 0.01);
        }
        if (overpressured && phase() == 2 && tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.5, getZ(), 1, 0.9, 0.6, 0.9, 0.02);
        }
        if (tickCount % 80 == 0) {
            level.playSound(null, this, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("soul_stoker_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        // the engine's roar shoves everyone within 7 away: take the outward part back near the rim or the trench
        for (LivingEntity e : victims(level, position(), 8.0)) {
            Vec3 v = e.getDeltaMovement();
            Vec3 h = safePush(level, e, new Vec3(v.x, 0, v.z));
            e.setDeltaMovement(h.x, Math.min(v.y, 0.3), h.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 4, getZ(), 60, 1.0, 1.0, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 2, getZ(), 80, 1.5, 2.0, 1.5, 0.05);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2, getZ(), 60, 1.5, 1.5, 1.5, 0.05);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("StokerCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("StokerRadius", radius);
        output.putBoolean("StokerOverpressure", overpressured);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("StokerCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("StokerRadius", 18);
        overpressured = input.getBooleanOr("StokerOverpressure", false) && phase() == 2;
    }
}
