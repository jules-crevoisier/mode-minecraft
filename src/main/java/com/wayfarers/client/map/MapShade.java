package com.wayfarers.client.map;

import com.wayfarers.config.WayfarersClientConfig;
import com.wayfarers.map.MapScan;
import com.wayfarers.map.RegionData;

/**
 * The relief baked into the map textures, from the explored column heights (no extra data: the server already
 * sends a height and a water depth per column). Computed once per texture build, never per frame.
 *
 * <ul>
 *   <li>hill-shading: the surface normal from the four neighbours, lit from the north-west at 45 degrees;</li>
 *   <li>valleys: a column lower than the ground 4 blocks around it is darker, a ridge a little lighter;</li>
 *   <li>height tint: high ground turns paler (hypsometric tint), land below sea level a little darker;</li>
 *   <li>water: the depth gradient is in {@link MapPalette}; here the sea bed's own relief shows faintly through
 *   shallow water and shores get a light rim;</li>
 *   <li>contour lines (option): every 16 blocks, a bolder one every 64, not on tree tops.</li>
 * </ul>
 *
 * tools/wf/worldmap.py shade_grid() is the same code for the mockups: keep them in step.
 */
final class MapShade {
    static final int UNKNOWN = Integer.MIN_VALUE;
    static final byte NONE = 0;
    static final byte LAND = 1;
    static final byte WATER = 2;
    static final byte TREE = 3;
    static final byte WALL = 4;
    /** Reach of the shading in columns (the valley test): a change re-shades this far around it. */
    static final int REACH = 4;
    private static final float INV_FLAT = (float) (1.0 / Math.sqrt(0.5));

    private static WayfarersClientConfig.MapRelief relief;
    private static boolean contours;
    private static float strength;
    private static int version;

    private MapShade() {}

    /** Reads the style from the config; true (and a new {@link #version()}) when it changed since the last call. */
    static boolean refresh() {
        WayfarersClientConfig.MapRelief r = WayfarersClientConfig.MAP_RELIEF.get();
        boolean c = WayfarersClientConfig.MAP_CONTOURS.get();
        if (r == relief && c == contours) {
            return false;
        }
        boolean first = relief == null;
        relief = r;
        contours = c;
        strength = switch (r) {
            case FLAT -> 0.0F;
            case NORMAL -> 0.6F;
            case STRONG -> 1.0F;
        };
        version++;
        return !first;
    }

    static int version() {
        if (relief == null) {
            refresh();
        }
        return version;
    }

    static byte kind(int mat) {
        if (mat <= MapScan.VOID) {
            return NONE;
        }
        return switch (mat) {
            case MapScan.WATER -> WATER;
            case MapScan.WALL -> WALL;
            case MapScan.FOLIAGE, MapScan.SPRUCE, MapScan.BIRCH -> TREE;
            default -> LAND;
        };
    }

    /** Fills one column of the scratch grid from {@code d} (column {@code i}); unknown columns get {@link #UNKNOWN}. */
    static void column(RegionData d, int i, Grid g, int o) {
        int m = d.mat[i] & 0xFF;
        byte k = kind(m);
        g.kind[o] = k;
        if (k == NONE) {
            g.h[o] = UNKNOWN;
            g.floor[o] = UNKNOWN;
            return;
        }
        g.h[o] = d.height[i];
        g.floor[o] = k == WATER ? d.height[i] - d.depth[i] : d.height[i];
        g.depth[o] = d.depth[i];
    }

    /** Scratch arrays for one bake: the area plus a {@link #REACH} margin, row length {@code stride}. */
    static final class Grid {
        int stride;
        int[] h = new int[0];
        int[] floor = new int[0];
        int[] depth = new int[0];
        byte[] kind = new byte[0];

        void size(int w, int hgt) {
            stride = w;
            int n = w * hgt;
            if (h.length < n) {
                h = new int[n];
                floor = new int[n];
                depth = new int[n];
                kind = new byte[n];
            }
            java.util.Arrays.fill(h, 0, n, UNKNOWN);
            java.util.Arrays.fill(floor, 0, n, UNKNOWN);
            java.util.Arrays.fill(kind, 0, n, NONE);
        }
    }

    /**
     * The shaded colour of grid cell {@code o} whose unshaded colour is {@code base}. {@code step}: blocks between two
     * cells (1, or 4 for thumbnails); {@code surface}: the overworld-style map (the cave view gets no height tint).
     */
    static int shade(int base, Grid g, int o, int step, boolean surface) {
        if (base == 0) {
            return 0;
        }
        byte k = g.kind[o];
        if (k == WALL || k == NONE) {
            return base;
        }
        int s = g.stride;
        int far = Math.max(1, REACH / step);
        float f = 1.0F;
        if (k == WATER) {
            if (strength > 0) {
                // the sea bed's relief, fading with depth
                int fh = g.floor[o];
                float light = light(fh, bed(g, o - 1, fh), bed(g, o + 1, fh), bed(g, o - s, fh), bed(g, o + s, fh), step);
                float fade = Math.max(0.0F, 1.0F - g.depth[o] / 24.0F);
                f += strength * 0.35F * fade * (light - 1.0F);
                if (land(g, o - 1) || land(g, o + 1) || land(g, o - s) || land(g, o + s)) {
                    // a pale rim along the shore
                    return MapPalette.mix(MapPalette.scale(base, f), 0xFFEFF6EE, 0.22F * strength + 0.06F);
                }
            }
            return MapPalette.scale(base, f);
        }
        int h = g.h[o];
        if (strength > 0) {
            float light = light(h, at(g, o - 1, h), at(g, o + 1, h), at(g, o - s, h), at(g, o + s, h), step);
            f += strength * 0.62F * (light - 1.0F);
            // valleys darker, ridges a little lighter
            int[] hh = g.h;
            int a = hh[o - far];
            int b = hh[o + far];
            int cc = hh[o - far * s];
            int d = hh[o + far * s];
            int n = (a != UNKNOWN ? 1 : 0) + (b != UNKNOWN ? 1 : 0) + (cc != UNKNOWN ? 1 : 0) + (d != UNKNOWN ? 1 : 0);
            if (n > 0) {
                long sum = (a != UNKNOWN ? a : 0L) + (b != UNKNOWN ? b : 0L) + (cc != UNKNOWN ? cc : 0L) + (d != UNKNOWN ? d : 0L);
                float curve = Math.max(-0.6F, Math.min(1.0F, (sum / (float) n - h) / 10.0F));
                f *= 1.0F - (curve > 0 ? 0.16F : 0.08F) * strength * curve;
            }
            f = Math.max(0.42F, Math.min(1.36F, f));
        }
        int c = MapPalette.scale(base, f);
        if (surface && strength > 0) {
            if (h > 68) {
                c = MapPalette.mix(c, 0xFFF3EBDA, Math.min(1.0F, (h - 68) / 150.0F) * 0.34F);
            } else if (h < 62) {
                c = MapPalette.scale(c, 1.0F - Math.min(1.0F, (62 - h) / 40.0F) * 0.14F);
            }
        }
        if (contours && k == LAND) {
            int band = Math.floorDiv(h, 16);
            int major = Math.floorDiv(h, 64);
            int line = Math.max(Math.max(contour(g, o - 1, band, major), contour(g, o + 1, band, major)),
                    Math.max(contour(g, o - s, band, major), contour(g, o + s, band, major)));
            if (line > 0) {
                c = MapPalette.scale(c, line == 2 ? 0.66F : 0.80F);
            }
        }
        return c;
    }

    /** 0: no contour between this column and q; 1: a contour line (q is in a lower 16-block band); 2: a bold one. */
    private static int contour(Grid g, int q, int band, int major) {
        if (g.h[q] == UNKNOWN || g.kind[q] == TREE || g.kind[q] == NONE || Math.floorDiv(g.h[q], 16) >= band) {
            return 0;
        }
        return Math.floorDiv(g.h[q], 64) < major ? 2 : 1;
    }

    private static boolean land(Grid g, int q) {
        return g.kind[q] == LAND || g.kind[q] == TREE;
    }

    private static int at(Grid g, int q, int fallback) {
        return g.h[q] == UNKNOWN ? fallback : g.h[q];
    }

    private static int bed(Grid g, int q, int fallback) {
        return g.kind[q] == WATER ? g.floor[q] : fallback;
    }

    /** Lambert light of the surface at height h (1 on flat ground, up to ~1.4 facing the light, 0 turned away). */
    private static float light(int h, int west, int east, int north, int south, int step) {
        float k = step > 1 ? 1.5F : 1.0F;
        float gx = (east - west) / (2.0F * step) * k;
        float gz = (south - north) / (2.0F * step) * k;
        float dot = (0.5F * gx + 0.70710678F + 0.5F * gz) / (float) Math.sqrt(gx * gx + 1.0F + gz * gz);
        return Math.max(0.0F, dot) * INV_FLAT;
    }
}
