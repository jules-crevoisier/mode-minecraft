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
 * explored terrain, markers, your coordinates and the biome you stand in.
 */
public final class MinimapHud {
    /** GUI pixels per block for each zoom level. */
    static final float[] ZOOMS = {0.5F, 1.0F, 2.0F, 4.0F};
    private static final int BORDER = 6;
    private static final int MARGIN = 4;
    private static final Identifier SQUARE = Wayfarers.id("map/frame_square");
    private static final Identifier PLATE = Wayfarers.id("map/plate");
    private static final String[] CARDINALS = {"n", "e", "s", "w"};

    private MinimapHud() {}

    public static void register(AddGuiOverlayLayersEvent event) {
        event.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK, Wayfarers.id("minimap"),
                ForgeLayeredDraw.BOSS_OVERLAY, MinimapHud::extract);
    }

    static int mapSize() {
        return switch (WayfarersClientConfig.MINIMAP_SIZE.get()) {
            case SMALL -> 64;
            case LARGE -> 128;
            default -> 96;
        };
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
        return mapSize() + BORDER * 2 + MARGIN + (WayfarersClientConfig.MINIMAP_COORDS.get() ? 24 : 2);
    }

    private static void extract(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (!visible(mc)) {
            return;
        }
        LocalPlayer player = mc.player;
        float pt = dt.getGameTimeDeltaPartialTick(false);
        int size = mapSize();
        int outer = size + BORDER * 2;
        boolean coords = WayfarersClientConfig.MINIMAP_COORDS.get();
        int textH = coords ? 22 : 0;
        WayfarersClientConfig.Corner corner = WayfarersClientConfig.MINIMAP_CORNER.get();
        boolean right = corner == WayfarersClientConfig.Corner.TOP_RIGHT || corner == WayfarersClientConfig.Corner.BOTTOM_RIGHT;
        boolean bottom = corner == WayfarersClientConfig.Corner.BOTTOM_LEFT || corner == WayfarersClientConfig.Corner.BOTTOM_RIGHT;
        int x = right ? g.guiWidth() - outer - MARGIN : MARGIN;
        int y = bottom ? g.guiHeight() - outer - MARGIN - textH : MARGIN;
        boolean round = WayfarersClientConfig.MINIMAP_SHAPE.get() == WayfarersClientConfig.MinimapShape.ROUND;
        boolean rotate = WayfarersClientConfig.MINIMAP_ROTATE.get();
        float scale = ZOOMS[Math.max(0, Math.min(ZOOMS.length - 1, WayfarersClientConfig.MINIMAP_ZOOM.get()))];

        double px = net.minecraft.util.Mth.lerp(pt, player.xo, player.getX());
        double pz = net.minecraft.util.Mth.lerp(pt, player.zo, player.getZ());
        float yaw = player.getViewYRot(pt);
        float angle = rotate ? (float) Math.toRadians(180.0 - yaw) : 0.0F;
        int ix = x + BORDER;
        int iy = y + BORDER;
        float cxs = ix + size / 2.0F;
        float cys = iy + size / 2.0F;

        // backdrop, terrain, then the frame on top
        g.fill(ix, iy, ix + size, iy + size, 0xFF2A221C);
        g.enableScissor(ix, iy, ix + size, iy + size);
        MapRenderer.tiles(g, px, pz, scale, cxs, cys, angle, size * 0.75F);
        g.disableScissor();

        // markers (inside the map; a few kinds stick to the rim when off the map)
        float half = size / 2.0F - 4;
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
            MapRenderer.marker(g, m, Math.round(cxs + (float) sx), Math.round(cys + (float) sy), !inside);
        }
        MapRenderer.arrow(g, cxs, cys, rotate ? 0.0F : (float) Math.toRadians(yaw + 180.0));

        if (round) {
            g.blitSprite(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, Wayfarers.id("map/frame_round_" + size), x, y, outer, outer);
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
            Font font = mc.font;
            int ty = y + outer + 1;
            String pos = player.getBlockX() + ", " + player.getBlockY() + ", " + player.getBlockZ();
            Component biome = player.level().getBiome(player.blockPosition()).unwrapKey()
                    .map(k -> MapPalette.biomeName(k.identifier().toString())).orElse(Component.empty());
            int w = Math.max(font.width(pos), font.width(biome)) + 8;
            int tw = Math.max(outer, Math.min(w, outer + 40));
            int tx = right ? x + outer - tw : x;
            WfGui.sprite(g, PLATE, tx, ty, tw, 21);
            g.centeredText(font, pos, tx + tw / 2, ty + 2, WfGui.CREAM);
            WfGui.textClipped(g, font, biome.getString(), tx + Math.max(4, (tw - font.width(biome)) / 2), ty + 11, tw - 8, WfGui.CREAM_SOFT, false);
        }
    }

    /** Next zoom level (wraps around); bound to a key. */
    public static void cycleZoom() {
        int z = WayfarersClientConfig.MINIMAP_ZOOM.get() + 1;
        WayfarersClientConfig.MINIMAP_ZOOM.set(z >= ZOOMS.length ? 0 : z);
        WayfarersClientConfig.MINIMAP_ZOOM.save();
    }

    public static void toggle() {
        WayfarersClientConfig.MINIMAP.set(!WayfarersClientConfig.MINIMAP.get());
        WayfarersClientConfig.MINIMAP.save();
    }
}
