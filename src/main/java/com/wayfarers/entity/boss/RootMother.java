package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.projectile.EvokerFangs;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.RootMother.ERUPT;
import static com.wayfarers.generated.MobAnims.RootMother.GRAB;
import static com.wayfarers.generated.MobAnims.RootMother.ROAR;
import static com.wayfarers.generated.MobAnims.RootMother.ROOTWAVE;
import static com.wayfarers.generated.MobAnims.RootMother.SPORES;
import static com.wayfarers.generated.MobAnims.RootMother.SPROUT;
import static com.wayfarers.generated.MobAnims.RootMother.STAGGER;
import static com.wayfarers.generated.MobAnims.RootMother.SWEEP;
import static com.wayfarers.generated.MobAnims.RootMother.TIMBER;
import static com.wayfarers.generated.MobAnims.RootMother.VOLLEY;

/**
 * La Mère-Racine (The Root Mother): boss of the Hollow Giant Tree, waiting in the root cavern beneath it.
 * A towering treant matriarch with a crown of branches, a carved mask and a hollow, beating amber heart.
 * <ul>
 *     <li>Phase 1: a wide branch-arm sweep, a grab-and-slam, root eruptions under every player (and a line
 *     of roots racing toward them), a fan of thorns, and "timber": she rears up creaking and topples
 *     forward like a felled tree, crushing a long line, then lies open to punishment.</li>
 *     <li>Phase 2: faster, the sweep chains into a thorn volley, the eruptions strike twice, thorns poison;
 *     new moves: spore clouds (poison), creaking saplings rising from the soil, and the root wave: two
 *     rings of erupting roots rolling across the whole cavern (jump them).</li>
 * </ul>
 */
public class RootMother extends WayfarerBoss {
    public static final float WIDTH = 2.2F;
    public static final float HEIGHT = 5.2F;

    private static final BlockParticleOption ROOT_DUST = new BlockParticleOption(ParticleTypes.BLOCK,
            Blocks.ROOTED_DIRT.defaultBlockState());
    private static final BlockParticleOption MOSS_DUST = new BlockParticleOption(ParticleTypes.BLOCK,
            Blocks.MOSS_BLOCK.defaultBlockState());

    /** The creature held during the grab, if any. */
    private @Nullable UUID grabbed;

    public RootMother(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.RootMother.TICKS;
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
        return 85.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.55F;
    }

    @Override
    protected double preferredRange() {
        return 3.8;
    }

    /** A creature of root and fungus: her own spores and poisons do not take. */
    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        if (effect.is(MobEffects.POISON) || effect.is(MobEffects.SLOWNESS)) {
            return false;
        }
        return super.canBeAffected(effect);
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.CREAKING_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.CREAKING_HEART_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.CREAKING_HEART_BREAK;
    }

    @Override
    public float getVoicePitch() {
        return 0.55F + random.nextFloat() * 0.1F;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.ROOTED_DIRT_STEP, 1.2F, 0.5F);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // 1. Sweep: the great right arm drawn back (19 t), a flat sweep across a wide arc.
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(19, 3, 10).range(0, 6.0).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.8, 100, ParticleTypes.FALLING_SPORE_BLOSSOM);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.CREAKING_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.2, 100, 15.0F, 1.6);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.45F);
                    level.playSound(null, b, SoundEvents.AZALEA_LEAVES_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    Vec3 p = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 4, 2.0, 0.3, 2.0, 0);
                    level.sendParticles(ParticleTypes.CHERRY_LEAVES, p.x, p.y + 2.5, p.z, 30, 2.5, 1.0, 2.5, 0.05);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "volley");
                    }
                })
                .build());

        // 2. Grab and slam: arms spread (16 t), she clutches whoever stands in front, lifts them high and
        //    smashes them into the ground (active tick 17). Missing still shakes the ground in front.
        out.add(BossAttack.of("grab").anim(GRAB).timing(16, 18, 14).range(0, 4.5).cooldown(130).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 3.8, 55, ParticleTypes.COMPOSTER);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CREAKING_ACTIVATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> ((RootMother) b).tryGrab(level))
                .active((b, level, t, tick) -> ((RootMother) b).holdAndSlam(level, tick))
                .end((b, level, t, tick) -> ((RootMother) b).grabbed = null)
                .build());

        // 3. Root eruption: claws raised (21 t) and driven into the soil; roots race toward every player and
        //    burst beneath them after a warning (14 t). Phase 2: a second burst follows them.
        out.add(BossAttack.of("erupt").anim(ERUPT).timing(21, 8, 11).range(3.0, 26).cooldown(140).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(ROOT_DUST, b.getX(), b.getY() + 0.2, b.getZ(), 12, 1.8, 0.1, 1.8, 0.1);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 0.4F);
                    hitAround(b, level, 2.6, 8.0F);
                    for (LivingEntity e : b.victims(level, b.position(), 26)) {
                        rootLine(level, b, e.position(), 0);
                        rootBurst(level, b, e.position(), 14, 13.0F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 6) {
                        for (LivingEntity e : b.victims(level, b.position(), 26)) {
                            rootBurst(level, b, e.position(), 12, 11.0F);
                        }
                    }
                })
                .build());

        // 4. Thorn volley: the crown flares (17 t), the left arm whips a fan of thorns. Phase 2: two fans,
        //    poisoned.
        out.add(BossAttack.of("volley").anim(VOLLEY).timing(17, 6, 9).range(6.0, 26).cooldown(70).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, b.getX(), b.getY() + 5.5, b.getZ(),
                                8, 1.6, 0.6, 1.6, 0);
                        b.telegraphArc(level, 9.0, 24, ParticleTypes.CHERRY_LEAVES);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.CHERRY_LEAVES_FALL, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> thorns(level, b, t, 7, 0))
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 4) {
                        thorns(level, b, t, 6, 0.09);
                    }
                })
                .build());

        // 5. Timber: she rears up creaking (25 t) and topples forward like a felled tree, crushing a long line.
        //    She lies there for a long punish window, then pushes herself up.
        out.add(BossAttack.of("timber").anim(TIMBER).timing(25, 3, 32).range(3.5, 10).cooldown(170).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        for (int i = 1; i <= 8; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ROOT_DUST, p.x, p.y + 0.15, p.z, 2, 0.5, 0, 0.5, 0);
                        }
                    }
                    if (tick == 0 || tick == 10) {
                        level.playSound(null, b, SoundEvents.CREAKING_TWITCH, SoundSource.HOSTILE, 3.0F, 0.4F);
                        level.playSound(null, b, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                    if (tick == 20) {
                        b.lunge(0.75, 0.05);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitLine(level, 8.5, 1.7, 20.0F, 1.0);
                    for (int i = 1; i <= 8; i++) {
                        Vec3 p = b.ahead(i);
                        level.sendParticles(ROOT_DUST, p.x, p.y + 0.3, p.z, 10, 0.8, 0.3, 0.8, 0.15);
                        level.sendParticles(MOSS_DUST, p.x, p.y + 0.5, p.z, 6, 0.8, 0.4, 0.8, 0.15);
                    }
                    Vec3 c = b.ahead(5.5);
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 3, 1.5, 0.2, 1.5, 0);
                    level.playSound(null, b, SoundEvents.ZOMBIE_BREAK_WOODEN_DOOR, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.35F);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(c, 7, 0.4, 9.0F, ROOT_DUST));
                    }
                })
                .build());

        // 6. (P2) Spores: arms flung wide (16 t), the crown shakes out poison spore clouds around her and on
        //    every player; a burst of spores knocks back anyone hugging her roots.
        out.add(BossAttack.of("spores").anim(SPORES).phaseTwo().timing(16, 16, 12).range(0, 22).cooldown(260).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, ParticleTypes.SPORE_BLOSSOM_AIR);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.SPORE_BLOSSOM_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.0, 9.0F, 1.6, 0.4);
                    sporeCloud(level, b, b.position(), 4.0F);
                    for (LivingEntity e : b.victims(level, b.position(), 22)) {
                        sporeCloud(level, b, e.position(), 2.6F);
                    }
                    level.playSound(null, b, SoundEvents.SPORE_BLOSSOM_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .active((b, level, t, tick) -> level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, b.getX(),
                        b.getY() + 5.5, b.getZ(), 14, 3.0, 1.0, 3.0, 0.02))
                .build());

        // 7. (P2) Sprout: she kneels and presses her claws to the soil (16 t): creaking saplings rise.
        out.add(BossAttack.of("sprout").anim(SPROUT).phaseTwo().timing(16, 4, 20).range(0, 30).cooldown(520).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.0, ParticleTypes.HAPPY_VILLAGER);
                    }
                })
                .impact((b, level, t, tick) -> {
                    int alive = level.getEntitiesOfClass(Mob.class, new AABB(b.blockPosition()).inflate(30),
                            m -> m.entityTags().contains(MINION_TAG)).size();
                    b.summon(level, EntityTypes.CREAKING, Math.max(0, Math.min(3, 5 - alive)), 5.0);
                    level.sendParticles(ROOT_DUST, b.getX(), b.getY() + 0.3, b.getZ(), 60, 5.0, 0.2, 5.0, 0.2);
                    level.playSound(null, b, SoundEvents.CREAKING_SPAWN, SoundSource.HOSTILE, 3.0F, 0.7F);
                    level.playSound(null, b, SoundEvents.CREAKING_HEART_SPAWN, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());

        // 8. (P2) Root wave, the spectacle: both arms raised high (25 t) and smashed down; a ring of erupting
        //    roots rolls across the whole cavern, a slower second ring follows. Jump each ring.
        out.add(BossAttack.of("rootwave").anim(ROOTWAVE).phaseTwo().timing(25, 10, 13).range(0, 18).cooldown(300).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 3.5, ROOT_DUST);
                        level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, b.getX(), b.getY() + 5, b.getZ(),
                                6, 2, 1, 2, 0);
                    }
                    if (tick == 0 || tick == 12) {
                        level.playSound(null, b, SoundEvents.CREAKING_HEART_IDLE, SoundSource.HOSTILE, 3.0F, 0.5F);
                        level.playSound(null, b, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 3.5, 16.0F, 1.4, 0.6);
                    b.addEffect(rootWave(b.position(), 20, 0.5, 12.0F));
                    level.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + 0.5, b.getZ(), 4, 1.5, 0.2, 1.5, 0);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.3F);
                    level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 9) {
                        b.addEffect(rootWave(b.position(), 20, 0.34, 10.0F));
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ grab and slam

    private void tryGrab(ServerLevel level) {
        Vec3 fwd = forward();
        LivingEntity best = null;
        double bestD = 99;
        for (LivingEntity e : victims(level, position(), 5.0)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= 4.3 && (d < 1.0 || to.normalize().dot(fwd) > 0.45) && d < bestD) {
                best = e;
                bestD = d;
            }
        }
        level.playSound(null, this, SoundEvents.CREAKING_ATTACK, SoundSource.HOSTILE, 2.5F, 0.5F);
        if (best != null) {
            grabbed = best.getUUID();
            best.hurtServer(level, damageSources().mobAttack(this), 4.0F);
            level.playSound(null, best, SoundEvents.MANGROVE_ROOTS_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
    }

    private @Nullable LivingEntity grabbedEntity(ServerLevel level) {
        if (grabbed == null) {
            return null;
        }
        Entity e = level.getEntity(grabbed);
        return e instanceof LivingEntity le && le.isAlive() ? le : null;
    }

    private void holdAndSlam(ServerLevel level, int tick) {
        LivingEntity held = grabbedEntity(level);
        if (tick < 15 && held != null) {
            // carried up in the claws: from chest height out front to high over her crown
            double lift = Math.min(1.0, tick / 13.0);
            Vec3 hand = ahead(2.2 - 1.6 * lift).add(0, 2.4 + 4.0 * lift, 0);
            held.teleportTo(hand.x, hand.y, hand.z);
            held.setDeltaMovement(Vec3.ZERO);
            held.fallDistance = 0;
            held.hurtMarked = true;
            if (tick % 3 == 0) {
                level.sendParticles(ROOT_DUST, hand.x, hand.y + 0.5, hand.z, 6, 0.4, 0.4, 0.4, 0.05);
            }
        }
        if (tick == 17) {
            Vec3 c = ahead(3.0);
            if (held != null) {
                held.teleportTo(c.x, c.y + 0.2, c.z);
                held.fallDistance = 0;
                strike(level, held, 18.0F, 0.6, 0.3);
            }
            hitCircle(level, c, 2.8, 12.0F, 1.0, 0.5);
            level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.4, c.z, 2, 0.6, 0.1, 0.6, 0);
            level.sendParticles(ROOT_DUST, c.x, c.y + 0.3, c.z, 40, 1.5, 0.2, 1.5, 0.2);
            level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.6F, 0.4F);
            level.playSound(null, this, SoundEvents.ZOMBIE_ATTACK_WOODEN_DOOR, SoundSource.HOSTILE, 2.5F, 0.5F);
            grabbed = null;
        }
    }

    // ------------------------------------------------------------------ private helpers (roots, thorns, spores)

    private static void hitAround(WayfarerBoss b, ServerLevel level, double radius, float damage) {
        b.hitCircle(level, b.position(), radius, damage, 1.0, 0.5);
        level.sendParticles(ROOT_DUST, b.getX(), b.getY() + 0.3, b.getZ(), 30, radius * 0.6, 0.2, radius * 0.6, 0.15);
    }

    /** Top of the floor near (x, y, z): the first sturdy block surface within a few blocks. */
    private static double groundY(ServerLevel level, double x, double y, double z) {
        BlockPos pos = BlockPos.containing(x, y + 2, z);
        for (int i = 0; i < 8; i++) {
            BlockPos below = pos.below();
            if (level.getBlockState(below).isFaceSturdy(level, below, Direction.UP) && level.isEmptyBlock(pos)) {
                return pos.getY();
            }
            pos = below;
        }
        return y;
    }

    private static void fang(ServerLevel level, WayfarerBoss b, double x, double y, double z, float yawRad, int warmup) {
        level.addFreshEntity(new EvokerFangs(level, x, groundY(level, x, y, z), z, yawRad, warmup, b));
    }

    /** A warned burst of roots under ``at``: warning dust for ``delay`` ticks, then a ring of fangs and a
     * throw upward. */
    private static void rootBurst(ServerLevel level, WayfarerBoss b, Vec3 at, int delay, float damage) {
        Vec3 g = new Vec3(at.x, groundY(level, at.x, at.y, at.z), at.z);
        b.addEffect(WayfarerBoss.eruption(g, delay, 1.9, damage, ROOT_DUST, MOSS_DUST));
        int warm = Math.max(0, delay - 8);
        fang(level, b, g.x, g.y, g.z, 0, warm);
        for (int i = 0; i < 6; i++) {
            float a = (float) (Math.PI * 2 * i / 6);
            fang(level, b, g.x + Mth.cos(a) * 1.4, g.y, g.z + Mth.sin(a) * 1.4, a, warm + 1);
        }
    }

    /** Roots racing through the soil from the boss toward ``to`` (a line of fangs, like an evoker). */
    private static void rootLine(ServerLevel level, WayfarerBoss b, Vec3 to, int delay) {
        Vec3 d = to.subtract(b.position()).multiply(1, 0, 1);
        double len = Math.min(14, d.length());
        if (len < 2) {
            return;
        }
        Vec3 dir = d.normalize();
        float yaw = (float) Mth.atan2(dir.z, dir.x);
        for (double s = 1.5; s < len - 1.5; s += 1.3) {
            fang(level, b, b.getX() + dir.x * s, b.getY(), b.getZ() + dir.z * s, yaw, delay + (int) (s * 0.8));
        }
    }

    /** A fan of thorns (arrows) aimed with a lead at the target; ``poison`` > 0 tips them (phase 2). */
    private static void thorns(ServerLevel level, WayfarerBoss b, @Nullable LivingEntity t, int count, double offset) {
        if (t == null) {
            return;
        }
        Vec3 from = b.position().add(0, 3.6, 0).add(b.forward().scale(1.2));
        Vec3 aim = t.position().add(t.getDeltaMovement().scale(6)).add(0, t.getBbHeight() * 0.5, 0).subtract(from);
        double dist = aim.horizontalDistance();
        float baseYaw = (float) Mth.atan2(aim.z, aim.x);
        for (int i = 0; i < count; i++) {
            double spread = (i - (count - 1) / 2.0) * 0.11 + offset;
            double a = baseYaw + spread;
            Arrow arrow = new Arrow(level, b, new ItemStack(Items.ARROW), null);
            arrow.setPos(from.x, from.y, from.z);
            arrow.pickup = AbstractArrow.Pickup.DISALLOWED;
            arrow.setBaseDamage(3.0);
            if (b.phase() == 2) {
                arrow.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0));
            }
            arrow.shoot(Math.cos(a) * dist, aim.y + dist * 0.12, Math.sin(a) * dist, 1.9F, 1.5F);
            level.addFreshEntity(arrow);
        }
        level.sendParticles(ParticleTypes.CHERRY_LEAVES, from.x, from.y, from.z, 20, 0.8, 0.8, 0.8, 0.1);
        level.playSound(null, b, SoundEvents.ARROW_SHOOT, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.playSound(null, b, SoundEvents.AZALEA_LEAVES_BREAK, SoundSource.HOSTILE, 2.0F, 0.8F);
    }

    /** A lingering cloud of poisonous spores. */
    private static void sporeCloud(ServerLevel level, WayfarerBoss b, Vec3 at, float radius) {
        AreaEffectCloud cloud = new AreaEffectCloud(level, at.x, at.y, at.z);
        cloud.setOwner(b);
        cloud.setRadius(radius);
        cloud.setDuration(160);
        cloud.setWaitTime(10);
        cloud.setRadiusPerTick(-radius / 220.0F);
        cloud.setCustomParticle(ParticleTypes.SPORE_BLOSSOM_AIR);
        cloud.addEffect(new MobEffectInstance(MobEffects.POISON, 90, 1));
        level.addFreshEntity(cloud);
    }

    /** The root wave: an expanding ring that hits whoever stands on its edge (jump it), with roots bursting
     * from the soil along it. */
    private static WayfarerBoss.Effect rootWave(Vec3 center, double maxRadius, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] radius = {1.5};
        double[] lastFang = {0};
        return (boss, level) -> {
            radius[0] += speed;
            double r = radius[0];
            int n = Math.max(16, (int) (r * 5));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(ROOT_DUST, center.x + Math.cos(a) * r, center.y + 0.2, center.z + Math.sin(a) * r,
                        2, 0.1, 0.1, 0.1, 0.05);
            }
            if (r - lastFang[0] >= 2.0) {
                lastFang[0] = r;
                int k = Math.max(6, (int) (r * Math.PI * 2 / 2.6));
                double off = boss.getRandom().nextDouble();
                for (int i = 0; i < k; i++) {
                    double a = Math.PI * 2 * (i + off) / k;
                    fang(level, boss, center.x + Math.cos(a) * (r + 0.6), center.y, center.z + Math.sin(a) * (r + 0.6),
                            (float) a, 0);
                }
                level.playSound(null, center.x, center.y, center.z, SoundEvents.EVOKER_FANGS_ATTACK, SoundSource.HOSTILE,
                        1.5F, 0.6F);
            }
            for (LivingEntity e : boss.victims(level, center, r + 1.5)) {
                double d = e.position().multiply(1, 0, 1).distanceTo(center.multiply(1, 0, 1));
                boolean grounded = e.getY() - center.y < 0.9;
                if (Math.abs(d - r) <= 1.0 && grounded && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.6, 0.55);
                }
            }
            return r >= maxRadius;
        };
    }

    // ------------------------------------------------------------------ ambience, phases, death

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 5 == 0) {
            ParticleOptions p = phase() == 2 ? ParticleTypes.SPORE_BLOSSOM_AIR : ParticleTypes.FALLING_SPORE_BLOSSOM;
            level.sendParticles(p, getX(), getY() + 5.2, getZ(), 3, 1.6, 0.5, 1.6, 0.0);
        }
        if (tickCount % 9 == 0) {
            level.sendParticles(ParticleTypes.CHERRY_LEAVES, getX(), getY() + 5.0, getZ(), 2, 1.8, 0.4, 1.8, 0.0);
        }
        if (phase() == 2 && tickCount % 40 == 0) {
            level.playSound(null, this, SoundEvents.CREAKING_HEART_IDLE, SoundSource.HOSTILE, 1.5F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("root_mother_rage"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, getX(), getY() + 3, getZ(), 120, 4, 2, 4, 0.05);
        level.sendParticles(ROOT_DUST, getX(), getY() + 0.3, getZ(), 80, 5, 0.2, 5, 0.2);
        level.playSound(null, this, SoundEvents.CREAKING_HEART_SPAWN, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.5F, 0.6F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(blockPosition()).inflate(40),
                m -> m.entityTags().contains(MINION_TAG))) {
            level.sendParticles(ParticleTypes.POOF, m.getX(), m.getY() + 1, m.getZ(), 10, 0.3, 0.5, 0.3, 0.05);
            m.discard();
        }
        level.sendParticles(ParticleTypes.CHERRY_LEAVES, getX(), getY() + 4, getZ(), 200, 4, 3, 4, 0.05);
        level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, getX(), getY() + 6, getZ(), 120, 6, 2, 6, 0);
    }
}
