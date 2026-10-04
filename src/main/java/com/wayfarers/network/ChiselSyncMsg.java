package com.wayfarers.network;

import com.wayfarers.chisel.ChiselFamilies;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.event.network.CustomPayloadEvent;

import java.util.ArrayList;
import java.util.List;

/** Server → client: the chisel families loaded from data packs (sent on login and after /reload). */
public record ChiselSyncMsg(List<ChiselFamilies.Data> families) {
    public static final StreamCodec<RegistryFriendlyByteBuf, ChiselSyncMsg> STREAM_CODEC =
            StreamCodec.ofMember(ChiselSyncMsg::encode, ChiselSyncMsg::decode);

    private static void encode(ChiselSyncMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeVarInt(msg.families.size());
        for (ChiselFamilies.Data d : msg.families) {
            buf.writeUtf(d.id());
            buf.writeVarInt(d.blocks().size());
            d.blocks().forEach(buf::writeUtf);
        }
    }

    private static ChiselSyncMsg decode(RegistryFriendlyByteBuf buf) {
        int n = buf.readVarInt();
        List<ChiselFamilies.Data> families = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            String id = buf.readUtf();
            int m = buf.readVarInt();
            List<String> blocks = new ArrayList<>(m);
            for (int j = 0; j < m; j++) {
                blocks.add(buf.readUtf());
            }
            families.add(new ChiselFamilies.Data(id, blocks));
        }
        return new ChiselSyncMsg(families);
    }

    static void handle(ChiselSyncMsg msg, CustomPayloadEvent.Context ctx) {
        ChiselFamilies.setClient(msg.families());
    }
}
