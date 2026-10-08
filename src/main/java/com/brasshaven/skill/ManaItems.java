package com.brasshaven.skill;

import com.brasshaven.event.EquipmentEvents;
import com.brasshaven.registry.ModItems;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;

/** Mana from gear: worn rings and amulets (accessory slots) and armour sets. */
public final class ManaItems {
    private ManaItems() {}

    /** Rings and amulets only count while worn in their accessory slot (accessory/Accessories). */
    private static boolean wears(ServerPlayer player, Item item) {
        return com.brasshaven.accessory.Accessories.wears(player, item);
    }

    public static float bonusMana(ServerPlayer player) {
        EquipmentEvents.ArmorSet set = EquipmentEvents.fullSet(player);
        float armor = set == EquipmentEvents.ArmorSet.ARCANE ? 100F : set == EquipmentEvents.ArmorSet.AETHER ? 75F : 0F;
        return (wears(player, ModItems.ARCANE_RING.get()) ? 50F : 0F) + armor;
    }

    public static float bonusRegen(ServerPlayer player) {
        float armor = EquipmentEvents.fullSet(player) == EquipmentEvents.ArmorSet.AETHER ? 1F : 0F;
        return (wears(player, ModItems.MANA_AMULET.get()) ? 0.5F : 0F) + armor;
    }

    /** Extra spell power from gear (the Arcanist robes). */
    public static float bonusPower(ServerPlayer player) {
        return EquipmentEvents.fullSet(player) == EquipmentEvents.ArmorSet.ARCANE ? 0.25F : 0F;
    }

    /** Spends mana for a spell (after the Thrift discount); false when there isn't enough. */
    public static boolean spend(ServerPlayer player, float cost) {
        if (player.isCreative()) {
            return true;
        }
        float real = cost * PlayerSkills.costMultiplier(player);
        float mana = PlayerSkills.mana(player);
        if (mana < real) {
            return false;
        }
        PlayerSkills.setMana(player, mana - real);
        SkillEvents.sync(player);
        return true;
    }
}
