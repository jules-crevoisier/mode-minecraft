package com.brasshaven.network;

import com.brasshaven.accessory.AccessoryContainer;
import com.brasshaven.accessory.Accessories;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.network.CustomPayloadEvent;

/**
 * Client → server, creative mode only: the creative inventory tab changed accessory slot {@code slot} (vanilla's
 * creative slot packet only accepts the vanilla inventory slots). Like vanilla, a creative player's client is trusted
 * with the item itself; the server still checks the mode and that the item fits the slot.
 */
public record AccessoryCreativeMsg(int slot, ItemStack stack) {
    public static final StreamCodec<RegistryFriendlyByteBuf, AccessoryCreativeMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeVarInt(msg.slot);
                ItemStack.OPTIONAL_STREAM_CODEC.encode(buf, msg.stack);
            },
            buf -> new AccessoryCreativeMsg(buf.readVarInt(), ItemStack.OPTIONAL_STREAM_CODEC.decode(buf)));

    static void handle(AccessoryCreativeMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player == null || !player.hasInfiniteMaterials()) {
            return;
        }
        AccessoryContainer worn = Accessories.get(player);
        if (msg.slot < 0 || msg.slot >= worn.getContainerSize()) {
            return;
        }
        ItemStack stack = msg.stack;
        if (!stack.isEmpty() && (!worn.canPlaceItem(msg.slot, stack) || !stack.isItemEnabled(player.level().enabledFeatures()))) {
            return;
        }
        worn.setItem(msg.slot, stack.copyWithCount(Math.min(1, stack.getCount())));
        worn.setChanged();
        int index = Accessories.menuIndex(player, msg.slot);
        if (index >= 0) {
            player.inventoryMenu.setRemoteSlot(index, worn.getItem(msg.slot));
        }
        player.inventoryMenu.broadcastChanges();
    }
}
