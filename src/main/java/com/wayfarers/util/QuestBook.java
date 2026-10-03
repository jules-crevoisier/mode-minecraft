package com.wayfarers.util;

import com.wayfarers.Wayfarers;
import com.wayfarers.generated.GeneratedContent;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.advancements.AdvancementProgress;
import com.wayfarers.network.QuestSnapshotMsg;
import com.wayfarers.network.WayfarersNet;

import java.util.ArrayList;
import java.util.List;

/** Quest progress (backed by the shared advancements): journal snapshots and the chat summary. */
public final class QuestBook {
    private QuestBook() {}

    /** The player's progress on every quest of every chapter, for the journal and the HUD tracker. */
    public static QuestSnapshotMsg snapshot(ServerPlayer player, boolean open) {
        MinecraftServer server = player.level().getServer();
        List<QuestSnapshotMsg.State> states = new ArrayList<>();
        for (GeneratedContent.Chapter chapter : GeneratedContent.CHAPTERS) {
            for (String quest : chapter.quests()) {
                AdvancementHolder holder = server.getAdvancements().get(Wayfarers.id(quest));
                if (holder == null) {
                    continue;
                }
                AdvancementProgress progress = player.getAdvancements().getOrStartProgress(holder);
                int done = 0;
                int total = 0;
                for (String ignored : progress.getCompletedCriteria()) {
                    done++;
                    total++;
                }
                for (String ignored : progress.getRemainingCriteria()) {
                    total++;
                }
                states.add(new QuestSnapshotMsg.State(quest, progress.isDone(), done, total));
            }
        }
        return new QuestSnapshotMsg(open, states);
    }

    /** Refreshes the journal/tracker of every online player (quest progress is shared by the group). */
    public static void pushToAll(MinecraftServer server) {
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            WayfarersNet.toPlayer(p, snapshot(p, false));
        }
    }

    public static void print(ServerPlayer player) {
        MinecraftServer server = player.level().getServer();
        player.sendSystemMessage(Component.translatable("message.wayfarers.atlas.header").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
        String next = null;
        boolean all = true;
        for (GeneratedContent.Chapter chapter : GeneratedContent.CHAPTERS) {
            int done = 0;
            int total = 0;
            for (String quest : chapter.quests()) {
                AdvancementHolder holder = server.getAdvancements().get(Wayfarers.id(quest));
                if (holder == null) {
                    continue;
                }
                total++;
                if (player.getAdvancements().getOrStartProgress(holder).isDone()) {
                    done++;
                } else if (next == null) {
                    next = "advancements.wayfarers." + quest.replace('/', '.') + ".title";
                }
            }
            if (total == 0) {
                continue;
            }
            all &= done == total;
            ChatFormatting color = done == total ? ChatFormatting.GREEN : done > 0 ? ChatFormatting.YELLOW : ChatFormatting.GRAY;
            player.sendSystemMessage(Component.translatable("message.wayfarers.atlas.chapter",
                    Component.translatable("chapter.wayfarers." + chapter.id()), done, total).withStyle(color));
        }
        if (all) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.atlas.done").withStyle(ChatFormatting.LIGHT_PURPLE));
        } else if (next != null) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.atlas.next", Component.translatable(next))
                    .withStyle(ChatFormatting.AQUA));
        }
    }
}
