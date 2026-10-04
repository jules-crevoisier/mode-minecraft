package com.wayfarers.command;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.datafixers.util.Pair;
import com.wayfarers.Wayfarers;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSource;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.MapColor;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.function.BiPredicate;

/**
 * /wayfarers biomeshots [biome]: for every biome of the mod, finds the nearest place where it covers the most ground,
 * really generates the 5 x 5 chunks there (trees, plants, ores, structures included) and draws them block by block
 * as an isometric diorama ({@link IsoRenderer}). Cave biomes get a cutaway: the rock above the cave floors is taken
 * away. Writes wayfarers-biome-&lt;id&gt;.png and the legend wayfarers-biomes.txt into the server folder (CI publishes
 * them with the world map, the wiki shows them on the biome cards).
 */
public final class BiomeShotsCommand {
    private static final int CHUNK_RADIUS = 2;
    private static final int SIZE = (CHUNK_RADIUS * 2 + 1) * 16;
    private static final int FRAME_W = 672;
    private static final int FRAME_H = 504;
    private static final int SEARCH_RADIUS = 6400;
    private static final int SEARCH_STEP = 32;
    private static final int REFINE_GRID = 64;
    private static final int REFINE_STEP = 8;
    private static final int[] CAVE_YS = {-48, -40, -32, -24, -16, -8, 0, 8, 16, 24, 32, 40};
    private static final long BUDGET_MS = 9 * 60_000L;
    /** Biomes that only live underground (they are never the surface biome, so they get the cutaway). */
    private static final Set<String> CAVES = Set.of("crystal_caverns", "underground_jungle", "deep_abyss",
            "thermal_caves", "fungal_grotto", "mithril_hollows");

    private static final int TINT_NONE = 0;
    private static final int TINT_GRASS = 1;
    private static final int TINT_FOLIAGE = 2;
    private static final int TINT_WATER = 3;

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
        Map<String, Holder<Biome>> targets = new java.util.TreeMap<>();
        for (Holder<Biome> b : biomes.possibleBiomes()) {
            String id = id(b);
            if (id.startsWith(Wayfarers.MODID + ":") && (only == null || id.endsWith(":" + only))) {
                targets.put(id, b);
            }
        }
        if (targets.isEmpty()) {
            src.sendFailure(Component.literal("Biome shots failed: no Wayfarers biome generates in this world (is the overhaul on?)"));
            return 0;
        }
        Search search = new Search(biomes, sampler, targets);
        search.run();
        Wayfarers.LOGGER.info("biome shot search done in {} ms, {} biomes", System.currentTimeMillis() - start, targets.size());

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
            boolean cave = CAVES.contains(path) || search.surface.get(id) == null;
            BlockPos hit = cave ? search.cave.get(id) : search.surface.get(id);
            if (hit == null) {
                Pair<BlockPos, Holder<Biome>> found = level.findClosestBiome3d(h -> h.equals(e.getValue()), BlockPos.ZERO,
                        SEARCH_RADIUS, SEARCH_STEP, 64);
                hit = found == null ? null : found.getFirst();
            }
            if (hit == null) {
                lines.add(String.format(Locale.ROOT, "%-30s skipped: not found within %d blocks", id, SEARCH_RADIUS));
                continue;
            }
            try {
                Shot shot = shoot(level, biomes, sampler, e.getValue(), hit, cave);
                ImageIO.write(shot.image, "png", dir.resolve("wayfarers-biome-" + path + ".png").toFile());
                long ms = System.currentTimeMillis() - t;
                lines.add(String.format(Locale.ROOT, "%-30s %-7s at %d %d y %d..%d  %d ms", id, cave ? "cave" : "surface",
                        shot.x, shot.z, shot.y0, shot.y1, ms));
                Wayfarers.LOGGER.info("biome shot {} ({}) at {} {}, y {}..{}, {} ms", id, cave ? "cave" : "surface",
                        shot.x, shot.z, shot.y0, shot.y1, ms);
                done++;
            } catch (IOException | RuntimeException ex) {
                String why = String.valueOf(ex.getMessage()).replace("Exception", "error");
                lines.add(String.format(Locale.ROOT, "%-30s skipped: %s", id, why));
                Wayfarers.LOGGER.warn("biome shot {} skipped ({})", id, why);
            }
            writeLegend(dir, lines);
            // the server does not tick while this command runs: let the chunk map unload (and save) the areas
            // already drawn, as a tick would, so memory stays flat over the 41 biomes (no block or entity ticking)
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
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(dir.resolve("wayfarers-biomes.txt")))) {
            lines.forEach(out::println);
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    static String id(Holder<Biome> b) {
        return b.unwrapKey().map(k -> k.identifier().toString()).orElse("?");
    }

    // ------------------------------------------------------------------ finding a good spot

    /**
     * One spiral walk from 0,0 for all biomes at once. Surface biomes are looked up with the climate at depth 0 (the
     * ground itself, cheap and exact for what you see), cave biomes at a dozen heights between y -48 and 40.
     */
    private static final class Search {
        final BiomeSource biomes;
        final Climate.Sampler sampler;
        final Map<String, Holder<Biome>> targets;
        final Map<String, BlockPos> surface = new HashMap<>();
        final Map<String, BlockPos> cave = new HashMap<>();

        Search(BiomeSource biomes, Climate.Sampler sampler, Map<String, Holder<Biome>> targets) {
            this.biomes = biomes;
            this.sampler = sampler;
            this.targets = targets;
        }

        boolean needSurface() {
            return biomes instanceof MultiNoiseBiomeSource
                    && targets.keySet().stream().anyMatch(id -> !isCave(id) && !surface.containsKey(id));
        }

        boolean needCave() {
            return targets.keySet().stream().anyMatch(id -> isCave(id) && !cave.containsKey(id))
                    || !(biomes instanceof MultiNoiseBiomeSource) && targets.keySet().stream().anyMatch(id -> !cave.containsKey(id));
        }

        static boolean isCave(String id) {
            return CAVES.contains(id.substring(id.indexOf(':') + 1));
        }

        void run() {
            int rings = SEARCH_RADIUS / SEARCH_STEP;
            boolean ns = needSurface();
            boolean nc = needCave();
            for (int r = 0; r <= rings && (ns || nc); r++) {
                for (int dz = -r; dz <= r; dz++) {
                    for (int dx = -r; dx <= r; dx += (dz == -r || dz == r || dx == r) ? 1 : 2 * r) {
                        int x = dx * SEARCH_STEP;
                        int z = dz * SEARCH_STEP;
                        if (ns) {
                            record(surface, surfaceBiome(biomes, sampler, x, z), new BlockPos(x, 64, z));
                        }
                        if (nc) {
                            for (int y : CAVE_YS) {
                                record(cave, biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(y),
                                        QuartPos.fromBlock(z), sampler), new BlockPos(x, y, z));
                            }
                        }
                    }
                }
                ns = ns && needSurface();
                nc = nc && needCave();
            }
        }

        private void record(Map<String, BlockPos> into, Holder<Biome> b, BlockPos pos) {
            String id = id(b);
            if (targets.containsKey(id) && !into.containsKey(id)) {
                into.put(id, pos);
            }
        }
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

    // ------------------------------------------------------------------ generating and drawing

    private record Shot(BufferedImage image, int x, int z, int y0, int y1) {}

    private static Shot shoot(ServerLevel level, BiomeSource biomes, Climate.Sampler sampler, Holder<Biome> biome,
                              BlockPos hit, boolean cave) {
        int[] centre;
        int caveY = hit.getY();
        if (cave) {
            int y = hit.getY();
            centre = bestWindow(hit, (x, z) -> biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(y),
                    QuartPos.fromBlock(z), sampler).equals(biome));
            // the height where the biome fills the window best
            int bestCount = -1;
            for (int yy = level.getMinY() + 8; yy <= 64; yy += 4) {
                int count = 0;
                for (int j = 0; j < 5; j++) {
                    for (int i = 0; i < 5; i++) {
                        int x = centre[0] - SIZE / 2 + 8 + i * 16;
                        int z = centre[1] - SIZE / 2 + 8 + j * 16;
                        if (biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(yy), QuartPos.fromBlock(z), sampler).equals(biome)) {
                            count++;
                        }
                    }
                }
                if (count > bestCount || count == bestCount && Math.abs(yy - hit.getY()) < Math.abs(caveY - hit.getY())) {
                    bestCount = count;
                    caveY = yy;
                }
            }
        } else {
            centre = bestWindow(hit, (x, z) -> surfaceBiome(biomes, sampler, x, z).equals(biome));
        }
        int ccx = Math.floorDiv(centre[0], 16);
        int ccz = Math.floorDiv(centre[1], 16);
        int x0 = (ccx - CHUNK_RADIUS) * 16;
        int z0 = (ccz - CHUNK_RADIUS) * 16;
        ServerChunkCache chunks = level.getChunkSource();
        ChunkPos centrePos = new ChunkPos(ccx, ccz);
        // one ticket over the 5 x 5 chunks: the server generates them (and the ring of neighbours their trees and
        // ores need) on all its worker threads; getChunk then waits on the main thread like /forceload does
        chunks.addTicketAndLoadWithRadius(TicketType.PLAYER_SPAWN, centrePos, CHUNK_RADIUS);
        try {
            for (int dz = -CHUNK_RADIUS; dz <= CHUNK_RADIUS; dz++) {
                for (int dx = -CHUNK_RADIUS; dx <= CHUNK_RADIUS; dx++) {
                    level.getChunk(ccx + dx, ccz + dz);
                }
            }
            return cave ? caveShot(level, x0, z0, caveY) : surfaceShot(level, x0, z0);
        } finally {
            chunks.removeTicketWithRadius(TicketType.PLAYER_SPAWN, centrePos, CHUNK_RADIUS);
        }
    }

    private static Shot surfaceShot(ServerLevel level, int x0, int z0) {
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
        int[] vox = sample(level, x0, z0, base, top, -1);
        BufferedImage img = new IsoRenderer(SIZE, top - base + 1, SIZE, vox, false).render();
        return new Shot(IsoRenderer.frame(img, FRAME_W, FRAME_H), x0 + SIZE / 2, z0 + SIZE / 2, base, top);
    }

    private static Shot caveShot(ServerLevel level, int x0, int z0, int y) {
        int base = Math.max(level.getMinY(), y - 28);
        int top = Math.min(level.getMaxY(), y + 16);
        int[] vox = sample(level, x0, z0, base, top, y);
        int sy = top - base + 1;
        vox = IsoRenderer.peel(vox, SIZE, sy, SIZE);
        BufferedImage img = new IsoRenderer(SIZE, sy, SIZE, vox, true).render();
        return new Shot(IsoRenderer.frame(img, FRAME_W, FRAME_H), x0 + SIZE / 2, z0 + SIZE / 2, base, top);
    }

    /** Reads the blocks of the box into voxels; biome tints come from the surface (or from tintY in caves). */
    private static int[] sample(ServerLevel level, int x0, int z0, int y0, int y1, int tintY) {
        int sy = y1 - y0 + 1;
        int[] vox = new int[sy * SIZE * SIZE];
        Map<BlockState, int[]> kinds = new IdentityHashMap<>();
        Map<Biome, int[]> tints = new IdentityHashMap<>();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int z = 0; z < SIZE; z++) {
            for (int x = 0; x < SIZE; x++) {
                int ty = tintY >= y0 ? tintY : level.getHeight(Heightmap.Types.WORLD_SURFACE, x0 + x, z0 + z) - 1;
                Biome b = level.getBiome(pos.set(x0 + x, ty, z0 + z)).value();
                int[] tint = tints.computeIfAbsent(b, k -> new int[] {
                        k.getSpecialEffects().grassColorOverride().orElse(0x79C05A),
                        k.getSpecialEffects().foliageColorOverride().orElse(0x59AE30),
                        k.getWaterColor()});
                for (int y = 0; y < sy; y++) {
                    pos.set(x0 + x, y0 + y, z0 + z);
                    BlockState state = level.getBlockState(pos);
                    if (state.isAir()) {
                        continue;
                    }
                    int[] k = kinds.computeIfAbsent(state, BiomeShotsCommand::classify);
                    if (k[0] == IsoRenderer.AIR) {
                        continue;
                    }
                    int rgb = switch (k[3]) {
                        case TINT_GRASS -> IsoRenderer.scale(tint[0], k[0] == IsoRenderer.PLANT ? 0.92 : 1.0);
                        case TINT_FOLIAGE -> IsoRenderer.scale(tint[1], 0.82);
                        case TINT_WATER -> tint[2];
                        default -> k[1];
                    };
                    vox[(y * SIZE + z) * SIZE + x] = IsoRenderer.voxel(k[0], rgb, k[2]);
                }
            }
        }
        return vox;
    }

    /** {kind, colour, flags, tint} for a block state. */
    private static int[] classify(BlockState state) {
        String name = BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
        FluidState fluid = state.getFluidState();
        boolean water = !fluid.isEmpty() && fluid.is(FluidTags.WATER);
        int glow = state.getLightEmission() > 0 ? IsoRenderer.GLOW : 0;
        MapColor map = state.getMapColor(EmptyBlockGetter.INSTANCE, BlockPos.ZERO);
        if (state.getBlock() instanceof LiquidBlock) {
            return water ? new int[] {IsoRenderer.WATER, 0x3F76E4, 0, TINT_WATER}
                    : new int[] {IsoRenderer.SOLID, 0xF07A1E, IsoRenderer.GLOW, TINT_NONE};
        }
        boolean noCollision = state.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO).isEmpty();
        if (water && noCollision && map == MapColor.WATER) {
            return new int[] {IsoRenderer.WATER, 0x3F76E4, 0, TINT_WATER};  // bubble columns, kelp, seagrass
        }
        if (map == MapColor.NONE) {
            return water ? new int[] {IsoRenderer.WATER, 0x3F76E4, 0, TINT_WATER} : new int[] {IsoRenderer.AIR, 0, 0, 0};
        }
        int wet = water ? IsoRenderer.WET : 0;
        int col = map.col;
        if (name.equals("snow") || name.endsWith("carpet") || name.equals("pink_petals") || name.equals("wildflowers")
                || name.equals("leaf_litter") || name.equals("lily_pad")) {
            int c = name.equals("snow") ? 0xF4F8FF : name.equals("lily_pad") ? 0x2E8A2E : col;
            return new int[] {IsoRenderer.CARPET, c, glow | wet, TINT_NONE};
        }
        if (noCollision) {
            boolean flower = state.is(BlockTags.FLOWERS) || state.is(BlockTags.SMALL_FLOWERS);
            if (flower) {
                return new int[] {IsoRenderer.PLANT, flowerColour(name, col), glow | wet | IsoRenderer.FLOWER, TINT_NONE};
            }
            int tint = map == MapColor.PLANT && (name.contains("grass") || name.contains("fern") || name.equals("vine")
                    || name.equals("sugar_cane") || name.equals("bush")) ? TINT_GRASS : TINT_NONE;
            return new int[] {IsoRenderer.PLANT, col, glow | wet, tint};
        }
        if (name.equals("grass_block")) {
            return new int[] {IsoRenderer.SOLID, col, glow | IsoRenderer.GRASSY, TINT_GRASS};
        }
        if (state.is(BlockTags.LEAVES)) {
            if (name.equals("spruce_leaves")) {
                return new int[] {IsoRenderer.SOLID, IsoRenderer.scale(0x619961, 0.8), glow, TINT_NONE};
            }
            if (name.equals("birch_leaves")) {
                return new int[] {IsoRenderer.SOLID, IsoRenderer.scale(0x80A755, 0.85), glow, TINT_NONE};
            }
            if (map == MapColor.PLANT) {
                return new int[] {IsoRenderer.SOLID, col, glow, TINT_FOLIAGE};
            }
            return new int[] {IsoRenderer.SOLID, IsoRenderer.scale(col, 0.85), glow, TINT_NONE};
        }
        return new int[] {IsoRenderer.SOLID, col, glow, TINT_NONE};
    }

    private static final Map<String, Integer> FLOWERS = new LinkedHashMap<>();

    static {
        FLOWERS.put("wither", 0x2A2A2A);
        FLOWERS.put("poppy", 0xD8302A);
        FLOWERS.put("rose", 0xD8302A);
        FLOWERS.put("red", 0xD8302A);
        FLOWERS.put("dandelion", 0xF2D13A);
        FLOWERS.put("sunflower", 0xF2D13A);
        FLOWERS.put("yellow", 0xF2D13A);
        FLOWERS.put("gold", 0xF2D13A);
        FLOWERS.put("cornflower", 0x4A78E0);
        FLOWERS.put("blue", 0x4A78E0);
        FLOWERS.put("orchid", 0x3FA8E8);
        FLOWERS.put("allium", 0xB060D0);
        FLOWERS.put("lilac", 0xC890D8);
        FLOWERS.put("purple", 0xB060D0);
        FLOWERS.put("violet", 0xB060D0);
        FLOWERS.put("peony", 0xF0A0C8);
        FLOWERS.put("pink", 0xF0A0C8);
        FLOWERS.put("cherry", 0xF0A0C8);
        FLOWERS.put("orange", 0xF08A2A);
        FLOWERS.put("torchflower", 0xF08A2A);
        FLOWERS.put("oxeye", 0xF2F2EC);
        FLOWERS.put("white", 0xF2F2EC);
        FLOWERS.put("lily", 0xF2F2EC);
        FLOWERS.put("azure", 0xF2F2EC);
        FLOWERS.put("daisy", 0xF2F2EC);
    }

    private static int flowerColour(String name, int mapColour) {
        for (Map.Entry<String, Integer> e : FLOWERS.entrySet()) {
            if (name.contains(e.getKey())) {
                return e.getValue();
            }
        }
        return mapColour != MapColor.PLANT.col ? mapColour : 0xE8C8F0;
    }
}
