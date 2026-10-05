package com.wayfarers.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Unbreakable headstone created on death; using it returns everything to the user's inventory. */
public class GraveBlock extends BaseEntityBlock {
    public static final MapCodec<GraveBlock> CODEC = simpleCodec(GraveBlock::new);
    public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
    private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 14, 15);

    public GraveBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new GraveBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel serverLevel && level.getBlockEntity(pos) instanceof GraveBlockEntity grave) {
            // the owner (and operators) first: on a public server nobody else empties a fresh grave
            long locked = grave.lockedMinutes();
            boolean op = player instanceof net.minecraft.server.level.ServerPlayer sp
                    && sp.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER);
            if (locked != 0 && !player.getUUID().equals(grave.owner()) && !op) {
                player.sendSystemMessage((locked < 0
                        ? Component.translatable("message.wayfarers.grave.locked", grave.ownerName())
                        : Component.translatable("message.wayfarers.grave.locked_for", grave.ownerName(), locked))
                        .withStyle(ChatFormatting.RED));
                return InteractionResult.SUCCESS;
            }
            for (ItemStack stack : grave.takeAll()) {
                if (!stack.isEmpty() && !player.getInventory().add(stack)) {
                    player.drop(stack, false);
                }
            }
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
            serverLevel.sendParticles(ParticleTypes.SOUL, pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5,
                    20, 0.3, 0.4, 0.3, 0.02);
            level.playSound(null, pos, SoundEvents.SOUL_ESCAPE.value(), SoundSource.BLOCKS, 1.0F, 1.0F);
            player.sendSystemMessage(Component.translatable("message.wayfarers.grave.restored").withStyle(ChatFormatting.GREEN));
        }
        return InteractionResult.SUCCESS;
    }
}
