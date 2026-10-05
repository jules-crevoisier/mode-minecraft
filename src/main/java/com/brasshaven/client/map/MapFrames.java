package com.brasshaven.client.map;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.renderer.texture.DynamicTexture;

/**
 * The minimap's round brass porthole, drawn for the exact size asked (any size from the slider, not a few fixed
 * sprites) into a texture of one texel per GUI pixel, so it is as crisp as the other GUI sprites at every GUI scale.
 * Rebuilt only when the size changes. tools/wf/worldmap.py round_frame() draws the same frame for the mockups.
 */
final class MapFrames {
    /** Frame width around the map, GUI px. */
    static final int BORDER = 6;

    private static final int SOOT = 0xFF0F0C0A;
    private static final int BRASS_HI = 0xFFF1D48A;
    private static final int BRASS_LT = 0xFFD9B25E;
    private static final int BRASS = 0xFFB58A45;
    private static final int BRASS_DK = 0xFF7C5A2B;
    private static final int BRASS_SH = 0xFF4E3819;
    private static final int IRON = 0xFF2B2320;
    private static final int IRON_LT = 0xFF3E3430;
    private static final int IRON_DK = 0xFF17120F;

    private static DynamicTexture round;
    private static int roundSize = -1;

    private MapFrames() {}

    /** The round frame around a map of diameter {@code size} whose frame's top-left corner is (x, y). */
    static void round(GuiGraphicsExtractor g, int x, int y, int size) {
        int n = size + BORDER * 2;
        if (round == null || roundSize != size) {
            if (round != null) {
                round.close();
            }
            round = new DynamicTexture(() -> "brasshaven minimap frame " + size, build(size));
            roundSize = size;
        }
        g.blit(round.getTextureView(), RenderSystem.getSamplerCache().getClampToEdge(FilterMode.NEAREST), x, y, x + n, y + n, 0, 1, 0, 1);
    }

    /** Square riveted iron plate with a round brass porthole of diameter {@code size} (the map shows through). */
    static NativeImage build(int size) {
        int n = size + BORDER * 2;
        NativeImage img = new NativeImage(n, n, true);
        double c = (n - 1) / 2.0;
        double r = size / 2.0;
        double lx = -0.70710678;
        double ly = -0.70710678; // light from the top left
        for (int y = 0; y < n; y++) {
            for (int x = 0; x < n; x++) {
                double dx = x - c;
                double dy = y - c;
                double d = Math.hypot(dx, dy);
                if (d < r - 0.35) {
                    continue; // the hole
                }
                double lit = d == 0 ? 0 : (dx / d) * lx + (dy / d) * ly; // 1 = faces the light
                int col;
                if (d < r + 0.65) {
                    col = SOOT;
                } else if (d < r + 1.65) {
                    // inner lip: lit on the far side (it is a hole)
                    col = mix(BRASS_SH, BRASS_DK, 0.5 - lit * 0.5);
                } else if (d < r + 4.6) {
                    double t = (d - r - 1.65) / 3.0; // 0 inner .. 1 outer
                    int base = mix(BRASS_LT, BRASS, t);
                    col = mix(base, lit > 0 ? BRASS_HI : BRASS_DK, Math.abs(lit) * 0.55);
                } else if (d < r + 5.6) {
                    col = SOOT;
                } else {
                    // iron plate with a faint grain
                    int v = hash(x, y, size);
                    col = v > 20 ? IRON : mix(IRON, v > 10 ? IRON_LT : IRON_DK, 0.6);
                }
                img.setPixel(x, y, col);
            }
        }
        // ticks on the ring every 30 degrees (the cardinal studs sit on 0/90/180/270)
        for (int k = 0; k < 12; k++) {
            if (k % 3 == 0) {
                continue;
            }
            double a = k * Math.PI / 6;
            for (double rr : new double[] {r + 2.6, r + 3.6}) {
                set(img, (int) Math.round(c + Math.sin(a) * rr), (int) Math.round(c - Math.cos(a) * rr), BRASS_SH);
            }
        }
        // plate edge (soot, then an iron bevel) and four rivets
        for (int i = 0; i < n; i++) {
            set(img, i, 0, SOOT);
            set(img, i, n - 1, SOOT);
            set(img, 0, i, SOOT);
            set(img, n - 1, i, SOOT);
        }
        for (int i = 1; i < n - 1; i++) {
            set(img, i, 1, IRON_LT);
            set(img, 1, i, IRON_LT);
            set(img, i, n - 2, IRON_DK);
            set(img, n - 2, i, IRON_DK);
        }
        for (int[] p : new int[][] {{2, 2}, {n - 4, 2}, {2, n - 4}, {n - 4, n - 4}}) {
            set(img, p[0], p[1], BRASS_HI);
            set(img, p[0] + 1, p[1], BRASS_LT);
            set(img, p[0], p[1] + 1, BRASS_LT);
            set(img, p[0] + 1, p[1] + 1, BRASS_SH);
        }
        return img;
    }

    private static void set(NativeImage img, int x, int y, int col) {
        if (x >= 0 && y >= 0 && x < img.getWidth() && y < img.getHeight()) {
            img.setPixel(x, y, col);
        }
    }

    /** 0..99, fixed per pixel and size. */
    private static int hash(int x, int y, int seed) {
        int h = x * 73856093 ^ y * 19349663 ^ seed * 83492791;
        h ^= h >>> 13;
        h *= 0x5bd1e995;
        h ^= h >>> 15;
        return Math.floorMod(h, 100);
    }

    private static int mix(int a, int b, double t) {
        int r = (int) Math.round(((a >> 16) & 0xFF) + (((b >> 16) & 0xFF) - ((a >> 16) & 0xFF)) * t);
        int g = (int) Math.round(((a >> 8) & 0xFF) + (((b >> 8) & 0xFF) - ((a >> 8) & 0xFF)) * t);
        int bl = (int) Math.round((a & 0xFF) + ((b & 0xFF) - (a & 0xFF)) * t);
        return 0xFF000000 | r << 16 | g << 8 | bl;
    }
}
