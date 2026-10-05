package com.brasshaven.client.social;

import com.brasshaven.client.gui.WfButton;
import com.brasshaven.client.gui.WfGui;
import com.brasshaven.client.gui.WfWidgets;
import com.brasshaven.social.SocialNet;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * The Company screen (key O): your companions with their health and where they are, the leader's switches
 * (friendly fire, shared experience), your company chat switch, inviting by name, and per companion: travel to them
 * from a waystone, make them leader, remove them. Without a company: found one, or answer the invitations waiting.
 * Everything is a request to the server, which checks rank, size and distances; the screen refreshes from the
 * server's answer.
 */
public class CompanyScreen extends Screen {
    private static final int W = 320;
    private static final int H = 200;
    private static final int LIST_X = 12;
    private static final int LIST_Y = 30;
    private static final int LIST_W = 172;
    private static final int LIST_H = 140;
    private static final int ROW = 24;
    private static final int SIDE_X = 192;
    private static final int SIDE_W = 116;

    private int left;
    private int top;
    private UUID selected;
    private int scroll;
    private EditBox nameBox;
    private final List<Runnable> refreshers = new ArrayList<>();

    public CompanyScreen() {
        super(Component.translatable("gui.brasshaven.company.title"));
    }

    private static SocialNet.CompanyState c() {
        return ClientSocial.company;
    }

    private static void send(SocialNet.CompanyAction.Action a, String arg) {
        SocialNet.toServer(new SocialNet.CompanyAction(a, arg));
    }

    /** The server changed something: rebuild the buttons for the new state. */
    public void refresh() {
        String typed = nameBox == null ? "" : nameBox.getValue();
        rebuildWidgets();
        if (nameBox != null) {
            nameBox.setValue(typed);
        }
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = WfGui.windowTop(height, H, 13);
        refreshers.clear();
        boolean on = ClientSocial.on(0);
        int sx = left + SIDE_X;
        nameBox = new EditBox(font, sx + 2, top + 114, SIDE_W - 4, 12, Component.translatable("gui.brasshaven.company.name_hint"));
        nameBox.setMaxLength(24);
        nameBox.setTextColor(WfGui.CREAM);
        nameBox.setBordered(false);
        if (!c().inCompany()) {
            nameBox.setHint(Component.translatable("gui.brasshaven.company.name_hint").withColor(WfGui.MUTED));
            addRenderableWidget(nameBox);
            WfButton found = addRenderableWidget(new WfButton(sx, top + 130, SIDE_W, 18, Component.translatable("gui.brasshaven.company.found"),
                    b -> send(SocialNet.CompanyAction.Action.CREATE, nameBox.getValue())));
            found.active = on;
            found.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.company.found.tip")));
            return;
        }
        boolean leader = ClientSocial.leader();
        int y = top + 34;
        toggle(sx, y, "friendly_fire", () -> c().friendlyFire(), SocialNet.CompanyAction.Action.FRIENDLY_FIRE, leader && on);
        toggle(sx, y + 18, "share_xp", () -> c().shareXp(), SocialNet.CompanyAction.Action.SHARE_XP, leader && on);
        toggle(sx, y + 36, "chat", () -> c().chat(), SocialNet.CompanyAction.Action.CHAT, on);
        addRenderableWidget(new WfWidgets.Toggle(sx, y + 54, Component.translatable("gui.brasshaven.company.hud"),
                Component.translatable("gui.brasshaven.company.hud.tip"), () -> ClientSocial.hudVisible,
                () -> ClientSocial.hudVisible = !ClientSocial.hudVisible));
        // invite (leader) or rename (leader) share the name field
        nameBox.setHint(Component.translatable("gui.brasshaven.company.player_hint").withColor(WfGui.MUTED));
        addRenderableWidget(nameBox);
        nameBox.active = leader && on;
        nameBox.setEditable(leader && on);
        int half = (SIDE_W - 4) / 2;
        WfButton invite = addRenderableWidget(new WfButton(sx, top + 130, half, 16, Component.translatable("gui.brasshaven.company.invite"),
                b -> send(SocialNet.CompanyAction.Action.INVITE, nameBox.getValue())));
        invite.active = leader && on && c().members().size() < ClientSocial.hello.maxCompany();
        invite.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.company.invite.tip")));
        WfButton rename = addRenderableWidget(new WfButton(sx + half + 4, top + 130, half, 16, Component.translatable("gui.brasshaven.company.rename"),
                b -> send(SocialNet.CompanyAction.Action.RENAME, nameBox.getValue())));
        rename.active = leader && on;
        rename.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.company.rename.tip")));
        // the selected companion
        WfButton join = addRenderableWidget(new WfButton(sx, top + 152, SIDE_W, 16, Component.translatable("gui.brasshaven.company.join"),
                b -> send(SocialNet.CompanyAction.Action.JOIN, selected.toString())));
        join.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.company.join.tip", ClientSocial.hello.joinCost())));
        WfButton promote = addRenderableWidget(new WfButton(sx, top + 172, half, 16, Component.translatable("gui.brasshaven.company.promote"),
                b -> send(SocialNet.CompanyAction.Action.PROMOTE, selected.toString())));
        promote.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.company.promote.tip")));
        WfButton kick = addRenderableWidget(new WfButton(sx + half + 4, top + 172, half, 16, Component.translatable("gui.brasshaven.company.kick"),
                b -> send(SocialNet.CompanyAction.Action.KICK, selected.toString())));
        kick.setTooltip(Tooltip.create(Component.translatable("gui.brasshaven.company.kick.tip")));
        refreshers.add(() -> {
            boolean other = selected != null && Minecraft.getInstance().player != null
                    && !selected.equals(Minecraft.getInstance().player.getUUID());
            boolean online = other && c().members().stream().anyMatch(m -> m.id().equals(selected) && m.online());
            join.active = on && online;
            promote.active = on && leader && other;
            kick.active = on && leader && other;
        });
        addRenderableWidget(new WfButton(left + LIST_X, top + LIST_Y + LIST_H + 4, LIST_W, 16,
                Component.translatable("gui.brasshaven.company.leave"), b -> send(SocialNet.CompanyAction.Action.LEAVE, "")));
    }

    private void toggle(int x, int y, String key, java.util.function.BooleanSupplier state, SocialNet.CompanyAction.Action a, boolean active) {
        WfWidgets.Toggle t = addRenderableWidget(new WfWidgets.Toggle(x, y, Component.translatable("gui.brasshaven.company." + key),
                Component.translatable("gui.brasshaven.company." + key + ".tip"), state, () -> send(a, "")));
        t.active = active;
    }

    // ------------------------------------------------------------------ drawing
    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        for (Runnable r : refreshers) {
            r.run();
        }
        Component title = c().inCompany() ? Component.literal(ClientSocial.companyName()) : this.title;
        WfGui.window(g, font, title, left, top, W, H);
        WfGui.sprite(g, WfGui.INSET, left + LIST_X, top + LIST_Y, LIST_W, LIST_H);
        if (c().inCompany()) {
            drawMembers(g, mouseX, mouseY);
            int sx = left + SIDE_X;
            int y = top + 34;
            String[] labels = {"friendly_fire", "share_xp", "chat", "hud"};
            for (int i = 0; i < labels.length; i++) {
                WfGui.textClipped(g, font, Component.translatable("gui.brasshaven.company." + labels[i]).getString(), sx + 30, y + i * 18 + 3,
                        SIDE_W - 30, WfGui.INK, false);
            }
            WfGui.sprite(g, WfGui.INSET, sx, top + 110, SIDE_W, 18);
            g.text(font, Component.translatable("gui.brasshaven.company.size", c().members().size(), ClientSocial.hello.maxCompany()),
                    sx, top + 21, WfGui.INK_SOFT, false);
        } else {
            drawInvites(g, mouseX, mouseY);
            int sx = left + SIDE_X;
            g.textWithWordWrap(font, Component.translatable("gui.brasshaven.company.none"), sx, top + 30, SIDE_W, WfGui.INK, false);
            WfGui.sprite(g, WfGui.INSET, sx, top + 110, SIDE_W, 18);
        }
        super.extractRenderState(g, mouseX, mouseY, a);
        g.centeredText(font, Component.translatable("gui.brasshaven.company.hint", ClientSocial.COMPANY_KEY.getTranslatedKeyMessage()),
                left + W / 2, top + H + 4, WfGui.CREAM);
    }

    private int visibleRows() {
        return (LIST_H - 6) / ROW;
    }

    private void drawMembers(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        List<SocialNet.MemberInfo> members = c().members();
        scroll = Mth.clamp(scroll, 0, Math.max(0, members.size() - visibleRows()));
        int rx = left + LIST_X + 3;
        int rw = LIST_W - 6;
        for (int i = 0; i < visibleRows() && i + scroll < members.size(); i++) {
            SocialNet.MemberInfo m = members.get(i + scroll);
            int ry = top + LIST_Y + 3 + i * ROW;
            boolean hover = mouseX >= rx && mouseX < rx + rw && mouseY >= ry && mouseY < ry + ROW - 1;
            if (m.id().equals(selected)) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, rx, ry, rw, ROW - 1);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, rx, ry, rw, ROW - 1);
            }
            ClientSocial.face(g, m.id(), m.name(), rx + 3, ry + 3, 16);
            boolean leader = m.id().equals(c().leader());
            int nx = rx + 23;
            if (leader) {
                WfGui.sprite(g, WfGui.icon("social_crown"), nx, ry + 1, 10, 10);
                nx += 11;
            }
            WfGui.textClipped(g, font, m.name(), nx, ry + 3, rw - (nx - rx) - 12, leader ? WfGui.GOLD : m.online() ? WfGui.CREAM : WfGui.MUTED, true);
            // online lamp
            g.fill(rx + rw - 8, ry + 4, rx + rw - 3, ry + 9, 0xFF0F0C0A);
            g.fill(rx + rw - 7, ry + 5, rx + rw - 4, ry + 8, m.online() ? 0xFF7CE35A : 0xFF5A4F45);
            SocialNet.Status s = ClientSocial.STATUS.get(m.id());
            if (s != null && m.online()) {
                float frac = s.maxHealth() <= 0 ? 0 : Mth.clamp(s.health() / s.maxHealth(), 0, 1);
                int bx = rx + 23;
                int by = ry + 15;
                g.fill(bx - 1, by - 1, bx + 61, by + 4, 0xFF0F0C0A);
                g.fill(bx, by, bx + Math.round(60 * frac), by + 3, frac > 0.5F ? 0xFF6FD04A : frac > 0.25F ? 0xFFF6C343 : 0xFFE0483B);
                int d = ClientSocial.distance(s);
                String where = d < 0 ? Component.translatable("gui.brasshaven.dim." + s.dim().substring(s.dim().indexOf(':') + 1)).getString()
                        : d + " m";
                WfGui.textClipped(g, font, where, bx + 66, by - 2, rw - 92, WfGui.CREAM_SOFT, true);
            } else if (!m.online()) {
                g.text(font, Component.translatable("gui.brasshaven.company.offline"), rx + 23, ry + 13, WfGui.MUTED, true);
            }
        }
    }

    private void drawInvites(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        List<SocialNet.Invite> inv = c().invites();
        int rx = left + LIST_X + 6;
        if (inv.isEmpty()) {
            g.textWithWordWrap(font, Component.translatable("gui.brasshaven.company.no_invites"), rx, top + LIST_Y + 8, LIST_W - 12,
                    WfGui.CREAM_SOFT, true);
            return;
        }
        g.text(font, Component.translatable("gui.brasshaven.company.invites"), rx, top + LIST_Y + 6, WfGui.GOLD, true);
        for (int i = 0; i < Math.min(4, inv.size()); i++) {
            SocialNet.Invite v = inv.get(i);
            int ry = top + LIST_Y + 20 + i * 26;
            WfGui.textClipped(g, font, v.companyName(), rx, ry, LIST_W - 70, WfGui.CREAM, true);
            WfGui.textClipped(g, font, Component.translatable("gui.brasshaven.company.invited_by", v.from()).getString(), rx, ry + 10,
                    LIST_W - 70, WfGui.CREAM_SOFT, true);
            drawSmall(g, "gui.brasshaven.company.accept", rx + LIST_W - 64, ry, mouseX, mouseY);
            drawSmall(g, "gui.brasshaven.company.decline", rx + LIST_W - 64, ry + 11, mouseX, mouseY);
        }
    }

    private void drawSmall(GuiGraphicsExtractor g, String key, int x, int y, int mouseX, int mouseY) {
        boolean hover = mouseX >= x && mouseX < x + 52 && mouseY >= y && mouseY < y + 10;
        WfGui.sprite(g, hover ? WfGui.BUTTON_HOVER : WfGui.BUTTON, x, y, 52, 10);
        WfGui.centered(g, font, Component.translatable(key), x + 26, y + 1, WfGui.PLATE_INK);
    }

    // ------------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x();
        double my = event.y();
        if (c().inCompany()) {
            int rx = left + LIST_X + 3;
            int rw = LIST_W - 6;
            List<SocialNet.MemberInfo> members = c().members();
            for (int i = 0; i < visibleRows() && i + scroll < members.size(); i++) {
                int ry = top + LIST_Y + 3 + i * ROW;
                if (mx >= rx && mx < rx + rw && my >= ry && my < ry + ROW - 1) {
                    selected = members.get(i + scroll).id();
                    return true;
                }
            }
        } else {
            List<SocialNet.Invite> inv = c().invites();
            int rx = left + LIST_X + 6 + LIST_W - 64;
            for (int i = 0; i < Math.min(4, inv.size()); i++) {
                int ry = top + LIST_Y + 20 + i * 26;
                if (mx >= rx && mx < rx + 52) {
                    if (my >= ry && my < ry + 10) {
                        send(SocialNet.CompanyAction.Action.ACCEPT, String.valueOf(inv.get(i).companyId()));
                        return true;
                    }
                    if (my >= ry + 11 && my < ry + 21) {
                        send(SocialNet.CompanyAction.Action.DECLINE, String.valueOf(inv.get(i).companyId()));
                        return true;
                    }
                }
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        scroll -= (int) Math.signum(scrollY);
        return true;
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (nameBox != null && nameBox.isFocused() && !event.isEscape()) {
            if (event.key() == 257 || event.key() == 335) {
                send(c().inCompany() ? SocialNet.CompanyAction.Action.INVITE : SocialNet.CompanyAction.Action.CREATE, nameBox.getValue());
                return true;
            }
            return nameBox.keyPressed(event) || true;
        }
        if (ClientSocial.COMPANY_KEY.matches(event)) {
            onClose();
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
