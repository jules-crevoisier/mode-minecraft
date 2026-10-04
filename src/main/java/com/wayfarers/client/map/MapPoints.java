package com.wayfarers.client.map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import com.mojang.logging.LogUtils;
import org.slf4j.Logger;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;

/**
 * What this client learned along the way, per world or server: structures located with a compass, its own graves and
 * the last compass target (waypoints and waystones come from the server). Saved as JSON in
 * wayfarers/maps/&lt;world&gt;/points.json under the game directory.
 */
final class MapPoints {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    /** A point on a map. {@code dim}: dimension id ("minecraft:overworld"). */
    public static final class Point {
        public String name;
        public String dim;
        public int x;
        public int y;
        public int z;
        public int color;
        public boolean visible = true;
        /** For waystones and structures: their id, to update instead of duplicate. */
        public String id;

        public Point() {}

        public Point(String id, String name, String dim, int x, int y, int z, int color) {
            this.id = id;
            this.name = name;
            this.dim = dim;
            this.x = x;
            this.y = y;
            this.z = z;
            this.color = color;
        }
    }

    private static final class Data {
        List<Point> structures = new ArrayList<>();
        List<Point> graves = new ArrayList<>();
        Point target;
    }

    private final Path file;
    private Data data = new Data();

    MapPoints(Path file) {
        this.file = file;
        load();
    }

    public List<Point> structures() {
        return data.structures;
    }

    public List<Point> graves() {
        return data.graves;
    }

    /** The last place a compass pointed to (null when none). */
    public Point target() {
        return data.target;
    }

    public void setTarget(Point p) {
        data.target = p;
        save();
    }

    /** Remembers a structure (by id + position); keeps the 200 most recent. */
    public void addStructure(Point p) {
        data.structures.removeIf(s -> s.dim.equals(p.dim) && Math.abs(s.x - p.x) < 48 && Math.abs(s.z - p.z) < 48);
        data.structures.add(p);
        while (data.structures.size() > 200) {
            data.structures.removeFirst();
        }
        save();
    }

    public void addGrave(Point p) {
        data.graves.removeIf(g -> g.dim.equals(p.dim) && g.x == p.x && g.y == p.y && g.z == p.z);
        data.graves.add(p);
        while (data.graves.size() > 8) {
            data.graves.removeFirst();
        }
        save();
    }

    public void removeGrave(Point p) {
        if (data.graves.remove(p)) {
            save();
        }
    }

    private void load() {
        if (!Files.isRegularFile(file)) {
            return;
        }
        try (Reader r = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            Data d = GSON.fromJson(r, new TypeToken<Data>() { }.getType());
            if (d != null) {
                d.structures = d.structures == null ? new ArrayList<>() : new ArrayList<>(d.structures);
                d.graves = d.graves == null ? new ArrayList<>() : new ArrayList<>(d.graves);
                d.structures.removeIf(p -> p == null || p.dim == null || p.name == null);
                d.graves.removeIf(p -> p == null || p.dim == null);
                data = d;
            }
        } catch (IOException | RuntimeException e) {
            LOGGER.warn("Wayfarers map: could not read {}: {}", file, e.toString());
        }
    }

    /** Writes the file (small; done right away so nothing is lost on a crash). */
    public void save() {
        String json = GSON.toJson(data);
        ClientMap.io().execute(() -> {
            try {
                Files.createDirectories(file.getParent());
                Path tmp = file.resolveSibling(file.getFileName() + ".tmp");
                try (Writer w = Files.newBufferedWriter(tmp, StandardCharsets.UTF_8)) {
                    w.write(json);
                }
                Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (IOException | RuntimeException e) {
                LOGGER.warn("Wayfarers map: could not save {}: {}", file, e.toString());
            }
        });
    }
}
