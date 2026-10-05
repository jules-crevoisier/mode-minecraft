package com.wayfarers.social;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.event.RegisterCommandsEvent;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/**
 * Commands of the multiplayer features, under /wayfarers (merged into the mod's command) plus /cc for the company
 * chat. They go through the same checked paths as the screens. The chat buttons of requests run
 * {@code /wayfarers social accept|decline <kind> <player>}.
 */
final class SocialCommand {
    private SocialCommand() {}

    static void register(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> d = event.getDispatcher();
        d.register(Commands.literal("wayfarers")
                .then(company())
                .then(Commands.literal("trade").then(Commands.argument("player", EntityArgument.player())
                        .executes(ctx -> {
                            Trade.request(ctx.getSource().getPlayerOrException(), EntityArgument.getPlayer(ctx, "player"));
                            return 1;
                        })))
                .then(Commands.literal("duel").then(Commands.argument("player", EntityArgument.player())
                        .executes(ctx -> {
                            Duels.challenge(ctx.getSource().getPlayerOrException(), EntityArgument.getPlayer(ctx, "player"));
                            return 1;
                        })))
                .then(Commands.literal("emote").then(Commands.argument("emote", StringArgumentType.word())
                        .suggests((ctx, b) -> SharedSuggestionProvider.suggest(Arrays.stream(Emotes.Emote.values())
                                .map(e -> e.name().toLowerCase(Locale.ROOT)), b))
                        .executes(ctx -> {
                            String name = StringArgumentType.getString(ctx, "emote").toUpperCase(Locale.ROOT);
                            for (Emotes.Emote e : Emotes.Emote.values()) {
                                if (e.name().equals(name)) {
                                    Emotes.play(ctx.getSource().getPlayerOrException(), e.ordinal());
                                    return 1;
                                }
                            }
                            return 0;
                        })))
                .then(Commands.literal("social")
                        .then(answer("accept", true))
                        .then(answer("decline", false))
                        .then(Commands.literal("selftest").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(SocialSelfTest::run))
                        .then(Commands.literal("status").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(SocialCommand::status))
                        .then(Commands.literal("demo").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(SocialCommand::demo))));
        d.register(Commands.literal("cc").then(Commands.argument("message", StringArgumentType.greedyString())
                .executes(ctx -> {
                    Companies.say(ctx.getSource().getPlayerOrException(), StringArgumentType.getString(ctx, "message"));
                    return 1;
                })));
    }

    private static LiteralArgumentBuilder<CommandSourceStack> company() {
        return Commands.literal("company")
                .then(Commands.literal("create").executes(ctx -> {
                    Companies.create(ctx.getSource().getPlayerOrException(), "");
                    return 1;
                }).then(Commands.argument("name", StringArgumentType.greedyString()).executes(ctx -> {
                    Companies.create(ctx.getSource().getPlayerOrException(), StringArgumentType.getString(ctx, "name"));
                    return 1;
                })))
                .then(Commands.literal("invite").then(Commands.argument("player", EntityArgument.player()).executes(ctx -> {
                    Companies.invite(ctx.getSource().getPlayerOrException(), EntityArgument.getPlayer(ctx, "player"));
                    return 1;
                })))
                .then(Commands.literal("leave").executes(ctx -> {
                    Companies.leave(ctx.getSource().getPlayerOrException());
                    return 1;
                }))
                .then(Commands.literal("kick").then(Commands.argument("name", StringArgumentType.word()).executes(ctx -> {
                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                    Companies.kick(p, member(p, StringArgumentType.getString(ctx, "name")));
                    return 1;
                })))
                .then(Commands.literal("promote").then(Commands.argument("name", StringArgumentType.word()).executes(ctx -> {
                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                    Companies.promote(p, member(p, StringArgumentType.getString(ctx, "name")));
                    return 1;
                })))
                .then(Commands.literal("rename").then(Commands.argument("name", StringArgumentType.greedyString()).executes(ctx -> {
                    action(ctx, SocialNet.CompanyAction.Action.RENAME, StringArgumentType.getString(ctx, "name"));
                    return 1;
                })))
                .then(Commands.literal("friendlyfire").executes(ctx -> action(ctx, SocialNet.CompanyAction.Action.FRIENDLY_FIRE, "")))
                .then(Commands.literal("sharexp").executes(ctx -> action(ctx, SocialNet.CompanyAction.Action.SHARE_XP, "")))
                .then(Commands.literal("chat").executes(ctx -> action(ctx, SocialNet.CompanyAction.Action.CHAT, "")))
                .then(Commands.literal("join").then(Commands.argument("player", EntityArgument.player()).executes(ctx -> {
                    Companies.askJoin(ctx.getSource().getPlayerOrException(), EntityArgument.getPlayer(ctx, "player").getUUID());
                    return 1;
                })));
    }

    private static int action(CommandContext<CommandSourceStack> ctx, SocialNet.CompanyAction.Action a, String arg)
            throws CommandSyntaxException {
        Companies.handle(ctx.getSource().getPlayerOrException(), new SocialNet.CompanyAction(a, arg));
        return 1;
    }

    private static UUID member(ServerPlayer p, String name) {
        SocialData.Company c = Companies.of(p);
        if (c != null) {
            for (SocialData.Member m : c.members.values()) {
                if (m.name().equalsIgnoreCase(name)) {
                    return m.id();
                }
            }
        }
        return null;
    }

    private static LiteralArgumentBuilder<CommandSourceStack> answer(String word, boolean yes) {
        return Commands.literal(word).then(Commands.argument("kind", StringArgumentType.word())
                .suggests((ctx, b) -> SharedSuggestionProvider.suggest(Arrays.stream(Social.RequestType.values())
                        .map(t -> t.name().toLowerCase(Locale.ROOT)), b))
                .then(Commands.argument("player", StringArgumentType.word()).executes(ctx -> {
                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                    Social.RequestType type;
                    try {
                        type = Social.RequestType.valueOf(StringArgumentType.getString(ctx, "kind").toUpperCase(Locale.ROOT));
                    } catch (IllegalArgumentException e) {
                        return 0;
                    }
                    Social.Request req = Social.take(p, type, StringArgumentType.getString(ctx, "player"));
                    if (!yes) {
                        if (req != null) {
                            ServerPlayer from = Social.online(p.level().getServer(), req.from());
                            if (from != null) {
                                Social.fail(from, "message.wayfarers.social.declined", p.getName());
                            }
                        }
                        if (type == Social.RequestType.INVITE) {
                            Companies.sync(p);
                        }
                        return 1;
                    }
                    switch (type) {
                        case TRADE -> Trade.accept(p, req);
                        case DUEL -> Duels.accept(p, req);
                        case INVITE -> Companies.acceptRequest(p, req);
                        case JOIN -> Companies.acceptJoin(p, req);
                    }
                    return 1;
                })));
    }

    /** Two demo wayfarers ("Ada" and "Brunel", never online). */
    static final UUID ADA = UUID.fromString("0000ada0-0000-4000-8000-000000000001");
    static final UUID BRUNEL = UUID.fromString("0000b0e1-0000-4000-8000-000000000002");

    private static ItemStack stack(net.minecraft.world.item.Item item, int n) {
        return new ItemStack(item, n);
    }

    /**
     * Operators (showcase, CI screenshots): fills the caller's company, inbox and the contract board with examples
     * from two demo wayfarers, so every screen has something to show on a server with one player.
     */
    private static int demo(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer p = ctx.getSource().getPlayerOrException();
        SocialData data = SocialData.get(ctx.getSource().getServer());
        data.rememberName(ADA, "Ada");
        data.rememberName(BRUNEL, "Brunel");
        SocialData.Company c = data.companyOf(p.getUUID());
        if (c == null) {
            c = data.newCompany("Brass Owls", p.getUUID(), p.getName().getString());
        }
        if (c.members.size() < Social.config().companyMaxSize.get() && data.companyOf(ADA) == null) {
            c.members.put(ADA, new SocialData.Member(ADA, "Ada"));
        }
        data.changed();
        long now = System.currentTimeMillis();
        data.deliver(p.getUUID(), new SocialData.Parcel(data.nextId(), BRUNEL, "Brunel",
                "The Contract Board wants iron for the airship hull. Pay is good!", List.of(), now - 3_600_000L, "letter"));
        data.deliver(p.getUUID(), new SocialData.Parcel(data.nextId(), Post.SYSTEM, "", "Brunel",
                List.of(stack(Items.OAK_LOG, 64)), now - 600_000L, "delivery"));
        data.deliver(p.getUUID(), new SocialData.Parcel(data.nextId(), ADA, "Ada",
                "Meet me at the Sky Harbour at dusk. I found the clockwork map: bring a compass!",
                List.of(stack(Items.CLOCK, 1), stack(Items.COPPER_INGOT, 24)), now - 120_000L, "letter"));
        long expires = now + Social.config().contractDays.get() * 86_400_000L;
        data.addContract(data.newContract(ADA, "Ada", stack(Items.IRON_INGOT, 1), 32, "for the airship hull",
                List.of(stack(Items.DIAMOND, 3)), now, expires));
        data.addContract(data.newContract(BRUNEL, "Brunel", stack(Items.GLOWSTONE_DUST, 1), 48, "lamps for the Undercity",
                List.of(stack(Items.EMERALD, 12)), now - 3_600_000L, expires - 86_400_000L));
        data.addContract(data.newContract(p.getUUID(), p.getName().getString(), stack(Items.OAK_LOG, 1), 128, "",
                List.of(stack(Items.GOLD_INGOT, 8)), now - 60_000L, expires));
        Companies.sync(ctx.getSource().getServer(), c);
        ctx.getSource().sendSuccess(() -> Component.literal("Social demo ready: company, 3 parcels, 3 contracts"), false);
        return 1;
    }

    private static int status(CommandContext<CommandSourceStack> ctx) {
        SocialData data = SocialData.get(ctx.getSource().getServer());
        int parcels = 0;
        for (String n : data.knownNames()) {
            UUID id = data.byName(n);
            if (id != null) {
                parcels += data.inbox(id).size();
            }
        }
        int fParcels = parcels;
        ctx.getSource().sendSuccess(() -> Component.literal("Social: " + data.knownNames().size() + " players known, "
                + data.companies().size() + " companies, " + fParcels + " parcels waiting, " + data.contracts().size()
                + " open contracts"), false);
        return 1;
    }
}
