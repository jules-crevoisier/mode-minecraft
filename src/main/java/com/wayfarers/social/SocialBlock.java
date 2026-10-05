package com.wayfarers.social;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.EnumMap;
import java.util.Map;

/**
 * The two blocks of the multiplayer features, turned towards the player who placed them: the Pneumatic Post (opens
 * the player's inbox and the writing desk) and the Contract Board (the server's open contracts). Neither stores
 * anything: mail and contracts live in the server's social data, so breaking a block loses nothing and every block
 * of a kind opens the same thing.
 */
public class SocialBlock extends HorizontalDirectionalBlock {
    public enum Kind { POST, BOARD }

    private final Kind kind;
    private final Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);

    private SocialBlock(Properties properties, Kind kind) {
        super(properties);
        this.kind = kind;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
        for (Direction d : Direction.Plane.HORIZONTAL) {
            shapes.put(d, kind == Kind.POST
                    ? Shapes.or(box(2, 0, 2, 14, 2, 14), box(4, 2, 4, 12, 16, 12))
                    : rotate(d, 0, 0, 5, 16, 16, 10));
        }
    }

    public static SocialBlock post(Properties p) {
        return new SocialBlock(p, Kind.POST);
    }

    public static SocialBlock board(Properties p) {
        return new SocialBlock(p, Kind.BOARD);
    }

    /** A box drawn for a block facing north, turned to face {@code d}. */
    private static VoxelShape rotate(Direction d, double x0, double y0, double z0, double x1, double y1, double z1) {
        return switch (d) {
            case SOUTH -> box(16 - x1, y0, 16 - z1, 16 - x0, y1, 16 - z0);
            case EAST -> box(16 - z1, y0, x0, 16 - z0, y1, x1);
            case WEST -> box(z0, y0, 16 - x1, z1, y1, 16 - x0);
            default -> box(x0, y0, z0, x1, y1, z1);
        };
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return kind == Kind.POST ? simpleCodec(SocialBlock::post) : simpleCodec(SocialBlock::board);
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
        return shapes.get(state.getValue(FACING));
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (player instanceof ServerPlayer sp) {
            if (kind == Kind.POST) {
                Post.open(sp, pos);
            } else {
                Contracts.open(sp, pos);
            }
        }
        return InteractionResult.SUCCESS;
    }
}
