package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.GraveKnight.CHARGE;
import static com.brasshaven.generated.MobAnims.GraveKnight.CLEAVE;
import static com.brasshaven.generated.MobAnims.GraveKnight.LEAP;
import static com.brasshaven.generated.MobAnims.GraveKnight.REND;
import static com.brasshaven.generated.MobAnims.GraveKnight.ROAR;
import static com.brasshaven.generated.MobAnims.GraveKnight.SLAM;
import static com.brasshaven.generated.MobAnims.GraveKnight.SPIN;
import static com.brasshaven.generated.MobAnims.GraveKnight.STAGGER;
import static com.brasshaven.generated.MobAnims.GraveKnight.SUMMON;
import static com.brasshaven.generated.MobAnims.GraveKnight.SWEEP;

/**
 * Le Chevalier des tombes (The Grave Knight): champion at the bottom of the Forgotten Catacombs. A crowned skeleton
 * lord in black-and-gold plate with a soul-fire greatsword.
 * <ul>
 *     <li>Phase 1: overhead cleave (line), wide sweep (arc), running thrust (gap closer), sword plunge with a
 *     soul-fire ring to jump, and the rising "grave rend" that sends a travelling line of warned soul eruptions.</li>
 *     <li>Phase 2 (below 50%, after a roar that raises two Skeleton Knights): faster; the cleave leaves a delayed
 *     line of eruptions and chains into the sweep, the thrust chains into the cleave, the plunge sends two rings,
 *     the rend fans into three lines; new moves: a leaping smash from afar, a double spin, and raising more knights.</li>
 * </ul>
 */
public class GraveKnight extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.6F;

    private final Set<UUID> chargeHits = new HashSet<>();

    public GraveKnight(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 280.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.GraveKnight.TICKS;
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
        return 65.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    // ------------------------------------------------------------------ private helpers

    /** A straight line of warned soul eruptions from {@code from} along {@code dir}, travelling outward. */
    private static void eruptionLine(WayfarerBoss b, Vec3 from, Vec3 dir, int count, double step, int delay, int stagger, float damage) {
        for (int i = 0; i < count; i++) {
            Vec3 p = from.add(dir.scale(1.5 + i * step));
            b.addEffect(WayfarerBoss.eruption(p, delay + i * stagger, 1.3, damage, ParticleTypes.SOUL, ParticleTypes.SOUL_FIRE_FLAME));
        }
    }

    private static Vec3 rotateY(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        return new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
    }

    private static int minionsAround(WayfarerBoss b, ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(b.blockPosition()).inflate(24, 8, 24),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // overhead cleave: 0.9 s wind-up, a line 5.5 long in front
        out.add(BossAttack.of("cleave").anim(CLEAVE).timing(18, 3, 11).range(0, 5.5).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 1; i <= 5; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.SOUL, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitLine(level, 5.5, 1.3, 15.0F, 1.0);
                    Vec3 p = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.2, p.z, 30, 0.4, 0.1, 2.0, 0.05);
                    level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.3, p.z, 1, 0, 0, 0, 0);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.6F, 0.5F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 2.0F, 0.5F);
                    if (b.phase() == 2) { // the cut keeps burning: a delayed line of eruptions along it
                        eruptionLine(b, b.position(), b.forward(), 5, 1.4, 14, 2, 9.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.45F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());

        // sweep: 0.7 s wind-up, a 160 degree arc of 5.5 blocks
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(14, 4, 10).range(0, 5.0).cooldown(45).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.0, 80, ParticleTypes.SOUL);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 5.5, 80, 12.0F, 1.4);
                    Vec3 p = b.ahead(2.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.5, p.z, 4, 1.6, 0.2, 1.6, 0);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());

        // charge: crouch 0.8 s, then a running thrust for 0.5 s that hits everything on its way once
        out.add(BossAttack.of("charge").anim(CHARGE).timing(16, 10, 10).range(5.5, 16).cooldown(80).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 9; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.SOUL, p.x, p.y + 0.15, p.z, 1, 0.2, 0, 0.2, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    ((GraveKnight) b).chargeHits.clear();
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 1.5F, 0.7F);
                })
                .active((b, level, t, tick) -> {
                    if (tick < 8) {
                        Vec3 f = b.forward().scale(0.95);
                        b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                        b.hurtMarked = true;
                    }
                    Vec3 tip = b.ahead(1.6);
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, tip.x, tip.y + 1.2, tip.z, 3, 0.2, 0.2, 0.2, 0.01);
                    for (LivingEntity e : b.victims(level, tip, 1.8)) {
                        if (((GraveKnight) b).chargeHits.add(e.getUUID())) {
                            b.strike(level, e, 13.0F, 1.6, 0.35);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "cleave");
                    }
                })
                .build());

        // plunge: 1.1 s wind-up (ring telegraph), the sword driven into the floor, a soul ring to jump over
        out.add(BossAttack.of("slam").anim(SLAM).timing(22, 2, 16).range(0, 7.0).cooldown(100).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(2.0), 3.5, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(2.0);
                    b.hitCircle(level, c, 3.5, 15.0F, 1.2, 0.5);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 13 : 10, 0.5, 9.0F, ParticleTypes.SOUL_FIRE_FLAME));
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 3, 1.0, 0.2, 1.0, 0);
                    level.sendParticles(ParticleTypes.SOUL, c.x, c.y + 0.5, c.z, 40, 1.5, 0.5, 1.5, 0.05);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 1) { // a second, slower ring right behind the first
                        b.addEffect(WayfarerBoss.wave(b.ahead(2.0), 13, 0.3, 8.0F, ParticleTypes.SOUL));
                    }
                })
                .build());

        // grave rend: 1.0 s crouch, a rising cut; a line of soul eruptions races toward the target (fan of 3 in phase 2)
        out.add(BossAttack.of("rend").anim(REND).timing(20, 2, 18).range(3.5, 18).cooldown(120).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, b.getX(), b.getY() + 0.3, b.getZ(), 10, 0.8, 0.1, 0.8, 0.02);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 1.5F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 dir = b.forward();
                    eruptionLine(b, b.position(), dir, 9, 1.5, 6, 2, 11.0F);
                    if (b.phase() == 2) {
                        eruptionLine(b, b.position(), rotateY(dir, 22), 8, 1.5, 9, 2, 9.0F);
                        eruptionLine(b, b.position(), rotateY(dir, -22), 8, 1.5, 9, 2, 9.0F);
                    }
                    level.playSound(null, b, SoundEvents.WITHER_SHOOT, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .build());

        // phase 2: raise the dead (two more Skeleton Knights if fewer than four minions stand)
        out.add(BossAttack.of("summon").anim(SUMMON).phaseTwo().timing(20, 1, 19).range(0, 30).cooldown(500).weight(5)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, ParticleTypes.SOUL);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (minionsAround(b, level) < 4) {
                        b.summon(level, ModEntities.SKELETON_KNIGHT.get(), 2, 4.0);
                    }
                    level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 1, b.getZ(), 60, 4.0, 0.3, 4.0, 0.05);
                })
                .build());

        // phase 2: leap from afar (0.7 s crouch with a ring on the target), smash on landing at 1.3 s
        out.add(BossAttack.of("leap").anim(LEAP).phaseTwo().timing(14, 12, 10).range(6, 18).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 3.0, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(2.0, dist * 0.15), 0.62);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_KNOCKBACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 11) {
                        b.hitCircle(level, b.position(), 3.5, 16.0F, 1.3, 0.5);
                        b.addEffect(WayfarerBoss.wave(b.position(), 9, 0.45, 8.0F, ParticleTypes.SOUL_FIRE_FLAME));
                        level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 0.4, b.getZ(), 4, 1.2, 0.2, 1.2, 0);
                        level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .build());

        // phase 2: double spin (0.6 s wind-up, 0.8 s of spinning), hits around him every 4 ticks
        out.add(BossAttack.of("spin").anim(SPIN).phaseTwo().timing(12, 16, 8).range(0, 5.5).cooldown(140).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.2, ParticleTypes.SOUL);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.hitCircle(level, b.position(), 4.2, 7.0F, 0.9, 0.2);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.6F + tick * 0.02F);
                    }
                    double a = tick * Math.PI / 4;
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX() + Math.cos(a) * 2.5, b.getY() + 1.4,
                            b.getZ() + Math.sin(a) * 2.5, 1, 0, 0, 0, 0);
                })
                .build());
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 5 == 0) { // soul embers off the crown and the blade
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 3.4, getZ(), 1, 0.25, 0.1, 0.25, 0.005);
            if (phase() == 2) {
                level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 1.5, getZ(), 2, 0.6, 1.0, 0.6, 0.01);
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("grave_knight_phase_two"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        summon(level, ModEntities.SKELETON_KNIGHT.get(), 2, 5.0);
        level.playSound(null, this, SoundEvents.WITHER_SKELETON_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
        for (int i = 0; i < 24; i++) {
            double a = Math.PI * 2 * i / 24;
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX() + Mth.cos((float) a) * 3, getY() + 0.2,
                    getZ() + Mth.sin((float) a) * 3, 2, 0, 0.3, 0, 0.02);
        }
    }
}
