package com.brasshaven.client;

import com.brasshaven.Brasshaven;
import com.brasshaven.config.BrasshavenClientConfig;
import com.brasshaven.release.BuildInfo;
import com.brasshaven.release.UpdateChecker;
import com.brasshaven.release.VersionGate;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.toasts.SystemToast;
import net.minecraft.client.gui.screens.DisconnectedScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.multiplayer.JoinMultiplayerScreen;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.CommonComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.client.gui.ModMismatchDisconnectedScreen;
import net.minecraftforge.event.network.ConnectionStartEvent;
import net.minecraftforge.network.NetworkContext;
import net.minecraftforge.network.packets.ModVersions;

import java.net.URI;

/**
 * Client side of releases: the update notice (a toast on the title screen, a chat line with the changelog link after
 * joining a world, once per launch) and a clear message when the server runs another Brasshaven version.
 */
public final class ReleaseClient {
    /** The connection being made to a server: Forge has its mod list once the handshake started. */
    private static volatile Connection connecting;
    private static boolean toastShown;
    private static boolean chatShown;

    private ReleaseClient() {}

    public static void register() {
        ConnectionStartEvent.BUS.addListener(e -> {
            if (e.isClient()) {
                connecting = e.getConnection();
            }
        });
        ScreenEvent.Opening.BUS.addListener(ReleaseClient::onScreenOpening);
        ClientPlayerNetworkEvent.LoggingIn.BUS.addListener(ReleaseClient::onJoin);
    }

    private static void onScreenOpening(ScreenEvent.Opening event) {
        if (event.getNewScreen() instanceof ModMismatchDisconnectedScreen) {
            // Forge refused the server (network protocol or registries differ): say which versions, and where to get
            // the right one, instead of the raw channel/registry table
            String server = serverVersion(connecting);
            if (server != null && !server.equals(BuildInfo.version())) {
                event.setNewScreen(new DisconnectedScreen(new JoinMultiplayerScreen(new TitleScreen()),
                        CommonComponents.CONNECT_FAILED,
                        VersionGate.mismatch(server, BuildInfo.version(), BuildInfo.DOWNLOAD_URL)));
            }
        } else if (event.getNewScreen() instanceof TitleScreen && !toastShown && enabled()) {
            toastShown = true;
            UpdateChecker.check().thenAccept(r -> r.ifPresent(rel -> Minecraft.getInstance().execute(() ->
                    SystemToast.addOrUpdate(Minecraft.getInstance().gui.toastManager(),
                            SystemToast.SystemToastId.PERIODIC_NOTIFICATION,
                            Component.translatable("toast.brasshaven.update.title"),
                            Component.translatable("toast.brasshaven.update.body", rel.version(), BuildInfo.version())))));
        }
    }

    private static void onJoin(ClientPlayerNetworkEvent.LoggingIn event) {
        String server = serverVersion(event.getConnection());
        if (server != null && !server.equals(BuildInfo.version())) {
            // the server let us in (compat.requireSameVersion off, or an older server): still worth knowing
            event.getPlayer().sendSystemMessage(Component.translatable("message.brasshaven.version.server_differs",
                    server, BuildInfo.version()).withStyle(ChatFormatting.GOLD));
        }
        if (chatShown || !enabled()) {
            return;
        }
        UpdateChecker.check().thenAccept(r -> r.ifPresent(rel -> Minecraft.getInstance().execute(() -> {
            Minecraft mc = Minecraft.getInstance();
            if (chatShown || mc.player == null) {
                return;
            }
            chatShown = true;
            mc.player.sendSystemMessage(Component.translatable("message.brasshaven.update.available",
                    rel.version(), BuildInfo.version(), link(rel.url())).withStyle(ChatFormatting.AQUA));
        })));
    }

    private static MutableComponent link(String url) {
        MutableComponent c = Component.translatable("message.brasshaven.update.changelog")
                .withStyle(ChatFormatting.UNDERLINE, ChatFormatting.YELLOW);
        try {
            URI uri = URI.create(url);
            if ("https".equals(uri.getScheme())) {
                c = c.withStyle(s -> s.withClickEvent(new ClickEvent.OpenUrl(uri)));
            }
        } catch (IllegalArgumentException e) {
            Brasshaven.LOGGER.debug("Brasshaven: bad release link {}", url);
        }
        return c;
    }

    private static boolean enabled() {
        return BrasshavenClientConfig.UPDATE_CHECK.get() && !UpdateChecker.disabledHere();
    }

    /** The Brasshaven version the server announced in the Forge handshake, or null (no handshake, no mod). */
    private static String serverVersion(Connection connection) {
        if (connection == null) {
            return null;
        }
        try {
            ModVersions.Info info = NetworkContext.get(connection).getModList().get(Brasshaven.MODID);
            return info == null ? null : info.version();
        } catch (RuntimeException e) {
            return null;
        }
    }
}
