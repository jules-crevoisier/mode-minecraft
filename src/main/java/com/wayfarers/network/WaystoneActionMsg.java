package com.wayfarers.network;

import com.wayfarers.util.Waystones;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/** Client → server: travel to, rename or pin a waystone from the travel screen. */
public record WaystoneActionMsg(Action action, String from, String target, String text) {
    public enum Action { WARP, RENAME, PIN }

    public static final StreamCodec<RegistryFriendlyByteBuf, WaystoneActionMsg> STREAM_CODEC =
            StreamCodec.ofMember(WaystoneActionMsg::encode, WaystoneActionMsg::decode);

    private static void encode(WaystoneActionMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeEnum(msg.action);
        buf.writeUtf(msg.from);
        buf.writeUtf(msg.target);
        buf.writeUtf(msg.text, 64);
    }

    private static WaystoneActionMsg decode(RegistryFriendlyByteBuf buf) {
        return new WaystoneActionMsg(buf.readEnum(Action.class), buf.readUtf(), buf.readUtf(), buf.readUtf(64));
    }

    static void handle(WaystoneActionMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player != null) {
            Waystones.handleAction(player, msg);
        }
    }
}
