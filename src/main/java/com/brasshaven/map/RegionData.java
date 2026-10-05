package com.brasshaven.map;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;
import java.util.zip.InflaterInputStream;

/**
 * Explored columns of a square area (a 256 x 256 block region, a 64 x 64 thumbnail of one, or a 16 x 16 chunk):
 * per column a material code (see {@link MapScan}), the floor material under water, the height, the water depth and
 * a biome (index into this area's palette of biome ids). Shared by the server store, the network messages and the
 * client cache, with one compact deflated encoding for all three.
 */
public final class RegionData {
    public static final int REGION_SHIFT = 8;
    public static final int REGION = 1 << REGION_SHIFT;
    public static final int MINI = 64;
    private static final int MAGIC = 0x57464D32; // "WFM2"

    public final int size;
    public final byte[] mat;
    public final byte[] floor;
    public final short[] height;
    public final byte[] depth;
    public final byte[] biome;
    private final List<String> palette = new ArrayList<>();
    private final Map<String, Integer> paletteIndex = new HashMap<>();
    /** Bumped every time a column changes (persistent, so clients can ask "anything newer than N?"). */
    public int revision;

    public RegionData(int size) {
        this.size = size;
        int n = size * size;
        mat = new byte[n];
        floor = new byte[n];
        height = new short[n];
        depth = new byte[n];
        biome = new byte[n];
    }

    /** A deep copy (taken on the server thread, encoded on the worker). */
    public RegionData copy() {
        RegionData r = new RegionData(size);
        System.arraycopy(mat, 0, r.mat, 0, mat.length);
        System.arraycopy(floor, 0, r.floor, 0, floor.length);
        System.arraycopy(height, 0, r.height, 0, height.length);
        System.arraycopy(depth, 0, r.depth, 0, depth.length);
        System.arraycopy(biome, 0, r.biome, 0, biome.length);
        for (String id : palette) {
            r.biomeIndex(id);
        }
        r.revision = revision;
        return r;
    }

    public int index(int x, int z) {
        return z * size + x;
    }

    public List<String> palette() {
        return palette;
    }

    /** Palette index (1-based; 0 = unknown) of a biome id, added if new. */
    public int biomeIndex(String id) {
        Integer i = paletteIndex.get(id);
        if (i != null) {
            return i;
        }
        if (palette.size() >= 250) {
            return 0;
        }
        palette.add(id);
        paletteIndex.put(id, palette.size());
        return palette.size();
    }

    public String biomeAt(int i) {
        int b = biome[i] & 0xFF;
        return b == 0 || b > palette.size() ? null : palette.get(b - 1);
    }

    public boolean known(int i) {
        return mat[i] != 0;
    }

    /** Sets one column; returns true if it changed. */
    public boolean set(int i, int material, int floorMaterial, int y, int waterDepth, int biomeIdx) {
        byte m = (byte) material;
        byte f = (byte) floorMaterial;
        short h = (short) y;
        byte d = (byte) waterDepth;
        byte b = (byte) biomeIdx;
        if (mat[i] == m && floor[i] == f && height[i] == h && depth[i] == d && biome[i] == b) {
            return false;
        }
        mat[i] = m;
        floor[i] = f;
        height[i] = h;
        depth[i] = d;
        biome[i] = b;
        return true;
    }

    /** Copies a smaller area (a chunk) in at (ox, oz), remapping its biome palette. Unknown columns are skipped. */
    public boolean paste(RegionData src, int ox, int oz) {
        int[] remap = new int[src.palette.size() + 1];
        for (int p = 0; p < src.palette.size(); p++) {
            remap[p + 1] = biomeIndex(src.palette.get(p));
        }
        boolean changed = false;
        for (int z = 0; z < src.size; z++) {
            for (int x = 0; x < src.size; x++) {
                int s = src.index(x, z);
                if (src.mat[s] == 0) {
                    continue;
                }
                int b = src.biome[s] & 0xFF;
                changed |= set(index(ox + x, oz + z), src.mat[s], src.floor[s], src.height[s], src.depth[s],
                        b < remap.length ? remap[b] : 0);
            }
        }
        return changed;
    }

    /** Fills the columns this area does not know yet from another one of the same size (merging a disk read). */
    public void fillUnknown(RegionData src) {
        int[] remap = new int[src.palette.size() + 1];
        for (int p = 0; p < src.palette.size(); p++) {
            remap[p + 1] = biomeIndex(src.palette.get(p));
        }
        for (int i = 0; i < mat.length && i < src.mat.length; i++) {
            if (mat[i] == 0 && src.mat[i] != 0) {
                int b = src.biome[i] & 0xFF;
                set(i, src.mat[i], src.floor[i], src.height[i], src.depth[i], b < remap.length ? remap[b] : 0);
            }
        }
        revision = Math.max(revision, src.revision);
    }

    /** Which columns a player may see (per-player exploration); null = all. */
    @FunctionalInterface
    public interface Visible {
        boolean test(int x, int z);
    }

    /**
     * Deflated encoding of an n x n grid sampled from this area at (x0 + i * step, z0 + j * step); columns that are
     * not {@code visible} are written as unknown. A whole region: (0, 0, 256, 1); a thumbnail: (1, 1, 64, 4); a chunk:
     * (cx * 16, cz * 16, 16, 1).
     */
    public byte[] encode(int x0, int z0, int n, int step, Visible visible) {
        int count = n * n;
        byte[] m = new byte[count];
        byte[] f = new byte[count];
        byte[] hh = new byte[count];
        byte[] hl = new byte[count];
        byte[] d = new byte[count];
        byte[] b = new byte[count];
        boolean[] used = new boolean[palette.size() + 1];
        for (int j = 0; j < n; j++) {
            for (int i = 0; i < n; i++) {
                int x = x0 + i * step;
                int z = z0 + j * step;
                int s = index(x, z);
                int o = j * n + i;
                if (mat[s] == 0 || visible != null && !visible.test(x, z)) {
                    continue;
                }
                m[o] = mat[s];
                f[o] = floor[s];
                hh[o] = (byte) (height[s] >> 8);
                hl[o] = (byte) height[s];
                d[o] = depth[s];
                int bi = biome[s] & 0xFF;
                if (bi >= used.length) {
                    bi = 0;
                }
                b[o] = (byte) bi;
                used[bi] = true;
            }
        }
        // only the palette entries this grid uses (chunks then carry 1-3 names, not the whole region's)
        List<String> pal = new ArrayList<>();
        int[] remap = new int[palette.size() + 1];
        for (int p = 1; p <= palette.size(); p++) {
            if (used[p]) {
                pal.add(palette.get(p - 1));
                remap[p] = pal.size();
            }
        }
        for (int o = 0; o < count; o++) {
            b[o] = (byte) remap[b[o] & 0xFF];
        }
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(Math.max(64, count / 4));
        Deflater deflater = new Deflater(5);
        try (DataOutputStream out = new DataOutputStream(new DeflaterOutputStream(bytes, deflater, 8192))) {
            out.writeInt(MAGIC);
            out.writeShort(n);
            out.writeInt(revision);
            out.writeByte(pal.size());
            for (String id : pal) {
                out.writeUTF(id);
            }
            out.write(m);
            out.write(f);
            out.write(hh);
            out.write(hl);
            out.write(d);
            out.write(b);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        } finally {
            deflater.end();
        }
        return bytes.toByteArray();
    }

    public byte[] encodeAll() {
        return encode(0, 0, size, 1, null);
    }

    /**
     * An n x n copy sampled at (x0 + i * step, z0 + j * step), hiding columns that are not {@code visible} (taken on
     * the server thread; encoding it can then happen on the worker).
     */
    public RegionData sample(int x0, int z0, int n, int step, Visible visible) {
        RegionData r = new RegionData(n);
        for (String id : palette) {
            r.biomeIndex(id);
        }
        r.revision = revision;
        for (int j = 0; j < n; j++) {
            for (int i = 0; i < n; i++) {
                int x = x0 + i * step;
                int z = z0 + j * step;
                int s = index(x, z);
                if (mat[s] == 0 || visible != null && !visible.test(x, z)) {
                    continue;
                }
                int o = j * n + i;
                r.mat[o] = mat[s];
                r.floor[o] = floor[s];
                r.height[o] = height[s];
                r.depth[o] = depth[s];
                r.biome[o] = biome[s];
            }
        }
        return r;
    }

    /** True when no column is known. */
    public boolean isEmpty() {
        for (byte m : mat) {
            if (m != 0) {
                return false;
            }
        }
        return true;
    }

    /** Reads {@link #encode} output; null when the data is not valid. */
    public static RegionData decode(byte[] data) {
        try (DataInputStream in = new DataInputStream(new InflaterInputStream(new ByteArrayInputStream(data)))) {
            if (in.readInt() != MAGIC) {
                return null;
            }
            int n = in.readUnsignedShort();
            if (n <= 0 || n > REGION) {
                return null;
            }
            RegionData r = new RegionData(n);
            r.revision = in.readInt();
            int p = in.readUnsignedByte();
            for (int i = 0; i < p; i++) {
                r.biomeIndex(in.readUTF());
            }
            int count = n * n;
            in.readFully(r.mat);
            in.readFully(r.floor);
            byte[] hh = new byte[count];
            byte[] hl = new byte[count];
            in.readFully(hh);
            in.readFully(hl);
            for (int i = 0; i < count; i++) {
                r.height[i] = (short) ((hh[i] << 8) | (hl[i] & 0xFF));
            }
            in.readFully(r.depth);
            in.readFully(r.biome);
            // a damaged file (or duplicate palette names) must not point past the palette: encode() indexes by it
            int pal = r.palette.size();
            for (int i = 0; i < count; i++) {
                if ((r.biome[i] & 0xFF) > pal) {
                    r.biome[i] = 0;
                }
            }
            return r;
        } catch (IOException | RuntimeException e) {
            return null;
        }
    }

    public static long key(int rx, int rz) {
        return ((long) rx << 32) | (rz & 0xFFFFFFFFL);
    }

    public static int keyX(long key) {
        return (int) (key >> 32);
    }

    public static int keyZ(long key) {
        return (int) key;
    }
}
