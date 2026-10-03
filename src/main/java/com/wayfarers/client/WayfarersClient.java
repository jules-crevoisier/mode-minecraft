package com.wayfarers.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.wayfarers.Wayfarers;
import com.wayfarers.generated.model.ModelRegistry;
import com.wayfarers.registry.ModEntities;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.bus.BusGroup;
import org.lwjgl.glfw.GLFW;

/** Client-only wiring: entity models and renderers, the boss bars, and the two key bindings (sort, magnet). */
public final class WayfarersClient {
    private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(Wayfarers.id("main"));
    public static final KeyMapping SORT_KEY = new KeyMapping("key.wayfarers.sort_inventory",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY);
    public static final KeyMapping MAGNET_KEY = new KeyMapping("key.wayfarers.toggle_magnet",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_M, CATEGORY);

    private WayfarersClient() {}

    public static void init(BusGroup modBus) {
        EntityRenderersEvent.RegisterLayerDefinitions.BUS.addListener(ModelRegistry::registerLayers);
        EntityRenderersEvent.RegisterRenderers.BUS.addListener(WayfarersClient::registerRenderers);
        AddGuiOverlayLayersEvent.BUS.addListener(EldenBossBar::register);
        RegisterKeyMappingsEvent.BUS.addListener(event -> {
            event.register(SORT_KEY);
            event.register(MAGNET_KEY);
        });
        TickEvent.ClientTickEvent.Post.BUS.addListener(event -> onClientTick());
    }

    private static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModEntities.RUIN_WALKER.get(), ctx -> new WayfarerMobRenderer<>(ctx, "ruin_walker"));
        event.registerEntityRenderer(ModEntities.MAP_WRAITH.get(), ctx -> new WayfarerMobRenderer<>(ctx, "map_wraith"));
        event.registerEntityRenderer(ModEntities.BASALT_GUARD.get(), ctx -> new WayfarerMobRenderer<>(ctx, "basalt_guard"));
        event.registerEntityRenderer(ModEntities.VOID_STALKER.get(), ctx -> new WayfarerMobRenderer<>(ctx, "void_stalker"));
        event.registerEntityRenderer(ModEntities.VOID_WARDEN.get(), ctx -> new WayfarerMobRenderer<>(ctx, "void_warden"));
        event.registerEntityRenderer(ModEntities.BOOMERANG.get(), ThrownItemRenderer::new);
        ModelRegistry.registerRenderers(event);
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
        while (MAGNET_KEY.consumeClick()) {
            if (connection != null && mc.player != null) {
                connection.sendCommand("wayfarers magnet");
            }
        }
    }
}
