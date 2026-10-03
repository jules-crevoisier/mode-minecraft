package com.wayfarers.client.gui;

import com.wayfarers.menu.TerminalMenu;
import com.wayfarers.network.TerminalClickMsg;
import com.wayfarers.network.WayfarersNet;
import com.wayfarers.util.StorageNetwork;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * Guild Terminal: one searchable grid with everything stored in the chests around (12 blocks).
 * Click to take a stack, right-click half, middle-click one, shift-click straight into your inventory;
 * click with an item on the cursor (or shift-click your inventory) to store it.
 */
public class TerminalScreen extends AbstractContainerScreen<TerminalMenu> {
    private static final int COLS = 9;
    private static final int ROWS = 5;
    private static final int GRID_X = 17;
    private static final int GRID_Y = 32;

    private EditBox search;
    private boolean byName;
    private int scroll;
    private final List<StorageNetwork.Entry> shown = new ArrayList<>();

    public TerminalScreen(TerminalMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, 196, 226);
    }

    @Override
    protected void init() {
        super.init();
        search = new EditBox(font, leftPos + 19, topPos + 17, 120, 11, Component.translatable("gui.wayfarers.storage.search"));
        search.setBordered(false);
        search.setTextColor(WfGui.CREAM);
        search.setHint(Component.translatable("gui.wayfarers.storage.search"));
        search.setMaxLength(32);
        addRenderableWidget(search);
        addRenderableWidget(new WfButton(leftPos + 146, topPos + 15, 36, 14, Component.translatable("gui.wayfarers.terminal.sort"),
                b -> byName = !byName));
        addRenderableWidget(new WfButton(leftPos + 15, topPos + 125, 80, 14, Component.translatable("gui.wayfarers.terminal.store_all"),
                b -> WayfarersNet.toServer(new TerminalClickMsg(TerminalClickMsg.Action.STORE_ALL, ItemStack.EMPTY))));
        addRenderableWidget(new WfButton(leftPos + 99, topPos + 125, 82, 14, Component.translatable("gui.wayfarers.terminal.store_matching"),
                b -> WayfarersNet.toServer(new TerminalClickMsg(TerminalClickMsg.Action.STORE_MATCHING, ItemStack.EMPTY))));
    }

    private void refresh() {
        shown.clear();
        String q = search == null ? "" : search.getValue().toLowerCase(Locale.ROOT).strip();
        for (StorageNetwork.Entry e : menu.clientContents) {
            if (q.isEmpty() || e.type().getHoverName().getString().toLowerCase(Locale.ROOT).contains(q)
                    || BuiltInRegistries.ITEM.getKey(e.type().getItem()).getPath().replace('_', ' ').contains(q)) {
                shown.add(e);
            }
        }
        if (byName) {
            shown.sort(Comparator.comparing(e -> e.type().getHoverName().getString()));
        }
        int maxScroll = Math.max(0, (shown.size() + COLS - 1) / COLS - ROWS);
        scroll = Math.max(0, Math.min(scroll, maxScroll));
    }

    private static String shortCount(int n) {
        if (n < 1000) {
            return String.valueOf(n);
        }
        if (n < 100_000) {
            return String.format(Locale.ROOT, "%.1fk", n / 1000.0).replace(".0k", "k");
        }
        return (n / 1000) + "k";
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        WfGui.window(g, font, title, leftPos, topPos, imageWidth, imageHeight);
        WfGui.sprite(g, WfGui.INSET, leftPos + 15, topPos + 14, 128, 15);
        WfGui.sprite(g, WfGui.INSET, leftPos + GRID_X - 3, topPos + GRID_Y - 3, COLS * 18 + 6, ROWS * 18 + 6);
        WfGui.sprite(g, WfGui.SCROLL_TRACK, leftPos + GRID_X + COLS * 18 + 5, topPos + GRID_Y - 2, 6, ROWS * 18 + 4);
        for (Slot slot : menu.slots) {
            WfGui.sprite(g, WfGui.INSET, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        // the title is on the brass plate; no inventory label
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        refresh();
        super.extractRenderState(g, mouseX, mouseY, a);
        StorageNetwork.Entry hovered = null;
        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                int i = (scroll + r) * COLS + c;
                if (i >= shown.size()) {
                    break;
                }
                StorageNetwork.Entry e = shown.get(i);
                int x = leftPos + GRID_X + c * 18;
                int y = topPos + GRID_Y + r * 18;
                g.item(e.type(), x, y);
                g.itemDecorations(font, e.type(), x, y, shortCount(e.count()));
                if (mouseX >= x && mouseX < x + 16 && mouseY >= y && mouseY < y + 16) {
                    g.fill(x, y, x + 16, y + 16, 0x60FFFFFF);
                    hovered = e;
                }
            }
        }
        int rows = (shown.size() + COLS - 1) / COLS;
        if (rows > ROWS) {
            int th = ROWS * 18 + 4;
            int thumb = Math.max(12, th * ROWS / rows);
            int pos = (th - thumb) * scroll / Math.max(1, rows - ROWS);
            WfGui.sprite(g, WfGui.SCROLL_THUMB, leftPos + GRID_X + COLS * 18 + 5, topPos + GRID_Y - 2 + pos, 6, thumb);
        }
        if (menu.clientContents.isEmpty()) {
            g.textWithWordWrap(font, Component.translatable("gui.wayfarers.terminal.empty", StorageNetwork.RANGE),
                    leftPos + GRID_X + 4, topPos + GRID_Y + 24, COLS * 18 - 8, WfGui.CREAM_SOFT, true);
        }
        if (hovered != null && menu.getCarried().isEmpty()) {
            g.setTooltipForNextFrame(font, hovered.type(), mouseX, mouseY);
        } else {
            extractTooltip(g, mouseX, mouseY);
        }
    }

    private StorageNetwork.Entry entryAt(double mx, double my) {
        int c = (int) Math.floor((mx - leftPos - GRID_X) / 18);
        int r = (int) Math.floor((my - topPos - GRID_Y) / 18);
        if (c < 0 || c >= COLS || r < 0 || r >= ROWS) {
            return null;
        }
        int i = (scroll + r) * COLS + c;
        return i < shown.size() ? shown.get(i) : null;
    }

    private boolean inGrid(double mx, double my) {
        return mx >= leftPos + GRID_X && mx < leftPos + GRID_X + COLS * 18 && my >= topPos + GRID_Y && my < topPos + GRID_Y + ROWS * 18;
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (inGrid(event.x(), event.y())) {
            if (!menu.getCarried().isEmpty()) {
                WayfarersNet.toServer(new TerminalClickMsg(TerminalClickMsg.Action.STORE_CARRIED, ItemStack.EMPTY));
                return true;
            }
            StorageNetwork.Entry e = entryAt(event.x(), event.y());
            if (e != null) {
                TerminalClickMsg.Action action = switch (event.button()) {
                    case 1 -> TerminalClickMsg.Action.TAKE_HALF;
                    case 2 -> TerminalClickMsg.Action.TAKE_ONE;
                    default -> event.hasShiftDown() ? TerminalClickMsg.Action.TAKE_TO_INVENTORY : TerminalClickMsg.Action.TAKE_STACK;
                };
                WayfarersNet.toServer(new TerminalClickMsg(action, e.type()));
            }
            return true;
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (inGrid(x, y)) {
            int rows = (shown.size() + COLS - 1) / COLS;
            scroll = (int) Math.max(0, Math.min(Math.max(0, rows - ROWS), scroll - Math.signum(scrollY)));
            return true;
        }
        return super.mouseScrolled(x, y, scrollX, scrollY);
    }

    @Override
    public boolean keyPressed(net.minecraft.client.input.KeyEvent event) {
        // typing in the search box must not close the screen with the inventory key
        if (search.isFocused() && !event.isEscape()) {
            return search.keyPressed(event) || true;
        }
        return super.keyPressed(event);
    }
}
