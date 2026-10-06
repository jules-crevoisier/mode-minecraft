package com.brasshaven.client.recipes;

import com.brasshaven.client.gui.WfGui;
import com.brasshaven.config.BrasshavenClientConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * The recipe viewer's item list in a brass-rimmed iron plate: page arrows and the page number on top, a grid of items,
 * a search box and the Brasshaven / everything filter at the bottom. Used beside container screens (RecipePanel) and
 * in the full-screen list (ItemListScreen). Left click on an item: its recipes; right click: its uses.
 *
 * <p>The filtering runs only when the search, the filter or the item list changes (the result indices go in an int
 * array reused between searches); a frame draws the visible slots and nothing else, without allocating.
 */
public final class ItemGrid {
    public static final int SLOT = 18;
    /** Frame thickness around the grid, and the header / search rows. */
    public static final int PAD = 6;
    public static final int HEADER = 14;
    public static final int SEARCH = 14;

    /** Box size for a grid of {@code cols} x {@code rows}. */
    public static int boxW(int cols) {
        return cols * SLOT + 2 * PAD;
    }

    public static int boxH(int rows) {
        return rows * SLOT + PAD + HEADER + 3 + SEARCH + PAD - 1;
    }

    /** Columns / rows that fit a box of this size. */
    public static int colsFor(int w) {
        return (w - 2 * PAD) / SLOT;
    }

    public static int rowsFor(int h) {
        return (h - (PAD + HEADER + 3 + SEARCH + PAD - 1)) / SLOT;
    }

    static final net.minecraft.resources.Identifier PANEL = WfGui.id("item_panel");
    static final net.minecraft.resources.Identifier SLOT_SPRITE = WfGui.id("recipe/slot");
    static final net.minecraft.resources.Identifier SMALL = WfGui.id("button_small");
    static final net.minecraft.resources.Identifier SMALL_HOVER = WfGui.id("button_small_hover");
    static final net.minecraft.resources.Identifier SMALL_OFF = WfGui.id("button_small_disabled");
    static final net.minecraft.resources.Identifier G_LEFT = WfGui.id("glyph/left");
    static final net.minecraft.resources.Identifier G_RIGHT = WfGui.id("glyph/right");
    static final net.minecraft.resources.Identifier G_MOD = WfGui.id("glyph/filter_mod");
    static final net.minecraft.resources.Identifier G_ALL = WfGui.id("glyph/filter_all");
    private static final Component NOTHING = Component.translatable("gui.brasshaven.recipes.nothing");

    // remembered while the game runs: the same search and page in every screen
    private static String query = "";
    private static int page;

    private int x;
    private int y;
    private int cols;
    private int rows;
    private final EditBox search;
    private int[] results = new int[0];
    private int count;
    private String shownQuery;
    private boolean shownModOnly;
    private int shownVersion = -1;
    private int shownPage = -1;
    private int shownPages = -1;
    private Component pageText = Component.empty();
    private ItemStack hovered = ItemStack.EMPTY;

    public ItemGrid() {
        Font font = Minecraft.getInstance().font;
        search = new EditBox(font, 0, 0, 40, 10, Component.translatable("gui.brasshaven.recipes.search"));
        search.setBordered(false);
        search.setTextColor(WfGui.CREAM);
        search.setHint(Component.translatable("gui.brasshaven.recipes.search").withColor(WfGui.MUTED));
        search.setMaxLength(40);
        search.setValue(query);
        search.setResponder(s -> query = s);
    }

    /** Places the box (outer size from {@link #boxW} / {@link #boxH}). */
    public void layout(int x, int y, int cols, int rows) {
        this.x = x;
        this.y = y;
        this.cols = cols;
        this.rows = rows;
        search.setX(x + PAD + 3);
        search.setY(y + h() - PAD - SEARCH + 4);
        search.setWidth(w() - 2 * PAD - 6 - 15);
        shownPage = -1;
    }

    public int w() {
        return boxW(cols);
    }

    public int h() {
        return boxH(rows);
    }

    public boolean contains(double mx, double my) {
        return mx >= x && mx < x + w() && my >= y && my < y + h();
    }

    public EditBox search() {
        return search;
    }

    public void setQuery(String q) {
        search.setValue(q);
        page = 0;
    }

    private int perPage() {
        return Math.max(1, cols * rows);
    }

    private int pages() {
        return Math.max(1, (count + perPage() - 1) / perPage());
    }

    private void refresh() {
        ItemIndex.ensure();
        boolean modOnly = BrasshavenClientConfig.RECIPE_MOD_ONLY.get();
        if (!search.getValue().equals(query)) {
            search.setValue(query); // typed in the other list (the full-screen one, or the panel)
        }
        String q = search.getValue();
        if (!q.equals(shownQuery) || modOnly != shownModOnly || ItemIndex.version() != shownVersion) {
            if (results.length < ItemIndex.size()) {
                results = new int[ItemIndex.size()];
            }
            if (shownQuery != null && !q.equals(shownQuery)) {
                page = 0;
            }
            count = ItemIndex.filter(q, modOnly, results);
            shownQuery = q;
            shownModOnly = modOnly;
            shownVersion = ItemIndex.version();
        }
        page = Math.max(0, Math.min(page, pages() - 1));
        if (page != shownPage || pages() != shownPages) {
            shownPage = page;
            shownPages = pages();
            pageText = Component.literal((page + 1) + " / " + pages());
        }
    }

    // ------------------------------------------------------------------ drawing

    private int gridX() {
        return x + PAD;
    }

    private int gridY() {
        return y + PAD + HEADER - 1;
    }

    private boolean over(int mx, int my, int bx, int by, int bw, int bh) {
        return mx >= bx && mx < bx + bw && my >= by && my < by + bh;
    }

    private int leftX() {
        return x + PAD;
    }

    private int rightX() {
        return x + w() - PAD - 12;
    }

    private int arrowsY() {
        return y + PAD - 1;
    }

    private int filterX() {
        return x + w() - PAD - 12;
    }

    private int filterY() {
        return y + h() - PAD - SEARCH + 1;
    }

    public void render(GuiGraphicsExtractor g, int mx, int my, float a) {
        refresh();
        Font font = Minecraft.getInstance().font;
        WfGui.sprite(g, PANEL, x, y, w(), h());
        // header: page arrows and the page number
        smallButton(g, leftX(), arrowsY(), G_LEFT, page > 0, mx, my);
        smallButton(g, rightX(), arrowsY(), G_RIGHT, page < pages() - 1, mx, my);
        g.centeredText(font, pageText, x + w() / 2, arrowsY() + 2, WfGui.CREAM_SOFT); // light text on iron: shadowed
        // the items of this page
        hovered = ItemStack.EMPTY;
        int gx = gridX();
        int gy = gridY();
        int start = page * perPage();
        for (int i = 0; i < perPage(); i++) {
            int sx = gx + (i % cols) * SLOT;
            int sy = gy + (i / cols) * SLOT;
            WfGui.sprite(g, SLOT_SPRITE, sx, sy, SLOT, SLOT);
            int k = start + i;
            if (k >= count) {
                continue;
            }
            ItemStack stack = ItemIndex.get(results[k]);
            g.item(stack, sx + 1, sy + 1);
            if (over(mx, my, sx, sy, SLOT, SLOT)) {
                g.fill(sx + 1, sy + 1, sx + 17, sy + 17, 0x60FFF5DC);
                hovered = stack;
            }
        }
        if (count == 0) {
            g.centeredText(font, NOTHING, x + w() / 2, gy + 6, WfGui.MUTED);
        }
        // search box and filter
        WfGui.sprite(g, WfGui.INSET, x + PAD, y + h() - PAD - SEARCH, w() - 2 * PAD - 14, SEARCH);
        search.extractRenderState(g, mx, my, a);
        boolean modOnly = BrasshavenClientConfig.RECIPE_MOD_ONLY.get();
        smallButton(g, filterX(), filterY(), modOnly ? G_MOD : G_ALL, true, mx, my);
        // tooltips
        if (!hovered.isEmpty()) {
            g.setTooltipForNextFrame(font, hovered, mx, my);
        } else if (over(mx, my, filterX(), filterY(), 12, 12)) {
            g.setComponentTooltipForNextFrame(font, List.of(
                    Component.translatable(modOnly ? "gui.brasshaven.recipes.filter.mod" : "gui.brasshaven.recipes.filter.all"),
                    Component.translatable("gui.brasshaven.recipes.filter.tip").withStyle(ChatFormatting.GRAY)), mx, my);
        } else if (over(mx, my, x + PAD, y + h() - PAD - SEARCH, w() - 2 * PAD - 14, SEARCH) && !search.isFocused()) {
            g.setComponentTooltipForNextFrame(font, searchTip(), mx, my);
        }
    }

    private static List<Component> searchTip() {
        List<Component> out = new ArrayList<>(3);
        out.add(Component.translatable("gui.brasshaven.recipes.search"));
        out.add(Component.translatable("gui.brasshaven.recipes.search.tip").withStyle(ChatFormatting.GRAY));
        return out;
    }

    static void smallButton(GuiGraphicsExtractor g, int bx, int by, net.minecraft.resources.Identifier glyph, boolean active, int mx, int my) {
        boolean hover = active && mx >= bx && mx < bx + 12 && my >= by && my < by + 12;
        WfGui.sprite(g, !active ? SMALL_OFF : hover ? SMALL_HOVER : SMALL, bx, by, 12, 12);
        WfGui.sprite(g, glyph, bx + 1, by + 1, 10, 10);
    }

    // ------------------------------------------------------------------ input

    /** The item under the mouse (drawn this frame), or empty. */
    public ItemStack hovered() {
        return hovered;
    }

    public ItemStack itemAt(double mx, double my) {
        refresh();
        int c = (int) Math.floor((mx - gridX()) / SLOT);
        int r = (int) Math.floor((my - gridY()) / SLOT);
        if (c < 0 || c >= cols || r < 0 || r >= rows) {
            return ItemStack.EMPTY;
        }
        int k = page * perPage() + r * cols + c;
        return k < count ? ItemIndex.get(results[k]) : ItemStack.EMPTY;
    }

    /** A click inside the box (always consumed). {@code open} gets the item and true for its uses. */
    public boolean mouseClicked(double mx, double my, int button, java.util.function.BiConsumer<ItemStack, Boolean> open) {
        int ix = (int) mx;
        int iy = (int) my;
        boolean inSearch = over(ix, iy, x + PAD, y + h() - PAD - SEARCH, w() - 2 * PAD - 14, SEARCH);
        if (inSearch && button == 1) {
            setQuery(""); // right click clears, like the creative search
        }
        search.setFocused(inSearch);
        if (inSearch) {
            return true;
        }
        if (over(ix, iy, leftX(), arrowsY(), 12, 12)) {
            turn(-1);
        } else if (over(ix, iy, rightX(), arrowsY(), 12, 12)) {
            turn(1);
        } else if (over(ix, iy, filterX(), filterY(), 12, 12)) {
            BrasshavenClientConfig.RECIPE_MOD_ONLY.set(!BrasshavenClientConfig.RECIPE_MOD_ONLY.get());
            BrasshavenClientConfig.RECIPE_MOD_ONLY.save();
            page = 0;
            click();
        } else {
            ItemStack stack = itemAt(mx, my);
            if (!stack.isEmpty() && (button == 0 || button == 1)) {
                open.accept(stack, button == 1);
            }
        }
        return true;
    }

    public void turn(int delta) {
        int before = page;
        page = Math.max(0, Math.min(pages() - 1, page + delta));
        if (page != before) {
            click();
        }
    }

    private static void click() {
        Minecraft.getInstance().getSoundManager().play(net.minecraft.client.resources.sounds.SimpleSoundInstance.forUI(
                net.minecraft.sounds.SoundEvents.UI_BUTTON_CLICK, 1.0F));
    }

    public boolean mouseScrolled(double scrollY) {
        if (scrollY != 0) {
            turn(scrollY > 0 ? -1 : 1);
        }
        return true;
    }

    public boolean searchFocused() {
        return search.isFocused();
    }

    public void unfocus() {
        search.setFocused(false);
    }

    /** Keys while the search box has the focus: all of them go to it (Escape / Enter leave it). */
    public boolean keyPressed(KeyEvent event) {
        if (!search.isFocused()) {
            return false;
        }
        if (event.isEscape() || event.key() == com.mojang.blaze3d.platform.InputConstants.KEY_RETURN) {
            search.setFocused(false);
            return true;
        }
        search.keyPressed(event);
        return true;
    }

    public boolean charTyped(CharacterEvent event) {
        return search.isFocused() && search.charTyped(event);
    }

    static boolean typing(Screen screen) {
        for (var child : screen.children()) {
            if (child instanceof EditBox box && box.isFocused() && box.isVisible()) {
                return true;
            }
        }
        return false;
    }
}
