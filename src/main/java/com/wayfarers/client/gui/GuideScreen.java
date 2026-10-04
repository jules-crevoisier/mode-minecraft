package com.wayfarers.client.gui;

import com.mojang.blaze3d.platform.InputConstants;
import com.wayfarers.generated.GeneratedGuide;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.ArrayList;
import java.util.List;

/**
 * The Wayfarer's Manual: an open book with the table of contents (categories and pages) on the left
 * and the selected page on the right: big icon, title, short paragraphs and the items it is about.
 *
 * <p>Pages are laid out with the real font when the screen opens (and again on resize): a page whose
 * text does not fit is split into continuation sheets ("Title (continued)", "2/3" in the corner), so no
 * text is ever cut. The arrows, the mouse wheel over the page and the keyboard (left/right, page up/down:
 * sheet by sheet; up/down: page by page; home/end) walk through the sheets in book order.
 */
public class GuideScreen extends Screen {
    private static final int MIN_W = 384;
    private static final int MAX_W = 440;
    private static final int MIN_H = 232;
    /** Width of the page card: fixed, so a page splits the same way on every screen width. */
    private static final int PAGE_W = 228;
    private static final int MAX_H = 296;
    private static final int LINE = 11;
    /** Height of one line of page text, and the extra space between two paragraphs. */
    private static final int TEXT_LINE = 9;
    private static final int PARA_GAP = 5;
    /** Height of the row of related items at the bottom of a page's first sheet. */
    private static final int ITEMS_ROW = 22;

    /** One screenful of a manual page. {@code lines} holds the wrapped text; {@code null} marks a paragraph gap. */
    private record Sheet(GeneratedGuide.Page page, int part, int parts, boolean compact,
                         List<FormattedCharSequence> title, List<FormattedCharSequence> lines) {}

    private int w = MIN_W;
    private int h = MIN_H;
    private int left;
    private int top;
    private int sheet;
    private int tocScroll;
    private boolean draggingToc;
    private final List<Object> toc = new ArrayList<>(); // GeneratedGuide.Category or GeneratedGuide.Page
    /** The pages in reading order: the order of the contents. */
    private final List<GeneratedGuide.Page> order = new ArrayList<>();
    private final List<Sheet> sheets = new ArrayList<>();
    /** The page (and sheet of that page) to show once the layout is known. */
    private GeneratedGuide.Page wantPage;
    private int wantPart;
    private WfButton prev;
    private WfButton next;

    public GuideScreen(String pageId) {
        super(Component.translatable("item.wayfarers.wayfarer_manual"));
        for (GeneratedGuide.Category c : GeneratedGuide.CATEGORIES) {
            toc.add(c);
            for (GeneratedGuide.Page p : GeneratedGuide.PAGES) {
                if (p.category().equals(c.id())) {
                    toc.add(p);
                    order.add(p);
                }
            }
        }
        wantPage = order.get(0);
        if (pageId != null) {
            for (GeneratedGuide.Page p : order) {
                if (p.id().equals(pageId)) {
                    wantPage = p;
                }
            }
        }
    }

    /**
     * Item -> manual page (empty: none). Asked for every tooltip frame and every tick in inventories, so memoized;
     * concurrent because tooltips are also built off-thread (creative search).
     */
    private static final java.util.Map<net.minecraft.world.item.Item, java.util.Optional<String>> PAGE_OF =
            new java.util.concurrent.ConcurrentHashMap<>();

    /** Opens the page about this item, if there is one. */
    public static String pageFor(ItemStack stack) {
        return PAGE_OF.computeIfAbsent(stack.getItem(), item -> {
            String id = BuiltInRegistries.ITEM.getKey(item).toString();
            for (GeneratedGuide.Page p : GeneratedGuide.PAGES) {
                if (p.items().contains(id)) {
                    return java.util.Optional.of(p.id());
                }
            }
            return java.util.Optional.empty();
        }).orElse(null);
    }

    private int tocX() { return left + 14; }
    private int tocY() { return top + 24; }
    /** The contents column takes the extra width of a wide screen, so long titles fit. */
    private int tocW() { return 120 + (w - MIN_W); }
    private int tocH() { return h - 36; }
    private int tocRows() { return (tocH() - 6) / LINE; }
    private int pageX() { return tocX() + tocW() + 8; }
    private int pageW() { return PAGE_W; }
    private int textX() { return pageX() + 7; }
    private int textW() { return pageW() - 14; }
    private int cardTop() { return top + 18; }
    private int cardBottom() { return top + h - 36; }

    @Override
    protected void init() {
        // a bigger book on big screens, never smaller than the classic 384 x 232
        w = Math.max(MIN_W, Math.min(MAX_W, width - 24));
        h = Math.max(MIN_H, Math.min(MAX_H, height - 28));
        left = (width - w) / 2;
        top = Math.max(8, (height - h) / 2);
        if (!sheets.isEmpty()) {
            Sheet s = sheets.get(sheet);
            wantPage = s.page();
            wantPart = s.part();
        }
        paginate();
        prev = addRenderableWidget(new WfButton(pageX() + 4, top + h - 32, 60, 18, Component.literal("<"), b -> go(sheet - 1)));
        next = addRenderableWidget(new WfButton(pageX() + pageW() - 64, top + h - 32, 60, 18, Component.literal(">"), b -> go(sheet + 1)));
        int start = 0;
        for (int i = 0; i < sheets.size(); i++) {
            Sheet s = sheets.get(i);
            if (s.page() == wantPage && s.part() <= wantPart) {
                start = i;
            }
        }
        go(start);
    }

    // ------------------------------------------------------------------ layout

    /**
     * Title lines of a sheet. A page normally opens with a big icon above a centred title; continuation sheets (and a
     * page that fits on one sheet only that way) use a compact header: a small icon beside the title.
     */
    private List<FormattedCharSequence> titleLines(GeneratedGuide.Page p, int part, boolean compact) {
        Component t = Component.translatable("guide.wayfarers." + p.id() + ".title");
        if (part > 0) {
            t = Component.empty().append(t).append(" ").append(Component.translatable("guide.wayfarers.continued"));
        }
        return font.split(t, compact ? pageW() - 52 : pageW() - 12);
    }

    /** Y of the first text line of a sheet. */
    private int bodyTop(boolean compact, int titleLines) {
        return compact ? top + 25 + Math.max(1, titleLines) * 10 + 6 : top + 60 + titleLines * 10 + 4;
    }

    /** Y below which no text line may go (room for the item row on the first sheet). */
    private int bodyBottom(GeneratedGuide.Page p, int part) {
        return cardBottom() - 4 - (part == 0 && !p.items().isEmpty() ? ITEMS_ROW : 0);
    }

    /** Splits every page into sheets that fit the card, measuring the wrapped text with the real font. */
    private void paginate() {
        sheets.clear();
        for (GeneratedGuide.Page p : order) {
            List<List<FormattedCharSequence>> paras = new ArrayList<>();
            for (int i = 0; i < p.paragraphs(); i++) {
                paras.add(font.split(Component.translatable("guide.wayfarers." + p.id() + ".p" + i), textW()));
            }
            boolean compact = false;
            List<List<FormattedCharSequence>> pageSheets = split(p, paras, false);
            if (pageSheets.size() > 1) {
                // a page just too long for the big header fits on one sheet with the compact one
                List<List<FormattedCharSequence>> tight = split(p, paras, true);
                if (tight.size() == 1) {
                    pageSheets = tight;
                    compact = true;
                }
            }
            for (int part = 0; part < pageSheets.size(); part++) {
                boolean c = compact || part > 0;
                sheets.add(new Sheet(p, part, pageSheets.size(), c, titleLines(p, part, c), pageSheets.get(part)));
            }
        }
    }

    /** The text lines of each sheet of a page ({@code null} = paragraph gap). */
    private List<List<FormattedCharSequence>> split(GeneratedGuide.Page p, List<List<FormattedCharSequence>> paras,
                                                    boolean compactFirst) {
        List<List<FormattedCharSequence>> pageSheets = new ArrayList<>();
        List<FormattedCharSequence> cur = new ArrayList<>();
        int y = bodyTop(compactFirst, titleLines(p, 0, compactFirst).size());
        int bottom = bodyBottom(p, 0);
        int nextTop = bodyTop(true, titleLines(p, 1, true).size());
        for (List<FormattedCharSequence> para : paras) {
            if (!cur.isEmpty()) {
                cur.add(null);
                y += PARA_GAP;
            }
            // a short paragraph that does not fit moves to the next sheet whole instead of being cut
            if (!cur.isEmpty() && y + para.size() * TEXT_LINE > bottom && para.size() <= 3) {
                cur.remove(cur.size() - 1);
                pageSheets.add(cur);
                cur = new ArrayList<>();
                y = nextTop;
                bottom = bodyBottom(p, 1);
            }
            for (FormattedCharSequence line : para) {
                // a sheet always takes at least one line, so even a tiny window shows everything
                if (y + TEXT_LINE > bottom && !cur.isEmpty()) {
                    if (cur.get(cur.size() - 1) == null) {
                        cur.remove(cur.size() - 1);
                    }
                    pageSheets.add(cur);
                    cur = new ArrayList<>();
                    y = nextTop;
                    bottom = bodyBottom(p, 1);
                }
                cur.add(line);
                y += TEXT_LINE;
            }
        }
        if (!cur.isEmpty() || pageSheets.isEmpty()) {
            pageSheets.add(cur);
        }
        return pageSheets;
    }

    // ------------------------------------------------------------------ navigation

    private void go(int target) {
        sheet = Math.max(0, Math.min(sheets.size() - 1, target));
        prev.active = sheet > 0;
        next.active = sheet < sheets.size() - 1;
        // when the text goes on over the page, the next button says so
        Sheet s = sheets.get(sheet);
        next.setMessage(s.part() < s.parts() - 1 ? Component.translatable("guide.wayfarers.more") : Component.literal(">"));
        // keep the current page visible in the contents
        int row = toc.indexOf(sheets.get(sheet).page());
        if (row < tocScroll) {
            tocScroll = Math.max(0, row - 1);
        } else if (row >= tocScroll + tocRows()) {
            tocScroll = row - tocRows() + 1;
        }
        clampToc();
    }

    /** Goes to the first sheet of the page {@code delta} pages away from the current one. */
    private void goPage(int delta) {
        int target = order.indexOf(sheets.get(sheet).page()) + delta;
        if (delta < 0 && sheets.get(sheet).part() > 0) {
            target++; // first "previous" press goes back to the start of the current page
        }
        target = Math.max(0, Math.min(order.size() - 1, target));
        goTo(order.get(target));
    }

    private void goTo(GeneratedGuide.Page p) {
        for (int i = 0; i < sheets.size(); i++) {
            if (sheets.get(i).page() == p) {
                go(i);
                return;
            }
        }
    }

    private void clampToc() {
        tocScroll = Math.max(0, Math.min(Math.max(0, toc.size() - tocRows()), tocScroll));
    }

    private static ItemStack stack(String id) {
        return BuiltInRegistries.ITEM.getOptional(Identifier.parse(id)).map(ItemStack::new).orElse(new ItemStack(Items.BOOK));
    }

    // ------------------------------------------------------------------ drawing

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, w, h);
        Sheet cur = sheets.get(sheet);
        GeneratedGuide.Page current = cur.page();
        // contents
        WfGui.sprite(g, WfGui.INSET, tocX(), tocY(), tocW(), tocH());
        boolean scrollable = toc.size() > tocRows();
        int rowW = tocW() - (scrollable ? 12 : 6);
        for (int i = 0; i < tocRows() && i + tocScroll < toc.size(); i++) {
            Object o = toc.get(i + tocScroll);
            int y = tocY() + 4 + i * LINE;
            if (o instanceof GeneratedGuide.Category c) {
                WfGui.textClipped(g, font, Component.translatable("guide.wayfarers.cat." + c.id()).getString(),
                        tocX() + 5, y + 1, rowW - 4, WfGui.GOLD, true);
            } else if (o instanceof GeneratedGuide.Page p) {
                boolean sel = p == current;
                boolean hover = mouseX >= tocX() + 3 && mouseX < tocX() + 3 + rowW && mouseY >= y && mouseY < y + LINE;
                if (sel) {
                    WfGui.sprite(g, WfGui.ROW_SELECTED, tocX() + 3, y - 1, rowW, LINE);
                } else if (hover) {
                    WfGui.sprite(g, WfGui.ROW_HOVER, tocX() + 3, y - 1, rowW, LINE);
                }
                Component name = Component.translatable("guide.wayfarers." + p.id() + ".title");
                WfGui.textClipped(g, font, name.getString(), tocX() + 12, y + 1, rowW - 12, sel ? WfGui.AETHER : WfGui.CREAM, true);
                if (hover && font.width(name) > rowW - 12) {
                    g.setTooltipForNextFrame(font, name, mouseX, mouseY); // the full title of a clipped row
                }
            }
        }
        if (scrollable) {
            int tx = tocX() + tocW() - 9;
            int ty = tocY() + 3;
            int th = tocH() - 6;
            WfGui.sprite(g, WfGui.SCROLL_TRACK, tx, ty, 6, th);
            int thumb = Math.max(12, th * tocRows() / toc.size());
            int max = toc.size() - tocRows();
            int pos = max == 0 ? 0 : (th - thumb) * tocScroll / max;
            WfGui.sprite(g, WfGui.SCROLL_THUMB, tx, ty + pos, 6, thumb);
        }
        // page
        int px = pageX();
        int pw = pageW();
        WfGui.sprite(g, WfGui.CARD, px, cardTop(), pw, cardBottom() - cardTop());
        int y;
        if (!cur.compact()) {
            g.pose().pushMatrix();
            g.pose().translate(px + pw / 2.0F - 16, top + 24);
            g.pose().scale(2.0F, 2.0F);
            g.item(stack(current.icon()), 0, 0);
            g.pose().popMatrix();
            y = top + 60;
            for (FormattedCharSequence line : cur.title()) {
                g.text(font, line, px + pw / 2 - font.width(line) / 2, y, WfGui.INK, false);
                y += 10;
            }
        } else {
            g.item(stack(current.icon()), px + 6, top + 23);
            y = top + 25;
            for (FormattedCharSequence line : cur.title()) {
                g.text(font, line, px + 26, y, WfGui.INK, false);
                y += 10;
            }
        }
        if (cur.parts() > 1) {
            String part = (cur.part() + 1) + "/" + cur.parts();
            g.text(font, part, px + pw - 6 - font.width(part), cur.compact() ? top + 25 : top + 23, WfGui.INK_SOFT, false);
        }
        y = bodyTop(cur.compact(), cur.title().size());
        for (FormattedCharSequence line : cur.lines()) {
            if (line == null) {
                y += PARA_GAP;
            } else {
                g.text(font, line, textX(), y, WfGui.INK_SOFT, false);
                y += TEXT_LINE;
            }
        }
        if (cur.part() == 0 && !current.items().isEmpty()) {
            int ix = textX();
            int iy = cardBottom() - 22;
            for (String id : current.items()) {
                ItemStack s = stack(id);
                g.item(s, ix, iy);
                if (mouseX >= ix && mouseX < ix + 16 && mouseY >= iy && mouseY < iy + 16) {
                    g.setTooltipForNextFrame(font, s, mouseX, mouseY);
                }
                ix += 20;
            }
        }
        WfGui.centered(g, font, Component.literal((sheet + 1) + " / " + sheets.size()), px + pw / 2, top + h - 27, WfGui.INK_SOFT);
        super.extractRenderState(g, mouseX, mouseY, a);
    }

    // ------------------------------------------------------------------ input

    private boolean overTocBar(double mx, double my) {
        return toc.size() > tocRows() && mx >= tocX() + tocW() - 10 && mx < tocX() + tocW() - 2
                && my >= tocY() + 3 && my < tocY() + tocH() - 3;
    }

    private void dragToc(double my) {
        int th = tocH() - 6;
        int thumb = Math.max(12, th * tocRows() / toc.size());
        double f = (my - (tocY() + 3) - thumb / 2.0) / Math.max(1, th - thumb);
        tocScroll = (int) Math.round(f * (toc.size() - tocRows()));
        clampToc();
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x();
        double my = event.y();
        if (overTocBar(mx, my)) {
            draggingToc = true;
            dragToc(my);
            return true;
        }
        for (int i = 0; i < tocRows() && i + tocScroll < toc.size(); i++) {
            int y = tocY() + 4 + i * LINE;
            if (mx >= tocX() + 3 && mx < tocX() + tocW() - 3 && my >= y && my < y + LINE
                    && toc.get(i + tocScroll) instanceof GeneratedGuide.Page p) {
                goTo(p);
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseDragged(MouseButtonEvent event, double dx, double dy) {
        if (draggingToc) {
            dragToc(event.y());
            return true;
        }
        return super.mouseDragged(event, dx, dy);
    }

    @Override
    public boolean mouseReleased(MouseButtonEvent event) {
        draggingToc = false;
        return super.mouseReleased(event);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (scrollY == 0) {
            return false;
        }
        if (x < pageX()) {
            tocScroll -= (int) Math.signum(scrollY);
            clampToc();
        } else {
            go(sheet - (int) Math.signum(scrollY));
        }
        return true;
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        int key = event.key();
        if (event.isRight() || key == InputConstants.KEY_PAGEDOWN) {
            go(sheet + 1);
            return true;
        }
        if (event.isLeft() || key == InputConstants.KEY_PAGEUP) {
            go(sheet - 1);
            return true;
        }
        if (event.isDown()) {
            goPage(1);
            return true;
        }
        if (event.isUp()) {
            goPage(-1);
            return true;
        }
        if (key == InputConstants.KEY_HOME) {
            go(0);
            return true;
        }
        if (key == InputConstants.KEY_END) {
            go(sheets.size() - 1);
            return true;
        }
        return super.keyPressed(event);
    }

    /** Screen to go back to on close (the player's inventory when the page was opened from it), else the game. */
    private net.minecraft.client.gui.screens.Screen back;

    public GuideScreen returningTo(net.minecraft.client.gui.screens.Screen back) {
        this.back = back;
        return this;
    }

    @Override
    public void onClose() {
        minecraft.gui.setScreen(back);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
