package com.wayfarers.world;

import com.wayfarers.Wayfarers;
import com.wayfarers.config.WayfarersConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraftforge.event.CommandEvent;
import net.minecraftforge.event.TickEvent;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.regex.Pattern;

/**
 * The terrain check of {@link FittedJigsawStructure}: samples the noise terrain under a start piece's footprint
 * (corners, edges, centre: a grid of 3 x 3 to 7 x 7 points) and says whether the site fits and how far to move the
 * pieces vertically. Pure functions of the generator's noise, so {@code /locate} and real generation agree.
 */
public final class SiteFit {
    /** Rise over run between two neighbouring samples is measured on at least this many blocks. */
    private static final int MIN_STEP = 4;
    private static final Pattern PLACE = Pattern.compile("(^|\\brun )place (structure|jigsaw|template) ");
    /** Set on the server thread for the length of a {@code /place} command (the player asked for that spot). */
    private static final ThreadLocal<Boolean> BYPASS = ThreadLocal.withInitial(() -> false);
    /** Per structure: [accepted, rejected], and the rejection reasons, for /wayfarers fitcheck. */
    private static final Map<String, AtomicLong[]> STATS = new ConcurrentHashMap<>();
    private static final Map<String, AtomicLong> REASONS = new ConcurrentHashMap<>();

    private SiteFit() {}

    public record Verdict(boolean ok, int dy, String why) {
        static Verdict reject(String why) {
            return new Verdict(false, 0, why);
        }

        static Verdict accept(int dy) {
            return new Verdict(true, dy, "fits");
        }
    }

    /** One terrain column: first free y above anything (water included) and above solid ground. */
    private record Sample(int x, int z, int top, int floor) {
        boolean wet() {
            return this.top > this.floor;
        }

        int depth() {
            return this.top - this.floor;
        }
    }

    // ------------------------------------------------------------------ switches

    public static void register() {
        CommandEvent.BUS.addListener(SiteFit::bypassForCommand);
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> BYPASS.remove());
    }

    /** {@code /place structure}: the operator chose the spot, build there whatever the terrain. */
    static void bypassForCommand(CommandEvent event) {
        String input = event.getParseResults().getReader().getString();
        if (PLACE.matcher(input.startsWith("/") ? input.substring(1) : input).find()) {
            BYPASS.set(true);
        }
    }

    /** Runs {@code task} on this thread with the site check off, like {@code /place structure} (the CI driver). */
    public static <T> T unchecked(java.util.function.Supplier<T> task) {
        boolean was = BYPASS.get();
        BYPASS.set(true);
        try {
            return task.get();
        } finally {
            BYPASS.set(was);
        }
    }

    static boolean active() {
        if (BYPASS.get()) {
            return false;
        }
        try {
            return WayfarersConfig.STRUCTURE_FIT.get();
        } catch (IllegalStateException notLoaded) {
            return true;
        }
    }

    static void record(String name, Verdict v) {
        STATS.computeIfAbsent(name, k -> new AtomicLong[] {new AtomicLong(), new AtomicLong()})[v.ok() ? 0 : 1].incrementAndGet();
        if (!v.ok()) {
            REASONS.computeIfAbsent(name + " " + v.why().split(" ")[0], k -> new AtomicLong()).incrementAndGet();
        }
    }

    /** "accepted N, rejected M (water 3, spread 7)" for a structure, from what this server has evaluated so far. */
    public static String stats(String name) {
        AtomicLong[] s = STATS.get(name);
        if (s == null) {
            return "no site evaluated";
        }
        Map<String, Long> why = new TreeMap<>();
        REASONS.forEach((k, n) -> {
            if (k.startsWith(name + " ")) {
                why.put(k.substring(name.length() + 1), n.get());
            }
        });
        return String.format(Locale.ROOT, "sites accepted %d, rejected %d %s", s[0].get(), s[1].get(), why);
    }

    // ------------------------------------------------------------------ geometry

    /** Ground layer of the start piece (world y). */
    public static int groundY(FittedJigsawStructure.Fit fit, StructurePiece piece) {
        if (fit.projected() && piece instanceof PoolElementStructurePiece pool) {
            return piece.getBoundingBox().minY() + pool.getGroundLevelDelta() - 1;
        }
        return piece.getBoundingBox().minY() + fit.ground();
    }

    /** World footprint {minX, minZ, maxX, maxZ}: the template's built columns when known, else the piece's box. */
    public static int[] footprint(StructurePiece piece) {
        BoundingBox box = piece.getBoundingBox();
        int[] all = {box.minX(), box.minZ(), box.maxX(), box.maxZ()};
        if (!(piece instanceof PoolElementStructurePiece pool) || !(pool.getElement() instanceof ChunkedPoolElement chunked)) {
            return all;
        }
        Optional<List<Integer>> fp = chunked.footprint();
        if (fp.isEmpty()) {
            return all;
        }
        List<Integer> f = fp.get();
        Rotation rot = pool.getRotation();
        BlockPos a = pool.getPosition().offset(StructureTemplate.transform(new BlockPos(f.get(0), 0, f.get(1)), Mirror.NONE, rot, BlockPos.ZERO));
        BlockPos b = pool.getPosition().offset(StructureTemplate.transform(new BlockPos(f.get(2), 0, f.get(3)), Mirror.NONE, rot, BlockPos.ZERO));
        return new int[] {
                Mth.clamp(Math.min(a.getX(), b.getX()), box.minX(), box.maxX()),
                Mth.clamp(Math.min(a.getZ(), b.getZ()), box.minZ(), box.maxZ()),
                Mth.clamp(Math.max(a.getX(), b.getX()), box.minX(), box.maxX()),
                Mth.clamp(Math.max(a.getZ(), b.getZ()), box.minZ(), box.maxZ())};
    }

    /** The direction the template's {@code sea_side} faces in the world, after the piece's rotation. */
    public static Optional<Direction> seaSide(FittedJigsawStructure.Fit fit, StructurePiece piece) {
        Rotation rot = piece instanceof PoolElementStructurePiece pool ? pool.getRotation() : Rotation.NONE;
        return fit.seaSide().map(Direction::byName).map(rot::rotate);
    }

    // ------------------------------------------------------------------ the cheap pre-test

    /** A pre-test score at or below this: the spot looks right, assemble and check it at once. */
    static final double LIKELY = 1.0;
    /** A pre-test score at or above this: not worth an assembly (water where there must be land, dry sea floor...). */
    static final double HOPELESS = 3.0;

    /**
     * How well a spot looks before any jigsaw is assembled (lower is better, {@link #LIKELY} and below: probably fits):
     * the terrain at the centre and the four corners of a square of half side {@code 0.75 half} around the start
     * position, where {@code half} is half the smallest side of the start template, so the square stays inside the
     * footprint whatever the rotation. Five columns (about one tenth of a full check) and no assembly; the full check
     * ({@link #evaluate}) still decides. Only ranks the nudges of one grid cell, so it may be rough.
     */
    static double preScore(FittedJigsawStructure.Fit fit, Structure.GenerationContext ctx, BlockPos start, int half) {
        if (fit.mode().equals("cavern")) {
            return 0.0;  // the Nether's fit needs whole columns: no cheap test, the nudges keep their order
        }
        ChunkGenerator gen = ctx.chunkGenerator();
        LevelHeightAccessor heights = ctx.heightAccessor();
        RandomState rs = ctx.randomState();
        int r = Math.max(2, Math.round(half * 0.75F));
        int[][] at = {{0, 0}, {-r, -r}, {r, -r}, {-r, r}, {r, r}};
        boolean needTop = !fit.mode().equals("underground");
        boolean needFloor = !fit.mode().equals("sky");
        int n = at.length;
        int[] top = new int[n];
        int[] floor = new int[n];
        int wet = 0;
        for (int k = 0; k < n; k++) {
            int x = start.getX() + at[k][0];
            int z = start.getZ() + at[k][1];
            top[k] = needTop ? gen.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, heights, rs) : 0;
            floor[k] = needFloor ? gen.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, heights, rs) : top[k];
            if (!needTop) {
                top[k] = floor[k];
            }
            wet += top[k] > floor[k] ? 1 : 0;
        }
        double wetShare = wet / (double) n;
        switch (fit.mode()) {
            case "land", "wetland" -> {
                boolean wetland = fit.mode().equals("wetland");
                int lo = Integer.MAX_VALUE;
                int hi = Integer.MIN_VALUE;
                for (int k = 0; k < n; k++) {
                    int h = wetland ? top[k] : floor[k];
                    lo = Math.min(lo, h);
                    hi = Math.max(hi, h);
                }
                double score = (hi - lo) / (double) Math.max(1, fit.spread());
                if (wetShare > fit.wet() + 1.0E-4) {
                    score = Math.max(score, 1.5 + 4.0 * (wetShare - fit.wet()));
                }
                if (wetShare < fit.minWet() - 1.0E-4) {
                    score = Math.max(score, 1.5 + 4.0 * (fit.minWet() - wetShare));
                }
                return score;
            }
            case "coast" -> {
                // a shore crosses the footprint: some samples wet, some dry, the dry ground near the sea
                if (wet == 0 || wet == n) {
                    return HOPELESS;
                }
                int sea = gen.getSeaLevel();
                int worst = 0;
                for (int k = 0; k < n; k++) {
                    if (top[k] == floor[k]) {
                        worst = Math.max(worst, Math.abs(floor[k] - sea));
                    }
                }
                return 0.5 * Math.abs(wetShare - 0.5) * 2 + worst / (double) Math.max(2, fit.spread() + 2);
            }
            case "seabed" -> {
                if (wetShare < fit.wet() - 1.0E-4) {
                    return wet == 0 ? HOPELESS : 1.5 + 4.0 * (fit.wet() - wetShare);
                }
                int lo = Integer.MAX_VALUE;
                int hi = Integer.MIN_VALUE;
                int shallowest = Integer.MAX_VALUE;
                for (int k = 0; k < n; k++) {
                    lo = Math.min(lo, floor[k]);
                    hi = Math.max(hi, floor[k]);
                    shallowest = Math.min(shallowest, top[k] - floor[k]);
                }
                double score = (hi - lo) / (double) Math.max(1, fit.spread());
                if (shallowest < fit.depth()) {
                    score = Math.max(score, 1.2 + (fit.depth() - shallowest) / (double) Math.max(1, fit.depth()));
                }
                return score;
            }
            case "sky" -> {
                // the start position is about the structure's middle: the terrain must stay well below it
                int highest = Integer.MIN_VALUE;
                for (int k = 0; k < n; k++) {
                    highest = Math.max(highest, top[k] - 1);
                }
                int over = highest - (start.getY() - fit.clearance());
                return over <= 0 ? 0.0 : over / (double) Math.max(1, fit.lift() + fit.clearance());
            }
            case "underground" -> {
                int lowest = Integer.MAX_VALUE;
                for (int k = 0; k < n; k++) {
                    lowest = Math.min(lowest, floor[k] - 1);
                }
                int under = start.getY() + fit.cover() - lowest;
                return under <= 0 ? 0.0 : under / (double) Math.max(1, fit.lift() + fit.cover());
            }
            default -> {
                return 0.0;
            }
        }
    }

    /** The rejection reason recorded for a cell whose every nudge failed the pre-test (no assembly was made). */
    static String preReason(FittedJigsawStructure.Fit fit, double bestScore) {
        return String.format(Locale.ROOT, "pretest %s %.1f", fit.mode(), bestScore);
    }

    // ------------------------------------------------------------------ the check

    public static Verdict evaluate(FittedJigsawStructure.Fit fit, StructurePiece start, Structure.GenerationContext ctx) {
        ChunkGenerator gen = ctx.chunkGenerator();
        LevelHeightAccessor heights = ctx.heightAccessor();
        RandomState rs = ctx.randomState();
        BoundingBox box = start.getBoundingBox();
        int ground = groundY(fit, start);
        int[] fp = fit.projected() ? footprint(start) : new int[] {box.minX(), box.minZ(), box.maxX(), box.maxZ()};
        int w = fp[2] - fp[0];
        int d = fp[3] - fp[1];
        int nx = Mth.clamp(Math.round(w / 16.0F) + 1, 3, 7);
        int nz = Mth.clamp(Math.round(d / 16.0F) + 1, 3, 7);

        if (fit.mode().equals("cavern")) {
            return cavern(fit, box, gen, heights, rs, fp, nx, nz);
        }
        Sample[] s = new Sample[nx * nz];
        for (int j = 0; j < nz; j++) {
            for (int i = 0; i < nx; i++) {
                int x = fp[0] + Math.round(w * i / (float) (nx - 1));
                int z = fp[1] + Math.round(d * j / (float) (nz - 1));
                int top = gen.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, heights, rs);
                int floor = gen.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, heights, rs);
                s[j * nx + i] = new Sample(x, z, top, floor);
            }
        }
        return switch (fit.mode()) {
            case "land", "wetland" -> land(fit, s, nx, nz, ground);
            case "coast" -> coast(fit, s, nx, nz, ground, gen.getSeaLevel(), seaSide(fit, start).orElse(Direction.SOUTH), fp);
            case "seabed" -> seabed(fit, s, nx, nz, ground);
            case "sky" -> sky(fit, s, box, heights);
            case "underground" -> underground(fit, s, box, heights);
            default -> Verdict.accept(0);
        };
    }

    /** Dry ground, flat enough: the start moves to the footprint's median ground (within reach of the foundations). */
    private static Verdict land(FittedJigsawStructure.Fit fit, Sample[] s, int nx, int nz, int ground) {
        boolean wetland = fit.mode().equals("wetland");
        int wet = 0;
        int[] h = new int[s.length];
        for (int k = 0; k < s.length; k++) {
            if (s[k].wet()) {
                wet++;
            }
            // the top block of the ground (wetland: the water surface counts as ground)
            h[k] = (wetland ? s[k].top() : s[k].floor()) - 1;
        }
        if (wet > fit.wet() * s.length + 1.0E-4) {
            return Verdict.reject(String.format(Locale.ROOT, "water %d%% > %d%%", wet * 100 / s.length, Math.round(fit.wet() * 100)));
        }
        if (wet < fit.minWet() * s.length - 1.0E-4) {
            return Verdict.reject(String.format(Locale.ROOT, "dry %d%% water < %d%%", wet * 100 / s.length, Math.round(fit.minWet() * 100)));
        }
        int[] sorted = h.clone();
        Arrays.sort(sorted);
        int min = sorted[0];
        int max = sorted[sorted.length - 1];
        if (max - min > fit.spread()) {
            return Verdict.reject("spread " + (max - min) + " > " + fit.spread());
        }
        double slope = steepest(s, h, nx, nz);
        if (slope > fit.slope()) {
            return Verdict.reject(String.format(Locale.ROOT, "slope %.2f > %.2f", slope, fit.slope()));
        }
        int target = Math.min(sorted[sorted.length / 2], min + fit.drop());
        return Verdict.accept(target - ground);
    }

    /** Water on the template's sea side, land on the other, a shore near sea level; the ground layer sits on the sea. */
    private static Verdict coast(FittedJigsawStructure.Fit fit, Sample[] s, int nx, int nz, int ground, int seaLevel,
                                 Direction sea, int[] fp) {
        int seaN = 0;
        int seaWet = 0;
        int landN = 0;
        int landDry = 0;
        int dryN = 0;
        int[] dry = new int[s.length];
        int[] h = new int[s.length];
        for (int k = 0; k < s.length; k++) {
            Sample p = s[k];
            double t = switch (sea) {
                case EAST -> (p.x() - fp[0]) / (double) Math.max(1, fp[2] - fp[0]);
                case WEST -> (fp[2] - p.x()) / (double) Math.max(1, fp[2] - fp[0]);
                case NORTH -> (fp[3] - p.z()) / (double) Math.max(1, fp[3] - fp[1]);
                default -> (p.z() - fp[1]) / (double) Math.max(1, fp[3] - fp[1]);
            };
            if (t >= 0.66) {
                seaN++;
                seaWet += p.wet() ? 1 : 0;
            } else if (t <= 0.34) {
                landN++;
                landDry += p.wet() ? 0 : 1;
            }
            if (!p.wet()) {
                dry[dryN++] = p.floor() - 1;
            }
            h[k] = p.wet() ? Integer.MIN_VALUE : p.floor() - 1;
        }
        if (seaN == 0 || seaWet < fit.wet() * seaN) {
            return Verdict.reject("sea side dry " + seaWet + "/" + seaN);
        }
        if (landN == 0 || landDry < fit.land() * landN) {
            return Verdict.reject("land side wet " + landDry + "/" + landN);
        }
        int[] d = Arrays.copyOf(dry, dryN);
        Arrays.sort(d);
        int shore = d[d.length / 2];
        if (shore > seaLevel - 1 + fit.spread() || shore < seaLevel - 3) {
            return Verdict.reject("shore " + (shore - seaLevel + 1) + " from the sea");
        }
        double slope = steepest(s, h, nx, nz);
        if (slope > fit.slope()) {
            return Verdict.reject(String.format(Locale.ROOT, "slope %.2f > %.2f", slope, fit.slope()));
        }
        // the ground layer (dock deck) one block above the sea surface (the top water block is seaLevel - 1)
        return Verdict.accept(seaLevel - ground);
    }

    /** Under water, deep enough, on a flat enough sea floor: the start moves to the median floor. */
    private static Verdict seabed(FittedJigsawStructure.Fit fit, Sample[] s, int nx, int nz, int ground) {
        int wet = 0;
        int[] depths = new int[s.length];
        int[] h = new int[s.length];
        for (int k = 0; k < s.length; k++) {
            if (s[k].wet()) {
                depths[wet++] = s[k].depth();
            }
            h[k] = s[k].floor() - 1;
        }
        if (wet < fit.wet() * s.length) {
            return Verdict.reject(String.format(Locale.ROOT, "water %d%% < %d%%", wet * 100 / s.length, Math.round(fit.wet() * 100)));
        }
        int[] dd = Arrays.copyOf(depths, wet);
        Arrays.sort(dd);
        if (dd[dd.length / 2] < fit.depth()) {
            return Verdict.reject("depth " + dd[dd.length / 2] + " < " + fit.depth());
        }
        int[] sorted = h.clone();
        Arrays.sort(sorted);
        if (sorted[sorted.length - 1] - sorted[0] > fit.spread()) {
            return Verdict.reject("spread " + (sorted[sorted.length - 1] - sorted[0]) + " > " + fit.spread());
        }
        double slope = steepest(s, h, nx, nz);
        if (slope > fit.slope()) {
            return Verdict.reject(String.format(Locale.ROOT, "slope %.2f > %.2f", slope, fit.slope()));
        }
        int target = Math.min(sorted[sorted.length / 2], sorted[0] + fit.drop());
        return Verdict.accept(target - ground);
    }

    /** Fixed height in the air: the terrain stays {@code clearance} below the underside (lifted by up to {@code lift}). */
    private static Verdict sky(FittedJigsawStructure.Fit fit, Sample[] s, BoundingBox box, LevelHeightAccessor heights) {
        int highest = heights.getMinY();
        for (Sample p : s) {
            highest = Math.max(highest, p.top() - 1);
        }
        int gap = box.minY() - highest;
        if (gap >= fit.clearance()) {
            return Verdict.accept(0);
        }
        int need = fit.clearance() - gap;
        if (need > fit.lift() || box.maxY() + need >= heights.getMaxY()) {
            return Verdict.reject("terrain " + (-gap) + " above the underside");
        }
        return Verdict.accept(need);
    }

    /** Fixed height in the rock: {@code cover} blocks between its top and the ground or sea floor (sunk by up to {@code lift}). */
    private static Verdict underground(FittedJigsawStructure.Fit fit, Sample[] s, BoundingBox box, LevelHeightAccessor heights) {
        int lowest = Integer.MAX_VALUE;
        for (Sample p : s) {
            lowest = Math.min(lowest, p.floor() - 1);
        }
        int cover = lowest - box.maxY();
        if (cover >= fit.cover()) {
            return Verdict.accept(0);
        }
        int need = fit.cover() - cover;
        if (need > fit.lift() || box.minY() - need <= heights.getMinY() + 4) {
            return Verdict.reject("cover " + cover + " < " + fit.cover());
        }
        return Verdict.accept(-need);
    }

    /** Nether: open air or the lava sea just above the deck over at least {@code open} of the footprint. */
    private static Verdict cavern(FittedJigsawStructure.Fit fit, BoundingBox box, ChunkGenerator gen, LevelHeightAccessor heights,
                                  RandomState rs, int[] fp, int nx, int nz) {
        int deck = box.minY() + fit.ground();
        int open = 0;
        int n = nx * nz;
        for (int j = 0; j < nz; j++) {
            for (int i = 0; i < nx; i++) {
                int x = fp[0] + Math.round((fp[2] - fp[0]) * i / (float) (nx - 1));
                int z = fp[1] + Math.round((fp[3] - fp[1]) * j / (float) (nz - 1));
                NoiseColumn column = gen.getBaseColumn(x, z, heights, rs);
                boolean clear = true;
                for (int y = deck + 1; y <= deck + 3 && clear; y++) {
                    BlockState state = column.getBlock(y);
                    clear = state.isAir() || !state.getFluidState().isEmpty();
                }
                open += clear ? 1 : 0;
            }
        }
        return open >= fit.open() * n ? Verdict.accept(0)
                : Verdict.reject(String.format(Locale.ROOT, "open %d%% < %d%%", open * 100 / n, Math.round(fit.open() * 100)));
    }

    /** Steepest rise over run between two horizontally or vertically neighbouring samples (skips MIN_VALUE heights). */
    private static double steepest(Sample[] s, int[] h, int nx, int nz) {
        double worst = 0;
        for (int j = 0; j < nz; j++) {
            for (int i = 0; i < nx; i++) {
                int k = j * nx + i;
                if (h[k] == Integer.MIN_VALUE) {
                    continue;
                }
                if (i + 1 < nx && h[k + 1] != Integer.MIN_VALUE) {
                    worst = Math.max(worst, Math.abs(h[k + 1] - h[k]) / (double) Math.max(MIN_STEP, s[k + 1].x() - s[k].x()));
                }
                if (j + 1 < nz && h[k + nx] != Integer.MIN_VALUE) {
                    worst = Math.max(worst, Math.abs(h[k + nx] - h[k]) / (double) Math.max(MIN_STEP, s[k + nx].z() - s[k].z()));
                }
            }
        }
        return worst;
    }
}
