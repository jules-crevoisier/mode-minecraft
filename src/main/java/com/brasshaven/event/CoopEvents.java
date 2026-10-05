package com.brasshaven.event;

import com.brasshaven.Brasshaven;
import com.brasshaven.data.BrasshavenData;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.entity.player.AdvancementEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;

/**
 * Co-op glue: every Brasshaven quest step reached by one player is granted to everybody (now
 * and when others log in later), and new players receive the Manual and the Atlas, a short welcome and the way to
 * the first Guild Agent ({@link com.brasshaven.util.Progression}).
 */
public final class CoopEvents {
    private static boolean sharing;
    /** Players whose quest progress changed this tick: their journal and tracker get a fresh snapshot once. */
    private static final java.util.Set<java.util.UUID> DIRTY = new java.util.HashSet<>();

    private CoopEvents() {}

    public static void register() {
        AdvancementEvent.AdvancementProgressEvent.BUS.addListener(CoopEvents::onProgress);
        net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent.BUS.addListener(
                (java.util.function.Consumer<net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent>) CoopEvents::onPlace);
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(CoopEvents::onLogin);
        net.minecraftforge.event.TickEvent.ServerTickEvent.Post.BUS.addListener(e -> flush(e.server()));
    }

    /** One snapshot per changed player at the end of the tick (a catch-up awards dozens of criteria at once). */
    private static void flush(MinecraftServer server) {
        if (DIRTY.isEmpty()) {
            return;
        }
        for (java.util.UUID id : DIRTY) {
            ServerPlayer p = server.getPlayerList().getPlayer(id);
            if (p != null) {
                com.brasshaven.network.BrasshavenNet.toPlayer(p, com.brasshaven.util.QuestBook.snapshot(p, false));
            }
        }
        DIRTY.clear();
    }

    /** Shares every single criterion, so partial progress (e.g. "visit every structure") is pooled. */
    private static void onProgress(AdvancementEvent.AdvancementProgressEvent event) {
        AdvancementHolder holder = event.getAdvancement();
        // the HUD tracker follows the player's own progress too (shared or not, and when someone else already did it)
        if (event.getEntity() instanceof ServerPlayer changed && holder.id().getNamespace().equals(Brasshaven.MODID)) {
            DIRTY.add(changed.getUUID());
        }
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
            // the Manual and the Atlas only, and the way to the first Guild Agent: the rest is earned (Progression)
            com.brasshaven.util.Progression.welcome(player);
        }
        com.brasshaven.network.BrasshavenNet.toPlayer(player, com.brasshaven.util.QuestBook.snapshot(player, false));
    }
}
