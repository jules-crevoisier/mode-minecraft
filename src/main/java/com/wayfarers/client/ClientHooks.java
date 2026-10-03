package com.wayfarers.client;

import com.wayfarers.client.gui.WaystoneScreen;
import com.wayfarers.network.WaystoneListMsg;
import net.minecraft.client.Minecraft;

/** Client-only entry points called from network handlers (never loaded on a dedicated server). */
public final class ClientHooks {
    private ClientHooks() {}

    public static void openWaystones(WaystoneListMsg msg) {
        Minecraft mc = Minecraft.getInstance();
        WaystoneScreen screen = new WaystoneScreen(msg);
        if (mc.gui.screen() instanceof WaystoneScreen old) {
            screen.withStateFrom(old);
        }
        mc.gui.setScreen(screen);
    }
}
