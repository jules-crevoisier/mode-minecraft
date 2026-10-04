package com.wayfarers.block;

import com.wayfarers.registry.ModBlockEntities;
import com.wayfarers.util.StorageNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * The Guild Terminal's memory: which linked containers the player excluded (a trash chest, a furnace input chest...),
 * and the last network scan, shared by everyone using this terminal and refreshed every few seconds.
 */
public class GuildTerminalBlockEntity extends BlockEntity {
    /** Ticks between two scans of the base while the terminal is in use. */
    private static final int REFRESH_TICKS = 100;
    private static final int MAX_EXCLUDED = 1024;
    private static final int MIN_FORCED_TICKS = 10;

    /** Game time of the last sneak-sort (sorting a whole base is rate-limited). */
    private long sortedAt = Long.MIN_VALUE;

    private final Set<BlockPos> excluded = new HashSet<>();
    private StorageNetwork.Scan scan = StorageNetwork.Scan.EMPTY;
    private long scannedAt = Long.MIN_VALUE;

    public GuildTerminalBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.GUILD_TERMINAL.get(), pos, state);
    }

    /** The current scan, redone when older than a few seconds (or right away with {@code force}). */
    public StorageNetwork.Scan scan(boolean force) {
        if (!(level instanceof ServerLevel serverLevel)) {
            return StorageNetwork.Scan.EMPTY;
        }
        long now = serverLevel.getGameTime();
        // forced scans (opening the screen) at most twice a second: spam-clicking must not rescan a huge base each time
        boolean stale = scannedAt == Long.MIN_VALUE || now < scannedAt
                || now - scannedAt >= (force ? MIN_FORCED_TICKS : REFRESH_TICKS);
        if (stale) {
            scan = StorageNetwork.scan(serverLevel, worldPosition);
            scannedAt = now;
            pruneExcluded(serverLevel);
        }
        return scan;
    }

    /** The containers items are taken from and stored in: linked, not excluded, still there. Closest first. */
    public List<Container> network() {
        List<Container> out = new ArrayList<>();
        for (StorageNetwork.Link link : scan(false).links()) {
            if (!excluded.contains(link.key) && link.valid()) {
                for (BaseContainerBlockEntity be : link.parts) {
                    out.add(be);
                }
            }
        }
        return out;
    }

    /** True (and starts the cooldown) when the whole network may be sorted now: at most once a second. */
    public boolean trySort() {
        long now = level == null ? 0 : level.getGameTime();
        if (sortedAt != Long.MIN_VALUE && now >= sortedAt && now - sortedAt < 20) {
            return false;
        }
        sortedAt = now;
        return true;
    }

    public boolean isExcluded(BlockPos key) {
        return excluded.contains(key);
    }

    /** Excludes or re-includes a linked container; returns false when {@code key} is not one of this network's. */
    public boolean toggle(BlockPos key) {
        boolean linked = scan.links().stream().anyMatch(l -> l.key.equals(key));
        if (!linked) {
            return false;
        }
        if (!excluded.remove(key)) {
            if (excluded.size() >= MAX_EXCLUDED) {
                return false;
            }
            excluded.add(key.immutable());
        }
        setChanged();
        return true;
    }

    /** Forgets exclusions of containers that were broken (only where the chunk is loaded, so nothing is lost). */
    private void pruneExcluded(ServerLevel serverLevel) {
        // a key is the container's own position (for a double chest, one of its halves)
        if (excluded.removeIf(p -> serverLevel.isLoaded(p) && !StorageNetwork.isStorage(serverLevel.getBlockEntity(p)))) {
            setChanged();
        }
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.store("excluded", BlockPos.CODEC.listOf(), List.copyOf(excluded));
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        excluded.clear();
        input.read("excluded", BlockPos.CODEC.listOf()).ifPresent(excluded::addAll);
        scannedAt = Long.MIN_VALUE;
    }
}
