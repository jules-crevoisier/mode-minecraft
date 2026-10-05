package com.wayfarers.util;

import com.wayfarers.Wayfarers;
import com.wayfarers.config.WayfarersConfig;
import it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraftforge.event.server.ServerStoppedEvent;

import java.util.HashMap;
import java.util.Map;

/**
 * Server limits on natural spawning of the mod's creatures (spawns.natural, spawns.maxLoadedPerType): an extra
 * condition on top of each creature's own spawn rules, so a busy server never fills up with one kind of creature.
 * Counting walks the loaded entities of a dimension at most every 5 seconds; spawns allowed in between count too.
 * Only natural spawns are limited: structures, spawners, altars, commands and spawn eggs are not.
 */
public final class SpawnCaps {
    private static final int RECOUNT_TICKS = 100;
    private static final Map<ResourceKey<Level>, Object2IntOpenHashMap<EntityType<?>>> COUNTS = new HashMap<>();
    private static final Map<ResourceKey<Level>, Long> COUNTED_AT = new HashMap<>();

    private SpawnCaps() {}

    public static void register() {
        ServerStoppedEvent.BUS.addListener(e -> {
            COUNTS.clear();
            COUNTED_AT.clear();
        });
    }

    /** The extra spawn condition (registered with Operation.AND for every naturally spawning creature of the mod). */
    public static boolean allow(EntityType<?> type, ServerLevelAccessor accessor, EntitySpawnReason reason) {
        if (reason != EntitySpawnReason.NATURAL && reason != EntitySpawnReason.CHUNK_GENERATION) {
            return true;
        }
        if (!WayfarersConfig.SPAWNS_ENABLED.get()) {
            return false;
        }
        // chunk generation may run off the server thread and is bounded by the generated area anyway: only the
        // natural spawning cycle (server thread) is counted
        if (reason != EntitySpawnReason.NATURAL) {
            return true;
        }
        int max = WayfarersConfig.SPAWNS_MAX_PER_TYPE.get();
        ServerLevel level = accessor.getLevel();
        long now = level.getGameTime();
        Long at = COUNTED_AT.get(level.dimension());
        Object2IntOpenHashMap<EntityType<?>> counts = COUNTS.get(level.dimension());
        if (counts == null || at == null || now < at || now - at >= RECOUNT_TICKS) {
            counts = count(level);
            COUNTS.put(level.dimension(), counts);
            COUNTED_AT.put(level.dimension(), now);
        }
        int n = counts.getInt(type);
        if (n >= max) {
            return false;
        }
        counts.put(type, n + 1);
        return true;
    }

    private static Object2IntOpenHashMap<EntityType<?>> count(ServerLevel level) {
        Object2IntOpenHashMap<EntityType<?>> counts = new Object2IntOpenHashMap<>();
        for (Entity e : level.getAllEntities()) {
            EntityType<?> type = e.getType();
            if (Wayfarers.MODID.equals(BuiltInRegistries.ENTITY_TYPE.getKey(type).getNamespace())) {
                counts.addTo(type, 1);
            }
        }
        return counts;
    }
}
