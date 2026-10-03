package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModEntities;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.List;

import static com.wayfarers.generated.MobAnims.BoneMatriarch.BURROW;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.DOUBLE_STING;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.PINCER;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.ROAR;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.SPRAY;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.STAGGER;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.STING;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.SUMMON;
import static com.wayfarers.generated.MobAnims.BoneMatriarch.SWEEP;

/**
 * La Matriarche d'os (The Bone Matriarch): champion at the bottom of the Sand Hypogeum. A giant scorpion-spider
 * queen of sand-bleached bone, crowned with a gold-and-lapis headdress.
 * <ul>
 *     <li>Phase 1: pincer combo (two snaps), tail sting (a long poisoned line), burrow-and-erupt (she sinks out of
 *     sight, a warned eruption bursts under the player and she surfaces there), sand spray (a blinding cone) and a
 *     tail sweep all around her (punishes standing behind).</li>
 *     <li>Phase 2 (below 50%, after a roar that calls two Crypt Crawlers): faster; pincers chain into the sting and the
 *     sting into the pincers, the burrow leaves three eruptions, the spray sweeps side to side; new moves: a
 *     double sting (the second one delayed and aimed) and a brood call of three Crypt Crawlers.</li>
 * </ul>
 */
public class BoneMatriarch extends WayfarerBoss {
    public static final float WIDTH = 3.0F;
    public static final float HEIGHT = 2.2F;

    private boolean burrowed;
    private Vec3 burrowTarget = Vec3.ZERO;

    public BoneMatriarch(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 300.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 11.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BoneMatriarch.TICKS;
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
        return 70.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.8;
    }

    // ------------------------------------------------------------------ private helpers

    private static ParticleOptions sandDust() {
        return new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.SAND.defaultBlockState());
    }

    private static ParticleOptions sandBurst() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.SAND.defaultBlockState());
    }

    private static Vec3 dirFromYaw(float yawDeg) {
        float r = yawDeg * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    private static float yawOf(Vec3 dir) {
        return (float) (Mth.atan2(dir.z, dir.x) * Mth.RAD_TO_DEG) - 90.0F;
    }

    /** Venomous line hit along {@code dir}: damage + Poison II for 5 s. */
    private static void stingLine(WayfarerBoss b, ServerLevel level, Vec3 dir, double length, float damage) {
        for (LivingEntity e : b.victims(level, b.position(), length + 1)) {
            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
            double along = to.dot(dir);
            double side = to.subtract(dir.scale(along)).length();
            if (along >= 0 && along <= length && side <= 1.0 + e.getBbWidth() / 2) {
                b.strike(level, e, damage, 0.8, 0.2);
                e.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 1), b);
            }
        }
        for (int i = 2; i <= (int) length; i++) {
            Vec3 p = b.position().add(dir.scale(i));
            level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y + 1.0, p.z, 2, 0.1, 0.1, 0.1, 0.02);
        }
        level.playSound(null, b, SoundEvents.BEE_STING, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /** Sand cone toward {@code dir}: small damage, Blindness and Slowness. */
    private static void sandCone(WayfarerBoss b, ServerLevel level, Vec3 dir, double range, double halfAngle, float damage) {
        double cos = Math.cos(Math.toRadians(halfAngle));
        for (LivingEntity e : b.victims(level, b.position(), range + 1)) {
            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range && (d < 1.5 || to.normalize().dot(dir) >= cos)) {
                b.strike(level, e, damage, 0.3, 0.05);
                e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 50, 0), b);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 50, 0), b);
            }
        }
        for (int i = 0; i < 6; i++) {
            double dist = 1.5 + b.getRandom().nextDouble() * (range - 1.5);
            double spread = (b.getRandom().nextDouble() - 0.5) * 2 * Math.toRadians(halfAngle);
            Vec3 d2 = new Vec3(dir.x * Math.cos(spread) - dir.z * Math.sin(spread), 0, dir.x * Math.sin(spread) + dir.z * Math.cos(spread));
            Vec3 p = b.position().add(d2.scale(dist));
            level.sendParticles(sandBurst(), p.x, p.y + 1.0, p.z, 4, 0.3, 0.3, 0.3, 0.1);
            level.sendParticles(sandDust(), p.x, p.y + 1.4, p.z, 2, 0.4, 0.2, 0.4, 0.0);
        }
    }

    private static int minionsAround(WayfarerBoss b, ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(b.blockPosition()).inflate(24, 8, 24),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    private void unburrow(ServerLevel level) {
        burrowed = false;
        setInvisible(false);
        level.sendParticles(sandBurst(), getX(), getY() + 0.5, getZ(), 60, 1.5, 0.6, 1.5, 0.2);
        level.playSound(null, this, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (burrowed) {
            return false; // under the sand
        }
        return super.hurtServer(level, source, amount);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // pincer combo: right claw at 0.6 s, left claw at 0.95 s
        out.add(BossAttack.of("pincer").anim(PINCER).timing(12, 8, 12).range(0, 4.8).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.2, 55, ParticleTypes.CRIT);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 4.4, 55, 10.0F, 0.8);
                    level.playSound(null, b, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 1.2F, 0.7F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 7) {
                        b.hitArc(level, 4.6, 55, 10.0F, 1.2);
                        level.playSound(null, b, SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, SoundSource.HOSTILE, 1.2F, 0.6F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "sting");
                    }
                })
                .build());

        // tail sting: 0.9 s coil with a line telegraph, a poisoned strike 6.5 blocks long
        out.add(BossAttack.of("sting").anim(STING).timing(18, 3, 11).range(0, 7.0).cooldown(50).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 1; i <= 6; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> stingLine(b, level, b.forward(), 6.5, 15.0F))
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "pincer");
                    }
                })
                .build());

        // burrow: sinks (0.8 s), invulnerable underground; a warned eruption under the target at 2.0 s, she surfaces there
        out.add(BossAttack.of("burrow").anim(BURROW).timing(16, 32, 12).range(4, 20).cooldown(160).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        level.sendParticles(sandBurst(), b.getX(), b.getY() + 0.3, b.getZ(), 12, 1.4, 0.2, 1.4, 0.15);
                    }
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    BoneMatriarch m = (BoneMatriarch) b;
                    m.burrowed = true;
                    m.setInvisible(true);
                    Vec3 p = t != null ? new Vec3(t.getX(), b.getY(), t.getZ()) : b.ahead(6);
                    m.burrowTarget = p;
                    b.addEffect(WayfarerBoss.eruption(p, 24, 2.6, 16.0F, sandDust(), sandBurst()));
                    if (b.phase() == 2) {
                        for (int i = 0; i < 2; i++) {
                            double a = b.getRandom().nextDouble() * Math.PI * 2;
                            Vec3 q = p.add(Math.cos(a) * 4, 0, Math.sin(a) * 4);
                            b.addEffect(WayfarerBoss.eruption(q, 30 + i * 6, 2.0, 11.0F, sandDust(), sandBurst()));
                        }
                    }
                })
                .active((b, level, t, tick) -> {
                    BoneMatriarch m = (BoneMatriarch) b;
                    if (tick % 4 == 0 && tick < 22) { // a moving mound of sand shows where she goes
                        Vec3 from = b.position();
                        Vec3 p = from.add(m.burrowTarget.subtract(from).scale(tick / 22.0));
                        level.sendParticles(sandBurst(), p.x, p.y + 0.2, p.z, 8, 0.6, 0.1, 0.6, 0.05);
                    }
                    if (tick == 22) {
                        b.teleportTo(m.burrowTarget.x, m.burrowTarget.y, m.burrowTarget.z);
                    }
                    if (tick == 24) {
                        m.unburrow(level);
                        level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .build());

        // sand spray: head thrown back (0.7 s), then a blinding cone of sand for 0.8 s (sweeping in phase 2)
        out.add(BossAttack.of("spray").anim(SPRAY).timing(14, 16, 12).range(0, 8).cooldown(90).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 6.5, 30, sandDust());
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.HUSK_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.4F))
                .active((b, level, t, tick) -> {
                    float yaw = b.getYRot();
                    if (b.phase() == 2) {
                        yaw += (float) Math.sin(tick * Math.PI / 8) * 35.0F;
                    }
                    Vec3 dir = dirFromYaw(yaw);
                    if (tick % 5 == 0) {
                        sandCone(b, level, dir, 7.0, 30, 4.0F);
                        level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.5F, 0.8F);
                    } else {
                        Vec3 p = b.position().add(dir.scale(3));
                        level.sendParticles(sandBurst(), p.x, p.y + 1.0, p.z, 6, 1.0, 0.3, 1.0, 0.1);
                    }
                })
                .build());

        // tail sweep: 0.7 s wind-up with a ring, the tail sweeps all around her (beats players hiding behind)
        out.add(BossAttack.of("tail_sweep").anim(SWEEP).timing(14, 4, 10).range(0, 5.0).cooldown(70).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 4.6, ParticleTypes.CRIT);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.6, 11.0F, 1.5, 0.3);
                    level.sendParticles(sandBurst(), b.getX(), b.getY() + 0.3, b.getZ(), 40, 3.0, 0.2, 3.0, 0.1);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());

        // phase 2: brood call (three Crypt Crawlers, if fewer than five minions are alive)
        out.add(BossAttack.of("summon").anim(SUMMON).phaseTwo().timing(20, 1, 19).range(0, 30).cooldown(450).weight(5)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, sandDust());
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (minionsAround(b, level) < 5) {
                        b.summon(level, ModEntities.CRYPT_CRAWLER.get(), 3, 4.5);
                    }
                    level.playSound(null, b, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.4F);
                    level.sendParticles(sandBurst(), b.getX(), b.getY() + 0.5, b.getZ(), 60, 3.0, 0.4, 3.0, 0.1);
                })
                .build());

        // phase 2: double sting; the first at 0.8 s along her facing, the second (1.5 s) aimed at where the target stands
        out.add(BossAttack.of("double_sting").anim(DOUBLE_STING).phaseTwo().timing(16, 15, 14).range(0, 7.0).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 1; i <= 6; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> stingLine(b, level, b.forward(), 6.5, 13.0F))
                .active((b, level, t, tick) -> {
                    if (t == null) {
                        return;
                    }
                    Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                    Vec3 dir = to.lengthSqr() < 0.01 ? b.forward() : to.normalize();
                    // only within 45 degrees of where she faces: sidestepping far enough still dodges it
                    if (dir.dot(b.forward()) < 0.7) {
                        float f = yawOf(b.forward());
                        float d = Mth.wrapDegrees(yawOf(dir) - f);
                        dir = dirFromYaw(f + Mth.clamp(d, -45.0F, 45.0F));
                    }
                    if (tick >= 6 && tick < 14 && tick % 2 == 0) {
                        for (int i = 1; i <= 6; i++) {
                            Vec3 p = b.position().add(dir.scale(i));
                            level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 14) {
                        stingLine(b, level, dir, 6.5, 13.0F);
                    }
                })
                .build());
    }

    @Override
    protected void bossTick(ServerLevel level) {
        // never stay hidden outside the burrow move (stagger, phase change, reset)
        BossAttack cur = currentAttack();
        if (burrowed && (cur == null || !"burrow".equals(cur.name))) {
            unburrow(level);
        }
        if (!burrowed && tickCount % 8 == 0) {
            level.sendParticles(sandDust(), getX(), getY() + 1.6, getZ(), 2, 1.2, 0.4, 1.2, 0.0);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        if (burrowed) {
            unburrow(level);
        }
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("bone_matriarch_phase_two"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        summon(level, ModEntities.CRYPT_CRAWLER.get(), 2, 4.0);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.sendParticles(sandBurst(), getX(), getY() + 0.5, getZ(), 80, 4.0, 0.5, 4.0, 0.2);
    }
}
