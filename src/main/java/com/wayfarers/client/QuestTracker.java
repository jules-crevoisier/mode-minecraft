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
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;

import java.util.List;

/** The tracked quest, pinned to the top-right corner of the HUD. Moves on to the next quest when done. */
public final class QuestTracker {
    private static final int W = 150;

    private QuestTracker() {}

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
        List<FormattedCharSequence> desc = font.split(ClientQuests.description(q), W - 28);
        int lines = Math.min(desc.size(), 3);
        int h = 34 + lines * 9;
        int x = g.guiWidth() - W - 6;
        int y = 6 + effectRows(mc) * 26;
        WfGui.sprite(g, WfGui.CARD, x, y, W, h);
        g.item(ClientQuests.icon(q), x + 5, y + 5);
        g.text(font, Component.translatable("gui.wayfarers.quests.tracker"), x + 25, y + 4, WfGui.INK_SOFT, false);
        WfGui.textClipped(g, font, ClientQuests.title(q).getString(), x + 25, y + 13, W - 30, WfGui.INK, false);
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

    /**
     * Rows of status effect icons vanilla draws in the top-right corner (beneficial ones on the first row, the
     * others on the second): the card goes below them instead of covering them.
     */
    private static int effectRows(Minecraft mc) {
        boolean good = false;
        boolean bad = false;
        for (net.minecraft.world.effect.MobEffectInstance e : mc.player.getActiveEffects()) {
            if (e.showIcon()) {
                if (e.getEffect().value().isBeneficial()) {
                    good = true;
                } else {
                    bad = true;
                }
            }
        }
        return bad ? 2 : good ? 1 : 0;
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
