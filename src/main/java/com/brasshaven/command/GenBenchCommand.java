package com.brasshaven.command;

import com.mojang.brigadier.context.CommandContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.biome.BiomeManager;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSource;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterList;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterLists;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.ProtoChunk;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.chunk.UpgradeData;
import net.minecraft.world.level.levelgen.Aquifer;
import net.minecraft.world.level.levelgen.Beardifier;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator;
import net.minecraft.world.level.levelgen.NoiseChunk;
import net.minecraft.world.level.levelgen.NoiseGeneratorSettings;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.WorldGenerationContext;
import net.minecraft.world.level.levelgen.blending.Blender;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * /brasshaven genbench: how fast the world generates, for the CI performance gate (tools/ci_smoke.py --world compares
 * a world with the Brasshaven biomes and terrain touches against a vanilla one and fails above 5 % more).
 * <ul>
 *   <li>{@code genbench area <x> <z> <size>}: really generates size x size fresh chunks around block x z with the
 *   game's chunk system on all its worker threads (noise, surface, carvers, structures, features, light) and gives
 *   the wall time per chunk. This is the number the gate compares.</li>
 *   <li>{@code genbench noise}: the terrain stages alone, chunk by chunk on one thread (a fresh proto chunk: its
 *   noise chunk, biomes, noise fill and surface rules; no structures, carvers or features), for vanilla's Overworld
 *   (minecraft:overworld settings, the overworld biome preset) and, when the world runs other settings (the biome
 *   pack's brasshaven:overworld), for the world's own generator too, side by side in the same JVM. Also the cost of one
 *   getBaseHeight and of one climate sample (biome lookups).</li>
 * </ul>
 * Each result line starts with "Genbench" and is also appended to brasshaven-genbench.txt in the server folder.
 */
public final class GenBenchCommand {
    private static final int NOISE_SIDE = 8;
    private static final int WARMUP = 8;
    private static final int HEIGHT_SAMPLES = 300;
    private static final int CLIMATE_SAMPLES = 20000;
    /** Far from spawn and from anything the other tests generate (block 20000 = chunk 1250). */
    private static final int BENCH_CHUNK = 1250;

    private GenBenchCommand() {}

    static int noise(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack src = ctx.getSource();
        ServerLevel level = src.getServer().overworld();
        List<String> lines = new ArrayList<>();
        var settingsRegistry = level.registryAccess().lookupOrThrow(Registries.NOISE_SETTINGS);
        var presets = level.registryAccess().lookupOrThrow(Registries.MULTI_NOISE_BIOME_SOURCE_PARAMETER_LIST);
        Optional<Holder.Reference<NoiseGeneratorSettings>> vanillaSettings = settingsRegistry.get(NoiseGeneratorSettings.OVERWORLD);
        Optional<Holder.Reference<MultiNoiseBiomeSourceParameterList>> vanillaBiomes = presets.get(MultiNoiseBiomeSourceParameterLists.OVERWORLD);
        if (vanillaSettings.isPresent() && vanillaBiomes.isPresent()) {
            NoiseBasedChunkGenerator vanilla = new NoiseBasedChunkGenerator(MultiNoiseBiomeSource.createFromPreset(vanillaBiomes.get()),
                    vanillaSettings.get());
            RandomState rs = RandomState.create(vanillaSettings.get().value(), level.registryAccess().lookupOrThrow(Registries.NOISE),
                    level.getSeed());
            lines.add(safeBench(level, "vanilla", vanilla, rs));
        } else {
            lines.add("Genbench vanilla: no minecraft:overworld noise settings in this world");
        }
        ChunkGenerator own = level.getChunkSource().getGenerator();
        if (own instanceof NoiseBasedChunkGenerator noise && !noise.generatorSettings().is(NoiseGeneratorSettings.OVERWORLD)) {
            String name = noise.generatorSettings().unwrapKey().map(k -> k.identifier().toString()).orElse("world");
            lines.add(safeBench(level, "world " + name, noise, level.getChunkSource().randomState()));
        } else {
            lines.add("Genbench world: " + (own instanceof NoiseBasedChunkGenerator ? "vanilla settings (measured above)"
                    : "not a noise generator (" + own.getClass().getSimpleName() + ")"));
        }
        return report(src, lines);
    }

    static int area(CommandContext<CommandSourceStack> ctx, int x, int z, int size) {
        CommandSourceStack src = ctx.getSource();
        ServerLevel level = src.getServer().overworld();
        ServerChunkCache chunks = level.getChunkSource();
        int side = Math.max(1, Math.min(size, 32));
        int radius = side / 2;
        ChunkPos centre = ChunkPos.containing(new net.minecraft.core.BlockPos(x, 0, z));
        int x0 = centre.x() - radius;
        int z0 = centre.z() - radius;
        int already = 0;
        for (int dz = 0; dz < side; dz++) {
            for (int dx = 0; dx < side; dx++) {
                already += chunks.getChunkNow(x0 + dx, z0 + dz) != null ? 1 : 0;
            }
        }
        long t = System.nanoTime();
        // one ticket over the area: the worker threads generate it in parallel, getChunk waits like /forceload
        chunks.addTicketAndLoadWithRadius(TicketType.PLAYER_SPAWN, centre, radius);
        try {
            for (int dz = 0; dz < side; dz++) {
                for (int dx = 0; dx < side; dx++) {
                    level.getChunk(x0 + dx, z0 + dz);
                }
            }
        } finally {
            chunks.removeTicketWithRadius(TicketType.PLAYER_SPAWN, centre, radius);
        }
        double ms = (System.nanoTime() - t) / 1.0e6;
        int count = side * side;
        String line = String.format(Locale.ROOT, "Genbench area: %d x %d chunks at block %d %d (%d already loaded) in %.0f ms: "
                + "%.1f ms/chunk (full generation, %d worker threads)", side, side, x, z, already, ms, ms / count,
                Runtime.getRuntime().availableProcessors());
        // let the chunk map unload the area (the server does not tick while a command runs)
        long until = System.currentTimeMillis() + 300;
        chunks.tick(() -> System.currentTimeMillis() < until, false);
        return report(src, List.of(line));
    }

    private static int report(CommandSourceStack src, List<String> lines) {
        Path file = src.getServer().getServerDirectory().resolve("brasshaven-genbench.txt");
        try {
            Files.write(file, lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            src.sendFailure(Component.literal("Genbench: could not write " + file + ": " + e.getMessage()));
        }
        for (String line : lines) {
            src.sendSuccess(() -> Component.literal(line), false);
        }
        return lines.size();
    }

    /** {@link #bench}, a failure reported on its line (and logged, so CI sees it) instead of losing the other one. */
    private static String safeBench(ServerLevel level, String label, NoiseBasedChunkGenerator gen, RandomState rs) {
        try {
            return bench(level, label, gen, rs);
        } catch (RuntimeException e) {
            com.brasshaven.Brasshaven.LOGGER.error("genbench {} failed", label, e);
            return "Genbench " + label + ": failed (" + e + ")";
        }
    }

    /** One generator: proto chunks (noise chunk, biomes, noise, surface), getBaseHeight, climate samples. */
    private static String bench(ServerLevel level, String label, NoiseBasedChunkGenerator gen, RandomState rs) {
        NoiseGeneratorSettings settings = gen.generatorSettings().value();
        Aquifer.FluidPicker fluids = fluidPicker(settings);
        long seed = BiomeManager.obfuscateSeed(level.getSeed());
        long chunkNanos = 0;
        int chunkCount = 0;
        for (int i = -WARMUP; i < NOISE_SIDE * NOISE_SIDE; i++) {
            // a few chunks off to the side first, so the measure does not include the first-use costs
            ChunkPos pos = i < 0 ? new ChunkPos(BENCH_CHUNK + 40 - i, BENCH_CHUNK)
                    : new ChunkPos(BENCH_CHUNK + i % NOISE_SIDE, BENCH_CHUNK + i / NOISE_SIDE);
            long t = System.nanoTime();
            ProtoChunk chunk = new ProtoChunk(pos, UpgradeData.EMPTY, level, level.palettedContainerFactory(), null);
            // made here, so the generator does not look for structures in the real world (there are none: a proto
            // chunk outside the chunk map)
            chunk.getOrCreateNoiseChunk(c -> NoiseChunk.forChunk(c, rs, Beardifier.EMPTY, settings, fluids, Blender.empty()));
            gen.createBiomes(rs, Blender.empty(), null, chunk).join();
            // the chunk system marks each step done; the surface step reads the biomes and refuses a chunk short of it
            chunk.setPersistedStatus(ChunkStatus.BIOMES);
            gen.fillFromNoise(Blender.empty(), rs, null, chunk).join();
            chunk.setPersistedStatus(ChunkStatus.NOISE);
            gen.buildSurface(chunk, new WorldGenerationContext(gen, chunk), rs, null, new BiomeManager(chunk, seed),
                    Blender.empty(), null);
            if (i >= 0) {
                chunkNanos += System.nanoTime() - t;
                chunkCount++;
            }
        }
        long t = System.nanoTime();
        for (int i = 0; i < HEIGHT_SAMPLES; i++) {
            int x = BENCH_CHUNK * 16 + 37 * i;
            int z = BENCH_CHUNK * 16 - 3000 + 53 * i;
            gen.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, level, rs);
        }
        double heightMs = (System.nanoTime() - t) / 1.0e6 / HEIGHT_SAMPLES;
        BiomeSource biomes = gen.getBiomeSource();
        Climate.Sampler sampler = rs.sampler();
        t = System.nanoTime();
        for (int i = 0; i < CLIMATE_SAMPLES; i++) {
            int x = BENCH_CHUNK * 16 + 64 + 29 * (i % 200);
            int z = BENCH_CHUNK * 16 + 3000 + 31 * (i / 200);
            biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(64), QuartPos.fromBlock(z), sampler);
        }
        double climateUs = (System.nanoTime() - t) / 1.0e3 / CLIMATE_SAMPLES;
        return String.format(Locale.ROOT, "Genbench %s: %.2f ms/chunk (noise chunk, biomes, noise, surface; %d chunks, 1 thread), "
                        + "getBaseHeight %.3f ms, climate sample %.1f us", label, chunkNanos / 1.0e6 / Math.max(1, chunkCount),
                chunkCount, heightMs, climateUs);
    }

    /** NoiseBasedChunkGenerator's own (private) global fluid picker: lava below y -54, the sea above. */
    private static Aquifer.FluidPicker fluidPicker(NoiseGeneratorSettings settings) {
        Aquifer.FluidStatus lava = new Aquifer.FluidStatus(-54, Blocks.LAVA.defaultBlockState());
        int seaLevel = settings.seaLevel();
        Aquifer.FluidStatus sea = new Aquifer.FluidStatus(seaLevel, settings.defaultFluid());
        return (x, y, z) -> y < Math.min(-54, seaLevel) ? lava : sea;
    }
}
