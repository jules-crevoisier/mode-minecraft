package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.BellKeeper.BELL_FALL;
import static com.brasshaven.generated.MobAnims.BellKeeper.CHARGE;
import static com.brasshaven.generated.MobAnims.BellKeeper.FRENZY;
import static com.brasshaven.generated.MobAnims.BellKeeper.KNELL;
import static com.brasshaven.generated.MobAnims.BellKeeper.REQUIEM;
import static com.brasshaven.generated.MobAnims.BellKeeper.ROAR;
import static com.brasshaven.generated.MobAnims.BellKeeper.SMASH;
import static com.brasshaven.generated.MobAnims.BellKeeper.STAGGER;
import static com.brasshaven.generated.MobAnims.BellKeeper.SWEEP;
import static com.brasshaven.generated.MobAnims.BellKeeper.TOLL;
import static com.brasshaven.generated.MobAnims.BellKeeper.TRIPLE_TOLL;

/**
 * Le Sonneur de glas (The Bell Keeper), boss of the Mountain Monastery's bell chamber: a five-block monk-knight
 * swinging a huge cracked bronze bell on a chain.
 * <ul>
 *     <li>Phase 1: toll (the claw strikes the bell: a sound ring to jump), overhead smash, wide chain sweep, knell
 *     (the bell planted mouth-down: two slow-rings that drag the feet), a lunging uppercut from afar.</li>
 *     <li>Phase 2: frenzied three-swing combo, triple toll (three rings at different speeds), requiem (ghost monks
 *     rise), the bell fall (the chain paid out, the bell crashes seven blocks away and cracks the floor),
 *     faster with combos (charge into sweep, smash into a delayed toll).</li>
 * </ul>
 */
public class BellKeeper extends WayfarerBoss {
    public static final float WIDTH = 1.9F;
    public static final float HEIGHT = 5.0F;

    /** Bronze sound rings, grey-blue slowing rings, soul glow of the ghost monks. */
    private static final ParticleOptions BRONZE = new DustParticleOptions(0xD9A04A, 1.6F);
    private static final ParticleOptions DIRGE = new DustParticleOptions(0x8A9CC4, 1.8F);
    private static final int MAX_GHOSTS = 4;

    public BellKeeper(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BellKeeper.TICKS;
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
        return 80.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // toll: the bell lifted before the chest, the claw rakes across it -> a bronze ring to jump over
        out.add(BossAttack.of("toll").anim(TOLL).timing(16, 2, 12).range(0, 12).cooldown(70).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.1, BRONZE);
                    }
                })
                .impact((b, level, t, tick) -> toll(b, level, 0.42, 9.0F))
                .build());
        // smash: whirled over the head (long telegraph), crashed down four blocks ahead
        out.add(BossAttack.of("smash").anim(SMASH).timing(20, 2, 18).range(0, 6.0).cooldown(60).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(4.0), 3.0, BRONZE);
                    }
                    if (tick == 8) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> smash(b, level, b.ahead(4.0)))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "toll"); // the delayed toll: a second rhythm right after the crash
                    }
                })
                .build());
        // sweep: the chain paid out and the bell swept round in a wide arc
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(17, 3, 12).range(0, 6.0).cooldown(50).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.0, 110, BRONZE);
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> sweep(b, level))
                .build());
        // knell: the bell dropped mouth-down and held while it hums; two slow grey rings drag the feet
        out.add(BossAttack.of("knell").anim(KNELL).timing(18, 20, 14).range(0, 10).cooldown(160).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 9.0, DIRGE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(2.2);
                    b.hitCircle(level, c, 2.5, 10.0F, 0.8, 0.3);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.35F);
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 2, 0.6, 0.1, 0.6, 0);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 10) {
                        b.addEffect(dirge(b.position(), 11.0, 0.32));
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                    level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 0.4, b.getZ(), 2, 1.5, 0.2, 1.5, 0.01);
                })
                .build());
        // charge: crouches with the bell dragged behind, then lunges into an uppercut (gap closer)
        out.add(BossAttack.of("charge").anim(CHARGE).timing(14, 6, 10).range(6.0, 16).cooldown(80).weight(8)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F))
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 2.0, BRONZE);
                    }
                    level.sendParticles(ParticleTypes.CRIT, b.getX(), b.getY() + 0.2, b.getZ(), 2, 0.6, 0.1, 0.6, 0.05);
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(1.9, dist * 0.2), 0.2);
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 1.4F, 0.6F);
                })
                .active(new BossAttack.Step() {
                    private final Set<UUID> hit = new HashSet<>();

                    @Override
                    public void run(WayfarerBoss b, ServerLevel level, LivingEntity t, int tick) {
                        if (tick == 0) {
                            hit.clear();
                        }
                        for (LivingEntity e : b.victims(level, b.ahead(1.5), 2.6)) {
                            if (hit.add(e.getUUID())) {
                                b.strike(level, e, 13.0F, 0.8, 0.9);
                            }
                        }
                        level.sendParticles(BRONZE, b.getX(), b.getY() + 0.5, b.getZ(), 6, 0.8, 0.4, 0.8, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());

        // ---------------------------------------------------------- phase 2
        // frenzy: sweep (impact), backhand (active 8), overhead crash (active 19)
        out.add(BossAttack.of("frenzy").anim(FRENZY).phaseTwo().timing(11, 20, 15).range(0, 6.0).cooldown(90).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 6.0, 100, BRONZE);
                    }
                })
                .impact((b, level, t, tick) -> sweep(b, level))
                .active((b, level, t, tick) -> {
                    if (tick == 8) {
                        b.hitArc(level, 6.5, 100, 12.0F, 1.4);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    } else if (tick == 12) {
                        b.telegraphRing(level, b.ahead(4.0), 3.0, BRONZE);
                    } else if (tick == 19) {
                        smash(b, level, b.ahead(4.0));
                    }
                })
                .build());
        // triple toll: three rings at three speeds; the rhythm, not the reflex, is the test
        out.add(BossAttack.of("triple_toll").anim(TRIPLE_TOLL).phaseTwo().timing(16, 19, 13).range(0, 14).cooldown(120).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.12, BRONZE);
                    }
                })
                .impact((b, level, t, tick) -> toll(b, level, 0.36, 8.0F))
                .active((b, level, t, tick) -> {
                    if (tick == 9) {
                        toll(b, level, 0.55, 8.0F);
                    } else if (tick == 18) {
                        toll(b, level, 0.44, 10.0F);
                    }
                })
                .build());
        // requiem: kneels, plants the bell, raises the claw; ghost monks rise around the arena
        out.add(BossAttack.of("requiem").anim(REQUIEM).phaseTwo().timing(16, 4, 24).range(0, 30).cooldown(500).weight(5)
                .windup((b, level, t, tick) -> level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 0.3, b.getZ(),
                        4, 3.0, 0.1, 3.0, 0.02))
                .impact((b, level, t, tick) -> {
                    ((BellKeeper) b).raiseGhosts(level, 3);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.3F);
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .build());
        // bell fall: the chain paid out, the bell whirled high and brought down seven blocks away;
        // the floor cracks in a ring of delayed bursts around the crater
        out.add(BossAttack.of("bell_fall").anim(BELL_FALL).phaseTwo().timing(22, 3, 23).range(5.0, 12).cooldown(140).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(7.0), 3.2, BRONZE);
                        b.telegraphRing(level, b.ahead(7.0), 4.8, ParticleTypes.SMOKE);
                    }
                    if (tick == 6 || tick == 14) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(7.0);
                    b.hitCircle(level, c, 3.2, 20.0F, 1.2, 0.7);
                    b.addEffect(WayfarerBoss.wave(c, 10, 0.45, 9.0F, BRONZE));
                    for (int i = 0; i < 6; i++) {
                        double a = Math.PI * 2 * i / 6 + b.getRandom().nextDouble() * 0.4;
                        Vec3 p = c.add(Math.cos(a) * 4.8, 0, Math.sin(a) * 4.8);
                        b.addEffect(WayfarerBoss.eruption(p, 12 + i * 2, 1.6, 10.0F, ParticleTypes.SMOKE, ParticleTypes.EXPLOSION));
                    }
                    level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y + 0.5, c.z, 1, 0, 0, 0, 0);
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.3F);
                    level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());
    }

    // ------------------------------------------------------------------ shared strikes

    /** The bell is struck: a bronze ring rolls out from the Keeper; jump it. */
    private static void toll(WayfarerBoss b, ServerLevel level, double speed, float damage) {
        b.addEffect(WayfarerBoss.wave(b.position(), 13, speed, damage, BRONZE));
        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.sendParticles(ParticleTypes.NOTE, b.getX(), b.getY() + 2.5, b.getZ(), 8, 1.0, 0.6, 1.0, 1.0);
    }

    /** Overhead crash: heavy circle, a short ring, stone dust. */
    private static void smash(WayfarerBoss b, ServerLevel level, Vec3 c) {
        b.hitCircle(level, c, 3.0, 19.0F, 1.0, 0.6);
        b.addEffect(WayfarerBoss.wave(c, 6, 0.4, 6.0F, BRONZE));
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.4, c.z, 3, 1.0, 0.2, 1.0, 0);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, c.x, c.y + 0.2, c.z, 10, 1.4, 0.1, 1.4, 0.02);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    /** Wide arc of the bell at the end of its chain. */
    private static void sweep(WayfarerBoss b, ServerLevel level) {
        b.hitArc(level, 6.5, 110, 14.0F, 1.6);
        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.4F);
        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.5F, 0.7F);
        Vec3 p = b.ahead(3.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.5, p.z, 4, 2.0, 0.2, 2.0, 0);
    }

    /**
     * A slow grey ring: whoever it catches on the ground is dragged down (Slowness III and Mining Fatigue) and
     * takes a little damage. Like the sound ring, it can be jumped.
     */
    private static Effect dirge(Vec3 center, double maxRadius, double speed) {
        Set<UUID> caught = new HashSet<>();
        double[] radius = {0.5};
        return (boss, level) -> {
            radius[0] += speed;
            double r = radius[0];
            int n = Math.max(16, (int) (r * 5));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(DIRGE, center.x + Math.cos(a) * r, center.y + 0.25, center.z + Math.sin(a) * r, 1, 0, 0.1, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, center, r + 1.5)) {
                double d = e.position().multiply(1, 0, 1).distanceTo(center.multiply(1, 0, 1));
                if (Math.abs(d - r) <= 1.0 && e.getY() - center.y < 0.9 && caught.add(e.getUUID())) {
                    boss.strike(level, e, 4.0F, 0.2, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 70, 2), boss);
                    e.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 100, 1), boss);
                }
            }
            return r >= maxRadius;
        };
    }

    /** Ghost monks (spectral vexes bound to the bell chamber) rise from the floor around the Keeper. */
    private void raiseGhosts(ServerLevel level, int wanted) {
        int alive = level.getEntitiesOfClass(Vex.class, getBoundingBox().inflate(40),
                v -> v.isAlive() && v.entityTags().contains(MINION_TAG)).size();
        for (int i = 0; i < Math.min(wanted, MAX_GHOSTS - alive); i++) {
            Vex ghost = EntityTypes.VEX.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (ghost == null) {
                continue;
            }
            double a = random.nextDouble() * Math.PI * 2;
            double x = getX() + Math.cos(a) * 5, z = getZ() + Math.sin(a) * 5;
            ghost.snapTo(x, getY() + 1.0, z, getYRot(), 0);
            ghost.addTag(MINION_TAG);
            ghost.setOwner(this);
            ghost.setBoundOrigin(blockPosition().above(2));
            ghost.setLimitedLife(20 * 25);
            ghost.setTarget(getTarget());
            level.addFreshEntity(ghost);
            level.sendParticles(ParticleTypes.SOUL, x, getY() + 0.5, z, 20, 0.3, 0.8, 0.3, 0.04);
            level.sendParticles(ParticleTypes.SCULK_SOUL, x, getY() + 0.2, z, 6, 0.4, 0.1, 0.4, 0.02);
        }
    }

    // ------------------------------------------------------------------ ambience, phases

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 10 == 0) { // faint ghost-light breathing out of the cowl
            Vec3 face = position().add(forward().scale(0.6));
            level.sendParticles(ParticleTypes.SOUL, face.x, getY() + 4.2, face.z, 1, 0.15, 0.1, 0.15, 0.01);
        }
        if (phase() == 2 && tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 1.0, getZ(), 2, 1.0, 0.8, 1.0, 0.01);
        }
        if (tickCount % 160 == 0 && currentAttack() == null) {
            level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 0.8F, 0.4F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("bell_keeper_frenzy"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        raiseGhosts(level, 2);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.3F);
        addEffect(WayfarerBoss.wave(position(), 14, 0.5, 6.0F, BRONZE));
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        for (Vex v : level.getEntitiesOfClass(Vex.class, getBoundingBox().inflate(48), v -> v.entityTags().contains(MINION_TAG))) {
            level.sendParticles(ParticleTypes.SOUL, v.getX(), v.getY() + 0.5, v.getZ(), 12, 0.3, 0.4, 0.3, 0.03);
            v.discard();
        }
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.25F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 4.0F, 0.3F);
    }
}
