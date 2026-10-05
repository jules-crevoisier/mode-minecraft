package com.brasshaven.social;

import com.brasshaven.Brasshaven;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.network.CustomPayloadEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.network.Channel;
import net.minecraftforge.network.ChannelBuilder;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.SimpleChannel;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Function;

/**
 * The multiplayer features' own channel (brasshaven:social), apart from the main one so the two evolve separately.
 *
 * <p>Clients never send items, counts of items they hold, positions or names they claim to be: only what they
 * want to do (an action, an id they were shown, a typed text). Every serverbound message is checked against a
 * per-player packet budget, the feature switch, and the open menu or the real world state before anything happens;
 * texts are read with a hard length cap. Clientbound lists are capped too.
 */
public final class SocialNet {
    private static final int VERSION = 1;
    /** Longest list a client accepts from the server (inbox, board, members...). */
    private static final int MAX_LIST = 512;

    public static final SimpleChannel CHANNEL = ChannelBuilder.named(Brasshaven.id("social"))
            .networkProtocolVersion(VERSION)
            .clientAcceptedVersions(Channel.VersionTest.exact(VERSION))
            .serverAcceptedVersions(Channel.VersionTest.exact(VERSION))
            .simpleChannel()
            .play()
                .clientbound()
                    .addMain(Hello.class, Hello.STREAM_CODEC, Hello::handle)
                    .addMain(CompanyState.class, CompanyState.STREAM_CODEC, CompanyState::handle)
                    .addMain(CompanyStatus.class, CompanyStatus.STREAM_CODEC, CompanyStatus::handle)
                    .addMain(PlayerCard.class, PlayerCard.STREAM_CODEC, PlayerCard::handle)
                    .addMain(Inbox.class, Inbox.STREAM_CODEC, Inbox::handle)
                    .addMain(Board.class, Board.STREAM_CODEC, Board::handle)
                .serverbound()
                    .addMain(CompanyAction.class, CompanyAction.STREAM_CODEC, CompanyAction::handle)
                    .addMain(PlayerAction.class, PlayerAction.STREAM_CODEC, PlayerAction::handle)
                    .addMain(EmoteAction.class, EmoteAction.STREAM_CODEC, EmoteAction::handle)
                    .addMain(PostAction.class, PostAction.STREAM_CODEC, PostAction::handle)
                    .addMain(BoardAction.class, BoardAction.STREAM_CODEC, BoardAction::handle)
            .build();

    private SocialNet() {}

    /** Touching the class builds the channel; must happen during mod construction. */
    public static void init() {
        Brasshaven.LOGGER.debug("Network channel {} v{}", CHANNEL.getName(), VERSION);
    }

    public static void toPlayer(ServerPlayer player, Object msg) {
        CHANNEL.send(msg, PacketDistributor.PLAYER.with(player));
    }

    public static void toServer(Object msg) {
        CHANNEL.send(msg, PacketDistributor.SERVER.noArg());
    }

    private static boolean client() {
        return FMLEnvironment.dist == Dist.CLIENT;
    }

    // ------------------------------------------------------------------ list helpers
    private static <T> void writeList(RegistryFriendlyByteBuf buf, List<T> list, BiConsumer<RegistryFriendlyByteBuf, T> w) {
        int n = Math.min(list.size(), MAX_LIST);
        buf.writeVarInt(n);
        for (int i = 0; i < n; i++) {
            w.accept(buf, list.get(i));
        }
    }

    private static <T> List<T> readList(RegistryFriendlyByteBuf buf, Function<RegistryFriendlyByteBuf, T> r) {
        int n = buf.readVarInt();
        if (n < 0 || n > MAX_LIST) {
            throw new IllegalArgumentException("list too long: " + n);
        }
        List<T> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add(r.apply(buf));
        }
        return out;
    }

    private static void writeItems(RegistryFriendlyByteBuf buf, List<ItemStack> items) {
        writeList(buf, items, (b, s) -> ItemStack.OPTIONAL_STREAM_CODEC.encode(b, s));
    }

    private static List<ItemStack> readItems(RegistryFriendlyByteBuf buf) {
        return readList(buf, ItemStack.OPTIONAL_STREAM_CODEC::decode);
    }

    // ================================================================== clientbound

    /**
     * On login: which features the server runs and their costs, so the client greys out what is off.
     * {@code flags}: bit 0 company, 1 trade, 2 post, 3 contracts, 4 emotes, 5 duels.
     */
    public record Hello(int flags, ItemStack postage, int postageBase, int postagePerStack, int joinCost, int maxCompany,
                        int contractDays) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Hello> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeVarInt(m.flags);
            ItemStack.OPTIONAL_STREAM_CODEC.encode(b, m.postage);
            b.writeVarInt(m.postageBase);
            b.writeVarInt(m.postagePerStack);
            b.writeVarInt(m.joinCost);
            b.writeVarInt(m.maxCompany);
            b.writeVarInt(m.contractDays);
        }, b -> new Hello(b.readVarInt(), ItemStack.OPTIONAL_STREAM_CODEC.decode(b), b.readVarInt(), b.readVarInt(),
                b.readVarInt(), b.readVarInt(), b.readVarInt()));

        public boolean on(int bit) {
            return (flags & (1 << bit)) != 0;
        }

        static void handle(Hello msg, CustomPayloadEvent.Context ctx) {
            if (client()) {
                com.brasshaven.client.social.ClientSocial.hello(msg);
            }
        }
    }

    public record MemberInfo(UUID id, String name, boolean online) {}

    /** A pending invitation to a company. */
    public record Invite(int companyId, String companyName, String from) {}

    /** The player's company (or none) and the invitations waiting for them. Sent on every change. */
    public record CompanyState(int id, String name, UUID leader, boolean friendlyFire, boolean shareXp, boolean chat,
                               List<MemberInfo> members, List<Invite> invites) {
        public static final StreamCodec<RegistryFriendlyByteBuf, CompanyState> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeVarInt(m.id);
            b.writeUtf(m.name, 64);
            b.writeUUID(m.leader);
            b.writeBoolean(m.friendlyFire);
            b.writeBoolean(m.shareXp);
            b.writeBoolean(m.chat);
            writeList(b, m.members, (bb, e) -> {
                bb.writeUUID(e.id);
                bb.writeUtf(e.name, 32);
                bb.writeBoolean(e.online);
            });
            writeList(b, m.invites, (bb, e) -> {
                bb.writeVarInt(e.companyId);
                bb.writeUtf(e.companyName, 64);
                bb.writeUtf(e.from, 32);
            });
        }, b -> new CompanyState(b.readVarInt(), b.readUtf(64), b.readUUID(), b.readBoolean(), b.readBoolean(), b.readBoolean(),
                readList(b, bb -> new MemberInfo(bb.readUUID(), bb.readUtf(32), bb.readBoolean())),
                readList(b, bb -> new Invite(bb.readVarInt(), bb.readUtf(64), bb.readUtf(32)))));

        public static final UUID NOBODY = new UUID(0, 0);

        public boolean inCompany() {
            return id > 0;
        }

        static void handle(CompanyState msg, CustomPayloadEvent.Context ctx) {
            if (client()) {
                com.brasshaven.client.social.ClientSocial.company(msg);
            }
        }
    }

    /** Health and place of one online companion (the HUD and the maps). */
    public record Status(UUID id, float health, float maxHealth, String dim, int x, int y, int z) {}

    /** Online companions' health and positions, at most once a second and only when something changed. */
    public record CompanyStatus(List<Status> members) {
        public static final StreamCodec<RegistryFriendlyByteBuf, CompanyStatus> STREAM_CODEC = StreamCodec.ofMember(
                (m, b) -> writeList(b, m.members, (bb, s) -> {
                    bb.writeUUID(s.id);
                    bb.writeFloat(s.health);
                    bb.writeFloat(s.maxHealth);
                    bb.writeUtf(s.dim, 128);
                    bb.writeVarInt(s.x);
                    bb.writeVarInt(s.y);
                    bb.writeVarInt(s.z);
                }),
                b -> new CompanyStatus(readList(b, bb -> new Status(bb.readUUID(), bb.readFloat(), bb.readFloat(), bb.readUtf(128),
                        bb.readVarInt(), bb.readVarInt(), bb.readVarInt()))));

        static void handle(CompanyStatus msg, CustomPayloadEvent.Context ctx) {
            if (client()) {
                com.brasshaven.client.social.ClientSocial.status(msg);
            }
        }
    }

    /**
     * Opens the card of another player (sneak + right-click on them, or the key): who they are and what you can do
     * together. {@code relation}: 0 none, 1 same company, 2 they can be invited.
     */
    public record PlayerCard(UUID id, String name, String company, int wins, int losses, int draws, int relation) {
        public static final StreamCodec<RegistryFriendlyByteBuf, PlayerCard> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeUUID(m.id);
            b.writeUtf(m.name, 32);
            b.writeUtf(m.company, 64);
            b.writeVarInt(m.wins);
            b.writeVarInt(m.losses);
            b.writeVarInt(m.draws);
            b.writeVarInt(m.relation);
        }, b -> new PlayerCard(b.readUUID(), b.readUtf(32), b.readUtf(64), b.readVarInt(), b.readVarInt(), b.readVarInt(),
                b.readVarInt()));

        static void handle(PlayerCard msg, CustomPayloadEvent.Context ctx) {
            if (client()) {
                com.brasshaven.client.social.ClientSocial.card(msg);
            }
        }
    }

    public record ParcelView(long id, String from, String text, String kind, long sentAt, List<ItemStack> items) {}

    /** The inbox shown by an open Pneumatic Post, plus the names it can send to (for completion). */
    public record Inbox(int containerId, List<ParcelView> parcels, List<String> names) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Inbox> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeVarInt(m.containerId);
            writeList(b, m.parcels, (bb, p) -> {
                bb.writeLong(p.id);
                bb.writeUtf(p.from, 32);
                bb.writeUtf(p.text, Post.MAX_TEXT + 32);
                bb.writeUtf(p.kind, 16);
                bb.writeLong(p.sentAt);
                writeItems(bb, p.items);
            });
            writeList(b, m.names, (bb, s) -> bb.writeUtf(s, 32));
        }, b -> new Inbox(b.readVarInt(),
                readList(b, bb -> new ParcelView(bb.readLong(), bb.readUtf(32), bb.readUtf(Post.MAX_TEXT + 32), bb.readUtf(16),
                        bb.readLong(), readItems(bb))),
                readList(b, bb -> bb.readUtf(32))));

        static void handle(Inbox msg, CustomPayloadEvent.Context ctx) {
            if (client()) {
                com.brasshaven.client.social.ClientSocial.inbox(msg);
            }
        }
    }

    public record ContractView(long id, String poster, boolean mine, ItemStack wanted, int amount, String note,
                               List<ItemStack> reward, long expiresAt) {}

    /** The open contracts shown by a Contract Board. */
    public record Board(int containerId, List<ContractView> contracts, int mine) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Board> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeVarInt(m.containerId);
            writeList(b, m.contracts, (bb, c) -> {
                bb.writeLong(c.id);
                bb.writeUtf(c.poster, 32);
                bb.writeBoolean(c.mine);
                ItemStack.OPTIONAL_STREAM_CODEC.encode(bb, c.wanted);
                bb.writeVarInt(c.amount);
                bb.writeUtf(c.note, Contracts.MAX_NOTE);
                writeItems(bb, c.reward);
                bb.writeLong(c.expiresAt);
            });
            b.writeVarInt(m.mine);
        }, b -> new Board(b.readVarInt(),
                readList(b, bb -> new ContractView(bb.readLong(), bb.readUtf(32), bb.readBoolean(),
                        ItemStack.OPTIONAL_STREAM_CODEC.decode(bb), bb.readVarInt(), bb.readUtf(Contracts.MAX_NOTE),
                        readItems(bb), bb.readLong())),
                b.readVarInt()));

        static void handle(Board msg, CustomPayloadEvent.Context ctx) {
            if (client()) {
                com.brasshaven.client.social.ClientSocial.board(msg);
            }
        }
    }

    // ================================================================== serverbound

    /** Company screen and commands. {@code arg}: a name, a company id or a member's UUID depending on the action. */
    public record CompanyAction(Action action, String arg) {
        public enum Action { CREATE, INVITE, ACCEPT, DECLINE, LEAVE, KICK, PROMOTE, FRIENDLY_FIRE, SHARE_XP, CHAT, JOIN, RENAME, REFRESH }

        public static final StreamCodec<RegistryFriendlyByteBuf, CompanyAction> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeEnum(m.action);
            b.writeUtf(m.arg, 64);
        }, b -> new CompanyAction(b.readEnum(Action.class), b.readUtf(64)));

        static void handle(CompanyAction msg, CustomPayloadEvent.Context ctx) {
            ServerPlayer player = ctx.getSender();
            if (player != null && Social.packetBudget(player)) {
                Companies.handle(player, msg);
            }
        }
    }

    /**
     * Something done to another player: open their card (by entity id, for the key; the server checks they are close
     * and in sight), or ask them to trade, duel or join your company (by UUID, from their card).
     */
    public record PlayerAction(Action action, int entityId, UUID target) {
        public enum Action { CARD, TRADE, DUEL, INVITE }

        public static final StreamCodec<RegistryFriendlyByteBuf, PlayerAction> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeEnum(m.action);
            b.writeVarInt(m.entityId);
            b.writeUUID(m.target);
        }, b -> new PlayerAction(b.readEnum(Action.class), b.readVarInt(), b.readUUID()));

        static void handle(PlayerAction msg, CustomPayloadEvent.Context ctx) {
            ServerPlayer player = ctx.getSender();
            if (player != null && Social.packetBudget(player)) {
                Social.playerAction(player, msg);
            }
        }
    }

    /** Plays an emote (index into {@link Emotes.Emote}). */
    public record EmoteAction(int emote) {
        public static final StreamCodec<RegistryFriendlyByteBuf, EmoteAction> STREAM_CODEC = StreamCodec.ofMember(
                (m, b) -> b.writeVarInt(m.emote), b -> new EmoteAction(b.readVarInt()));

        static void handle(EmoteAction msg, CustomPayloadEvent.Context ctx) {
            ServerPlayer player = ctx.getSender();
            if (player != null && Social.packetBudget(player)) {
                Emotes.play(player, msg.emote);
            }
        }
    }

    /** Pneumatic Post screen: send the parcel being written, take a parcel's items, or throw away a read letter. */
    public record PostAction(int containerId, Action action, long parcel, String recipient, String text) {
        public enum Action { REFRESH, SEND, COLLECT, DISCARD }

        public static final StreamCodec<RegistryFriendlyByteBuf, PostAction> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeVarInt(m.containerId);
            b.writeEnum(m.action);
            b.writeLong(m.parcel);
            b.writeUtf(m.recipient, 32);
            b.writeUtf(m.text, Post.MAX_TEXT);
        }, b -> new PostAction(b.readVarInt(), b.readEnum(Action.class), b.readLong(), b.readUtf(32), b.readUtf(Post.MAX_TEXT)));

        static void handle(PostAction msg, CustomPayloadEvent.Context ctx) {
            ServerPlayer player = ctx.getSender();
            if (player != null && Social.packetBudget(player)) {
                Post.handle(player, msg);
            }
        }
    }

    /** Contract Board screen: post the contract being written, deliver to one, or cancel one of yours. */
    public record BoardAction(int containerId, Action action, long contract, int amount, String note) {
        public enum Action { REFRESH, POST, DELIVER, CANCEL }

        public static final StreamCodec<RegistryFriendlyByteBuf, BoardAction> STREAM_CODEC = StreamCodec.ofMember((m, b) -> {
            b.writeVarInt(m.containerId);
            b.writeEnum(m.action);
            b.writeLong(m.contract);
            b.writeVarInt(m.amount);
            b.writeUtf(m.note, Contracts.MAX_NOTE);
        }, b -> new BoardAction(b.readVarInt(), b.readEnum(Action.class), b.readLong(), b.readVarInt(), b.readUtf(Contracts.MAX_NOTE)));

        static void handle(BoardAction msg, CustomPayloadEvent.Context ctx) {
            ServerPlayer player = ctx.getSender();
            if (player != null && Social.packetBudget(player)) {
                Contracts.handle(player, msg);
            }
        }
    }
}
