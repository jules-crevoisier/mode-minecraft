package com.wayfarers.block;

import com.wayfarers.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Marks a Storage Relay so a Guild Terminal's scan finds it among the chunk's block entities (no block-by-block
 * search). It holds no data.
 */
public class StorageRelayBlockEntity extends BlockEntity {
    public StorageRelayBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.STORAGE_RELAY.get(), pos, state);
    }
}
