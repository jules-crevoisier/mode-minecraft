package com.brasshaven.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.ArrayList;
import java.util.List;

/**
 * Server → client: open (or refresh) the contracts screen of a quest giver. One entry per contract it gives, plus
 * the deliveries addressed to it that the player carries ({@code receiver}); {@code state} is a
 * {@link com.brasshaven.util.NpcQuests.State} ordinal.
 */
public record NpcDialogMsg(int entityId, String role, List<Entry> entries) {
    public record Entry(String id, int state, int progress, int needed, boolean receiver) {}

    public static final StreamCodec<RegistryFriendlyByteBuf, NpcDialogMsg> STREAM_CODEC =
            StreamCodec.ofMember(NpcDialogMsg::encode, NpcDialogMsg::decode);

    private static void encode(NpcDialogMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeVarInt(msg.entityId);
        buf.writeUtf(msg.role);
        buf.writeVarInt(msg.entries.size());
        for (Entry e : msg.entries) {
            buf.writeUtf(e.id);
            buf.writeVarInt(e.state);
            buf.writeVarInt(e.progress);
            buf.writeVarInt(e.needed);
            buf.writeBoolean(e.receiver);
        }
    }

    private static NpcDialogMsg decode(RegistryFriendlyByteBuf buf) {
        int entity = buf.readVarInt();
        String role = buf.readUtf();
        int n = buf.readVarInt();
        List<Entry> list = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            list.add(new Entry(buf.readUtf(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readBoolean()));
        }
        return new NpcDialogMsg(entity, role, list);
    }

    static void handle(NpcDialogMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.brasshaven.client.ClientHooks.npcDialog(msg);
        }
    }
}
