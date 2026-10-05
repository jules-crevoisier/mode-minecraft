package com.brasshaven.util;

import com.brasshaven.network.TipMsg;
import com.brasshaven.network.BrasshavenNet;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * One-time tips: the first time a player meets a system (a waystone, a grave, an elite, a Blood Moon...)
 * a small card explains it and links to the manual page. Remembered per player in its persistent data.
 */
public final class Tips {
    private static final String KEY = "brasshaven_tips";

    private Tips() {}

    public static void show(ServerPlayer player, String tip) {
        // under "PlayerPersisted" so Forge copies it to the new player entity after death
        CompoundTag data = player.getPersistentData();
        CompoundTag persisted = data.getCompoundOrEmpty("PlayerPersisted");
        CompoundTag seen = persisted.getCompoundOrEmpty(KEY);
        if (seen.getBooleanOr(tip, false)) {
            return;
        }
        seen.putBoolean(tip, true);
        persisted.put(KEY, seen);
        data.put("PlayerPersisted", persisted);
        BrasshavenNet.toPlayer(player, new TipMsg(tip));
    }

    public static void showNear(ServerLevel level, Vec3 pos, double radius, String tip) {
        for (ServerPlayer p : level.players()) {
            if (p.position().distanceToSqr(pos) < radius * radius) {
                show(p, tip);
            }
        }
    }
}
