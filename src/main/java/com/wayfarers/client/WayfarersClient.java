package com.wayfarers.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.wayfarers.Wayfarers;
import com.wayfarers.generated.model.ModelRegistry;
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

    private WayfarersClient() {}

    public static void init(BusGroup modBus) {
        EntityRenderersEvent.RegisterLayerDefinitions.BUS.addListener(ModelRegistry::registerLayers);
        EntityRenderersEvent.RegisterRenderers.BUS.addListener(WayfarersClient::registerRenderers);
        AddGuiOverlayLayersEvent.BUS.addListener(EldenBossBar::register);
        AddGuiOverlayLayersEvent.BUS.addListener(QuestTracker::register);
        MobHealthBars.register();
        RegisterKeyMappingsEvent.BUS.addListener(event -> {
            event.register(SORT_KEY);
            event.register(MAGNET_KEY);
            event.register(QUESTS_KEY);
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
        Minecraft mc = Minecraft.getInstance();
        ClientPacketListener connection = mc.getConnection();
        while (SORT_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("wayfarers sort");
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
        while (MAGNET_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("wayfarers magnet");
            }
        }
    }
}
