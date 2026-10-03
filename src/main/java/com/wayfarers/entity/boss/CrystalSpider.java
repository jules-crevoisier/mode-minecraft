package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static com.wayfarers.generated.MobAnims.CrystalSpider.BROOD;
import static com.wayfarers.generated.MobAnims.CrystalSpider.POUNCE;
import static com.wayfarers.generated.MobAnims.CrystalSpider.ROAR;
import static com.wayfarers.generated.MobAnims.CrystalSpider.SHARDS;
import static com.wayfarers.generated.MobAnims.CrystalSpider.SKITTER;
import static com.wayfarers.generated.MobAnims.CrystalSpider.SPIKES;
import static com.wayfarers.generated.MobAnims.CrystalSpider.STAB;
import static com.wayfarers.generated.MobAnims.CrystalSpider.STAGGER;
import static com.wayfarers.generated.MobAnims.CrystalSpider.STORM;
import static com.wayfarers.generated.MobAnims.CrystalSpider.WEB;

/**
 * La Matriarche de cristal (The Crystal Matriarch), boss of the Crystal Grotto: an enormous spider whose carapace
 * has grown into amethyst and lithite.
 * <ul>
 *     <li>Phase 1: rearing leg stab, a crouching pounce from mid range, a web shot that slows (and briefly pins with
 *     a cobweb, always cleared again), lines of crystal spikes erupting toward the target, a fan of crystal shards
 *     fired from her abdomen.</li>
 *     <li>Phase 2 (after a roar): faster; stabs chain into spike lines; a crystal storm (shards fall all over the
 *     nest for three seconds, each spot marked first), a brood of cave spiders, and a skittering side-dash that
 *     ends in a lunge.</li>
 * </ul>
 */
public class CrystalSpider extends WayfarerBoss {
    public static final float WIDTH = 3.2F;
    public static final float HEIGHT = 2.4F;
    private static final int WEB_TICKS = 50;

    private static final ParticleOptions AMETHYST = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState());
    private static final ParticleOptions CLUSTER = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_CLUSTER.defaultBlockState());

    /** Temporary cobwebs placed by web shots, with the tick they disappear. */
    private final Map<BlockPos, Integer> webs = new HashMap<>();
    private boolean landed;

    public CrystalSpider(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 440.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.CrystalSpider.TICKS;
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
        return 70.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.0;
    }

    /** Spiders walk through their own webs. */
    @Override
    public void makeStuckInBlock(BlockState state, Vec3 speedMultiplier) {
        if (!state.is(Blocks.COBWEB)) {
            super.makeStuckInBlock(state, speedMultiplier);
        }
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // leg stab: rears up on her hind legs, both front legs raised (0.65 s), then stabbed down
        out.add(BossAttack.of("stab").anim(STAB).timing(13, 3, 10).range(0, 5.0).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 4.5, 35, ParticleTypes.WITCH);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 4.8, 40, 13.0F, 0.8);
                    Vec3 p = b.ahead(3.5);
                    level.sendParticles(AMETHYST, p.x, p.y + 0.2, p.z, 20, 0.8, 0.1, 0.8, 0.1);
                    level.playSound(null, b, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.SPIDER_HURT, SoundSource.HOSTILE, 1.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "spikes");
                    }
                })
                .build());
        // pounce: crouches low (ring on the target), springs, lands with a crash of crystal
        out.add(BossAttack.of("pounce").anim(POUNCE).timing(14, 12, 12).range(5.0, 16.0).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 2.8, ParticleTypes.WITCH);
                    }
                })
                .impact((b, level, t, tick) -> {
                    landed = false;
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(2.2, dist * 0.17), 0.55);
                    level.playSound(null, b, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .active((b, level, t, tick) -> {
                    if (landed || !(tick == 11 || (tick >= 5 && b.onGround()))) {
                        return;
                    }
                    landed = true;
                    b.hitCircle(level, b.position(), 2.8, 15.0F, 1.2, 0.5);
                    level.sendParticles(AMETHYST, b.getX(), b.getY() + 0.2, b.getZ(), 40, 1.6, 0.1, 1.6, 0.15);
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());
        // web shot: the abdomen arches over her back and sprays a web ball (slows, pins for a moment)
        out.add(BossAttack.of("web").anim(WEB).timing(12, 4, 12).range(4.0, 20.0).cooldown(110).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        level.sendParticles(ParticleTypes.ITEM_COBWEB, b.getX(), b.getY() + 2.6, b.getZ(), 3, 0.4, 0.3, 0.4, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 from = b.position().add(0, 2.4, 0);
                    Vec3 to = t != null ? t.position().add(0, 0.8, 0) : b.ahead(12).add(0, 0.8, 0);
                    b.addEffect(webShot(from, to.subtract(from).normalize(), 0.9));
                    if (b.phase() == 2 && t != null) { // two more, to either side
                        Vec3 d = to.subtract(from).normalize();
                        b.addEffect(webShot(from, rotate(d, 18), 0.9));
                        b.addEffect(webShot(from, rotate(d, -18), 0.9));
                    }
                    level.playSound(null, b, SoundEvents.LLAMA_SPIT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.COBWEB_PLACE, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());
        // crystal spikes: drives her front legs into the floor; three lines of spikes race toward the target
        out.add(BossAttack.of("spikes").anim(SPIKES).timing(16, 8, 8).range(0, 18.0).cooldown(100).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int a = -20; a <= 20; a += 20) {
                            for (int i = 2; i <= 4; i++) {
                                Vec3 p = b.position().add(rotate(b.forward(), a).scale(i * 1.5));
                                level.sendParticles(ParticleTypes.GLOW, p.x, p.y + 0.1, p.z, 1, 0.2, 0, 0.2, 0);
                            }
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    int lines = b.phase() == 2 ? 5 : 3;
                    for (int l = 0; l < lines; l++) {
                        double a = (l - (lines - 1) / 2.0) * 20;
                        Vec3 dir = rotate(b.forward(), a);
                        for (int i = 1; i <= 9; i++) {
                            b.addEffect(crystalSpike(b.position().add(dir.scale(1.2 + i * 1.5)), 8 + i * 2, 1.1, 12.0F));
                        }
                    }
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.sendParticles(AMETHYST, b.ahead(2).x, b.getY() + 0.2, b.ahead(2).z, 30, 1.0, 0.1, 1.0, 0.15);
                })
                .build());
        // shard volley: the abdomen lifts and shudders, then looses a fan of crystal shards
        out.add(BossAttack.of("shards").anim(SHARDS).timing(14, 6, 10).range(3.0, 24.0).cooldown(80).weight(9)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.GLOW, b.getX(), b.getY() + 2.6, b.getZ(), 2, 0.8, 0.5, 0.8, 0.02);
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> shardFan(level, t, b.phase() == 2 ? 8 : 5))
                .active((b, level, t, tick) -> {
                    if (tick == 4 && b.phase() == 2) {
                        shardFan(level, t, 5);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // crystal storm: rears and screeches; for three seconds shards rain on the nest, every spot marked first
        out.add(BossAttack.of("storm").anim(STORM).phaseTwo().timing(18, 12, 10).range(0, 30.0).cooldown(260).weight(7)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 3.0, b.getZ(), 3, 1.0, 0.8, 1.0, 0.05);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.SPIDER_DEATH, SoundSource.HOSTILE, 2.5F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 4.0F, 0.4F);
                    for (int i = 0; i < 26; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 2.5 + b.getRandom().nextDouble() * 11;
                        Vec3 p = b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r);
                        b.addEffect(fallingShard(p, 24 + b.getRandom().nextInt(50), 1.6, 12.0F));
                    }
                    for (LivingEntity e : b.victims(level, b.position(), 26.0)) {
                        for (int k = 0; k < 3; k++) {
                            b.addEffect(fallingShard(e.position(), 24 + k * 20, 1.6, 12.0F));
                        }
                    }
                })
                .build());
        // brood: the abdomen pulses and cave spiders pour out
        out.add(BossAttack.of("brood").anim(BROOD).phaseTwo().timing(12, 2, 14).range(0, 30.0).cooldown(420).weight(5)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.SPIDER_STEP, SoundSource.HOSTILE, 1.5F, 1.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.summon(level, EntityTypes.CAVE_SPIDER, 3, 2.5);
                    level.sendParticles(ParticleTypes.ITEM_COBWEB, b.getX(), b.getY() + 1.2, b.getZ(), 30, 1.5, 0.5, 1.5, 0.05);
                    level.playSound(null, b, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 2.0F, 1.3F);
                })
                .build());
        // skitter: drops low, darts sideways, then lunges in at the target and lashes all around
        out.add(BossAttack.of("skitter").anim(SKITTER).phaseTwo().timing(10, 10, 10).range(3.0, 14.0).cooldown(100).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 2.6, ParticleTypes.WITCH);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 side = rotate(b.forward(), b.getRandom().nextBoolean() ? 90 : -90).scale(1.3);
                    b.setDeltaMovement(side.x, 0.1, side.z);
                    b.hurtMarked = true;
                    level.playSound(null, b, SoundEvents.SPIDER_STEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .active((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.WITCH, b.getX(), b.getY() + 0.3, b.getZ(), 3, 0.8, 0.1, 0.8, 0.02);
                    if (tick == 5 && t != null) {
                        Vec3 d = t.position().subtract(b.position()).multiply(1, 0, 1);
                        Vec3 v = d.normalize().scale(Math.min(1.6, d.length() * 0.22));
                        b.setDeltaMovement(v.x, 0.2, v.z);
                        b.hurtMarked = true;
                    }
                    if (tick == 9) {
                        b.hitCircle(level, b.position(), 2.8, 12.0F, 1.0, 0.3);
                        level.sendParticles(AMETHYST, b.getX(), b.getY() + 0.3, b.getZ(), 25, 1.5, 0.2, 1.5, 0.1);
                        level.playSound(null, b, SoundEvents.SPIDER_HURT, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void shardFan(ServerLevel level, LivingEntity target, int count) {
        Vec3 from = position().add(forward().scale(-0.5)).add(0, 2.6, 0);
        Vec3 aim = target != null
                ? target.position().add(0, target.getBbHeight() * 0.5, 0).subtract(from).normalize()
                : forward();
        for (int i = 0; i < count; i++) {
            double a = (i - (count - 1) / 2.0) * 8.0;
            Vec3 flat = rotate(new Vec3(aim.x, 0, aim.z), a);
            double horiz = Math.sqrt(aim.x * aim.x + aim.z * aim.z);
            Vec3 dir = new Vec3(flat.x * horiz, aim.y, flat.z * horiz).normalize();
            addEffect(shard(from, dir, 1.1, 8.0F));
        }
        level.sendParticles(AMETHYST, from.x, from.y, from.z, 25, 0.8, 0.5, 0.8, 0.2);
        level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        return new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c).normalize();
    }

    private static boolean solid(ServerLevel level, Vec3 p) {
        return level.getBlockState(BlockPos.containing(p)).blocksMotion();
    }

    /** A flying crystal shard: a straight, visible bolt that hurts the first victim it touches. */
    private static Effect shard(Vec3 start, Vec3 dir, double speed, float damage) {
        Vec3[] pos = {start};
        int[] age = {0};
        return (boss, level) -> {
            for (int step = 0; step < 2; step++) {
                Vec3 p = pos[0] = pos[0].add(dir.scale(speed / 2));
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0, 0, 0, 0);
                level.sendParticles(AMETHYST, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
                for (LivingEntity e : boss.victims(level, p, 1.2)) {
                    if (e.getBoundingBox().inflate(0.3).contains(p)) {
                        boss.strike(level, e, damage, 0.4, 0.1);
                        level.playSound(null, p.x, p.y, p.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 1.0F, 1.2F);
                        return true;
                    }
                }
                if (solid(level, p)) {
                    level.sendParticles(CLUSTER, p.x, p.y, p.z, 8, 0.2, 0.2, 0.2, 0.05);
                    return true;
                }
            }
            return ++age[0] > 30;
        };
    }

    /** A web ball: slows whoever it hits and briefly pins them with a cobweb that the boss clears again. */
    private Effect webShot(Vec3 start, Vec3 dir, double speed) {
        Vec3[] pos = {start};
        int[] age = {0};
        return (boss, level) -> {
            Vec3 p = pos[0] = pos[0].add(dir.scale(speed));
            level.sendParticles(ParticleTypes.ITEM_COBWEB, p.x, p.y, p.z, 4, 0.15, 0.15, 0.15, 0.01);
            level.sendParticles(ParticleTypes.WHITE_ASH, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0);
            for (LivingEntity e : boss.victims(level, p, 1.4)) {
                if (e.getBoundingBox().inflate(0.5).contains(p)) {
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
                    e.hurtServer(level, boss.damageSources().mobAttack(boss), 4.0F);
                    BlockPos at = e.blockPosition();
                    if (level.getBlockState(at).isAir()) {
                        level.setBlock(at, Blocks.COBWEB.defaultBlockState(), 3);
                        webs.put(at.immutable(), tickCount + WEB_TICKS);
                    }
                    level.sendParticles(ParticleTypes.ITEM_COBWEB, e.getX(), e.getY() + 1, e.getZ(), 30, 0.5, 0.6, 0.5, 0.05);
                    level.playSound(null, e, SoundEvents.COBWEB_PLACE, SoundSource.HOSTILE, 1.5F, 0.7F);
                    return true;
                }
            }
            return solid(level, p) || ++age[0] > 25;
        };
    }

    /** A crystal spike bursting from the floor after {@code delay} ticks of glowing warning. */
    private static Effect crystalSpike(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 3 == 0) {
                    level.sendParticles(ParticleTypes.GLOW, pos.x, pos.y + 0.1, pos.z, 3, radius * 0.4, 0.02, radius * 0.4, 0);
                }
                return false;
            }
            level.sendParticles(CLUSTER, pos.x, pos.y + 0.6, pos.z, 18, radius * 0.3, 0.6, radius * 0.3, 0.15);
            level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.8, pos.z, 6, 0.15, 0.8, 0.15, 0.04);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 1.0F, 0.7F);
            for (LivingEntity e : boss.victims(level, pos, radius + 0.5)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius + e.getBbWidth() / 2) {
                    boss.strike(level, e, damage, 0.2, 0.7);
                }
            }
            return true;
        };
    }

    /** A shard falling from the geode roof: a ring and a descending glimmer mark the spot, then it shatters. */
    private static Effect fallingShard(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 4 == 0) {
                    boss.telegraphRing(level, pos, radius, ParticleTypes.WITCH);
                }
                if (delay - k <= 12) {
                    double h = 10.0 * (delay - k) / 12.0;
                    level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + h, pos.z, 2, 0.1, 0.2, 0.1, 0);
                    level.sendParticles(AMETHYST, pos.x, pos.y + h, pos.z, 2, 0.15, 0.2, 0.15, 0);
                }
                return false;
            }
            level.sendParticles(CLUSTER, pos.x, pos.y + 0.4, pos.z, 26, radius * 0.4, 0.4, radius * 0.4, 0.2);
            level.sendParticles(ParticleTypes.GLOW, pos.x, pos.y + 0.4, pos.z, 10, radius * 0.4, 0.3, radius * 0.4, 0.05);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
            for (LivingEntity e : boss.victims(level, pos, radius + 0.5)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius + e.getBbWidth() / 2) {
                    boss.strike(level, e, damage, 0.2, 0.3);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ webs, ambience

    private void clearWebs(ServerLevel level, boolean all) {
        webs.entrySet().removeIf(en -> {
            if (all || tickCount >= en.getValue()) {
                if (level.getBlockState(en.getKey()).is(Blocks.COBWEB)) {
                    level.removeBlock(en.getKey(), false);
                    level.sendParticles(ParticleTypes.ITEM_COBWEB, en.getKey().getX() + 0.5, en.getKey().getY() + 0.5,
                            en.getKey().getZ() + 0.5, 6, 0.3, 0.3, 0.3, 0.02);
                }
                return true;
            }
            return false;
        });
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (!webs.isEmpty()) {
            clearWebs(level, false);
        }
        if (tickCount % 6 == 0) { // crystals glimmer on her back
            level.sendParticles(ParticleTypes.GLOW, getX(), getY() + 2.4, getZ(), 1, 0.7, 0.5, 0.9, 0.0);
        }
        if (phase() == 2 && tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2.2, getZ(), 1, 0.9, 0.6, 1.1, 0.01);
        }
        if (tickCount % 90 == 0) {
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.5F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("crystal_spider_frenzy"), 0.25,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(CLUSTER, getX(), getY() + 1.5, getZ(), 60, 2.0, 1.0, 2.0, 0.3);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 4.0F, 0.3F);
        level.playSound(null, this, SoundEvents.SPIDER_DEATH, SoundSource.HOSTILE, 2.5F, 0.3F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        clearWebs(level, true);
    }

    @Override
    public void onRemoval(Entity.RemovalReason reason) {
        if (level() instanceof ServerLevel level) {
            clearWebs(level, true);
        }
        super.onRemoval(reason);
    }
}
