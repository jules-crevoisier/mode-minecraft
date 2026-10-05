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
 * Sylvain (Sylvan): gardeners, herbalists, woodwrights and wardens of the Sylvan Palace and the Hollow Giant
 * Tree. Tall and quick; the Sylvan Warden is an archer that keeps 5 to 12 blocks from its foe and looses an arrow at
 * 0.75 s of its draw. Sylvans never take fall damage (they land like cats).
 */
public class Sylvan extends Resident {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 2.05F;

    public Sylvan(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        // the guard role raises health and armour (guardStats); only guards fight, with this damage
        return residentAttributes(0.32)
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ATTACK_DAMAGE, 9.0);
    }

    @Override
    public GeneratedFolk.People people() {
        return GeneratedFolk.SYLVAN;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Sylvan.TICKS;
    }

    @Override
    protected double[] guardStats() {
        return new double[] {30.0, 9.0, 4.0};
    }

    @Override
    protected int attackImpact() {
        return 15;
    }

    @Override
    protected SoundEvent voice() {
        return SoundEvents.ALLAY_AMBIENT_WITHOUT_ITEM;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.75F;
    }

    @Override
    protected boolean archer() {
        return true;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, net.minecraft.world.damagesource.DamageSource source) {
        return false;
    }
}
