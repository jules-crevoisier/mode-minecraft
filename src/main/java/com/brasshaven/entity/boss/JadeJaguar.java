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

import static com.brasshaven.generated.MobAnims.JadeJaguar.BELLOW;
import static com.brasshaven.generated.MobAnims.JadeJaguar.CLAW;
import static com.brasshaven.generated.MobAnims.JadeJaguar.MAUL;
import static com.brasshaven.generated.MobAnims.JadeJaguar.PERCH;
import static com.brasshaven.generated.MobAnims.JadeJaguar.POUNCE;
import static com.brasshaven.generated.MobAnims.JadeJaguar.ROAR;
import static com.brasshaven.generated.MobAnims.JadeJaguar.SPIRITS;
import static com.brasshaven.generated.MobAnims.JadeJaguar.STAGGER;
import static com.brasshaven.generated.MobAnims.JadeJaguar.TAIL_SWEEP;

/**
 * Le Jaguar de jade (The Jade Jaguar): boss of the Jungle Ziggurat, prowling the sacred cenote under the pyramid.
 * Fast and agile: it never lets the player rest at range.
 * <ul>
 *     <li>Phase 1: pounce (gap closer), double claw rake, tail sweep (all around it), bellow (a cone that blasts the
 *     player away), and the perch: it springs high above the floor, clings there watching, then dives on the
 *     player's shadow.</li>
 *     <li>Phase 2 (after a roar): faster; pounces chain into triple pounces, the rake chains into a tail sweep,
 *     jade spirits (three spectral jaguars that dash through the player one after the other, each telegraphed by a
 *     glowing track), and the maul: it rears up and hammers the floor, sending two rings to jump.</li>
 * </ul>
 */
public class JadeJaguar extends WayfarerBoss {
    public static final float WIDTH = 2.4F;
    public static final float HEIGHT = 3.0F;

    private static final DustParticleOptions JADE = new DustParticleOptions(0x3FCB8A, 1.6F);
    private static final DustParticleOptions JADE_DIM = new DustParticleOptions(0x1E7A56, 1.2F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF0C040, 1.2F);

    /** Pounces still to chain in a phase 2 frenzy. */
    private int chainLeft;
    private boolean chaining;
    /** Perch: the height it clings at, and where it dives. */
    private double apexY;
    private Vec3 diveTo = Vec3.ZERO;

    public JadeJaguar(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 380.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ARMOR_TOUGHNESS, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.31)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.JadeJaguar.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.GREEN;
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
        return 60.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;   // a cat always lands
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // pounce: crouches with the haunches coiled (0.7 s), springs at the target and lands claws first
        out.add(BossAttack.of("pounce").anim(POUNCE).timing(14, 8, 10).range(4.5, 16).cooldown(60).weight(10)
                .start((b, level, t, tick) -> {
                    JadeJaguar self = (JadeJaguar) b;
                    if (!self.chaining) {
                        self.chainLeft = b.phase() == 2 && b.getRandom().nextFloat() < 0.6F ? 2 : 0;
                    }
                    self.chaining = false;
                    level.playSound(null, b, SoundEvents.HOGLIN_ANGRY, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 2.5, JADE);
                    }
                    level.sendParticles(JADE_DIM, b.getX(), b.getY() + 0.2, b.getZ(), 3, 1.0, 0.05, 1.0, 0);
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Mth.clamp(dist * 0.17, 0.8, 2.4), 0.5);
                    level.playSound(null, b, SoundEvents.PHANTOM_BITE, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 6) {
                        b.hitCircle(level, b.position(), 3.0, 14.0F, 1.0, 0.4);
                        level.sendParticles(ParticleTypes.CRIT, b.getX(), b.getY() + 0.5, b.getZ(), 30, 1.5, 0.3, 1.5, 0.3);
                        level.sendParticles(JADE, b.getX(), b.getY() + 0.2, b.getZ(), 30, 1.8, 0.1, 1.8, 0.05);
                        level.playSound(null, b, SoundEvents.RAVAGER_STEP, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .end((b, level, t, tick) -> {
                    JadeJaguar self = (JadeJaguar) b;
                    if (self.chainLeft > 0 && t != null && t.isAlive()) {
                        self.chainLeft--;
                        self.chaining = true;
                        b.chain(level, "pounce");
                    }
                })
                .build());
        // claw: rises on the hind legs (0.6 s), right paw rakes, then the left (0.95 s)
        out.add(BossAttack.of("claw").anim(CLAW).timing(12, 8, 12).range(0, 4.5).cooldown(25).weight(14)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.0, 70, JADE_DIM);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 7) {
                        b.lunge(0.35, 0.0);
                        b.hitArc(level, 4.5, 80, tick == 0 ? 10.0F : 11.0F, 0.8);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.8F, tick == 0 ? 0.8F : 0.7F);
                        Vec3 p = b.ahead(2.0);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 1, 0, 0, 0, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "tail_sweep");
                    }
                })
                .build());
        // tail sweep: coils (0.75 s, a ring warns all around), then whirls a full turn, the tail lashing everything near
        out.add(BossAttack.of("tail_sweep").anim(TAIL_SWEEP).timing(15, 6, 11).range(0, 5.0).cooldown(70).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.5, JADE_DIM);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 5.5, 11.0F, 1.6, 0.35);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    double a = tick * Math.PI / 3;
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, b.getX() + Math.cos(a) * 3.5, b.getY() + 1.0,
                            b.getZ() + Math.sin(a) * 3.5, 1, 0, 0, 0, 0);
                })
                .build());
        // bellow: the head drawn low (0.8 s), then a roar that blasts everything in front off its feet
        out.add(BossAttack.of("bellow").anim(BELLOW).timing(16, 10, 10).range(0, 9).cooldown(140).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 9.0, 45, GOLD);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.POLAR_BEAR_WARNING, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 3.0F, 0.7F);
                    Vec3 fwd = b.forward();
                    double cos = Math.cos(Math.toRadians(50));
                    for (LivingEntity e : b.victims(level, b.position(), 10)) {
                        Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
                        if (to.length() <= 9.5 && (to.length() < 1.5 || to.normalize().dot(fwd) >= cos)) {
                            b.strike(level, e, 7.0F, 0, 0);
                            Vec3 push = to.normalize().scale(2.6);
                            e.push(push.x, 0.6, push.z);
                            e.hurtMarked = true;
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    for (int i = 1; i <= 4; i++) {
                        Vec3 p = b.ahead(i * 2.0 + tick * 0.2);
                        level.sendParticles(ParticleTypes.GUST, p.x, p.y + 1.3, p.z, 1, 0.3, 0.3, 0.3, 0);
                    }
                })
                .build());
        // perch: crouch (0.6 s), spring high above the floor and cling there watching (its shadow ring follows the
        // player), dive at 1.6 s and land at 1.8 s; a long recovery after the landing
        out.add(BossAttack.of("perch").anim(PERCH).timing(12, 28, 20).range(0, 28).cooldown(300).weight(5)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(JADE_DIM, b.getX(), b.getY() + 0.2, b.getZ(), 4, 1.2, 0.05, 1.2, 0);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.HOGLIN_ANGRY, SoundSource.HOSTILE, 1.8F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    JadeJaguar self = (JadeJaguar) b;
                    int k = 1;
                    BlockPos base = b.blockPosition();
                    while (k < 8 && level.getBlockState(base.above(k + 4)).isAir()) {
                        k++;
                    }
                    self.apexY = b.getY() + k;
                    self.diveTo = t != null ? t.position() : b.position();
                    b.setNoGravity(true);
                    level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.2, b.getZ(), 20, 1.0, 0.1, 1.0, 0.05);
                })
                .active((b, level, t, tick) -> {
                    JadeJaguar self = (JadeJaguar) b;
                    if (tick <= 5) {
                        b.setDeltaMovement(0, (self.apexY - b.getY()) * 0.45, 0);
                        b.hurtMarked = true;
                    } else if (tick < 20) {
                        b.setDeltaMovement(Vec3.ZERO);
                        b.hurtMarked = true;
                        if (t != null && tick < 18) {
                            self.diveTo = t.position();
                        }
                        if (tick % 2 == 0) {
                            b.telegraphRing(level, self.diveTo, 3.5, JADE);
                            level.sendParticles(JADE_DIM, b.getX(), b.getY() + 1, b.getZ(), 4, 1.0, 0.6, 1.0, 0.02);
                        }
                        if (tick == 16) {
                            level.playSound(null, b, SoundEvents.PHANTOM_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                        }
                    } else if (tick < 24) {
                        Vec3 v = self.diveTo.subtract(b.position());
                        b.setDeltaMovement(v.scale(1.0 / (24 - tick)));
                        b.hurtMarked = true;
                        level.sendParticles(JADE, b.getX(), b.getY() + 1, b.getZ(), 6, 0.6, 0.6, 0.6, 0.02);
                    } else if (tick == 24) {
                        b.setNoGravity(false);
                        b.setDeltaMovement(Vec3.ZERO);
                        b.hitCircle(level, b.position(), 3.5, 16.0F, 1.2, 0.5);
                        if (b.phase() == 2) {
                            b.addEffect(WayfarerBoss.wave(b.position(), 10, 0.5, 8.0F, JADE));
                        }
                        level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 0.5, b.getZ(), 3, 1.0, 0.2, 1.0, 0);
                        level.sendParticles(JADE, b.getX(), b.getY() + 0.2, b.getZ(), 60, 2.5, 0.2, 2.5, 0.1);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.7F);
                    }
                })
                .end((b, level, t, tick) -> b.setNoGravity(false))
                .build());

        // ---------------------------------------------------------------- phase 2
        // spirits: sits back and howls (0.8 s); three jade ghosts take shape around the player, each marks its
        // track on the floor, then dashes through
        out.add(BossAttack.of("spirits").anim(SPIRITS).phaseTwo().timing(16, 4, 20).range(0, 30).cooldown(260).weight(7)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(JADE, b.getX(), b.getY() + 3.2, b.getZ(), 4, 0.6, 0.6, 0.6, 0.05);
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 1.5F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (t == null) {
                        return;
                    }
                    double a0 = b.getRandom().nextDouble() * Math.PI * 2;
                    for (int i = 0; i < 3; i++) {
                        double a = a0 + i * Math.PI * 2 / 3;
                        Vec3 from = t.position().add(Math.cos(a) * 7.0, 0, Math.sin(a) * 7.0);
                        b.addEffect(spirit(from, t, i * 14));
                    }
                    level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 1.2F);
                })
                .build());
        // maul: rears up tall (1.05 s) and hammers the floor with both forepaws: two rings roll out to be jumped
        out.add(BossAttack.of("maul").anim(MAUL).phaseTwo().timing(21, 2, 15).range(0, 7).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(2.5), 3.5, GOLD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(2.5);
                    b.hitCircle(level, c, 3.5, 16.0F, 1.0, 0.5);
                    b.addEffect(WayfarerBoss.wave(c, 13, 0.5, 8.0F, JADE));
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 3, 1.0, 0.2, 1.0, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 1) {
                        b.addEffect(delayedWave(b.ahead(2.5), 8));
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private effects

    /** A second ring, released a little after the first so a single jump does not clear both. */
    private static Effect delayedWave(Vec3 c, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            if (++t[0] < delay) {
                return false;
            }
            boss.addEffect(WayfarerBoss.wave(c, 13, 0.4, 8.0F, GOLD));
            return true;
        };
    }

    /**
     * A jade spirit: after {@code delay} ticks it takes shape at {@code from} (a jaguar of green light), marks its
     * track toward the prey on the floor for 16 ticks, then dashes along it, hurting whoever it passes through.
     */
    private static Effect spirit(Vec3 from, LivingEntity prey, int delay) {
        int[] t = {0};
        Vec3[] pos = {from};
        Vec3[] dir = {Vec3.ZERO};
        double[] run = {0};
        Set<UUID> hit = new HashSet<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                return false;
            }
            int s = k - delay;
            if (s == 0) {
                Vec3 to = prey.position().subtract(from).multiply(1, 0, 1);
                dir[0] = to.lengthSqr() < 0.01 ? boss.forward() : to.normalize();
                pos[0] = new Vec3(from.x, prey.getY(), from.z);
                level.playSound(null, from.x, from.y, from.z, SoundEvents.EVOKER_CAST_SPELL, SoundSource.HOSTILE, 1.5F, 1.4F);
            }
            Vec3 p = pos[0];
            Vec3 d = dir[0];
            if (s < 16) {
                drawSpirit(level, p, d, s % 2 == 0);
                if (s % 2 == 0) {
                    for (double u = 1; u <= 16; u += 1.0) {
                        Vec3 q = p.add(d.scale(u));
                        level.sendParticles(JADE_DIM, q.x, q.y + 0.1, q.z, 1, 0.05, 0, 0.05, 0);
                    }
                }
                return false;
            }
            if (s == 16) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.PHANTOM_BITE, SoundSource.HOSTILE, 2.0F, 0.8F);
            }
            pos[0] = p.add(d.scale(1.15));
            run[0] += 1.15;
            drawSpirit(level, pos[0], d, true);
            for (LivingEntity e : boss.victims(level, pos[0], 2.0)) {
                if (e.position().distanceTo(pos[0]) <= 1.6 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 10.0F, 0.9, 0.3);
                }
            }
            if (run[0] >= 16) {
                level.sendParticles(JADE, pos[0].x, pos[0].y + 1, pos[0].z, 30, 0.6, 0.6, 0.6, 0.1);
                return true;
            }
            return false;
        };
    }

    /** A rough jaguar of green light: body, head and a trailing tail, drawn along its heading. */
    private static void drawSpirit(ServerLevel level, Vec3 p, Vec3 d, boolean bright) {
        DustParticleOptions c = bright ? JADE : JADE_DIM;
        for (double u = -1.2; u <= 1.2; u += 0.6) {
            Vec3 q = p.add(d.scale(u));
            level.sendParticles(c, q.x, q.y + 1.0, q.z, 2, 0.25, 0.25, 0.25, 0);
        }
        Vec3 h = p.add(d.scale(1.8));
        level.sendParticles(c, h.x, h.y + 1.4, h.z, 3, 0.2, 0.2, 0.2, 0);
        level.sendParticles(GOLD, h.x, h.y + 1.5, h.z, 1, 0.1, 0.05, 0.1, 0);
        Vec3 tail = p.add(d.scale(-2.2));
        level.sendParticles(c, tail.x, tail.y + 1.3, tail.z, 1, 0.3, 0.2, 0.3, 0);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.4, p.z, 1, 0.5, 0.1, 0.5, 0);
    }

    // ------------------------------------------------------------------ hooks

    @Override
    protected void bossTick(ServerLevel level) {
        BossAttack a = currentAttack();
        if (isNoGravity() && (a == null || !a.name.equals("perch"))) {
            setNoGravity(false);   // the perch was interrupted (stagger, phase change): fall back down
        }
        if (tickCount % (phase() == 2 ? 4 : 8) == 0) {
            level.sendParticles(JADE_DIM, getX(), getY() + 2.2, getZ(), 2, 0.8, 0.6, 1.2, 0);
        }
        if (phase() == 2 && tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.GLOW, getX(), getY() + 2.6, getZ(), 1, 0.6, 0.3, 1.0, 0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("jade_jaguar_phase_two"), 0.25,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        setNoGravity(false);
        level.sendParticles(JADE, getX(), getY() + 1.5, getZ(), 120, 3.0, 1.5, 3.0, 0.1);
        level.playSound(null, this, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 2.0F, 1.2F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(JADE, getX(), getY() + 1.5, getZ(), 200, 2.0, 1.5, 2.0, 0.1);
        level.sendParticles(GOLD, getX(), getY() + 1.5, getZ(), 60, 2.0, 1.5, 2.0, 0.1);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
    }
}
