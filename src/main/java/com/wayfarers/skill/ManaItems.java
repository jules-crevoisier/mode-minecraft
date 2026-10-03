package com.wayfarers.skill;

import com.wayfarers.registry.ModItems;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;

/** Rings and amulets that boost mana just by being carried (no extra equipment slots needed). */
public final class ManaItems {
    private ManaItems() {}

    private static boolean carries(ServerPlayer player, Item item) {
        Inventory inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            if (inv.getItem(i).is(item)) {
                return true;
            }
        }
        return false;
    }

    public static float bonusMana(ServerPlayer player) {
        return carries(player, ModItems.ARCANE_RING.get()) ? 50F : 0F;
    }

    public static float bonusRegen(ServerPlayer player) {
        return carries(player, ModItems.MANA_AMULET.get()) ? 0.5F : 0F;
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
