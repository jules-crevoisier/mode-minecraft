package com.brasshaven.map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.material.MapColor;

import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;

/**
 * Reads a loaded chunk into map columns. Works on both sides: the server scans chunks around players into the shared
 * map, the client scans the chunks around itself for the live cave view.
 *
 * <p>Material codes: 0 unknown, 1 nothing to draw (void), 2..65 a vanilla {@link MapColor} (id + 2), and codes the
 * client tints with the biome like the world does: {@link #GRASS}, {@link #PLANT}, {@link #FOLIAGE}, {@link #WATER};
 * {@link #SPRUCE} and {@link #BIRCH} leaves have fixed tints; {@link #WALL} is solid rock in a cave slice.
 */
public final class MapScan {
    public static final int UNKNOWN = 0;
    public static final int VOID = 1;
    public static final int GRASS = 200;
    public static final int PLANT = 201;
    public static final int FOLIAGE = 202;
    public static final int SPRUCE = 203;
    public static final int BIRCH = 204;
    public static final int WATER = 205;
    public static final int WALL = 206;

    /** Surface (heightmap) scan. */
    public static final int SURFACE = Integer.MIN_VALUE;
    /** Nether-like dimensions: the first floor under the ceiling. */
    public static final int ROOF = Integer.MIN_VALUE + 1;

    private static final Set<Block> GRASS_BLOCKS = Set.of(Blocks.GRASS_BLOCK);
    private static final Set<Block> PLANTS = Set.of(Blocks.SHORT_GRASS, Blocks.TALL_GRASS, Blocks.FERN, Blocks.LARGE_FERN,
            Blocks.BUSH, Blocks.SUGAR_CANE);
    private static final Set<Block> FOLIAGE_BLOCKS = Set.of(Blocks.OAK_LEAVES, Blocks.JUNGLE_LEAVES, Blocks.ACACIA_LEAVES,
            Blocks.DARK_OAK_LEAVES, Blocks.MANGROVE_LEAVES, Blocks.VINE);

    private final Map<Holder<Biome>, String> biomeIds = new IdentityHashMap<>();
    private final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
    private final BlockPos.MutableBlockPos below = new BlockPos.MutableBlockPos();
    private int material;
    private int floorMaterial;
    private int height;
    private int depth;

    /**
     * Scans {@code chunk} into {@code into}, whose column (0, 0) is the block (ox, oz). {@code mode}: {@link #SURFACE},
     * {@link #ROOF}, or the height of a cave slice. Returns true when a column changed.
     */
    public boolean scan(Level level, LevelChunk chunk, RegionData into, int ox, int oz, int mode) {
        int x0 = chunk.getPos().getMinBlockX();
        int z0 = chunk.getPos().getMinBlockZ();
        int minY = level.getMinY();
        int top = mode == ROOF ? minY + level.dimensionType().logicalHeight() - 1 : Math.min(mode, level.getMaxY());
        boolean changed = false;
        for (int lz = 0; lz < 16; lz++) {
            for (int lx = 0; lx < 16; lx++) {
                int wx = x0 + lx;
                int wz = z0 + lz;
                if (mode == SURFACE) {
                    surface(level, chunk, wx, wz, minY);
                } else {
                    slice(level, chunk, wx, wz, top, minY, mode == ROOF ? 64 : 10, mode == ROOF ? 160 : 48);
                }
                int b = material == VOID ? 0 : into.biomeIndex(biomeId(chunk.getNoiseBiome(QuartPos.fromBlock(wx),
                        QuartPos.fromBlock(height), QuartPos.fromBlock(wz))));
                changed |= into.set(into.index(wx - ox, wz - oz), material, floorMaterial, height, depth, b);
            }
        }
        return changed;
    }

    /** Forgets the biome holders of a world that was closed (they belong to its registries). */
    public void clearCache() {
        biomeIds.clear();
    }

    private String biomeId(Holder<Biome> holder) {
        return biomeIds.computeIfAbsent(holder, h -> h.unwrapKey().map(k -> k.identifier().toString()).orElse("minecraft:plains"));
    }

    private void surface(Level level, LevelChunk chunk, int wx, int wz, int minY) {
        int y = chunk.getHeight(Heightmap.Types.WORLD_SURFACE, wx, wz);
        if (y < minY) {
            empty(minY);
            return;
        }
        pos.set(wx, y, wz);
        BlockState state = chunk.getBlockState(pos);
        MapColor mc = state.getMapColor(level, pos);
        while (mc == MapColor.NONE && y > minY) {
            pos.setY(--y);
            state = chunk.getBlockState(pos);
            mc = state.getMapColor(level, pos);
        }
        if (mc == MapColor.NONE) {
            empty(minY);
            return;
        }
        column(level, chunk, state, mc, y, minY);
    }

    /** From {@code top} down: through a wall (at most {@code wallSearch} blocks) to the floor of the space below. */
    private void slice(Level level, LevelChunk chunk, int wx, int wz, int top, int minY, int wallSearch, int maxDepth) {
        int y = top;
        pos.set(wx, y, wz);
        BlockState state = chunk.getBlockState(pos);
        MapColor mc = state.getMapColor(level, pos);
        while (mc != MapColor.NONE && y > minY && top - y < wallSearch) {
            pos.setY(--y);
            state = chunk.getBlockState(pos);
            mc = state.getMapColor(level, pos);
        }
        if (mc != MapColor.NONE) {
            material = WALL;
            floorMaterial = 0;
            height = top;
            depth = 0;
            return;
        }
        while (mc == MapColor.NONE && y > minY && top - y < maxDepth) {
            pos.setY(--y);
            state = chunk.getBlockState(pos);
            mc = state.getMapColor(level, pos);
        }
        if (mc == MapColor.NONE) {
            empty(y);
            return;
        }
        column(level, chunk, state, mc, y, minY);
    }

    private void empty(int y) {
        material = VOID;
        floorMaterial = 0;
        height = y;
        depth = 0;
    }

    private void column(Level level, LevelChunk chunk, BlockState state, MapColor mc, int y, int minY) {
        height = y;
        depth = 0;
        floorMaterial = 0;
        if (!state.getFluidState().isEmpty() && state.getFluidState().is(FluidTags.WATER)) {
            below.set(pos);
            BlockState floor = state;
            int d = 0;
            int by = y;
            while (by > minY && d < 64) {
                below.setY(--by);
                floor = chunk.getBlockState(below);
                d++;
                if (floor.getFluidState().isEmpty() || !floor.getFluidState().is(FluidTags.WATER)) {
                    break;
                }
            }
            material = WATER;
            depth = Math.max(1, Math.min(127, d));
            MapColor fc = floor.getMapColor(level, below);
            floorMaterial = fc == MapColor.NONE || fc == MapColor.WATER ? 0 : code(floor, fc);
            return;
        }
        material = code(state, mc);
    }

    private static int code(BlockState state, MapColor mc) {
        Block b = state.getBlock();
        if (GRASS_BLOCKS.contains(b)) {
            return GRASS;
        }
        if (PLANTS.contains(b)) {
            return PLANT;
        }
        if (FOLIAGE_BLOCKS.contains(b)) {
            return FOLIAGE;
        }
        if (b == Blocks.SPRUCE_LEAVES) {
            return SPRUCE;
        }
        if (b == Blocks.BIRCH_LEAVES) {
            return BIRCH;
        }
        if (mc == MapColor.WATER) {
            return WATER;
        }
        return mc.id + 2;
    }
}
