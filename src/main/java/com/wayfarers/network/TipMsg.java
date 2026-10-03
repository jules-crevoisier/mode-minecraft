package com.wayfarers.network;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

/** Server → client: show a one-time tip card (see util/Tips and tools/wf/guide.py TIPS). */
public record TipMsg(String tip) {
    public static final StreamCodec<RegistryFriendlyByteBuf, TipMsg> STREAM_CODEC =
            StreamCodec.ofMember((msg, buf) -> buf.writeUtf(msg.tip), buf -> new TipMsg(buf.readUtf()));

    static void handle(TipMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.TipCards.show(msg.tip());
        }
    }
}
