package com.wayfarers.social;

import com.wayfarers.data.WayfarersData;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.event.ServerChatEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerXpEvent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * The Company: a party of up to {@code company.maxSize} players. The leader invites (inviting with no company founds
 * one), renames, promotes, removes members and sets the two switches: friendly fire (off: companions cannot hurt each
 * other, projectiles and potions included) and shared experience (experience orbs picked up are split evenly with the
 * companions nearby: nothing is created, the picker keeps the remainder). Every member can talk in the company chat
 * (/cc, or a switch that sends normal chat to the company only) and ask a companion to be joined from a waystone:
 * once the companion accepts, the traveller pays the levels and appears beside them.
 *
 * <p>Members see their companions' health and position on the HUD and gold-framed on the maps: one small packet
 * per second at most, only when something changed, only to the company.
 */
public final class Companies {
    public static final int MAX_NAME = 24;
    private static final double WAYSTONE_REACH = 8.0;

    /** Players whose normal chat goes to their company only. */
    private static final Set<UUID> CHAT_MODE = new HashSet<>();
    /** Player -> server tick of the experience orb they just touched (the next XP change of that tick is shared). */
    private static final Map<UUID, Long> PICKUP = new HashMap<>();
    /** Company id -> hash of the last status sent, so an unchanged company sends nothing. */
    private static final Map<Integer, Integer> LAST_STATUS = new HashMap<>();
    private static boolean sharing;

    private Companies() {}

    static void register() {
        LivingAttackEvent.BUS.addListener((Predicate<LivingAttackEvent>) e -> e.getEntity() instanceof ServerPlayer victim
                && blocksFriendlyFire(victim, e.getSource()));
        ServerChatEvent.BUS.addListener((Predicate<ServerChatEvent>) Companies::onChat);
        PlayerXpEvent.PickupXp.BUS.addListener((Consumer<PlayerXpEvent.PickupXp>) e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                PICKUP.put(p.getUUID(), (long) p.level().getServer().getTickCount());
            }
        });
        PlayerXpEvent.XpChange.BUS.addListener((Consumer<PlayerXpEvent.XpChange>) Companies::onXp);
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                PICKUP.remove(p.getUUID());
                SocialData.Company c = SocialData.get(p.level().getServer()).companyOf(p.getUUID());
                if (c != null) {
                    // the others see them go offline (after the player list dropped them)
                    p.level().getServer().execute(() -> sync(p.level().getServer(), c));
                }
            }
        });
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> {
            if (e.server().getTickCount() % 20 == 7 && Social.enabled(Social.Feature.COMPANY)) {
                sendStatus(e.server());
            }
        });
    }

    static void onLogin(ServerPlayer player) {
        MinecraftServer server = player.level().getServer();
        SocialData.Company c = SocialData.get(server).companyOf(player.getUUID());
        if (c != null) {
            // keep the stored name in step with renamed accounts
            c.members.put(player.getUUID(), new SocialData.Member(player.getUUID(), player.getName().getString()));
            SocialData.get(server).changed();
            sync(server, c);
            LAST_STATUS.remove(c.id);
        } else {
            sync(player);
        }
    }

    // ------------------------------------------------------------------ queries
    public static SocialData.Company of(ServerPlayer player) {
        return SocialData.get(player.level().getServer()).companyOf(player.getUUID());
    }

    public static boolean companions(ServerPlayer a, ServerPlayer b) {
        if (a == b) {
            return false;
        }
        SocialData.Company c = of(a);
        return c != null && c.members.containsKey(b.getUUID());
    }

    static Component displayName(SocialData.Company c) {
        return c.name.isEmpty()
                ? Component.translatable("gui.wayfarers.company.default_name",
                SocialData.get(Social.server()).name(c.leader))
                : Component.literal(c.name);
    }

    private static boolean isLeader(SocialData.Company c, ServerPlayer p) {
        return c.leader.equals(p.getUUID());
    }

    // ------------------------------------------------------------------ actions
    static void handle(ServerPlayer player, SocialNet.CompanyAction msg) {
        if (msg.action() == SocialNet.CompanyAction.Action.REFRESH) {
            sync(player);
            return;
        }
        if (!Social.require(player, Social.Feature.COMPANY)) {
            return;
        }
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Company c = data.companyOf(player.getUUID());
        String arg = msg.arg();
        switch (msg.action()) {
            case CREATE -> create(player, arg);
            case INVITE -> {
                ServerPlayer target = server.getPlayerList().getPlayerByName(Social.clean(arg, 16));
                if (target == null) {
                    Social.fail(player, "message.wayfarers.social.not_online");
                } else {
                    invite(player, target);
                }
            }
            case ACCEPT -> accept(player, parseInt(arg));
            case DECLINE -> decline(player, parseInt(arg));
            case LEAVE -> leave(player);
            case KICK -> kick(player, parseUuid(arg));
            case PROMOTE -> promote(player, parseUuid(arg));
            case FRIENDLY_FIRE, SHARE_XP -> {
                if (c == null || !isLeader(c, player)) {
                    Social.fail(player, "message.wayfarers.company.leader_only");
                    return;
                }
                boolean ff = msg.action() == SocialNet.CompanyAction.Action.FRIENDLY_FIRE;
                if (ff) {
                    c.friendlyFire = !c.friendlyFire;
                } else {
                    c.shareXp = !c.shareXp;
                }
                data.changed();
                boolean on = ff ? c.friendlyFire : c.shareXp;
                tell(server, c, Component.translatable(ff ? "message.wayfarers.company.friendly_fire" : "message.wayfarers.company.share_xp",
                        player.getName(), Component.translatable(on ? "options.on" : "options.off")));
                sync(server, c);
            }
            case CHAT -> toggleChat(player);
            case JOIN -> askJoin(player, parseUuid(arg));
            case RENAME -> {
                if (c == null || !isLeader(c, player)) {
                    Social.fail(player, "message.wayfarers.company.leader_only");
                    return;
                }
                c.name = Social.clean(arg, MAX_NAME);
                data.changed();
                tell(server, c, Component.translatable("message.wayfarers.company.renamed", player.getName(), displayName(c)));
                sync(server, c);
            }
            default -> {
            }
        }
    }

    private static int parseInt(String s) {
        try {
            return Integer.parseInt(s.strip());
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    private static UUID parseUuid(String s) {
        try {
            return UUID.fromString(s.strip());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    static SocialData.Company create(ServerPlayer player, String name) {
        SocialData data = SocialData.get(player.level().getServer());
        if (data.companyOf(player.getUUID()) != null) {
            Social.fail(player, "message.wayfarers.company.already");
            return null;
        }
        if (!Social.cooldown(player, "company_create", 100)) {
            Social.fail(player, "message.wayfarers.social.slow_down");
            return null;
        }
        SocialData.Company c = data.newCompany(Social.clean(name, MAX_NAME), player.getUUID(), player.getName().getString());
        Social.dropRequests(player.getUUID(), Social.RequestType.INVITE);
        Social.info(player, "message.wayfarers.company.created", displayName(c));
        com.wayfarers.util.Tips.show(player, "company");
        sync(player.level().getServer(), c);
        return c;
    }

    /** Invites a player; with no company yet, founds one first. Only the leader invites. */
    static void invite(ServerPlayer player, ServerPlayer target) {
        if (!Social.require(player, Social.Feature.COMPANY)) {
            return;
        }
        SocialData data = SocialData.get(player.level().getServer());
        SocialData.Company c = data.companyOf(player.getUUID());
        if (target == player) {
            return;
        }
        if (data.companyOf(target.getUUID()) != null) {
            Social.fail(player, "message.wayfarers.company.target_taken", target.getName());
            return;
        }
        if (c != null && !isLeader(c, player)) {
            Social.fail(player, "message.wayfarers.company.leader_only");
            return;
        }
        if (c != null && c.members.size() >= Social.config().companyMaxSize.get()) {
            Social.fail(player, "message.wayfarers.company.full");
            return;
        }
        if (!Social.cooldown(player, "invite:" + target.getUUID(), 100)) {
            Social.fail(player, "message.wayfarers.social.slow_down");
            return;
        }
        if (c == null) {
            c = create(player, "");
            if (c == null) {
                return;
            }
        }
        if (Social.request(player, target, Social.RequestType.INVITE, c.id,
                Component.translatable("message.wayfarers.company.invited", player.getName(), displayName(c)))) {
            Social.info(player, "message.wayfarers.social.request_sent", target.getName());
            sync(target);
        }
    }

    static void accept(ServerPlayer player, int companyId) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        Social.Request req = null;
        for (Social.Request r : Social.requestsTo(player.getUUID(), Social.RequestType.INVITE)) {
            if (r.data() == companyId) {
                req = Social.take(player, Social.RequestType.INVITE, r.fromName());
            }
        }
        acceptRequest(player, req);
    }

    /** Joins the company of an invitation taken from the pending requests (null: it expired). */
    static void acceptRequest(ServerPlayer player, Social.Request req) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Company c = req == null ? null : data.company(req.data());
        if (c == null) {
            Social.fail(player, "message.wayfarers.social.no_request");
            sync(player);
            return;
        }
        if (data.companyOf(player.getUUID()) != null) {
            Social.fail(player, "message.wayfarers.company.already");
            return;
        }
        if (c.members.size() >= Social.config().companyMaxSize.get()) {
            Social.fail(player, "message.wayfarers.company.full");
            return;
        }
        c.members.put(player.getUUID(), new SocialData.Member(player.getUUID(), player.getName().getString()));
        data.changed();
        Social.dropRequests(player.getUUID(), Social.RequestType.INVITE);
        tell(server, c, Component.translatable("message.wayfarers.company.joined", player.getName(), displayName(c)));
        com.wayfarers.util.Tips.show(player, "company");
        LAST_STATUS.remove(c.id);
        sync(server, c);
    }

    static void decline(ServerPlayer player, int companyId) {
        for (Social.Request r : Social.requestsTo(player.getUUID(), Social.RequestType.INVITE)) {
            if (r.data() == companyId) {
                Social.take(player, Social.RequestType.INVITE, r.fromName());
                ServerPlayer from = Social.online(player.level().getServer(), r.from());
                if (from != null) {
                    Social.fail(from, "message.wayfarers.social.declined", player.getName());
                }
            }
        }
        sync(player);
    }

    static void leave(ServerPlayer player) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Company c = data.companyOf(player.getUUID());
        if (c == null) {
            return;
        }
        removeMember(server, data, c, player.getUUID());
        Social.info(player, "message.wayfarers.company.left_you");
        if (data.company(c.id) != null) {
            tell(server, c, Component.translatable("message.wayfarers.company.left", player.getName()));
        }
        sync(player);
    }

    private static void removeMember(MinecraftServer server, SocialData data, SocialData.Company c, UUID who) {
        c.members.remove(who);
        CHAT_MODE.remove(who);
        if (c.members.isEmpty()) {
            data.removeCompany(c.id);
            LAST_STATUS.remove(c.id);
            return;
        }
        if (c.leader.equals(who)) {
            c.leader = c.members.keySet().iterator().next();
            tell(server, c, Component.translatable("message.wayfarers.company.new_leader", data.name(c.leader)));
        }
        data.changed();
        LAST_STATUS.remove(c.id);
        sync(server, c);
    }

    static void kick(ServerPlayer player, UUID who) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Company c = data.companyOf(player.getUUID());
        if (c == null || !isLeader(c, player)) {
            Social.fail(player, "message.wayfarers.company.leader_only");
            return;
        }
        if (who == null || who.equals(player.getUUID()) || !c.members.containsKey(who)) {
            return;
        }
        String name = data.name(who);
        removeMember(server, data, c, who);
        tell(server, c, Component.translatable("message.wayfarers.company.kicked", name));
        ServerPlayer gone = Social.online(server, who);
        if (gone != null) {
            Social.fail(gone, "message.wayfarers.company.kicked_you", displayName(c));
            sync(gone);
        }
    }

    static void promote(ServerPlayer player, UUID who) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Company c = data.companyOf(player.getUUID());
        if (c == null || !isLeader(c, player)) {
            Social.fail(player, "message.wayfarers.company.leader_only");
            return;
        }
        if (who == null || !c.members.containsKey(who) || who.equals(c.leader)) {
            return;
        }
        c.leader = who;
        data.changed();
        tell(server, c, Component.translatable("message.wayfarers.company.new_leader", data.name(who)));
        sync(server, c);
    }

    static void toggleChat(ServerPlayer player) {
        if (of(player) == null) {
            Social.fail(player, "message.wayfarers.company.none");
            return;
        }
        boolean on = CHAT_MODE.add(player.getUUID()) || !CHAT_MODE.remove(player.getUUID());
        Social.info(player, on ? "message.wayfarers.company.chat_on" : "message.wayfarers.company.chat_off");
        sync(player);
    }

    /** Company chat: /cc, or every chat line while the switch is on. */
    static void say(ServerPlayer player, String raw) {
        SocialData.Company c = of(player);
        if (c == null) {
            Social.fail(player, "message.wayfarers.company.none");
            return;
        }
        if (!Social.require(player, Social.Feature.COMPANY)) {
            return;
        }
        String text = Social.clean(raw, 256);
        if (text.isEmpty()) {
            return;
        }
        Component line = Component.literal("[").append(displayName(c)).append("] ").withStyle(ChatFormatting.AQUA)
                .append(Component.literal("<").append(player.getName()).append("> ").withStyle(ChatFormatting.WHITE))
                .append(Component.literal(text).withStyle(ChatFormatting.AQUA));
        tell(player.level().getServer(), c, line);
        com.wayfarers.Wayfarers.LOGGER.info("[Company {}] <{}> {}", c.id, player.getName().getString(), text);
    }

    private static boolean onChat(ServerChatEvent e) {
        ServerPlayer p = e.getPlayer();
        if (CHAT_MODE.contains(p.getUUID()) && Social.enabled(Social.Feature.COMPANY) && of(p) != null) {
            say(p, e.getRawText());
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ friendly fire and shared experience
    /** True when this hit is one companion hurting another with friendly fire off (and they are not in a duel). */
    static boolean blocksFriendlyFire(ServerPlayer victim, DamageSource source) {
        if (!(source.getEntity() instanceof ServerPlayer attacker) || attacker == victim || !Social.enabled(Social.Feature.COMPANY)) {
            return false;
        }
        SocialData.Company c = of(victim);
        return c != null && !c.friendlyFire && c.members.containsKey(attacker.getUUID()) && !Duels.fighting(victim, attacker);
    }

    private static void onXp(PlayerXpEvent.XpChange e) {
        if (sharing || e.getAmount() <= 0 || !(e.getEntity() instanceof ServerPlayer picker) || !Social.enabled(Social.Feature.COMPANY)) {
            return;
        }
        Long tick = PICKUP.remove(picker.getUUID());
        MinecraftServer server = picker.level().getServer();
        if (tick == null || tick != server.getTickCount()) {
            return; // only experience orbs are shared: never commands, trades or the shares themselves
        }
        SocialData.Company c = of(picker);
        if (c == null || !c.shareXp) {
            return;
        }
        double range = Social.config().companyXpRange.get();
        List<ServerPlayer> mates = new ArrayList<>();
        for (UUID id : c.members.keySet()) {
            ServerPlayer m = Social.online(server, id);
            if (m != null && m != picker && m.isAlive() && !m.isSpectator() && m.level() == picker.level()
                    && m.distanceToSqr(picker) <= range * range) {
                mates.add(m);
            }
        }
        int share = e.getAmount() / (mates.size() + 1);
        if (mates.isEmpty() || share <= 0) {
            return;
        }
        e.setAmount(e.getAmount() - share * mates.size());
        sharing = true;
        try {
            for (ServerPlayer m : mates) {
                m.giveExperiencePoints(share);
            }
        } finally {
            sharing = false;
        }
    }

    // ------------------------------------------------------------------ travel to a companion
    private static boolean atWaystone(ServerPlayer p) {
        ServerLevel level = p.level();
        for (Map.Entry<String, WayfarersData.Waystone> e : WayfarersData.get(level.getServer()).sortedWaystones()) {
            WayfarersData.Waystone w = e.getValue();
            if (w.levelKey().equals(level.dimension()) && w.pos().closerToCenterThan(p.position(), WAYSTONE_REACH)
                    && (!level.isLoaded(w.pos()) || level.getBlockState(w.pos()).getBlock() instanceof com.wayfarers.block.WaystoneBlock)) {
                return true;
            }
        }
        return false;
    }

    private static boolean free(ServerPlayer p) {
        return p.isCreative() || p.isSpectator();
    }

    /** Why this traveller cannot go to this companion right now (null: they can). */
    private static String joinProblem(ServerPlayer traveller, ServerPlayer mate) {
        if (!atWaystone(traveller)) {
            return "message.wayfarers.company.join_waystone";
        }
        int cost = Social.config().companyJoinCost.get();
        if (!free(traveller) && traveller.experienceLevel < cost) {
            return "message.wayfarers.company.join_levels";
        }
        if (Duels.inDuel(traveller) || Duels.inDuel(mate) || Trade.trading(traveller)) {
            return "message.wayfarers.company.join_busy";
        }
        if (!mate.isAlive() || mate.isSpectator() || mate.isInLava() || mate.isFallFlying()
                || !(mate.onGround() || mate.isInWater())) {
            return "message.wayfarers.company.join_unsafe";
        }
        AABB around = mate.getBoundingBox().inflate(64);
        if (!mate.level().getEntitiesOfClass(com.wayfarers.boss.WayfarerBoss.class, around, net.minecraft.world.entity.LivingEntity::isAlive).isEmpty()) {
            return "message.wayfarers.company.join_boss";
        }
        return null;
    }

    static void askJoin(ServerPlayer player, UUID mateId) {
        MinecraftServer server = player.level().getServer();
        ServerPlayer mate = mateId == null ? null : Social.online(server, mateId);
        if (mate == null || !companions(player, mate)) {
            Social.fail(player, "message.wayfarers.social.not_online");
            return;
        }
        long left = Social.cooldownLeft(player, "join");
        if (left > 0) {
            Social.fail(player, "message.wayfarers.company.join_cooldown", left / 20 + 1);
            return;
        }
        String problem = joinProblem(player, mate);
        if (problem != null) {
            Social.fail(player, problem, Social.config().companyJoinCost.get());
            return;
        }
        if (!Social.cooldown(player, "join_ask", 100)) {
            Social.fail(player, "message.wayfarers.social.slow_down");
            return;
        }
        if (Social.request(player, mate, Social.RequestType.JOIN, 0,
                Component.translatable("message.wayfarers.company.join_request", player.getName()))) {
            Social.info(player, "message.wayfarers.social.request_sent", mate.getName());
        }
    }

    /** The companion accepted: check everything again, charge the levels and move the traveller. */
    static void acceptJoin(ServerPlayer mate, Social.Request req) {
        MinecraftServer server = mate.level().getServer();
        ServerPlayer traveller = req == null ? null : Social.online(server, req.from());
        if (traveller == null || !companions(traveller, mate)) {
            Social.fail(mate, "message.wayfarers.social.no_request");
            return;
        }
        String problem = joinProblem(traveller, mate);
        if (problem != null) {
            Social.fail(traveller, problem, Social.config().companyJoinCost.get());
            Social.fail(mate, "message.wayfarers.company.join_failed", traveller.getName());
            return;
        }
        if (!Social.cooldown(traveller, "join", Social.config().companyJoinCooldown.get() * 20)) {
            return;
        }
        int cost = Social.config().companyJoinCost.get();
        if (!free(traveller) && cost > 0) {
            traveller.giveExperienceLevels(-cost);
        }
        ServerLevel from = traveller.level();
        from.sendParticles(ParticleTypes.PORTAL, traveller.getX(), traveller.getY() + 1, traveller.getZ(), 60, 0.4, 0.8, 0.4, 0.2);
        ServerLevel to = mate.level();
        BlockPos at = mate.blockPosition();
        traveller.teleportTo(to, mate.getX(), mate.getY(), mate.getZ(), Set.of(), mate.getYRot(), traveller.getXRot(), false);
        to.playSound(null, at, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 0.8F, 1.2F);
        to.sendParticles(ParticleTypes.REVERSE_PORTAL, mate.getX(), mate.getY() + 1, mate.getZ(), 60, 0.4, 0.8, 0.4, 0.1);
        Social.info(traveller, "message.wayfarers.company.joined_mate", mate.getName());
        Social.info(mate, "message.wayfarers.company.mate_arrived", traveller.getName());
    }

    // ------------------------------------------------------------------ sync
    static void tell(MinecraftServer server, SocialData.Company c, Component line) {
        for (UUID id : c.members.keySet()) {
            ServerPlayer p = Social.online(server, id);
            if (p != null) {
                p.sendSystemMessage(line.copy().withStyle(s -> s.getColor() == null ? s.withColor(ChatFormatting.AQUA) : s));
            }
        }
    }

    static void sync(MinecraftServer server, SocialData.Company c) {
        for (UUID id : c.members.keySet()) {
            ServerPlayer p = Social.online(server, id);
            if (p != null) {
                sync(p);
            }
        }
    }

    /** Sends a player their company (or none) and their pending invitations. */
    static void sync(ServerPlayer player) {
        MinecraftServer server = player.level().getServer();
        SocialData data = SocialData.get(server);
        SocialData.Company c = data.companyOf(player.getUUID());
        List<SocialNet.Invite> invites = new ArrayList<>();
        for (Social.Request r : Social.requestsTo(player.getUUID(), Social.RequestType.INVITE)) {
            SocialData.Company ic = data.company(r.data());
            if (ic != null) {
                invites.add(new SocialNet.Invite(ic.id, displayName(ic).getString(), r.fromName()));
            }
        }
        if (c == null) {
            SocialNet.toPlayer(player, new SocialNet.CompanyState(0, "", SocialNet.CompanyState.NOBODY, false, false, false,
                    List.of(), invites));
            return;
        }
        List<SocialNet.MemberInfo> members = new ArrayList<>();
        for (SocialData.Member m : c.members.values()) {
            members.add(new SocialNet.MemberInfo(m.id(), m.name(), Social.online(server, m.id()) != null));
        }
        SocialNet.toPlayer(player, new SocialNet.CompanyState(c.id, c.name, c.leader, c.friendlyFire, c.shareXp,
                CHAT_MODE.contains(player.getUUID()), members, invites));
    }

    private static void sendStatus(MinecraftServer server) {
        for (SocialData.Company c : SocialData.get(server).companies()) {
            List<ServerPlayer> online = new ArrayList<>();
            for (UUID id : c.members.keySet()) {
                ServerPlayer p = Social.online(server, id);
                if (p != null) {
                    online.add(p);
                }
            }
            if (online.size() < 2) {
                continue;
            }
            List<SocialNet.Status> list = new ArrayList<>();
            int hash = 1;
            for (ServerPlayer p : online) {
                String dim = p.level().dimension().identifier().toString();
                // half hearts and 2-block steps: a companion standing still sends nothing
                float hp = Math.round(p.getHealth() * 2) / 2.0F;
                list.add(new SocialNet.Status(p.getUUID(), hp, p.getMaxHealth(), dim, p.getBlockX(), p.getBlockY(), p.getBlockZ()));
                hash = 31 * hash + java.util.Objects.hash(p.getUUID(), hp, p.getMaxHealth(), dim, p.getBlockX() >> 1, p.getBlockZ() >> 1,
                        p.getBlockY() >> 2);
            }
            Integer last = LAST_STATUS.put(c.id, hash);
            if (last != null && last == hash) {
                continue;
            }
            SocialNet.CompanyStatus msg = new SocialNet.CompanyStatus(list);
            for (ServerPlayer p : online) {
                SocialNet.toPlayer(p, msg);
            }
        }
    }

    /** For the self-test: the share each of n players gets from an orb, and what the picker keeps. */
    static int[] split(int amount, int mates) {
        int share = amount / (mates + 1);
        return new int[] {share, amount - share * mates};
    }
}
