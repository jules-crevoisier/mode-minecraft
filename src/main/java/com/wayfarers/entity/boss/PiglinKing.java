package com.wayfarers.entity.boss;

import com.wayfarers.Wayfarers;
import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.PiglinKing.CHARGE;
import static com.wayfarers.generated.MobAnims.PiglinKing.COINS;
import static com.wayfarers.generated.MobAnims.PiglinKing.POUND;
import static com.wayfarers.generated.MobAnims.PiglinKing.ROAR;
import static com.wayfarers.generated.MobAnims.PiglinKing.SMASH;
import static com.wayfarers.generated.MobAnims.PiglinKing.STAGGER;
import static com.wayfarers.generated.MobAnims.PiglinKing.SUMMON;
import static com.wayfarers.generated.MobAnims.PiglinKing.SWING;
import static com.wayfarers.generated.MobAnims.PiglinKing.THROW;
import static com.wayfarers.generated.MobAnims.PiglinKing.WHIRL;

/**
 * Le Roi piglin doré (The Golden Piglin King): boss of the Piglin Sanctuary, a massive piglin brute king
 * with a giant golden mace-axe.
 * <ul>
 *     <li>Phase 1: overhead mace smash, wide swing, a belly charge across the hall, a ground pound with a
 *     golden shockwave (jump it), a rain of gold coins on marked spots, and a bellow that calls brutes.</li>
 *     <li>Phase 2 (enraged, red eyes, faster): the charge comes twice, the smash sends a shockwave, the pound
 *     sends two, the coin rain doubles, a mace throw that flies out along a line and comes back, and a
 *     whirlwind that drags itself toward the player.</li>
 * </ul>
 */
public class PiglinKing extends WayfarerBoss {
    public static final float WIDTH = 2.2F;
    public static final float HEIGHT = 4.2F;
    private static final int GOLD = 0xFFC83C;
    private static final int MAX_MINIONS = 4;
    private static final double THROW_RANGE = 11.0;
    private int charges;

    public PiglinKing(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 580.0)
                .add(Attributes.ARMOR, 16.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.PiglinKing.TICKS;
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
        return 100.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.8;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // smash: the mace lifted over the crown, brought down on a marked spot (0.85 s)
        out.add(BossAttack.of("smash").anim(SMASH).timing(17, 3, 16).range(0, 6.0).cooldown(45).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(3.4), 2.6, gold(1.2F));
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.4);
                    b.hitCircle(level, c, 2.8, 19.0F, 1.0, 0.6);
                    debris(level, c, 40);
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(c, 7, 0.5, 8.0F, gold(1.6F)));
                    }
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.7F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.2F, 0.6F);
                })
                .build());
        // swing: the mace swung far out to his right, then a flat sweep across (0.70 s)
        out.add(BossAttack.of("swing").anim(SWING).timing(14, 3, 13).range(0, 6.0).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.5, 110, gold(1.2F));
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 6.0, 110, 15.0F, 1.9);
                    Vec3 p = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.5, p.z, 3, 1.5, 0.2, 1.5, 0);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_AIR, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "smash");
                    }
                })
                .build());
        // charge: paws the ground with head and belly lowered, then barrels through (0.75 s, then 12 ticks)
        out.add(BossAttack.of("charge").anim(CHARGE).timing(15, 12, 13).range(5.0, 20.0).cooldown(110).weight(9)
                .start((b, level, t, tick) -> ((PiglinKing) b).chargeHits.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.NETHERRACK.defaultBlockState()),
                                b.getX(), b.getY() + 0.1, b.getZ(), 8, 0.6, 0.05, 0.6, 0.1);
                        for (int i = 2; i <= 13; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(gold(1.0F), p.x, p.y + 0.15, p.z, 1, 0.3, 0, 0.3, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.HOGLIN_ANGRY, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 1.6F, 0.8F))
                .active((b, level, t, tick) -> {
                    PiglinKing k = (PiglinKing) b;
                    Vec3 f = b.forward().scale(0.85);
                    b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                    b.hurtMarked = true;
                    for (LivingEntity v : b.victims(level, b.ahead(1.2), 2.2)) {
                        if (k.chargeHits.add(v.getUUID())) {
                            b.strike(level, v, 16.0F, 2.2, 0.55);
                            level.playSound(null, b, SoundEvents.HOGLIN_ATTACK, SoundSource.HOSTILE, 2.0F, 0.6F);
                        }
                    }
                    if (tick % 2 == 0) {
                        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.NETHERRACK.defaultBlockState()),
                                b.getX(), b.getY() + 0.1, b.getZ(), 10, 0.8, 0.05, 0.8, 0.1);
                        level.playSound(null, b, SoundEvents.PIGLIN_BRUTE_STEP, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .end((b, level, t, tick) -> {
                    PiglinKing k = (PiglinKing) b;
                    // phase 2: he wheels round and charges a second time (a new wind-up, re-aimed)
                    if (b.phase() == 2 && k.charges++ % 2 == 0) {
                        b.chain(level, "charge");
                    }
                })
                .build());
        // pound: a hop, then mace, fist and belly hammer the ground: a golden shockwave (1.00 s)
        out.add(BossAttack.of("pound").anim(POUND).timing(20, 3, 17).range(0, 8.0).cooldown(110).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 3.5, gold(1.4F));
                    }
                    if (tick == 10) {
                        b.lunge(0.0, 0.45);
                        level.playSound(null, b, SoundEvents.PIGLIN_BRUTE_ANGRY, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.position();
                    b.hitCircle(level, c, 3.5, 18.0F, 1.4, 0.6);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 15 : 11, 0.5, 11.0F, gold(1.8F)));
                    debris(level, c, 60);
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.4, c.z, 3, 1.0, 0.1, 1.0, 0);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.4F);
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 2) { // a second, slower ring right behind the first
                        b.addEffect(WayfarerBoss.wave(b.position(), 15, 0.32, 9.0F, gold(1.3F)));
                    }
                })
                .build());
        // coins: digs into his hoard and flings it to the sky; the gold rains down on marked spots (0.70 s)
        out.add(BossAttack.of("coins").anim(COINS).timing(14, 3, 19).range(0, 24.0).cooldown(200).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        level.sendParticles(nugget(), b.getX(), b.getY() + 1.6, b.getZ(), 3, 0.6, 0.2, 0.6, 0.05);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.PIGLIN_ADMIRING_ITEM, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.sendParticles(nugget(), b.getX(), b.getY() + 4.5, b.getZ(), 60, 1.0, 1.5, 1.0, 0.6);
                    level.playSound(null, b, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.PIGLIN_CELEBRATE, SoundSource.HOSTILE, 2.0F, 0.6F);
                    int n = 0;
                    for (LivingEntity v : b.victims(level, b.position(), 26)) {
                        if (v instanceof Player) {
                            b.addEffect(coin(v.position(), 22 + n * 4));
                            n++;
                        }
                    }
                    int extra = b.phase() == 2 ? 14 : 7;
                    for (int i = 0; i < extra; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 2.5 + b.getRandom().nextDouble() * 10;
                        b.addEffect(coin(b.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 18 + i * 3));
                    }
                })
                .build());
        // summon: a bellowing call: his brutes come running (0.60 s)
        out.add(BossAttack.of("summon").anim(SUMMON).timing(12, 1, 23).range(0, 30).cooldown(520).weight(5)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.PIGLIN_BRUTE_ANGRY, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0F, 0.8F);
                    int room = MAX_MINIONS - ((PiglinKing) b).minions(level);
                    if (room > 0) {
                        b.summon(level, EntityTypes.PIGLIN_BRUTE, Math.min(room, b.phase() == 2 ? 2 : 1), 4.0);
                    }
                    if (room > 1) {
                        b.summon(level, EntityTypes.PIGLIN, Math.min(room - 1, 2), 5.0);
                    }
                })
                .build());
        // throw (phase 2): the mace hurled spinning down a line, then flying back to his hand (0.80 s)
        out.add(BossAttack.of("throw").anim(THROW).phaseTwo().timing(16, 18, 14).range(3.5, 16.0).cooldown(130).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= THROW_RANGE; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(gold(1.0F), p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(thrownMace());
                    level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_AIR, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // whirl (phase 2): mace held out, three heavy turns that drag him toward the player (0.60 s, then 20)
        out.add(BossAttack.of("whirl").anim(WHIRL).phaseTwo().timing(12, 20, 12).range(0, 7.0).cooldown(150).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.8, gold(1.3F));
                    }
                })
                .active((b, level, t, tick) -> {
                    if (t != null) {
                        Vec3 to = t.position().subtract(b.position()).multiply(1, 0, 1);
                        if (to.length() > 1.5) {
                            Vec3 m = to.normalize().scale(0.16);
                            b.setDeltaMovement(m.x, b.getDeltaMovement().y, m.z);
                            b.hurtMarked = true;
                        }
                    }
                    if (tick % 4 == 0) {
                        b.hitCircle(level, b.position(), 4.6, 10.0F, 1.4, 0.35);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    double a0 = tick * 0.75;
                    for (int k = 0; k < 3; k++) {
                        double a = a0 + k * Math.PI * 2 / 3;
                        level.sendParticles(gold(1.6F), b.getX() + Math.cos(a) * 4.2, b.getY() + 1.6, b.getZ() + Math.sin(a) * 4.2,
                                3, 0.2, 0.2, 0.2, 0);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private helpers

    private final Set<UUID> chargeHits = new HashSet<>();

    private static ParticleOptions gold(float scale) {
        return new DustParticleOptions(GOLD, scale);
    }

    private static ParticleOptions nugget() {
        return new ItemParticleOption(ParticleTypes.ITEM, Items.GOLD_NUGGET);
    }

    private static void debris(ServerLevel level, Vec3 c, int count) {
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.GOLD_BLOCK.defaultBlockState()),
                c.x, c.y + 0.3, c.z, count, 1.2, 0.3, 1.2, 0.2);
        level.sendParticles(nugget(), c.x, c.y + 0.6, c.z, count / 2, 0.8, 0.4, 0.8, 0.25);
    }

    private int minions(ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(32, 12, 32),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    /** A falling gold coin: golden dust drifts down onto a marked circle, then the coin strikes. */
    private static Effect coin(Vec3 target, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            Vec3 pos = new Vec3(target.x, boss.getY(), target.z);
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    boss.telegraphRing(level, pos, 1.7, gold(1.0F));
                    level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.GOLD_BLOCK.defaultBlockState()),
                            pos.x, pos.y + 7, pos.z, 3, 0.6, 0.3, 0.6, 0);
                }
                int left = delay - t[0];
                if (left <= 8) {
                    level.sendParticles(nugget(), pos.x, pos.y + left * 0.9, pos.z, 4, 0.2, 0.2, 0.2, 0);
                }
                t[0]++;
                return false;
            }
            debris(level, pos, 24);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 2.0F, 0.6F);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.8F, 1.4F);
            for (LivingEntity e : boss.victims(level, pos, 1.9)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= 1.9) {
                    boss.strike(level, e, 11.0F, 0.3, 0.4);
                }
            }
            return true;
        };
    }

    /**
     * The thrown mace: a spinning gold blur that flies {@link #THROW_RANGE} blocks along the locked facing in
     * 9 ticks, hitting everything in its path, then flies back along the same line and hits again.
     */
    private static Effect thrownMace() {
        int[] t = {0};
        Set<UUID> out = new HashSet<>();
        Set<UUID> back = new HashSet<>();
        return (boss, level) -> {
            int k = t[0]++;
            double d = k <= 9 ? THROW_RANGE * k / 9.0 : THROW_RANGE * (18 - k) / 9.0;
            Vec3 p = boss.ahead(Math.max(1.0, d)).add(0, 2.0, 0);
            level.sendParticles(gold(2.0F), p.x, p.y, p.z, 6, 0.4, 0.4, 0.4, 0);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 4, 0.3, 0.3, 0.3, 0.1);
            if (k % 3 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.2F, 1.4F);
            }
            Set<UUID> hit = k <= 9 ? out : back;
            for (LivingEntity e : boss.victims(level, p, 2.0)) {
                if (e.position().add(0, e.getBbHeight() / 2, 0).distanceTo(p) <= 1.9 && hit.add(e.getUUID())) {
                    boss.strike(level, e, 15.0F, 1.2, 0.4);
                }
            }
            if (k == 9) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.TRIDENT_RETURN, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            return k >= 18;
        };
    }

    // ------------------------------------------------------------------ ambience, phases

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 10 == 0) {
            level.sendParticles(gold(1.0F), getX(), getY() + 2.5, getZ(), 3, 0.9, 1.2, 0.9, 0);
        }
        if (phase() == 2 && tickCount % 3 == 0) {
            // enraged: his eyes burn red
            Vec3 f = forward();
            Vec3 side = new Vec3(-f.z, 0, f.x).scale(0.35);
            Vec3 eyes = position().add(f.scale(0.75)).add(0, 3.25, 0);
            for (int s = -1; s <= 1; s += 2) {
                Vec3 e = eyes.add(side.scale(s));
                level.sendParticles(new DustParticleOptions(0xFF1A1A, 0.8F), e.x, e.y, e.z, 1, 0.02, 0.02, 0.02, 0);
            }
            if (tickCount % 30 == 0) {
                level.sendParticles(ParticleTypes.ANGRY_VILLAGER, getX(), getY() + 4.4, getZ(), 1, 0.3, 0.1, 0.3, 0);
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(Wayfarers.id("piglin_king_phase_two"), 0.25,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        charges = 0;
        level.sendParticles(nugget(), getX(), getY() + 3, getZ(), 80, 1.5, 1.0, 1.5, 0.5);
        level.playSound(null, this, SoundEvents.PIGLIN_BRUTE_ANGRY, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.6F);
        int room = MAX_MINIONS - minions(level);
        if (room > 0) {
            summon(level, EntityTypes.PIGLIN_BRUTE, Math.min(room, 2), 5.0);
        }
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
        level.sendParticles(nugget(), getX(), getY() + 2, getZ(), 150, 1.5, 1.5, 1.5, 0.4);
        level.playSound(null, this, SoundEvents.PIGLIN_BRUTE_CONVERTED_TO_ZOMBIFIED, SoundSource.HOSTILE, 2.0F, 0.5F);
    }
}
