package com.wayfarers.world;

import com.mojang.datafixers.util.Either;
import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.wayfarers.Wayfarers;
import com.wayfarers.registry.ModWorldgen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.QuartPos;
import net.minecraft.core.Vec3i;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * {@code "type": "wayfarers:fitted_jigsaw"}: a vanilla jigsaw structure (every field of {@code minecraft:jigsaw},
 * unchanged) whose start must first fit the terrain ({@code "fit"}, written by tools/wf/placement.py).
 *
 * <p>Vanilla projects a jigsaw start on the height of one column, its centre, and builds it whatever the ground
 * around looks like: on a slope one side floats and the other is buried, on a lake shore the yard is a pond. Here
 * the start piece is assembled as usual, then {@link SiteFit} samples the real terrain under its footprint with
 * {@code ChunkGenerator.getBaseHeight} (the same noise the chunks will get, before any chunk exists) and either
 * rejects the site or moves the start to the right height (the footprint's median ground instead of its centre
 * column, the sea surface for a coast, above an island for a floating structure).
 *
 * <p>A rejected site behaves like a grid cell whose biome does not suit the structure: the start is simply absent,
 * {@code /locate}, structure compasses and explorer maps skip it and look at the next cell (they all go through
 * {@link #findValidGenerationPoint}, via the structure check). {@code /place structure} skips the check
 * ({@link SiteFit#bypassForCommand}), and {@code world.structureFit = false} in the common config turns it off.
 */
public final class FittedJigsawStructure extends Structure {
    public static final Set<String> MODES = Set.of("land", "wetland", "coast", "seabed", "sky", "underground", "cavern");

    /**
     * The terrain a start must find (see tools/wf/placement.py "Site selection" for what each mode checks).
     *
     * @param minWet land / wetland: at least this share of the samples under water (swamp huts want a marsh)
     * @param ground ground layer height above the template's lowest layer (for fixed-height structures: the deck)
     * @param pond   share of the footprint the template floods itself (ponds, moats): water the fit check expects
     */
    public record Fit(String mode, int spread, float slope, float wet, float minWet, float land, int drop, int depth,
                      int clearance, int cover, int lift, float open, int ground, Optional<String> seaSide, float pond) {
        private static final Codec<String> MODE = Codec.STRING.validate(m -> MODES.contains(m)
                ? DataResult.success(m) : DataResult.error(() -> "Unknown fit mode " + m + " (one of " + MODES + ")"));
        private static final Codec<String> SIDE = Codec.STRING.validate(s -> Set.of("north", "south", "east", "west").contains(s)
                ? DataResult.success(s) : DataResult.error(() -> "Unknown sea side " + s));
        public static final Codec<Fit> CODEC = RecordCodecBuilder.create(i -> i.group(
                MODE.fieldOf("mode").forGetter(Fit::mode),
                Codec.intRange(0, 256).optionalFieldOf("spread", 8).forGetter(Fit::spread),
                Codec.floatRange(0.0F, 16.0F).optionalFieldOf("slope", 0.8F).forGetter(Fit::slope),
                Codec.floatRange(0.0F, 1.0F).optionalFieldOf("wet", 0.05F).forGetter(Fit::wet),
                Codec.floatRange(0.0F, 1.0F).optionalFieldOf("min_wet", 0.0F).forGetter(Fit::minWet),
                Codec.floatRange(0.0F, 1.0F).optionalFieldOf("land", 0.5F).forGetter(Fit::land),
                Codec.intRange(0, 64).optionalFieldOf("drop", 10).forGetter(Fit::drop),
                Codec.intRange(0, 256).optionalFieldOf("depth", 0).forGetter(Fit::depth),
                Codec.intRange(0, 256).optionalFieldOf("clearance", 0).forGetter(Fit::clearance),
                Codec.intRange(0, 256).optionalFieldOf("cover", 0).forGetter(Fit::cover),
                Codec.intRange(0, 256).optionalFieldOf("lift", 0).forGetter(Fit::lift),
                Codec.floatRange(0.0F, 1.0F).optionalFieldOf("open", 0.0F).forGetter(Fit::open),
                Codec.intRange(0, 4096).optionalFieldOf("ground", 0).forGetter(Fit::ground),
                SIDE.optionalFieldOf("sea_side").forGetter(Fit::seaSide),
                Codec.floatRange(0.0F, 1.0F).optionalFieldOf("pond", 0.0F).forGetter(Fit::pond)
        ).apply(i, Fit::new));

        /** Placed on a heightmap (its start piece carries its ground depth), rather than at a fixed height. */
        public boolean projected() {
            return switch (this.mode) {
                case "land", "wetland", "coast", "seabed" -> true;
                default -> false;
            };
        }
    }

    public static final MapCodec<FittedJigsawStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            JigsawStructure.CODEC.forGetter(s -> s.jigsaw),
            Fit.CODEC.fieldOf("fit").forGetter(s -> s.fit)
    ).apply(i, FittedJigsawStructure::new));

    private final JigsawStructure jigsaw;
    private final Fit fit;
    /** "wayfarers:guild_outpost" style name for logs and the fit statistics (from the start pool). */
    private final String name;

    public FittedJigsawStructure(JigsawStructure jigsaw, Fit fit) {
        super(new StructureSettings(jigsaw.biomes(), jigsaw.spawnOverrides(), jigsaw.step(), jigsaw.terrainAdaptation()));
        this.jigsaw = jigsaw;
        this.fit = fit;
        this.name = jigsaw.getStartPool().unwrapKey()
                .map(k -> k.identifier().toString().replaceFirst("/start$", ""))
                .orElse(Wayfarers.MODID + ":?");
    }

    public Fit fit() {
        return this.fit;
    }

    public String name() {
        return this.name;
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        return this.jigsaw.findGenerationPoint(context);
    }

    /**
     * Chunk offsets tried when the grid cell's own spot does not fit: the start may slide up to two chunks (32 blocks)
     * to a flatter or drier spot nearby, instead of the whole cell being lost (on hills and by lakes most failing cells
     * miss by a few blocks). Two chunks keep the pieces well inside the reach of structure references.
     */
    private static final int[][] NUDGES = {{0, 0}, {2, 0}, {-2, 0}, {0, 2}, {0, -2}};
    /** Jigsaw assemblies plus full terrain checks per grid cell, at most (the expensive part of a site check). */
    private static final int FULL_CHECKS = 2;
    /** Decisions kept per structure (a cell is asked twice: by /locate or the structure check, then by the chunk). */
    private static final int DECISION_CACHE = 4096;

    /** Half the smallest side of the start templates' footprints (blocks), for the cheap pre-test; -1 until known. */
    private volatile int startHalf = -1;
    /** Grid cell (chunk) -> the nudge that fitted and its vertical move, or -1 when the cell was rejected. */
    private final Map<Long, Decision> decisions = new ConcurrentHashMap<>();

    private record Decision(long seed, int nudge, int dy) {}

    private record Candidate(int nudge, GenerationContext context, GenerationStub stub, double score) {}

    /**
     * The jigsaw start, its biome (checked first: it is far cheaper than the terrain), then the terrain fit, which may
     * move the pieces up or down. When the spot does not fit, nearby spots of the same cell are tried ({@link #NUDGES}).
     *
     * <p>Cost: each nudge first gets a cheap pre-test ({@link SiteFit#preScore}: five height samples on the start
     * template's footprint, no jigsaw assembly); a spot that looks right is assembled and fully checked at once (the
     * first good one ends the search), the others are ranked by their pre-test and only the best are assembled, at
     * most {@link #FULL_CHECKS} assemblies per cell. The decision is remembered, so the chunk that generates the
     * structure after /locate or the structure check found it does not search again, and the fit statistics count
     * each cell once.
     */
    @Override
    public Optional<GenerationStub> findValidGenerationPoint(GenerationContext context) {
        if (!SiteFit.active()) {
            return this.tryAt(context, false).map(Attempt::stub);
        }
        long key = context.chunkPos().pack();
        Decision known = this.decisions.get(key);
        if (known != null && known.seed() == context.seed()) {
            if (known.nudge() < 0) {
                return Optional.empty();
            }
            Optional<GenerationStub> replay = this.replay(nudged(context, known.nudge()), known.dy());
            if (replay.isPresent()) {
                return replay;
            }
        }
        int half = this.startHalf(context);
        SiteFit.Verdict first = null;
        int full = 0;
        List<Candidate> later = new ArrayList<>();
        for (int i = 0; i < NUDGES.length && full < FULL_CHECKS; i++) {
            GenerationContext at = nudged(context, i);
            Optional<GenerationStub> stub = this.startAt(at);
            if (stub.isEmpty()) {
                continue;
            }
            double score = SiteFit.preScore(this.fit, at, stub.get().position(), half);
            if (score > SiteFit.LIKELY) {
                later.add(new Candidate(i, at, stub.get(), score));
                continue;
            }
            full++;
            Optional<Attempt> attempt = this.check(at, stub.get());
            if (attempt.isPresent() && attempt.get().verdict().ok()) {
                return this.accept(key, context.seed(), i, attempt.get());
            }
            if (first == null && attempt.isPresent()) {
                first = attempt.get().verdict();
            }
        }
        later.sort(Comparator.comparingDouble(Candidate::score));
        for (Candidate c : later) {
            if (full >= FULL_CHECKS || c.score() >= SiteFit.HOPELESS) {
                break;
            }
            full++;
            Optional<Attempt> attempt = this.check(c.context(), c.stub());
            if (attempt.isPresent() && attempt.get().verdict().ok()) {
                return this.accept(key, context.seed(), c.nudge(), attempt.get());
            }
            if (first == null && attempt.isPresent()) {
                first = attempt.get().verdict();
            }
        }
        if (first == null && !later.isEmpty()) {
            first = SiteFit.Verdict.reject(SiteFit.preReason(this.fit, later.get(0).score()));
        }
        if (first != null) {
            SiteFit.record(this.name, first);
        }
        this.remember(key, new Decision(context.seed(), -1, 0));
        return Optional.empty();
    }

    private Optional<GenerationStub> accept(long key, long seed, int nudge, Attempt attempt) {
        SiteFit.record(this.name, attempt.verdict());
        this.remember(key, new Decision(seed, nudge, attempt.verdict().dy()));
        return Optional.of(attempt.stub());
    }

    private void remember(long key, Decision decision) {
        if (this.decisions.size() >= DECISION_CACHE) {
            this.decisions.clear();
        }
        this.decisions.put(key, decision);
    }

    private static GenerationContext nudged(GenerationContext context, int nudge) {
        int[] n = NUDGES[nudge];
        if (n[0] == 0 && n[1] == 0) {
            return context;
        }
        return new GenerationContext(context.registryAccess(), context.chunkGenerator(), context.biomeSource(),
                context.randomState(), context.structureTemplateManager(), context.seed(),
                new ChunkPos(context.chunkPos().x() + n[0], context.chunkPos().z() + n[1]), context.heightAccessor(),
                context.validBiome());
    }

    /** The pieces of a decision already taken: the same start (same random), assembled and moved by {@code dy}. */
    private Optional<GenerationStub> replay(GenerationContext at, int dy) {
        Optional<GenerationStub> found = this.findGenerationPoint(at);
        if (found.isEmpty()) {
            return Optional.empty();
        }
        StructurePiecesBuilder builder = found.get().getPiecesBuilder();
        if (builder.build().pieces().isEmpty()) {
            return Optional.empty();
        }
        if (dy != 0) {
            builder.offsetPiecesVertically(dy);
        }
        return Optional.of(new GenerationStub(found.get().position().above(dy), Either.right(builder)));
    }

    /** Half the smallest side of the start pool's templates (their built footprint when known), at least 4. */
    private int startHalf(GenerationContext context) {
        int half = this.startHalf;
        if (half >= 0) {
            return half;
        }
        int smallest = Integer.MAX_VALUE;
        try {
            for (Pair<StructurePoolElement, Integer> e : this.jigsaw.getStartPool().value().getTemplates()) {
                StructurePoolElement element = e.getFirst();
                Optional<List<Integer>> fp = element instanceof ChunkedPoolElement chunked ? chunked.footprint() : Optional.empty();
                if (fp.isPresent()) {
                    List<Integer> f = fp.get();
                    smallest = Math.min(smallest, Math.min(f.get(2) - f.get(0), f.get(3) - f.get(1)) + 1);
                } else {
                    Vec3i size = element.getSize(context.structureTemplateManager(), Rotation.NONE);
                    smallest = Math.min(smallest, Math.min(size.getX(), size.getZ()));
                }
            }
        } catch (RuntimeException e) {
            smallest = Integer.MAX_VALUE;
        }
        half = smallest == Integer.MAX_VALUE ? 8 : Math.max(4, smallest / 2);
        this.startHalf = half;
        return half;
    }

    private record Attempt(GenerationStub stub, SiteFit.Verdict verdict) {}

    /** The start at this context's chunk if its biome suits (no jigsaw assembly yet). */
    private Optional<GenerationStub> startAt(GenerationContext context) {
        Optional<GenerationStub> found = this.findGenerationPoint(context);
        if (found.isEmpty()) {
            return Optional.empty();
        }
        BlockPos pos = found.get().position();
        if (!context.validBiome().test(context.chunkGenerator().getBiomeSource().getNoiseBiome(QuartPos.fromBlock(pos.getX()),
                QuartPos.fromBlock(pos.getY()), QuartPos.fromBlock(pos.getZ()), context.randomState().sampler()))) {
            return Optional.empty();
        }
        return found;
    }

    /** The start at this context's chunk if its biome suits; with {@code check}, also its terrain verdict (moved when ok). */
    private Optional<Attempt> tryAt(GenerationContext context, boolean check) {
        Optional<GenerationStub> found = this.startAt(context);
        if (found.isEmpty()) {
            return Optional.empty();
        }
        return check ? this.check(context, found.get()) : Optional.of(new Attempt(found.get(), null));
    }

    /** Assembles the jigsaw and checks the start piece on the terrain (moved when it fits). */
    private Optional<Attempt> check(GenerationContext context, GenerationStub stub) {
        BlockPos pos = stub.position();
        StructurePiecesBuilder builder = stub.getPiecesBuilder();
        List<StructurePiece> pieces = builder.build().pieces();
        if (pieces.isEmpty()) {
            return Optional.empty();
        }
        SiteFit.Verdict verdict = SiteFit.evaluate(this.fit, pieces.get(0), context);
        if (!verdict.ok()) {
            return Optional.of(new Attempt(stub, verdict));
        }
        if (verdict.dy() != 0) {
            builder.offsetPiecesVertically(verdict.dy());
        }
        return Optional.of(new Attempt(new GenerationStub(pos.above(verdict.dy()), Either.right(builder)), verdict));
    }

    @Override
    public StructureType<?> type() {
        return ModWorldgen.FITTED_JIGSAW.get();
    }
}
