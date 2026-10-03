package com.wayfarers.network;

import com.wayfarers.Wayfarers;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.network.Channel;
import net.minecraftforge.network.ChannelBuilder;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.SimpleChannel;

/**
 * The mod's network channel. Screens are opened by the server (it owns the data) with a snapshot
 * message, and the client answers with small action messages that the server validates.
 */
public final class WayfarersNet {
    private static final int VERSION = 1;

    public static final SimpleChannel CHANNEL = ChannelBuilder.named(Wayfarers.id("main"))
            .networkProtocolVersion(VERSION)
            .clientAcceptedVersions(Channel.VersionTest.exact(VERSION))
            .serverAcceptedVersions(Channel.VersionTest.exact(VERSION))
            .simpleChannel()
            .play()
                .clientbound()
                    .addMain(WaystoneListMsg.class, WaystoneListMsg.STREAM_CODEC, WaystoneListMsg::handle)
                .serverbound()
                    .addMain(WaystoneActionMsg.class, WaystoneActionMsg.STREAM_CODEC, WaystoneActionMsg::handle)
            .build();

    private WayfarersNet() {}

    /** Touching the class builds the channel; must happen during mod construction. */
    public static void init() {
        Wayfarers.LOGGER.debug("Network channel {} v{}", CHANNEL.getName(), VERSION);
    }

    public static void toPlayer(ServerPlayer player, Object msg) {
        CHANNEL.send(msg, PacketDistributor.PLAYER.with(player));
    }

    public static void toServer(Object msg) {
        CHANNEL.send(msg, PacketDistributor.SERVER.noArg());
    }
}
