package com.brasshaven.client.gui;

import com.brasshaven.Brasshaven;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

/** The Brasshaven GUI theme (brass, riveted iron, parchment): sprite ids, colours and drawing helpers. */
public final class WfGui {
    private WfGui() {}

    public static final Identifier PANEL = Brasshaven.id("panel");
    public static final Identifier INSET = Brasshaven.id("inset");
    public static final Identifier CARD = Brasshaven.id("card");
    public static final Identifier TITLE_PLATE = Brasshaven.id("title_plate");
    public static final Identifier BUTTON = Brasshaven.id("button");
    public static final Identifier BUTTON_HOVER = Brasshaven.id("button_hover");
    public static final Identifier BUTTON_DISABLED = Brasshaven.id("button_disabled");
    public static final Identifier ROW_HOVER = Brasshaven.id("row_hover");
    public static final Identifier ROW_SELECTED = Brasshaven.id("row_selected");
    public static final Identifier SCROLL_THUMB = Brasshaven.id("scroll_thumb");
    public static final Identifier SCROLL_TRACK = Brasshaven.id("scroll_track");

    /*
     * Text colours. Contrast ratios (WCAG) against the calm parchment (#EBDDBE) or the dark iron wells (#221B18):
     * every body text is above 7:1, secondary text above 4.5:1. Dark text never gets a drop shadow (it smudges);
     * light text on iron always does.
     */
    /** Body text and titles on parchment: near-black brown, 12:1. */
    public static final int INK = 0xFF2A1C10;
    /** Secondary text on parchment (labels, hints, page numbers): still a dark brown, 8.6:1. */
    public static final int INK_SOFT = 0xFF4A3520;
    /** "Done" / good news on parchment, 5.4:1. */
    public static final int INK_GREEN = 0xFF1F6418;
    /** Warnings on parchment (locked, full), 7.9:1. */
    public static final int INK_RED = 0xFF7A1810;
    /** Text on dark iron, 15:1. */
    public static final int CREAM = 0xFFFFF5DC;
    /** Secondary text on dark iron (distances, hints), 10:1. */
    public static final int CREAM_SOFT = 0xFFDCCDB0;
    /** Unavailable entries on dark iron (locked quests, hidden layers): dimmed but readable, 6:1. */
    public static final int MUTED = 0xFFA89C8A;
    public static final int AETHER = 0xFF9FE6FF;
    public static final int GOLD = 0xFFF6C343;
    /** Engraved text on the brass title plates. */
    public static final int PLATE_INK = 0xFF2B1B0C;

    public static Identifier id(String sprite) {
        return Brasshaven.id(sprite);
    }

    public static Identifier icon(String name) {
        return Brasshaven.id("icon/" + name);
    }

    public static void sprite(GuiGraphicsExtractor g, Identifier sprite, int x, int y, int w, int h) {
        g.blitSprite(RenderPipelines.GUI_TEXTURED, sprite, x, y, w, h);
    }

    /** The main window frame with an engraved title plate centred on its top edge. */
    public static void window(GuiGraphicsExtractor g, Font font, Component title, int x, int y, int w, int h) {
        sprite(g, PANEL, x, y, w, h);
        Component t = bold(title);
        int tw = Math.max(90, font.width(t) + 24);
        sprite(g, TITLE_PLATE, x + (w - tw) / 2, y - 5, tw, 18);
        centered(g, font, t, x + w / 2, y, PLATE_INK);
    }

    /** A title in bold (Minecraft's bold: each glyph drawn twice, 1 px apart, and 1 px wider). */
    public static Component bold(Component text) {
        return text.copy().withStyle(net.minecraft.ChatFormatting.BOLD);
    }

    /**
     * Top of a window of height {@code h} centred on a screen of height {@code screenH}, counting the title plate that
     * sticks out 5 px above it and {@code below} px of hint text under it, so neither is cut on a small screen
     * (1280 x 720 at GUI scale 3 is 427 x 240).
     */
    public static int windowTop(int screenH, int h, int below) {
        return (screenH - h - 5 - below) / 2 + 5;
    }

    /**
     * Centred text without a drop shadow: ink on parchment or brass. ({@code GuiGraphicsExtractor.centeredText}
     * always draws a shadow, which smudges dark text on a light background.)
     */
    public static void centered(GuiGraphicsExtractor g, Font font, Component text, int x, int y, int color) {
        g.text(font, text, x - font.width(text) / 2, y, color, false);
    }

    public static void centered(GuiGraphicsExtractor g, Font font, net.minecraft.util.FormattedCharSequence text, int x, int y,
                                int color) {
        g.text(font, text, x - font.width(text) / 2, y, color, false);
    }

    /** A bold title centred on {@code cx}, cut to {@code width} pixels with an ellipsis. No shadow (ink on parchment). */
    public static void titleClipped(GuiGraphicsExtractor g, Font font, String text, int cx, int y, int width, int color) {
        Component t = bold(Component.literal(text));
        if (font.width(t) > width) {
            Component dots = bold(Component.literal("..."));
            String cut = font.substrByWidth(t, width - font.width(dots)).getString();
            t = bold(Component.literal(cut + "..."));
        }
        centered(g, font, t, cx, y, color);
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
