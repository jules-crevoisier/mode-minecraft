package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
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
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.DuneKing.FLAIL;
import static com.brasshaven.generated.MobAnims.DuneKing.HOOK;
import static com.brasshaven.generated.MobAnims.DuneKing.JARS;
import static com.brasshaven.generated.MobAnims.DuneKing.JUDGEMENT;
import static com.brasshaven.generated.MobAnims.DuneKing.QUICKSAND;
import static com.brasshaven.generated.MobAnims.DuneKing.ROAR;
import static com.brasshaven.generated.MobAnims.DuneKing.SANDSTORM;
import static com.brasshaven.generated.MobAnims.DuneKing.SCARABS;
import static com.brasshaven.generated.MobAnims.DuneKing.STAGGER;
import static com.brasshaven.generated.MobAnims.DuneKing.SUMMON;

/**
 * Le Roi des dunes (The Dune King), the undead pharaoh-king of the Necropolis of Kings: a gaunt mummy under a towering
 * double crown, a lapis-and-gold collar, a crook and a flail, four canopic jars orbiting him and turquoise eyes.
 * He waits in the arena at the bottom of the tombs.
 * <p>460 health, armour 10, poise 85, hits of 8 to 16.
 * <ul>
 *     <li>Phase 1: <b>flail combo</b> (three lashes, 10/10/14), <b>crook hook</b> (a line up to 11 blocks: 10 and the
 *     victim is pulled in, then the flail), <b>sandstorm</b> (a cone of sand: blindness and slowness, light damage),
 *     <b>summon</b> (husks rise from the sand, never more than 4) and <b>canopic jars</b> (four curse bolts, 8 +
 *     wither).</li>
 *     <li>Phase 2 (after a roar at half health): he rises and floats, <b>quicksand</b> (pools burst in three
 *     spiral arms spreading out across the floor, plus one under every player: 12 + slowness), <b>scarab swarm</b>
 *     (two low rings of scarabs to jump, 10) and the <b>judgement</b>: a low beam sweeping 200 degrees across the
 *     arena (16): jump it or stand behind him.</li>
 * </ul>
 */
public class DuneKing extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 4.6F;
    private static final int MAX_MUMMIES = 4;
    private static final double HOOK_RANGE = 11.0;
    private static final double BEAM_LENGTH = 18.0;

    /** The last hook caught someone (the flail follows). */
    private boolean hooked;
    /** Judgement beam: tick of the last hit per victim. */
    private final Map<UUID, Integer> judged = new HashMap<>();

    public DuneKing(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 460.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.2);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.DuneKing.TICKS;
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
        return 85.0F;
    }

    @Override
    protected double preferredRange() {
        return 5.0;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // flail combo: the flail raised behind his shoulder (0.7 s, the arc is outlined), then three lashes half a
        // second apart, the last one heavier and wider
        out.add(BossAttack.of("flail").anim(FLAIL).timing(14, 22, 12).range(0, 6.5).cooldown(60).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.0, 70, ParticleTypes.WAX_ON);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> lash(b, level, 6.0, 70, 10.0F, 0.8))
                .active((b, level, t, tick) -> {
                    if (tick == 10) {
                        lash(b, level, 6.0, 70, 10.0F, 0.8);
                    } else if (tick == 20) {
                        lash(b, level, 6.5, 85, 14.0F, 1.6);
                    } else if (tick % 5 == 0) {
                        b.telegraphArc(level, tick > 10 ? 6.5 : 6.0, tick > 10 ? 85 : 70, ParticleTypes.WAX_ON);
                    }
                })
                .build());
        // crook hook: the crook levelled and drawn back (0.8 s, a dotted line shows its reach), then it shoots out: the
        // first creature on the line is hooked, hurt and pulled in front of him, and the flail follows
        out.add(BossAttack.of("hook").anim(HOOK).timing(16, 4, 14).range(4.0, HOOK_RANGE).cooldown(100).weight(9)
                .start((b, level, t, tick) -> hooked = false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= HOOK_RANGE; d += 1.5) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.WAX_ON, p.x, floorY(b) + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.HUSK_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DuneKing k) {
                        k.throwHook(level);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof DuneKing k && k.hooked) {
                        b.chain(level, "flail");
                    }
                })
                .build());
        // sandstorm: both arms swept up gathering the sand (1.0 s, the cone is outlined), then a 1.5 s storm blows in a
        // 70 degree cone 10 blocks long: blindness, slowness and a little damage every half second
        out.add(BossAttack.of("sandstorm").anim(SANDSTORM).timing(20, 30, 12).range(0, 10.0).cooldown(170).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 9.5, 35, sandDust());
                        b.telegraphArc(level, 5.0, 35, sandDust());
                    }
                    double a = tick * 0.5;
                    level.sendParticles(sandDust(), b.getX() + Math.cos(a) * 1.5, b.getY() + 2.5, b.getZ() + Math.sin(a) * 1.5,
                            3, 0.2, 0.4, 0.2, 0.02);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    Vec3 fwd = b.forward();
                    for (int i = 0; i < 10; i++) {
                        double ang = (b.getRandom().nextDouble() - 0.5) * 70;
                        double d = 1.5 + b.getRandom().nextDouble() * 8.5;
                        Vec3 p = b.position().add(rotate(fwd, ang).scale(d));
                        level.sendParticles(sandDust(), p.x, floorY(b) + 0.4 + b.getRandom().nextDouble() * 2.0, p.z,
                                1, 0.2, 0.2, 0.2, 0.05);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BRUSH_SAND, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    if (tick % 10 == 0) {
                        double cos = Math.cos(Math.toRadians(35));
                        for (LivingEntity e : b.victims(level, b.position(), 10.5)) {
                            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
                            if (to.length() <= 10.0 && (to.length() < 1.0 || to.normalize().dot(fwd) >= cos)) {
                                b.strike(level, e, 3.0F, 0.3, 0.05);
                                e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), b);
                                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), b);
                            }
                        }
                    }
                })
                .build());
        // summon: crook and flail crossed over the crown (1.0 s, sand churns where they will rise), the crook struck on
        // the floor: husks claw their way out of the sand, never more than four at once
        out.add(BossAttack.of("summon").anim(SUMMON).timing(20, 4, 16).range(0, 30.0).cooldown(400).weight(5)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && b instanceof DuneKing k) {
                        for (Vec3 p : k.risePoints()) {
                            level.sendParticles(sandDust(), p.x, p.y + 0.1, p.z, 6, 0.5, 0.05, 0.5, 0.02);
                            b.telegraphRing(level, p, 1.0, ParticleTypes.SOUL);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof DuneKing k) {
                        k.raiseMummies(level, b.phase() == 2 ? 3 : 2);
                    }
                    level.playSound(null, b, SoundEvents.ZOMBIE_INFECT, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // canopic jars: the crook pointed at the foe (0.7 s, a ring marks the target), then each of the four jars spits a
        // curse bolt in turn, aimed where the target stands at that moment: 8 and a short wither
        out.add(BossAttack.of("jars").anim(JARS).timing(14, 24, 12).range(3.0, 24.0).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 1.4, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                    level.sendParticles(ParticleTypes.GLOW, b.getX(), b.getY() + 2.8, b.getZ(), 2, 1.2, 0.3, 1.2, 0.01);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.0F, 1.4F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 6 == 0 && tick < 24 && t != null) {
                        double ang = b.tickCount * 6.0 + tick * 15;      // the jar that is in front at this moment
                        Vec3 from = b.position().add(rotate(b.forward(), ang % 90 - 45).scale(1.3)).add(0, 2.8, 0);
                        Vec3 to = t.position().add(0, t.getBbHeight() * 0.5, 0);
                        b.addEffect(curseBolt(from, to.subtract(from).normalize(), 26.0, 8.0F));
                        level.playSound(null, b, SoundEvents.WITHER_SHOOT, SoundSource.HOSTILE, 0.8F, 1.6F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // quicksand: palms turned to the floor (1.0 s, sand swirls round him), then quicksand bursts in three spiral
        // arms spreading out to 14 blocks, plus a pool under every player; each pool is warned by falling sand
        out.add(BossAttack.of("quicksand").anim(QUICKSAND).phaseTwo().timing(20, 40, 14).range(0, 16.0).cooldown(220)
                .weight(8).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, floor(b), 2.5, sandDust());
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.SAND_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = floor(b);
                    double spin = b.getRandom().nextDouble() * Math.PI * 2;
                    for (int arm = 0; arm < 3; arm++) {
                        for (int i = 0; i < 8; i++) {
                            double r = 2.5 + i * 1.6;
                            double a = spin + arm * Math.PI * 2 / 3 + i * 0.35;
                            Vec3 p = c.add(Math.cos(a) * r, 0, Math.sin(a) * r);
                            b.addEffect(quicksand(p, 12 + i * 4, 1.7, 12.0F));
                        }
                    }
                    for (LivingEntity e : b.victims(level, b.position(), 18.0)) {
                        b.addEffect(quicksand(new Vec3(e.getX(), c.y, e.getZ()), 24, 1.8, 12.0F));
                    }
                    level.playSound(null, b, SoundEvents.SUSPICIOUS_SAND_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());
        // scarab swarm: the flail raised high (0.8 s, the scarabs gather at his feet) and cracked on the floor: two low
        // rings of scarabs roll out across the arena; jump each one
        out.add(BossAttack.of("scarabs").anim(SCARABS).phaseTwo().timing(16, 30, 12).range(0, 14.0).cooldown(160).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, floor(b), 2.0, scarab());
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.SILVERFISH_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = floor(b);
                    b.addEffect(scarabWave(c));
                    b.addEffect(delayed(16, scarabWave(c)));
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.playSound(null, b, SoundEvents.SILVERFISH_STEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .build());
        // judgement: the crook held out level and the eyes blaze (1.2 s, a line of light marks where the beam starts,
        // on his left), then a low beam sweeps 200 degrees from his left to his right over 2.5 s: jump it as it passes,
        // or get behind him
        out.add(BossAttack.of("judgement").anim(JUDGEMENT).phaseTwo().timing(24, 50, 16).range(0, 20.0).cooldown(280)
                .weight(7).track(false)
                .start((b, level, t, tick) -> judged.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        Vec3 dir = rotate(b.forward(), -100);
                        Vec3 c = floor(b);
                        for (double d = 1.5; d <= BEAM_LENGTH; d += 1.0) {
                            Vec3 p = c.add(dir.scale(d));
                            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
                        }
                        for (int a = -100; a <= 100; a += 20) {
                            Vec3 p = c.add(rotate(b.forward(), a).scale(3.0));
                            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    level.sendParticles(ParticleTypes.GLOW, b.getX(), b.getY() + 4.0, b.getZ(), 1, 0.2, 0.1, 0.2, 0.01);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.5F, 1.2F))
                .active((b, level, t, tick) -> {
                    if (b instanceof DuneKing k) {
                        k.judgementBeam(level, -100 + 200.0 * tick / 49.0);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private static void lash(WayfarerBoss b, ServerLevel level, double range, double halfAngle, float damage, double kb) {
        b.hitArc(level, range, halfAngle, damage, kb);
        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, b, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.8F);
        for (double a = -halfAngle; a <= halfAngle; a += 20) {
            Vec3 p = b.position().add(rotate(b.forward(), a).scale(range * 0.7));
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** The crook shoots down the aimed line; the first creature it meets is hurt and pulled in front of him. */
    private void throwHook(ServerLevel level) {
        Vec3 fwd = forward();
        LivingEntity best = null;
        double bestAlong = HOOK_RANGE + 1;
        for (LivingEntity e : victims(level, position(), HOOK_RANGE + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= HOOK_RANGE && side <= 1.0 + e.getBbWidth() / 2 && along < bestAlong
                    && Math.abs(e.getY() - floorY(this)) < 4) {
                best = e;
                bestAlong = along;
            }
        }
        double reach = best != null ? bestAlong : HOOK_RANGE;
        Vec3 hand = position().add(0, 2.0, 0);
        for (double d = 1; d <= reach; d += 0.5) {
            Vec3 p = hand.add(fwd.scale(d));
            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        level.playSound(null, this, SoundEvents.TRIDENT_RETURN, SoundSource.HOSTILE, 2.0F, 0.6F);
        if (best == null) {
            return;
        }
        if (best.hurtServer(level, damageSources().mobAttack(this), 10.0F)) {
            hooked = true;
            Vec3 dest = ahead(2.2);
            Vec3 pull = dest.subtract(best.position()).multiply(1, 0, 1);
            double dist = pull.length();
            Vec3 v = dist > 0.1 ? pull.normalize().scale(Math.min(2.0, 0.35 + dist * 0.16)) : Vec3.ZERO;
            best.setDeltaMovement(v.x, 0.4, v.z);
            best.hurtMarked = true;
            level.playSound(null, best, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
    }

    /** Four places on a ring around him where the dead rise. */
    private List<Vec3> risePoints() {
        Vec3 c = floor(this);
        double base = Math.toRadians(getYRot());
        return List.of(0, 1, 2, 3).stream().map(i -> {
            double a = base + Math.PI / 4 + i * Math.PI / 2;
            return c.add(Math.cos(a) * 6.0, 0, Math.sin(a) * 6.0);
        }).toList();
    }

    /** Husks claw out of the sand at the rise points, never more than {@link #MAX_MUMMIES} alive at once. */
    private void raiseMummies(ServerLevel level, int wanted) {
        int alive = level.getEntitiesOfClass(Husk.class, getBoundingBox().inflate(40),
                h -> h.isAlive() && h.entityTags().contains(MINION_TAG)).size();
        List<Vec3> points = risePoints();
        for (int i = 0; i < Math.min(wanted, MAX_MUMMIES - alive); i++) {
            Husk husk = EntityTypes.HUSK.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (husk == null) {
                continue;
            }
            Vec3 p = points.get((i + random.nextInt(4)) % 4);
            husk.snapTo(p.x, p.y, p.z, getYRot(), 0);
            husk.addTag(MINION_TAG);
            husk.setTarget(getTarget());
            level.addFreshEntity(husk);
            level.sendParticles(sandDust(), p.x, p.y + 0.5, p.z, 40, 0.5, 0.8, 0.5, 0.05);
            level.sendParticles(ParticleTypes.SOUL, p.x, p.y + 0.5, p.z, 8, 0.3, 0.6, 0.3, 0.03);
        }
    }

    /** The judgement beam, {@code degrees} from his facing (negative is his left): low, it can be jumped. */
    private void judgementBeam(ServerLevel level, double degrees) {
        Vec3 dir = rotate(forward(), degrees);
        Vec3 c = floor(this);
        for (double d = 1.0; d <= BEAM_LENGTH; d += 0.5) {
            Vec3 p = c.add(dir.scale(d));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.4, p.z, 1, 0.02, 0.05, 0.02, 0);
            if (((int) (d * 2)) % 6 == 0) {
                level.sendParticles(ParticleTypes.GLOW, p.x, p.y + 0.4, p.z, 1, 0.05, 0.05, 0.05, 0);
            }
        }
        if (tickCount % 6 == 0) {
            level.playSound(null, this, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 2.5F, 1.6F);
        }
        for (LivingEntity e : victims(level, c, BEAM_LENGTH + 1)) {
            Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            boolean grounded = e.getY() - c.y < 0.9;
            Integer last = judged.get(e.getUUID());
            if (along >= 0 && along <= BEAM_LENGTH && side <= 0.7 + e.getBbWidth() / 2 && grounded
                    && (last == null || tickCount - last >= 10)) {
                judged.put(e.getUUID(), tickCount);
                strike(level, e, 16.0F, 0.8, 0.3);
                e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100, 0), this);
            }
        }
    }

    private static BlockParticleOption sandDust() {
        return new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.SAND.defaultBlockState());
    }

    private static DustParticleOptions scarab() {
        return new DustParticleOptions(0x2A3A20, 1.4F);
    }

    /** A low ring of scarabs rolling out to the edge of the arena: jump it. */
    private static Effect scarabWave(Vec3 c) {
        Effect ring = WayfarerBoss.wave(c, 16.0, 0.5, 10.0F, scarab());
        int[] t = {0};
        return (boss, level) -> {
            if (t[0]++ % 2 == 0) {
                double r = 0.5 + t[0] * 0.5;
                for (int i = 0; i < 8; i++) {
                    double a = Math.PI * 2 * i / 8 + t[0] * 0.1;
                    level.sendParticles(ParticleTypes.SMOKE, c.x + Math.cos(a) * r, c.y + 0.1, c.z + Math.sin(a) * r, 1, 0.1, 0, 0.1, 0);
                }
            }
            return ring.tick(boss, level);
        };
    }

    /** A pool of quicksand: falling sand for {@code delay} ticks, then a burst that hurts and slows. */
    private static Effect quicksand(Vec3 pos, int delay, double radius, float damage) {
        Effect burst = WayfarerBoss.eruption(pos, delay, radius, damage, sandDust(),
                new BlockParticleOption(ParticleTypes.BLOCK, Blocks.SAND.defaultBlockState()));
        int[] t = {0};
        return (boss, level) -> {
            boolean done = burst.tick(boss, level);
            if (!done && t[0]++ % 4 == 0) {
                boss.telegraphRing(level, pos, radius, sandDust());
            }
            if (done) {
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2), boss);
                    }
                }
            }
            return done;
        };
    }

    /** A curse bolt from a canopic jar: flies straight at 0.7 blocks a tick, stops on walls, 8 damage and wither. */
    private static Effect curseBolt(Vec3 from, Vec3 dir, double maxDist, float damage) {
        double[] d = {0};
        return (boss, level) -> {
            d[0] += 0.7;
            Vec3 p = from.add(dir.scale(d[0]));
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0.01);
            level.sendParticles(ParticleTypes.GLOW, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
            BlockPos bp = BlockPos.containing(p);
            if (!level.getBlockState(bp).getCollisionShape(level, bp).isEmpty()) {
                level.sendParticles(ParticleTypes.SOUL, p.x, p.y, p.z, 6, 0.2, 0.2, 0.2, 0.02);
                return true;
            }
            for (LivingEntity e : boss.victims(level, p, 1.5)) {
                if (e.getBoundingBox().inflate(0.3).contains(p)) {
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage)) {
                        e.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 0), boss);
                    }
                    level.sendParticles(ParticleTypes.SOUL, p.x, p.y, p.z, 10, 0.2, 0.2, 0.2, 0.03);
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.DECORATED_POT_SHATTER, SoundSource.HOSTILE, 0.8F, 1.4F);
                    return true;
                }
            }
            return d[0] >= maxDist;
        };
    }

    /** Height of the floor under the boss (he floats in phase 2; ground moves are drawn on the floor). */
    private static double floorY(WayfarerBoss b) {
        BlockPos.MutableBlockPos p = b.blockPosition().mutable();
        for (int i = 0; i < 6; i++) {
            BlockPos below = p.below();
            if (!b.level().getBlockState(below).getCollisionShape(b.level(), below).isEmpty()) {
                return p.getY();
            }
            p.move(0, -1, 0);
        }
        return b.getY();
    }

    private static Vec3 floor(WayfarerBoss b) {
        return new Vec3(b.getX(), floorY(b), b.getZ());
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis (positive turns toward the boss's right). */
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

    // ------------------------------------------------------------------ floating, ambience, phase 2

    @Override
    protected void bossTick(ServerLevel level) {
        boolean floating = phase() == 2;
        if (isNoGravity() != floating) {
            setNoGravity(floating);
        }
        if (floating) {   // hover 1.4 blocks over the floor and drift toward the target between moves
            double dy = (floorY(this) + 1.4 - getY()) * 0.15;
            Vec3 v = getDeltaMovement();
            double vx = v.x;
            double vz = v.z;
            LivingEntity t = getTarget();
            if (currentAttack() == null && !isStaggered() && t != null) {
                Vec3 to = t.position().subtract(position()).multiply(1, 0, 1);
                if (to.length() > preferredRange()) {
                    Vec3 d = to.normalize().scale(0.17);
                    vx = d.x;
                    vz = d.z;
                } else {
                    vx *= 0.5;
                    vz *= 0.5;
                }
            }
            setDeltaMovement(vx, dy, vz);
            if (tickCount % 3 == 0) {
                level.sendParticles(sandDust(), getX(), floorY(this) + 0.2, getZ(), 2, 0.6, 0.05, 0.6, 0.01);
            }
        }
        if (tickCount % 10 == 0) {   // turquoise light in the eye sockets, the jars trailing a glow
            Vec3 face = position().add(forward().scale(0.3));
            level.sendParticles(ParticleTypes.GLOW, face.x, getY() + 3.9, face.z, 1, 0.1, 0.05, 0.1, 0);
            double a = tickCount * 0.105;
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX() + Math.cos(a) * 1.25, getY() + 2.8,
                    getZ() + Math.sin(a) * 1.25, 1, 0, 0, 0, 0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        setNoGravity(true);
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("dune_king_risen"), 0.15,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        for (int i = 0; i < 40; i++) {   // a column of sand rising around him as he lifts off the floor
            double a = i * 0.45;
            double r = 2.5 - i * 0.04;
            level.sendParticles(sandDust(), getX() + Math.cos(a) * r, getY() + i * 0.12, getZ() + Math.sin(a) * r, 3, 0.1, 0.1, 0.1, 0.02);
        }
        level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 2.0, getZ(), 30, 1.0, 1.5, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.5F, 1.2F);
        level.playSound(null, this, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        setNoGravity(false);
        level.sendParticles(sandDust(), getX(), getY() + 2.0, getZ(), 150, 1.0, 2.0, 1.0, 0.05);
        level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 2.5, getZ(), 40, 0.8, 1.5, 0.8, 0.08);
        level.playSound(null, this, SoundEvents.HUSK_DEATH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.SUSPICIOUS_SAND_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
        for (Husk h : level.getEntitiesOfClass(Husk.class, getBoundingBox().inflate(48), h -> h.entityTags().contains(MINION_TAG))) {
            level.sendParticles(sandDust(), h.getX(), h.getY() + 1.0, h.getZ(), 20, 0.3, 0.6, 0.3, 0.02);
            h.discard();   // the dead sink back into the sand
        }
    }
}
