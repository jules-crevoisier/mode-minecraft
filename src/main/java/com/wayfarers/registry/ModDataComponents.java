package com.wayfarers.registry;

import com.mojang.serialization.Codec;
import com.wayfarers.Wayfarers;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModDataComponents {
    public static final DeferredRegister<DataComponentType<?>> COMPONENTS =
            DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, Wayfarers.MODID);

    /** Index of the structure the Structure Compass is tuned to (-1 = any). */
    public static final RegistryObject<DataComponentType<Integer>> COMPASS_TARGET = COMPONENTS.register("compass_target",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
    /** Hits landed with the Frost Blade (every third one freezes). */
    public static final RegistryObject<DataComponentType<Integer>> FROST_HITS = COMPONENTS.register("frost_hits",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

    private ModDataComponents() {}
}
