package com.brasshaven.util;

import com.brasshaven.entity.WayfarerNpc;
import com.brasshaven.generated.GeneratedNpcs;
import com.brasshaven.network.ContractSyncMsg;
import com.brasshaven.network.NpcDialogMsg;
import com.brasshaven.network.BrasshavenNet;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;

/**
 * Contracts of the quest givers ({@link WayfarerNpc}, table in {@link GeneratedNpcs}, written in tools/wf/npcs.py).
 *
 * <p>Each player has their own contracts, kept in the player's persistent data (they survive death): the accepted
 * ones with their progress, and the finished ones. A contract is accepted from its giver, then:
 * <ul>
 *     <li><b>fetch</b>: the items are counted in the inventory and taken when it is turned in;</li>
 *     <li><b>hunt</b>: kills of the target made after accepting count;</li>
 *     <li><b>explore</b>: entering the target structure (checked every two seconds) completes it;</li>
 *     <li><b>deliver</b>: the giver hands over a sealed parcel, which goes to any NPC of the {@code to} role.</li>
 * </ul>
 * Turning in gives the rewards (items, experience). The server checks everything: the client only asks.
 */
public final class NpcQuests {
    private static final String KEY = "brasshaven_contracts";
    private static final String PARCEL = "brasshaven_parcel";
    /** Talking reach (blocks, squared). */
    private static final double REACH_SQR = 8.0 * 8.0;

    /** What a contract is to a player, seen from one NPC (ordinals are sent to the client). */
    public enum State { AVAILABLE, ACTIVE, READY, DONE, LOCKED, DELIVERY }

    public static final int ACCEPT = 0;
    public static final int TURN_IN = 1;
    public static final int PARCEL_AGAIN = 2;

    private NpcQuests() {}

    public static void register() {
        LivingDeathEvent.BUS.addListener((Consumer<LivingDeathEvent>) NpcQuests::onDeath);
        TickEvent.PlayerTickEvent.Post.BUS.addListener(NpcQuests::onPlayerTick);
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(NpcQuests::onLogin);
    }

    // ------------------------------------------------------------------ table

    public static Optional<GeneratedNpcs.Quest> quest(String id) {
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            if (q.id().equals(id)) {
                return Optional.of(q);
            }
        }
        return Optional.empty();
    }

    public static int needed(GeneratedNpcs.Quest q) {
        return switch (q.kind()) {
            case FETCH, HUNT -> q.count();
            case EXPLORE, DELIVER -> 1;
        };
    }

    // ------------------------------------------------------------------ storage

    private static CompoundTag data(ServerPlayer player) {
        CompoundTag root = player.getPersistentData();
        CompoundTag persisted = root.getCompoundOrEmpty("PlayerPersisted");
        CompoundTag tag = persisted.getCompoundOrEmpty(KEY);
        persisted.put(KEY, tag);
        root.put("PlayerPersisted", persisted);
        return tag;
    }

    /** Accepted contracts and their stored progress (kills, structure found), in acceptance order. */
    public static Map<String, Integer> active(ServerPlayer player) {
        CompoundTag act = data(player).getCompoundOrEmpty("active");
        Map<String, Integer> out = new LinkedHashMap<>();
        for (String k : act.keySet()) {
            out.put(k, act.getIntOr(k, 0));
        }
        return out;
    }

    private static void setProgress(ServerPlayer player, String id, int progress) {
        CompoundTag d = data(player);
        CompoundTag act = d.getCompoundOrEmpty("active");
        act.putInt(id, progress);
        d.put("active", act);
    }

    public static Set<String> done(ServerPlayer player) {
        Set<String> out = new LinkedHashSet<>();
        for (Tag t : data(player).getListOrEmpty("done")) {
            t.asString().ifPresent(out::add);
        }
        return out;
    }

    private static void finish(ServerPlayer player, String id) {
        CompoundTag d = data(player);
        CompoundTag act = d.getCompoundOrEmpty("active");
        act.remove(id);
        d.put("active", act);
        ListTag list = d.getListOrEmpty("done");
        list.add(StringTag.valueOf(id));
        d.put("done", list);
    }

    /** Operators: forget every contract of a player. */
    public static void reset(ServerPlayer player) {
        CompoundTag d = data(player);
        d.put("active", new CompoundTag());
        d.put("done", new ListTag());
        sync(player);
    }

    // ------------------------------------------------------------------ progress

    /** Current progress: items carried (fetch), kills (hunt), structure found (explore), parcel carried (deliver). */
    public static int progress(ServerPlayer player, GeneratedNpcs.Quest q) {
        return switch (q.kind()) {
            case FETCH -> Math.min(q.count(), countItem(player, q.target()));
            case HUNT, EXPLORE -> Math.min(needed(q), active(player).getOrDefault(q.id(), 0));
            case DELIVER -> parcelSlot(player, q.id()) >= 0 ? 1 : 0;
        };
    }

    public static State state(ServerPlayer player, GeneratedNpcs.Quest q, String role) {
        if (done(player).contains(q.id())) {
            return State.DONE;
        }
        boolean receiver = q.kind() == GeneratedNpcs.Kind.DELIVER && q.to().equals(role);
        if (active(player).containsKey(q.id())) {
            if (q.kind() == GeneratedNpcs.Kind.DELIVER) {
                return receiver ? (progress(player, q) > 0 ? State.DELIVERY : State.ACTIVE) : State.ACTIVE;
            }
            return progress(player, q) >= needed(q) ? State.READY : State.ACTIVE;
        }
        if (!q.after().isEmpty() && !done(player).contains(q.after())) {
            return State.LOCKED;
        }
        return State.AVAILABLE;
    }

    private static int countItem(ServerPlayer player, String id) {
        Item item = item(id);
        if (item == null) {
            return 0;
        }
        int n = 0;
        for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
            if (stack.is(item) && !isParcel(stack)) {
                n += stack.getCount();
            }
        }
        return n;
    }

    private static void takeItem(ServerPlayer player, String id, int count) {
        Item item = item(id);
        for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
            if (count <= 0) {
                break;
            }
            if (item != null && stack.is(item) && !isParcel(stack)) {
                int n = Math.min(count, stack.getCount());
                stack.shrink(n);
                count -= n;
            }
        }
        player.getInventory().setChanged();
    }

    private static Item item(String id) {
        return BuiltInRegistries.ITEM.getOptional(Identifier.parse(id)).orElse(null);
    }

    // ------------------------------------------------------------------ parcels

    public static ItemStack parcel(GeneratedNpcs.Quest q) {
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_NAME, Component.translatable("npcquest.brasshaven." + q.id() + ".parcel")
                .withStyle(ChatFormatting.GOLD));
        stack.set(DataComponents.LORE, new ItemLore(List.of(Component.translatable("message.brasshaven.npc.parcel.lore",
                Component.translatable("npc.brasshaven.role." + q.to())))));
        CompoundTag tag = new CompoundTag();
        tag.putString(PARCEL, q.id());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        stack.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        return stack;
    }

    private static boolean isParcel(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data != null && !data.copyTag().getStringOr(PARCEL, "").isEmpty();
    }

    /** Inventory slot holding the parcel of contract {@code id}, or -1. */
    private static int parcelSlot(ServerPlayer player, String id) {
        var items = player.getInventory().getNonEquipmentItems();
        for (int i = 0; i < items.size(); i++) {
            CustomData data = items.get(i).get(DataComponents.CUSTOM_DATA);
            if (data != null && id.equals(data.copyTag().getStringOr(PARCEL, ""))) {
                return i;
            }
        }
        return -1;
    }

    private static void give(ServerPlayer player, ItemStack stack) {
        if (!player.getInventory().add(stack)) {
            player.drop(stack, false);
        }
    }

    // ------------------------------------------------------------------ talking to an NPC

    /** Opens (or refreshes) the contracts screen of {@code npc} for {@code player}. */
    public static void open(ServerPlayer player, WayfarerNpc npc) {
        String role = npc.role();
        List<NpcDialogMsg.Entry> entries = new ArrayList<>();
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            boolean giver = q.giver().equals(role);
            boolean receiver = q.kind() == GeneratedNpcs.Kind.DELIVER && q.to().equals(role)
                    && active(player).containsKey(q.id());
            if (giver || receiver) {
                State s = state(player, q, role);
                entries.add(new NpcDialogMsg.Entry(q.id(), s.ordinal(), progress(player, q), needed(q), receiver));
            }
        }
        BrasshavenNet.toPlayer(player, new NpcDialogMsg(npc.getId(), role, entries));
        Tips.show(player, "npc");
        if (role.equals("guild_agent")) {
            Progression.metAgent(player); // the progression ladder's first step, wherever the agent stands
        }
    }

    /** The items a contract gives when it is handed in. */
    public static List<ItemStack> rewardStacks(GeneratedNpcs.Quest q) {
        List<ItemStack> out = new ArrayList<>();
        for (GeneratedNpcs.Reward r : q.rewards()) {
            Item item = item(r.item());
            if (item != null) {
                out.add(new ItemStack(item, r.count()));
            }
        }
        return out;
    }

    /** Marks the contract finished and gives its rewards (items, experience). */
    private static void reward(ServerPlayer player, GeneratedNpcs.Quest q) {
        finish(player, q.id());
        for (ItemStack stack : rewardStacks(q)) {
            give(player, stack);
        }
        if (q.xp() > 0) {
            player.giveExperiencePoints(q.xp());
        }
        Progression.contractFinished(player, q);
    }

    /**
     * Operators ({@code /brasshaven contracts complete}): finishes a contract for a player as if it had been handed
     * in (rewards included), whatever its state; its parcel, if any, is left alone. False when it was already done.
     */
    public static boolean complete(ServerPlayer player, GeneratedNpcs.Quest q) {
        if (done(player).contains(q.id())) {
            return false;
        }
        reward(player, q);
        sync(player);
        return true;
    }

    /** A button of the contracts screen: validated here (reach, role, state, items). */
    public static void handle(ServerPlayer player, int entityId, String id, int action) {
        Entity e = player.level().getEntity(entityId);
        if (!(e instanceof WayfarerNpc npc) || !npc.isAlive() || player.distanceToSqr(npc) > REACH_SQR) {
            player.sendOverlayMessage(Component.translatable("message.brasshaven.npc.too_far").withStyle(ChatFormatting.RED));
            return;
        }
        Optional<GeneratedNpcs.Quest> found = quest(id);
        if (found.isEmpty()) {
            return;
        }
        GeneratedNpcs.Quest q = found.get();
        String role = npc.role();
        State s = state(player, q, role);
        Component title = Component.translatable("npcquest.brasshaven." + q.id() + ".title");
        switch (action) {
            case ACCEPT -> {
                if (!q.giver().equals(role) || s != State.AVAILABLE) {
                    break;
                }
                setProgress(player, q.id(), 0);
                if (q.kind() == GeneratedNpcs.Kind.DELIVER) {
                    giveParcel(player, q);
                }
                npc.nod();
                player.sendSystemMessage(Component.translatable("message.brasshaven.npc.accepted", title)
                        .withStyle(ChatFormatting.GOLD));
                Progression.contractAccepted(player, q); // an "explore" contract marks its target on the map
            }
            case TURN_IN -> {
                boolean mine = q.kind() == GeneratedNpcs.Kind.DELIVER ? q.to().equals(role) : q.giver().equals(role);
                if (!mine || !(s == State.READY || s == State.DELIVERY)) {
                    player.sendOverlayMessage(Component.translatable("message.brasshaven.npc.missing").withStyle(ChatFormatting.RED));
                    break;
                }
                if (q.kind() == GeneratedNpcs.Kind.FETCH) {
                    takeItem(player, q.target(), q.count());
                } else if (q.kind() == GeneratedNpcs.Kind.DELIVER) {
                    int slot = parcelSlot(player, q.id());
                    if (slot < 0) {
                        break;
                    }
                    player.getInventory().getNonEquipmentItems().get(slot).shrink(1);
                    player.getInventory().setChanged();
                }
                reward(player, q);
                npc.nod();
                player.sendSystemMessage(Component.translatable("message.brasshaven.npc.completed", title)
                        .withStyle(ChatFormatting.GREEN));
            }
            case PARCEL_AGAIN -> {
                if (q.kind() == GeneratedNpcs.Kind.DELIVER && q.giver().equals(role) && s == State.ACTIVE
                        && parcelSlot(player, q.id()) < 0) {
                    giveParcel(player, q);
                }
            }
            default -> {
            }
        }
        sync(player);
        open(player, npc);
    }

    private static void giveParcel(ServerPlayer player, GeneratedNpcs.Quest q) {
        ItemStack stack = parcel(q);
        Component name = stack.getHoverName();
        give(player, stack);
        player.sendSystemMessage(Component.translatable("message.brasshaven.npc.parcel", name).withStyle(ChatFormatting.GRAY));
    }

    // ------------------------------------------------------------------ the journal and the tracker

    /** Sends the player's accepted and finished contracts (journal tab, HUD tracker). */
    public static void sync(ServerPlayer player) {
        List<ContractSyncMsg.Entry> list = new ArrayList<>();
        Map<String, Integer> act = active(player);
        Set<String> fin = done(player);
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            if (act.containsKey(q.id()) || fin.contains(q.id())) {
                boolean d = fin.contains(q.id());
                list.add(new ContractSyncMsg.Entry(q.id(), d, d ? needed(q) : progress(player, q), needed(q)));
            }
        }
        BrasshavenNet.toPlayer(player, new ContractSyncMsg(list));
    }

    // ------------------------------------------------------------------ events

    private static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            sync(player);
        }
    }

    private static void onDeath(LivingDeathEvent event) {
        if (!(event.getSource().getEntity() instanceof ServerPlayer player)) {
            return;
        }
        Map<String, Integer> act = active(player);
        if (act.isEmpty()) {
            return;
        }
        String type = BuiltInRegistries.ENTITY_TYPE.getKey(event.getEntity().getType()).toString();
        boolean changed = false;
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            if (q.kind() != GeneratedNpcs.Kind.HUNT || !q.target().equals(type) || !act.containsKey(q.id())) {
                continue;
            }
            int n = act.get(q.id());
            if (n >= q.count()) {
                continue;
            }
            setProgress(player, q.id(), n + 1);
            changed = true;
            player.sendOverlayMessage(Component.translatable("message.brasshaven.npc.progress",
                    Component.translatable("npcquest.brasshaven." + q.id() + ".title"), n + 1, q.count())
                    .withStyle(n + 1 >= q.count() ? ChatFormatting.GREEN : ChatFormatting.GOLD));
        }
        if (changed) {
            sync(player);
        }
    }

    private static void onPlayerTick(TickEvent.PlayerTickEvent.Post event) {
        if (!(event.player() instanceof ServerPlayer player) || player.tickCount % 40 != 7) {
            return;
        }
        Map<String, Integer> act = active(player);
        if (act.isEmpty()) {
            return;
        }
        ServerLevel level = (ServerLevel) player.level();
        var registry = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
        boolean changed = false;
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            if (q.kind() != GeneratedNpcs.Kind.EXPLORE || act.getOrDefault(q.id(), 1) > 0) {
                continue;
            }
            Structure structure = registry.getValue(Identifier.parse(q.target()));
            if (structure != null && level.structureManager().getStructureWithPieceAt(player.blockPosition(), structure).isValid()) {
                setProgress(player, q.id(), 1);
                changed = true;
                player.sendSystemMessage(Component.translatable("message.brasshaven.npc.explored",
                        Component.translatable("npcquest.brasshaven." + q.id() + ".title")).withStyle(ChatFormatting.GREEN));
            }
        }
        if (changed) {
            sync(player);
        }
    }
}
