package com.wayfarers.command;

import com.mojang.brigadier.context.CommandContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.TreeMap;

/**
 * /wayfarers worldmap: draws what the generator would make around 0,0 without generating a single chunk.
 * Writes three images and a legend into the server folder (used by CI to publish previews of the world):
 * surface biomes shaded by height, cave biomes at y -20, and a vertical slice through the terrain and caves.
 */
public final class WorldMapCommand {
    private static final int SIZE = 256;
    private static final int STEP = 15;
    private static final int SLICE_W = 512;
    private static final int SLICE_STEP = 4;

    private WorldMapCommand() {}

    static int run(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack src = ctx.getSource();
        ServerLevel level = src.getServer().overworld();
        ChunkGenerator gen = level.getChunkSource().getGenerator();
        RandomState random = level.getChunkSource().randomState();
        BiomeSource biomes = gen.getBiomeSource();
        Climate.Sampler sampler = random.sampler();
        Path dir = src.getServer().getServerDirectory();
        long t = System.currentTimeMillis();
        Map<String, int[]> legend = new TreeMap<>();
        BufferedImage surface = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_RGB);
        BufferedImage caves = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_RGB);
        int half = SIZE / 2;
        int minH = Integer.MAX_VALUE;
        int maxH = Integer.MIN_VALUE;
        for (int px = 0; px < SIZE; px++) {
            for (int pz = 0; pz < SIZE; pz++) {
                int x = (px - half) * STEP;
                int z = (pz - half) * STEP;
                int h = gen.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, level, random);
                minH = Math.min(minH, h);
                maxH = Math.max(maxH, h);
                Holder<Biome> biome = biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(Math.max(h, 63)),
                        QuartPos.fromBlock(z), sampler);
                String id = biome.unwrapKey().map(k -> k.identifier().toString()).orElse("?");
                int base = color(id);
                legend.computeIfAbsent(id, k -> new int[] {base, 0})[1]++;
                double shade = 0.55 + 0.45 * Math.max(0, Math.min(1, (h - 40) / 220.0));
                int rgb = scale(base, shade);
                if (h < 62) {
                    rgb = mix(rgb, 0x1E50B4, 0.55);
                }
                surface.setRGB(px, pz, rgb);
                Holder<Biome> cave = biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(-20), QuartPos.fromBlock(z), sampler);
                String cid = cave.unwrapKey().map(k -> k.identifier().toString()).orElse("?");
                legend.computeIfAbsent(cid, k -> new int[] {color(cid), 0});
                caves.setRGB(px, pz, color(cid));
            }
        }
        int height = level.getHeight();
        int minY = level.getMinY();
        BufferedImage slice = new BufferedImage(SLICE_W, height, BufferedImage.TYPE_INT_RGB);
        for (int px = 0; px < SLICE_W; px++) {
            int x = (px - SLICE_W / 2) * SLICE_STEP;
            NoiseColumn column = gen.getBaseColumn(x, 0, level, random);
            for (int y = minY; y < minY + height; y++) {
                BlockState state = column.getBlock(y);
                int rgb;
                if (state.isAir()) {
                    rgb = y > 62 ? 0x9CC4FF : 0x101014;
                } else if (state.getFluidState().isSource() && state.getFluidState().getAmount() > 0) {
                    rgb = state.getFluidState().is(FluidTags.LAVA) ? 0xFF7A1A : 0x2A5BD7;
                } else {
                    rgb = state.getMapColor(level, BlockPos.ZERO).col;
                    if (rgb == 0) {
                        rgb = 0x707070;
                    }
                }
                slice.setRGB(px, minY + height - 1 - y, rgb);
            }
        }
        try {
            ImageIO.write(surface, "png", dir.resolve("wayfarers-worldmap.png").toFile());
            ImageIO.write(caves, "png", dir.resolve("wayfarers-worldmap-caves.png").toFile());
            ImageIO.write(slice, "png", dir.resolve("wayfarers-worldmap-slice.png").toFile());
            try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(dir.resolve("wayfarers-worldmap.txt")))) {
                out.printf("area %d x %d blocks around 0,0 (1 px = %d blocks); height %d..%d%n", SIZE * STEP, SIZE * STEP, STEP, minH, maxH);
                int total = SIZE * SIZE;
                for (Map.Entry<String, int[]> e : legend.entrySet()) {
                    out.printf("#%06x %-36s %5.1f%%%n", e.getValue()[0], e.getKey(), 100.0 * e.getValue()[1] / total);
                }
            }
        } catch (IOException e) {
            src.sendFailure(Component.literal("worldmap: " + e.getMessage()));
            return 0;
        }
        long ms = System.currentTimeMillis() - t;
        int lo = minH;
        int hi = maxH;
        src.sendSuccess(() -> Component.literal("World map written to " + dir + " in " + ms + " ms (height " + lo + ".." + hi + ")"), false);
        return 1;
    }

    /** A stable, distinct colour per biome id. */
    static int color(String id) {
        int h = id.hashCode();
        float hue = ((h & 0xFFFF) / 65535f);
        float sat = 0.45f + ((h >>> 16) & 0xFF) / 255f * 0.4f;
        return java.awt.Color.HSBtoRGB(hue, sat, 0.92f) & 0xFFFFFF;
    }

    private static int scale(int rgb, double f) {
        int r = (int) Math.min(255, ((rgb >> 16) & 255) * f);
        int g = (int) Math.min(255, ((rgb >> 8) & 255) * f);
        int b = (int) Math.min(255, (rgb & 255) * f);
        return (r << 16) | (g << 8) | b;
    }

    private static int mix(int a, int b, double t) {
        int r = (int) (((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
        int g = (int) (((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
        int bl = (int) ((a & 255) * (1 - t) + (b & 255) * t);
        return (r << 16) | (g << 8) | bl;
    }
}
