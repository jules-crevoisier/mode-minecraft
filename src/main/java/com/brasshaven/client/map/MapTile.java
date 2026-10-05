package com.brasshaven.client.map;

import com.brasshaven.map.RegionData;
import net.minecraft.client.renderer.texture.DynamicTexture;

/**
 * Client copy of one 256 x 256 block region: the full column data while it is on screen, or just a 64 x 64
 * thumbnail when the world map is zoomed out. GPU textures are made on demand and only re-uploaded where columns
 * changed.
 */
final class MapTile {
    static final int SHIFT = RegionData.REGION_SHIFT;
    static final int SIZE = RegionData.REGION;
    static final int MASK = SIZE - 1;
    static final int MINI = RegionData.MINI;

    final int rx;
    final int rz;

    /** Full data (null until received, or after eviction). */
    RegionData full;
    /** Revisions the client holds (0: none). */
    int fullRev;
    int miniRev;
    long fullAsked;
    long miniAsked;
    long lastUse;

    // full texture
    DynamicTexture texture;
    int dirtyMinX;
    int dirtyMinZ;
    int dirtyMaxX = MASK;
    int dirtyMaxZ = MASK;
    long lastUpload;
    long lastTextureUse;

    // thumbnail: ARGB, kept after the full data is evicted
    int[] mini;
    boolean miniStale = true;
    DynamicTexture miniTexture;
    boolean miniTextureDirty = true;
    long lastMiniUse;

    MapTile(int rx, int rz) {
        this.rx = rx;
        this.rz = rz;
    }

    void markDirty(int x0, int z0, int x1, int z1) {
        dirtyMinX = Math.min(dirtyMinX, Math.max(0, x0));
        dirtyMinZ = Math.min(dirtyMinZ, Math.max(0, z0));
        dirtyMaxX = Math.max(dirtyMaxX, Math.min(MASK, x1));
        dirtyMaxZ = Math.max(dirtyMaxZ, Math.min(MASK, z1));
        miniStale = true;
    }

    void markAllDirty() {
        markDirty(0, 0, MASK, MASK);
    }

    boolean textureDirty() {
        return dirtyMaxX >= dirtyMinX;
    }

    void clearTextureDirty() {
        dirtyMinX = SIZE;
        dirtyMinZ = SIZE;
        dirtyMaxX = -1;
        dirtyMaxZ = -1;
    }

    void closeTexture() {
        if (texture != null) {
            MapRenderer.close(texture);
            texture = null;
        }
    }

    void closeMiniTexture() {
        if (miniTexture != null) {
            MapRenderer.close(miniTexture);
            miniTexture = null;
        }
    }

    void close() {
        closeTexture();
        closeMiniTexture();
    }
}
