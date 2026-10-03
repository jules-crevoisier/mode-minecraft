package com.wayfarers.entity;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModBlocks;
import net.minecraft.core.BlockPos;
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
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;

import static com.wayfarers.generated.MobAnims.DrownedWarden.ROAR;
import static com.wayfarers.generated.MobAnims.DrownedWarden.SLAM;
import static com.wayfarers.generated.MobAnims.DrownedWarden.STAGGER;
import static com.wayfarers.generated.MobAnims.DrownedWarden.SUMMON;
import static com.wayfarers.generated.MobAnims.DrownedWarden.SWEEP;
import static com.wayfarers.generated.MobAnims.DrownedWarden.THRUST;
import static com.wayfarers.generated.MobAnims.DrownedWarden.WHIRL;

/**
 * Boss of the Sunken Citadel: a drowned king with a great trident.
 * <ul>
 *     <li>Phase 1: trident thrust (line), wide sweep (arc), double-handed slam that sends a tidal ring (jump it),
 *     calls drowned.</li>
 *     <li>Phase 2 (after a roar): faster, thrust chains into a sweep, two tidal rings per slam, a leaping strike
 *     from afar and a whirlpool spin that drags players in.</li>
 * </ul>
 */
public class DrownedWarden extends WayfarerBoss {
    public DrownedWarden(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 380.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.DrownedWarden.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.BLUE;
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
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        out.add(BossAttack.of("thrust").anim(THRUST).timing(15, 3, 12).range(0, 6.5).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        for (int i = 1; i <= 6; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.BUBBLE_POP, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.9, 0.05);
                    b.hitLine(level, 6.5, 1.1, 14.0F, 1.0);
                    level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.45F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(16, 4, 10).range(0, 5.0).cooldown(50).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 5 == 0) {
                        b.telegraphArc(level, 5.0, 80, ParticleTypes.BUBBLE_POP);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 5.5, 85, 11.0F, 1.4);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    Vec3 p = b.ahead(2.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.5, p.z, 3, 1.5, 0.2, 1.5, 0);
                })
                .build());
        out.add(BossAttack.of("slam").anim(SLAM).timing(21, 2, 18).range(0, 7.0).cooldown(90).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(2.5), 4.0, ParticleTypes.SPLASH);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(2.5);
                    b.hitCircle(level, c, 4.0, 16.0F, 1.0, 0.5);
                    b.addEffect(WayfarerBoss.wave(c, b.phase() == 2 ? 14 : 10, 0.45, 8.0F, ParticleTypes.SPLASH));
                    level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 3, 1.0, 0.2, 1.0, 0);
                    level.playSound(null, b, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (b.phase() == 2 && tick == 1) { // a second, slower ring right behind the first
                        b.addEffect(WayfarerBoss.wave(b.ahead(2.5), 14, 0.3, 8.0F, ParticleTypes.BUBBLE_POP));
                    }
                })
                .build());
        out.add(BossAttack.of("summon").anim(SUMMON).timing(10, 1, 22).range(0, 30).cooldown(420).weight(4)
                .impact((b, level, t, tick) -> {
                    b.summon(level, EntityTypes.DROWNED, b.phase() == 2 ? 3 : 2, 4.0);
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.5F, 0.8F);
                })
                .build());
        out.add(BossAttack.of("leap").anim(THRUST).phaseTwo().timing(14, 6, 14).range(6.5, 16).cooldown(80).weight(8)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 3 == 0) {
                        b.telegraphRing(level, t.position(), 2.5, ParticleTypes.BUBBLE_POP);
                    }
                })
                .impact((b, level, t, tick) -> {
                    double dist = t == null ? 8 : Math.sqrt(b.distanceToSqr(t));
                    b.lunge(Math.min(2.2, dist * 0.17), 0.45);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 5) {
                        b.hitCircle(level, b.position(), 3.0, 13.0F, 1.2, 0.4);
                        level.sendParticles(ParticleTypes.SPLASH, b.getX(), b.getY() + 0.2, b.getZ(), 60, 2.0, 0.1, 2.0, 0.3);
                    }
                })
                .build());
        out.add(BossAttack.of("whirl").anim(WHIRL).phaseTwo().timing(8, 16, 10).range(0, 9).cooldown(150).weight(7)
                .windup((b, level, t, tick) -> b.telegraphRing(level, b.position(), 3.2, ParticleTypes.NAUTILUS))
                .active((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), 12)) {
                        Vec3 pull = b.position().subtract(e.position()).multiply(1, 0, 1).normalize().scale(0.12);
                        e.push(pull.x, 0, pull.z);
                        e.hurtMarked = true;
                    }
                    if (tick % 4 == 0) {
                        b.hitCircle(level, b.position(), 3.2, 6.0F, 0.6, 0.2);
                    }
                    level.sendParticles(ParticleTypes.NAUTILUS, b.getX(), b.getY() + 1, b.getZ(), 12, 3.0, 0.6, 3.0, 0.4);
                })
                .build());
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (tickCount % 6 == 0) {
            level.sendParticles(ParticleTypes.BUBBLE_POP, getX(), getY() + 3, getZ(), 4, 0.8, 1.2, 0.8, 0.02);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("phase_two_speed"), 0.25,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 0.6F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
    }
}
