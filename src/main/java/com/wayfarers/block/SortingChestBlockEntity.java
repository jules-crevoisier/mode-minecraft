package com.wayfarers.block;

import com.wayfarers.registry.ModBlockEntities;
import com.wayfarers.util.InventoryUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

/**
 * A 54-slot chest that pulls in dropped items around it and keeps itself sorted
 * (it only reorganises when nobody is looking inside, so items never jump under the cursor).
 */
public class SortingChestBlockEntity extends BaseContainerBlockEntity {
    public static final int SIZE = 54;
    private static final int VACUUM_RADIUS = 6;
    private NonNullList<ItemStack> items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
    private boolean dirty;
    private int ticker;

    public SortingChestBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.SORTING_CHEST.get(), pos, state);
        // spread the item pull over the ticks: chests loaded together don't all search for items on the same tick
        ticker = (int) Math.floorMod(pos.asLong() * 0x9E3779B97F4A7C15L >>> 40, 40);
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable("block.wayfarers.sorting_chest");
    }

    @Override
    protected NonNullList<ItemStack> getItems() {
        return items;
    }

    @Override
    protected void setItems(NonNullList<ItemStack> newItems) {
        this.items = newItems;
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        return ChestMenu.sixRows(containerId, inventory, this);
    }

    @Override
    public int getContainerSize() {
        return SIZE;
    }

    @Override
    public void setChanged() {
        super.setChanged();
        dirty = true;
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
    }

    void serverTick() {
        if (!(level instanceof ServerLevel serverLevel) || ++ticker % 10 != 0) {
            return;
        }
        AABB area = new AABB(worldPosition).inflate(VACUUM_RADIUS);
        for (ItemEntity drop : serverLevel.getEntitiesOfClass(ItemEntity.class, area, e -> e.isAlive() && !e.hasPickUpDelay())) {
            ItemStack before = drop.getItem();
            ItemStack rest = InventoryUtil.insert(this, before, false);
            if (rest.getCount() != before.getCount()) {
                serverLevel.sendParticles(ParticleTypes.PORTAL, drop.getX(), drop.getY() + 0.2, drop.getZ(), 6, 0.1, 0.1, 0.1, 0.2);
                if (rest.isEmpty()) {
                    drop.discard();
                } else {
                    drop.setItem(rest);
                }
            }
        }
        if (dirty && ticker % 40 == 0 && !isBeingViewed(serverLevel)) {
            sortNow();
        }
    }

    public void sortNow() {
        InventoryUtil.sortContainer(this);
        dirty = false;
    }

    private boolean isBeingViewed(ServerLevel level) {
        for (Player player : level.players()) {
            if (player.containerMenu instanceof ChestMenu menu && menu.getContainer() == this) {
                return true;
            }
        }
        return false;
    }
}
