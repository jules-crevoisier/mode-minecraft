package com.brasshaven.util;

import com.brasshaven.Brasshaven;
import com.brasshaven.generated.GeneratedContent;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.advancements.AdvancementProgress;
import com.brasshaven.network.QuestSnapshotMsg;
import com.brasshaven.network.BrasshavenNet;

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
                AdvancementHolder holder = server.getAdvancements().get(Brasshaven.id(quest));
                if (holder == null) {
                    continue;
                }
                AdvancementProgress progress = player.getAdvancements().getOrStartProgress(holder);
                // objectives are the requirement groups: "find an outpost OR meet a Guild Agent" is one objective
                var requirements = holder.value().requirements();
                int total = Math.max(1, requirements.size());
                int done = progress.isDone() ? total : requirements.count(c -> {
                    var criterion = progress.getCriterion(c);
                    return criterion != null && criterion.isDone();
                });
                states.add(new QuestSnapshotMsg.State(quest, progress.isDone(), done, total));
            }
        }
        return new QuestSnapshotMsg(open, states);
    }

    /** Refreshes the journal/tracker of every online player (quest progress is shared by the group). */
    public static void pushToAll(MinecraftServer server) {
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            BrasshavenNet.toPlayer(p, snapshot(p, false));
        }
    }

    public static void print(ServerPlayer player) {
        MinecraftServer server = player.level().getServer();
        player.sendSystemMessage(Component.translatable("message.brasshaven.atlas.header").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
        String next = null;
        boolean all = true;
        for (GeneratedContent.Chapter chapter : GeneratedContent.CHAPTERS) {
            int done = 0;
            int total = 0;
            for (String quest : chapter.quests()) {
                AdvancementHolder holder = server.getAdvancements().get(Brasshaven.id(quest));
                if (holder == null) {
                    continue;
                }
                total++;
                if (player.getAdvancements().getOrStartProgress(holder).isDone()) {
                    done++;
                } else if (next == null) {
                    next = "advancements.brasshaven." + quest.replace('/', '.') + ".title";
                }
            }
            if (total == 0) {
                continue;
            }
            all &= done == total;
            ChatFormatting color = done == total ? ChatFormatting.GREEN : done > 0 ? ChatFormatting.YELLOW : ChatFormatting.GRAY;
            player.sendSystemMessage(Component.translatable("message.brasshaven.atlas.chapter",
                    Component.translatable("chapter.brasshaven." + chapter.id()), done, total).withStyle(color));
        }
        // the next goal is the progression ladder's next step while there is one, then the first unfinished quest
        String step = Progression.next(player);
        if (!step.isEmpty()) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.atlas.next", Progression.title(step))
                    .withStyle(ChatFormatting.AQUA));
        } else if (all) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.atlas.done").withStyle(ChatFormatting.LIGHT_PURPLE));
        } else if (next != null) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.atlas.next", Component.translatable(next))
                    .withStyle(ChatFormatting.AQUA));
        }
    }
}
