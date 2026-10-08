package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
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
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.IronHelmsman.BROADSIDE;
import static com.brasshaven.generated.MobAnims.IronHelmsman.CHARGE;
import static com.brasshaven.generated.MobAnims.IronHelmsman.HARPOON;
import static com.brasshaven.generated.MobAnims.IronHelmsman.OVERLOAD;
import static com.brasshaven.generated.MobAnims.IronHelmsman.ROAR;
import static com.brasshaven.generated.MobAnims.IronHelmsman.SLAM;
import static com.brasshaven.generated.MobAnims.IronHelmsman.STAGGER;
import static com.brasshaven.generated.MobAnims.IronHelmsman.SWEEP;
import static com.brasshaven.generated.MobAnims.IronHelmsman.VENT;
import static com.brasshaven.generated.MobAnims.IronHelmsman.WHIRL;

/**
 * Le Timonier de Fer (The Iron Helmsman), pilot and champion of the Walking Fortress: a hulking armoured captain fused
 * into a steam harness, a boiler on his back, a harpoon-cannon for a right arm and a ship's anchor dragged on a chain
 * in his left hand. He waits on the walker's open top deck, between the bridge tower and the smokestacks.
 * <p>A hard overworld fight meant for well-geared players: 450 health, armour 15, poise 95, hits of 10 to 22.
 * <ul>
 *     <li>Phase 1: <b>anchor sweep</b> (210 degree swing, 17), <b>anchor slam</b> (22 in front, then a shockwave ring
 *     to jump, 10), <b>harpoon</b> (a line shot up to 18 blocks: 10 and the victim is reeled in, then he sweeps),
 *     <b>steam vent</b> (a telegraphed 6-block scalding burst around him and a lingering cloud: punishes hugging),
 *     <b>ram</b> (a shoulder charge, 16).</li>
 *     <li>Phase 2 (after a roar at half health): faster, combos (sweep into slam, ram into sweep, slam into harpoon),
 *     <b>boiler overload</b> (four rings of fire bursts spreading out from him), <b>anchor whirl</b> (the anchor spun
 *     on its chain for two seconds while he walks you down) and <b>broadside</b>: he signals the walker's guns and
 *     three volleys of warned shells land on every player's position, plus strays on the deck.</li>
 * </ul>
 */
public class IronHelmsman extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 5.2F;
    private static final double VENT_RADIUS = 6.0;
    private static final double WHIRL_RADIUS = 5.5;
    private static final double HARPOON_RANGE = 18.0;

    /** Players already hit by the current ram (one hit per charge). */
    private final Set<UUID> rammed = new HashSet<>();
    /** Whoever the last harpoon caught (the follow-up sweep only comes when it hits). */
    private boolean hooked;

    public IronHelmsman(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 450.0)
                .add(Attributes.ARMOR, 15.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.IronHelmsman.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.WHITE;
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
        return 95.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.5;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // anchor sweep: hauled back to his left for a full second, then swung across 210 degrees in front of him
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(20, 4, 14).range(0, 7.0).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.8, 105, ParticleTypes.CRIT);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    if (tick % 3 == 0) {
                        Vec3 p = b.position().add(rotate(b.forward(), -100).scale(2.6));
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 0.2, p.z, 3, 0.3, 0.1, 0.3, 0.05);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 7.0, 105, 17.0F, 1.8);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 0.6F);
                    for (int a = -105; a <= 105; a += 15) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(5.2));
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.0, p.z, 1, 0, 0, 0, 0);
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 0.3, p.z, 2, 0.2, 0.1, 0.2, 0.05);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "slam");
                    }
                })
                .build());
        // anchor slam: heaved overhead (1.1 s), crashed down 4 blocks ahead; a shockwave ring rolls out: jump it
        out.add(BossAttack.of("slam").anim(SLAM).timing(22, 3, 15).range(0, 8.0).cooldown(80).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(4.0), 3.2, ParticleTypes.CRIT);
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(4.0);
                    b.hitCircle(level, c, 3.2, 22.0F, 1.2, 0.6);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 13 : 10, 0.5, 10.0F, ParticleTypes.LARGE_SMOKE));
                    if (b.phase() == 2) {
                        b.addEffect(delayed(14, WayfarerBoss.wave(c, 13, 0.45, 9.0F, ParticleTypes.FLAME)));
                    }
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 3, 0.8, 0.1, 0.8, 0);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, c.x, c.y + 0.3, c.z, 30, 1.4, 0.3, 1.4, 0.05);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "harpoon");
                    }
                })
                .build());
        // harpoon: the cannon arm is raised and aimed (0.8 s, a dotted line shows the aim), the harpoon flies down the
        // line; whoever it skewers is reeled in to the anchor's reach, and he follows with a sweep
        out.add(BossAttack.of("harpoon").anim(HARPOON).timing(16, 4, 14).range(5.0, HARPOON_RANGE).cooldown(110).weight(9)
                .start((b, level, t, tick) -> hooked = false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 2; d <= HARPOON_RANGE; d += 2) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 1.8F, 0.5F);
                        level.sendParticles(ParticleTypes.WHITE_SMOKE, b.getX(), b.getY() + 4.6, b.getZ(), 3, 0.2, 0.2, 0.2, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof IronHelmsman h) {
                        h.fireHarpoon(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof IronHelmsman h && h.hooked) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // steam vent: he hunches while the boiler swells and hisses (1.2 s, a ring of steam marks the reach), then
        // scalding steam bursts all around him and lingers for half a second
        out.add(BossAttack.of("vent").anim(VENT).timing(24, 10, 12).range(0, 5.5).cooldown(140).weight(8).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), VENT_RADIUS, ParticleTypes.CLOUD);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 1.5F, 0.6F + tick * 0.02F);
                    }
                    level.sendParticles(ParticleTypes.WHITE_SMOKE, b.getX(), b.getY() + 3.2, b.getZ(), 3, 0.8, 0.6, 0.8, 0.02);
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), VENT_RADIUS)) {
                        if (flatDist(e.position(), b.position()) <= VENT_RADIUS) {
                            b.strike(level, e, 12.0F, 1.6, 0.4);
                            scald(e, 60);
                        }
                    }
                    level.playSound(null, b, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.GENERIC_EXTINGUISH_FIRE, SoundSource.HOSTILE, 2.0F, 0.4F);
                    steamBurst(level, b.position(), VENT_RADIUS, 80);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 5 == 4) {
                        b.hitCircle(level, b.position(), VENT_RADIUS - 1.5, 4.0F, 0.6, 0.1);
                    }
                    steamBurst(level, b.position(), VENT_RADIUS - 1.0, 12);
                })
                .build());
        // ram: shoulder lowered behind the pauldron (0.8 s, a line of smoke along the path), then he barrels forward
        out.add(BossAttack.of("charge").anim(CHARGE).timing(16, 14, 12).range(6.0, 20.0).cooldown(100).weight(8)
                .start((b, level, t, tick) -> rammed.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 14; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.LARGE_SMOKE, p.x, p.y + 0.2, p.z, 1, 0.15, 0, 0.15, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(1.15, 0.0);
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    Vec3 f = b.forward().scale(1.05);
                    b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                    b.hurtMarked = true;
                    Vec3 front = b.ahead(1.8);
                    for (LivingEntity e : b.victims(level, front, 2.2)) {
                        if (rammed.add(e.getUUID())) {
                            b.strike(level, e, 16.0F, 2.2, 0.55);
                            level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.8F, 0.6F);
                        }
                    }
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 0.3, b.getZ(), 3, 0.7, 0.1, 0.7, 0.01);
                    level.sendParticles(ParticleTypes.WHITE_SMOKE, b.getX(), b.getY() + 4.8, b.getZ(), 2, 0.2, 0.2, 0.2, 0.05);
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // boiler overload: the boiler glows and swells (1.2 s, a ring of flame around him), then fire bursts out of
        // the deck in four rings spreading outward, each warned by smoke
        out.add(BossAttack.of("overload").anim(OVERLOAD).phaseTwo().timing(24, 30, 14).range(0, 14.0).cooldown(220).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 3.0, ParticleTypes.FLAME);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    level.sendParticles(ParticleTypes.LAVA, b.getX(), b.getY() + 3.0, b.getZ(), 1, 0.6, 0.6, 0.6, 0);
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.position();
                    double spin = b.getRandom().nextDouble() * Math.PI;
                    for (int ring = 0; ring < 4; ring++) {
                        double r = 3.0 + ring * 3.0;
                        int n = 6 + ring * 4;
                        for (int i = 0; i < n; i++) {
                            double a = spin + ring * 0.4 + Math.PI * 2 * i / n;
                            Vec3 p = c.add(Math.cos(a) * r, 0, Math.sin(a) * r);
                            b.addEffect(fireBurst(p, 12 + ring * 7, 1.6, 14.0F));
                        }
                    }
                    level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, c.x, c.y + 5.0, c.z, 30, 0.4, 0.8, 0.4, 0.08);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 5.0, b.getZ(), 6, 0.3, 0.5, 0.3, 0.05);
                    }
                })
                .build());
        // anchor whirl: the chain is paid out (0.7 s), then the anchor spins around him for two seconds while he
        // walks the target down; every few ticks the spinning anchor hits everything in reach
        out.add(BossAttack.of("whirl").anim(WHIRL).phaseTwo().timing(14, 40, 14).range(0, 9.0).cooldown(180).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), WHIRL_RADIUS, ParticleTypes.CRIT);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (t != null) {
                        Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                        if (to.length() > 1.5) {
                            Vec3 d = to.normalize().scale(0.15);
                            b.setDeltaMovement(d.x, b.getDeltaMovement().y, d.z);
                            b.hurtMarked = true;
                        }
                    }
                    if (tick % 6 == 0) {
                        b.hitCircle(level, b.position(), WHIRL_RADIUS, 10.0F, 1.5, 0.3);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.2F, 0.8F);
                    }
                    double a = tick * 0.55;
                    for (int k = 0; k < 3; k++) {
                        double aa = a - k * 0.18;
                        level.sendParticles(k == 0 ? ParticleTypes.ELECTRIC_SPARK : ParticleTypes.CRIT,
                                b.getX() + Math.cos(aa) * (WHIRL_RADIUS - 0.8), b.getY() + 1.4,
                                b.getZ() + Math.sin(aa) * (WHIRL_RADIUS - 0.8), 3, 0.2, 0.2, 0.2, 0.01);
                    }
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // broadside: the cannon arm is raised to the sky as a signal (1.0 s), the horn sounds and the walker's guns
        // fire: three volleys of shells land on every player's position (each warned for a second by a ring of
        // smoke and a whistle), plus strays scattered on the deck. Keep moving.
        out.add(BossAttack.of("broadside").anim(BROADSIDE).phaseTwo().timing(20, 38, 14).range(0, 30.0).cooldown(300).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 3.0F, 0.8F);
                    }
                    if (tick % 4 == 0) {
                        level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 6.0, b.getZ(), 4, 0.3, 0.4, 0.3, 0.05);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                    for (LivingEntity e : b.victims(level, b.position(), 30.0)) {
                        for (int v = 0; v < 3; v++) {
                            b.addEffect(shell(e, v * 12, 20, 2.6, 16.0F));
                        }
                    }
                    for (int i = 0; i < 6; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 4 + b.getRandom().nextDouble() * 9;
                        Vec3 p = b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r);
                        b.addEffect(delayed(i * 5, shellAt(p, 22, 2.6, 16.0F)));
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 12 == 0) { // the guns of the walker, booming somewhere below the deck
                        level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** The harpoon flies down the aimed line; the first creature it meets is hurt and reeled in. */
    private void fireHarpoon(ServerLevel level) {
        Vec3 fwd = forward();
        Vec3 muzzle = position().add(0, 2.2, 0).add(fwd.scale(1.6));
        LivingEntity best = null;
        double bestAlong = HARPOON_RANGE + 1;
        for (LivingEntity e : victims(level, position(), HARPOON_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= HARPOON_RANGE && side <= 1.1 + e.getBbWidth() / 2 && along < bestAlong
                    && Math.abs(e.getY() - getY()) < 5) {
                best = e;
                bestAlong = along;
            }
        }
        double reach = best != null ? bestAlong : HARPOON_RANGE;
        for (double d = 1; d <= reach; d += 0.6) {
            Vec3 p = muzzle.add(fwd.scale(d)).add(0, -d / reach * 1.0, 0);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        level.sendParticles(ParticleTypes.LARGE_SMOKE, muzzle.x, muzzle.y, muzzle.z, 12, 0.3, 0.3, 0.3, 0.05);
        level.playSound(null, this, SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
        if (best == null) {
            return;
        }
        if (best.hurtServer(level, damageSources().mobAttack(this), 10.0F)) {
            hooked = true;
            Vec3 dest = ahead(2.8);
            Vec3 pull = dest.subtract(best.position()).multiply(1, 0, 1);
            double dist = pull.length();
            Vec3 v = dist > 0.1 ? pull.normalize().scale(Math.min(2.4, 0.35 + dist * 0.16)) : Vec3.ZERO;
            best.setDeltaMovement(v.x, 0.45, v.z);
            best.hurtMarked = true;
            level.playSound(null, best, SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 2.0F, 0.6F);
            level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return a.multiply(1, 0, 1).distanceTo(b.multiply(1, 0, 1));
    }

    /** Sets {@code e} on fire for at least {@code ticks} (scalding steam, fire bursts). */
    private static void scald(LivingEntity e, int ticks) {
        e.setRemainingFireTicks(Math.max(e.getRemainingFireTicks(), ticks));
    }

    private static void steamBurst(ServerLevel level, Vec3 c, double radius, int count) {
        for (int i = 0; i < count; i++) {
            double a = level.getRandom().nextDouble() * Math.PI * 2;
            double r = Math.sqrt(level.getRandom().nextDouble()) * radius;
            level.sendParticles(i % 3 == 0 ? ParticleTypes.CLOUD : ParticleTypes.WHITE_SMOKE,
                    c.x + Math.cos(a) * r, c.y + 0.3 + level.getRandom().nextDouble() * 1.6, c.z + Math.sin(a) * r,
                    1, 0, 0.05, 0, 0.02);
        }
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis (keeps its y at 0). */
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

    /** A warned fire burst from the deck (the boiler overload): smoke for {@code delay} ticks, then flame that burns. */
    private static Effect fireBurst(Vec3 pos, int delay, double radius, float damage) {
        Effect burst = WayfarerBoss.eruption(pos, delay, radius, damage, ParticleTypes.SMOKE, ParticleTypes.FLAME);
        int[] t = {0};
        return (boss, level) -> {
            boolean done = burst.tick(boss, level);
            if (done) {
                level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y + 0.3, pos.z, 4, radius * 0.3, 0.2, radius * 0.3, 0);
                if (t[0]++ == 0) {
                    level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.8F, 0.6F);
                }
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (flatDist(e.position(), pos) <= radius) {
                        scald(e, 60);
                    }
                }
            }
            return done;
        };
    }

    /** A cannon shell aimed at {@code target}: after {@code wait} ticks it locks the spot where they stand. */
    private static Effect shell(LivingEntity target, int wait, int warn, double radius, float damage) {
        int[] t = {0};
        Effect[] inner = {null};
        return (boss, level) -> {
            if (inner[0] == null) {
                if (t[0]++ < wait) {
                    return false;
                }
                if (!target.isAlive()) {
                    return true;
                }
                inner[0] = shellAt(target.position(), warn, radius, damage);
            }
            return inner[0].tick(boss, level);
        };
    }

    /**
     * A shell landing on {@code pos}: a ring of smoke and a rising whistle for {@code warn} ticks, then an explosion
     * (particles and sound only, the deck is not broken) that hurts and throws whoever stands in it.
     */
    private static Effect shellAt(Vec3 pos, int warn, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, ParticleTypes.LARGE_SMOKE);
                    level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.1, pos.z, 2, radius * 0.3, 0, radius * 0.3, 0);
                }
                if (k == warn - 10) {
                    level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.5F, 1.8F);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.EXPLOSION, pos.x, pos.y + 0.5, pos.z, 3, radius * 0.3, 0.3, radius * 0.3, 0);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y + 0.5, pos.z, 20, radius * 0.4, 0.8, radius * 0.4, 0.05);
            level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.3, pos.z, 15, radius * 0.4, 0.3, radius * 0.4, 0.05);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F,
                    0.8F + level.getRandom().nextFloat() * 0.3F);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (flatDist(e.position(), pos) <= radius) {
                    boss.strike(level, e, damage, 0.8, 0.7);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ ambience, phase 2

    @Override
    protected void bossTick(ServerLevel level) {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        if (tickCount % (phase() == 2 ? 3 : 6) == 0) {   // smoke from the stack on his back, off to his left
            double sx = getX() + Mth.sin(yaw) * 0.6 + Mth.cos(yaw) * 0.4;
            double sz = getZ() - Mth.cos(yaw) * 0.6 + Mth.sin(yaw) * 0.4;
            level.sendParticles(phase() == 2 ? ParticleTypes.LARGE_SMOKE : ParticleTypes.SMOKE, sx, getY() + 5.3, sz,
                    1, 0.05, 0.05, 0.05, 0.01);
        }
        if (tickCount % 40 == 0) {
            level.playSound(null, this, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 0.6F, 0.5F);
        }
        if (phase() == 2 && tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 1, 0.7, 1.0, 0.7, 0.01);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("iron_helmsman_full_steam"), 0.15,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
        steamBurst(level, position(), 4.0, 100);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 5.5, getZ(), 40, 0.4, 1.0, 0.4, 0.1);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2.5, getZ(), 5, 1.0, 1.5, 1.0, 0);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 3, getZ(), 60, 1.0, 2.0, 1.0, 0.08);
        steamBurst(level, position(), 4.0, 80);
        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
        level.playSound(null, this, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0F, 0.4F);
    }
}
