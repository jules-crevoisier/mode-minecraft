package com.brasshaven.social;

import net.minecraft.ChatFormatting;
import net.minecraft.core.NonNullList;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * Secure trade between two players standing close together.
 *
 * <p>Each puts items in their own 9-slot offer, which the session holds (not the player). Both see both offers live.
 * When both press Accept a 3-second countdown starts; any change to either offer, or either player pressing Accept
 * again, stops it and clears both acceptances, so nobody can swap an item at the last moment. At zero the server
 * checks that each side's items fit in the other's inventory, then moves everything in that same tick: no item exists
 * twice and none is lost. Anything that ends a trade early (closing the screen, walking away, changing dimension,
 * dying, logging out, the server stopping) gives each offer back to its owner, through {@link Social#giveOrMail}.
 * Every completed trade is written to the server log.
 */
public final class Trade {
    private static final int COUNTDOWN = 60;
    private static final List<Session> SESSIONS = new ArrayList<>();

    private Trade() {}

    static void register() {
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick());
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                cancel(p, "message.brasshaven.trade.cancel_left");
            }
        });
        // a dead player's offer goes to their own inbox (giveOrMail), never into the death drops
        LivingDeathEvent.BUS.addListener((Consumer<LivingDeathEvent>) e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                cancel(p, "message.brasshaven.trade.cancel_left");
            }
        });
    }

    public static boolean trading(ServerPlayer p) {
        return session(p) != null;
    }

    private static Session session(ServerPlayer p) {
        for (Session s : SESSIONS) {
            if (!s.closed && (s.players[0] == p || s.players[1] == p)) {
                return s;
            }
        }
        return null;
    }

    private static void cancel(ServerPlayer p, String why) {
        Session s = session(p);
        if (s != null) {
            s.cancel(why);
        }
    }

    static void cancelAll() {
        for (Session s : new ArrayList<>(SESSIONS)) {
            s.cancel("message.brasshaven.trade.cancel_left");
        }
        SESSIONS.clear();
    }

    private static void tick() {
        if (SESSIONS.isEmpty()) {
            return;
        }
        for (Session s : new ArrayList<>(SESSIONS)) {
            s.tick();
        }
        SESSIONS.removeIf(s -> s.closed);
    }

    // ------------------------------------------------------------------ requests
    private static String problem(ServerPlayer a, ServerPlayer b) {
        if (a.level() != b.level() || a.distanceTo(b) > Social.config().tradeDistance.get()) {
            return "message.brasshaven.trade.too_far";
        }
        if (!a.isAlive() || !b.isAlive() || a.isSpectator() || b.isSpectator()) {
            return "message.brasshaven.trade.busy";
        }
        if (trading(a) || trading(b) || Duels.inDuel(a) || Duels.inDuel(b)) {
            return "message.brasshaven.trade.busy";
        }
        return null;
    }

    static void request(ServerPlayer from, ServerPlayer to) {
        if (!Social.require(from, Social.Feature.TRADE) || from == to) {
            return;
        }
        String p = problem(from, to);
        if (p != null) {
            Social.fail(from, p, to.getName());
            return;
        }
        if (!Social.cooldown(from, "trade:" + to.getUUID(), 60)) {
            Social.fail(from, "message.brasshaven.social.slow_down");
            return;
        }
        if (Social.request(from, to, Social.RequestType.TRADE, 0, Component.translatable("message.brasshaven.trade.request", from.getName()))) {
            Social.info(from, "message.brasshaven.social.request_sent", to.getName());
        }
    }

    static void accept(ServerPlayer to, Social.Request req) {
        ServerPlayer from = req == null ? null : Social.online(to.level().getServer(), req.from());
        if (from == null) {
            Social.fail(to, "message.brasshaven.social.no_request");
            return;
        }
        if (!Social.require(to, Social.Feature.TRADE)) {
            return;
        }
        String p = problem(from, to);
        if (p != null) {
            Social.fail(to, p, from.getName());
            return;
        }
        Session s = new Session(from, to);
        SESSIONS.add(s);
        s.open();
        com.brasshaven.util.Tips.show(from, "trade");
        com.brasshaven.util.Tips.show(to, "trade");
    }

    // ------------------------------------------------------------------ inventory maths (also used by the self-test)
    /**
     * Whether every stack of {@code incoming} fits into these 36 main-inventory slots (stacking onto equal items,
     * then into empty slots), worked out on copies.
     */
    static boolean fits(List<ItemStack> slots, List<ItemStack> incoming) {
        List<ItemStack> sim = new ArrayList<>();
        for (ItemStack s : slots) {
            sim.add(s.copy());
        }
        for (ItemStack in : incoming) {
            int left = in.getCount();
            for (ItemStack s : sim) {
                if (left <= 0) {
                    break;
                }
                if (!s.isEmpty() && ItemStack.isSameItemSameComponents(s, in) && s.isStackable()) {
                    int room = s.getMaxStackSize() - s.getCount();
                    if (room > 0) {
                        int n = Math.min(room, left);
                        s.grow(n);
                        left -= n;
                    }
                }
            }
            for (int i = 0; i < sim.size() && left > 0; i++) {
                if (sim.get(i).isEmpty()) {
                    int n = Math.min(in.getMaxStackSize(), left);
                    sim.set(i, in.copyWithCount(n));
                    left -= n;
                }
            }
            if (left > 0) {
                return false;
            }
        }
        return true;
    }

    private static List<ItemStack> mainSlots(ServerPlayer p) {
        NonNullList<ItemStack> items = p.getInventory().getNonEquipmentItems();
        return items.subList(0, Math.min(items.size(), Inventory.INVENTORY_SIZE));
    }

    private static List<ItemStack> contents(SimpleContainer c) {
        List<ItemStack> out = new ArrayList<>();
        for (int i = 0; i < c.getContainerSize(); i++) {
            if (!c.getItem(i).isEmpty()) {
                out.add(c.getItem(i).copy());
            }
        }
        return out;
    }

    // ------------------------------------------------------------------ a trade in progress
    static final class Session {
        final ServerPlayer[] players = new ServerPlayer[2];
        final Offer[] offers = {new Offer(), new Offer()};
        final TradeMenu[] menus = new TradeMenu[2];
        final boolean[] accepted = new boolean[2];
        int countdown;
        int problem;
        boolean closed;
        private boolean committing;

        /** An offer: any change clears both acceptances. */
        final class Offer extends SimpleContainer {
            Offer() {
                super(TradeMenu.OFFER);
            }

            @Override
            public void setChanged() {
                super.setChanged();
                if (!committing && !closed) {
                    reset();
                }
            }
        }

        Session(ServerPlayer a, ServerPlayer b) {
            players[0] = a;
            players[1] = b;
        }

        private ContainerData view(int side) {
            return new ContainerData() {
                @Override
                public int get(int i) {
                    return switch (i) {
                        case 0 -> accepted[side] ? 1 : 0;
                        case 1 -> accepted[1 - side] ? 1 : 0;
                        case 2 -> countdown;
                        case 3 -> problem == 0 ? 0 : problem == side + 1 ? 1 : 2;
                        default -> 0;
                    };
                }

                @Override
                public void set(int i, int v) {
                }

                @Override
                public int getCount() {
                    return TradeMenu.DATA;
                }
            };
        }

        void open() {
            for (int side = 0; side < 2; side++) {
                final int sd = side;
                ServerPlayer p = players[side];
                String partner = players[1 - side].getName().getString();
                ((net.minecraftforge.common.extensions.IForgeServerPlayer) p).openMenu(new SimpleMenuProvider((id, inv, pl) -> {
                    TradeMenu m = new TradeMenu(id, inv, offers[sd], offers[1 - sd], view(sd), this, sd, partner);
                    menus[sd] = m;
                    return m;
                }, Component.translatable("gui.brasshaven.trade.title", partner)), buf -> buf.writeUtf(partner, 32));
            }
            if (menus[0] == null || menus[1] == null || players[0].containerMenu != menus[0] || players[1].containerMenu != menus[1]) {
                cancel("message.brasshaven.trade.cancel_closed");
            }
        }

        boolean valid(int side) {
            if (closed) {
                return false;
            }
            ServerPlayer a = players[side];
            ServerPlayer b = players[1 - side];
            return a.isAlive() && b.isAlive() && !b.hasDisconnected() && a.level() == b.level()
                    && a.distanceTo(b) <= Social.config().tradeDistance.get() + 2;
        }

        void reset() {
            boolean was = accepted[0] || accepted[1] || countdown > 0;
            accepted[0] = false;
            accepted[1] = false;
            countdown = 0;
            if (was) {
                for (ServerPlayer p : players) {
                    Social.ding(p, SoundEvents.NOTE_BLOCK_BASS, 0.8F);
                }
            }
        }

        void button(ServerPlayer player, int side, int id) {
            if (closed || players[side] != player) {
                return;
            }
            if (id == TradeMenu.BUTTON_CANCEL) {
                cancel("message.brasshaven.trade.cancel_closed");
                return;
            }
            if (id != TradeMenu.BUTTON_ACCEPT) {
                return;
            }
            if (accepted[side]) {
                // taking the acceptance back stops the countdown for both
                reset();
                return;
            }
            accepted[side] = true;
            problem = 0;
            if (accepted[0] && accepted[1]) {
                countdown = COUNTDOWN;
            }
            for (ServerPlayer p : players) {
                Social.ding(p, SoundEvents.NOTE_BLOCK_PLING, accepted[0] && accepted[1] ? 1.6F : 1.2F);
            }
        }

        void tick() {
            if (closed) {
                return;
            }
            for (int side = 0; side < 2; side++) {
                ServerPlayer p = players[side];
                if (p.hasDisconnected() || p.isRemoved() || p.containerMenu != menus[side]) {
                    cancel("message.brasshaven.trade.cancel_closed");
                    return;
                }
                if (!valid(side)) {
                    cancel("message.brasshaven.trade.cancel_far");
                    return;
                }
            }
            if (countdown > 0 && accepted[0] && accepted[1]) {
                countdown--;
                if (countdown % 20 == 0 && countdown > 0) {
                    for (ServerPlayer p : players) {
                        Social.ding(p, SoundEvents.NOTE_BLOCK_HAT, 1.5F);
                    }
                }
                if (countdown == 0) {
                    commit();
                }
            }
        }

        /** Both accepted and the countdown ran out: swap everything in this tick, or nothing. */
        private void commit() {
            List<ItemStack> toB = contents(offers[0]);
            List<ItemStack> toA = contents(offers[1]);
            if (toB.isEmpty() && toA.isEmpty()) {
                reset();
                return;
            }
            if (!fits(mainSlots(players[0]), toA)) {
                problem = 1;
                reset();
                Social.fail(players[0], "message.brasshaven.trade.no_room_you");
                Social.fail(players[1], "message.brasshaven.trade.no_room_them", players[0].getName());
                return;
            }
            if (!fits(mainSlots(players[1]), toB)) {
                problem = 2;
                reset();
                Social.fail(players[1], "message.brasshaven.trade.no_room_you");
                Social.fail(players[0], "message.brasshaven.trade.no_room_them", players[1].getName());
                return;
            }
            committing = true;
            closed = true;
            offers[0].clearContent();
            offers[1].clearContent();
            committing = false;
            Social.giveOrMail(players[0], toA, "returned");
            Social.giveOrMail(players[1], toB, "returned");
            com.brasshaven.Brasshaven.LOGGER.info("Trade: {} gave {} / {} gave {}", players[0].getName().getString(), toB,
                    players[1].getName().getString(), toA);
            for (int side = 0; side < 2; side++) {
                ServerPlayer p = players[side];
                if (p.containerMenu == menus[side]) {
                    p.closeContainer();
                }
                p.sendSystemMessage(Component.translatable("message.brasshaven.trade.done", players[1 - side].getName())
                        .withStyle(ChatFormatting.GREEN));
                Social.ding(p, SoundEvents.PLAYER_LEVELUP, 1.4F);
            }
        }

        /** The screen of one side was closed (by the player, or by the server). */
        void menuClosed(int side) {
            if (!closed) {
                cancel("message.brasshaven.trade.cancel_closed");
            }
        }

        void cancel(String why) {
            if (closed) {
                return;
            }
            closed = true;
            committing = true;
            List<ItemStack> backA = contents(offers[0]);
            List<ItemStack> backB = contents(offers[1]);
            offers[0].clearContent();
            offers[1].clearContent();
            committing = false;
            Social.giveOrMail(players[0], backA, "returned");
            Social.giveOrMail(players[1], backB, "returned");
            for (int side = 0; side < 2; side++) {
                ServerPlayer p = players[side];
                if (!p.hasDisconnected() && p.containerMenu == menus[side]) {
                    p.closeContainer();
                }
                if (!p.hasDisconnected()) {
                    p.sendSystemMessage(Component.translatable(why, players[1 - side].getName()).withStyle(ChatFormatting.RED));
                }
            }
        }
    }
}
