package com.wayfarers.data;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.wayfarers.Wayfarers;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Server-wide state shared by the whole group of players: discovered waystones and the
 * quests (advancements) completed by anyone. Stored once, in the overworld's data storage.
 */
public final class WayfarersData extends SavedData {
    public record Waystone(String name, Identifier dimension, BlockPos pos) {
        public static final Codec<Waystone> CODEC = RecordCodecBuilder.create(b -> b.group(
                Codec.STRING.fieldOf("name").forGetter(Waystone::name),
                Identifier.CODEC.fieldOf("dimension").forGetter(Waystone::dimension),
                BlockPos.CODEC.fieldOf("pos").forGetter(Waystone::pos)
        ).apply(b, Waystone::new));

        public ResourceKey<Level> levelKey() {
            return ResourceKey.create(Registries.DIMENSION, dimension);
        }
    }

    public static final Codec<WayfarersData> CODEC = RecordCodecBuilder.create(b -> b.group(
            Codec.unboundedMap(Codec.STRING, Waystone.CODEC).fieldOf("waystones").forGetter(d -> d.waystones),
            Codec.STRING.listOf().fieldOf("quests").forGetter(d -> List.copyOf(d.quests)),
            Codec.INT.fieldOf("next_id").forGetter(d -> d.nextId),
            Codec.STRING.listOf().optionalFieldOf("welcomed", List.of()).forGetter(d -> List.copyOf(d.welcomed))
    ).apply(b, WayfarersData::new));

    public static final SavedDataType<WayfarersData> TYPE = new SavedDataType<>(
            Wayfarers.id("guild"), WayfarersData::new, CODEC, null);

    private final Map<String, Waystone> waystones;
    private final Set<String> quests;
    private final Set<String> welcomed;
    private int nextId;

    public WayfarersData() {
        this(Map.of(), List.of(), 1, List.of());
    }

    private WayfarersData(Map<String, Waystone> waystones, List<String> quests, int nextId, List<String> welcomed) {
        this.waystones = new LinkedHashMap<>(waystones);
        this.quests = new HashSet<>(quests);
        this.nextId = nextId;
        this.welcomed = new HashSet<>(welcomed);
    }

    /** True the first time a given player joins the world. */
    public boolean welcome(java.util.UUID player) {
        boolean added = welcomed.add(player.toString());
        if (added) {
            setDirty();
        }
        return added;
    }

    public static WayfarersData get(MinecraftServer server) {
        ServerLevel overworld = server.getLevel(Level.OVERWORLD);
        return overworld.getDataStorage().computeIfAbsent(TYPE);
    }

    // ------------------------------------------------------------------ waystones
    public Optional<String> findWaystone(Level level, BlockPos pos) {
        Identifier dim = level.dimension().identifier();
        return waystones.entrySet().stream()
                .filter(e -> e.getValue().pos().equals(pos) && e.getValue().dimension().equals(dim))
                .map(Map.Entry::getKey)
                .findFirst();
    }

    /** Registers the waystone if needed and returns its id plus whether it was new. */
    public String addWaystone(Level level, BlockPos pos, String name) {
        Optional<String> existing = findWaystone(level, pos);
        if (existing.isPresent()) {
            return existing.get();
        }
        String id = "w" + nextId++;
        waystones.put(id, new Waystone(name, level.dimension().identifier(), pos.immutable()));
        setDirty();
        return id;
    }

    public void removeWaystone(Level level, BlockPos pos) {
        findWaystone(level, pos).ifPresent(id -> {
            waystones.remove(id);
            setDirty();
        });
    }

    public Optional<Waystone> waystone(String id) {
        return Optional.ofNullable(waystones.get(id));
    }

    public List<Map.Entry<String, Waystone>> sortedWaystones() {
        List<Map.Entry<String, Waystone>> list = new ArrayList<>(waystones.entrySet());
        list.sort(Comparator.comparing((Map.Entry<String, Waystone> e) -> e.getValue().dimension().toString())
                .thenComparing(e -> e.getValue().name()));
        return list;
    }

    public int waystoneCount() {
        return waystones.size();
    }

    // ------------------------------------------------------------------ shared quests
    /** Records one criterion ("namespace:path#criterion") reached by anyone; false if already known. */
    public boolean markCriterion(Identifier advancement, String criterion) {
        boolean added = quests.add(advancement + "#" + criterion);
        if (added) {
            setDirty();
        }
        return added;
    }

    public Set<String> quests() {
        return Set.copyOf(quests);
    }

    public void clearQuests() {
        quests.clear();
        setDirty();
    }
}
