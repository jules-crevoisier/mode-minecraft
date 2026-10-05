package com.brasshaven.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

/**
 * Server → client map data (see {@link com.brasshaven.map.MapServer} for the protocol). {@code kind}: what the
 * payload is; {@code dim}: the dimension it belongs to; {@code a}, {@code b}: region or chunk coordinates.
 */
public record MapDataMsg(int kind, String dim, int a, int b, byte[] data) {
    /** A whole 256 x 256 region (deflated {@link com.brasshaven.map.RegionData}). */
    public static final int TILE = 0;
    /** A 64 x 64 thumbnail of a region, for the zoomed-out world map. */
    public static final int MINI = 1;
    /** One freshly scanned 16 x 16 chunk of a region the client is looking at. */
    public static final int CHUNK = 2;
    /** Every waypoint the player may see and every waystone. */
    public static final int POINTS = 3;
    /** Positions of the other players of the dimension. */
    public static final int PLAYERS = 4;
    /** Someone pinged a spot (a = x, b = z; data: name and y). */
    public static final int PING = 5;

    public static final StreamCodec<RegistryFriendlyByteBuf, MapDataMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeByte(msg.kind);
                buf.writeUtf(msg.dim);
                buf.writeVarInt(msg.a);
                buf.writeVarInt(msg.b);
                buf.writeByteArray(msg.data);
            },
            buf -> new MapDataMsg(buf.readByte(), buf.readUtf(), buf.readVarInt(), buf.readVarInt(), buf.readByteArray(1 << 20)));

    static void handle(MapDataMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.brasshaven.client.ClientHooks.mapData(msg);
        }
    }
}
