package com.wayfarers.client.map;

import com.wayfarers.Wayfarers;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.config.WayfarersClientConfig;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;

import java.util.List;

/**
 * The minimap: a brass porthole (or square bezel) in a corner of the screen, north-up or turning with you, with the
 * explored terrain, markers, and under it a compact plate with your coordinates and the biome you stand in.
 *
 * <p>Any size from 48 to 160 GUI px, frame included (68 by default): the slider of the world map's options, or the
 * four presets (56, 68, 96, 128) cycled with Shift + the minimap key or picked in the settings screen. The round frame
 * is drawn for the exact size ({@link MapFrames}) and the square one is a nine-slice: both stay crisp at any GUI
 * scale. The player arrow and the markers grow with the map (a 7 px arrow on the small ones).
 */
public final class MinimapHud {
    /** GUI pixels per block for each zoom level. */
    static final float[] ZOOMS = {0.5F, 1.0F, 2.0F, 4.0F};
    private static final int BORDER = MapFrames.BORDER;
    private static final int MARGIN = 4;
    /** Height of the coordinates / biome plate under the map. */
    private static final int PLATE_H = 20;
    private static final Identifier SQUARE = Wayfarers.id("map/frame_square");
    private static final Identifier PLATE = Wayfarers.id("map/plate");
    private static final String[] CARDINALS = {"n", "e", "s", "w"};

    private MinimapHud() {}

    public static void register(AddGuiOverlayLayersEvent event) {
        event.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK, Wayfarers.id("minimap"),
                ForgeLayeredDraw.BOSS_OVERLAY, MinimapHud::extract);
    }

    /** Diameter of the map itself (inside the frame) in GUI pixels. */
    static int mapSize() {
        return WayfarersClientConfig.minimapPixels() - BORDER * 2;
    }

    private static boolean visible(Minecraft mc) {
        return WayfarersClientConfig.MINIMAP.get() && mc.player != null && mc.level != null
                && !(mc.gui.screen() instanceof WorldMapScreen) && !mc.getDebugOverlay().showDebugScreen();
    }

    /** Height taken at the top right of the screen (so the quest tracker can move below it). */
    public static int reservedTopRight() {
        Minecraft mc = Minecraft.getInstance();
        if (!visible(mc) || WayfarersClientConfig.MINIMAP_CORNER.get() != WayfarersClientConfig.Corner.TOP_RIGHT) {
            return 0;
        }
        // the tracker goes at 6 + this: 4 px under the minimap (which starts MARGIN px down) and its plate
        return mapSize() + BORDER * 2 + (WayfarersClientConfig.MINIMAP_COORDS.get() ? PLATE_H + 1 : 0) + 2;
    }

    private static void extract(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (!visible(mc)) {
            return;
        }
        draw(g, dt.getGameTimeDeltaPartialTick(false));
    }

    /** Draws the minimap as set in the config (also the live preview of the world map's options). */
    static void draw(GuiGraphicsExtractor g, float pt) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        if (player == null || mc.level == null) {
            return;
        }
        int size = mapSize();
        int outer = size + BORDER * 2;
        boolean coords = WayfarersClientConfig.MINIMAP_COORDS.get();
        int textH = coords ? PLATE_H + 1 : 0;
        WayfarersClientConfig.Corner corner = WayfarersClientConfig.MINIMAP_CORNER.get();
        boolean right = corner == WayfarersClientConfig.Corner.TOP_RIGHT || corner == WayfarersClientConfig.Corner.BOTTOM_RIGHT;
        boolean bottom = corner == WayfarersClientConfig.Corner.BOTTOM_LEFT || corner == WayfarersClientConfig.Corner.BOTTOM_RIGHT;
        int x = right ? g.guiWidth() - outer - MARGIN : MARGIN;
        int y = bottom ? g.guiHeight() - outer - MARGIN - textH : MARGIN;
        boolean round = WayfarersClientConfig.MINIMAP_SHAPE.get() == WayfarersClientConfig.MinimapShape.ROUND;
        boolean rotate = WayfarersClientConfig.MINIMAP_ROTATE.get();
        float scale = ZOOMS[Math.max(0, Math.min(ZOOMS.length - 1, WayfarersClientConfig.MINIMAP_ZOOM.get()))];
        int alpha = Math.round(255 * Math.max(30, Math.min(100, WayfarersClientConfig.MINIMAP_OPACITY.get())) / 100F);

        double px = net.minecraft.util.Mth.lerp(pt, player.xo, player.getX());
        double pz = net.minecraft.util.Mth.lerp(pt, player.zo, player.getZ());
        float yaw = player.getViewYRot(pt);
        float angle = rotate ? (float) Math.toRadians(180.0 - yaw) : 0.0F;
        int ix = x + BORDER;
        int iy = y + BORDER;
        float cxs = ix + size / 2.0F;
        float cys = iy + size / 2.0F;

        // backdrop, terrain (faded by the opacity setting), then the frame on top
        g.fill(ix, iy, ix + size, iy + size, alpha << 24 | 0x2A221C);
        g.enableScissor(ix, iy, ix + size, iy + size);
        MapRenderer.tiles(g, px, pz, scale, cxs, cys, angle, size * 0.75F, alpha >= 255 ? -1 : alpha << 24 | 0xFFFFFF);
        g.disableScissor();

        // markers (inside the map; a few kinds stick to the rim when off the map), sized to the map
        float markerSize = MapRenderer.minimapMarker(outer);
        float half = size / 2.0F - Math.max(3.0F, markerSize / 2.0F - 0.5F);
        double cos = Math.cos(angle);
        double sin = Math.sin(angle);
        List<ClientMap.Marker> markers = ClientMap.markers();
        for (ClientMap.Marker m : markers) {
            double dx = (m.x() - px) * scale;
            double dz = (m.z() - pz) * scale;
            double sx = dx * cos - dz * sin;
            double sy = dx * sin + dz * cos;
            boolean inside = round ? sx * sx + sy * sy <= half * half : Math.abs(sx) <= half && Math.abs(sy) <= half;
            if (!inside) {
                if (m.kind() != ClientMap.Kind.WAYPOINT && m.kind() != ClientMap.Kind.TARGET && m.kind() != ClientMap.Kind.PING
                        && m.kind() != ClientMap.Kind.DEATH) {
                    continue;
                }
                double k = round ? half / Math.sqrt(sx * sx + sy * sy) : half / Math.max(Math.abs(sx), Math.abs(sy));
                sx *= k;
                sy *= k;
            }
            MapRenderer.marker(g, m, Math.round(cxs + (float) sx), Math.round(cys + (float) sy), !inside, markerSize);
        }
        MapRenderer.arrow(g, cxs, cys, rotate ? 0.0F : (float) Math.toRadians(yaw + 180.0), MapRenderer.minimapArrow(outer));

        if (round) {
            // drawn for this exact size, one texel per GUI pixel: no stretched pixels
            MapFrames.round(g, x, y, size);
        } else {
            WfGui.sprite(g, SQUARE, x, y, outer, outer);
        }
        // N / E / S / W studs on the rim
        for (int i = 0; i < 4; i++) {
            double a = angle + i * Math.PI / 2;
            double dirX = Math.sin(a);
            double dirY = -Math.cos(a);
            double r = size / 2.0 + BORDER / 2.0;
            if (!round) {
                r = r / Math.max(Math.abs(dirX), Math.abs(dirY));
            }
            int sx = Math.round(cxs + (float) (dirX * r));
            int sy = Math.round(cys + (float) (dirY * r));
            MapRenderer.spriteCentered(g, Wayfarers.id("map/cardinal_" + CARDINALS[i]), sx, sy, 9, -1);
        }

        if (coords) {
            // a compact dark plate as wide as its text (at least the map's width), on the screen-edge side
            Font font = mc.font;
            int ty = y + outer + 1;
            String pos = player.getBlockX() + ", " + player.getBlockY() + ", " + player.getBlockZ();
            String biome = player.level().getBiome(player.blockPosition()).unwrapKey()
                    .map(k -> MapPalette.biomeName(k.identifier().toString())).orElse(Component.empty()).getString();
            int max = Math.max(outer, Math.min(g.guiWidth() / 3, 150));
            int tw = Math.min(max, Math.max(outer, Math.max(font.width(pos), font.width(biome)) + 8));
            int tx = right ? x + outer - tw : x;
            WfGui.sprite(g, PLATE, tx, ty, tw, PLATE_H);
            WfGui.textClipped(g, font, pos, tx + Math.max(4, (tw - font.width(pos)) / 2), ty + 2, tw - 6, WfGui.CREAM, true);
            WfGui.textClipped(g, font, biome, tx + Math.max(4, (tw - font.width(biome)) / 2), ty + 11, tw - 6, WfGui.CREAM_SOFT, true);
        }
    }

    /** Next zoom level (wraps around); bound to a key. */
    public static void cycleZoom() {
        int z = WayfarersClientConfig.MINIMAP_ZOOM.get() + 1;
        WayfarersClientConfig.MINIMAP_ZOOM.set(z >= ZOOMS.length ? 0 : z);
        WayfarersClientConfig.MINIMAP_ZOOM.save();
        float s = ZOOMS[WayfarersClientConfig.MINIMAP_ZOOM.get()];
        overlay(Component.translatable("message.wayfarers.minimap.zoom",
                s >= 1 ? Component.translatable("gui.wayfarers.map.scale_in", (int) s)
                        : Component.translatable("gui.wayfarers.map.scale_out", (int) (1 / s))));
    }

    /** Next size preset, the first bigger than now (wraps around); Shift + the minimap key. Shows the minimap if hidden. */
    public static void cycleSize() {
        WayfarersClientConfig.MinimapSize[] sizes = WayfarersClientConfig.MinimapSize.values();
        int now = WayfarersClientConfig.minimapPixels();
        WayfarersClientConfig.MinimapSize next = sizes[0];
        for (WayfarersClientConfig.MinimapSize s : sizes) {
            if (s.outer > now) {
                next = s;
                break;
            }
        }
        setSize(next);
        if (!WayfarersClientConfig.MINIMAP.get()) {
            WayfarersClientConfig.MINIMAP.set(true);
            WayfarersClientConfig.MINIMAP.save();
        }
        overlay(Component.translatable("message.wayfarers.minimap.size", sizeName(next), next.outer,
                com.wayfarers.client.WayfarersClient.MINIMAP_KEY.getTranslatedKeyMessage()));
    }

    public static void setSize(WayfarersClientConfig.MinimapSize size) {
        WayfarersClientConfig.MINIMAP_SIZE.set(size);
        WayfarersClientConfig.MINIMAP_SIZE.save();
        WayfarersClientConfig.setMinimapPixels(size.outer);
    }

    /** True when the minimap is exactly this preset's size. */
    public static boolean isSize(WayfarersClientConfig.MinimapSize size) {
        return WayfarersClientConfig.minimapPixels() == size.outer;
    }

    public static Component sizeName(WayfarersClientConfig.MinimapSize size) {
        return Component.translatable("gui.wayfarers.settings.minimap_size." + size.name().toLowerCase(java.util.Locale.ROOT));
    }

    public static void toggle() {
        WayfarersClientConfig.MINIMAP.set(!WayfarersClientConfig.MINIMAP.get());
        WayfarersClientConfig.MINIMAP.save();
        Component key = com.wayfarers.client.WayfarersClient.MINIMAP_KEY.getTranslatedKeyMessage();
        overlay(WayfarersClientConfig.MINIMAP.get()
                ? Component.translatable("message.wayfarers.minimap.shown", key)
                : Component.translatable("message.wayfarers.minimap.hidden", key));
    }

    /** A short line above the hotbar (the action bar). */
    private static void overlay(Component message) {
        LocalPlayer player = Minecraft.getInstance().player;
        if (player != null) {
            player.sendOverlayMessage(message);
        }
    }
}
