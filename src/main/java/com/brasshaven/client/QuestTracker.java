package com.brasshaven.client;

import com.brasshaven.Brasshaven;
import com.brasshaven.client.gui.WfGui;
import com.brasshaven.config.BrasshavenClientConfig;
import com.brasshaven.generated.GeneratedContent;
import com.brasshaven.network.QuestSnapshotMsg;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FormattedText;
import net.minecraft.network.chat.Style;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;

import java.util.ArrayList;
import java.util.List;

/**
 * The tracked quest, pinned to the top-right corner of the HUD: a compact parchment card with the quest's icon, its
 * bold title and progress bar side by side, and the objective in dark ink under them (three lines at most, ending on
 * "..." when longer; the journal shows it whole). Moves on to the next quest when done.
 */
public final class QuestTracker {
    private static final int W = 132;
    private static final int PAD = 4;
    private static final int MAX_LINES = 3;

    // the HUD is drawn every frame: word-wrap the description and build the icon once per quest (and language)
    private static String cachedKey = "";
    private static List<String> cachedDesc = List.of();
    private static String cachedTitle = "";
    private static ItemStack cachedIcon = ItemStack.EMPTY;
    private static boolean iconResolved;

    private QuestTracker() {}

    private static void refreshCache(Minecraft mc, String q) {
        String key = q + '|' + mc.getLanguageManager().getSelected() + '|' + System.identityHashCode(mc.getConnection());
        if (!key.equals(cachedKey)) {
            cachedKey = key;
            Font font = mc.font;
            int width = W - PAD * 2;
            List<String> lines = new ArrayList<>();
            for (FormattedText line : font.getSplitter().splitLines(ClientQuests.description(q), width, Style.EMPTY)) {
                lines.add(line.getString());
            }
            if (lines.size() > MAX_LINES) {
                String last = lines.get(MAX_LINES - 1);
                lines = new ArrayList<>(lines.subList(0, MAX_LINES));
                lines.set(MAX_LINES - 1, font.plainSubstrByWidth(last, width - font.width("...")).stripTrailing() + "...");
            }
            cachedDesc = lines;
            cachedTitle = ClientQuests.title(q).getString();
            iconResolved = false;
        }
        if (!iconResolved) { // the advancement tree (with the icon) may arrive after the first frames
            iconResolved = ClientQuests.display(q).isPresent();
            cachedIcon = ClientQuests.icon(q);
        }
    }

    public static void register(AddGuiOverlayLayersEvent event) {
        event.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK, Brasshaven.id("quest_tracker"),
                ForgeLayeredDraw.BOSS_OVERLAY, QuestTracker::extract);
    }

    private static void extract(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        String q = BrasshavenClientConfig.TRACKED_QUEST.get();
        if (q.isEmpty() || !BrasshavenClientConfig.QUEST_TRACKER.get() || mc.player == null
                || mc.gui.screen() != null) {
            return;
        }
        Font font = mc.font;
        QuestSnapshotMsg.State s = ClientQuests.state(q);
        refreshCache(mc, q);
        List<String> desc = cachedDesc;
        // icon beside the bold title and the progress bar, then the objective in dark ink (no "Tracked quest" header)
        int h = PAD + 18 + desc.size() * 9 + PAD - 1;
        int x = g.guiWidth() - W - 4;
        int y = 4 + Math.max(effectRows(mc) * 26, com.brasshaven.client.map.MinimapHud.reservedTopRight());
        WfGui.sprite(g, WfGui.CARD, x, y, W, h);
        g.item(cachedIcon, x + PAD, y + PAD + 1);
        int titleW = W - PAD * 2 - 19;
        Component title = WfGui.bold(Component.literal(cachedTitle));
        if (font.width(title) > titleW) {
            title = WfGui.bold(Component.literal(font.substrByWidth(title, titleW - font.width(WfGui.bold(Component.literal("..."))))
                    .getString() + "..."));
        }
        g.text(font, title, x + PAD + 19, y + PAD, WfGui.INK, false);
        String count = s.completed() + "/" + s.total();
        int cw = font.width(count);
        int bx = x + PAD + 19;
        int bw = W - PAD * 2 - 19 - cw - 3;
        int by = y + PAD + 11;
        WfGui.sprite(g, WfGui.id("bar_back"), bx, by, bw, 6);
        int fill = s.total() == 0 ? 0 : (bw - 2) * s.completed() / s.total();
        if (fill > 0) {
            WfGui.sprite(g, WfGui.id("bar_fill"), bx + 1, by + 1, fill, 4);
        }
        g.text(font, count, x + W - PAD - cw, by - 1, WfGui.INK_SOFT, false);
        for (int i = 0; i < desc.size(); i++) {
            g.text(font, desc.get(i), x + PAD, y + PAD + 18 + i * 9, WfGui.INK, false);
        }
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
        String q = BrasshavenClientConfig.TRACKED_QUEST.get();
        if (q.isEmpty() || !ClientQuests.done(q)) {
            return;
        }
        String next = "";
        for (GeneratedContent.Chapter c : GeneratedContent.CHAPTERS) {
            if (c.quests().contains(q)) {
                next = c.quests().stream().filter(n -> !ClientQuests.done(n) && ClientQuests.unlocked(n)).findFirst().orElse("");
            }
        }
        BrasshavenClientConfig.TRACKED_QUEST.set(next);
        BrasshavenClientConfig.TRACKED_QUEST.save();
    }
}
