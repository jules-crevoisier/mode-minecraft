package com.brasshaven.client;

import com.brasshaven.client.gui.QuestJournalScreen;
import com.brasshaven.client.gui.WaystoneScreen;
import com.brasshaven.network.QuestSnapshotMsg;
import com.brasshaven.network.WaystoneListMsg;
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

    public static void terminalContents(com.brasshaven.network.TerminalContentsMsg msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && mc.player.containerMenu instanceof com.brasshaven.menu.TerminalMenu menu
                && menu.containerId == msg.containerId()) {
            menu.clientContents = msg.entries();
            menu.clientLinked = msg.linked();
            menu.clientFree = msg.freeSlots();
        }
    }

    public static void terminalLinks(com.brasshaven.network.TerminalLinksMsg msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && mc.player.containerMenu instanceof com.brasshaven.menu.TerminalMenu menu
                && menu.containerId == msg.containerId()) {
            menu.clientLinks = msg;
        }
    }

    public static void mapData(com.brasshaven.network.MapDataMsg msg) {
        com.brasshaven.client.map.ClientMap.receive(msg);
    }

    public static void openWorldMap() {
        Minecraft.getInstance().gui.setScreen(new com.brasshaven.client.map.WorldMapScreen());
    }

    public static void openGuide(String page) {
        Minecraft.getInstance().gui.setScreen(new com.brasshaven.client.gui.GuideScreen(page));
    }

    public static void npcDialog(com.brasshaven.network.NpcDialogMsg msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.gui.screen() instanceof com.brasshaven.client.gui.NpcDialogScreen open && open.entityId() == msg.entityId()) {
            open.refresh(msg);
        } else {
            mc.gui.setScreen(new com.brasshaven.client.gui.NpcDialogScreen(msg));
        }
    }

    public static void contracts(com.brasshaven.network.ContractSyncMsg msg) {
        ClientContracts.update(msg);
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
