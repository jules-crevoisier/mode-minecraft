package com.wayfarers.util;

import com.wayfarers.block.MachineBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * The chests a Guild Terminal sees: every container (chest, barrel, sorting chest, shulker box...) within
 * {@link #RANGE} blocks. No cables, no power: put the terminal in your storage room and it works.
 */
public final class StorageNetwork {
    public static final int RANGE = 12;

    /** An item type and how many of it the network holds. */
    public record Entry(ItemStack type, int count) {}

    private record Key(ItemStack stack) {
        @Override
        public boolean equals(Object o) {
            return o instanceof Key k && ItemStack.isSameItemSameComponents(stack, k.stack);
        }

        @Override
        public int hashCode() {
            return ItemStack.hashItemAndComponents(stack);
        }
    }

    private StorageNetwork() {}

    public static List<Container> containers(ServerLevel level, BlockPos center) {
        List<Container> result = new ArrayList<>();
        for (BlockPos p : BlockPos.betweenClosed(center.offset(-RANGE, -RANGE / 2, -RANGE), center.offset(RANGE, RANGE / 2, RANGE))) {
            BlockEntity be = level.getBlockEntity(p);
            // machine buffers are not storage (a block placer would place whatever got stored in it)
            if (be instanceof BaseContainerBlockEntity container && container.getContainerSize() >= 9
                    && !(be instanceof MachineBlockEntity)) {
                result.add(container);
            }
        }
        return result;
    }

    /** Every item type in the network with its total count, most plentiful first. */
    public static List<Entry> contents(List<Container> containers) {
        Map<Key, Integer> totals = new LinkedHashMap<>();
        for (Container c : containers) {
            for (int i = 0; i < c.getContainerSize(); i++) {
                ItemStack s = c.getItem(i);
                if (!s.isEmpty()) {
                    totals.merge(new Key(s.copyWithCount(1)), s.getCount(), Integer::sum);
                }
            }
        }
        List<Entry> list = new ArrayList<>();
        totals.forEach((k, v) -> list.add(new Entry(k.stack, v)));
        list.sort(Comparator.comparingInt(Entry::count).reversed());
        return list;
    }

    /** Removes up to {@code amount} items like {@code type} from the network and returns them as one stack. */
    public static ItemStack extract(List<Container> containers, ItemStack type, int amount) {
        int want = Math.min(amount, type.getMaxStackSize());
        ItemStack out = ItemStack.EMPTY;
        for (Container c : containers) {
            for (int i = 0; i < c.getContainerSize() && want > 0; i++) {
                ItemStack s = c.getItem(i);
                if (!s.isEmpty() && ItemStack.isSameItemSameComponents(s, type)) {
                    int take = Math.min(want, s.getCount());
                    if (out.isEmpty()) {
                        out = s.copyWithCount(take);
                    } else {
                        out.grow(take);
                    }
                    s.shrink(take);
                    c.setItem(i, s.isEmpty() ? ItemStack.EMPTY : s);
                    want -= take;
                }
            }
            c.setChanged();
            if (want <= 0) {
                break;
            }
        }
        return out;
    }

    /** Puts {@code stack} into the network (onto matching stacks first, then empty slots); returns what's left. */
    public static ItemStack insert(List<Container> containers, ItemStack stack) {
        ItemStack rest = stack;
        for (Container c : containers) {
            if (InventoryUtil.contains(c, rest)) {
                rest = InventoryUtil.insert(c, rest, false);
                c.setChanged();
                if (rest.isEmpty()) {
                    return ItemStack.EMPTY;
                }
            }
        }
        for (Container c : containers) {
            rest = InventoryUtil.insert(c, rest, false);
            c.setChanged();
            if (rest.isEmpty()) {
                return ItemStack.EMPTY;
            }
        }
        return rest;
    }
}
