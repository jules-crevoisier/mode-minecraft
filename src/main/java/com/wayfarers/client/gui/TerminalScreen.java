package com.wayfarers.client.gui;

import com.wayfarers.client.StorageHighlight;
import com.wayfarers.menu.TerminalMenu;
import com.wayfarers.network.TerminalClickMsg;
import com.wayfarers.network.TerminalLinksMsg;
import com.wayfarers.network.TerminalToggleMsg;
import com.wayfarers.network.WayfarersNet;
import com.wayfarers.util.StorageNetwork;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Guild Terminal: one searchable grid with everything stored in the base (the terminal's reach plus its Storage
 * Relays). Click to take a stack, right-click half, middle-click one, shift-click straight into your inventory; click
 * with an item on the cursor (or shift-click your inventory) to store it. The Network page lists the linked
 * containers by type: click one to exclude it (or include it again), "Show in world" outlines them all.
 */
public class TerminalScreen extends AbstractContainerScreen<TerminalMenu> {
    private static final int COLS = 9;
    private static final int ROWS = 5;
    private static final int GRID_X = 17;
    private static final int GRID_Y = 32;
    private static final int STATUS_Y = 126;
    private static final int BUTTONS_Y = 136;
    /**
     * 8 px of frame under the hotbar, like the machine screens: 235 px, the most a 240 px tall screen (1280 x 720 at
     * GUI scale 3) can show with the title plate 5 px above.
     */
    private static final int HEIGHT = TerminalMenu.INV_Y + 83;

    private enum Sort { COUNT, NAME, MOD }

    /** A line of the Network page: a group header (info == null) or one linked container. */
    private record Row(TerminalLinksMsg.Info info, Component label, double distance) {}

    // remembered while the game runs, like the creative inventory's search
    private static Sort sort = Sort.COUNT;
    private static boolean networkPage;

    private EditBox search;
    private WfButton sortButton;
    private WfButton networkButton;
    private final List<WfButton> itemButtons = new ArrayList<>();
    private final List<WfButton> networkButtons = new ArrayList<>();
    private int scroll;
    private int linkScroll;
    private final List<StorageNetwork.Entry> shown = new ArrayList<>();
    private List<StorageNetwork.Entry> shownFrom;
    private String shownQuery;
    private Sort shownSort;
    private final List<Row> rows = new ArrayList<>();
    private TerminalLinksMsg rowsFrom;

    public TerminalScreen(TerminalMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, 196, HEIGHT);
    }

    @Override
    protected void init() {
        super.init();
        topPos = WfGui.windowTop(height, imageHeight, 0);
        itemButtons.clear();
        networkButtons.clear();
        search = new EditBox(font, leftPos + 19, topPos + 17, 96, 11, Component.translatable("gui.wayfarers.storage.search"));
        search.setBordered(false);
        search.setTextColor(WfGui.CREAM);
        search.setHint(Component.translatable("gui.wayfarers.storage.search"));
        search.setMaxLength(32);
        addRenderableWidget(search);
        sortButton = addRenderableWidget(new WfButton(leftPos + 122, topPos + 15, 38, 14, sortLabel(), b -> {
            sort = Sort.values()[(sort.ordinal() + 1) % Sort.values().length];
            b.setMessage(sortLabel());
        }));
        sortButton.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.terminal.sort.tip")));
        networkButton = addRenderableWidget(new WfButton(leftPos + 163, topPos + 15, 20, 14, Component.empty(), b -> {
            networkPage = !networkPage;
        }));
        networkButton.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.terminal.network.tip")));
        // widths fit the French labels ("Tout ranger", "Ranger identiques") without scrolling text
        itemButtons.add(addRenderableWidget(new WfButton(leftPos + 15, topPos + BUTTONS_Y, 66, 14,
                Component.translatable("gui.wayfarers.terminal.store_all"),
                b -> WayfarersNet.toServer(new TerminalClickMsg(TerminalClickMsg.Action.STORE_ALL, ItemStack.EMPTY)))));
        itemButtons.add(addRenderableWidget(new WfButton(leftPos + 85, topPos + BUTTONS_Y, 96, 14,
                Component.translatable("gui.wayfarers.terminal.store_matching"),
                b -> WayfarersNet.toServer(new TerminalClickMsg(TerminalClickMsg.Action.STORE_MATCHING, ItemStack.EMPTY)))));
        WfButton show = addRenderableWidget(new WfButton(leftPos + 15, topPos + BUTTONS_Y, 100, 14,
                Component.translatable("gui.wayfarers.terminal.show"), b -> {
                    if (menu.clientLinks != null) {
                        StorageHighlight.show(menu.clientLinks);
                        onClose();
                    }
                }));
        show.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.terminal.show.tip")));
        networkButtons.add(show);
        networkButtons.add(addRenderableWidget(new WfButton(leftPos + 119, topPos + BUTTONS_Y, 62, 14,
                Component.translatable("gui.wayfarers.terminal.back"), b -> networkPage = false)));
        updatePage();
    }

    private static Component sortLabel() {
        return Component.translatable("gui.wayfarers.terminal.sort." + sort.name().toLowerCase(Locale.ROOT));
    }

    private void updatePage() {
        for (WfButton b : itemButtons) {
            b.visible = !networkPage;
        }
        for (WfButton b : networkButtons) {
            b.visible = networkPage;
        }
        search.visible = !networkPage;
        sortButton.visible = !networkPage;
        if (networkPage && search.isFocused()) {
            search.setFocused(false);
        }
    }

    // ------------------------------------------------------------------ items page
    private void refresh() {
        // filtering and sorting thousands of entries every frame is costly: only redo it when something changed
        String q = search == null ? "" : search.getValue().toLowerCase(Locale.ROOT).strip();
        if (menu.clientContents == shownFrom && q.equals(shownQuery) && sort == shownSort) {
            return;
        }
        shownFrom = menu.clientContents;
        shownQuery = q;
        shownSort = sort;
        shown.clear();
        boolean byMod = q.startsWith("@");
        String needle = byMod ? q.substring(1) : q;
        for (StorageNetwork.Entry e : menu.clientContents) {
            var key = BuiltInRegistries.ITEM.getKey(e.type().getItem());
            boolean match = needle.isEmpty() || (byMod ? key.getNamespace().contains(needle)
                    : e.type().getHoverName().getString().toLowerCase(Locale.ROOT).contains(needle)
                    || key.getPath().replace('_', ' ').contains(needle));
            if (match) {
                shown.add(e);
            }
        }
        // the server sends them most plentiful first
        Comparator<StorageNetwork.Entry> byName = Comparator.comparing(e -> e.type().getHoverName().getString());
        if (sort == Sort.NAME) {
            shown.sort(byName);
        } else if (sort == Sort.MOD) {
            shown.sort(Comparator.<StorageNetwork.Entry, String>comparing(
                    e -> BuiltInRegistries.ITEM.getKey(e.type().getItem()).getNamespace()).thenComparing(byName));
        }
        int maxScroll = Math.max(0, (shown.size() + COLS - 1) / COLS - ROWS);
        scroll = Math.max(0, Math.min(scroll, maxScroll));
    }

    /** 999, 1.2k, 45k, 1.2M. */
    public static String shortCount(long n) {
        if (n < 1000) {
            return String.valueOf(n);
        }
        if (n < 100_000) {
            return String.format(Locale.ROOT, "%.1fk", n / 1000.0).replace(".0k", "k");
        }
        if (n < 1_000_000) {
            return (n / 1000) + "k";
        }
        return String.format(Locale.ROOT, "%.1fM", n / 1_000_000.0).replace(".0M", "M");
    }

    // ------------------------------------------------------------------ network page
    private void buildRows() {
        TerminalLinksMsg links = menu.clientLinks;
        if (links == rowsFrom) {
            return;
        }
        rowsFrom = links;
        rows.clear();
        if (links == null) {
            return;
        }
        Map<Item, List<TerminalLinksMsg.Info>> groups = new LinkedHashMap<>();
        for (TerminalLinksMsg.Info info : links.links()) {
            groups.computeIfAbsent(info.icon().getItem(), k -> new ArrayList<>()).add(info);
        }
        List<Map.Entry<Item, List<TerminalLinksMsg.Info>>> sorted = new ArrayList<>(groups.entrySet());
        sorted.sort(Comparator.comparing(e -> e.getValue().get(0).icon().getHoverName().getString()));
        var terminal = menu.pos();
        for (var group : sorted) {
            List<TerminalLinksMsg.Info> list = group.getValue();
            rows.add(new Row(null, Component.translatable("gui.wayfarers.terminal.group",
                    list.get(0).icon().getHoverName(), list.size()), 0));
            for (TerminalLinksMsg.Info info : list) {
                Component name = info.doubled()
                        ? Component.translatable("gui.wayfarers.terminal.double", info.icon().getHoverName())
                        : info.icon().getHoverName();
                rows.add(new Row(info, name, Math.sqrt(info.pos().distSqr(terminal))));
            }
        }
    }

    private int maxLinkScroll() {
        return Math.max(0, rows.size() - ROWS);
    }

    private Row rowAt(double mx, double my) {
        if (mx < leftPos + GRID_X || mx >= leftPos + GRID_X + COLS * 18 || my < topPos + GRID_Y || my >= topPos + GRID_Y + ROWS * 18) {
            return null;
        }
        int i = linkScroll + (int) ((my - topPos - GRID_Y) / 18);
        return i < rows.size() ? rows.get(i) : null;
    }

    // ------------------------------------------------------------------ drawing
    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        WfGui.window(g, font, title, leftPos, topPos, imageWidth, imageHeight);
        if (!networkPage) {
            WfGui.sprite(g, WfGui.INSET, leftPos + 15, topPos + 14, 104, 15);
        }
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
        updatePage();
        if (networkPage) {
            buildRows();
            linkScroll = Math.max(0, Math.min(linkScroll, maxLinkScroll()));
        } else {
            refresh();
        }
        super.extractRenderState(g, mouseX, mouseY, a);
        WfGui.sprite(g, WfGui.icon("network"), networkButton.getX() + 2, networkButton.getY() - 1, 16, 16);
        if (networkPage) {
            renderNetwork(g, mouseX, mouseY);
        } else {
            renderItems(g, mouseX, mouseY);
        }
    }

    private void scrollbar(GuiGraphicsExtractor g, int total, int visible, int offset) {
        if (total > visible) {
            int th = ROWS * 18 + 4;
            int thumb = Math.max(12, th * visible / total);
            int pos = (th - thumb) * offset / Math.max(1, total - visible);
            WfGui.sprite(g, WfGui.SCROLL_THUMB, leftPos + GRID_X + COLS * 18 + 5, topPos + GRID_Y - 2 + pos, 6, thumb);
        }
    }

    private void renderItems(GuiGraphicsExtractor g, int mouseX, int mouseY) {
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
        scrollbar(g, (shown.size() + COLS - 1) / COLS, ROWS, scroll);
        if (menu.clientContents.isEmpty()) {
            int range = menu.clientLinks != null ? menu.clientLinks.range() : 48;
            Component msg = menu.clientLinked > 0 ? Component.translatable("gui.wayfarers.terminal.all_empty")
                    : Component.translatable("gui.wayfarers.terminal.empty", range);
            g.textWithWordWrap(font, msg, leftPos + GRID_X + 4, topPos + GRID_Y + 18, COLS * 18 - 8, WfGui.CREAM_SOFT, true);
        }
        Component status = Component.translatable("gui.wayfarers.terminal.status", menu.clientLinked, shortCount(menu.clientFree));
        WfGui.textClipped(g, font, status.getString(), leftPos + GRID_X, topPos + STATUS_Y, COLS * 18 + 10,
                menu.clientFree == 0 && menu.clientLinked > 0 ? 0xFFB0302A : WfGui.INK_SOFT, false);
        if (hovered != null && menu.getCarried().isEmpty()) {
            List<Component> lines = new ArrayList<>(getTooltipFromContainerItem(hovered.type()));
            lines.add(Component.translatable("gui.wayfarers.terminal.stored", String.format(Locale.ROOT, "%,d", hovered.count()))
                    .withStyle(ChatFormatting.GOLD));
            g.setTooltipForNextFrame(font, lines, hovered.type().getTooltipImage(), mouseX, mouseY);
        } else {
            extractTooltip(g, mouseX, mouseY);
        }
    }

    private void renderNetwork(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        TerminalLinksMsg links = menu.clientLinks;
        g.text(font, Component.translatable("gui.wayfarers.terminal.network"), leftPos + 18, topPos + 18, WfGui.GOLD, false);
        Row hovered = rowAt(mouseX, mouseY);
        for (int r = 0; r < ROWS; r++) {
            int i = linkScroll + r;
            if (i >= rows.size()) {
                break;
            }
            Row row = rows.get(i);
            int x = leftPos + GRID_X;
            int y = topPos + GRID_Y + r * 18;
            if (row.info == null) {
                WfGui.textClipped(g, font, row.label.getString(), x + 2, y + 5, COLS * 18 - 4, WfGui.GOLD, false);
                g.fill(x + 1, y + 15, x + COLS * 18 - 1, y + 16, 0x40F6C343);
                continue;
            }
            boolean excluded = row.info.excluded();
            if (row == hovered) {
                WfGui.sprite(g, WfGui.ROW_HOVER, x, y, COLS * 18, 18);
            }
            g.item(row.info.icon(), x + 1, y + 1);
            String dist = Math.round(row.distance) + " m";
            int distW = font.width(dist);
            WfGui.textClipped(g, font, row.label.getString(), x + 20, y + 5, COLS * 18 - 42 - distW,
                    excluded ? 0xFF8A7D6A : WfGui.CREAM, false);
            g.text(font, dist, x + COLS * 18 - 20 - distW, y + 5, WfGui.CREAM_SOFT, false);
            WfGui.sprite(g, WfGui.icon(excluded ? "excluded" : "done"), x + COLS * 18 - 18, y + 1, 16, 16);
        }
        scrollbar(g, rows.size(), ROWS, linkScroll);
        if (links == null || links.links().isEmpty()) {
            int range = links != null ? links.range() : 48;
            g.textWithWordWrap(font, Component.translatable("gui.wayfarers.terminal.empty", range),
                    leftPos + GRID_X + 4, topPos + GRID_Y + 18, COLS * 18 - 8, WfGui.CREAM_SOFT, true);
        }
        if (links != null) {
            Component status = Component.translatable("gui.wayfarers.terminal.network_status", menu.clientLinked,
                    links.relays(), links.range());
            WfGui.textClipped(g, font, status.getString(), leftPos + GRID_X, topPos + STATUS_Y, COLS * 18 + 10,
                    links.capped() ? 0xFFB0302A : WfGui.INK_SOFT, false);
        }
        if (hovered != null && hovered.info != null) {
            var p = hovered.info.pos();
            List<Component> lines = new ArrayList<>();
            lines.add(hovered.label.copy().withStyle(ChatFormatting.GOLD));
            lines.add(Component.translatable("gui.wayfarers.terminal.link.pos", p.getX(), p.getY(), p.getZ()).withStyle(ChatFormatting.GRAY));
            lines.add(Component.translatable("gui.wayfarers.terminal.link.slots", hovered.info.slots()).withStyle(ChatFormatting.GRAY));
            lines.add(Component.translatable(hovered.info.excluded() ? "gui.wayfarers.terminal.link.include"
                    : "gui.wayfarers.terminal.link.exclude").withStyle(ChatFormatting.YELLOW));
            g.setComponentTooltipForNextFrame(font, lines, mouseX, mouseY);
        } else if (links != null && links.capped() && mouseY >= topPos + STATUS_Y && mouseY < topPos + STATUS_Y + 9
                && mouseX >= leftPos + GRID_X && mouseX < leftPos + GRID_X + COLS * 18) {
            g.setTooltipForNextFrame(font, Component.translatable("gui.wayfarers.terminal.capped"), mouseX, mouseY);
        } else {
            extractTooltip(g, mouseX, mouseY);
        }
    }

    // ------------------------------------------------------------------ input
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
        if (networkPage && inGrid(event.x(), event.y())) {
            Row row = rowAt(event.x(), event.y());
            if (row != null && row.info != null && event.button() == 0) {
                WayfarersNet.toServer(new TerminalToggleMsg(row.info.pos()));
            }
            return true;
        }
        if (!networkPage && inGrid(event.x(), event.y())) {
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
            if (networkPage) {
                linkScroll = (int) Math.max(0, Math.min(maxLinkScroll(), linkScroll - Math.signum(scrollY)));
            } else {
                int rowsTotal = (shown.size() + COLS - 1) / COLS;
                scroll = (int) Math.max(0, Math.min(Math.max(0, rowsTotal - ROWS), scroll - Math.signum(scrollY)));
            }
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
