package com.brasshaven.entity.folk;

import com.brasshaven.generated.GeneratedFolk;
import com.brasshaven.generated.MobAnims;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.level.Level;

/**
 * Nain (Dwarf): smiths, miners, brewers, gemcutters and horned-helm guards of the Deep Dwarven City and the
 * dwarven mines. Short, broad and sturdy: the guard's two-handed axe chop (lands at 0.55 s) knocks back hard.
 */
public class Dwarf extends Resident {
    public static final float WIDTH = 0.8F;
    public static final float HEIGHT = 1.4F;

    public Dwarf(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return residentAttributes(24.0, 0.27);
    }

    @Override
    public GeneratedFolk.People people() {
        return GeneratedFolk.DWARF;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Dwarf.TICKS;
    }

    @Override
    protected double[] guardStats() {
        return new double[] {40.0, 7.0, 8.0};
    }

    @Override
    protected int attackImpact() {
        return 11;
    }

    @Override
    protected SoundEvent voice() {
        return SoundEvents.VILLAGER_AMBIENT;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.72F;
    }

    @Override
    protected double knockback() {
        return 0.7;
    }
}
