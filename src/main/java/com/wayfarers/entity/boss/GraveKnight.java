package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;

import java.util.List;

/** Le Chevalier des tombes (The Grave Knight): champion at the bottom of the Catacombes oubliées. */
public class GraveKnight extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.6F;

    public GraveKnight(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 240.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 9.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.GraveKnight.TICKS;
    }

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        out.add(BossAttack.of("strike").timing(14, 3, 12).range(0, 4.5).cooldown(20)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.0, 60, ParticleTypes.CRIT);
                    }
                })
                .impact((b, level, t, tick) -> b.hitArc(level, 4.5, 70, 11.0F, 1.0))
                .build());
    }
}
