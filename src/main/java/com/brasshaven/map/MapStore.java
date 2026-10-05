package com.brasshaven.map;

import com.mojang.logging.LogUtils;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongArrayList;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * The shared map of one dimension on the server: 256 x 256 block regions kept in memory while players are around
 * them, read and written on the map worker thread (world/data/brasshaven_map/&lt;dimension&gt;/r.X.Z.bin, the deflated
 * {@link RegionData} encoding). Nothing here touches the disk on the server thread.
 */
final class MapStore {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final int MAX_REGIONS = 160;
    /** Remembered "no file there" answers (bounded: a client may ask for any coordinates). */
    private static final int MAX_MISSING = 65536;
    /** A region file is ~100 KB; anything much larger is damaged (and must not be read into memory whole). */
    private static final long MAX_FILE = 4L << 20;

    /** In-memory state of a region. */
    static final class Region {
        final long key;
        RegionData data;
        boolean loading;
        boolean create;
        boolean dirty;
        long lastUse;
        /** Server game time of each chunk's last scan (session only). */
        final long[] scannedAt = new long[256];
        /** Chunks that waited for the region to load. */
        LongArrayList waiting;
        byte[] fullCache;
        int fullCacheRev = -1;
        byte[] miniCache;
        int miniCacheRev = -1;

        Region(long key) {
            this.key = key;
        }

        boolean ready() {
            return data != null && !loading;
        }
    }

    enum State { READY, LOADING, MISSING }

    final String dimId;
    private final Path dir;
    private final Long2ObjectOpenHashMap<Region> regions = new Long2ObjectOpenHashMap<>();
    private final LongOpenHashSet missing = new LongOpenHashSet();
    private final ConcurrentLinkedQueue<Object[]> loaded = new ConcurrentLinkedQueue<>();

    MapStore(String dimId, Path dir) {
        this.dimId = dimId;
        this.dir = dir;
    }

    private Path file(long key) {
        return dir.resolve("r." + RegionData.keyX(key) + "." + RegionData.keyZ(key) + ".bin");
    }

    Region region(long key) {
        Region r = regions.get(key);
        if (r != null) {
            r.lastUse = System.currentTimeMillis();
        }
        return r;
    }

    /**
     * Makes a region available: READY (in memory), LOADING (asked from disk, try again later) or MISSING (never
     * explored; only when {@code create} is false — otherwise an empty region is made).
     */
    State ensure(long key, boolean create) {
        Region r = regions.get(key);
        if (r != null) {
            r.lastUse = System.currentTimeMillis();
            if (r.loading) {
                r.create |= create;
                return State.LOADING;
            }
            return State.READY;
        }
        if (missing.contains(key)) {
            if (!create) {
                return State.MISSING;
            }
            missing.remove(key);
            r = new Region(key);
            r.data = new RegionData(RegionData.REGION);
            r.lastUse = System.currentTimeMillis();
            regions.put(key, r);
            return State.READY;
        }
        r = new Region(key);
        r.loading = true;
        r.create = create;
        r.lastUse = System.currentTimeMillis();
        regions.put(key, r);
        Path f = file(key);
        MapServer.worker().execute(() -> loaded.add(new Object[] {key, read(f)}));
        return State.LOADING;
    }

    private static RegionData read(Path f) {
        if (!Files.isRegularFile(f)) {
            return null;
        }
        try {
            if (Files.size(f) > MAX_FILE) {
                LOGGER.warn("Brasshaven map: ignoring oversized region {}", f);
                return null;
            }
            RegionData d = RegionData.decode(Files.readAllBytes(f));
            if (d == null || d.size != RegionData.REGION) {
                LOGGER.warn("Brasshaven map: ignoring unreadable region {}", f);
                return null;
            }
            return d;
        } catch (IOException | RuntimeException e) {
            // a damaged region is simply rebuilt from the chunks players see
            LOGGER.warn("Brasshaven map: could not read {}: {}", f, e.toString());
            return null;
        }
    }

    /** Server thread: installs finished reads; returns the chunks that waited for them. */
    void pollLoads(LongArrayList readyChunks) {
        Object[] o;
        while ((o = loaded.poll()) != null) {
            long key = (Long) o[0];
            RegionData d = (RegionData) o[1];
            Region r = regions.get(key);
            if (r == null || !r.loading) {
                continue;
            }
            r.loading = false;
            if (d == null) {
                if (!r.create) {
                    regions.remove(key);
                    if (missing.size() >= MAX_MISSING) {
                        missing.clear();
                    }
                    missing.add(key);
                    continue;
                }
                d = new RegionData(RegionData.REGION);
            }
            r.data = d;
            if (r.waiting != null) {
                readyChunks.addAll(r.waiting);
                r.waiting = null;
            }
        }
    }

    /** Queues a write of every changed region (copies are taken now, written on the worker). */
    void save(boolean dropIdle, long idleMs) {
        long now = System.currentTimeMillis();
        List<Long> drop = new ArrayList<>();
        for (Region r : regions.values()) {
            if (!r.ready()) {
                continue;
            }
            if (r.dirty) {
                r.dirty = false;
                RegionData copy = r.data.copy();
                Path f = file(r.key);
                MapServer.worker().execute(() -> write(f, copy.encodeAll()));
            }
            if (dropIdle && now - r.lastUse > idleMs) {
                drop.add(r.key);
            }
        }
        for (long k : drop) {
            regions.remove(k);
        }
    }

    /** Keeps at most MAX_REGIONS in memory: saves and drops the least recently used ones not in {@code keep}. */
    void evict(LongOpenHashSet keep) {
        if (regions.size() <= MAX_REGIONS) {
            return;
        }
        List<Region> list = new ArrayList<>(regions.values());
        list.sort(Comparator.comparingLong(r -> r.lastUse));
        int excess = regions.size() - MAX_REGIONS;
        for (Region r : list) {
            if (excess <= 0) {
                break;
            }
            if (!r.ready() || keep.contains(r.key)) {
                continue;
            }
            if (r.dirty) {
                r.dirty = false;
                RegionData copy = r.data.copy();
                Path f = file(r.key);
                MapServer.worker().execute(() -> write(f, copy.encodeAll()));
            }
            regions.remove(r.key);
            excess--;
        }
    }

    private static void write(Path f, byte[] bytes) {
        try {
            Files.createDirectories(f.getParent());
            Path tmp = f.resolveSibling(f.getFileName() + ".tmp");
            Files.write(tmp, bytes);
            try {
                Files.move(tmp, f, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (java.nio.file.AtomicMoveNotSupportedException e) {
                Files.move(tmp, f, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            LOGGER.warn("Brasshaven map: could not save {}: {}", f, e.toString());
        }
    }

    Long2ObjectMap<Region> regions() {
        return regions;
    }
}
