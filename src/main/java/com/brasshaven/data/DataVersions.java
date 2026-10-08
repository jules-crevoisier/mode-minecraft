package com.brasshaven.data;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.Dynamic;
import com.mojang.serialization.DynamicOps;
import com.brasshaven.Brasshaven;
import com.brasshaven.release.BuildInfo;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.event.server.ServerAboutToStartEvent;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.UnaryOperator;

/**
 * Format versions of everything the mod saves in a world, so that a world keeps loading after the jar is updated.
 *
 * <p>Each kind of saved data writes a {@code data_version}. A save without one is version 0 (written before
 * versioning; it has the same layout as version 1). When a format changes: bump the constant here, and add a
 * migration step from the previous version that rewrites the old data into the new layout (the codec-based data use
 * {@link #versioned}, whose steps work on the raw NBT as a {@link Dynamic}). Steps run in order, so a world several
 * versions behind is brought up to date in one load. Data written by a NEWER version of the mod (a downgrade) is read
 * as well as possible and logged: keep the world backup made before updating.
 */
public final class DataVersions {
    /** BrasshavenData: waystones, shared quests, welcomed players (world/data/brasshaven_guild.dat). */
    public static final int GUILD = 1;
    /** Shared world map: world/data/brasshaven_map/ (regions, waypoints.json, explored/). */
    public static final int MAP = 1;
    /** Guild Terminal block entity (storage network settings: excluded containers). */
    public static final int TERMINAL = 1;
    /** BossCycles: NG+ defeat counters per boss type (world/data/brasshaven_boss_cycles.dat). */
    public static final int BOSS_CYCLES = 1;
    /** Worn accessories of a player (player persistent data, "brasshaven_accessories"; accessory/Accessories). */
    public static final int ACCESSORIES = 1;

    public static final String FIELD = "data_version";

    private DataVersions() {}

    public static void register() {
        ServerAboutToStartEvent.BUS.addListener(e -> migrateMap(e.getServer()));
    }

    /**
     * Wraps a SavedData codec: decoding upgrades older data step by step ({@code steps.get(v)} turns version v into
     * v + 1), encoding writes {@code data_version}.
     */
    public static <A> Codec<A> versioned(String name, Codec<A> codec, int current, Map<Integer, UnaryOperator<Dynamic<?>>> steps) {
        Map<Integer, UnaryOperator<Dynamic<?>>> ordered = new TreeMap<>(steps);
        return new Codec<>() {
            @Override
            public <T> DataResult<Pair<A, T>> decode(DynamicOps<T> ops, T input) {
                Dynamic<?> data = new Dynamic<>(ops, input);
                int from = data.get(FIELD).asInt(0);
                if (from > current) {
                    Brasshaven.LOGGER.warn("Brasshaven: the {} data of this world was saved by a newer version of the mod "
                            + "(format {}, this jar reads {}); reading what it can", name, from, current);
                }
                for (int v = from; v < current; v++) {
                    UnaryOperator<Dynamic<?>> step = ordered.get(v);
                    if (step != null) {
                        data = step.apply(data);
                    }
                }
                if (from < current) {
                    Brasshaven.LOGGER.info("Brasshaven: upgraded the {} data of this world from format {} to {}", name, from, current);
                }
                return codec.parse(data).map(a -> Pair.of(a, ops.empty()));
            }

            @Override
            public <T> DataResult<T> encode(A input, DynamicOps<T> ops, T prefix) {
                return codec.encode(input, ops, prefix)
                        .flatMap(t -> ops.mergeToMap(t, ops.createString(FIELD), ops.createInt(current)));
            }
        };
    }

    /** Logs a block entity or file saved by a newer format (a downgrade); returns the version it was saved with. */
    public static int check(String name, int from, int current) {
        if (from > current) {
            Brasshaven.LOGGER.warn("Brasshaven: {} data saved by a newer version of the mod (format {}, this jar reads {})",
                    name, from, current);
        }
        return from;
    }

    /**
     * The world map lives in its own files: world/data/brasshaven_map/format.json records their version. Runs before
     * the map is opened (the map starts with the first player).
     */
    private static void migrateMap(MinecraftServer server) {
        Path root = server.getWorldPath(LevelResource.ROOT).resolve("data").resolve("brasshaven_map");
        Path marker = root.resolve("format.json");
        try {
            int from = 0;
            if (Files.isRegularFile(marker)) {
                JsonObject o = JsonParser.parseString(Files.readString(marker, StandardCharsets.UTF_8)).getAsJsonObject();
                from = o.has(FIELD) ? o.get(FIELD).getAsInt() : 0;
            } else if (!Files.isDirectory(root)) {
                from = MAP; // a world without a map yet: it starts in the current format
            }
            check("world map", from, MAP);
            // version 0 -> 1: the layout written before versioning is version 1, nothing to convert.
            // A future step goes here: if (from < 2) { ...rewrite the files under root... }
            if (from < MAP || !Files.isRegularFile(marker)) {
                Files.createDirectories(root);
                JsonObject o = new JsonObject();
                o.addProperty(FIELD, Math.max(from, MAP));
                o.addProperty("mod_version", BuildInfo.version());
                Files.writeString(marker, o.toString(), StandardCharsets.UTF_8);
            }
        } catch (java.io.IOException | RuntimeException e) {
            Brasshaven.LOGGER.warn("Brasshaven: could not check the world map format in {} ({})", root, e.getMessage());
        }
    }
}
