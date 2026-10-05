package com.wayfarers.util;

import com.wayfarers.data.WayfarersData;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.level.block.Block;

import com.wayfarers.network.WaystoneActionMsg;
import com.wayfarers.network.WaystoneListMsg;
import com.wayfarers.network.WayfarersNet;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class Waystones {
    /** Player -> server tick of their last waystone journey (the cooldown of waystones.cooldownSeconds). */
    private static final Map<java.util.UUID, Integer> LAST_WARP = new java.util.HashMap<>();

    private Waystones() {}

    /** Forgets a player who left (see ServerGuard). */
    public static void forget(java.util.UUID id) {
        LAST_WARP.remove(id);
    }

    public static String defaultName(ServerLevel level, BlockPos pos) {
        String biome = level.getBiome(pos).unwrapKey()
                .map(k -> k.identifier().getPath())
                .orElse("waystone");
        StringBuilder sb = new StringBuilder();
        for (String word : biome.split("_")) {
            if (!word.isEmpty()) {
                sb.append(Character.toUpperCase(word.charAt(0))).append(word.substring(1)).append(' ');
            }
        }
        return sb.toString().trim() + " (" + pos.getX() + ", " + pos.getZ() + ")";
    }

    /** Discovers the waystone at {@code pos} for everyone, then shows the travel menu. */
    public static void discoverAndList(ServerLevel level, BlockPos pos, ServerPlayer player) {
        WayfarersData data = WayfarersData.get(level.getServer());
        boolean known = data.findWaystone(level, pos).isPresent();
        String here = data.addWaystone(level, pos, defaultName(level, pos));
        if (here == null) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.full",
                    com.wayfarers.config.WayfarersConfig.WAYSTONE_MAX.get()).withStyle(ChatFormatting.RED));
            return;
        }
        if (!known) {
            String name = data.waystone(here).map(WayfarersData.Waystone::name).orElse("?");
            level.getServer().getPlayerList().broadcastSystemMessage(
                    Component.translatable("message.wayfarers.waystone.discovered", name).withStyle(ChatFormatting.AQUA), false);
            level.sendParticles(ParticleTypes.END_ROD, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5,
                    40, 0.4, 0.6, 0.4, 0.05);
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0F, 1.0F);
        }
        list(player, here);
        Tips.show(player, "waystone");
    }

    /** Opens the travel screen on the player's client (current = the waystone they stand at, or ""). */
    public static void list(ServerPlayer player, String currentId) {
        WayfarersData data = WayfarersData.get(player.level().getServer());
        List<WaystoneListMsg.Entry> entries = new ArrayList<>();
        for (Map.Entry<String, WayfarersData.Waystone> e : data.sortedWaystones()) {
            WayfarersData.Waystone w = e.getValue();
            entries.add(new WaystoneListMsg.Entry(e.getKey(), w.name(), w.dimension().getPath(),
                    w.pos().getX(), w.pos().getY(), w.pos().getZ(), w.pinned()));
        }
        WayfarersNet.toPlayer(player, new WaystoneListMsg(currentId, entries));
    }

    private static boolean isOp(ServerPlayer player) {
        return player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER);
    }

    /**
     * Validates and runs an action sent from the travel screen. Nothing the client sends is trusted: the player must
     * stand at the waystone {@code from} (in its dimension), the target must exist, and the server config decides
     * cooldown, cost, cross-dimension travel and who may rename (docs/SERVER_ADMIN.md).
     */
    public static void handleAction(ServerPlayer player, WaystoneActionMsg msg) {
        WayfarersData data = WayfarersData.get(player.level().getServer());
        boolean op = isOp(player);
        boolean atStone = data.waystone(msg.from())
                .filter(w -> w.levelKey().equals(player.level().dimension())
                        && w.pos().closerToCenterThan(player.position(), 8.0))
                .isPresent();
        if (!atStone && !op) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.too_far").withStyle(ChatFormatting.RED));
            return;
        }
        switch (msg.action()) {
            case WARP -> {
                if (msg.target().equals(msg.from())) {
                    return;
                }
                var target = data.waystone(msg.target());
                if (target.isPresent() && !op && !mayTravel(player, target.get())) {
                    return;
                }
                int cost = target.map(t -> cost(player, t)).orElse(0); // before the journey: it may change dimension
                if (!warp(player, msg.target())) {
                    player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.gone").withStyle(ChatFormatting.RED));
                    list(player, msg.from());
                } else if (!op) {
                    payForTravel(player, cost);
                }
            }
            case RENAME, PIN -> {
                // waystones are shared by the whole server: by default only the stone you stand at can be renamed
                if (!op && com.wayfarers.config.WayfarersConfig.WAYSTONE_RENAME_HERE_ONLY.get() && !msg.target().equals(msg.from())) {
                    player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.rename_here")
                            .withStyle(ChatFormatting.RED));
                } else if (msg.action() == WaystoneActionMsg.Action.PIN) {
                    data.togglePinned(msg.target());
                } else {
                    String name = msg.text().strip();
                    if (!name.isEmpty() && name.length() <= WayfarersData.MAX_NAME) {
                        data.renameWaystone(msg.target(), name);
                    }
                }
                list(player, msg.from());
            }
        }
    }

    private static boolean crossDimension(ServerPlayer player, WayfarersData.Waystone target) {
        return !target.levelKey().equals(player.level().dimension());
    }

    private static int cost(ServerPlayer player, WayfarersData.Waystone target) {
        int cost = com.wayfarers.config.WayfarersConfig.WAYSTONE_COST.get();
        return crossDimension(player, target) ? cost * 2 : cost;
    }

    /** Cross-dimension rule, cooldown and cost (creative players pay nothing); tells the player why not. */
    private static boolean mayTravel(ServerPlayer player, WayfarersData.Waystone target) {
        if (crossDimension(player, target) && !com.wayfarers.config.WayfarersConfig.WAYSTONE_CROSS_DIMENSION.get()) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.no_cross_dimension")
                    .withStyle(ChatFormatting.RED));
            return false;
        }
        int now = player.level().getServer().getTickCount();
        Integer last = LAST_WARP.get(player.getUUID());
        int wait = com.wayfarers.config.WayfarersConfig.WAYSTONE_COOLDOWN.get() * 20;
        if (last != null && now >= last && now - last < wait) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.cooldown", (wait - (now - last) + 19) / 20)
                    .withStyle(ChatFormatting.RED));
            return false;
        }
        int cost = cost(player, target);
        if (cost > 0 && !player.getAbilities().instabuild && player.experienceLevel < cost) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.cost", cost).withStyle(ChatFormatting.RED));
            return false;
        }
        return true;
    }

    private static void payForTravel(ServerPlayer player, int cost) {
        LAST_WARP.put(player.getUUID(), player.level().getServer().getTickCount());
        if (cost > 0 && !player.getAbilities().instabuild) {
            player.giveExperienceLevels(-cost);
        }
    }

    /** Teleports the player next to the waystone; returns false when it no longer exists. */
    public static boolean warp(ServerPlayer player, String id) {
        WayfarersData data = WayfarersData.get(player.level().getServer());
        var target = data.waystone(id);
        if (target.isEmpty()) {
            return false;
        }
        WayfarersData.Waystone w = target.get();
        ServerLevel level = player.level().getServer().getLevel(w.levelKey());
        if (level == null) {
            return false;
        }
        Block block = level.getBlockState(w.pos()).getBlock();
        if (!(block instanceof com.wayfarers.block.WaystoneBlock) && level.isLoaded(w.pos())) {
            data.removeWaystone(level, w.pos());
            return false;
        }
        BlockPos dest = safeSpotNear(level, w.pos());
        ServerLevel from = player.level();
        from.sendParticles(ParticleTypes.PORTAL, player.getX(), player.getY() + 1, player.getZ(), 60, 0.4, 0.8, 0.4, 0.2);
        player.teleportTo(level, dest.getX() + 0.5, dest.getY(), dest.getZ() + 0.5, Set.of(), player.getYRot(), player.getXRot(), false);
        level.playSound(null, dest, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 0.8F, 1.2F);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, dest.getX() + 0.5, dest.getY() + 1, dest.getZ() + 0.5, 60, 0.4, 0.8, 0.4, 0.1);
        player.sendSystemMessage(Component.translatable("message.wayfarers.waystone.travel", w.name()).withStyle(ChatFormatting.AQUA));
        return true;
    }

    private static BlockPos safeSpotNear(ServerLevel level, BlockPos waystone) {
        for (BlockPos offset : List.of(new BlockPos(0, 0, 1), new BlockPos(1, 0, 0), new BlockPos(0, 0, -1),
                new BlockPos(-1, 0, 0), new BlockPos(1, 0, 1), new BlockPos(-1, 0, -1))) {
            BlockPos p = waystone.offset(offset);
            for (int dy = -1; dy <= 2; dy++) {
                BlockPos feet = p.above(dy);
                if (level.getBlockState(feet).isAir() && level.getBlockState(feet.above()).isAir()
                        && !level.getBlockState(feet.below()).isAir()) {
                    return feet;
                }
            }
        }
        return waystone.above();
    }
}
