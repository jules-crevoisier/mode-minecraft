package com.brasshaven.colossal;

import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;

import java.util.Locale;

/** The six vault armour sets; {@link #worn} counts the pieces of a set a player has on (2 and 4 unlock its bonuses). */
public enum ColossalSet {
    LOCKKEEPER("ga"), TURBINE_ENGINEER("dd"), BOG_PILGRIM("mire"), SUN_PRIEST("sz"), IRONCLAD("dw"), CANOPY_STALKER("cc");

    private static final EquipmentSlot[] SLOTS = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};

    /** The structure key of the tooltip ("Relic of the Great Aqueduct", tooltip.brasshaven.relic.&lt;key&gt;). */
    public final String structure;

    ColossalSet(String structure) {
        this.structure = structure;
    }

    /** The set prefix of the item ids and lang keys (lockkeeper, turbine_engineer...). */
    public String prefix() {
        return name().toLowerCase(Locale.ROOT);
    }

    public int worn(Player player) {
        int n = 0;
        for (EquipmentSlot slot : SLOTS) {
            Item item = player.getItemBySlot(slot).getItem();
            if (item instanceof ColossalArmorItem armor && armor.set() == this) {
                n++;
            }
        }
        return n;
    }
}
