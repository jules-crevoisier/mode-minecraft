package com.brasshaven.command;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.datafixers.util.Pair;
import com.brasshaven.Brasshaven;
import com.brasshaven.generated.GeneratedContent;
import com.brasshaven.world.FittedJigsawStructure;
import com.brasshaven.world.SiteFit;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * /brasshaven fitcheck [structure]: for every Overworld structure of the mod that stands on the terrain (land, shore,
 * sea floor, sky), finds the nearest one to 0,0 with the game's own locate, really generates the chunks around it and
 * measures how it sits:
 * <ul>
 *   <li><b>float</b>: share of the footprint's edge columns where a block at the ground layer has 3+ blocks of air
 *   (or water, except on a shore) right under it: a floating edge;</li>
 *   <li><b>buried</b>: share of the edge columns where the natural terrain just outside rises above the ground layer by
 *   more than the site check allows (4 blocks, or half the structure's height spread + 2): a buried wall or entrance;</li>
 *   <li><b>water</b>: share of the footprint flooded at the ground layer, against what the template floods itself
 *   (ponds, moats) plus the water the site check allows;</li>
 *   <li><b>clearance</b> (sky): columns where the terrain reaches the underside.</li>
 * </ul>
 * Each one is drawn in place as an isometric diorama (brasshaven-fit-&lt;id&gt;.png, {@link IsoRenderer}); the report
 * brasshaven-fit.txt gives one line per structure with OK / MISFIT / NOT_FOUND / SKIPPED. CI (tools/ci_smoke.py
 * --fit) runs it in a fresh vanilla world and fails on a MISFIT, so every structure is checked on real terrain.
 *
 * <p>{@code /brasshaven fitcheck shard <i> <n>} checks every n-th structure from the i-th (CI runs two shards on two
 * machines) and writes brasshaven-fit-shard&lt;i&gt;.txt. The whole command keeps to {@link #BUDGET_MS} and each
 * structure's locate to {@link #LOCATE_BUDGET_MS} (it searches in growing rings and gives up between two rings): what
 * is left is reported as SKIPPED with the reason, never as a pass. tools/ci_smoke.py waits {@code BUDGET_MS} plus
 * one structure's worth, so the server always answers before the script gives up.
 */
public final class FitCheckCommand {
    private static final int LOCATE_RADIUS = 64;
    /** Locate rings, in grid cells: the search grows ring by ring and checks the time between two of them. */
    private static final int[] LOCATE_STEPS = {4, 8, 12, 16, 24, 32, 40, 48, 56, 64};
    /** Whole command (keep in step with FIT_BUDGET in tools/ci_smoke.py). */
    static final long BUDGET_MS = 22 * 60_000L;
    /** One structure's locate. */
    static final long LOCATE_BUDGET_MS = 5 * 60_000L;
    private static final int MARGIN = 12;
    private static final int MAX_SIDE = 176;
    private static final int MAX_HEIGHT = 224;
    private static final int FRAME_W = 960;
    private static final int FRAME_H = 720;
    /** Misfit thresholds: edge columns floating, edge columns buried, columns of the sky footprint hitting terrain. */
    static final double MAX_FLOAT = 0.10;
    static final double MAX_BURIED = 0.25;
    static final double MAX_SKY_HIT = 0.02;
    static final double WATER_SLACK = 0.05;

    private FitCheckCommand() {}

    private record Measure(int edges, int floating, int buried, int inner, int water, double allowedWater,
                           int skyColumns, int skyHits) {
        double floatShare() {
            return this.edges == 0 ? 0 : this.floating / (double) this.edges;
        }

        double buriedShare() {
            return this.edges == 0 ? 0 : this.buried / (double) this.edges;
        }

        double waterShare() {
            return this.inner == 0 ? 0 : this.water / (double) this.inner;
        }

        double skyShare() {
            return this.skyColumns == 0 ? 0 : this.skyHits / (double) this.skyColumns;
        }

        List<String> problems() {
            List<String> out = new ArrayList<>();
            if (floatShare() > MAX_FLOAT) {
                out.add("floating edges");
            }
            if (buriedShare() > MAX_BURIED) {
                out.add("buried edges");
            }
            if (waterShare() > this.allowedWater) {
                out.add("flooded");
            }
            if (skyShare() > MAX_SKY_HIT) {
                out.add("terrain through the underside");
            }
            return out;
        }
    }

    static int run(CommandContext<CommandSourceStack> ctx, String only) {
        return run(ctx, only, 0, 1);
    }

    static int run(CommandContext<CommandSourceStack> ctx, String only, int shard, int shards) {
        CommandSourceStack src = ctx.getSource();
        if (shards < 1 || shard < 0 || shard >= shards) {
            src.sendFailure(Component.literal("Fit check failed: shard " + shard + " of " + shards));
            return 0;
        }
        String report = shards > 1 ? "brasshaven-fit-shard" + shard + ".txt" : "brasshaven-fit.txt";
        ServerLevel level = src.getServer().overworld();
        Path dir = src.getServer().getServerDirectory();
        long start = System.currentTimeMillis();
        var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        List<String> lines = new ArrayList<>();
        lines.add(String.format(Locale.ROOT, "structure fit%s: nearest of each to 0,0 (locate radius %d cells); misfit = float > %d%%, "
                        + "buried > %d%%, water > allowed, sky hits > %d%% of columns",
                shards > 1 ? " (shard " + (shard + 1) + " of " + shards + ")" : "",
                LOCATE_RADIUS, Math.round(MAX_FLOAT * 100), Math.round(MAX_BURIED * 100), Math.round(MAX_SKY_HIT * 100)));
        int checked = 0;
        int misfits = 0;
        int missing = 0;
        int skipped = 0;
        int index = -1;
        for (GeneratedContent.StructureInfo info : GeneratedContent.STRUCTURES) {
            String id = info.id();
            if (!info.dimension().equals("overworld") || only != null && !id.equals(only)) {
                continue;
            }
            index++;
            if (index % shards != shard) {
                continue;
            }
            Optional<Holder.Reference<Structure>> holder = registry.get(ResourceKey.create(Registries.STRUCTURE, Brasshaven.id(id)));
            if (holder.isEmpty() || !(holder.get().value() instanceof FittedJigsawStructure fitted)) {
                lines.add(String.format(Locale.ROOT, "%-22s %-11s SKIPPED   not a fitted structure", id, "-"));
                continue;
            }
            String mode = fitted.fit().mode();
            if (mode.equals("underground") || mode.equals("cavern")) {
                lines.add(String.format(Locale.ROOT, "%-22s %-11s SKIPPED   underground", id, mode));
                continue;
            }
            if (System.currentTimeMillis() - start > BUDGET_MS) {
                lines.add(String.format(Locale.ROOT, "%-22s %-11s SKIPPED   time budget used up (%d s)", id, mode, BUDGET_MS / 1000));
                skipped++;
                continue;
            }
            long t = System.currentTimeMillis();
            long deadline = Math.min(t + LOCATE_BUDGET_MS, start + BUDGET_MS + LOCATE_BUDGET_MS / 2);
            String line;
            try {
                line = check(level, dir, id, holder.get(), fitted, deadline);
            } catch (RuntimeException e) {
                line = String.format(Locale.ROOT, "%-22s %-11s ERROR     %s", id, mode, e);
                Brasshaven.LOGGER.warn("fit check of {} failed", id, e);
            }
            line += String.format(Locale.ROOT, "  %d ms  [%s]", System.currentTimeMillis() - t, SiteFit.stats(fitted.name()));
            lines.add(line);
            Brasshaven.LOGGER.info("fit check: {}", line);
            if (line.contains(" SKIPPED ")) {
                skipped++;
            } else {
                checked++;
            }
            misfits += line.contains(" MISFIT ") ? 1 : 0;
            missing += line.contains(" NOT_FOUND ") ? 1 : 0;
            writeReport(dir, report, lines);
            // let the chunk map unload the areas already measured (the server does not tick while this runs)
            long until = System.currentTimeMillis() + 300;
            level.getChunkSource().tick(() -> System.currentTimeMillis() < until, false);
        }
        if (!writeReport(dir, report, lines)) {
            src.sendFailure(Component.literal("Fit check failed: could not write " + report + " in " + dir));
            return 0;
        }
        long secs = (System.currentTimeMillis() - start) / 1000;
        String summary = String.format(Locale.ROOT, "Fit check written: %d structures, %d misfits, %d not found, %d skipped in %d s (%s)",
                checked, misfits, missing, skipped, secs, report);
        src.sendSuccess(() -> Component.literal(summary), false);
        return checked > 0 ? 1 : 0;
    }

    private static boolean writeReport(Path dir, String name, List<String> lines) {
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(dir.resolve(name)))) {
            lines.forEach(out::println);
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    private static String check(ServerLevel level, Path dir, String id, Holder<Structure> holder, FittedJigsawStructure fitted,
                                long deadline) {
        FittedJigsawStructure.Fit fit = fitted.fit();
        String mode = fit.mode();
        Pair<BlockPos, Holder<Structure>> found = null;
        int searched = 0;
        long t = System.currentTimeMillis();
        for (int radius : LOCATE_STEPS) {
            if (System.currentTimeMillis() > deadline) {
                return String.format(Locale.ROOT, "%-22s %-11s SKIPPED   locate gave up after %d s (searched rings up to %d of %d grid cells)",
                        id, mode, (System.currentTimeMillis() - t) / 1000, searched, LOCATE_RADIUS);
            }
            // the rings already searched cost nothing the second time (the structure check keeps its answers)
            found = level.getChunkSource().getGenerator()
                    .findNearestMapStructure(level, HolderSet.direct(holder), BlockPos.ZERO, radius, false);
            searched = radius;
            if (found != null) {
                break;
            }
        }
        if (found == null) {
            return String.format(Locale.ROOT, "%-22s %-11s NOT_FOUND within %d grid cells", id, mode, LOCATE_RADIUS);
        }
        ChunkPos startChunk = ChunkPos.containing(found.getFirst());
        ChunkAccess chunk = level.getChunk(startChunk.x(), startChunk.z(), ChunkStatus.STRUCTURE_STARTS);
        StructureStart start = chunk.getStartForStructure(fitted);
        if (start == null || !start.isValid() || start.getPieces().isEmpty()) {
            return String.format(Locale.ROOT, "%-22s %-11s NOT_FOUND located at %d %d but no start there", id, mode,
                    found.getFirst().getX(), found.getFirst().getZ());
        }
        StructurePiece piece = start.getPieces().get(0);
        BoundingBox box = piece.getBoundingBox();
        int g = SiteFit.groundY(fit, piece);
        int[] fp = fit.projected() ? SiteFit.footprint(piece) : new int[] {box.minX(), box.minZ(), box.maxX(), box.maxZ()};
        int cx = (fp[0] + fp[2]) >> 1;
        int cz = (fp[1] + fp[3]) >> 1;
        int radius = Mth.clamp((Math.max(fp[2] - fp[0], fp[3] - fp[1]) / 2 + MARGIN + 15) / 16, 1, 6);
        ChunkPos centre = ChunkPos.containing(new BlockPos(cx, 0, cz));
        ServerChunkCache chunks = level.getChunkSource();
        chunks.addTicketAndLoadWithRadius(TicketType.PLAYER_SPAWN, centre, radius);
        try {
            for (int dz = -radius; dz <= radius; dz++) {
                for (int dx = -radius; dx <= radius; dx++) {
                    level.getChunk(centre.x() + dx, centre.z() + dz);
                }
            }
            Measure m = measure(level, fit, fp, g, box);
            List<String> problems = m.problems();
            String shot = render(level, dir, id, fp, g, box, mode);
            return String.format(Locale.ROOT, "%-22s %-11s %-9s at %d %d ground y %d  float %d%%  buried %d%%  water %d%%/%d%%%s  %s%s",
                    id, mode, problems.isEmpty() ? "OK" : "MISFIT", cx, cz, g,
                    Math.round(m.floatShare() * 100), Math.round(m.buriedShare() * 100),
                    Math.round(m.waterShare() * 100), Math.round(Math.min(1.0, m.allowedWater()) * 100),
                    m.skyColumns() > 0 ? String.format(Locale.ROOT, "  sky hits %d%%", Math.round(m.skyShare() * 100)) : "",
                    problems.isEmpty() ? "" : String.join(", ", problems) + "  ", shot);
        } finally {
            chunks.removeTicketWithRadius(TicketType.PLAYER_SPAWN, centre, radius);
        }
    }

    // ------------------------------------------------------------------ measuring

    private static Measure measure(ServerLevel level, FittedJigsawStructure.Fit fit, int[] fp, int g, BoundingBox box) {
        String mode = fit.mode();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int edges = 0;
        int floating = 0;
        int buried = 0;
        if (!mode.equals("sky")) {
            boolean waterIsGap = !mode.equals("coast");
            boolean checkBuried = mode.equals("land") || mode.equals("wetland");
            // a site accepted with a height spread of S sits at its median: its high side may cut S/2 into the slope
            int buriedRise = Math.max(4, fit.spread() / 2 + 2);
            List<int[]> edge = new ArrayList<>();
            for (int x = fp[0]; x <= fp[2]; x++) {
                edge.add(new int[] {x, fp[1], 0, -1});
                edge.add(new int[] {x, fp[3], 0, 1});
            }
            for (int z = fp[1] + 1; z < fp[3]; z++) {
                edge.add(new int[] {fp[0], z, -1, 0});
                edge.add(new int[] {fp[2], z, 1, 0});
            }
            for (int[] e : edge) {
                edges++;
                for (int y = g + 1; y >= g - 2; y--) {
                    if (solid(level, pos.set(e[0], y, e[1]))) {
                        int gap = 0;
                        while (gap < 4 && isGap(level.getBlockState(pos.set(e[0], y - 1 - gap, e[1])), waterIsGap)) {
                            gap++;
                        }
                        floating += gap >= 3 ? 1 : 0;
                        break;
                    }
                }
                if (checkBuried && naturalTop(level, pos, e[0] + e[2], e[1] + e[3], g + 32, g - 24) >= g + buriedRise) {
                    buried++;
                }
            }
        }
        int inner = 0;
        int water = 0;
        if (mode.equals("land")) {
            for (int x = fp[0] + 1; x < fp[2]; x += 2) {
                for (int z = fp[1] + 1; z < fp[3]; z += 2) {
                    inner++;
                    if (level.getBlockState(pos.set(x, g + 1, z)).getFluidState().is(FluidTags.WATER)
                            || level.getBlockState(pos.set(x, g, z)).getFluidState().is(FluidTags.WATER)) {
                        water++;
                    }
                }
            }
        }
        int skyColumns = 0;
        int skyHits = 0;
        if (mode.equals("sky")) {
            var gen = level.getChunkSource().getGenerator();
            var rs = level.getChunkSource().randomState();
            for (int x = box.minX(); x <= box.maxX(); x += 4) {
                for (int z = box.minZ(); z <= box.maxZ(); z += 4) {
                    skyColumns++;
                    if (gen.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, level, rs) - 1 >= box.minY()) {
                        skyHits++;
                    }
                }
            }
        }
        return new Measure(edges, floating, buried, inner, water, fit.pond() + fit.wet() + WATER_SLACK, skyColumns, skyHits);
    }

    private static boolean solid(ServerLevel level, BlockPos pos) {
        return !level.getBlockState(pos).getCollisionShape(level, pos).isEmpty();
    }

    private static boolean isGap(BlockState state, boolean waterIsGap) {
        return state.isAir() || waterIsGap && !state.getFluidState().isEmpty() && state.getFluidState().is(FluidTags.WATER)
                && state.getCollisionShape(net.minecraft.world.level.EmptyBlockGetter.INSTANCE, BlockPos.ZERO).isEmpty();
    }

    /** Highest natural solid block (not leaves, not logs) of a column between y1 and y0, or y0 - 1. */
    private static int naturalTop(ServerLevel level, BlockPos.MutableBlockPos pos, int x, int z, int y1, int y0) {
        for (int y = y1; y >= y0; y--) {
            BlockState state = level.getBlockState(pos.set(x, y, z));
            if (state.isAir() || state.is(BlockTags.LEAVES) || state.is(BlockTags.LOGS)) {
                continue;
            }
            if (!state.getCollisionShape(level, pos).isEmpty()) {
                return y;
            }
        }
        return y0 - 1;
    }

    // ------------------------------------------------------------------ drawing

    private static String render(ServerLevel level, Path dir, String id, int[] fp, int g, BoundingBox box, String mode) {
        int x0 = fp[0] - MARGIN;
        int z0 = fp[1] - MARGIN;
        int sx = Math.min(MAX_SIDE, fp[2] - fp[0] + 1 + 2 * MARGIN);
        int sz = Math.min(MAX_SIDE, fp[3] - fp[1] + 1 + 2 * MARGIN);
        x0 += Math.max(0, (fp[2] - fp[0] + 1 + 2 * MARGIN - sx) / 2);
        z0 += Math.max(0, (fp[3] - fp[1] + 1 + 2 * MARGIN - sz) / 2);
        int lowest = Integer.MAX_VALUE;
        int highest = level.getMinY();
        for (int x = x0; x < x0 + sx; x += 4) {
            for (int z = z0; z < z0 + sz; z += 4) {
                lowest = Math.min(lowest, level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z) - 1);
                highest = Math.max(highest, level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1);
            }
        }
        int y1 = Math.min(level.getMaxY(), Math.max(box.maxY(), highest) + 2);
        int y0 = mode.equals("sky") ? Math.min(box.minY(), lowest) - 4 : Math.min(g, lowest) - 12;
        y0 = Math.max(level.getMinY(), Math.max(y0, y1 - MAX_HEIGHT));
        try {
            int[] vox = BlockSampler.sample(level, x0, z0, sx, sz, y0, y1);
            BufferedImage img = new IsoRenderer(sx, y1 - y0 + 1, sz, vox).render();
            String name = "brasshaven-fit-" + id + ".png";
            ImageIO.write(IsoRenderer.frame(img, FRAME_W, FRAME_H), "png", dir.resolve(name).toFile());
            return name;
        } catch (IOException | RuntimeException e) {
            return "no picture (" + e.getMessage() + ")";
        }
    }
}
