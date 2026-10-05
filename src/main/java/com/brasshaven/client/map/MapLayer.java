package com.brasshaven.client.map;

import com.mojang.blaze3d.platform.NativeImage;
import com.brasshaven.map.MapScan;
import com.brasshaven.map.RegionData;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import net.minecraft.client.renderer.texture.DynamicTexture;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * The regions of one map on the client: a dimension's shared map (filled by the server) or the live cave view
 * (scanned locally). Builds the GPU textures with relief shading, re-uploads only changed regions (throttled) and
 * keeps memory bounded by evicting what has not been looked at for a while.
 */
final class MapLayer {
    private static final int MAX_FULL = 72;
    private static final int MAX_TEXTURES = 96;
    private static final int MAX_MINI_TEXTURES = 1500;
    /** Regions known at all (mostly 64 x 64 thumbnails); beyond this the least recently seen are forgotten. */
    private static final int MAX_TILES = 4096;
    private static final long UPLOAD_INTERVAL_MS = 150;
    /** Texture builds per ~frame (16 ms): each costs about a millisecond. */
    private static final int UPLOADS_PER_FRAME = 2;

    final String dim;
    /** Cave view: scanned on this client, never asked from the server. */
    final boolean local;
    private final Long2ObjectOpenHashMap<MapTile> tiles = new Long2ObjectOpenHashMap<>();
    /** Scratch of the bakes (render thread only). */
    private static final MapShade.Grid GRID = new MapShade.Grid();
    private static int[] scratch = new int[MapTile.SIZE * MapTile.SIZE];
    /** Texture builds so far, all layers: the 3D view redraws when it changes. */
    static int bakes;
    private int uploads;
    private long frame;

    MapLayer(String dim, boolean local) {
        this.dim = dim;
        this.local = local;
    }

    MapTile peek(int rx, int rz) {
        return tiles.get(RegionData.key(rx, rz));
    }

    MapTile tile(int rx, int rz) {
        return tiles.computeIfAbsent(RegionData.key(rx, rz), k -> new MapTile(rx, rz));
    }

    Iterable<MapTile> all() {
        return tiles.values();
    }

    /** Full data for local scanning (allocated if needed). */
    RegionData localData(int rx, int rz) {
        MapTile t = tile(rx, rz);
        if (t.full == null) {
            t.full = new RegionData(MapTile.SIZE);
            t.markAllDirty();
        }
        t.lastUse = System.currentTimeMillis();
        return t.full;
    }

    // ------------------------------------------------------------------ data from the server
    void receiveFull(int rx, int rz, RegionData d) {
        if (d.size != MapTile.SIZE) {
            return;
        }
        MapTile t = tile(rx, rz);
        t.full = d;
        t.fullRev = d.revision;
        t.miniRev = Math.max(t.miniRev, d.revision);
        t.lastUse = System.currentTimeMillis();
        // its own columns, and the relief along the edges of the regions around it
        markDirty(rx << MapTile.SHIFT, rz << MapTile.SHIFT, (rx << MapTile.SHIFT) + MapTile.MASK, (rz << MapTile.SHIFT) + MapTile.MASK);
    }

    void receiveMini(int rx, int rz, RegionData d) {
        if (d.size != MapTile.MINI) {
            return;
        }
        MapTile t = tile(rx, rz);
        t.miniRev = d.revision;
        if (t.full != null) {
            return; // the thumbnail is built from the full data
        }
        int[][] tints = MapPalette.resolve(d.palette());
        int[] out = new int[MapTile.MINI * MapTile.MINI];
        int r = MapShade.REACH;
        int w = MapTile.MINI + 2 * r;
        MapShade.Grid g = GRID;
        g.size(w, w);
        for (int z = 0; z < MapTile.MINI; z++) {
            for (int x = 0; x < MapTile.MINI; x++) {
                MapShade.column(d, z * MapTile.MINI + x, g, (z + r) * w + x + r);
            }
        }
        for (int z = 0; z < MapTile.MINI; z++) {
            for (int x = 0; x < MapTile.MINI; x++) {
                int i = z * MapTile.MINI + x;
                out[i] = MapShade.shade(MapPalette.color(d, i, tints), g, (z + r) * w + x + r, 4, !local);
            }
        }
        t.mini = out;
        t.miniStale = false;
        t.miniTextureDirty = true;
    }

    /** A freshly scanned chunk; only applied over full data (the revision follows only when no update was missed). */
    void receiveChunk(int cx, int cz, RegionData d) {
        MapTile t = peek(cx >> 4, cz >> 4);
        if (t == null || t.full == null || d.size != 16) {
            return;
        }
        t.full.paste(d, (cx & 15) << 4, (cz & 15) << 4);
        if (d.revision == t.fullRev + 1) {
            t.fullRev = d.revision;
        }
        markDirty(cx << 4, cz << 4, (cx << 4) + 15, (cz << 4) + 15);
    }

    /** A block area changed: its pixels and the relief of the columns around it (in this region or the next). */
    void markDirty(int x0, int z0, int x1, int z1) {
        int r = MapShade.REACH;
        x0 -= r;
        z0 -= r;
        x1 += r;
        z1 += r;
        for (int rz = z0 >> MapTile.SHIFT; rz <= z1 >> MapTile.SHIFT; rz++) {
            for (int rx = x0 >> MapTile.SHIFT; rx <= x1 >> MapTile.SHIFT; rx++) {
                MapTile t = peek(rx, rz);
                if (t != null && t.full != null) {
                    int bx = rx << MapTile.SHIFT;
                    int bz = rz << MapTile.SHIFT;
                    t.markDirty(x0 - bx, z0 - bz, x1 - bx, z1 - bz);
                }
            }
        }
    }

    /** The relief settings changed: every texture is shaded again (thumbnails without full data are asked anew). */
    void restyle() {
        for (MapTile t : tiles.values()) {
            if (t.full != null) {
                t.markAllDirty();
            } else if (t.mini != null) {
                t.miniRev = 0;
                t.miniAsked = 0;
            }
        }
    }

    // ------------------------------------------------------------------ queries
    /** Full data of the region holding block (wx, wz), or null. */
    RegionData fullAt(int wx, int wz) {
        MapTile t = peek(wx >> MapTile.SHIFT, wz >> MapTile.SHIFT);
        return t == null ? null : t.full;
    }

    /** {height, biome id} of a known column, else null. */
    Object[] columnAt(int wx, int wz) {
        MapTile t = peek(wx >> MapTile.SHIFT, wz >> MapTile.SHIFT);
        if (t == null || t.full == null) {
            return null;
        }
        int i = ((wz & MapTile.MASK) << MapTile.SHIFT) | (wx & MapTile.MASK);
        if ((t.full.mat[i] & 0xFF) <= MapScan.VOID) {
            return null;
        }
        return new Object[] {(int) t.full.height[i], t.full.biomeAt(i)};
    }

    // ------------------------------------------------------------------ shading
    /**
     * Shaded colours (see {@link MapShade}) of the columns x0..x1, z0..z1 of {@code t}'s full data into {@code out},
     * row by row; the relief reads the neighbouring regions along the edges.
     */
    private void bake(MapTile t, int x0, int z0, int x1, int z1, int[] out) {
        int r = MapShade.REACH;
        int w = x1 - x0 + 1 + 2 * r;
        int h = z1 - z0 + 1 + 2 * r;
        MapShade.Grid g = GRID;
        g.size(w, h);
        MapTile[] near = new MapTile[9];
        for (int dz = -1; dz <= 1; dz++) {
            for (int dx = -1; dx <= 1; dx++) {
                near[(dz + 1) * 3 + dx + 1] = dx == 0 && dz == 0 ? t : peek(t.rx + dx, t.rz + dz);
            }
        }
        for (int gz = 0; gz < h; gz++) {
            int lz = z0 - r + gz;
            int tz = lz < 0 ? 0 : lz > MapTile.MASK ? 2 : 1;
            for (int gx = 0; gx < w; gx++) {
                int lx = x0 - r + gx;
                MapTile n = near[tz * 3 + (lx < 0 ? 0 : lx > MapTile.MASK ? 2 : 1)];
                if (n != null && n.full != null) {
                    MapShade.column(n.full, ((lz & MapTile.MASK) << MapTile.SHIFT) | (lx & MapTile.MASK), g, gz * w + gx);
                }
            }
        }
        int[][] tints = MapPalette.resolve(t.full.palette());
        int ow = x1 - x0 + 1;
        for (int z = z0; z <= z1; z++) {
            for (int x = x0; x <= x1; x++) {
                int base = MapPalette.color(t.full, (z << MapTile.SHIFT) | x, tints);
                out[(z - z0) * ow + x - x0] = MapShade.shade(base, g, (z - z0 + r) * w + x - x0 + r, 1, !local);
            }
        }
    }

    // ------------------------------------------------------------------ textures
    private boolean mayUpload() {
        long now = System.nanoTime() / 16_000_000L;
        if (now != frame) {
            frame = now;
            uploads = 0;
        }
        return uploads < UPLOADS_PER_FRAME;
    }

    /** Full-resolution texture, refreshed where it changed (throttled); null when there is nothing yet. */
    DynamicTexture texture(MapTile t) {
        long now = System.currentTimeMillis();
        t.lastUse = now;
        t.lastTextureUse = now;
        if (t.full == null) {
            return t.texture;
        }
        boolean fresh = t.texture == null;
        if (fresh) {
            if (!mayUpload()) {
                return null;
            }
            t.texture = new DynamicTexture(() -> "brasshaven map " + t.rx + "," + t.rz, MapTile.SIZE, MapTile.SIZE, true);
            t.markAllDirty();
        }
        if (t.textureDirty() && (fresh || now - t.lastUpload >= UPLOAD_INTERVAL_MS) && mayUpload()) {
            uploads++;
            bakes++;
            NativeImage img = t.texture.getPixels();
            bake(t, t.dirtyMinX, t.dirtyMinZ, t.dirtyMaxX, t.dirtyMaxZ, scratch);
            int ow = t.dirtyMaxX - t.dirtyMinX + 1;
            for (int z = t.dirtyMinZ; z <= t.dirtyMaxZ; z++) {
                for (int x = t.dirtyMinX; x <= t.dirtyMaxX; x++) {
                    img.setPixel(x, z, scratch[(z - t.dirtyMinZ) * ow + x - t.dirtyMinX]);
                }
            }
            t.clearTextureDirty();
            t.texture.upload();
            t.lastUpload = now;
        }
        return t.texture;
    }

    /** 64 x 64 thumbnail texture (zoomed-out world map); null when there is none yet. */
    DynamicTexture miniTexture(MapTile t) {
        long now = System.currentTimeMillis();
        t.lastMiniUse = now;
        if (t.full != null && (t.mini == null || t.miniStale && now - t.lastUpload >= 1000) && mayUpload()) {
            uploads++;
            buildMini(t);
            t.lastUpload = now;
        }
        if (t.mini == null) {
            return null;
        }
        if (t.miniTexture == null) {
            t.miniTexture = new DynamicTexture(() -> "brasshaven map mini " + t.rx + "," + t.rz, MapTile.MINI, MapTile.MINI, true);
            t.miniTextureDirty = true;
        }
        if (t.miniTextureDirty) {
            NativeImage img = t.miniTexture.getPixels();
            for (int z = 0; z < MapTile.MINI; z++) {
                for (int x = 0; x < MapTile.MINI; x++) {
                    img.setPixel(x, z, t.mini[z * MapTile.MINI + x]);
                }
            }
            t.miniTexture.upload();
            t.miniTextureDirty = false;
        }
        return t.miniTexture;
    }

    private void buildMini(MapTile t) {
        bake(t, 0, 0, MapTile.MASK, MapTile.MASK, scratch);
        int[] out = t.mini != null ? t.mini : new int[MapTile.MINI * MapTile.MINI];
        for (int z = 0; z < MapTile.MINI; z++) {
            for (int x = 0; x < MapTile.MINI; x++) {
                int r = 0;
                int g = 0;
                int b = 0;
                int n = 0;
                for (int dz = 1; dz < 4; dz += 2) {
                    for (int dx = 1; dx < 4; dx += 2) {
                        int c = scratch[((z * 4 + dz) << MapTile.SHIFT) | (x * 4 + dx)];
                        if (c != 0) {
                            r += (c >> 16) & 0xFF;
                            g += (c >> 8) & 0xFF;
                            b += c & 0xFF;
                            n++;
                        }
                    }
                }
                out[z * MapTile.MINI + x] = n < 2 ? 0 : 0xFF000000 | (r / n) << 16 | (g / n) << 8 | (b / n);
            }
        }
        t.mini = out;
        t.miniStale = false;
        t.miniTextureDirty = true;
    }

    // ------------------------------------------------------------------ memory
    /** Drops the least recently used data and textures (never the player's own region and its neighbours). */
    void evict(int prx, int prz) {
        List<MapTile> full = new ArrayList<>();
        List<MapTile> tex = new ArrayList<>();
        List<MapTile> minis = new ArrayList<>();
        for (MapTile t : tiles.values()) {
            if (t.full != null) {
                full.add(t);
            }
            if (t.texture != null) {
                tex.add(t);
            }
            if (t.miniTexture != null) {
                minis.add(t);
            }
        }
        long now = System.currentTimeMillis();
        if (tex.size() > MAX_TEXTURES) {
            tex.sort(Comparator.comparingLong(t -> t.lastTextureUse));
            for (int i = 0; i < tex.size() - MAX_TEXTURES; i++) {
                if (now - tex.get(i).lastTextureUse > 2000) {
                    tex.get(i).closeTexture();
                }
            }
        }
        if (minis.size() > MAX_MINI_TEXTURES) {
            minis.sort(Comparator.comparingLong(t -> t.lastMiniUse));
            for (int i = 0; i < minis.size() - MAX_MINI_TEXTURES; i++) {
                minis.get(i).closeMiniTexture();
            }
        }
        if (!local && tiles.size() > MAX_TILES) {
            // thumbnails (16 KB each) of everything ever looked at: forget the longest unseen, they are asked again
            List<MapTile> idle = new ArrayList<>();
            for (MapTile t : tiles.values()) {
                if (t.full == null && t.texture == null) {
                    idle.add(t);
                }
            }
            idle.sort(Comparator.comparingLong(MapLayer::lastSeen));
            for (int i = 0; i < idle.size() && tiles.size() > MAX_TILES * 3 / 4; i++) {
                MapTile t = idle.get(i);
                if (now - lastSeen(t) < 5000) {
                    break;
                }
                t.close();
                tiles.remove(RegionData.key(t.rx, t.rz));
            }
        }
        if (full.size() > MAX_FULL) {
            full.sort(Comparator.comparingLong(t -> t.lastUse));
            int drop = full.size() - MAX_FULL;
            for (MapTile t : full) {
                if (drop <= 0) {
                    break;
                }
                if (Math.abs(t.rx - prx) <= 1 && Math.abs(t.rz - prz) <= 1 || now - t.lastUse < 5000) {
                    continue;
                }
                if (local) {
                    t.close();
                    tiles.remove(RegionData.key(t.rx, t.rz));
                } else {
                    if (t.mini == null || t.miniStale) {
                        buildMini(t);
                    }
                    t.full = null;
                    t.fullRev = 0;
                    t.fullAsked = 0;
                    t.closeTexture();
                }
                drop--;
            }
        }
    }

    /** Frees the GPU textures (rebuilt from the data when drawn again): this layer's dimension was left. */
    void closeTextures() {
        for (MapTile t : tiles.values()) {
            t.close(); // texture() / miniTexture() refill a new one entirely
        }
    }

    private static long lastSeen(MapTile t) {
        return Math.max(Math.max(t.lastUse, t.lastMiniUse), Math.max(t.fullAsked, t.miniAsked));
    }

    void clear() {
        for (MapTile t : tiles.values()) {
            t.close();
        }
        tiles.clear();
    }
}
