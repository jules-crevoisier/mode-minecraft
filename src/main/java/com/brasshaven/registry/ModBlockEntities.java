package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import com.brasshaven.block.BossSealBlockEntity;
import com.brasshaven.block.CrateBlockEntity;
import com.brasshaven.block.GraveBlockEntity;
import com.brasshaven.block.MachineBlockEntity;
import com.brasshaven.block.SortingChestBlockEntity;
import com.brasshaven.generated.GeneratedMachines;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.Set;

public final class ModBlockEntities {
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, Brasshaven.MODID);

    public static final RegistryObject<BlockEntityType<SortingChestBlockEntity>> SORTING_CHEST =
            BLOCK_ENTITIES.register("sorting_chest",
                    () -> new BlockEntityType<>(SortingChestBlockEntity::new, Set.of(ModBlocks.SORTING_CHEST.get())));
    public static final RegistryObject<BlockEntityType<GraveBlockEntity>> GRAVE =
            BLOCK_ENTITIES.register("grave",
                    () -> new BlockEntityType<>(GraveBlockEntity::new, Set.of(ModBlocks.GRAVE.get())));
    public static final RegistryObject<BlockEntityType<BossSealBlockEntity>> BOSS_SEAL =
            BLOCK_ENTITIES.register("boss_seal",
                    () -> new BlockEntityType<>(BossSealBlockEntity::new, Set.of(ModBlocks.BOSS_SEAL.get())));
    public static final RegistryObject<BlockEntityType<CrateBlockEntity>> CRATE =
            BLOCK_ENTITIES.register("compacting_crate",
                    () -> new BlockEntityType<>(CrateBlockEntity::new, Set.of(ModBlocks.COMPACTING_CRATE.get())));
    public static final RegistryObject<BlockEntityType<MachineBlockEntity>> MACHINE =
            BLOCK_ENTITIES.register("machine",
                    () -> new BlockEntityType<>(MachineBlockEntity::new, Set.of(GeneratedMachines.blocks())));
    public static final RegistryObject<BlockEntityType<com.brasshaven.block.GuildTerminalBlockEntity>> GUILD_TERMINAL =
            BLOCK_ENTITIES.register("guild_terminal", () -> new BlockEntityType<>(com.brasshaven.block.GuildTerminalBlockEntity::new,
                    Set.of(ModBlocks.GUILD_TERMINAL.get())));
    public static final RegistryObject<BlockEntityType<com.brasshaven.block.StorageRelayBlockEntity>> STORAGE_RELAY =
            BLOCK_ENTITIES.register("storage_relay", () -> new BlockEntityType<>(com.brasshaven.block.StorageRelayBlockEntity::new,
                    Set.of(ModBlocks.STORAGE_RELAY.get())));

    private ModBlockEntities() {}
}
