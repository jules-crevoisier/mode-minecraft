package com.wayfarers.network;

import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.util.ArrayList;
import java.util.List;

/**
 * Server → client: the containers linked to the open Guild Terminal (for its Network page and the "Show" outline),
 * sent when the screen opens and whenever the list changes.
 */
public record TerminalLinksMsg(int containerId, int range, int relays, boolean capped, List<Info> links) {
    /** One linked container: its position (a double chest's lower half), its block as an icon, its slots. */
    public record Info(BlockPos pos, ItemStack icon, int slots, boolean doubled, boolean excluded) {}

    public static final StreamCodec<RegistryFriendlyByteBuf, TerminalLinksMsg> STREAM_CODEC =
            StreamCodec.ofMember(TerminalLinksMsg::encode, TerminalLinksMsg::decode);

    private static void encode(TerminalLinksMsg msg, RegistryFriendlyByteBuf buf) {
        buf.writeVarInt(msg.containerId);
        buf.writeVarInt(msg.range);
        buf.writeVarInt(msg.relays);
        buf.writeBoolean(msg.capped);
        buf.writeVarInt(msg.links.size());
        for (Info i : msg.links) {
            buf.writeBlockPos(i.pos);
            ItemStack.OPTIONAL_STREAM_CODEC.encode(buf, i.icon);
            buf.writeVarInt(i.slots);
            buf.writeBoolean(i.doubled);
            buf.writeBoolean(i.excluded);
        }
    }

    private static TerminalLinksMsg decode(RegistryFriendlyByteBuf buf) {
        int id = buf.readVarInt();
        int range = buf.readVarInt();
        int relays = buf.readVarInt();
        boolean capped = buf.readBoolean();
        int n = buf.readVarInt();
        List<Info> list = new ArrayList<>(Math.min(n, 4096));
        for (int k = 0; k < n; k++) {
            list.add(new Info(buf.readBlockPos(), ItemStack.OPTIONAL_STREAM_CODEC.decode(buf), buf.readVarInt(),
                    buf.readBoolean(), buf.readBoolean()));
        }
        return new TerminalLinksMsg(id, range, relays, capped, list);
    }

    static void handle(TerminalLinksMsg msg, CustomPayloadEvent.Context ctx) {
        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.ClientHooks.terminalLinks(msg);
        }
    }
}
