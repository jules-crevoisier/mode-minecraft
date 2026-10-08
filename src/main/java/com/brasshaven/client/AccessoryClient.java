package com.brasshaven.client;

import com.brasshaven.Brasshaven;
import com.brasshaven.accessory.AccessoryContainer;
import com.brasshaven.accessory.AccessorySlot;
import com.brasshaven.accessory.AccessorySlotType;
import com.brasshaven.accessory.Accessories;
import com.brasshaven.network.AccessoryCreativeMsg;
import com.brasshaven.network.AccessoryMoveMsg;
import com.brasshaven.network.BrasshavenNet;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.AbstractRecipeBookScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.screens.recipebook.RecipeBookComponent;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.ContainerScreenEvent;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;
import org.jetbrains.annotations.Nullable;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Optional;
import java.util.function.Predicate;

/**
 * The accessory slots on screen: a column left of the armour in the survival inventory (hidden while the recipe book
 * covers it), a hand-drawn panel of five slots right of the armour in the creative inventory tab (the creative tab
 * would put the real slots on top of the hotbar), the empty-slot hint, and shift-click to wear an accessory (sent to
 * the server, which moves it: the vanilla quick-move doesn't know these slots).
 */
public final class AccessoryClient {
    private static final Identifier PANEL = Brasshaven.id("accessory/panel");
    private static final Identifier SLOT = Brasshaven.id("accessory/slot");
    /** Creative inventory tab: slot positions right of the armour (three, then two). */
    private static final int[][] CREATIVE = {{127, 6}, {145, 6}, {163, 6}, {127, 33}, {145, 33}};
    private static @Nullable Field recipeBook;

    private AccessoryClient() {}

    public static void register() {
        try {
            recipeBook = ObfuscationReflectionHelper.findField(AbstractRecipeBookScreen.class, "recipeBookComponent");
        } catch (RuntimeException e) {
            Brasshaven.LOGGER.warn("Brasshaven: recipe book state not readable, accessory slots stay visible", e);
        }
        ScreenEvent.Render.Pre.BUS.addListener((Predicate<ScreenEvent.Render.Pre>) e -> {
            // the creative tab wraps every inventory slot at a fixed place (ours would land on the hotbar): there the
            // real slots stay hidden and the creative panel below stands in for them
            AccessorySlot.hidden = e.getScreen() instanceof InventoryScreen inv && recipeBookOpen(inv)
                    || e.getScreen() instanceof CreativeModeInventoryScreen;
            return false;
        });
        ContainerScreenEvent.Render.Background.BUS.addListener(AccessoryClient::background);
        ScreenEvent.MouseButtonPressed.Pre.BUS.addListener((Predicate<ScreenEvent.MouseButtonPressed.Pre>) AccessoryClient::click);
    }

    private static boolean recipeBookOpen(InventoryScreen screen) {
        if (recipeBook == null) {
            return false;
        }
        try {
            return recipeBook.get(screen) instanceof RecipeBookComponent<?> book && book.isVisible();
        } catch (IllegalAccessException e) {
            return false;
        }
    }

    private static boolean ownInventory(Object screen) {
        return screen instanceof InventoryScreen
                || screen instanceof CreativeModeInventoryScreen c && c.isInventoryOpen();
    }

    // ------------------------------------------------------------------ drawing
    private static void background(ContainerScreenEvent.Render.Background e) {
        AbstractContainerScreen<?> screen = e.getContainerScreen();
        GuiGraphicsExtractor g = e.getGuiGraphics();
        int left = screen.getGuiLeft(), top = screen.getGuiTop();
        if (screen instanceof InventoryScreen) {
            if (AccessorySlot.hidden) {
                return;
            }
            int n = AccessorySlotType.LAYOUT.length;
            g.blitSprite(RenderPipelines.GUI_TEXTURED, PANEL, left + Accessories.INV_X - 5, top + Accessories.INV_Y - 5,
                    26, n * 18 + 8);
            for (int i = 0; i < n; i++) {
                g.blitSprite(RenderPipelines.GUI_TEXTURED, SLOT, left + Accessories.INV_X - 1, top + Accessories.INV_Y - 1 + i * 18,
                        18, 18);
            }
        } else if (screen instanceof CreativeModeInventoryScreen creative && creative.isInventoryOpen()) {
            creativePanel(creative, g, e.getMouseX(), e.getMouseY());
            return;
        } else {
            return;
        }
        // hovering an empty slot: what goes there
        Slot hovered = screen.getSlotUnderMouse();
        if (hovered instanceof AccessorySlot a && !a.hasItem() && screen.getMenu().getCarried().isEmpty()) {
            emptyHint(g, a.type, e.getMouseX(), e.getMouseY());
        }
    }

    private static void emptyHint(GuiGraphicsExtractor g, AccessorySlotType type, int mx, int my) {
        g.setTooltipForNextFrame(Minecraft.getInstance().font, List.of(
                Component.translatable("gui.brasshaven.accessory.empty", type.label()),
                Component.translatable("tooltip.brasshaven.accessory.worn").withStyle(ChatFormatting.GRAY)),
                Optional.empty(), mx, my);
    }

    // ------------------------------------------------------------------ creative inventory tab
    /** Index of the creative panel slot under the mouse, or -1. */
    private static int creativeSlotAt(CreativeModeInventoryScreen screen, double mx, double my) {
        for (int i = 0; i < CREATIVE.length; i++) {
            int x = screen.getGuiLeft() + CREATIVE[i][0], y = screen.getGuiTop() + CREATIVE[i][1];
            if (mx >= x - 1 && mx < x + 17 && my >= y - 1 && my < y + 17) {
                return i;
            }
        }
        return -1;
    }

    /** The five accessory slots right of the armour, drawn and handled by hand (see {@link #creativeClick}). */
    private static void creativePanel(CreativeModeInventoryScreen screen, GuiGraphicsExtractor g, int mx, int my) {
        Player player = Minecraft.getInstance().player;
        if (player == null) {
            return;
        }
        AccessoryContainer worn = Accessories.get(player);
        int hover = creativeSlotAt(screen, mx, my);
        for (int i = 0; i < CREATIVE.length && i < worn.getContainerSize(); i++) {
            int x = screen.getGuiLeft() + CREATIVE[i][0], y = screen.getGuiTop() + CREATIVE[i][1];
            g.blitSprite(RenderPipelines.GUI_TEXTURED, SLOT, x - 1, y - 1, 18, 18);
            ItemStack stack = worn.getItem(i);
            if (stack.isEmpty()) {
                g.blitSprite(RenderPipelines.GUI_TEXTURED, worn.type(i).icon, x, y, 16, 16);
            } else {
                g.item(stack, x, y);
                g.itemDecorations(Minecraft.getInstance().font, stack, x, y);
            }
            if (i == hover) {
                g.fill(x, y, x + 16, y + 16, 0x80FFFFFF);
            }
        }
        if (hover >= 0 && screen.getMenu().getCarried().isEmpty()) {
            ItemStack stack = worn.getItem(hover);
            if (stack.isEmpty()) {
                emptyHint(g, worn.type(hover), mx, my);
            } else {
                g.setTooltipForNextFrame(Minecraft.getInstance().font, stack, mx, my);
            }
        }
    }

    /**
     * A click on the creative panel: pick up, put down or swap with the cursor (a creative player's cursor is their
     * own), shift-click takes it off into the inventory. The server applies it (AccessoryCreativeMsg).
     */
    private static boolean creativeClick(CreativeModeInventoryScreen screen, Player player, double mx, double my,
                                         int button, boolean shift) {
        int i = creativeSlotAt(screen, mx, my);
        if (i < 0 || button > 1) {
            return false;
        }
        AccessoryContainer worn = Accessories.get(player);
        ItemStack inSlot = worn.getItem(i);
        ItemStack carried = screen.getMenu().getCarried();
        if (shift) {
            if (!inSlot.isEmpty()) {
                BrasshavenNet.toServer(new AccessoryMoveMsg(i, false));
            }
            return true;
        }
        if (!carried.isEmpty() && !worn.canPlaceItem(i, carried)) {
            return true; // doesn't fit this slot: nothing happens (the item stays on the cursor)
        }
        ItemStack put = carried.isEmpty() ? ItemStack.EMPTY : carried.copyWithCount(1);
        ItemStack rest = carried.isEmpty() ? ItemStack.EMPTY : carried.copyWithCount(carried.getCount() - 1);
        if (!rest.isEmpty() && !inSlot.isEmpty()) {
            return true; // a stack on the cursor and an item in the slot: no room to swap
        }
        worn.setItem(i, put);
        screen.getMenu().setCarried(inSlot.isEmpty() ? rest : inSlot.copy());
        BrasshavenNet.toServer(new AccessoryCreativeMsg(i, put.copy()));
        return true;
    }

    // ------------------------------------------------------------------ shift-click
    private static boolean click(ScreenEvent.MouseButtonPressed.Pre e) {
        if (!ownInventory(e.getScreen()) || !(e.getScreen() instanceof AbstractContainerScreen<?> screen)) {
            return false;
        }
        Player player = Minecraft.getInstance().player;
        if (player == null) {
            return false;
        }
        if (screen instanceof CreativeModeInventoryScreen creative && creative.isInventoryOpen()
                && creativeClick(creative, player, e.getMouseX(), e.getMouseY(), e.getInfo().button(), e.getInfo().hasShiftDown())) {
            return true;
        }
        Slot s = screen.getSlotUnderMouse();
        if (e.getInfo().button() != 0 || !e.getInfo().hasShiftDown() || s == null || !s.hasItem()
                || !screen.getMenu().getCarried().isEmpty()) {
            return false;
        }
        if (s instanceof AccessorySlot) {
            return false; // survival: the vanilla quick-move puts it back into the inventory
        }
        if (s.container != player.getInventory()) {
            return false;
        }
        int index = s.getSlotIndex();
        ItemStack stack = s.getItem();
        if ((index < Inventory.INVENTORY_SIZE || index == Inventory.SLOT_OFFHAND) && AccessorySlotType.of(stack) != null
                && Accessories.freeSlotFor(player, stack) >= 0) {
            BrasshavenNet.toServer(new AccessoryMoveMsg(index, true));
            return true;
        }
        return false;
    }
}
