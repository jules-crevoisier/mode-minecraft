package com.wayfarers.network;

import com.wayfarers.util.ContainerActions;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/** Client → server: one of the storage buttons of a container screen was pressed. */
public record ContainerActionMsg(ContainerActions.Action action) {
    public static final StreamCodec<RegistryFriendlyByteBuf, ContainerActionMsg> STREAM_CODEC =
            StreamCodec.ofMember((msg, buf) -> buf.writeEnum(msg.action),
                    buf -> new ContainerActionMsg(buf.readEnum(ContainerActions.Action.class)));

    static void handle(ContainerActionMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player != null && !player.isSpectator()) {
            ContainerActions.run(player, msg.action);
        }
    }
}
