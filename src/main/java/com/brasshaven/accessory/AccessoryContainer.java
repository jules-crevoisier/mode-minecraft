package com.brasshaven.accessory;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/** The worn accessories of one player (one per player object, held by its {@link AccessorySlot}s). */
public final class AccessoryContainer extends SimpleContainer {
    private final Player owner;
    /** Loading from the saved data: don't write it back while filling. */
    boolean loading;

    AccessoryContainer(Player owner) {
        super(AccessorySlotType.LAYOUT.length);
        this.owner = owner;
    }

    public Player owner() {
        return owner;
    }

    public AccessorySlotType type(int slot) {
        return AccessorySlotType.LAYOUT[slot];
    }

    @Override
    public int getMaxStackSize() {
        return 1;
    }

    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        return slot >= 0 && slot < getContainerSize() && type(slot).fits(stack);
    }

    @Override
    public boolean stillValid(Player player) {
        return player == owner;
    }

    @Override
    public void setChanged() {
        super.setChanged();
        if (!loading && owner instanceof ServerPlayer sp) {
            Accessories.save(sp, this);
        }
    }
}
