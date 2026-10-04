package com.wayfarers.client.map;

import com.wayfarers.map.MapScan;
import com.wayfarers.map.RegionData;
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
            int water = scale(t[2], 0.86F);
            int f = d.floor[i] & 0xFF;
            int depth = d.depth[i];
            if (f > MapScan.VOID && f != MapScan.WATER && depth <= 4) {
                float shallow = depth <= 1 ? 0.5F : depth == 2 ? 0.34F : 0.18F;
                water = mix(water, material(f, t), shallow);
            }
            return water;
        }
        return material(m, t);
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
            default -> m - 2 < 64 ? 0xFF000000 | MapColor.byId(m - 2).col : WALL;
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
