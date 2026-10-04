package com.wayfarers.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.FenceBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.UntintedParticleLeavesBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.WoodType;
import net.minecraftforge.common.ToolAction;
import net.minecraftforge.common.ToolActions;
import org.jetbrains.annotations.Nullable;

import java.util.function.Supplier;

/**
 * Wood blocks of the mod (Glowwood, Rustwood; registered by the generated GeneratedWorldBlocks).
 *
 * <p>They burn like vanilla wood: vanilla's own table (FireBlock#setFlammable) is private, so each block answers
 * Forge's IForgeBlock#getFlammability / #getFireSpreadSpeed itself, with vanilla's numbers. Logs are stripped by
 * an axe through IForgeBlock#getToolModifiedState. (No @Override on those: the API stubs used for type-checking are
 * unpatched vanilla.)
 */
public final class WoodBlocks {
    /** Vanilla FireBlock odds: {spread speed (ignite odds), flammability (burn odds)}. */
    public static final int[] LOG = {5, 5};
    public static final int[] PLANKS = {5, 20};
    public static final int[] LEAVES = {30, 60};

    private WoodBlocks() {}

    /** Log or wood block (axis); {@code stripped} is what an axe turns it into, null when already stripped. */
    public static class Log extends RotatedPillarBlock {
        private final @Nullable Supplier<? extends Block> stripped;

        public Log(@Nullable Supplier<? extends Block> stripped, BlockBehaviour.Properties properties) {
            super(properties);
            this.stripped = stripped;
        }

        /** Forge IForgeBlock#getToolModifiedState: the axe strips the bark and keeps the axis. */
        @Nullable
        public BlockState getToolModifiedState(BlockState state, UseOnContext context, ToolAction toolAction, boolean simulate) {
            if (stripped != null && toolAction == ToolActions.AXE_STRIP) {
                return stripped.get().defaultBlockState().setValue(AXIS, state.getValue(AXIS));
            }
            return null;
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return LOG[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return LOG[0];
        }
    }

    public static class Planks extends Block {
        public Planks(BlockBehaviour.Properties properties) {
            super(properties);
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[0];
        }
    }

    public static class Stairs extends StairBlock {
        public Stairs(BlockState base, BlockBehaviour.Properties properties) {
            super(base, properties);
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[0];
        }
    }

    public static class Slab extends SlabBlock {
        public Slab(BlockBehaviour.Properties properties) {
            super(properties);
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[0];
        }
    }

    public static class Fence extends FenceBlock {
        public Fence(BlockBehaviour.Properties properties) {
            super(properties);
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[0];
        }
    }

    public static class FenceGate extends FenceGateBlock {
        public FenceGate(WoodType type, BlockBehaviour.Properties properties) {
            super(type, properties);
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return PLANKS[0];
        }
    }

    /** Leaves with their own falling-leaf particle colour (the textures are already coloured: no biome tint). */
    public static class Leaves extends UntintedParticleLeavesBlock {
        public Leaves(float particleChance, ParticleOptions particle, BlockBehaviour.Properties properties) {
            super(particleChance, particle, properties);
        }

        public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return LEAVES[1];
        }

        public int getFireSpreadSpeed(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
            return LEAVES[0];
        }
    }
}
