package com.brasshaven.event;

import com.brasshaven.Brasshaven;
import com.brasshaven.data.BrasshavenData;
import com.brasshaven.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.entity.player.AdvancementEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;

/**
 * Co-op glue: every Brasshaven quest step reached by one player is granted to everybody (now
 * and when others log in later), and new players receive the Atlas plus a short welcome.
 */
public final class CoopEvents {
    private static boolean sharing;

    private CoopEvents() {}

    public static void register() {
        AdvancementEvent.AdvancementProgressEvent.BUS.addListener(CoopEvents::onProgress);
        net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent.BUS.addListener(
                (java.util.function.Consumer<net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent>) CoopEvents::onPlace);
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(CoopEvents::onLogin);
    }

    /** Shares every single criterion, so partial progress (e.g. "visit every structure") is pooled. */
    private static void onProgress(AdvancementEvent.AdvancementProgressEvent event) {
        AdvancementHolder holder = event.getAdvancement();
        if (sharing || !com.brasshaven.config.BrasshavenConfig.QUESTS_SHARED.get()
                || event.getProgressType() != AdvancementEvent.AdvancementProgressEvent.ProgressType.GRANT
                || !(event.getEntity() instanceof ServerPlayer earner)
                || !holder.id().getNamespace().equals(Brasshaven.MODID) || holder.id().getPath().equals("root")) {
            return;
        }
        MinecraftServer server = earner.level().getServer();
        if (!BrasshavenData.get(server).markCriterion(holder.id(), event.getCriterionName())) {
            return;
        }
        boolean completed = event.getAdvancementProgress().isDone();
        sharing = true;
        try {
            for (ServerPlayer other : server.getPlayerList().getPlayers()) {
                if (other == earner) {
                    continue;
                }
                boolean wasDone = other.getAdvancements().getOrStartProgress(holder).isDone();
                other.getAdvancements().award(holder, event.getCriterionName());
                if (completed && !wasDone && other.getAdvancements().getOrStartProgress(holder).isDone()) {
                    other.sendSystemMessage(Component.translatable("message.brasshaven.shared", earner.getDisplayName(),
                            holder.value().display().map(d -> d.getTitle()).orElse(Component.literal(holder.id().toString())))
                            .withStyle(ChatFormatting.DARK_AQUA));
                }
            }
        } finally {
            sharing = false;
        }
        com.brasshaven.util.QuestBook.pushToAll(server);
    }

    /** Placing a storage block for the first time explains it. */
    private static void onPlace(net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent event) {
        if (event.getEntity() instanceof ServerPlayer player && !com.brasshaven.util.ServerGuard.probing()) {
            var block = event.getPlacedBlock().getBlock();
            if (block == com.brasshaven.registry.ModBlocks.SORTING_CHEST.get()) {
                com.brasshaven.util.Tips.show(player, "sorting_chest");
            } else if (block == com.brasshaven.registry.ModBlocks.GUILD_TERMINAL.get()) {
                com.brasshaven.util.Tips.show(player, "guild_terminal");
            }
        }
    }

    private static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        MinecraftServer server = player.level().getServer();
        BrasshavenData data = BrasshavenData.get(server);
        // quests.catchUpOnJoin: off on a public server, so a new (or alt) account doesn't collect every reward at once
        boolean catchUp = com.brasshaven.config.BrasshavenConfig.QUESTS_SHARED.get()
                && com.brasshaven.config.BrasshavenConfig.QUESTS_CATCH_UP.get();
        sharing = true;
        try {
            for (String entry : catchUp ? data.quests() : java.util.Set.<String>of()) {
                int hash = entry.indexOf('#');
                if (hash < 0) {
                    continue;
                }
                AdvancementHolder holder = server.getAdvancements().get(Identifier.parse(entry.substring(0, hash)));
                if (holder != null) {
                    player.getAdvancements().award(holder, entry.substring(hash + 1));
                }
            }
        } finally {
            sharing = false;
        }
        if (data.welcome(player.getUUID())) {
            player.getInventory().add(new ItemStack(ModItems.WAYFARER_ATLAS.get()));
            player.getInventory().add(new ItemStack(ModItems.WAYFARER_MANUAL.get()));
            player.getInventory().add(new ItemStack(ModItems.STRUCTURE_COMPASS.get()));
            player.sendSystemMessage(Component.translatable("message.brasshaven.welcome", Component.keybind("key.brasshaven.quests"))
                    .withStyle(ChatFormatting.GOLD));
        }
        com.brasshaven.network.BrasshavenNet.toPlayer(player, com.brasshaven.util.QuestBook.snapshot(player, false));
    }
}
