package com.wayfarers.client.map;

import com.wayfarers.Wayfarers;
import com.wayfarers.client.WayfarersClient;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.client.gui.WfWidgets;
import com.wayfarers.config.WayfarersClientConfig;
import com.wayfarers.map.MapProtocol;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * The world map (M): the shared explored world on parchment. Drag to pan, wheel to zoom, click a marker for its card,
 * right-click for waypoints and pings, middle-click to ping. The side panel holds the legend (click to hide a kind)
 * and your waypoints. A tool button tilts it into a 3D view ({@link MapView3D}); the gear opens the options panel:
 * the minimap's exact size (slider) and presets, corner, shape, rotation, coordinates and opacity, shown live in its
 * corner while the panel is open, and the relief of the maps (hill-shading, contour lines).
 */
public class WorldMapScreen extends Screen {
    private static final Identifier PARCHMENT = Wayfarers.id("map/parchment");
    private static final Identifier FRAME = Wayfarers.id("map/frame_square");
    private static final int SIDEBAR = 116;
    private static final int ROW = 12;
    private static final int MIN_ZOOM = -6;
    private static final int MAX_ZOOM = 6;
    /** Closest zoom-out of the 3D view (half a pixel per block: the full regions, which carry the heights). */
    private static final int MIN_ZOOM_3D = -2;
    // the options panel: width, label column, row height, rows (8 for the minimap, 2 for the relief) and height
    private static final int OPT_W = 210;
    private static final int OPT_LABEL = 82;
    private static final int OPT_ROW = 16;
    private static final int OPT_ROWS = 10;
    private static final int OPT_HEAD = 24;
    /** Inside the brass border of the panel. */
    private static final int OPT_PAD = 12;
    private static final int OPT_SECTION = 14;
    private static final int OPT_H = OPT_HEAD + OPT_ROWS * OPT_ROW + OPT_SECTION + 10;
    private static final String S = "gui.wayfarers.settings.";
    private static final String O = "gui.wayfarers.map.options.";

    private static int zoom;
    private static boolean sidebarOpen = true;

    private double centerX;
    private double centerZ;
    private boolean follow = true;
    private boolean dragging;
    private double pressX;
    private double pressY;
    private int listScroll;

    private ClientMap.Marker selected;
    private ContextMenu menu;
    private Editor editor;
    private final List<Btn> buttons = new ArrayList<>();
    /** Buttons from this index on belong to the editor (the only ones clickable while it is open). */
    private int editorButtons;
    /** The marker card's area (clicks there do not reach the map). */
    private int[] cardRect;
    private List<ClientMap.Marker> markers = List.of();

    private int mx0;
    private int my0;
    private int mx1;
    private int my1;

    private final MapView3D view3d = new MapView3D();
    /** Ground height at the centre line of the 3D view, eased so panning over hills does not jolt the view. */
    private float refY = Float.NaN;
    private boolean optionsOpen;
    private int optX;
    private int optY;
    private final List<AbstractWidget> optionWidgets = new ArrayList<>();
    private WfWidgets.Stepper sizeSlider;

    /** A clickable area rebuilt every frame. */
    private record Btn(int x, int y, int w, int h, Runnable action) {
        boolean hit(double px, double py) {
            return px >= x && px < x + w && py >= y && py < y + h;
        }
    }

    private record ContextMenu(int x, int y, int wx, int wz, List<Component> labels, List<Runnable> actions) {}

    /** The waypoint editor (new or existing). */
    private final class Editor {
        final MapProtocol.Waypoint editing;
        final int x;
        final int y;
        final int z;
        int color;
        int icon;
        boolean shared;
        final EditBox name;

        Editor(MapProtocol.Waypoint w, int x, int y, int z) {
            this.editing = w;
            this.x = x;
            this.y = y;
            this.z = z;
            this.color = w == null ? WAYPOINT_COLORS[(int) (Math.abs((long) x * 31 + z) % WAYPOINT_COLORS.length)] : w.color();
            this.icon = w == null ? 0 : w.icon();
            this.shared = w != null && w.shared();
            name = new EditBox(font, 0, 0, 160, 14, Component.translatable("gui.wayfarers.map.name"));
            name.setMaxLength(MapProtocol.MAX_NAME);
            name.setValue(w == null ? Component.translatable("gui.wayfarers.map.default_name", x, z).getString() : w.name());
            addRenderableWidget(name);
            setFocused(name);
            layout();
        }

        int left() {
            return (mx0 + mx1) / 2 - 100;
        }

        int top() {
            return (my0 + my1) / 2 - 66;
        }

        void layout() {
            name.setX(left() + 20);
            name.setY(top() + 22);
        }

        void save() {
            String n = name.getValue().strip();
            if (n.isEmpty()) {
                return;
            }
            if (editing == null) {
                ClientMap.addWaypoint(n, x, y, z, color, icon, shared);
            } else {
                ClientMap.editWaypoint(editing, n, color, icon, shared);
            }
            close();
        }

        void close() {
            removeWidget(name);
            editor = null;
        }
    }

    static final int[] WAYPOINT_COLORS = {0xE0483B, 0xF39C34, 0xF6C343, 0x7CE35A, 0x2EE6C5, 0x3FA9FF, 0x9B6BFF, 0xFF7AD9,
            0xF3E3C0, 0x8C7B66};

    public WorldMapScreen() {
        super(Component.translatable("gui.wayfarers.map.title"));
    }

    // ------------------------------------------------------------------ geometry
    private float scale() {
        return (float) Math.pow(2.0, zoom / 2.0);
    }

    private boolean showSidebar() {
        return sidebarOpen && width >= 360;
    }

    private static boolean is3d() {
        return WayfarersClientConfig.MAP_3D.get();
    }

    /** Screen px per block of ground along z: squashed in the 3D view. */
    private float depthScale() {
        return scale() * (is3d() ? MapView3D.DEPTH : 1.0F);
    }

    private int ref() {
        return Float.isNaN(refY) ? 64 : Math.round(refY);
    }

    private void layout() {
        mx0 = 18;
        my0 = 24;
        mx1 = width - 18 - (showSidebar() ? SIDEBAR + 6 : 0);
        my1 = height - 30;
        if (editor != null) {
            editor.layout();
        }
    }

    private double worldX(double sx) {
        return centerX + (sx - (mx0 + mx1) / 2.0) / scale();
    }

    /** The z under a screen row, on flat ground at the reference height (the 3D view's ground plane). */
    private double worldZ(double sy) {
        return centerZ + (sy - (my0 + my1) / 2.0) / depthScale();
    }

    /** The z of the land drawn at a screen point: in the 3D view, the block row actually under the cursor. */
    private double worldZ(double sx, double sy) {
        if (is3d()) {
            int z = view3d.zAt((int) Math.floor(sx) - mx0, (int) Math.floor(sy) - my0);
            if (z != Integer.MIN_VALUE) {
                return z + 0.5;
            }
        }
        return worldZ(sy);
    }

    private float screenX(double wx) {
        return (float) ((mx0 + mx1) / 2.0 + (wx - centerX) * scale());
    }

    private float screenY(double wz) {
        return (float) ((my0 + my1) / 2.0 + (wz - centerZ) * depthScale());
    }

    /** Screen y of a point at height wy (raised in the 3D view). */
    private float screenY(double wz, double wy) {
        float y = screenY(wz);
        return is3d() ? y - (float) ((wy - ref()) * scale() * MapView3D.RISE) : y;
    }

    private boolean inMap(double x, double y) {
        return x >= mx0 && x < mx1 && y >= my0 && y < my1;
    }

    @Override
    protected void init() {
        layout();
        if (optionsOpen) {
            buildOptions(); // the widgets were cleared with the resize
        }
        LocalPlayer p = Minecraft.getInstance().player;
        if (p != null && follow) {
            centerX = p.getX();
            centerZ = p.getZ();
        }
    }

    @Override
    public void tick() {
        LocalPlayer p = Minecraft.getInstance().player;
        if (p == null) {
            onClose();
        }
    }

    // ------------------------------------------------------------------ rendering
    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        g.fill(0, 0, width, height, 0xC0100C0A);
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        if (player == null) {
            return;
        }
        layout();
        buttons.clear();
        if (follow) {
            centerX = Mth.lerp(a, player.xo, player.getX());
            centerZ = Mth.lerp(a, player.zo, player.getZ());
        }
        float scale = scale();
        WfGui.window(g, font, title, 4, 6, width - 8, height - 10);

        // the map: parchment, explored terrain, grid, markers
        WfGui.sprite(g, PARCHMENT, mx0, my0, mx1 - mx0, my1 - my0);
        g.enableScissor(mx0, my0, mx1, my1);
        float cxs = (mx0 + mx1) / 2.0F;
        float cys = (my0 + my1) / 2.0F;
        float radius = (float) Math.hypot(mx1 - mx0, my1 - my0) / 2.0F;
        boolean tilted = is3d();
        if (tilted) {
            terrain3d(g, player, scale);
        } else {
            MapRenderer.tiles(g, centerX, centerZ, scale, cxs, cys, 0, radius);
            grid(g, scale);
        }
        markers = visibleMarkers();
        float markerSize = MapRenderer.worldMarker(zoom);
        ClientMap.Marker hover = inMap(mouseX, mouseY) && menu == null && editor == null && !inOptions(mouseX, mouseY)
                ? markerAt(mouseX, mouseY) : null;
        for (ClientMap.Marker m : markers) {
            int sx = Math.round(screenX(m.x()));
            int sy = Math.round(screenY(m.z(), m.y()));
            if (m == selected || selected != null && m.ref() != null && m.ref().equals(selected.ref()) && m.kind() == selected.kind()) {
                MapRenderer.ring(g, sx, sy, Math.round(markerSize * 0.75F), 0xFFF6C343);
            }
            MapRenderer.marker(g, m, sx, sy, false, markerSize);
            int below = Math.round(markerSize / 2) + 2;
            if (scale >= 1.0F && (m.kind() == ClientMap.Kind.WAYPOINT || m.kind() == ClientMap.Kind.WAYSTONE)) {
                String label = m.label();
                int lw = font.width(label);
                g.fill(sx - lw / 2 - 2, sy + below, sx + lw / 2 + 2, sy + below + 10, 0x90100C0A);
                g.centeredText(font, label, sx, sy + below + 1, m.kind() == ClientMap.Kind.WAYPOINT ? 0xFF000000 | m.color() : WfGui.AETHER);
            }
        }
        float yaw = player.getViewYRot(a);
        MapRenderer.arrow(g, screenX(Mth.lerp(a, player.xo, player.getX())),
                screenY(Mth.lerp(a, player.zo, player.getZ()), Mth.lerp(a, player.yo, player.getY())),
                (float) Math.toRadians(yaw + 180.0), MapRenderer.worldArrow(zoom));
        g.disableScissor();
        WfGui.sprite(g, FRAME, mx0 - 4, my0 - 4, mx1 - mx0 + 8, my1 - my0 + 8);
        Component chip = tilted ? Component.translatable("gui.wayfarers.map.view_3d")
                : ClientMap.caveActive() ? Component.translatable("gui.wayfarers.map.cave_view") : null;
        if (chip != null) {
            int cw = font.width(chip) + 10;
            WfGui.sprite(g, Wayfarers.id("map/plate"), mx0 + 4, my0 + 4, cw, 13);
            g.text(font, chip, mx0 + 9, my0 + 7, WfGui.AETHER, false);
        }

        // tool buttons, top right of the map
        int bx = mx1 - 20;
        int by = my0 + 4;
        toolButton(g, "center", bx, by, mouseX, mouseY, () -> follow = true, "gui.wayfarers.map.center");
        toolButton(g, "zoom_in", bx, by + 19, mouseX, mouseY, () -> zoomAt(1, cxs, cys), "gui.wayfarers.map.zoom_in");
        toolButton(g, "zoom_out", bx, by + 38, mouseX, mouseY, () -> zoomAt(-1, cxs, cys), "gui.wayfarers.map.zoom_out");
        toolButton(g, "cave", bx, by + 57, mouseX, mouseY, () -> {
            WayfarersClientConfig.CAVE_MAP.set(!WayfarersClientConfig.CAVE_MAP.get());
            WayfarersClientConfig.CAVE_MAP.save();
        }, WayfarersClientConfig.CAVE_MAP.get() ? "gui.wayfarers.map.cave_on" : "gui.wayfarers.map.cave_off");
        int ty = by + 76;
        if (width >= 360) {
            toolButton(g, "list", bx, ty, mouseX, mouseY, () -> sidebarOpen = !sidebarOpen, "gui.wayfarers.map.sidebar");
            ty += 19;
        }
        toolButton(g, "view3d", bx, ty, mouseX, mouseY, () -> set3d(!is3d()),
                tilted ? "gui.wayfarers.map.view3d_on" : "gui.wayfarers.map.view3d_off");
        toolButton(g, "options", bx, ty + 19, mouseX, mouseY, () -> {
            if (optionsOpen) {
                closeOptions();
            } else {
                openOptions();
            }
        }, "gui.wayfarers.map.options");

        statusBar(g, mouseX, mouseY, scale);
        if (showSidebar()) {
            sidebar(g, mouseX, mouseY, player);
        }
        cardRect = null;
        if (selected != null) {
            card(g, mouseX, mouseY, player);
        }
        if (optionsOpen) {
            // the minimap itself, live, in its corner: every change of the panel shows at once
            if (WayfarersClientConfig.MINIMAP.get()) {
                MinimapHud.draw(g, a);
            }
            optionsPanel(g);
        }
        super.extractRenderState(g, mouseX, mouseY, a);
        if (menu != null) {
            contextMenu(g, mouseX, mouseY);
        }
        if (editor != null) {
            editorButtons = buttons.size();
            editorPanel(g, mouseX, mouseY);
            editor.name.extractRenderState(g, mouseX, mouseY, a);
        }
        if (hover != null) {
            tooltip(g, hover, mouseX, mouseY, player);
        }
    }

    private List<ClientMap.Marker> visibleMarkers() {
        List<ClientMap.Marker> out = new ArrayList<>();
        for (ClientMap.Marker m : ClientMap.markers()) {
            if (!ClientMap.HIDDEN[m.kind().ordinal()]) {
                out.add(m);
            }
        }
        // players and pings on top
        out.sort(Comparator.comparingInt(m -> -m.kind().ordinal()));
        return out;
    }

    private ClientMap.Marker markerAt(double x, double y) {
        ClientMap.Marker best = null;
        double reach = Math.max(6.0, MapRenderer.worldMarker(zoom) * 0.75);
        double bestD = reach * reach;
        for (ClientMap.Marker m : markers) {
            double dx = screenX(m.x()) - x;
            double dy = screenY(m.z(), m.y()) - y;
            double d = dx * dx + dy * dy;
            if (d <= bestD) {
                bestD = d;
                best = m;
            }
        }
        return best;
    }

    /** Faint ink lines: regions (256 blocks) when zoomed out, chunks when zoomed in. */
    private void grid(GuiGraphicsExtractor g, float scale) {
        int step = scale >= 2.0F ? 16 : scale >= 0.25F ? 256 : 1024;
        int color = scale >= 2.0F ? 0x18000000 : 0x28000000;
        double x0 = worldX(mx0);
        double x1 = worldX(mx1);
        double z0 = worldZ(my0);
        double z1 = worldZ(my1);
        for (long gx = (long) Math.floor(x0 / step) * step; gx <= x1; gx += step) {
            int sx = Math.round(screenX(gx));
            g.fill(sx, my0, sx + 1, my1, color);
        }
        for (long gz = (long) Math.floor(z0 / step) * step; gz <= z1; gz += step) {
            int sy = Math.round(screenY(gz));
            g.fill(mx0, sy, mx1, sy + 1, color);
        }
    }

    private void toolButton(GuiGraphicsExtractor g, String glyph, int x, int y, int mouseX, int mouseY, Runnable action, String tip) {
        boolean hover = mouseX >= x && mouseX < x + 16 && mouseY >= y && mouseY < y + 16 && menu == null && editor == null
                && !inOptions(mouseX, mouseY);
        WfGui.sprite(g, WfGui.id(hover ? "button_small_hover" : "button_small"), x, y, 16, 16);
        WfGui.sprite(g, Wayfarers.id("map/glyph/" + glyph), x + 3, y + 3, 10, 10);
        buttons.add(new Btn(x, y, 16, 16, action));
        if (hover) {
            g.setTooltipForNextFrame(font, Component.translatable(tip), mouseX, mouseY);
        }
    }

    /** A brass text button; registered for clicks. */
    private void textButton(GuiGraphicsExtractor g, Component label, int x, int y, int w, int mouseX, int mouseY, Runnable action) {
        boolean hover = mouseX >= x && mouseX < x + w && mouseY >= y && mouseY < y + 14;
        WfGui.sprite(g, hover ? WfGui.BUTTON_HOVER : WfGui.BUTTON, x, y, w, 14);
        g.centeredText(font, label, x + w / 2, y + 3, 0xFFFFF4DC);
        buttons.add(new Btn(x, y, w, 14, action));
    }

    private void statusBar(GuiGraphicsExtractor g, int mouseX, int mouseY, float scale) {
        int y = my1 + 7;
        String left;
        if (inMap(mouseX, mouseY)) {
            int wx = Mth.floor(worldX(mouseX));
            int wz = Mth.floor(worldZ(mouseX, mouseY));
            MapLayer cave = ClientMap.cave();
            Object[] col = cave != null ? cave.columnAt(wx, wz) : null;
            if (col == null && ClientMap.layer() != null) {
                col = ClientMap.layer().columnAt(wx, wz);
            }
            if (col != null) {
                Component biome = col[1] == null ? Component.empty() : MapPalette.biomeName((String) col[1]);
                left = Component.translatable("gui.wayfarers.map.cursor", wx, col[0], wz, biome).getString();
            } else {
                left = Component.translatable("gui.wayfarers.map.cursor_unknown", wx, wz).getString();
            }
        } else {
            left = hint(mx1 - mx0 - 90);
        }
        WfGui.textClipped(g, font, left, mx0, y, mx1 - mx0 - 90, WfGui.INK, false);
        String sc = scale >= 1.0F ? Component.translatable("gui.wayfarers.map.scale_in", (int) scale).getString()
                : Component.translatable("gui.wayfarers.map.scale_out", Math.round(1.0F / scale)).getString();
        g.text(font, sc, mx1 - font.width(sc), y, WfGui.INK_SOFT, false);
    }

    /**
     * The controls hint. When it is wider than the status bar (narrow windows, French), its " - " separated parts
     * are shown a few at a time, in turn, instead of being cut off.
     */
    private String hint(int width) {
        String full = Component.translatable("gui.wayfarers.map.hint").getString();
        if (font.width(full) <= width) {
            return full;
        }
        List<String> pages = new ArrayList<>();
        StringBuilder line = new StringBuilder();
        for (String part : full.split(" - ")) {
            String next = line.isEmpty() ? part : line + " - " + part;
            if (!line.isEmpty() && font.width(next) > width) {
                pages.add(line.toString());
                line = new StringBuilder(part);
            } else {
                line = new StringBuilder(next);
            }
        }
        if (!line.isEmpty()) {
            pages.add(line.toString());
        }
        return pages.get((int) (System.currentTimeMillis() / 3000 % pages.size()));
    }

    // ------------------------------------------------------------------ side panel
    private void sidebar(GuiGraphicsExtractor g, int mouseX, int mouseY, LocalPlayer player) {
        int x = mx1 + 6;
        int w = width - 18 - x;
        int y = my0 - 4;
        int h = my1 - my0 + 8;
        WfGui.sprite(g, WfGui.INSET, x, y, w, h);
        g.text(font, WfGui.bold(Component.translatable("gui.wayfarers.map.legend")), x + 6, y + 5, WfGui.GOLD, true);
        int ly = y + 16;
        for (ClientMap.Kind k : ClientMap.Kind.values()) {
            boolean hidden = ClientMap.HIDDEN[k.ordinal()];
            boolean hover = mouseX >= x + 3 && mouseX < x + w - 3 && mouseY >= ly && mouseY < ly + 11;
            if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, x + 3, ly, w - 6, 11);
            }
            Identifier icon = k == ClientMap.Kind.WAYPOINT ? Wayfarers.id("map/wp/flag") : Wayfarers.id("map/marker/" + k.name().toLowerCase(Locale.ROOT));
            int tint = k == ClientMap.Kind.WAYPOINT ? 0xFFE0483B : -1;
            g.blitSprite(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, icon, x + 6, ly + 1, 9, 9, hidden ? 0x60FFFFFF & tint : tint);
            Component label = Component.translatable("gui.wayfarers.map.kind." + k.name().toLowerCase(Locale.ROOT));
            g.text(font, hidden ? label.copy().withStyle(ChatFormatting.STRIKETHROUGH) : label, x + 18, ly + 2,
                    hidden ? WfGui.MUTED : WfGui.CREAM, true);
            int kind = k.ordinal();
            buttons.add(new Btn(x + 3, ly, w - 6, 11, () -> ClientMap.HIDDEN[kind] = !ClientMap.HIDDEN[kind]));
            ly += 11;
        }
        ly += 4;
        g.fill(x + 5, ly, x + w - 5, ly + 1, 0xFF7C5A2B);
        ly += 4;
        g.text(font, WfGui.bold(Component.translatable("gui.wayfarers.map.waypoints")), x + 6, ly, WfGui.GOLD, true);
        ly += 11;
        List<MapProtocol.Waypoint> list = new ArrayList<>();
        for (MapProtocol.Waypoint wp : ClientMap.waypoints()) {
            if (wp.dim().equals(ClientMap.dimension())) {
                list.add(wp);
            }
        }
        list.sort(Comparator.comparingDouble(wp -> distSq(player, wp.x(), wp.z())));
        int bottom = y + h - 22;
        int rows = Math.max(1, (bottom - ly) / ROW);
        listScroll = Math.max(0, Math.min(listScroll, list.size() - rows));
        if (list.isEmpty()) {
            g.textWithWordWrap(font, Component.translatable("gui.wayfarers.map.no_waypoints"), x + 6, ly + 2, w - 12, WfGui.CREAM_SOFT, true);
        }
        for (int i = 0; i < rows && i + listScroll < list.size(); i++) {
            MapProtocol.Waypoint wp = list.get(i + listScroll);
            int ry = ly + i * ROW;
            boolean hover = mouseX >= x + 3 && mouseX < x + w - 3 && mouseY >= ry && mouseY < ry + ROW;
            boolean sel = selected != null && wp.equals(selected.ref());
            if (sel) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, x + 3, ry, w - 6, ROW);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, x + 3, ry, w - 6, ROW);
            }
            g.blitSprite(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED,
                    Wayfarers.id("map/wp/" + MapProtocol.ICONS[wp.icon()]), x + 5, ry + 1, 9, 9, 0xFF000000 | wp.color());
            String dist = distance(player, wp.x(), wp.z());
            int dw = font.width(dist);
            WfGui.textClipped(g, font, wp.name(), x + 17, ry + 2, w - 26 - dw, ClientMap.mine(wp) ? WfGui.CREAM : WfGui.AETHER, true);
            g.text(font, dist, x + w - 6 - dw, ry + 2, WfGui.CREAM_SOFT, true);
            buttons.add(new Btn(x + 3, ry, w - 6, ROW, () -> {
                follow = false;
                centerX = wp.x() + 0.5;
                centerZ = wp.z() + 0.5;
                select(wp);
            }));
        }
        textButton(g, Component.translatable("gui.wayfarers.map.add_here"), x + 4, y + h - 18, w - 8, mouseX, mouseY,
                () -> openEditor(null, player.getBlockX(), player.getBlockY(), player.getBlockZ()));
    }

    private void select(MapProtocol.Waypoint wp) {
        for (ClientMap.Marker m : ClientMap.markers()) {
            if (wp.equals(m.ref())) {
                selected = m;
            }
        }
    }

    private static double distSq(LocalPlayer p, int x, int z) {
        double dx = p.getX() - x - 0.5;
        double dz = p.getZ() - z - 0.5;
        return dx * dx + dz * dz;
    }

    private static String distance(LocalPlayer p, double x, double z) {
        double d = Math.sqrt(distSq(p, (int) Math.floor(x), (int) Math.floor(z)));
        return d >= 1000 ? String.format(Locale.ROOT, "%.1f km", d / 1000.0) : (int) d + " m";
    }

    // ------------------------------------------------------------------ marker card
    private void card(GuiGraphicsExtractor g, int mouseX, int mouseY, LocalPlayer player) {
        ClientMap.Marker m = refreshSelected();
        if (m == null) {
            selected = null;
            return;
        }
        boolean ownWaypoint = m.ref() instanceof MapProtocol.Waypoint w && (ClientMap.mine(w) || isOp(player));
        int w = 180; // three buttons that fit "Supprimer" / "Partager"
        int h = ownWaypoint ? 66 : 46;
        int x = mx0 + 6;
        int y = my1 - h - 6;
        cardRect = new int[] {x, y, x + w, y + h};
        WfGui.sprite(g, WfGui.CARD, x, y, w, h);
        MapRenderer.marker(g, m, x + 10, y + 10, false);
        String label = m.label() == null ? "" : m.label();
        WfGui.titleClipped(g, font, label, x + 19 + Math.min(w - 40, font.width(WfGui.bold(Component.literal(label)))) / 2, y + 6,
                w - 40, WfGui.INK);
        buttons.add(new Btn(x + w - 13, y + 3, 10, 10, () -> selected = null));
        g.text(font, "x", x + w - 10, y + 3, WfGui.INK_SOFT, false);
        String line2 = Component.translatable("gui.wayfarers.map.one." + m.kind().name().toLowerCase(Locale.ROOT)).getString()
                + (m.detail() != null && m.kind() != ClientMap.Kind.WAYSTONE && m.kind() != ClientMap.Kind.GRAVE ? " - " + m.detail() : "");
        WfGui.textClipped(g, font, line2, x + 6, y + 18, w - 12, WfGui.INK_SOFT, false);
        g.text(font, ClientMap.coords((int) Math.floor(m.x()), (int) Math.floor(m.y()), (int) Math.floor(m.z())) + "   "
                + distance(player, m.x(), m.z()), x + 6, y + 30, WfGui.INK_SOFT, false);
        if (m.ref() instanceof MapProtocol.Waypoint wp && ownWaypoint) {
            int bw = (w - 16) / 3;
            textButton(g, Component.translatable("gui.wayfarers.map.edit"), x + 5, y + h - 19, bw, mouseX, mouseY,
                    () -> openEditor(wp, wp.x(), wp.y(), wp.z()));
            textButton(g, Component.translatable(wp.shared() ? "gui.wayfarers.map.make_private" : "gui.wayfarers.map.share"),
                    x + 8 + bw, y + h - 19, bw, mouseX, mouseY, () -> ClientMap.editWaypoint(wp, wp.name(), wp.color(), wp.icon(), !wp.shared()));
            textButton(g, Component.translatable("gui.wayfarers.map.delete"), x + 11 + bw * 2, y + h - 19, bw, mouseX, mouseY, () -> {
                ClientMap.deleteWaypoint(wp);
                selected = null;
            });
        }
    }

    /** The selected marker as it is now (waypoints may have been edited by the server meanwhile). */
    private ClientMap.Marker refreshSelected() {
        for (ClientMap.Marker m : markers) {
            if (m.kind() == selected.kind() && sameThing(m, selected)) {
                return m;
            }
        }
        return null;
    }

    private static boolean sameThing(ClientMap.Marker a, ClientMap.Marker b) {
        if (a.ref() instanceof MapProtocol.Waypoint wa && b.ref() instanceof MapProtocol.Waypoint wb) {
            return wa.id().equals(wb.id());
        }
        if (a.ref() instanceof MapProtocol.Waystone sa && b.ref() instanceof MapProtocol.Waystone sb) {
            return sa.id().equals(sb.id());
        }
        if (a.kind() == ClientMap.Kind.PLAYER) {
            return a.label().equals(b.label());
        }
        return Math.abs(a.x() - b.x()) < 1 && Math.abs(a.z() - b.z()) < 1;
    }

    private static boolean isOp(LocalPlayer p) {
        return p.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER);
    }

    private void tooltip(GuiGraphicsExtractor g, ClientMap.Marker m, int mouseX, int mouseY, LocalPlayer player) {
        List<FormattedCharSequence> lines = new ArrayList<>();
        int color = m.kind() == ClientMap.Kind.WAYPOINT ? m.color() : m.kind() == ClientMap.Kind.WAYSTONE ? WfGui.AETHER : WfGui.GOLD;
        lines.add(Component.literal(m.label() == null ? "" : m.label()).withColor(color & 0xFFFFFF).getVisualOrderText());
        if (m.detail() != null && m.kind() != ClientMap.Kind.WAYSTONE) {
            lines.add(Component.literal(m.detail()).withStyle(ChatFormatting.GRAY).getVisualOrderText());
        }
        lines.add(Component.literal(ClientMap.coords((int) Math.floor(m.x()), (int) Math.floor(m.y()), (int) Math.floor(m.z()))
                + " - " + distance(player, m.x(), m.z())).withStyle(ChatFormatting.GRAY).getVisualOrderText());
        g.setTooltipForNextFrame(font, lines, mouseX, mouseY);
    }

    // ------------------------------------------------------------------ context menu and editor
    private void openMenu(int x, int y) {
        int wx = Mth.floor(worldX(x));
        int wz = Mth.floor(worldZ(x, y));
        int wy = groundY(wx, wz);
        List<Component> labels = new ArrayList<>();
        List<Runnable> actions = new ArrayList<>();
        ClientMap.Marker m = markerAt(x, y);
        LocalPlayer player = Minecraft.getInstance().player;
        if (m != null && m.ref() instanceof MapProtocol.Waypoint wp && player != null && (ClientMap.mine(wp) || isOp(player))) {
            labels.add(Component.translatable("gui.wayfarers.map.edit"));
            actions.add(() -> openEditor(wp, wp.x(), wp.y(), wp.z()));
            labels.add(Component.translatable(wp.shared() ? "gui.wayfarers.map.make_private" : "gui.wayfarers.map.share"));
            actions.add(() -> ClientMap.editWaypoint(wp, wp.name(), wp.color(), wp.icon(), !wp.shared()));
            labels.add(Component.translatable("gui.wayfarers.map.delete"));
            actions.add(() -> ClientMap.deleteWaypoint(wp));
        }
        labels.add(Component.translatable("gui.wayfarers.map.add_waypoint"));
        actions.add(() -> openEditor(null, wx, wy, wz));
        labels.add(Component.translatable("gui.wayfarers.map.ping"));
        actions.add(() -> ClientMap.ping(wx, wy, wz));
        labels.add(Component.translatable("gui.wayfarers.map.copy"));
        actions.add(() -> Minecraft.getInstance().keyboardHandler.setClipboard(wx + " " + wy + " " + wz));
        int w = 0;
        for (Component c : labels) {
            w = Math.max(w, font.width(c));
        }
        int mw = w + 16;
        int mh = labels.size() * 12 + 6;
        menu = new ContextMenu(Math.min(x, width - mw - 4), Math.min(y, height - mh - 4), wx, wz, labels, actions);
    }

    private int groundY(int wx, int wz) {
        MapLayer cave = ClientMap.cave();
        Object[] col = cave != null ? cave.columnAt(wx, wz) : null;
        if (col == null && ClientMap.layer() != null) {
            col = ClientMap.layer().columnAt(wx, wz);
        }
        LocalPlayer p = Minecraft.getInstance().player;
        return col != null ? (Integer) col[0] + 1 : p != null ? p.getBlockY() : 64;
    }

    private void contextMenu(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        int w = 0;
        for (Component c : menu.labels()) {
            w = Math.max(w, font.width(c));
        }
        w += 16;
        int h = menu.labels().size() * 12 + 6;
        WfGui.sprite(g, WfGui.CARD, menu.x(), menu.y(), w, h);
        for (int i = 0; i < menu.labels().size(); i++) {
            int ry = menu.y() + 3 + i * 12;
            boolean hover = mouseX >= menu.x() + 2 && mouseX < menu.x() + w - 2 && mouseY >= ry && mouseY < ry + 12;
            if (hover) {
                g.fill(menu.x() + 2, ry, menu.x() + w - 2, ry + 12, 0x40B58A45);
            }
            g.text(font, menu.labels().get(i), menu.x() + 8, ry + 2, WfGui.INK, false);
        }
    }

    private void openEditor(MapProtocol.Waypoint w, int x, int y, int z) {
        menu = null;
        if (editor != null) {
            editor.close();
        }
        editor = new Editor(w, x, y, z);
    }

    private void editorPanel(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        int x = editor.left();
        int y = editor.top();
        int w = 200;
        int h = 132;
        g.fill(mx0, my0, mx1, my1, 0x60100C0A);
        WfGui.sprite(g, WfGui.PANEL, x, y, w, h);
        // bold ink on the parchment, without the drop shadow that smudged it
        WfGui.centered(g, font, WfGui.bold(Component.translatable(editor.editing == null ? "gui.wayfarers.map.new_waypoint"
                : "gui.wayfarers.map.edit_waypoint")), x + w / 2, y + 10, WfGui.INK);
        // colours
        int cy = y + 42;
        for (int i = 0; i < WAYPOINT_COLORS.length; i++) {
            int sx = x + 20 + i * 16;
            int col = WAYPOINT_COLORS[i];
            boolean sel = editor.color == col;
            g.fill(sx - 1, cy - 1, sx + 13, cy + 13, sel ? 0xFFF6C343 : 0xFF3B2A1A);
            g.fill(sx, cy, sx + 12, cy + 12, 0xFF000000 | col);
            buttons.add(new Btn(sx, cy, 12, 12, () -> editor.color = col));
        }
        // icons
        int iy = y + 60;
        for (int i = 0; i < MapProtocol.ICONS.length; i++) {
            int sx = x + 20 + i * 18;
            boolean sel = editor.icon == i;
            WfGui.sprite(g, WfGui.id(sel ? "button_small_hover" : "button_small"), sx, iy, 15, 15);
            g.blitSprite(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED, Wayfarers.id("map/wp/" + MapProtocol.ICONS[i]),
                    sx + 3, iy + 3, 9, 9, 0xFF000000 | editor.color);
            int icon = i;
            buttons.add(new Btn(sx, iy, 15, 15, () -> editor.icon = icon));
        }
        // shared toggle
        int ty = y + 82;
        boolean hover = mouseX >= x + 20 && mouseX < x + w - 20 && mouseY >= ty && mouseY < ty + 11;
        g.fill(x + 20, ty, x + 31, ty + 11, 0xFF3B2A1A);
        g.fill(x + 21, ty + 1, x + 30, ty + 10, hover ? 0xFFF3E6C6 : 0xFFE3D0A8);
        if (editor.shared) {
            g.fill(x + 23, ty + 3, x + 28, ty + 8, 0xFF2F8A2A);
        }
        g.text(font, Component.translatable("gui.wayfarers.map.share_toggle"), x + 35, ty + 2, WfGui.INK, false);
        buttons.add(new Btn(x + 20, ty, w - 40, 11, () -> editor.shared = !editor.shared));
        g.text(font, ClientMap.coords(editor.x, editor.y, editor.z), x + 20, ty + 15, WfGui.INK_SOFT, false);
        textButton(g, Component.translatable("gui.wayfarers.map.save"), x + 20, y + h - 22, 76, mouseX, mouseY, editor::save);
        textButton(g, Component.translatable("gui.cancel"), x + w - 96, y + h - 22, 76, mouseX, mouseY, editor::close);
    }

    // ------------------------------------------------------------------ input
    private void zoomAt(int delta, double sx, double sy) {
        int nz = Mth.clamp(zoom + delta, is3d() ? MIN_ZOOM_3D : MIN_ZOOM, MAX_ZOOM);
        if (nz == zoom) {
            return;
        }
        double wx = worldX(sx);
        double wz = worldZ(sy);
        zoom = nz;
        if (!follow) {
            centerX = wx - (sx - (mx0 + mx1) / 2.0) / scale();
            centerZ = wz - (sy - (my0 + my1) / 2.0) / depthScale();
        }
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double x = event.x();
        double y = event.y();
        if (editor != null) {
            for (Btn b : List.copyOf(buttons.subList(Math.min(editorButtons, buttons.size()), buttons.size()))) {
                if (b.hit(x, y)) {
                    b.action().run();
                    return true;
                }
            }
            return super.mouseClicked(event, doubleClick);
        }
        if (menu != null) {
            int w = 0;
            for (Component c : menu.labels()) {
                w = Math.max(w, font.width(c));
            }
            w += 16;
            for (int i = 0; i < menu.labels().size(); i++) {
                int ry = menu.y() + 3 + i * 12;
                if (x >= menu.x() && x < menu.x() + w && y >= ry && y < ry + 12) {
                    Runnable r = menu.actions().get(i);
                    menu = null;
                    r.run();
                    return true;
                }
            }
            menu = null;
            return true;
        }
        if (optionsOpen && inOptions(x, y)) {
            if (x >= optX + OPT_W - 22 && y < optY + 22) {
                closeOptions();
                return true;
            }
            super.mouseClicked(event, doubleClick);
            return true; // the panel's own background: not a click on the map or the buttons under it
        }
        if (event.button() == 0) {
            for (Btn b : List.copyOf(buttons)) {
                if (b.hit(x, y)) {
                    b.action().run();
                    return true;
                }
            }
        }
        if (cardRect != null && x >= cardRect[0] && x < cardRect[2] && y >= cardRect[1] && y < cardRect[3]) {
            return true;
        }
        if (inMap(x, y)) {
            if (event.button() == 1) {
                openMenu((int) x, (int) y);
                return true;
            }
            if (event.button() == 2) {
                int wx = Mth.floor(worldX(x));
                int wz = Mth.floor(worldZ(x, y));
                ClientMap.ping(wx, groundY(wx, wz), wz);
                return true;
            }
            if (event.button() == 0) {
                dragging = true;
                pressX = x;
                pressY = y;
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseDragged(MouseButtonEvent event, double dx, double dy) {
        if (dragging && editor == null) {
            if (Math.abs(event.x() - pressX) + Math.abs(event.y() - pressY) > 2) {
                if (follow) {
                    follow = false;
                }
                centerX -= dx / scale();
                centerZ -= dy / depthScale();
            }
            return true;
        }
        return super.mouseDragged(event, dx, dy);
    }

    @Override
    public boolean mouseReleased(MouseButtonEvent event) {
        if (dragging) {
            dragging = false;
            if (Math.abs(event.x() - pressX) + Math.abs(event.y() - pressY) <= 2) {
                selected = markerAt(event.x(), event.y());
            }
            return true;
        }
        return super.mouseReleased(event);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (editor != null) {
            return true;
        }
        if (optionsOpen && inOptions(x, y)) {
            return super.mouseScrolled(x, y, scrollX, scrollY);
        }
        if (showSidebar() && x >= mx1 + 6) {
            listScroll = Math.max(0, listScroll - (int) Math.signum(scrollY));
            return true;
        }
        if (inMap(x, y) && scrollY != 0) {
            zoomAt(scrollY > 0 ? 1 : -1, x, y);
            return true;
        }
        return false;
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (editor != null) {
            if (event.isEscape()) {
                editor.close();
                return true;
            }
            if (event.key() == 257 || event.key() == 335) {
                editor.save();
                return true;
            }
            return super.keyPressed(event);
        }
        if (menu != null && event.isEscape()) {
            menu = null;
            return true;
        }
        if (optionsOpen && event.isEscape()) {
            closeOptions();
            return true;
        }
        if (WayfarersClient.MAP_KEY.matches(event)) {
            onClose();
            return true;
        }
        if (event.key() == 32) {
            follow = true;
            return true;
        }
        if (event.key() == 61 || event.key() == 334) {
            zoomAt(1, (mx0 + mx1) / 2.0, (my0 + my1) / 2.0);
            return true;
        }
        if (event.key() == 45 || event.key() == 333) {
            zoomAt(-1, (mx0 + mx1) / 2.0, (my0 + my1) / 2.0);
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void removed() {
        view3d.close();
        super.removed();
    }

    // ------------------------------------------------------------------ 3D view
    /** Turns the tilted view on or off (saved); it shows full regions only, so it zooms in to half a pixel per block. */
    public void set3d(boolean on) {
        WayfarersClientConfig.MAP_3D.set(on);
        WayfarersClientConfig.MAP_3D.save();
        if (on && zoom < MIN_ZOOM_3D) {
            zoom = MIN_ZOOM_3D;
        }
        refY = Float.NaN;
    }

    private void terrain3d(GuiGraphicsExtractor g, LocalPlayer player, float scale) {
        MapLayer base = ClientMap.layer();
        if (base == null) {
            return;
        }
        if (zoom < MIN_ZOOM_3D) {
            zoom = MIN_ZOOM_3D;
            scale = scale();
        }
        // the ground at the centre of the view sets the height drawn level with the centre line
        Object[] col = base.columnAt(Mth.floor(centerX), Mth.floor(centerZ));
        float target = col != null ? (Integer) col[0] : (float) player.getY();
        refY = Float.isNaN(refY) ? target : refY + (target - refY) * 0.15F;
        int[] r = MapView3D.regions(centerX, centerZ, scale, mx1 - mx0, my1 - my0, ref());
        for (int rz = r[1]; rz <= r[3]; rz++) {
            for (int rx = r[0]; rx <= r[2]; rx++) {
                ClientMap.want(rx, rz, true);
                MapTile t = base.peek(rx, rz);
                if (t != null && t.full != null) {
                    base.texture(t); // builds or refreshes it (throttled): the view reads its shaded pixels
                }
            }
        }
        view3d.draw(g, base, centerX, centerZ, scale, mx0, my0, mx1 - mx0, my1 - my0, ref());
    }

    // ------------------------------------------------------------------ options panel
    private boolean inOptions(double x, double y) {
        return optionsOpen && x >= optX && x < optX + OPT_W && y >= optY && y < optY + OPT_H;
    }

    /** Opens the options panel (the gear button; also the CI client test). */
    public void openOptions() {
        menu = null;
        optionsOpen = true;
        buildOptions();
    }

    private void closeOptions() {
        optionsOpen = false;
        for (AbstractWidget w : optionWidgets) {
            removeWidget(w);
        }
        optionWidgets.clear();
        sizeSlider = null;
    }

    private int optRow(int i) {
        return optY + OPT_HEAD + i * OPT_ROW + (i >= 8 ? OPT_SECTION : 0);
    }

    private <T extends AbstractWidget> T option(T w) {
        optionWidgets.add(addRenderableWidget(w));
        return w;
    }

    private static int sizeStep() {
        return (WayfarersClientConfig.minimapPixels() - WayfarersClientConfig.MINIMAP_MIN + WayfarersClientConfig.MINIMAP_STEP / 2)
                / WayfarersClientConfig.MINIMAP_STEP;
    }

    private static void flip(net.minecraftforge.common.ForgeConfigSpec.BooleanValue v) {
        v.set(!v.get());
        v.save();
    }

    /**
     * The panel's controls, on the side away from the minimap so the live minimap stays in view: shown, exact size
     * (slider, 4 px steps), presets, corner, shape, rotation, coordinates, opacity; then the relief and the contours.
     */
    private void buildOptions() {
        for (AbstractWidget w : optionWidgets) {
            removeWidget(w);
        }
        optionWidgets.clear();
        WayfarersClientConfig.Corner corner = WayfarersClientConfig.MINIMAP_CORNER.get();
        boolean minimapLeft = corner == WayfarersClientConfig.Corner.TOP_LEFT || corner == WayfarersClientConfig.Corner.BOTTOM_LEFT;
        optX = minimapLeft ? width - OPT_W - 6 : 6;
        optY = Math.max(2, (height - OPT_H) / 2);
        int cx = optX + OPT_LABEL;
        int cw = OPT_W - OPT_LABEL - OPT_PAD;
        option(new WfWidgets.Toggle(cx, optRow(0) + 1, Component.translatable(S + "minimap"), Component.translatable(S + "minimap.tip"),
                WayfarersClientConfig.MINIMAP::get, () -> flip(WayfarersClientConfig.MINIMAP)));
        // exact size: 48 .. 160 px in steps of 4, ticks under the presets
        int min = WayfarersClientConfig.MINIMAP_MIN;
        int stepPx = WayfarersClientConfig.MINIMAP_STEP;
        WayfarersClientConfig.MinimapSize[] presets = WayfarersClientConfig.MinimapSize.values();
        int[] marks = new int[presets.length];
        for (int i = 0; i < presets.length; i++) {
            marks[i] = (presets[i].outer - min) / stepPx;
        }
        sizeSlider = option(new WfWidgets.Stepper(cx, optRow(1) - 1, cw - 32, (WayfarersClientConfig.MINIMAP_MAX - min) / stepPx + 1,
                sizeStep(), st -> Component.literal((min + st * stepPx) + " px"), Component.translatable(O + "size.tip"),
                st -> WayfarersClientConfig.setMinimapPixels(min + st * stepPx)).marks(marks));
        int bw = (cw - (presets.length - 1) * 2) / presets.length;
        for (int i = 0; i < presets.length; i++) {
            WayfarersClientConfig.MinimapSize p = presets[i];
            option(new WfWidgets.Choice(cx + i * (bw + 2), optRow(2), bw, 14, Component.literal(String.valueOf(p.outer)),
                    Component.translatable(S + "minimap_size.tip.choice", MinimapHud.sizeName(p), p.outer),
                    () -> MinimapHud.isSize(p), () -> MinimapHud.setSize(p)));
        }
        int x = cx;
        for (WayfarersClientConfig.Corner c : WayfarersClientConfig.Corner.values()) {
            String key = c.name().toLowerCase(Locale.ROOT);
            Component text = Component.translatable(S + "minimap_corner." + key);
            option(new WfWidgets.Choice(x, optRow(3), 22, 14, text, text, () -> WayfarersClientConfig.MINIMAP_CORNER.get() == c, () -> {
                WayfarersClientConfig.MINIMAP_CORNER.set(c);
                WayfarersClientConfig.MINIMAP_CORNER.save();
                buildOptions(); // the panel moves away from the minimap
            }).iconOnly(WfGui.id("glyph/corner_" + key)));
            x += 24;
        }
        WayfarersClientConfig.MinimapShape[] shapes = WayfarersClientConfig.MinimapShape.values();
        int sw = (cw - 2) / shapes.length;
        for (int i = 0; i < shapes.length; i++) {
            WayfarersClientConfig.MinimapShape shape = shapes[i];
            String key = shape.name().toLowerCase(Locale.ROOT);
            option(new WfWidgets.Choice(cx + i * (sw + 2), optRow(4), sw, 14, Component.translatable(S + "minimap_shape." + key),
                    Component.translatable(S + "minimap_shape." + key + ".tip"), () -> WayfarersClientConfig.MINIMAP_SHAPE.get() == shape, () -> {
                        WayfarersClientConfig.MINIMAP_SHAPE.set(shape);
                        WayfarersClientConfig.MINIMAP_SHAPE.save();
                    }));
        }
        option(new WfWidgets.Toggle(cx, optRow(5) + 1, Component.translatable(S + "minimap_rotate"), Component.translatable(S + "minimap_rotate.tip"),
                WayfarersClientConfig.MINIMAP_ROTATE::get, () -> flip(WayfarersClientConfig.MINIMAP_ROTATE)));
        option(new WfWidgets.Toggle(cx, optRow(6) + 1, Component.translatable(S + "minimap_coords"), Component.translatable(S + "minimap_coords.tip"),
                WayfarersClientConfig.MINIMAP_COORDS::get, () -> flip(WayfarersClientConfig.MINIMAP_COORDS)));
        int opacity = (Math.max(30, Math.min(100, WayfarersClientConfig.MINIMAP_OPACITY.get())) - 30) / 10;
        option(new WfWidgets.Stepper(cx, optRow(7) - 1, cw - 32, 8, opacity, st -> Component.literal((30 + st * 10) + " %"),
                Component.translatable(S + "minimap_opacity.tip"), st -> {
                    WayfarersClientConfig.MINIMAP_OPACITY.set(30 + st * 10);
                    WayfarersClientConfig.MINIMAP_OPACITY.save();
                }));
        // the maps' relief (both maps; the textures are shaded again at once)
        WayfarersClientConfig.MapRelief[] reliefs = WayfarersClientConfig.MapRelief.values();
        int rw = (cw - (reliefs.length - 1) * 2) / reliefs.length;
        for (int i = 0; i < reliefs.length; i++) {
            WayfarersClientConfig.MapRelief rel = reliefs[i];
            String key = rel.name().toLowerCase(Locale.ROOT);
            option(new WfWidgets.Choice(cx + i * (rw + 2), optRow(8), rw, 14, Component.translatable(O + "relief." + key),
                    Component.translatable(O + "relief." + key + ".tip"), () -> WayfarersClientConfig.MAP_RELIEF.get() == rel, () -> {
                        WayfarersClientConfig.MAP_RELIEF.set(rel);
                        WayfarersClientConfig.MAP_RELIEF.save();
                    }));
        }
        option(new WfWidgets.Toggle(cx, optRow(9) + 1, Component.translatable(O + "contours"), Component.translatable(O + "contours.tip"),
                WayfarersClientConfig.MAP_CONTOURS::get, () -> flip(WayfarersClientConfig.MAP_CONTOURS)));
    }

    /** The panel's plate and labels (its widgets are drawn with the screen's). */
    private void optionsPanel(GuiGraphicsExtractor g) {
        if (sizeSlider != null) {
            sizeSlider.sync(sizeStep()); // a preset or Shift + H moved it
        }
        WfGui.sprite(g, WfGui.PANEL, optX, optY, OPT_W, OPT_H);
        WfGui.centered(g, font, WfGui.bold(Component.translatable(O + "title")), optX + OPT_W / 2, optY + 10, WfGui.INK);
        String[] labels = {O + "shown", S + "minimap_size", O + "presets", S + "minimap_corner", S + "minimap_shape",
                O + "rotate", S + "minimap_coords", S + "minimap_opacity", O + "relief", O + "contours"};
        for (int i = 0; i < labels.length; i++) {
            WfGui.textClipped(g, font, Component.translatable(labels[i]).getString(), optX + OPT_PAD, optRow(i) + 4, OPT_LABEL - OPT_PAD - 2, WfGui.INK, false);
        }
        int cx = optX + OPT_LABEL;
        int cw = OPT_W - OPT_LABEL - OPT_PAD;
        g.text(font, WayfarersClientConfig.minimapPixels() + " px", cx + cw - 29, optRow(1) + 4, WfGui.INK_SOFT, false);
        g.text(font, WayfarersClientConfig.MINIMAP_OPACITY.get() + " %", cx + cw - 29, optRow(7) + 4, WfGui.INK_SOFT, false);
        for (int i : new int[] {0, 5, 6, 9}) {
            boolean on = switch (i) {
                case 0 -> WayfarersClientConfig.MINIMAP.get();
                case 5 -> WayfarersClientConfig.MINIMAP_ROTATE.get();
                case 6 -> WayfarersClientConfig.MINIMAP_COORDS.get();
                default -> WayfarersClientConfig.MAP_CONTOURS.get();
            };
            g.text(font, Component.translatable("gui.wayfarers.machine." + (on ? "on" : "off")), cx + 30, optRow(i) + 4, WfGui.INK_SOFT, false);
        }
        // the maps' section, under a thin brass rule
        int sy = optRow(8) - OPT_SECTION;
        g.fill(optX + OPT_PAD, sy + 3, optX + OPT_W - OPT_PAD, sy + 4, 0xFF7C5A2B);
        WfGui.centered(g, font, WfGui.bold(Component.translatable(O + "relief_title")), optX + OPT_W / 2, sy + 5, WfGui.INK);
        // close (handled in mouseClicked: the panel covers the other buttons)
        g.text(font, "x", optX + OPT_W - 18, optY + 9, WfGui.INK_SOFT, false);
    }
}
