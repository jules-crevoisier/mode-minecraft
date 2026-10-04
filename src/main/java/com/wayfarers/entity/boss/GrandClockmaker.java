package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.entity.automaton.ClockworkSpider;
import com.wayfarers.entity.automaton.HotRivetEntity;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModEntities;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.List;

import static com.wayfarers.generated.MobAnims.GrandClockmaker.BLINK;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.CHIME;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.GEARS;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.ROAR;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.SLAM;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.STAGGER;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.SUMMON;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.SWEEP;
import static com.wayfarers.generated.MobAnims.GrandClockmaker.TIMESTOP;

/**
 * Le Grand Horloger (The Grand Clockmaker), champion of the Clockwork Citadel: a tall clockwork gentleman whose
 * chest is a clock face, with gear wings and a pendulum cane. His arena is the Clock Vault under the clock tower.
 * <ul>
 *     <li>Phase 1: <b>pendulum sweep</b> (a 220 degree swing of the cane, 15), <b>cane slam</b> (18 in front and a
 *     ring of sparks rolling out: jump it), <b>cog fan</b> (3 spinning brass cogs thrown at range, 7 each),
 *     <b>wind-up</b> (two Clockwork Spiders join the fight, never more than four at once) and <b>time stop</b>: the
 *     hands rewind for 1.2 s while a ring closes around him; whoever is still inside the 9-block ring when it
 *     chimes is frozen (Slowness IV and Mining Fatigue for 2 s). Get out of the ring.</li>
 *     <li>Phase 2 (after a roar at half health): faster, sparks crackle on him, combos (sweep into slam, slam into
 *     cogs), five cogs per fan, a <b>time skip</b> (he vanishes and reappears behind his prey, then sweeps) and the
 *     <b>midnight chime</b>: twelve bells toll one after another around him, each a burst where a warning glints,
 *     and a thirteenth under every player.</li>
 * </ul>
 */
public class GrandClockmaker extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 4.4F;
    private static final double TIMESTOP_RADIUS = 9.0;

    private int tock;

    public GrandClockmaker(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.GrandClockmaker.TICKS;
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
        return 75.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // pendulum sweep: the cane is lifted out to the right and behind, then swings across 220 degrees
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(18, 3, 13).range(0, 6.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.2, 110, ParticleTypes.ELECTRIC_SPARK);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.5, 110, 15.0F, 1.6);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.2F, 1.4F);
                    for (int a = -110; a <= 110; a += 20) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(4.8));
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 1.0, p.z, 3, 0.2, 0.2, 0.2, 0.05);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "slam");
                    }
                })
                .build());
        // cane slam: overhead, the pendulum bob crashes down in front, a ring of sparks rolls out (jump it)
        out.add(BossAttack.of("slam").anim(SLAM).timing(20, 3, 13).range(0, 7.0).cooldown(80).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 3.0, ParticleTypes.ELECTRIC_SPARK);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.5);
                    b.hitCircle(level, c, 3.0, 18.0F, 1.0, 0.5);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 12 : 9, 0.5, 8.0F, ParticleTypes.ELECTRIC_SPARK));
                    if (b.phase() == 2) {
                        b.addEffect(delayed(12, WayfarerBoss.wave(c, 12, 0.4, 7.0F, ParticleTypes.WAX_OFF)));
                    }
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 2, 0.6, 0.1, 0.6, 0);
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y + 0.3, c.z, 40, 1.2, 0.3, 1.2, 0.3);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.7F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.9F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "gears");
                    }
                })
                .build());
        // cog fan: the left hand flings spinning brass cogs at the target
        out.add(BossAttack.of("gears").anim(GEARS).timing(12, 4, 10).range(4.0, 24.0).cooldown(70).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        Vec3 p = b.position().add(0, 3.0, 0);
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 2, 0.4, 0.3, 0.4, 0.05);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 1.5F, 1.0F);
                    }
                })
                .impact((b, level, t, tick) -> cogFan(level, t, b.phase() == 2 ? 5 : 3))
                .build());
        // wind-up: clockwork spiders join the fight (never more than four at once)
        out.add(BossAttack.of("summon").anim(SUMMON).timing(16, 2, 14).range(0, 30.0).cooldown(420).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 1.5F, 1.2F + tick * 0.03F);
                    }
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, b.getX(), b.getY() + 3.2, b.getZ(), 2, 0.5, 0.4, 0.5, 0.05);
                })
                .impact((b, level, t, tick) -> {
                    int alive = level.getEntitiesOfClass(ClockworkSpider.class, new AABB(b.blockPosition()).inflate(32),
                            e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
                    int count = Math.min(b.phase() == 2 ? 3 : 2, 4 - alive);
                    if (count > 0) {
                        b.summon(level, ModEntities.CLOCKWORK_SPIDER.get(), count, 2.5);
                    }
                    level.playSound(null, b, SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 1.5F, 0.8F);
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 1.0F, 1.8F);
                })
                .build());
        // time stop: the hands rewind while a ring closes around him; whoever is still inside when it chimes freezes
        out.add(BossAttack.of("timestop").anim(TIMESTOP).timing(24, 4, 12).range(0, 14.0).cooldown(320).weight(7).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), TIMESTOP_RADIUS, ParticleTypes.END_ROD);
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 2.0F, tick % 8 == 0 ? 0.8F : 1.0F);
                    }
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 2.6, b.getZ(), 4, 0.6, 0.6, 0.6, 0.05);
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.5F, 0.7F);
                    level.playSound(null, b, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    for (LivingEntity e : b.victims(level, b.position(), TIMESTOP_RADIUS)) {
                        if (e.position().multiply(1, 0, 1).distanceTo(b.position().multiply(1, 0, 1)) > TIMESTOP_RADIUS) {
                            continue;
                        }
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 3), b);
                        e.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 40, 2), b);
                        e.setDeltaMovement(0, Math.min(0, e.getDeltaMovement().y), 0);
                        e.hurtMarked = true;
                        level.sendParticles(ParticleTypes.END_ROD, e.getX(), e.getY() + 1.0, e.getZ(), 12, 0.4, 0.6, 0.4, 0.01);
                    }
                    for (int i = 0; i < 48; i++) {
                        double a = Math.PI * 2 * i / 48;
                        level.sendParticles(ParticleTypes.WAX_OFF, b.getX() + Math.cos(a) * TIMESTOP_RADIUS, b.getY() + 0.5,
                                b.getZ() + Math.sin(a) * TIMESTOP_RADIUS, 1, 0, 0.3, 0, 0);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // time skip: a crouch, a crackle, and he steps out of time behind his prey, then sweeps
        out.add(BossAttack.of("blink").anim(BLINK).phaseTwo().timing(10, 2, 6).range(6.0, 26.0).cooldown(140).weight(8)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 1.5, b.getZ(), 8, 0.6, 1.2, 0.6, 0.05);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 1.5F, 1.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (t != null && b instanceof GrandClockmaker g) {
                        g.skipBehind(level, t);
                    }
                })
                .end((b, level, t, tick) -> b.chain(level, "sweep"))
                .build());
        // midnight chime: twelve bells toll around him, one after another, then one under every player
        out.add(BossAttack.of("chime").anim(CHIME).phaseTwo().timing(20, 24, 12).range(0, 20.0).cooldown(260).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 6.0, ParticleTypes.WAX_ON);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 1.2F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.position();
                    float yaw = b.getYRot();
                    for (int h = 0; h < 12; h++) {
                        double a = Math.toRadians(yaw + 90 + h * 30);
                        Vec3 p = c.add(Math.cos(a) * 6.0, 0, Math.sin(a) * 6.0);
                        b.addEffect(toll(p, 8 + h * 3, 2.0, 11.0F, 0.5F + h * 0.07F));
                    }
                    for (LivingEntity e : b.victims(level, c, 22.0)) {
                        b.addEffect(toll(e.position(), 46, 1.8, 12.0F, 0.5F));
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.0F, 0.8F);
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    /** Steps out of time and reappears 2.5 blocks behind the target, facing it (stays put if there is no room). */
    private void skipBehind(ServerLevel level, LivingEntity target) {
        Vec3 look = target.getLookAngle().multiply(1, 0, 1);
        if (look.lengthSqr() < 1.0E-4) {
            look = target.position().subtract(position()).multiply(1, 0, 1);
        }
        look = look.normalize();
        Vec3 from = position();
        for (double side : new double[]{0, 60, -60, 180}) {
            Vec3 dir = rotate(look, side).scale(-2.5);
            Vec3 to = target.position().add(dir);
            if (randomTeleport(to.x, target.getY(), to.z, false)) {
                // the move's locked facing too, or the active frames would turn him back to where he stood before
                snapFacing((float) (Mth.atan2(target.getZ() - getZ(), target.getX() - getX()) * Mth.RAD_TO_DEG) - 90.0F);
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, from.x, from.y + 2, from.z, 40, 0.5, 1.5, 0.5, 0.1);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 30, 0.5, 1.5, 0.5, 0.2);
                level.playSound(null, from.x, from.y, from.z, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.6F);
                level.playSound(null, this, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                return;
            }
        }
    }

    /** A fan of spinning brass cogs from the left hand toward the target. */
    private void cogFan(ServerLevel level, LivingEntity target, int count) {
        Vec3 from = position().add(0, 2.9, 0).add(forward().scale(0.8));
        Vec3 aim = target != null
                ? target.position().add(0, target.getBbHeight() * 0.5, 0).subtract(from).normalize()
                : forward();
        for (int i = 0; i < count; i++) {
            double a = (i - (count - 1) / 2.0) * 11.0;
            Vec3 dir = rotate(aim, a);
            dir = new Vec3(dir.x, aim.y, dir.z).normalize();
            HotRivetEntity cog = new HotRivetEntity(level, this, true, 7.0F);
            cog.setPos(from.x, from.y, from.z);
            cog.shoot(dir.x, dir.y, dir.z, 1.1F, 1.0F);
            level.addFreshEntity(cog);
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, from.x, from.y, from.z, 20, 0.4, 0.4, 0.4, 0.2);
        level.playSound(null, this, SoundEvents.DISPENSER_LAUNCH, SoundSource.HOSTILE, 1.5F, 0.7F);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.0F, 1.4F);
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

    /**
     * One hour of the midnight chime: a glint of wax-on sparks marks the spot for {@code delay} ticks, then a bell
     * tolls and a burst of sparks throws up whoever stands there.
     */
    private static Effect toll(Vec3 pos, int delay, double radius, float damage, float pitch) {
        int[] t = {0};
        ParticleOptions warn = ParticleTypes.WAX_ON;
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, warn);
                }
                return false;
            }
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, pos.x, pos.y + 0.5, pos.z, 30, radius * 0.4, 1.0, radius * 0.4, 0.2);
            level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.5, pos.z, 8, radius * 0.3, 1.2, radius * 0.3, 0.05);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 2.0F, pitch);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                    boss.strike(level, e, damage, 0.3, 0.8);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ ambience, phase 2

    @Override
    protected void bossTick(ServerLevel level) {
        int period = phase() == 2 ? 10 : 20;
        if (tickCount % period == 0) { // tick... tock...
            tock ^= 1;
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.HOSTILE, 1.2F, tock == 0 ? 0.7F : 0.55F);
        }
        if (tickCount % 6 == 0) {   // steam from the exhaust on his back
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            level.sendParticles(ParticleTypes.WHITE_SMOKE, getX() + Mth.sin(yaw) * 0.3, getY() + 4.1, getZ() - Mth.cos(yaw) * 0.3,
                    1, 0.05, 0.05, 0.05, 0.01);
        }
        if (phase() == 2 && tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 2, 0.6, 1.2, 0.6, 0.05);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("grand_clockmaker_overwound"), 0.15,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.5, getZ(), 80, 1.2, 2.0, 1.2, 0.3);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2, getZ(), 4, 0.8, 1.2, 0.8, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2, getZ(), 120, 1.0, 2.0, 1.0, 0.4);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 2, getZ(), 40, 0.8, 1.5, 0.8, 0.05);
        for (int i = 0; i < 3; i++) {
            level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 3.0F, 0.5F + i * 0.2F);
        }
        // his clockwork spiders wind down with him
        for (ClockworkSpider s : level.getEntitiesOfClass(ClockworkSpider.class, new AABB(blockPosition()).inflate(40),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG))) {
            s.kill(level);
        }
    }
}
