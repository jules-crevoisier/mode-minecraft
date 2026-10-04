package com.wayfarers.client.map;

import com.mojang.logging.LogUtils;
import com.wayfarers.config.WayfarersClientConfig;
import com.wayfarers.map.MapProtocol;
import com.wayfarers.map.MapScan;
import com.wayfarers.map.RegionData;
import com.wayfarers.network.MapActionMsg;
import com.wayfarers.network.MapDataMsg;
import com.wayfarers.network.WayfarersNet;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongArrayFIFOQueue;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.LevelResource;
import org.slf4j.Logger;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Client state of the maps: the regions received from the server (one layer per dimension), the live cave view
 * scanned from the chunks around the player, the points to show (waypoints, waystones, players, pings, plus what
 * this client noticed: its graves, structures found with a compass) and the requests for regions on screen.
 */
public final class ClientMap {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final long PING_MS = 60_000;

    /** What a marker is; also the legend entries and filters of the world map. */
    public enum Kind { PLAYER, WAYPOINT, WAYSTONE, PING, TARGET, STRUCTURE, GRAVE, DEATH, SPAWN }

    /** One thing to draw on a map. {@code ref}: the waypoint or waystone behind it, if any. */
    public record Marker(Kind kind, double x, double y, double z, int color, String label, String detail, Object ref,
                         float yaw) {}

    public record Ping(String dim, int x, int y, int z, String name, long until) {}

    private static ExecutorService io;
    private static final Map<String, MapLayer> LAYERS = new HashMap<>();
    private static MapLayer cave;
    private static ClientLevel level;
    private static String dim = "";
    private static String worldId;
    private static MapPoints local;

    private static List<MapProtocol.Waypoint> waypoints = List.of();
    private static List<MapProtocol.Waystone> waystones = List.of();
    private static List<MapProtocol.PlayerPos> players = List.of();
    private static String playersDim = "";
    private static long playersAt;
    private static final List<Ping> PINGS = new ArrayList<>();
    /** Legend filters (world map): hidden kinds. */
    public static final boolean[] HIDDEN = new boolean[Kind.values().length];

    // requests
    private static final LongOpenHashSet WANT_FULL = new LongOpenHashSet();
    private static final LongOpenHashSet WANT_MINI = new LongOpenHashSet();

    // cave view
    private static boolean caveActive;
    private static int caveVotes;
    private static int sliceY;
    private static int scannedSlice = Integer.MIN_VALUE;
    private static final Long2ObjectOpenHashMap<LevelChunk> SEEN = new Long2ObjectOpenHashMap<>();
    private static final LongArrayFIFOQueue QUEUE = new LongArrayFIFOQueue();
    private static final LongOpenHashSet QUEUED = new LongOpenHashSet();
    private static final MapScan SCAN = new MapScan();
    private static int tick;

    private ClientMap() {}

    static synchronized ExecutorService io() {
        if (io == null) {
            io = Executors.newSingleThreadExecutor(r -> {
                Thread t = new Thread(r, "Wayfarers map client IO");
                t.setDaemon(true);
                return t;
            });
        }
        return io;
    }

    // ------------------------------------------------------------------ accessors for the renderers
    public static String dimension() {
        return dim;
    }

    static MapLayer layer() {
        return level == null ? null : LAYERS.computeIfAbsent(dim, d -> new MapLayer(d, false));
    }

    /** The live cave view when it is on, else null. */
    static MapLayer cave() {
        return caveActive ? cave : null;
    }

    public static boolean caveActive() {
        return caveActive;
    }

    /** Asks for a region the renderer wants to draw ({@code full}: at full resolution, else its thumbnail). */
    static void want(int rx, int rz, boolean full) {
        (full ? WANT_FULL : WANT_MINI).add(RegionData.key(rx, rz));
    }

    public static List<MapProtocol.Waypoint> waypoints() {
        return waypoints;
    }

    public static boolean mine(MapProtocol.Waypoint w) {
        LocalPlayer p = Minecraft.getInstance().player;
        return p != null && w.owner().equals(p.getUUID().toString());
    }

    // ------------------------------------------------------------------ lifecycle
    private static String worldId(Minecraft mc) {
        String raw;
        IntegratedServer sp = mc.getSingleplayerServer();
        ServerData sd = mc.getCurrentServer();
        if (sp != null) {
            Path p = sp.getWorldPath(LevelResource.ROOT).toAbsolutePath().normalize().getFileName();
            raw = "sp_" + (p == null ? "world" : p.toString());
        } else if (sd != null) {
            raw = "mp_" + sd.ip;
        } else {
            raw = "unknown";
        }
        return raw.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9._-]", "_");
    }

    private static void reset() {
        for (MapLayer l : LAYERS.values()) {
            l.clear();
        }
        LAYERS.clear();
        if (cave != null) {
            cave.clear();
            cave = null;
        }
        SEEN.clear();
        QUEUE.clear();
        QUEUED.clear();
        caveActive = false;
        waypoints = List.of();
        waystones = List.of();
        players = List.of();
        PINGS.clear();
        WANT_FULL.clear();
        WANT_MINI.clear();
        MapPalette.reset();
        local = null;
        worldId = null;
        level = null;
        dim = "";
    }

    public static void onLogout() {
        reset();
    }

    public static void tick() {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel lvl = mc.level;
        LocalPlayer player = mc.player;
        if (lvl == null || player == null) {
            if (level != null) {
                reset();
            }
            return;
        }
        if (lvl != level) {
            String id = worldId(mc);
            if (!id.equals(worldId)) {
                reset();
                worldId = id;
                local = new MapPoints(mc.gameDirectory.toPath().resolve("wayfarers").resolve("maps").resolve(id).resolve("points.json"));
            }
            level = lvl;
            dim = lvl.dimension().identifier().toString();
            if (cave != null) {
                cave.clear();
            }
            cave = new MapLayer(dim, true);
            SEEN.clear();
            QUEUE.clear();
            QUEUED.clear();
            caveActive = false;
            caveVotes = 0;
            MapPalette.reset();
        }
        tick++;
        updateCaveMode(lvl, player);
        if (caveActive) {
            scanCaves(lvl, player);
        }
        if (tick % 5 == 0) {
            sendRequests(player);
        }
        if (tick % 40 == 0) {
            int prx = player.getBlockX() >> MapTile.SHIFT;
            int prz = player.getBlockZ() >> MapTile.SHIFT;
            for (MapLayer l : LAYERS.values()) {
                l.evict(prx, prz);
            }
            if (cave != null) {
                cave.evict(prx, prz);
            }
            long now = System.currentTimeMillis();
            PINGS.removeIf(p -> p.until() < now);
            checkGraves(lvl, player);
        }
    }

    // ------------------------------------------------------------------ requests
    private static void sendRequests(LocalPlayer player) {
        MapLayer l = layer();
        if (l == null || WANT_FULL.isEmpty() && WANT_MINI.isEmpty()) {
            return;
        }
        long now = System.currentTimeMillis();
        List<MapProtocol.Request> out = new ArrayList<>();
        int prx = player.getBlockX() >> MapTile.SHIFT;
        int prz = player.getBlockZ() >> MapTile.SHIFT;
        List<Long> full = new ArrayList<>(WANT_FULL);
        full.sort((a, b) -> Integer.compare(dist(a, prx, prz), dist(b, prx, prz)));
        for (long k : full) {
            MapTile t = l.tile(RegionData.keyX(k), RegionData.keyZ(k));
            long wait = t.full == null ? (t.fullAsked == 0 ? 0 : 8000) : 15000;
            if (now - t.fullAsked >= wait && out.size() < 48) {
                t.fullAsked = now;
                out.add(new MapProtocol.Request(t.rx, t.rz, true, t.full == null ? 0 : t.fullRev));
            }
        }
        for (long k : WANT_MINI) {
            MapTile t = l.tile(RegionData.keyX(k), RegionData.keyZ(k));
            if (t.full != null) {
                continue;
            }
            long wait = t.mini == null ? (t.miniAsked == 0 ? 0 : 10000) : 30000;
            if (now - t.miniAsked >= wait && out.size() < 64) {
                t.miniAsked = now;
                out.add(new MapProtocol.Request(t.rx, t.rz, false, t.mini == null ? 0 : t.miniRev));
            }
        }
        WANT_FULL.clear();
        WANT_MINI.clear();
        if (!out.isEmpty()) {
            WayfarersNet.toServer(new MapActionMsg(MapActionMsg.REQUEST, MapProtocol.requests(dim, out)));
        }
    }

    private static int dist(long k, int rx, int rz) {
        return Math.abs(RegionData.keyX(k) - rx) + Math.abs(RegionData.keyZ(k) - rz);
    }

    // ------------------------------------------------------------------ data from the server
    public static void receive(MapDataMsg msg) {
        if (level == null) {
            return;
        }
        switch (msg.kind()) {
            case MapDataMsg.TILE, MapDataMsg.MINI, MapDataMsg.CHUNK -> {
                RegionData d = RegionData.decode(msg.data());
                if (d == null) {
                    return;
                }
                MapLayer l = LAYERS.computeIfAbsent(msg.dim(), x -> new MapLayer(x, false));
                if (msg.kind() == MapDataMsg.TILE) {
                    l.receiveFull(msg.a(), msg.b(), d);
                } else if (msg.kind() == MapDataMsg.MINI) {
                    l.receiveMini(msg.a(), msg.b(), d);
                } else {
                    l.receiveChunk(msg.a(), msg.b(), d);
                }
            }
            case MapDataMsg.POINTS -> {
                Object[] p = MapProtocol.readPoints(msg.data());
                if (p != null) {
                    @SuppressWarnings("unchecked")
                    List<MapProtocol.Waypoint> w = (List<MapProtocol.Waypoint>) p[0];
                    @SuppressWarnings("unchecked")
                    List<MapProtocol.Waystone> s = (List<MapProtocol.Waystone>) p[1];
                    waypoints = Collections.unmodifiableList(w);
                    waystones = Collections.unmodifiableList(s);
                }
            }
            case MapDataMsg.PLAYERS -> {
                List<MapProtocol.PlayerPos> list = MapProtocol.readPlayers(msg.data());
                if (list != null) {
                    players = list;
                    playersDim = msg.dim();
                    playersAt = System.currentTimeMillis();
                }
            }
            case MapDataMsg.PING -> {
                Object[] p = MapProtocol.read(msg.data(), in -> new Object[] {in.readUTF(), in.readInt()});
                if (p != null) {
                    PINGS.removeIf(o -> o.name().equals(p[0]));
                    PINGS.add(new Ping(msg.dim(), msg.a(), (Integer) p[1], msg.b(), (String) p[0], System.currentTimeMillis() + PING_MS));
                    Minecraft.getInstance().getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.NOTE_BLOCK_BELL.value(), 1.5F, 0.6F));
                }
            }
            default -> { }
        }
    }

    // ------------------------------------------------------------------ actions (sent to the server)
    public static void addWaypoint(String name, int x, int y, int z, int color, int icon, boolean shared) {
        String d = dim;
        WayfarersNet.toServer(new MapActionMsg(MapActionMsg.WAYPOINT_ADD, MapProtocol.bytes(out -> {
            out.writeUTF(MapProtocol.clean(name));
            out.writeUTF(d);
            out.writeInt(x);
            out.writeInt(y);
            out.writeInt(z);
            out.writeInt(color);
            out.writeByte(icon);
            out.writeBoolean(shared);
        })));
    }

    public static void editWaypoint(MapProtocol.Waypoint w, String name, int color, int icon, boolean shared) {
        WayfarersNet.toServer(new MapActionMsg(MapActionMsg.WAYPOINT_EDIT, MapProtocol.bytes(out -> {
            out.writeUTF(w.id());
            out.writeUTF(MapProtocol.clean(name));
            out.writeInt(color);
            out.writeByte(icon);
            out.writeBoolean(shared);
        })));
    }

    public static void deleteWaypoint(MapProtocol.Waypoint w) {
        WayfarersNet.toServer(new MapActionMsg(MapActionMsg.WAYPOINT_DELETE, MapProtocol.bytes(out -> out.writeUTF(w.id()))));
    }

    public static void ping(int x, int y, int z) {
        String d = dim;
        WayfarersNet.toServer(new MapActionMsg(MapActionMsg.PING, MapProtocol.bytes(out -> {
            out.writeUTF(d);
            out.writeInt(x);
            out.writeInt(y);
            out.writeInt(z);
        })));
    }

    /** Ping key: the block you look at (up to 256 blocks away), or your own position. */
    public static void pingLook() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.getCameraEntity() == null) {
            return;
        }
        net.minecraft.world.phys.HitResult hit = mc.getCameraEntity().pick(256.0, 1.0F, false);
        BlockPos at = hit instanceof net.minecraft.world.phys.BlockHitResult bh && hit.getType() != net.minecraft.world.phys.HitResult.Type.MISS
                ? bh.getBlockPos() : mc.player.blockPosition();
        ping(at.getX(), at.getY(), at.getZ());
    }

    // ------------------------------------------------------------------ chat: compass results and graves
    /** Remembers what the server tells this player in chat: a structure the compass found, a new grave. */
    public static void onSystemMessage(Component message) {
        if (local == null || level == null || !(message.getContents() instanceof TranslatableContents tc)) {
            return;
        }
        Object[] args = tc.getArgs();
        try {
            if (tc.getKey().equals("message.wayfarers.compass.found") && args.length >= 5) {
                String name = args[0] instanceof Component c ? c.getString() : String.valueOf(args[0]);
                int x = number(args[3]);
                int z = number(args[4]);
                LocalPlayer p = Minecraft.getInstance().player;
                int y = p == null ? 64 : p.getBlockY();
                MapPoints.Point pt = new MapPoints.Point("structure", name, dim, x, y, z, 0xF6C343);
                local.addStructure(pt);
                local.setTarget(new MapPoints.Point("target", name, dim, x, y, z, 0x3FD0FF));
            } else if (tc.getKey().equals("message.wayfarers.grave") && args.length >= 4) {
                String path = String.valueOf(args[3] instanceof Component c ? c.getString() : args[3]);
                String d = dim.endsWith(":" + path) ? dim : path.contains(":") ? path : "minecraft:" + path;
                local.addGrave(new MapPoints.Point("grave", "", d, number(args[0]), number(args[1]), number(args[2]), 0xB9A98E));
            }
        } catch (RuntimeException e) {
            LOGGER.debug("Wayfarers map: unreadable message {}", tc.getKey());
        }
    }

    private static int number(Object o) {
        if (o instanceof Number n) {
            return n.intValue();
        }
        String s = o instanceof Component c ? c.getString() : String.valueOf(o);
        return Integer.parseInt(s.strip());
    }

    /** Forgets graves that have been emptied (the block is gone) once their chunk is loaded. */
    private static void checkGraves(ClientLevel lvl, LocalPlayer player) {
        if (local == null) {
            return;
        }
        for (MapPoints.Point g : new ArrayList<>(local.graves())) {
            if (!g.dim.equals(dim)) {
                continue;
            }
            BlockPos pos = new BlockPos(g.x, g.y, g.z);
            if (player.blockPosition().distSqr(pos) < 48 * 48 && lvl.isLoaded(pos)
                    && !lvl.getBlockState(pos).is(com.wayfarers.registry.ModBlocks.GRAVE.get())) {
                local.removeGrave(g);
            }
        }
    }

    /** Clears the compass target (world map button). */
    public static void clearTarget() {
        if (local != null) {
            local.setTarget(null);
        }
    }

    // ------------------------------------------------------------------ markers
    /** Everything to draw on the map of the current dimension. */
    public static List<Marker> markers() {
        Minecraft mc = Minecraft.getInstance();
        List<Marker> out = new ArrayList<>();
        if (level == null || mc.player == null) {
            return out;
        }
        GlobalPos spawn = level.getRespawnData().globalPos();
        if (spawn.dimension() == level.dimension()) {
            BlockPos s = spawn.pos();
            out.add(new Marker(Kind.SPAWN, s.getX() + 0.5, s.getY(), s.getZ() + 0.5, 0xFFF3E3C0,
                    Component.translatable("gui.wayfarers.map.spawn").getString(), coords(s), null, 0));
        }
        mc.player.getLastDeathLocation().ifPresent(g -> {
            if (g.dimension() == level.dimension()) {
                out.add(new Marker(Kind.DEATH, g.pos().getX() + 0.5, g.pos().getY(), g.pos().getZ() + 0.5, 0xFFE0483B,
                        Component.translatable("gui.wayfarers.map.death").getString(), coords(g.pos()), null, 0));
            }
        });
        if (local != null) {
            for (MapPoints.Point g : local.graves()) {
                if (g.dim.equals(dim)) {
                    out.add(new Marker(Kind.GRAVE, g.x + 0.5, g.y, g.z + 0.5, 0xFFB9A98E,
                            Component.translatable("gui.wayfarers.map.grave").getString(), coords(g.x, g.y, g.z), g, 0));
                }
            }
            for (MapPoints.Point s : local.structures()) {
                if (s.dim.equals(dim)) {
                    out.add(new Marker(Kind.STRUCTURE, s.x + 0.5, s.y, s.z + 0.5, 0xFFF6C343, s.name,
                            Component.translatable("gui.wayfarers.map.structure").getString(), s, 0));
                }
            }
            MapPoints.Point t = local.target();
            if (t != null && t.dim.equals(dim)) {
                out.add(new Marker(Kind.TARGET, t.x + 0.5, t.y, t.z + 0.5, 0xFF3FD0FF, t.name,
                        Component.translatable("gui.wayfarers.map.target").getString(), t, 0));
            }
        }
        for (MapProtocol.Waystone w : waystones) {
            if (w.dim().equals(dim)) {
                out.add(new Marker(Kind.WAYSTONE, w.x() + 0.5, w.y(), w.z() + 0.5, 0xFF9FE6FF, w.name(),
                        coords(w.x(), w.y(), w.z()), w, 0));
            }
        }
        for (MapProtocol.Waypoint w : waypoints) {
            if (w.dim().equals(dim)) {
                String detail = mine(w) ? (w.shared() ? Component.translatable("gui.wayfarers.map.shared").getString() : null)
                        : Component.translatable("gui.wayfarers.map.by", w.ownerName()).getString();
                out.add(new Marker(Kind.WAYPOINT, w.x() + 0.5, w.y(), w.z() + 0.5, 0xFF000000 | w.color(), w.name(), detail, w, 0));
            }
        }
        long now = System.currentTimeMillis();
        for (Ping p : PINGS) {
            if (p.dim().equals(dim) && p.until() > now) {
                out.add(new Marker(Kind.PING, p.x() + 0.5, p.y(), p.z() + 0.5, 0xFFFF7A3C, p.name(),
                        coords(p.x(), p.y(), p.z()), p, 0));
            }
        }
        if (WayfarersClientConfig.MAP_PLAYERS.get() && playersDim.equals(dim) && now - playersAt < 5000) {
            String me = mc.player.getName().getString();
            for (MapProtocol.PlayerPos p : players) {
                if (p.name().equals(me)) {
                    continue;
                }
                // a player close enough to be seen moves smoothly; others jump once a second
                double x = p.x() + 0.5;
                double y = p.y();
                double z = p.z() + 0.5;
                float yaw = p.yaw();
                for (net.minecraft.client.player.AbstractClientPlayer seen : level.players()) {
                    if (seen.getName().getString().equals(p.name())) {
                        x = seen.getX();
                        y = seen.getY();
                        z = seen.getZ();
                        yaw = seen.getYRot();
                    }
                }
                out.add(new Marker(Kind.PLAYER, x, y, z, 0xFFFFFFFF, p.name(), null, p, yaw));
            }
        }
        return out;
    }

    static String coords(BlockPos p) {
        return coords(p.getX(), p.getY(), p.getZ());
    }

    static String coords(int x, int y, int z) {
        return x + ", " + y + ", " + z;
    }

    // ------------------------------------------------------------------ cave view (local)
    private static void updateCaveMode(ClientLevel lvl, LocalPlayer player) {
        boolean want;
        if (!WayfarersClientConfig.CAVE_MAP.get()) {
            want = false;
        } else if (lvl.dimensionType().hasCeiling()) {
            want = true;
        } else if (!lvl.dimensionType().hasSkyLight()) {
            want = false;
        } else {
            BlockPos head = BlockPos.containing(player.getX(), player.getEyeY(), player.getZ());
            int surface = lvl.getChunk(head.getX() >> 4, head.getZ() >> 4)
                    .getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, head.getX(), head.getZ());
            want = surface > head.getY() + 3 && lvl.getBrightness(LightLayer.SKY, head) < 6;
        }
        caveVotes = Math.max(-10, Math.min(10, caveVotes + (want ? 1 : -1)));
        if (!caveActive && caveVotes >= 6) {
            caveActive = true;
            scannedSlice = Integer.MIN_VALUE;
        } else if (caveActive && caveVotes <= -6) {
            caveActive = false;
            if (cave != null) {
                cave.clear();
            }
            SEEN.clear();
            QUEUE.clear();
            QUEUED.clear();
        }
        sliceY = player.getBlockY() + 2;
    }

    private static void scanCaves(ClientLevel lvl, LocalPlayer player) {
        int pcx = player.getBlockX() >> 4;
        int pcz = player.getBlockZ() >> 4;
        if (Math.abs(sliceY - scannedSlice) >= 3) {
            // moved up or down: rescan everything around, nearest first
            scannedSlice = sliceY;
            SEEN.clear();
            QUEUE.clear();
            QUEUED.clear();
        }
        int r = Math.min(Minecraft.getInstance().options.getEffectiveRenderDistance(), 8);
        if (tick % 10 == 0) {
            // spiral from the player: new chunks get queued nearest first
            for (int ring = 0; ring <= r; ring++) {
                for (int dz = -ring; dz <= ring; dz++) {
                    for (int dx = -ring; dx <= ring; dx++) {
                        if (Math.max(Math.abs(dx), Math.abs(dz)) != ring) {
                            continue;
                        }
                        int cx = pcx + dx;
                        int cz = pcz + dz;
                        LevelChunk c = lvl.getChunkSource().getChunk(cx, cz, ChunkStatus.FULL, false);
                        long k = ChunkPos.pack(cx, cz);
                        if (c != null && SEEN.get(k) != c && QUEUED.add(k)) {
                            QUEUE.enqueue(k);
                        }
                    }
                }
            }
            SEEN.long2ObjectEntrySet().removeIf(e -> Math.max(Math.abs(ChunkPos.getX(e.getLongKey()) - pcx),
                    Math.abs(ChunkPos.getZ(e.getLongKey()) - pcz)) > r + 2);
        }
        // the chunks right around you are refreshed every second or so (digging shows up)
        int ring = tick % 9;
        long near = ChunkPos.pack(pcx + ring % 3 - 1, pcz + ring / 3 - 1);
        if (QUEUED.add(near)) {
            QUEUE.enqueue(near);
        }
        long start = System.nanoTime();
        int done = 0;
        while (!QUEUE.isEmpty() && done < 12 && System.nanoTime() - start < 1_500_000L) {
            long k = QUEUE.dequeueLong();
            QUEUED.remove(k);
            int cx = ChunkPos.getX(k);
            int cz = ChunkPos.getZ(k);
            LevelChunk c = lvl.getChunkSource().getChunk(cx, cz, ChunkStatus.FULL, false);
            if (c == null) {
                continue;
            }
            SEEN.put(k, c);
            int rx = cx >> 4;
            int rz = cz >> 4;
            if (SCAN.scan(lvl, c, cave.localData(rx, rz), rx << MapTile.SHIFT, rz << MapTile.SHIFT, sliceY)) {
                cave.markDirty(cx << 4, cz << 4, (cx << 4) + 15, (cz << 4) + 15);
            }
            done++;
        }
    }
}
