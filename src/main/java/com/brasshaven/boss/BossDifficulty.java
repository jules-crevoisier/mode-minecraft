package com.brasshaven.boss;

import com.brasshaven.Brasshaven;
import com.brasshaven.item.BossWeaponItem;
import com.brasshaven.registry.ModItems;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraftforge.event.AnvilUpdateEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;

import java.util.function.Consumer;

/**
 * Server hooks of the boss difficulty pass: every hit a boss deals (melee, moves, waves, its projectiles) is scaled by
 * its co-op / NG+ multiplier, and the Ember of Ascension upgrades a boss weapon on an anvil.
 */
public final class BossDifficulty {
    /** Most Embers of Ascension one weapon takes (+1 attack damage each). */
    public static final int MAX_ASCENSION = 5;
    public static final Identifier ASCENSION = Brasshaven.id("ascension");

    private BossDifficulty() {}

    public static void register() {
        LivingHurtEvent.BUS.addListener((Consumer<LivingHurtEvent>) e -> {
            if (e.getSource().getEntity() instanceof WayfarerBoss boss && !(e.getEntity() instanceof WayfarerBoss)) {
                float m = boss.damageMultiplier();
                if (m != 1.0F) {
                    e.setAmount(e.getAmount() * m);
                }
            }
        });
        AnvilUpdateEvent.BUS.addListener((Consumer<AnvilUpdateEvent>) BossDifficulty::anvil);
    }

    /** Current ascension level of a boss weapon (0 when never upgraded). */
    public static int ascension(ItemStack stack) {
        ItemAttributeModifiers mods = stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
        for (ItemAttributeModifiers.Entry entry : mods.modifiers()) {
            if (entry.matches(Attributes.ATTACK_DAMAGE, ASCENSION)) {
                return (int) Math.round(entry.modifier().amount());
            }
        }
        return 0;
    }

    private static void anvil(AnvilUpdateEvent e) {
        ItemStack left = e.getLeft();
        ItemStack right = e.getRight();
        if (!(left.getItem() instanceof BossWeaponItem) || !right.is(ModItems.EMBER_OF_ASCENSION.get())) {
            return;
        }
        int level = ascension(left);
        if (level >= MAX_ASCENSION) {
            return;
        }
        ItemStack out = left.copy();
        ItemAttributeModifiers mods = out.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
        out.set(DataComponents.ATTRIBUTE_MODIFIERS, mods.withModifierAdded(Attributes.ATTACK_DAMAGE,
                new AttributeModifier(ASCENSION, level + 1, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND));
        e.setOutput(out);
        e.setCost(5L + 3L * level);
        e.setMaterialCost(1);
    }
}
