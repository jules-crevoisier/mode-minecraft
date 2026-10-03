package com.wayfarers.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.api.distmarker.Dist;

import java.util.ArrayList;
import java.util.List;

/** Server → client: opens (or refreshes) the waystone travel screen. */
public record WaystoneListMsg(String current, List<Entry> entries) {
    /** One known waystone; {@code dimension} is the level id path ("overworld", "the_nether"...). */
    public record Entry(String id, String name, String dimension, int x, int y, int z, boolean pinned) {}

    public static final StreamCodec<RegistryFriendlyByteBuf, WaystoneListMsg> STREAM_CODEC =
            StreamCodec.ofMember(WaystoneListMsg::encode, WaystoneListMsg::decode);

    private static void encode(WaystoneListMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeUtf(msg.current);
        buf.writeVarInt(msg.entries.size());
        for (Entry e : msg.entries) {
            buf.writeUtf(e.id);
            buf.writeUtf(e.name, 64);
            buf.writeUtf(e.dimension);
            buf.writeVarInt(e.x);
            buf.writeVarInt(e.y);
            buf.writeVarInt(e.z);
            buf.writeBoolean(e.pinned);
        }
    }

    private static WaystoneListMsg decode(RegistryFriendlyByteBuf buf) {
        String current = buf.readUtf();
        int n = buf.readVarInt();
        List<Entry> entries = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            entries.add(new Entry(buf.readUtf(), buf.readUtf(64), buf.readUtf(), buf.readVarInt(), buf.readVarInt(),
                    buf.readVarInt(), buf.readBoolean()));
        }
        return new WaystoneListMsg(current, entries);
    }

    static void handle(WaystoneListMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.ClientHooks.openWaystones(msg);
        }
    }
}
