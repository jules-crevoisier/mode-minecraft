package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.menu.TerminalMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraftforge.common.extensions.IForgeMenuType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModMenus {
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(ForgeRegistries.MENU_TYPES, Wayfarers.MODID);

    public static final RegistryObject<MenuType<TerminalMenu>> TERMINAL = MENUS.register("terminal",
            () -> IForgeMenuType.create((id, inv, buf) -> new TerminalMenu(id, inv, buf.readBlockPos())));

    private ModMenus() {}
}
