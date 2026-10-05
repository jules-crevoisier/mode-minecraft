package com.brasshaven.registry;

import com.mojang.serialization.MapCodec;
import com.brasshaven.Brasshaven;
import com.brasshaven.world.ChunkedPoolElement;
import com.brasshaven.world.ClearOfStructuresFilter;
import com.brasshaven.world.CuratedSpreadPlacement;
import com.brasshaven.world.FittedJigsawStructure;
import com.brasshaven.world.GroundedPoolElement;
import com.brasshaven.world.ToggledFeaturesModifier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.placement.PlacementModifierType;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacementType;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.minecraftforge.common.world.BiomeModifier;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * Worldgen codecs the data pack refers to: the column-split and grounded template pool elements, the structure placement and the
 * terrain-fitted jigsaw structure type; the placement filter that keeps big decorations out of structures and the
 * config-switched biome modifier of the terrain touches (tools/wf/worldbiomes.py).
 */
public final class ModWorldgen {
    public static final DeferredRegister<StructurePoolElementType<?>> POOL_ELEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_POOL_ELEMENT, Brasshaven.MODID);
    public static final DeferredRegister<StructurePlacementType<?>> PLACEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_PLACEMENT, Brasshaven.MODID);

    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES =
            DeferredRegister.create(Registries.STRUCTURE_TYPE, Brasshaven.MODID);

    /** {@code "element_type": "brasshaven:chunked_template"} (written by tools/wf/chunking.py). */
    public static final RegistryObject<StructurePoolElementType<ChunkedPoolElement>> CHUNKED_TEMPLATE =
            POOL_ELEMENTS.register("chunked_template", () -> () -> ChunkedPoolElement.CODEC);

    /** {@code "element_type": "brasshaven:grounded_single"}: a single template with its ground depth (tools/wf/village.py). */
    public static final RegistryObject<StructurePoolElementType<GroundedPoolElement>> GROUNDED_SINGLE =
            POOL_ELEMENTS.register("grounded_single", () -> () -> GroundedPoolElement.CODEC);

    /** {@code "type": "brasshaven:curated_spread"} in our structure sets (written by tools/wf/placement.py). */
    public static final RegistryObject<StructurePlacementType<CuratedSpreadPlacement>> CURATED_SPREAD =
            PLACEMENTS.register("curated_spread", () -> () -> CuratedSpreadPlacement.CODEC);

    /** {@code "type": "brasshaven:fitted_jigsaw"}: every structure of the mod (tools/wf/defs.py structure_json). */
    public static final RegistryObject<StructureType<FittedJigsawStructure>> FITTED_JIGSAW =
            STRUCTURE_TYPES.register("fitted_jigsaw", () -> () -> FittedJigsawStructure.CODEC);

    public static final DeferredRegister<PlacementModifierType<?>> PLACEMENT_MODIFIERS =
            DeferredRegister.create(Registries.PLACEMENT_MODIFIER_TYPE, Brasshaven.MODID);

    /** {@code "type": "brasshaven:clear_of_structures"} on the big surface decorations (tools/wf/worldbiomes.py). */
    public static final RegistryObject<PlacementModifierType<ClearOfStructuresFilter>> CLEAR_OF_STRUCTURES =
            PLACEMENT_MODIFIERS.register("clear_of_structures", () -> () -> ClearOfStructuresFilter.CODEC);

    public static final DeferredRegister<MapCodec<? extends BiomeModifier>> BIOME_MODIFIERS =
            DeferredRegister.create(ForgeRegistries.Keys.BIOME_MODIFIER_SERIALIZERS, Brasshaven.MODID);

    /** {@code "type": "brasshaven:toggled_features"}: the terrain touches, each behind a world.terrain.* option. */
    public static final RegistryObject<MapCodec<ToggledFeaturesModifier>> TOGGLED_FEATURES =
            BIOME_MODIFIERS.register("toggled_features", () -> ToggledFeaturesModifier.CODEC);

    private ModWorldgen() {}
}
