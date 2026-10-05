package com.brasshaven.client;

import com.brasshaven.generated.GeneratedNpcs;
import com.brasshaven.network.ContractSyncMsg;
import com.brasshaven.network.QuestSnapshotMsg;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Client copy of the player's contracts (pushed by the server, {@link com.brasshaven.util.NpcQuests#sync}). In the
 * quest journal and the HUD tracker a contract is the quest id {@code "npc/<contract id>"}; a fetch contract counts
 * the items in the local inventory so the tracker follows what the player picks up.
 */
public final class ClientContracts {
    public static final String PREFIX = "npc/";
    private static final Map<String, ContractSyncMsg.Entry> STATES = new HashMap<>();

    private ClientContracts() {}

    public static void update(ContractSyncMsg msg) {
        STATES.clear();
        for (ContractSyncMsg.Entry e : msg.contracts()) {
            STATES.put(e.id(), e);
        }
    }

    public static boolean isContract(String quest) {
        return quest != null && quest.startsWith(PREFIX);
    }

    public static String id(String quest) {
        return isContract(quest) ? quest.substring(PREFIX.length()) : quest;
    }

    public static Optional<GeneratedNpcs.Quest> quest(String quest) {
        String id = id(quest);
        return GeneratedNpcs.QUESTS.stream().filter(q -> q.id().equals(id)).findFirst();
    }

    /** Journal ids ("npc/...") of the accepted and finished contracts, in the table's order. */
    public static List<String> journal() {
        List<String> out = new ArrayList<>();
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            if (STATES.containsKey(q.id())) {
                out.add(PREFIX + q.id());
            }
        }
        return out;
    }

    public static boolean accepted(String quest) {
        ContractSyncMsg.Entry e = STATES.get(id(quest));
        return e != null && !e.done();
    }

    public static QuestSnapshotMsg.State state(String quest) {
        ContractSyncMsg.Entry e = STATES.get(id(quest));
        if (e == null) {
            return new QuestSnapshotMsg.State(quest, false, 0, quest(quest).map(q -> needed(q)).orElse(1));
        }
        int progress = e.progress();
        Optional<GeneratedNpcs.Quest> q = quest(quest);
        if (!e.done() && q.isPresent() && q.get().kind() == GeneratedNpcs.Kind.FETCH) {
            progress = Math.min(q.get().count(), carried(q.get().target()));
        }
        return new QuestSnapshotMsg.State(quest, e.done(), e.done() ? e.needed() : progress, e.needed());
    }

    private static int needed(GeneratedNpcs.Quest q) {
        return q.kind() == GeneratedNpcs.Kind.FETCH || q.kind() == GeneratedNpcs.Kind.HUNT ? q.count() : 1;
    }

    private static int carried(String itemId) {
        Minecraft mc = Minecraft.getInstance();
        Item item = BuiltInRegistries.ITEM.getOptional(Identifier.parse(itemId)).orElse(null);
        if (mc.player == null || item == null) {
            return 0;
        }
        int n = 0;
        for (ItemStack stack : mc.player.getInventory().getNonEquipmentItems()) {
            if (stack.is(item)) {
                n += stack.getCount();
            }
        }
        return n;
    }

    public static Component title(String quest) {
        return Component.translatable("npcquest.brasshaven." + id(quest) + ".title");
    }

    public static Component description(String quest) {
        return Component.translatable("npcquest.brasshaven." + id(quest) + ".description");
    }

    public static Component story(String quest) {
        return Component.translatable("npcquest.brasshaven." + id(quest) + ".story");
    }

    public static ItemStack icon(String quest) {
        return quest(quest).flatMap(q -> BuiltInRegistries.ITEM.getOptional(Identifier.parse(q.icon())))
                .map(ItemStack::new).orElse(new ItemStack(Items.PAPER));
    }
}
