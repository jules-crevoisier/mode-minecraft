package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModBlocks;
import com.wayfarers.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.PowerParticleOption;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.LarvaMother.BIRTH;
import static com.wayfarers.generated.MobAnims.LarvaMother.BITE;
import static com.wayfarers.generated.MobAnims.LarvaMother.BURROW;
import static com.wayfarers.generated.MobAnims.LarvaMother.ROAR;
import static com.wayfarers.generated.MobAnims.LarvaMother.ROLL;
import static com.wayfarers.generated.MobAnims.LarvaMother.SLAM;
import static com.wayfarers.generated.MobAnims.LarvaMother.SPIT;
import static com.wayfarers.generated.MobAnims.LarvaMother.STAGGER;

/**
 * La Mère-Larve (The Larva Mother): champion of the Void Crypt, a bloated void-grub queen with a ring of
 * mandibles and a glowing egg sac.
 * <ul>
 *     <li><b>Phase 1</b> (340 hp): <i>lunge bite</i> (14-tick rear with a portal line, 6-block lunge, 14 dmg),
 *     <i>body slam</i> (18-tick rear, 4.5-block crash 15 dmg + an expanding void ring to jump, 7 dmg),
 *     <i>void acid</i> (16 ticks, a 14-block spit line, 9 dmg, then an acid trail for 4 s: 3 dmg every 0.5 s +
 *     Weakness) and <i>burrow</i> (6 to 26 blocks: she dives, hidden and invulnerable, surfaces under her target:
 *     a 3.5-block portal ring warns for 16 ticks, then 16 dmg and a toss).</li>
 *     <li><b>Phase 2</b> (after a roar, +20% speed, 2 larvae at once): the bite can chain into the slam, the slam
 *     sends a second slower ring, the spit fans into three lines, plus <i>birth</i> (3 void larvae squeezed from the
 *     sac) and <i>rolling charge</i> (16-tick curl, then 24 ticks of rolling, 12 dmg to everything in her path, a
 *     crash shockwave when she hits a wall).</li>
 * </ul>
 */
public class LarvaMother extends WayfarerBoss {
    public static final float WIDTH = 2.8F;
    public static final float HEIGHT = 2.4F;

    /** Dragon-breath motes (a power option in 26.2): the void acid. */
    private static final PowerParticleOption ACID = PowerParticleOption.create(ParticleTypes.DRAGON_BREATH, 1.0F);

    private final Set<UUID> rollHits = new HashSet<>();
    private boolean hidden;
    private boolean crashed;
    private Vec3 eruptAt = Vec3.ZERO;

    public LarvaMother(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 340.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.LarvaMother.TICKS;
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
        return 80.0F;
    }

    @Override
    protected double preferredRange() {
        return 4.0;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (hidden) {
            return false; // underground
        }
        return super.hurtServer(level, source, damage);
    }

    private void setHidden(boolean h) {
        hidden = h;
        setInvisible(h);
    }

    // ------------------------------------------------------------------ private helpers

    private Vec3 dir(float yawOffset) {
        Vec3 f = forward();
        double a = Math.toRadians(yawOffset);
        return new Vec3(f.x * Math.cos(a) - f.z * Math.sin(a), 0, f.x * Math.sin(a) + f.z * Math.cos(a));
    }

    /** Line hit along an arbitrary direction (the engine's hitLine only follows the facing). */
    private void hitAlong(ServerLevel level, Vec3 d, double length, double halfWidth, float damage, double knockback) {
        for (LivingEntity e : victims(level, position(), length + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(d);
            double side = to.subtract(d.scale(along)).length();
            if (along >= 0 && along <= length && side <= halfWidth + e.getBbWidth() / 2) {
                strike(level, e, damage, knockback, 0.2);
            }
        }
    }

    /** A trail of void acid along a line: purple mist for {@code duration} ticks, 3 damage + Weakness every 10 ticks. */
    private static Effect acidTrail(Vec3 from, Vec3 d, double length, int duration) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k % 3 == 0) {
                for (double s = 1.5; s <= length; s += 1.5) {
                    level.sendParticles(ACID, from.x + d.x * s, from.y + 0.15, from.z + d.z * s,
                            2, 0.35, 0.05, 0.35, 0.005);
                }
            }
            if (k % 10 == 0) {
                for (LivingEntity e : boss.victims(level, from.add(d.scale(length / 2)), length / 2 + 1.5)) {
                    Vec3 to = e.position().subtract(from).multiply(1, 0, 1);
                    double along = to.dot(d);
                    double side = to.subtract(d.scale(along)).length();
                    if (along >= 0 && along <= length && side <= 1.3 && Math.abs(e.getY() - from.y) < 1.5) {
                        e.hurtServer(level, boss.damageSources().magic(), 3.0F);
                        e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 0), boss);
                    }
                }
            }
            return k >= duration;
        };
    }

    private void spitLine(ServerLevel level, float yawOffset) {
        Vec3 d = dir(yawOffset);
        hitAlong(level, d, 14.0, 1.2, 9.0F, 0.4);
        Vec3 mouth = position().add(0, 2.0, 0);
        for (double s = 1; s <= 14; s += 1) {
            level.sendParticles(ACID, mouth.x + d.x * s, mouth.y - s * 0.12, mouth.z + d.z * s,
                    3, 0.15, 0.15, 0.15, 0.01);
        }
        addEffect(acidTrail(position(), d, 14.0, 80));
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        out.add(BossAttack.of("bite").anim(BITE).timing(14, 3, 11).range(0, 6.0).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 1; i <= 6; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.9, 0.05);
                    b.hitLine(level, 6.0, 1.5, 14.0F, 1.0);
                    level.playSound(null, b, SoundEvents.EVOKER_FANGS_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.PHANTOM_BITE, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "slam");
                    }
                })
                .build());
        out.add(BossAttack.of("slam").anim(SLAM).timing(18, 2, 16).range(0, 7.0).cooldown(80).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(2.5), 4.5, ParticleTypes.REVERSE_PORTAL);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(2.5);
                    b.hitCircle(level, c, 4.5, 15.0F, 1.0, 0.5);
                    b.addEffect(WayfarerBoss.wave(c, 10, 0.45, 7.0F, ParticleTypes.REVERSE_PORTAL));
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 3, 1.2, 0.2, 1.2, 0);
                    level.sendParticles(ParticleTypes.PORTAL, c.x, c.y + 0.5, c.z, 60, 2.0, 0.5, 2.0, 0.5);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.4F);
                    level.playSound(null, b, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 3.0F, 0.4F);
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 1) {
                        b.addEffect(WayfarerBoss.wave(b.ahead(2.5), 14, 0.3, 7.0F, ACID));
                    }
                })
                .build());
        out.add(BossAttack.of("spit").anim(SPIT).timing(16, 2, 14).range(4, 18).cooldown(90).weight(8)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 1.2F, 1.8F))
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        LarvaMother lm = (LarvaMother) b;
                        float[] fan = b.phase() == 2 ? new float[]{-25, 0, 25} : new float[]{0};
                        for (float off : fan) {
                            Vec3 d = lm.dir(off);
                            for (int i = 2; i <= 14; i += 2) {
                                level.sendParticles(ACID, b.getX() + d.x * i, b.getY() + 0.15,
                                        b.getZ() + d.z * i, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    LarvaMother lm = (LarvaMother) b;
                    lm.spitLine(level, 0);
                    if (b.phase() == 2) {
                        lm.spitLine(level, -25);
                        lm.spitLine(level, 25);
                    }
                    level.playSound(null, b, SoundEvents.ENDER_DRAGON_SHOOT, SoundSource.HOSTILE, 2.0F, 0.7F);
                })
                .build());
        out.add(BossAttack.of("burrow").anim(BURROW).timing(32, 2, 14).range(6, 26).cooldown(160).weight(7)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.WARDEN_DIG, SoundSource.HOSTILE, 2.5F, 0.7F))
                .windup((b, level, t, tick) -> {
                    LarvaMother lm = (LarvaMother) b;
                    if (tick < 15) {
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 0.2, b.getZ(), 12, 1.4, 0.1, 1.4, 0.05);
                        level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 0.2, b.getZ(), 3, 1.2, 0.1, 1.2, 0.01);
                    } else if (tick == 15) {
                        lm.setHidden(true);
                        lm.eruptAt = t != null ? t.position() : b.position();
                        b.teleportTo(lm.eruptAt.x, lm.eruptAt.y, lm.eruptAt.z);
                        level.playSound(null, b, SoundEvents.WARDEN_DIG, SoundSource.HOSTILE, 2.0F, 0.5F);
                    } else if (tick % 2 == 0) {
                        b.telegraphRing(level, lm.eruptAt, 3.5, ParticleTypes.REVERSE_PORTAL);
                        level.sendParticles(ParticleTypes.PORTAL, lm.eruptAt.x, lm.eruptAt.y + 0.2, lm.eruptAt.z,
                                8, 1.5, 0.1, 1.5, 0.3);
                    }
                })
                .impact((b, level, t, tick) -> {
                    LarvaMother lm = (LarvaMother) b;
                    lm.setHidden(false);
                    b.hitCircle(level, b.position(), 3.5, 16.0F, 0.6, 1.0);
                    level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 0.5, b.getZ(), 4, 1.5, 0.3, 1.5, 0);
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 1, b.getZ(), 80, 1.5, 1.5, 1.5, 0.2);
                    level.playSound(null, b, SoundEvents.WARDEN_EMERGE, SoundSource.HOSTILE, 2.0F, 1.2F);
                })
                .build());
        out.add(BossAttack.of("birth").anim(BIRTH).phaseTwo().timing(16, 1, 19).range(0, 30).cooldown(400).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        Vec3 back = b.ahead(-3.5);
                        level.sendParticles(ParticleTypes.PORTAL, back.x, back.y + 1.5, back.z, 10, 1.2, 1.0, 1.2, 0.2);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.summon(level, ModEntities.VOID_LARVA.get(), 3, 3.0);
                    level.playSound(null, b, SoundEvents.SNIFFER_EGG_CRACK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        out.add(BossAttack.of("roll").anim(ROLL).phaseTwo().timing(16, 24, 12).range(4, 22).cooldown(130).weight(8)
                .start((b, level, t, tick) -> {
                    LarvaMother lm = (LarvaMother) b;
                    lm.rollHits.clear();
                    lm.crashed = false;
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 16; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 0.15, p.z, 2, 0.8, 0, 0.8, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F))
                .active((b, level, t, tick) -> {
                    LarvaMother lm = (LarvaMother) b;
                    if (lm.crashed) {
                        return;
                    }
                    if (tick > 3 && b.horizontalCollision) { // smashed into a wall: a shockwave, then she stops
                        lm.crashed = true;
                        b.setDeltaMovement(0, 0, 0);
                        b.hitCircle(level, b.position(), 4.0, 10.0F, 1.2, 0.5);
                        level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 1, b.getZ(), 3, 1.0, 0.5, 1.0, 0);
                        level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
                        return;
                    }
                    b.lunge(0.8, b.getDeltaMovement().y);
                    for (LivingEntity e : b.victims(level, b.position(), 2.8)) {
                        if (lm.rollHits.add(e.getUUID())) {
                            b.strike(level, e, 12.0F, 1.5, 0.5);
                        }
                    }
                    if (tick % 2 == 0) {
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 0.3, b.getZ(), 10, 1.2, 0.2, 1.2, 0.05);
                        level.playSound(null, b, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 0.8F, 0.5F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ ambience, phases

    @Override
    protected void bossTick(ServerLevel level) {
        if (hidden && currentAttack() == null) {
            setHidden(false); // interrupted (arena reset): never stay underground
        }
        if (!hidden && tickCount % 6 == 0) {
            Vec3 back = position().add(forward().scale(-3.0));
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, back.x, getY() + 1.6, back.z, 2, 1.0, 0.8, 1.0, 0.01);
            level.sendParticles(ACID, getX(), getY() + 1.8, getZ(), 1, 0.4, 0.2, 0.4, 0.005);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("phase_two_speed"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        summon(level, ModEntities.VOID_LARVA.get(), 2, 3.0);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 2.5F, 0.5F);
        level.sendParticles(ParticleTypes.PORTAL, getX(), getY() + 1.5, getZ(), 120, 2.0, 1.0, 2.0, 0.8);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 1, getZ(), 150, 2.0, 1.0, 2.0, 0.3);
        level.playSound(null, this, SoundEvents.SLIME_DEATH, SoundSource.HOSTILE, 3.0F, 0.4F);
    }
}
