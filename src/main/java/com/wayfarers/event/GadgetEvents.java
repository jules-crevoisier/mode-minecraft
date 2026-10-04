package com.wayfarers.event;

import com.wayfarers.item.GliderItem;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingFallEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.fml.LogicalSide;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Predicate;

/** Steam gadgets that act every tick: the Brass Glider, and soft landings after a glide or a grapple. */
public final class GadgetEvents {
    /** Player -> game time until which a landing does no damage (server). */
    private static final Map<UUID, Long> SOFT_LANDING = new HashMap<>();

    private GadgetEvents() {}

    public static void register() {
        TickEvent.PlayerTickEvent.Pre.BUS.addListener(GadgetEvents::onPlayerTick);
        LivingFallEvent.BUS.addListener((Predicate<LivingFallEvent>) GadgetEvents::onFall);
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(event -> {
            SOFT_LANDING.remove(event.getEntity().getUUID());
            GliderItem.forget(event.getEntity().getUUID());
        });
    }

    /** Landings within the next {@code ticks} ticks do no damage. Server side. */
    public static void softLanding(Player player, int ticks) {
        if (player instanceof ServerPlayer sp) {
            SOFT_LANDING.merge(sp.getUUID(), sp.level().getGameTime() + ticks, Math::max);
        }
    }

    private static void onPlayerTick(TickEvent.PlayerTickEvent.Pre event) {
        Player player = event.player();
        if (event.side() == LogicalSide.CLIENT) {
            // only the local player's movement is simulated here; other players arrive as positions
            if (player.isLocalPlayer()) {
                GliderItem.glideClient(player);
            }
        } else if (player instanceof ServerPlayer sp) {
            GliderItem.glideServer(sp);
        }
    }

    private static boolean onFall(LivingFallEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return false;
        }
        Long until = SOFT_LANDING.get(player.getUUID());
        if (until == null) {
            return false;
        }
        if (until < player.level().getGameTime()) {
            SOFT_LANDING.remove(player.getUUID());
            return false;
        }
        return true;
    }
}
