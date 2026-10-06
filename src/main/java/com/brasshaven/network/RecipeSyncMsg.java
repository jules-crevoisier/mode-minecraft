package com.brasshaven.network;

import com.brasshaven.recipe.RecipeSync;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

/**
 * Server → client: one part of the recipe viewer's data (recipe/RecipeSync), already encoded by the server. The client
 * keeps the bytes and decodes them the first time the viewer needs them (client/recipes/ClientRecipes).
 */
public record RecipeSyncMsg(int generation, int part, int parts, byte[] data) {
    public static final StreamCodec<RegistryFriendlyByteBuf, RecipeSyncMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeVarInt(msg.generation);
                buf.writeVarInt(msg.part);
                buf.writeVarInt(msg.parts);
                buf.writeByteArray(msg.data);
            },
            buf -> new RecipeSyncMsg(buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readByteArray(RecipeSync.PART_BYTES + 4096)));

    static void handle(RecipeSyncMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.brasshaven.client.recipes.ClientRecipes.receive(msg.generation, msg.part, msg.parts, msg.data);
        }
    }
}
