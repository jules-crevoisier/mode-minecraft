package com.wayfarers.client;

import com.wayfarers.client.gui.WfGui;
import com.wayfarers.network.ContainerActionMsg;
import com.wayfarers.network.WayfarersNet;
import com.wayfarers.util.ContainerActions;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.narration.NarrationElementOutput;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.input.InputWithModifiers;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.ScreenEvent;

import java.util.Locale;
import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * Storage helpers on every container screen: Sort / Take all / Deposit matching / Quick-stack nearby
 * buttons, a search box that dims the slots that don't match, and middle-click to sort.
 */
public final class ContainerButtons {
    private static EditBox search;
    private static AbstractContainerScreen<?> searchScreen;

    private ContainerButtons() {}

    public static void register() {
        ScreenEvent.Init.Post.BUS.addListener(ContainerButtons::onInit);
        ScreenEvent.Render.Post.BUS.addListener(ContainerButtons::onRender);
        ScreenEvent.MouseButtonPressed.Pre.BUS.addListener((Predicate<ScreenEvent.MouseButtonPressed.Pre>) ContainerButtons::onClick);
    }

    /** A 12x12 brass button with a glyph. */
    private static final class IconButton extends AbstractButton {
        private final String glyph;
        private final Runnable action;

        IconButton(int x, int y, String glyph, Component tip, Runnable action) {
            super(x, y, 12, 12, tip);
            this.glyph = glyph;
            this.action = action;
            setTooltip(Tooltip.create(tip));
        }

        @Override
        public void onPress(InputWithModifiers input) {
            action.run();
        }

        @Override
        protected void extractContents(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
            WfGui.sprite(g, WfGui.id(isHoveredOrFocused() ? "button_small_hover" : "button_small"), getX(), getY(), 12, 12);
            WfGui.sprite(g, WfGui.id("glyph/" + glyph), getX() + 1, getY() + 1, 10, 10);
        }

        @Override
        protected void updateWidgetNarration(NarrationElementOutput output) {
            defaultButtonNarrationText(output);
        }
    }

    private static boolean supported(Object screen) {
        return screen instanceof AbstractContainerScreen<?> && !(screen instanceof CreativeModeInventoryScreen);
    }

    private static void send(ContainerActions.Action action) {
        WayfarersNet.toServer(new ContainerActionMsg(action));
    }

    private static void onInit(ScreenEvent.Init.Post event) {
        if (!supported(event.getScreen())) {
            return;
        }
        AbstractContainerScreen<?> screen = (AbstractContainerScreen<?>) event.getScreen();
        int left = screen.getGuiLeft();
        int top = screen.getGuiTop();
        int right = left + screen.getXSize();
        Consumer<IconButton> add = event::addListener;
        if (screen instanceof InventoryScreen) {
            add.accept(new IconButton(right - 14, top - 14, "sort", Component.translatable("gui.wayfarers.storage.sort_inventory"),
                    () -> send(ContainerActions.Action.SORT_PLAYER)));
            add.accept(new IconButton(right - 28, top - 14, "nearby", Component.translatable("gui.wayfarers.storage.nearby"),
                    () -> send(ContainerActions.Action.QUICK_STACK_NEARBY)));
            searchScreen = null;
            return;
        }
        int containerSlots = 0;
        for (Slot slot : screen.getMenu().slots) {
            if (!(slot.container instanceof Inventory)) {
                containerSlots++;
            }
        }
        if (containerSlots < 5) {
            return; // crafting tables, furnaces... keep them clean
        }
        String[][] buttons = {
                {"sort", "gui.wayfarers.storage.sort", "SORT_CONTAINER"},
                {"take", "gui.wayfarers.storage.take_all", "TAKE_ALL"},
                {"deposit", "gui.wayfarers.storage.deposit", "DEPOSIT_MATCHING"},
                {"nearby", "gui.wayfarers.storage.nearby", "QUICK_STACK_NEARBY"},
        };
        for (int i = 0; i < buttons.length; i++) {
            String[] b = buttons[i];
            ContainerActions.Action action = ContainerActions.Action.valueOf(b[2]);
            add.accept(new IconButton(right - 14 - i * 13, top - 14, b[0], Component.translatable(b[1]), () -> send(action)));
        }
        String previous = search != null && searchScreen != null && searchScreen.getClass() == screen.getClass() ? search.getValue() : "";
        search = new EditBox(Minecraft.getInstance().font, left + 2, top - 13, Math.max(40, screen.getXSize() - 4 * 13 - 8), 11,
                Component.translatable("gui.wayfarers.storage.search"));
        search.setHint(Component.translatable("gui.wayfarers.storage.search"));
        search.setMaxLength(24);
        search.setValue(previous);
        searchScreen = screen;
        event.addListener(search);
    }

    private static boolean matches(ItemStack stack, String q) {
        if (stack.isEmpty()) {
            return false;
        }
        if (stack.getHoverName().getString().toLowerCase(Locale.ROOT).contains(q)) {
            return true;
        }
        return BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath().replace('_', ' ').contains(q);
    }

    private static void onRender(ScreenEvent.Render.Post event) {
        if (search == null || event.getScreen() != searchScreen || search.getValue().isBlank()) {
            return;
        }
        String q = search.getValue().toLowerCase(Locale.ROOT).strip();
        AbstractContainerScreen<?> screen = searchScreen;
        GuiGraphicsExtractor g = event.getGuiGraphics();
        for (Slot slot : screen.getMenu().slots) {
            if (slot.container instanceof Inventory) {
                continue;
            }
            int x = screen.getGuiLeft() + slot.x;
            int y = screen.getGuiTop() + slot.y;
            if (matches(slot.getItem(), q)) {
                g.outline(x - 1, y - 1, 18, 18, 0xFFF6C343);
            } else {
                g.fill(x, y, x + 16, y + 16, 0xB0101010);
            }
        }
    }

    /** Middle-click a slot to sort the inventory it belongs to (not in creative, where it picks blocks). */
    private static boolean onClick(ScreenEvent.MouseButtonPressed.Pre event) {
        Minecraft mc = Minecraft.getInstance();
        if (event.getInfo().button() != 2 || !supported(event.getScreen()) || mc.player == null || mc.player.isCreative()) {
            return false;
        }
        Slot slot = ((AbstractContainerScreen<?>) event.getScreen()).getSlotUnderMouse();
        if (slot == null) {
            return false;
        }
        send(slot.container instanceof Inventory ? ContainerActions.Action.SORT_PLAYER : ContainerActions.Action.SORT_CONTAINER);
        return true;
    }
}
