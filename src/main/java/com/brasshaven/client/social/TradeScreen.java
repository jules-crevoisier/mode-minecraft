package com.brasshaven.client.social;

import com.brasshaven.client.gui.WfButton;
import com.brasshaven.client.gui.WfGui;
import com.brasshaven.social.TradeMenu;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;

/**
 * The trade screen: your offer on the left, theirs on the right (look, don't touch), a lamp for each side's
 * acceptance between them and the countdown once both accepted. Accept / Cancel are vanilla menu-button clicks.
 */
public class TradeScreen extends AbstractContainerScreen<TradeMenu> implements com.brasshaven.client.ContainerButtons.Exempt {
    private WfButton accept;

    public TradeScreen(TradeMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, TradeMenu.W, TradeMenu.H);
    }

    @Override
    protected void init() {
        super.init();
        topPos = WfGui.windowTop(height, imageHeight, 0);
        accept = addRenderableWidget(new WfButton(leftPos + TradeMenu.MY_X, topPos + TradeMenu.GRID_Y + 58, 54, 18,
                Component.translatable("gui.brasshaven.trade.accept"), b -> click(TradeMenu.BUTTON_ACCEPT)));
        accept.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.trade.accept.tip")));
        addRenderableWidget(new WfButton(leftPos + TradeMenu.THEIR_X, topPos + TradeMenu.GRID_Y + 58, 54, 18,
                Component.translatable("gui.brasshaven.trade.cancel"), b -> click(TradeMenu.BUTTON_CANCEL)));
    }

    private void click(int id) {
        if (minecraft != null && minecraft.gameMode != null) {
            minecraft.gameMode.handleInventoryButtonClick(menu.containerId, id);
        }
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        WfGui.window(g, font, title, leftPos, topPos, imageWidth, imageHeight);
        int gy = topPos + TradeMenu.GRID_Y;
        // your offer in a brass-rimmed well, theirs in a dark one
        WfGui.sprite(g, WfGui.INSET, leftPos + TradeMenu.MY_X - 3, gy - 3, 60, 60);
        WfGui.sprite(g, WfGui.INSET, leftPos + TradeMenu.THEIR_X - 3, gy - 3, 60, 60);
        if (menu.meAccepted()) {
            g.outline(leftPos + TradeMenu.MY_X - 4, gy - 4, 62, 62, 0xFF7CE35A);
        }
        if (menu.theyAccepted()) {
            g.outline(leftPos + TradeMenu.THEIR_X - 4, gy - 4, 62, 62, 0xFF7CE35A);
        }
        for (Slot slot : menu.slots) {
            if (!menu.isMine(slot) && !menu.isTheirs(slot)) {
                WfGui.sprite(g, WfGui.INSET, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
            }
        }
        // the exchange arrows between the offers
        int mx = leftPos + imageWidth / 2;
        int my = gy + 16;
        for (int i = 0; i < 22; i++) {
            g.fill(mx - 11 + i, my, mx - 10 + i, my + 2, WfGui.GOLD);
            g.fill(mx - 11 + i, my + 12, mx - 10 + i, my + 14, WfGui.GOLD);
        }
        for (int i = 0; i < 4; i++) {
            g.fill(mx + 7 + i - 4, my - 3 + i, mx + 8 + i - 4, my + 5 - i, WfGui.GOLD);
            g.fill(mx - 8 - i + 4, my + 9 + i, mx - 7 - i + 4, my + 17 - i, WfGui.GOLD);
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        WfGui.centered(g, font, Component.translatable("gui.brasshaven.trade.yours"), TradeMenu.MY_X + 27, TradeMenu.GRID_Y - 12, WfGui.INK);
        WfGui.titleClipped(g, font, menu.partner, TradeMenu.THEIR_X + 27, TradeMenu.GRID_Y - 12, 70, WfGui.INK);
        int cx = imageWidth / 2;
        lamp(g, cx - 12, TradeMenu.GRID_Y + 38, menu.meAccepted());
        lamp(g, cx + 4, TradeMenu.GRID_Y + 38, menu.theyAccepted());
        Component status;
        int color = WfGui.INK_SOFT;
        if (menu.problem() == 1) {
            status = Component.translatable("gui.brasshaven.trade.no_room_you");
            color = WfGui.INK_RED;
        } else if (menu.problem() == 2) {
            status = Component.translatable("gui.brasshaven.trade.no_room_them");
            color = WfGui.INK_RED;
        } else if (menu.countdown() > 0) {
            status = Component.translatable("gui.brasshaven.trade.countdown", menu.countdown() / 20 + 1);
            color = WfGui.INK_GREEN;
        } else if (menu.meAccepted()) {
            status = Component.translatable("gui.brasshaven.trade.waiting");
        } else if (menu.theyAccepted()) {
            status = Component.translatable("gui.brasshaven.trade.they_accepted");
            color = WfGui.INK_GREEN;
        } else {
            status = Component.translatable("gui.brasshaven.trade.hint");
        }
        java.util.List<net.minecraft.util.FormattedCharSequence> lines = font.split(status, imageWidth - 24);
        for (int i = 0; i < Math.min(2, lines.size()); i++) {
            WfGui.centered(g, font, lines.get(i), cx, TradeMenu.GRID_Y + 80 + i * 9, color);
        }
        accept.setMessage(Component.translatable(menu.meAccepted() ? "gui.brasshaven.trade.accepted" : "gui.brasshaven.trade.accept"));
    }

    private static void lamp(GuiGraphicsExtractor g, int x, int y, boolean on) {
        g.fill(x, y, x + 8, y + 8, 0xFF0F0C0A);
        g.fill(x + 1, y + 1, x + 7, y + 7, on ? 0xFF7CE35A : 0xFF5A4F45);
        if (on) {
            g.fill(x + 2, y + 2, x + 4, y + 4, 0xFFD8FFC0);
        }
    }
}
