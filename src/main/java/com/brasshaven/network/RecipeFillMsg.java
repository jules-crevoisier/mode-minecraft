package com.brasshaven.network;

import com.brasshaven.recipe.RecipeFill;
import com.brasshaven.util.ServerGuard;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.network.CustomPayloadEvent;

/**
 * Client → server: the recipe viewer's "+" button. Names the open menu and a recipe; {@code max} is the shift-click
 * "as many as possible". The server moves the items itself (recipe/RecipeFill), with vanilla's recipe-book placement.
 */
public record RecipeFillMsg(int containerId, Identifier recipe, boolean max) {
    public static final StreamCodec<RegistryFriendlyByteBuf, RecipeFillMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeVarInt(msg.containerId);
                buf.writeIdentifier(msg.recipe);
                buf.writeBoolean(msg.max);
            },
            // a recipe id is short: bounded at decode time like the other serverbound strings (docs/SERVER_AUDIT.md S8)
            buf -> new RecipeFillMsg(buf.readVarInt(), Identifier.parse(buf.readUtf(256)), buf.readBoolean()));

    static void handle(RecipeFillMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        // the vanilla recipe book places at most a few recipes a second too
        if (ServerGuard.canAct(player) && ServerGuard.allow(player, "recipe_fill", 6, 4.0)) {
            RecipeFill.place(player, msg.containerId, msg.recipe, msg.max);
        }
    }
}
