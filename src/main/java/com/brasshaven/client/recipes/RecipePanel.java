package com.brasshaven.client.recipes;

import com.brasshaven.client.gui.WfGui;
import com.brasshaven.config.BrasshavenClientConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/**
 * The item list beside a container screen (inventory, crafting table, furnaces, chests, the mod's machines...), in the
 * free space right of the window: as many columns as fit (3 to 9), the screen's full height. It never covers the
 * window: when fewer than 3 columns fit (a wide window, a small screen, the recipe book open), only a small button
 * stays in the top-right corner and opens the list full screen (ItemListScreen). When the player has potion effects,
 * the inventory shows them in their compact form between the window and the list.
 *
 * <p>The layout is worked out again only when the window moves or the screen is resized (the recipe book opening
 * shifts the window); drawing reuses it.
 */
public final class RecipePanel {
    private static final Identifier TOGGLE_GLYPH = WfGui.id("glyph/recipes");
    /** Room kept for the compact potion effects (32 px icons) between the window and the list. */
    private static final int EFFECTS = 35;

    private static ItemGrid grid;
    private static AbstractContainerScreen<?> laidOutFor;
    private static long layoutKey = Long.MIN_VALUE;
    private static boolean fits;
    /** The small button shown instead of the list when it does not fit (x < 0: no room for it either). */
    private static int toggleX = -1;
    private static int toggleY;

    private RecipePanel() {}

    public static boolean shown() {
        return RecipeViewer.enabled() && BrasshavenClientConfig.RECIPE_PANEL.get();
    }

    static ItemGrid grid() {
        if (grid == null) {
            grid = new ItemGrid();
        }
        return grid;
    }

    private static boolean effectsShown(AbstractContainerScreen<?> s) {
        Minecraft mc = Minecraft.getInstance();
        return (s instanceof InventoryScreen || s instanceof CreativeModeInventoryScreen) && mc.player != null
                && !mc.player.getActiveEffects().isEmpty();
    }

    /** Lays the panel out for this screen if its window moved (or another screen is open). */
    static void layout(AbstractContainerScreen<?> s) {
        int right = s.getGuiLeft() + s.getXSize();
        boolean effects = effectsShown(s);
        long key = ((long) right << 40) ^ ((long) s.width << 24) ^ ((long) s.height << 8) ^ (effects ? 1 : 0);
        if (s == laidOutFor && key == layoutKey) {
            return;
        }
        laidOutFor = s;
        layoutKey = key;
        int x0 = right + 4 + (effects ? EFFECTS : 0);
        int x1 = s.width - 4;
        int cols = Math.min(9, ItemGrid.colsFor(x1 - x0));
        int rows = Math.min(16, ItemGrid.rowsFor(s.height - 8));
        fits = cols >= 3 && rows >= 3;
        if (fits) {
            grid().layout(x1 - ItemGrid.boxW(cols), (s.height - ItemGrid.boxH(rows)) / 2, cols, rows);
            toggleX = -1;
        } else {
            grid().unfocus();
            toggleX = s.width - 16 >= right + 2 ? s.width - 16 : -1;
            toggleY = 4;
        }
    }

    static void render(AbstractContainerScreen<?> s, GuiGraphicsExtractor g, int mx, int my, float a) {
        layout(s);
        if (fits) {
            grid().render(g, mx, my, a);
            if (!s.getMenu().getCarried().isEmpty() && grid().contains(mx, my)) {
                s.extractCarriedItem(g, mx, my); // the item on the cursor stays above the list
            }
        } else if (toggleX >= 0) {
            ItemGrid.smallButton(g, toggleX, toggleY, TOGGLE_GLYPH, true, mx, my);
            if (overToggle(mx, my)) {
                Minecraft mc = Minecraft.getInstance();
                g.setComponentTooltipForNextFrame(mc.font, List.of(Component.translatable("gui.brasshaven.recipes.list"),
                        Component.translatable("gui.brasshaven.recipes.list.tip").withStyle(ChatFormatting.GRAY)), mx, my);
            }
        }
    }

    private static boolean overToggle(double mx, double my) {
        return toggleX >= 0 && mx >= toggleX && mx < toggleX + 12 && my >= toggleY && my < toggleY + 12;
    }

    /** A click on the list or its button: handled and consumed (the window must not see it: it would drop the item). */
    static boolean mouseClicked(AbstractContainerScreen<?> s, double mx, double my, int button) {
        layout(s);
        if (fits && grid().contains(mx, my)) {
            grid().mouseClicked(mx, my, button, (stack, uses) -> RecipeViewer.open(stack, uses, s));
            if (grid().searchFocused()) {
                s.setFocused(null); // the window's own search box (chests) lets go of the keyboard
            }
            return true;
        }
        grid().unfocus();
        if (!fits && overToggle(mx, my)) {
            Minecraft.getInstance().gui.setScreen(new ItemListScreen(s));
            return true;
        }
        return false;
    }

    static boolean over(AbstractContainerScreen<?> s, double mx, double my) {
        layout(s);
        return fits ? grid().contains(mx, my) : overToggle(mx, my);
    }

    static boolean mouseScrolled(AbstractContainerScreen<?> s, double mx, double my, double scrollY) {
        layout(s);
        return fits && grid().contains(mx, my) && grid().mouseScrolled(scrollY);
    }

    /** The list's item under the mouse (drawn last frame), or empty. */
    static ItemStack hovered(AbstractContainerScreen<?> s) {
        return fits && s == laidOutFor ? grid().hovered() : ItemStack.EMPTY;
    }

    /** Potion effects of the inventory: compact while the list is beside it, so they fit the room kept for them. */
    static boolean compactEffects(AbstractContainerScreen<?> s) {
        layout(s);
        return fits;
    }

    /** CI and the tests: the list's search. */
    public static void setSearch(String query) {
        grid().setQuery(query);
    }
}
