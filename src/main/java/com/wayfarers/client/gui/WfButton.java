package com.wayfarers.client.gui;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.network.chat.Component;

/** A brass plate button in the Wayfarers theme. */
public class WfButton extends Button {
    public WfButton(int x, int y, int width, int height, Component message, OnPress onPress) {
        super(x, y, width, height, message, onPress, DEFAULT_NARRATION);
    }

    @Override
    protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.sprite(g, !this.active ? WfGui.BUTTON_DISABLED : this.isHoveredOrFocused() ? WfGui.BUTTON_HOVER : WfGui.BUTTON,
                getX(), getY(), getWidth(), getHeight());
        this.extractDefaultLabel(g.textRendererForWidget(this, GuiGraphicsExtractor.HoveredTextEffects.NONE));
    }
}
