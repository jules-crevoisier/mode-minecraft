package com.wayfarers.map;

import com.mojang.logging.LogUtils;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import org.slf4j.Logger;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.zip.DeflaterOutputStream;
import java.util.zip.InflaterInputStream;

/**
 * Which chunks each player has seen themselves (a 256-bit mask per region), kept even when exploration is shared so
 * that switching {@code map.sharedExploration} off later still gives everyone their own map.
 * Stored in world/data/wayfarers_map/explored/&lt;uuid&gt;.bin, only while the player is online.
 */
final class MapExplorers {
    private static final Logger LOGGER = LogUtils.getLogger();

    static final class Explorer {
        final Map<String, Long2ObjectOpenHashMap<long[]>> dims = new HashMap<>();
        boolean dirty;

        boolean mark(String dim, int cx, int cz) {
            long key = RegionData.key(cx >> 4, cz >> 4);
            long[] bits = dims.computeIfAbsent(dim, d -> new Long2ObjectOpenHashMap<>()).computeIfAbsent(key, k -> new long[4]);
            int bit = ((cz & 15) << 4) | (cx & 15);
            long m = 1L << (bit & 63);
            if ((bits[bit >> 6] & m) != 0) {
                return false;
            }
            bits[bit >> 6] |= m;
            dirty = true;
            return true;
        }

        /** The region's mask (a copy, for the worker thread), or null when the player saw none of it. */
        long[] mask(String dim, long region) {
            Long2ObjectOpenHashMap<long[]> m = dims.get(dim);
            long[] bits = m == null ? null : m.get(region);
            return bits == null ? null : bits.clone();
        }

        boolean has(String dim, int cx, int cz) {
            Long2ObjectOpenHashMap<long[]> m = dims.get(dim);
            long[] bits = m == null ? null : m.get(RegionData.key(cx >> 4, cz >> 4));
            int bit = ((cz & 15) << 4) | (cx & 15);
            return bits != null && (bits[bit >> 6] & (1L << (bit & 63))) != 0;
        }
    }

    static boolean visible(long[] mask, int x, int z) {
        int bit = ((z >> 4) << 4) | (x >> 4);
        return mask != null && (mask[bit >> 6] & (1L << (bit & 63))) != 0;
    }

    private final Path dir;
    private final Map<UUID, Explorer> online = new HashMap<>();

    MapExplorers(Path dir) {
        this.dir = dir;
    }

    Explorer get(UUID id) {
        return online.computeIfAbsent(id, this::read);
    }

    private Explorer read(UUID id) {
        Explorer e = new Explorer();
        Path f = dir.resolve(id + ".bin");
        if (!Files.isRegularFile(f)) {
            return e;
        }
        try (DataInputStream in = new DataInputStream(new InflaterInputStream(new ByteArrayInputStream(Files.readAllBytes(f))))) {
            int dims = in.readInt();
            for (int d = 0; d < dims && d < 256; d++) {
                String dim = in.readUTF();
                int n = in.readInt();
                if (n < 0 || n > 4_000_000) {
                    throw new IOException("bad region count " + n); // damaged file: never allocate from it
                }
                Long2ObjectOpenHashMap<long[]> m = new Long2ObjectOpenHashMap<>(Math.min(n, 4096));
                for (int i = 0; i < n; i++) {
                    long key = in.readLong();
                    m.put(key, new long[] {in.readLong(), in.readLong(), in.readLong(), in.readLong()});
                }
                e.dims.put(dim, m);
            }
        } catch (IOException | RuntimeException ex) {
            LOGGER.warn("Wayfarers map: could not read {}: {}", f, ex.toString());
        }
        return e;
    }

    /** Writes changed explorers on the worker; {@code forget}: also drop this player from memory (logout). */
    void save(UUID only, boolean forget) {
        for (Map.Entry<UUID, Explorer> en : online.entrySet()) {
            if (only != null && !en.getKey().equals(only) || !en.getValue().dirty) {
                continue;
            }
            Explorer e = en.getValue();
            e.dirty = false;
            ByteArrayOutputStream b = new ByteArrayOutputStream();
            try (DataOutputStream out = new DataOutputStream(new DeflaterOutputStream(b))) {
                out.writeInt(e.dims.size());
                for (Map.Entry<String, Long2ObjectOpenHashMap<long[]>> d : e.dims.entrySet()) {
                    out.writeUTF(d.getKey());
                    out.writeInt(d.getValue().size());
                    for (Long2ObjectMap.Entry<long[]> r : d.getValue().long2ObjectEntrySet()) {
                        out.writeLong(r.getLongKey());
                        for (long l : r.getValue()) {
                            out.writeLong(l);
                        }
                    }
                }
            } catch (IOException ex) {
                continue;
            }
            byte[] bytes = b.toByteArray();
            Path f = dir.resolve(en.getKey() + ".bin");
            MapServer.worker().execute(() -> {
                try {
                    Files.createDirectories(dir);
                    Path tmp = f.resolveSibling(f.getFileName() + ".tmp");
                    Files.write(tmp, bytes);
                    Files.move(tmp, f, StandardCopyOption.REPLACE_EXISTING);
                } catch (IOException ex) {
                    LOGGER.warn("Wayfarers map: could not save {}: {}", f, ex.toString());
                }
            });
        }
        if (forget && only != null) {
            online.remove(only);
        }
    }
}
