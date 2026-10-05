package com.brasshaven.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.EnumMap;
import java.util.Map;

/**
 * Decorative furniture with a real 3D shape (models and boxes come from tools/wf/furniture.py).
 * Boxes are given for a block facing north and rotated for the other directions.
 */
public class FurnitureBlock extends Block {
    public enum Mount { NONE, PLAYER, AWAY, WALL, AXIS }

    protected final Mount mount;
    protected final Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);

    protected FurnitureBlock(Properties properties, Mount mount, double[][] boxes) {
        super(properties);
        this.mount = mount;
        for (Direction d : Direction.values()) {
            shapes.put(d, shape(boxes, d));
        }
    }

    public static Block create(Properties properties, Mount mount, double[][] boxes) {
        return switch (mount) {
            case NONE -> new FurnitureBlock(properties, mount, boxes);
            case AXIS -> new Pillar(properties, mount, boxes);
            default -> new Facing(properties, mount, boxes);
        };
    }

    /** The boxes turned so their north side faces {@code d} (UP/DOWN: laid along that axis, for pipes). */
    private static VoxelShape shape(double[][] boxes, Direction d) {
        VoxelShape out = Shapes.empty();
        for (double[] b : boxes) {
            double[] p = rotate(b[0], b[1], b[2], d);
            double[] q = rotate(b[3], b[4], b[5], d);
            out = Shapes.or(out, Block.box(Math.min(p[0], q[0]), Math.min(p[1], q[1]), Math.min(p[2], q[2]),
                    Math.max(p[0], q[0]), Math.max(p[1], q[1]), Math.max(p[2], q[2])));
        }
        return out.optimize();
    }

    private static double[] rotate(double x, double y, double z, Direction d) {
        return switch (d) {
            case EAST -> new double[] {16 - z, y, x};
            case SOUTH -> new double[] {16 - x, y, 16 - z};
            case WEST -> new double[] {z, y, 16 - x};
            case UP, NORTH -> new double[] {x, y, z};
            // DOWN is used for pillars lying along Z (y and z swapped); EAST-WEST pillars use the X case below
            case DOWN -> new double[] {x, z, y};
        };
    }

    protected VoxelShape shapeFor(BlockState state) {
        return shapes.get(Direction.NORTH);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapeFor(state);
    }

    /** Furniture that turns: towards the player, away from them, or flat against the clicked wall. */
    public static class Facing extends FurnitureBlock {
        public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;

        protected Facing(Properties properties, Mount mount, double[][] boxes) {
            super(properties, mount, boxes);
            registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            builder.add(FACING);
        }

        @Override
        public BlockState getStateForPlacement(BlockPlaceContext context) {
            Direction facing = switch (mount) {
                case WALL -> context.getClickedFace().getAxis().isHorizontal() ? context.getClickedFace()
                        : context.getHorizontalDirection().getOpposite();
                case AWAY -> context.getHorizontalDirection();
                default -> context.getHorizontalDirection().getOpposite();
            };
            return defaultBlockState().setValue(FACING, facing);
        }

        @Override
        protected VoxelShape shapeFor(BlockState state) {
            return shapes.get(state.getValue(FACING));
        }

        @Override
        protected BlockState rotate(BlockState state, Rotation rotation) {
            return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
        }

        @Override
        protected BlockState mirror(BlockState state, Mirror mirror) {
            return state.rotate(mirror.getRotation(state.getValue(FACING)));
        }
    }

    /** A pillar along X, Y or Z, placed like a log (pipes). */
    public static class Pillar extends FurnitureBlock {
        public static final EnumProperty<Direction.Axis> AXIS = BlockStateProperties.AXIS;
        private final VoxelShape xShape;

        protected Pillar(Properties properties, Mount mount, double[][] boxes) {
            super(properties, mount, boxes);
            double[][] alongX = new double[boxes.length][];
            for (int i = 0; i < boxes.length; i++) {
                double[] b = boxes[i];
                alongX[i] = new double[] {b[1], b[0], b[2], b[4], b[3], b[5]};
            }
            VoxelShape out = Shapes.empty();
            for (double[] b : alongX) {
                out = Shapes.or(out, Block.box(b[0], b[1], b[2], b[3], b[4], b[5]));
            }
            xShape = out.optimize();
            registerDefaultState(stateDefinition.any().setValue(AXIS, Direction.Axis.Y));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            builder.add(AXIS);
        }

        @Override
        public BlockState getStateForPlacement(BlockPlaceContext context) {
            return defaultBlockState().setValue(AXIS, context.getClickedFace().getAxis());
        }

        @Override
        protected VoxelShape shapeFor(BlockState state) {
            return switch (state.getValue(AXIS)) {
                case Y -> shapes.get(Direction.UP);
                case Z -> shapes.get(Direction.DOWN);
                case X -> xShape;
            };
        }

        @Override
        protected BlockState rotate(BlockState state, Rotation rotation) {
            Direction.Axis axis = state.getValue(AXIS);
            if (axis != Direction.Axis.Y && (rotation == Rotation.CLOCKWISE_90 || rotation == Rotation.COUNTERCLOCKWISE_90)) {
                return state.setValue(AXIS, axis == Direction.Axis.X ? Direction.Axis.Z : Direction.Axis.X);
            }
            return state;
        }
    }
}
