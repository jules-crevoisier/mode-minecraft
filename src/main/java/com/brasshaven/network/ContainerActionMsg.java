package com.brasshaven.network;

import com.brasshaven.util.ContainerActions;
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
        // sorting and quick-stack walk containers (quick-stack: every chest around): a few per second at most
        if (com.brasshaven.util.ServerGuard.canAct(player) && com.brasshaven.util.ServerGuard.allow(player, "container_action", 6, 3.0)) {
            ContainerActions.run(player, msg.action);
        }
    }
}
