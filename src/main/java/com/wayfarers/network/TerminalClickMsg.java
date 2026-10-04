package com.wayfarers.network;

import com.wayfarers.menu.TerminalMenu;
import com.wayfarers.util.StorageNetwork;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.network.CustomPayloadEvent;

import java.util.List;

/**
 * Client → server: a click on the Guild Terminal's grid.
 * TAKE_STACK / TAKE_HALF / TAKE_ONE put items on the cursor, TAKE_TO_INVENTORY moves a stack into the
 * inventory (shift-click), STORE_CARRIED stores the cursor stack, STORE_ALL / STORE_MATCHING store the
 * main inventory (all of it, or only what the network already holds).
 */
public record TerminalClickMsg(Action action, ItemStack type) {
    public enum Action { TAKE_STACK, TAKE_HALF, TAKE_ONE, TAKE_TO_INVENTORY, STORE_CARRIED, STORE_ALL, STORE_MATCHING }

    public static final StreamCodec<RegistryFriendlyByteBuf, TerminalClickMsg> STREAM_CODEC =
            StreamCodec.ofMember(TerminalClickMsg::encode, TerminalClickMsg::decode);

    private static void encode(TerminalClickMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeEnum(msg.action);
        ItemStack.OPTIONAL_STREAM_CODEC.encode(buf, msg.type);
    }

    private static TerminalClickMsg decode(RegistryFriendlyByteBuf buf) {
        return new TerminalClickMsg(buf.readEnum(Action.class), ItemStack.OPTIONAL_STREAM_CODEC.decode(buf));
    }

    static void handle(TerminalClickMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer player = ctx.getSender();
        if (player == null || !(player.containerMenu instanceof TerminalMenu menu) || !menu.stillValid(player)) {
            return;
        }
        List<Container> net = menu.network();
        ItemStack carried = menu.getCarried();
        switch (msg.action) {
            case TAKE_STACK, TAKE_HALF, TAKE_ONE -> {
                if (!carried.isEmpty() || msg.type.isEmpty()) {
                    break;
                }
                int amount = switch (msg.action) {
                    case TAKE_ONE -> 1;
                    case TAKE_HALF -> Math.max(1, Math.min(msg.type.getMaxStackSize(), StorageNetwork.count(net, msg.type)) / 2);
                    default -> msg.type.getMaxStackSize();
                };
                menu.setCarried(StorageNetwork.extract(net, msg.type, amount));
            }
            case TAKE_TO_INVENTORY -> {
                if (msg.type.isEmpty()) {
                    break;
                }
                ItemStack taken = StorageNetwork.extract(net, msg.type, msg.type.getMaxStackSize());
                if (!player.getInventory().add(taken) && !taken.isEmpty()) {
                    ItemStack back = StorageNetwork.insert(net, taken);
                    if (!back.isEmpty()) {
                        player.drop(back, false);
                    }
                }
            }
            case STORE_CARRIED -> {
                if (!carried.isEmpty()) {
                    menu.setCarried(StorageNetwork.insert(net, carried));
                }
            }
            case STORE_ALL, STORE_MATCHING -> {
                // one index of the network for the whole inventory (huge bases: no pass per stack)
                StorageNetwork.Inserter inserter = new StorageNetwork.Inserter(net);
                var inv = player.getInventory();
                for (int i = 9; i < 36; i++) {
                    ItemStack s = inv.getItem(i);
                    if (s.isEmpty() || (msg.action == Action.STORE_MATCHING && !inserter.holds(s))) {
                        continue;
                    }
                    inv.setItem(i, inserter.insert(s));
                }
            }
        }
        menu.dirty();
        menu.broadcastChanges();
    }
}
