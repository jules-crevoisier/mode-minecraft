package com.brasshaven.map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import com.mojang.logging.LogUtils;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Waypoints of every player, kept by the server in world/data/brasshaven_map/waypoints.json. Each one has an owner
 * and is either private (only its owner sees it) or shared with everyone.
 */
final class MapWaypoints {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    static final int MAX_PER_PLAYER = 250;
    /** Every player's together (bounds the file, memory and the POINTS message). */
    static final int MAX_TOTAL = 10_000;

    private final Path file;
    private final List<MapProtocol.Waypoint> list = new ArrayList<>();
    private boolean dirty;

    MapWaypoints(Path file) {
        this.file = file;
        if (Files.isRegularFile(file)) {
            try {
                List<MapProtocol.Waypoint> read = GSON.fromJson(Files.readString(file, StandardCharsets.UTF_8),
                        new TypeToken<List<MapProtocol.Waypoint>>() { }.getType());
                if (read != null) {
                    for (MapProtocol.Waypoint w : read) {
                        if (w != null && w.id() != null && w.owner() != null && w.dim() != null && w.name() != null) {
                            // a hand-edited file may lack the owner's name: writeUTF(null) would fail every login
                            list.add(w.ownerName() != null ? w : new MapProtocol.Waypoint(w.id(), w.owner(), "?", w.name(),
                                    w.dim(), w.x(), w.y(), w.z(), w.color(), w.icon(), w.shared()));
                        }
                    }
                }
            } catch (IOException | RuntimeException e) {
                LOGGER.warn("Brasshaven map: could not read {}: {}", file, e.toString());
            }
        }
    }

    List<MapProtocol.Waypoint> visibleTo(UUID player) {
        String id = player.toString();
        // the player's own first: a POINTS message that would be too big drops the others' shared ones
        List<MapProtocol.Waypoint> out = new ArrayList<>();
        for (MapProtocol.Waypoint w : list) {
            if (w.owner().equals(id)) {
                out.add(w);
            }
        }
        for (MapProtocol.Waypoint w : list) {
            if (w.shared() && !w.owner().equals(id)) {
                out.add(w);
            }
        }
        return out;
    }

    MapProtocol.Waypoint get(String id) {
        for (MapProtocol.Waypoint w : list) {
            if (w.id().equals(id)) {
                return w;
            }
        }
        return null;
    }

    boolean add(MapProtocol.Waypoint w) {
        long mine = list.stream().filter(o -> o.owner().equals(w.owner())).count();
        if (mine >= MAX_PER_PLAYER || list.size() >= MAX_TOTAL) {
            return false;
        }
        list.add(w);
        dirty = true;
        return true;
    }

    void replace(MapProtocol.Waypoint old, MapProtocol.Waypoint w) {
        int i = list.indexOf(old);
        if (i >= 0) {
            list.set(i, w);
            dirty = true;
        }
    }

    void remove(MapProtocol.Waypoint w) {
        dirty |= list.remove(w);
    }

    /** Writes the file on the map worker if anything changed. */
    void save() {
        if (!dirty) {
            return;
        }
        dirty = false;
        String json = GSON.toJson(list);
        MapServer.worker().execute(() -> {
            try {
                Files.createDirectories(file.getParent());
                Path tmp = file.resolveSibling(file.getFileName() + ".tmp");
                Files.writeString(tmp, json, StandardCharsets.UTF_8);
                Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING);
            } catch (IOException e) {
                LOGGER.warn("Brasshaven map: could not save {}: {}", file, e.toString());
            }
        });
    }
}
