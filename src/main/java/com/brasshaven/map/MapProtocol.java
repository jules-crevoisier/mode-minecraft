package com.brasshaven.map;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Payloads of the map messages ({@link com.brasshaven.network.MapDataMsg} and
 * {@link com.brasshaven.network.MapActionMsg}): plain DataOutput layouts, shared by both sides.
 */
public final class MapProtocol {
    public static final int MAX_NAME = 32;
    /** Waypoint icons: index into the client's icon sprites. */
    public static final String[] ICONS = {"flag", "house", "star", "mine", "skull", "chest"};

    private MapProtocol() {}

    /** A region the client wants: {@code full} region or thumbnail, and the revision it already has (0: none). */
    public record Request(int rx, int rz, boolean full, int knownRevision) {}

    public record Waypoint(String id, String owner, String ownerName, String name, String dim, int x, int y, int z, int color,
                           int icon, boolean shared) {}

    public record Waystone(String id, String name, String dim, int x, int y, int z) {}

    public record PlayerPos(String name, int x, int y, int z, float yaw) {}

    @FunctionalInterface
    public interface Writer {
        void write(DataOutputStream out) throws IOException;
    }

    @FunctionalInterface
    public interface Reader<T> {
        T read(DataInputStream in) throws IOException;
    }

    public static byte[] bytes(Writer w) {
        ByteArrayOutputStream b = new ByteArrayOutputStream(256);
        try (DataOutputStream out = new DataOutputStream(b)) {
            w.write(out);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        return b.toByteArray();
    }

    /** Reads a payload; null when it is malformed (never trust the other side). */
    public static <T> T read(byte[] data, Reader<T> r) {
        try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(data))) {
            return r.read(in);
        } catch (IOException | RuntimeException e) {
            return null;
        }
    }

    public static String clean(String s) {
        String t = s == null ? "" : s.strip();
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < t.length() && b.length() < MAX_NAME; i++) {
            char c = t.charAt(i);
            if (c >= ' ' && c != '§' && c != 0x7F) {
                b.append(c);
            }
        }
        return b.toString();
    }

    // ------------------------------------------------------------------ requests
    public static byte[] requests(String dim, List<Request> list) {
        return bytes(out -> {
            out.writeUTF(dim);
            out.writeShort(list.size());
            for (Request r : list) {
                out.writeInt(r.rx());
                out.writeInt(r.rz());
                out.writeBoolean(r.full());
                out.writeInt(r.knownRevision());
            }
        });
    }

    /** {dim, list}; at most 64 requests are read. */
    public static Object[] readRequests(byte[] data) {
        return read(data, in -> {
            String dim = in.readUTF();
            int n = Math.min(64, in.readUnsignedShort());
            List<Request> list = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                list.add(new Request(in.readInt(), in.readInt(), in.readBoolean(), in.readInt()));
            }
            return new Object[] {dim, list};
        });
    }

    // ------------------------------------------------------------------ points
    public static void writeWaypoint(DataOutputStream out, Waypoint w) throws IOException {
        out.writeUTF(w.id());
        out.writeUTF(w.owner());
        out.writeUTF(w.ownerName());
        out.writeUTF(w.name());
        out.writeUTF(w.dim());
        out.writeInt(w.x());
        out.writeInt(w.y());
        out.writeInt(w.z());
        out.writeInt(w.color());
        out.writeByte(w.icon());
        out.writeBoolean(w.shared());
    }

    public static Waypoint readWaypoint(DataInputStream in) throws IOException {
        return new Waypoint(in.readUTF(), in.readUTF(), in.readUTF(), clean(in.readUTF()), in.readUTF(), in.readInt(), in.readInt(),
                in.readInt(), in.readInt() & 0xFFFFFF, Math.floorMod(in.readByte(), ICONS.length), in.readBoolean());
    }

    /** Most bytes of waypoints / waystones in one POINTS message (a custom payload may not exceed 1 MiB). */
    private static final int MAX_POINTS_BYTES = 600_000;
    private static final int MAX_STONES_BYTES = 300_000;

    /** {@code waypoints} should list the player's own first: what does not fit in the message is left out. */
    public static byte[] points(List<Waypoint> waypoints, List<Waystone> waystones) {
        int[] counts = new int[2];
        byte[] wps = bytes(out -> {
            for (Waypoint w : waypoints) {
                if (out.size() > MAX_POINTS_BYTES) {
                    break;
                }
                writeWaypoint(out, w);
                counts[0]++;
            }
        });
        byte[] stones = bytes(out -> {
            for (Waystone s : waystones) {
                if (out.size() > MAX_STONES_BYTES) {
                    break;
                }
                out.writeUTF(s.id());
                out.writeUTF(s.name());
                out.writeUTF(s.dim());
                out.writeInt(s.x());
                out.writeInt(s.y());
                out.writeInt(s.z());
                counts[1]++;
            }
        });
        return bytes(out -> {
            out.writeInt(counts[0]);
            out.write(wps);
            out.writeInt(counts[1]);
            out.write(stones);
        });
    }

    /** {List&lt;Waypoint&gt;, List&lt;Waystone&gt;}. */
    public static Object[] readPoints(byte[] data) {
        return read(data, in -> {
            int n = in.readInt();
            List<Waypoint> wps = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                wps.add(readWaypoint(in));
            }
            int m = in.readInt();
            List<Waystone> stones = new ArrayList<>();
            for (int i = 0; i < m; i++) {
                stones.add(new Waystone(in.readUTF(), in.readUTF(), in.readUTF(), in.readInt(), in.readInt(), in.readInt()));
            }
            return new Object[] {wps, stones};
        });
    }

    public static byte[] players(List<PlayerPos> list) {
        return bytes(out -> {
            out.writeShort(list.size());
            for (PlayerPos p : list) {
                out.writeUTF(p.name());
                out.writeInt(p.x());
                out.writeInt(p.y());
                out.writeInt(p.z());
                out.writeFloat(p.yaw());
            }
        });
    }

    public static List<PlayerPos> readPlayers(byte[] data) {
        return read(data, in -> {
            int n = in.readUnsignedShort();
            List<PlayerPos> list = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                list.add(new PlayerPos(in.readUTF(), in.readInt(), in.readInt(), in.readInt(), in.readFloat()));
            }
            return list;
        });
    }
}
