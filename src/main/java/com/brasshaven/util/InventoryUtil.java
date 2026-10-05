package com.brasshaven.util;

import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** Sorting, merging and insertion helpers shared by the sorting chest, terminal and key binding. */
public final class InventoryUtil {
    private InventoryUtil() {}

    private static final Comparator<ItemStack> ORDER = Comparator
            .comparing((ItemStack s) -> BuiltInRegistries.ITEM.getKey(s.getItem()).toString())
            .thenComparing(s -> s.getHoverName().getString())
            .thenComparing(ItemStack::getCount, Comparator.reverseOrder());

    /** Merges identical stacks (same item and components) and sorts them. */
    public static List<ItemStack> compactAndSort(List<ItemStack> stacks) {
        List<ItemStack> merged = new ArrayList<>();
        for (ItemStack stack : stacks) {
            if (stack.isEmpty()) {
                continue;
            }
            ItemStack remaining = stack.copy();
            for (ItemStack target : merged) {
                if (remaining.isEmpty()) {
                    break;
                }
                if (ItemStack.isSameItemSameComponents(target, remaining) && target.getCount() < target.getMaxStackSize()) {
                    int move = Math.min(remaining.getCount(), target.getMaxStackSize() - target.getCount());
                    target.grow(move);
                    remaining.shrink(move);
                }
            }
            if (!remaining.isEmpty()) {
                merged.add(remaining);
            }
        }
        merged.sort(ORDER);
        return merged;
    }

    public static void sortContainer(Container container) {
        sortRange(container, 0, container.getContainerSize());
    }

    /** Sorts slots [from, to) of the container in place. */
    public static void sortRange(Container container, int from, int to) {
        List<ItemStack> stacks = new ArrayList<>();
        for (int i = from; i < to; i++) {
            stacks.add(container.getItem(i));
        }
        List<ItemStack> sorted = compactAndSort(stacks);
        for (int i = from; i < to; i++) {
            int k = i - from;
            container.setItem(i, k < sorted.size() ? sorted.get(k) : ItemStack.EMPTY);
        }
        container.setChanged();
    }

    /** Sorts the main inventory of a player (hotbar and armor are left untouched). */
    public static void sortPlayer(Player player) {
        NonNullList<ItemStack> items = player.getInventory().getNonEquipmentItems();
        List<ItemStack> main = new ArrayList<>(items.subList(9, items.size()));
        List<ItemStack> sorted = compactAndSort(main);
        for (int i = 9; i < items.size(); i++) {
            int k = i - 9;
            items.set(i, k < sorted.size() ? sorted.get(k) : ItemStack.EMPTY);
        }
        player.getInventory().setChanged();
    }

    public static boolean contains(Container container, ItemStack like) {
        for (int i = 0; i < container.getContainerSize(); i++) {
            if (ItemStack.isSameItemSameComponents(container.getItem(i), like)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Inserts as much of {@code stack} as possible: first on top of identical stacks, then
     * (unless {@code mergeOnly}) into empty slots. Returns what could not be stored.
     */
    public static ItemStack insert(Container container, ItemStack stack, boolean mergeOnly) {
        ItemStack remaining = stack.copy();
        int size = container.getContainerSize();
        // a container may hold less than a full stack per slot (Container#getMaxStackSize)
        int limit = Math.min(container.getMaxStackSize(remaining), remaining.getMaxStackSize());
        for (int i = 0; i < size && !remaining.isEmpty(); i++) {
            ItemStack target = container.getItem(i);
            if (!target.isEmpty() && ItemStack.isSameItemSameComponents(target, remaining) && target.getCount() < limit) {
                int move = Math.min(remaining.getCount(), limit - target.getCount());
                target.grow(move);
                remaining.shrink(move);
                container.setItem(i, target);
            }
        }
        if (!mergeOnly) {
            for (int i = 0; i < size && !remaining.isEmpty(); i++) {
                if (container.getItem(i).isEmpty() && container.canPlaceItem(i, remaining)) {
                    int move = Math.min(remaining.getCount(), limit);
                    container.setItem(i, remaining.copyWithCount(move));
                    remaining.shrink(move);
                }
            }
        }
        if (remaining.getCount() != stack.getCount()) {
            container.setChanged();
        }
        return remaining;
    }
}
