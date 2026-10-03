package com.wayfarers.menu;

import com.wayfarers.network.TerminalContentsMsg;
import com.wayfarers.network.WayfarersNet;
import com.wayfarers.registry.ModBlocks;
import com.wayfarers.registry.ModMenus;
import com.wayfarers.util.StorageNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * The Guild Terminal's menu: the player's inventory as real slots; the storage network is shown as a
 * virtual grid that the server keeps in sync ({@link TerminalContentsMsg}). Shift-clicking an inventory
 * slot stores it in the network; clicks on the grid are sent as {@code TerminalClickMsg}.
 */
public class TerminalMenu extends AbstractContainerMenu {
    public static final int INV_X = 17;
    public static final int INV_Y = 142;

    private final BlockPos pos;
    private final Player player;
    private int syncTimer;
    private int lastHash;

    /** Client copy of the network contents. */
    public List<StorageNetwork.Entry> clientContents = new ArrayList<>();

    public TerminalMenu(int id, Inventory inv, BlockPos pos) {
        super(ModMenus.TERMINAL.get(), id);
        this.pos = pos;
        this.player = inv.player;
        addStandardInventorySlots(inv, INV_X, INV_Y);
    }

    public BlockPos pos() {
        return pos;
    }

    public List<Container> network() {
        return player.level() instanceof ServerLevel level ? StorageNetwork.containers(level, pos) : List.of();
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (player.level().isClientSide() || !slot.hasItem()) {
            return ItemStack.EMPTY;
        }
        ItemStack rest = StorageNetwork.insert(network(), slot.getItem());
        slot.set(rest);
        syncTimer = 0;
        return ItemStack.EMPTY;
    }

    @Override
    public boolean stillValid(Player player) {
        return player.level().getBlockState(pos).is(ModBlocks.GUILD_TERMINAL.get())
                && player.position().closerThan(net.minecraft.world.phys.Vec3.atCenterOf(pos), 8.0);
    }

    @Override
    public void broadcastChanges() {
        super.broadcastChanges();
        if (player instanceof ServerPlayer sp && --syncTimer <= 0) {
            syncTimer = 10;
            List<StorageNetwork.Entry> contents = StorageNetwork.contents(network());
            int hash = 1;
            for (StorageNetwork.Entry e : contents) {
                hash = 31 * hash + ItemStack.hashItemAndComponents(e.type()) * 17 + e.count();
            }
            if (hash != lastHash) {
                lastHash = hash;
                WayfarersNet.toPlayer(sp, new TerminalContentsMsg(containerId, contents));
            }
        }
    }

    /** Forces a resync on the next tick (after a take/insert). */
    public void dirty() {
        syncTimer = 0;
        lastHash = 0;
    }
}
