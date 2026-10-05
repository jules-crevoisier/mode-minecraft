package com.brasshaven.registry;

import com.mojang.serialization.Codec;
import com.brasshaven.Brasshaven;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModDataComponents {
    public static final DeferredRegister<DataComponentType<?>> COMPONENTS =
            DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, Brasshaven.MODID);

    /** Index of the structure the Structure Compass is tuned to (-1 = any). */
    public static final RegistryObject<DataComponentType<Integer>> COMPASS_TARGET = COMPONENTS.register("compass_target",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
    /** Hits landed with the Frost Blade (every third one freezes). */
    public static final RegistryObject<DataComponentType<Integer>> FROST_HITS = COMPONENTS.register("frost_hits",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
    /** Builder's Wand symmetry mode (BuilderWandItem.Symmetry ordinal: off, mirror X, mirror Z, both). */
    public static final RegistryObject<DataComponentType<Integer>> WAND_SYMMETRY = COMPONENTS.register("wand_symmetry",
            () -> DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
    /** Builder's Wand mirror centre (block and dimension). */
    public static final RegistryObject<DataComponentType<net.minecraft.core.GlobalPos>> WAND_MIRROR = COMPONENTS.register("wand_mirror",
            () -> DataComponentType.<net.minecraft.core.GlobalPos>builder().persistent(net.minecraft.core.GlobalPos.CODEC)
                    .networkSynchronized(net.minecraft.core.GlobalPos.STREAM_CODEC).build());

    private ModDataComponents() {}
}
