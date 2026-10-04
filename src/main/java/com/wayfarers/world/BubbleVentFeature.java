package com.wayfarers.world;

import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BubbleColumnBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * Hydrothermal vents on the sea floor (wayfarers:bubble_vent): one to three little basalt chimneys around a glowing
 * core of magma, each blowing an upward bubble column (soul sand at its foot) all the way to the surface, so
 * swimmers can ride them up like a geyser. The magma is always capped by rock, so no downward whirlpool forms.
 */
public class BubbleVentFeature extends Feature<NoneFeatureConfiguration> {
    public BubbleVentFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> context) {
        WorldGenLevel level = context.level();
        RandomSource random = context.random();
        BlockPos origin = context.origin();
        int vents = 1 + random.nextInt(3);
        boolean placed = false;
        for (int i = 0; i < vents; i++) {
            int x = origin.getX() + (i == 0 ? 0 : random.nextInt(7) - 3);
            int z = origin.getZ() + (i == 0 ? 0 : random.nextInt(7) - 3);
            int y = level.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, x, z);
            placed |= vent(level, random, new BlockPos(x, y, z), i == 0);
        }
        return placed;
    }

    private static boolean isWater(WorldGenLevel level, BlockPos pos) {
        return level.getBlockState(pos).is(Blocks.WATER) && level.getFluidState(pos).is(FluidTags.WATER);
    }

    /** {@code base} is the first water block above the floor. */
    private static boolean vent(WorldGenLevel level, RandomSource random, BlockPos base, boolean big) {
        if (!isWater(level, base) || !isWater(level, base.above(4))) {
            return false;
        }
        // not on top of a vent placed just before: its chimney would cut that one's column in two (the cut-off
        // top would float over rock, an invalid bubble column)
        for (BlockPos p : BlockPos.betweenClosed(base.offset(-1, -1, -1), base.offset(1, 3, 1))) {
            if (level.getBlockState(p).is(Blocks.BUBBLE_COLUMN)) {
                return false;
            }
        }
        BlockState rock = Blocks.BASALT.defaultBlockState();
        BlockState smooth = Blocks.SMOOTH_BASALT.defaultBlockState();
        BlockState magma = Blocks.MAGMA_BLOCK.defaultBlockState();
        // the floor: soul sand under the column, magma around it, all of it capped by the chimney
        level.setBlock(base.below(), Blocks.SOUL_SAND.defaultBlockState(), 2);
        int chimney = big ? 2 + random.nextInt(2) : 1 + random.nextInt(2);
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                if (dx == 0 && dz == 0) {
                    continue;
                }
                BlockPos p = base.offset(dx, 0, dz);
                level.setBlock(p.below(), magma, 2);
                int h = chimney - ((dx != 0 && dz != 0) ? 1 : 0);
                for (int y = 0; y < Math.max(1, h); y++) {
                    level.setBlock(p.above(y), y == h - 1 && random.nextBoolean() ? smooth : rock, 2);
                }
            }
        }
        // a loose skirt of rubble and a few glowing cracks on the outer ring
        if (big) {
            for (int i = 0; i < 6; i++) {
                int dx = random.nextInt(5) - 2;
                int dz = random.nextInt(5) - 2;
                if (Math.abs(dx) < 2 && Math.abs(dz) < 2) {
                    continue;
                }
                BlockPos p = base.offset(dx, 0, dz);
                BlockPos floor = new BlockPos(p.getX(), level.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, p.getX(), p.getZ()), p.getZ());
                if (isWater(level, floor) && Math.abs(floor.getY() - base.getY()) <= 2) {
                    level.setBlock(floor, random.nextInt(3) == 0 ? Blocks.TUFF.defaultBlockState() : smooth, 2);
                }
            }
        }
        // the upward column, up to the last water block under the surface
        BlockState column = Blocks.BUBBLE_COLUMN.defaultBlockState().setValue(BubbleColumnBlock.DRAG_DOWN, false);
        BlockPos.MutableBlockPos p = base.mutable();
        int guard = 0;
        while (isWater(level, p) && guard++ < 128) {
            level.setBlock(p, column, 2);
            p.move(0, 1, 0);
        }
        return true;
    }
}
