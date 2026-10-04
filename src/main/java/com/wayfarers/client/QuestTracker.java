package com.wayfarers.client;

import com.wayfarers.Wayfarers;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.config.WayfarersClientConfig;
import com.wayfarers.generated.GeneratedContent;
import com.wayfarers.network.QuestSnapshotMsg;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;

import java.util.List;

/** The tracked quest, pinned to the top-right corner of the HUD. Moves on to the next quest when done. */
public final class QuestTracker {
    private static final int W = 150;

    // the HUD is drawn every frame: word-wrap the description and build the icon once per quest (and language)
    private static String cachedKey = "";
    private static List<FormattedCharSequence> cachedDesc = List.of();
    private static String cachedTitle = "";
    private static ItemStack cachedIcon = ItemStack.EMPTY;
    private static boolean iconResolved;

    private QuestTracker() {}

    private static void refreshCache(Minecraft mc, String q) {
        String key = q + '|' + mc.getLanguageManager().getSelected() + '|' + System.identityHashCode(mc.getConnection());
        if (!key.equals(cachedKey)) {
            cachedKey = key;
            cachedDesc = mc.font.split(ClientQuests.description(q), W - 28);
            cachedTitle = ClientQuests.title(q).getString();
            iconResolved = false;
        }
        if (!iconResolved) { // the advancement tree (with the icon) may arrive after the first frames
            iconResolved = ClientQuests.display(q).isPresent();
            cachedIcon = ClientQuests.icon(q);
        }
    }

    public static void register(AddGuiOverlayLayersEvent event) {
        event.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK, Wayfarers.id("quest_tracker"),
                ForgeLayeredDraw.BOSS_OVERLAY, QuestTracker::extract);
    }

    private static void extract(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        String q = WayfarersClientConfig.TRACKED_QUEST.get();
        if (q.isEmpty() || !WayfarersClientConfig.QUEST_TRACKER.get() || mc.player == null
                || mc.gui.screen() != null) {
            return;
        }
        Font font = mc.font;
        QuestSnapshotMsg.State s = ClientQuests.state(q);
        refreshCache(mc, q);
        List<FormattedCharSequence> desc = cachedDesc;
        int lines = Math.min(desc.size(), 3);
        int h = 34 + lines * 9;
        int x = g.guiWidth() - W - 6;
        int y = 6;
        WfGui.sprite(g, WfGui.CARD, x, y, W, h);
        g.item(cachedIcon, x + 5, y + 5);
        g.text(font, Component.translatable("gui.wayfarers.quests.tracker"), x + 25, y + 4, WfGui.INK_SOFT, false);
        WfGui.textClipped(g, font, cachedTitle, x + 25, y + 13, W - 30, WfGui.INK, false);
        for (int i = 0; i < lines; i++) {
            g.text(font, desc.get(i), x + 5, y + 25 + i * 9, WfGui.INK_SOFT, false);
        }
        int by = y + h - 9;
        int bw = W - 40;
        WfGui.sprite(g, WfGui.id("bar_back"), x + 5, by, bw, 6);
        int fill = s.total() == 0 ? 0 : (bw - 2) * s.completed() / s.total();
        if (fill > 0) {
            WfGui.sprite(g, WfGui.id("bar_fill"), x + 6, by + 1, fill, 4);
        }
        g.text(font, s.completed() + "/" + s.total(), x + bw + 9, by - 1, WfGui.INK, false);
    }

    /** When the tracked quest is completed, follow the next available quest of the same chapter. */
    public static void tick() {
        String q = WayfarersClientConfig.TRACKED_QUEST.get();
        if (q.isEmpty() || !ClientQuests.done(q)) {
            return;
        }
        String next = "";
        for (GeneratedContent.Chapter c : GeneratedContent.CHAPTERS) {
            if (c.quests().contains(q)) {
                next = c.quests().stream().filter(n -> !ClientQuests.done(n) && ClientQuests.unlocked(n)).findFirst().orElse("");
            }
        }
        WayfarersClientConfig.TRACKED_QUEST.set(next);
        WayfarersClientConfig.TRACKED_QUEST.save();
    }
}
