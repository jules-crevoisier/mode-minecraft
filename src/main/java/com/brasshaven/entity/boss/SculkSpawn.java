package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.ShriekParticleOption;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.SculkSpawn.BOOMS;
import static com.brasshaven.generated.MobAnims.SculkSpawn.ERUPT;
import static com.brasshaven.generated.MobAnims.SculkSpawn.LUNGE;
import static com.brasshaven.generated.MobAnims.SculkSpawn.PULSE;
import static com.brasshaven.generated.MobAnims.SculkSpawn.ROAR;
import static com.brasshaven.generated.MobAnims.SculkSpawn.SCREAM;
import static com.brasshaven.generated.MobAnims.SculkSpawn.SLAM;
import static com.brasshaven.generated.MobAnims.SculkSpawn.SONIC;
import static com.brasshaven.generated.MobAnims.SculkSpawn.STAGGER;
import static com.brasshaven.generated.MobAnims.SculkSpawn.WHIP;

/**
 * Le Rejeton du sculk (The Sculk Spawn): boss of the Sealed Lab, a blind abomination grown from the lab's
 * catalyst. It hunts by sound: every second it turns on the loudest player (sprinting and fighting are loud,
 * sneaking is quiet, distance muffles).
 * <ul>
 *     <li>Phase 1: tendril whip (wide arc), double-arm slam (crater + jumpable sculk ring), sonic boom (long
 *     line through armour), darkness pulse (burst around it + Darkness), sculk eruptions under every player.</li>
 *     <li>Phase 2 (after a roar): faster, eruptions come twice and ring the boss, the whip chains into the slam,
 *     shrieker scream (knockback, Darkness, Slowness), crawling lunge, and a fan of three chained sonic booms.</li>
 * </ul>
 */
public class SculkSpawn extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 4.8F;
    private static final BlockParticleOption SCULK_BITS = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.SCULK.defaultBlockState());

    public SculkSpawn(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 480.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SculkSpawn.TICKS;
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
        return 80.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // tendril whip: the crown of tendrils lashes a wide arc in front (impact 0.8 s)
        out.add(BossAttack.of("whip").anim(WHIP).timing(16, 3, 11).range(0, 6.0).cooldown(36).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.WARDEN_TENDRIL_CLICKS, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.5, 75, ParticleTypes.SCULK_CHARGE_POP);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.5, 75, 13.0F, 1.4);
                    Vec3 p = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 2.0, p.z, 4, 2.0, 0.4, 2.0, 0);
                    level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y + 2.5, p.z, 12, 2.0, 0.6, 2.0, 0.02);
                    level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, this, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.HOSTILE, 2.0F, 1.2F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "slam");
                    }
                })
                .build());
        // double-arm slam: both claws over the head, then down: a crater and a sculk ring to jump (impact 1.0 s)
        out.add(BossAttack.of("slam").anim(SLAM).timing(20, 2, 18).range(0, 6.5).cooldown(70).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.2), 3.6, ParticleTypes.SCULK_CHARGE_POP);
                    }
                    if (tick == 8) {
                        level.playSound(null, this, SoundEvents.WARDEN_ANGRY, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.2);
                    b.hitCircle(level, c, 3.6, 18.0F, 1.3, 0.6);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 12 : 9, 0.5, 9.0F, ParticleTypes.SCULK_SOUL));
                    level.sendParticles(SCULK_BITS, c.x, c.y + 0.3, c.z, 70, 1.6, 0.3, 1.6, 0.2);
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.4, c.z, 3, 1.0, 0.2, 1.0, 0);
                    level.playSound(null, this, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.6F, 0.6F);
                })
                .build());
        // sonic boom: the heart flares, the jaw unhinges, a shriek of force down a long line (impact 1.25 s)
        out.add(BossAttack.of("sonic").anim(SONIC).phaseOne().timing(25, 3, 14).range(4.0, 22.0).cooldown(110).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 3.0F, 1.0F);
                    }
                    if (tick % 3 == 0) {
                        lineTelegraph(level, 0, 20);
                    }
                    heartGlow(level, 3);
                })
                .impact((b, level, t, tick) -> boom(level, 0, 20, 16.0F))
                .build());
        // darkness pulse: curls around its heart, then bursts: knockback ring and Darkness on everyone (impact 0.9 s)
        out.add(BossAttack.of("pulse").anim(PULSE).timing(18, 4, 16).range(0, 8.0).cooldown(170).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick == 0 || tick == 9) {
                        level.playSound(null, this, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 4.0F, 0.6F);
                    }
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 6.5, ParticleTypes.SCULK_SOUL);
                    }
                    heartGlow(level, 4);
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 6.5, 10.0F, 1.8, 0.5);
                    darken(level, 26, 100);
                    for (int r = 1; r <= 7; r++) {
                        b.telegraphRing(level, b.position().add(0, 0.6, 0), r, ParticleTypes.SCULK_SOUL);
                    }
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 11, 0.55, 8.0F, ParticleTypes.SCULK_CHARGE_POP));
                    }
                    level.playSound(null, this, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 5.0F, 0.4F);
                    level.playSound(null, this, SoundEvents.SCULK_CATALYST_BLOOM, SoundSource.HOSTILE, 3.0F, 0.6F);
                })
                .build());
        // sculk eruptions: the claws plunge into the floor and sculk bursts under every player (impact 0.85 s)
        out.add(BossAttack.of("erupt").anim(ERUPT).timing(17, 12, 11).range(3.0, 24.0).cooldown(150).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        for (Player p : listeners(level)) {
                            level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, p.getX(), p.getY() + 0.1, p.getZ(), 4, 0.6, 0.0, 0.6, 0.01);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.sendParticles(SCULK_BITS, b.ahead(2.5).x, b.getY() + 0.3, b.ahead(2.5).z, 50, 1.2, 0.2, 1.2, 0.2);
                    level.playSound(null, this, SoundEvents.WARDEN_DIG, SoundSource.HOSTILE, 3.0F, 0.8F);
                    for (Player p : listeners(level)) {
                        b.addEffect(sculkSpike(p.position(), 16, 1.8, 12.0F));
                    }
                    if (b.phase() == 2) { // a ring of spikes around itself, a beat later
                        for (int i = 0; i < 8; i++) {
                            double a = Math.PI * 2 * i / 8;
                            b.addEffect(sculkSpike(b.position().add(Math.cos(a) * 4.5, 0, Math.sin(a) * 4.5), 24, 1.6, 10.0F));
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 8) { // a second volley where the players are heading
                        for (Player p : listeners(level)) {
                            Vec3 lead = p.position().add(p.getDeltaMovement().multiply(14, 0, 14));
                            b.addEffect(sculkSpike(lead, 14, 1.8, 12.0F));
                        }
                    }
                })
                .build());
        // ---- phase 2
        // shrieker scream: rears up and shrieks: knockback, Darkness and a crushing slow (impact 0.9 s)
        out.add(BossAttack.of("scream").anim(SCREAM).phaseTwo().timing(18, 20, 10).range(0, 12.0).cooldown(240).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 11.0, ParticleTypes.SCULK_SOUL);
                    }
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.HOSTILE, 2.0F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), 11.0)) {
                        if (e.distanceTo(b) <= 11.0) {
                            b.strike(level, e, 8.0F, 2.2, 0.55);
                            e.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 160, 0), b);
                            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50, 2), b);
                        }
                    }
                    level.playSound(null, this, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.HOSTILE, 4.0F, 0.6F);
                    level.playSound(null, this, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 4.0F, 0.8F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.sendParticles(new ShriekParticleOption(0), b.getX(), b.getY() + 4.6, b.getZ(), 1, 0, 0, 0, 0);
                    }
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position().add(0, 0.4, 0), 1.0 + tick * 0.5, ParticleTypes.SCULK_SOUL);
                    }
                })
                .build());
        // crawling lunge: drops onto all fours and springs claws-first at a distant player (impact 0.7 s)
        out.add(BossAttack.of("lunge").anim(LUNGE).phaseTwo().timing(14, 6, 16).range(5.0, 16.0).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 2.6, ParticleTypes.SCULK_CHARGE_POP);
                    }
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.WARDEN_SNIFF, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(2.4, dist * 0.17), 0.3);
                    level.playSound(null, this, SoundEvents.WARDEN_AGITATED, SoundSource.HOSTILE, 3.0F, 0.7F);
                })
                .active((b, level, t, tick) -> {
                    level.sendParticles(SCULK_BITS, b.getX(), b.getY() + 0.2, b.getZ(), 6, 0.8, 0.1, 0.8, 0.1);
                    if (tick == 3) {
                        b.hitCircle(level, b.position(), 3.0, 15.0F, 1.2, 0.4);
                        level.playSound(null, this, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.HOSTILE, 3.0F, 0.8F);
                    }
                })
                .build());
        // chained booms: three sonic booms fanned left, centre, right (1.0 s, 1.6 s, 2.2 s)
        out.add(BossAttack.of("booms").anim(BOOMS).phaseTwo().timing(20, 25, 15).range(4.0, 24.0).cooldown(200).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 3.0F, 1.2F);
                    }
                    if (tick % 4 == 0) {
                        lineTelegraph(level, -15, 20);
                    }
                    heartGlow(level, 3);
                })
                .impact((b, level, t, tick) -> boom(level, -15, 20, 13.0F))
                .active((b, level, t, tick) -> {
                    if (tick < 12 && tick % 3 == 0) {
                        lineTelegraph(level, 0, 20);
                    } else if (tick > 12 && tick < 24 && tick % 3 == 0) {
                        lineTelegraph(level, 15, 20);
                    }
                    if (tick == 12) {
                        boom(level, 0, 20, 13.0F);
                    } else if (tick == 24) {
                        boom(level, 15, 20, 13.0F);
                    }
                })
                .build());
        // a phase-2 sonic boom that follows up with a lunge when the player is still far
        out.add(BossAttack.of("sonic2").anim(SONIC).phaseTwo().timing(25, 3, 14).range(5.0, 22.0).cooldown(120).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 3.0F, 1.1F);
                    }
                    if (tick % 3 == 0) {
                        lineTelegraph(level, 0, 22);
                    }
                    heartGlow(level, 3);
                })
                .impact((b, level, t, tick) -> boom(level, 0, 22, 16.0F))
                .end((b, level, t, tick) -> {
                    if (t != null && b.distanceTo(t) > 6.0 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "lunge");
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private helpers

    /** Players the boss can hear: alive, in survival/adventure, within the arena. */
    private List<Player> listeners(ServerLevel level) {
        return level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(26, 10, 26),
                p -> p.isAlive() && !p.isCreative() && !p.isSpectator());
    }

    /** Loudness score (lower = heard better): distance, muffled by sneaking, sharpened by running and fighting. */
    private double hearing(Player p) {
        double score = distanceTo(p);
        if (p.isSprinting()) {
            score -= 6.0;
        }
        if (p.isCrouching() || p.isSteppingCarefully()) {
            score += 8.0;
        }
        if (p.tickCount - p.getLastHurtMobTimestamp() < 60) {
            score -= 6.0;
        }
        return score;
    }

    private void heartGlow(ServerLevel level, int every) {
        if (tickCount % every == 0) {
            Vec3 h = position().add(forward().scale(0.7)).add(0, 3.1, 0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, h.x, h.y, h.z, 1, 0.3, 0.3, 0.3, 0.02);
            level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, h.x, h.y, h.z, 3, 0.5, 0.5, 0.5, 0.0);
        }
    }

    private Vec3 dir(float yawOffset) {
        float yaw = (getYRot() + yawOffset) * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** Ground telegraph of a sonic boom's line. */
    private void lineTelegraph(ServerLevel level, float yawOffset, double length) {
        Vec3 d = dir(yawOffset);
        for (double s = 2.0; s <= length; s += 1.5) {
            Vec3 p = position().add(d.scale(s));
            level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
        }
    }

    /** Warden-style sonic boom: hits everything along the line, through armour, and throws it back. */
    private void boom(ServerLevel level, float yawOffset, double length, float damage) {
        Vec3 d = dir(yawOffset);
        Vec3 start = position().add(0, 2.8, 0).add(d.scale(1.2));
        for (double s = 0; s <= length; s += 1.0) {
            Vec3 p = start.add(d.scale(s)).add(0, -s * 0.06, 0);
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        for (LivingEntity e : victims(level, position(), length + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(d);
            double side = to.subtract(d.scale(along)).length();
            if (along >= 0 && along <= length && side <= 1.4 + e.getBbWidth() / 2 && Math.abs(e.getY() - getY()) < 4.5) {
                if (e.hurtServer(level, damageSources().sonicBoom(this), damage)) {
                    e.push(d.x * 1.6, 0.45, d.z * 1.6);
                    e.hurtMarked = true;
                }
            }
        }
        level.playSound(null, this, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3.0F, 1.0F);
    }

    private void darken(ServerLevel level, double radius, int ticks) {
        for (LivingEntity e : victims(level, position(), radius)) {
            e.addEffect(new MobEffectInstance(MobEffects.DARKNESS, ticks, 0), this);
        }
    }

    /** A sculk spike: the floor charges (warning) for {@code delay} ticks, then a burst of sculk throws up. */
    private static Effect sculkSpike(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, pos.x, pos.y + 0.1, pos.z, 5, radius * 0.45, 0.02, radius * 0.45, 0.0);
                    level.sendParticles(SCULK_BITS, pos.x, pos.y + 0.1, pos.z, 2, radius * 0.4, 0.0, radius * 0.4, 0.0);
                }
                if (t[0] == delay / 2) {
                    level.playSound(null, BlockPos.containing(pos), SoundEvents.SCULK_BLOCK_SPREAD, SoundSource.HOSTILE, 1.5F, 0.6F);
                }
                t[0]++;
                return false;
            }
            level.sendParticles(ParticleTypes.SCULK_SOUL, pos.x, pos.y + 0.6, pos.z, 18, radius * 0.35, 1.2, radius * 0.35, 0.08);
            level.sendParticles(SCULK_BITS, pos.x, pos.y + 0.8, pos.z, 40, radius * 0.3, 1.0, radius * 0.3, 0.25);
            level.playSound(null, BlockPos.containing(pos), SoundEvents.SCULK_CATALYST_BLOOM, SoundSource.HOSTILE, 2.0F, 0.8F);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.3, 0.9);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ hunting by sound, ambience

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 20 == 0 && currentAttack() == null) {
            Player best = null;
            double bestScore = Double.MAX_VALUE;
            for (Player p : listeners(level)) {
                double s = hearing(p);
                if (s < bestScore) {
                    bestScore = s;
                    best = p;
                }
            }
            @Nullable LivingEntity current = getTarget();
            if (best != null && best != current && (current == null || bestScore + 2.0 < (current instanceof Player cp ? hearing(cp) : 99))) {
                setTarget(best);
                level.playSound(null, this, SoundEvents.WARDEN_LISTENING_ANGRY, SoundSource.HOSTILE, 2.0F, 0.8F);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, getX(), getY() + 5.0, getZ(), 12, 1.0, 0.4, 1.0, 0.02);
            }
        }
        int beat = phase() == 2 ? 24 : 40;
        if (tickCount % beat == 0) {
            level.playSound(null, this, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 1.6F, 0.8F);
        }
        if (tickCount % 7 == 0) {
            level.sendParticles(ParticleTypes.SCULK_SOUL, getX(), getY() + 3.2, getZ(), 1, 0.6, 0.6, 0.6, 0.01);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("phase_two_speed"), 0.22,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        darken(level, 30, 120);
        for (int i = 0; i < 10; i++) {
            double a = Math.PI * 2 * i / 10;
            addEffect(sculkSpike(position().add(Math.cos(a) * 6, 0, Math.sin(a) * 6), 30 + i * 2, 1.6, 9.0F));
        }
        level.playSound(null, this, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 4.0F, 0.6F);
        level.playSound(null, this, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.HOSTILE, 4.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
        level.sendParticles(ParticleTypes.SCULK_SOUL, getX(), getY() + 2, getZ(), 120, 1.5, 2.0, 1.5, 0.08);
    }
}
