package com.brasshaven.item;

import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemContainerContents;
import net.minecraft.world.level.Level;

/** Portable slots stored on the item itself (vanilla container component): 27, or 54 for the Explorer's Backpack. */
public class TravelBackpackItem extends TooltipItem {
    private final int rows;

    public TravelBackpackItem(Properties properties) {
        this(properties, 3);
    }

    public TravelBackpackItem(Properties properties, int rows) {
        super(properties);
        this.rows = rows;
    }

    /**
     * A backpack never goes into a shulker box or a bundle. Backpacks may hold shulker boxes, so without this a
     * backpack of shulker boxes of backpacks... nests without end: a single item could grow past what a packet or a
     * chunk can carry (an "NBT bomb" that kicks players or corrupts the chunk it lies in).
     */
    @Override
    public boolean canFitInsideContainerItems() {
        return false;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack backpack = player.getItemInHand(hand);
        if (!level.isClientSide()) {
            BackpackContainer container = new BackpackContainer(backpack, rows * 9);
            player.openMenu(new SimpleMenuProvider((id, inventory, p) -> new BackpackMenu(id, inventory, container, backpack, rows),
                    backpack.getHoverName()));
            level.playSound(null, player, SoundEvents.ARMOR_EQUIP_LEATHER.value(), SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }

    /** Writes every change straight back into the backpack's container component. */
    static final class BackpackContainer extends SimpleContainer {
        private final ItemStack backpack;

        BackpackContainer(ItemStack backpack, int size) {
            super(size);
            this.backpack = backpack;
            NonNullList<ItemStack> items = NonNullList.withSize(size, ItemStack.EMPTY);
            backpack.getOrDefault(DataComponents.CONTAINER, ItemContainerContents.EMPTY).copyInto(items);
            for (int i = 0; i < size; i++) {
                super.setItem(i, items.get(i));
            }
        }

        @Override
        public void setChanged() {
            super.setChanged();
            backpack.set(DataComponents.CONTAINER, ItemContainerContents.fromItems(getItems()));
        }

        @Override
        public boolean canPlaceItem(int slot, ItemStack stack) {
            return !(stack.getItem() instanceof TravelBackpackItem) && !containsBackpack(stack);
        }

        @Override
        public boolean stillValid(Player player) {
            return !backpack.isEmpty() && (player.getMainHandItem() == backpack || player.getOffhandItem() == backpack);
        }
    }

    /** What may never go inside a backpack: a backpack, or a container item (shulker box...) holding one. */
    private static boolean isBackpack(ItemStack stack) {
        return stack.getItem() instanceof TravelBackpackItem || containsBackpack(stack);
    }

    /** A container item (shulker box made before backpacks were kept out of them) that holds a backpack. */
    static boolean containsBackpack(ItemStack stack) {
        ItemContainerContents contents = stack.get(DataComponents.CONTAINER);
        if (contents == null) {
            return false;
        }
        for (var inside : contents.nonEmptyItems()) {
            if (inside.item().value() instanceof TravelBackpackItem) {
                return true;
            }
        }
        return false;
    }

    /**
     * A plain 3-row chest menu that never lets a backpack go inside a backpack, and never moves the
     * backpack that is open (vanilla chest slots ignore {@code canPlaceItem}).
     */
    static final class BackpackMenu extends ChestMenu {
        private final ItemStack backpack;
        private final int size;

        BackpackMenu(int id, Inventory inventory, Container container, ItemStack backpack, int rows) {
            super(rows == 6 ? MenuType.GENERIC_9x6 : MenuType.GENERIC_9x3, id, inventory, container, rows);
            this.backpack = backpack;
            this.size = rows * 9;
        }

        @Override
        public void clicked(int slotIndex, int button, ContainerInput input, Player player) {
            ItemStack swapped = input == ContainerInput.SWAP && button >= 0 && button < player.getInventory().getContainerSize()
                    ? player.getInventory().getItem(button) : ItemStack.EMPTY;
            if (swapped == backpack) {
                return;
            }
            if (slotIndex >= 0 && slotIndex < slots.size()) {
                if (slots.get(slotIndex).getItem() == backpack) {
                    return;
                }
                boolean intoBackpack = slotIndex < size;
                if (intoBackpack && (isBackpack(getCarried()) || isBackpack(swapped))) {
                    return;
                }
            }
            super.clicked(slotIndex, button, input, player);
        }

        @Override
        public ItemStack quickMoveStack(Player player, int slotIndex) {
            if (slotIndex >= size && isBackpack(slots.get(slotIndex).getItem())) {
                return ItemStack.EMPTY;
            }
            return super.quickMoveStack(player, slotIndex);
        }
    }
}
