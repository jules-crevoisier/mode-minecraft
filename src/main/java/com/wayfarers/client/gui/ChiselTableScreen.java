package com.wayfarers.client.gui;

import com.wayfarers.menu.ChiselTableMenu;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;

/**
 * Chisel Table screen: the input slot on the left, the variants of its chisel family in a grid on the right
 * (the current one framed in gold); click a variant to convert the whole stack.
 */
public class ChiselTableScreen extends AbstractContainerScreen<ChiselTableMenu> {
    public ChiselTableScreen(ChiselTableMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, 196, 190);
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        WfGui.window(g, font, title, leftPos, topPos, imageWidth, imageHeight);
        int gx = leftPos + ChiselTableMenu.GRID_X;
        int gy = topPos + ChiselTableMenu.GRID_Y;
        // input well, an arrow towards the variants, the variant grid
        WfGui.sprite(g, WfGui.INSET, leftPos + ChiselTableMenu.INPUT_X - 6, topPos + ChiselTableMenu.INPUT_Y - 6, 28, 28);
        int ay = topPos + ChiselTableMenu.INPUT_Y + 7;
        for (int i = 0; i < 14; i++) {
            int x = leftPos + ChiselTableMenu.INPUT_X + 24 + i;
            int half = i >= 10 ? 13 - i : 0;
            g.fill(x, ay - half, x + 1, ay + 2 + half, WfGui.GOLD);
        }
        WfGui.sprite(g, WfGui.INSET, gx - 3, gy - 3, ChiselTableMenu.COLS * 18 + 6, ChiselTableMenu.ROWS * 18 + 6);
        for (Slot slot : menu.slots) {
            if (!menu.isVariantSlot(slot)) {
                WfGui.sprite(g, WfGui.INSET, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
            } else if (menu.isCurrent(slot)) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
            } else if (slot.hasItem() && isHovering(slot.x, slot.y, 16, 16, mouseX, mouseY)) {
                WfGui.sprite(g, WfGui.ROW_HOVER, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
            }
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        // the title is on the brass plate; one hint line under the grid instead of the inventory label
        Component hint;
        if (!menu.hasInput()) {
            hint = Component.translatable("gui.wayfarers.chisel_table.empty");
        } else if (menu.familySize() == 0) {
            hint = Component.translatable("gui.wayfarers.chisel_table.none");
        } else {
            hint = Component.translatable("gui.wayfarers.chisel_table.pick", menu.familySize());
        }
        g.centeredText(font, hint, imageWidth / 2, ChiselTableMenu.GRID_Y + ChiselTableMenu.ROWS * 18 + 8, WfGui.CREAM_SOFT);
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractRenderState(g, mouseX, mouseY, a);
        extractTooltip(g, mouseX, mouseY);
    }
}
