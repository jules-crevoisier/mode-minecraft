package com.brasshaven.colossal;

import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;

/** Client-only helpers of the vault gear (only ever called behind a Dist.CLIENT check). */
final class ColossalClient {
    private ColossalClient() {}

    /** Pieces of a set the local player wears (lights up the bonuses already active in the tooltip). */
    static int worn(ColossalSet set) {
        Player p = Minecraft.getInstance().player;
        return p == null ? 0 : set.worn(p);
    }
}
