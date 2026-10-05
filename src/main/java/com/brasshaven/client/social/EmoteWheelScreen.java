package com.brasshaven.client.social;

import com.brasshaven.client.gui.WfGui;
import com.brasshaven.social.SocialNet;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;

import java.util.Locale;

/**
 * The emote wheel (key Y): eight brass medallions in a ring. Click one, or press its number (1-8), to play it; the
 * centre names the one under the mouse. Everyone within 24 blocks sees the gesture.
 */
public class EmoteWheelScreen extends Screen {
    static final String[] EMOTES = {"wave", "bow", "cheer", "clap", "point", "laugh", "thanks", "rally"};
    private static final int RADIUS = 62;
    private static final int CELL = 34;

    private int cx;
    private int cy;

    public EmoteWheelScreen() {
        super(Component.translatable("gui.brasshaven.emote.title"));
    }

    @Override
    protected void init() {
        cx = width / 2;
        cy = height / 2;
    }

    private int cellX(int i) {
        return cx + (int) Math.round(Math.sin(i * Math.PI * 2 / EMOTES.length) * RADIUS) - CELL / 2;
    }

    private int cellY(int i) {
        return cy - (int) Math.round(Math.cos(i * Math.PI * 2 / EMOTES.length) * RADIUS) - CELL / 2;
    }

    private int at(double mx, double my) {
        for (int i = 0; i < EMOTES.length; i++) {
            if (mx >= cellX(i) && mx < cellX(i) + CELL && my >= cellY(i) && my < cellY(i) + CELL) {
                return i;
            }
        }
        return -1;
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        boolean on = ClientSocial.on(4);
        int hover = at(mouseX, mouseY);
        // the hub: a dark iron disc with a brass rim, the hovered emote's name in it
        WfGui.sprite(g, WfGui.PANEL, cx - 46, cy - 22, 92, 44);
        Component center = !on ? Component.translatable("message.brasshaven.social.disabled")
                : hover >= 0 ? Component.translatable("gui.brasshaven.emote." + EMOTES[hover])
                : Component.translatable("gui.brasshaven.emote.title");
        WfGui.centered(g, font, WfGui.bold(center), cx, cy - 8, WfGui.INK);
        WfGui.centered(g, font, Component.translatable("gui.brasshaven.emote.hint"), cx, cy + 4, WfGui.INK_SOFT);
        for (int i = 0; i < EMOTES.length; i++) {
            int x = cellX(i);
            int y = cellY(i);
            WfGui.sprite(g, hover == i && on ? WfGui.BUTTON_HOVER : on ? WfGui.BUTTON : WfGui.BUTTON_DISABLED, x, y, CELL, CELL);
            WfGui.sprite(g, WfGui.icon("emote_" + EMOTES[i]), x + 5, y + 4, 24, 24);
            g.text(font, String.valueOf(i + 1), x + CELL - 7, y + CELL - 10, WfGui.CREAM, true);
        }
        super.extractRenderState(g, mouseX, mouseY, a);
    }

    private void play(int i) {
        if (i >= 0 && ClientSocial.on(4)) {
            SocialNet.toServer(new SocialNet.EmoteAction(i));
            onClose();
        }
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        int i = at(event.x(), event.y());
        if (i >= 0) {
            play(i);
            return true;
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        int k = event.key();
        if (k >= '1' && k < '1' + EMOTES.length) {
            play(k - '1');
            return true;
        }
        if (ClientSocial.EMOTE_KEY.matches(event)) {
            onClose();
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    static String id(int i) {
        return EMOTES[i].toUpperCase(Locale.ROOT);
    }
}
