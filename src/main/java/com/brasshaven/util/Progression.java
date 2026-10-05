package com.brasshaven.util;

import com.brasshaven.Brasshaven;
import com.brasshaven.generated.GeneratedContent;
import com.brasshaven.generated.GeneratedNpcs;
import com.brasshaven.map.MapServer;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * The progression ladder ({@link GeneratedContent#LADDER}, written in tools/wf/progression.py): a newcomer receives
 * only the Manual and the Atlas, is pointed to the nearest Guild Outpost, and earns the rest step by step. The
 * Structure Compass is the reward of the Guild Agent's survey contract ({@link GeneratedContent#COMPASS_CONTRACT}).
 *
 * <p>Advancement steps follow {@code quests.shareProgress} / {@code quests.catchUpOnJoin} like every quest; contract
 * steps are always per player (kept in the player's data by {@link NpcQuests}), so a player who joins an old server
 * still earns their own compass. Directions are given as private map waypoints ({@link MapServer#guideWaypoint}) and a
 * chat line with distance, heading and coordinates.
 */
public final class Progression {
    /** The ladder's first step: meet a Guild Agent (at a Guild Outpost, or any Guild Agent: criterion "met_agent"). */
    public static final String FIRST_STEP = "first_steps/guild_outpost";
    public static final String MET_AGENT = "met_agent";
    /** Search radii (chunks): the Guild Outpost (as far as the Structure Compass looks), a village, a contract's target. */
    static final int GUILD_RADIUS = 100;
    static final int VILLAGE_RADIUS = 64;
    static final int TARGET_RADIUS = 100;
    private static final int GOLD = 0xE8B23A;
    private static final int CYAN = 0x4FC3D9;
    private static final int ICON_HOUSE = 1;
    private static final int ICON_STAR = 2;
    /** Under the player's "PlayerPersisted" data: what the first-join guidance found ("guild_outpost x z",
     * "village x z" or "none"), for operators and the CI client test. */
    public static final String KEY = "brasshaven_guide";

    private Progression() {}

    // ------------------------------------------------------------------ the ladder

    /** Whether the player has done a ladder step (an unknown advancement counts as done, so it is skipped). */
    public static boolean done(ServerPlayer player, String step) {
        if (step.startsWith("npc/")) {
            return NpcQuests.done(player).contains(step.substring(4));
        }
        AdvancementHolder holder = player.level().getServer().getAdvancements().get(Brasshaven.id(step));
        return holder == null || player.getAdvancements().getOrStartProgress(holder).isDone();
    }

    /** The first ladder step the player has not done, or "" when the whole ladder is done. */
    public static String next(ServerPlayer player) {
        for (String step : GeneratedContent.LADDER) {
            if (!done(player, step)) {
                return step;
            }
        }
        return "";
    }

    /** Title of a ladder step (a quest or a contract). */
    public static Component title(String step) {
        return step.startsWith("npc/") ? Component.translatable("npcquest.brasshaven." + step.substring(4) + ".title")
                : Component.translatable("advancements.brasshaven." + step.replace('/', '.') + ".title");
    }

    // ------------------------------------------------------------------ first join

    /** The first-join kit ({@link GeneratedContent#STARTER_KIT}): the Manual and the Atlas, nothing else. */
    public static List<ItemStack> starterKit() {
        List<ItemStack> out = new ArrayList<>();
        for (String id : GeneratedContent.STARTER_KIT) {
            BuiltInRegistries.ITEM.getOptional(Identifier.parse(id)).ifPresent(item -> out.add(new ItemStack(item)));
        }
        return out;
    }

    /** A player's very first login on this world: the kit, the welcome line and the way to the first Guild Agent. */
    public static void welcome(ServerPlayer player) {
        for (ItemStack stack : starterKit()) {
            if (!player.getInventory().add(stack)) {
                player.drop(stack, false);
            }
        }
        player.sendSystemMessage(Component.translatable("message.brasshaven.welcome", Component.keybind("key.brasshaven.quests"))
                .withStyle(ChatFormatting.GOLD));
        pointToGuild(player, false);
    }

    // ------------------------------------------------------------------ directions

    /**
     * Marks the nearest Guild Outpost on the player's map (a village when there is no outpost within reach) and says
     * where it is. {@code budgeted}: a search spends one of the server-wide compass searches (the Atlas asks again
     * on every use until the first step is done).
     */
    public static void pointToGuild(ServerPlayer player, boolean budgeted) {
        ServerLevel level = player.level();
        if (level.dimension() != Level.OVERWORLD) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.guide.overworld").withStyle(ChatFormatting.GRAY));
            return;
        }
        BlockPos from = player.blockPosition();
        int index = StructureLocator.index("guild_outpost");
        StructureLocator.Found found = index < 0 ? null : locate(level, from, index, GUILD_RADIUS, budgeted);
        if (found == StructureLocator.BUSY) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.compass.busy").withStyle(ChatFormatting.GRAY));
            return;
        }
        String kind = "guild_outpost";
        if (found == null) {
            found = locate(level, from, StructureLocator.VILLAGE, VILLAGE_RADIUS, budgeted);
            if (found == StructureLocator.BUSY) {
                player.sendSystemMessage(Component.translatable("message.brasshaven.compass.busy").withStyle(ChatFormatting.GRAY));
                return;
            }
            kind = "village";
        }
        if (found == null) {
            remember(player, "none");
            player.sendSystemMessage(Component.translatable("message.brasshaven.guide.none").withStyle(ChatFormatting.GOLD));
            return;
        }
        BlockPos pos = found.pos();
        MapServer.guideWaypoint(player, "guild", placeName(player, kind), level, pos, GOLD, ICON_HOUSE);
        remember(player, kind + " " + pos.getX() + " " + pos.getZ());
        player.sendSystemMessage(directions(kind.equals("village") ? "message.brasshaven.guide.village"
                : "message.brasshaven.guide.guild", null, from, pos).withStyle(ChatFormatting.GOLD));
    }

    private static StructureLocator.Found locate(ServerLevel level, BlockPos from, int index, int radius, boolean budgeted) {
        return budgeted ? StructureLocator.nearestBudgeted(level, from, index, radius)
                : StructureLocator.nearest(level, from, index, radius);
    }

    private static MutableComponent directions(String key, Component name, BlockPos from, BlockPos to) {
        int distance = (int) Math.sqrt(from.distSqr(new BlockPos(to.getX(), from.getY(), to.getZ())));
        String dir = StructureLocator.compassDirection(from, to);
        return name == null ? Component.translatable(key, distance, dir, to.getX(), to.getZ())
                : Component.translatable(key, name, distance, dir, to.getX(), to.getZ());
    }

    private static void remember(ServerPlayer player, String what) {
        CompoundTag root = player.getPersistentData();
        CompoundTag persisted = root.getCompoundOrEmpty("PlayerPersisted");
        persisted.putString(KEY, what);
        root.put("PlayerPersisted", persisted);
    }

    /** What the guidance last found for this player ("" when it never ran). */
    public static String remembered(ServerPlayer player) {
        return player.getPersistentData().getCompoundOrEmpty("PlayerPersisted").getStringOr(KEY, "");
    }

    /** A place name in the player's language (waypoint names are plain text). */
    static String placeName(ServerPlayer player, String id) {
        List<String> names = GeneratedContent.PLACE_NAMES.get(id);
        if (names == null) {
            return id;
        }
        String lang = player.clientInformation().language();
        return names.get(lang != null && lang.toLowerCase(Locale.ROOT).startsWith("fr") ? 1 : 0);
    }

    // ------------------------------------------------------------------ hooks (NpcQuests, the Atlas)

    /** Talking to any Guild Agent completes the first step, even away from a Guild Outpost (a village Guild Post). */
    public static void metAgent(ServerPlayer player) {
        AdvancementHolder holder = player.level().getServer().getAdvancements().get(Brasshaven.id(FIRST_STEP));
        if (holder != null && !player.getAdvancements().getOrStartProgress(holder).isDone()) {
            player.getAdvancements().award(holder, MET_AGENT);
        }
    }

    /** The Atlas, used before the first step is done, shows the way to the Guild again. */
    public static void atlasUsed(ServerPlayer player) {
        if (!done(player, FIRST_STEP)) {
            pointToGuild(player, true);
        }
    }

    /** An "explore" contract was accepted: its nearest target structure goes on the player's map. */
    public static void contractAccepted(ServerPlayer player, GeneratedNpcs.Quest q) {
        if (q.kind() != GeneratedNpcs.Kind.EXPLORE) {
            return;
        }
        String id = q.target().substring(q.target().indexOf(':') + 1);
        int index = StructureLocator.index(id);
        ServerLevel level = player.level();
        if (index < 0 || !GeneratedContent.STRUCTURES.get(index).dimension()
                .equals(level.dimension().identifier().getPath().replace("the_", ""))) {
            return;
        }
        BlockPos from = player.blockPosition();
        StructureLocator.Found found = StructureLocator.nearest(level, from, index, TARGET_RADIUS);
        Component name = Component.translatable("structure.brasshaven." + id);
        if (found == null) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.guide.target_none", name, TARGET_RADIUS * 16)
                    .withStyle(ChatFormatting.GRAY));
            return;
        }
        MapServer.guideWaypoint(player, "contract_" + q.id(), placeName(player, id), level, found.pos(), CYAN, ICON_STAR);
        player.sendSystemMessage(directions("message.brasshaven.guide.target", name, from, found.pos())
                .withStyle(ChatFormatting.AQUA));
    }

    /** A contract was handed in: its map mark goes away; the compass contract explains the compass once. */
    public static void contractFinished(ServerPlayer player, GeneratedNpcs.Quest q) {
        MapServer.removeGuideWaypoint(player, "contract_" + q.id());
        Item compass = com.brasshaven.registry.ModItems.STRUCTURE_COMPASS.get();
        for (GeneratedNpcs.Reward r : q.rewards()) {
            if (BuiltInRegistries.ITEM.getOptional(Identifier.parse(r.item())).orElse(null) == compass) {
                Tips.show(player, "compass");
            }
        }
    }
}
