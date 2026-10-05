package com.brasshaven.menu;

import com.brasshaven.block.GuildTerminalBlockEntity;
import com.brasshaven.network.TerminalContentsMsg;
import com.brasshaven.network.TerminalLinksMsg;
import com.brasshaven.network.BrasshavenNet;
import com.brasshaven.registry.ModBlocks;
import com.brasshaven.registry.ModMenus;
import com.brasshaven.util.StorageNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * The Guild Terminal's menu: the player's inventory as real slots; the storage network is shown as a virtual grid
 * that the server keeps in sync ({@link TerminalContentsMsg}, and {@link TerminalLinksMsg} for the list of linked
 * containers). Shift-clicking an inventory slot stores it in the network; clicks on the grid are sent as
 * {@code TerminalClickMsg}. Every take/store works on the live containers, on the server thread, so two players on
 * the same terminal (or a chest opened meanwhile) can never duplicate items.
 */
public class TerminalMenu extends AbstractContainerMenu {
    public static final int INV_X = 17;
    public static final int INV_Y = 152;

    private final BlockPos pos;
    private final Player player;
    private int syncTimer;
    private int lastHash = Integer.MIN_VALUE;
    private int lastLinksHash = Integer.MIN_VALUE;

    /** Client copy of the network contents and status. */
    public List<StorageNetwork.Entry> clientContents = new ArrayList<>();
    public int clientLinked;
    public int clientFree;
    /** Client copy of the linked containers (null until the server sent them). */
    public @Nullable TerminalLinksMsg clientLinks;

    public TerminalMenu(int id, Inventory inv, BlockPos pos) {
        super(ModMenus.TERMINAL.get(), id);
        this.pos = pos;
        this.player = inv.player;
        addStandardInventorySlots(inv, INV_X, INV_Y);
    }

    public BlockPos pos() {
        return pos;
    }

    private @Nullable GuildTerminalBlockEntity terminal() {
        return player.level() instanceof ServerLevel level && level.getBlockEntity(pos) instanceof GuildTerminalBlockEntity t
                ? t : null;
    }

    /** The containers to take from and store in (server side; empty on the client). */
    public List<Container> network() {
        GuildTerminalBlockEntity t = terminal();
        return t == null ? List.of() : t.network();
    }

    public void toggle(BlockPos key) {
        GuildTerminalBlockEntity t = terminal();
        if (t != null && t.toggle(key)) {
            dirty();
            broadcastChanges();
        }
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (player.level().isClientSide() || !slot.hasItem()) {
            return ItemStack.EMPTY;
        }
        // each shift-click indexes the whole network: the same per-player limit as the grid clicks
        if (player instanceof ServerPlayer sp && !com.brasshaven.util.ServerGuard.allow(sp, "terminal_click", 30, 15.0)) {
            return ItemStack.EMPTY;
        }
        ItemStack rest = StorageNetwork.insert(network(), slot.getItem());
        slot.set(rest);
        dirty();
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
        if (!(player instanceof ServerPlayer sp) || --syncTimer > 0) {
            return;
        }
        syncTimer = 10;
        GuildTerminalBlockEntity t = terminal();
        if (t == null) {
            return;
        }
        StorageNetwork.Scan scan = t.scan(false);
        GuildTerminalBlockEntity.Snapshot snapshot = t.snapshot();
        List<StorageNetwork.Entry> contents = snapshot.contents();
        int linked = 0;
        int linksHash = scan.relays() * 31 + (scan.capped() ? 1 : 0);
        for (StorageNetwork.Link link : scan.links()) {
            boolean excluded = t.isExcluded(link.key);
            if (!excluded) {
                linked++;
            }
            linksHash = 31 * linksHash + link.key.hashCode() * 7 + link.parts.size() * 2 + (excluded ? 1 : 0);
        }
        int free = snapshot.freeSlots();
        int hash = linked * 31 + free;
        for (StorageNetwork.Entry e : contents) {
            hash = 31 * hash + ItemStack.hashItemAndComponents(e.type()) * 17 + e.count();
        }
        if (linksHash != lastLinksHash) {
            lastLinksHash = linksHash;
            List<TerminalLinksMsg.Info> infos = new ArrayList<>(scan.links().size());
            for (StorageNetwork.Link link : scan.links()) {
                infos.add(new TerminalLinksMsg.Info(link.key, new ItemStack(link.first().getBlockState().getBlock().asItem()),
                        link.slots(), link.parts.size() > 1, t.isExcluded(link.key)));
            }
            BrasshavenNet.toPlayer(sp, new TerminalLinksMsg(containerId, StorageNetwork.terminalRange(), scan.relays(),
                    scan.capped(), infos));
        }
        if (hash != lastHash) {
            lastHash = hash;
            BrasshavenNet.toPlayer(sp, new TerminalContentsMsg(containerId, contents, linked, free));
        }
    }

    /** Forces a resync on the next tick (after a take/insert). */
    public void dirty() {
        syncTimer = 0;
        lastHash = Integer.MIN_VALUE;
        GuildTerminalBlockEntity t = terminal();
        if (t != null) {
            t.invalidateContents();
        }
    }
}
