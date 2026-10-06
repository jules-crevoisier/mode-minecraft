package com.brasshaven.client.recipes;

import com.brasshaven.client.gui.GuideScreen;
import com.brasshaven.client.gui.WfButton;
import com.brasshaven.client.gui.WfGui;
import com.brasshaven.client.gui.WfWidgets;
import com.brasshaven.network.BrasshavenNet;
import com.brasshaven.network.RecipeFillMsg;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Util;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.AbstractCraftingMenu;
import net.minecraft.world.inventory.AbstractFurnaceMenu;
import net.minecraft.world.inventory.RecipeBookMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * The recipe viewer's recipe screen: how to make an item ("Recipes") or what it is used in ("Uses"), one tab per kind
 * of recipe (crafting, the furnaces, campfire, stonecutter, smithing, the Chisel Table, others), as many recipes per
 * page as fit. Slots holding several possible items (tags) cycle through them every second (Shift holds them still).
 * Click an item: its recipes; right click: its uses; Backspace or the back button: the previous item.
 *
 * <p>Opened from a crafting table, the inventory's 2x2 grid or a furnace, each recipe that fits gets a "+" button: the
 * server moves the ingredients from the inventory into the grid (RecipeFillMsg, vanilla's recipe-book placement;
 * Shift: as many as possible). Missing ingredients are tinted red; with some missing the grid gets the recipe's
 * outline instead, like the recipe book. Closing this screen goes back to the window it was opened from.
 */
public class RecipeScreen extends Screen {
    private static final int W = 300;
    private static final int H = 214;
    /** The card holding the recipes, inside the window. */
    private static final int CARD_X = 10;
    private static final int CARD_Y = 62;
    private static final int CARD_W = 280;
    private static final int CARD_H = 124;
    private static final int TAB = 22;

    private static final Identifier SLOT = WfGui.id("recipe/slot");
    private static final Identifier SLOT_BIG = WfGui.id("recipe/slot_big");
    private static final Identifier ARROW = WfGui.id("recipe/arrow");
    private static final Identifier FLAME = WfGui.id("recipe/flame");
    private static final Identifier SHAPELESS = WfGui.id("recipe/shapeless");
    private static final Identifier PLUS = WfGui.id("glyph/plus");
    private static final Identifier PLUS_MISSING = WfGui.id("glyph/plus_missing");
    private static final int RED = 0x80E0483B;

    private record State(ItemStack stack, boolean uses, RecipeCategory tab, int page) {}

    final @Nullable Screen parent;
    private final Deque<State> history = new ArrayDeque<>();
    private ItemStack focus;
    private boolean uses;
    private Map<RecipeCategory, List<ViewRecipe>> recipes = Map.of();
    private Map<RecipeCategory, List<ViewRecipe>> usesOf = Map.of();
    private final List<RecipeCategory> tabs = new ArrayList<>();
    private int tab;
    private int page;
    private int left;
    private int top;
    private Component hint = Component.empty();
    private Component pageText = Component.empty();
    private String tabText = "";
    private String focusName = "";
    private String focusMod = "";
    private Component windowTitle = Component.empty();
    private WfWidgets.Choice modeButton;
    private WfWidgets.Choice manualButton;
    private WfWidgets.Choice backButton;
    private WfButton prev;
    private WfButton next;
    /** Per visible recipe: which input slots the inventory cannot fill (null: no "+" for it). */
    private final Map<ViewRecipe, boolean[]> missing = new IdentityHashMap<>();
    private int missingAge;
    /** init() has run (the screen is shown): widgets can be rebuilt. */
    private boolean laidOut;

    public RecipeScreen(ItemStack stack, boolean uses, @Nullable Screen parent) {
        super(Component.translatable(uses ? "gui.brasshaven.recipes.uses" : "gui.brasshaven.recipes.recipes"));
        this.parent = parent;
        show(stack, uses, false);
    }

    /** Shows another item (pushing the current one on the back history when {@code push}). */
    public void show(ItemStack stack, boolean uses, boolean push) {
        if (push && focus != null) {
            history.push(new State(focus, this.uses, currentTab(), page));
            if (history.size() > 64) {
                history.removeLast();
            }
        }
        this.focus = stack.copyWithCount(1);
        this.recipes = ClientRecipes.recipes(focus);
        this.usesOf = ClientRecipes.uses(focus);
        setMode(uses, null, 0);
    }

    private void setMode(boolean uses, @Nullable RecipeCategory wantTab, int wantPage) {
        this.uses = uses;
        windowTitle = Component.translatable(uses ? "gui.brasshaven.recipes.uses" : "gui.brasshaven.recipes.recipes");
        tabs.clear();
        tabs.addAll(current().keySet());
        tab = Math.max(0, wantTab == null ? 0 : tabs.indexOf(wantTab));
        page = wantPage;
        focusName = focus.getHoverName().getString();
        Identifier key = BuiltInRegistries.ITEM.getKey(focus.getItem());
        focusMod = net.minecraftforge.fml.ModList.getModContainerById(key.getNamespace())
                .map(c -> c.getModInfo().getDisplayName()).orElse(key.getNamespace());
        // only once the screen has been laid out: the constructor comes here too (show), and in 26.2 `minecraft` is
        // already set there, so a rebuild then ran init() on a 0 x 0 screen and its widgets stayed (Screen.init(w, h)
        // calls init() without clearing them the first time): a second ">" button over the first recipe
        if (laidOut) {
            rebuildWidgets();
        }
    }

    private Map<RecipeCategory, List<ViewRecipe>> current() {
        return uses ? usesOf : recipes;
    }

    private @Nullable RecipeCategory currentTab() {
        return tabs.isEmpty() ? null : tabs.get(tab);
    }

    private List<ViewRecipe> list() {
        RecipeCategory c = currentTab();
        return c == null ? List.of() : current().getOrDefault(c, List.of());
    }

    private static int count(Map<RecipeCategory, List<ViewRecipe>> map) {
        int n = 0;
        for (List<ViewRecipe> l : map.values()) {
            n += l.size();
        }
        return n;
    }

    // ------------------------------------------------------------------ layout

    private int cols() {
        RecipeCategory c = currentTab();
        return c == null ? 1 : Math.max(1, CARD_W / c.cellW);
    }

    private int rows() {
        RecipeCategory c = currentTab();
        return c == null ? 1 : Math.max(1, CARD_H / c.cellH);
    }

    private int perPage() {
        return cols() * rows();
    }

    private int pages() {
        return Math.max(1, (list().size() + perPage() - 1) / perPage());
    }

    /** Top-left of the {@code i}-th recipe of the page (the cells are centred in the card). */
    private int cellX(int i) {
        RecipeCategory c = currentTab();
        int used = cols() * c.cellW;
        return left + CARD_X + (CARD_W - used) / 2 + (i % cols()) * c.cellW;
    }

    private int cellY(int i) {
        RecipeCategory c = currentTab();
        int used = rows() * c.cellH;
        return top + CARD_Y + (CARD_H - used) / 2 + (i / cols()) * c.cellH;
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = WfGui.windowTop(height, H, 13);
        page = Math.max(0, Math.min(page, pages() - 1));
        hint = RecipeViewer.hint();
        // the other list (recipes <-> uses) and its size; the manual page; back to the previous item
        boolean otherUses = !uses;
        int otherCount = count(otherUses ? usesOf : recipes);
        Component other = Component.translatable(otherUses ? "gui.brasshaven.recipes.to_uses" : "gui.brasshaven.recipes.to_recipes", otherCount);
        int bw = Math.max(60, font.width(other) + 12);
        int bx = left + W - 10 - 18 - 2 - 18 - 4 - bw;
        modeButton = addRenderableWidget(new WfWidgets.Choice(bx, top + 15, bw, 18, other,
                Component.translatable(otherUses ? "gui.brasshaven.recipes.to_uses.tip" : "gui.brasshaven.recipes.to_recipes.tip"),
                () -> false, () -> switchMode()).toggles());
        modeButton.active = otherCount > 0;
        String manualPage = GuideScreen.pageFor(focus);
        manualButton = addRenderableWidget(new WfWidgets.Choice(left + W - 10 - 18 - 2 - 18, top + 15, 18, 18,
                Component.translatable("gui.brasshaven.recipes.manual"),
                Component.translatable(manualPage != null ? "gui.brasshaven.recipes.manual.tip" : "gui.brasshaven.recipes.manual.none"),
                () -> false, this::openManual).toggles().iconOnly(WfGui.id("glyph/book")).icon(WfGui.id("glyph/book"), 10));
        manualButton.active = manualPage != null;
        backButton = addRenderableWidget(new WfWidgets.Choice(left + W - 10 - 18, top + 15, 18, 18,
                Component.translatable("gui.brasshaven.recipes.back"), Component.translatable("gui.brasshaven.recipes.back.tip"),
                () -> false, this::back).toggles().iconOnly(WfGui.id("glyph/back")).icon(WfGui.id("glyph/back"), 10));
        backButton.active = !history.isEmpty();
        prev = addRenderableWidget(new WfButton(left + 10, top + H - 24, 40, 16, Component.literal("<"), b -> turn(-1)));
        next = addRenderableWidget(new WfButton(left + W - 50, top + H - 24, 40, 16, Component.literal(">"), b -> turn(1)));
        pageChanged();
        laidOut = true;
    }

    private void pageChanged() {
        page = Math.max(0, Math.min(page, pages() - 1));
        prev.active = page > 0;
        next.active = page < pages() - 1;
        pageText = Component.translatable("gui.brasshaven.recipes.page", page + 1, pages());
        RecipeCategory c = currentTab();
        tabText = c == null ? "" : Component.translatable("gui.brasshaven.recipes.tab", c.title(), list().size()).getString();
        missingAge = 0;
        updateMissing();
    }

    private void turn(int delta) {
        int before = page;
        page = Math.max(0, Math.min(pages() - 1, page + delta));
        if (page != before) {
            pageChanged();
        }
    }

    private void selectTab(int i) {
        if (i >= 0 && i < tabs.size() && i != tab) {
            tab = i;
            page = 0;
            pageChanged();
        }
    }

    private void switchMode() {
        history.push(new State(focus, uses, currentTab(), page));
        setMode(!uses, null, 0);
    }

    private void back() {
        State s = history.poll();
        if (s != null) {
            focus = s.stack();
            recipes = ClientRecipes.recipes(focus);
            usesOf = ClientRecipes.uses(focus);
            setMode(s.uses(), s.tab(), s.page());
        }
    }

    private void openManual() {
        String page = GuideScreen.pageFor(focus);
        if (page != null) {
            minecraft.gui.setScreen(new GuideScreen(page).returningTo(this));
        }
    }

    @Override
    public Component getTitle() {
        return windowTitle;
    }

    // ------------------------------------------------------------------ the "+" button

    /** The open crafting grid or furnace the "+" button fills, or null. */
    private @Nullable AbstractContainerMenu fillTarget() {
        AbstractContainerScreen<?> screen = RecipeViewer.containerOf(parent);
        if (screen == null || screen instanceof CreativeModeInventoryScreen || minecraft.player == null) {
            return null;
        }
        AbstractContainerMenu menu = screen.getMenu();
        return menu instanceof RecipeBookMenu && menu == minecraft.player.containerMenu ? menu : null;
    }

    /** The recipe fits the open grid (the same checks as the server's RecipeFill). */
    private static boolean canFill(AbstractContainerMenu menu, ViewRecipe r) {
        if (r.id() == null || !r.vanillaType()) {
            return false;
        }
        if (menu instanceof AbstractCraftingMenu crafting) {
            return r.category() == RecipeCategory.CRAFTING && (crafting.getInputGridSlots().size() >= 9 || r.fitsInventoryGrid());
        }
        if (menu instanceof AbstractFurnaceMenu furnace) {
            return switch (furnace.getRecipeBookType()) {
                case FURNACE -> r.category() == RecipeCategory.SMELTING;
                case BLAST_FURNACE -> r.category() == RecipeCategory.BLASTING;
                case SMOKER -> r.category() == RecipeCategory.SMOKING;
                default -> false;
            };
        }
        return false;
    }

    private static List<Slot> gridSlots(AbstractContainerMenu menu) {
        if (menu instanceof AbstractCraftingMenu crafting) {
            return crafting.getInputGridSlots();
        }
        return List.of(menu.getSlot(0));
    }

    /**
     * Which input slots the player's items cannot fill, for the recipes of this page: the inventory and what is in the
     * grid now (placing a recipe puts the grid back first), each slot taking the alternative there is most of.
     */
    private void updateMissing() {
        missing.clear();
        AbstractContainerMenu menu = fillTarget();
        if (menu == null) {
            return;
        }
        Map<Item, Integer> have = new IdentityHashMap<>();
        Inventory inv = minecraft.player.getInventory();
        for (int i = 0; i < Inventory.INVENTORY_SIZE; i++) {
            ItemStack s = inv.getItem(i);
            if (!s.isEmpty()) {
                have.merge(s.getItem(), s.getCount(), Integer::sum);
            }
        }
        for (Slot slot : gridSlots(menu)) {
            if (slot.hasItem()) {
                have.merge(slot.getItem().getItem(), slot.getItem().getCount(), Integer::sum);
            }
        }
        List<ViewRecipe> list = list();
        int start = page * perPage();
        for (int i = start; i < Math.min(list.size(), start + perPage()); i++) {
            ViewRecipe r = list.get(i);
            if (canFill(menu, r)) {
                missing.put(r, missingSlots(r, new IdentityHashMap<>(have)));
            }
        }
    }

    private static boolean[] missingSlots(ViewRecipe r, Map<Item, Integer> have) {
        List<List<ItemStack>> in = r.inputs();
        boolean[] out = new boolean[in.size()];
        // the slots with the fewest choices pick first
        Integer[] order = new Integer[in.size()];
        for (int i = 0; i < order.length; i++) {
            order[i] = i;
        }
        java.util.Arrays.sort(order, (a, b) -> Integer.compare(in.get(a).size(), in.get(b).size()));
        for (int i : order) {
            List<ItemStack> alts = in.get(i);
            if (alts.isEmpty()) {
                continue;
            }
            Item best = null;
            int most = 0;
            for (ItemStack alt : alts) {
                int n = have.getOrDefault(alt.getItem(), 0);
                if (n > most) {
                    most = n;
                    best = alt.getItem();
                }
            }
            if (best == null) {
                out[i] = true;
            } else {
                have.put(best, most - 1);
            }
        }
        return out;
    }

    private static boolean anyMissing(boolean[] m) {
        for (boolean b : m) {
            if (b) {
                return true;
            }
        }
        return false;
    }

    private void fill(ViewRecipe r, boolean max) {
        AbstractContainerMenu menu = fillTarget();
        AbstractContainerScreen<?> screen = RecipeViewer.containerOf(parent);
        if (menu == null || screen == null || r.id() == null) {
            return;
        }
        // back to the window first: the server's answer (the filled grid, or the recipe's outline) goes there
        minecraft.gui.setScreen(screen);
        BrasshavenNet.toServer(new RecipeFillMsg(menu.containerId, r.id(), max));
    }

    @Override
    public void tick() {
        // the inventory can change while the screen is open (items picked up, a hopper...)
        if (++missingAge >= 10) {
            missingAge = 0;
            updateMissing();
        }
    }

    // ------------------------------------------------------------------ drawing

    /** The item a slot shows now: one per second through its choices, held still while Shift is down. */
    private ItemStack cycle(List<ItemStack> alts) {
        if (alts.isEmpty()) {
            return ItemStack.EMPTY;
        }
        long t = minecraft.hasShiftDown() ? frozen : (frozen = Util.getMillis() / 1000L);
        return alts.get((int) (t % alts.size()));
    }

    private long frozen;
    // what the mouse is over, found while drawing
    private ItemStack hoverStack = ItemStack.EMPTY;
    private @Nullable ViewRecipe hoverRecipe;
    private int hoverAlts;
    private boolean hoverMissing;
    private boolean hoverOutput;
    private @Nullable ViewRecipe hoverPlus;
    private int hoverTab = -1;

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, getTitle(), left, top, W, H);
        hoverStack = ItemStack.EMPTY;
        hoverRecipe = null;
        hoverPlus = null;
        hoverTab = -1;
        hoverShapeless = false;
        // header: the item, its name and mod
        WfGui.sprite(g, WfGui.INSET, left + 10, top + 14, 20, 20);
        g.item(focus, left + 12, top + 16);
        if (over(mouseX, mouseY, left + 10, top + 14, 20, 20)) {
            hover(focus, null, 1, false, false);
        }
        int nameW = modeButton.getX() - (left + 35) - 4;
        WfGui.textClipped(g, font, focusName, left + 35, top + 15, nameW, WfGui.INK, false);
        WfGui.textClipped(g, font, focusMod, left + 35, top + 25, nameW, WfGui.INK_SOFT, false);
        // tabs
        for (int i = 0; i < tabs.size(); i++) {
            int tx = left + 10 + i * (TAB + 2);
            int ty = top + 38;
            boolean on = i == tab;
            boolean hover = over(mouseX, mouseY, tx, ty, TAB, 20);
            WfGui.sprite(g, on ? (hover ? WfWidgets.BUTTON_ON_HOVER : WfWidgets.BUTTON_ON) : hover ? WfGui.BUTTON_HOVER : WfGui.BUTTON,
                    tx, ty, TAB, 20);
            g.item(tabs.get(i).icon(), tx + 3, ty + 2);
            if (hover) {
                hoverTab = i;
            }
        }
        int textX = left + 10 + tabs.size() * (TAB + 2) + 4;
        WfGui.textClipped(g, font, tabText, textX, top + 44, left + W - 10 - textX, WfGui.INK, false);
        // the recipes of this page
        WfGui.sprite(g, WfGui.CARD, left + CARD_X - 2, top + CARD_Y - 2, CARD_W + 4, CARD_H + 4);
        List<ViewRecipe> list = list();
        int start = page * perPage();
        for (int i = start; i < Math.min(list.size(), start + perPage()); i++) {
            drawRecipe(g, list.get(i), cellX(i - start), cellY(i - start), mouseX, mouseY);
        }
        if (list.isEmpty()) {
            Component msg = !ClientRecipes.ready() ? Component.translatable("gui.brasshaven.recipes.waiting")
                    : Component.translatable(uses ? "gui.brasshaven.recipes.no_uses" : "gui.brasshaven.recipes.no_recipes", focusName);
            g.textWithWordWrap(font, msg, left + CARD_X + 8, top + CARD_Y + 10, CARD_W - 16, WfGui.INK, false);
        }
        WfGui.centered(g, font, pageText, left + W / 2, top + H - 20, WfGui.INK_SOFT);
        g.centeredText(font, hint, left + W / 2, top + H + 4, WfGui.CREAM);
        super.extractRenderState(g, mouseX, mouseY, a);
        tooltip(g, mouseX, mouseY);
    }

    private static boolean over(int mx, int my, int x, int y, int w, int h) {
        return mx >= x && mx < x + w && my >= y && my < y + h;
    }

    private void hover(ItemStack stack, @Nullable ViewRecipe r, int alts, boolean missing, boolean output) {
        hoverStack = stack;
        hoverRecipe = r;
        hoverAlts = alts;
        hoverMissing = missing;
        hoverOutput = output;
    }

    /** An 18 px slot with the current choice of {@code alts}. */
    private void slot(GuiGraphicsExtractor g, int x, int y, List<ItemStack> alts, @Nullable ViewRecipe r, boolean red, int mx, int my) {
        slot(g, x, y, cycle(alts), alts.size(), r, red, mx, my);
    }

    private void slot(GuiGraphicsExtractor g, int x, int y, ItemStack s, int alts, @Nullable ViewRecipe r, boolean red, int mx, int my) {
        WfGui.sprite(g, SLOT, x, y, 18, 18);
        if (!s.isEmpty()) {
            g.item(s, x + 1, y + 1);
            g.itemDecorations(font, s, x + 1, y + 1);
        }
        if (red) {
            // over the item, like a slot's highlight: a full block would hide a tint drawn under it
            g.fill(x + 1, y + 1, x + 17, y + 17, RED);
        }
        if (over(mx, my, x, y, 18, 18)) {
            g.fill(x + 1, y + 1, x + 17, y + 17, 0x50FFF5DC);
            if (!s.isEmpty()) {
                hover(s, r, alts, red, false);
            }
        }
    }

    /** The 26 px result slot. */
    private void output(GuiGraphicsExtractor g, int x, int y, List<ItemStack> alts, ViewRecipe r, int mx, int my) {
        WfGui.sprite(g, SLOT_BIG, x, y, 26, 26);
        ItemStack s = cycle(alts);
        if (!s.isEmpty()) {
            g.item(s, x + 5, y + 5);
            g.itemDecorations(font, s, x + 5, y + 5);
        }
        if (over(mx, my, x, y, 26, 26)) {
            g.fill(x + 1, y + 1, x + 25, y + 25, 0x50FFF5DC);
            if (!s.isEmpty()) {
                hover(s, r, alts.size(), false, true);
            }
        }
    }

    private void plus(GuiGraphicsExtractor g, int x, int y, ViewRecipe r, int mx, int my) {
        boolean[] m = missing.get(r);
        if (m == null) {
            return;
        }
        boolean lacking = anyMissing(m);
        boolean hover = over(mx, my, x, y, 12, 12);
        WfGui.sprite(g, hover ? ItemGrid.SMALL_HOVER : ItemGrid.SMALL, x, y, 12, 12);
        WfGui.sprite(g, lacking ? PLUS_MISSING : PLUS, x + 1, y + 1, 10, 10);
        if (hover) {
            hoverPlus = r;
        }
    }

    private boolean red(ViewRecipe r, int slot) {
        boolean[] m = missing.get(r);
        return m != null && slot < m.length && m[slot];
    }

    private void drawRecipe(GuiGraphicsExtractor g, ViewRecipe r, int x, int y, int mx, int my) {
        List<List<ItemStack>> in = r.inputs();
        switch (r.category()) {
            case CRAFTING -> {
                for (int i = 0; i < 9; i++) {
                    int sx = x + 4 + (i % 3) * 18;
                    int sy = y + 4 + (i / 3) * 18;
                    int k = craftingInput(r, i % 3, i / 3);
                    slot(g, sx, sy, k >= 0 ? in.get(k) : List.of(), r, k >= 0 && red(r, k), mx, my);
                }
                WfGui.sprite(g, ARROW, x + 62, y + 23, 22, 15);
                if (r.shapeless()) {
                    WfGui.sprite(g, SHAPELESS, x + 67, y + 8, 12, 12);
                    if (over(mx, my, x + 67, y + 8, 12, 12)) {
                        hoverShapeless = true;
                    }
                }
                output(g, x + 90, y + 18, r.outputs(), r, mx, my);
                plus(g, x + 120, y + 25, r, mx, my);
            }
            case SMELTING, BLASTING, SMOKING, CAMPFIRE -> {
                slot(g, x + 4, y + 2, in.get(0), r, red(r, 0), mx, my);
                WfGui.sprite(g, FLAME, x + 6, y + 22, 14, 14);
                WfGui.sprite(g, ARROW, x + 28, y + 8, 22, 15);
                output(g, x + 56, y + 3, r.outputs(), r, mx, my);
                plus(g, x + 86, y + 10, r, mx, my);
                g.text(font, cookText(r), x + 26, y + 29, WfGui.INK_SOFT, false);
            }
            case STONECUTTING -> {
                slot(g, x + 4, y + 4, in.get(0), r, false, mx, my);
                WfGui.sprite(g, ARROW, x + 26, y + 6, 22, 15);
                output(g, x + 52, y, r.outputs(), r, mx, my);
            }
            case SMITHING -> {
                for (int i = 0; i < 3; i++) {
                    slot(g, x + 4 + i * 18, y + 4, in.get(i), r, false, mx, my);
                }
                WfGui.sprite(g, ARROW, x + 62, y + 6, 22, 15);
                output(g, x + 88, y, r.outputs(), r, mx, my);
            }
            case CHISEL -> {
                slot(g, x + 4, y + 13, in.get(0), r, false, mx, my);
                WfGui.sprite(g, ARROW, x + 26, y + 15, 22, 15);
                List<ItemStack> outs = r.outputs();
                for (int i = 0; i < Math.min(24, outs.size()); i++) {
                    slot(g, x + 54 + (i % 12) * 18, y + 4 + (i / 12) * 18, outs.get(i), 1, r, false, mx, my);
                }
            }
            default -> {
                slot(g, x + 4, y + 4, r.station(), r, false, mx, my);
                WfGui.sprite(g, ARROW, x + 26, y + 6, 22, 15);
                output(g, x + 52, y, r.outputs(), r, mx, my);
            }
        }
    }

    private boolean hoverShapeless;

    /** Which input fills the crafting grid's cell (col, row), or -1. */
    private static int craftingInput(ViewRecipe r, int col, int row) {
        if (r.width() > 0) {
            return col < r.width() && row < r.height() ? row * r.width() + col : -1;
        }
        int k = row * 3 + col;
        return k < r.inputs().size() ? k : -1;
    }

    private final Map<ViewRecipe, String> cookTexts = new IdentityHashMap<>();

    /** "10 s - 0.1 XP" (seconds and experience of a furnace recipe), built once per recipe. */
    private String cookText(ViewRecipe r) {
        return cookTexts.computeIfAbsent(r, k -> {
            String dot = Component.translatable("gui.brasshaven.machine.decimal").getString();
            String secs = k.cookTime() % 20 == 0 ? String.valueOf(k.cookTime() / 20)
                    : String.format(Locale.ROOT, "%.1f", k.cookTime() / 20.0).replace(".", dot);
            String xp = String.format(Locale.ROOT, "%.2f", k.xp()).replaceAll("0+$", "").replaceAll("\\.$", "").replace(".", dot);
            return Component.translatable("gui.brasshaven.recipes.cook", secs, xp).getString();
        });
    }

    private void tooltip(GuiGraphicsExtractor g, int mx, int my) {
        if (hoverPlus != null) {
            List<Component> lines = new ArrayList<>();
            boolean[] m = missing.get(hoverPlus);
            lines.add(Component.translatable("gui.brasshaven.recipes.fill"));
            lines.add(Component.translatable("gui.brasshaven.recipes.fill.tip").withStyle(ChatFormatting.GRAY));
            lines.add(Component.translatable("gui.brasshaven.recipes.fill.max").withStyle(ChatFormatting.GRAY));
            if (m != null && anyMissing(m)) {
                lines.add(Component.translatable("gui.brasshaven.recipes.fill.missing").withStyle(ChatFormatting.RED));
                for (int i = 0; i < m.length; i++) {
                    if (m[i] && !hoverPlus.inputs().get(i).isEmpty()) {
                        lines.add(Component.literal("- ").append(hoverPlus.inputs().get(i).get(0).getHoverName())
                                .withStyle(ChatFormatting.RED));
                    }
                }
                lines.add(Component.translatable("gui.brasshaven.recipes.fill.ghost").withStyle(ChatFormatting.GRAY));
            }
            g.setComponentTooltipForNextFrame(font, lines, mx, my);
            return;
        }
        if (hoverTab >= 0) {
            RecipeCategory c = tabs.get(hoverTab);
            g.setComponentTooltipForNextFrame(font, List.of(c.title(),
                    Component.translatable("gui.brasshaven.recipes.count", current().get(c).size()).withStyle(ChatFormatting.GRAY)), mx, my);
            return;
        }
        if (!hoverStack.isEmpty()) {
            List<Component> lines = new ArrayList<>(Screen.getTooltipFromItem(minecraft, hoverStack));
            if (hoverMissing) {
                lines.add(Component.translatable("gui.brasshaven.recipes.missing").withStyle(ChatFormatting.RED));
            }
            if (hoverAlts > 1) {
                lines.add(Component.translatable("gui.brasshaven.recipes.alternatives", hoverAlts).withStyle(ChatFormatting.GRAY));
            }
            if (hoverOutput && hoverRecipe != null && hoverRecipe.id() != null && minecraft.options.advancedItemTooltips) {
                lines.add(Component.translatable("gui.brasshaven.recipes.id", hoverRecipe.id().toString()).withStyle(ChatFormatting.DARK_GRAY));
            }
            g.setTooltipForNextFrame(font, lines, hoverStack.getTooltipImage(), mx, my);
            return;
        }
        if (hoverShapeless) {
            g.setTooltipForNextFrame(font, Component.translatable("gui.brasshaven.recipes.shapeless"), mx, my);
        }
    }

    // ------------------------------------------------------------------ input

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        int mx = (int) event.x();
        int my = (int) event.y();
        if (hoverPlus != null && event.button() == 0) {
            fill(hoverPlus, event.hasShiftDown());
            return true;
        }
        for (int i = 0; i < tabs.size(); i++) {
            if (over(mx, my, left + 10 + i * (TAB + 2), top + 38, TAB, 20)) {
                selectTab(i);
                return true;
            }
        }
        if (!hoverStack.isEmpty() && (event.button() == 0 || event.button() == 1)
                && over(mx, my, left + CARD_X - 2, top + CARD_Y - 2, CARD_W + 4, CARD_H + 4)) {
            show(hoverStack, event.button() == 1, true);
            return true;
        }
        if (event.button() == 3) {
            back(); // the mouse's "back" side button
            return true;
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        if (scrollY != 0) {
            turn(scrollY > 0 ? -1 : 1);
        }
        return true;
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (!hoverStack.isEmpty() && (com.brasshaven.client.BrasshavenClient.RECIPES_KEY.matches(event)
                || com.brasshaven.client.BrasshavenClient.USES_KEY.matches(event))) {
            show(hoverStack, com.brasshaven.client.BrasshavenClient.USES_KEY.matches(event), true);
            return true;
        }
        int key = event.key();
        if (key == InputConstants.KEY_BACKSPACE) {
            back();
            return true;
        }
        if (event.isRight() || key == InputConstants.KEY_PAGEDOWN) {
            turn(1);
            return true;
        }
        if (event.isLeft() || key == InputConstants.KEY_PAGEUP) {
            turn(-1);
            return true;
        }
        if (event.isDown() || key == InputConstants.KEY_TAB) {
            selectTab(tabs.isEmpty() ? 0 : (tab + 1) % tabs.size());
            return true;
        }
        if (event.isUp()) {
            selectTab(tabs.isEmpty() ? 0 : (tab + tabs.size() - 1) % tabs.size());
            return true;
        }
        if (minecraft.options.keyInventory.matches(event)) {
            onClose();
            return true;
        }
        return super.keyPressed(event);
    }

    /** Back to the window the viewer was opened from (the container stays open on the server meanwhile). */
    @Override
    public void onClose() {
        minecraft.gui.setScreen(parent);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    // ------------------------------------------------------------------ CI

    /** The first recipe on this page that the "+" button can place, or null (CI). */
    public @Nullable ViewRecipe firstFillable() {
        for (ViewRecipe r : list()) {
            if (missing.containsKey(r)) {
                return r;
            }
        }
        return null;
    }

    /** Presses the "+" button of a recipe (CI). */
    public void pressFill(ViewRecipe r, boolean max) {
        fill(r, max);
    }

    /** Selects the tab of a category, if the item has one (CI). */
    public void selectCategory(RecipeCategory c) {
        selectTab(tabs.indexOf(c));
    }

    public int recipeCount() {
        return count(current());
    }

    /**
     * What is wrong with the screen's widgets, or null (CI): exactly the five of the last init(), each once, each inside
     * the window.
     */
    public @Nullable String widgetProblem() {
        List<? extends net.minecraft.client.gui.components.events.GuiEventListener> kids = children();
        List<net.minecraft.client.gui.components.AbstractWidget> expected = List.of(modeButton, manualButton, backButton, prev, next);
        if (kids.size() != expected.size()) {
            return kids.size() + " widgets instead of " + expected.size() + ": " + kids;
        }
        for (var w : expected) {
            if (kids.stream().filter(k -> k == w).count() != 1) {
                return "widget " + w.getMessage().getString() + " not listed once";
            }
            if (w.getX() < left || w.getY() < top || w.getRight() > left + W || w.getBottom() > top + H) {
                return "widget " + w.getMessage().getString() + " at " + w.getX() + "," + w.getY() + " outside the window";
            }
        }
        return null;
    }
}
