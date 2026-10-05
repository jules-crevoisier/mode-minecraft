package com.brasshaven.util;

import com.brasshaven.block.MachineBlock;
import com.brasshaven.block.MachineBlockEntity;
import com.brasshaven.config.BrasshavenConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraftforge.common.util.BlockSnapshot;
import net.minecraftforge.event.ForgeEventFactory;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.level.BlockEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.common.util.Result;
import org.jetbrains.annotations.Nullable;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Predicate;

/**
 * Server-side guards shared by every client action (docs/SERVER_AUDIT.md):
 * <ul>
 *     <li>{@link #canAct}: the sender is connected, alive and not a spectator;</li>
 *     <li>{@link #allow}: a per-player token bucket, so a modified client can not flood the server with actions;</li>
 *     <li>{@link #mayBreak} / {@link #mayPlace}: asks spawn protection and protection mods (Forge's break and place
 *     events) before the mod changes a block on a player's behalf;</li>
 *     <li>the per-chunk machine limit;</li>
 *     <li>one place that forgets per-player state when a player leaves (no map keyed by a player grows forever).</li>
 * </ul>
 * Everything here runs on the server thread (network handlers are registered with {@code addMain}).
 */
public final class ServerGuard {
    /** True while {@link #mayBreak} / {@link #mayPlace} ask the protection mods: our own listeners must not act. */
    private static boolean probing;

    /** Per player: per action key, {tokens * 1000, last refill nanos}. */
    private static final Map<UUID, Map<String, long[]>> BUCKETS = new HashMap<>();

    private ServerGuard() {}

    public static void register() {
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> forget(e.getEntity().getUUID()));
        ServerStoppedEvent.BUS.addListener(e -> BUCKETS.clear());
        BlockEvent.EntityPlaceEvent.BUS.addListener((Predicate<BlockEvent.EntityPlaceEvent>) ServerGuard::onPlace);
    }

    /** Everything the mod keeps per player in memory, dropped when the player leaves. */
    private static void forget(UUID id) {
        BUCKETS.remove(id);
        com.brasshaven.event.DangerEvents.forget(id);
        com.brasshaven.event.EquipmentEvents.forget(id);
        com.brasshaven.item.BuilderWandItem.forget(id);
        com.brasshaven.block.CrateBlock.forget(id);
        Waystones.forget(id);
    }

    /** A real, connected, living, non-spectator player (a click can arrive after death or while leaving). */
    public static boolean canAct(@Nullable ServerPlayer player) {
        return player != null && !player.isRemoved() && player.isAlive() && !player.isSpectator()
                && !player.hasDisconnected();
    }

    /**
     * Token bucket: true when {@code player} may do one more {@code key} action now. Up to {@code burst} actions at
     * once, then {@code perSecond} a second.
     */
    public static boolean allow(ServerPlayer player, String key, int burst, double perSecond) {
        long now = System.nanoTime();
        long[] b = BUCKETS.computeIfAbsent(player.getUUID(), k -> new HashMap<>()).computeIfAbsent(key,
                k -> new long[] {burst * 1000L, now});
        long refill = (long) ((now - b[1]) / 1_000_000_000.0 * perSecond * 1000.0);
        if (refill > 0) {
            b[0] = Math.min(burst * 1000L, b[0] + refill);
            b[1] = now;
        }
        if (b[0] < 1000L) {
            return false;
        }
        b[0] -= 1000L;
        return true;
    }

    // ------------------------------------------------------------------ protection

    /**
     * May {@code player} break the block at {@code pos}? Spawn protection, world border and protection mods (the
     * Forge break event, which claim mods cancel) all have their say. Server side only.
     */
    public static boolean mayBreak(ServerLevel level, BlockPos pos, ServerPlayer player) {
        if (!level.mayInteract(player, pos) || player.blockActionRestricted(level, pos, player.gameMode.getGameModeForPlayer())) {
            return false;
        }
        BlockState state = level.getBlockState(pos);
        BlockEvent.BreakEvent event = new BlockEvent.BreakEvent(level, pos, state, player, Result.DEFAULT);
        boolean was = probing;
        probing = true;
        try {
            boolean cancelled = BlockEvent.BreakEvent.BUS.post(event);
            return !cancelled && !event.getResult().isDenied();
        } finally {
            probing = was;
        }
    }

    /** True while the mod is only asking whether a block may change (listeners must not act on that event). */
    public static boolean probing() {
        return probing;
    }

    /** May {@code player} place a block at {@code pos} (an empty or replaceable spot)? See {@link #mayBreak}. */
    public static boolean mayPlace(ServerLevel level, BlockPos pos, ServerPlayer player) {
        if (!level.mayInteract(player, pos) || !player.mayBuild()) {
            return false;
        }
        BlockSnapshot snapshot = BlockSnapshot.create(level.dimension(), level, pos);
        boolean was = probing;
        probing = true;
        try {
            return !ForgeEventFactory.onBlockPlace(player, snapshot, net.minecraft.core.Direction.UP);
        } finally {
            probing = was;
        }
    }

    // ------------------------------------------------------------------ machines per chunk

    /** How many Brasshaven machines the chunk at {@code pos} holds. */
    public static int machinesInChunk(ServerLevel level, BlockPos pos) {
        LevelChunk chunk = level.getChunkSource().getChunkNow(pos.getX() >> 4, pos.getZ() >> 4);
        if (chunk == null) {
            return 0;
        }
        int n = 0;
        for (BlockEntity be : chunk.getBlockEntities().values()) {
            if (be instanceof MachineBlockEntity && !be.isRemoved()) {
                n++;
            }
        }
        return n;
    }

    /** True when one more machine fits in the chunk of {@code pos} (counting one already placed there). */
    public static boolean machineFits(ServerLevel level, BlockPos pos, boolean alreadyPlaced) {
        int max = BrasshavenConfig.MACHINES_PER_CHUNK.get();
        return max <= 0 || machinesInChunk(level, pos) - (alreadyPlaced ? 1 : 0) < max;
    }

    /** Refuses a machine placed by a player in a chunk that already holds the configured most. */
    private static boolean onPlace(BlockEvent.EntityPlaceEvent event) {
        if (probing || !(event.getPlacedBlock().getBlock() instanceof MachineBlock) || !(event.getLevel() instanceof ServerLevel level)) {
            return false;
        }
        if (machineFits(level, event.getPos(), true)) {
            return false;
        }
        if (event.getEntity() instanceof Player player) {
            player.sendOverlayMessage(Component.translatable("message.brasshaven.machine.chunk_full",
                    BrasshavenConfig.MACHINES_PER_CHUNK.get()).withStyle(ChatFormatting.RED));
        }
        return true;
    }
}
