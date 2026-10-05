package com.brasshaven.client.map;

import com.brasshaven.map.MapScan;
import com.brasshaven.map.RegionData;
import net.minecraft.client.Minecraft;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.material.MapColor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Turns map material codes into colours on the client: vanilla map colours, and the biome tints (grass, foliage,
 * water) taken from the biome registry the client received, so the map shows the same greens and blues as the world.
 */
final class MapPalette {
    private static final Map<String, int[]> BIOMES = new HashMap<>();
    private static final int[] DEFAULT = {0xFF91BD59, 0xFF77AB2F, 0xFF3F76E4};
    private static final int WALL = 0xFF2E2621;

    private MapPalette() {}

    static void reset() {
        BIOMES.clear();
    }

    /** {grass, foliage, water} of a biome id. */
    static int[] biome(String id) {
        if (id == null) {
            return DEFAULT;
        }
        int[] c = BIOMES.get(id);
        if (c == null) {
            c = DEFAULT;
            Minecraft mc = Minecraft.getInstance();
            if (mc.level != null) {
                try {
                    Registry<Biome> reg = mc.level.registryAccess().lookupOrThrow(Registries.BIOME);
                    Biome b = reg.getValue(Identifier.parse(id));
                    if (b != null) {
                        c = new int[] {0xFF000000 | b.getGrassColor(0, 0), 0xFF000000 | b.getFoliageColor(), 0xFF000000 | b.getWaterColor()};
                    }
                } catch (RuntimeException ignored) {
                    // unknown or malformed id: default tints
                }
            }
            BIOMES.put(id, c);
        }
        return c;
    }

    /** Per palette entry of a region (index 0 = unknown biome). */
    static int[][] resolve(List<String> palette) {
        int[][] out = new int[palette.size() + 1][];
        out[0] = DEFAULT;
        for (int i = 0; i < palette.size(); i++) {
            out[i + 1] = biome(palette.get(i));
        }
        return out;
    }

    /** Unshaded colour of column {@code i} (0: nothing to draw). */
    static int color(RegionData d, int i, int[][] tints) {
        int m = d.mat[i] & 0xFF;
        if (m <= MapScan.VOID) {
            return 0;
        }
        int b = d.biome[i] & 0xFF;
        int[] t = b < tints.length ? tints[b] : DEFAULT;
        if (m == MapScan.WATER) {
            return water(t[2], d.depth[i], d.floor[i] & 0xFF, t);
        }
        return material(m, t);
    }

    /**
     * Water by depth: light over the shallows (the bed shows through the first blocks), a deep navy far down, on the
     * biome's own water hue.
     */
    static int water(int tint, int depth, int floorMat, int[] t) {
        float f = (float) Math.sqrt(Math.max(0, Math.min(30, depth - 1)) / 30.0F);
        int shallow = mix(tint, 0xFFFFFFFF, 0.12F);
        int deep = mix(scale(tint, 0.52F), 0xFF0B1C3E, 0.32F);
        int c = mix(shallow, deep, f);
        if (floorMat > MapScan.VOID && floorMat != MapScan.WATER && depth <= 4) {
            float bed = depth <= 1 ? 0.55F : depth == 2 ? 0.38F : depth == 3 ? 0.22F : 0.10F;
            c = mix(c, material(floorMat, t), bed);
        }
        return c;
    }

    private static int material(int m, int[] t) {
        return switch (m) {
            case MapScan.GRASS -> scale(t[0], 0.86F);
            case MapScan.PLANT -> scale(t[0], 0.78F);
            case MapScan.FOLIAGE -> scale(t[1], 0.74F);
            case MapScan.SPRUCE -> scale(0xFF619961, 0.74F);
            case MapScan.BIRCH -> scale(0xFF80A755, 0.74F);
            case MapScan.WATER -> scale(t[2], 0.86F);
            case MapScan.WALL -> WALL;
            // MapColor.NONE (col 0: air-like, glass, barriers, columns scanned before they were filled in) is
            // left transparent, so the parchment shows instead of black holes
            default -> m - 2 < 64 ? (MapColor.byId(m - 2).col == 0 ? 0 : 0xFF000000 | MapColor.byId(m - 2).col) : WALL;
        };
    }

    static int scale(int c, float f) {
        int r = Math.min(255, Math.max(0, (int) (((c >> 16) & 0xFF) * f)));
        int g = Math.min(255, Math.max(0, (int) (((c >> 8) & 0xFF) * f)));
        int b = Math.min(255, Math.max(0, (int) ((c & 0xFF) * f)));
        return 0xFF000000 | r << 16 | g << 8 | b;
    }

    static int mix(int a, int b, float t) {
        int r = (int) (((a >> 16) & 0xFF) * (1 - t) + ((b >> 16) & 0xFF) * t);
        int g = (int) (((a >> 8) & 0xFF) * (1 - t) + ((b >> 8) & 0xFF) * t);
        int bl = (int) ((a & 0xFF) * (1 - t) + (b & 0xFF) * t);
        return 0xFF000000 | r << 16 | g << 8 | bl;
    }

    /** Human name of a biome id ("minecraft:dark_forest" -> its translated name). */
    static net.minecraft.network.chat.Component biomeName(String id) {
        Identifier rl = Identifier.tryParse(id);
        if (rl == null) {
            return net.minecraft.network.chat.Component.literal(id);
        }
        return net.minecraft.network.chat.Component.translatable("biome." + rl.getNamespace() + "." + rl.getPath());
    }
}
