package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.world.ChunkedPoolElement;
import com.wayfarers.world.CuratedSpreadPlacement;
import com.wayfarers.world.FittedJigsawStructure;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacementType;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

/**
 * Worldgen codecs the data pack refers to: the column-split template pool element, the structure placement and the
 * terrain-fitted jigsaw structure type.
 */
public final class ModWorldgen {
    public static final DeferredRegister<StructurePoolElementType<?>> POOL_ELEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_POOL_ELEMENT, Wayfarers.MODID);
    public static final DeferredRegister<StructurePlacementType<?>> PLACEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_PLACEMENT, Wayfarers.MODID);

    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES =
            DeferredRegister.create(Registries.STRUCTURE_TYPE, Wayfarers.MODID);

    /** {@code "element_type": "wayfarers:chunked_template"} (written by tools/wf/chunking.py). */
    public static final RegistryObject<StructurePoolElementType<ChunkedPoolElement>> CHUNKED_TEMPLATE =
            POOL_ELEMENTS.register("chunked_template", () -> () -> ChunkedPoolElement.CODEC);

    /** {@code "type": "wayfarers:curated_spread"} in our structure sets (written by tools/wf/placement.py). */
    public static final RegistryObject<StructurePlacementType<CuratedSpreadPlacement>> CURATED_SPREAD =
            PLACEMENTS.register("curated_spread", () -> () -> CuratedSpreadPlacement.CODEC);

    /** {@code "type": "wayfarers:fitted_jigsaw"}: every structure of the mod (tools/wf/defs.py structure_json). */
    public static final RegistryObject<StructureType<FittedJigsawStructure>> FITTED_JIGSAW =
            STRUCTURE_TYPES.register("fitted_jigsaw", () -> () -> FittedJigsawStructure.CODEC);

    private ModWorldgen() {}
}
