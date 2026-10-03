package com.wayfarers.client;

import com.wayfarers.client.gui.QuestJournalScreen;
import com.wayfarers.client.gui.WaystoneScreen;
import com.wayfarers.network.QuestSnapshotMsg;
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

    public static void terminalContents(com.wayfarers.network.TerminalContentsMsg msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && mc.player.containerMenu instanceof com.wayfarers.menu.TerminalMenu menu
                && menu.containerId == msg.containerId()) {
            menu.clientContents = msg.entries();
        }
    }

    public static void openGuide(String page) {
        Minecraft.getInstance().gui.setScreen(new com.wayfarers.client.gui.GuideScreen(page));
    }

    public static void questSnapshot(QuestSnapshotMsg msg) {
        ClientQuests.update(msg);
        Minecraft mc = Minecraft.getInstance();
        if (mc.gui.screen() instanceof QuestJournalScreen journal) {
            journal.refresh(msg);
        } else if (msg.open()) {
            mc.gui.setScreen(new QuestJournalScreen());
        }
    }
}
