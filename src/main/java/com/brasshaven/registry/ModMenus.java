package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import com.brasshaven.menu.TerminalMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraftforge.common.extensions.IForgeMenuType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModMenus {
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(ForgeRegistries.MENU_TYPES, Brasshaven.MODID);

    public static final RegistryObject<MenuType<TerminalMenu>> TERMINAL = MENUS.register("terminal",
            () -> IForgeMenuType.create((id, inv, buf) -> new TerminalMenu(id, inv, buf.readBlockPos())));
    public static final RegistryObject<MenuType<com.brasshaven.menu.ChiselTableMenu>> CHISEL_TABLE = MENUS.register("chisel_table",
            () -> IForgeMenuType.create((id, inv, buf) -> new com.brasshaven.menu.ChiselTableMenu(id, inv, buf.readBlockPos())));
    public static final RegistryObject<MenuType<com.brasshaven.menu.MachineMenu>> MACHINE = MENUS.register("machine",
            () -> IForgeMenuType.create(com.brasshaven.menu.MachineMenu::new));

    private ModMenus() {}
}
