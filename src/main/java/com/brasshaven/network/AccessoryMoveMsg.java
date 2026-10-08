package com.brasshaven.network;

import com.brasshaven.accessory.AccessoryContainer;
import com.brasshaven.accessory.Accessories;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.network.CustomPayloadEvent;

/**
 * Client → server: shift-click on an accessory. {@code equip}: move the item of inventory slot {@code from} (0..35, or
 * 40 the off hand) into the first free accessory slot it fits; otherwise move accessory {@code from} back into the
 * inventory. The server checks everything (the vanilla quick-move of the inventory menu doesn't know the slots).
 */
public record AccessoryMoveMsg(int from, boolean equip) {
    public static final StreamCodec<RegistryFriendlyByteBuf, AccessoryMoveMsg> STREAM_CODEC = StreamCodec.ofMember(
            (msg, buf) -> {
                buf.writeVarInt(msg.from);
                buf.writeBoolean(msg.equip);
            },
            buf -> new AccessoryMoveMsg(buf.readVarInt(), buf.readBoolean()));

    static void handle(AccessoryMoveMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player == null || player.isSpectator() || !player.isAlive()
                || !com.brasshaven.util.ServerGuard.allow(player, "accessory_move", 20, 10.0)) {
            return;
        }
        if (player.containerMenu != player.inventoryMenu || !player.inventoryMenu.getCarried().isEmpty()) {
            return; // only from the player's own inventory screen, with nothing on the cursor
        }
        Inventory inv = player.getInventory();
        AccessoryContainer worn = Accessories.get(player);
        if (msg.equip) {
            boolean valid = (msg.from >= 0 && msg.from < Inventory.INVENTORY_SIZE) || msg.from == Inventory.SLOT_OFFHAND;
            if (!valid) {
                return;
            }
            ItemStack stack = inv.getItem(msg.from);
            int slot = Accessories.freeSlotFor(player, stack);
            if (slot < 0) {
                return;
            }
            worn.setItem(slot, stack.split(1));
            inv.setChanged();
            worn.setChanged();
        } else {
            if (msg.from < 0 || msg.from >= worn.getContainerSize() || worn.getItem(msg.from).isEmpty()) {
                return;
            }
            ItemStack stack = worn.getItem(msg.from).copy();
            if (inv.add(stack)) {
                worn.setItem(msg.from, ItemStack.EMPTY);
                worn.setChanged();
            }
        }
        player.inventoryMenu.broadcastChanges();
    }
}
