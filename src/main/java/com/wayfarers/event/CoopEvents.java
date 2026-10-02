package com.wayfarers.event;

import com.wayfarers.Wayfarers;
import com.wayfarers.data.WayfarersData;
import com.wayfarers.registry.ModItems;
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
 * Co-op glue: every Wayfarers quest earned by one player is granted to everybody (now and
 * when others log in later), and new players receive the Atlas plus a short welcome.
 */
public final class CoopEvents {
    private static boolean sharing;

    private CoopEvents() {}

    public static void register() {
        AdvancementEvent.AdvancementEarnEvent.BUS.addListener(CoopEvents::onAdvancement);
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(CoopEvents::onLogin);
    }

    private static void onAdvancement(AdvancementEvent.AdvancementEarnEvent event) {
        AdvancementHolder holder = event.getAdvancement();
        if (sharing || !(event.getEntity() instanceof ServerPlayer earner)
                || !holder.id().getNamespace().equals(Wayfarers.MODID) || holder.id().getPath().equals("root")) {
            return;
        }
        MinecraftServer server = earner.level().getServer();
        if (!WayfarersData.get(server).markQuest(holder.id())) {
            return;
        }
        sharing = true;
        try {
            for (ServerPlayer other : server.getPlayerList().getPlayers()) {
                if (other != earner && grant(other, holder)) {
                    other.sendSystemMessage(Component.translatable("message.wayfarers.shared", earner.getDisplayName(),
                            holder.value().display().map(d -> d.getTitle()).orElse(Component.literal(holder.id().toString())))
                            .withStyle(ChatFormatting.DARK_AQUA));
                }
            }
        } finally {
            sharing = false;
        }
    }

    private static boolean grant(ServerPlayer player, AdvancementHolder holder) {
        boolean any = false;
        for (String criterion : holder.value().criteria().keySet()) {
            any |= player.getAdvancements().award(holder, criterion);
        }
        return any;
    }

    private static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        MinecraftServer server = player.level().getServer();
        WayfarersData data = WayfarersData.get(server);
        sharing = true;
        try {
            for (String id : data.quests()) {
                AdvancementHolder holder = server.getAdvancements().get(Identifier.parse(id));
                if (holder != null) {
                    grant(player, holder);
                }
            }
        } finally {
            sharing = false;
        }
        if (data.welcome(player.getUUID())) {
            player.getInventory().add(new ItemStack(ModItems.WAYFARER_ATLAS.get()));
            player.getInventory().add(new ItemStack(ModItems.STRUCTURE_COMPASS.get()));
            player.sendSystemMessage(Component.translatable("message.wayfarers.welcome").withStyle(ChatFormatting.GOLD));
        }
    }
}
