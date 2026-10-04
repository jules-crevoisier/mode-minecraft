package com.wayfarers.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.wayfarers.registry.ModWorldgen;
import net.minecraft.core.Holder;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.RegistryFileCodec;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadType;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacementType;

import java.util.List;
import java.util.Optional;

/**
 * {@code "type": "wayfarers:curated_spread"}: vanilla {@code random_spread} (same grid, same salt maths, so
 * {@code /locate} and explorer maps work unchanged) with two extras the vanilla placement lacks:
 * <ul>
 *   <li>{@code avoid}: a list of {@code {set, chunks}}; a start is dropped when one of those structure sets has a
 *   start within {@code chunks} chunks (vanilla's {@code exclusion_zone} takes a single set);</li>
 *   <li>{@code min_spawn_distance}: no start within that many chunks of 0,0 (the wonders keep away from spawn).</li>
 * </ul>
 * Written by tools/wf/placement.py; tools/validate.py checks that the {@code avoid} graph has no cycle (a cycle would
 * recurse forever, exactly like two vanilla exclusion zones pointing at each other).
 */
public class CuratedSpreadPlacement extends RandomSpreadStructurePlacement {
    public record Avoid(Holder<StructureSet> set, int chunks) {
        public static final Codec<Avoid> CODEC = RecordCodecBuilder.create(i -> i.group(
                RegistryFileCodec.create(Registries.STRUCTURE_SET, StructureSet.DIRECT_CODEC, false).fieldOf("set").forGetter(Avoid::set),
                Codec.intRange(1, 32).fieldOf("chunks").forGetter(Avoid::chunks)
        ).apply(i, Avoid::new));
    }

    public static final MapCodec<CuratedSpreadPlacement> CODEC = RecordCodecBuilder.<CuratedSpreadPlacement>mapCodec(i -> placementCodec(i).and(i.group(
            Codec.intRange(0, 4096).fieldOf("spacing").forGetter(CuratedSpreadPlacement::spacing),
            Codec.intRange(0, 4096).fieldOf("separation").forGetter(CuratedSpreadPlacement::separation),
            RandomSpreadType.CODEC.optionalFieldOf("spread_type", RandomSpreadType.LINEAR).forGetter(CuratedSpreadPlacement::spreadType),
            Avoid.CODEC.listOf().optionalFieldOf("avoid", List.of()).forGetter(p -> p.avoid),
            Codec.intRange(0, 4096).optionalFieldOf("min_spawn_distance", 0).forGetter(p -> p.minSpawnDistance)
    )).apply(i, CuratedSpreadPlacement::new)).validate(CuratedSpreadPlacement::validate);

    private final List<Avoid> avoid;
    private final int minSpawnDistance;

    public CuratedSpreadPlacement(Vec3i locateOffset, StructurePlacement.FrequencyReductionMethod frequencyReductionMethod,
                                  float frequency, int salt, Optional<StructurePlacement.ExclusionZone> exclusionZone,
                                  int spacing, int separation, RandomSpreadType spreadType, List<Avoid> avoid, int minSpawnDistance) {
        super(locateOffset, frequencyReductionMethod, frequency, salt, exclusionZone, spacing, separation, spreadType);
        this.avoid = List.copyOf(avoid);
        this.minSpawnDistance = minSpawnDistance;
    }

    private static DataResult<CuratedSpreadPlacement> validate(CuratedSpreadPlacement p) {
        return p.spacing() <= p.separation() ? DataResult.error(() -> "Spacing has to be larger than separation") : DataResult.success(p);
    }

    @Override
    protected boolean isPlacementChunk(ChunkGeneratorStructureState state, int sourceX, int sourceZ) {
        if (!super.isPlacementChunk(state, sourceX, sourceZ)) {
            return false;
        }
        long r = this.minSpawnDistance;
        return r == 0 || (long) sourceX * sourceX + (long) sourceZ * sourceZ >= r * r;
    }

    @Override
    public boolean applyInteractionsWithOtherStructures(ChunkGeneratorStructureState state, int sourceX, int sourceZ) {
        if (!super.applyInteractionsWithOtherStructures(state, sourceX, sourceZ)) {
            return false;
        }
        for (Avoid a : this.avoid) {
            if (state.hasStructureChunkInRange(a.set(), sourceX, sourceZ, a.chunks())) {
                return false;
            }
        }
        return true;
    }

    @Override
    public StructurePlacementType<?> type() {
        return ModWorldgen.CURATED_SPREAD.get();
    }
}
