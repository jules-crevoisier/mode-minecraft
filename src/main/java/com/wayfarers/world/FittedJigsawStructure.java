package com.wayfarers.world;

import com.mojang.datafixers.util.Either;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.wayfarers.Wayfarers;
import com.wayfarers.registry.ModWorldgen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.QuartPos;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;

import java.util.List;
import java.util.Optional;
import java.util.Set;

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
     * The jigsaw start, its biome (checked first: it is far cheaper than the terrain), then the terrain fit, which may
     * move the pieces up or down. The pieces are assembled here once and handed over ready-made.
     */
    @Override
    public Optional<GenerationStub> findValidGenerationPoint(GenerationContext context) {
        Optional<GenerationStub> found = this.findGenerationPoint(context);
        if (found.isEmpty()) {
            return found;
        }
        GenerationStub stub = found.get();
        BlockPos pos = stub.position();
        if (!context.validBiome().test(context.chunkGenerator().getBiomeSource().getNoiseBiome(QuartPos.fromBlock(pos.getX()),
                QuartPos.fromBlock(pos.getY()), QuartPos.fromBlock(pos.getZ()), context.randomState().sampler()))) {
            return Optional.empty();
        }
        if (!SiteFit.active()) {
            return found;
        }
        StructurePiecesBuilder builder = stub.getPiecesBuilder();
        List<StructurePiece> pieces = builder.build().pieces();
        if (pieces.isEmpty()) {
            return Optional.empty();
        }
        SiteFit.Verdict verdict = SiteFit.evaluate(this.fit, pieces.get(0), context);
        SiteFit.record(this.name, verdict);
        if (!verdict.ok()) {
            return Optional.empty();
        }
        if (verdict.dy() != 0) {
            builder.offsetPiecesVertically(verdict.dy());
        }
        return Optional.of(new GenerationStub(pos.above(verdict.dy()), Either.right(builder)));
    }

    @Override
    public StructureType<?> type() {
        return ModWorldgen.FITTED_JIGSAW.get();
    }
}
