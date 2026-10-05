package com.wayfarers.network;

import com.wayfarers.item.BuilderWandItem;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.network.CustomPayloadEvent;

/** Client → server: the wand-mode key was pressed; cycle the symmetry of the Builder's Wand in hand. */
public record WandModeMsg() {
    public static final StreamCodec<RegistryFriendlyByteBuf, WandModeMsg> STREAM_CODEC =
            StreamCodec.ofMember((msg, buf) -> {}, buf -> new WandModeMsg());

    static void handle(WandModeMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (!com.wayfarers.util.ServerGuard.canAct(player) || !com.wayfarers.util.ServerGuard.allow(player, "wand_mode", 4, 4.0)) {
            return;
        }
        for (InteractionHand hand : InteractionHand.values()) {
            ItemStack stack = player.getItemInHand(hand);
            if (stack.getItem() instanceof BuilderWandItem) {
                BuilderWandItem.cycleSymmetry(player, stack);
                return;
            }
        }
    }
}
