package com.wayfarers.block;

import com.mojang.serialization.MapCodec;
import com.wayfarers.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.redstone.Orientation;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

/**
 * One block class for every simple machine: no power network, no pipes to learn. Each machine does one
 * visible job, shows its setting when clicked and explains itself in its tooltip and manual page.
 */
public class MachineBlock extends BaseEntityBlock {
    public static final EnumProperty<Direction> FACING = BlockStateProperties.FACING;
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;

    public enum Kind {
        /** Harvests ripe crops around it, replants, and stores the harvest. */
        HARVESTER(true, false, true),
        /** Makes plants around and below it grow faster and keeps farmland wet. */
        SPRINKLER(false, false, false),
        /** Pulls in items and experience orbs nearby, then feeds the container below. */
        VACUUM(true, false, false),
        /** Breaks the block in front of it on a redstone pulse. */
        BREAKER(true, false, true),
        /** Places a block in front of it on a redstone pulse. */
        PLACER(true, false, true),
        /** Sends a short redstone pulse every few seconds. */
        TIMER(false, true, false),
        /** Broadcasts the redstone signal it receives on its colour channel. */
        TRANSMITTER(false, false, false),
        /** Outputs a signal while a transmitter of its colour is powered. */
        RECEIVER(false, true, false),
        /** Outputs a signal while players, monsters, animals or items are near. */
        DETECTOR(false, true, false);

        public final boolean hasInventory;
        public final boolean emitsSignal;
        public final boolean anyFacing;

        Kind(boolean hasInventory, boolean emitsSignal, boolean anyFacing) {
            this.hasInventory = hasInventory;
            this.emitsSignal = emitsSignal;
            this.anyFacing = anyFacing;
        }

        public boolean readsRedstone() {
            return this == BREAKER || this == PLACER || this == TRANSMITTER;
        }
    }

    private final Kind kind;
    private final MapCodec<MachineBlock> codec;

    public MachineBlock(Properties properties, Kind kind) {
        super(properties);
        this.kind = kind;
        this.codec = simpleCodec(p -> new MachineBlock(p, kind));
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(POWERED, false));
    }

    public Kind kind() {
        return kind;
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return codec;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, POWERED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction facing = kind.anyFacing ? context.getNearestLookingDirection().getOpposite()
                : context.getHorizontalDirection().getOpposite();
        return defaultBlockState().setValue(FACING, facing);
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new MachineBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    // ------------------------------------------------------------------ interaction
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide() && level.getBlockEntity(pos) instanceof MachineBlockEntity machine) {
            machine.use(player);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        DyeColor dye = stack.get(DataComponents.DYE);
        if ((kind == Kind.TRANSMITTER || kind == Kind.RECEIVER) && dye != null) {
            if (!level.isClientSide() && level.getBlockEntity(pos) instanceof MachineBlockEntity machine) {
                machine.setChannel(player, dye.getId());
            }
            return InteractionResult.SUCCESS;
        }
        return InteractionResult.TRY_WITH_EMPTY_HAND;
    }

    // ------------------------------------------------------------------ redstone
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, @Nullable Orientation orientation,
                                   boolean movedByPiston) {
        if (level.isClientSide() || !kind.readsRedstone()) {
            return;
        }
        boolean powered = level.hasNeighborSignal(pos);
        if (powered == state.getValue(POWERED)) {
            return;
        }
        level.setBlock(pos, state.setValue(POWERED, powered), Block.UPDATE_CLIENTS);
        if (powered && (kind == Kind.BREAKER || kind == Kind.PLACER)) {
            level.scheduleTick(pos, this, 2);
        }
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (level.getBlockEntity(pos) instanceof MachineBlockEntity machine) {
            machine.pulse(level);
        }
    }

    @Override
    protected boolean isSignalSource(BlockState state) {
        return kind.emitsSignal;
    }

    @Override
    protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
        if (!kind.emitsSignal) {
            return 0;
        }
        if (kind == Kind.DETECTOR) {
            return level.getBlockEntity(pos) instanceof MachineBlockEntity machine ? machine.signal() : 0;
        }
        return state.getValue(POWERED) ? 15 : 0;
    }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) {
        return kind.hasInventory;
    }

    @Override
    protected int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos, Direction direction) {
        return AbstractContainerMenu.getRedstoneSignalFromBlockEntity(level.getBlockEntity(pos));
    }

    @Override
    public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide() || type != ModBlockEntities.MACHINE.get() || kind == Kind.BREAKER || kind == Kind.PLACER) {
            return null;
        }
        return (lvl, pos, st, be) -> ((MachineBlockEntity) be).serverTick((ServerLevel) lvl, st);
    }
}
