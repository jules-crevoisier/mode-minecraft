package com.wayfarers.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/**
 * Client → server map actions (see {@link com.wayfarers.map.MapServer}): ask for regions, add / edit / delete a
 * waypoint, or ping a spot for everyone. The payload is small and validated by the server.
 */
public record MapActionMsg(int kind, byte[] data) {
    public static final int REQUEST = 0;
    public static final int WAYPOINT_ADD = 1;
    public static final int WAYPOINT_EDIT = 2;
    public static final int WAYPOINT_DELETE = 3;
    public static final int PING = 4;

    public static final StreamCodec<RegistryFriendlyByteBuf, MapActionMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeByte(msg.kind);
                buf.writeByteArray(msg.data);
            },
            buf -> new MapActionMsg(buf.readByte(), buf.readByteArray(8192)));

    static void handle(MapActionMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player != null) {
            com.wayfarers.map.MapServer.handle(player, msg);
        }
    }
}
