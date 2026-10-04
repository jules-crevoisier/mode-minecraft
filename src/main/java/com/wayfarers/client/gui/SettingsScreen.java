package com.wayfarers.client.gui;

import com.wayfarers.config.WayfarersClientConfig;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.options.controls.KeyBindsScreen;
import net.minecraft.network.chat.Component;
import net.minecraftforge.common.ForgeConfigSpec;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * Wayfarers display settings (config/wayfarers-client.toml) in the mod's own theme, opened by the "Config" button
 * of the mods list: health bars, damage numbers, quest tracker, tip cards, and a shortcut to the key bindings.
 * Every change is saved at once.
 */
public class SettingsScreen extends Screen {
    private static final String K = "gui.wayfarers.settings.";
    private static final int W = 300;
    private static final int ROW_H = 22;
    private static final int ROWS = 5;
    private static final int H = 40 + ROWS * ROW_H + 30;
    private static final int CX = 120;

    private final @Nullable Screen parent;
    private final List<Component[]> rows = new ArrayList<>();
    private int left;
    private int top;

    public SettingsScreen(@Nullable Screen parent) {
        super(Component.translatable(K + "title"));
        this.parent = parent;
    }

    private int rowY(int i) {
        return top + 26 + i * ROW_H;
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
        rows.clear();
        // health bars: three choices
        row("health_bars");
        WayfarersClientConfig.HealthBars[] modes = WayfarersClientConfig.HealthBars.values();
        int x = left + CX;
        for (WayfarersClientConfig.HealthBars mode : modes) {
            String key = mode.name().toLowerCase(java.util.Locale.ROOT);
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
        row("keys");
        Component keys = Component.translatable(K + "keys.button");
        addRenderableWidget(new WfButton(left + CX, rowY(4), Math.max(60, font.width(keys) + 16), 18, keys,
                b -> minecraft.gui.setScreen(new KeyBindsScreen(this, minecraft.options))));
        addRenderableWidget(new WfButton(left + W / 2 - 50, top + H - 28, 100, 20, Component.translatable("gui.done"), b -> onClose()));
    }

    private void row(String key) {
        rows.add(new Component[] {Component.translatable(K + key), Component.translatable(K + key + ".tip")});
    }

    private void toggle(int i, String key, ForgeConfigSpec.BooleanValue value) {
        row(key);
        addRenderableWidget(new WfWidgets.Toggle(left + CX, rowY(i) + 2, rows.get(i)[0], rows.get(i)[1], value::get, () -> {
            value.set(!value.get());
            value.save();
        }));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, W, H);
        for (int i = 0; i < rows.size(); i++) {
            WfGui.textClipped(g, font, rows.get(i)[0].getString(), left + 12, rowY(i) + 5, CX - 16, WfGui.INK, false);
            if (i >= 1 && i <= 3) {
                boolean on = switch (i) {
                    case 1 -> WayfarersClientConfig.DAMAGE_NUMBERS.get();
                    case 2 -> WayfarersClientConfig.QUEST_TRACKER.get();
                    default -> WayfarersClientConfig.TIPS.get();
                };
                g.text(font, Component.translatable("gui.wayfarers.machine." + (on ? "on" : "off")), left + CX + 30, rowY(i) + 5,
                        WfGui.INK, false);
            }
        }
        super.extractRenderState(g, mouseX, mouseY, a);
        for (int i = 0; i < rows.size(); i++) {
            if (mouseX >= left + 12 && mouseX < left + CX - 4 && mouseY >= rowY(i) && mouseY < rowY(i) + 18) {
                g.setComponentTooltipForNextFrame(font, List.of(rows.get(i)[0], rows.get(i)[1]), mouseX, mouseY);
            }
        }
    }

    @Override
    public void onClose() {
        minecraft.gui.setScreen(parent);
    }
}
