package com.wayfarers.map;

import com.mojang.logging.LogUtils;
import com.wayfarers.config.WayfarersConfig;
import com.wayfarers.data.WayfarersData;
import com.wayfarers.network.MapActionMsg;
import com.wayfarers.network.MapDataMsg;
import com.wayfarers.network.WayfarersNet;
import it.unimi.dsi.fastutil.longs.Long2LongOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongArrayList;
import it.unimi.dsi.fastutil.longs.LongLinkedOpenHashSet;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.level.ChunkWatchEvent;
import net.minecraftforge.event.level.LevelEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import org.slf4j.Logger;

import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * The server side of the world map: one shared map per dimension, built from the chunks players load, plus
 * server-kept waypoints and live pings.
 *
 * <h2>How it stays cheap</h2>
 * Chunks are only scanned when a player is sent them (or stands in them, to catch building), at most once every few
 * minutes each, from a bounded queue with a time budget of about a millisecond per tick. Regions are read, encoded
 * and written on one background thread; the server thread only copies arrays. Each player has an outgoing byte
 * budget, so a client opening the world map never floods the connection.
 *
 * <h2>Protocol</h2>
 * Client to server ({@link MapActionMsg}): {@code REQUEST} [dimension, (rx, rz, full|thumbnail, known revision)...]
 * for the regions on screen, sent again every ~15 s while they stay on screen; {@code WAYPOINT_ADD / EDIT / DELETE};
 * {@code PING} [dimension, x, y, z]. Server to client ({@link MapDataMsg}): {@code TILE} / {@code MINI} (a region or
 * its 64 x 64 thumbnail, deflated {@link RegionData}, only when newer than the client's revision), {@code CHUNK}
 * (a freshly scanned chunk, pushed to clients that asked for its region in the last 40 s), {@code POINTS} (waypoints
 * the player may see + every waystone, on login and on change), {@code PLAYERS} (positions in the dimension, once
 * a second) and {@code PING}.
 */
public final class MapServer {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final long BUDGET_NS = 1_000_000L;
    private static final int MAX_SCANS_PER_TICK = 24;
    private static final int MAX_QUEUE = 16384;
    private static final long RESCAN_TICKS = 6000;
    private static final long NEAR_RESCAN_TICKS = 400;
    private static final long SUBSCRIPTION_MS = 40_000;
    /** Server-thread time per tick for copying the regions players asked for (all players together). */
    private static final long REQUEST_BUDGET_NS = 2_000_000L;
    private static final long MAX_OUTBOX_BYTES = 1_500_000L;
    /** Regions farther than the world border (30 million blocks) are never asked for by an honest client. */
    private static final int MAX_REGION_COORD = 30_000_000 / RegionData.REGION + 2;

    private static ExecutorService worker;
    private static MinecraftServer server;
    private static Path root;
    private static final Map<String, MapStore> STORES = new HashMap<>();
    private static final Map<String, ServerLevel> LEVELS = new HashMap<>();
    private static final Map<String, LongLinkedOpenHashSet> QUEUES = new HashMap<>();
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final ConcurrentLinkedQueue<Runnable> COMPLETED = new ConcurrentLinkedQueue<>();
    private static final MapScan SCAN = new MapScan();
    private static MapWaypoints waypoints;
    private static MapExplorers explorers;
    private static int waystoneHash;

    private MapServer() {}

    /** Per-player state: pending region requests, subscriptions and the outgoing queue. */
    private static final class Session {
        final UUID id;
        final ArrayDeque<Object[]> requests = new ArrayDeque<>();
        final Map<String, Long2LongOpenHashMap> subs = new HashMap<>();
        final ArrayDeque<MapDataMsg> outbox = new ArrayDeque<>();
        /** Bytes waiting in {@link #outbox}: no new region is prepared while the connection is this far behind. */
        long outboxBytes;
        long budget;
        int inFlight;
        long lastPing;
        /** Server tick at which the waypoints are sent once more after login (the first copy can arrive before the
         * client has its world); -1 when done. */
        int resendPointsAt = -1;

        Session(UUID id) {
            this.id = id;
        }

        boolean subscribed(String dim, long region, long now) {
            Long2LongOpenHashMap m = subs.get(dim);
            return m != null && m.get(region) > now;
        }

        void queue(MapDataMsg msg) {
            if (outbox.size() >= 512) {
                // the client re-asks for its regions every few seconds and will get the newer revision then
                outboxBytes -= outbox.pollFirst().data().length;
            }
            outbox.addLast(msg);
            outboxBytes += msg.data().length;
        }

        MapDataMsg poll() {
            MapDataMsg msg = outbox.pollFirst();
            outboxBytes -= msg.data().length;
            return msg;
        }
    }

    public static void register() {
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick(e.server()));
        ChunkWatchEvent.Watch.BUS.addListener(MapServer::onWatch);
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                start(p.level().getServer());
                Session session = new Session(p.getUUID());
                session.resendPointsAt = server.getTickCount() + 60;
                SESSIONS.put(p.getUUID(), session);
                explorers.get(p.getUUID());
                sendPoints(p);
                com.wayfarers.util.Tips.show(p, "map");
            }
        });
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> {
            if (server != null) {
                SESSIONS.remove(e.getEntity().getUUID());
                explorers.save(e.getEntity().getUUID(), true);
            }
        });
        LevelEvent.Save.BUS.addListener(e -> {
            if (server != null && e.getLevel() instanceof ServerLevel level) {
                MapStore store = STORES.get(dimId(level));
                if (store != null) {
                    store.save(true, 300_000);
                }
                if (level.dimension() == net.minecraft.world.level.Level.OVERWORLD) {
                    waypoints.save();
                    explorers.save(null, false);
                }
            }
        });
        ServerStoppingEvent.BUS.addListener(e -> stop());
    }

    static synchronized ExecutorService worker() {
        if (worker == null || worker.isShutdown()) {
            worker = Executors.newSingleThreadExecutor(r -> {
                Thread t = new Thread(r, "Wayfarers map worker");
                t.setDaemon(true);
                t.setPriority(Thread.NORM_PRIORITY - 1);
                return t;
            });
        }
        return worker;
    }

    private static void start(MinecraftServer s) {
        if (server == s) {
            return;
        }
        stop();
        server = s;
        root = s.getWorldPath(LevelResource.ROOT).resolve("data").resolve("wayfarers_map");
        waypoints = new MapWaypoints(root.resolve("waypoints.json"));
        explorers = new MapExplorers(root.resolve("explored"));
        waystoneHash = 0;
    }

    private static void stop() {
        if (server == null) {
            return;
        }
        for (MapStore store : STORES.values()) {
            store.save(false, 0);
        }
        waypoints.save();
        explorers.save(null, false);
        try {
            worker().submit(() -> { }).get(15, TimeUnit.SECONDS);
        } catch (Exception e) {
            LOGGER.warn("Wayfarers map: saving took too long: {}", e.toString());
        }
        STORES.clear();
        LEVELS.clear();
        QUEUES.clear();
        SESSIONS.clear();
        COMPLETED.clear();
        SCAN.clearCache();
        server = null;
    }

    static String dimId(ServerLevel level) {
        return level.dimension().identifier().toString();
    }

    private static MapStore store(String dim) {
        return STORES.computeIfAbsent(dim, d -> new MapStore(d, root.resolve(d.replace(':', '_'))));
    }

    private static ServerLevel level(String dim) {
        ServerLevel l = LEVELS.get(dim);
        if (l == null && server != null) {
            for (ServerLevel level : server.getAllLevels()) {
                LEVELS.put(dimId(level), level);
            }
            l = LEVELS.get(dim);
        }
        return l;
    }

    private static boolean shared() {
        return WayfarersConfig.MAP_SHARED.get();
    }

    // ------------------------------------------------------------------ exploration
    private static void onWatch(ChunkWatchEvent.Watch e) {
        start(e.getLevel().getServer());
        String dim = dimId(e.getLevel());
        int cx = e.getPos().x();
        int cz = e.getPos().z();
        boolean fresh = explorers.get(e.getPlayer().getUUID()).mark(dim, cx, cz);
        if (fresh && !shared()) {
            // this chunk just became visible to the player: send it if they are looking at its region
            Session s = SESSIONS.get(e.getPlayer().getUUID());
            MapStore.Region r = store(dim).region(RegionData.key(cx >> 4, cz >> 4));
            if (s != null && r != null && r.ready() && s.subscribed(dim, r.key, System.currentTimeMillis())) {
                s.queue(chunkMsg(dim, r, cx, cz, revisionFor(s, dim, r)));
            }
        }
        enqueue(dim, cx, cz, RESCAN_TICKS);
    }

    private static void enqueue(String dim, int cx, int cz, long maxAge) {
        MapStore store = store(dim);
        MapStore.Region r = store.region(RegionData.key(cx >> 4, cz >> 4));
        if (r != null && r.ready()) {
            long at = r.scannedAt[((cz & 15) << 4) | (cx & 15)];
            if (at != 0 && server.getTickCount() - at < maxAge) {
                return;
            }
        }
        LongLinkedOpenHashSet q = QUEUES.computeIfAbsent(dim, d -> new LongLinkedOpenHashSet());
        if (q.size() < MAX_QUEUE) {
            q.add(ChunkPos.pack(cx, cz));
        }
    }

    private static void scanSome() {
        long start = System.nanoTime();
        int done = 0;
        LongArrayList ready = new LongArrayList();
        for (Map.Entry<String, MapStore> e : STORES.entrySet()) {
            ready.clear();
            e.getValue().pollLoads(ready);
            if (!ready.isEmpty()) {
                LongLinkedOpenHashSet q = QUEUES.computeIfAbsent(e.getKey(), d -> new LongLinkedOpenHashSet());
                for (long c : ready) {
                    q.addAndMoveToFirst(c);
                }
            }
        }
        for (Map.Entry<String, LongLinkedOpenHashSet> e : QUEUES.entrySet()) {
            String dim = e.getKey();
            LongLinkedOpenHashSet q = e.getValue();
            ServerLevel level = level(dim);
            if (level == null) {
                q.clear();
                continue;
            }
            MapStore store = store(dim);
            int mode = level.dimensionType().hasCeiling() ? MapScan.ROOF : MapScan.SURFACE;
            while (!q.isEmpty() && done < MAX_SCANS_PER_TICK && System.nanoTime() - start < BUDGET_NS) {
                long c = q.removeFirstLong();
                int cx = ChunkPos.getX(c);
                int cz = ChunkPos.getZ(c);
                LevelChunk chunk = level.getChunkSource().getChunkNow(cx, cz);
                if (chunk == null) {
                    continue;
                }
                long rk = RegionData.key(cx >> 4, cz >> 4);
                if (store.ensure(rk, true) != MapStore.State.READY) {
                    MapStore.Region r = store.region(rk);
                    if (r != null) {
                        if (r.waiting == null) {
                            r.waiting = new LongArrayList();
                        }
                        if (r.waiting.size() < 256) {
                            r.waiting.add(c);
                        }
                    }
                    continue;
                }
                MapStore.Region r = store.region(rk);
                done++;
                r.scannedAt[((cz & 15) << 4) | (cx & 15)] = server.getTickCount();
                if (SCAN.scan(level, chunk, r.data, (cx >> 4) << 8, (cz >> 4) << 8, mode)) {
                    r.data.revision++;
                    r.dirty = true;
                    pushChunk(dim, r, cx, cz);
                }
            }
        }
    }

    private static MapDataMsg chunkMsg(String dim, MapStore.Region r, int cx, int cz, int revision) {
        RegionData chunk = r.data.sample((cx & 15) << 4, (cz & 15) << 4, 16, 1, null);
        chunk.revision = revision;
        return new MapDataMsg(MapDataMsg.CHUNK, dim, cx, cz, chunk.encodeAll());
    }

    /**
     * The revision of a region as one player sees it. Shared: the region's own. Per player, the chunks they saw
     * count too (the region's data does not change when a second player walks into chunks already mapped, yet their
     * map must update): both only ever grow, so "newer than N" keeps working.
     */
    private static int revisionFor(Session s, String dim, MapStore.Region r) {
        if (shared()) {
            return r.data.revision;
        }
        long[] mask = explorers.get(s.id).mask(dim, r.key);
        int seen = 0;
        if (mask != null) {
            for (long m : mask) {
                seen += Long.bitCount(m);
            }
        }
        return r.data.revision + seen;
    }

    /** Sends a freshly changed chunk to the players looking at its region. */
    private static void pushChunk(String dim, MapStore.Region r, int cx, int cz) {
        long now = System.currentTimeMillis();
        MapDataMsg msg = null;
        boolean shared = shared();
        for (Session s : SESSIONS.values()) {
            if (!s.subscribed(dim, r.key, now) || !shared && !explorers.get(s.id).has(dim, cx, cz)) {
                continue;
            }
            if (!shared) {
                s.queue(chunkMsg(dim, r, cx, cz, revisionFor(s, dim, r)));
                continue;
            }
            if (msg == null) {
                msg = chunkMsg(dim, r, cx, cz, r.data.revision);
            }
            s.queue(msg);
        }
    }

    // ------------------------------------------------------------------ requests
    private static void handleRequests(ServerPlayer player, Session s, long deadline) {
        long now = System.currentTimeMillis();
        int handled = 0;
        boolean shared = shared();
        while (!s.requests.isEmpty() && handled < 6 && s.inFlight < 3 && s.outboxBytes < MAX_OUTBOX_BYTES
                && System.nanoTime() < deadline) {
            Object[] q = s.requests.pollFirst();
            String dim = (String) q[0];
            MapProtocol.Request req = (MapProtocol.Request) q[1];
            int tries = (Integer) q[2];
            if (level(dim) == null || Math.abs(req.rx()) > MAX_REGION_COORD || Math.abs(req.rz()) > MAX_REGION_COORD) {
                continue;
            }
            MapStore store = store(dim);
            long rk = RegionData.key(req.rx(), req.rz());
            if (req.full()) {
                Long2LongOpenHashMap subs = s.subs.computeIfAbsent(dim, d -> new Long2LongOpenHashMap());
                subs.put(rk, now + SUBSCRIPTION_MS);
            }
            handled++;
            MapStore.State st = store.ensure(rk, false);
            if (st == MapStore.State.MISSING) {
                continue;
            }
            if (st == MapStore.State.LOADING) {
                if (tries < 200) {
                    s.requests.addLast(new Object[] {dim, req, tries + 1});
                }
                continue;
            }
            MapStore.Region r = store.region(rk);
            int rev = r.data.revision;
            int seenRev = shared ? rev : revisionFor(s, dim, r);
            if (req.knownRevision() > 0 && seenRev <= req.knownRevision()) {
                continue;
            }
            int kind = req.full() ? MapDataMsg.TILE : MapDataMsg.MINI;
            if (shared) {
                byte[] cached = req.full() ? (r.fullCacheRev == rev ? r.fullCache : null) : (r.miniCacheRev == rev ? r.miniCache : null);
                if (cached != null) {
                    s.queue(new MapDataMsg(kind, dim, req.rx(), req.rz(), cached));
                    continue;
                }
            }
            long[] mask = shared ? null : explorers.get(s.id).mask(dim, rk);
            if (!shared && mask == null) {
                continue;
            }
            RegionData.Visible visible = shared ? null : (x, z) -> MapExplorers.visible(mask, x, z);
            RegionData sample = req.full() ? r.data.sample(0, 0, RegionData.REGION, 1, visible)
                    : r.data.sample(1, 1, RegionData.MINI, 4, visible);
            sample.revision = seenRev;
            s.inFlight++;
            worker().execute(() -> {
                byte[] bytes;
                try {
                    bytes = sample.encodeAll();
                } catch (RuntimeException ex) {
                    // never leave the session waiting for an answer that will not come
                    LOGGER.warn("Wayfarers map: could not encode a region: {}", ex.toString());
                    COMPLETED.add(() -> s.inFlight--);
                    return;
                }
                COMPLETED.add(() -> {
                    s.inFlight--;
                    if (shared && r.data != null && r.data.revision == rev) {
                        if (req.full()) {
                            r.fullCache = bytes;
                            r.fullCacheRev = rev;
                        } else {
                            r.miniCache = bytes;
                            r.miniCacheRev = rev;
                        }
                    }
                    s.queue(new MapDataMsg(kind, dim, req.rx(), req.rz(), bytes));
                });
            });
        }
    }

    // ------------------------------------------------------------------ tick
    private static void tick(MinecraftServer s) {
        if (server != s) {
            if (s.getPlayerList().getPlayers().isEmpty()) {
                return;
            }
            start(s);
        }
        Runnable done;
        while ((done = COMPLETED.poll()) != null) {
            done.run();
        }
        int tick = s.getTickCount();
        List<ServerPlayer> players = s.getPlayerList().getPlayers();
        // chunks the players stand in: rescanned every 20 s so building shows up
        if (tick % 40 == 0) {
            for (ServerPlayer p : players) {
                String dim = dimId(p.level());
                int pcx = p.blockPosition().getX() >> 4;
                int pcz = p.blockPosition().getZ() >> 4;
                for (int dz = -1; dz <= 1; dz++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        enqueue(dim, pcx + dx, pcz + dz, NEAR_RESCAN_TICKS);
                    }
                }
            }
        }
        scanSome();
        long perTick = s.isDedicatedServer() ? 12_000 : 96_000;
        long deadline = System.nanoTime() + REQUEST_BUDGET_NS;
        // a different player goes first each tick, so the time budget is shared fairly
        int first = players.isEmpty() ? 0 : tick % players.size();
        for (int pi = 0; pi < players.size(); pi++) {
            ServerPlayer p = players.get((first + pi) % players.size());
            Session ss = SESSIONS.get(p.getUUID());
            if (ss == null) {
                continue;
            }
            if (ss.resendPointsAt >= 0 && tick >= ss.resendPointsAt) {
                ss.resendPointsAt = -1;
                sendPoints(p);
            }
            handleRequests(p, ss, deadline);
            ss.budget = Math.min(ss.budget + perTick, perTick * 40);
            while (!ss.outbox.isEmpty() && ss.budget > 0) {
                MapDataMsg msg = ss.poll();
                ss.budget -= msg.data().length + 48;
                WayfarersNet.toPlayer(p, msg);
            }
        }
        if (tick % 20 == 0) {
            sendPlayers(players);
        }
        if (tick % 100 == 0) {
            int h = waystoneHash(s);
            if (h != waystoneHash) {
                waystoneHash = h;
                for (ServerPlayer p : players) {
                    sendPoints(p);
                }
            }
        }
        if (tick % 1200 == 0) {
            long now = System.currentTimeMillis();
            for (Session ss : SESSIONS.values()) {
                for (Long2LongOpenHashMap m : ss.subs.values()) {
                    m.long2LongEntrySet().removeIf(en -> en.getLongValue() < now);
                }
            }
        }
        // memory bound: a player scrolling a zoomed-out world map can load many regions within a minute
        if (tick % 100 == 0) {
            for (Map.Entry<String, MapStore> e : STORES.entrySet()) {
                LongOpenHashSet keep = new LongOpenHashSet();
                for (ServerPlayer p : players) {
                    if (dimId(p.level()).equals(e.getKey())) {
                        int rx = p.blockPosition().getX() >> 8;
                        int rz = p.blockPosition().getZ() >> 8;
                        for (int dz = -1; dz <= 1; dz++) {
                            for (int dx = -1; dx <= 1; dx++) {
                                keep.add(RegionData.key(rx + dx, rz + dz));
                            }
                        }
                    }
                }
                e.getValue().evict(keep);
            }
        }
    }

    private static void sendPlayers(List<ServerPlayer> players) {
        if (players.size() < 2 || !WayfarersConfig.MAP_PLAYERS.get()) {
            return;
        }
        Map<String, List<MapProtocol.PlayerPos>> byDim = new HashMap<>();
        for (ServerPlayer p : players) {
            if (!p.isSpectator()) {
                byDim.computeIfAbsent(dimId(p.level()), d -> new ArrayList<>()).add(new MapProtocol.PlayerPos(
                        p.getName().getString(), p.getBlockX(), p.getBlockY(), p.getBlockZ(), p.getYRot()));
            }
        }
        Map<String, MapDataMsg> msgs = new HashMap<>();
        for (ServerPlayer p : players) {
            String dim = dimId(p.level());
            List<MapProtocol.PlayerPos> list = byDim.get(dim);
            if (list == null || list.size() < 2 && list.getFirst().name().equals(p.getName().getString())) {
                continue;
            }
            WayfarersNet.toPlayer(p, msgs.computeIfAbsent(dim, d -> new MapDataMsg(MapDataMsg.PLAYERS, d, 0, 0,
                    MapProtocol.players(list))));
        }
    }

    // ------------------------------------------------------------------ points
    private static int waystoneHash(MinecraftServer s) {
        int h = 1;
        for (Map.Entry<String, WayfarersData.Waystone> e : WayfarersData.get(s).sortedWaystones()) {
            h = 31 * h + Objects.hash(e.getKey(), e.getValue().name(), e.getValue().dimension(), e.getValue().pos());
        }
        return h == 0 ? 1 : h;
    }

    private static void sendPoints(ServerPlayer p) {
        List<MapProtocol.Waystone> stones = new ArrayList<>();
        for (Map.Entry<String, WayfarersData.Waystone> e : WayfarersData.get(server).sortedWaystones()) {
            WayfarersData.Waystone w = e.getValue();
            stones.add(new MapProtocol.Waystone(e.getKey(), w.name(), w.dimension().toString(), w.pos().getX(), w.pos().getY(),
                    w.pos().getZ()));
        }
        WayfarersNet.toPlayer(p, new MapDataMsg(MapDataMsg.POINTS, "", 0, 0,
                MapProtocol.points(waypoints.visibleTo(p.getUUID()), stones)));
    }

    private static void syncPoints(ServerPlayer owner, boolean everyone) {
        if (everyone) {
            for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                sendPoints(p);
            }
        } else {
            sendPoints(owner);
        }
    }

    private static boolean isOp(ServerPlayer p) {
        return p.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER);
    }

    // ------------------------------------------------------------------ client actions
    public static void handle(ServerPlayer player, MapActionMsg msg) {
        start(player.level().getServer());
        Session s = SESSIONS.computeIfAbsent(player.getUUID(), Session::new);
        switch (msg.kind()) {
            case MapActionMsg.REQUEST -> {
                Object[] r = MapProtocol.readRequests(msg.data());
                if (r == null) {
                    return;
                }
                @SuppressWarnings("unchecked")
                List<MapProtocol.Request> list = (List<MapProtocol.Request>) r[1];
                for (MapProtocol.Request req : list) {
                    if (s.requests.size() < 160) {
                        s.requests.addLast(new Object[] {r[0], req, 0});
                    }
                }
            }
            case MapActionMsg.WAYPOINT_ADD -> {
                MapProtocol.Waypoint w = MapProtocol.read(msg.data(), in -> new MapProtocol.Waypoint(UUID.randomUUID().toString(),
                        player.getUUID().toString(), player.getName().getString(), MapProtocol.clean(in.readUTF()), in.readUTF(),
                        in.readInt(), in.readInt(), in.readInt(), in.readInt() & 0xFFFFFF,
                        Math.floorMod(in.readByte(), MapProtocol.ICONS.length), in.readBoolean()));
                if (w == null || w.name().isEmpty() || w.dim().length() > 64 || level(w.dim()) == null || Math.abs(w.x()) > 30_000_000
                        || Math.abs(w.z()) > 30_000_000 || Math.abs(w.y()) > 4096) {
                    return;
                }
                if (!waypoints.add(w)) {
                    player.sendSystemMessage(Component.translatable("message.wayfarers.map.too_many", MapWaypoints.MAX_PER_PLAYER)
                            .withStyle(ChatFormatting.RED));
                    return;
                }
                waypoints.save();
                syncPoints(player, w.shared());
            }
            case MapActionMsg.WAYPOINT_EDIT -> {
                Object[] e = MapProtocol.read(msg.data(), in -> new Object[] {in.readUTF(), MapProtocol.clean(in.readUTF()),
                        in.readInt() & 0xFFFFFF, Math.floorMod(in.readByte(), MapProtocol.ICONS.length), in.readBoolean()});
                MapProtocol.Waypoint old = e == null ? null : waypoints.get((String) e[0]);
                if (old == null || ((String) e[1]).isEmpty() || !old.owner().equals(player.getUUID().toString()) && !isOp(player)) {
                    return;
                }
                MapProtocol.Waypoint w = new MapProtocol.Waypoint(old.id(), old.owner(), old.ownerName(), (String) e[1], old.dim(),
                        old.x(), old.y(), old.z(), (Integer) e[2], (Integer) e[3], (Boolean) e[4]);
                waypoints.replace(old, w);
                waypoints.save();
                syncPoints(player, old.shared() || w.shared() || !old.owner().equals(player.getUUID().toString()));
            }
            case MapActionMsg.WAYPOINT_DELETE -> {
                String id = MapProtocol.read(msg.data(), in -> in.readUTF());
                MapProtocol.Waypoint old = id == null ? null : waypoints.get(id);
                if (old == null || !old.owner().equals(player.getUUID().toString()) && !isOp(player)) {
                    return;
                }
                waypoints.remove(old);
                waypoints.save();
                syncPoints(player, old.shared() || !old.owner().equals(player.getUUID().toString()));
            }
            case MapActionMsg.PING -> {
                Object[] p = MapProtocol.read(msg.data(), in -> new Object[] {in.readUTF(), in.readInt(), in.readInt(), in.readInt()});
                long now = System.currentTimeMillis();
                if (p == null || now - s.lastPing < 3000 || level((String) p[0]) == null) {
                    return;
                }
                s.lastPing = now;
                int x = Math.clamp((Integer) p[1], -30_000_000, 30_000_000);
                int y = Math.clamp((Integer) p[2], -4096, 4096);
                int z = Math.clamp((Integer) p[3], -30_000_000, 30_000_000);
                String dim = (String) p[0];
                String name = player.getName().getString();
                MapDataMsg out = new MapDataMsg(MapDataMsg.PING, dim, x, z, MapProtocol.bytes(o -> {
                    o.writeUTF(name);
                    o.writeInt(y);
                }));
                // only where the ping can be seen: the players of that dimension
                Component chat = Component.translatable("message.wayfarers.map.ping", player.getDisplayName(), x, z)
                        .withStyle(ChatFormatting.AQUA);
                for (ServerPlayer other : server.getPlayerList().getPlayers()) {
                    if (dimId(other.level()).equals(dim)) {
                        WayfarersNet.toPlayer(other, out);
                        other.sendSystemMessage(chat);
                    }
                }
            }
            default -> { }
        }
    }
}
