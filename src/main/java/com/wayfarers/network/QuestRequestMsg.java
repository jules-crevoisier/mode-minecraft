package com.wayfarers.network;

import com.wayfarers.util.QuestBook;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/** Client → server: "send me my quest progress" (and open the journal when {@code open}). */
public record QuestRequestMsg(boolean open) {
    public static final StreamCodec<RegistryFriendlyByteBuf, QuestRequestMsg> STREAM_CODEC =
            StreamCodec.ofMember((msg, buf) -> buf.writeBoolean(msg.open), buf -> new QuestRequestMsg(buf.readBoolean()));

    static void handle(QuestRequestMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player != null) {
            WayfarersNet.toPlayer(player, QuestBook.snapshot(player, msg.open));
        }
    }
}
