package com.wayfarers.item;

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

/** 27 portable slots stored on the item itself (vanilla container component). */
public class TravelBackpackItem extends TooltipItem {
    public static final int SIZE = 27;

    public TravelBackpackItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack backpack = player.getItemInHand(hand);
        if (!level.isClientSide()) {
            BackpackContainer container = new BackpackContainer(backpack);
            player.openMenu(new SimpleMenuProvider((id, inventory, p) -> new BackpackMenu(id, inventory, container, backpack),
                    backpack.getHoverName()));
            level.playSound(null, player, SoundEvents.ARMOR_EQUIP_LEATHER.value(), SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }

    /** Writes every change straight back into the backpack's container component. */
    static final class BackpackContainer extends SimpleContainer {
        private final ItemStack backpack;

        BackpackContainer(ItemStack backpack) {
            super(SIZE);
            this.backpack = backpack;
            NonNullList<ItemStack> items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
            backpack.getOrDefault(DataComponents.CONTAINER, ItemContainerContents.EMPTY).copyInto(items);
            for (int i = 0; i < SIZE; i++) {
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
            return !(stack.getItem() instanceof TravelBackpackItem);
        }

        @Override
        public boolean stillValid(Player player) {
            return !backpack.isEmpty() && (player.getMainHandItem() == backpack || player.getOffhandItem() == backpack);
        }
    }

    private static boolean isBackpack(ItemStack stack) {
        return stack.getItem() instanceof TravelBackpackItem;
    }

    /**
     * A plain 3-row chest menu that never lets a backpack go inside a backpack, and never moves the
     * backpack that is open (vanilla chest slots ignore {@code canPlaceItem}).
     */
    static final class BackpackMenu extends ChestMenu {
        private final ItemStack backpack;

        BackpackMenu(int id, Inventory inventory, Container container, ItemStack backpack) {
            super(MenuType.GENERIC_9x3, id, inventory, container, 3);
            this.backpack = backpack;
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
                boolean intoBackpack = slotIndex < SIZE;
                if (intoBackpack && (isBackpack(getCarried()) || isBackpack(swapped))) {
                    return;
                }
            }
            super.clicked(slotIndex, button, input, player);
        }

        @Override
        public ItemStack quickMoveStack(Player player, int slotIndex) {
            if (slotIndex >= SIZE && isBackpack(slots.get(slotIndex).getItem())) {
                return ItemStack.EMPTY;
            }
            return super.quickMoveStack(player, slotIndex);
        }
    }
}
