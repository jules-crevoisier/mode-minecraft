package com.brasshaven.social;

import com.brasshaven.registry.ModSocial;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * An open Contract Board: a sample slot for the item wanted (a copy, never the real item: click with an item to set
 * it, with an empty hand to clear it), 6 reward slots (real items, escrowed when the contract is posted, given back
 * when the screen closes without posting) and the player's inventory. The list and the post / deliver / cancel
 * actions go through {@link SocialNet.BoardAction}, checked against this menu.
 */
public class ContractMenu extends AbstractContainerMenu {
    public static final int W = PostMenu.W;
    public static final int H = PostMenu.H;
    public static final int WANT_X = 196;
    public static final int WANT_Y = 54;
    public static final int REWARD = 6;
    public static final int REWARD_X = 196;
    public static final int REWARD_Y = 92;
    public static final int INV_X = PostMenu.INV_X;
    public static final int INV_Y = PostMenu.INV_Y;
    /** Client only: the slots show while the "Post a contract" tab is open. */
    public static boolean posting;

    final SimpleContainer wanted = new SimpleContainer(1);
    final SimpleContainer reward = new SimpleContainer(REWARD);
    private final ContainerLevelAccess access;
    private final boolean client;
    public final BlockPos pos;

    public ContractMenu(int id, Inventory inv, BlockPos pos) {
        super(ModSocial.CONTRACT_BOARD.get(), id);
        this.pos = pos;
        this.client = inv.player.level().isClientSide();
        this.access = client ? ContainerLevelAccess.NULL : ContainerLevelAccess.create(inv.player.level(), pos);
        addSlot(new Slot(wanted, 0, WANT_X, WANT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }

            @Override
            public boolean mayPickup(Player player) {
                return false;
            }

            @Override
            public boolean isActive() {
                return !client || posting;
            }
        });
        for (int i = 0; i < REWARD; i++) {
            addSlot(new Slot(reward, i, REWARD_X + (i % 3) * 18, REWARD_Y + (i / 3) * 18) {
                @Override
                public boolean isActive() {
                    return !client || posting;
                }
            });
        }
        addStandardInventorySlots(inv, INV_X, INV_Y);
    }

    public boolean isWantedSlot(Slot slot) {
        return slot.index == 0;
    }

    public boolean isRewardSlot(Slot slot) {
        return slot.index >= 1 && slot.index <= REWARD;
    }

    public ItemStack wantedItem() {
        return wanted.getItem(0);
    }

    List<ItemStack> rewards() {
        List<ItemStack> out = new ArrayList<>();
        for (int i = 0; i < REWARD; i++) {
            if (!reward.getItem(i).isEmpty()) {
                out.add(reward.getItem(i).copy());
            }
        }
        return out;
    }

    @Override
    public void clicked(int slotIndex, int button, ContainerInput action, Player player) {
        if (slotIndex == 0) {
            // the sample: a copy of the carried item (one, undamaged), never the item itself
            if (action == ContainerInput.PICKUP || action == ContainerInput.QUICK_MOVE) {
                ItemStack carried = getCarried();
                wanted.setItem(0, carried.isEmpty() || action == ContainerInput.QUICK_MOVE ? ItemStack.EMPTY : Contracts.sample(carried));
            }
            return;
        }
        super.clicked(slotIndex, button, action, player);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem() || isWantedSlot(slot)) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (isRewardSlot(slot)) {
            if (!moveItemStackTo(stack, 1 + REWARD, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (!moveItemStackTo(stack, 1, 1 + REWARD, false)) {
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
    public boolean canTakeItemForPickAll(ItemStack carried, Slot target) {
        return !isWantedSlot(target) && super.canTakeItemForPickAll(carried, target);
    }

    @Override
    public boolean canDragTo(Slot slot) {
        return !isWantedSlot(slot);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, ModSocial.CONTRACT_BOARD_BLOCK.get());
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        if (!client && player instanceof ServerPlayer sp) {
            List<ItemStack> back = rewards();
            reward.clearContent();
            wanted.clearContent();
            Social.giveOrMail(sp, back, "returned");
        }
    }
}
