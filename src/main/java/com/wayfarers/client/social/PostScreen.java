package com.wayfarers.client.social;

import com.wayfarers.client.gui.WfButton;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.client.gui.WfWidgets;
import com.wayfarers.social.PostMenu;
import com.wayfarers.social.SocialNet;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.MultiLineEditBox;
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
import java.util.Locale;

/**
 * The Pneumatic Post: an Inbox tab (letters and parcels, newest first; the selected one is read on the parchment card,
 * its items taken with "Take items") and a Write tab (recipient with name completion, the letter, up to 6 stacks in
 * the parcel slots, the postage shown on the Send button).
 */
public class PostScreen extends AbstractContainerScreen<PostMenu> implements com.wayfarers.client.ContainerButtons.Exempt {
    private static final int LIST_X = 12;
    private static final int LIST_Y = 36;
    private static final int LIST_W = 164;
    private static final int LIST_H = 82;
    private static final int ROW = 20;
    private static final int CARD_X = 184;
    private static final int CARD_W = 134;
    private static final int CARD_H = 104;

    private SocialNet.Inbox inbox;
    private boolean writing;
    private long selected = -1;
    private int scroll;
    private int textScroll;
    private EditBox to;
    private MultiLineEditBox letter;
    private WfButton send;
    private WfButton take;
    private WfButton discard;
    private String keepTo = "";
    private String keepLetter = "";

    public PostScreen(PostMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, PostMenu.W, PostMenu.H);
    }

    public void receive(SocialNet.Inbox msg) {
        inbox = msg;
        if (selected < 0 || msg.parcels().stream().noneMatch(p -> p.id() == selected)) {
            selected = msg.parcels().isEmpty() ? -1 : msg.parcels().get(0).id();
            textScroll = 0;
        }
        updateTabs();
    }

    @Override
    protected void init() {
        super.init();
        topPos = WfGui.windowTop(height, imageHeight, 0);
        addRenderableWidget(new WfWidgets.Choice(leftPos + 12, topPos + 16, 80, 16, Component.translatable("gui.wayfarers.post.inbox"),
                Component.translatable("gui.wayfarers.post.inbox.tip"), () -> !writing, () -> setWriting(false)));
        addRenderableWidget(new WfWidgets.Choice(leftPos + 96, topPos + 16, 80, 16, Component.translatable("gui.wayfarers.post.write"),
                Component.translatable("gui.wayfarers.post.write.tip"), () -> writing, () -> setWriting(true)));
        to = new EditBox(font, leftPos + LIST_X + 22, topPos + LIST_Y + 3, LIST_W - 26, 12, Component.translatable("gui.wayfarers.post.to"));
        to.setMaxLength(16);
        to.setBordered(false);
        to.setTextColor(WfGui.CREAM);
        to.setHint(Component.translatable("gui.wayfarers.post.to_hint").withColor(WfGui.MUTED));
        to.setValue(keepTo);
        to.setResponder(s -> suggest());
        addRenderableWidget(to);
        letter = MultiLineEditBox.builder().setX(leftPos + LIST_X).setY(topPos + LIST_Y + 20)
                .setPlaceholder(Component.translatable("gui.wayfarers.post.letter_hint"))
                .build(font, LIST_W, 62, Component.translatable("gui.wayfarers.post.letter"));
        letter.setCharacterLimit(com.wayfarers.social.Post.MAX_TEXT);
        letter.setValue(keepLetter);
        addRenderableWidget(letter);
        send = addRenderableWidget(new WfButton(leftPos + LIST_X, topPos + LIST_Y + 86, LIST_W, 16, Component.empty(), b -> doSend()));
        send.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.post.send.tip")));
        take = addRenderableWidget(new WfButton(leftPos + LIST_X, topPos + LIST_Y + 86, 98, 16, Component.translatable("gui.wayfarers.post.take"),
                b -> action(SocialNet.PostAction.Action.COLLECT)));
        discard = addRenderableWidget(new WfButton(leftPos + LIST_X + 102, topPos + LIST_Y + 86, LIST_W - 102, 16,
                Component.translatable("gui.wayfarers.post.discard"), b -> action(SocialNet.PostAction.Action.DISCARD)));
        discard.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.post.discard.tip")));
        updateTabs();
        if (inbox == null) {
            SocialNet.toServer(new SocialNet.PostAction(menu.containerId, SocialNet.PostAction.Action.REFRESH, 0, "", ""));
        }
    }

    @Override
    public void removed() {
        PostMenu.composing = false;
        super.removed();
    }

    private void setWriting(boolean w) {
        writing = w;
        updateTabs();
    }

    private void updateTabs() {
        PostMenu.composing = writing;
        if (to == null) {
            return;
        }
        keepTo = to.getValue();
        keepLetter = letter.getValue();
        to.visible = writing;
        letter.visible = writing;
        send.visible = writing;
        take.visible = !writing;
        discard.visible = !writing;
        SocialNet.ParcelView p = selectedParcel();
        take.active = p != null && !p.items().isEmpty();
        discard.active = p != null && p.items().isEmpty();
        int stacks = (int) menu.slots.stream().filter(s -> menu.isParcelSlot(s) && s.hasItem()).count();
        int cost = ClientSocial.hello.postageBase() + ClientSocial.hello.postagePerStack() * stacks;
        boolean free = ClientSocial.hello.postage().isEmpty() || cost == 0;
        send.setMessage(free ? Component.translatable("gui.wayfarers.post.send")
                : Component.translatable("gui.wayfarers.post.send_cost", cost, ClientSocial.hello.postage().getHoverName()));
        send.active = ClientSocial.on(2) && !to.getValue().isBlank();
        if (!writing && (to.isFocused() || letter.isFocused())) {
            setFocused(null);
        }
    }

    private SocialNet.ParcelView selectedParcel() {
        if (inbox == null) {
            return null;
        }
        for (SocialNet.ParcelView p : inbox.parcels()) {
            if (p.id() == selected) {
                return p;
            }
        }
        return null;
    }

    private void action(SocialNet.PostAction.Action a) {
        if (selected >= 0) {
            SocialNet.toServer(new SocialNet.PostAction(menu.containerId, a, selected, "", ""));
        }
    }

    private void doSend() {
        SocialNet.toServer(new SocialNet.PostAction(menu.containerId, SocialNet.PostAction.Action.SEND, 0, to.getValue().strip(),
                letter.getValue()));
        letter.setValue("");
        keepLetter = "";
    }

    /** Greyed completion of the recipient's name from the players the server knows. */
    private void suggest() {
        String typed = to.getValue();
        to.setSuggestion(null);
        if (inbox == null || typed.isEmpty()) {
            return;
        }
        for (String n : inbox.names()) {
            if (n.toLowerCase(Locale.ROOT).startsWith(typed.toLowerCase(Locale.ROOT)) && n.length() > typed.length()) {
                to.setSuggestion(n.substring(typed.length()));
                return;
            }
        }
    }

    // ------------------------------------------------------------------ drawing
    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        WfGui.window(g, font, title, leftPos, topPos, imageWidth, imageHeight);
        WfGui.sprite(g, WfGui.CARD, leftPos + CARD_X, topPos + LIST_Y, CARD_W, CARD_H);
        if (writing) {
            WfGui.sprite(g, WfGui.INSET, leftPos + LIST_X, topPos + LIST_Y, LIST_W, 16);
            WfGui.sprite(g, WfGui.INSET, leftPos + PostMenu.ATTACH_X - 3, topPos + PostMenu.ATTACH_Y - 3, 60, 42);
        } else {
            WfGui.sprite(g, WfGui.INSET, leftPos + LIST_X, topPos + LIST_Y, LIST_W, LIST_H);
        }
        for (Slot slot : menu.slots) {
            if (slot.isActive()) {
                WfGui.sprite(g, WfGui.INSET, leftPos + slot.x - 1, topPos + slot.y - 1, 18, 18);
            }
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        int cx = CARD_X + CARD_W / 2;
        if (writing) {
            g.text(font, Component.translatable("gui.wayfarers.post.to"), LIST_X + 3, LIST_Y + 4, WfGui.CREAM_SOFT, true);
            WfGui.centered(g, font, WfGui.bold(Component.translatable("gui.wayfarers.post.parcel")), cx, LIST_Y + 4, WfGui.INK);
            List<FormattedCharSequence> hint = font.split(Component.translatable("gui.wayfarers.post.parcel_hint"), CARD_W - 10);
            for (int i = 0; i < Math.min(4, hint.size()); i++) {
                WfGui.centered(g, font, hint.get(i), cx, PostMenu.ATTACH_Y + 44 + i * 9, WfGui.INK_SOFT);
            }
            return;
        }
        drawInbox(g, mouseX - leftPos, mouseY - topPos);
        SocialNet.ParcelView p = selectedParcel();
        if (p == null) {
            List<FormattedCharSequence> lines = font.split(Component.translatable(inbox == null ? "gui.wayfarers.post.loading"
                    : "gui.wayfarers.post.empty"), CARD_W - 12);
            for (int i = 0; i < lines.size(); i++) {
                WfGui.centered(g, font, lines.get(i), cx, LIST_Y + 30 + i * 10, WfGui.INK_SOFT);
            }
            return;
        }
        WfGui.titleClipped(g, font, from(p).getString(), cx, LIST_Y + 5, CARD_W - 10, WfGui.INK);
        WfGui.centered(g, font, Component.literal(age(p.sentAt())), cx, LIST_Y + 16, WfGui.INK_SOFT);
        List<FormattedCharSequence> lines = font.split(body(p), CARD_W - 12);
        int maxLines = 6;
        textScroll = Mth.clamp(textScroll, 0, Math.max(0, lines.size() - maxLines));
        for (int i = 0; i < maxLines && i + textScroll < lines.size(); i++) {
            g.text(font, lines.get(i + textScroll), CARD_X + 6, LIST_Y + 28 + i * 9, WfGui.INK, false);
        }
        if (lines.size() > maxLines) {
            g.text(font, textScroll + maxLines < lines.size() ? "v" : "^", CARD_X + CARD_W - 9, LIST_Y + 74, WfGui.INK_SOFT, false);
        }
        int ix = CARD_X + (CARD_W - Math.min(6, p.items().size()) * 18) / 2;
        for (int i = 0; i < Math.min(6, p.items().size()); i++) {
            ItemStack s = p.items().get(i);
            g.item(s, ix + i * 18, LIST_Y + 84);
            g.itemDecorations(font, s, ix + i * 18, LIST_Y + 84);
        }
        if (p.items().size() > 6) {
            g.text(font, "+" + (p.items().size() - 6), CARD_X + CARD_W - 16, LIST_Y + 76, WfGui.INK_SOFT, false);
        }
    }

    private static Component from(SocialNet.ParcelView p) {
        return p.kind().equals("letter") ? Component.translatable("gui.wayfarers.post.from", p.from())
                : Component.translatable("gui.wayfarers.post.kind." + p.kind());
    }

    private static Component body(SocialNet.ParcelView p) {
        if (p.kind().equals("letter")) {
            return Component.literal(p.text().isEmpty() ? "" : p.text());
        }
        return Component.translatable("gui.wayfarers.post.body." + p.kind(), p.text());
    }

    private static String age(long sentAt) {
        long min = Math.max(0, (System.currentTimeMillis() - sentAt) / 60_000);
        if (min < 1) {
            return Component.translatable("gui.wayfarers.post.just_now").getString();
        }
        if (min < 60) {
            return Component.translatable("gui.wayfarers.post.minutes", min).getString();
        }
        if (min < 60 * 48) {
            return Component.translatable("gui.wayfarers.post.hours", min / 60).getString();
        }
        return Component.translatable("gui.wayfarers.post.days", min / 1440).getString();
    }

    private int visibleRows() {
        return (LIST_H - 4) / ROW;
    }

    private void drawInbox(GuiGraphicsExtractor g, int mx, int my) {
        if (inbox == null) {
            return;
        }
        List<SocialNet.ParcelView> list = inbox.parcels();
        scroll = Mth.clamp(scroll, 0, Math.max(0, list.size() - visibleRows()));
        int rx = LIST_X + 2;
        int rw = LIST_W - 4;
        for (int i = 0; i < visibleRows() && i + scroll < list.size(); i++) {
            SocialNet.ParcelView p = list.get(i + scroll);
            int ry = LIST_Y + 2 + i * ROW;
            boolean hover = mx >= rx && mx < rx + rw && my >= ry && my < ry + ROW - 1;
            if (p.id() == selected) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, rx, ry, rw, ROW - 1);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, rx, ry, rw, ROW - 1);
            }
            String icon = p.kind().equals("letter") ? (p.items().isEmpty() ? "social_mail" : "social_parcel") : "social_contract";
            WfGui.sprite(g, WfGui.icon(icon), rx + 2, ry + 1, 16, 16);
            WfGui.textClipped(g, font, from(p).getString(), rx + 21, ry + 2, rw - 24, WfGui.CREAM, true);
            String sub = p.items().isEmpty() ? p.text().replace('\n', ' ')
                    : Component.translatable("gui.wayfarers.post.stacks", p.items().size()).getString();
            WfGui.textClipped(g, font, sub, rx + 21, ry + 11, rw - 24, WfGui.CREAM_SOFT, true);
        }
        if (list.isEmpty()) {
            g.textWithWordWrap(font, Component.translatable("gui.wayfarers.post.empty_list"), rx + 4, LIST_Y + 8, rw - 8, WfGui.CREAM_SOFT, true);
        }
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        updateTabs();
        super.extractRenderState(g, mouseX, mouseY, a);
        if (!writing) {
            SocialNet.ParcelView p = selectedParcel();
            if (p != null) {
                int ix = leftPos + CARD_X + (CARD_W - Math.min(6, p.items().size()) * 18) / 2;
                int iy = topPos + LIST_Y + 84;
                for (int i = 0; i < Math.min(6, p.items().size()); i++) {
                    if (mouseX >= ix + i * 18 && mouseX < ix + i * 18 + 16 && mouseY >= iy && mouseY < iy + 16) {
                        g.setTooltipForNextFrame(font, p.items().get(i), mouseX, mouseY);
                    }
                }
            }
        } else if (inbox != null && ClientSocial.hello.postage().getCount() > 0) {
            int stacks = (int) menu.slots.stream().filter(s -> menu.isParcelSlot(s) && s.hasItem()).count();
            int cost = ClientSocial.hello.postageBase() + ClientSocial.hello.postagePerStack() * stacks;
            if (cost > 0) {
                g.item(ClientSocial.hello.postage(), leftPos + CARD_X + CARD_W - 20, topPos + LIST_Y + 2);
            }
        }
    }

    // ------------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (!writing && inbox != null) {
            double mx = event.x() - leftPos;
            double my = event.y() - topPos;
            int rx = LIST_X + 2;
            int rw = LIST_W - 4;
            List<SocialNet.ParcelView> list = inbox.parcels();
            for (int i = 0; i < visibleRows() && i + scroll < list.size(); i++) {
                int ry = LIST_Y + 2 + i * ROW;
                if (mx >= rx && mx < rx + rw && my >= ry && my < ry + ROW - 1) {
                    selected = list.get(i + scroll).id();
                    textScroll = 0;
                    if (doubleClick && !list.get(i + scroll).items().isEmpty()) {
                        action(SocialNet.PostAction.Action.COLLECT);
                    }
                    return true;
                }
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (!writing) {
            if (x >= leftPos + CARD_X) {
                textScroll -= (int) Math.signum(scrollY);
            } else {
                scroll -= (int) Math.signum(scrollY);
            }
            return true;
        }
        return super.mouseScrolled(x, y, scrollX, scrollY);
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (writing && to.isFocused() && event.key() == 258 && inbox != null) {
            // Tab completes the name
            for (String n : inbox.names()) {
                if (n.toLowerCase(Locale.ROOT).startsWith(to.getValue().toLowerCase(Locale.ROOT))) {
                    to.setValue(n);
                    break;
                }
            }
            return true;
        }
        if (writing && (to.isFocused() || letter.isFocused()) && !event.isEscape()) {
            return getFocused().keyPressed(event) || true;
        }
        return super.keyPressed(event);
    }
}
