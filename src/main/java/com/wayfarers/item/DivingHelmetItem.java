package com.wayfarers.item;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/**
 * Casque de scaphandre (Diving Helmet): a brass dome with a glass porthole. Worn with the head under water it gives
 * Conduit Power, like standing next to a conduit: water breathing, clear sight under water and full mining speed.
 * (Its attribute modifiers also remove the underwater mining penalty, see ModOcean.)
 */
public class DivingHelmetItem extends TooltipItem {
    public DivingHelmetItem(Properties properties) {
        super(properties);
    }

    @Override
    public void inventoryTick(ItemStack stack, ServerLevel level, Entity owner, @Nullable EquipmentSlot slot) {
        super.inventoryTick(stack, level, owner, slot);
        if (slot == EquipmentSlot.HEAD && owner instanceof LivingEntity living && owner.tickCount % 20 == 0
                && living.isEyeInFluid(FluidTags.WATER)) {
            // top it up only when it runs low: every refresh is an effect packet to the client (and a conduit
            // nearby already keeps it topped up)
            MobEffectInstance current = living.getEffect(MobEffects.CONDUIT_POWER);
            if (current == null || current.endsWithin(200)) {
                living.addEffect(new MobEffectInstance(MobEffects.CONDUIT_POWER, 260, 0, true, false, true));
            }
        }
    }
}
