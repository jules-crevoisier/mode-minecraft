package com.wayfarers.world;

import com.mojang.serialization.MapCodec;
import com.wayfarers.Wayfarers;
import com.wayfarers.registry.ModWorldgen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.levelgen.placement.PlacementContext;
import net.minecraft.world.level.levelgen.placement.PlacementFilter;
import net.minecraft.world.level.levelgen.placement.PlacementModifierType;
import net.minecraft.world.level.levelgen.structure.Structure;

import java.util.Map;

/**
 * {@code {"type": "wayfarers:clear_of_structures"}}: keeps a surface feature of the overhaul (thorns, giant mushrooms,
 * hoodoos, boulders, trees...) out of the chunks a surface structure reaches. Features generate after the structure
 * pieces, so without it a thorn could grow through the witch hut it stands next to.
 *
 * <p>A chunk knows every structure whose bounding box covers it (its structure references, filled in the
 * structure_references step, long before features), so the check reads only the chunk being decorated. Only the
 * structures in the tag {@code wayfarers:clears_decoration} count (surface ones: mineshafts or strongholds under a
 * forest must not strip its trees).
 */
public final class ClearOfStructuresFilter extends PlacementFilter {
    private static final ClearOfStructuresFilter INSTANCE = new ClearOfStructuresFilter();
    public static final MapCodec<ClearOfStructuresFilter> CODEC = MapCodec.unit(() -> INSTANCE);
    public static final TagKey<Structure> CLEARS = TagKey.create(Registries.STRUCTURE, Wayfarers.id("clears_decoration"));

    private ClearOfStructuresFilter() {}

    @Override
    protected boolean shouldPlace(PlacementContext context, RandomSource random, BlockPos origin) {
        Map<Structure, ?> refs = context.getLevel().getChunk(origin).getAllReferences();
        if (refs.isEmpty()) {
            return true;
        }
        Registry<Structure> registry = context.getLevel().registryAccess().lookupOrThrow(Registries.STRUCTURE);
        for (Structure structure : refs.keySet()) {
            if (registry.wrapAsHolder(structure).is(CLEARS)) {
                return false;
            }
        }
        return true;
    }

    @Override
    public PlacementModifierType<?> type() {
        return ModWorldgen.CLEAR_OF_STRUCTURES.get();
    }
}
