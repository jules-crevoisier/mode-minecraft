package com.wayfarers.network;

import com.wayfarers.menu.TerminalMenu;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/** Client → server: exclude (or include again) one linked container of the open Guild Terminal's network. */
public record TerminalToggleMsg(BlockPos pos) {
    public static final StreamCodec<RegistryFriendlyByteBuf, TerminalToggleMsg> STREAM_CODEC =
            StreamCodec.ofMember((msg, buf) -> buf.writeBlockPos(msg.pos), buf -> new TerminalToggleMsg(buf.readBlockPos()));

    static void handle(TerminalToggleMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player != null && player.containerMenu instanceof TerminalMenu menu && menu.stillValid(player)) {
            menu.toggle(msg.pos);
        }
    }
}
