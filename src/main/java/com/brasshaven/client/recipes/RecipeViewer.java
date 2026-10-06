package com.brasshaven.client.recipes;

import com.brasshaven.Brasshaven;
import com.brasshaven.client.BrasshavenClient;
import com.brasshaven.config.BrasshavenClientConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.event.entity.player.ItemTooltipEvent;
import net.minecraftforge.fml.ModList;
import org.jetbrains.annotations.Nullable;

import java.util.function.Predicate;

/**
 * The built-in recipe viewer ("JEI-like", in the mod's theme), client side. In any container screen: R over an item
 * (a slot or the item list) shows how to make it, U what it is used in (RecipeScreen); I shows or hides the item list
 * beside the window (RecipePanel), remembered in the client config. The recipes come from the server (RecipeSync).
 *
 * <p>When JEI is installed the viewer steps aside (no list, no keys, no tooltip line) unless the client config says to
 * keep both ({@code recipes.alongsideJei}).
 */
public final class RecipeViewer {
    private static final boolean JEI = ModList.isLoaded("jei");

    private RecipeViewer() {}

    public static boolean enabled() {
        return BrasshavenClientConfig.RECIPE_VIEWER.get() && (!JEI || BrasshavenClientConfig.RECIPE_WITH_JEI.get());
    }

    private static boolean panelOn(Screen s) {
        return s instanceof AbstractContainerScreen<?> && RecipePanel.shown();
    }

    public static void register() {
        ScreenEvent.Init.Post.BUS.addListener(e -> {
            if (enabled() && e.getScreen() instanceof AbstractContainerScreen<?>) {
                RecipePanel.grid().unfocus(); // a window opens with the keyboard its own, never in the list's search
                // the first inventory opened after joining decodes the recipes and lists the items, not the first R
                ClientRecipes.warmUp();
                ItemIndex.ensure();
            }
        });
        ScreenEvent.Render.Post.BUS.addListener(e -> {
            if (panelOn(e.getScreen())) {
                RecipePanel.render((AbstractContainerScreen<?>) e.getScreen(), e.getGuiGraphics(), e.getMouseX(), e.getMouseY(),
                        e.getPartialTick());
            }
        });
        ScreenEvent.MouseButtonPressed.Pre.BUS.addListener((Predicate<ScreenEvent.MouseButtonPressed.Pre>) e ->
                panelOn(e.getScreen()) && RecipePanel.mouseClicked((AbstractContainerScreen<?>) e.getScreen(), e.getMouseX(),
                        e.getMouseY(), e.getInfo().button()));
        ScreenEvent.MouseButtonReleased.Pre.BUS.addListener((Predicate<ScreenEvent.MouseButtonReleased.Pre>) e ->
                panelOn(e.getScreen()) && RecipePanel.over((AbstractContainerScreen<?>) e.getScreen(), e.getMouseX(), e.getMouseY()));
        ScreenEvent.MouseScrolled.Pre.BUS.addListener((Predicate<ScreenEvent.MouseScrolled.Pre>) e ->
                panelOn(e.getScreen()) && RecipePanel.mouseScrolled((AbstractContainerScreen<?>) e.getScreen(), e.getMouseX(),
                        e.getMouseY(), e.getDeltaY()));
        ScreenEvent.KeyPressed.Pre.BUS.addListener((Predicate<ScreenEvent.KeyPressed.Pre>) RecipeViewer::onKey);
        ScreenEvent.CharacterTyped.Pre.BUS.addListener((Predicate<ScreenEvent.CharacterTyped.Pre>) e ->
                panelOn(e.getScreen()) && RecipePanel.grid().charTyped(e.getInfo()));
        ScreenEvent.RenderInventoryMobEffects.BUS.addListener((Predicate<ScreenEvent.RenderInventoryMobEffects>) e -> {
            if (panelOn(e.getScreen()) && RecipePanel.compactEffects((AbstractContainerScreen<?>) e.getScreen())) {
                e.setCompact(true);
            }
            return false;
        });
        ItemTooltipEvent.BUS.addListener(RecipeViewer::onTooltip);
        ClientPlayerNetworkEvent.LoggingOut.BUS.addListener(e -> ClientRecipes.clear());
    }

    private static boolean onKey(ScreenEvent.KeyPressed.Pre e) {
        if (!(e.getScreen() instanceof AbstractContainerScreen<?> s) || !enabled()) {
            return false;
        }
        KeyEvent key = e.getInfo();
        if (RecipePanel.shown() && RecipePanel.grid().searchFocused()) {
            return RecipePanel.grid().keyPressed(key); // typing in the list's search: every key goes there
        }
        if (ItemGrid.typing(s)) {
            return false; // another search box (creative inventory, chest search) has the keyboard
        }
        if (BrasshavenClient.RECIPE_PANEL_KEY.matches(key)) {
            BrasshavenClientConfig.RECIPE_PANEL.set(!BrasshavenClientConfig.RECIPE_PANEL.get());
            BrasshavenClientConfig.RECIPE_PANEL.save();
            return true;
        }
        ItemStack stack = RecipePanel.shown() ? RecipePanel.hovered(s) : ItemStack.EMPTY;
        if (stack.isEmpty()) {
            Slot slot = s.getSlotUnderMouse();
            if (slot != null && slot.hasItem()) {
                stack = slot.getItem();
            }
        }
        return !stack.isEmpty() && lookup(key, stack, s);
    }

    /** R or U pressed over {@code stack}: opens its recipes or uses. */
    static boolean lookup(KeyEvent key, ItemStack stack, Screen from) {
        if (BrasshavenClient.RECIPES_KEY.matches(key)) {
            open(stack, false, from);
            return true;
        }
        if (BrasshavenClient.USES_KEY.matches(key)) {
            open(stack, true, from);
            return true;
        }
        return false;
    }

    /** Shows the recipes ({@code uses} false) or uses of an item; closing the recipe screen goes back to {@code from}. */
    public static void open(ItemStack stack, boolean uses, @Nullable Screen from) {
        if (stack.isEmpty()) {
            return;
        }
        if (from instanceof RecipeScreen recipes) {
            recipes.show(stack, uses, true);
            return;
        }
        Minecraft.getInstance().gui.setScreen(new RecipeScreen(stack, uses, from));
    }

    /** The container screen behind a chain of viewer screens (where the "+" button fills the grid), or null. */
    static @Nullable AbstractContainerScreen<?> containerOf(@Nullable Screen s) {
        for (int guard = 0; guard < 8 && s != null; guard++) {
            if (s instanceof AbstractContainerScreen<?> c) {
                return c;
            }
            s = s instanceof ItemListScreen list ? list.parent : s instanceof RecipeScreen r ? r.parent : null;
        }
        return null;
    }

    /** "R / click: recipes - U / right click: uses", with the player's keys. */
    static Component hint() {
        return Component.translatable("gui.brasshaven.recipes.keys", BrasshavenClient.RECIPES_KEY.getTranslatedKeyMessage(),
                BrasshavenClient.USES_KEY.getTranslatedKeyMessage());
    }

    /** "R: recipes - U: uses" under the mod's items (after the manual line), while the viewer is on. */
    private static void onTooltip(ItemTooltipEvent event) {
        Minecraft mc = Minecraft.getInstance();
        // only tooltips drawn now (the creative search builds tooltips on another thread to index them)
        if (!mc.isSameThread() || mc.gui.screen() == null || !enabled()) {
            return;
        }
        ItemStack stack = event.getItemStack();
        if (!BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals(Brasshaven.MODID)) {
            return;
        }
        event.getToolTip().add(Component.translatable("gui.brasshaven.recipes.tooltip",
                BrasshavenClient.RECIPES_KEY.getTranslatedKeyMessage(), BrasshavenClient.USES_KEY.getTranslatedKeyMessage())
                .withStyle(ChatFormatting.GRAY));
    }
}
