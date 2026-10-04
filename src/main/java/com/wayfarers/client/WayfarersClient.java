package com.wayfarers.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.wayfarers.Wayfarers;
import com.wayfarers.client.render.CrateRenderer;
import com.wayfarers.generated.model.ModelRegistry;
import com.wayfarers.registry.ModBlockEntities;
import com.wayfarers.registry.ModEntities;
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

/** Client-only wiring: entity models and renderers, HUD layers (boss bars, quest tracker) and key bindings. */
public final class WayfarersClient {
    private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(Wayfarers.id("main"));
    public static final KeyMapping SORT_KEY = new KeyMapping("key.wayfarers.sort_inventory",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY);
    public static final KeyMapping MAGNET_KEY = new KeyMapping("key.wayfarers.toggle_magnet",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_M, CATEGORY);
    public static final KeyMapping QUESTS_KEY = new KeyMapping("key.wayfarers.quests",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_J, CATEGORY);
    public static final KeyMapping SKILLS_KEY = new KeyMapping("key.wayfarers.skills",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_K, CATEGORY);
    public static final KeyMapping ABILITY_KEY = new KeyMapping("key.wayfarers.ability",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_V, CATEGORY);
    /** Builder's Wand in hand: cycle its symmetry (off, mirror X, mirror Z, both). */
    public static final KeyMapping WAND_KEY = new KeyMapping("key.wayfarers.wand_symmetry",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_G, CATEGORY);
    /** Held over an item in an inventory: opens its manual page (TipCards). */
    public static final KeyMapping MANUAL_KEY = new KeyMapping("key.wayfarers.manual_page",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_W, CATEGORY);

    private WayfarersClient() {}

    public static void init(BusGroup modBus) {
        EntityRenderersEvent.RegisterLayerDefinitions.BUS.addListener(ModelRegistry::registerLayers);
        EntityRenderersEvent.RegisterRenderers.BUS.addListener(WayfarersClient::registerRenderers);
        AddGuiOverlayLayersEvent.BUS.addListener(EldenBossBar::register);
        AddGuiOverlayLayersEvent.BUS.addListener(QuestTracker::register);
        MobHealthBars.register();
        ContainerButtons.register();
        WandPreview.register();
        StorageHighlight.register();
        net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent.getBus(modBus).addListener(event -> event.enqueueWork(() ->
                {
                    net.minecraft.client.gui.screens.MenuScreens.register(com.wayfarers.registry.ModMenus.TERMINAL.get(),
                            com.wayfarers.client.gui.TerminalScreen::new);
                    net.minecraft.client.gui.screens.MenuScreens.register(com.wayfarers.registry.ModMenus.CHISEL_TABLE.get(),
                            com.wayfarers.client.gui.ChiselTableScreen::new);
                    net.minecraft.client.gui.screens.MenuScreens.register(com.wayfarers.registry.ModMenus.MACHINE.get(),
                            com.wayfarers.client.gui.MachineScreen::new);
                }));
        AddGuiOverlayLayersEvent.BUS.addListener(TipCards::register);
        AddGuiOverlayLayersEvent.BUS.addListener(ManaHud::register);
        net.minecraftforge.event.entity.player.ItemTooltipEvent.BUS.addListener(TipCards::onTooltip);
        TipCards.registerKeys();
        // "Config" button of the mods list: the display settings in the mod's own theme
        net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext.get().registerExtensionPoint(
                net.minecraftforge.client.ConfigScreenHandler.ConfigScreenFactory.class,
                () -> new net.minecraftforge.client.ConfigScreenHandler.ConfigScreenFactory(
                        (mc, parent) -> new com.wayfarers.client.gui.SettingsScreen(parent)));
        RegisterKeyMappingsEvent.BUS.addListener(event -> {
            event.register(SORT_KEY);
            event.register(MAGNET_KEY);
            event.register(QUESTS_KEY);
            event.register(SKILLS_KEY);
            event.register(ABILITY_KEY);
            event.register(WAND_KEY);
            event.register(MANUAL_KEY);
        });
        TickEvent.ClientTickEvent.Post.BUS.addListener(event -> onClientTick());
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        humanoid(event, ModEntities.RUIN_WALKER.get(), "ruin_walker");
        humanoid(event, ModEntities.MAP_WRAITH.get(), "map_wraith");
        humanoid(event, ModEntities.BASALT_GUARD.get(), "basalt_guard");
        humanoid(event, ModEntities.VOID_STALKER.get(), "void_stalker");
        humanoid(event, ModEntities.VOID_WARDEN.get(), "void_warden");
        event.registerEntityRenderer(ModEntities.BOOMERANG.get(), ThrownItemRenderer::new);
        event.registerEntityRenderer(ModEntities.GRAPPLING_HOOK.get(), com.wayfarers.client.render.GrapplingHookRenderer::new);
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
        EldenBossBar.tick();
        TipCards.tick();
        MachineAreaPreview.tick();
        Minecraft mc = Minecraft.getInstance();
        ClientPacketListener connection = mc.getConnection();
        while (SORT_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("wayfarers sort");
            }
        }
        while (SKILLS_KEY.consumeClick()) {
            if (mc.player != null) {
                mc.gui.setScreen(new com.wayfarers.client.gui.SkillTreeScreen());
            }
        }
        while (ABILITY_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                com.wayfarers.network.WayfarersNet.toServer(new com.wayfarers.network.SkillActionMsg(
                        com.wayfarers.network.SkillActionMsg.Action.USE_ACTIVE, ""));
            }
        }
        while (QUESTS_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                com.wayfarers.network.WayfarersNet.toServer(new com.wayfarers.network.QuestRequestMsg(true));
            }
        }
        if (mc.player != null && mc.player.tickCount % 20 == 0) {
            QuestTracker.tick();
        }
        while (WAND_KEY.consumeClick()) {
            if (connection != null && mc.player != null && (mc.player.getMainHandItem().getItem() instanceof com.wayfarers.item.BuilderWandItem
                    || mc.player.getOffhandItem().getItem() instanceof com.wayfarers.item.BuilderWandItem)) {
                com.wayfarers.network.WayfarersNet.toServer(new com.wayfarers.network.WandModeMsg());
            }
        }
        while (MAGNET_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("wayfarers magnet");
            }
        }
    }
}
