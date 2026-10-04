package com.wayfarers.client.gui;

import com.wayfarers.client.WayfarersClient;
import com.wayfarers.client.map.MinimapHud;
import com.wayfarers.config.WayfarersClientConfig;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.options.controls.KeyBindsScreen;
import net.minecraft.network.chat.Component;
import net.minecraftforge.common.ForgeConfigSpec;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.BooleanSupplier;

/**
 * Wayfarers display settings (config/wayfarers-client.toml) in the mod's own theme, opened by the "Config" button
 * of the mods list. Two tabs: "Display" (health bars, damage numbers, quest tracker, tip cards, key bindings) and
 * "Minimap" (shown or not, size, corner, shape, rotation, coordinates, opacity). Every change is saved at once.
 */
public class SettingsScreen extends Screen {
    private static final String K = "gui.wayfarers.settings.";
    private static final int W = 360;
    private static final int ROW_H = 20;
    private static final int ROWS = 7;
    /** Y of the first row from the window top (under the title plate and the tab buttons). */
    private static final int FIRST = 42;
    /** The in-game keys line under the minimap rows. */
    private static final int HINT = 12;
    private static final int H = FIRST + ROWS * ROW_H + HINT + 28;
    /** X of the controls column from the window's left edge. */
    private static final int CX = 124;
    private static final int[] OPACITIES = {30, 40, 50, 60, 70, 80, 90, 100};

    /** The open tab (0 display, 1 minimap), kept while the game runs. */
    private static int tab;

    private final @Nullable Screen parent;
    /** Per row: name, tooltip, and the value of its switch (null when the row has no on/off switch). */
    private final List<Row> rows = new ArrayList<>();
    private int left;
    private int top;

    private record Row(Component name, Component tip, @Nullable BooleanSupplier on) {}

    public SettingsScreen(@Nullable Screen parent) {
        super(Component.translatable(K + "title"));
        this.parent = parent;
    }

    private int rowY(int i) {
        return top + FIRST + i * ROW_H;
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = WfGui.windowTop(height, H, 0);
        rows.clear();
        // the two tabs, side by side under the title plate
        Component[] tabs = {Component.translatable(K + "tab.display"), Component.translatable(K + "tab.minimap")};
        int tw = 0;
        for (Component t : tabs) {
            tw = Math.max(tw, font.width(t) + 16);
        }
        tw = Math.max(80, tw);
        for (int i = 0; i < tabs.length; i++) {
            int index = i;
            addRenderableWidget(new WfWidgets.Choice(left + W / 2 - tw - 2 + i * (tw + 4), top + 17, tw, 16, tabs[i],
                    Component.translatable(K + "tab." + (i == 0 ? "display" : "minimap") + ".tip"), () -> tab == index, () -> {
                        tab = index;
                        rebuildWidgets();
                    }));
        }
        if (tab == 0) {
            initDisplay();
        } else {
            initMinimap();
        }
        addRenderableWidget(new WfButton(left + W / 2 - 50, top + H - 26, 100, 20, Component.translatable("gui.done"), b -> onClose()));
    }

    private void initDisplay() {
        row("health_bars", null);
        int x = left + CX;
        for (WayfarersClientConfig.HealthBars mode : WayfarersClientConfig.HealthBars.values()) {
            String key = mode.name().toLowerCase(Locale.ROOT);
            Component text = Component.translatable(K + "health_bars." + key);
            int w = Math.max(18, font.width(text) + 10);
            addRenderableWidget(new WfWidgets.Choice(x, rowY(0), w, 18, text, Component.translatable(K + "health_bars." + key + ".tip"),
                    () -> WayfarersClientConfig.HEALTH_BARS.get() == mode, () -> {
                        WayfarersClientConfig.HEALTH_BARS.set(mode);
                        WayfarersClientConfig.HEALTH_BARS.save();
                    }));
            x += w + 2;
        }
        toggle(1, "damage_numbers", WayfarersClientConfig.DAMAGE_NUMBERS);
        toggle(2, "quest_tracker", WayfarersClientConfig.QUEST_TRACKER);
        toggle(3, "tips", WayfarersClientConfig.TIPS);
        row("keys", null);
        Component keys = Component.translatable(K + "keys.button");
        addRenderableWidget(new WfButton(left + CX, rowY(4), Math.max(60, font.width(keys) + 16), 18, keys,
                b -> minecraft.gui.setScreen(new KeyBindsScreen(this, minecraft.options))));
    }

    private void initMinimap() {
        toggle(0, "minimap", WayfarersClientConfig.MINIMAP);
        // size: four presets, named, with their size in pixels in the tooltip
        row("minimap_size", null);
        int x = left + CX;
        for (WayfarersClientConfig.MinimapSize size : WayfarersClientConfig.MinimapSize.values()) {
            Component text = MinimapHud.sizeName(size);
            int w = Math.max(18, font.width(text) + 10);
            addRenderableWidget(new WfWidgets.Choice(x, rowY(1), w, 18, text, Component.translatable(K + "minimap_size.tip.choice", text, size.outer),
                    () -> WayfarersClientConfig.MINIMAP_SIZE.get() == size, () -> MinimapHud.setSize(size)));
            x += w + 2;
        }
        // corner: four small buttons, each showing a screen with its corner lit
        row("minimap_corner", null);
        x = left + CX;
        for (WayfarersClientConfig.Corner corner : WayfarersClientConfig.Corner.values()) {
            String key = corner.name().toLowerCase(Locale.ROOT);
            Component text = Component.translatable(K + "minimap_corner." + key);
            addRenderableWidget(new WfWidgets.Choice(x, rowY(2), 22, 18, text, text,
                    () -> WayfarersClientConfig.MINIMAP_CORNER.get() == corner, () -> {
                        WayfarersClientConfig.MINIMAP_CORNER.set(corner);
                        WayfarersClientConfig.MINIMAP_CORNER.save();
                    }).iconOnly(WfGui.id("glyph/corner_" + key)));
            x += 24;
        }
        row("minimap_shape", null);
        x = left + CX;
        for (WayfarersClientConfig.MinimapShape shape : WayfarersClientConfig.MinimapShape.values()) {
            String key = shape.name().toLowerCase(Locale.ROOT);
            Component text = Component.translatable(K + "minimap_shape." + key);
            int w = Math.max(18, font.width(text) + 10);
            addRenderableWidget(new WfWidgets.Choice(x, rowY(3), w, 18, text, Component.translatable(K + "minimap_shape." + key + ".tip"),
                    () -> WayfarersClientConfig.MINIMAP_SHAPE.get() == shape, () -> {
                        WayfarersClientConfig.MINIMAP_SHAPE.set(shape);
                        WayfarersClientConfig.MINIMAP_SHAPE.save();
                    }));
            x += w + 2;
        }
        toggle(4, "minimap_rotate", WayfarersClientConfig.MINIMAP_ROTATE);
        toggle(5, "minimap_coords", WayfarersClientConfig.MINIMAP_COORDS);
        row("minimap_opacity", null);
        int current = 0;
        for (int i = 0; i < OPACITIES.length; i++) {
            if (OPACITIES[i] <= WayfarersClientConfig.MINIMAP_OPACITY.get()) {
                current = i;
            }
        }
        addRenderableWidget(new WfWidgets.Stepper(left + CX, rowY(6), 112, OPACITIES.length, current,
                s -> Component.literal(OPACITIES[s] + " %"), rows.get(6).tip(), s -> {
                    WayfarersClientConfig.MINIMAP_OPACITY.set(OPACITIES[s]);
                    WayfarersClientConfig.MINIMAP_OPACITY.save();
                }));
    }

    private void row(String key, @Nullable BooleanSupplier on) {
        rows.add(new Row(Component.translatable(K + key), Component.translatable(K + key + ".tip"), on));
    }

    private void toggle(int i, String key, ForgeConfigSpec.BooleanValue value) {
        row(key, value::get);
        addRenderableWidget(new WfWidgets.Toggle(left + CX, rowY(i) + 2, rows.get(i).name(), rows.get(i).tip(), value::get, () -> {
            value.set(!value.get());
            value.save();
        }));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, W, H);
        for (int i = 0; i < rows.size(); i++) {
            Row r = rows.get(i);
            WfGui.textClipped(g, font, r.name().getString(), left + 12, rowY(i) + 5, CX - 16, WfGui.INK, false);
            if (r.on() != null) {
                g.text(font, Component.translatable("gui.wayfarers.machine." + (r.on().getAsBoolean() ? "on" : "off")),
                        left + CX + 30, rowY(i) + 5, WfGui.INK_SOFT, false);
            }
        }
        if (tab == 1) {
            // the slider's own label is only read by the narrator: the value goes beside it
            g.text(font, WayfarersClientConfig.MINIMAP_OPACITY.get() + " %", left + CX + 118, rowY(6) + 5, WfGui.INK_SOFT, false);
            Component hint = Component.translatable(K + "minimap.keys", WayfarersClient.MINIMAP_KEY.getTranslatedKeyMessage(),
                    WayfarersClient.MINIMAP_ZOOM_KEY.getTranslatedKeyMessage());
            WfGui.centered(g, font, hint, left + W / 2, rowY(ROWS) + 2, WfGui.INK_SOFT);
        }
        super.extractRenderState(g, mouseX, mouseY, a);
        for (int i = 0; i < rows.size(); i++) {
            if (mouseX >= left + 12 && mouseX < left + CX - 4 && mouseY >= rowY(i) && mouseY < rowY(i) + 18) {
                g.setComponentTooltipForNextFrame(font, List.of(rows.get(i).name(), rows.get(i).tip()), mouseX, mouseY);
            }
        }
    }

    @Override
    public void onClose() {
        minecraft.gui.setScreen(parent);
    }
}
