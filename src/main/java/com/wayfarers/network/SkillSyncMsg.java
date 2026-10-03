package com.wayfarers.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.ArrayList;
import java.util.List;

/** Server → client: talent points, unlocked talents, selected active ability (+ its cooldown) and mana. */
public record SkillSyncMsg(int points, int earned, List<String> unlocked, String active, float mana, float maxMana,
                           long cooldownTicks) {
    public static final StreamCodec<RegistryFriendlyByteBuf, SkillSyncMsg> STREAM_CODEC =
            StreamCodec.ofMember(SkillSyncMsg::encode, SkillSyncMsg::decode);

    private static void encode(SkillSyncMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeVarInt(msg.points);
        buf.writeVarInt(msg.earned);
        buf.writeVarInt(msg.unlocked.size());
        msg.unlocked.forEach(buf::writeUtf);
        buf.writeUtf(msg.active);
        buf.writeFloat(msg.mana);
        buf.writeFloat(msg.maxMana);
        buf.writeVarLong(msg.cooldownTicks);
    }

    private static SkillSyncMsg decode(RegistryFriendlyByteBuf buf) {
        int points = buf.readVarInt();
        int earned = buf.readVarInt();
        int n = buf.readVarInt();
        List<String> unlocked = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            unlocked.add(buf.readUtf());
        }
        return new SkillSyncMsg(points, earned, unlocked, buf.readUtf(), buf.readFloat(), buf.readFloat(), buf.readVarLong());
    }

    static void handle(SkillSyncMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.ClientSkills.update(msg);
        }
    }
}
