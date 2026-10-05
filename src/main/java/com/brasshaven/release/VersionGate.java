package com.brasshaven.release;

import com.brasshaven.Brasshaven;
import com.brasshaven.config.BrasshavenConfig;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.server.network.ConfigurationTask;
import net.minecraftforge.event.network.GatherLoginConfigurationTasksEvent;
import net.minecraftforge.network.ConnectionType;
import net.minecraftforge.network.NetworkContext;
import net.minecraftforge.network.config.ConfigurationTaskContext;
import net.minecraftforge.network.packets.ModVersions;

import java.util.function.Consumer;

/**
 * Turns a client/server version mismatch into a clear message instead of a registry or channel error.
 *
 * <p>Server side: a login configuration task, after Forge's own (by then the client has sent its mod list), refuses a
 * client whose Brasshaven version differs from the server's ({@code compat.requireSameVersion}, on by default). The
 * reason names both versions and the download page, in the player's language when their jar knows the key and in
 * French and English otherwise (an older jar). A mismatch Forge catches first (network protocol, registries) is
 * reworded on the client by {@code client.ReleaseClient}.
 */
public final class VersionGate {
    public static final String MESSAGE_KEY = "disconnect.brasshaven.version_mismatch";
    /** Shown by jars that do not know {@link #MESSAGE_KEY} (args: server version, client version, download page). */
    private static final String FALLBACK =
            "Brasshaven : version différente / version mismatch\n\n"
            + "Ce serveur utilise Brasshaven %1$s, tu as la %2$s. Installe la même version que le serveur :\n"
            + "This server runs Brasshaven %1$s, you have %2$s. Install the same version as the server:\n\n%3$s";

    private static final ConfigurationTask.Type TYPE = new ConfigurationTask.Type(Brasshaven.MODID + ":version_check");

    private VersionGate() {}

    public static void register() {
        GatherLoginConfigurationTasksEvent.BUS.addListener(VersionGate::gather);
    }

    private static void gather(GatherLoginConfigurationTasksEvent event) {
        if (NetworkContext.get(event.getConnection()).getType() == ConnectionType.MODDED) {
            event.addTask(new Task());
        }
    }

    /** The disconnect reason: the player's language when their jar has the key, French + English otherwise. */
    public static Component mismatch(String serverVersion, String clientVersion, String url) {
        return Component.translatableWithFallback(MESSAGE_KEY, FALLBACK, serverVersion, clientVersion, url);
    }

    /** Download page players are sent to: the server's {@code compat.downloadUrl}, else the mod's own page. */
    public static String downloadUrl() {
        String url = BrasshavenConfig.DOWNLOAD_URL.get();
        return url == null || url.isBlank() ? BuildInfo.DOWNLOAD_URL : url.trim();
    }

    private static final class Task implements ConfigurationTask {
        /** Forge runs this overload (ConfigurationTask's Forge default); finishing is up to the task. */
        public void start(ConfigurationTaskContext ctx) {
            ModVersions.Info remote = NetworkContext.get(ctx.getConnection()).getModList().get(Brasshaven.MODID);
            String mine = BuildInfo.version();
            if (remote == null || remote.version().equals(mine) || !BrasshavenConfig.REQUIRE_SAME_VERSION.get()) {
                ctx.finish(TYPE);
                return;
            }
            Brasshaven.LOGGER.info("Brasshaven: a client with Brasshaven {} was refused, this server runs {} "
                    + "(compat.requireSameVersion in brasshaven-common.toml)", remote.version(), mine);
            Component reason = mismatch(mine, remote.version(), downloadUrl());
            // through the packet listener: it sends the reason to the client before closing (Connection.disconnect
            // alone would only close, and the player would see a bare "connection lost")
            if (ctx.getConnection().getPacketListener() instanceof net.minecraft.server.network.ServerCommonPacketListenerImpl listener) {
                listener.disconnect(reason);
            } else {
                ctx.getConnection().disconnect(reason);
            }
        }

        @Override
        public void start(Consumer<Packet<?>> send) {
            throw new IllegalStateException("Forge starts configuration tasks with a context");
        }

        @Override
        public Type type() {
            return TYPE;
        }
    }
}
