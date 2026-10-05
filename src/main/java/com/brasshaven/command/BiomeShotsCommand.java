package com.brasshaven.command;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.datafixers.util.Pair;
import com.brasshaven.Brasshaven;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSource;
import net.minecraft.world.level.levelgen.Heightmap;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.BiPredicate;

/**
 * /brasshaven biomeshots [biome]: for every Brasshaven biome of the world (Crimson Mire, Volcanic Highlands, Pale
 * Dunes), finds the nearest place where it covers the most ground, really generates the 5 x 5 chunks there (plants,
 * objects, ores, structures included) and draws them block by block as an isometric diorama ({@link IsoRenderer}).
 * Writes brasshaven-biome-&lt;id&gt;.png and the legend brasshaven-biomes.txt into the server folder (CI publishes them
 * with the previews, the wiki shows them on the biome cards).
 */
public final class BiomeShotsCommand {
    private static final int CHUNK_RADIUS = 2;
    private static final int SIZE = (CHUNK_RADIUS * 2 + 1) * 16;
    private static final int FRAME_W = 672;
    private static final int FRAME_H = 504;
    private static final int SEARCH_RADIUS = 8000;
    private static final int SEARCH_STEP = 32;
    private static final int REFINE_GRID = 64;
    private static final int REFINE_STEP = 8;
    private static final long BUDGET_MS = 6 * 60_000L;

    private BiomeShotsCommand() {}

    static int run(CommandContext<CommandSourceStack> ctx) {
        return run(ctx, null);
    }

    static int run(CommandContext<CommandSourceStack> ctx, String only) {
        CommandSourceStack src = ctx.getSource();
        ServerLevel level = src.getServer().overworld();
        Path dir = src.getServer().getServerDirectory();
        long start = System.currentTimeMillis();
        BiomeSource biomes = level.getChunkSource().getGenerator().getBiomeSource();
        Climate.Sampler sampler = level.getChunkSource().randomState().sampler();
        Map<String, Holder<Biome>> targets = new TreeMap<>();
        for (Holder<Biome> b : biomes.possibleBiomes()) {
            String id = id(b);
            if (id.startsWith(Brasshaven.MODID + ":") && (only == null || id.endsWith(":" + only))) {
                targets.put(id, b);
            }
        }
        if (targets.isEmpty()) {
            src.sendFailure(Component.literal("Biome shots failed: no Brasshaven biome generates in this world "
                    + "(is the brasshaven:custom_biomes pack on?)"));
            return 0;
        }
        Map<String, BlockPos> found = search(biomes, sampler, targets);
        List<String> lines = new ArrayList<>();
        lines.add(String.format(Locale.ROOT, "biome shots: %d x %d blocks per biome, %d x %d px, 8 px per block, nearest to 0,0",
                SIZE, SIZE, FRAME_W, FRAME_H));
        int done = 0;
        for (Map.Entry<String, Holder<Biome>> e : targets.entrySet()) {
            String id = e.getKey();
            String path = id.substring(id.indexOf(':') + 1);
            long t = System.currentTimeMillis();
            if (t - start > BUDGET_MS) {
                lines.add(String.format(Locale.ROOT, "%-30s skipped: time budget used up", id));
                continue;
            }
            BlockPos hit = found.get(id);
            if (hit == null) {
                Pair<BlockPos, Holder<Biome>> near = level.findClosestBiome3d(h -> h.equals(e.getValue()), BlockPos.ZERO,
                        SEARCH_RADIUS, SEARCH_STEP, 64);
                hit = near == null ? null : near.getFirst();
            }
            if (hit == null) {
                lines.add(String.format(Locale.ROOT, "%-30s skipped: not found within %d blocks", id, SEARCH_RADIUS));
                continue;
            }
            try {
                Shot shot = shoot(level, biomes, sampler, e.getValue(), hit);
                ImageIO.write(shot.image, "png", dir.resolve("brasshaven-biome-" + path + ".png").toFile());
                long ms = System.currentTimeMillis() - t;
                lines.add(String.format(Locale.ROOT, "%-30s surface at %d %d y %d..%d  %d ms", id, shot.x, shot.z,
                        shot.y0, shot.y1, ms));
                Brasshaven.LOGGER.info("biome shot {} at {} {}, y {}..{}, {} ms", id, shot.x, shot.z, shot.y0, shot.y1, ms);
                done++;
            } catch (IOException | RuntimeException ex) {
                String why = String.valueOf(ex.getMessage()).replace("Exception", "error");
                lines.add(String.format(Locale.ROOT, "%-30s skipped: %s", id, why));
                Brasshaven.LOGGER.warn("biome shot {} skipped ({})", id, why);
            }
            writeLegend(dir, lines);
            // the server does not tick while this command runs: let the chunk map unload (and save) the areas drawn
            long until = System.currentTimeMillis() + 300;
            level.getChunkSource().tick(() -> System.currentTimeMillis() < until, false);
        }
        if (!writeLegend(dir, lines)) {
            src.sendFailure(Component.literal("Biome shots failed: could not write the legend in " + dir));
            return 0;
        }
        long secs = (System.currentTimeMillis() - start) / 1000;
        int count = done;
        int total = targets.size();
        src.sendSuccess(() -> Component.literal("Biome shots written: " + count + " of " + total + " biomes in " + secs + " s"), false);
        return count > 0 ? 1 : 0;
    }

    private static boolean writeLegend(Path dir, List<String> lines) {
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(dir.resolve("brasshaven-biomes.txt")))) {
            lines.forEach(out::println);
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    static String id(Holder<Biome> b) {
        return b.unwrapKey().map(k -> k.identifier().toString()).orElse("?");
    }

    /** One spiral walk from 0,0 for all targets at once, with the climate at the ground (depth 0). */
    private static Map<String, BlockPos> search(BiomeSource biomes, Climate.Sampler sampler, Map<String, Holder<Biome>> targets) {
        Map<String, BlockPos> out = new HashMap<>();
        int rings = SEARCH_RADIUS / SEARCH_STEP;
        for (int r = 0; r <= rings && out.size() < targets.size(); r++) {
            for (int dz = -r; dz <= r; dz++) {
                for (int dx = -r; dx <= r; dx += (dz == -r || dz == r || dx == r) ? 1 : 2 * r) {
                    int x = dx * SEARCH_STEP;
                    int z = dz * SEARCH_STEP;
                    String id = id(surfaceBiome(biomes, sampler, x, z));
                    if (targets.containsKey(id) && !out.containsKey(id)) {
                        out.put(id, new BlockPos(x, 64, z));
                    }
                }
            }
        }
        return out;
    }

    /** The biome of the ground itself at x, z: the climate there with the depth set to 0 (the surface). */
    static Holder<Biome> surfaceBiome(BiomeSource biomes, Climate.Sampler sampler, int x, int z) {
        if (!(biomes instanceof MultiNoiseBiomeSource multi)) {
            return biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(64), QuartPos.fromBlock(z), sampler);
        }
        Climate.TargetPoint t = sampler.sample(QuartPos.fromBlock(x), QuartPos.fromBlock(64), QuartPos.fromBlock(z));
        return multi.getNoiseBiome(new Climate.TargetPoint(t.temperature(), t.humidity(), t.continentalness(), t.erosion(),
                0L, t.weirdness()));
    }

    /**
     * Around the first place found (usually the edge of the biome), the 80 x 80 window that holds the most of it,
     * sampled every 8 blocks over 512 x 512 blocks. Returns the window centre.
     */
    private static int[] bestWindow(BlockPos hit, BiPredicate<Integer, Integer> inside) {
        int g = REFINE_GRID;
        int half = g / 2 * REFINE_STEP;
        int[] sum = new int[(g + 1) * (g + 1)];
        for (int j = 0; j < g; j++) {
            for (int i = 0; i < g; i++) {
                int x = hit.getX() - half + i * REFINE_STEP;
                int z = hit.getZ() - half + j * REFINE_STEP;
                int v = inside.test(x, z) ? 1 : 0;
                sum[(j + 1) * (g + 1) + i + 1] = v + sum[j * (g + 1) + i + 1] + sum[(j + 1) * (g + 1) + i] - sum[j * (g + 1) + i];
            }
        }
        int win = SIZE / REFINE_STEP;
        int best = -1;
        long bestDist = Long.MAX_VALUE;
        int bx = hit.getX();
        int bz = hit.getZ();
        for (int j = 0; j + win <= g; j++) {
            for (int i = 0; i + win <= g; i++) {
                int c = sum[(j + win) * (g + 1) + i + win] - sum[j * (g + 1) + i + win] - sum[(j + win) * (g + 1) + i] + sum[j * (g + 1) + i];
                int cx = hit.getX() - half + (i + win / 2) * REFINE_STEP;
                int cz = hit.getZ() - half + (j + win / 2) * REFINE_STEP;
                long d = (long) (cx - hit.getX()) * (cx - hit.getX()) + (long) (cz - hit.getZ()) * (cz - hit.getZ());
                if (c > best || c == best && d < bestDist) {
                    best = c;
                    bestDist = d;
                    bx = cx;
                    bz = cz;
                }
            }
        }
        return new int[] {bx, bz};
    }

    private record Shot(BufferedImage image, int x, int z, int y0, int y1) {}

    private static Shot shoot(ServerLevel level, BiomeSource biomes, Climate.Sampler sampler, Holder<Biome> biome, BlockPos hit) {
        int[] centre = bestWindow(hit, (x, z) -> surfaceBiome(biomes, sampler, x, z).equals(biome));
        int ccx = Math.floorDiv(centre[0], 16);
        int ccz = Math.floorDiv(centre[1], 16);
        int x0 = (ccx - CHUNK_RADIUS) * 16;
        int z0 = (ccz - CHUNK_RADIUS) * 16;
        ServerChunkCache chunks = level.getChunkSource();
        ChunkPos centrePos = new ChunkPos(ccx, ccz);
        // one ticket over the 5 x 5 chunks: the server generates them (and the ring of neighbours their decorations
        // need) on all its worker threads; getChunk then waits on the main thread like /forceload does
        chunks.addTicketAndLoadWithRadius(TicketType.PLAYER_SPAWN, centrePos, CHUNK_RADIUS);
        try {
            for (int dz = -CHUNK_RADIUS; dz <= CHUNK_RADIUS; dz++) {
                for (int dx = -CHUNK_RADIUS; dx <= CHUNK_RADIUS; dx++) {
                    level.getChunk(ccx + dx, ccz + dz);
                }
            }
            int maxTop = level.getMinY();
            int minFloor = Integer.MAX_VALUE;
            for (int z = 0; z < SIZE; z++) {
                for (int x = 0; x < SIZE; x++) {
                    maxTop = Math.max(maxTop, level.getHeight(Heightmap.Types.WORLD_SURFACE, x0 + x, z0 + z) - 1);
                    minFloor = Math.min(minFloor, level.getHeight(Heightmap.Types.OCEAN_FLOOR, x0 + x, z0 + z) - 1);
                }
            }
            int base = Math.max(level.getMinY(), minFloor - 6);
            base = Math.max(base, maxTop - 180);
            int top = Math.max(maxTop, base + 1);
            int[] vox = BlockSampler.sample(level, x0, z0, SIZE, SIZE, base, top);
            BufferedImage img = new IsoRenderer(SIZE, top - base + 1, SIZE, vox).render();
            return new Shot(IsoRenderer.frame(img, FRAME_W, FRAME_H), x0 + SIZE / 2, z0 + SIZE / 2, base, top);
        } finally {
            chunks.removeTicketWithRadius(TicketType.PLAYER_SPAWN, centrePos, CHUNK_RADIUS);
        }
    }
}
