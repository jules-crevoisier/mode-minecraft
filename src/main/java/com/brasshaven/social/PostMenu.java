package com.brasshaven.social;

import com.brasshaven.registry.ModSocial;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * An open Pneumatic Post: the 6 slots of the parcel being written (real items, given back when the screen closes
 * without sending) and the player's inventory. The inbox and the send / take / discard actions go through
 * {@link SocialNet.PostAction}, checked against this menu (same id, still in reach of the block).
 */
public class PostMenu extends AbstractContainerMenu {
    public static final int W = 330;
    public static final int H = 226;
    public static final int ATTACH = 6;
    public static final int ATTACH_X = 224;
    public static final int ATTACH_Y = 52;
    public static final int INV_X = (W - 162) / 2;
    public static final int INV_Y = 144;
    /** Client only: the parcel slots show while the "Write" tab is open. */
    public static boolean composing;

    final SimpleContainer parcel = new SimpleContainer(ATTACH);
    private final ContainerLevelAccess access;
    private final boolean client;
    public final BlockPos pos;

    public PostMenu(int id, Inventory inv, BlockPos pos) {
        super(ModSocial.POST.get(), id);
        this.pos = pos;
        this.client = inv.player.level().isClientSide();
        this.access = client ? ContainerLevelAccess.NULL : ContainerLevelAccess.create(inv.player.level(), pos);
        for (int i = 0; i < ATTACH; i++) {
            addSlot(new Slot(parcel, i, ATTACH_X + (i % 3) * 18, ATTACH_Y + (i / 3) * 18) {
                @Override
                public boolean isActive() {
                    return !client || composing;
                }
            });
        }
        addStandardInventorySlots(inv, INV_X, INV_Y);
    }

    public boolean isParcelSlot(Slot slot) {
        return slot.index < ATTACH;
    }

    /** Non-empty stacks of the parcel, copied. */
    List<ItemStack> attachments() {
        List<ItemStack> out = new ArrayList<>();
        for (int i = 0; i < ATTACH; i++) {
            if (!parcel.getItem(i).isEmpty()) {
                out.add(parcel.getItem(i).copy());
            }
        }
        return out;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (isParcelSlot(slot)) {
            if (!moveItemStackTo(stack, ATTACH, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (!moveItemStackTo(stack, 0, ATTACH, false)) {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) {
            slot.setByPlayer(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        if (stack.getCount() == copy.getCount()) {
            return ItemStack.EMPTY;
        }
        slot.onTake(player, stack);
        return copy;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, ModSocial.PNEUMATIC_POST.get());
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        if (!client && player instanceof ServerPlayer sp) {
            List<ItemStack> back = attachments();
            parcel.clearContent();
            Social.giveOrMail(sp, back, "returned");
        }
    }
}
