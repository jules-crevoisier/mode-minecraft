package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

import static com.brasshaven.generated.MobAnims.ChainedJailer.HOOK;
import static com.brasshaven.generated.MobAnims.ChainedJailer.KICK;
import static com.brasshaven.generated.MobAnims.ChainedJailer.LASH;
import static com.brasshaven.generated.MobAnims.ChainedJailer.PYRE;
import static com.brasshaven.generated.MobAnims.ChainedJailer.ROAR;
import static com.brasshaven.generated.MobAnims.ChainedJailer.SHACKLES;
import static com.brasshaven.generated.MobAnims.ChainedJailer.SLAM;
import static com.brasshaven.generated.MobAnims.ChainedJailer.STAGGER;
import static com.brasshaven.generated.MobAnims.ChainedJailer.UNCHAIN;
import static com.brasshaven.generated.MobAnims.ChainedJailer.VERDICT;
import static com.brasshaven.generated.MobAnims.ChainedJailer.WHIRL;

/**
 * Le Geôlier enchaîné (The Chained Jailer), warden of the Chained Bastion's prison: a hunched giant of blackstone and
 * gilded iron whose head is a locked cage full of fire, a padlock for a heart, a gibbet on his back, a burning
 * fetter-ball dragged on a chain in his right fist and a shackled gauntlet on his left. He waits in the boss drum.
 * <p>A hard Nether fight: 600 health, armour 14, poise 100, hits of 8 to 20. Three phases:
 * <ul>
 *     <li>Phase 1: <b>chain lash</b> (a 220 degree sweep of the burning ball, 16 + fire), <b>hook</b> (a chain thrown
 *     down a line: 9 and the victim is dragged to him, then he slams), <b>slam</b> (both fists, 20 in front and a
 *     ring of fire to jump), <b>shackles</b> (chains burst from the floor under every player after a warning ring:
 *     8 and held fast for 1.5 s), <b>kick</b> (shoves huggers away).</li>
 *     <li>Phase 2 (a roar at 60%): faster, combos (lash into hook, shackles into hook, slam into lash), <b>whirl</b>
 *     (the ball spun round him for two seconds while he walks you down) and <b>pyre</b> (eight lines of fire run out
 *     from his fists like the bars of a cell, in two volleys: stand between the bars).</li>
 *     <li>Phase 3 (at 30%): <b>unchain</b>, he kneels (invulnerable) and tears his own chains apart in a fire nova;
 *     from then on he is faster, burns whoever hugs him and every 12 seconds casts the <b>verdict</b>: chains of
 *     judgement rain on every player in three volleys (warned by rings), binding and burning.</li>
 * </ul>
 */
public class ChainedJailer extends WayfarerBoss {
    public static final float WIDTH = 2.6F;
    public static final float HEIGHT = 5.2F;
    private static final double HOOK_RANGE = 16.0;
    private static final double WHIRL_RADIUS = 6.5;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final int VERDICT_EVERY = 240;
    private static final DustParticleOptions IRON = new DustParticleOptions(0x8A8690, 1.3F);

    /** The last hook caught someone (the slam follows). */
    private boolean hooked;
    /** Someone was shackled by the last shackles (phase 2 follows with the hook). */
    private boolean bound;
    /** Phase 3: he tore his chains off. */
    private boolean unchained;
    /** Invulnerable while tearing the chains apart. */
    private int unchainGuard;
    private int phaseTwoTick = -1;
    private int verdictTimer;

    public ChainedJailer(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
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
        return MobAnims.ChainedJailer.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.RED;
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
        return 0.6F;
    }

    @Override
    protected double preferredRange() {
        return 4.5;
    }

    /** Phase 3 counts as a third stage of the fight (the base class knows only two). */
    public boolean isUnchained() {
        return unchained;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // chain lash: the chain drawn back and out to his right (0.9 s, the reach is outlined in flame), then the
        // burning ball swept flat across 220 degrees in front of him
        out.add(BossAttack.of("lash").anim(LASH).timing(18, 4, 14).range(0, 8.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 7.8, 110, ParticleTypes.FLAME);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 8.0, 110)) {
                        b.strike(level, e, 16.0F, 1.6, 0.25);
                        burn(e, 60);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    for (int a = -110; a <= 110; a += 12) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(6.0));
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 1.0, p.z, 3, 0.2, 0.2, 0.2, 0.02);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof ChainedJailer j && b.phase() == 2) {
                        float r = b.getRandom().nextFloat();
                        if (r < (j.unchained ? 0.5F : 0.35F)) {
                            b.chain(level, j.unchained && r < 0.25F ? "slam" : "hook");
                        }
                    }
                })
                .build());
        // hook: the chain wound back over his shoulder (0.8 s, a line of embers shows the throw), then hurled down
        // the line; whoever it catches is hurt and dragged to his feet, and he slams them
        out.add(BossAttack.of("hook").anim(HOOK).timing(16, 4, 14).range(5.0, HOOK_RANGE).cooldown(110).weight(9)
                .start((b, level, t, tick) -> hooked = false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 2; d <= HOOK_RANGE; d += 2) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof ChainedJailer j) {
                        j.throwHook(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof ChainedJailer j && j.hooked) {
                        b.chain(level, "slam");
                    }
                })
                .build());
        // slam: both fists heaved overhead (1.1 s, the landing ring glows), crashed down 3.5 ahead; a ring of fire
        // rolls out (jump it), two in phase 2
        out.add(BossAttack.of("slam").anim(SLAM).timing(22, 3, 16).range(0, 7.0).cooldown(80).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 3.2, ParticleTypes.FLAME);
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.BLAZE_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.5);
                    b.hitCircle(level, c, 3.2, 20.0F, 1.2, 0.6);
                    for (LivingEntity e : b.victims(level, c, 3.2)) {
                        burn(e, 60);
                    }
                    b.addEffect(WayfarerBoss.wave(c, 11, 0.5, 9.0F, ParticleTypes.FLAME));
                    if (b.phase() == 2) {
                        b.addEffect(delayed(12, WayfarerBoss.wave(c, 11, 0.5, 9.0F, ParticleTypes.SOUL_FIRE_FLAME)));
                    }
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 3, 0.8, 0.1, 0.8, 0);
                    level.sendParticles(ParticleTypes.LAVA, c.x, c.y + 0.3, c.z, 20, 1.4, 0.3, 1.4, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.3F) {
                        b.chain(level, "lash");
                    }
                })
                .build());
        // shackles: the gauntlet raised, its broken chain rattling (0.9 s), then swept down: under every player (and a
        // few strays) a ring of iron dust warns for 0.8 s, then chains burst up: 8 damage and held fast for 1.5 s
        out.add(BossAttack.of("shackles").anim(SHACKLES).timing(18, 20, 12).range(0, 20.0).cooldown(160).weight(8)
                .track(false)
                .start((b, level, t, tick) -> bound = false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.03F);
                    }
                    level.sendParticles(IRON, b.getX(), b.getY() + 4.0, b.getZ(), 2, 1.0, 0.6, 1.0, 0);
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof ChainedJailer j)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.4F);
                    for (LivingEntity e : b.victims(level, b.position(), 22.0)) {
                        b.addEffect(j.shackle(e.position(), 16, 1.6, 8.0F, 30));
                    }
                    int strays = b.phase() == 2 ? 4 : 2;
                    for (int i = 0; i < strays; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 3 + b.getRandom().nextDouble() * 8;
                        b.addEffect(j.shackle(b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 16, 1.6, 8.0F, 30));
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof ChainedJailer j && j.bound && b.phase() == 2 && t != null && b.distanceTo(t) > 5.0
                            && b.distanceTo(t) < HOOK_RANGE) {
                        b.chain(level, "hook");
                    }
                })
                .build());
        // kick: the foot drawn back (0.6 s, a short arc at his feet), then a heavy front kick that clears huggers
        out.add(BossAttack.of("kick").anim(KICK).timing(12, 3, 10).range(0, 3.5).cooldown(60).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 3.8, 60, ParticleTypes.SMOKE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 3.8, 60)) {
                        b.strike(level, e, 12.0F, 2.4, 0.45);
                    }
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // whirl: the chain paid out to his side (0.7 s, a ring of flame marks the reach), then the burning ball spun
        // round him for two seconds while he walks the target down
        out.add(BossAttack.of("whirl").anim(WHIRL).phaseTwo().timing(14, 40, 14).range(0, 9.0).cooldown(180).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), WHIRL_RADIUS, ParticleTypes.FLAME);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (t != null) {
                        Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                        if (to.length() > 1.5) {
                            Vec3 d = to.normalize().scale(b instanceof ChainedJailer j && j.unchained ? 0.19 : 0.15);
                            b.setDeltaMovement(d.x, b.getDeltaMovement().y, d.z);
                            b.hurtMarked = true;
                        }
                    }
                    if (tick % 6 == 0) {
                        for (LivingEntity e : b.victims(level, b.position(), WHIRL_RADIUS)) {
                            if (flatDist(e.position(), b.position()) <= WHIRL_RADIUS) {
                                b.strike(level, e, 9.0F, 1.5, 0.3);
                                burn(e, 40);
                            }
                        }
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                        level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.0F, 0.6F);
                    }
                    double a = tick * 0.55;
                    for (int k = 0; k < 3; k++) {
                        double aa = a - k * 0.18;
                        level.sendParticles(k == 0 ? ParticleTypes.LAVA : ParticleTypes.FLAME,
                                b.getX() + Math.cos(aa) * (WHIRL_RADIUS - 0.8), b.getY() + 1.4,
                                b.getZ() + Math.sin(aa) * (WHIRL_RADIUS - 0.8), 3, 0.2, 0.2, 0.2, 0.01);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // pyre: arms spread wide as the fire gathers (1.1 s, eight lines of embers on the floor), then both fists driven
        // into the floor: fire bursts run out along the four straight bars, then along the four diagonal ones
        out.add(BossAttack.of("pyre").anim(PYRE).phaseTwo().timing(22, 30, 14).range(0, 16.0).cooldown(220).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        for (int k = 0; k < 8; k++) {
                            Vec3 dir = rotate(b.forward(), k * 45);
                            for (double d = 2; d <= 14; d += 2) {
                                Vec3 p = b.position().add(dir.scale(d));
                                level.sendParticles(k % 2 == 0 ? ParticleTypes.FLAME : ParticleTypes.SMALL_FLAME,
                                        p.x, p.y + 0.1, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (int k = 0; k < 8; k++) {
                        Vec3 dir = rotate(b.forward(), k * 45);
                        int base = k % 2 == 0 ? 6 : 20;
                        for (int d = 2; d <= 14; d += 2) {
                            Vec3 p = b.position().add(dir.scale(d));
                            b.addEffect(fireBurst(p, base + d, 1.3, 13.0F));
                        }
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // unchain: he kneels and strains against his own chains (1.5 s, invulnerable, the fire in his cage swells),
        // then tears them apart: a nova of fire rolls out (jump it) and a ring of bursts erupts round him
        out.add(BossAttack.of("unchain").anim(UNCHAIN).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    unchainGuard = 52;
                    level.playSound(null, b, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.2, ParticleTypes.FLAME);
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.02F);
                    }
                    level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 3.5, b.getZ(), 4, 0.6, 0.6, 0.6, 0.03);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof ChainedJailer j) {
                        j.breakChains(level);
                    }
                })
                .build());
        // verdict: the chain whirled overhead (1.2 s), then flung up into the dark; chains of judgement rain on every
        // player in three volleys a second apart, each warned for 0.9 s by a ring of iron and flame: 14, held and burnt
        out.add(BossAttack.of("verdict").anim(VERDICT).phaseTwo().timing(24, 40, 16).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.4F);
                        level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 6.0, b.getZ(), 10, 1.5, 0.2, 1.5, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof ChainedJailer j)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    List<LivingEntity> targets = b.victims(level, b.position(), 30.0);
                    for (int v = 0; v < 3; v++) {
                        for (LivingEntity e : targets) {
                            b.addEffect(delayed(v * 20, j.shackleOn(e, 18, 1.8, 14.0F, 24)));
                        }
                        for (int i = 0; i < b.scaledCount(3); i++) {
                            double a = b.getRandom().nextDouble() * Math.PI * 2;
                            double r = 3 + b.getRandom().nextDouble() * 10;
                            Vec3 p = b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r);
                            b.addEffect(delayed(v * 20 + i * 3, j.shackle(p, 18, 1.8, 14.0F, 24)));
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** Living targets inside the arc that {@link #hitArc} covers (so a hit can also burn). */
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

    /** The chain flies down the aimed line; the first creature it meets is hurt and dragged to his feet. */
    private void throwHook(ServerLevel level) {
        Vec3 fwd = forward();
        Vec3 hand = position().add(0, 2.4, 0).add(fwd.scale(1.4));
        LivingEntity best = null;
        double bestAlong = HOOK_RANGE + 1;
        for (LivingEntity e : victims(level, position(), HOOK_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= HOOK_RANGE && side <= 1.1 + e.getBbWidth() / 2 && along < bestAlong
                    && Math.abs(e.getY() - getY()) < 5) {
                best = e;
                bestAlong = along;
            }
        }
        double reach = best != null ? bestAlong : HOOK_RANGE;
        for (double d = 1; d <= reach; d += 0.5) {
            Vec3 p = hand.add(fwd.scale(d)).add(0, -d / reach * 1.4, 0);
            level.sendParticles(d % 1.0 == 0 ? IRON : ParticleTypes.FLAME, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.6F);
        level.playSound(null, this, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
        if (best == null) {
            return;
        }
        if (best.hurtServer(level, damageSources().mobAttack(this), 9.0F)) {
            hooked = true;
            burn(best, 40);
            Vec3 dest = ahead(2.6);
            Vec3 pull = dest.subtract(best.position()).multiply(1, 0, 1);
            double dist = pull.length();
            Vec3 v = dist > 0.1 ? pull.normalize().scale(Math.min(2.4, 0.35 + dist * 0.16)) : Vec3.ZERO;
            best.setDeltaMovement(v.x, 0.45, v.z);
            best.hurtMarked = true;
            level.playSound(null, best, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    /**
     * A shackle on {@code pos}: a ring of iron dust and flame for {@code warn} ticks, then chains burst up: whoever
     * stands in it takes {@code damage} and is held fast for {@code hold} ticks (and burnt once he is unchained).
     */
    private Effect shackle(Vec3 pos, int warn, double radius, float damage, int hold) {
        int[] t = {0};
        List<LivingEntity> held = new ArrayList<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, IRON);
                    level.sendParticles(ParticleTypes.SMALL_FLAME, pos.x, pos.y + 0.1, pos.z, 2, radius * 0.3, 0, radius * 0.3, 0);
                }
                if (k == warn - 8) {
                    level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                }
                return false;
            }
            if (k == warn) {
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.8F, 0.5F);
                for (int i = 0; i < 6; i++) {               // the chains shooting up
                    double a = Math.PI * 2 * i / 6;
                    for (double y = 0; y < 2.4; y += 0.4) {
                        level.sendParticles(IRON, pos.x + Math.cos(a) * radius * 0.7, pos.y + y, pos.z + Math.sin(a) * radius * 0.7,
                                1, 0, 0, 0, 0);
                    }
                }
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (flatDist(e.position(), pos) <= radius && e.getY() - pos.y < 1.5) {
                        if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage)) {
                            held.add(e);
                            bound = true;
                            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, hold + 10, 3), boss);
                            if (unchained) {
                                burn(e, 60);
                            }
                        }
                    }
                }
                return held.isEmpty();
            }
            // held fast: no walking out and no jumping until the chains let go
            for (LivingEntity e : held) {
                if (e.isAlive()) {
                    e.setDeltaMovement(0, Math.min(0, e.getDeltaMovement().y), 0);
                    e.hurtMarked = true;
                    if (k % 4 == 0) {
                        level.sendParticles(IRON, e.getX(), e.getY() + 0.6, e.getZ(), 4, 0.3, 0.4, 0.3, 0);
                    }
                }
            }
            return k >= warn + hold;
        };
    }

    /** A shackle that follows {@code target} during its warning and locks where it stands at the last moment. */
    private Effect shackleOn(LivingEntity target, int warn, double radius, float damage, int hold) {
        int lock = Math.max(4, warn / 3);       // the ring follows for the first part of the warning, then stops
        int[] t = {0};
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (!target.isAlive()) {
                    return true;
                }
                if (t[0]++ < lock) {
                    if (t[0] % 2 == 0) {
                        boss.telegraphRing(level, target.position(), radius, ParticleTypes.SMALL_FLAME);
                    }
                    return false;
                }
                inner[0] = shackle(target.position(), warn - lock, radius, damage, hold);
            }
            return inner[0].tick(boss, level);
        };
    }

    /** Phase 3 starts: the chains snap, a fire nova rolls out and he is faster from now on. */
    private void breakChains(ServerLevel level) {
        unchained = true;
        verdictTimer = 80;
        Vec3 c = position();
        addEffect(WayfarerBoss.wave(c, 14, 0.55, 12.0F, ParticleTypes.FLAME));
        for (int i = 0; i < 12; i++) {
            double a = Math.PI * 2 * i / 12;
            addEffect(fireBurst(c.add(Math.cos(a) * 5.0, 0, Math.sin(a) * 5.0), 14, 1.5, 12.0F));
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("chained_jailer_unchained"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 2, c.z, 6, 1.2, 1.0, 1.2, 0);
        level.sendParticles(IRON, c.x, c.y + 2.5, c.z, 60, 1.5, 1.5, 1.5, 0.2);
        level.sendParticles(ParticleTypes.LAVA, c.x, c.y + 2.5, c.z, 30, 1.0, 1.0, 1.0, 0);
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return a.multiply(1, 0, 1).distanceTo(b.multiply(1, 0, 1));
    }

    private static void burn(LivingEntity e, int ticks) {
        e.setRemainingFireTicks(Math.max(e.getRemainingFireTicks(), ticks));
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
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

    /** A warned fire burst from the floor: smoke for {@code delay} ticks, then flame that hurts and burns. */
    private static Effect fireBurst(Vec3 pos, int delay, double radius, float damage) {
        Effect burst = WayfarerBoss.eruption(pos, delay, radius, damage, ParticleTypes.SMOKE, ParticleTypes.FLAME);
        return (boss, level) -> {
            boolean done = burst.tick(boss, level);
            if (done) {
                level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 0.3, pos.z, 3, radius * 0.3, 0.2, radius * 0.3, 0);
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.7F, 0.6F);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (flatDist(e.position(), pos) <= radius) {
                        burn(e, 60);
                    }
                }
            }
            return done;
        };
    }

    // ------------------------------------------------------------------ phase 3, ambience

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (unchainGuard > 0) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 6, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (unchainGuard > 0) {
            unchainGuard--;
        }
        if (phase() == 1) {
            if (unchained) {    // the fight was reset: chained again
                unchained = false;
                phaseTwoTick = -1;
            }
        } else if (phaseTwoTick >= 0 && tickCount - phaseTwoTick > 50 && currentAttack() == null && !isStaggered()
                && getTarget() != null && getTarget().isAlive()) {
            if (!unchained && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "unchain");
            } else if (unchained && --verdictTimer <= 0) {
                verdictTimer = (int) Math.round(VERDICT_EVERY * cooldownScale());
                chain(level, "verdict");
            }
        }
        // ambience: the fire in his cage and the gibbet, sparks off the dragged ball
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        if (tickCount % (unchained ? 2 : 5) == 0) {
            double hx = getX() - Mth.sin(yaw) * 0.6;
            double hz = getZ() + Mth.cos(yaw) * 0.6;
            level.sendParticles(unchained ? ParticleTypes.FLAME : ParticleTypes.SMALL_FLAME, hx, getY() + 4.5, hz,
                    1, 0.15, 0.1, 0.15, 0.01);
        }
        if (tickCount % 8 == 0) {
            double bx = getX() + Mth.sin(yaw) * 0.6 - Mth.cos(yaw) * 1.3;
            double bz = getZ() - Mth.cos(yaw) * 0.6 - Mth.sin(yaw) * 1.3;
            level.sendParticles(ParticleTypes.SMOKE, bx, getY() + 4.6, bz, 1, 0.1, 0.1, 0.1, 0.01);
        }
        if (tickCount % 60 == 0) {
            level.playSound(null, this, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.0F, 0.5F);
        }
        if (unchained) {
            if (tickCount % 4 == 0) {
                level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 2, 0.8, 1.2, 0.8, 0.01);
            }
            if (tickCount % 20 == 0) {          // a burning aura: hugging him is no longer safe
                for (LivingEntity e : victims(level, position(), 3.0)) {
                    if (flatDist(e.position(), position()) <= 3.0) {
                        e.hurtServer(level, damageSources().mobAttack(this), 3.0F);
                        burn(e, 40);
                    }
                }
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        phaseTwoTick = tickCount;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("chained_jailer_wrath"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BLAZE_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 60, 1.0, 1.5, 1.0, 0.05);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2.5, getZ(), 5, 1.0, 1.5, 1.0, 0);
        level.sendParticles(IRON, getX(), getY() + 2.5, getZ(), 80, 1.5, 2.0, 1.5, 0.2);
        level.sendParticles(ParticleTypes.LAVA, getX(), getY() + 3, getZ(), 30, 1.0, 1.5, 1.0, 0);
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.IRON_DOOR_OPEN, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
    }
}
