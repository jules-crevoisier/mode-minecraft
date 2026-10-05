package com.brasshaven.util;

import com.brasshaven.block.GuildTerminalBlock;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * The storage buttons added to every container screen (Quark / Inventory Profiles style):
 * sort the container, take everything, deposit the items it already holds, and quick-stack the whole
 * inventory into nearby chests (Terraria style). All of it runs on the server through the open menu.
 */
public final class ContainerActions {
    public enum Action { SORT_CONTAINER, SORT_PLAYER, TAKE_ALL, DEPOSIT_MATCHING, QUICK_STACK_NEARBY }

    public static final int NEARBY_RANGE = 8;

    private ContainerActions() {}

    public static void run(ServerPlayer player, Action action) {
        AbstractContainerMenu menu = player.containerMenu;
        // a container broken (or left) since the screen opened: vanilla closes the menu on the player's next tick,
        // a click arriving before that must not move items in or out of it
        if (!(menu instanceof InventoryMenu) && !menu.stillValid(player)) {
            return;
        }
        switch (action) {
            case SORT_PLAYER -> InventoryUtil.sortPlayer(player);
            case SORT_CONTAINER -> {
                if (menu instanceof InventoryMenu) {
                    InventoryUtil.sortPlayer(player);
                } else {
                    sortContainer(menu, player);
                }
            }
            case TAKE_ALL -> {
                for (Slot slot : menu.slots) {
                    if (!isPlayerSlot(slot, player) && slot.hasItem() && slot.mayPickup(player)) {
                        menu.quickMoveStack(player, slot.index);
                    }
                }
            }
            case DEPOSIT_MATCHING -> {
                List<ItemStack> present = new ArrayList<>();
                for (Slot slot : menu.slots) {
                    if (!isPlayerSlot(slot, player) && slot.hasItem()) {
                        present.add(slot.getItem());
                    }
                }
                for (Slot slot : menu.slots) {
                    if (isPlayerSlot(slot, player) && slot.getContainerSlot() >= Inventory.getSelectionSize()
                            && slot.getContainerSlot() < 36 && slot.hasItem()
                            && present.stream().anyMatch(p -> ItemStack.isSameItemSameComponents(p, slot.getItem()))) {
                        menu.quickMoveStack(player, slot.index);
                    }
                }
            }
            case QUICK_STACK_NEARBY -> {
                int range = com.brasshaven.config.BrasshavenConfig.QUICK_STACK_RANGE.get();
                if (range <= 0) {
                    return;
                }
                ServerLevel level = player.level();
                List<Container> chests = new ArrayList<>();
                for (Container c : GuildTerminalBlock.nearbyStorage(level, player.blockPosition(), range + 1)) {
                    if (c instanceof net.minecraft.world.level.block.entity.BlockEntity be
                            && be.getBlockPos().closerToCenterThan(player.position(), range + 1)) {
                        chests.add(c);
                    }
                }
                int[] result = GuildTerminalBlock.deposit(player, chests);
                player.sendOverlayMessage(Component.translatable("message.brasshaven.quick_stack", result[0], result[1])
                        .withStyle(ChatFormatting.GOLD));
            }
        }
        menu.broadcastChanges();
        player.level().playSound(null, player, SoundEvents.BUNDLE_INSERT, SoundSource.PLAYERS, 0.5F, 1.1F);
    }

    private static boolean isPlayerSlot(Slot slot, ServerPlayer player) {
        return slot.container == player.getInventory();
    }

    /** Merges and sorts the stacks of every non-player slot of the open menu, in place. */
    private static void sortContainer(AbstractContainerMenu menu, ServerPlayer player) {
        List<Slot> slots = new ArrayList<>();
        List<ItemStack> stacks = new ArrayList<>();
        for (Slot slot : menu.slots) {
            if (!isPlayerSlot(slot, player) && slot.mayPickup(player)) {
                slots.add(slot);
                if (slot.hasItem()) {
                    stacks.add(slot.getItem().copy());
                }
            }
        }
        if (slots.isEmpty()) {
            return;
        }
        // only sort plain storage: every slot must accept any item (skips furnaces, brewing stands...)
        for (Slot slot : slots) {
            if (!slot.mayPlace(new ItemStack(net.minecraft.world.item.Items.COBBLESTONE))) {
                return;
            }
        }
        List<ItemStack> sorted = InventoryUtil.compactAndSort(stacks);
        // never lose an item: every sorted stack must have a slot that takes a stack that big
        if (sorted.size() > slots.size()) {
            return;
        }
        for (int i = 0; i < sorted.size(); i++) {
            if (slots.get(i).getMaxStackSize(sorted.get(i)) < sorted.get(i).getCount()) {
                return;
            }
        }
        for (int i = 0; i < slots.size(); i++) {
            slots.get(i).set(i < sorted.size() ? sorted.get(i) : ItemStack.EMPTY);
        }
    }
}
