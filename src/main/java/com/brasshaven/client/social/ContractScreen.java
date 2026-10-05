package com.brasshaven.client.social;

import com.brasshaven.client.gui.WfButton;
import com.brasshaven.client.gui.WfGui;
import com.brasshaven.client.gui.WfWidgets;
import com.brasshaven.social.ContractMenu;
import com.brasshaven.social.Contracts;
import com.brasshaven.social.SocialNet;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/**
 * The Contract Board: a Board tab (every open contract, yours first; the selected one on the parchment card with its
 * reward, Deliver or Cancel) and a Post tab (a sample of the wanted item, how many, a note, the reward slots).
 */
public class ContractScreen extends AbstractContainerScreen<ContractMenu> implements com.brasshaven.client.ContainerButtons.Exempt {
    private static final int LIST_X = 12;
    private static final int LIST_Y = 36;
    private static final int LIST_W = 164;
    private static final int LIST_H = 82;
    private static final int ROW = 20;
    private static final int CARD_X = 184;
    private static final int CARD_W = 134;
    private static final int CARD_H = 104;

    private SocialNet.Board board;
    private boolean posting;
    private long selected = -1;
    private int scroll;
    private int amount = 16;
    private EditBox amountBox;
    private EditBox note;
    private WfButton post;
    private WfButton deliver;
    private WfButton cancel;
    private WfButton minus;
    private WfButton plus;
    private String keepNote = "";

    public ContractScreen(ContractMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, ContractMenu.W, ContractMenu.H);
    }

    public void receive(SocialNet.Board msg) {
        board = msg;
        if (selected < 0 || msg.contracts().stream().noneMatch(c -> c.id() == selected)) {
            selected = msg.contracts().isEmpty() ? -1 : msg.contracts().get(0).id();
        }
        if (posting && msg.mine() > 0 && menu.wantedItem().isEmpty()) {
            // just posted: show it on the board
            posting = false;
        }
        update();
    }

    @Override
    protected void init() {
        super.init();
        topPos = WfGui.windowTop(height, imageHeight, 0);
        addRenderableWidget(new WfWidgets.Choice(leftPos + 12, topPos + 16, 80, 16, Component.translatable("gui.brasshaven.contract.board"),
                Component.translatable("gui.brasshaven.contract.board.tip"), () -> !posting, () -> setPosting(false)));
        addRenderableWidget(new WfWidgets.Choice(leftPos + 96, topPos + 16, 80, 16, Component.translatable("gui.brasshaven.contract.post"),
                Component.translatable("gui.brasshaven.contract.post.tip"), () -> posting, () -> setPosting(true)));
        int ax = leftPos + ContractMenu.WANT_X + 22;
        int ay = topPos + ContractMenu.WANT_Y;
        minus = addRenderableWidget(new WfButton(ax, ay, 14, 16, Component.literal("-"), b -> setAmount(amount - step())));
        amountBox = new EditBox(font, ax + 18, ay + 4, 36, 10, Component.translatable("gui.brasshaven.contract.amount"));
        amountBox.setBordered(false);
        amountBox.setMaxLength(3);
        amountBox.setTextColor(WfGui.CREAM);
        amountBox.setValue(String.valueOf(amount));
        amountBox.setResponder(s -> {
            String nums = s.replaceAll("[^0-9]", "");
            if (!nums.equals(s)) {
                amountBox.setValue(nums);
                return;
            }
            try {
                amount = Mth.clamp(Integer.parseInt(s), 1, Contracts.MAX_AMOUNT);
            } catch (NumberFormatException e) {
                amount = 1;
            }
        });
        addRenderableWidget(amountBox);
        plus = addRenderableWidget(new WfButton(ax + 58, ay, 14, 16, Component.literal("+"), b -> setAmount(amount + step())));
        plus.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.contract.step")));
        minus.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.contract.step")));
        note = new EditBox(font, leftPos + LIST_X + 4, topPos + LIST_Y + 68, LIST_W - 8, 12, Component.translatable("gui.brasshaven.contract.note"));
        note.setBordered(false);
        note.setMaxLength(Contracts.MAX_NOTE);
        note.setTextColor(WfGui.CREAM);
        note.setHint(Component.translatable("gui.brasshaven.contract.note_hint").withColor(WfGui.MUTED));
        note.setValue(keepNote);
        addRenderableWidget(note);
        post = addRenderableWidget(new WfButton(leftPos + LIST_X, topPos + LIST_Y + 86, LIST_W, 16, Component.translatable("gui.brasshaven.contract.post_button"),
                b -> SocialNet.toServer(new SocialNet.BoardAction(menu.containerId, SocialNet.BoardAction.Action.POST, 0, amount, note.getValue()))));
        post.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.contract.post_button.tip", ClientSocial.hello.contractDays())));
        deliver = addRenderableWidget(new WfButton(leftPos + LIST_X, topPos + LIST_Y + 86, LIST_W, 16, Component.translatable("gui.brasshaven.contract.deliver"),
                b -> act(SocialNet.BoardAction.Action.DELIVER)));
        deliver.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.contract.deliver.tip")));
        cancel = addRenderableWidget(new WfButton(leftPos + LIST_X, topPos + LIST_Y + 86, LIST_W, 16, Component.translatable("gui.brasshaven.contract.cancel"),
                b -> act(SocialNet.BoardAction.Action.CANCEL)));
        cancel.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.contract.cancel.tip")));
        update();
        if (board == null) {
            SocialNet.toServer(new SocialNet.BoardAction(menu.containerId, SocialNet.BoardAction.Action.REFRESH, 0, 0, ""));
        }
    }

    private int step() {
        return minecraft != null && minecraft.hasShiftDown() ? 16 : 1;
    }

    private void setAmount(int a) {
        amount = Mth.clamp(a, 1, Contracts.MAX_AMOUNT);
        amountBox.setValue(String.valueOf(amount));
    }

    @Override
    public void removed() {
        ContractMenu.posting = false;
        super.removed();
    }

    private void setPosting(boolean p) {
        posting = p;
        update();
    }

    private void act(SocialNet.BoardAction.Action a) {
        if (selected >= 0) {
            SocialNet.toServer(new SocialNet.BoardAction(menu.containerId, a, selected, 0, ""));
        }
    }

    private SocialNet.ContractView current() {
        if (board == null) {
            return null;
        }
        for (SocialNet.ContractView c : board.contracts()) {
            if (c.id() == selected) {
                return c;
            }
        }
        return null;
    }

    private void update() {
        ContractMenu.posting = posting;
        if (post == null) {
            return;
        }
        keepNote = note.getValue();
        boolean on = ClientSocial.on(3);
        for (var w : List.of(minus, plus, post)) {
            w.visible = posting;
        }
        amountBox.visible = posting;
        note.visible = posting;
        SocialNet.ContractView c = current();
        deliver.visible = !posting && (c == null || !c.mine());
        cancel.visible = !posting && c != null && c.mine();
        deliver.active = on && c != null && !c.mine();
        cancel.active = c != null && c.mine();
        post.active = on && !menu.wantedItem().isEmpty();
        if (!posting && (note.isFocused() || amountBox.isFocused())) {
            setFocused(null);
        }
    }

    // ------------------------------------------------------------------ drawing
    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        WfGui.window(g, font, title, leftPos, topPos, imageWidth, imageHeight);
        WfGui.sprite(g, WfGui.CARD, leftPos + CARD_X, topPos + LIST_Y, CARD_W, CARD_H);
        if (posting) {
            WfGui.sprite(g, WfGui.INSET, leftPos + LIST_X, topPos + LIST_Y + 64, LIST_W, 18);
            WfGui.sprite(g, WfGui.INSET, leftPos + ContractMenu.WANT_X + 38, topPos + ContractMenu.WANT_Y, 38, 16);
            WfGui.sprite(g, WfGui.INSET, leftPos + ContractMenu.REWARD_X - 3, topPos + ContractMenu.REWARD_Y - 3, 60, 42);
        } else {
            WfGui.sprite(g, WfGui.INSET, leftPos + LIST_X, topPos + LIST_Y, LIST_W, LIST_H);
        }
        for (Slot slot : menu.slots) {
            if (slot.isActive()) {
                WfGui.sprite(g, menu.isWantedSlot(slot) ? WfGui.ROW_SELECTED : WfGui.INSET, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
            }
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        int cx = CARD_X + CARD_W / 2;
        if (posting) {
            List<FormattedCharSequence> help = font.split(Component.translatable("gui.brasshaven.contract.post_help"), LIST_W - 4);
            for (int i = 0; i < Math.min(6, help.size()); i++) {
                g.text(font, help.get(i), LIST_X + 2, LIST_Y + 2 + i * 10, WfGui.INK, false);
            }
            g.text(font, WfGui.bold(Component.translatable("gui.brasshaven.contract.wanted")), CARD_X + 8, LIST_Y + 5, WfGui.INK, false);
            g.text(font, WfGui.bold(Component.translatable("gui.brasshaven.contract.reward")), CARD_X + 8, ContractMenu.REWARD_Y - 10,
                    WfGui.INK, false);
            ItemStack w = menu.wantedItem();
            WfGui.textClipped(g, font, w.isEmpty() ? Component.translatable("gui.brasshaven.contract.sample_hint").getString()
                    : w.getHoverName().getString(), CARD_X + 8, ContractMenu.WANT_Y + 19, CARD_W - 14, WfGui.INK_SOFT, false);
            return;
        }
        drawList(g, mouseX - leftPos, mouseY - topPos);
        SocialNet.ContractView c = current();
        if (c == null) {
            List<FormattedCharSequence> lines = font.split(Component.translatable(board == null ? "gui.brasshaven.post.loading"
                    : "gui.brasshaven.contract.empty"), CARD_W - 12);
            for (int i = 0; i < lines.size(); i++) {
                WfGui.centered(g, font, lines.get(i), cx, LIST_Y + 30 + i * 10, WfGui.INK_SOFT);
            }
            return;
        }
        g.text(font, WfGui.bold(Component.translatable("gui.brasshaven.contract.wanted")), CARD_X + 8, LIST_Y + 5, WfGui.INK, false);
        g.item(c.wanted(), CARD_X + 8, LIST_Y + 16);
        WfGui.textClipped(g, font, c.amount() + " × " + c.wanted().getHoverName().getString(), CARD_X + 28, LIST_Y + 20,
                CARD_W - 34, WfGui.INK, false);
        int y = LIST_Y + 36;
        if (!c.note().isEmpty()) {
            List<FormattedCharSequence> nl = font.split(Component.literal("“" + c.note() + "”"), CARD_W - 14);
            for (int i = 0; i < Math.min(2, nl.size()); i++) {
                g.text(font, nl.get(i), CARD_X + 8, y, WfGui.INK_SOFT, false);
                y += 9;
            }
        }
        g.text(font, WfGui.bold(Component.translatable("gui.brasshaven.contract.reward")), CARD_X + 8, LIST_Y + 58, WfGui.INK, false);
        int ix = CARD_X + 8;
        for (int i = 0; i < Math.min(6, c.reward().size()); i++) {
            g.item(c.reward().get(i), ix + i * 18, LIST_Y + 68);
            g.itemDecorations(font, c.reward().get(i), ix + i * 18, LIST_Y + 68);
        }
        long hours = Math.max(0, (c.expiresAt() - System.currentTimeMillis()) / 3_600_000);
        Component by = Component.translatable("gui.brasshaven.contract.by", c.poster());
        WfGui.textClipped(g, font, by.getString() + " · " + Component.translatable(hours >= 48 ? "gui.brasshaven.contract.days_left"
                : "gui.brasshaven.contract.hours_left", hours >= 48 ? hours / 24 : hours).getString(), CARD_X + 8, LIST_Y + 90, CARD_W - 14,
                WfGui.INK_SOFT, false);
    }

    private int visibleRows() {
        return (LIST_H - 4) / ROW;
    }

    private void drawList(GuiGraphicsExtractor g, int mx, int my) {
        if (board == null) {
            return;
        }
        List<SocialNet.ContractView> list = board.contracts();
        scroll = Mth.clamp(scroll, 0, Math.max(0, list.size() - visibleRows()));
        int rx = LIST_X + 2;
        int rw = LIST_W - 4;
        for (int i = 0; i < visibleRows() && i + scroll < list.size(); i++) {
            SocialNet.ContractView c = list.get(i + scroll);
            int ry = LIST_Y + 2 + i * ROW;
            boolean hover = mx >= rx && mx < rx + rw && my >= ry && my < ry + ROW - 1;
            if (c.id() == selected) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, rx, ry, rw, ROW - 1);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, rx, ry, rw, ROW - 1);
            }
            g.item(c.wanted(), rx + 2, ry + 1);
            WfGui.textClipped(g, font, c.amount() + " × " + c.wanted().getHoverName().getString(), rx + 21, ry + 2, rw - 24,
                    c.mine() ? WfGui.GOLD : WfGui.CREAM, true);
            WfGui.textClipped(g, font, Component.translatable("gui.brasshaven.contract.by", c.poster()).getString(), rx + 21, ry + 11,
                    rw - 24, WfGui.CREAM_SOFT, true);
        }
        if (list.isEmpty()) {
            g.textWithWordWrap(font, Component.translatable("gui.brasshaven.contract.empty_list"), rx + 4, LIST_Y + 8, rw - 8, WfGui.CREAM_SOFT, true);
        }
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        update();
        super.extractRenderState(g, mouseX, mouseY, a);
        SocialNet.ContractView c = posting ? null : current();
        if (c != null) {
            int ix = leftPos + CARD_X + 8;
            int iy = topPos + LIST_Y + 68;
            for (int i = 0; i < Math.min(6, c.reward().size()); i++) {
                if (mouseX >= ix + i * 18 && mouseX < ix + i * 18 + 16 && mouseY >= iy && mouseY < iy + 16) {
                    g.setTooltipForNextFrame(font, c.reward().get(i), mouseX, mouseY);
                }
            }
            int wx = leftPos + CARD_X + 8;
            int wy = topPos + LIST_Y + 16;
            if (mouseX >= wx && mouseX < wx + 16 && mouseY >= wy && mouseY < wy + 16) {
                g.setTooltipForNextFrame(font, c.wanted(), mouseX, mouseY);
            }
        }
    }

    // ------------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (!posting && board != null) {
            double mx = event.x() - leftPos;
            double my = event.y() - topPos;
            int rx = LIST_X + 2;
            int rw = LIST_W - 4;
            List<SocialNet.ContractView> list = board.contracts();
            for (int i = 0; i < visibleRows() && i + scroll < list.size(); i++) {
                int ry = LIST_Y + 2 + i * ROW;
                if (mx >= rx && mx < rx + rw && my >= ry && my < ry + ROW - 1) {
                    selected = list.get(i + scroll).id();
                    return true;
                }
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (!posting) {
            scroll -= (int) Math.signum(scrollY);
            return true;
        }
        return super.mouseScrolled(x, y, scrollX, scrollY);
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (posting && (note.isFocused() || amountBox.isFocused()) && !event.isEscape()) {
            return getFocused().keyPressed(event) || true;
        }
        return super.keyPressed(event);
    }
}
