package com.brasshaven.client.recipes;

import com.brasshaven.client.gui.WfGui;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/**
 * The recipe viewer's item list, full screen: for windows that leave no room beside them for the list (the button in
 * the corner opens it). Closing it goes back to that window.
 */
public class ItemListScreen extends Screen {
    final @Nullable Screen parent;
    private final ItemGrid grid = new ItemGrid();
    private int top;

    public ItemListScreen(@Nullable Screen parent) {
        super(Component.translatable("gui.brasshaven.recipes.list"));
        this.parent = parent;
    }

    @Override
    protected void init() {
        int cols = Math.max(3, Math.min(14, ItemGrid.colsFor(width - 24)));
        int rows = Math.max(3, Math.min(12, ItemGrid.rowsFor(height - 43)));
        int w = ItemGrid.boxW(cols);
        int h = ItemGrid.boxH(rows);
        // the title plate sits on the top rim, above the page arrows: 9 px more above the box than a window's
        top = WfGui.windowTop(height, h + 9, 13) + 9;
        grid.layout((width - w) / 2, top, cols, rows);
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractRenderState(g, mouseX, mouseY, a);
        grid.render(g, mouseX, mouseY, a);
        int cx = width / 2;
        Component t = WfGui.bold(title);
        int tw = Math.max(90, font.width(t) + 24);
        WfGui.sprite(g, WfGui.TITLE_PLATE, cx - tw / 2, top - 14, tw, 18);
        WfGui.centered(g, font, t, cx, top - 9, WfGui.PLATE_INK);
        g.centeredText(font, RecipeViewer.hint(), cx, top + grid.h() + 4, WfGui.CREAM);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (grid.contains(event.x(), event.y())) {
            return grid.mouseClicked(event.x(), event.y(), event.button(), (stack, uses) -> RecipeViewer.open(stack, uses, this));
        }
        grid.unfocus();
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        return grid.mouseScrolled(scrollY);
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (grid.keyPressed(event)) {
            return true;
        }
        ItemStack hovered = grid.hovered();
        if (!hovered.isEmpty() && RecipeViewer.lookup(event, hovered, this)) {
            return true;
        }
        if (minecraft.options.keyInventory.matches(event)) {
            onClose();
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean charTyped(CharacterEvent event) {
        return grid.charTyped(event) || super.charTyped(event);
    }

    @Override
    public void onClose() {
        minecraft.gui.setScreen(parent);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
