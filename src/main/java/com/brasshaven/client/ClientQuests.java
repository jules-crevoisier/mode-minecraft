package com.brasshaven.client;

import com.brasshaven.Brasshaven;
import com.brasshaven.generated.GeneratedContent;
import com.brasshaven.network.QuestSnapshotMsg;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.DisplayInfo;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientAdvancements;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/** Client copy of the player's quest progress (pushed by the server) plus display helpers. */
public final class ClientQuests {
    private static final Map<String, QuestSnapshotMsg.State> STATES = new HashMap<>();

    private ClientQuests() {}

    public static void update(QuestSnapshotMsg msg) {
        STATES.clear();
        for (QuestSnapshotMsg.State s : msg.quests()) {
            STATES.put(s.id(), s);
        }
    }

    public static QuestSnapshotMsg.State state(String quest) {
        if (ClientContracts.isContract(quest)) {
            return ClientContracts.state(quest);
        }
        return STATES.getOrDefault(quest, new QuestSnapshotMsg.State(quest, false, 0, 1));
    }

    public static boolean done(String quest) {
        return state(quest).done();
    }

    public static Optional<AdvancementHolder> holder(String quest) {
        if (ClientContracts.isContract(quest)) {
            return Optional.empty(); // a quest giver's contract, not an advancement
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.getConnection() == null) {
            return Optional.empty();
        }
        ClientAdvancements adv = mc.getConnection().getAdvancements();
        return Optional.ofNullable(adv.get(Brasshaven.id(quest)));
    }

    public static Optional<DisplayInfo> display(String quest) {
        return holder(quest).flatMap(h -> h.value().display());
    }

    public static Component title(String quest) {
        if (ClientContracts.isContract(quest)) {
            return ClientContracts.title(quest);
        }
        return Component.translatable("advancements.brasshaven." + quest.replace('/', '.') + ".title");
    }

    public static Component description(String quest) {
        if (ClientContracts.isContract(quest)) {
            return ClientContracts.description(quest);
        }
        return Component.translatable("advancements.brasshaven." + quest.replace('/', '.') + ".description");
    }

    public static ItemStack icon(String quest) {
        if (ClientContracts.isContract(quest)) {
            return ClientContracts.icon(quest);
        }
        return display(quest).map(d -> d.getIcon().create()).orElse(new ItemStack(Items.BOOK));
    }

    /** The quest whose completion unlocks this one (null for the first quest of a chapter). */
    public static String parent(String quest) {
        return holder(quest).flatMap(h -> h.value().parent())
                .filter(id -> id.getNamespace().equals(Brasshaven.MODID) && !id.getPath().equals("root"))
                .map(id -> id.getPath()).orElse(null);
    }

    /** A quest is available once its parent is done (or it has none). */
    public static boolean unlocked(String quest) {
        String p = parent(quest);
        return p == null || done(p);
    }

    public static boolean hidden(String quest) {
        return display(quest).map(DisplayInfo::isHidden).orElse(false) && !done(quest);
    }

    public static int[] chapterProgress(GeneratedContent.Chapter chapter) {
        int done = 0;
        for (String q : chapter.quests()) {
            if (done(q)) {
                done++;
            }
        }
        return new int[] {done, chapter.quests().size()};
    }
}
