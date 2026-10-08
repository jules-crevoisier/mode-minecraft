package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
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
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.FallenSeraph.BEAM;
import static com.brasshaven.generated.MobAnims.FallenSeraph.BLINK;
import static com.brasshaven.generated.MobAnims.FallenSeraph.DIVE;
import static com.brasshaven.generated.MobAnims.FallenSeraph.GLAIVE;
import static com.brasshaven.generated.MobAnims.FallenSeraph.NOVA;
import static com.brasshaven.generated.MobAnims.FallenSeraph.PILLARS;
import static com.brasshaven.generated.MobAnims.FallenSeraph.RAIN;
import static com.brasshaven.generated.MobAnims.FallenSeraph.ROAR;
import static com.brasshaven.generated.MobAnims.FallenSeraph.SHARDS;
import static com.brasshaven.generated.MobAnims.FallenSeraph.SHATTER;
import static com.brasshaven.generated.MobAnims.FallenSeraph.STAGGER;
import static com.brasshaven.generated.MobAnims.FallenSeraph.THRUST;

/**
 * Le Séraphin déchu (The Fallen Seraph), guardian of the Shattered Halo: a haloed angel of the broken ring hovering
 * over the arena disc, a great broken halo behind her head, one wing whole and one burnt to the void, six halo
 * shards orbiting her and a glaive whose blade is a crescent of halo. She wakes on the floating disc at the centre
 * of the ring.
 * <p>780 health, armour 14, poise 110, hits of 9 to 22. Three phases:
 * <ul>
 *     <li>Phase 1: <b>glaive sweep</b> (210 degrees, 17), <b>thrust</b> (a gliding lunge down a marked line, 16),
 *     <b>halo shards</b> (six shards flung one after another, 9 each), <b>lances of light</b> (rings under every
 *     player and a few strays, then columns of light, 14) and <b>blink</b> (she reappears at the edge of the disc,
 *     the destination ringed in portal light, then follows up with the shards).</li>
 *     <li>Phase 2 (roar at 60%): the <b>blinding sweep</b> (a beam from the halo sweeps 160 degrees from her left to
 *     her right, 14 + blindness; safe only close to her or behind her), the <b>nova</b> (a ring of light rolls out,
 *     then a second one rolls back in from the edge: jump both), a second volley of lances, two-shard fans, combos.</li>
 *     <li>Phase 3 (at 25%, an invulnerable <b>shatter</b>): the disc cracks. Six fissures run from the centre to the
 *     rim and flare in turn (warned, 10 + slowness); beyond the gold ring the disc crumbles (3 every half second),
 *     so the fight closes in. She adds the <b>shattered sky</b> (four volleys of falling shards on every player)
 *     and the <b>seraph's fall</b> (a gold ring follows you, locks, and she dives on it from the sky: 22 + a wave).</li>
 * </ul>
 * The disc floats over the void: no move throws a player outward near the rim (see {@link #strike}), and her own
 * glide never carries her off the edge.
 */
public class FallenSeraph extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 4.4F;
    private static final float PHASE_THREE_AT = 0.25F;
    private static final double BEAM_LENGTH = 20.0;
    private static final double BEAM_INNER = 3.5;
    private static final int CRACKS = 6;

    /** Arena centre and radius (from the seal), saved with the boss. */
    private @Nullable Vec3 centre;
    private int radius = 16;
    /** Phase 3: the disc has cracked. */
    private boolean shattered;
    /** Ticks of invulnerability left while she shatters the disc. */
    private int shatterGuard;
    /** Angles (degrees) of the fissures across the disc in phase 3. */
    private final List<Double> cracks = new ArrayList<>();
    private int flareTimer;
    private int specialTimer;
    /** The phase 2 roar is playing until this tick. */
    private int roarUntil;

    private final Set<UUID> struck = new HashSet<>();
    private final Map<UUID, Integer> beamHits = new HashMap<>();
    private final List<Vec3> spots = new ArrayList<>();
    private @Nullable Vec3 dest;

    public FallenSeraph(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 780.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.2);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.FallenSeraph.TICKS;
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
        return 110.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.6F;
    }

    @Override
    protected double preferredRange() {
        return 5.0;
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
            output.putLong("SeraphCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("SeraphRadius", radius);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("SeraphCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("SeraphRadius", 16);
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Radius of the safe part of the disc in phase 3 (the gold ring); the rest crumbles. */
    private double rim() {
        return Math.max(6.0, Math.min(12.0, radius - 3.0));
    }

    private double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Top of the first solid block at or below {@code y + 2} (scanning 8 blocks), or NaN over the void. */
    private double floorY(ServerLevel level, double x, double y, double z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(y + 2), Mth.floor(z));
        for (int i = 0; i < 8; i++) {
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return p.getY() + 1.0;
            }
            p.move(0, -1, 0);
        }
        return Double.NaN;
    }

    /** A standing spot on the floor at (x, z): solid ground near the arena's level and room for her above. */
    private @Nullable Vec3 safeSpot(ServerLevel level, double x, double z) {
        double y = floorY(level, x, centre().y + 1, z);
        if (Double.isNaN(y) || Math.abs(y - centre().y) > 3) {
            return null;
        }
        for (int dy = 0; dy < 4; dy++) {
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

    private void teleport(ServerLevel level, Vec3 to) {
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 2, getZ(), 40, 0.5, 1.2, 0.5, 0.08);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 12, 0.4, 1.0, 0.4, 0.05);
        teleportTo(to.x, to.y, to.z);
        getNavigation().stop();
        setDeltaMovement(Vec3.ZERO);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, to.x, to.y + 2, to.z, 40, 0.5, 1.2, 0.5, 0.08);
        level.sendParticles(ParticleTypes.END_ROD, to.x, to.y + 2, to.z, 20, 0.6, 1.2, 0.6, 0.08);
        level.playSound(null, to.x, to.y, to.z, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    private void face(@Nullable LivingEntity t) {
        if (t != null) {
            snapFacing((float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F);
        }
    }

    // ------------------------------------------------------------------ fairness over the void

    /**
     * Every hit of hers (moves, waves, eruptions, the NG+ shockwave) comes through here. Near the rim of the disc the
     * outward part of the knockback is removed: she never throws a player off the edge.
     */
    @Override
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (!e.hurtServer(level, damageSources().mobAttack(this), damage) || knockback <= 0) {
            return;
        }
        Vec3 push = e.position().subtract(position()).multiply(1, 0, 1);
        push = push.lengthSqr() < 1.0E-4 ? Vec3.ZERO : push.normalize().scale(knockback);
        Vec3 radial = e.position().subtract(centre()).multiply(1, 0, 1);
        double r = radial.length();
        if (r > radius - 6.0 && r > 0.1) {
            Vec3 n = radial.scale(1.0 / r);
            double out = push.dot(n);
            if (out > 0) {
                push = push.subtract(n.scale(out));     // keep only the sideways part
            }
            push = push.scale(0.5);
            lift = Math.min(lift, 0.35);
        }
        e.push(push.x, lift, push.z);
        e.hurtMarked = true;
    }

    /** Pure damage, no push. */
    private void hurt(ServerLevel level, LivingEntity e, float damage) {
        e.hurtServer(level, damageSources().mobAttack(this), damage);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // glaive sweep: the glaive drawn back over her right shoulder (0.8 s, the arc is outlined in light), then one
        // sweep over 210 degrees from her right to her left
        out.add(BossAttack.of("glaive").anim(GLAIVE).timing(16, 4, 14).range(0, 6.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 6.5, 105, ParticleTypes.END_ROD);
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.5, 105, 17.0F, 0.6);
                    sweepParticles(b, level, 6.5, 105);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.distanceTo(t) > 3.5 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "thrust");
                    }
                })
                .build());
        // thrust: the glaive levelled and drawn back (0.7 s, a line of light marks her path), then she glides along it
        // point first: 16 once per target. She stops short of the edge of the disc.
        out.add(BossAttack.of("thrust").anim(THRUST).timing(14, 8, 14).range(4.0, 14.0).cooldown(90).weight(9)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 11.5; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.END_ROD, p.x, b.getY() + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 2.0F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.5F, 0.6F))
                .active((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.glide(level, 1.3);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s && s.shattered && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "glaive");
                    }
                })
                .build());
        // halo shards: the left hand raised, the orbit spins up (0.9 s, a ring of light marks the target), then the six
        // shards are flung one after another at where the target stands at that moment: 9 each (phase 2: fans of two)
        out.add(BossAttack.of("shards").anim(SHARDS).timing(18, 24, 12).range(3.5, 26.0).cooldown(100).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 1.3, ParticleTypes.END_ROD);
                    }
                    double a = tick * 0.6;
                    level.sendParticles(ParticleTypes.END_ROD, b.getX() + Math.cos(a) * 1.4, b.getY() + 2.6,
                            b.getZ() + Math.sin(a) * 1.4, 1, 0, 0, 0, 0);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0 && tick < 24 && t != null) {
                        double ang = tick * 15.0 + b.tickCount * 6.0;
                        Vec3 from = b.position().add(rotate(b.forward(), ang % 120 - 60).scale(1.3)).add(0, 2.6, 0);
                        Vec3 to = t.position().add(0, t.getBbHeight() * 0.5, 0);
                        Vec3 dir = to.subtract(from).normalize();
                        if (b.phase() == 2) {
                            b.addEffect(shard(from, tilt(dir, -9), 28.0, 9.0F));
                            b.addEffect(shard(from, tilt(dir, 9), 28.0, 9.0F));
                        } else {
                            b.addEffect(shard(from, dir, 28.0, 9.0F));
                        }
                        level.playSound(null, b, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 1.5F, 1.4F);
                    }
                })
                .build());
        // lances of light: both hands raised to the sky (1.0 s); rings are drawn under every player and a few strays,
        // with light falling into them; then columns of light strike them all: 14. Phase 2: a second volley follows on
        // where the players have moved to (0.7 s warning)
        out.add(BossAttack.of("pillars").anim(PILLARS).timing(20, 22, 12).range(0, 24.0).cooldown(140).weight(8)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.pickSpots(level, b.phase() == 2 ? 5 : 3);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s && tick % 2 == 0) {
                        for (Vec3 p : s.spots) {
                            b.telegraphRing(level, p, 1.8, ParticleTypes.END_ROD);
                            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 9.0 - tick * 0.42, p.z, 1, 0.05, 0, 0.05, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.lances(level);
                        if (b.phase() == 2) {
                            s.spots.clear();
                            for (LivingEntity e : b.victims(level, b.position(), 26.0)) {
                                s.spots.add(s.floorUnder(level, e.position()));
                            }
                        } else {
                            s.spots.clear();
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof FallenSeraph s) || s.spots.isEmpty()) {
                        return;
                    }
                    if (tick < 14 && tick % 2 == 0) {
                        for (Vec3 p : s.spots) {
                            b.telegraphRing(level, p, 1.8, ParticleTypes.END_ROD);
                        }
                    } else if (tick == 14) {
                        s.lances(level);
                        s.spots.clear();
                    }
                })
                .build());
        // blink: the wings fold round her (0.6 s) while portal light rings the place she will appear, at the edge of the
        // disc opposite her target; she bursts out there and follows up (shards, or the blinding sweep in phase 2)
        out.add(BossAttack.of("blink").anim(BLINK).timing(12, 2, 6).range(0, 30.0).cooldown(160).weight(7).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.dest = s.edgeSpot(level, t);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s && s.dest != null && tick % 2 == 0) {
                        b.telegraphRing(level, s.dest, 1.6, ParticleTypes.REVERSE_PORTAL);
                        level.sendParticles(ParticleTypes.PORTAL, s.dest.x, s.dest.y + 1.5, s.dest.z, 6, 0.3, 1.0, 0.3, 0.3);
                    }
                    level.sendParticles(ParticleTypes.PORTAL, b.getX(), b.getY() + 2, b.getZ(), 4, 0.6, 1.2, 0.6, 0.5);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_MIRROR, SoundSource.HOSTILE, 2.0F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s && s.dest != null) {
                        s.teleport(level, s.dest);
                        s.face(t);
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.8F);
                    }
                })
                .end((b, level, t, tick) -> {
                    float r = b.getRandom().nextFloat();
                    if (b.phase() == 2 && r < 0.4F) {
                        b.chain(level, "beam");
                    } else if (r < (b.phase() == 2 ? 0.75F : 0.55F)) {
                        b.chain(level, "shards");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // blinding sweep: she rises, head thrown back, the halo blazing (1.2 s: a line of light on her left marks where
        // the beam starts, dots at 3.5 blocks mark the safe circle under her); then a beam pours from the halo and sweeps
        // 160 degrees from her left to her right in 2 s: 14 and blindness, every half second. Too tall to jump: stay
        // close under her, or get behind her
        out.add(BossAttack.of("beam").anim(BEAM).phaseTwo().timing(24, 40, 16).range(0, 22.0).cooldown(260).weight(7)
                .track(false)
                .start((b, level, t, tick) -> beamHits.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        Vec3 dir = rotate(b.forward(), -80);
                        for (double d = BEAM_INNER; d <= BEAM_LENGTH; d += 1.0) {
                            Vec3 p = b.position().add(dir.scale(d));
                            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
                        }
                        for (int a = -80; a <= 80; a += 16) {
                            Vec3 p = b.position().add(rotate(b.forward(), a).scale(BEAM_INNER));
                            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 5.0, b.getZ(), 2, 0.6, 0.6, 0.6, 0.02);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
                    } else if (tick == 12) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.5F, 1.4F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.beam(level, -80 + 160.0 * tick / 39.0);
                    }
                })
                .build());
        // nova: the halo raised over her head (1.0 s: a ring at her feet, and the edge of the disc lit in portal light),
        // thrust out: a ring of light rolls out across the disc (12, jump it), and 0.8 s later a second ring rolls back
        // in from the edge toward her (12, jump it again)
        out.add(BossAttack.of("nova").anim(NOVA).phaseTwo().timing(20, 36, 14).range(0, 16.0).cooldown(200).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 2.0, ParticleTypes.END_ROD);
                    }
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 15.0, ParticleTypes.REVERSE_PORTAL);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.5F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(WayfarerBoss.wave(b.position(), 15.0, 0.6, 12.0F, ParticleTypes.END_ROD));
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 16) {
                        b.addEffect(inwardWave(b.position(), 15.0, 0.6, 12.0F));
                        level.playSound(null, b, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 1.4F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (scheduled by bossTick, never rolled)
        // shatter: the transition. She rises and curls up, invulnerable (2.0 s), the fissures already glowing under the
        // floor; she slams down: the disc cracks and a ring rolls out (8, jump it)
        out.add(BossAttack.of("shatter").anim(SHATTER).timing(40, 4, 16).range(9999, 9999).weight(1).track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.beginShatter(level);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s && tick % 2 == 0) {
                        s.drawCracks(level, tick / 40.0, ParticleTypes.END_ROD);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.0F, 0.4F + tick * 0.01F);
                    }
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 2.5, b.getZ(), 4, 0.8, 1.2, 0.8, 0.05);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FallenSeraph s) {
                        s.completeShatter(level);
                    }
                })
                .build());
        // shattered sky: she hurls her shards at the sky (1.1 s); four volleys fall back, 0.55 s apart: a ring under
        // every player and three strays, light falling into it for 0.8 s, then the shard lands: 13
        out.add(BossAttack.of("rain").anim(RAIN).timing(22, 44, 14).range(9999, 9999).weight(1).track(false)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 3 + tick * 0.2, b.getZ(), 2, 0.8, 0.2, 0.8, 0.02);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.EVOKER_CAST_SPELL, SoundSource.HOSTILE, 2.5F, 0.6F);
                    } else if (tick == 20) {
                        level.playSound(null, b, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 11 == 0 && tick < 44 && b instanceof FallenSeraph s) {
                        s.volley(level);
                    }
                })
                .build());
        // seraph's fall: she beats her wings and soars (a gold ring follows the target for 0.8 s), the ring locks and
        // turns to fire as she appears high above it, and 0.7 s later she falls glaive-first on it: 22 in 3.5 blocks
        // and a ring (9, jump it). A long recovery on the floor
        out.add(BossAttack.of("dive").anim(DIVE).timing(30, 4, 22).range(9999, 9999).weight(1).track(false)
                .start((b, level, t, tick) -> dest = null)
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof FallenSeraph s)) {
                        return;
                    }
                    if (tick < 16 && t != null) {
                        Vec3 p = s.safeSpot(level, t.getX(), t.getZ());
                        if (p != null) {
                            s.dest = p;
                        }
                    }
                    if (tick == 16 && s.dest != null) {
                        s.teleport(level, s.dest);
                        level.playSound(null, b, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    if (s.dest != null && tick % 2 == 0) {
                        b.telegraphRing(level, s.dest, 3.5, tick < 16 ? ParticleTypes.END_ROD : ParticleTypes.SOUL_FIRE_FLAME);
                        b.telegraphRing(level, s.dest, 1.0, ParticleTypes.WAX_ON);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 3.0F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 3.5, 22.0F, 0.6, 0.3);
                    b.addEffect(WayfarerBoss.wave(b.position(), 9.0, 0.5, 9.0F, ParticleTypes.END_ROD));
                    level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 0.5, b.getZ(), 4, 1.2, 0.2, 1.2, 0);
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 0.5, b.getZ(), 60, 1.5, 0.3, 1.5, 0.2);
                    level.playSound(null, b, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private static void sweepParticles(WayfarerBoss b, ServerLevel level, double range, double halfAngle) {
        for (double a = -halfAngle; a <= halfAngle; a += 15) {
            Vec3 p = b.position().add(rotate(b.forward(), a).scale(range * 0.7));
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.4, p.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 1.4, p.z, 1, 0.1, 0.1, 0.1, 0.02);
        }
    }

    /** The thrust's glide: a step forward per tick, never past the safe part of the disc; hits once per target. */
    private void glide(ServerLevel level, double step) {
        Vec3 next = position().add(forward().scale(step));
        double limit = (shattered ? rim() : radius) - 2.5;
        if (flatDist(next, centre()) <= limit && safeSpot(level, next.x, next.z) != null) {
            move(MoverType.SELF, forward().scale(step));
        }
        Vec3 tip = position().add(forward().scale(1.6));
        level.sendParticles(ParticleTypes.END_ROD, tip.x, getY() + 1.4, tip.z, 3, 0.3, 0.3, 0.3, 0.02);
        for (LivingEntity e : victims(level, tip, 2.4)) {
            if (flatDist(e.position(), tip) <= 1.9 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, 16.0F, 0.5, 0.2);
            }
        }
    }

    /** Ring spots for the lances: every player near her, plus a few strays on the safe disc. */
    private void pickSpots(ServerLevel level, int strays) {
        spots.clear();
        for (LivingEntity e : victims(level, position(), 26.0)) {
            spots.add(floorUnder(level, e.position()));
        }
        double max = (shattered ? rim() : radius) - 2.0;
        for (int i = 0, tries = 0; i < strays && tries < 20; tries++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = 2.0 + random.nextDouble() * Math.max(1.0, max - 2.0);
            Vec3 p = safeSpot(level, centre().x + Math.cos(a) * r, centre().z + Math.sin(a) * r);
            if (p != null) {
                spots.add(p);
                i++;
            }
        }
    }

    /** Columns of light on every spot: 14, a small lift, no push. */
    private void lances(ServerLevel level) {
        for (Vec3 p : spots) {
            for (double y = 0; y < 7; y += 0.5) {
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + y, p.z, 2, 0.25, 0.1, 0.25, 0.01);
            }
            level.sendParticles(ParticleTypes.GLOW, p.x, p.y + 0.3, p.z, 8, 0.7, 0.1, 0.7, 0.02);
            for (LivingEntity e : victims(level, p, 2.0)) {
                if (flatDist(e.position(), p) <= 1.8 + e.getBbWidth() / 2) {
                    hurt(level, e, 14.0F);
                    e.push(0, 0.45, 0);
                    e.hurtMarked = true;
                }
            }
        }
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.5F, 1.6F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 2.5F, 0.8F);
    }

    /** Where the blink lands: the edge of the disc opposite the target (or the safe ring in phase 3). */
    private @Nullable Vec3 edgeSpot(ServerLevel level, @Nullable LivingEntity t) {
        Vec3 c = centre();
        double base = t != null ? Math.atan2(t.getZ() - c.z, t.getX() - c.x) + Math.PI : random.nextDouble() * Math.PI * 2;
        double r = shattered ? rim() - 2.0 : Math.min(13.0, radius - 3.0);
        for (int i = 0; i < 8; i++) {
            double a = base + (random.nextDouble() - 0.5) * 1.4 + (i / 2) * 0.5 * (i % 2 == 0 ? 1 : -1);
            Vec3 p = safeSpot(level, c.x + Math.cos(a) * r, c.z + Math.sin(a) * r);
            if (p != null) {
                return p;
            }
        }
        return null;
    }

    /** The blinding sweep at {@code degrees} from her facing (negative is her left). */
    private void beam(ServerLevel level, double degrees) {
        Vec3 dir = rotate(forward(), degrees);
        Vec3 c = position();
        for (double d = BEAM_INNER; d <= BEAM_LENGTH; d += 0.6) {
            Vec3 p = c.add(dir.scale(d));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.6, p.z, 1, 0.03, 0.05, 0.03, 0);
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 1.8, p.z, 1, 0.03, 0.05, 0.03, 0);
            if (((int) (d * 2)) % 5 == 0) {
                level.sendParticles(ParticleTypes.GLOW, p.x, p.y + 1.2, p.z, 1, 0.05, 0.4, 0.05, 0);
            }
        }
        // the beam's source at the halo
        level.sendParticles(ParticleTypes.END_ROD, c.x, c.y + 5.2, c.z, 2, 0.3, 0.3, 0.3, 0.01);
        if (tickCount % 6 == 0) {
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 3.0F, 1.8F);
        }
        for (LivingEntity e : victims(level, c, BEAM_LENGTH + 1)) {
            Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            Integer last = beamHits.get(e.getUUID());
            if (along >= BEAM_INNER - 0.5 && along <= BEAM_LENGTH + 0.5 && side <= 0.8 + e.getBbWidth() / 2
                    && Math.abs(e.getY() - c.y) < 3.0 && (last == null || tickCount - last >= 10)) {
                beamHits.put(e.getUUID(), tickCount);
                hurt(level, e, 14.0F);
                e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0), this);
            }
        }
    }

    /** One volley of the shattered sky: a falling shard on every player and three strays. */
    private void volley(ServerLevel level) {
        List<Vec3> at = new ArrayList<>();
        for (LivingEntity e : victims(level, position(), 26.0)) {
            at.add(floorUnder(level, e.position()));
        }
        double max = rim() - 1.0;
        for (int i = 0, tries = 0; i < 3 && tries < 15; tries++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = random.nextDouble() * max;
            Vec3 p = safeSpot(level, centre().x + Math.cos(a) * r, centre().z + Math.sin(a) * r);
            if (p != null) {
                at.add(p);
                i++;
            }
        }
        for (Vec3 p : at) {
            addEffect(fallingShard(p, 16, 1.6, 13.0F));
        }
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    // ------------------------------------------------------------------ phase 3: the disc cracks

    private void beginShatter(ServerLevel level) {
        shatterGuard = 70;
        cracks.clear();
        double base = random.nextDouble() * 360.0;
        for (int i = 0; i < CRACKS; i++) {
            cracks.add(base + i * 360.0 / CRACKS + (random.nextDouble() - 0.5) * 24.0);
        }
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 3.0F, 1.4F);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void completeShatter(ServerLevel level) {
        shatterGuard = 0;
        flareTimer = 100;
        specialTimer = 60;
        drawCracks(level, 1.0, ParticleTypes.EXPLOSION);
        addEffect(WayfarerBoss.wave(position(), radius, 0.7, 8.0F, ParticleTypes.REVERSE_PORTAL));
        level.playSound(null, this, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 4.0F, 0.3F);
        level.playSound(null, this, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 4.0F, 0.4F);
    }

    /** Particles along every fissure, out to {@code reach} (0..1) of the disc's radius. */
    private void drawCracks(ServerLevel level, double reach, ParticleOptions p) {
        Vec3 c = centre();
        double len = Math.max(2.0, radius * Math.min(1.0, reach));
        double step = p == ParticleTypes.EXPLOSION ? 3.0 : 0.8;
        for (double ang : cracks) {
            double a = Math.toRadians(ang);
            for (double d = 1.5; d <= len; d += step) {
                double jag = Math.sin(d * 1.7 + ang) * 0.35;
                double x = c.x + Math.cos(a) * d - Math.sin(a) * jag;
                double z = c.z + Math.sin(a) * d + Math.cos(a) * jag;
                level.sendParticles(p, x, c.y + 0.1, z, 1, 0.05, 0, 0.05, 0);
            }
        }
    }

    /** Phase 3 upkeep: the cracks smoulder, flare in turn, the rim crumbles, and the special moves are scheduled. */
    private void tickShattered(ServerLevel level) {
        Vec3 c = centre();
        double rim = rim();
        if (tickCount % 10 == 0) {
            drawCracks(level, 1.0, ParticleTypes.REVERSE_PORTAL);
            int n = (int) (rim * 6);
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(VOID_DUST, c.x + Math.cos(a) * rim, c.y + 0.2, c.z + Math.sin(a) * rim, 1, 0, 0.05, 0, 0);
            }
            for (int i = 0; i < 10; i++) {   // the outer disc crumbling
                double a = random.nextDouble() * Math.PI * 2;
                double r = rim + 0.5 + random.nextDouble() * Math.max(0.5, radius - rim);
                level.sendParticles(END_STONE_CRUMBS, c.x + Math.cos(a) * r, c.y + 0.3, c.z + Math.sin(a) * r, 2, 0.2, 0.1, 0.2, 0.05);
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, c.x + Math.cos(a) * r, c.y + 0.4, c.z + Math.sin(a) * r, 1, 0.2, 0.2, 0.2, 0.02);
            }
            for (LivingEntity e : victims(level, c, radius + 3.0)) {
                double r = flatDist(e.position(), c);
                if (r > rim + 0.3 && r < radius + 3.0 && Math.abs(e.getY() - c.y) < 4) {
                    hurt(level, e, 3.0F);
                }
            }
        }
        if (tickCount % 40 == 0) {
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.0F, 0.3F);
        }
        BossAttack cur = currentAttack();
        boolean light = cur == null || cur.name.equals("glaive") || cur.name.equals("thrust") || cur.name.equals("shards");
        if (--flareTimer <= 0 && light && !cracks.isEmpty()) {
            int first = random.nextInt(cracks.size());
            addEffect(crackFlare(cracks.get(first), 24));
            addEffect(crackFlare(cracks.get((first + cracks.size() / 2) % cracks.size()), 24));
            flareTimer = (int) Math.round((110 + random.nextInt(40)) * cycleSpeed());
        }
        LivingEntity t = getTarget();
        if (cur == null && !isStaggered() && t != null && t.isAlive() && --specialTimer <= 0) {
            chain(level, random.nextBoolean() ? "rain" : "dive");
            specialTimer = (int) Math.round((150 + random.nextInt(60)) * cooldownScale());
        }
    }

    private void resetShatter() {
        shattered = false;
        shatterGuard = 0;
        cracks.clear();
    }

    // ------------------------------------------------------------------ effects

    private static final DustParticleOptions VOID_DUST = new DustParticleOptions(0xB070FF, 1.3F);
    private static final BlockParticleOption END_STONE_CRUMBS =
            new BlockParticleOption(ParticleTypes.BLOCK, Blocks.END_STONE_BRICKS.defaultBlockState());

    /** A thrown halo shard: flies straight at 0.9 blocks a tick, stops on walls: 9 and a short glow. */
    private static Effect shard(Vec3 from, Vec3 dir, double maxDist, float damage) {
        double[] d = {0};
        return (boss, level) -> {
            d[0] += 0.9;
            Vec3 p = from.add(dir.scale(d[0]));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 2, 0.04, 0.04, 0.04, 0.0);
            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y, p.z, 1, 0.04, 0.04, 0.04, 0.0);
            BlockPos bp = BlockPos.containing(p);
            if (!level.getBlockState(bp).getCollisionShape(level, bp).isEmpty()) {
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 8, 0.2, 0.2, 0.2, 0.05);
                return true;
            }
            for (LivingEntity e : boss.victims(level, p, 1.5)) {
                if (e.getBoundingBox().inflate(0.3).contains(p)) {
                    boss.strike(level, e, damage, 0.2, 0.1);
                    e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 60, 0), boss);
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 12, 0.2, 0.2, 0.2, 0.06);
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 1.0F, 1.4F);
                    return true;
                }
            }
            return d[0] >= maxDist;
        };
    }

    /** A ring rolling in from {@code maxRadius} toward {@code c}: hits once whoever stands on it at ground level. */
    private static Effect inwardWave(Vec3 c, double maxRadius, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] r = {maxRadius};
        return (boss, level) -> {
            r[0] -= speed;
            int n = Math.max(16, (int) (r[0] * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, c.x + Math.cos(a) * r[0], c.y + 0.2, c.z + Math.sin(a) * r[0],
                        1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, c, r[0] + 1.5)) {
                double d = e.position().multiply(1, 0, 1).distanceTo(c.multiply(1, 0, 1));
                if (Math.abs(d - r[0]) <= 1.0 && e.getY() - c.y < 0.9 && hit.add(e.getUUID())) {
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage) && d > 0.1) {
                        Vec3 in = c.subtract(e.position()).multiply(1, 0, 1).normalize().scale(0.4);   // toward the centre
                        e.push(in.x, 0.3, in.z);
                        e.hurtMarked = true;
                    }
                }
            }
            return r[0] <= 1.0;
        };
    }

    /** A shard falling from the sky: a ring and falling light for {@code delay} ticks, then 13 in the ring. */
    private static Effect fallingShard(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, ParticleTypes.END_ROD);
                }
                level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 12.0 * (1.0 - (double) t[0] / delay), pos.z,
                        2, 0.05, 0.1, 0.05, 0);
                t[0]++;
                return false;
            }
            level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.4, pos.z, 20, radius * 0.4, 0.6, radius * 0.4, 0.08);
            level.sendParticles(ParticleTypes.WAX_ON, pos.x, pos.y + 0.4, pos.z, 10, radius * 0.4, 0.3, radius * 0.4, 0.05);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 1.5F, 0.8F);
            for (LivingEntity e : boss.victims(level, pos, radius + 1)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius + e.getBbWidth() / 2) {
                    e.hurtServer(level, boss.damageSources().mobAttack(boss), damage);
                }
            }
            return true;
        };
    }

    /** A fissure flares: light seeps along it for {@code delay} ticks, then it bursts: 10, a small lift, slowness. */
    private Effect crackFlare(double angle, int delay) {
        int[] t = {0};
        double a = Math.toRadians(angle);
        Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
        return (boss, level) -> {
            Vec3 c = centre();
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    for (double d = 1.5; d <= radius; d += 1.0) {
                        Vec3 p = c.add(dir.scale(d));
                        level.sendParticles(ParticleTypes.END_ROD, p.x, c.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                    }
                }
                if (t[0] == 0) {
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 0.5F);
                }
                t[0]++;
                return false;
            }
            for (double d = 1.5; d <= radius; d += 0.8) {
                Vec3 p = c.add(dir.scale(d));
                level.sendParticles(ParticleTypes.END_ROD, p.x, c.y + 0.5, p.z, 2, 0.15, 0.5, 0.15, 0.04);
                level.sendParticles(END_STONE_CRUMBS, p.x, c.y + 0.3, p.z, 2, 0.2, 0.2, 0.2, 0.05);
            }
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
            for (LivingEntity e : victims(level, c, radius + 2.0)) {
                Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                double along = to.dot(dir);
                double side = to.subtract(dir.scale(along)).length();
                if (along >= 1.0 && along <= radius + 1 && side <= 1.0 + e.getBbWidth() / 2 && Math.abs(e.getY() - c.y) < 1.2) {
                    hurt(level, e, 10.0F);
                    e.push(0, 0.4, 0);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                }
            }
            return true;
        };
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis (positive turns toward her right). */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    /** A 3D direction turned by {@code degrees} around the vertical axis, keeping its slope. */
    private static Vec3 tilt(Vec3 dir, double degrees) {
        Vec3 flat = rotate(dir, degrees);
        double h = Math.hypot(dir.x, dir.z);
        return new Vec3(flat.x * h, dir.y, flat.z * h).normalize();
    }

    // ------------------------------------------------------------------ brain: phase 3, ambience, fairness

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (shatterGuard > 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2.5, getZ(), 6, 0.6, 1.0, 0.6, 0.05);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (phase() == 1 && (shattered || shatterGuard > 0)) {
            resetShatter();   // the fight was reset: the disc heals
        }
        if (shatterGuard > 0) {
            shatterGuard--;
        }
        // never lost to the void: back to the centre if she ever leaves the disc
        Vec3 c = centre();
        if (getY() < c.y - 4 || flatDist(position(), c) > radius + 3) {
            Vec3 home = safeSpot(level, c.x, c.z);
            teleport(level, home != null ? home : c);
        }
        if (phase() == 2 && !shattered && getHealth() <= getMaxHealth() * PHASE_THREE_AT && currentAttack() == null
                && !isStaggered() && tickCount > roarUntil) {
            shattered = true;
            chain(level, "shatter");
        }
        if (shattered && shatterGuard == 0) {
            tickShattered(level);
        }
        if (tickCount % 8 == 0) {   // the halo's light and the orbiting shards
            Vec3 back = position().subtract(forward().scale(0.5));
            level.sendParticles(ParticleTypes.END_ROD, back.x, getY() + 5.0, back.z, 1, 0.5, 0.4, 0.5, 0.005);
            double a = tickCount * 0.105;
            level.sendParticles(ParticleTypes.WAX_ON, getX() + Math.cos(a) * 1.25, getY() + 2.1, getZ() + Math.sin(a) * 1.25,
                    1, 0, 0, 0, 0);
        }
        if (phase() == 2 && tickCount % 6 == 0) {   // the void climbing her robe
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 0.8, getZ(), 2, 0.5, 0.4, 0.5, 0.01);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        roarUntil = tickCount + MobAnims.FallenSeraph.TICKS[ROAR] + 5;
        // the engine's roar shoves everyone nearby; on a disc over the void that shove is replaced by a gentle one
        // that never points outward near the rim
        for (LivingEntity e : victims(level, position(), 7.5)) {
            Vec3 away = e.position().subtract(position()).multiply(1, 0, 1);
            Vec3 v = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize().scale(0.5);
            if (flatDist(e.position(), centre()) > radius - 6.0) {
                v = Vec3.ZERO;
            }
            e.setDeltaMovement(v.x, 0.3, v.z);
            e.hurtMarked = true;
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("fallen_seraph_ascended"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3.0, getZ(), 80, 1.2, 2.0, 1.2, 0.15);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1.0, getZ(), 60, 1.0, 1.0, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2.5, getZ(), 160, 1.2, 2.5, 1.2, 0.2);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 2.0, getZ(), 80, 1.0, 2.0, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        if (shattered) {
            drawCracks(level, 1.0, ParticleTypes.WAX_ON);   // the fissures close with her light
        }
        resetShatter();
    }
}
