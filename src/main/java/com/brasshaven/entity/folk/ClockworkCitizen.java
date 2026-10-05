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
 * Citoyen mécanique (Clockwork Citizen): gearwrights, mechanics, chronometrists and sentinels of the Clockwork
 * Citadel. Made of brass: it never drowns, and the sentinel's piston punch (lands at 0.5 s) throws its foe back.
 */
public class ClockworkCitizen extends Resident {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 1.95F;

    public ClockworkCitizen(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        // the guard role raises health and armour (guardStats); only guards fight, with this damage
        return residentAttributes(0.26)
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0);
    }

    @Override
    public GeneratedFolk.People people() {
        return GeneratedFolk.CLOCKWORK_CITIZEN;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ClockworkCitizen.TICKS;
    }

    @Override
    protected double[] guardStats() {
        return new double[] {50.0, 8.0, 10.0};
    }

    @Override
    protected int attackImpact() {
        return 10;
    }

    @Override
    protected SoundEvent voice() {
        return SoundEvents.COPPER_GOLEM_SPIN;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.1F;
    }

    @Override
    protected double knockback() {
        return 1.0;
    }

    @Override
    protected int decreaseAirSupply(int currentSupply) {
        return currentSupply;
    }

    @Override
    protected SoundEvent getHurtSound(net.minecraft.world.damagesource.DamageSource source) {
        return SoundEvents.COPPER_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.COPPER_GOLEM_DEATH;
    }

    @Override
    protected void playStepSound(net.minecraft.core.BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
        playSound(SoundEvents.COPPER_GOLEM_STEP, 0.3F, 1.2F);
    }
}
