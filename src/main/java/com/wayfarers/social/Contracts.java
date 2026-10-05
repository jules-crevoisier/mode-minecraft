package com.wayfarers.social;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.Permissions;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.TickEvent;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Guild contracts: "bring me 32 iron ingots, I pay 3 diamonds". The poster puts a sample of the wanted item and the
 * reward in a Contract Board; the reward leaves their hands at once and is held by the contract (escrow). Anyone else
 * who has the goods in their inventory clicks Deliver: in the same tick the exact items (same item, same components,
 * undamaged) leave the deliverer's inventory for the poster's Pneumatic Post inbox, and the reward goes to the
 * deliverer (inventory, the rest by post). The poster may cancel an open contract (reward back); after
 * {@code contracts.expiryDays} it expires and the reward goes back by post. Operators can cancel any contract.
 */
public final class Contracts {
    public static final int MAX_NOTE = 64;
    public static final int MAX_AMOUNT = 999;

    private Contracts() {}

    static void register() {
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> {
            if (e.server().getTickCount() % 1200 == 600) {
                expire(e.server(), System.currentTimeMillis());
            }
        });
    }

    /** What a contract asks for, from the item shown: one, undamaged, everything else exact. */
    static ItemStack sample(ItemStack shown) {
        ItemStack s = shown.copyWithCount(1);
        if (s.isDamageableItem()) {
            s.setDamageValue(0);
        }
        return s;
    }

    static boolean matches(ItemStack stack, ItemStack wanted) {
        return !stack.isEmpty() && ItemStack.isSameItemSameComponents(stack, wanted);
    }

    /** How many of the wanted item these slots hold. */
    static int count(List<ItemStack> slots, ItemStack wanted) {
        int n = 0;
        for (ItemStack s : slots) {
            if (matches(s, wanted)) {
                n += s.getCount();
            }
        }
        return n;
    }

    /** Takes {@code amount} of the wanted item out of these slots; returns them as full stacks. Check {@link #count} first. */
    static List<ItemStack> take(List<ItemStack> slots, ItemStack wanted, int amount) {
        int left = amount;
        for (ItemStack s : slots) {
            if (left <= 0) {
                break;
            }
            if (matches(s, wanted)) {
                int n = Math.min(left, s.getCount());
                s.shrink(n);
                left -= n;
            }
        }
        List<ItemStack> out = new ArrayList<>();
        int taken = amount - left;
        int max = Math.max(1, wanted.getMaxStackSize());
        while (taken > 0) {
            int n = Math.min(max, taken);
            out.add(wanted.copyWithCount(n));
            taken -= n;
        }
        return out;
    }

    // ------------------------------------------------------------------ the board
    static void open(ServerPlayer player, BlockPos pos) {
        if (!Social.require(player, Social.Feature.CONTRACTS)) {
            return;
        }
        ((net.minecraftforge.common.extensions.IForgeServerPlayer) player).openMenu(
                new SimpleMenuProvider((id, inv, p) -> new ContractMenu(id, inv, pos), Component.translatable("block.wayfarers.contract_board")),
                buf -> buf.writeBlockPos(pos));
        if (player.containerMenu instanceof ContractMenu m) {
            sendBoard(player, m);
        }
        com.wayfarers.util.Tips.show(player, "contract_board");
    }

    static void sendBoard(ServerPlayer player, ContractMenu menu) {
        SocialData data = SocialData.get(player.level().getServer());
        List<SocialData.Contract> all = new ArrayList<>(data.contracts());
        // yours first, then the newest
        all.sort(Comparator.comparing((SocialData.Contract c) -> !c.poster.equals(player.getUUID()))
                .thenComparing(c -> -c.postedAt));
        List<SocialNet.ContractView> views = new ArrayList<>();
        int mine = 0;
        for (SocialData.Contract c : all) {
            boolean own = c.poster.equals(player.getUUID());
            if (own) {
                mine++;
            }
            views.add(new SocialNet.ContractView(c.id, c.posterName, own, c.wanted, c.amount, c.note, c.reward, c.expiresAt));
        }
        SocialNet.toPlayer(player, new SocialNet.Board(menu.containerId, views, mine));
    }

    static void handle(ServerPlayer player, SocialNet.BoardAction msg) {
        if (!(player.containerMenu instanceof ContractMenu menu) || menu.containerId != msg.containerId() || !menu.stillValid(player)) {
            return;
        }
        if (!Social.require(player, Social.Feature.CONTRACTS)) {
            return;
        }
        switch (msg.action()) {
            case REFRESH -> sendBoard(player, menu);
            case POST -> post(player, menu, msg.amount(), msg.note());
            case DELIVER -> deliver(player, menu, msg.contract());
            case CANCEL -> cancel(player, menu, msg.contract());
        }
    }

    private static void post(ServerPlayer player, ContractMenu menu, int amount, String rawNote) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        ItemStack wanted = menu.wantedItem();
        List<ItemStack> reward = menu.rewards();
        if (wanted.isEmpty()) {
            Social.fail(player, "message.wayfarers.contract.no_sample");
            return;
        }
        if (reward.isEmpty()) {
            Social.fail(player, "message.wayfarers.contract.no_reward");
            return;
        }
        if (amount < 1 || amount > MAX_AMOUNT) {
            Social.fail(player, "message.wayfarers.contract.amount", MAX_AMOUNT);
            return;
        }
        long open = data.contracts().stream().filter(c -> c.poster.equals(player.getUUID())).count();
        if (open >= Social.config().contractsPerPlayer.get()) {
            Social.fail(player, "message.wayfarers.contract.too_many", Social.config().contractsPerPlayer.get());
            return;
        }
        if (!Social.cooldown(player, "contract_post", 60)) {
            Social.fail(player, "message.wayfarers.social.slow_down");
            return;
        }
        long now = System.currentTimeMillis();
        long expires = now + Social.config().contractDays.get() * 86_400_000L;
        // escrow: the reward leaves the menu and enters the contract in the same tick
        menu.reward.clearContent();
        menu.wanted.clearContent();
        SocialData.Contract c = data.newContract(player.getUUID(), player.getName().getString(), sample(wanted), amount,
                Social.clean(rawNote, MAX_NOTE), reward, now, expires);
        data.addContract(c);
        menu.broadcastChanges();
        player.level().playSound(null, menu.pos, SoundEvents.BOOK_PAGE_TURN, SoundSource.BLOCKS, 1.0F, 1.0F);
        com.wayfarers.Wayfarers.LOGGER.info("Contract {} posted by {}: {} x {} for {}", c.id, c.posterName, amount, c.wanted, reward);
        Component line = Component.translatable("message.wayfarers.contract.posted", player.getName(), amount, c.wanted.getHoverName())
                .withStyle(ChatFormatting.GOLD);
        if (Social.cooldown(player, "contract_announce", 20 * 60)) {
            server.getPlayerList().broadcastSystemMessage(line, false);
        } else {
            player.sendSystemMessage(line);
        }
        sendBoard(player, menu);
    }

    private static void deliver(ServerPlayer player, ContractMenu menu, long id) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Contract c = data.contract(id);
        if (c == null) {
            Social.fail(player, "message.wayfarers.contract.gone");
            sendBoard(player, menu);
            return;
        }
        if (c.poster.equals(player.getUUID())) {
            Social.fail(player, "message.wayfarers.contract.own");
            return;
        }
        List<ItemStack> slots = player.getInventory().getNonEquipmentItems();
        int have = count(slots, c.wanted);
        if (have < c.amount) {
            Social.fail(player, "message.wayfarers.contract.missing", c.amount - have, c.wanted.getHoverName());
            return;
        }
        if (!Social.cooldown(player, "contract_deliver", 10)) {
            return;
        }
        // one tick: off the board, goods out of the inventory to the poster's inbox, reward to the deliverer
        data.removeContract(id);
        List<ItemStack> goods = take(slots, c.wanted, c.amount);
        player.getInventory().setChanged();
        Post.system(server, c.poster, "delivery", player.getName().getString(), goods);
        Social.giveOrMail(player, c.reward, "reward");
        menu.broadcastChanges();
        player.level().playSound(null, menu.pos, SoundEvents.VILLAGER_YES, SoundSource.BLOCKS, 0.8F, 1.0F);
        player.level().playSound(null, menu.pos, SoundEvents.PLAYER_LEVELUP, SoundSource.BLOCKS, 0.5F, 1.4F);
        com.wayfarers.Wayfarers.LOGGER.info("Contract {} delivered by {} to {}", c.id, player.getName().getString(), c.posterName);
        Social.info(player, "message.wayfarers.contract.delivered", c.posterName);
        ServerPlayer poster = Social.online(server, c.poster);
        if (poster != null) {
            Social.info(poster, "message.wayfarers.contract.fulfilled", player.getName(), c.amount, c.wanted.getHoverName());
        }
        com.wayfarers.util.Tips.show(player, "pneumatic_post");
        sendBoard(player, menu);
    }

    private static void cancel(ServerPlayer player, ContractMenu menu, long id) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Contract c = data.contract(id);
        if (c == null) {
            sendBoard(player, menu);
            return;
        }
        boolean own = c.poster.equals(player.getUUID());
        if (!own && !player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)) {
            Social.fail(player, "message.wayfarers.contract.not_yours");
            return;
        }
        data.removeContract(id);
        if (own) {
            Social.giveOrMail(player, c.reward, "refund");
        } else {
            Post.system(server, c.poster, "refund", "", c.reward);
        }
        Social.info(player, "message.wayfarers.contract.cancelled");
        com.wayfarers.Wayfarers.LOGGER.info("Contract {} of {} cancelled by {}", c.id, c.posterName, player.getName().getString());
        sendBoard(player, menu);
    }

    /** Expired contracts give their reward back to the poster by post. Returns how many expired. */
    static int expire(MinecraftServer server, long now) {
        SocialData data = SocialData.get(server);
        List<SocialData.Contract> old = data.contracts().stream().filter(c -> c.expiresAt <= now).toList();
        for (SocialData.Contract c : old) {
            data.removeContract(c.id);
            Post.system(server, c.poster, "refund", "", c.reward);
        }
        return old.size();
    }
}
