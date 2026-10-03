package com.wayfarers.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.ArrayList;
import java.util.List;

/**
 * Server → client: the player's progress on every quest (titles, icons and parents come from the
 * advancement tree the client already has). {@code open} asks the client to show the journal.
 */
public record QuestSnapshotMsg(boolean open, List<State> quests) {
    public record State(String id, boolean done, int completed, int total) {}

    public static final StreamCodec<RegistryFriendlyByteBuf, QuestSnapshotMsg> STREAM_CODEC =
            StreamCodec.ofMember(QuestSnapshotMsg::encode, QuestSnapshotMsg::decode);

    private static void encode(QuestSnapshotMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeBoolean(msg.open);
        buf.writeVarInt(msg.quests.size());
        for (State s : msg.quests) {
            buf.writeUtf(s.id);
            buf.writeBoolean(s.done);
            buf.writeVarInt(s.completed);
            buf.writeVarInt(s.total);
        }
    }

    private static QuestSnapshotMsg decode(RegistryFriendlyByteBuf buf) {
        boolean open = buf.readBoolean();
        int n = buf.readVarInt();
        List<State> list = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            list.add(new State(buf.readUtf(), buf.readBoolean(), buf.readVarInt(), buf.readVarInt()));
        }
        return new QuestSnapshotMsg(open, list);
    }

    static void handle(QuestSnapshotMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.ClientHooks.questSnapshot(msg);
        }
    }
}
