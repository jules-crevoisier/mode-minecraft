package com.brasshaven.social;

import com.brasshaven.config.SocialConfig;
import com.brasshaven.config.BrasshavenConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Predicate;

/**
 * The multiplayer features of Brasshaven: the Company (parties), secure trade, the Pneumatic Post, guild contracts,
 * emotes and duels. This class wires them up and holds what they share: the feature switches, the per-player packet
 * budget and cooldowns, pending requests ("Alice wants to trade: [Accept] [Decline]"), text cleaning, and
 * {@link #giveOrMail}, the one way items go back to a player (inventory first, the rest by post: never dropped,
 * never lost when the player is offline or dead).
 */
public final class Social {
    public enum Feature { COMPANY, TRADE, POST, CONTRACTS, EMOTES, DUELS }

    /** Kinds of requests one player sends another, answered with /brasshaven social accept|decline. */
    public enum RequestType { TRADE, DUEL, INVITE, JOIN }

    /** A pending request; {@code data}: the company id of an invitation. */
    public record Request(RequestType type, UUID from, String fromName, UUID to, long expires, int data) {}

    private static final int REQUEST_TICKS = 60 * 20;
    private static final int MAX_OUTGOING = 6;
    /** Serverbound social packets one player may send per second before the rest are ignored. */
    private static final int PACKETS_PER_SECOND = 30;

    private static final List<Request> REQUESTS = new ArrayList<>();
    private static final Map<UUID, int[]> BUDGET = new HashMap<>();
    private static final Map<UUID, Map<String, Long>> COOLDOWNS = new HashMap<>();

    private Social() {}

    public static void register() {
        SocialNet.init();
        Companies.register();
        Trade.register();
        Duels.register();
        Emotes.register();
        Post.register();
        Contracts.register();
        net.minecraftforge.event.RegisterCommandsEvent.BUS.addListener(SocialCommand::register);
        ServerStoppingEvent.BUS.addListener(e -> {
            Trade.cancelAll();
            Duels.stopAll();
            REQUESTS.clear();
            BUDGET.clear();
            COOLDOWNS.clear();
        });
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                onLogin(p);
            }
        });
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                REQUESTS.removeIf(r -> r.from().equals(p.getUUID()) || r.to().equals(p.getUUID()));
                BUDGET.remove(p.getUUID());
                COOLDOWNS.remove(p.getUUID());
            }
        });
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> {
            if (e.server().getTickCount() % 20 == 0) {
                long now = e.server().getTickCount();
                REQUESTS.removeIf(r -> r.expires() < now);
            }
        });
        // sneak + right-click another player with an empty hand: their card (trade, duel, invite)
        PlayerInteractEvent.EntityInteractSpecific.BUS.addListener((Predicate<PlayerInteractEvent.EntityInteractSpecific>) e -> {
            if (e.getEntity() instanceof ServerPlayer player && e.getTarget() instanceof ServerPlayer target
                    && e.getHand() == InteractionHand.MAIN_HAND && player.isShiftKeyDown()
                    && player.getMainHandItem().isEmpty() && !target.isSpectator()) {
                openCard(player, target);
                return true;
            }
            return false;
        });
    }

    public static SocialConfig config() {
        return BrasshavenConfig.SOCIAL;
    }

    public static boolean enabled(Feature f) {
        SocialConfig c = config();
        return switch (f) {
            case COMPANY -> c.companyEnabled.get();
            case TRADE -> c.tradeEnabled.get();
            case POST -> c.postEnabled.get();
            case CONTRACTS -> c.contractsEnabled.get();
            case EMOTES -> c.emotesEnabled.get();
            case DUELS -> c.duelsEnabled.get();
        };
    }

    /** Checks the switch; tells the player when it is off. */
    public static boolean require(ServerPlayer player, Feature f) {
        if (enabled(f)) {
            return true;
        }
        fail(player, "message.brasshaven.social.disabled");
        return false;
    }

    // ------------------------------------------------------------------ login
    private static void onLogin(ServerPlayer player) {
        SocialData data = SocialData.get(player.level().getServer());
        data.rememberName(player.getUUID(), player.getName().getString());
        SocialNet.toPlayer(player, hello());
        Companies.onLogin(player);
        Post.onLogin(player);
    }

    static SocialNet.Hello hello() {
        int flags = 0;
        for (Feature f : Feature.values()) {
            if (enabled(f)) {
                flags |= 1 << f.ordinal();
            }
        }
        SocialConfig c = config();
        return new SocialNet.Hello(flags, postageItem().map(ItemStack::new).orElse(ItemStack.EMPTY), c.postageBase.get(),
                c.postagePerStack.get(), c.companyJoinCost.get(), c.companyMaxSize.get(), c.contractDays.get());
    }

    /** The postage item of the config, if any (and if it exists). */
    static java.util.Optional<Item> postageItem() {
        String id = config().postageItem.get().strip();
        if (id.isEmpty()) {
            return java.util.Optional.empty();
        }
        Identifier rl = Identifier.tryParse(id);
        if (rl == null) {
            return java.util.Optional.empty();
        }
        return BuiltInRegistries.ITEM.getOptional(rl).filter(i -> i != Items.AIR);
    }

    // ------------------------------------------------------------------ budgets and cooldowns
    /** False once a player sent more than {@link #PACKETS_PER_SECOND} social packets within a second. */
    static boolean packetBudget(ServerPlayer player) {
        long second = player.level().getServer().getTickCount() / 20;
        int[] b = BUDGET.computeIfAbsent(player.getUUID(), k -> new int[2]);
        if (b[0] != (int) second) {
            b[0] = (int) second;
            b[1] = 0;
        }
        return ++b[1] <= PACKETS_PER_SECOND;
    }

    /** True (and starts the cooldown) when {@code key} is ready for this player; otherwise false. */
    static boolean cooldown(ServerPlayer player, String key, int ticks) {
        long now = player.level().getServer().getTickCount();
        Map<String, Long> map = COOLDOWNS.computeIfAbsent(player.getUUID(), k -> new HashMap<>());
        Long until = map.get(key);
        if (until != null && until > now) {
            return false;
        }
        map.put(key, now + ticks);
        return true;
    }

    /** Ticks left on a cooldown (0 when ready). */
    static long cooldownLeft(ServerPlayer player, String key) {
        Long until = COOLDOWNS.getOrDefault(player.getUUID(), Map.of()).get(key);
        return until == null ? 0 : Math.max(0, until - player.level().getServer().getTickCount());
    }

    // ------------------------------------------------------------------ requests
    /**
     * Stores a request from {@code from} to {@code to} (replacing the same one), and shows {@code to} the prompt with
     * [Accept] [Decline]. False when {@code from} already has too many requests waiting.
     */
    static boolean request(ServerPlayer from, ServerPlayer to, RequestType type, int data, Component prompt) {
        long now = from.level().getServer().getTickCount();
        REQUESTS.removeIf(r -> r.type() == type && r.from().equals(from.getUUID()) && r.to().equals(to.getUUID()));
        if (REQUESTS.stream().filter(r -> r.from().equals(from.getUUID())).count() >= MAX_OUTGOING) {
            fail(from, "message.brasshaven.social.too_many_requests");
            return false;
        }
        String fromName = from.getName().getString();
        REQUESTS.add(new Request(type, from.getUUID(), fromName, to.getUUID(), now + REQUEST_TICKS, data));
        String t = type.name().toLowerCase(java.util.Locale.ROOT);
        to.sendSystemMessage(prompt.copy().withStyle(ChatFormatting.GOLD)
                .append(" ").append(button("message.brasshaven.social.accept", "/brasshaven social accept " + t + " " + fromName,
                        ChatFormatting.GREEN))
                .append(" ").append(button("message.brasshaven.social.decline", "/brasshaven social decline " + t + " " + fromName,
                        ChatFormatting.RED)));
        ding(to, net.minecraft.sounds.SoundEvents.NOTE_BLOCK_BELL, 1.4F);
        return true;
    }

    /** Removes and returns the live request of this type sent to {@code to} by the player named {@code fromName}. */
    static Request take(ServerPlayer to, RequestType type, String fromName) {
        long now = to.level().getServer().getTickCount();
        for (Iterator<Request> it = REQUESTS.iterator(); it.hasNext(); ) {
            Request r = it.next();
            if (r.type() == type && r.to().equals(to.getUUID()) && r.fromName().equalsIgnoreCase(fromName)) {
                it.remove();
                return r.expires() >= now ? r : null;
            }
        }
        return null;
    }

    /** Live requests of a type sent to a player (company invitations in the company screen). */
    static List<Request> requestsTo(UUID to, RequestType type) {
        return REQUESTS.stream().filter(r -> r.type() == type && r.to().equals(to)).toList();
    }

    static void dropRequests(UUID player, RequestType type) {
        REQUESTS.removeIf(r -> r.type() == type && (r.from().equals(player) || r.to().equals(player)));
    }

    // ------------------------------------------------------------------ the player card
    static void openCard(ServerPlayer player, ServerPlayer target) {
        if (target == player || !cooldown(player, "card", 5)) {
            return;
        }
        SocialData data = SocialData.get(player.level().getServer());
        SocialData.Company theirs = data.companyOf(target.getUUID());
        SocialData.Company mine = data.companyOf(player.getUUID());
        int relation = 0;
        if (mine != null && mine == theirs) {
            relation = 1;
        } else if (theirs == null && enabled(Feature.COMPANY)
                && (mine == null || (mine.leader.equals(player.getUUID()) && mine.members.size() < config().companyMaxSize.get()))) {
            relation = 2;
        }
        SocialData.DuelRecord rec = data.duelRecord(target.getUUID());
        SocialNet.toPlayer(player, new SocialNet.PlayerCard(target.getUUID(), target.getName().getString(),
                theirs == null ? "" : theirs.name, rec.wins(), rec.losses(), rec.draws(), relation));
    }

    static void playerAction(ServerPlayer player, SocialNet.PlayerAction msg) {
        MinecraftServer srv = player.level().getServer();
        if (msg.action() == SocialNet.PlayerAction.Action.CARD) {
            Entity e = player.level().getEntity(msg.entityId());
            if (e instanceof ServerPlayer target && target != player && !target.isSpectator()
                    && target.distanceToSqr(player) < 12 * 12 && player.hasLineOfSight(target)) {
                openCard(player, target);
            }
            return;
        }
        ServerPlayer target = srv.getPlayerList().getPlayer(msg.target());
        if (target == null || target == player) {
            fail(player, "message.brasshaven.social.not_online");
            return;
        }
        switch (msg.action()) {
            case TRADE -> Trade.request(player, target);
            case DUEL -> Duels.challenge(player, target);
            case INVITE -> Companies.invite(player, target);
            default -> {
            }
        }
    }

    // ------------------------------------------------------------------ items
    /**
     * Gives items back to a player: into the inventory, and what does not fit (or everything, when they are dead or
     * gone) into their own Pneumatic Post inbox as a parcel of this kind ("returned", "reward", "refund"). Never drops
     * anything in the world.
     */
    static void giveOrMail(ServerPlayer player, List<ItemStack> stacks, String kind) {
        List<ItemStack> rest = new ArrayList<>();
        boolean present = player.isAlive() && !player.hasDisconnected() && !player.isRemoved();
        for (ItemStack s : stacks) {
            if (s.isEmpty()) {
                continue;
            }
            ItemStack copy = s.copy();
            if (present) {
                player.getInventory().add(copy);
            }
            if (!copy.isEmpty()) {
                rest.add(copy);
            }
        }
        if (!rest.isEmpty()) {
            Post.system(player.level().getServer(), player.getUUID(), kind, "", rest);
            if (present) {
                player.sendSystemMessage(Component.translatable("message.brasshaven.social.mailed_back").withStyle(ChatFormatting.GOLD));
            }
        }
        if (present) {
            player.containerMenu.broadcastChanges();
        }
    }

    // ------------------------------------------------------------------ text
    /** One line of player text: no formatting codes or control characters, trimmed, at most {@code max} characters. */
    static String clean(String raw, int max) {
        return cleanText(raw, max, false);
    }

    /** Player text that may keep line breaks (letters). */
    static String cleanText(String raw, int max, boolean newlines) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < raw.length() && sb.length() < max; i++) {
            char c = raw.charAt(i);
            if (c == '§') {
                i++; // drop the formatting code and its letter
            } else if (c == '\n' && newlines) {
                sb.append('\n');
            } else if (c >= ' ' && c != '\u007f') {
                sb.append(c);
            }
        }
        return sb.toString().strip();
    }

    // ------------------------------------------------------------------ messages
    static MutableComponent button(String key, String command, ChatFormatting color) {
        return Component.literal("[").append(Component.translatable(key)).append("]")
                .withStyle(s -> s.withColor(color).withBold(true)
                        .withClickEvent(new ClickEvent.RunCommand(command))
                        .withHoverEvent(new HoverEvent.ShowText(Component.literal(command))));
    }

    static void fail(ServerPlayer player, String key, Object... args) {
        player.sendSystemMessage(Component.translatable(key, args).withStyle(ChatFormatting.RED));
    }

    static void info(ServerPlayer player, String key, Object... args) {
        player.sendSystemMessage(Component.translatable(key, args).withStyle(ChatFormatting.GOLD));
    }

    /** A sound only this player hears. */
    static void ding(ServerPlayer player, net.minecraft.core.Holder<net.minecraft.sounds.SoundEvent> sound, float pitch) {
        player.connection.send(new net.minecraft.network.protocol.game.ClientboundSoundPacket(sound,
                net.minecraft.sounds.SoundSource.PLAYERS, player.getX(), player.getY(), player.getZ(), 0.7F, pitch,
                player.getRandom().nextLong()));
    }

    static void ding(ServerPlayer player, net.minecraft.sounds.SoundEvent sound, float pitch) {
        ding(player, BuiltInRegistries.SOUND_EVENT.wrapAsHolder(sound), pitch);
    }

    static ServerPlayer online(MinecraftServer srv, UUID id) {
        return srv == null ? null : srv.getPlayerList().getPlayer(id);
    }
}
