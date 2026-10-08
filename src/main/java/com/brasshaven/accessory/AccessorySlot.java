package com.brasshaven.accessory;

import net.minecraft.resources.Identifier;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/** One accessory slot of the player's inventory menu: takes one item of its kind, shows a silhouette when empty. */
public class AccessorySlot extends Slot {
    /** Client only: the slots are hidden (the recipe book covers the place where they are drawn). */
    public static volatile boolean hidden;

    public final AccessorySlotType type;
    public final AccessoryContainer accessories;

    public AccessorySlot(AccessoryContainer container, int slot, int x, int y) {
        super(container, slot, x, y);
        this.accessories = container;
        this.type = container.type(slot);
    }

    @Override
    public boolean mayPlace(ItemStack stack) {
        return type.fits(stack);
    }

    @Override
    public int getMaxStackSize() {
        return 1;
    }

    @Override
    public int getMaxStackSize(ItemStack stack) {
        return 1;
    }

    @Override
    public @Nullable Identifier getNoItemIcon() {
        return type.icon;
    }

    @Override
    public boolean isActive() {
        return !hidden;
    }
}
