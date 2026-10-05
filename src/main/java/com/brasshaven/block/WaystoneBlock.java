package com.brasshaven.block;

import com.brasshaven.data.BrasshavenData;
import com.brasshaven.util.Waystones;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

/**
 * Waystones are shared by every player: the first person to touch one (or to place it)
 * makes it available to the whole server. Using it opens the travel screen (search, favourites,
 * renaming); travelling is only allowed while standing at a waystone.
 */
public class WaystoneBlock extends Block {
    private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 16, 15);

    public WaystoneBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        super.setPlacedBy(level, pos, state, placer, stack);
        if (level instanceof ServerLevel serverLevel) {
            Component custom = stack.get(DataComponents.CUSTOM_NAME);
            String name = custom != null ? custom.getString() : Waystones.defaultName(serverLevel, pos);
            BrasshavenData.get(serverLevel.getServer()).addWaystone(level, pos, name);
            if (placer instanceof ServerPlayer player) {
                player.sendSystemMessage(Component.translatable("message.brasshaven.waystone.discovered", name));
            }
        }
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel serverLevel && player instanceof ServerPlayer serverPlayer) {
            Waystones.discoverAndList(serverLevel, pos, serverPlayer);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (level instanceof ServerLevel serverLevel) {
            BrasshavenData.get(serverLevel.getServer()).removeWaystone(level, pos);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }
}
