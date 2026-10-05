package com.brasshaven.social;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * Duels: one player challenges another standing nearby; once accepted, a ring of red dust marks the arena around the
 * point between them and a 3-2-1 countdown runs (no hits count during it). The fight ends when a duelist would fall
 * to the other's blow (they keep half a heart: nobody dies, nothing drops), leaves the ring, logs out, or dies of
 * anything else; past {@code duels.maxSeconds} it is a draw. Outsiders cannot hit the duelists and the duelists cannot
 * hit outsiders. Results go to the duel record (shown on the player card) and, if enabled, to the whole server.
 *
 * <p>Duels can only start away from bosses, so a duel never shields anyone from a boss fight.
 */
public final class Duels {
    private static final int COUNTDOWN = 60;
    private static final List<Duel> DUELS = new ArrayList<>();
    private static final DustParticleOptions RING = new DustParticleOptions(0xD8402C, 1.2F);

    private Duels() {}

    static final class Duel {
        final ServerPlayer a;
        final ServerPlayer b;
        final ServerLevel level;
        final Vec3 center;
        final double radius;
        int age;
        boolean over;

        Duel(ServerPlayer a, ServerPlayer b, double radius) {
            this.a = a;
            this.b = b;
            this.level = a.level();
            this.center = a.position().add(b.position()).scale(0.5);
            this.radius = radius;
        }

        boolean fighting() {
            return !over && age >= COUNTDOWN;
        }

        boolean has(ServerPlayer p) {
            return p == a || p == b;
        }

        ServerPlayer other(ServerPlayer p) {
            return p == a ? b : a;
        }
    }

    static void register() {
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick(e.server()));
        LivingAttackEvent.BUS.addListener((Predicate<LivingAttackEvent>) e -> blocks(e.getEntity(), e.getSource()));
        // the last blow of the opponent leaves half a heart and ends the duel
        LivingDamageEvent.BUS.addListener((Consumer<LivingDamageEvent>) e -> {
            if (e.getEntity() instanceof ServerPlayer victim && e.getSource().getEntity() instanceof ServerPlayer attacker) {
                Duel d = duelOf(victim);
                if (d != null && d.fighting() && d.other(victim) == attacker && e.getAmount() >= victim.getHealth() - 0.5F) {
                    e.setAmount(Math.max(0, victim.getHealth() - 1.0F));
                    finish(d, attacker, "message.brasshaven.duel.won");
                }
            }
        });
        LivingDeathEvent.BUS.addListener((Consumer<LivingDeathEvent>) e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                Duel d = duelOf(p);
                if (d != null) {
                    finish(d, d.other(p), "message.brasshaven.duel.won_fell");
                }
            }
        });
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                Duel d = duelOf(p);
                if (d != null) {
                    finish(d, d.other(p), "message.brasshaven.duel.won_left");
                }
            }
        });
    }

    static Duel duelOf(ServerPlayer p) {
        for (Duel d : DUELS) {
            if (!d.over && d.has(p)) {
                return d;
            }
        }
        return null;
    }

    public static boolean inDuel(ServerPlayer p) {
        return duelOf(p) != null;
    }

    /** True while these two fight each other (friendly fire does not apply then). */
    public static boolean fighting(ServerPlayer a, ServerPlayer b) {
        Duel d = duelOf(a);
        return d != null && d.fighting() && d.other(a) == b;
    }

    /** Hits that do not count: between duelists during the countdown, and between a duelist and an outsider. */
    private static boolean blocks(LivingEntity victim, DamageSource source) {
        if (DUELS.isEmpty() || !(source.getEntity() instanceof ServerPlayer attacker) || attacker == victim) {
            return false;
        }
        Duel dv = victim instanceof ServerPlayer v ? duelOf(v) : null;
        Duel da = duelOf(attacker);
        if (dv != null && dv == da) {
            return !dv.fighting();
        }
        // an outsider hitting a duelist, or a duelist hitting another player
        return dv != null || (da != null && victim instanceof ServerPlayer);
    }

    static void stopAll() {
        DUELS.clear();
    }

    // ------------------------------------------------------------------ challenge
    private static String problem(ServerPlayer a, ServerPlayer b) {
        if (a.level() != b.level() || a.distanceTo(b) > 16) {
            return "message.brasshaven.duel.too_far";
        }
        if (inDuel(a) || inDuel(b) || Trade.trading(a) || Trade.trading(b) || !a.isAlive() || !b.isAlive()
                || a.isSpectator() || b.isSpectator()) {
            return "message.brasshaven.duel.busy";
        }
        AABB around = a.getBoundingBox().minmax(b.getBoundingBox()).inflate(64);
        if (!a.level().getEntitiesOfClass(com.brasshaven.boss.WayfarerBoss.class, around, LivingEntity::isAlive).isEmpty()) {
            return "message.brasshaven.duel.boss";
        }
        return null;
    }

    static void challenge(ServerPlayer from, ServerPlayer to) {
        if (!Social.require(from, Social.Feature.DUELS) || from == to) {
            return;
        }
        String p = problem(from, to);
        if (p != null) {
            Social.fail(from, p, to.getName());
            return;
        }
        if (!Social.cooldown(from, "duel:" + to.getUUID(), 200)) {
            Social.fail(from, "message.brasshaven.social.slow_down");
            return;
        }
        if (Social.request(from, to, Social.RequestType.DUEL, 0, Component.translatable("message.brasshaven.duel.request", from.getName()))) {
            Social.info(from, "message.brasshaven.social.request_sent", to.getName());
        }
    }

    static void accept(ServerPlayer to, Social.Request req) {
        ServerPlayer from = req == null ? null : Social.online(to.level().getServer(), req.from());
        if (from == null) {
            Social.fail(to, "message.brasshaven.social.no_request");
            return;
        }
        if (!Social.require(to, Social.Feature.DUELS)) {
            return;
        }
        String p = problem(from, to);
        if (p != null) {
            Social.fail(to, p, from.getName());
            return;
        }
        Duel d = new Duel(from, to, Social.config().duelRadius.get());
        DUELS.add(d);
        for (ServerPlayer pl : List.of(from, to)) {
            pl.connection.send(new ClientboundSetTitlesAnimationPacket(0, 25, 5));
            Social.info(pl, "message.brasshaven.duel.started", d.other(pl).getName(), (int) d.radius);
            com.brasshaven.util.Tips.show(pl, "duel");
        }
    }

    // ------------------------------------------------------------------ the fight
    private static void tick(MinecraftServer server) {
        if (DUELS.isEmpty()) {
            return;
        }
        int maxTicks = COUNTDOWN + Social.config().duelSeconds.get() * 20;
        for (Duel d : new ArrayList<>(DUELS)) {
            if (d.over) {
                continue;
            }
            d.age++;
            if (d.age <= COUNTDOWN && d.age % 20 == 0) {
                int n = (COUNTDOWN - d.age) / 20;
                for (ServerPlayer p : List.of(d.a, d.b)) {
                    p.connection.send(new ClientboundSetTitleTextPacket(n > 0 ? Component.literal(String.valueOf(n)).withStyle(ChatFormatting.GOLD)
                            : Component.translatable("message.brasshaven.duel.fight").withStyle(ChatFormatting.RED)));
                    p.connection.send(new ClientboundSetSubtitleTextPacket(Component.translatable("message.brasshaven.duel.vs",
                            d.other(p).getName())));
                    Social.ding(p, n > 0 ? SoundEvents.NOTE_BLOCK_HAT : SoundEvents.NOTE_BLOCK_BELL, n > 0 ? 1.0F : 0.8F);
                }
            }
            if (d.age % 10 == 0) {
                ring(d);
            }
            for (ServerPlayer p : List.of(d.a, d.b)) {
                if (p.level() != d.level || p.position().distanceToSqr(d.center.x, p.getY(), d.center.z) > (d.radius + 0.5) * (d.radius + 0.5)) {
                    finish(d, d.other(p), "message.brasshaven.duel.won_ring");
                    break;
                }
            }
            if (!d.over && d.age >= maxTicks) {
                finish(d, null, "message.brasshaven.duel.draw");
            }
        }
        DUELS.removeIf(d -> d.over);
    }

    private static void ring(Duel d) {
        int points = (int) Math.max(24, d.radius * 3);
        for (ServerPlayer p : List.of(d.a, d.b)) {
            for (int i = 0; i < points; i++) {
                double ang = Math.PI * 2 * i / points;
                double x = d.center.x + Math.cos(ang) * d.radius;
                double z = d.center.z + Math.sin(ang) * d.radius;
                // only the duelists see the ring (sent to each of them, near their own height)
                d.level.sendParticles(p, RING, false, false, x, p.getY() + 0.3, z, 1, 0, 0, 0, 0);
            }
        }
    }

    private static void finish(Duel d, ServerPlayer winner, String key) {
        if (d.over) {
            return;
        }
        d.over = true;
        MinecraftServer server = d.a.level().getServer();
        SocialData data = SocialData.get(server);
        ServerPlayer loser = winner == null ? null : d.other(winner);
        Component line;
        if (winner == null) {
            data.recordDuel(d.a.getUUID(), 0, 0, 1);
            data.recordDuel(d.b.getUUID(), 0, 0, 1);
            line = Component.translatable(key, d.a.getName(), d.b.getName()).withStyle(ChatFormatting.GOLD);
        } else {
            data.recordDuel(winner.getUUID(), 1, 0, 0);
            data.recordDuel(loser.getUUID(), 0, 1, 0);
            line = Component.translatable(key, winner.getName(), loser.getName()).withStyle(ChatFormatting.GOLD);
        }
        com.brasshaven.Brasshaven.LOGGER.info("Duel {} vs {}: {}", d.a.getName().getString(), d.b.getName().getString(),
                winner == null ? "draw" : winner.getName().getString() + " won");
        if (Social.config().duelAnnounce.get()) {
            server.getPlayerList().broadcastSystemMessage(line, false);
        } else {
            d.a.sendSystemMessage(line);
            d.b.sendSystemMessage(line);
        }
        for (ServerPlayer p : List.of(d.a, d.b)) {
            if (p.isAlive() && !p.hasDisconnected()) {
                p.connection.send(new ClientboundSetTitleTextPacket(Component.translatable(
                        winner == null ? "message.brasshaven.duel.title_draw" : p == winner ? "message.brasshaven.duel.title_win"
                                : "message.brasshaven.duel.title_loss").withStyle(p == winner ? ChatFormatting.GOLD : ChatFormatting.GRAY)));
                p.connection.send(new ClientboundSetSubtitleTextPacket(Component.empty()));
                p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 1));
                Social.ding(p, p == winner ? SoundEvents.PLAYER_LEVELUP : SoundEvents.NOTE_BLOCK_BASS.value(), 1.0F);
            }
        }
    }

    /** For the self-test: whether a point is inside the ring of a duel centred at (cx, cz). */
    static boolean inRing(double cx, double cz, double radius, double x, double z) {
        return (x - cx) * (x - cx) + (z - cz) * (z - cz) <= (radius + 0.5) * (radius + 0.5);
    }
}
