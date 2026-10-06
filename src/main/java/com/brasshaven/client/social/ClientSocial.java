package com.brasshaven.client.social;

import com.mojang.blaze3d.platform.InputConstants;
import com.brasshaven.Brasshaven;
import com.brasshaven.client.gui.WfGui;
import com.brasshaven.registry.ModSocial;
import com.brasshaven.social.SocialNet;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.PlayerFaceExtractor;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.bus.BusGroup;
import org.lwjgl.glfw.GLFW;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Client side of the multiplayer features: what the server told us (switches, our company, companions' health and
 * places), the keys (company screen, emote wheel, card of the player you look at), the companions HUD and the
 * screens the server opens (player card, post, board, trade).
 */
public final class ClientSocial {
    private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(Brasshaven.id("social"));
    public static final KeyMapping COMPANY_KEY = new KeyMapping("key.brasshaven.company",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_O, CATEGORY);
    public static final KeyMapping EMOTE_KEY = new KeyMapping("key.brasshaven.emotes",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_Y, CATEGORY);
    public static final KeyMapping CARD_KEY = new KeyMapping("key.brasshaven.player_card",
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_U, CATEGORY);

    /** Until the server says otherwise (an older server sends nothing): everything on, no postage. */
    public static SocialNet.Hello hello = new SocialNet.Hello(0x3F, ItemStack.EMPTY, 0, 0, 0, 8, 7);
    public static SocialNet.CompanyState company = empty();
    public static final Map<UUID, SocialNet.Status> STATUS = new HashMap<>();
    public static long statusAt;
    public static boolean hudVisible = true;

    private ClientSocial() {}

    private static SocialNet.CompanyState empty() {
        return new SocialNet.CompanyState(0, "", SocialNet.CompanyState.NOBODY, false, false, false, List.of(), List.of());
    }

    public static void init(BusGroup modBus) {
        // in game only: U over an item in an inventory is the recipe viewer's "uses" key (a GUI key), no conflict
        ((net.minecraftforge.client.extensions.IForgeKeyMapping) CARD_KEY).setKeyConflictContext(
                net.minecraftforge.client.settings.KeyConflictContext.IN_GAME);
        RegisterKeyMappingsEvent.BUS.addListener(e -> {
            e.register(COMPANY_KEY);
            e.register(EMOTE_KEY);
            e.register(CARD_KEY);
        });
        AddGuiOverlayLayersEvent.BUS.addListener(e -> e.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK,
                Brasshaven.id("company"), ForgeLayeredDraw.BOSS_OVERLAY, ClientSocial::extractHud));
        TickEvent.ClientTickEvent.Post.BUS.addListener(e -> tick());
        ClientPlayerNetworkEvent.LoggingOut.BUS.addListener(e -> {
            company = empty();
            STATUS.clear();
            hello = new SocialNet.Hello(0x3F, ItemStack.EMPTY, 0, 0, 0, 8, 7);
        });
        net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent.getBus(modBus).addListener(event -> event.enqueueWork(() -> {
            net.minecraft.client.gui.screens.MenuScreens.register(ModSocial.TRADE.get(), TradeScreen::new);
            net.minecraft.client.gui.screens.MenuScreens.register(ModSocial.POST.get(), PostScreen::new);
            net.minecraft.client.gui.screens.MenuScreens.register(ModSocial.CONTRACT_BOARD.get(), ContractScreen::new);
        }));
    }

    private static void tick() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.getConnection() == null) {
            return;
        }
        while (COMPANY_KEY.consumeClick()) {
            openCompany();
        }
        while (EMOTE_KEY.consumeClick()) {
            if (mc.gui.screen() == null) {
                mc.gui.setScreen(new EmoteWheelScreen());
            }
        }
        while (CARD_KEY.consumeClick()) {
            Entity e = mc.crosshairPickEntity;
            if (e instanceof Player p && p != mc.player) {
                SocialNet.toServer(new SocialNet.PlayerAction(SocialNet.PlayerAction.Action.CARD, p.getId(), p.getUUID()));
            } else {
                mc.player.sendOverlayMessage(net.minecraft.network.chat.Component.translatable("gui.brasshaven.card.look"));
            }
        }
    }

    public static void openCompany() {
        Minecraft.getInstance().gui.setScreen(new CompanyScreen());
        SocialNet.toServer(new SocialNet.CompanyAction(SocialNet.CompanyAction.Action.REFRESH, ""));
    }

    // ------------------------------------------------------------------ from the server
    public static void hello(SocialNet.Hello msg) {
        hello = msg;
    }

    public static void company(SocialNet.CompanyState msg) {
        company = msg;
        if (!msg.inCompany()) {
            STATUS.clear();
        } else {
            STATUS.keySet().removeIf(id -> msg.members().stream().noneMatch(m -> m.id().equals(id)));
        }
        if (Minecraft.getInstance().gui.screen() instanceof CompanyScreen s) {
            s.refresh();
        }
    }

    public static void status(SocialNet.CompanyStatus msg) {
        STATUS.clear();
        for (SocialNet.Status s : msg.members()) {
            STATUS.put(s.id(), s);
        }
        statusAt = System.currentTimeMillis();
    }

    public static void card(SocialNet.PlayerCard msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.gui.screen() == null || mc.gui.screen() instanceof PlayerCardScreen) {
            mc.gui.setScreen(new PlayerCardScreen(msg));
        }
    }

    public static void inbox(SocialNet.Inbox msg) {
        if (Minecraft.getInstance().gui.screen() instanceof PostScreen s && s.getMenu().containerId == msg.containerId()) {
            s.receive(msg);
        }
    }

    public static void board(SocialNet.Board msg) {
        if (Minecraft.getInstance().gui.screen() instanceof ContractScreen s && s.getMenu().containerId == msg.containerId()) {
            s.receive(msg);
        }
    }

    // ------------------------------------------------------------------ queries
    public static boolean on(int featureBit) {
        return hello.on(featureBit);
    }

    /** Whether this player name belongs to our company (gold frame on the maps). */
    public static boolean isCompanion(String name) {
        if (!company.inCompany()) {
            return false;
        }
        for (SocialNet.MemberInfo m : company.members()) {
            if (m.name().equals(name)) {
                return true;
            }
        }
        return false;
    }

    public static boolean leader() {
        Minecraft mc = Minecraft.getInstance();
        return mc.player != null && company.inCompany() && company.leader().equals(mc.player.getUUID());
    }

    public static String companyName() {
        if (!company.inCompany()) {
            return "";
        }
        if (!company.name().isEmpty()) {
            return company.name();
        }
        String leader = "?";
        for (SocialNet.MemberInfo m : company.members()) {
            if (m.id().equals(company.leader())) {
                leader = m.name();
            }
        }
        return net.minecraft.network.chat.Component.translatable("gui.brasshaven.company.default_name", leader).getString();
    }

    /** Distance in blocks to a companion in our dimension, or -1. */
    public static int distance(SocialNet.Status s) {
        LocalPlayer me = Minecraft.getInstance().player;
        if (me == null || !me.level().dimension().identifier().toString().equals(s.dim())) {
            return -1;
        }
        return (int) Math.sqrt(me.distanceToSqr(s.x() + 0.5, s.y(), s.z() + 0.5));
    }

    public static void face(GuiGraphicsExtractor g, UUID id, String name, int x, int y, int size) {
        var conn = Minecraft.getInstance().getConnection();
        PlayerInfo info = conn == null ? null : conn.getPlayerInfo(id);
        if (info != null) {
            PlayerFaceExtractor.extractRenderState(g, info.getSkin(), x, y, size);
        } else {
            g.fill(x, y, x + size, y + size, 0xFF3E3430);
            WfGui.centered(g, Minecraft.getInstance().font, net.minecraft.network.chat.Component.literal(
                    name.isEmpty() ? "?" : name.substring(0, 1).toUpperCase(java.util.Locale.ROOT)), x + size / 2, y + (size - 8) / 2, WfGui.CREAM);
        }
    }

    // ------------------------------------------------------------------ the companions HUD
    /**
     * Left edge, middle of the screen: a small brass-edged card per online companion, with their face, name, health
     * bar and the distance and direction to them (or their dimension). Hidden with no companion online, in a
     * screen, with F1, or from the company screen.
     */
    private static void extractHud(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (!hudVisible || mc.player == null || mc.gui.hud.isHidden() || !company.inCompany() || STATUS.isEmpty()
                || System.currentTimeMillis() - statusAt > 10_000) {
            return;
        }
        Font font = mc.font;
        List<SocialNet.Status> mates = new java.util.ArrayList<>();
        for (SocialNet.Status s : STATUS.values()) {
            if (!s.id().equals(mc.player.getUUID())) {
                mates.add(s);
            }
        }
        if (mates.isEmpty()) {
            return;
        }
        int rowH = 21;
        int w = 92;
        int x = 3;
        // a big company (company.maxSize up to 100): the nearest companions that fit, then "+N"
        int fit = Math.max(1, (g.guiHeight() - 40) / rowH);
        int hidden = 0;
        if (mates.size() > fit) {
            mates.sort(java.util.Comparator.comparingInt(s -> {
                int d = distance(s);
                return d < 0 ? Integer.MAX_VALUE : d;
            }));
            hidden = mates.size() - (fit - 1);
            mates = mates.subList(0, fit - 1);
        }
        int rows = mates.size() + (hidden > 0 ? 1 : 0);
        int y = g.guiHeight() / 2 - rows * rowH / 2;
        for (SocialNet.Status s : mates) {
            String name = "?";
            for (SocialNet.MemberInfo m : company.members()) {
                if (m.id().equals(s.id())) {
                    name = m.name();
                }
            }
            g.fill(x, y, x + w, y + rowH - 2, 0xA00F0C0A);
            g.fill(x, y, x + 1, y + rowH - 2, 0xFFB58A45);
            face(g, s.id(), name, x + 3, y + 3, 13);
            boolean leader = s.id().equals(company.leader());
            WfGui.textClipped(g, font, name, x + 19, y + 2, w - 22, leader ? WfGui.GOLD : WfGui.CREAM, true);
            // health bar
            float frac = s.maxHealth() <= 0 ? 0 : Mth.clamp(s.health() / s.maxHealth(), 0, 1);
            int bx = x + 19;
            int by = y + 12;
            int bw = 40;
            g.fill(bx - 1, by - 1, bx + bw + 1, by + 4, 0xFF0F0C0A);
            int col = frac > 0.5F ? 0xFF6FD04A : frac > 0.25F ? 0xFFF6C343 : 0xFFE0483B;
            g.fill(bx, by, bx + Math.round(bw * frac), by + 3, col);
            int d = distance(s);
            String where;
            if (d < 0) {
                String dim = s.dim().substring(s.dim().indexOf(':') + 1);
                where = net.minecraft.network.chat.Component.translatable("gui.brasshaven.dim." + dim).getString();
            } else {
                where = d >= 1000 ? String.format(java.util.Locale.ROOT, "%.1fk", d / 1000.0) : d + "m";
                arrow(g, mc.player, s, x + w - 8, y + 13);
            }
            g.text(font, where, bx + bw + 4, by - 2, WfGui.CREAM_SOFT, true);
            y += rowH;
        }
        if (hidden > 0) {
            g.fill(x, y, x + w, y + 12, 0xA00F0C0A);
            g.text(font, "+" + hidden, x + 6, y + 2, WfGui.CREAM_SOFT, true);
        }
    }

    /** A little gold arrow pointing at a companion, relative to where we look. */
    private static void arrow(GuiGraphicsExtractor g, LocalPlayer me, SocialNet.Status s, int cx, int cy) {
        double dx = s.x() + 0.5 - me.getX();
        double dz = s.z() + 0.5 - me.getZ();
        // screen angle: 0 = right, -90 = up (straight ahead)
        double ang = Math.atan2(dz, dx) - Math.toRadians(me.getYRot()) - Math.PI;
        for (int i = 0; i < 5; i++) {
            int px = cx + (int) Math.round(Math.cos(ang) * (i - 2));
            int py = cy + (int) Math.round(Math.sin(ang) * (i - 2));
            g.fill(px, py, px + 1, py + 1, i == 4 ? 0xFFFFF4B0 : 0xFFF6C343);
        }
        int hx = cx + (int) Math.round(Math.cos(ang) * 2);
        int hy = cy + (int) Math.round(Math.sin(ang) * 2);
        g.fill(hx - 1, hy - 1, hx + 2, hy + 2, 0xFFF6C343);
    }
}
