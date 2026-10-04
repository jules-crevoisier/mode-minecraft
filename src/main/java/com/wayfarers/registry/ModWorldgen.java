package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.world.ChunkedPoolElement;
import com.wayfarers.world.CuratedSpreadPlacement;
import com.wayfarers.world.GroundedPoolElement;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacementType;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

/** Worldgen codecs the data pack refers to: the column-split and grounded template pool elements and the structure placement. */
public final class ModWorldgen {
    public static final DeferredRegister<StructurePoolElementType<?>> POOL_ELEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_POOL_ELEMENT, Wayfarers.MODID);
    public static final DeferredRegister<StructurePlacementType<?>> PLACEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_PLACEMENT, Wayfarers.MODID);

    /** {@code "element_type": "wayfarers:chunked_template"} (written by tools/wf/chunking.py). */
    public static final RegistryObject<StructurePoolElementType<ChunkedPoolElement>> CHUNKED_TEMPLATE =
            POOL_ELEMENTS.register("chunked_template", () -> () -> ChunkedPoolElement.CODEC);

    /** {@code "element_type": "wayfarers:grounded_single"}: a single template with its ground depth (tools/wf/village.py). */
    public static final RegistryObject<StructurePoolElementType<GroundedPoolElement>> GROUNDED_SINGLE =
            POOL_ELEMENTS.register("grounded_single", () -> () -> GroundedPoolElement.CODEC);

    /** {@code "type": "wayfarers:curated_spread"} in our structure sets (written by tools/wf/placement.py). */
    public static final RegistryObject<StructurePlacementType<CuratedSpreadPlacement>> CURATED_SPREAD =
            PLACEMENTS.register("curated_spread", () -> () -> CuratedSpreadPlacement.CODEC);

    private ModWorldgen() {}
}
