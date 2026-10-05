package com.wayfarers.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.wayfarers.Wayfarers;
import com.wayfarers.config.WayfarersConfig;
import com.wayfarers.registry.ModWorldgen;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraftforge.common.world.BiomeModifier;
import net.minecraftforge.common.world.ModifiableBiomeInfo;

/**
 * {@code {"type": "wayfarers:toggled_features", "toggle": "boulders", "biomes": [...], "features": ..., "step": ...}}:
 * Forge's add_features behind a config switch ({@code world.terrain.<toggle>}, {@link WayfarersConfig#terrainTouch}).
 * Switched off, the biome is left exactly as it was: the feature is not even listed, so it costs nothing. Biome
 * modifiers apply when a server starts, so a change of the option takes effect at the next start (new chunks only).
 * The terrain touches use it (tools/wf/worldbiomes.py TOUCHES).
 */
public record ToggledFeaturesModifier(String toggle, HolderSet<Biome> biomes, HolderSet<PlacedFeature> features,
                                      GenerationStep.Decoration step) implements BiomeModifier {
    public static final MapCodec<ToggledFeaturesModifier> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Codec.STRING.fieldOf("toggle").forGetter(ToggledFeaturesModifier::toggle),
            Biome.LIST_CODEC.fieldOf("biomes").forGetter(ToggledFeaturesModifier::biomes),
            PlacedFeature.LIST_CODEC.fieldOf("features").forGetter(ToggledFeaturesModifier::features),
            GenerationStep.Decoration.CODEC.fieldOf("step").forGetter(ToggledFeaturesModifier::step)
    ).apply(i, ToggledFeaturesModifier::new));

    @Override
    public void modify(Holder<Biome> biome, Phase phase, ModifiableBiomeInfo.BiomeInfo.Builder builder) {
        if (phase != Phase.ADD || !biomes.contains(biome)) {
            return;
        }
        Boolean on = WayfarersConfig.terrainTouch(toggle);
        if (on == null) {
            Wayfarers.LOGGER.warn("Biome modifier with an unknown terrain toggle '{}': left off", toggle);
            return;
        }
        if (on) {
            for (Holder<PlacedFeature> feature : features) {
                builder.getGenerationSettings().addFeature(step, feature);
            }
        }
    }

    @Override
    public MapCodec<? extends BiomeModifier> codec() {
        return ModWorldgen.TOGGLED_FEATURES.get();
    }
}
