package com.brasshaven.client.map;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.brasshaven.map.MapScan;
import com.brasshaven.map.RegionData;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.renderer.texture.DynamicTexture;

import java.util.Arrays;

/**
 * The world map's tilted "3D" view: the explored land seen from the south at a slant, every column raised to its
 * height, with the south faces of steps and cliffs drawn as darker walls. The GUI only draws rectangles and
 * textures, so it is rendered on the CPU (one pass per screen column, near to far, each pixel written once) into a
 * texture the size of the map area, from the region textures already shaded by {@link MapShade}. It is redrawn only
 * when the view or the map data changed, at most ~30 times a second, in a few milliseconds.
 *
 * <p>Projection (GUI px, {@code s} px per block): x = mid + (wx - cx) s; y = mid + (wz - cz) s DEPTH - (wy - ref) s
 * RISE. {@link #zAt} gives back the block row under a pixel, for clicks.
 */
final class MapView3D {
    /** Squash of the ground's north-south axis (the view looks down at about 45 degrees). */
    static final float DEPTH = 0.72F;
    /** Screen height of one block of height, per block of ground: a little exaggerated, Minecraft hills are low. */
    static final float RISE = 0.9F;
    /** Height range searched above / below the reference height (blocks). */
    /** At the edge of the explored land, the cut goes down to this height: the map looks like a model on the table. */
    private static final int EDGE_BASE = 58;
    private static final int ABOVE = 128;
    private static final int BELOW = 96;
    private static final long MIN_INTERVAL_MS = 33;

    private DynamicTexture tex;
    private int w;
    private int h;
    private int[] buf = new int[0];
    private int[] zbuf = new int[0];
    private boolean valid;

    // what the texture shows
    private double kx = Double.NaN;
    private double kz;
    private float ks;
    private int kref;
    private int kbakes;
    private long lastRender;

    /** Regions (inclusive) the view can show: asked for at full resolution and their textures kept built. */
    static int[] regions(double cx, double cz, float s, int w, int h, int ref) {
        double halfX = w / 2.0 / s;
        double near = (h / 2.0 + ABOVE * s * RISE) / (s * DEPTH);
        double far = (h / 2.0 + BELOW * s * RISE) / (s * DEPTH);
        return new int[] {(int) Math.floor((cx - halfX) / MapTile.SIZE), (int) Math.floor((cz - far) / MapTile.SIZE),
                (int) Math.floor((cx + halfX) / MapTile.SIZE), (int) Math.floor((cz + near) / MapTile.SIZE)};
    }

    /**
     * Draws the view of {@code layer} centred on (cx, cz) at {@code s} GUI px per block into (x, y, w, h), with ground
     * at height {@code ref} at the centre line. Redrawn when something changed (throttled while it keeps changing).
     */
    void draw(GuiGraphicsExtractor g, MapLayer layer, double cx, double cz, float s, int x, int y, int w, int h, int ref) {
        if (w <= 0 || h <= 0) {
            return;
        }
        long now = System.currentTimeMillis();
        boolean changed = w != this.w || h != this.h || cx != kx || cz != kz || s != ks || ref != kref || MapLayer.bakes != kbakes;
        if (changed && (now - lastRender >= MIN_INTERVAL_MS || !valid || w != this.w || h != this.h)) {
            render(layer, cx, cz, s, w, h, ref);
            lastRender = now;
        }
        if (tex != null && valid) {
            g.blit(tex.getTextureView(), RenderSystem.getSamplerCache().getClampToEdge(FilterMode.NEAREST), x, y, x + w, y + h, 0, 1, 0, 1);
        }
    }

    /** The block row (world z) drawn at map pixel (px, py) from the map's top-left corner, else Integer.MIN_VALUE. */
    int zAt(int px, int py) {
        if (!valid || px < 0 || py < 0 || px >= w || py >= h) {
            return Integer.MIN_VALUE;
        }
        return zbuf[py * w + px];
    }

    void close() {
        if (tex != null) {
            tex.close();
            tex = null;
        }
        valid = false;
    }

    private void render(MapLayer layer, double cx, double cz, float s, int w, int h, int ref) {
        if (tex == null || this.w != w || this.h != h) {
            if (tex != null) {
                tex.close();
            }
            tex = new DynamicTexture(() -> "brasshaven map 3d view", w, h, true);
            buf = new int[w * h];
            zbuf = new int[w * h];
            this.w = w;
            this.h = h;
        }
        kx = cx;
        kz = cz;
        ks = s;
        kref = ref;
        kbakes = MapLayer.bakes;
        Arrays.fill(buf, 0);
        Arrays.fill(zbuf, Integer.MIN_VALUE);
        float mid = h / 2.0F;
        float depth = s * DEPTH;
        float rise = s * RISE;
        int zNear = (int) Math.ceil(cz + (mid + ABOVE * rise) / depth);
        int zFar = (int) Math.floor(cz - (mid + BELOW * rise) / depth);
        // zoomed out, a row of pixels holds several blocks: one in `step` is enough
        int step = Math.max(1, (int) (1.0F / depth));
        zNear = Math.floorDiv(zNear, step) * step;
        for (int px = 0; px < w; px++) {
            int bx = (int) Math.floor(cx + (px + 0.5 - w / 2.0) / s);
            int rx = bx >> MapTile.SHIFT;
            int lx = bx & MapTile.MASK;
            int top = h; // rows top.. h-1 of this column are drawn
            int nearH = Integer.MIN_VALUE; // height of the cell just in front (MIN: nothing known there)
            int cachedRz = Integer.MIN_VALUE;
            RegionData data = null;
            NativeImage img = null;
            for (int bz = zNear; bz >= zFar && top > 0; bz -= step) {
                int rz = bz >> MapTile.SHIFT;
                if (rz != cachedRz) {
                    cachedRz = rz;
                    MapTile t = layer.peek(rx, rz);
                    data = t == null ? null : t.full;
                    img = data == null || t.texture == null ? null : t.texture.getPixels();
                }
                if (data == null || img == null) {
                    nearH = Integer.MIN_VALUE;
                    continue;
                }
                int lz = bz & MapTile.MASK;
                int i = (lz << MapTile.SHIFT) | lx;
                if ((data.mat[i] & 0xFF) <= MapScan.VOID) {
                    nearH = Integer.MIN_VALUE;
                    continue;
                }
                int color = img.getPixel(lx, lz);
                if ((color >>> 24) == 0) {
                    nearH = Integer.MIN_VALUE;
                    continue;
                }
                int hh = data.height[i];
                // the top face spans the cell's north edge to its south edge; the wall under it goes down to the top
                // of the cell in front (or to EDGE_BASE at the edge of the explored land)
                float yFar = mid + (float) ((bz - cz) * depth) - (hh + 1 - ref) * rise;
                int y0 = Math.round(yFar);
                int yFace = Math.max(y0 + 1, Math.round(yFar + step * depth));
                int base = nearH == Integer.MIN_VALUE ? Math.min(hh - 2, EDGE_BASE) : Math.min(hh, nearH);
                int yBase = Math.round(mid + (float) ((bz + step - cz) * depth) - (base + 1 - ref) * rise);
                int from = Math.max(0, y0);
                int to = Math.min(top, Math.max(yFace, yBase));
                if (from < to) {
                    int wall = (data.mat[i] & 0xFF) == MapScan.WATER ? MapPalette.scale(color, 0.7F)
                            : MapPalette.scale(MapPalette.mix(color, 0xFF5B4630, 0.45F), 0.62F);
                    for (int yy = from; yy < to; yy++) {
                        int o = yy * w + px;
                        if (yy < yFace) {
                            buf[o] = color;
                        } else {
                            // walls darken going down
                            float k = Math.min(1.0F, (yy - yFace) / Math.max(4.0F, rise * 10));
                            buf[o] = MapPalette.scale(wall, 1.0F - 0.22F * k);
                        }
                        zbuf[o] = bz;
                    }
                    top = from;
                }
                nearH = hh;
            }
        }
        NativeImage out = tex.getPixels();
        for (int yy = 0; yy < h; yy++) {
            for (int xx = 0; xx < w; xx++) {
                out.setPixel(xx, yy, buf[yy * w + xx]);
            }
        }
        tex.upload();
        valid = true;
    }
}
