package com.wayfarers.social;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * The Pneumatic Post: letters and parcels between players, delivered at once into the recipient's inbox, which every
 * Pneumatic Post block opens (like an ender chest, but for mail). The recipient may be offline: anyone who ever
 * joined the server can be written to.
 *
 * <p>Sending costs postage (config) and is rate-limited; a player's inbox holds a limited number of letters (system
 * parcels: contract goods and rewards, items given back, always get through). Taking a parcel's items puts in the
 * inventory what fits and leaves the rest in the parcel: nothing is dropped. A letter can only be thrown away once
 * it holds no items.
 */
public final class Post {
    public static final int MAX_TEXT = 256;
    /** The sender of system parcels. */
    static final UUID SYSTEM = new UUID(0, 0);

    private Post() {}

    static void register() {
    }

    static void onLogin(ServerPlayer player) {
        if (!Social.enabled(Social.Feature.POST)) {
            return;
        }
        int n = SocialData.get(player.level().getServer()).inbox(player.getUUID()).size();
        if (n > 0) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.post.waiting", n).withStyle(ChatFormatting.GOLD));
        }
    }

    static void open(ServerPlayer player, BlockPos pos) {
        if (!Social.require(player, Social.Feature.POST)) {
            return;
        }
        ((net.minecraftforge.common.extensions.IForgeServerPlayer) player).openMenu(
                new SimpleMenuProvider((id, inv, p) -> new PostMenu(id, inv, pos), Component.translatable("block.wayfarers.pneumatic_post")),
                buf -> buf.writeBlockPos(pos));
        if (player.containerMenu instanceof PostMenu m) {
            sendInbox(player, m);
        }
        com.wayfarers.util.Tips.show(player, "pneumatic_post");
    }

    static void sendInbox(ServerPlayer player, PostMenu menu) {
        SocialData data = SocialData.get(player.level().getServer());
        List<SocialNet.ParcelView> views = new ArrayList<>();
        List<SocialData.Parcel> inbox = data.inbox(player.getUUID());
        // newest first
        for (int i = inbox.size() - 1; i >= 0; i--) {
            SocialData.Parcel p = inbox.get(i);
            views.add(new SocialNet.ParcelView(p.id(), p.fromName(), p.text(), p.kind(), p.sentAt(), p.items()));
        }
        List<String> names = new ArrayList<>(data.knownNames());
        names.remove(player.getName().getString());
        names.sort(String.CASE_INSENSITIVE_ORDER);
        if (names.size() > 300) {
            names = names.subList(0, 300);
        }
        SocialNet.toPlayer(player, new SocialNet.Inbox(menu.containerId, views, names));
    }

    static void handle(ServerPlayer player, SocialNet.PostAction msg) {
        if (!(player.containerMenu instanceof PostMenu menu) || menu.containerId != msg.containerId() || !menu.stillValid(player)) {
            return;
        }
        if (!Social.require(player, Social.Feature.POST)) {
            return;
        }
        switch (msg.action()) {
            case REFRESH -> sendInbox(player, menu);
            case SEND -> send(player, menu, msg.recipient(), msg.text());
            case COLLECT -> collect(player, menu, msg.parcel());
            case DISCARD -> discard(player, menu, msg.parcel());
        }
    }

    /** Postage for a parcel of {@code stacks} stacks. */
    static int postage(int stacks) {
        return Social.config().postageBase.get() + Social.config().postagePerStack.get() * stacks;
    }

    private static int count(Inventory inv, Item item) {
        int n = 0;
        for (ItemStack s : inv.getNonEquipmentItems()) {
            if (s.is(item) && s.getComponentsPatch().isEmpty()) {
                n += s.getCount();
            }
        }
        return n;
    }

    private static void pay(Inventory inv, Item item, int amount) {
        for (ItemStack s : inv.getNonEquipmentItems()) {
            if (amount <= 0) {
                break;
            }
            if (s.is(item) && s.getComponentsPatch().isEmpty()) {
                int n = Math.min(amount, s.getCount());
                s.shrink(n);
                amount -= n;
            }
        }
    }

    private static void send(ServerPlayer player, PostMenu menu, String recipientName, String rawText) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        UUID to = data.byName(Social.clean(recipientName, 16));
        if (to == null) {
            Social.fail(player, "message.wayfarers.post.unknown", Social.clean(recipientName, 16));
            return;
        }
        if (to.equals(player.getUUID())) {
            Social.fail(player, "message.wayfarers.post.self");
            return;
        }
        String text = Social.cleanText(rawText, MAX_TEXT, true);
        List<ItemStack> items = menu.attachments();
        if (text.isEmpty() && items.isEmpty()) {
            Social.fail(player, "message.wayfarers.post.empty");
            return;
        }
        long letters = data.inbox(to).stream().filter(p -> !p.system()).count();
        if (letters >= Social.config().inboxLimit.get()) {
            Social.fail(player, "message.wayfarers.post.full", data.name(to));
            return;
        }
        int interval = Math.max(1, 1200 / Social.config().sendsPerMinute.get());
        if (!Social.cooldown(player, "post", interval)) {
            Social.fail(player, "message.wayfarers.social.slow_down");
            return;
        }
        Optional<Item> postage = Social.postageItem();
        int cost = postage(items.size());
        if (postage.isPresent() && cost > 0 && !player.isCreative()) {
            if (count(player.getInventory(), postage.get()) < cost) {
                Social.fail(player, "message.wayfarers.post.postage", cost, new ItemStack(postage.get()).getHoverName());
                return;
            }
            pay(player.getInventory(), postage.get(), cost);
        }
        // the parcel leaves the menu and enters the inbox in the same tick
        menu.parcel.clearContent();
        SocialData.Parcel parcel = new SocialData.Parcel(data.nextId(), player.getUUID(), player.getName().getString(), text,
                items, System.currentTimeMillis(), "letter");
        data.deliver(to, parcel);
        menu.broadcastChanges();
        player.level().playSound(null, menu.pos, SoundEvents.PISTON_EXTEND, SoundSource.BLOCKS, 0.6F, 1.6F);
        player.level().playSound(null, menu.pos, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 0.3F, 1.8F);
        Social.info(player, "message.wayfarers.post.sent", data.name(to));
        com.wayfarers.Wayfarers.LOGGER.info("Post: {} -> {}: {} item stack(s)", player.getName().getString(), data.name(to), items.size());
        notifyRecipient(server, to, player.getName().getString());
        sendInbox(player, menu);
    }

    private static void notifyRecipient(MinecraftServer server, UUID to, String from) {
        ServerPlayer r = Social.online(server, to);
        if (r != null) {
            r.sendSystemMessage(Component.translatable(from.isEmpty() ? "message.wayfarers.post.arrived_system"
                    : "message.wayfarers.post.arrived", from).withStyle(ChatFormatting.GOLD));
            Social.ding(r, SoundEvents.NOTE_BLOCK_CHIME, 1.2F);
            if (r.containerMenu instanceof PostMenu m) {
                sendInbox(r, m);
            }
        }
    }

    /** Delivers a parcel from the post itself (contract goods, rewards, refunds, items given back). */
    static void system(MinecraftServer server, UUID to, String kind, String text, List<ItemStack> items) {
        if (server == null) {
            return;
        }
        List<ItemStack> copy = new ArrayList<>();
        for (ItemStack s : items) {
            if (!s.isEmpty()) {
                copy.add(s.copy());
            }
        }
        // a big delivery is cut in parcels of 27 stacks, so one inbox line never holds a chest's worth
        SocialData data = SocialData.get(server);
        for (int i = 0; i < copy.size() || (i == 0 && copy.isEmpty()); i += 27) {
            List<ItemStack> part = copy.isEmpty() ? List.of() : copy.subList(i, Math.min(copy.size(), i + 27));
            data.deliver(to, new SocialData.Parcel(data.nextId(), SYSTEM, "", Social.clean(text, 64), new ArrayList<>(part),
                    System.currentTimeMillis(), kind));
            if (copy.isEmpty()) {
                break;
            }
        }
        notifyRecipient(server, to, "");
    }

    private static void collect(ServerPlayer player, PostMenu menu, long id) {
        SocialData data = SocialData.get(player.level().getServer());
        SocialData.Parcel p = data.parcel(player.getUUID(), id);
        if (p == null) {
            sendInbox(player, menu);
            return;
        }
        List<ItemStack> left = new ArrayList<>();
        int taken = 0;
        for (ItemStack s : p.items()) {
            ItemStack copy = s.copy();
            int before = copy.getCount();
            player.getInventory().add(copy);
            taken += before - copy.getCount();
            if (!copy.isEmpty()) {
                left.add(copy);
            }
        }
        if (left.isEmpty() && (p.system() || p.text().isEmpty())) {
            data.updateParcel(player.getUUID(), id, null);
        } else {
            data.updateParcel(player.getUUID(), id, new SocialData.Parcel(p.id(), p.from(), p.fromName(), p.text(), left,
                    p.sentAt(), p.kind()));
        }
        if (!left.isEmpty()) {
            Social.fail(player, "message.wayfarers.post.no_room");
        }
        if (taken > 0) {
            player.level().playSound(null, menu.pos, SoundEvents.BUNDLE_REMOVE_ONE, SoundSource.BLOCKS, 0.8F, 1.0F);
        }
        menu.broadcastChanges();
        sendInbox(player, menu);
    }

    private static void discard(ServerPlayer player, PostMenu menu, long id) {
        SocialData data = SocialData.get(player.level().getServer());
        SocialData.Parcel p = data.parcel(player.getUUID(), id);
        if (p != null && p.items().isEmpty()) {
            data.updateParcel(player.getUUID(), id, null);
        } else if (p != null) {
            Social.fail(player, "message.wayfarers.post.not_empty");
        }
        sendInbox(player, menu);
    }
}
