package com.brasshaven.network;

import com.brasshaven.Brasshaven;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.network.Channel;
import net.minecraftforge.network.ChannelBuilder;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.SimpleChannel;

/**
 * The mod's network channel. Screens are opened by the server (it owns the data) with a snapshot
 * message, and the client answers with small action messages that the server validates.
 */
public final class BrasshavenNet {
    /**
     * gradle.properties {@code network_protocol}: bump it when a message is added, removed or changes its encoding
     * (not for every release; the mod version itself is checked by release.VersionGate).
     */
    private static final int VERSION = com.brasshaven.release.BuildInfo.PROTOCOL;

    public static final SimpleChannel CHANNEL = ChannelBuilder.named(Brasshaven.id("main"))
            .networkProtocolVersion(VERSION)
            .clientAcceptedVersions(Channel.VersionTest.exact(VERSION))
            .serverAcceptedVersions(Channel.VersionTest.exact(VERSION))
            .simpleChannel()
            .play()
                .clientbound()
                    .addMain(WaystoneListMsg.class, WaystoneListMsg.STREAM_CODEC, WaystoneListMsg::handle)
                    .addMain(QuestSnapshotMsg.class, QuestSnapshotMsg.STREAM_CODEC, QuestSnapshotMsg::handle)
                    .addMain(TipMsg.class, TipMsg.STREAM_CODEC, TipMsg::handle)
                    .addMain(TerminalContentsMsg.class, TerminalContentsMsg.STREAM_CODEC, TerminalContentsMsg::handle)
                    .addMain(SkillSyncMsg.class, SkillSyncMsg.STREAM_CODEC, SkillSyncMsg::handle)
                    .addMain(ChiselSyncMsg.class, ChiselSyncMsg.STREAM_CODEC, ChiselSyncMsg::handle)
                    .addMain(TerminalLinksMsg.class, TerminalLinksMsg.STREAM_CODEC, TerminalLinksMsg::handle)
                    .addMain(MapDataMsg.class, MapDataMsg.STREAM_CODEC, MapDataMsg::handle)
                    .addMain(NpcDialogMsg.class, NpcDialogMsg.STREAM_CODEC, NpcDialogMsg::handle)
                    .addMain(ContractSyncMsg.class, ContractSyncMsg.STREAM_CODEC, ContractSyncMsg::handle)
                .serverbound()
                    .addMain(WaystoneActionMsg.class, WaystoneActionMsg.STREAM_CODEC, WaystoneActionMsg::handle)
                    .addMain(QuestRequestMsg.class, QuestRequestMsg.STREAM_CODEC, QuestRequestMsg::handle)
                    .addMain(ContainerActionMsg.class, ContainerActionMsg.STREAM_CODEC, ContainerActionMsg::handle)
                    .addMain(TerminalClickMsg.class, TerminalClickMsg.STREAM_CODEC, TerminalClickMsg::handle)
                    .addMain(SkillActionMsg.class, SkillActionMsg.STREAM_CODEC, SkillActionMsg::handle)
                    .addMain(WandModeMsg.class, WandModeMsg.STREAM_CODEC, WandModeMsg::handle)
                    .addMain(TerminalToggleMsg.class, TerminalToggleMsg.STREAM_CODEC, TerminalToggleMsg::handle)
                    .addMain(MapActionMsg.class, MapActionMsg.STREAM_CODEC, MapActionMsg::handle)
                    .addMain(NpcActionMsg.class, NpcActionMsg.STREAM_CODEC, NpcActionMsg::handle)
            .build();

    private BrasshavenNet() {}

    /** Touching the class builds the channel; must happen during mod construction. */
    public static void init() {
        Brasshaven.LOGGER.debug("Network channel {} v{}", CHANNEL.getName(), VERSION);
    }

    public static void toPlayer(ServerPlayer player, Object msg) {
        CHANNEL.send(msg, PacketDistributor.PLAYER.with(player));
    }

    public static void toServer(Object msg) {
        CHANNEL.send(msg, PacketDistributor.SERVER.noArg());
    }
}
