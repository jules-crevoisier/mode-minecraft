package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
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
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.cubemob.Slime;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrownSplashPotion;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.Potion;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;

import static com.wayfarers.generated.MobAnims.SwampCrone.BARRAGE;
import static com.wayfarers.generated.MobAnims.SwampCrone.DASH;
import static com.wayfarers.generated.MobAnims.SwampCrone.ERUPT;
import static com.wayfarers.generated.MobAnims.SwampCrone.HEX;
import static com.wayfarers.generated.MobAnims.SwampCrone.HOP;
import static com.wayfarers.generated.MobAnims.SwampCrone.ROAR;
import static com.wayfarers.generated.MobAnims.SwampCrone.STAGGER;
import static com.wayfarers.generated.MobAnims.SwampCrone.SUMMON;
import static com.wayfarers.generated.MobAnims.SwampCrone.SWIPE;
import static com.wayfarers.generated.MobAnims.SwampCrone.THROW;

/**
 * La Grand-Mère du marais (The Swamp Crone): boss of the Swamp Witch Huts, brewing in the drowned grotto
 * under the bog. A giant hunched hag with a bubbling cauldron strapped to her back and a lantern staff.
 * <ul>
 *     <li>Phase 1: potion barrage (three splash potions, aimed with a lead), staff swipe, the hex mark that
 *     follows a player then bursts, slimes tipped out of her cauldron, and the frog leap (a gap-closer
 *     with a splash shockwave on landing).</li>
 *     <li>Phase 2: faster and nastier brews (strong harming); the swipe chains into a hex; new moves:
 *     boiling cauldron eruptions (geysers under every player that leave poison pools), the broom dash
 *     (rides her staff across the arena trailing poison), and the double barrage. Witches answer her call.</li>
 * </ul>
 */
public class SwampCrone extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 3.6F;

    public SwampCrone(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 360.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ARMOR_TOUGHNESS, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SwampCrone.TICKS;
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
        return 60.0F;
    }

    @Override
    protected double preferredRange() {
        return 5.0;
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    /** Her own brews do not take on her. */
    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        if (effect.is(MobEffects.POISON) || effect.is(MobEffects.SLOWNESS) || effect.is(MobEffects.WEAKNESS)) {
            return false;
        }
        return super.canBeAffected(effect);
    }

    /** Splashes of her own potions (and her witches' stray brews) never hurt her. */
    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        Entity src = source.getEntity();
        if (src == this || (src != null && src.entityTags().contains(MINION_TAG))) {
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.WITCH_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.WITCH_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.WITCH_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.6F + random.nextFloat() * 0.1F;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // 1. Potion barrage: reaches into the cauldron (13 t), hurls three splash potions in a spread.
        out.add(BossAttack.of("throw").anim(THROW).timing(13, 2, 13).range(4.0, 22).cooldown(45).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BOTTLE_FILL, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                    if (tick % 3 == 0) {
                        Vec3 c = cauldronTop(b);
                        level.sendParticles(ParticleTypes.WITCH, c.x, c.y, c.z, 4, 0.4, 0.2, 0.4, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> barrage(level, b, t, 3, 0))
                .build());

        // 2. Staff swipe: the staff drawn far back (13 t), a wide swing. Phase 2: may chain into a hex.
        out.add(BossAttack.of("swipe").anim(SWIPE).timing(13, 3, 10).range(0, 5.0).cooldown(35).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.6, 95, ParticleTypes.WITCH);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 5.0, 95, 13.0F, 1.5);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    Vec3 p = b.ahead(2.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.2, p.z, 3, 1.5, 0.2, 1.5, 0);
                    level.sendParticles(ParticleTypes.GLOW, p.x, p.y + 1.5, p.z, 12, 1.5, 0.4, 1.5, 0.05);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, "hex");
                    }
                })
                .build());

        // 3. Hex mark: the lantern raised (16 t); a sigil clings to the target's feet for a second, then
        //    stops and bursts 0.7 s later. Keep moving.
        out.add(BossAttack.of("hex").anim(HEX).timing(16, 2, 14).range(3.0, 28).cooldown(110).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(ParticleTypes.GLOW, b.getX(), b.getY() + 4.0, b.getZ(), 6, 0.5, 0.5, 0.5, 0.05);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_BLINDNESS, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), 28)) {
                        b.addEffect(hexMark(e, b.phase() == 2 ? 14 : 18, 16.0F));
                    }
                    level.playSound(null, b, SoundEvents.EVOKER_CAST_SPELL, SoundSource.HOSTILE, 2.0F, 0.7F);
                })
                .build());

        // 4. Summon: bows deep and tips the cauldron over her head (18 t): slimes slop out; witches in phase 2.
        out.add(BossAttack.of("summon").anim(SUMMON).timing(18, 4, 14).range(0, 30).cooldown(480).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        Vec3 c = cauldronTop(b);
                        level.sendParticles(ParticleTypes.ITEM_SLIME, c.x, c.y, c.z, 6, 0.5, 0.3, 0.5, 0.05);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.BREWING_STAND_BREW, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    int alive = level.getEntitiesOfClass(Mob.class, new AABB(b.blockPosition()).inflate(30),
                            m -> m.entityTags().contains(MINION_TAG)).size();
                    int n = Math.max(0, Math.min(b.phase() == 2 ? 3 : 2, 5 - alive));
                    spillSlimes(level, b, n);
                    if (b.phase() == 2 && alive < 4) {
                        b.summon(level, EntityTypes.WITCH, 1, 5.0);
                    }
                    Vec3 p = b.ahead(2.0);
                    level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + 0.5, p.z, 60, 1.2, 0.3, 1.2, 0.2);
                    level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());

        // 5. Frog leap (gap-closer): a deep crouch (14 t), she leaps at the target and lands with a splash
        //    shockwave (active tick 7).
        out.add(BossAttack.of("hop").anim(HOP).timing(14, 8, 10).range(5.0, 16).cooldown(90).weight(9)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 3.0, ParticleTypes.SPLASH);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.FROG_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(1.7, dist * 0.17), 0.6);
                    level.playSound(null, b, SoundEvents.FROG_LONG_JUMP, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 7) {
                        b.hitCircle(level, b.position(), 3.2, 14.0F, 1.2, 0.5);
                        b.addEffect(WayfarerBoss.wave(b.position(), 7, 0.45, 7.0F, ParticleTypes.SPLASH));
                        level.sendParticles(ParticleTypes.SPLASH, b.getX(), b.getY() + 0.2, b.getZ(), 80, 2.0, 0.2, 2.0, 0.3);
                        level.sendParticles(ParticleTypes.ITEM_SLIME, b.getX(), b.getY() + 0.3, b.getZ(), 30, 1.5, 0.2, 1.5, 0.1);
                        level.playSound(null, b, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 2.5F, 0.4F);
                        level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.5F, 0.6F);
                        if (b.phase() == 2) {
                            poisonPool(level, b, b.position(), 2.5F, 120);
                        }
                    }
                })
                .build());

        // 6. (P2) Boiling eruption: the cauldron boils over (18 t), the staff strikes the mud: scalding geysers
        //    burst under every player and around her after a warning, leaving poison pools.
        out.add(BossAttack.of("erupt").anim(ERUPT).phaseTwo().timing(18, 6, 16).range(0, 24).cooldown(220).weight(7)
                .windup((b, level, t, tick) -> {
                    Vec3 c = cauldronTop(b);
                    level.sendParticles(ParticleTypes.ITEM_SLIME, c.x, c.y + 0.3, c.z, 4, 0.4, 0.4, 0.4, 0.1);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.6F);
                        level.playSound(null, b, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), 24)) {
                        b.addEffect(geyser(e.position(), 16, 14.0F));
                    }
                    for (int i = 0; i < 4; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 3 + b.getRandom().nextDouble() * 6;
                        b.addEffect(geyser(b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 16 + i * 5, 14.0F));
                    }
                    level.sendParticles(ParticleTypes.SPLASH, b.getX(), b.getY() + 0.2, b.getZ(), 40, 1.0, 0.1, 1.0, 0.2);
                    level.playSound(null, b, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());

        // 7. (P2) Broom dash: she mounts her staff (15 t, the path is shown), streaks across the arena for
        //    8 ticks, hitting everything she passes and trailing poison.
        out.add(BossAttack.of("dash").anim(DASH).phaseTwo().timing(15, 8, 13).range(5.0, 20).cooldown(160).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 1; i <= 11; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.WITCH, p.x, p.y + 0.2, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.BREEZE_JUMP, SoundSource.HOSTILE, 2.0F, 0.6F))
                .active((b, level, t, tick) -> {
                    b.lunge(1.25, 0.02);
                    b.hitCircle(level, b.position(), 1.8, 13.0F, 1.3, 0.4);
                    level.sendParticles(ParticleTypes.WITCH, b.getX(), b.getY() + 1.0, b.getZ(), 10, 0.4, 0.4, 0.4, 0.05);
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.5, b.getZ(), 3, 0.3, 0.2, 0.3, 0.02);
                    if (tick % 3 == 1) {
                        poisonPool(level, b, b.position(), 1.6F, 100);
                    }
                })
                .build());

        // 8. (P2) Double barrage: two volleys of four potions, 0.6 s apart.
        out.add(BossAttack.of("barrage").anim(BARRAGE).phaseTwo().timing(12, 14, 14).range(4.0, 24).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        Vec3 c = cauldronTop(b);
                        level.sendParticles(ParticleTypes.WITCH, c.x, c.y, c.z, 5, 0.4, 0.2, 0.4, 0.02);
                    }
                })
                .impact((b, level, t, tick) -> barrage(level, b, t, 4, -0.12))
                .active((b, level, t, tick) -> {
                    if (tick == 12) {
                        barrage(level, b, t, 4, 0.12);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private helpers

    private static Vec3 cauldronTop(WayfarerBoss b) {
        return b.position().subtract(b.forward().scale(0.6)).add(0, 3.0, 0);
    }

    /** Splash potions thrown in a spread toward the target, with a lead. */
    private static void barrage(ServerLevel level, WayfarerBoss b, @Nullable LivingEntity t, int count, double skew) {
        if (t == null) {
            return;
        }
        Vec3 from = b.position().add(0, 3.0, 0).add(b.forward().scale(0.8));
        Vec3 aim = t.position().add(t.getDeltaMovement().scale(8)).subtract(from);
        double dist = aim.horizontalDistance();
        double base = Math.atan2(aim.z, aim.x);
        for (int i = 0; i < count; i++) {
            double a = base + skew + (i - (count - 1) / 2.0) * (dist > 10 ? 0.09 : 0.16);
            double d = dist * (0.9 + 0.1 * i / Math.max(1, count - 1));
            Holder<Potion> brew = pickBrew(b, i);
            ThrownSplashPotion potion = new ThrownSplashPotion(level, from.x, from.y, from.z,
                    PotionContents.createItemStack(Items.SPLASH_POTION, brew));
            potion.setOwner(b);
            potion.shoot(Math.cos(a) * d, aim.y + d * 0.25, Math.sin(a) * d, 0.85F, 3.0F);
            level.addFreshEntity(potion);
        }
        level.playSound(null, b, SoundEvents.WITCH_THROW, SoundSource.HOSTILE, 2.0F, 0.6F);
        level.playSound(null, b, SoundEvents.SPLASH_POTION_THROW, SoundSource.HOSTILE, 1.5F, 0.7F);
    }

    private static Holder<Potion> pickBrew(WayfarerBoss b, int i) {
        boolean p2 = b.phase() == 2;
        return switch (i % 3) {
            case 0 -> p2 ? Potions.STRONG_HARMING : Potions.HARMING;
            case 1 -> p2 ? Potions.STRONG_POISON : Potions.POISON;
            default -> b.getRandom().nextBoolean() ? Potions.SLOWNESS : Potions.WEAKNESS;
        };
    }

    /** The hex: a sigil that clings to the victim's feet for ``follow`` ticks, then holds still and bursts
     * 14 ticks later. */
    private static WayfarerBoss.Effect hexMark(LivingEntity victim, int follow, float damage) {
        int[] t = {0};
        Vec3[] pos = {victim.position()};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < follow && victim.isAlive()) {
                pos[0] = victim.position();
            }
            Vec3 p = pos[0];
            double r = k < follow ? 2.4 : 2.4 * (1.0 - (k - follow) / 18.0) + 0.6;
            if (k % 2 == 0) {
                boss.telegraphRing(level, p, r, k < follow ? ParticleTypes.WITCH : ParticleTypes.GLOW);
                level.sendParticles(ParticleTypes.ENCHANT, p.x, p.y + 0.3, p.z, 4, 0.5, 0.1, 0.5, 0.2);
            }
            if (k == follow) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.EVOKER_PREPARE_WOLOLO, SoundSource.HOSTILE, 1.8F, 0.8F);
            }
            if (k >= follow + 14) {
                boss.hitCircle(level, p, 2.6, damage, 0.6, 0.7);
                level.sendParticles(ParticleTypes.WITCH, p.x, p.y + 1.0, p.z, 60, 1.2, 1.0, 1.2, 0.2);
                level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.5, p.z, 2, 0.5, 0.2, 0.5, 0);
                level.playSound(null, p.x, p.y, p.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.4F, 1.2F);
                return true;
            }
            return false;
        };
    }

    /** A scalding geyser: bubbles at the spot for ``delay`` ticks, then a column of brew that throws up and
     * leaves a poison pool. */
    private static WayfarerBoss.Effect geyser(Vec3 at, int delay, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            Vec3 p = new Vec3(at.x, groundY(level, at.x, at.y, at.z), at.z);
            if (t[0]++ < delay) {
                if (t[0] % 2 == 0) {
                    level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y + 0.1, p.z, 4, 0.8, 0.05, 0.8, 0.02);
                    level.sendParticles(ParticleTypes.BUBBLE_POP, p.x, p.y + 0.2, p.z, 3, 0.8, 0.05, 0.8, 0.02);
                }
                if (t[0] % 8 == 0) {
                    level.playSound(null, p.x, p.y, p.z, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 1.0F, 0.6F);
                }
                return false;
            }
            for (int y = 0; y < 5; y++) {
                level.sendParticles(ParticleTypes.SPLASH, p.x, p.y + y * 0.8, p.z, 25, 0.5, 0.3, 0.5, 0.2);
                level.sendParticles(ParticleTypes.WITCH, p.x, p.y + y * 0.8, p.z, 4, 0.4, 0.3, 0.4, 0.05);
            }
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (e.position().multiply(1, 0, 1).distanceTo(p.multiply(1, 0, 1)) <= 2.0) {
                    boss.strike(level, e, damage, 0.2, 1.0);
                }
            }
            poisonPool(level, boss, p, 2.2F, 140);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 2.0F, 0.5F);
            level.playSound(null, p.x, p.y, p.z, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.8F);
            return true;
        };
    }

    private static double groundY(ServerLevel level, double x, double y, double z) {
        BlockPos pos = BlockPos.containing(x, y + 2, z);
        for (int i = 0; i < 8; i++) {
            BlockPos below = pos.below();
            if (level.getBlockState(below).isFaceSturdy(level, below, Direction.UP) && !level.getBlockState(pos).isSolid()) {
                return pos.getY();
            }
            pos = below;
        }
        return y;
    }

    /** A lingering pool of poisonous brew. */
    private static void poisonPool(ServerLevel level, WayfarerBoss b, Vec3 at, float radius, int duration) {
        AreaEffectCloud cloud = new AreaEffectCloud(level, at.x, at.y, at.z);
        cloud.setOwner(b);
        cloud.setRadius(radius);
        cloud.setDuration(duration);
        cloud.setWaitTime(6);
        cloud.setRadiusPerTick(-radius / (duration + 40.0F));
        cloud.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1));
        level.addFreshEntity(cloud);
    }

    /** Slimes slopped out of the cauldron in front of her. */
    private static void spillSlimes(ServerLevel level, WayfarerBoss b, int count) {
        for (int i = 0; i < count; i++) {
            Slime slime = EntityTypes.SLIME.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (slime == null) {
                continue;
            }
            slime.setSize(2, true);
            Vec3 p = b.ahead(1.8).add((i - (count - 1) / 2.0) * 1.2, 1.5, 0);
            slime.snapTo(p.x, p.y, p.z, b.getYRot(), 0);
            Vec3 f = b.forward().scale(0.35);
            slime.setDeltaMovement(f.x + (b.getRandom().nextDouble() - 0.5) * 0.3, 0.3, f.z);
            slime.addTag(MINION_TAG);
            slime.setTarget(b.getTarget());
            level.addFreshEntity(slime);
            level.sendParticles(ParticleTypes.ITEM_SLIME, p.x, p.y, p.z, 15, 0.4, 0.4, 0.4, 0.1);
        }
    }

    // ------------------------------------------------------------------ ambience, phases, death

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 4 == 0) {
            Vec3 c = cauldronTop(this);
            level.sendParticles(phase() == 2 ? ParticleTypes.ITEM_SLIME : ParticleTypes.WITCH, c.x, c.y, c.z,
                    2, 0.35, 0.1, 0.35, 0.01);
        }
        if (tickCount % 50 == 0) {
            Vec3 c = cauldronTop(this);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.BREWING_STAND_BREW, SoundSource.HOSTILE, 0.8F, 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("swamp_crone_frenzy"), 0.25,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 c = cauldronTop(this);
        level.sendParticles(ParticleTypes.ITEM_SLIME, c.x, c.y, c.z, 80, 1.5, 1.5, 1.5, 0.2);
        level.sendParticles(ParticleTypes.WITCH, getX(), getY() + 2, getZ(), 80, 2, 1.5, 2, 0.1);
        level.playSound(null, this, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(blockPosition()).inflate(40),
                m -> m.entityTags().contains(MINION_TAG))) {
            level.sendParticles(ParticleTypes.POOF, m.getX(), m.getY() + 1, m.getZ(), 10, 0.3, 0.5, 0.3, 0.05);
            m.discard();
        }
        level.sendParticles(ParticleTypes.WITCH, getX(), getY() + 2, getZ(), 150, 2, 2, 2, 0.1);
        level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 3, getZ(), 100, 1.5, 1, 1.5, 0.3);
    }
}
