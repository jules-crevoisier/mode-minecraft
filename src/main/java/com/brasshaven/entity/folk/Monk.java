package com.brasshaven.entity.folk;

import com.brasshaven.generated.GeneratedFolk;
import com.brasshaven.generated.MobAnims;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;

/**
 * Moine (Monk): scribes, healers, cooks and staff-wielding wardens of the Mountain Monastery. The warden's
 * staff sweep (lands at 0.5 s) knocks back far; monks shrug off the cold of the peaks (no freezing).
 */
public class Monk extends Resident {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.95F;

    public Monk(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        // the guard role raises health and armour (guardStats); only guards fight, with this damage
        return residentAttributes(0.3)
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0);
    }

    @Override
    public GeneratedFolk.People people() {
        return GeneratedFolk.MONK;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Monk.TICKS;
    }

    @Override
    protected double[] guardStats() {
        return new double[] {36.0, 6.0, 4.0};
    }

    @Override
    protected int attackImpact() {
        return 10;
    }

    @Override
    protected SoundEvent voice() {
        return SoundEvents.VILLAGER_AMBIENT;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.9F;
    }

    @Override
    protected double knockback() {
        return 0.9;
    }

    @Override
    public boolean canFreeze() {
        return false;
    }
}
