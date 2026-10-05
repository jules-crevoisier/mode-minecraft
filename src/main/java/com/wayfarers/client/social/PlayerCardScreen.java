package com.wayfarers.client.social;

import com.wayfarers.client.gui.WfButton;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.social.SocialNet;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * The card of another player (sneak + right-click on them, or look at them and press the card key): their face,
 * name, company and duel record, and what you can do together: trade, duel, invite them to your company, wave.
 * Each button only asks the server, which checks everything again.
 */
public class PlayerCardScreen extends Screen {
    private static final int W = 230;
    private static final int H = 132;

    private final SocialNet.PlayerCard card;
    private int left;
    private int top;

    public PlayerCardScreen(SocialNet.PlayerCard card) {
        super(Component.literal(card.name()));
        this.card = card;
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = WfGui.windowTop(height, H, 13);
        int bw = (W - 24 - 8) / 3;
        int y = top + 78;
        WfButton trade = addRenderableWidget(new WfButton(left + 12, y, bw, 20, Component.translatable("gui.wayfarers.card.trade"),
                b -> send(SocialNet.PlayerAction.Action.TRADE)));
        trade.active = ClientSocial.on(1);
        trade.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.card.trade.tip")));
        WfButton duel = addRenderableWidget(new WfButton(left + 16 + bw, y, bw, 20, Component.translatable("gui.wayfarers.card.duel"),
                b -> send(SocialNet.PlayerAction.Action.DUEL)));
        duel.active = ClientSocial.on(5);
        duel.setTooltip(Tooltip.create(Component.translatable("gui.wayfarers.card.duel.tip")));
        WfButton invite = addRenderableWidget(new WfButton(left + 20 + 2 * bw, y, bw, 20, Component.translatable("gui.wayfarers.card.invite"),
                b -> send(SocialNet.PlayerAction.Action.INVITE)));
        invite.active = ClientSocial.on(0) && card.relation() == 2;
        invite.setTooltip(Tooltip.create(Component.translatable(card.relation() == 1 ? "gui.wayfarers.card.invite.same"
                : card.relation() == 2 ? "gui.wayfarers.card.invite.tip" : "gui.wayfarers.card.invite.no")));
        int y2 = top + 104;
        WfButton wave = addRenderableWidget(new WfButton(left + 12, y2, bw, 18, Component.translatable("gui.wayfarers.emote.wave"), b -> {
            SocialNet.toServer(new SocialNet.EmoteAction(0));
            onClose();
        }));
        wave.active = ClientSocial.on(4);
        WfButton bow = addRenderableWidget(new WfButton(left + 16 + bw, y2, bw, 18, Component.translatable("gui.wayfarers.emote.bow"), b -> {
            SocialNet.toServer(new SocialNet.EmoteAction(1));
            onClose();
        }));
        bow.active = ClientSocial.on(4);
        addRenderableWidget(new WfButton(left + 20 + 2 * bw, y2, bw, 18, Component.translatable("gui.done"), b -> onClose()));
    }

    private void send(SocialNet.PlayerAction.Action action) {
        SocialNet.toServer(new SocialNet.PlayerAction(action, -1, card.id()));
        onClose();
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, Component.translatable("gui.wayfarers.card.title"), left, top, W, H);
        WfGui.sprite(g, WfGui.INSET, left + 12, top + 18, 40, 40);
        ClientSocial.face(g, card.id(), card.name(), left + 16, top + 22, 32);
        WfGui.titleClipped(g, font, card.name(), left + 60 + (W - 72) / 2, top + 20, W - 72, WfGui.INK);
        int cx = left + 60 + (W - 72) / 2;
        Component company = card.company().isEmpty() ? Component.translatable("gui.wayfarers.card.no_company")
                : Component.translatable("gui.wayfarers.card.company", card.company());
        WfGui.centered(g, font, card.relation() == 1 ? Component.translatable("gui.wayfarers.card.companion") : company, cx, top + 34,
                card.relation() == 1 ? WfGui.INK_GREEN : WfGui.INK_SOFT);
        WfGui.centered(g, font, Component.translatable("gui.wayfarers.card.record", card.wins(), card.losses(), card.draws()), cx,
                top + 46, WfGui.INK_SOFT);
        super.extractRenderState(g, mouseX, mouseY, a);
        g.centeredText(font, Component.translatable("gui.wayfarers.card.hint", ClientSocial.CARD_KEY.getTranslatedKeyMessage()),
                left + W / 2, top + H + 4, WfGui.CREAM);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
