package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
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

import static com.brasshaven.generated.MobAnims.FrostJarl.BASH;
import static com.brasshaven.generated.MobAnims.FrostJarl.BLIZZARD;
import static com.brasshaven.generated.MobAnims.FrostJarl.BREATH;
import static com.brasshaven.generated.MobAnims.FrostJarl.CLEAVE;
import static com.brasshaven.generated.MobAnims.FrostJarl.HUSCARLS;
import static com.brasshaven.generated.MobAnims.FrostJarl.LEAP;
import static com.brasshaven.generated.MobAnims.FrostJarl.RAMPAGE;
import static com.brasshaven.generated.MobAnims.FrostJarl.RIMEBURST;
import static com.brasshaven.generated.MobAnims.FrostJarl.ROAR;
import static com.brasshaven.generated.MobAnims.FrostJarl.SPIKES;
import static com.brasshaven.generated.MobAnims.FrostJarl.STAGGER;
import static com.brasshaven.generated.MobAnims.FrostJarl.WINTER;

/**
 * Le Jarl de givre (The Frost Jarl), the dead king of the Glacier Hall of the Frost Jarls: a 5.7-block Norse giant
 * frozen on his feet, a bearded Dane axe with a blade of blue ice in his right fist, a round shield crusted with frost
 * on his left arm, a beard of hoarfrost that parts for his ice breath. He waits in the domed hall inside the horn.
 * <p>A hard fight: 540 health, armour 14, poise 110, hits of 4 to 20. His shield blocks 65% of every blow that comes
 * from in front while he is between moves (strike during his recoveries, or from the sides). Three phases:
 * <ul>
 *     <li>Phase 1: <b>cleave</b> (a diagonal axe cut over 130 degrees, 18 + frost), <b>shield bash</b> (a shove with
 *     the shield, 12, throws you back, breaks a raised shield), <b>ice breath</b> (a cone of frost swept from his
 *     right to his left for 1.5 s: 4 every quarter second and it freezes you), <b>ice spikes</b> (the axe driven into
 *     the floor: spikes run out along a line, and one rises under the target), <b>jarl's leap</b> (he jumps onto a
 *     ring that follows you, 20 + a frost wave to jump), and every half minute his <b>frozen huscarls</b> (skeleton
 *     knights, two at most, more in co-op) rise from the ice.</li>
 *     <li>Phase 2 (a roar at 65%): faster, combos, <b>rampage</b> (three blows in a row, each telegraphed: cleave,
 *     backhand, overhead chop) and <b>rimeburst</b> (rings of spikes burst out from his axe one after another:
 *     stand in a gap between the rings, they are marked).</li>
 *     <li>Phase 3 (at 30%): <b>Fimbulwinter</b>, he kneels (invulnerable) and freezes the hall. From then on the
 *     floor freezes whoever stands still (move!), a frost pulse runs through the floor every 7 s (jump it), the
 *     breath and rimeburst grow, and every 13 s the <b>blizzard</b> rains three volleys of ice spikes on everyone.</li>
 * </ul>
 */
public class FrostJarl extends WayfarerBoss {
    public static final float WIDTH = 2.2F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double CLEAVE_RANGE = 6.8;
    private static final double CLEAVE_HALF = 65;
    private static final double BREATH_RANGE = 11.0;
    private static final double SPIKE_RADIUS = 1.4;
    private static final int HUSCARLS_EVERY = 640;
    private static final int PULSE_EVERY = 140;
    private static final int PULSE_WARN = 24;
    private static final int BLIZZARD_EVERY = 260;
    private static final double[] RINGS = {2.5, 5.5, 8.5, 11.5, 14.5};
    private static final double RING_HALF = 1.1;
    private static final DustParticleOptions RIME = new DustParticleOptions(0xBFEFFF, 1.4F);
    private static final DustParticleOptions FROST_BLUE = new DustParticleOptions(0x5AB8F0, 1.2F);

    /** Arena centre and radius (from the seal), saved with the boss. */
    private @Nullable Vec3 centre;
    private int radius = 15;
    /** Phase 3: the hall has frozen over. */
    private boolean frozen;
    /** Invulnerable while he freezes the hall. */
    private int winterGuard;
    /** The shield is raised square during the bash wind-up. */
    private boolean bashGuard;
    private int roarUntil = -1;
    private int huscarlTimer = 300;
    private int pulseTimer;
    private int blizzardTimer;
    private final List<Vec3> spots = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();
    private final Map<UUID, Vec3> lastPos = new HashMap<>();
    private @Nullable Vec3 leapFrom;
    private @Nullable Vec3 leapTo;

    public FrostJarl(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 540.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.FrostJarl.TICKS;
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
        return 110.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 4.5;
    }

    /** Phase 3 counts as a third stage of the fight (the base class knows only two). */
    public boolean isFrozenOver() {
        return frozen;
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
            output.putLong("JarlCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("JarlRadius", radius);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("JarlCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("JarlRadius", 15);
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // cleave: the axe hauled up over his right shoulder (0.9 s, the arc outlined in snow), then a diagonal cut
        // across his front
        out.add(BossAttack.of("cleave").anim(CLEAVE).timing(18, 4, 14).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, CLEAVE_RANGE, CLEAVE_HALF, ParticleTypes.SNOWFLAKE);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.POLAR_BEAR_WARNING, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, CLEAVE_RANGE, CLEAVE_HALF)) {
                        b.strike(level, e, 18.0F, 1.4, 0.25);
                        chill(e, 60);
                    }
                    sweepParticles(b, level, CLEAVE_RANGE - 1.5, CLEAVE_HALF);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 4.5 ? "bash" : "spikes");
                    }
                })
                .build());
        // shield bash: the shield raised square before him (0.6 s, guarded from the front, a short arc at his feet),
        // then a shove that throws you back and knocks a raised shield aside
        out.add(BossAttack.of("bash").anim(BASH).timing(12, 6, 12).range(0, 5.0).cooldown(70).weight(9)
                .start((b, level, t, tick) -> {
                    bashGuard = true;
                    struck.clear();
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 4.4, 50, ParticleTypes.ITEM_SNOWBALL);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    bashGuard = false;
                    b.lunge(0.75, 0.0);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick > 3) {
                        return;
                    }
                    for (LivingEntity e : arcVictims(b, level, 4.2, 50)) {
                        if (struck.add(e.getUUID())) {
                            boolean blocking = e instanceof Player p && p.isBlocking();
                            b.strike(level, e, 12.0F, 2.6, 0.4);
                            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 2), b);
                            if (blocking && e instanceof Player p) {        // the shield is knocked aside for 5 s
                                p.getCooldowns().addCooldown(p.getUseItem(), 100);
                                p.stopUsingItem();
                                level.playSound(null, p, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 1.5F, 0.8F);
                            }
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    bashGuard = false;
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 7.0 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "cleave");
                    }
                })
                .build());
        // ice breath: he rears back, chest swelling (1.0 s, the cone outlined in snow), then the breath pours out and
        // sweeps from his right to his left for 1.5 s; every quarter second it hurts and freezes
        out.add(BossAttack.of("breath").anim(BREATH).timing(20, 30, 14).range(0, 11.0).cooldown(150).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0 && b instanceof FrostJarl j) {
                        double sweep = j.breathSweep();
                        b.telegraphArc(level, BREATH_RANGE, sweep + 20, ParticleTypes.SNOWFLAKE);
                        for (double s : new double[]{sweep + 20, -sweep - 20}) {
                            Vec3 dir = rotate(b.forward(), s);
                            for (double d = 2; d < BREATH_RANGE; d += 1.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PLAYER_BREATH, SoundSource.HOSTILE, 3.0F, 0.4F);
                    }
                    level.sendParticles(ParticleTypes.SNOWFLAKE, b.getX(), b.getY() + 4.8, b.getZ(), 2, 0.6, 0.4, 0.6, 0.0);
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof FrostJarl j)) {
                        return;
                    }
                    double sweep = j.breathSweep();
                    double ang = sweep - 2 * sweep * tick / 29.0;           // from his right to his left
                    Vec3 dir = rotate(b.forward(), ang);
                    Vec3 mouth = b.position().add(0, 4.7, 0).add(b.forward().scale(1.3));
                    for (double d = 1; d <= BREATH_RANGE; d += 1.0) {
                        Vec3 p = mouth.add(dir.scale(d)).add(0, -4.2 * d / BREATH_RANGE, 0);
                        double spread = 0.1 + d * 0.12;
                        level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y, p.z, 2, spread, spread * 0.5, spread, 0.02);
                        if (d % 3 == 0) {
                            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y, p.z, 1, spread, spread * 0.4, spread, 0.01);
                        }
                    }
                    if (tick % 5 == 0) {
                        float dmg = j.frozen ? 5.0F : 4.0F;
                        double cos = Math.cos(Math.toRadians(20));
                        for (LivingEntity e : b.victims(level, b.position(), BREATH_RANGE + 1)) {
                            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
                            double dist = to.length();
                            if (dist <= BREATH_RANGE && dist > 0.5 && to.normalize().dot(dir) >= cos
                                    && e.getY() - b.getY() < 4.0) {
                                if (e.hurtServer(level, b.damageSources().mobAttack(b), dmg)) {
                                    chill(e, 45);
                                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), b);
                                }
                            }
                        }
                        level.playSound(null, b, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.0F, 1.6F);
                    }
                })
                .build());
        // ice spikes: the axe raised high (1.1 s, the line of spikes marked on the floor), then driven into the floor;
        // spikes run out along the line (three lines in phase 2) and one rises under the target (under every player
        // in phase 2)
        out.add(BossAttack.of("spikes").anim(SPIKES).timing(22, 24, 14).range(3.0, 20.0).cooldown(120).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        double[] fan = b.phase() == 2 ? new double[]{-22, 0, 22} : new double[]{0};
                        for (double a : fan) {
                            Vec3 dir = rotate(b.forward(), a);
                            for (double d = 2; d <= 18; d += 1.5) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof FrostJarl j)) {
                        return;
                    }
                    double[] fan = b.phase() == 2 ? new double[]{-22, 0, 22} : new double[]{0};
                    for (double a : fan) {
                        Vec3 dir = rotate(b.forward(), a);
                        for (double d = 2; d <= 18; d += 1.5) {
                            b.addEffect(iceSpike(b.position().add(dir.scale(d)), 4 + (int) Math.round(d * 1.1),
                                    SPIKE_RADIUS, 14.0F));
                        }
                    }
                    if (b.phase() == 2) {
                        for (LivingEntity e : b.victims(level, b.position(), 24.0)) {
                            if (e instanceof Player) {
                                b.addEffect(j.iceSpikeOn(e, 20, 1.6, 12.0F));
                            }
                        }
                    } else if (t != null) {
                        b.addEffect(j.iceSpikeOn(t, 20, 1.6, 12.0F));
                    }
                    Vec3 c = b.ahead(2.5);
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
                            c.x, c.y + 0.3, c.z, 40, 1.0, 0.2, 1.0, 0.2);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // jarl's leap: he crouches (1.0 s) while a ring follows the target, then locks; he springs and crashes down
        // on it half a second later: 20 and a frost wave to jump
        out.add(BossAttack.of("leap").anim(LEAP).timing(20, 10, 16).range(7.0, 22.0).cooldown(170).weight(7)
                .start((b, level, t, tick) -> {
                    leapTo = null;
                    leapFrom = null;
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof FrostJarl j)) {
                        return;
                    }
                    if (tick < 14 && t != null) {
                        j.leapTo = j.clampToArena(t.position());
                    }
                    if (j.leapTo != null && tick % 2 == 0) {
                        b.telegraphRing(level, j.leapTo, 3.5, tick < 14 ? ParticleTypes.SNOWFLAKE : FROST_BLUE);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.2, b.getZ(), 2, 0.8, 0, 0.8, 0.02);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FrostJarl j) {
                        j.leapFrom = b.position();
                        if (j.leapTo == null) {
                            j.leapTo = b.ahead(8);
                        }
                        Vec3 to = j.leapTo.subtract(b.position());
                        b.snapFacing((float) (Mth.atan2(to.z, to.x) * (180.0 / Math.PI)) - 90.0F);
                    }
                    level.playSound(null, b, SoundEvents.GOAT_LONG_JUMP, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof FrostJarl j) {
                        j.leapStep(level, tick);
                    }
                })
                .build());
        // frozen huscarls: never rolled; bossTick chains it every half minute while there is room. The axe thrust to
        // the sky with a bellow (0.8 s, rings of frost where they will rise), then slammed down: they rise from the ice
        out.add(BossAttack.of("huscarls").anim(HUSCARLS).timing(16, 4, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof FrostJarl j) {
                        j.pickHuscarlSpots(level);
                    }
                    level.playSound(null, b, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 p : spots) {
                            b.telegraphRing(level, p, 1.0, ParticleTypes.SNOWFLAKE);
                            level.sendParticles(RIME, p.x, p.y + 0.2, p.z, 3, 0.3, 0.1, 0.3, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FrostJarl j) {
                        j.raiseHuscarls(level);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // rampage: three blows, each with its own wind-up: a cleave from his right (0.8 s), a backhand from his left
        // (0.5 s later), an overhead chop down a line (0.6 s later); he turns toward you between the blows
        out.add(BossAttack.of("rampage").anim(RAMPAGE).phaseTwo().timing(16, 30, 16).range(0, 7.5).cooldown(170).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.5, 65, ParticleTypes.SNOWFLAKE);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.POLAR_BEAR_WARNING, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 10) {
                        for (LivingEntity e : arcVictims(b, level, 6.5, 65)) {
                            b.strike(level, e, 14.0F, 1.2, 0.2);
                            chill(e, 40);
                        }
                        sweepParticles(b, level, 5.0, 65);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F + tick * 0.02F);
                    } else if (tick == 22) {
                        for (LivingEntity e : lineVictims(b, level, 7.5, 1.5)) {
                            b.strike(level, e, 20.0F, 0.8, 0.5);
                            chill(e, 60);
                        }
                        for (int k = 0; k < 3; k++) {
                            b.addEffect(iceSpike(b.ahead(8.5 + k * 1.7), 6 + k * 3, SPIKE_RADIUS, 12.0F));
                        }
                        Vec3 c = b.ahead(3.5);
                        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
                                c.x, c.y + 0.3, c.z, 30, 0.8, 0.2, 0.8, 0.2);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    if ((tick == 3 || tick == 13) && t != null && b instanceof FrostJarl j) {
                        j.turnToward(t, 40.0F);
                    }
                    if (tick > 3 && tick < 10 && tick % 2 == 0) {
                        b.telegraphArc(level, 6.5, 65, ParticleTypes.SNOWFLAKE);
                    }
                    if (tick > 13 && tick < 22 && tick % 2 == 0) {
                        for (double d = 1.5; d <= 7.5; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 0.15, p.z, 2, 0.6, 0, 0.6, 0);
                        }
                    }
                })
                .build());
        // rimeburst: the axe spun and planted upright (1.1 s, the five rings shown on the floor); rings of spikes burst
        // outward one after another, 7 ticks apart (and back inward in phase 3): the marked gaps between rings are safe
        out.add(BossAttack.of("rimeburst").anim(RIMEBURST).phaseTwo().timing(22, 36, 14).range(0, 14.0).cooldown(230)
                .weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        for (double r : RINGS) {
                            b.telegraphRing(level, b.position(), r, ParticleTypes.SNOWFLAKE);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof FrostJarl j)) {
                        return;
                    }
                    Vec3 c = b.position();
                    for (int k = 0; k < RINGS.length; k++) {
                        b.addEffect(j.spikeRing(c, RINGS[k], 4 + k * 7, 13.0F));
                        if (j.frozen) {                                 // and back in, the same rings
                            b.addEffect(j.spikeRing(c, RINGS[RINGS.length - 1 - k], 44 + k * 6, 11.0F));
                        }
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // winter: he sinks to one knee, axe raised (1.5 s, invulnerable, frost climbing him), then drives it into the
        // floor: a frost nova rolls out (jump it) and the hall freezes over
        out.add(BossAttack.of("winter").anim(WINTER).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    winterGuard = 50;
                    level.playSound(null, b, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.25, ParticleTypes.SNOWFLAKE);
                        level.playSound(null, b, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.02F);
                    }
                    level.sendParticles(RIME, b.getX(), b.getY() + 2.5, b.getZ(), 6, 1.0, 1.5, 1.0, 0.02);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof FrostJarl j) {
                        j.freezeHall(level);
                    }
                })
                .build());
        // blizzard: the axe raised to the oculus, turning (1.2 s), then held high while ice spikes rain from the
        // storm: three volleys a second apart, a ring under every player (it follows for a third of its warning,
        // then locks) and a few strays
        out.add(BossAttack.of("blizzard").anim(BLIZZARD).phaseTwo().timing(24, 40, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.SNOWFLAKE, b.getX(), b.getY() + 7.5, b.getZ(), 20, 3.0, 0.5, 3.0, 0.05);
                        level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 8.0, b.getZ(), 6, 2.5, 0.3, 2.5, 0.01);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof FrostJarl j)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    List<LivingEntity> targets = b.victims(level, j.centre(), j.radius + 4.0);
                    for (int v = 0; v < 3; v++) {
                        for (LivingEntity e : targets) {
                            b.addEffect(delayed(v * 18, j.iceSpikeOn(e, 20, 1.7, 14.0F)));
                        }
                        for (int i = 0; i < b.scaledCount(3); i++) {
                            double a = b.getRandom().nextDouble() * Math.PI * 2;
                            double r = 3 + b.getRandom().nextDouble() * Math.max(4, j.radius - 4);
                            Vec3 p = j.centre().add(Math.cos(a) * r, 0, Math.sin(a) * r);
                            b.addEffect(delayed(v * 18 + i * 3, iceSpike(p, 20, 1.7, 14.0F)));
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0 && b instanceof FrostJarl j) {
                        Vec3 c = j.centre();
                        level.sendParticles(ParticleTypes.SNOWFLAKE, c.x, c.y + 9, c.z, 40, j.radius * 0.6, 1.0, j.radius * 0.6, 0.05);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** Half-angle of the breath's sweep (wider once the hall is frozen). */
    private double breathSweep() {
        return frozen ? 40.0 : (phase() == 2 ? 32.0 : 25.0);
    }

    private static List<LivingEntity> arcVictims(WayfarerBoss b, ServerLevel level, double range, double halfAngle) {
        Vec3 fwd = b.forward();
        double cos = Math.cos(Math.toRadians(halfAngle));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : b.victims(level, b.position(), range + 1)) {
            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                out.add(e);
            }
        }
        return out;
    }

    private static List<LivingEntity> lineVictims(WayfarerBoss b, ServerLevel level, double length, double halfWidth) {
        Vec3 fwd = b.forward();
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : b.victims(level, b.position(), length + 1)) {
            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= length && side <= halfWidth + e.getBbWidth() / 2) {
                out.add(e);
            }
        }
        return out;
    }

    private static void sweepParticles(WayfarerBoss b, ServerLevel level, double r, double halfAngle) {
        for (double a = -halfAngle; a <= halfAngle; a += 10) {
            Vec3 p = b.position().add(rotate(b.forward(), a).scale(r));
            level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.2, p.z, 3, 0.2, 0.3, 0.2, 0.02);
        }
        Vec3 c = b.ahead(r * 0.6);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.4, c.z, 1, 0, 0, 0, 0);
    }

    /** Frost bites: frozen ticks pile up (the vanilla freeze overlay and slowdown, then freezing damage). */
    private static void chill(LivingEntity e, int ticks) {
        int cap = e.getTicksRequiredToFreeze() + 120;
        e.setTicksFrozen(Math.min(cap, e.getTicksFrozen() + ticks));
    }

    /** Turn toward {@code target} by at most {@code maxTurn} degrees, then keep that facing. */
    private void turnToward(LivingEntity target, float maxTurn) {
        double dx = target.getX() - getX();
        double dz = target.getZ() - getZ();
        float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private Vec3 clampToArena(Vec3 p) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(3.0, radius - 2.5);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, getY(), c.z + off.z);
    }

    /** One tick of the leap: an arc from where he sprang to the locked ring, landing on the last tick. */
    private void leapStep(ServerLevel level, int tick) {
        if (leapFrom == null || leapTo == null) {
            return;
        }
        resetFallDistance();
        double f = Math.min(1.0, (tick + 1) / 10.0);
        Vec3 want = leapFrom.add(leapTo.subtract(leapFrom).scale(f)).add(0, 5.0 * Math.sin(Math.PI * f), 0);
        Vec3 d = want.subtract(position());
        setDeltaMovement(d);
        hurtMarked = true;
        level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 1, getZ(), 4, 0.6, 0.6, 0.6, 0.02);
        if (tick % 2 == 0) {
            telegraphRing(level, leapTo, 3.5, FROST_BLUE);
        }
        if (tick == 9) {
            Vec3 c = leapTo;
            hitCircle(level, c, 3.5, 20.0F, 1.0, 0.5);
            for (LivingEntity e : victims(level, c, 3.5)) {
                chill(e, 60);
            }
            addEffect(WayfarerBoss.wave(c, 10, 0.5, 9.0F, ParticleTypes.SNOWFLAKE));
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
                    c.x, c.y + 0.3, c.z, 60, 1.6, 0.3, 1.6, 0.25);
            level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 2, 0.6, 0.1, 0.6, 0);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
    }

    private int minions(ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(centre())).inflate(radius + 12, 12, radius + 12),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    /** Huscarls alive at most: two (three once the hall is frozen), +1 per two extra players. */
    private int huscarlCap() {
        return scaledCount(frozen ? 3 : 2);
    }

    private void pickHuscarlSpots(ServerLevel level) {
        spots.clear();
        int room = Math.max(0, huscarlCap() - minions(level));
        int n = Math.min(room, scaledCount(2));
        double base = getRandom().nextDouble() * Math.PI * 2;
        for (int i = 0; i < n; i++) {
            double a = base + Math.PI * 2 * i / Math.max(1, n);
            spots.add(clampToArena(position().add(Math.cos(a) * 5.0, 0, Math.sin(a) * 5.0)));
        }
    }

    private void raiseHuscarls(ServerLevel level) {
        level.playSound(null, this, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.5F);
        for (Vec3 p : spots) {
            Mob m = ModEntities.SKELETON_KNIGHT.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (m == null) {
                continue;
            }
            m.snapTo(p.x, p.y, p.z, getYRot(), 0);
            m.addTag(MINION_TAG);
            m.setTarget(getTarget());
            level.addFreshEntity(m);
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
                    p.x, p.y + 0.5, p.z, 30, 0.4, 0.8, 0.4, 0.15);
            level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1, p.z, 20, 0.4, 0.8, 0.4, 0.05);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
        spots.clear();
    }

    /**
     * An ice spike on {@code pos}: a ring of snow for {@code warn} ticks (it whitens just before), then the spike
     * bursts up: {@code damage}, thrown up, frozen. It stays a moment as a pillar of ice dust.
     */
    private static Effect iceSpike(Vec3 pos, int warn, double radius, float damage) {
        int[] t = {0};
        BlockParticleOption ice = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState());
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, warn - k <= 6 ? ParticleTypes.ITEM_SNOWBALL : ParticleTypes.SNOWFLAKE);
                }
                return false;
            }
            if (k == warn) {
                level.sendParticles(ice, pos.x, pos.y + 1.0, pos.z, 24, radius * 0.3, 0.9, radius * 0.3, 0.1);
                level.sendParticles(ParticleTypes.ITEM_SNOWBALL, pos.x, pos.y + 1.2, pos.z, 10, radius * 0.3, 0.8, radius * 0.3, 0.05);
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 0.9F, 0.7F);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (flatDist(e.position(), pos) <= radius + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 2.0) {
                        boss.strike(level, e, damage, 0.3, 0.9);
                        chill(e, 50);
                    }
                }
                return false;
            }
            if (k % 2 == 0) {                                  // the spike lingers a moment
                for (double y = 0.2; y < 2.4; y += 0.5) {
                    level.sendParticles(RIME, pos.x, pos.y + y, pos.z, 1, 0.1, 0.05, 0.1, 0);
                }
            }
            return k >= warn + 8;
        };
    }

    /** An ice spike that follows {@code target} for the first third of its warning, then locks where it stands. */
    private Effect iceSpikeOn(LivingEntity target, int warn, double radius, float damage) {
        int lock = Math.max(4, warn / 3);
        int[] t = {0};
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (!target.isAlive()) {
                    return true;
                }
                if (t[0]++ < lock) {
                    if (t[0] % 2 == 0) {
                        boss.telegraphRing(level, target.position(), radius, ParticleTypes.SNOWFLAKE);
                    }
                    return false;
                }
                inner[0] = iceSpike(target.position(), warn - lock, radius, damage);
            }
            return inner[0].tick(boss, level);
        };
    }

    /**
     * A ring of spikes round {@code c} at {@code r}: shown faintly while it waits, whiter for its last 6 ticks, then
     * it bursts: whoever stands within {@link #RING_HALF} of the ring takes {@code damage} and is thrown up.
     */
    private Effect spikeRing(Vec3 c, double r, int delay, float damage) {
        int[] t = {0};
        BlockParticleOption ice = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState());
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 4 == 0 || delay - k <= 6 && k % 2 == 0) {
                    boss.telegraphRing(level, c, r, delay - k <= 6 ? ParticleTypes.ITEM_SNOWBALL : ParticleTypes.SNOWFLAKE);
                }
                return false;
            }
            int n = Math.max(10, (int) (r * 3));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(ice, c.x + Math.cos(a) * r, c.y + 0.8, c.z + Math.sin(a) * r, 3, 0.25, 0.6, 0.25, 0.08);
            }
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 1.6F, 0.5F + (float) r * 0.03F);
            for (LivingEntity e : boss.victims(level, c, r + RING_HALF + 1)) {
                double d = flatDist(e.position(), c);
                if (Math.abs(d - r) <= RING_HALF + e.getBbWidth() / 2 && Math.abs(e.getY() - c.y) < 2.0) {
                    boss.strike(level, e, damage, 0.3, 0.8);
                    chill(e, 40);
                }
            }
            return true;
        };
    }

    /** Phase 3 starts: a frost nova, the floor freezes, he is faster from now on. */
    private void freezeHall(ServerLevel level) {
        frozen = true;
        pulseTimer = 100;
        blizzardTimer = 120;
        Vec3 c = position();
        addEffect(WayfarerBoss.wave(c, Math.max(10, radius), 0.55, 12.0F, ParticleTypes.SNOWFLAKE));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("frost_jarl_winter"), 0.15,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 h = centre();
        level.sendParticles(ParticleTypes.SNOWFLAKE, h.x, h.y + 0.3, h.z, 300, radius * 0.6, 0.1, radius * 0.6, 0.02);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.BLUE_ICE.defaultBlockState()),
                c.x, c.y + 0.5, c.z, 80, 2.0, 0.3, 2.0, 0.3);
        level.playSound(null, this, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    /** Phase 3: the frozen floor bites whoever stands still, and pulses (jump it). */
    private void tickWinter(ServerLevel level) {
        Vec3 c = centre();
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.SNOWFLAKE, c.x, c.y + 0.2, c.z, 12, radius * 0.6, 0.05, radius * 0.6, 0.01);
        }
        if (tickCount % 5 == 0) {
            for (LivingEntity e : victims(level, c, radius + 2.0)) {
                if (!(e instanceof Player)) {
                    continue;
                }
                Vec3 prev = lastPos.put(e.getUUID(), e.position());
                boolean still = prev != null && flatDist(prev, e.position()) < 0.6;
                if (still && e.onGround()) {
                    chill(e, 22);                               // net +12 a quarter second against the thaw
                    level.sendParticles(RIME, e.getX(), e.getY() + 0.3, e.getZ(), 4, 0.3, 0.2, 0.3, 0);
                }
                if (tickCount % 20 == 0 && e.getTicksFrozen() >= e.getTicksRequiredToFreeze()) {
                    if (e.hurtServer(level, damageSources().mobAttack(this), 3.0F)) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 2), this);
                    }
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.ICE.defaultBlockState()),
                            e.getX(), e.getY() + 1, e.getZ(), 10, 0.3, 0.5, 0.3, 0.1);
                }
            }
        }
        // the frost pulse: the floor whitens round every player for 1.2 s, then a pulse hits whoever is on the ground
        if (--pulseTimer == PULSE_WARN) {
            level.playSound(null, c.x, c.y, c.z, SoundEvents.POWDER_SNOW_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 2.0F, 0.4F);
        }
        if (pulseTimer > 0 && pulseTimer <= PULSE_WARN) {
            if (pulseTimer % 3 == 0) {
                level.sendParticles(ParticleTypes.ITEM_SNOWBALL, c.x, c.y + 0.15, c.z, 40, radius * 0.6, 0.02, radius * 0.6, 0);
                for (LivingEntity e : victims(level, c, radius + 2.0)) {
                    telegraphRing(level, e.position(), 1.2, ParticleTypes.ITEM_SNOWBALL);
                }
            }
        } else if (pulseTimer <= 0) {
            pulseTimer = (int) Math.round(PULSE_EVERY * cooldownScale());
            level.sendParticles(ParticleTypes.SNOWFLAKE, c.x, c.y + 0.4, c.z, 200, radius * 0.6, 0.2, radius * 0.6, 0.08);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
            for (LivingEntity e : victims(level, c, radius + 2.0)) {
                if (e.onGround() && Math.abs(e.getY() - c.y) < 1.5 && flatDist(e.position(), c) <= radius + 1.0) {
                    if (e.hurtServer(level, damageSources().mobAttack(this), 7.0F)) {
                        chill(e, 60);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
                    }
                }
            }
        }
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis (positive: toward his right). */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    /** Runs {@code inner} after {@code delay} ticks. */
    private static Effect delayed(int delay, Effect inner) {
        int[] t = {0};
        return (boss, level) -> t[0]++ >= delay && inner.tick(boss, level);
    }

    // ------------------------------------------------------------------ the shield, phase 3, ambience

    private boolean isFrontal(DamageSource source) {
        Vec3 from = source.getSourcePosition();
        if (from == null) {
            return false;
        }
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        if (to.lengthSqr() < 1.0E-4) {
            return false;
        }
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        Vec3 fwd = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
        return to.normalize().dot(fwd) >= Math.cos(Math.toRadians(55));
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (winterGuard > 0) {
            level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 2.5, getZ(), 6, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        // his shield faces you while he walks and while he readies the bash: frontal blows lose 65%
        if (!isStaggered() && (currentAttack() == null || bashGuard) && source.getEntity() != null
                && !source.is(DamageTypeTags.BYPASSES_SHIELD) && isFrontal(source)) {
            amount *= 0.35F;
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 1.5F, 0.6F + random.nextFloat() * 0.2F);
            Vec3 p = position().add(forward().scale(1.2));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 2.0, p.z, 8, 0.3, 0.4, 0.3, 0.2);
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (winterGuard > 0) {
            winterGuard--;
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        if (phase() == 1 && frozen) {                   // the fight was reset: the hall thaws
            frozen = false;
            roarUntil = -1;
            lastPos.clear();
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("frost_jarl_winter"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("frost_jarl_wrath"));
            }
        }
        boolean free = fighting && currentAttack() == null && !isStaggered() && tickCount > roarUntil;
        if (fighting && --huscarlTimer <= 0 && free && huscarlCap() - minions(level) > 0) {
            huscarlTimer = (int) Math.round(HUSCARLS_EVERY * cooldownScale());
            chain(level, "huscarls");
            free = false;
        }
        if (phase() == 2 && free) {
            if (!frozen && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "winter");
            } else if (frozen && --blizzardTimer <= 0) {
                blizzardTimer = (int) Math.round(BLIZZARD_EVERY * cooldownScale());
                chain(level, "blizzard");
            }
        }
        if (frozen && fighting) {
            tickWinter(level);
        }
        // ambience: frost breath from the beard, rime falling off him, the axe's glowing edge
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        if (tickCount % (frozen ? 3 : 6) == 0) {
            double hx = getX() - Mth.sin(yaw) * 1.0;
            double hz = getZ() + Mth.cos(yaw) * 1.0;
            level.sendParticles(ParticleTypes.SNOWFLAKE, hx, getY() + 4.6, hz, 1, 0.15, 0.1, 0.15, 0.01);
        }
        if (tickCount % 10 == 0) {
            level.sendParticles(RIME, getX(), getY() + 3.0, getZ(), 2, 0.9, 1.4, 0.9, 0);
        }
        if (tickCount % 80 == 0) {
            level.playSound(null, this, SoundEvents.PLAYER_BREATH, SoundSource.HOSTILE, 1.0F, 0.4F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("frost_jarl_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        addEffect(WayfarerBoss.wave(position(), 9, 0.5, 6.0F, ParticleTypes.SNOWFLAKE));
        level.playSound(null, this, SoundEvents.GOAT_HORN_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 2.5, getZ(), 80, 1.5, 2.0, 1.5, 0.08);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(blockPosition()).inflate(40),
                m -> m.entityTags().contains(MINION_TAG))) {
            level.sendParticles(ParticleTypes.SNOWFLAKE, m.getX(), m.getY() + 1, m.getZ(), 15, 0.3, 0.6, 0.3, 0.05);
            m.discard();
        }
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()),
                getX(), getY() + 2.5, getZ(), 120, 1.2, 2.0, 1.2, 0.3);
        level.sendParticles(ParticleTypes.SNOWFLAKE, getX(), getY() + 3, getZ(), 150, 2.0, 2.5, 2.0, 0.1);
        level.playSound(null, this, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.GOAT_HORN_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }
}
