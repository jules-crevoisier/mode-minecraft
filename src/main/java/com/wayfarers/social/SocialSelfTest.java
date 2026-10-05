package com.wayfarers.social;

import com.google.gson.JsonArray;
import com.google.gson.JsonPrimitive;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.NbtOps;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.RegistryOps;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * {@code /wayfarers social selftest} (operators; run by the CI server smoke test from the console, where there are no
 * players): checks the server-side rules of the multiplayer features without a client. Saved data round trip (with
 * items and components), lenient decoding, trade space maths, contract matching and item conservation, shared
 * experience maths, text cleaning, the duel ring, inbox edits, contract expiry with refund by post, and the config.
 * Prints "Social self-test passed (n checks)" or one "Social self-test FAILED: ..." line per broken rule.
 */
final class SocialSelfTest {
    private final List<String> failures = new ArrayList<>();
    private int checks;

    private SocialSelfTest() {}

    private void check(boolean ok, String what) {
        checks++;
        if (!ok) {
            failures.add(what);
        }
    }

    static int run(CommandContext<CommandSourceStack> ctx) {
        SocialSelfTest t = new SocialSelfTest();
        MinecraftServer server = ctx.getSource().getServer();
        try {
            t.data(server);
            t.lenient();
            t.trade();
            t.contracts();
            t.sharing();
            t.text();
            t.ring();
            t.expiry(server);
            t.config();
        } catch (RuntimeException e) {
            t.failures.add("crashed: " + e);
        }
        if (t.failures.isEmpty()) {
            int n = t.checks;
            ctx.getSource().sendSuccess(() -> Component.literal("Social self-test passed (" + n + " checks)"), false);
            return 1;
        }
        for (String f : t.failures) {
            ctx.getSource().sendFailure(Component.literal("Social self-test FAILED: " + f));
        }
        return 0;
    }

    private static int total(List<ItemStack> stacks, ItemStack like) {
        int n = 0;
        for (ItemStack s : stacks) {
            if (ItemStack.isSameItemSameComponents(s, like)) {
                n += s.getCount();
            }
        }
        return n;
    }

    /** Saved data survives a save and load with every kind of record, items and components included. */
    private void data(MinecraftServer server) {
        SocialData d = new SocialData();
        UUID a = UUID.randomUUID();
        UUID b = UUID.randomUUID();
        d.rememberName(a, "Alice");
        d.rememberName(b, "Bob");
        SocialData.Company c = d.newCompany("Brass Owls", a, "Alice");
        c.members.put(b, new SocialData.Member(b, "Bob"));
        c.friendlyFire = true;
        ItemStack named = new ItemStack(Items.DIAMOND_SWORD);
        named.set(DataComponents.CUSTOM_NAME, Component.literal("Clockwork Edge"));
        d.deliver(b, new SocialData.Parcel(d.nextId(), a, "Alice", "Hello\nBob", List.of(new ItemStack(Items.IRON_INGOT, 64), named),
                1234L, "letter"));
        d.addContract(d.newContract(a, "Alice", new ItemStack(Items.OAK_LOG), 128, "for the airship",
                List.of(new ItemStack(Items.EMERALD, 5)), 10L, 20L));
        d.recordDuel(a, 1, 0, 0);
        d.recordDuel(b, 0, 1, 0);
        RegistryOps<Tag> ops = server.registryAccess().createSerializationContext(NbtOps.INSTANCE);
        Tag saved = SocialData.CODEC.encodeStart(ops, d).getOrThrow();
        SocialData back = SocialData.CODEC.parse(ops, saved).getOrThrow();
        check(back.name(b).equals("Bob") && back.byName("alice") != null && a.equals(back.byName("ALICE")), "names round trip");
        SocialData.Company bc = back.companyOf(b);
        check(bc != null && bc.name.equals("Brass Owls") && bc.leader.equals(a) && bc.members.size() == 2 && bc.friendlyFire
                && !bc.shareXp, "company round trip");
        List<SocialData.Parcel> inbox = back.inbox(b);
        check(inbox.size() == 1 && inbox.get(0).text().equals("Hello\nBob") && inbox.get(0).items().size() == 2
                && ItemStack.matches(inbox.get(0).items().get(1), named) && inbox.get(0).items().get(0).getCount() == 64,
                "parcel round trip");
        SocialData.Contract ct = back.contracts().iterator().next();
        check(back.contracts().size() == 1 && ct.amount == 128 && ct.wanted.is(Items.OAK_LOG) && ct.wanted.getCount() == 1
                && ct.reward.size() == 1 && ct.reward.get(0).getCount() == 5 && ct.note.equals("for the airship"), "contract round trip");
        check(back.duelRecord(a).wins() == 1 && back.duelRecord(b).losses() == 1, "duel records round trip");
        // inbox edits: take part of a parcel, then remove it
        long id = inbox.get(0).id();
        back.updateParcel(b, id, new SocialData.Parcel(id, a, "Alice", "Hello\nBob", List.of(named), 1234L, "letter"));
        check(back.parcel(b, id) != null && back.parcel(b, id).items().size() == 1, "parcel update");
        back.updateParcel(b, id, null);
        check(back.inbox(b).isEmpty(), "parcel removal");
        long n1 = back.nextId();
        check(back.nextId() == n1 + 1, "ids increase");
    }

    /** A broken element costs only itself. */
    private void lenient() {
        JsonArray arr = new JsonArray();
        arr.add(new JsonPrimitive(1));
        arr.add(new JsonPrimitive("not a number"));
        arr.add(new JsonPrimitive(3));
        List<Integer> out = SocialCodecs.lenientList(Codec.INT, "self-test number").parse(JsonOps.INSTANCE, arr).getOrThrow();
        check(out.equals(List.of(1, 3)), "lenient list skips a broken element");
    }

    private static NonNullList<ItemStack> inventory() {
        return NonNullList.withSize(36, ItemStack.EMPTY);
    }

    /** Trades only happen when everything fits. */
    private void trade() {
        NonNullList<ItemStack> inv = inventory();
        for (int i = 0; i < 35; i++) {
            inv.set(i, new ItemStack(Items.STONE, 64));
        }
        check(Trade.fits(inv, List.of(new ItemStack(Items.DIRT, 64))), "one stack fits one empty slot");
        check(!Trade.fits(inv, List.of(new ItemStack(Items.DIRT, 64), new ItemStack(Items.DIRT, 1))), "two stacks do not fit one slot");
        inv.set(35, new ItemStack(Items.STONE, 60));
        check(Trade.fits(inv, List.of(new ItemStack(Items.STONE, 4))), "items stack onto a partial stack");
        check(!Trade.fits(inv, List.of(new ItemStack(Items.STONE, 5))), "no room past a full inventory");
        check(inv.get(35).getCount() == 60, "the space check works on copies");
        check(!Trade.fits(inv, List.of(new ItemStack(Items.DIAMOND_SWORD))), "unstackable items need an empty slot");
    }

    /** Deliveries take exactly the items asked for, and no item appears or disappears. */
    private void contracts() {
        NonNullList<ItemStack> inv = inventory();
        inv.set(0, new ItemStack(Items.IRON_INGOT, 30));
        inv.set(5, new ItemStack(Items.IRON_INGOT, 10));
        ItemStack renamed = new ItemStack(Items.IRON_INGOT, 5);
        renamed.set(DataComponents.CUSTOM_NAME, Component.literal("Lucky ingot"));
        inv.set(7, renamed);
        ItemStack wanted = Contracts.sample(new ItemStack(Items.IRON_INGOT, 17));
        check(wanted.getCount() == 1, "a sample is one item");
        check(Contracts.count(inv, wanted) == 40, "renamed items do not count as plain ones");
        List<ItemStack> goods = Contracts.take(inv, wanted, 32);
        check(total(goods, wanted) == 32 && goods.stream().allMatch(s -> s.getCount() <= s.getMaxStackSize()), "delivery takes 32");
        check(Contracts.count(inv, wanted) == 8 && inv.get(7).getCount() == 5, "the rest stays in the inventory");
        ItemStack worn = new ItemStack(Items.IRON_PICKAXE);
        worn.setDamageValue(100);
        ItemStack s = Contracts.sample(worn);
        check(s.getDamageValue() == 0, "a sample of a worn tool asks for an undamaged one");
        NonNullList<ItemStack> inv2 = inventory();
        inv2.set(0, worn);
        check(Contracts.count(inv2, s) == 0, "a worn tool does not fulfil a contract");
    }

    /** Shared experience never creates experience. */
    private void sharing() {
        for (int amount : new int[] {1, 2, 7, 10, 100}) {
            for (int mates = 1; mates <= 7; mates++) {
                int[] r = Companies.split(amount, mates);
                check(r[0] * mates + r[1] == amount && r[1] >= r[0] && r[0] >= 0, "xp split " + amount + "/" + mates);
            }
        }
    }

    private void text() {
        check(Social.clean("§cHi\u0000 there  ", 64).equals("Hi there"), "formatting codes and control characters removed");
        check(Social.cleanText("a\nb", 64, true).equals("a\nb") && Social.clean("a\nb", 64).equals("ab"), "line breaks only in letters");
        check(Social.clean("x".repeat(500), 24).length() == 24, "length cap");
    }

    private void ring() {
        check(Duels.inRing(0, 0, 20, 14, 14) && !Duels.inRing(0, 0, 20, 15, 15), "duel ring");
    }

    /** An expired contract leaves the board and its reward goes back to the poster by post. */
    private void expiry(MinecraftServer server) {
        SocialData d = SocialData.get(server);
        UUID ghost = UUID.randomUUID();
        SocialData.Contract c = d.newContract(ghost, "SelfTest", new ItemStack(Items.COBBLESTONE), 1, "",
                List.of(new ItemStack(Items.GOLD_INGOT, 3)), 0L, 1L);
        d.addContract(c);
        int expired = Contracts.expire(server, 2L);
        check(expired >= 1 && d.contract(c.id) == null, "contract expired");
        List<SocialData.Parcel> in = d.inbox(ghost);
        check(in.size() == 1 && in.get(0).kind().equals("refund") && total(in.get(0).items(), new ItemStack(Items.GOLD_INGOT)) == 3,
                "refund by post");
        for (SocialData.Parcel p : new ArrayList<>(in)) {
            d.updateParcel(ghost, p.id(), null);
        }
        check(d.inbox(ghost).isEmpty(), "self-test leaves no trace");
    }

    private void config() {
        check(Social.config().companyMaxSize.get() >= 2, "company size");
        check(Social.config().postageItem.get().isBlank() || Social.postageItem().isPresent(), "postage item exists");
        check(Social.hello() != null, "feature switches");
    }
}
