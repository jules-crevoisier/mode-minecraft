package com.brasshaven.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.brasshaven.Brasshaven;
import com.brasshaven.client.render.CrateRenderer;
import com.brasshaven.generated.model.ModelRegistry;
import com.brasshaven.registry.ModBlockEntities;
import com.brasshaven.registry.ModEntities;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.bus.BusGroup;
import org.lwjgl.glfw.GLFW;

/** Client-only wiring: entity models and renderers, HUD layers (boss bars, quest tracker, minimap) and key bindings. */
public final class BrasshavenClient {
    private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(Brasshaven.id("main"));
    public static final KeyMapping SORT_KEY = new KeyMapping("key.brasshaven.sort_inventory",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY);
    public static final KeyMapping MAGNET_KEY = new KeyMapping("key.brasshaven.toggle_magnet",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_N, CATEGORY);
    /** World map, minimap show/hide, minimap zoom and map ping (see client/map). */
    public static final KeyMapping MAP_KEY = new KeyMapping("key.brasshaven.world_map",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_M, CATEGORY);
    public static final KeyMapping MINIMAP_KEY = new KeyMapping("key.brasshaven.toggle_minimap",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_H, CATEGORY);
    public static final KeyMapping MINIMAP_ZOOM_KEY = new KeyMapping("key.brasshaven.minimap_zoom",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_Z, CATEGORY);
    public static final KeyMapping PING_KEY = new KeyMapping("key.brasshaven.map_ping",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_B, CATEGORY);
    public static final KeyMapping QUESTS_KEY = new KeyMapping("key.brasshaven.quests",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_J, CATEGORY);
    public static final KeyMapping SKILLS_KEY = new KeyMapping("key.brasshaven.skills",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_K, CATEGORY);
    public static final KeyMapping ABILITY_KEY = new KeyMapping("key.brasshaven.ability",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_V, CATEGORY);
    /** Builder's Wand in hand: cycle its symmetry (off, mirror X, mirror Z, both). */
    public static final KeyMapping WAND_KEY = new KeyMapping("key.brasshaven.wand_symmetry",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_G, CATEGORY);
    /** Held over an item in an inventory: opens its manual page (TipCards). */
    public static final KeyMapping MANUAL_KEY = new KeyMapping("key.brasshaven.manual_page",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_W, CATEGORY);

    /** Recipe viewer (client/recipes): over an item in an inventory, its recipes / its uses; I shows or hides the item list. */
    public static final KeyMapping RECIPES_KEY = new KeyMapping("key.brasshaven.recipes",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY);
    public static final KeyMapping USES_KEY = new KeyMapping("key.brasshaven.uses",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_U, CATEGORY);
    public static final KeyMapping RECIPE_PANEL_KEY = new KeyMapping("key.brasshaven.recipe_panel",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_I, CATEGORY);

    private BrasshavenClient() {}

    public static void init(BusGroup modBus, net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext context) {
        // the manual key only means something with an inventory open: as a GUI-only binding it doesn't show up as
        // a conflict with "Walk Forwards" (also W) in the controls screen
        ((net.minecraftforge.client.extensions.IForgeKeyMapping) MANUAL_KEY).setKeyConflictContext(
                net.minecraftforge.client.settings.KeyConflictContext.GUI);
        // the recipe viewer's keys work in inventories only; the in-game keys on the same letters (R sorts, U opens a
        // player's card) only work with no screen open: different contexts, so the controls screen shows no conflict
        for (KeyMapping gui : new KeyMapping[] {RECIPES_KEY, USES_KEY, RECIPE_PANEL_KEY}) {
            ((net.minecraftforge.client.extensions.IForgeKeyMapping) gui).setKeyConflictContext(
                    net.minecraftforge.client.settings.KeyConflictContext.GUI);
        }
        ((net.minecraftforge.client.extensions.IForgeKeyMapping) SORT_KEY).setKeyConflictContext(
                net.minecraftforge.client.settings.KeyConflictContext.IN_GAME);
        EntityRenderersEvent.RegisterLayerDefinitions.BUS.addListener(ModelRegistry::registerLayers);
        EntityRenderersEvent.RegisterRenderers.BUS.addListener(BrasshavenClient::registerRenderers);
        AddGuiOverlayLayersEvent.BUS.addListener(EldenBossBar::register);
        AddGuiOverlayLayersEvent.BUS.addListener(QuestTracker::register);
        MobHealthBars.register();
        ContainerButtons.register();
        WandPreview.register();
        StorageHighlight.register();
        net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent.getBus(modBus).addListener(event -> event.enqueueWork(() ->
                {
                    net.minecraft.client.gui.screens.MenuScreens.register(com.brasshaven.registry.ModMenus.TERMINAL.get(),
                            com.brasshaven.client.gui.TerminalScreen::new);
                    net.minecraft.client.gui.screens.MenuScreens.register(com.brasshaven.registry.ModMenus.CHISEL_TABLE.get(),
                            com.brasshaven.client.gui.ChiselTableScreen::new);
                    net.minecraft.client.gui.screens.MenuScreens.register(com.brasshaven.registry.ModMenus.MACHINE.get(),
                            com.brasshaven.client.gui.MachineScreen::new);
                }));
        AddGuiOverlayLayersEvent.BUS.addListener(TipCards::register);
        AddGuiOverlayLayersEvent.BUS.addListener(ManaHud::register);
        AddGuiOverlayLayersEvent.BUS.addListener(com.brasshaven.client.map.MinimapHud::register);
        net.minecraftforge.client.event.ClientPlayerNetworkEvent.LoggingOut.BUS.addListener(e -> com.brasshaven.client.map.ClientMap.onLogout());
        net.minecraftforge.client.event.SystemMessageReceivedEvent.BUS.addListener(
                (java.util.function.Predicate<net.minecraftforge.client.event.SystemMessageReceivedEvent>) e -> {
                    com.brasshaven.client.map.ClientMap.onSystemMessage(e.getMessage());
                    return false;
                });
        // every Brasshaven item gets the same tooltip layout (item/BrassTooltip); the classes that don't add it
        // themselves (vanilla tool, block and egg classes) get it here, under the name
        com.brasshaven.item.BrassTooltip.shiftDown = () -> Minecraft.getInstance().hasShiftDown();
        net.minecraftforge.event.entity.player.ItemTooltipEvent.BUS.addListener(BrasshavenClient::onTooltip);
        net.minecraftforge.event.entity.player.ItemTooltipEvent.BUS.addListener(TipCards::onTooltip);
        AccessoryClient.register();
        TipCards.registerKeys();
        com.brasshaven.client.recipes.RecipeViewer.register();
        ReleaseClient.register();
        // "Config" button of the mods list: the display settings in the mod's own theme
        context.registerExtensionPoint(
                net.minecraftforge.client.ConfigScreenHandler.ConfigScreenFactory.class,
                () -> new net.minecraftforge.client.ConfigScreenHandler.ConfigScreenFactory(
                        (mc, parent) -> new com.brasshaven.client.gui.SettingsScreen(parent)));
        RegisterKeyMappingsEvent.BUS.addListener(event -> {
            event.register(SORT_KEY);
            event.register(MAGNET_KEY);
            event.register(QUESTS_KEY);
            event.register(SKILLS_KEY);
            event.register(ABILITY_KEY);
            event.register(WAND_KEY);
            event.register(MANUAL_KEY);
            event.register(MAP_KEY);
            event.register(MINIMAP_KEY);
            event.register(MINIMAP_ZOOM_KEY);
            event.register(PING_KEY);
            event.register(RECIPES_KEY);
            event.register(USES_KEY);
            event.register(RECIPE_PANEL_KEY);
        });
        TickEvent.ClientTickEvent.Post.BUS.addListener(event -> onClientTick());
        // scripted screenshot run for CI; inert unless the JVM has -Dbrasshaven.ci=true
        CiDriver.register();
    }

    private static void onTooltip(net.minecraftforge.event.entity.player.ItemTooltipEvent event) {
        net.minecraft.world.item.ItemStack stack = event.getItemStack();
        if (stack.isEmpty() || stack.getItem() instanceof com.brasshaven.item.BrassTooltip.Styled
                || !Brasshaven.MODID.equals(net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace())) {
            return;
        }
        java.util.List<net.minecraft.network.chat.Component> lines = com.brasshaven.item.BrassTooltip.lines(stack);
        java.util.List<net.minecraft.network.chat.Component> tip = event.getToolTip();
        tip.addAll(Math.min(1, tip.size()), lines);
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        humanoid(event, ModEntities.RUIN_WALKER.get(), "ruin_walker");
        humanoid(event, ModEntities.MAP_WRAITH.get(), "map_wraith");
        humanoid(event, ModEntities.BASALT_GUARD.get(), "basalt_guard");
        humanoid(event, ModEntities.VOID_STALKER.get(), "void_stalker");
        humanoid(event, ModEntities.VOID_WARDEN.get(), "void_warden");
        event.registerEntityRenderer(ModEntities.BOOMERANG.get(), ThrownItemRenderer::new);
        event.registerEntityRenderer(ModEntities.GRAPPLING_HOOK.get(), com.brasshaven.client.render.GrapplingHookRenderer::new);
        event.registerEntityRenderer(ModEntities.RIVET.get(), ctx -> new ThrownItemRenderer<>(ctx, 0.5F, false));
        event.registerEntityRenderer(ModEntities.HOT_RIVET.get(), ThrownItemRenderer::new);
        event.registerBlockEntityRenderer(ModBlockEntities.CRATE.get(), CrateRenderer::new);
        ModelRegistry.registerRenderers(event);
    }

    /** Vanilla humanoid model with the mob's painted skin, unless the mob has its own generated model. */
    private static <T extends Mob> void humanoid(EntityRenderersEvent.RegisterRenderers event, EntityType<T> type, String skin) {
        if (!ModelRegistry.NAMES.contains(skin)) {
            event.registerEntityRenderer(type, ctx -> new WayfarerMobRenderer<>(ctx, skin));
        }
    }

    private static void onClientTick() {
        com.brasshaven.client.map.ClientMap.tick();
        EldenBossBar.tick();
        TipCards.tick();
        MachineAreaPreview.tick();
        Minecraft mc = Minecraft.getInstance();
        ClientPacketListener connection = mc.getConnection();
        while (SORT_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("brasshaven sort");
            }
        }
        while (SKILLS_KEY.consumeClick()) {
            if (mc.player != null) {
                mc.gui.setScreen(new com.brasshaven.client.gui.SkillTreeScreen());
            }
        }
        while (ABILITY_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                com.brasshaven.network.BrasshavenNet.toServer(new com.brasshaven.network.SkillActionMsg(
                        com.brasshaven.network.SkillActionMsg.Action.USE_ACTIVE, ""));
            }
        }
        while (QUESTS_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                com.brasshaven.network.BrasshavenNet.toServer(new com.brasshaven.network.QuestRequestMsg(true));
            }
        }
        if (mc.player != null && mc.player.tickCount % 20 == 0) {
            QuestTracker.tick();
        }
        while (WAND_KEY.consumeClick()) {
            if (connection != null && mc.player != null && (mc.player.getMainHandItem().getItem() instanceof com.brasshaven.item.BuilderWandItem
                    || mc.player.getOffhandItem().getItem() instanceof com.brasshaven.item.BuilderWandItem)) {
                com.brasshaven.network.BrasshavenNet.toServer(new com.brasshaven.network.WandModeMsg());
            }
        }
        while (MAP_KEY.consumeClick()) {
            if (mc.player != null && mc.level != null) {
                ClientHooks.openWorldMap();
            }
        }
        while (MINIMAP_KEY.consumeClick()) {
            // H shows / hides the minimap, Shift + H steps through its four sizes
            if (mc.hasShiftDown()) {
                com.brasshaven.client.map.MinimapHud.cycleSize();
            } else {
                com.brasshaven.client.map.MinimapHud.toggle();
            }
        }
        while (MINIMAP_ZOOM_KEY.consumeClick()) {
            com.brasshaven.client.map.MinimapHud.cycleZoom();
        }
        while (PING_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                com.brasshaven.client.map.ClientMap.pingLook();
            }
        }
        while (MAGNET_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("brasshaven magnet");
            }
        }
    }
}
