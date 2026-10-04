package com.wayfarers.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.wayfarers.Wayfarers;
import com.wayfarers.registry.ModWorldgen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Vec3i;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.JigsawReplacementProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorList;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorType;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * One structure piece stored as one or several column templates ({@code wayfarers:chunked_template} in a template
 * pool, written by tools/wf/chunking.py). Small surface pieces use it too, with a single column, for its
 * {@code ground_level_delta}.
 *
 * <p>For the jigsaw machinery it is a single piece with the size of the whole build: same bounding box, same
 * start height, same terrain adaptation (the beard is computed per piece box) as the single template it replaces.
 * The difference is in {@link #place}: vanilla walks a template's entire block list for every chunk the piece
 * touches, while this element only places the columns whose box intersects the chunk being generated. Each column
 * is placed exactly like a {@code single_pool_element} would place the whole template (same settings, processors
 * and flags), so blocks, block entities, loot tables and entities come out the same.
 *
 * <p>The column templates go through the server's template manager, which normally keeps every template it ever
 * loaded until shutdown; {@link Loaded} drops the least recently used columns once about {@link Loaded#BUDGET}
 * block entries are held, so finished structures do not stay in memory.
 */
public class ChunkedPoolElement extends StructurePoolElement {
    public record Cell(Identifier location, Vec3i offset, Vec3i size, int blocks) {
        public static final Codec<Cell> CODEC = RecordCodecBuilder.create(i -> i.group(
                Identifier.CODEC.fieldOf("location").forGetter(Cell::location),
                Vec3i.CODEC.fieldOf("offset").forGetter(Cell::offset),
                Vec3i.CODEC.fieldOf("size").forGetter(Cell::size),
                Codec.INT.optionalFieldOf("blocks", 0).forGetter(Cell::blocks)
        ).apply(i, Cell::new));
    }

    public static final MapCodec<ChunkedPoolElement> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Vec3i.CODEC.fieldOf("size").forGetter(e -> e.size),
            Cell.CODEC.listOf().fieldOf("cells").forGetter(e -> e.cells),
            StructureProcessorType.LIST_CODEC.fieldOf("processors").forGetter(e -> e.processors),
            projectionCodec(),
            LiquidSettings.CODEC.optionalFieldOf("override_liquid_settings").forGetter(e -> e.overrideLiquidSettings),
            Codec.intRange(0, 4096).optionalFieldOf("ground_level_delta", 1).forGetter(e -> e.groundLevelDelta),
            Codec.INT.listOf(4, 4).optionalFieldOf("footprint").forGetter(e -> e.footprint)
    ).apply(i, ChunkedPoolElement::new));

    private static final Set<Identifier> REPORTED_MISSING = ConcurrentHashMap.newKeySet();

    private final Vec3i size;
    private final List<Cell> cells;
    private final Holder<StructureProcessorList> processors;
    private final Optional<LiquidSettings> overrideLiquidSettings;
    /**
     * Height of the template's ground layer above its lowest layer, plus one (vanilla elements always say 1: their
     * lowest layer is the ground). Our surface templates carry cellars, skirts and foundations below the ground
     * layer; the jigsaw start puts {@code minY + groundLevelDelta} on the heightmap and the beardifier flattens the
     * terrain around that same height, so with the default 1 the beard would dig a moat at the foundation's
     * bottom instead of meeting the real ground (written by tools/gen_structures.py).
     */
    private final int groundLevelDelta;
    /**
     * Built columns of the template (x0, z0, x1, z1, template coordinates): what the site check of
     * {@link FittedJigsawStructure} samples, instead of the whole box with its skirts and empty corners.
     */
    private final Optional<List<Integer>> footprint;

    protected ChunkedPoolElement(Vec3i size, List<Cell> cells, Holder<StructureProcessorList> processors,
                                 StructureTemplatePool.Projection projection,
                                 Optional<LiquidSettings> overrideLiquidSettings, int groundLevelDelta,
                                 Optional<List<Integer>> footprint) {
        super(projection);
        this.size = size;
        this.cells = List.copyOf(cells);
        this.processors = processors;
        this.overrideLiquidSettings = overrideLiquidSettings;
        this.groundLevelDelta = groundLevelDelta;
        this.footprint = footprint.map(List::copyOf);
    }

    /** The built columns {x0, z0, x1, z1} in template coordinates, when the generator wrote them. */
    public Optional<List<Integer>> footprint() {
        return this.footprint;
    }

    @Override
    public int getGroundLevelDelta() {
        return this.groundLevelDelta;
    }

    @Override
    public Vec3i getSize(StructureTemplateManager structureTemplateManager, Rotation rotation) {
        return switch (rotation) {
            case COUNTERCLOCKWISE_90, CLOCKWISE_90 -> new Vec3i(this.size.getZ(), this.size.getY(), this.size.getX());
            default -> this.size;
        };
    }

    @Override
    public List<StructureTemplate.JigsawBlockInfo> getShuffledJigsawBlocks(StructureTemplateManager structureTemplateManager,
                                                                          BlockPos position, Rotation rotation, RandomSource random) {
        return new ArrayList<>();
    }

    @Override
    public BoundingBox getBoundingBox(StructureTemplateManager structureTemplateManager, BlockPos position, Rotation rotation) {
        return box(position, this.size, rotation);
    }

    @Override
    public boolean place(StructureTemplateManager structureTemplateManager, WorldGenLevel level, StructureManager structureManager,
                         ChunkGenerator generator, BlockPos position, BlockPos referencePos, Rotation rotation, BoundingBox chunkBB,
                         RandomSource random, LiquidSettings liquidSettings, boolean keepJigsaws) {
        StructurePlaceSettings settings = null;
        for (Cell cell : this.cells) {
            BlockPos origin = position.offset(StructureTemplate.transform(new BlockPos(cell.offset()), Mirror.NONE, rotation, BlockPos.ZERO));
            if (!box(origin, cell.size(), rotation).intersects(chunkBB)) {
                continue;
            }
            Optional<StructureTemplate> template = structureTemplateManager.get(cell.location());
            if (template.isEmpty()) {
                if (REPORTED_MISSING.add(cell.location())) {
                    Wayfarers.LOGGER.error("Missing structure column template {}", cell.location());
                }
                continue;
            }
            Loaded.touch(structureTemplateManager, cell.location(), cell.blocks());
            if (settings == null) {
                settings = this.getSettings(rotation, chunkBB, liquidSettings, keepJigsaws);
            }
            // 18 = UPDATE_CLIENTS | UPDATE_KNOWN_SHAPE, like SinglePoolElement
            template.get().placeInWorld(level, origin, referencePos, settings, random, 18);
        }
        return true;
    }

    /** The settings SinglePoolElement uses for a whole template, shared by every column of the chunk. */
    private StructurePlaceSettings getSettings(Rotation rotation, BoundingBox chunkBB, LiquidSettings liquidSettings, boolean keepJigsaws) {
        StructurePlaceSettings settings = new StructurePlaceSettings();
        settings.setBoundingBox(chunkBB);
        settings.setRotation(rotation);
        settings.setKnownShape(true);
        settings.setIgnoreEntities(false);
        settings.addProcessor(BlockIgnoreProcessor.STRUCTURE_BLOCK);
        settings.setFinalizeEntities(true);
        settings.setLiquidSettings(this.overrideLiquidSettings.orElse(liquidSettings));
        if (!keepJigsaws) {
            settings.addProcessor(JigsawReplacementProcessor.INSTANCE);
        }
        this.processors.value().list().forEach(settings::addProcessor);
        this.getProjection().getProcessors().forEach(settings::addProcessor);
        return settings;
    }

    /** Same box as StructureTemplate#getBoundingBox for a template of {@code size} placed at {@code origin}. */
    private static BoundingBox box(BlockPos origin, Vec3i size, Rotation rotation) {
        BlockPos far = StructureTemplate.transform(new BlockPos(size.getX() - 1, size.getY() - 1, size.getZ() - 1),
                Mirror.NONE, rotation, BlockPos.ZERO);
        return BoundingBox.fromCorners(origin, origin.offset(far));
    }

    @Override
    public StructurePoolElementType<?> getType() {
        return ModWorldgen.CHUNKED_TEMPLATE.get();
    }

    @Override
    public String toString() {
        return "Chunked[" + (this.cells.isEmpty() ? "" : this.cells.get(0).location()) + " +" + Math.max(0, this.cells.size() - 1) + "]";
    }

    /** Least recently used column templates kept in the template manager's cache, up to about BUDGET block entries. */
    static final class Loaded {
        /** About 50-60 MB of StructureBlockInfo: room for several big structures generating at once. */
        static final long BUDGET = 1_000_000L;
        private static final LinkedHashMap<Identifier, Integer> ORDER = new LinkedHashMap<>(64, 0.75F, true);
        private static WeakReference<StructureTemplateManager> owner = new WeakReference<>(null);
        private static long total;

        private Loaded() {}

        static synchronized void touch(StructureTemplateManager manager, Identifier id, int blocks) {
            if (owner.get() != manager) {
                // a new server (or world) has its own manager: forget the previous one's bookkeeping
                ORDER.clear();
                total = 0;
                owner = new WeakReference<>(manager);
            }
            int weight = Math.max(1, blocks);
            Integer previous = ORDER.put(id, weight);
            total += weight - (previous == null ? 0 : previous);
            Iterator<Map.Entry<Identifier, Integer>> eldest = ORDER.entrySet().iterator();
            while (total > BUDGET && eldest.hasNext()) {
                Map.Entry<Identifier, Integer> entry = eldest.next();
                if (entry.getKey().equals(id)) {
                    break; // only the column being placed is left
                }
                total -= entry.getValue();
                eldest.remove();
                // the next chunk that needs it loads it again; a thread still placing it keeps its own reference
                manager.remove(entry.getKey());
            }
        }
    }
}
