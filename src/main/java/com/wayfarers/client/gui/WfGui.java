package com.wayfarers.client.gui;

import com.wayfarers.Wayfarers;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

/** The Wayfarers GUI theme (brass, riveted iron, parchment): sprite ids, colours and drawing helpers. */
public final class WfGui {
    private WfGui() {}

    public static final Identifier PANEL = Wayfarers.id("panel");
    public static final Identifier INSET = Wayfarers.id("inset");
    public static final Identifier CARD = Wayfarers.id("card");
    public static final Identifier TITLE_PLATE = Wayfarers.id("title_plate");
    public static final Identifier BUTTON = Wayfarers.id("button");
    public static final Identifier BUTTON_HOVER = Wayfarers.id("button_hover");
    public static final Identifier BUTTON_DISABLED = Wayfarers.id("button_disabled");
    public static final Identifier ROW_HOVER = Wayfarers.id("row_hover");
    public static final Identifier ROW_SELECTED = Wayfarers.id("row_selected");
    public static final Identifier SCROLL_THUMB = Wayfarers.id("scroll_thumb");
    public static final Identifier SCROLL_TRACK = Wayfarers.id("scroll_track");

    /** Text on parchment. */
    public static final int INK = 0xFF3B2A1A;
    public static final int INK_SOFT = 0xFF6E5A40;
    /** Text on dark iron. */
    public static final int CREAM = 0xFFF3E3C0;
    public static final int CREAM_SOFT = 0xFFB9A98E;
    public static final int AETHER = 0xFF9FE6FF;
    public static final int GOLD = 0xFFF6C343;
    public static final int PLATE_INK = 0xFF2B1B0C;

    public static Identifier id(String sprite) {
        return Wayfarers.id(sprite);
    }

    public static Identifier icon(String name) {
        return Wayfarers.id("icon/" + name);
    }

    public static void sprite(GuiGraphicsExtractor g, Identifier sprite, int x, int y, int w, int h) {
        g.blitSprite(RenderPipelines.GUI_TEXTURED, sprite, x, y, w, h);
    }

    /** The main window frame with an engraved title plate centred on its top edge. */
    public static void window(GuiGraphicsExtractor g, Font font, Component title, int x, int y, int w, int h) {
        sprite(g, PANEL, x, y, w, h);
        int tw = Math.max(90, font.width(title) + 24);
        sprite(g, TITLE_PLATE, x + (w - tw) / 2, y - 5, tw, 18);
        g.centeredText(font, title, x + w / 2, y, PLATE_INK);
    }

    /** Draws ``text`` cut to ``width`` pixels with an ellipsis. */
    public static void textClipped(GuiGraphicsExtractor g, Font font, String text, int x, int y, int width, int color,
                                   boolean shadow) {
        String s = text;
        if (font.width(s) > width) {
            s = font.plainSubstrByWidth(s, width - font.width("...")) + "...";
        }
        g.text(font, s, x, y, color, shadow);
    }
}
