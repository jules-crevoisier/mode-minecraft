package com.wayfarers.menu;

import com.wayfarers.chisel.ChiselFamilies;
import com.wayfarers.registry.ModBlocks;
import com.wayfarers.registry.ModMenus;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;

/**
 * The Chisel Table: put a stack of blocks in the input slot, every variant of its chisel family appears on the
 * right; click one to turn the whole stack into it, for free. Both sides compute the variants (the families are
 * synced to clients), the server's result wins.
 */
public class ChiselTableMenu extends AbstractContainerMenu {
    public static final int INPUT_X = 26;
    public static final int INPUT_Y = 44;
    public static final int GRID_X = 66;
    public static final int GRID_Y = 26;
    public static final int COLS = 5;
    public static final int ROWS = 3;
    public static final int VARIANTS = COLS * ROWS;
    public static final int INV_X = 17;
    public static final int INV_Y = 104;
    private static final int INPUT_SLOT = 0;
    private static final int FIRST_VARIANT = 1;
    private static final int FIRST_INV = FIRST_VARIANT + VARIANTS;

    private final ContainerLevelAccess access;
    private final Level level;
    private final Container input = new SimpleContainer(1) {
        @Override
        public void setChanged() {
            super.setChanged();
            slotsChanged(this);
        }
    };
    private final SimpleContainer variants = new SimpleContainer(VARIANTS);
    private int familySize;

    public ChiselTableMenu(int id, Inventory inv, BlockPos pos) {
        super(ModMenus.CHISEL_TABLE.get(), id);
        this.level = inv.player.level();
        this.access = ContainerLevelAccess.create(level, pos);
        addSlot(new Slot(input, 0, INPUT_X, INPUT_Y));
        for (int i = 0; i < VARIANTS; i++) {
            addSlot(new Slot(variants, i, GRID_X + (i % COLS) * 18, GRID_Y + (i / COLS) * 18) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;
                }

                @Override
                public boolean mayPickup(Player player) {
                    return false;
                }
            });
        }
        addStandardInventorySlots(inv, INV_X, INV_Y);
    }

    /** How many variants the current input has (0 when it cannot be chiselled). */
    public int familySize() {
        return familySize;
    }

    public boolean hasInput() {
        return !input.getItem(0).isEmpty();
    }

    public boolean isVariantSlot(Slot slot) {
        return slot.index >= FIRST_VARIANT && slot.index < FIRST_INV;
    }

    /** Whether this variant slot shows the item already in the input. */
    public boolean isCurrent(Slot slot) {
        return isVariantSlot(slot) && slot.hasItem() && slot.getItem().is(input.getItem(0).getItem());
    }

    @Override
    public void slotsChanged(Container container) {
        if (container == input) {
            refreshVariants();
        }
        super.slotsChanged(container);
    }

    private void refreshVariants() {
        variants.clearContent();
        familySize = 0;
        ChiselFamilies.Family family = ChiselFamilies.family(level, input.getItem(0));
        if (family == null) {
            return;
        }
        int i = 0;
        for (Block b : family.blocks()) {
            Item item = b.asItem();
            if (item != net.minecraft.world.item.Items.AIR && i < VARIANTS) {
                variants.setItem(i++, new ItemStack(item));
            }
        }
        familySize = i;
    }

    @Override
    public void clicked(int slotIndex, int button, ContainerInput action, Player player) {
        if (slotIndex >= FIRST_VARIANT && slotIndex < FIRST_INV) {
            if (action == ContainerInput.PICKUP || action == ContainerInput.QUICK_MOVE) {
                convert(slotIndex - FIRST_VARIANT, player);
            }
            return;
        }
        super.clicked(slotIndex, button, action, player);
    }

    private void convert(int variant, Player player) {
        ItemStack in = input.getItem(0);
        ItemStack target = variants.getItem(variant);
        if (in.isEmpty() || target.isEmpty() || in.is(target.getItem())) {
            return;
        }
        input.setItem(0, new ItemStack(target.getItem(), in.getCount()));
        access.execute((lvl, pos) -> {
            if (!lvl.isClientSide()) {
                lvl.playSound(null, pos, SoundEvents.UI_STONECUTTER_TAKE_RESULT, SoundSource.BLOCKS, 1.0F,
                        0.9F + lvl.getRandom().nextFloat() * 0.2F);
            }
        });
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem() || isVariantSlot(slot)) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (index == INPUT_SLOT) {
            if (!moveItemStackTo(stack, FIRST_INV, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (!moveItemStackTo(stack, INPUT_SLOT, INPUT_SLOT + 1, false)) {
            // not chisellable or input full: shuffle between main inventory and hotbar like vanilla
            int hotbar = slots.size() - 9;
            if (index < hotbar ? !moveItemStackTo(stack, hotbar, slots.size(), false)
                    : !moveItemStackTo(stack, FIRST_INV, hotbar, false)) {
                return ItemStack.EMPTY;
            }
        }
        if (stack.isEmpty()) {
            slot.setByPlayer(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        return stack.getCount() == copy.getCount() ? ItemStack.EMPTY : copy;
    }

    @Override
    public boolean canTakeItemForPickAll(ItemStack carried, Slot target) {
        return !isVariantSlot(target) && super.canTakeItemForPickAll(carried, target);
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, ModBlocks.CHISEL_TABLE.get());
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        access.execute((lvl, pos) -> clearContainer(player, input));
    }
}
