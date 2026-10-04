package com.wayfarers.util;

import com.mojang.datafixers.util.Pair;
import com.wayfarers.Wayfarers;
import com.wayfarers.generated.GeneratedContent;
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

/** Finds the nearest Wayfarers structure (optionally of one kind) in the player's dimension. */
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
        ServerStoppedEvent.BUS.addListener(e -> CACHE.clear());
    }

    /** @param index index in {@link GeneratedContent#STRUCTURES}, or -1 for any structure of this dimension */
    public static @Nullable Found nearest(ServerLevel level, BlockPos from, int index, int radiusChunks) {
        Query key = new Query(level.dimension(), index, radiusChunks, ChunkPos.containing(from).pack());
        Optional<Found> cached = CACHE.get(key);
        if (cached == null) {
            cached = Optional.ofNullable(search(level, from, index, radiusChunks));
            CACHE.put(key, cached);
        }
        return cached.orElse(null);
    }

    private static @Nullable Found search(ServerLevel level, BlockPos from, int index, int radiusChunks) {
        var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        List<Holder<Structure>> wanted = new ArrayList<>();
        String dim = level.dimension().identifier().getPath().replace("the_", "");
        for (int i = 0; i < GeneratedContent.STRUCTURES.size(); i++) {
            GeneratedContent.StructureInfo info = GeneratedContent.STRUCTURES.get(i);
            if ((index >= 0 && i != index) || (index < 0 && !info.dimension().equals(dim))) {
                continue;
            }
            registry.get(ResourceKey.create(Registries.STRUCTURE, Wayfarers.id(info.id()))).ifPresent(wanted::add);
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
