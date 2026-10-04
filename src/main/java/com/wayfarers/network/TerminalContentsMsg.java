package com.wayfarers.network;

import com.wayfarers.util.StorageNetwork;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.ArrayList;
import java.util.List;

/**
 * Server to client: what the Guild Terminal's storage network holds (item type + total count), how many containers
 * are linked (a double chest counts once, excluded ones not at all) and how many slots are free.
 */
public record TerminalContentsMsg(int containerId, List<StorageNetwork.Entry> entries, int linked, int freeSlots) {
    private static final int MAX_BYTES = 600_000;

    public static final StreamCodec<RegistryFriendlyByteBuf, TerminalContentsMsg> STREAM_CODEC =
            StreamCodec.ofMember(TerminalContentsMsg::encode, TerminalContentsMsg::decode);

    private static void encode(TerminalContentsMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeVarInt(msg.containerId);
        buf.writeVarInt(msg.linked);
        buf.writeVarInt(msg.freeSlots);
        // a custom payload may not exceed 1 MiB (the player would be disconnected): a base full of unique items with
        // big components (filled shulker boxes, written books) stops at a budget; the rest are the least plentiful
        int start = buf.writerIndex();
        for (StorageNetwork.Entry e : msg.entries) {
            if (buf.writerIndex() - start > MAX_BYTES) {
                break;
            }
            buf.writeBoolean(true);
            ItemStack.STREAM_CODEC.encode(buf, e.type());
            buf.writeVarInt(e.count());
        }
        buf.writeBoolean(false);
    }

    private static TerminalContentsMsg decode(RegistryFriendlyByteBuf buf) {
        int id = buf.readVarInt();
        int linked = buf.readVarInt();
        int free = buf.readVarInt();
        List<StorageNetwork.Entry> list = new ArrayList<>();
        while (buf.readBoolean()) {
            list.add(new StorageNetwork.Entry(ItemStack.STREAM_CODEC.decode(buf), buf.readVarInt()));
        }
        return new TerminalContentsMsg(id, list, linked, free);
    }

    static void handle(TerminalContentsMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.ClientHooks.terminalContents(msg);
        }
    }
}
