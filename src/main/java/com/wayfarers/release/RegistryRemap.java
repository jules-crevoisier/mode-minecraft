package com.wayfarers.release;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.wayfarers.Wayfarers;
import net.minecraft.core.Registry;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.MissingMappingsEvent;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * Keeps worlds loading across updates when an id of the mod was renamed or removed. The committed list
 * tools/data/registry_ids.json (copied into the jar as META-INF/wayfarers/registry_ids.json) has, per registry,
 * {@code "aliases": {"old_id": "new_id"}} and {@code "removed": {"old_id": "why"}}; tools/validate.py refuses an id
 * that disappears without one of them. When a save (or a server) still knows an old id, Forge asks through
 * {@link MissingMappingsEvent}: an alias remaps it to the new block/item/entity, so placed blocks, items in chests and
 * creatures keep existing; a removed id is dropped with a log line instead of the "missing entries" prompt.
 */
public final class RegistryRemap {
    private static final Map<String, Map<String, String>> ALIASES = new HashMap<>();
    private static final Map<String, Map<String, String>> REMOVED = new HashMap<>();

    private RegistryRemap() {}

    public static void register() {
        load();
        MissingMappingsEvent.BUS.addListener(RegistryRemap::onMissing);
    }

    private static void onMissing(MissingMappingsEvent event) {
        handle(event, ForgeRegistries.Keys.BLOCKS, "block");
        handle(event, ForgeRegistries.Keys.ITEMS, "item");
        handle(event, ForgeRegistries.Keys.ENTITY_TYPES, "entity_type");
        handle(event, ForgeRegistries.Keys.BLOCK_ENTITY_TYPES, "block_entity_type");
        handle(event, ForgeRegistries.Keys.MENU_TYPES, "menu");
    }

    private static <T> void handle(MissingMappingsEvent event, ResourceKey<? extends Registry<T>> key, String kind) {
        Map<String, String> aliases = ALIASES.getOrDefault(kind, Map.of());
        Map<String, String> removed = REMOVED.getOrDefault(kind, Map.of());
        for (MissingMappingsEvent.Mapping<T> m : event.getMappings(key, Wayfarers.MODID)) {
            String old = m.getKey().getPath();
            String to = aliases.get(old);
            if (to != null) {
                Identifier target = to.contains(":") ? Identifier.parse(to) : Wayfarers.id(to);
                T value = m.getRegistry().getValue(target);
                if (value != null && m.getRegistry().containsKey(target)) {
                    m.remap(value);
                    Wayfarers.LOGGER.info("Wayfarers: {} {} is now {}", kind, m.getKey(), target);
                    continue;
                }
                Wayfarers.LOGGER.warn("Wayfarers: {} {} should become {}, which does not exist", kind, m.getKey(), target);
            }
            if (removed.containsKey(old)) {
                m.warn();
                Wayfarers.LOGGER.info("Wayfarers: {} {} was removed from the mod ({})", kind, m.getKey(), removed.get(old));
            }
        }
    }

    private static void load() {
        try (InputStream in = RegistryRemap.class.getResourceAsStream("/META-INF/wayfarers/registry_ids.json")) {
            if (in == null) {
                return;
            }
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            read(root, "aliases", ALIASES);
            read(root, "removed", REMOVED);
        } catch (java.io.IOException | RuntimeException e) {
            Wayfarers.LOGGER.warn("Wayfarers: the registry id list in the jar is unreadable ({})", e.getMessage());
        }
    }

    private static void read(JsonObject root, String section, Map<String, Map<String, String>> into) {
        JsonElement s = root.get(section);
        if (s == null || !s.isJsonObject()) {
            return;
        }
        for (Map.Entry<String, JsonElement> kind : s.getAsJsonObject().entrySet()) {
            if (!kind.getValue().isJsonObject()) {
                continue;
            }
            Map<String, String> map = new HashMap<>();
            for (Map.Entry<String, JsonElement> e : kind.getValue().getAsJsonObject().entrySet()) {
                if (e.getValue().isJsonPrimitive()) {
                    map.put(e.getKey(), e.getValue().getAsString());
                }
            }
            into.put(kind.getKey(), map);
        }
    }
}
