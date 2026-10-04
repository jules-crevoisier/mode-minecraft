package com.wayfarers.client.gui;

import com.wayfarers.block.MachineBlock;
import com.wayfarers.block.MachineBlockEntity;
import com.wayfarers.client.ContainerButtons;
import com.wayfarers.client.MachineAreaPreview;
import com.wayfarers.menu.MachineMenu;
import com.wayfarers.network.ContainerActionMsg;
import com.wayfarers.network.WayfarersNet;
import com.wayfarers.util.ContainerActions;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import static com.wayfarers.menu.MachineMenu.*;

/**
 * The screen of every machine (one layout per kind, see {@link MachineMenu} for the shared geometry): a header with
 * the machine and what it does, a live status line with a coloured lamp, then one row per setting with clear
 * controls (option buttons, switches, a slider, dye swatches), each with a tooltip. Machines that store items show
 * their 9 slots on the right and the player inventory below. Every change goes to the server, which validates it;
 * the controls only light up once the server's value comes back.
 */
public class MachineScreen extends AbstractContainerScreen<MachineMenu> implements ContainerButtons.Exempt {
    private static final String K = "gui.wayfarers.machine.";
    private static final int LABEL_W = CX - LABEL_X - 4;
    private static final int[] OUTPUT_ORDER = {0, 1, 2, 3, 4, 5, 6, 7};
    private static final String[] OUTPUT_NAMES = {"auto", "down", "up", "north", "south", "west", "east", "keep"};

    private final MachineBlock.Kind kind;
    private final String kindKey;
    private final ItemStack icon;
    private final Component[] labels;
    private final Component[] labelTips;
    private List<FormattedCharSequence> descLines = List.of();
    private boolean descClipped;
    private final List<WfWidgets.Choice> outputs = new ArrayList<>();
    private final List<WfWidgets.Choice> pulses = new ArrayList<>();
    private WfWidgets.Choice filterMode;
    private WfWidgets.Choice takeXp;
    private WfWidgets.Stepper interval;
    private int signalLampX;

    public MachineScreen(MachineMenu menu, Inventory inv, Component title) {
        super(menu, inv, title, W, MachineMenu.height(menu.kind));
        this.kind = menu.kind;
        this.kindKey = kind.name().toLowerCase(Locale.ROOT);
        BlockState state = inv.player.level().getBlockState(menu.pos);
        this.icon = state.getBlock() instanceof MachineBlock ? new ItemStack(state.getBlock()) : ItemStack.EMPTY;
        int rows = MachineMenu.rows(kind);
        this.labels = new Component[rows];
        this.labelTips = new Component[rows];
        this.inventoryLabelY = -1000; // the inventory has a divider instead of a caption
    }

    // ------------------------------------------------------------------ setup
    @Override
    protected void init() {
        super.init();
        outputs.clear();
        pulses.clear();
        Component what = Component.translatable(K + "what." + kindKey);
        descLines = font.split(what, W - 36 - 10);
        descClipped = descLines.size() > 2;
        if (descClipped) {
            descLines = List.of(descLines.get(0), clip(descLines.get(1), W - 36 - 10));
        }
        switch (kind) {
            case HARVESTER -> {
                areaRow(0, "area");
                toggleRow(1, "replant", T_REPLANT, 1);
                outputRow(2);
                redstoneRow(3);
            }
            case VACUUM -> {
                areaRow(0, "range");
                xpRow(1);
                filterRow(2);
                redstoneRow(3);
            }
            case BREAKER -> {
                label(0, "front");
                label(1, "drops");
                label(2, "facing");
            }
            case PLACER -> {
                label(0, "next");
                label(1, "source");
                label(2, "facing");
            }
            case SPRINKLER -> {
                areaRow(0, "area");
                redstoneRow(1);
            }
            case TIMER -> {
                timerRows();
                redstoneRow(2);
                label(3, "next_pulse");
            }
            case TRANSMITTER, RECEIVER -> channelRows();
            case DETECTOR -> {
                targetRow(0);
                areaRow(1, "range");
                outputModeRow(2);
            }
        }
        if (kind.hasInventory) {
            addRenderableWidget(new WfWidgets.Choice(leftPos + BUF_X + 54 - 12, topPos + ROW_Y0 - 1, 12, 12,
                    Component.translatable(K + "take_all"), Component.translatable(K + "take_all.tip"), () -> false,
                    () -> WayfarersNet.toServer(new ContainerActionMsg(ContainerActions.Action.TAKE_ALL)))
                    .toggles().iconOnly(WfGui.id("glyph/take")).icon(WfGui.id("glyph/take"), 10));
        }
        containerTick();
    }

    private void send(int action, int value) {
        if (minecraft.gameMode != null) {
            minecraft.gameMode.handleInventoryButtonClick(menu.containerId, MachineMenu.button(action, value));
        }
    }

    private void label(int row, String key) {
        labels[row] = Component.translatable(K + "label." + key);
        labelTips[row] = Component.translatable(K + "label." + key + ".tip");
    }

    private int rowTop(int row) {
        return topPos + rowY(row);
    }

    private WfWidgets.Choice choice(int x, int y, int w, Component label, Component tip, java.util.function.BooleanSupplier on,
                                    Runnable action) {
        return addRenderableWidget(new WfWidgets.Choice(x, y, w, 18, label, tip, on, action));
    }

    private static Component square(int radius) {
        int size = radius * 2 + 1;
        return Component.literal(size + "x" + size);
    }

    private void areaRow(int row, String key) {
        label(row, key);
        int[] radii = MachineBlockEntity.radii(kind);
        boolean square = kind == MachineBlock.Kind.HARVESTER || kind == MachineBlock.Kind.SPRINKLER;
        int x = leftPos + CX;
        for (int i = 0; i < radii.length; i++) {
            int r = radii[i];
            int idx = i;
            Component text = square ? square(r) : Component.literal(String.valueOf(r));
            Component tip = square ? Component.translatable(K + "area.tip", r * 2 + 1, r * 2 + 1)
                    : Component.translatable(K + "range.tip", r);
            int w = Math.max(18, font.width(text) + 10);
            choice(x, rowTop(row), w, text, tip, () -> menu.get(D_RADIUS) == idx, () -> send(A_RADIUS, idx));
            x += w + 2;
        }
        addRenderableWidget(new WfWidgets.Choice(x + 4, rowTop(row), 18, 18, Component.translatable(K + "show_area"),
                Component.translatable(K + "show_area.tip"), () -> MachineAreaPreview.isShown(menu.pos),
                () -> MachineAreaPreview.toggle(menu.pos, kind, area())).toggles().iconOnly(WfGui.id("machine/show_area")));
    }

    private AABB area() {
        int[] radii = MachineBlockEntity.radii(kind);
        int r = radii.length == 0 ? 0 : radii[Math.floorMod(menu.get(D_RADIUS), radii.length)];
        return MachineBlockEntity.workArea(kind, menu.pos, r);
    }

    private void redstoneRow(int row) {
        label(row, "redstone");
        String[] modes = {"always", "high", "low"};
        for (int i = 0; i < 3; i++) {
            int mode = i;
            choice(leftPos + CX + i * 20, rowTop(row), 18, Component.translatable(K + "redstone." + modes[i]),
                    Component.translatable(K + "redstone." + modes[i] + ".tip"), () -> menu.get(D_REDSTONE) == mode,
                    () -> send(A_REDSTONE, mode)).iconOnly(WfGui.id("machine/rs_" + modes[i]));
        }
    }

    private void toggleRow(int row, String key, int toggle, int bit) {
        label(row, key);
        addRenderableWidget(new WfWidgets.Toggle(leftPos + CX, rowTop(row) + 2, labels[row], labelTips[row],
                () -> menu.flag(bit), () -> send(A_TOGGLE, toggle)));
    }

    private void outputRow(int row) {
        label(row, "output");
        int x = leftPos + CX;
        for (int i : OUTPUT_ORDER) {
            int value = i;
            String name = OUTPUT_NAMES[i];
            boolean letter = i >= 3 && i <= 6;
            WfWidgets.Choice c = choice(x, rowTop(row), 14, Component.translatable(K + "output." + name + (letter ? ".letter" : "")),
                    Component.empty(), () -> menu.get(D_OUTPUT) == value, () -> send(A_OUTPUT, value));
            if (!letter) {
                c.iconOnly(WfGui.id("machine/dir_" + (i == 0 ? "auto" : i == 7 ? "keep" : name)));
            }
            if (i >= 1 && i <= 6) {
                c.marker(() -> hasContainer(Direction.from3DDataValue(value - 1)));
            }
            outputs.add(c);
            x += 14;
        }
    }

    private boolean hasContainer(Direction d) {
        return (menu.get(D_SIDES) & (1 << d.get3DDataValue())) != 0;
    }

    private void xpRow(int row) {
        label(row, "xp");
        addRenderableWidget(new WfWidgets.Toggle(leftPos + CX, rowTop(row) + 2, labels[row],
                Component.translatable(K + "collect_xp.tip"), () -> menu.flag(2), () -> send(A_TOGGLE, T_COLLECT_XP)));
        int x = leftPos + CX + 30;
        takeXp = choice(x, rowTop(row), leftPos + BUF_X - 8 - x, Component.literal("0"), Component.translatable(K + "take_xp.tip"),
                () -> false, () -> send(A_TAKE_XP, 0)).toggles().icon(WfGui.icon("xp"), 16);
    }

    private void filterRow(int row) {
        label(row, "filter");
        filterMode = choice(leftPos + CX, rowTop(row), 18, Component.translatable(K + "filter.allow"), Component.empty(),
                () -> false, () -> send(A_TOGGLE, T_WHITELIST)).toggles().iconOnly(WfGui.id("machine/filter_allow"));
    }

    private void timerRows() {
        label(0, "interval");
        int steps = MachineBlockEntity.TIMER_INTERVALS.length;
        interval = addRenderableWidget(new WfWidgets.Stepper(leftPos + CX, rowTop(0), 120, steps, menu.get(D_INTERVAL),
                i -> seconds(MachineBlockEntity.intervalTicks(i)), labelTipsOf(0), i -> send(A_INTERVAL, i)));
        label(1, "pulse");
        int x = leftPos + CX;
        for (int i = 0; i < MachineBlockEntity.PULSE_LENGTHS.length; i++) {
            int idx = i;
            Component text = seconds(MachineBlockEntity.PULSE_LENGTHS[i]);
            int w = Math.max(18, font.width(text) + 10);
            pulses.add(choice(x, rowTop(1), w, text, Component.translatable(K + "pulse.tip", text), () -> menu.get(D_PULSE) == idx,
                    () -> send(A_PULSE, idx)));
            x += w + 2;
        }
    }

    private Component labelTipsOf(int row) {
        return labelTips[row] == null ? Component.empty() : labelTips[row];
    }

    private void channelRows() {
        label(0, "channel");
        for (int i = 0; i < 16; i++) {
            int ch = i;
            DyeColor dye = DyeColor.byId(i);
            Component name = Component.translatable("color.minecraft." + dye.getName());
            addRenderableWidget(new WfWidgets.Choice(leftPos + CX + (i % 8) * 18, rowTop(i / 8) + 1, 16, 16, name,
                    Component.translatable(K + "channel.tip", name), () -> menu.get(D_CHANNEL) == ch, () -> send(A_CHANNEL, ch))
                    .swatch(dye.getTextureDiffuseColor()));
        }
    }

    private void targetRow(int row) {
        label(row, "target");
        for (int i = 0; i < MachineBlockEntity.DETECTOR_MODES.length; i++) {
            int mode = i;
            String name = MachineBlockEntity.DETECTOR_MODES[i];
            choice(leftPos + CX + i * 20, rowTop(row), 18, Component.translatable("message.wayfarers.machine.detector." + name),
                    Component.translatable(K + "target." + name + ".tip"), () -> menu.get(D_TARGET) == mode,
                    () -> send(A_TARGET, mode)).iconOnly(WfGui.id("machine/target_" + name));
        }
    }

    private void outputModeRow(int row) {
        label(row, "signal");
        int x = leftPos + CX;
        for (int i = 0; i < 2; i++) {
            boolean inv = i == 1;
            Component text = Component.translatable(K + (inv ? "inverted" : "normal"));
            int w = Math.max(18, font.width(text) + 10);
            choice(x, rowTop(row), w, text, Component.translatable(K + (inv ? "inverted" : "normal") + ".tip"),
                    () -> menu.flag(8) == inv, () -> send(A_TOGGLE, T_INVERTED));
            x += w + 2;
        }
        signalLampX = x + 2 - leftPos;
    }

    // ------------------------------------------------------------------ live updates
    @Override
    protected void containerTick() {
        for (int k = 0; k < outputs.size(); k++) {
            int i = OUTPUT_ORDER[k];
            MutableComponent tip = Component.translatable(K + "output." + OUTPUT_NAMES[i] + ".tip");
            if (i >= 1 && i <= 6) {
                tip.append("\n").append(Component.translatable(K + (hasContainer(Direction.from3DDataValue(i - 1))
                        ? "output.container" : "output.nothing")).withStyle(ChatFormatting.GRAY));
            }
            outputs.get(k).tip(tip);
        }
        if (filterMode != null) {
            boolean allow = menu.flag(4);
            filterMode.iconOnly(WfGui.id(allow ? "machine/filter_allow" : "machine/filter_deny"));
            filterMode.setMessage(Component.translatable(K + (allow ? "filter.allow" : "filter.deny")));
            filterMode.tip(Component.translatable(K + (allow ? "filter.allow" : "filter.deny") + ".tip"));
        }
        if (takeXp != null) {
            int xp = menu.get(D_XP);
            takeXp.setMessage(Component.literal(xp >= Short.MAX_VALUE ? xp + "+" : String.valueOf(xp)));
            takeXp.active = xp > 0;
        }
        if (interval != null) {
            interval.sync(menu.get(D_INTERVAL));
            int ticks = MachineBlockEntity.intervalTicks(interval.step());
            for (int i = 0; i < pulses.size(); i++) {
                pulses.get(i).active = MachineBlockEntity.PULSE_LENGTHS[i] <= ticks - 2;
            }
        }
        if (kind.hasArea()) {
            MachineAreaPreview.update(menu.pos, area());
        }
    }

    // ------------------------------------------------------------------ text helpers
    private Component seconds(int ticks) {
        String n = ticks % 20 == 0 ? String.valueOf(ticks / 20)
                : String.format(Locale.ROOT, "%.1f", ticks / 20.0).replace(".", Component.translatable(K + "decimal").getString());
        return Component.translatable(K + "seconds", n);
    }

    private FormattedCharSequence clip(FormattedCharSequence line, int width) {
        StringBuilder sb = new StringBuilder();
        line.accept((i, style, cp) -> {
            sb.appendCodePoint(cp);
            return true;
        });
        return Component.literal(clipString(sb.toString(), width)).getVisualOrderText();
    }

    private String clipString(String s, int width) {
        if (font.width(s) <= width) {
            return s;
        }
        return font.plainSubstrByWidth(s, width - font.width("...")) + "...";
    }

    private ItemStack previewOrEmpty() {
        return menu.preview();
    }

    private Component previewName() {
        ItemStack p = previewOrEmpty();
        return p.isEmpty() ? Component.translatable(K + "the_block") : p.getHoverName();
    }

    private int detectorSignal() {
        int count = menu.get(D_COUNT_A);
        return menu.flag(8) ? (count == 0 ? 15 : 0) : Math.min(15, count);
    }

    private Component statusText() {
        MachineBlockEntity.Status s = menu.status();
        String key = K + "status." + s.name().toLowerCase(Locale.ROOT);
        int arg = menu.get(D_STATUS_ARG);
        return switch (s) {
            case HARVESTING, WATERING, DETECTED -> Component.translatable(key, arg);
            case READY_BREAK, CANT_BREAK, READY_PLACE -> Component.translatable(key, previewName());
            case COUNTDOWN -> Component.translatable(key, seconds(Math.max(1, menu.get(D_COUNTDOWN))));
            default -> Component.translatable(key);
        };
    }

    private Direction facing() {
        BlockState state = minecraft.level == null ? null : minecraft.level.getBlockState(menu.pos);
        return state != null && state.hasProperty(MachineBlock.FACING) ? state.getValue(MachineBlock.FACING) : Direction.NORTH;
    }

    // ------------------------------------------------------------------ rendering
    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        int x = leftPos;
        int y = topPos;
        WfGui.window(g, font, title, x, y, imageWidth, imageHeight);
        WfGui.sprite(g, WfGui.INSET, x + 10, y + 14, 20, 20);
        WfGui.sprite(g, WfGui.INSET, x + 10, y + STATUS_Y, W - 20, 14);
        for (Slot slot : menu.slots) {
            WfGui.sprite(g, WfGui.INSET, x + slot.x - 1, y + slot.y - 1, 18, 18);
        }
        if (kind.hasInventory) {
            int dy = y + MachineMenu.invY(kind) - 5;
            g.fill(x + 10, dy, x + W - 10, dy + 1, 0xFFB79C6C);
            g.fill(x + 10, dy + 1, x + W - 10, dy + 2, 0xFFF0E2C0);
        }
        if (kind == MachineBlock.Kind.TIMER) {
            int bw = W - 10 - CX - 40;
            int by = y + rowY(3) + 6;
            WfGui.sprite(g, WfGui.id("bar_back"), x + CX, by, bw, 6);
            int total = MachineBlockEntity.intervalTicks(menu.get(D_INTERVAL));
            int left = Math.min(total, Math.max(0, menu.get(D_COUNTDOWN)));
            int fill = (bw - 2) * (total - left) / Math.max(1, total);
            if (menu.flag(32)) {
                fill = bw - 2;
            }
            if (fill > 0) {
                WfGui.sprite(g, WfGui.id(menu.flag(32) ? "bar_done" : "bar_fill"), x + CX + 1, by + 1, fill, 4);
            }
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        // header: the machine, what it does, then the status lamp and line
        if (!icon.isEmpty()) {
            g.item(icon, 12, 16);
        }
        int dy = descLines.size() > 1 ? 16 : 20;
        for (FormattedCharSequence line : descLines) {
            g.text(font, line, 36, dy, WfGui.INK_SOFT, false);
            dy += 9;
        }
        MachineBlockEntity.Status status = menu.status();
        String lamp = switch (status.lamp) {
            case 0 -> "lamp_green";
            case 1 -> "lamp_amber";
            default -> "lamp_red";
        };
        WfGui.sprite(g, WfGui.id(lamp), 15, STATUS_Y + 4, 7, 7);
        g.text(font, clipString(statusText().getString(), W - 20 - 22), 25, STATUS_Y + 3, WfGui.CREAM, true);
        // row labels
        for (int i = 0; i < labels.length; i++) {
            if (labels[i] != null) {
                g.text(font, clipString(labels[i].getString(), LABEL_W), LABEL_X, rowY(i) + 5, WfGui.INK, false);
            }
        }
        switch (kind) {
            case HARVESTER -> onOff(g, 1, 1);
            case BREAKER, PLACER -> frontRows(g);
            case TIMER -> {
                g.text(font, seconds(MachineBlockEntity.intervalTicks(interval.step())), CX + 126, rowY(0) + 5, WfGui.INK, false);
                Component next = menu.flag(32) ? Component.translatable(K + "pulse_now")
                        : seconds(Math.max(1, menu.get(D_COUNTDOWN)));
                g.text(font, next, W - 10 - 34, rowY(3) + 5, WfGui.INK, false);
            }
            case TRANSMITTER, RECEIVER -> {
                DyeColor dye = DyeColor.byId(menu.get(D_CHANNEL));
                g.text(font, clipString(Component.translatable("color.minecraft." + dye.getName()).getString(), LABEL_W),
                        LABEL_X, rowY(1) + 5, WfGui.INK, false);
                Component info = Component.translatable(K + "channel.shared", menu.get(D_COUNT_A), menu.get(D_COUNT_B));
                g.text(font, clipString(info.getString(), W - 20), LABEL_X, rowY(2) + 5, WfGui.INK_SOFT, false);
            }
            case DETECTOR -> {
                int sig = detectorSignal();
                int x = signalLampX;
                WfGui.sprite(g, WfGui.id(sig > 0 ? "lamp_red" : "lamp_off"), x, rowY(2) + 6, 7, 7);
                g.text(font, Component.translatable(K + "signal_strength", sig), x + 10, rowY(2) + 5, WfGui.INK_SOFT, false);
            }
            default -> {
            }
        }
        if (kind.hasRedstoneMode()) {
            // the redstone input, live: a lamp in a little well (and a word when the window has room for it)
            int row = redstoneRowIndex();
            boolean input = menu.flag(16);
            int x = CX + 3 * 20 + 2;
            WfGui.sprite(g, WfGui.INSET, x, rowY(row), 18, 18);
            WfGui.sprite(g, WfGui.id(input ? "lamp_red" : "lamp_off"), x + 5, rowY(row) + 5, 7, 7);
            if (!kind.hasInventory) {
                g.text(font, Component.translatable(K + (input ? "input_on" : "input_off")), x + 22, rowY(row) + 5, WfGui.INK_SOFT, false);
            }
        }
        if (kind.hasInventory) {
            g.text(font, clipString(Component.translatable(K + "stored").getString(), 54 - 14), BUF_X, ROW_Y0 + 1, WfGui.INK_SOFT, false);
        }
    }

    /** "On" / "Off" next to a lever switch. */
    private int redstoneRowIndex() {
        return kind == MachineBlock.Kind.SPRINKLER ? 1 : kind == MachineBlock.Kind.TIMER ? 2 : 3;
    }

    private void onOff(GuiGraphicsExtractor g, int row, int bit) {
        g.text(font, Component.translatable(K + (menu.flag(bit) ? "on" : "off")), CX + 30, rowY(row) + 5, WfGui.INK, false);
    }

    private void frontRows(GuiGraphicsExtractor g) {
        boolean breaker = kind == MachineBlock.Kind.BREAKER;
        ItemStack preview = previewOrEmpty();
        int maxW = BUF_X - 8 - (CX + 22);
        Component name = !preview.isEmpty() ? preview.getHoverName()
                : Component.translatable(K + (breaker ? "front.empty" : "next.none"));
        g.text(font, clipString(name.getString(), maxW), CX + 22, rowY(0) + 5, preview.isEmpty() ? WfGui.INK_SOFT : WfGui.INK, false);
        Direction facing = facing();
        boolean chest = hasContainer(facing.getOpposite());
        Component where = Component.translatable(K + (breaker ? (chest ? "drops.chest" : "drops.self") : (chest ? "source.chest" : "source.self")));
        g.text(font, clipString(where.getString(), BUF_X - 8 - CX), CX, rowY(1) + 5, chest ? 0xFF2F6A22 : WfGui.INK_SOFT, false);
        Component dir = Component.translatable(K + "dir." + facing.getName());
        g.text(font, clipString(dir.getString(), BUF_X - 8 - CX), CX, rowY(2) + 5, WfGui.INK, false);
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractRenderState(g, mouseX, mouseY, a);
        int mx = mouseX - leftPos;
        int my = mouseY - topPos;
        if (menu.getCarried().isEmpty() && hoveredSlot == null) {
            List<Component> tip = hoverTip(mx, my);
            if (!tip.isEmpty()) {
                g.setComponentTooltipForNextFrame(font, tip, mouseX, mouseY);
            }
        }
        if (hoveredSlot != null && menu.getCarried().isEmpty() && !hoveredSlot.hasItem() && menu.isFilterSlot(hoveredSlot)) {
            g.setComponentTooltipForNextFrame(font, List.of(Component.translatable(K + "filter.slot.tip")), mouseX, mouseY);
        }
    }

    /** Tooltips of the non-widget parts: status line, description, row labels. */
    private List<Component> hoverTip(int mx, int my) {
        if (my >= STATUS_Y && my < STATUS_Y + 14 && mx >= 10 && mx < W - 10) {
            return List.of(statusText(), Component.translatable(K + "status.tip").withStyle(ChatFormatting.GRAY));
        }
        if (my >= 14 && my < 34 && mx >= 10 && mx < W - 10) {
            return List.of(title.copy().withStyle(ChatFormatting.GOLD), Component.translatable(K + "what." + kindKey),
                    Component.translatable(K + "howto." + kindKey).withStyle(ChatFormatting.GRAY));
        }
        if (kind.hasRedstoneMode()) {
            int x = CX + 3 * 20 + 2;
            int y = rowY(redstoneRowIndex());
            if (mx >= x && mx < x + 18 && my >= y && my < y + 18) {
                return List.of(Component.translatable(K + (menu.flag(16) ? "input_on" : "input_off")),
                        Component.translatable(K + "input.tip").withStyle(ChatFormatting.GRAY));
            }
        }
        if (mx >= LABEL_X && mx < CX - 2) {
            for (int i = 0; i < labels.length; i++) {
                if (labels[i] != null && my >= rowY(i) && my < rowY(i) + 18) {
                    return List.of(labels[i].copy().withStyle(ChatFormatting.GOLD), labelTips[i]);
                }
            }
        }
        return List.of();
    }
}
