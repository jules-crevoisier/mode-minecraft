package com.wayfarers.command;

import java.awt.image.BufferedImage;

/**
 * Draws a box of blocks as an isometric voxel diorama (plain Java, no game classes, so it can be tried out on a fake
 * grid). Each block is an 8 x 8 px hexagon: top face lit, left face (+z) a little darker, right face (+x) in shade.
 * The sun comes from -x at 45 degrees and casts block shadows; water is drawn see-through on top of the ground below
 * it; plants are small sprites; carpets and snow layers are thin plates. For caves the top layer of the box is the
 * cut: rock there is drawn darker so the holes into the caverns read at a glance.
 *
 * <p>A voxel is an int: bits 0-23 colour, bits 24-26 the kind, then flags (see the constants).
 */
final class IsoRenderer {
    static final int AIR = 0;
    static final int SOLID = 1;
    static final int PLANT = 2;
    static final int CARPET = 3;
    static final int WATER = 4;
    static final int GLOW = 1 << 27;
    static final int WET = 1 << 28;
    static final int GRASSY = 1 << 29;
    static final int FLOWER = 1 << 30;
    /** The top of this block is a section through the rock (cave cutaway): drawn darker. */
    static final int CUT = 1 << 31;

    private static final int CELL = 8;
    private static final int DIRT = 0x8C6444;
    private static final int STEM = 0x4C8C34;
    /** Which face each pixel of the 8 x 8 cell belongs to: 0 none, 1 top, 2 left (+z), 3 right (+x). */
    private static final byte[][] FACE = new byte[CELL][CELL];
    /** For side-face pixels: distance in px below the top edge of that face (to paint the grass band). */
    private static final float[][] BELOW_EDGE = new float[CELL][CELL];
    private static final String[][] PLANTS = {
            {"........", "...#....", ".#..#.#.", "..#.##..", ".#.##.#.", "..####..", "...##...", "........"},
            {"........", "....#...", ".#.#..#.", "..##.#..", ".#.##.#.", "..####..", "...##...", "........"},
            {"........", "........", "..#..#..", "...##...", "..#.##..", "...##...", "...##...", "........"},
    };

    static {
        for (int r = 0; r < CELL; r++) {
            for (int c = 0; c < CELL; c++) {
                double u = c + 0.5;
                double v = r + 0.5;
                if (Math.abs(u - 4) / 4 + Math.abs(v - 2) / 2 < 1) {
                    FACE[r][c] = 1;
                } else if (u < 4 && v > 2 + u / 2 && v < 6 + u / 2) {
                    FACE[r][c] = 2;
                    BELOW_EDGE[r][c] = (float) (v - (2 + u / 2));
                } else if (u > 4 && v > 6 - u / 2 && v < 10 - u / 2) {
                    FACE[r][c] = 3;
                    BELOW_EDGE[r][c] = (float) (v - (6 - u / 2));
                }
            }
        }
    }

    private final int sx;
    private final int sy;
    private final int sz;
    private final int[] vox;
    private final boolean cut;
    private int[] px;
    private int w;
    private int h;

    /**
     * @param vox voxels indexed {@code (y * sz + z) * sx + x}; outside the box counts as air
     * @param cut true for a cave cutaway (see {@link #peel}): deeper blocks fade a little
     */
    IsoRenderer(int sx, int sy, int sz, int[] vox, boolean cut) {
        this.sx = sx;
        this.sy = sy;
        this.sz = sz;
        this.vox = vox;
        this.cut = cut;
    }

    static int voxel(int kind, int rgb, int flags) {
        return (kind << 24) | (rgb & 0xFFFFFF) | flags;
    }

    static int kind(int v) {
        return (v >>> 24) & 7;
    }

    private int at(int x, int y, int z) {
        if (x < 0 || y < 0 || z < 0 || x >= sx || y >= sy || z >= sz) {
            return 0;
        }
        return vox[(y * sz + z) * sx + x];
    }

    private boolean opaque(int x, int y, int z) {
        return kind(at(x, y, z)) == SOLID;
    }

    private boolean wet(int v) {
        return kind(v) == WATER || (v & WET) != 0;
    }

    /** The diorama on a transparent background, 8 px per block, exactly as large as the box needs. */
    BufferedImage render() {
        w = (sx + sz) * CELL / 2;
        h = (sx + sz) * CELL / 4 + sy * CELL / 2;
        px = new int[w * h];
        int maxS = (sx - 1) + (sz - 1) + (sy - 1);
        for (int s = 0; s <= maxS; s++) {
            for (int y = 0; y < sy; y++) {
                for (int x = 0; x < sx; x++) {
                    int z = s - y - x;
                    if (z < 0 || z >= sz) {
                        continue;
                    }
                    int v = vox[(y * sz + z) * sx + x];
                    if (v != 0) {
                        draw(x, y, z, v);
                    }
                }
            }
        }
        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        img.setRGB(0, 0, w, h, px, 0, w);
        return img;
    }

    private void draw(int x, int y, int z, int v) {
        int ox = (x - z) * CELL / 2 + (sz - 1) * CELL / 2;
        int oy = (x + z) * CELL / 4 - y * CELL / 2 + (sy - 1) * CELL / 2;
        int rgb = v & 0xFFFFFF;
        boolean glow = (v & GLOW) != 0;
        double fog = 1.0;
        if (cut && !glow) {
            fog = Math.max(0.55, 1.0 - 0.014 * (sy - 1 - y));
        }
        double blockNoise = 1.0 + (((hash(x, y, z) & 255) / 255.0) - 0.5) * 0.10;
        switch (kind(v)) {
            case SOLID -> drawSolid(x, y, z, v, rgb, glow, fog * blockNoise, ox, oy);
            case PLANT -> drawPlant(x, y, z, v, rgb, glow, fog * blockNoise, ox, oy);
            case CARPET -> drawCarpet(x, y, z, rgb, glow, fog * blockNoise, ox, oy);
            default -> { }
        }
        if (wet(v)) {
            drawWater(x, y, z, v, ox, oy);
        }
    }

    private void drawSolid(int x, int y, int z, int v, int rgb, boolean glow, double f, int ox, int oy) {
        boolean top = !opaque(x, y + 1, z);
        boolean left = !opaque(x, y, z + 1);
        boolean right = !opaque(x + 1, y, z);
        if (!top && !left && !right) {
            return;
        }
        double topF = glow ? 1.15 : 1.0;
        boolean section = (v & CUT) != 0;
        if (top && !glow) {
            if (section) {
                topF = 0.58;
            } else {
                if (shadowed(x, y + 1, z)) {
                    topF *= 0.70;
                }
                int occ = (opaque(x - 1, y + 1, z) ? 1 : 0) + (opaque(x, y + 1, z - 1) ? 1 : 0)
                        + (opaque(x + 1, y + 1, z) ? 1 : 0) + (opaque(x, y + 1, z + 1) ? 1 : 0);
                topF *= 1.0 - 0.07 * occ;
            }
        }
        double leftF = glow ? 1.0 : 0.80 * (left && shadowed(x, y, z + 1) ? 0.78 : 1.0);
        double rightF = glow ? 0.88 : 0.60;
        boolean grassy = (v & GRASSY) != 0;
        for (int r = 0; r < CELL; r++) {
            for (int c = 0; c < CELL; c++) {
                int face = FACE[r][c];
                int col;
                double k;
                if (face == 1 && top) {
                    col = section ? mix(rgb, 0x45454E, 0.25) : rgb;
                    k = topF;
                } else if (face == 2 && left) {
                    col = grassy && BELOW_EDGE[r][c] > 1.0 ? DIRT : rgb;
                    k = leftF * (BELOW_EDGE[r][c] < 1.0 ? 1.06 : 1.0);
                } else if (face == 3 && right) {
                    col = grassy && BELOW_EDGE[r][c] > 1.0 ? DIRT : rgb;
                    k = rightF * (BELOW_EDGE[r][c] < 1.0 ? 1.06 : 1.0);
                } else {
                    continue;
                }
                double n = 1.0 + (((hash(x * 8 + c, y, z * 8 + r) & 255) / 255.0) - 0.5) * 0.08;
                put(ox + c, oy + r, scale(col, k * f * n), 1.0);
            }
        }
    }

    private void drawPlant(int x, int y, int z, int v, int rgb, boolean glow, double f, int ox, int oy) {
        String[] mask = PLANTS[hash(x, y * 7, z) % PLANTS.length];
        boolean flip = (hash(z, y, x) & 1) == 1;
        boolean flower = (v & FLOWER) != 0;
        boolean shade = shadowed(x, y, z);
        for (int r = 0; r < CELL; r++) {
            for (int c = 0; c < CELL; c++) {
                if (mask[r].charAt(flip ? CELL - 1 - c : c) != '#') {
                    continue;
                }
                int col = flower && r > 3 ? STEM : rgb;
                double k = (c < 4 ? 1.0 : 0.80) * (shade && !glow ? 0.75 : 1.0) * (glow ? 1.15 : 1.0);
                put(ox + c, oy + r, scale(col, k * f), 1.0);
            }
        }
    }

    private void drawCarpet(int x, int y, int z, int rgb, boolean glow, double f, int ox, int oy) {
        double k = glow ? 1.1 : (shadowed(x, y, z) ? 0.72 : 1.0);
        for (int r = 0; r < 4; r++) {
            for (int c = 0; c < CELL; c++) {
                if (FACE[r][c] == 1) {
                    double n = 1.0 + (((hash(x * 8 + c, y, z * 8 + r) & 255) / 255.0) - 0.5) * 0.06;
                    put(ox + c, oy + r + 3, scale(rgb, k * f * n), 1.0);
                }
            }
        }
    }

    private void drawWater(int x, int y, int z, int v, int ox, int oy) {
        int above = at(x, y + 1, z);
        int rgb = kind(v) == WATER ? v & 0xFFFFFF : 0x3F76E4;
        boolean top = !wet(above) && kind(above) != SOLID;
        int na = at(x + 1, y, z);
        int nb = at(x, y, z + 1);
        boolean right = x == sx - 1 || kind(na) == AIR;
        boolean left = z == sz - 1 || kind(nb) == AIR;
        if (!top && !left && !right) {
            return;
        }
        int depth = 0;
        while (depth < 20 && wet(at(x, y - depth - 1, z))) {
            depth++;
        }
        double a = Math.min(0.86, 0.50 + 0.03 * depth);
        for (int r = 0; r < CELL; r++) {
            for (int c = 0; c < CELL; c++) {
                int face = FACE[r][c];
                if (face == 1 && top) {
                    double n = 1.0 + (((hash(x * 8 + c, y, z * 8 + r) & 255) / 255.0) - 0.5) * 0.08;
                    put(ox + c, oy + r, scale(rgb, 1.05 * n), a);
                } else if (face == 2 && left) {
                    put(ox + c, oy + r, scale(rgb, 0.85), 0.55);
                } else if (face == 3 && right) {
                    put(ox + c, oy + r, scale(rgb, 0.70), 0.55);
                }
            }
        }
    }

    /** True when a solid block stands between this cell and the sun (towards -x, 45 degrees up). */
    private boolean shadowed(int x, int y, int z) {
        for (int k = 1; k <= 48; k++) {
            if (x - k < 0 || y + k >= sy) {
                return false;
            }
            if (opaque(x - k, y + k, z)) {
                return true;
            }
        }
        return false;
    }

    private void put(int x, int y, int rgb, double alpha) {
        if (x < 0 || y < 0 || x >= w || y >= h) {
            return;
        }
        int i = y * w + x;
        int under = px[i];
        if (alpha >= 1.0 || (under >>> 24) == 0) {
            int a = alpha >= 1.0 ? 255 : (int) (alpha * 255);
            px[i] = (a << 24) | rgb;
            return;
        }
        px[i] = 0xFF000000 | mix(under & 0xFFFFFF, rgb, alpha);
    }

    // ------------------------------------------------------------------ cave cutaway

    /**
     * Opens a block of rock so its caves can be seen from above. In each column the rock above the highest cave
     * opening is taken away (the cave floor shows); columns of solid rock keep a wall that starts 3 blocks above the
     * nearest cave floor and rises one block per block away from it. Seen from the isometric camera those slopes run
     * along the line of sight, so they never hide the floors behind them. The new tops of the rock get {@link #CUT}.
     */
    static int[] peel(int[] vox, int sx, int sy, int sz) {
        int[] out = vox.clone();
        int[] height = new int[sx * sz];
        int big = 1 << 20;
        boolean any = false;
        for (int z = 0; z < sz; z++) {
            for (int x = 0; x < sx; x++) {
                int open = -1;
                for (int y = sy - 1; y >= 0; y--) {
                    if (kind(vox[(y * sz + z) * sx + x]) != SOLID) {
                        open = y;
                        break;
                    }
                }
                if (open < 0) {
                    height[z * sx + x] = big;
                    continue;
                }
                any = true;
                int floor = open;
                while (floor >= 0 && kind(vox[(floor * sz + z) * sx + x]) != SOLID) {
                    floor--;
                }
                for (int y = open + 1; y < sy; y++) {
                    out[(y * sz + z) * sx + x] = 0;
                }
                height[z * sx + x] = -(floor + 3) - 1;  // negative: a cave column (fixed), value floor + 3
            }
        }
        if (!any) {
            return out;
        }
        // chamfer pass over the solid columns: lowest neighbour + 1, cave columns seed at floor + 3
        int[] hh = new int[sx * sz];
        for (int i = 0; i < hh.length; i++) {
            hh[i] = height[i] < 0 ? -height[i] - 1 : big;
        }
        for (int pass = 0; pass < 4; pass++) {
            boolean back = (pass & 1) == 1;
            for (int k = 0; k < sx * sz; k++) {
                int i = back ? sx * sz - 1 - k : k;
                if (height[i] < 0) {
                    continue;
                }
                int x = i % sx;
                int z = i / sx;
                int best = hh[i];
                for (int dz = -1; dz <= 1; dz++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        int nx = x + dx;
                        int nz = z + dz;
                        if ((dx != 0 || dz != 0) && nx >= 0 && nz >= 0 && nx < sx && nz < sz) {
                            best = Math.min(best, hh[nz * sx + nx] + 1);
                        }
                    }
                }
                hh[i] = best;
            }
        }
        for (int z = 0; z < sz; z++) {
            for (int x = 0; x < sx; x++) {
                if (height[z * sx + x] < 0) {
                    continue;
                }
                int top = Math.min(sy - 1, hh[z * sx + x]);
                for (int y = top + 1; y < sy; y++) {
                    out[(y * sz + z) * sx + x] = 0;
                }
                if (top >= 0) {
                    out[(top * sz + z) * sx + x] |= CUT;
                }
            }
        }
        return out;
    }

    // ------------------------------------------------------------------ framing

    /**
     * Fits the diorama into a {@code fw x fh} transparent frame (scaled down if needed, never up), with a soft
     * shadow under it.
     */
    static BufferedImage frame(BufferedImage src, int fw, int fh) {
        int w = src.getWidth();
        int h = src.getHeight();
        int[] p = src.getRGB(0, 0, w, h, null, 0, w);
        int x0 = w;
        int y0 = h;
        int x1 = -1;
        int y1 = -1;
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                if ((p[y * w + x] >>> 24) != 0) {
                    x0 = Math.min(x0, x);
                    y0 = Math.min(y0, y);
                    x1 = Math.max(x1, x);
                    y1 = Math.max(y1, y);
                }
            }
        }
        BufferedImage out = new BufferedImage(fw, fh, BufferedImage.TYPE_INT_ARGB);
        if (x1 < 0) {
            return out;
        }
        int bw = x1 - x0 + 1;
        int bh = y1 - y0 + 1;
        int margin = 14;
        double s = Math.min(1.0, Math.min((fw - 2.0 * margin) / bw, (fh - 2.0 * margin) / bh));
        int dw = Math.max(1, (int) Math.round(bw * s));
        int dh = Math.max(1, (int) Math.round(bh * s));
        int[] scaled = resample(p, w, x0, y0, bw, bh, dw, dh);
        int dx = (fw - dw) / 2;
        int dy = (fh - dh) / 2;
        int[] o = new int[fw * fh];
        // shadow: the silhouette, blurred and pushed down a little
        float[] mask = new float[fw * fh];
        int drop = 7;
        for (int y = 0; y < dh; y++) {
            for (int x = 0; x < dw; x++) {
                int tx = dx + x;
                int ty = dy + y + drop;
                if (tx < fw && ty < fh) {
                    mask[ty * fw + tx] = (scaled[y * dw + x] >>> 24) / 255f;
                }
            }
        }
        for (int pass = 0; pass < 3; pass++) {
            mask = blur(mask, fw, fh, 4);
        }
        for (int i = 0; i < o.length; i++) {
            int a = (int) (mask[i] * 0.38f * 255);
            o[i] = a << 24;
        }
        for (int y = 0; y < dh; y++) {
            for (int x = 0; x < dw; x++) {
                int c = scaled[y * dw + x];
                int ca = c >>> 24;
                if (ca == 0) {
                    continue;
                }
                int i = (dy + y) * fw + dx + x;
                o[i] = over(c, o[i]);
            }
        }
        out.setRGB(0, 0, fw, fh, o, 0, fw);
        return out;
    }

    /** Area-averaged resampling with premultiplied alpha (no dark fringes at the transparent edges). */
    private static int[] resample(int[] p, int w, int x0, int y0, int bw, int bh, int dw, int dh) {
        int[] out = new int[dw * dh];
        if (dw == bw && dh == bh) {
            for (int y = 0; y < bh; y++) {
                System.arraycopy(p, (y0 + y) * w + x0, out, y * dw, bw);
            }
            return out;
        }
        int ss = 4;
        for (int y = 0; y < dh; y++) {
            for (int x = 0; x < dw; x++) {
                double a = 0;
                double r = 0;
                double g = 0;
                double b = 0;
                for (int j = 0; j < ss; j++) {
                    int syy = y0 + Math.min(bh - 1, (int) ((y + (j + 0.5) / ss) * bh / dh));
                    for (int i = 0; i < ss; i++) {
                        int sxx = x0 + Math.min(bw - 1, (int) ((x + (i + 0.5) / ss) * bw / dw));
                        int c = p[syy * w + sxx];
                        double ca = (c >>> 24) / 255.0;
                        a += ca;
                        r += ((c >> 16) & 255) * ca;
                        g += ((c >> 8) & 255) * ca;
                        b += (c & 255) * ca;
                    }
                }
                int n = ss * ss;
                if (a <= 0) {
                    continue;
                }
                int oa = (int) Math.round(a / n * 255);
                out[y * dw + x] = (oa << 24) | (clamp(r / a) << 16) | (clamp(g / a) << 8) | clamp(b / a);
            }
        }
        return out;
    }

    private static float[] blur(float[] m, int w, int h, int rad) {
        float[] t = new float[m.length];
        float[] o = new float[m.length];
        for (int y = 0; y < h; y++) {
            float acc = 0;
            for (int x = -rad; x < w; x++) {
                if (x + rad < w) {
                    acc += m[y * w + x + rad];
                }
                if (x - rad - 1 >= 0) {
                    acc -= m[y * w + x - rad - 1];
                }
                if (x >= 0) {
                    t[y * w + x] = acc / (2 * rad + 1);
                }
            }
        }
        for (int x = 0; x < w; x++) {
            float acc = 0;
            for (int y = -rad; y < h; y++) {
                if (y + rad < h) {
                    acc += t[(y + rad) * w + x];
                }
                if (y - rad - 1 >= 0) {
                    acc -= t[(y - rad - 1) * w + x];
                }
                if (y >= 0) {
                    o[y * w + x] = acc / (2 * rad + 1);
                }
            }
        }
        return o;
    }

    /** Source-over compositing of two non-premultiplied ARGB colours. */
    private static int over(int src, int dst) {
        double sa = (src >>> 24) / 255.0;
        double da = (dst >>> 24) / 255.0;
        double oa = sa + da * (1 - sa);
        if (oa <= 0) {
            return 0;
        }
        int r = clamp((((src >> 16) & 255) * sa + ((dst >> 16) & 255) * da * (1 - sa)) / oa);
        int g = clamp((((src >> 8) & 255) * sa + ((dst >> 8) & 255) * da * (1 - sa)) / oa);
        int b = clamp(((src & 255) * sa + (dst & 255) * da * (1 - sa)) / oa);
        return ((int) Math.round(oa * 255) << 24) | (r << 16) | (g << 8) | b;
    }

    // ------------------------------------------------------------------ colour helpers

    static int scale(int rgb, double f) {
        int r = clamp(((rgb >> 16) & 255) * f);
        int g = clamp(((rgb >> 8) & 255) * f);
        int b = clamp((rgb & 255) * f);
        return (r << 16) | (g << 8) | b;
    }

    static int mix(int a, int b, double t) {
        int r = clamp(((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
        int g = clamp(((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
        int bl = clamp((a & 255) * (1 - t) + (b & 255) * t);
        return (r << 16) | (g << 8) | bl;
    }

    private static int clamp(double v) {
        return (int) Math.max(0, Math.min(255, Math.round(v)));
    }

    private static int hash(int x, int y, int z) {
        int hsh = x * 73856093 ^ y * 19349663 ^ z * 83492791;
        hsh ^= hsh >>> 13;
        hsh *= 0x5bd1e995;
        hsh ^= hsh >>> 15;
        return hsh & 0x7FFFFFFF;
    }
}
