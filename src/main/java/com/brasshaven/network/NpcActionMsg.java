package com.brasshaven.network;

import com.brasshaven.util.NpcQuests;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/**
 * Client → server: a button of a quest giver's screen ({@link NpcQuests#ACCEPT}, {@link NpcQuests#TURN_IN},
 * {@link NpcQuests#PARCEL_AGAIN}). The server checks the reach, the role and the contract's state.
 */
public record NpcActionMsg(int entityId, String quest, int action) {
    public static final StreamCodec<RegistryFriendlyByteBuf, NpcActionMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeVarInt(msg.entityId);
                buf.writeUtf(msg.quest);
                buf.writeVarInt(msg.action);
            },
            buf -> new NpcActionMsg(buf.readVarInt(), buf.readUtf(), buf.readVarInt()));

    static void handle(NpcActionMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player != null) {
            NpcQuests.handle(player, msg.entityId, msg.quest, msg.action);
        }
    }
}
