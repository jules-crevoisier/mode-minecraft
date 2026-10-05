package com.brasshaven.world;

import com.brasshaven.Brasshaven;
import com.brasshaven.config.BrasshavenConfig;
import net.minecraft.network.chat.Component;
import net.minecraft.server.packs.PackLocationInfo;
import net.minecraft.server.packs.PackSelectionConfig;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraftforge.event.AddPackFindersEvent;
import net.minecraftforge.fml.ModList;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;

/**
 * Offers the Brasshaven biomes (Crimson Mire, Volcanic Highlands, Pale Dunes) as a built-in data pack shipped inside
 * the jar (custom_biomes_pack/, written by tools/gen_world.py). The pack holds one file: the "Default" world preset
 * (minecraft:normal), whose Overworld uses vanilla's own biome parameter list with a few climate cells handed to our
 * biomes, on the noise settings brasshaven:overworld (vanilla's plus our surface rules): the terrain itself is
 * Minecraft's. A world preset only matters when a world is created, so Superflat, Amplified, Large Biomes and
 * existing worlds are left alone, and a world keeps its biomes whatever the pack or config say later (its dimensions
 * are saved with it). The biomes, the noise settings, their features and the terrain touches live in the mod's own
 * data and are always loaded.
 *
 * <p>With {@code world.customBiomes = true} (default) it is a built-in pack, ticked for every new world; with
 * {@code false} it is a feature pack: listed, but off unless the player ticks it. As with any custom Overworld biome
 * list, Minecraft shows its "experimental settings" warning when a world is created with it.
 */
public final class CustomBiomesPack {
    public static final String PACK_ID = Brasshaven.MODID + ":custom_biomes";

    private CustomBiomesPack() {}

    public static void addPacks(AddPackFindersEvent event) {
        if (event.getPackType() != PackType.SERVER_DATA) {
            return;
        }
        Path root = ModList.getModFileById(Brasshaven.MODID).getFile().findResource("custom_biomes_pack");
        if (!Files.isDirectory(root)) {
            Brasshaven.LOGGER.warn("Brasshaven biome pack missing from the jar ({})", root);
            return;
        }
        boolean on = BrasshavenConfig.CUSTOM_BIOMES.get();
        PackLocationInfo info = new PackLocationInfo(PACK_ID, Component.translatable("pack.brasshaven.custom_biomes"),
                on ? PackSource.BUILT_IN : PackSource.FEATURE, Optional.empty());
        Pack pack = Pack.readMetaAndCreate(info, new PathPackResources.PathResourcesSupplier(root), PackType.SERVER_DATA,
                new PackSelectionConfig(false, Pack.Position.TOP, false));
        if (pack != null) {
            event.addRepositorySource(consumer -> consumer.accept(pack));
        }
    }
}
