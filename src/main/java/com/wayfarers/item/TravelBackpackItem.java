package com.wayfarers.item;

import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
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
            player.openMenu(new SimpleMenuProvider((id, inventory, p) -> ChestMenu.threeRows(id, inventory, container),
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
}
