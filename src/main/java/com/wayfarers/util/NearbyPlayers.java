package com.wayfarers.util;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

/**
 * Player searches that walk the level's (short) player list instead of every entity section inside a large box.
 * Same result as {@code level.getEntitiesOfClass(Player.class, box, filter)}: players whose bounding box touches
 * {@code box}. Meant for checks that run every few ticks over big areas (boss arenas, gaze tests).
 */
public final class NearbyPlayers {
    private NearbyPlayers() {}

    public static List<Player> in(ServerLevel level, AABB box, Predicate<? super Player> filter) {
        List<Player> out = new ArrayList<>(2);
        for (ServerPlayer p : level.players()) {
            if (p.getBoundingBox().intersects(box) && filter.test(p)) {
                out.add(p);
            }
        }
        return out;
    }

    public static boolean any(ServerLevel level, AABB box, Predicate<? super Player> filter) {
        for (ServerPlayer p : level.players()) {
            if (p.getBoundingBox().intersects(box) && filter.test(p)) {
                return true;
            }
        }
        return false;
    }
}
