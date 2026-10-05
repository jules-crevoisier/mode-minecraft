package com.wayfarers.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.ArrayList;
import java.util.List;

/** Server → client: the player's accepted and finished contracts (the journal's Contracts tab, the HUD tracker). */
public record ContractSyncMsg(List<Entry> contracts) {
    public record Entry(String id, boolean done, int progress, int needed) {}

    public static final StreamCodec<RegistryFriendlyByteBuf, ContractSyncMsg> STREAM_CODEC =
            StreamCodec.ofMember(ContractSyncMsg::encode, ContractSyncMsg::decode);

    private static void encode(ContractSyncMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeVarInt(msg.contracts.size());
        for (Entry e : msg.contracts) {
            buf.writeUtf(e.id);
            buf.writeBoolean(e.done);
            buf.writeVarInt(e.progress);
            buf.writeVarInt(e.needed);
        }
    }

    private static ContractSyncMsg decode(RegistryFriendlyByteBuf buf) {
        int n = buf.readVarInt();
        List<Entry> list = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            list.add(new Entry(buf.readUtf(), buf.readBoolean(), buf.readVarInt(), buf.readVarInt()));
        }
        return new ContractSyncMsg(list);
    }

    static void handle(ContractSyncMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.ClientHooks.contracts(msg);
        }
    }
}
