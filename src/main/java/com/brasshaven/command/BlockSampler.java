package com.brasshaven.command;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.MapColor;

import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Reads a box of the world into the voxels {@link IsoRenderer} draws: each block state becomes a kind (solid, plant,
 * carpet, water), a colour (its map colour, or the biome's grass, foliage or water tint) and flags (glow, wet,
 * grassy, flower). Used by the structure fit renders ({@link FitCheckCommand}).
 */
final class BlockSampler {
    private static final int TINT_NONE = 0;
    private static final int TINT_GRASS = 1;
    private static final int TINT_FOLIAGE = 2;
    private static final int TINT_WATER = 3;

    private BlockSampler() {}

    /** The blocks of the {@code sx x sz} box from y0 to y1, biome tints taken at the surface of each column. */
    static int[] sample(ServerLevel level, int x0, int z0, int sx, int sz, int y0, int y1) {
        int sy = y1 - y0 + 1;
        int[] vox = new int[sy * sz * sx];
        Map<BlockState, int[]> kinds = new IdentityHashMap<>();
        Map<Biome, int[]> tints = new IdentityHashMap<>();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int z = 0; z < sz; z++) {
            for (int x = 0; x < sx; x++) {
                int ty = level.getHeight(Heightmap.Types.WORLD_SURFACE, x0 + x, z0 + z) - 1;
                Biome b = level.getBiome(pos.set(x0 + x, ty, z0 + z)).value();
                int[] tint = tints.computeIfAbsent(b, k -> new int[] {
                        k.getSpecialEffects().grassColorOverride().orElse(0x79C05A),
                        k.getSpecialEffects().foliageColorOverride().orElse(0x59AE30),
                        k.getWaterColor()});
                for (int y = 0; y < sy; y++) {
                    pos.set(x0 + x, y0 + y, z0 + z);
                    BlockState state = level.getBlockState(pos);
                    if (state.isAir()) {
                        continue;
                    }
                    int[] k = kinds.computeIfAbsent(state, BlockSampler::classify);
                    if (k[0] == IsoRenderer.AIR) {
                        continue;
                    }
                    int rgb = switch (k[3]) {
                        case TINT_GRASS -> IsoRenderer.scale(tint[0], k[0] == IsoRenderer.PLANT ? 0.92 : 1.0);
                        case TINT_FOLIAGE -> IsoRenderer.scale(tint[1], 0.82);
                        case TINT_WATER -> tint[2];
                        default -> k[1];
                    };
                    vox[(y * sz + z) * sx + x] = IsoRenderer.voxel(k[0], rgb, k[2]);
                }
            }
        }
        return vox;
    }

    /** {kind, colour, flags, tint} for a block state. */
    private static int[] classify(BlockState state) {
        String name = BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
        FluidState fluid = state.getFluidState();
        boolean water = !fluid.isEmpty() && fluid.is(FluidTags.WATER);
        int glow = state.getLightEmission() > 0 ? IsoRenderer.GLOW : 0;
        MapColor map = state.getMapColor(EmptyBlockGetter.INSTANCE, BlockPos.ZERO);
        if (state.getBlock() instanceof LiquidBlock) {
            return water ? new int[] {IsoRenderer.WATER, 0x3F76E4, 0, TINT_WATER}
                    : new int[] {IsoRenderer.SOLID, 0xF07A1E, IsoRenderer.GLOW, TINT_NONE};
        }
        boolean noCollision = state.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO).isEmpty();
        if (water && noCollision && map == MapColor.WATER) {
            return new int[] {IsoRenderer.WATER, 0x3F76E4, 0, TINT_WATER};  // bubble columns, kelp, seagrass
        }
        if (map == MapColor.NONE) {
            return water ? new int[] {IsoRenderer.WATER, 0x3F76E4, 0, TINT_WATER} : new int[] {IsoRenderer.AIR, 0, 0, 0};
        }
        int wet = water ? IsoRenderer.WET : 0;
        int col = map.col;
        if (name.equals("snow") || name.endsWith("carpet") || name.equals("pink_petals") || name.equals("wildflowers")
                || name.equals("leaf_litter") || name.equals("lily_pad")) {
            int c = name.equals("snow") ? 0xF4F8FF : name.equals("lily_pad") ? 0x2E8A2E : col;
            return new int[] {IsoRenderer.CARPET, c, glow | wet, TINT_NONE};
        }
        if (noCollision) {
            boolean flower = state.is(BlockTags.FLOWERS) || state.is(BlockTags.SMALL_FLOWERS);
            if (flower) {
                return new int[] {IsoRenderer.PLANT, flowerColour(name, col), glow | wet | IsoRenderer.FLOWER, TINT_NONE};
            }
            int tint = map == MapColor.PLANT && (name.contains("grass") || name.contains("fern") || name.equals("vine")
                    || name.equals("sugar_cane") || name.equals("bush")) ? TINT_GRASS : TINT_NONE;
            return new int[] {IsoRenderer.PLANT, col, glow | wet, tint};
        }
        if (name.equals("grass_block")) {
            return new int[] {IsoRenderer.SOLID, col, glow | IsoRenderer.GRASSY, TINT_GRASS};
        }
        if (state.is(BlockTags.LEAVES)) {
            if (name.equals("spruce_leaves")) {
                return new int[] {IsoRenderer.SOLID, IsoRenderer.scale(0x619961, 0.8), glow, TINT_NONE};
            }
            if (name.equals("birch_leaves")) {
                return new int[] {IsoRenderer.SOLID, IsoRenderer.scale(0x80A755, 0.85), glow, TINT_NONE};
            }
            if (map == MapColor.PLANT) {
                return new int[] {IsoRenderer.SOLID, col, glow, TINT_FOLIAGE};
            }
            return new int[] {IsoRenderer.SOLID, IsoRenderer.scale(col, 0.85), glow, TINT_NONE};
        }
        return new int[] {IsoRenderer.SOLID, col, glow, TINT_NONE};
    }

    private static final Map<String, Integer> FLOWERS = new LinkedHashMap<>();

    static {
        FLOWERS.put("wither", 0x2A2A2A);
        FLOWERS.put("poppy", 0xD8302A);
        FLOWERS.put("rose", 0xD8302A);
        FLOWERS.put("red", 0xD8302A);
        FLOWERS.put("dandelion", 0xF2D13A);
        FLOWERS.put("sunflower", 0xF2D13A);
        FLOWERS.put("yellow", 0xF2D13A);
        FLOWERS.put("gold", 0xF2D13A);
        FLOWERS.put("cornflower", 0x4A78E0);
        FLOWERS.put("blue", 0x4A78E0);
        FLOWERS.put("orchid", 0x3FA8E8);
        FLOWERS.put("allium", 0xB060D0);
        FLOWERS.put("lilac", 0xC890D8);
        FLOWERS.put("purple", 0xB060D0);
        FLOWERS.put("violet", 0xB060D0);
        FLOWERS.put("peony", 0xF0A0C8);
        FLOWERS.put("pink", 0xF0A0C8);
        FLOWERS.put("cherry", 0xF0A0C8);
        FLOWERS.put("orange", 0xF08A2A);
        FLOWERS.put("torchflower", 0xF08A2A);
        FLOWERS.put("oxeye", 0xF2F2EC);
        FLOWERS.put("white", 0xF2F2EC);
        FLOWERS.put("lily", 0xF2F2EC);
        FLOWERS.put("azure", 0xF2F2EC);
        FLOWERS.put("daisy", 0xF2F2EC);
    }

    private static int flowerColour(String name, int mapColour) {
        for (Map.Entry<String, Integer> e : FLOWERS.entrySet()) {
            if (name.contains(e.getKey())) {
                return e.getValue();
            }
        }
        return mapColour != MapColor.PLANT.col ? mapColour : 0xE8C8F0;
    }
}
