package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.SoulReaper.COMBO;
import static com.brasshaven.generated.MobAnims.SoulReaper.ERUPT;
import static com.brasshaven.generated.MobAnims.SoulReaper.GRAB;
import static com.brasshaven.generated.MobAnims.SoulReaper.LASH;
import static com.brasshaven.generated.MobAnims.SoulReaper.REAP;
import static com.brasshaven.generated.MobAnims.SoulReaper.ROAR;
import static com.brasshaven.generated.MobAnims.SoulReaper.STAGGER;
import static com.brasshaven.generated.MobAnims.SoulReaper.SUMMON;
import static com.brasshaven.generated.MobAnims.SoulReaper.SWEEP;
import static com.brasshaven.generated.MobAnims.SoulReaper.THROW;
import static com.brasshaven.generated.MobAnims.SoulReaper.WAVE;

/**
 * La Faucheuse des âmes (The Soul Reaper): boss of the Tour des âmes, fought on the summit platform.
 * A 4.5-block reaper that floats on its own soul fire (no gravity, a private hover/drift brain that keeps it
 * inside the arena) and fights with a gigantic scythe and a soul lantern on a chain.
 * <ul>
 *     <li>Phase 1: wide scythe sweep (arc), forehand/backhand combo, scythe throw that spins out along a line and
 *     comes back, a two-handed slam sending a soul-fire ring (jump it), a teleport behind the target followed by a
 *     delayed chop, and a lantern-chain lash that pulls and bursts into soul fire.</li>
 *     <li>Phase 2 (after a roar): faster drift, combos chain into each other, soul eruptions under every player and
 *     across the arena, minions (wither skeletons and vexes as soul wisps), and the reaping grab that lifts a
 *     victim, drains it and hurls it away.</li>
 * </ul>
 */
public class SoulReaper extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 4.4F;
    /** Height the reaper floats above the floor (blocks). */
    private static final double HOVER = 0.9;

    private @Nullable Vec3 center;
    private int radius = 12;
    private int roarTimer;
    private int strafeDir = 1;
    private @Nullable LivingEntity grabbed;

    public SoulReaper(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SoulReaper.TICKS;
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
        return 85.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    // ------------------------------------------------------------------ arena memory, goals

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.center = Vec3.atBottomCenterOf(c);
        this.radius = r;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (center != null) {
            output.putLong("ReaperCenter", BlockPos.containing(center).asLong());
        }
        output.putInt("ReaperRadius", radius);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("ReaperCenter", Long.MIN_VALUE);
        center = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("ReaperRadius", 12);
    }

    /** The reaper floats: its own drift goal replaces the walking chase of other bosses. */
    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new DriftGoal());
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 16.0F));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    private Vec3 arenaCenter() {
        if (center == null) {
            center = position();
        }
        return center;
    }

    private boolean busy() {
        return currentAttack() != null || isStaggered() || roarTimer > 0;
    }

    // ------------------------------------------------------------------ geometry helpers

    /** Top of the first solid block at or below {@code y} (scanning 12 blocks), or NaN over the void. */
    private double floorY(ServerLevel level, double x, double y, double z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(y + 0.5), Mth.floor(z));
        for (int i = 0; i < 12; i++) {
            if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                return p.getY() + 1.0;
            }
            p.move(0, -1, 0);
        }
        return Double.NaN;
    }

    /** The point on the floor under {@code v} (or v itself over the void). */
    private Vec3 ground(ServerLevel level, Vec3 v) {
        double y = floorY(level, v.x, v.y + 1.0, v.z);
        return Double.isNaN(y) ? v : new Vec3(v.x, y, v.z);
    }

    /** Pull a point back inside the arena circle (margin in blocks). */
    private Vec3 clampToArena(Vec3 v, double margin) {
        Vec3 c = arenaCenter();
        Vec3 d = new Vec3(v.x - c.x, 0, v.z - c.z);
        double max = Math.max(2.0, radius - margin);
        if (d.length() > max) {
            d = d.normalize().scale(max);
        }
        return new Vec3(c.x + d.x, v.y, c.z + d.z);
    }

    /** Ground telegraph of an arc in front, drawn on the floor (the reaper floats above it). */
    private void arcOnFloor(ServerLevel level, double range, double halfAngle, ParticleOptions particle) {
        Vec3 f = forward();
        double base = Math.atan2(f.z, f.x);
        double floor = ground(level, position()).y;
        for (double a = -halfAngle; a <= halfAngle; a += Math.max(6, halfAngle / 7)) {
            double r = Math.toRadians(a) + base;
            for (double d = range * 0.5; d <= range; d += range * 0.5) {
                level.sendParticles(particle, getX() + Math.cos(r) * d, floor + 0.15, getZ() + Math.sin(r) * d, 1, 0, 0, 0, 0);
            }
        }
    }

    /** Ground telegraph of a straight line in front. */
    private void lineOnFloor(ServerLevel level, double length, ParticleOptions particle) {
        Vec3 f = forward();
        double floor = ground(level, position()).y;
        for (double d = 1.0; d <= length; d += 0.8) {
            level.sendParticles(particle, getX() + f.x * d, floor + 0.15, getZ() + f.z * d, 1, 0.05, 0, 0.05, 0);
        }
    }

    private boolean inLine(LivingEntity e, double length, double halfWidth) {
        Vec3 fwd = forward();
        Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
        double along = to.dot(fwd);
        double side = to.subtract(fwd.scale(along)).length();
        return along >= 0 && along <= length && side <= halfWidth + e.getBbWidth() / 2;
    }

    private static WayfarerBoss.Effect withSound(Vec3 pos, WayfarerBoss.Effect inner) {
        return (boss, level) -> {
            boolean done = inner.tick(boss, level);
            if (done) {
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.SOUL_ESCAPE, SoundSource.HOSTILE, 1.6F, 0.6F);
            }
            return done;
        };
    }

    /** A soul eruption on the floor at {@code at}: warned by drifting souls, then a pillar of soul fire. */
    private void erupt(ServerLevel level, Vec3 at, int delay, double r, float damage) {
        Vec3 g = ground(level, clampToArena(at, 1.0));
        addEffect(withSound(g, WayfarerBoss.eruption(g, delay, r, damage, ParticleTypes.SOUL, ParticleTypes.SOUL_FIRE_FLAME)));
    }

    /**
     * The thrown scythe: spins out along {@code dir} for {@code outTicks}, then flies back to the reaper. Hits each
     * victim at most once on the way out and once on the way back.
     */
    private WayfarerBoss.Effect thrownScythe(Vec3 origin, Vec3 dir, double reach, int outTicks, float damage) {
        Set<UUID> hitOut = new HashSet<>();
        Set<UUID> hitBack = new HashSet<>();
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            boolean out = k <= outTicks;
            double f = out ? (double) k / outTicks : 1.0 - (double) (k - outTicks) / outTicks;
            Vec3 from = out ? origin : boss.position();
            Vec3 p = from.add(dir.scale(reach * Math.sin(f * Math.PI / 2))).add(0, 1.4, 0);
            for (int i = 0; i < 4; i++) { // the spinning crescent
                double a = k * 0.9 + i * Math.PI / 2;
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x + Math.cos(a) * 1.4, p.y, p.z + Math.sin(a) * 1.4,
                        1, 0, 0, 0, 0);
            }
            if (k % 2 == 0) {
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
            if (k % 5 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.4F, 0.45F);
            }
            for (LivingEntity e : boss.victims(level, p, 2.5)) {
                if (e.position().multiply(1, 0, 1).distanceTo(p.multiply(1, 0, 1)) <= 1.8 && Math.abs(e.getY() + 1 - p.y) < 2.2
                        && (out ? hitOut : hitBack).add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.7, 0.3);
                }
            }
            return k >= outTicks * 2;
        };
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // 1. wide sweep: the scythe hauled back over the right shoulder, a flat crescent across the front
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(16, 4, 14).range(0, 6.0).cooldown(40).weight(12)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WITHER_SKELETON_AMBIENT,
                        SoundSource.HOSTILE, 1.5F, 0.5F))
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        arcOnFloor(level, 6.0, 100, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.5, 0.0);
                    b.hitArc(level, 6.0, 100, 15.0F, 1.3);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 1.5F, 0.8F);
                    Vec3 p = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 4, 2.0, 0.2, 2.0, 0);
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 1.6, p.z, 30, 2.5, 0.2, 2.5, 0.02);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "combo");
                    }
                })
                .build());

        // 2. combo: forehand at 0.7 s, the blade spun round the snath, a wider backhand at 1.2 s
        out.add(BossAttack.of("combo").anim(COMBO).timing(14, 12, 16).range(0, 6.0).cooldown(70).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        arcOnFloor(level, 5.5, 95, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.4, 0.0);
                    b.hitArc(level, 5.5, 95, 13.0F, 1.0);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 4) {
                        arcOnFloor(level, 6.0, 110, ParticleTypes.SOUL);
                    }
                    if (tick == 10) {
                        b.lunge(0.6, 0.0);
                        b.hitArc(level, 6.0, 110, 14.0F, 1.5);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.4F);
                        Vec3 p = b.ahead(3.0);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 4, 2.0, 0.2, 2.0, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "wave");
                    }
                })
                .build());

        // 3. scythe throw: drawn back for 0.9 s, hurled spinning 14 blocks down a line and back to the hand
        out.add(BossAttack.of("throw").anim(THROW).timing(18, 30, 12).range(5.0, 18.0).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        lineOnFloor(level, 14.0, ParticleTypes.SOUL);
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(thrownScythe(b.position(), b.forward(), 14.0, 15, 13.0F));
                    level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "reap");
                    }
                })
                .build());

        // 4. soul wave: scythe raised two-handed (1 s), the blade driven into the floor, a ring to jump over
        out.add(BossAttack.of("wave").anim(WAVE).timing(20, 3, 18).range(0, 8.0).cooldown(90).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, ground(level, b.ahead(3.0)), 3.5, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                    if (tick == 12) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 1.2F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = ground(level, b.ahead(3.0));
                    b.hitCircle(level, c, 3.5, 16.0F, 1.0, 0.6);
                    b.addEffect(WayfarerBoss.wave(c, radius + 2, b.phase() == 2 ? 0.5 : 0.42, 10.0F, ParticleTypes.SOUL_FIRE_FLAME));
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, c.x, c.y + 0.3, c.z, 80, 1.5, 0.3, 1.5, 0.15);
                    level.sendParticles(ParticleTypes.SOUL, c.x, c.y + 0.5, c.z, 30, 1.5, 0.5, 1.5, 0.05);
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.SOUL_ESCAPE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 2) { // a second, slower ring right behind the first
                        b.addEffect(WayfarerBoss.wave(ground(level, b.ahead(3.0)), radius + 2, 0.3, 9.0F, ParticleTypes.SOUL));
                    }
                })
                .build());

        // 5. reap: vanishes into soul smoke, reappears behind the target, rears up (0.8 s) and chops
        out.add(BossAttack.of("reap").anim(REAP).timing(16, 3, 16).range(4.0, 20.0).cooldown(140).weight(7)
                .start((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 2, b.getZ(), 40, 0.6, 1.5, 0.6, 0.05);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 2, b.getZ(), 30, 0.6, 1.5, 0.6, 0.02);
                    level.playSound(null, b, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.5F);
                    if (t != null) {
                        Vec3 look = Vec3.directionFromRotation(0, t.getYRot());
                        Vec3 behind = clampToArena(t.position().subtract(look.scale(2.8)), 1.5);
                        double fy = floorY(level, behind.x, t.getY() + 1, behind.z);
                        if (!Double.isNaN(fy)) {
                            b.teleportTo(behind.x, fy + HOVER, behind.z);
                        }
                    }
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, b.getX(), b.getY() + 1, b.getZ(), 40, 0.5, 1.2, 0.5, 0.03);
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                    if (tick % 4 == 2) {
                        arcOnFloor(level, 5.0, 55, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.6, 0.0);
                    b.hitArc(level, 5.0, 55, 18.0F, 1.2);
                    Vec3 p = ground(level, b.ahead(3.0));
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.2, p.z, 40, 0.4, 0.1, 1.5, 0.08);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.4F);
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.SOUL_SAND_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "wave");
                    }
                })
                .build());

        // 6. lantern lash: the chain wheeled overhead (0.7 s), cracked 9 blocks forward; pulls and bursts
        out.add(BossAttack.of("lash").anim(LASH).timing(14, 4, 14).range(3.0, 10.0).cooldown(60).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        lineOnFloor(level, 9.0, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 1.2F, 0.6F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), 10.0)) {
                        if (inLine(e, 9.0, 1.1)) {
                            b.strike(level, e, 12.0F, 0.0, 0.2);
                            Vec3 pull = b.position().subtract(e.position()).multiply(1, 0, 1).normalize().scale(0.9);
                            e.push(pull.x, 0.25, pull.z);
                            e.hurtMarked = true;
                            e.setRemainingFireTicks(60);
                        }
                    }
                    Vec3 end = ground(level, b.ahead(9.0));
                    b.hitCircle(level, end, 2.2, 8.0F, 0.6, 0.4);
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, end.x, end.y + 0.5, end.z, 50, 1.0, 0.6, 1.0, 0.08);
                    level.playSound(null, end.x, end.y, end.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.6F, 0.5F);
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.6F, 0.5F);
                })
                .build());

        // 7. (phase 2) soul eruptions: arms flung up, pillars of soul fire under every player and across the arena
        out.add(BossAttack.of("erupt").anim(ERUPT).phaseTwo().timing(16, 30, 16).range(0, 30.0).cooldown(260).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, ground(level, b.position()), 2.0 + tick * 0.15, ParticleTypes.SOUL);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.WITHER_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, arenaCenter(), radius + 4)) {
                        if (e instanceof Player) {
                            erupt(level, e.position(), 22, 2.2, 15.0F);
                        }
                    }
                    Vec3 c = arenaCenter();
                    for (int i = 0; i < 9; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double d = 2.0 + b.getRandom().nextDouble() * (radius - 3);
                        erupt(level, c.add(Math.cos(a) * d, b.getY() - c.y, Math.sin(a) * d), 16 + i * 3, 2.0, 13.0F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 12 || tick == 24) { // keep moving: two more pillars follow each player
                        for (LivingEntity e : b.victims(level, arenaCenter(), radius + 4)) {
                            if (e instanceof Player) {
                                erupt(level, e.position(), 18, 2.0, 13.0F);
                            }
                        }
                    }
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, b.getX(), b.getY() + 3, b.getZ(), 6, 1.5, 1.0, 1.5, 0.05);
                    }
                })
                .build());

        // 8. (phase 2) summon: the lantern raised, wither skeletons and soul wisps (vexes) answer
        out.add(BossAttack.of("summon").anim(SUMMON).phaseTwo().timing(14, 1, 25).range(0, 30.0).cooldown(500).weight(5)
                .windup((b, level, t, tick) -> level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 4, b.getZ(),
                        3, 0.4, 0.4, 0.4, 0.02))
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.6F);
                    if (countMinions(level) < 4) {
                        summonMinion(level, EntityTypes.WITHER_SKELETON);
                        summonMinion(level, EntityTypes.WITHER_SKELETON);
                        summonMinion(level, EntityTypes.VEX);
                        summonMinion(level, EntityTypes.VEX);
                    }
                })
                .build());

        // 9. (phase 2) reaping grab: claw drawn back (0.9 s), a lunging snatch; the victim is lifted, drained, hurled
        out.add(BossAttack.of("grab").anim(GRAB).phaseTwo().timing(18, 40, 14).range(0, 5.0).cooldown(200).weight(7)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 2.0F, 0.7F))
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        arcOnFloor(level, 4.5, 30, ParticleTypes.SCULK_SOUL);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.8, 0.0);
                    grabbed = null;
                    for (LivingEntity e : b.victims(level, b.position(), 6.0)) {
                        if (inLine(e, 4.8, 1.2)) {
                            grabbed = e;
                            break;
                        }
                    }
                    if (grabbed != null) {
                        grabbed.hurtServer(level, b.damageSources().mobAttack(b), 6.0F);
                        level.playSound(null, b, SoundEvents.WITHER_SHOOT, SoundSource.HOSTILE, 1.5F, 0.5F);
                    } else {
                        level.playSound(null, b, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 1.5F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> tickGrab(level, tick))
                .build());
    }

    /** Hold, drain and finally hurl the grabbed victim (active ticks 0..39, release at 2.75 s = tick 37). */
    private void tickGrab(ServerLevel level, int tick) {
        LivingEntity e = grabbed;
        if (e == null) {
            return;
        }
        if (!e.isAlive() || e.isRemoved()) {
            grabbed = null;
            return;
        }
        if (tick >= 37) {
            e.resetFallDistance();
            strike(level, e, 8.0F, 1.8, 0.5);
            e.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1), this);
            level.playSound(null, this, SoundEvents.WITHER_HURT, SoundSource.HOSTILE, 1.5F, 0.6F);
            grabbed = null;
            return;
        }
        Vec3 hold = position().add(forward().scale(2.0)).add(0, 1.4 + Math.min(tick, 25) * 0.07, 0);
        e.teleportTo(hold.x, hold.y, hold.z);
        e.setDeltaMovement(Vec3.ZERO);
        e.resetFallDistance();
        e.hurtMarked = true;
        if (tick >= 6 && tick % 8 == 6) {
            e.hurtServer(level, damageSources().indirectMagic(this, this), 3.5F);
            heal(5.0F);
            level.playSound(null, this, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 1.6F, 0.7F);
        }
        Vec3 chest = position().add(0, 3.0, 0);
        Vec3 d = chest.subtract(e.position().add(0, 1, 0));
        for (int i = 0; i < 5; i++) { // souls streaming from the victim into the reaper's ribcage
            double f = (tick % 5 + i * 5) / 25.0;
            Vec3 p = e.position().add(0, 1, 0).add(d.scale(f));
            level.sendParticles(ParticleTypes.SOUL, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
        }
    }

    private int countMinions(ServerLevel level) {
        Vec3 c = arenaCenter();
        return level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(radius + 6, 8, radius + 6),
                m -> m.isAlive() && m.entityTags().contains(MINION_TAG) && m.position().distanceTo(c) < radius + 8).size();
    }

    private void summonMinion(ServerLevel level, EntityType<? extends Mob> type) {
        Mob minion = type.create(level, EntitySpawnReason.MOB_SUMMONED);
        if (minion == null) {
            return;
        }
        Vec3 c = arenaCenter();
        double a = getRandom().nextDouble() * Math.PI * 2;
        double d = 3.0 + getRandom().nextDouble() * Math.max(1.0, radius - 6.0);
        Vec3 at = ground(level, new Vec3(c.x + Math.cos(a) * d, getY() + 1, c.z + Math.sin(a) * d));
        minion.snapTo(at.x, at.y + (minion instanceof Vex ? 1.5 : 0.0), at.z, getRandom().nextFloat() * 360F, 0);
        minion.finalizeSpawn(level, level.getCurrentDifficultyAt(BlockPos.containing(at)), EntitySpawnReason.MOB_SUMMONED, null);
        if (minion instanceof Vex vex) {
            vex.setOwner(this);
            vex.setLimitedLife(20 * 30);
        }
        minion.addTag(MINION_TAG);
        minion.setTarget(getTarget());
        level.addFreshEntity(minion);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, at.x, at.y + 0.2, at.z, 30, 0.4, 0.1, 0.4, 0.06);
        level.sendParticles(ParticleTypes.SOUL, at.x, at.y + 1, at.z, 15, 0.3, 0.8, 0.3, 0.02);
    }

    // ------------------------------------------------------------------ every tick: hover, ambience

    @Override
    protected void bossTick(ServerLevel level) {
        if (roarTimer > 0) {
            roarTimer--;
        }
        // the hover: ease toward a gently bobbing height above whatever floor lies below
        double floor = floorY(level, getX(), getY(), getZ());
        Vec3 dm = getDeltaMovement();
        if (!Double.isNaN(floor)) {
            double want = floor + HOVER + 0.15 * Math.sin(tickCount * 0.07);
            double vy = Mth.clamp((want - getY()) * 0.2, -0.35, 0.35);
            setDeltaMovement(dm.x, vy, dm.z);
        } else {
            setDeltaMovement(dm.x, Math.min(dm.y, 0.0) * 0.5, dm.z); // over the void: hold height, drift home
            Vec3 back = arenaCenter().subtract(position()).multiply(1, 0, 1).normalize().scale(0.15);
            setDeltaMovement(getDeltaMovement().add(back));
        }
        resetFallDistance();
        // a grab interrupted by a stagger drops its victim
        if (grabbed != null && currentAttack() == null) {
            grabbed = null;
        }
        if (tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 0.2, getZ(), 2, 0.35, 0.1, 0.35, 0.01);
        }
        if (tickCount % 7 == 0) {
            level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 0.8, getZ(), 1, 0.6, 0.4, 0.6, 0.01);
        }
        if (tickCount % 120 == 0 && getTarget() != null) {
            level.playSound(null, this, SoundEvents.WITHER_SKELETON_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.4F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        roarTimer = MobAnims.SoulReaper.TICKS[ROAR];
        level.playSound(null, this, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.5F, 0.6F);
        Vec3 g = ground(level, position());
        addEffect(WayfarerBoss.wave(g, radius + 2, 0.55, 6.0F, ParticleTypes.SOUL_FIRE_FLAME));
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 2, getZ(), 120, 1.0, 2.0, 1.0, 0.12);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        grabbed = null;
        level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 2, getZ(), 120, 1.0, 2.0, 1.0, 0.08);
        BlockPos c = BlockPos.containing(arenaCenter());
        for (BlockPos pos : BlockPos.betweenClosed(c.offset(-radius - 6, -14, -radius - 6), c.offset(radius + 6, 6, radius + 6))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
    }

    // ------------------------------------------------------------------ drifting movement

    /** Glide toward the target, circle it at close range, never leave the arena. */
    private final class DriftGoal extends Goal {
        DriftGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity t = getTarget();
            if (t == null || busy()) {
                return;
            }
            getLookControl().setLookAt(t, 30.0F, 30.0F);
            Vec3 to = t.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d < 1.0E-3) {
                return;
            }
            Vec3 dir = to.scale(1.0 / d);
            double speed = phase() == 2 ? 0.12 : 0.09;
            if (tickCount % 70 == 0) {
                strafeDir = getRandom().nextBoolean() ? 1 : -1;
            }
            Vec3 side = new Vec3(-dir.z, 0, dir.x).scale(strafeDir);
            Vec3 v;
            if (d > preferredRange() + 0.5) {
                v = dir.scale(speed).add(side.scale(speed * 0.25));
            } else if (d < 2.0) {
                v = dir.scale(-speed * 0.6);
            } else {
                v = side.scale(speed * 0.5);
            }
            Vec3 next = position().add(v.scale(4));
            if (clampToArena(next, 1.5).distanceTo(next) > 1.0E-3) { // would cross the rim: slide along it
                Vec3 out = next.subtract(arenaCenter()).multiply(1, 0, 1).normalize();
                v = v.subtract(out.scale(Math.max(0, v.dot(out)) + 0.05));
            }
            Vec3 dm = getDeltaMovement();
            setDeltaMovement(dm.x * 0.5 + v.x, dm.y, dm.z * 0.5 + v.z);
            float yaw = (float) (Mth.atan2(dir.z, dir.x) * (180.0 / Math.PI)) - 90.0F;
            float turned = Mth.approachDegrees(getYRot(), yaw, 12.0F);
            setYRot(turned);
            yBodyRot = turned;
        }
    }
}
