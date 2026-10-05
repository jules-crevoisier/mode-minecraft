package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import com.brasshaven.generated.ModDecor;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModTabs {
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, Brasshaven.MODID);

    public static final RegistryObject<CreativeModeTab> MAIN = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.brasshaven"))
            .icon(() -> new ItemStack(ModItems.WAYFARER_ATLAS.get()))
            .withTabsBefore(CreativeModeTabs.SPAWN_EGGS)
            .displayItems((params, output) -> {
                ModItems.ALL.forEach(item -> output.accept(item.get()));
                ModDecor.ITEMS.forEach(item -> output.accept(item.get()));
                com.brasshaven.generated.GeneratedWorldBlocks.ITEMS.forEach(item -> output.accept(item.get()));
            })
            .build());

    private ModTabs() {}
}
