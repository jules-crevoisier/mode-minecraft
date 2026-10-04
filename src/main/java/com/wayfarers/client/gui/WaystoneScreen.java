package com.wayfarers.client.gui;

import com.wayfarers.network.WaystoneActionMsg;
import com.wayfarers.network.WaystoneListMsg;
import com.wayfarers.network.WayfarersNet;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.player.Player;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * Travel map opened by a waystone: every waystone the group discovered, pinned ones first, then the
 * closest ones of this dimension. Click to select, double-click (or "Travel") to warp, star to pin,
 * and rename from the details card.
 */
public class WaystoneScreen extends Screen {
    private static final int W = 300;
    private static final int H = 210;
    private static final int ROW = 20;

    private final String current;
    private final List<WaystoneListMsg.Entry> all;
    private final List<WaystoneListMsg.Entry> shown = new ArrayList<>();
    private String selected;
    private int scroll;
    private long lastClick;
    private String lastClickId = "";
    private boolean renaming;

    private int left;
    private int top;
    private EditBox search;
    private EditBox renameBox;
    private WfButton travel;
    private WfButton pin;
    private WfButton rename;

    public WaystoneScreen(WaystoneListMsg msg) {
        super(Component.translatable("gui.wayfarers.waystones.title"));
        this.current = msg.current();
        this.all = new ArrayList<>(msg.entries());
        this.all.sort(Comparator.comparing((WaystoneListMsg.Entry e) -> !e.id().equals(current))
                .thenComparing(e -> !e.pinned())
                .thenComparing(e -> !sameDimension(e))
                .thenComparingDouble(this::distance)
                .thenComparing(WaystoneListMsg.Entry::name));
        this.selected = all.stream().filter(e -> !e.id().equals(current)).map(WaystoneListMsg.Entry::id).findFirst().orElse(null);
    }

    /** Keeps the search text and selection when the server refreshes the list (after a rename or pin). */
    public WaystoneScreen withStateFrom(WaystoneScreen old) {
        if (old.selected != null && all.stream().anyMatch(e -> e.id().equals(old.selected))) {
            this.selected = old.selected;
        }
        this.scroll = old.scroll;
        this.pendingSearch = old.search != null ? old.search.getValue() : "";
        return this;
    }

    private String pendingSearch = "";

    // ------------------------------------------------------------------ layout
    private int listX() { return left + 12; }
    private int listY() { return top + 32; }
    private int listW() { return 172; }
    private int listH() { return H - 44; }
    private int visibleRows() { return (listH() - 8) / ROW; }
    private int cardX() { return listX() + listW() + 8; }
    private int cardY() { return top + 16; }
    private int cardW() { return W - listW() - 32; }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
        search = new EditBox(font, listX() + 5, listY() - 13, listW() - 10, 11, Component.translatable("gui.wayfarers.waystones.search"));
        search.setBordered(false);
        search.setMaxLength(32);
        search.setTextColor(WfGui.CREAM);
        search.setHint(Component.translatable("gui.wayfarers.waystones.search"));
        search.setValue(pendingSearch);
        search.setResponder(s -> refilter());
        addRenderableWidget(search);

        int bx = cardX() + 6;
        int bw = cardW() - 12;
        travel = addRenderableWidget(new WfButton(bx, cardY() + 92, bw, 20, Component.translatable("gui.wayfarers.waystones.travel"), b -> travel()));
        pin = addRenderableWidget(new WfButton(bx, cardY() + 116, bw, 18, Component.translatable("gui.wayfarers.waystones.pin"), b -> send(WaystoneActionMsg.Action.PIN, "")));
        rename = addRenderableWidget(new WfButton(bx, cardY() + 138, bw, 18, Component.translatable("gui.wayfarers.waystones.rename"), b -> toggleRename()));
        renameBox = new EditBox(font, bx, cardY() + 22, bw, 14, Component.translatable("gui.wayfarers.waystones.rename"));
        renameBox.setMaxLength(32);
        renameBox.setVisible(false);
        addRenderableWidget(renameBox);
        refilter();
        updateButtons();
    }

    private void refilter() {
        String q = search == null ? "" : search.getValue().toLowerCase(Locale.ROOT).strip();
        shown.clear();
        for (WaystoneListMsg.Entry e : all) {
            if (q.isEmpty() || e.name().toLowerCase(Locale.ROOT).contains(q)) {
                shown.add(e);
            }
        }
        scroll = Math.max(0, Math.min(scroll, shown.size() - visibleRows()));
    }

    private WaystoneListMsg.Entry selectedEntry() {
        if (selected == null) {
            return null;
        }
        return all.stream().filter(e -> e.id().equals(selected)).findFirst().orElse(null);
    }

    private void updateButtons() {
        WaystoneListMsg.Entry e = selectedEntry();
        boolean usable = e != null && !e.id().equals(current) && !current.isEmpty();
        travel.active = usable;
        pin.active = e != null && !current.isEmpty();
        rename.active = e != null && !current.isEmpty();
        pin.setMessage(Component.translatable(e != null && e.pinned() ? "gui.wayfarers.waystones.unpin" : "gui.wayfarers.waystones.pin"));
        rename.setMessage(Component.translatable(renaming ? "gui.wayfarers.waystones.save" : "gui.wayfarers.waystones.rename"));
        renameBox.setVisible(renaming);
    }

    // ------------------------------------------------------------------ actions
    private void send(WaystoneActionMsg.Action action, String text) {
        WaystoneListMsg.Entry e = selectedEntry();
        if (e != null) {
            WayfarersNet.toServer(new WaystoneActionMsg(action, current, e.id(), text));
        }
    }

    private void travel() {
        WaystoneListMsg.Entry e = selectedEntry();
        if (e != null && !e.id().equals(current)) {
            send(WaystoneActionMsg.Action.WARP, "");
            onClose();
        }
    }

    private void toggleRename() {
        WaystoneListMsg.Entry e = selectedEntry();
        if (e == null) {
            return;
        }
        if (renaming) {
            send(WaystoneActionMsg.Action.RENAME, renameBox.getValue());
            renaming = false;
        } else {
            renaming = true;
            renameBox.setValue(e.name());
            setFocused(renameBox);
        }
        updateButtons();
    }

    // ------------------------------------------------------------------ helpers
    private boolean sameDimension(WaystoneListMsg.Entry e) {
        Player p = Minecraft.getInstance().player;
        return p != null && p.level().dimension().identifier().getPath().equals(e.dimension());
    }

    private double distance(WaystoneListMsg.Entry e) {
        Player p = Minecraft.getInstance().player;
        if (p == null || !sameDimension(e)) {
            return Double.MAX_VALUE;
        }
        return Math.sqrt(p.distanceToSqr(e.x() + 0.5, p.getY(), e.z() + 0.5));
    }

    private static String dimIcon(String dim) {
        return switch (dim) {
            case "the_nether" -> "nether";
            case "the_end" -> "end";
            default -> "overworld";
        };
    }

    private String distanceLabel(WaystoneListMsg.Entry e) {
        if (e.id().equals(current)) {
            return Component.translatable("gui.wayfarers.waystones.here").getString();
        }
        if (!sameDimension(e)) {
            return Component.translatable("gui.wayfarers.dim." + e.dimension()).getString();
        }
        double d = distance(e);
        return d >= 1000 ? String.format(Locale.ROOT, "%.1f km", d / 1000.0) : (int) d + " m";
    }

    // ------------------------------------------------------------------ rendering
    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, W, H);
        WfGui.sprite(g, WfGui.INSET, listX(), listY() - 15, listW(), 14);
        WfGui.sprite(g, WfGui.INSET, listX(), listY(), listW(), listH());

        int rows = visibleRows();
        int rowW = listW() - 12;
        for (int i = 0; i < rows && i + scroll < shown.size(); i++) {
            WaystoneListMsg.Entry e = shown.get(i + scroll);
            int rx = listX() + 3;
            int ry = listY() + 4 + i * ROW;
            boolean hover = mouseX >= rx && mouseX < rx + rowW && mouseY >= ry && mouseY < ry + ROW - 1;
            if (e.id().equals(selected)) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, rx, ry, rowW, ROW - 1);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, rx, ry, rowW, ROW - 1);
            }
            boolean here = e.id().equals(current);
            WfGui.sprite(g, WfGui.icon(here ? "here" : dimIcon(e.dimension())), rx + 3, ry + 1, 16, 16);
            String dist = distanceLabel(e);
            int distW = font.width(dist);
            WfGui.textClipped(g, font, e.name(), rx + 22, ry + 5, rowW - 44 - distW, here ? WfGui.AETHER : WfGui.CREAM, true);
            g.text(font, dist, rx + rowW - 22 - distW, ry + 5, WfGui.CREAM_SOFT, true);
            WfGui.sprite(g, WfGui.icon(e.pinned() ? "pin" : "pin_off"), rx + rowW - 19, ry + 1, 16, 16);
        }
        if (shown.size() > rows) {
            int tx = listX() + listW() - 9;
            int ty = listY() + 3;
            int th = listH() - 6;
            WfGui.sprite(g, WfGui.SCROLL_TRACK, tx, ty, 6, th);
            int thumb = Math.max(16, th * rows / shown.size());
            int pos = (th - thumb) * scroll / Math.max(1, shown.size() - rows);
            WfGui.sprite(g, WfGui.SCROLL_THUMB, tx, ty + pos, 6, thumb);
        }
        if (all.size() <= 1) {
            g.textWithWordWrap(font, Component.translatable("gui.wayfarers.waystones.empty"), listX() + 8, listY() + 30,
                    listW() - 16, WfGui.CREAM_SOFT, true);
        }

        // details card
        WfGui.sprite(g, WfGui.CARD, cardX(), cardY(), cardW(), H - 30);
        WaystoneListMsg.Entry e = selectedEntry();
        int cx = cardX() + cardW() / 2;
        if (e != null) {
            WfGui.sprite(g, WfGui.icon(dimIcon(e.dimension())), cx - 8, cardY() + 6, 16, 16);
            if (!renaming) {
                WfGui.textClipped(g, font, e.name(), cardX() + 5, cardY() + 26, cardW() - 10, WfGui.INK, false);
            }
            WfGui.centered(g, font, Component.translatable("gui.wayfarers.dim." + e.dimension()), cx, cardY() + 40, WfGui.INK_SOFT);
            // far-off or negative coordinates are wider than the card: they wrap onto a second line
            int ty = cardY() + 52;
            for (FormattedCharSequence line : font.split(Component.translatable("gui.wayfarers.waystones.coords", e.x(), e.y(), e.z()),
                    cardW() - 8)) {
                WfGui.centered(g, font, line, cx, ty, WfGui.INK_SOFT);
                ty += 10;
            }
            if (sameDimension(e) && !e.id().equals(current)) {
                WfGui.centered(g, font, Component.translatable("gui.wayfarers.waystones.distance", (int) distance(e)), cx, ty + 2, WfGui.INK_SOFT);
            }
        }
        g.centeredText(font, Component.translatable("gui.wayfarers.waystones.hint"), left + W / 2, top + H + 4, WfGui.CREAM_SOFT);
        super.extractRenderState(g, mouseX, mouseY, a);
    }

    // ------------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x();
        double my = event.y();
        int rows = visibleRows();
        int rowW = listW() - 12;
        int rx = listX() + 3;
        for (int i = 0; i < rows && i + scroll < shown.size(); i++) {
            int ry = listY() + 4 + i * ROW;
            if (mx >= rx && mx < rx + rowW && my >= ry && my < ry + ROW - 1) {
                WaystoneListMsg.Entry e = shown.get(i + scroll);
                selected = e.id();
                renaming = false;
                if (mx >= rx + rowW - 20 && !current.isEmpty()) {
                    send(WaystoneActionMsg.Action.PIN, "");
                } else {
                    long now = System.currentTimeMillis();
                    if ((doubleClick || now - lastClick < 350) && e.id().equals(lastClickId)) {
                        travel();
                    }
                    lastClick = now;
                    lastClickId = e.id();
                }
                updateButtons();
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        int max = Math.max(0, shown.size() - visibleRows());
        scroll = (int) Math.max(0, Math.min(max, scroll - Math.signum(scrollY)));
        return true;
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (renaming && renameBox.isFocused() && (event.key() == 257 || event.key() == 335)) {
            toggleRename();
            return true;
        }
        // keyboard: up / down walk the list (even while typing in the search box), Enter travels
        if (!renaming && (event.isUp() || event.isDown()) && !shown.isEmpty()) {
            int i = 0;
            for (int k = 0; k < shown.size(); k++) {
                if (shown.get(k).id().equals(selected)) {
                    i = k + (event.isUp() ? -1 : 1);
                }
            }
            i = Math.max(0, Math.min(shown.size() - 1, i));
            selected = shown.get(i).id();
            if (i < scroll) {
                scroll = i;
            } else if (i >= scroll + visibleRows()) {
                scroll = i - visibleRows() + 1;
            }
            updateButtons();
            return true;
        }
        if (!renaming && (event.key() == 257 || event.key() == 335) && (getFocused() == null || getFocused() == search)
                && travel.active) {
            travel();
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
