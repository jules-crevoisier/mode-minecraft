package com.wayfarers.client.gui;

import com.wayfarers.client.ClientQuests;
import com.wayfarers.config.WayfarersClientConfig;
import com.wayfarers.generated.GeneratedContent;
import com.wayfarers.network.QuestSnapshotMsg;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * The quest journal: chapters on the left, the chapter's quests in the middle, and a parchment card
 * with the objective, progress, rewards and a "Track" button that pins the quest to the HUD.
 */
public class QuestJournalScreen extends Screen {
    private static final int W = 384;
    /** The window's height on a big screen; a small one (427 x 240) gets a shorter one. */
    private static final int MAX_H = 228;
    private static final int TAB_H = 30;
    private static final int ROW = 22;

    private int h = MAX_H;
    private int left;
    private int top;
    private int chapter;
    private String selected;
    private int scroll;
    private WfButton track;

    public QuestJournalScreen() {
        super(Component.translatable("gui.wayfarers.quests.title"));
        String tracked = WayfarersClientConfig.TRACKED_QUEST.get();
        chapter = 0;
        for (int i = 0; i < GeneratedContent.CHAPTERS.size(); i++) {
            if (GeneratedContent.CHAPTERS.get(i).quests().contains(tracked)) {
                chapter = i;
                selected = tracked;
                return;
            }
        }
        for (int i = 0; i < GeneratedContent.CHAPTERS.size(); i++) {
            int[] p = ClientQuests.chapterProgress(GeneratedContent.CHAPTERS.get(i));
            if (p[0] < p[1]) {
                chapter = i;
                break;
            }
        }
        selectDefault();
    }

    private List<String> quests() {
        return GeneratedContent.CHAPTERS.get(chapter).quests();
    }

    private void selectDefault() {
        selected = quests().stream().filter(q -> !ClientQuests.done(q) && ClientQuests.unlocked(q)).findFirst()
                .orElse(quests().isEmpty() ? null : quests().get(0));
        scroll = 0;
    }

    // ------------------------------------------------------------------ layout
    private int tabX() { return left + 12; }
    private int tabY() { return top + 22; }
    private int tabW() { return 104; }
    private int listX() { return left + 122; }
    private int listY() { return top + 22; }
    private int listW() { return 132; }
    private int listH() { return h - 34; }
    private int rows() { return (listH() - 6) / ROW; }
    private int cardX() { return left + 260; }
    private int cardY() { return top + 18; }
    private int cardW() { return W - 272; }
    private int cardH() { return h - 28; }

    @Override
    protected void init() {
        // room for the title plate above and the keyboard hint below (13 px) on a small screen
        h = Math.min(MAX_H, height - 20);
        left = (width - W) / 2;
        top = WfGui.windowTop(height, h, 13);
        scroll = Math.max(0, Math.min(scroll, quests().size() - rows()));
        track = addRenderableWidget(new WfButton(cardX() + 6, cardY() + cardH() - 26, cardW() - 12, 20,
                Component.translatable("gui.wayfarers.quests.track"), b -> toggleTrack()));
        updateTrack();
    }

    /** Called when the server pushes fresh progress while the journal is open. */
    public void refresh(QuestSnapshotMsg msg) {
        updateTrack();
    }

    private void toggleTrack() {
        if (selected == null) {
            return;
        }
        String now = WayfarersClientConfig.TRACKED_QUEST.get();
        WayfarersClientConfig.TRACKED_QUEST.set(selected.equals(now) ? "" : selected);
        WayfarersClientConfig.TRACKED_QUEST.save();
        updateTrack();
    }

    private void updateTrack() {
        if (track == null) {
            return;
        }
        boolean tracked = selected != null && selected.equals(WayfarersClientConfig.TRACKED_QUEST.get());
        track.setMessage(Component.translatable(tracked ? "gui.wayfarers.quests.untrack" : "gui.wayfarers.quests.track"));
        track.active = selected != null && !ClientQuests.done(selected) && ClientQuests.unlocked(selected);
    }

    // ------------------------------------------------------------------ rendering
    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, W, h);
        drawTabs(g, mouseX, mouseY);
        drawList(g, mouseX, mouseY);
        descCut = false;
        drawCard(g);
        // keyboard hint under the window, like the waystone screen's
        g.centeredText(font, Component.translatable("gui.wayfarers.quests.keys"), left + W / 2, top + h + 4, WfGui.CREAM);
        super.extractRenderState(g, mouseX, mouseY, a);
        hoverTips(g, mouseX, mouseY);
    }

    private boolean descCut;

    /** Tooltips: full names (rows and tabs are clipped), what the status icons mean, a long description. */
    private void hoverTips(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        List<Component> tip = new ArrayList<>();
        for (int i = 0; i < GeneratedContent.CHAPTERS.size(); i++) {
            int y = tabY() + i * (TAB_H + 4);
            if (mouseX >= tabX() && mouseX < tabX() + tabW() && mouseY >= y && mouseY < y + TAB_H) {
                GeneratedContent.Chapter c = GeneratedContent.CHAPTERS.get(i);
                int[] p = ClientQuests.chapterProgress(c);
                tip.add(Component.translatable("chapter.wayfarers." + c.id()));
                tip.add(Component.translatable("gui.wayfarers.quests.objectives", p[0], p[1]).withStyle(net.minecraft.ChatFormatting.GRAY));
            }
        }
        List<String> qs = quests();
        int rowW = listW() - 12;
        for (int i = 0; i < rows() && i + scroll < qs.size(); i++) {
            int rx = listX() + 3;
            int ry = listY() + 3 + i * ROW;
            if (mouseX >= rx && mouseX < rx + rowW && mouseY >= ry && mouseY < ry + ROW - 1) {
                String q = qs.get(i + scroll);
                tip.add(ClientQuests.hidden(q) ? Component.translatable("gui.wayfarers.quests.hidden") : ClientQuests.title(q));
                if (ClientQuests.done(q)) {
                    tip.add(Component.translatable("gui.wayfarers.quests.done").withStyle(net.minecraft.ChatFormatting.GREEN));
                } else if (!ClientQuests.unlocked(q)) {
                    String parent = ClientQuests.parent(q);
                    tip.add(Component.translatable("gui.wayfarers.quests.locked",
                            parent == null ? Component.literal("?") : ClientQuests.title(parent)).withStyle(net.minecraft.ChatFormatting.RED));
                } else {
                    QuestSnapshotMsg.State s = ClientQuests.state(q);
                    tip.add(Component.translatable("gui.wayfarers.quests.objectives", s.completed(), s.total())
                            .withStyle(net.minecraft.ChatFormatting.GRAY));
                }
                if (q.equals(WayfarersClientConfig.TRACKED_QUEST.get())) {
                    tip.add(Component.translatable("gui.wayfarers.quests.tracker").withStyle(net.minecraft.ChatFormatting.GOLD));
                }
            }
        }
        if (descCut && selected != null && mouseX >= cardX() && mouseX < cardX() + cardW() && mouseY >= cardY() + 26
                && mouseY < cardY() + cardH() - 56) {
            g.setTooltipForNextFrame(font, font.split(ClientQuests.description(selected), 220), mouseX, mouseY);
            return;
        }
        if (!tip.isEmpty()) {
            g.setComponentTooltipForNextFrame(font, tip, mouseX, mouseY);
        }
    }

    private void drawTabs(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        for (int i = 0; i < GeneratedContent.CHAPTERS.size(); i++) {
            GeneratedContent.Chapter c = GeneratedContent.CHAPTERS.get(i);
            int x = tabX();
            int y = tabY() + i * (TAB_H + 4);
            boolean hover = mouseX >= x && mouseX < x + tabW() && mouseY >= y && mouseY < y + TAB_H;
            WfGui.sprite(g, WfGui.INSET, x, y, tabW(), TAB_H);
            if (i == chapter) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, x + 2, y + 2, tabW() - 4, TAB_H - 4);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, x + 2, y + 2, tabW() - 4, TAB_H - 4);
            }
            if (!c.quests().isEmpty()) {
                g.item(ClientQuests.icon(c.quests().get(0)), x + 4, y + 4);
            }
            WfGui.textClipped(g, font, Component.translatable("chapter.wayfarers." + c.id()).getString(), x + 23, y + 5,
                    tabW() - 27, i == chapter ? WfGui.GOLD : WfGui.CREAM, true);
            int[] p = ClientQuests.chapterProgress(c);
            int bw = tabW() - 30;
            WfGui.sprite(g, WfGui.id("bar_back"), x + 23, y + 18, bw, 6);
            int fill = p[1] == 0 ? 0 : (bw - 2) * p[0] / p[1];
            if (fill > 0) {
                WfGui.sprite(g, WfGui.id(p[0] == p[1] ? "bar_done" : "bar_fill"), x + 24, y + 19, fill, 4);
            }
        }
    }

    private void drawList(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        WfGui.sprite(g, WfGui.INSET, listX(), listY(), listW(), listH());
        List<String> qs = quests();
        int rowW = listW() - 12;
        for (int i = 0; i < rows() && i + scroll < qs.size(); i++) {
            String q = qs.get(i + scroll);
            int rx = listX() + 3;
            int ry = listY() + 3 + i * ROW;
            boolean hover = mouseX >= rx && mouseX < rx + rowW && mouseY >= ry && mouseY < ry + ROW - 1;
            if (q.equals(selected)) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, rx, ry, rowW, ROW - 1);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, rx, ry, rowW, ROW - 1);
            }
            boolean done = ClientQuests.done(q);
            boolean unlocked = ClientQuests.unlocked(q);
            boolean hidden = ClientQuests.hidden(q);
            if (!hidden) {
                g.item(ClientQuests.icon(q), rx + 2, ry + 2);
            }
            String name = hidden ? "???" : ClientQuests.title(q).getString();
            int color = done ? 0xFFA6F07A : unlocked ? WfGui.CREAM : WfGui.MUTED;
            WfGui.textClipped(g, font, name, rx + 21, ry + 7, rowW - 40, color, true);
            String status = done ? "done" : !unlocked ? "lock" : ClientQuests.state(q).completed() > 0 ? "progress" : null;
            if (status != null) {
                WfGui.sprite(g, WfGui.icon(status), rx + rowW - 18, ry + 2, 16, 16);
            }
            if (q.equals(WayfarersClientConfig.TRACKED_QUEST.get())) {
                WfGui.sprite(g, WfGui.icon("track"), rx + rowW - 34, ry + 2, 16, 16);
            }
        }
        if (qs.size() > rows()) {
            int tx = listX() + listW() - 9;
            int ty = listY() + 3;
            int th = listH() - 6;
            WfGui.sprite(g, WfGui.SCROLL_TRACK, tx, ty, 6, th);
            int thumb = Math.max(16, th * rows() / qs.size());
            int pos = (th - thumb) * scroll / Math.max(1, qs.size() - rows());
            WfGui.sprite(g, WfGui.SCROLL_THUMB, tx, ty + pos, 6, thumb);
        }
    }

    private void drawCard(GuiGraphicsExtractor g) {
        int x = cardX();
        int y = cardY();
        int w = cardW();
        WfGui.sprite(g, WfGui.CARD, x, y, w, cardH());
        if (selected == null) {
            return;
        }
        String q = selected;
        boolean hidden = ClientQuests.hidden(q);
        boolean done = ClientQuests.done(q);
        boolean unlocked = ClientQuests.unlocked(q);
        g.item(ClientQuests.icon(q), x + w / 2 - 8, y + 6);
        int ty = y + 26;
        Component name = WfGui.bold(hidden ? Component.translatable("gui.wayfarers.quests.hidden") : ClientQuests.title(q));
        for (FormattedCharSequence line : font.split(name, w - 10)) {
            WfGui.centered(g, font, line, x + w / 2, ty, WfGui.INK);
            ty += 10;
        }
        ty += 3;
        if (!hidden) {
            List<FormattedCharSequence> desc = font.split(ClientQuests.description(q), w - 10);
            for (int i = 0; i < Math.min(desc.size(), 6); i++) {
                if (i == 5 && desc.size() > 6) {
                    // a long (often French) description: end on "..." and show the whole text on hover
                    g.text(font, "...", x + 5, ty, WfGui.INK, false);
                    descCut = true;
                } else {
                    g.text(font, desc.get(i), x + 5, ty, WfGui.INK, false);
                }
                ty += 9;
            }
        }
        ty += 4;
        if (done) {
            WfGui.centered(g, font, WfGui.bold(Component.translatable("gui.wayfarers.quests.done")), x + w / 2, ty, WfGui.INK_GREEN);
        } else if (!unlocked) {
            String parent = ClientQuests.parent(q);
            Component pn = parent == null ? Component.literal("?") : ClientQuests.title(parent);
            for (FormattedCharSequence line : font.split(Component.translatable("gui.wayfarers.quests.locked", pn), w - 10)) {
                g.text(font, line, x + 5, ty, WfGui.INK_RED, false);
                ty += 9;
            }
        } else {
            QuestSnapshotMsg.State s = ClientQuests.state(q);
            g.text(font, Component.translatable("gui.wayfarers.quests.objectives", s.completed(), s.total()), x + 5, ty, WfGui.INK, false);
            ty += 10;
            int bw = w - 10;
            WfGui.sprite(g, WfGui.id("bar_back"), x + 5, ty, bw, 6);
            int fill = s.total() == 0 ? 0 : (bw - 2) * s.completed() / s.total();
            if (fill > 0) {
                WfGui.sprite(g, WfGui.id("bar_fill"), x + 6, ty + 1, fill, 4);
            }
        }
        // rewards
        String reward = GeneratedContent.REWARDS.getOrDefault(q, "0|");
        String[] parts = reward.split("\\|", -1);
        int xp = Integer.parseInt(parts[0]);
        List<ItemStack> items = new ArrayList<>();
        if (parts.length > 1 && !parts[1].isEmpty()) {
            for (String it : parts[1].split(";")) {
                String[] ic = it.split("\\*");
                BuiltInRegistries.ITEM.getOptional(Identifier.parse(ic[0]))
                        .ifPresent(item -> items.add(new ItemStack(item, Integer.parseInt(ic[1]))));
            }
        }
        if (xp > 0 || !items.isEmpty()) {
            int ry = cardY() + cardH() - 52;
            g.text(font, WfGui.bold(Component.translatable("gui.wayfarers.quests.rewards")), x + 5, ry, WfGui.INK, false);
            int ix = x + 5;
            ry += 10;
            if (xp > 0) {
                WfGui.sprite(g, WfGui.icon("xp"), ix, ry, 16, 16);
                g.text(font, String.valueOf(xp), ix + 16, ry + 5, WfGui.INK_GREEN, false);
                ix += 22 + font.width(String.valueOf(xp));
            }
            for (ItemStack stack : items) {
                if (ix + 16 > x + w - 4) {
                    break;
                }
                g.item(stack, ix, ry);
                g.itemDecorations(font, stack, ix, ry);
                ix += 18;
            }
        }
    }

    // ------------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x();
        double my = event.y();
        for (int i = 0; i < GeneratedContent.CHAPTERS.size(); i++) {
            int y = tabY() + i * (TAB_H + 4);
            if (mx >= tabX() && mx < tabX() + tabW() && my >= y && my < y + TAB_H) {
                chapter = i;
                selectDefault();
                updateTrack();
                return true;
            }
        }
        List<String> qs = quests();
        int rowW = listW() - 12;
        for (int i = 0; i < rows() && i + scroll < qs.size(); i++) {
            int rx = listX() + 3;
            int ry = listY() + 3 + i * ROW;
            if (mx >= rx && mx < rx + rowW && my >= ry && my < ry + ROW - 1) {
                selected = qs.get(i + scroll);
                if (doubleClick && track.active) {
                    toggleTrack();
                }
                updateTrack();
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        int max = Math.max(0, quests().size() - rows());
        scroll = (int) Math.max(0, Math.min(max, scroll - Math.signum(scrollY)));
        return true;
    }

    /**
     * Keyboard: up / down pick a quest, left / right a chapter, Enter tracks the quest, and the journal key (J)
     * closes the journal like it opened it.
     */
    @Override
    public boolean keyPressed(net.minecraft.client.input.KeyEvent event) {
        if (com.wayfarers.client.WayfarersClient.QUESTS_KEY.matches(event)) {
            onClose();
            return true;
        }
        List<String> qs = quests();
        int key = event.key();
        if (event.isUp() || event.isDown()) {
            if (!qs.isEmpty()) {
                int i = selected == null ? -1 : qs.indexOf(selected);
                i = Math.max(0, Math.min(qs.size() - 1, i + (event.isUp() ? -1 : 1)));
                selected = qs.get(i);
                if (i < scroll) {
                    scroll = i;
                } else if (i >= scroll + rows()) {
                    scroll = i - rows() + 1;
                }
                updateTrack();
            }
            return true;
        }
        if (event.isLeft() || event.isRight()) {
            int c = Math.max(0, Math.min(GeneratedContent.CHAPTERS.size() - 1, chapter + (event.isLeft() ? -1 : 1)));
            if (c != chapter) {
                chapter = c;
                selectDefault();
                updateTrack();
            }
            return true;
        }
        if ((key == 257 || key == 335) && track.active && getFocused() == null) {
            toggleTrack();
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
