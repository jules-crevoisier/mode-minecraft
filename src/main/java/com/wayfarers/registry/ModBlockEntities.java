package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.block.GraveBlockEntity;
import com.wayfarers.block.SortingChestBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.Set;

public final class ModBlockEntities {
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, Wayfarers.MODID);

    public static final RegistryObject<BlockEntityType<SortingChestBlockEntity>> SORTING_CHEST =
            BLOCK_ENTITIES.register("sorting_chest",
                    () -> new BlockEntityType<>(SortingChestBlockEntity::new, Set.of(ModBlocks.SORTING_CHEST.get())));
    public static final RegistryObject<BlockEntityType<GraveBlockEntity>> GRAVE =
            BLOCK_ENTITIES.register("grave",
                    () -> new BlockEntityType<>(GraveBlockEntity::new, Set.of(ModBlocks.GRAVE.get())));

    private ModBlockEntities() {}
}
