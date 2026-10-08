package com.brasshaven.boss;

import com.brasshaven.Brasshaven;
import com.brasshaven.data.DataVersions;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.util.HashMap;
import java.util.Map;

/**
 * NG+ cycles, per world: how many times each boss type (entity id, e.g. {@code brasshaven:iron_helmsman}) was
 * defeated. A boss spawned after {@code n} defeats fights at cycle {@code min(n, MAX)}: stronger, faster, richer loot.
 * Stored once, in the overworld's data storage (world/data/brasshaven_boss_cycles.dat).
 */
public final class BossCycles extends SavedData {
    public static final int MAX = 7;

    public static final Codec<BossCycles> CODEC = RecordCodecBuilder.create(b -> b.group(
            Codec.unboundedMap(Codec.STRING, Codec.INT).optionalFieldOf("defeats", Map.of()).forGetter(d -> d.defeats)
    ).apply(b, BossCycles::new));

    public static final SavedDataType<BossCycles> TYPE = new SavedDataType<>(
            Brasshaven.id("boss_cycles"), BossCycles::new,
            DataVersions.versioned("boss_cycles", CODEC, DataVersions.BOSS_CYCLES, Map.of()), null);

    private final Map<String, Integer> defeats;

    public BossCycles() {
        this(Map.of());
    }

    private BossCycles(Map<String, Integer> defeats) {
        this.defeats = new HashMap<>(defeats);
    }

    public static BossCycles get(MinecraftServer server) {
        ServerLevel overworld = server.getLevel(Level.OVERWORLD);
        return overworld.getDataStorage().computeIfAbsent(TYPE);
    }

    /** Cycle the next fight against this boss runs at (0 = first fight). */
    public int cycle(String bossId) {
        return Math.min(MAX, Math.max(0, defeats.getOrDefault(bossId, 0)));
    }

    public int defeats(String bossId) {
        return defeats.getOrDefault(bossId, 0);
    }

    /** One more defeat of this boss type; returns the new cycle. */
    public int defeated(String bossId) {
        defeats.merge(bossId, 1, Integer::sum);
        setDirty();
        return cycle(bossId);
    }

    /** Admin: force the cycle (the defeat count becomes {@code cycle}). */
    public void setCycle(String bossId, int cycle) {
        defeats.put(bossId, Math.min(MAX, Math.max(0, cycle)));
        setDirty();
    }
}
