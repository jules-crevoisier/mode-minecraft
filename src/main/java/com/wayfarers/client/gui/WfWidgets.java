package com.wayfarers.client.gui;

import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.narration.NarrationElementOutput;
import net.minecraft.client.input.InputWithModifiers;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import org.jetbrains.annotations.Nullable;

import java.util.function.BooleanSupplier;
import java.util.function.IntConsumer;
import java.util.function.IntFunction;

/**
 * Controls of the Wayfarers theme for settings screens: option buttons that light up when chosen (text, icon or
 * dye swatch), a brass lever switch and a stepped slider. All of them take keyboard focus (Tab, Enter / Space,
 * arrow keys on the slider) and carry a tooltip.
 */
public final class WfWidgets {
    private WfWidgets() {}

    public static final Identifier BUTTON_ON = WfGui.id("button_on");

    /** Hovered, or focused from the keyboard (a mouse click also focuses a widget; that should not keep it lit). */
    public static boolean lit(net.minecraft.client.gui.components.AbstractWidget w) {
        return w.isHovered() || (w.isFocused() && net.minecraft.client.Minecraft.getInstance().getLastInputType().isKeyboard());
    }
    public static final Identifier BUTTON_ON_HOVER = WfGui.id("button_on_hover");

    /** One option of a group: brass plate, or a lit iron plate with a gold rim while it is the chosen one. */
    public static class Choice extends AbstractButton {
        private final BooleanSupplier selected;
        private final Runnable action;
        private @Nullable Identifier icon;
        private int iconSize;
        private boolean showLabel = true;
        private boolean toggles;
        private int swatch;
        private boolean isSwatch;
        private @Nullable BooleanSupplier marker;

        public Choice(int x, int y, int w, int h, Component label, Component tip, BooleanSupplier selected, Runnable action) {
            super(x, y, w, h, label);
            this.selected = selected;
            this.action = action;
            setTooltip(Tooltip.create(tip));
        }

        /** Shows a GUI sprite before the label (12x12, or 16x16 when the button is tall enough for it). */
        public Choice icon(Identifier sprite) {
            this.icon = sprite;
            return this;
        }

        /** Shows a GUI sprite of the given size before the label. */
        public Choice icon(Identifier sprite, int size) {
            this.icon = sprite;
            this.iconSize = size;
            return this;
        }

        /** Shows only the sprite; the label is still read by the narrator. */
        public Choice iconOnly(Identifier sprite) {
            this.icon = sprite;
            this.showLabel = false;
            return this;
        }

        /** Runs its action on every press, even while selected (on/off buttons, actions). */
        public Choice toggles() {
            this.toggles = true;
            return this;
        }

        /** Draws a dye-colour swatch instead of a plate. */
        public Choice swatch(int rgb) {
            this.swatch = 0xFF000000 | rgb;
            this.isSwatch = true;
            return this;
        }

        /** A small green dot in the top-right corner while {@code marker} is true (e.g. "a chest is on that side"). */
        public Choice marker(BooleanSupplier marker) {
            this.marker = marker;
            return this;
        }

        public void tip(Component tip) {
            setTooltip(Tooltip.create(tip));
        }

        public boolean isSelected() {
            return selected.getAsBoolean();
        }

        @Override
        public void onPress(InputWithModifiers input) {
            if (toggles || !isSelected()) {
                action.run();
            }
        }

        @Override
        protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
            int x = getX();
            int y = getY();
            int w = getWidth();
            int h = getHeight();
            boolean on = isSelected();
            boolean hover = active && lit(this);
            Font font = net.minecraft.client.Minecraft.getInstance().font;
            if (isSwatch) {
                if (on) {
                    g.fill(x - 2, y - 2, x + w + 2, y + h + 2, WfGui.GOLD);
                    g.fill(x - 1, y - 1, x + w + 1, y + h + 1, WfGui.PLATE_INK);
                } else if (hover) {
                    g.outline(x - 1, y - 1, w + 2, h + 2, 0xFFD9B25E);
                }
                g.fill(x, y, x + w, y + h, swatch);
                WfGui.sprite(g, WfGui.id("swatch_frame"), x, y, w, h);
                return;
            }
            Identifier plate = on ? (hover ? BUTTON_ON_HOVER : BUTTON_ON)
                    : !active ? WfGui.BUTTON_DISABLED : hover ? WfGui.BUTTON_HOVER : WfGui.BUTTON;
            WfGui.sprite(g, plate, x, y, w, h);
            Component label = getMessage();
            boolean hasLabel = showLabel && !label.getString().isEmpty();
            int iconSize = icon == null ? 0 : this.iconSize > 0 ? this.iconSize : (h >= 18 && w >= 18 && hasLabel ? 16 : 12);
            int textW = hasLabel ? font.width(label) : 0;
            int contentW = iconSize + (iconSize > 0 && hasLabel ? 2 : 0) + textW;
            int cx = x + (w - contentW + 1) / 2;
            if (icon != null) {
                WfGui.sprite(g, icon, cx, y + (h - iconSize) / 2, iconSize, iconSize);
                cx += iconSize + 2;
            }
            if (hasLabel) {
                int color = on ? WfGui.GOLD : !active ? 0xFFC9C0B4 : 0xFFFFFFFF;
                g.text(font, label, cx, y + (h - 8) / 2, color, true);
            }
            if (marker != null && marker.getAsBoolean()) {
                g.fill(x + w - 5, y + 1, x + w - 1, y + 5, 0xFF0F0C0A);
                g.fill(x + w - 4, y + 2, x + w - 2, y + 4, 0xFF7CE35A);
            }
        }

        @Override
        protected void updateWidgetNarration(NarrationElementOutput output) {
            defaultButtonNarrationText(output);
        }
    }

    /** A brass lever switch (26x14): knob left = off, knob right on a lit groove = on. */
    public static class Toggle extends AbstractButton {
        private final BooleanSupplier on;
        private final Runnable action;

        public Toggle(int x, int y, Component label, Component tip, BooleanSupplier on, Runnable action) {
            super(x, y, 26, 14, label);
            this.on = on;
            this.action = action;
            setTooltip(Tooltip.create(tip));
        }

        @Override
        public void onPress(InputWithModifiers input) {
            action.run();
        }

        @Override
        protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
            String name = (on.getAsBoolean() ? "toggle_on" : "toggle_off") + (lit(this) ? "_hover" : "");
            WfGui.sprite(g, WfGui.id(name), getX(), getY(), 26, 14);
        }

        @Override
        protected void updateWidgetNarration(NarrationElementOutput output) {
            defaultButtonNarrationText(output);
        }
    }

    /** A slider over {@code steps} fixed values: brass knob on an iron groove with a tick per step. */
    public static class Stepper extends AbstractSliderButton {
        private final int steps;
        private final IntConsumer onStep;
        private final IntFunction<Component> label;
        private int step;
        private boolean held;
        private int[] marks;

        public Stepper(int x, int y, int w, int steps, int initial, IntFunction<Component> label, Component tip, IntConsumer onStep) {
            super(x, y, w, 18, label.apply(initial), steps <= 1 ? 0 : initial / (double) (steps - 1));
            this.steps = steps;
            this.step = initial;
            this.label = label;
            this.onStep = onStep;
            setTooltip(Tooltip.create(tip));
        }

        public int step() {
            return step;
        }

        /** Draws a tick only under these steps (sliders with many steps: the presets), instead of one per step. */
        public Stepper marks(int... steps) {
            this.marks = steps;
            return this;
        }

        private boolean marked(int i) {
            for (int m : marks) {
                if (m == i) {
                    return true;
                }
            }
            return false;
        }

        /** The server's value, unless the player is dragging the knob right now. */
        public void sync(int serverStep) {
            if (!held && serverStep != step) {
                step = Mth.clamp(serverStep, 0, steps - 1);
                value = steps <= 1 ? 0 : step / (double) (steps - 1);
                updateMessage();
            }
        }

        @Override
        protected void updateMessage() {
            setMessage(label.apply(step));
        }

        @Override
        protected void applyValue() {
            int s = (int) Math.round(value * (steps - 1));
            if (s != step) {
                step = s;
                onStep.accept(s);
            }
        }

        @Override
        public void onClick(MouseButtonEvent event, boolean doubleClick) {
            held = true;
            super.onClick(event, doubleClick);
        }

        @Override
        public void onRelease(MouseButtonEvent event) {
            held = false;
            value = steps <= 1 ? 0 : step / (double) (steps - 1); // snap the knob onto its tick
            super.onRelease(event);
        }

        @Override
        public boolean keyPressed(KeyEvent event) {
            if (isFocused() && (event.isLeft() || event.isRight())) {
                int s = Mth.clamp(step + (event.isLeft() ? -1 : 1), 0, steps - 1);
                if (s != step) {
                    setValue(steps <= 1 ? 0 : s / (double) (steps - 1));
                }
                return true;
            }
            return super.keyPressed(event);
        }

        @Override
        public void extractWidgetRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
            int x = getX();
            int y = getY();
            int w = getWidth();
            WfGui.sprite(g, WfGui.id("slider_track"), x, y + 6, w, 6);
            for (int i = 0; i < steps; i++) {
                if (marks != null && i != step && !marked(i)) {
                    continue;
                }
                int tx = x + 4 + Math.round(i * (w - 8) / (float) Math.max(1, steps - 1));
                g.fill(tx, y + 14, tx + 1, y + 16, i == step ? 0xFFF6C343 : 0xFF7C5A2B);
            }
            if (isFocused() && net.minecraft.client.Minecraft.getInstance().getLastInputType().isKeyboard()) {
                g.outline(x - 1, y + 5, w + 2, 8, 0xFFF6C343);
            }
            int kx = x + (int) (value * (w - 8));
            WfGui.sprite(g, WfGui.id(lit(this) || held ? "slider_knob_hover" : "slider_knob"), kx, y + 2, 8, 14);
        }
    }
}
