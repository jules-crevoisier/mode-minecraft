package com.brasshaven.recipe;

import com.brasshaven.Brasshaven;
import com.brasshaven.network.BrasshavenNet;
import com.brasshaven.network.RecipeSyncMsg;
import io.netty.buffer.Unpooled;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.display.RecipeDisplay;
import net.minecraft.world.item.crafting.display.RecipeDisplayId;
import net.minecraftforge.event.OnDatapackSyncEvent;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Recipes for the built-in recipe viewer (client/recipes). Since 1.21.2 the server keeps the recipes to itself: a
 * client only gets the recipe book entries of the recipes its player has unlocked. The viewer shows them all, so the
 * server sends every recipe's <em>display</em> (the vanilla {@link RecipeDisplay}: slots, result, station; encoded with
 * the vanilla codecs, tags stay tags) with its id and recipe type: vanilla, the mod's and every data pack's.
 *
 * <p>Built once per recipe reload (the {@link RecipeManager} is a new object after {@code /reload}), already encoded and
 * cut into parts of {@link #PART_BYTES} at most, then sent to each player on login and to everyone after a reload
 * ({@link OnDatapackSyncEvent}, after the tags). About 2000 recipes make some 120 KiB (63 bytes a recipe: registry ids
 * are varints, a tag is its name), so one message; a dedicated server's connection compresses it to about 40 KiB. The
 * size is logged at each build.
 */
public final class RecipeSync {
    /** Most bytes in one message: far under the 1 MiB a custom payload may carry. */
    public static final int PART_BYTES = 192 * 1024;

    private static RecipeManager builtFor;
    private static List<RecipeSyncMsg> messages = List.of();
    private static int generation;

    private RecipeSync() {}

    public static void register() {
        OnDatapackSyncEvent.BUS.addListener(event -> {
            List<RecipeSyncMsg> msgs = messages(event.getPlayerList().getServer());
            for (ServerPlayer player : event.getPlayers()) {
                for (RecipeSyncMsg msg : msgs) {
                    BrasshavenNet.toPlayer(player, msg);
                }
            }
        });
    }

    private static synchronized List<RecipeSyncMsg> messages(MinecraftServer server) {
        RecipeManager recipes = server.getRecipeManager();
        if (recipes != builtFor) {
            builtFor = recipes;
            messages = build(server.registryAccess(), recipes, ++generation);
        }
        return messages;
    }

    /**
     * Every display of every recipe, in the recipe manager's order (sorted by id: the mod's before minecraft's).
     * Part layout: varint type count, the recipe type ids, varint entry count, then per entry the recipe id, the index
     * of its type and the {@link RecipeDisplay}.
     */
    static List<RecipeSyncMsg> build(RegistryAccess access, RecipeManager recipes, int gen) {
        long start = System.nanoTime();
        List<byte[]> parts = new ArrayList<>();
        Map<Identifier, Integer> types = new LinkedHashMap<>();
        RegistryFriendlyByteBuf body = new RegistryFriendlyByteBuf(Unpooled.buffer(), access);
        RegistryFriendlyByteBuf one = new RegistryFriendlyByteBuf(Unpooled.buffer(), access);
        int entries = 0;
        int total = 0;
        int skipped = 0;
        int displays = 0;
        Set<Identifier> ids = new HashSet<>();
        for (int i = 0; ; i++) {
            RecipeManager.ServerDisplayInfo info = recipes.getRecipeFromDisplay(new RecipeDisplayId(i));
            if (info == null) {
                break;
            }
            RecipeHolder<?> holder = info.parent();
            Identifier type = BuiltInRegistries.RECIPE_TYPE.getKey(holder.value().getType());
            if (type == null) {
                continue;
            }
            one.clear();
            try {
                one.writeIdentifier(holder.id().identifier());
                one.writeVarInt(types.computeIfAbsent(type, k -> types.size()));
                RecipeDisplay.STREAM_CODEC.encode(one, info.display().display());
            } catch (RuntimeException e) {
                // a mod's display that does not encode: leave it out of the viewer rather than the whole list
                if (skipped++ == 0) {
                    Brasshaven.LOGGER.warn("Recipe viewer: recipe {} could not be encoded, skipped: {}", holder.id().identifier(), e.toString());
                }
                continue;
            }
            if (body.readableBytes() + one.readableBytes() > PART_BYTES && entries > 0) {
                parts.add(part(access, types, entries, body));
                total += parts.get(parts.size() - 1).length;
                types.clear();
                body.clear();
                entries = 0;
                // the type index was taken from the old part's table: write the entry again for the new one
                one.clear();
                one.writeIdentifier(holder.id().identifier());
                one.writeVarInt(types.computeIfAbsent(type, k -> types.size()));
                RecipeDisplay.STREAM_CODEC.encode(one, info.display().display());
            }
            body.writeBytes(one, one.readerIndex(), one.readableBytes());
            entries++;
            displays++;
            ids.add(holder.id().identifier());
        }
        if (entries > 0 || parts.isEmpty()) {
            parts.add(part(access, types, entries, body));
            total += parts.get(parts.size() - 1).length;
        }
        body.release();
        one.release();
        List<RecipeSyncMsg> out = new ArrayList<>();
        for (int p = 0; p < parts.size(); p++) {
            out.add(new RecipeSyncMsg(gen, p, parts.size(), parts.get(p)));
        }
        Brasshaven.LOGGER.info("Recipe viewer: {} recipes ({} displays{}), {} KiB in {} message(s), built in {} ms", ids.size(),
                displays, skipped > 0 ? ", " + skipped + " skipped" : "",
                (total + 1023) / 1024, out.size(), (System.nanoTime() - start) / 1_000_000);
        return List.copyOf(out);
    }

    private static byte[] part(RegistryAccess access, Map<Identifier, Integer> types, int entries, RegistryFriendlyByteBuf body) {
        RegistryFriendlyByteBuf buf = new RegistryFriendlyByteBuf(Unpooled.buffer(body.readableBytes() + 256), access);
        buf.writeVarInt(types.size());
        types.keySet().forEach(buf::writeIdentifier);
        buf.writeVarInt(entries);
        buf.writeBytes(body, body.readerIndex(), body.readableBytes());
        byte[] bytes = new byte[buf.readableBytes()];
        buf.readBytes(bytes);
        buf.release();
        return bytes;
    }
}
