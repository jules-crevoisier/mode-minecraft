package com.brasshaven.util;

import com.mojang.datafixers.util.Pair;
import com.brasshaven.Brasshaven;
import com.brasshaven.generated.GeneratedContent;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraftforge.event.server.ServerStoppedEvent;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Finds the nearest Brasshaven structure (optionally of one kind) in the player's dimension. */
public final class StructureLocator {
    private StructureLocator() {}

    public record Found(BlockPos pos, String structureId) {}

    private record Query(ResourceKey<Level> dimension, int index, int radiusChunks, long chunk) {}

    private static final int CACHE_SIZE = 256;

    /**
     * Locating is expensive (it walks structure placements over up to 100+ chunks and may compute structure starts
     * of ungenerated chunks) and its answer never changes for a given world, so answers are remembered per starting
     * chunk: compasses used again from the same chunk, or by several players standing together, cost nothing.
     * "Nothing found" is remembered too: it is the slowest search of all (the whole radius).
     */
    private static final Map<Query, Optional<Found>> CACHE = new LinkedHashMap<>(64, 0.75F, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<Query, Optional<Found>> eldest) {
            return size() > CACHE_SIZE;
        }
    };

    /** Forgets the remembered answers when the server stops (another world may be opened next). */
    public static void register() {
        ServerStoppedEvent.BUS.addListener(e -> {
            CACHE.clear();
            tokens = -1;
        });
    }

    /** Answer of {@link #nearestBudgeted} when the server-wide search budget is used up for now. */
    public static final Found BUSY = new Found(BlockPos.ZERO, "");

    /** Searches allowed right now, refilled at compass.searchesPerMinute (shared by every player). */
    private static double tokens = -1;
    private static long refilledAt;

    /** @param index index in {@link GeneratedContent#STRUCTURES}, -1 for any structure of this dimension, {@link #VILLAGE} */
    public static @Nullable Found nearest(ServerLevel level, BlockPos from, int index, int radiusChunks) {
        return nearest(level, from, index, radiusChunks, false);
    }

    /**
     * Like {@link #nearest}, for players' items: a search that is not remembered yet spends one of the server-wide
     * searches of compass.searchesPerMinute, and {@link #BUSY} comes back when none is left (a crowd of players each
     * using a compass every 3 seconds in a different place must not stall the server thread).
     */
    public static @Nullable Found nearestBudgeted(ServerLevel level, BlockPos from, int index, int radiusChunks) {
        return nearest(level, from, index, radiusChunks, true);
    }

    private static @Nullable Found nearest(ServerLevel level, BlockPos from, int index, int radiusChunks, boolean budgeted) {
        // answers are shared by 4 x 4 chunk cells (64 blocks): the search starts at the cell's centre, so a player
        // walking around asks again only every few dozen blocks, and a group shares one answer
        ChunkPos chunk = ChunkPos.containing(from);
        int cx = chunk.x() >> 2, cz = chunk.z() >> 2;
        Query key = new Query(level.dimension(), index, radiusChunks, ChunkPos.pack(cx, cz));
        Optional<Found> cached = CACHE.get(key);
        if (cached == null) {
            if (budgeted && !takeToken()) {
                return BUSY;
            }
            BlockPos centre = new BlockPos((cx << 6) + 32, from.getY(), (cz << 6) + 32);
            cached = Optional.ofNullable(search(level, centre, index, radiusChunks));
            CACHE.put(key, cached);
        }
        return cached.orElse(null);
    }

    private static boolean takeToken() {
        double perMinute = com.brasshaven.config.BrasshavenConfig.LOCATE_PER_MINUTE.get();
        double burst = Math.max(3.0, perMinute / 6.0);
        long now = System.nanoTime();
        if (tokens < 0) {
            tokens = burst;
            refilledAt = now;
        }
        tokens = Math.min(burst, tokens + (now - refilledAt) / 60_000_000_000.0 * perMinute);
        refilledAt = now;
        if (tokens < 1.0) {
            return false;
        }
        tokens -= 1.0;
        return true;
    }

    /** Index for {@link #nearest}: any village (the {@code minecraft:village} structure tag), found as "village". */
    public static final int VILLAGE = -2;

    /** Index of a structure in {@link GeneratedContent#STRUCTURES} by its id (without namespace), or -1. */
    public static int index(String id) {
        for (int i = 0; i < GeneratedContent.STRUCTURES.size(); i++) {
            if (GeneratedContent.STRUCTURES.get(i).id().equals(id)) {
                return i;
            }
        }
        return -1;
    }

    private static @Nullable Found search(ServerLevel level, BlockPos from, int index, int radiusChunks) {
        var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        if (index == VILLAGE) {
            Optional<HolderSet.Named<Structure>> villages = registry.get(net.minecraft.tags.StructureTags.VILLAGE);
            if (villages.isEmpty()) {
                return null;
            }
            Pair<BlockPos, Holder<Structure>> result = level.getChunkSource().getGenerator()
                    .findNearestMapStructure(level, villages.get(), from, radiusChunks, false);
            return result == null ? null : new Found(result.getFirst(), "village");
        }
        List<Holder<Structure>> wanted = new ArrayList<>();
        String dim = level.dimension().identifier().getPath().replace("the_", "");
        for (int i = 0; i < GeneratedContent.STRUCTURES.size(); i++) {
            GeneratedContent.StructureInfo info = GeneratedContent.STRUCTURES.get(i);
            if ((index >= 0 && i != index) || (index < 0 && !info.dimension().equals(dim))) {
                continue;
            }
            registry.get(ResourceKey.create(Registries.STRUCTURE, Brasshaven.id(info.id()))).ifPresent(wanted::add);
        }
        if (wanted.isEmpty()) {
            return null;
        }
        Pair<BlockPos, Holder<Structure>> result = level.getChunkSource().getGenerator()
                .findNearestMapStructure(level, HolderSet.direct(wanted), from, radiusChunks, false);
        if (result == null) {
            return null;
        }
        String id = result.getSecond().unwrapKey().map(k -> k.identifier().getPath()).orElse("?");
        return new Found(result.getFirst(), id);
    }

    public static String compassDirection(BlockPos from, BlockPos to) {
        double angle = Math.toDegrees(Math.atan2(to.getZ() - from.getZ(), to.getX() - from.getX()));
        String[] dirs = {"E", "SE", "S", "SW", "W", "NW", "N", "NE"};
        int idx = (int) Math.round(((angle % 360) + 360) % 360 / 45.0) % 8;
        return dirs[idx];
    }
}
