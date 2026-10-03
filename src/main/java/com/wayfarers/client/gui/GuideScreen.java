package com.wayfarers.client.gui;

import com.wayfarers.generated.GeneratedGuide;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
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
 */
public class GuideScreen extends Screen {
    private static final int W = 384;
    private static final int H = 232;
    private static final int LINE = 11;

    private int left;
    private int top;
    private int page;
    private int tocScroll;
    private final List<Object> toc = new ArrayList<>(); // GeneratedGuide.Category or GeneratedGuide.Page
    private WfButton prev;
    private WfButton next;

    public GuideScreen(String pageId) {
        super(Component.translatable("item.wayfarers.wayfarer_manual"));
        for (GeneratedGuide.Category c : GeneratedGuide.CATEGORIES) {
            toc.add(c);
            for (GeneratedGuide.Page p : GeneratedGuide.PAGES) {
                if (p.category().equals(c.id())) {
                    toc.add(p);
                }
            }
        }
        page = 0;
        if (pageId != null) {
            for (int i = 0; i < GeneratedGuide.PAGES.size(); i++) {
                if (GeneratedGuide.PAGES.get(i).id().equals(pageId)) {
                    page = i;
                }
            }
        }
    }

    /** Opens the page about this item, if there is one. */
    public static String pageFor(ItemStack stack) {
        String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        for (GeneratedGuide.Page p : GeneratedGuide.PAGES) {
            if (p.items().contains(id)) {
                return p.id();
            }
        }
        return null;
    }

    private int tocX() { return left + 14; }
    private int tocY() { return top + 24; }
    private int tocW() { return 120; }
    private int tocH() { return H - 36; }
    private int tocRows() { return (tocH() - 6) / LINE; }
    private int pageX() { return left + 142; }
    private int pageW() { return W - 156; }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
        prev = addRenderableWidget(new WfButton(pageX() + 4, top + H - 32, 60, 18, Component.literal("<"), b -> go(page - 1)));
        next = addRenderableWidget(new WfButton(pageX() + pageW() - 64, top + H - 32, 60, 18, Component.literal(">"), b -> go(page + 1)));
        go(page);
    }

    private void go(int p) {
        page = Math.max(0, Math.min(GeneratedGuide.PAGES.size() - 1, p));
        prev.active = page > 0;
        next.active = page < GeneratedGuide.PAGES.size() - 1;
        // keep the current page visible in the contents
        int row = toc.indexOf(GeneratedGuide.PAGES.get(page));
        if (row < tocScroll) {
            tocScroll = Math.max(0, row - 1);
        } else if (row >= tocScroll + tocRows()) {
            tocScroll = row - tocRows() + 1;
        }
    }

    private static ItemStack stack(String id) {
        return BuiltInRegistries.ITEM.getOptional(Identifier.parse(id)).map(ItemStack::new).orElse(new ItemStack(Items.BOOK));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, W, H);
        // contents
        WfGui.sprite(g, WfGui.INSET, tocX(), tocY(), tocW(), tocH());
        GeneratedGuide.Page current = GeneratedGuide.PAGES.get(page);
        for (int i = 0; i < tocRows() && i + tocScroll < toc.size(); i++) {
            Object o = toc.get(i + tocScroll);
            int y = tocY() + 4 + i * LINE;
            if (o instanceof GeneratedGuide.Category c) {
                g.text(font, Component.translatable("guide.wayfarers.cat." + c.id()), tocX() + 5, y + 1, WfGui.GOLD, true);
            } else if (o instanceof GeneratedGuide.Page p) {
                boolean sel = p == current;
                boolean hover = mouseX >= tocX() + 3 && mouseX < tocX() + tocW() - 3 && mouseY >= y && mouseY < y + LINE;
                if (sel) {
                    WfGui.sprite(g, WfGui.ROW_SELECTED, tocX() + 3, y - 1, tocW() - 6, LINE);
                } else if (hover) {
                    WfGui.sprite(g, WfGui.ROW_HOVER, tocX() + 3, y - 1, tocW() - 6, LINE);
                }
                WfGui.textClipped(g, font, Component.translatable("guide.wayfarers." + p.id() + ".title").getString(),
                        tocX() + 12, y + 1, tocW() - 18, sel ? WfGui.AETHER : WfGui.CREAM, true);
            }
        }
        // page
        int px = pageX();
        int pw = pageW();
        WfGui.sprite(g, WfGui.CARD, px, top + 18, pw, H - 54);
        g.pose().pushMatrix();
        g.pose().translate(px + pw / 2.0F - 16, top + 24);
        g.pose().scale(2.0F, 2.0F);
        g.item(stack(current.icon()), 0, 0);
        g.pose().popMatrix();
        int y = top + 60;
        for (FormattedCharSequence line : font.split(Component.translatable("guide.wayfarers." + current.id() + ".title"), pw - 12)) {
            g.centeredText(font, line, px + pw / 2, y, WfGui.INK);
            y += 10;
        }
        y += 4;
        int bottom = top + H - 54 - (current.items().isEmpty() ? 0 : 22);
        for (int i = 0; i < current.paragraphs(); i++) {
            for (FormattedCharSequence line : font.split(Component.translatable("guide.wayfarers." + current.id() + ".p" + i), pw - 14)) {
                if (y < bottom) {
                    g.text(font, line, px + 7, y, WfGui.INK_SOFT, false);
                }
                y += 9;
            }
            y += 5;
        }
        if (!current.items().isEmpty()) {
            int ix = px + 7;
            int iy = top + H - 58;
            for (String id : current.items()) {
                ItemStack s = stack(id);
                g.item(s, ix, iy);
                if (mouseX >= ix && mouseX < ix + 16 && mouseY >= iy && mouseY < iy + 16) {
                    g.setTooltipForNextFrame(font, s, mouseX, mouseY);
                }
                ix += 20;
            }
        }
        g.centeredText(font, Component.literal((page + 1) + " / " + GeneratedGuide.PAGES.size()), px + pw / 2, top + H - 27, WfGui.INK_SOFT);
        super.extractRenderState(g, mouseX, mouseY, a);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x();
        double my = event.y();
        for (int i = 0; i < tocRows() && i + tocScroll < toc.size(); i++) {
            int y = tocY() + 4 + i * LINE;
            if (mx >= tocX() + 3 && mx < tocX() + tocW() - 3 && my >= y && my < y + LINE
                    && toc.get(i + tocScroll) instanceof GeneratedGuide.Page p) {
                go(GeneratedGuide.PAGES.indexOf(p));
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (x < pageX()) {
            int max = Math.max(0, toc.size() - tocRows());
            tocScroll = (int) Math.max(0, Math.min(max, tocScroll - Math.signum(scrollY)));
        } else {
            go(page - (int) Math.signum(scrollY));
        }
        return true;
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
