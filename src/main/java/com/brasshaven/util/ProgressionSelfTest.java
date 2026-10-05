package com.brasshaven.util;

import com.brasshaven.Brasshaven;
import com.brasshaven.generated.GeneratedContent;
import com.brasshaven.generated.GeneratedNpcs;
import com.brasshaven.registry.ModItems;
import com.mojang.brigadier.context.CommandContext;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeType;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * {@code /brasshaven progression selftest} (operators; run by the CI server smoke test from the console, where there
 * are no players): the rules of the progression ladder ({@link Progression}) on the loaded server data.
 * <ul>
 *     <li>the first-join kit is the Manual and the Atlas, without the Structure Compass;</li>
 *     <li>the compass contract exists, is a Guild Agent's, gives the compass (through the same reward code as a real
 *     turn-in) and can be reached from a contract without prerequisite, through Guild Agent contracts only;</li>
 *     <li>no other Guild Agent contract before it gives a compass, and the ladder's first quest does not either;</li>
 *     <li>every ladder step is a loaded quest or a known contract, the compass step comes right after the first one
 *     and the first quest can be completed by meeting a Guild Agent;</li>
 *     <li>the crafting gate: a compass and four map fragments no longer make a Structure Compass, the new recipe
 *     (with a Lithite Shard) does;</li>
 *     <li>the places marked on the map have names.</li>
 * </ul>
 * Prints "Progression self-test passed (n checks)" or one "Progression self-test FAILED: ..." line per broken rule.
 */
public final class ProgressionSelfTest {
    private final List<String> failures = new ArrayList<>();
    private int checks;

    private ProgressionSelfTest() {}

    private void check(boolean ok, String what) {
        checks++;
        if (!ok) {
            failures.add(what);
        }
    }

    public static int run(CommandContext<CommandSourceStack> ctx) {
        ProgressionSelfTest t = new ProgressionSelfTest();
        MinecraftServer server = ctx.getSource().getServer();
        try {
            t.kit();
            t.contracts();
            t.ladder(server);
            t.recipe(server);
            t.places();
        } catch (RuntimeException e) {
            t.failures.add("crashed: " + e);
        }
        if (t.failures.isEmpty()) {
            int n = t.checks;
            ctx.getSource().sendSuccess(() -> Component.literal("Progression self-test passed (" + n + " checks)"), false);
            return 1;
        }
        for (String f : t.failures) {
            ctx.getSource().sendFailure(Component.literal("Progression self-test FAILED: " + f));
        }
        return 0;
    }

    private static boolean has(List<ItemStack> stacks, net.minecraft.world.item.Item item) {
        return stacks.stream().anyMatch(s -> s.is(item));
    }

    private void kit() {
        List<ItemStack> kit = Progression.starterKit();
        check(kit.size() == GeneratedContent.STARTER_KIT.size(), "starter kit: unknown item in " + GeneratedContent.STARTER_KIT);
        check(has(kit, ModItems.WAYFARER_MANUAL.get()), "starter kit: no Wayfarer's Manual");
        check(has(kit, ModItems.WAYFARER_ATLAS.get()), "starter kit: no Wayfarer's Atlas");
        check(!has(kit, ModItems.STRUCTURE_COMPASS.get()), "starter kit: the Structure Compass must be earned, not given");
    }

    private void contracts() {
        Optional<GeneratedNpcs.Quest> found = NpcQuests.quest(GeneratedContent.COMPASS_CONTRACT);
        check(found.isPresent(), "compass contract " + GeneratedContent.COMPASS_CONTRACT + " missing");
        if (found.isEmpty()) {
            return;
        }
        GeneratedNpcs.Quest q = found.get();
        check(q.giver().equals("guild_agent"), "compass contract: not a Guild Agent's (" + q.giver() + ")");
        // the reward path of a real turn-in (NpcQuests.reward uses the same stacks)
        check(has(NpcQuests.rewardStacks(q), ModItems.STRUCTURE_COMPASS.get()), "compass contract: no Structure Compass in its rewards");
        // its prerequisites: a chain of Guild Agent contracts back to one without prerequisite, none giving a compass
        Set<String> seen = new HashSet<>();
        GeneratedNpcs.Quest at = q;
        while (!at.after().isEmpty()) {
            if (!seen.add(at.id())) {
                failures.add("compass contract: prerequisite loop at " + at.id());
                return;
            }
            Optional<GeneratedNpcs.Quest> before = NpcQuests.quest(at.after());
            check(before.isPresent(), "compass contract: unknown prerequisite " + at.after());
            if (before.isEmpty()) {
                return;
            }
            at = before.get();
            check(at.giver().equals("guild_agent"), "compass contract: prerequisite " + at.id() + " is not a Guild Agent's");
            check(!has(NpcQuests.rewardStacks(at), ModItems.STRUCTURE_COMPASS.get()),
                    "contract " + at.id() + " gives a compass before the compass contract");
        }
        checks++;
    }

    private void ladder(MinecraftServer server) {
        List<String> ladder = GeneratedContent.LADDER;
        check(!ladder.isEmpty() && ladder.getFirst().equals(Progression.FIRST_STEP), "ladder: must start with " + Progression.FIRST_STEP);
        for (String step : ladder) {
            if (step.startsWith("npc/")) {
                check(NpcQuests.quest(step.substring(4)).isPresent(), "ladder: unknown contract " + step);
            } else {
                check(server.getAdvancements().get(Brasshaven.id(step)) != null, "ladder: quest " + step + " not loaded");
            }
        }
        String compassStep = "npc/" + GeneratedContent.COMPASS_CONTRACT;
        check(ladder.contains(compassStep), "ladder: no compass step " + compassStep);
        // between the first step and the compass: only contracts of its own chain (no detour through a structure)
        int at = ladder.indexOf(compassStep);
        for (int i = 1; i < at; i++) {
            check(ladder.get(i).startsWith("npc/"), "ladder: " + ladder.get(i) + " comes before the compass; it needs no "
                    + "compass, but the first contracts should come first");
        }
        AdvancementHolder first = server.getAdvancements().get(Brasshaven.id(Progression.FIRST_STEP));
        if (first != null) {
            check(first.value().criteria().containsKey(Progression.MET_AGENT), "first quest: no " + Progression.MET_AGENT + " criterion");
            check(first.value().requirements().size() == 1, "first quest: finding an outpost OR meeting an agent must be one objective");
        }
    }

    private void recipe(MinecraftServer server) {
        ServerLevel level = server.overworld();
        ItemStack e = ItemStack.EMPTY;
        ItemStack f = new ItemStack(ModItems.MAP_FRAGMENT.get());
        ItemStack c = new ItemStack(Items.COMPASS);
        ItemStack l = new ItemStack(ModItems.LITHITE_SHARD.get());
        CraftingInput old = CraftingInput.of(3, 3, List.of(e, f, e, f, c, f, e, f, e));
        boolean oldMakes = server.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, old, level)
                .map(h -> h.value().assemble(old).is(ModItems.STRUCTURE_COMPASS.get())).orElse(false);
        check(!oldMakes, "recipe: a compass and four map fragments still make a Structure Compass");
        CraftingInput gated = CraftingInput.of(3, 3, List.of(e, l, e, f, c, f, e, f, e));
        boolean gatedMakes = server.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, gated, level)
                .map(h -> h.value().assemble(gated).is(ModItems.STRUCTURE_COMPASS.get())).orElse(false);
        check(gatedMakes, "recipe: a lithite shard, a compass and three map fragments do not make a Structure Compass");
    }

    private void places() {
        check(GeneratedContent.PLACE_NAMES.containsKey("guild_outpost"), "no map name for the Guild Outpost");
        check(GeneratedContent.PLACE_NAMES.containsKey("village"), "no map name for a village");
        check(StructureLocator.index("guild_outpost") >= 0, "the Guild Outpost is not a known structure");
        for (GeneratedNpcs.Quest q : GeneratedNpcs.QUESTS) {
            if (q.kind() == GeneratedNpcs.Kind.EXPLORE) {
                String id = q.target().substring(q.target().indexOf(':') + 1);
                check(StructureLocator.index(id) >= 0 && GeneratedContent.PLACE_NAMES.containsKey(id),
                        "explore contract " + q.id() + ": unknown structure " + q.target());
            }
        }
    }
}
